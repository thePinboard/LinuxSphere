import base64
import hashlib
import json
import os
import platform
import re
import shutil
import socket
import tempfile
import time
import uuid
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from common import *

def vir(*args,**kwargs): return run('virsh','-c','qemu:///system',*args,**kwargs)
def inc(*args,**kwargs): return run('incus',*args,**kwargs)
def compute():
    if ROLE.read_text().strip() not in ('worker','hybrid'): raise ValueError(tr('This requires a worker or hybrid node.'))
def mem():
    data=dict((l.split(':')[0],int(l.split()[1])//1024) for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith(('MemTotal:','MemAvailable:')))
    return data['MemTotal'],data['MemAvailable']
def cpu():
    def read():
        values=list(map(int,Path('/proc/stat').read_text().splitlines()[0].split()[1:9]))
        return sum(values),values[3]+values[4]
    t,idle=read();time.sleep(.16);t2,idle2=read()
    return round(100*(1-(idle2-idle)/max(1,t2-t)),1)
def list_vm():
    names=[s for s in vir('list','--all','--name',timeout=8).splitlines() if s]
    rows=[]
    for n in names:
        x=ET.fromstring(vir('dumpxml',n));state=vir('domstate',n)
        rows.append(dict(kind='vm',name=n,state=state,cpu=int(x.findtext('vcpu','1')),ram=int(x.findtext('memory','0'))//1024,managed=(DISKS/n).is_dir()))
    return rows
def list_ct():
    items=json.loads(inc('list','--format=json',timeout=10))
    return [dict(kind='ct',name=i['name'],state=i['status'].lower(),cpu=i['expanded_config'].get('limits.cpu','–'),
                 ram=i['expanded_config'].get('limits.memory','–'),managed=i['config'].get('user.linuxsphere')=='true') for i in items if i['type']=='container']
def status():
    role=ROLE.read_text().strip();total,free=mem();storage=shutil.disk_usage(DISKS if DISKS.exists() else ROOT)
    warnings=[]; guests=[]
    if role in ('worker','hybrid'):
        with ThreadPoolExecutor(2) as ex:
            for f in [ex.submit(localized_task(list_vm)),ex.submit(localized_task(list_ct))]:
                try:guests.extend(f.result())
                except (OSError,ValueError) as e:warnings.append(str(e))
    for g in guests:g['undo']=(PRIVATE/('resources-'+g['kind']+'-'+g['name']+'.json')).exists()
    interfaces=json.loads(run('ip','-j','address','show',timeout=3))
    devs=[dict(name=i['ifname'],state=i.get('operstate',''),ip=[a['local'] for a in i.get('addr_info',[]) if a.get('scope')=='global']) for i in interfaces if i['ifname']!='lo']
    model=next((l.split(':',1)[1].strip() for l in Path('/proc/cpuinfo').read_text().splitlines() if l.startswith('model name')),platform.machine())
    return dict(host=socket.gethostname(),role=role,cpu=cpu(),cores=os.cpu_count(),model=model,ram=total,free=free,
                storage=storage.total,available=storage.free,uptime=int(float(Path('/proc/uptime').read_text().split()[0])),
                kernel=platform.release(),kvm=os.access('/dev/kvm',os.R_OK|os.W_OK),guests=guests,interfaces=devs,warnings=warnings,
                media=sorted(p.name for p in MEDIA.glob('*.iso') if p.is_file()),ips=run('hostname','-I').split())
def verify_limits(a):
    return number(a.get('cpu'),1,os.cpu_count() or 1,'vCPU'),number(a.get('ram'),32,max(32,mem()[0]-160),'RAM (MiB)')
def path_media(s):
    if not isinstance(s,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,106}\.iso',s):raise ValueError(tr('Choose a valid ISO filename.'))
    return MEDIA/s
def el(p,k,**attr): return ET.SubElement(p,k,{i:str(v) for i,v in attr.items()})
def define(xml):
    with tempfile.NamedTemporaryFile() as f:
        f.write(ET.tostring(xml));f.flush();return vir('define',f.name)
def vm_xml(n,c,m,volume,iso,uefi,machine='q35',media_first=True):
    x=ET.Element('domain',type='kvm' if os.access('/dev/kvm',os.R_OK|os.W_OK) else 'qemu')
    el(x,'name').text=n;el(x,'memory',unit='MiB').text=str(m);el(x,'vcpu').text=str(c)
    osel=el(x,'os');el(osel,'type',arch='x86_64',machine=machine).text='hvm'
    if uefi:osel.set('firmware','efi')
    feat=el(x,'features');el(feat,'acpi');el(feat,'apic')
    dev=el(x,'devices');disk=el(dev,'disk',type='file',device='disk')
    el(disk,'driver',name='qemu',type='qcow2');el(disk,'source',file=volume);el(disk,'target',dev='hda' if machine=='pc' else 'vda',bus='ide' if machine=='pc' else 'virtio');el(disk,'boot',order=2 if iso and media_first else 1)
    if iso:
        cd=el(dev,'disk',type='file',device='cdrom');el(cd,'driver',name='qemu',type='raw')
        el(cd,'source',file=iso);el(cd,'target',dev='hdc' if machine=='pc' else 'sda',bus='ide' if machine=='pc' else 'sata');el(cd,'readonly');el(cd,'boot',order=1 if media_first else 2)
    net=el(dev,'interface',type='network');el(net,'source',network='default');el(net,'model',type='virtio')
    el(dev,'graphics',type='vnc',port='-1',autoport='yes',listen='127.0.0.1')
    el(el(dev,'video'),'model',type='vga');el(el(dev,'serial',type='pty'),'target',port=0)
    el(el(dev,'console',type='pty'),'target',type='serial',port=0);el(dev,'input',type='tablet',bus='usb')
    return x
def create(a):
    compute(); n=name(a['name']); c,m=verify_limits(a);kind=a['kind']
    with locked('guest-'+n):
        if kind=='ct':
            image=a.get('image','sphere-mini')
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9./:_-]{0,100}',image):raise ValueError(tr('Invalid image.'))
            inc('init',image,n,'-c','limits.cpu='+str(c),'-c',f'limits.memory={m}MiB','-c','user.linuxsphere=true',timeout=600)
        elif kind=='vm':
            size=number(a.get('disk'),1,16384,tr('Disk (GiB)'));iso=path_media(a['media']) if a.get('media') else None
            if iso and not iso.is_file():raise ValueError(tr('Installation media is missing on this node.'))
            if n in vir('list','--all','--name').splitlines():raise ValueError(tr('This VM name is already taken.'))
            d=DISKS/n;d.mkdir();d.chmod(0o755)
            try:
                run('qemu-img','create','-f','qcow2',d/'system.qcow2',str(size)+'G')
                d.joinpath('system.qcow2').chmod(0o600)
                define(vm_xml(n,c,m,d/'system.qcow2',iso,a.get('uefi',False)))
            except Exception:
                shutil.rmtree(d);raise
        else:raise ValueError(tr('Choose a VM or container.'))
    return {'name':n}
def action(a):
    import safechange
    compute();n=name(a['name']);kind=a['kind'];act=a['action']
    with locked('guest-'+n):
        if act=='undo-resources':safechange.undo(kind,n)
        elif act=='resources':
            c,m=verify_limits(a);before=safechange.read(kind,n)
            if kind=='ct':inc('config','set',n,f'limits.cpu={c}',f'limits.memory={m}MiB')
            elif kind=='vm':
                if vir('domstate',n)!='shut off':raise ValueError(tr('Shut down the VM cleanly first.'))
                x=ET.fromstring(vir('dumpxml','--inactive',n));v=x.find('vcpu')
                if v is None or x.find('vcpus') is not None or x.find('cpu/topology') is not None or x.find('numatune') is not None:
                    raise ValueError(tr('Use advanced VM management to change this CPU topology.'))
                v.text=str(c);v.attrib.pop('current',None)
                for k in ['memory','currentMemory']:
                    e=x.find(k)
                    if e is not None:e.set('unit','MiB');e.text=str(m)
                define(x)
            else:raise ValueError(tr('Unknown guest type.'))
            safechange.record(kind,n,before)
        elif act in ('start','stop') and kind in ('vm','ct'):
            if kind=='vm':vir('start' if act=='start' else 'shutdown',n)
            else:inc('start' if act=='start' else 'stop',n,timeout=90)
        else:raise ValueError(tr('Unknown action.'))
    return {'ok':True}
def upload(a):
    compute();f=path_media(a['file'])
    total=number(a['size'],1,64*GIB,tr('ISO size'))
    ident=hashlib.sha256((f.name+'|'+str(total)+'|'+str(a.get('stamp',''))[:80]).encode()).hexdigest()
    tmp=MEDIA/('.'+ident+'.partial')
    with locked('media-'+digest(f.name)):
        if f.exists():raise ValueError(tr('A media file with this name already exists.'))
        offset=tmp.stat().st_size if tmp.exists() else 0
        if a.get('probe'):return {'offset':offset}
        if number(a['offset'],0,total,tr('Position'))!=offset:raise ValueError(tr('Upload position changed. Select the same file again to resume.'))
        part=base64.b64decode(a['data'],validate=True)
        if not 0<len(part)<=524288 or offset+len(part)>total:raise ValueError(tr('Invalid data block.'))
        if shutil.disk_usage(MEDIA).free<128*1024**2+len(part):raise ValueError(tr('128 MiB must remain available for the host.'))
        with tmp.open('ab') as out:out.write(part)
        offset+=len(part)
        if offset==total:
            with tmp.open('rb') as i:i.seek(32769);valid=i.read(5)==b'CD001'
            if not valid:tmp.unlink();raise ValueError(tr('The file does not contain an ISO 9660 filesystem.'))
            tmp.chmod(0o644);os.replace(tmp,f)
    return {'offset':offset}
