import base64
import hashlib
import json
import os
import re
import shutil
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlencode
from common import *

def library():
    return [{'name':p.name,'size':p.stat().st_size} for p in sorted((ROOT/'droid').glob('*.dscap'),reverse=True)]
def check(resp):
    if resp.status not in range(200,300):
        msg=resp.read(6000)
        try: detail=json.loads(msg).get('error')
        except ValueError: detail=None
        raise ValueError(detail or tr('DroidSphere returned HTTP {status}.', status=resp.status))
def talk(a):
    addr=address(a['address'],8443);pin=a['pin'];origin='https://'+addr;cookie=None
    @contextmanager
    def request(method,path,body=None,headers=None):
        c=connection(addr,pin,timeout=3600)
        try:
            h={'Origin':origin,**(headers or {})}
            if cookie:h['Cookie']=cookie
            if isinstance(body,dict):h['Content-Type']='application/json';body=json.dumps(body).encode()
            c.request(method,path,body,headers=h);res=c.getresponse();check(res);yield res
        finally:c.close()
    with request('POST','/api/login',{'code':a['code']}) as r:
        sc=r.getheader('Set-Cookie','').split(';')[0];r.read()
        if not sc.startswith('ds_session='):raise ValueError(tr('DroidSphere did not confirm the session.'))
        cookie=sc
    try:
        op=a['operation']
        if op=='list':
            with request('GET','/api/state') as r:j=json.load(r)
            return {'machines':[{'id':m['id'],'name':m.get('name'),'arch':m.get('profile',m.get('kind','')),'running':m.get('active',False)} for m in j.get('machines',[])]}
        pw=a['password']
        if not 12<=len(pw)<=256:raise ValueError(tr('Enter a capsule password between 12 and 256 characters.'))
        if op=='pull':
            mid=str(a['id'])
            if not re.fullmatch('[a-f0-9]{12}',mid):raise ValueError(tr('Invalid VM ID.'))
            with request('POST','/api/export-ticket',{'id':mid,'password':pw}) as r:ticket=json.load(r)['grant']
            target=ROOT/'droid'/f'{time.strftime("%Y%m%d-%H%M%S")}-{mid}-{secrets.token_hex(3)}.dscap'
            tmp=target.with_suffix('.part')
            try:
                with request('GET','/api/backup?'+urlencode({'id':mid,'grant':ticket})) as r,tmp.open('xb') as f:
                    total=int(r.getheader('Content-Length') or 0)
                    if total<=32 or total>100*GIB or total+64*1024**2>shutil.disk_usage(tmp.parent).free:raise ValueError(tr('Check the capsule length and available disk space.'))
                    h=r.read(8)
                    if h!=b'DSVECAP\x02':raise ValueError(tr('This is not an encrypted DroidSphere export.'))
                    f.write(h);received=8
                    while data:=r.read(1024**2):
                        received+=len(data)
                        if received>total:raise ValueError(tr('Invalid transfer length.'))
                        f.write(data)
                    if received!=total:raise ValueError(tr('Transfer incomplete.'))
                    f.flush();os.fsync(f.fileno())
                os.replace(tmp,target)
            finally:tmp.unlink(missing_ok=True)
            return {'file':target.name}
        if op=='push':
            fn=str(a.get('file',''))
            if fn not in [p['name'] for p in library()]:raise ValueError(tr('Select a capsule from this node.'))
            f=ROOT/'droid'/fn
            with f.open('rb') as stream,request('POST','/api/restore',stream,{'X-Capsule-Key':base64.b64encode(pw.encode()).decode(),'Content-Length':str(f.stat().st_size),'Content-Type':'application/octet-stream'}) as r:return json.load(r)
        raise ValueError(tr('Unknown transfer operation.'))
    finally:
        try:
            with request('POST','/api/logout',{}) as r:r.read()
        except (ValueError,OSError):pass
