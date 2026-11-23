"""Save a single reversible CPU/RAM change per guest and reject stale undo data."""
import xml.etree.ElementTree as ET
from common import *
from guests import define,inc,vir
def path(kind,n):return PRIVATE/f'resources-{kind}-{n}.json'
def read(kind,n):
    if kind=='vm':
        x=ET.fromstring(vir('dumpxml','--inactive',n))
        return {'uuid':x.findtext('uuid'),'fields':{k:(ET.tostring(x.find(k),encoding='unicode').strip() if x.find(k) is not None else None) for k in ('vcpu','memory','currentMemory')}}
    if kind!='ct':raise ValueError(tr('Unknown guest type.'))
    j=json.loads(inc('query','/1.0/instances/'+n));c=j['config']
    return {'uuid':c.get('volatile.uuid',j.get('created_at')), 'fields':{k:c.get(k) for k in ('limits.cpu','limits.memory')}}
def record(kind,n,before):
    after=read(kind,n)
    if before!=after:atomic(path(kind,n),{'before':before,'after':after})
def undo(kind,n):
    file=path(kind,n);s=jsonread(file)
    if not s:raise ValueError(tr('No change is available to undo.'))
    if read(kind,n)!=s['after']:raise ValueError(tr('Resources have changed since then. Check the current values.'))
    if kind=='vm':
        if vir('domstate',n)!='shut off':raise ValueError(tr('Shut down the VM first.'))
        x=ET.fromstring(vir('dumpxml','--inactive',n))
        for k,element in s['before']['fields'].items():
            old=x.find(k)
            if old is not None:x.remove(old)
            if element:x.append(ET.fromstring(element))
        define(x)
    else:
        # One atomic Incus update. Empty values remove previously absent local overrides.
        args=[k+'='+(v or '') for k,v in s['before']['fields'].items()]
        inc('config','set',n,*args)
    file.unlink()
