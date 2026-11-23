import base64
import hashlib
import json
import os
import secrets
import socket
import ssl
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from common import *
from guests import inc, compute

PEERS=PRIVATE/'peers.json'
GRANTS=PRIVATE/'grants.json'
GROUPS=PRIVATE/'groups.json'
def cert():
    with locked('tls'):
        crt=PRIVATE/'node.crt';key=PRIVATE/'node.key'
        if not key.exists() or not crt.exists():
            run('openssl','req','-new','-newkey','ec','-pkeyopt','ec_paramgen_curve:P-256','-x509','-nodes','-days','3650','-subj','/CN=LinuxSphere-node','-keyout',key,'-out',crt)
            key.chmod(0o600)
        return crt,key
def fingerprint():
    return hashlib.sha256(ssl.PEM_cert_to_DER_cert(cert()[0].read_text())).hexdigest()
def invite():
    with locked('grants'):
        token=secrets.token_urlsafe(25);atomic(PRIVATE/'invite.json',{'digest':digest(token),'end':time.time()+600})
    return {'code':fingerprint()+'.'+token,'minutes':10}
def enroll(a):
    with locked('grants'):
        inv=PRIVATE/'invite.json';j=jsonread(inv,{})
        if time.time()>j.get('end',0) or not secrets.compare_digest(j.get('digest',''),digest(str(a.get('code','')))):raise PermissionError(tr('Invalid or expired invitation.'))
        alias=name(a['manager']);grants=jsonread(GRANTS,{})
        token=secrets.token_urlsafe(36);grants[alias]=digest(token);atomic(GRANTS,grants);inv.unlink()
        return {'token':token,'host':socket.gethostname()}
def request(peer,path,obj,timeout=120):
    conn=connection(peer['address'],peer['pin'],timeout)
    try:
        headers={'Content-Type':'application/json','Accept-Language':language()}
        if peer.get('token'):headers['Authorization']='Bearer '+peer['token']
        conn.request('POST',path,json.dumps(obj).encode(),headers)
        r=conn.getresponse();result=json.loads(r.read(4<<20))
        if r.status not in range(200,300):raise ValueError(result.get('error',f'HTTP {r.status}'))
        return result
    finally:conn.close()
def add(a):
    if ROLE.read_text().strip() not in ('manager','hybrid'):raise ValueError(tr('Connect nodes from a manager or hybrid host.'))
    alias=name(a['alias'])
    if alias=='local':raise ValueError(tr('The name local is reserved.'))
    pin,sep,token=str(a['code']).strip().partition('.')
    if not sep:raise ValueError(tr('Enter the full invitation code.'))
    peer={'pin':pin,'address':address(a['address'])}
    if pin.lower()==fingerprint():raise ValueError(tr('This is the local node.'))
    with locked('peers'):
        peers=jsonread(PEERS,{})
        if alias in peers or len(peers)>=64:raise ValueError(tr('Node alias is in use or the 64-node limit has been reached.'))
        manager='m-'+Path('/etc/machine-id').read_text().strip()[:24]
        resp=request(peer,'/v1/enroll',{'code':token,'manager':manager});peer['token']=resp['token'];peers[alias]=peer;atomic(PEERS,peers)
    return {'alias':alias}
def remove(a):
    with locked('peers'):
        peers=jsonread(PEERS,{});alias=name(a['alias'])
        p=peers.get(alias)
        if not p:raise ValueError(tr('Node not found.'))
        if any(any(t['node']==alias for t in g['workers']+[g['desktop']]) for g in jsonread(GROUPS,{}).values()):raise ValueError(tr('Remove the associated SphereFusion group first.'))
        request(p,'/v1/revoke',{});peers.pop(alias);atomic(PEERS,peers)
    return {'ok':True}
def peer_list():
    return [{'id':k,'address':p['address']} for k,p in jsonread(PEERS,{}).items()]
def call(node,op,args,timeout=180):
    from control import local
    if node=='local':return local(op,args)
    p=jsonread(PEERS,{}).get(name(node))
    if not p:raise ValueError(tr('Node not found.'))
    return request(p,'/v1/node',{'op':op,'args':args},timeout)
def fusion_save(a):
    g=name(a['name']);d=a['desktop'];ws=a['workers']
    if not isinstance(ws,list) or not 1<=len(ws)<=32:raise ValueError(tr('Select 1 to 32 worker containers.'))
    if len({(t['node'],t['name']) for t in ws})!=len(ws):raise ValueError(tr('The same worker was selected twice.'))
    cache={}
    for t,k in [(d,'vm')]+[(w,'ct') for w in ws]:
        node=name(t['node']);guest=name(t['name'])
        if node not in cache:cache[node]=call(node,'status',{},20)['guests']
        if not any(i['name']==guest and i['kind']==k for i in cache[node]):raise ValueError(tr('Guest not found on the selected node.'))
    with locked('groups'):
        groups=jsonread(GROUPS,{})
        if g in groups:raise ValueError(tr('Group name is in use.'))
        groups[g]={'desktop':d,'workers':ws};atomic(GROUPS,groups)
    return {'name':g}
def group_key(a):
    n=name(a['name'])
    with locked('groups'):
        groups=jsonread(GROUPS,{})
        if n not in groups:raise ValueError(tr('Group not found.'))
        token=secrets.token_urlsafe(32);groups[n]['auth']=digest(token);atomic(GROUPS,groups)
    return {'group':n,'key':token,'pin':fingerprint(),'port':9443}
def group_list():
    return [{'name':n,'desktop':v['desktop'],'workers':v['workers']} for n,v in jsonread(GROUPS,{}).items()]
def group_delete(a):
    with locked('groups'):
        gs=jsonread(GROUPS,{}); gs.pop(name(a['name']),None);atomic(GROUPS,gs)
    return {'ok':True}
def task_cmd(a):
    compute();n=name(a['name']);argv=a['argv']
    if not isinstance(argv,list) or not 1<=len(argv)<=48 or not all(isinstance(z,str) and 0<len(z)<=2048 and '\0' not in z for z in argv):raise ValueError(tr('Invalid argument list.'))
    if not argv[0].startswith('/'):raise ValueError(tr('Enter an absolute path to the guest program.'))
    # Only designated, unprivileged, managed containers serve guest-submitted jobs.
    info=json.loads(inc('query','/1.0/instances/'+n))
    config=info.get('expanded_config',info.get('config',{}))
    if info.get('type')!='container' or config.get('user.linuxsphere')!='true' or config.get('security.privileged','false')!='false' or config.get('raw.lxc') or config.get('raw.idmap'):
        raise ValueError(tr('Use an unprivileged LinuxSphere container as the worker.'))
    input_data=a.get('input','')
    if not isinstance(input_data,str) or len(input_data.encode())>65536:raise ValueError(tr('Input is too large.'))
    with tempfile.TemporaryFile() as std:
        # Bound captured output, duration and concurrent tasks, including requests from guests.
        with locked('fusion-worker-'+n,False):
            result=subprocess.run(['prlimit','--fsize=131072:131072','--','incus','exec',n,'--user','65534','--group','65534','--cwd','/tmp','--','/bin/timeout','60',*argv],
                                  input=input_data.encode(),stdout=std,stderr=subprocess.STDOUT,timeout=70)
        std.seek(0);output=std.read(65536).decode(errors='replace')
    return {'worker':n,'code':result.returncode,'output':output}
def batch(a):
    g=name(a['name']);groups=jsonread(GROUPS,{});group=groups.get(g)
    if not group:raise ValueError(tr('Group not found.'))
    jobs=a['jobs'];workers=group['workers']
    if not isinstance(jobs,list) or not 1<=len(jobs)<=32:raise ValueError(tr('Submit 1 to 32 jobs.'))
    indexed=[None]*len(jobs)
    def process(k):
        worker=workers[k]
        for i in range(k,len(jobs),len(workers)):
            try:indexed[i]={'node':worker['node'],**call(worker['node'],'task',{'name':worker['name'],'argv':jobs[i]['argv'],'input':jobs[i].get('input','')},85)}
            except (ValueError,OSError,subprocess.TimeoutExpired) as e:indexed[i]={'node':worker['node'],'worker':worker['name'],'code':1,'output':str(e)}
    with locked('fusion-'+g,False), ThreadPoolExecutor(min(8,len(workers))) as ex:list(ex.map(localized_task(process),range(min(len(jobs),len(workers)))))
    return {'results':indexed}
