import json
import re
import shutil
import subprocess
import tempfile
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from common import *
from guests import compute, define, inc, vir

def restic(*args, cwd=None, timeout=14400):
    base=ROOT/'backups'
    password=PRIVATE/'restic.key'
    with locked('repository'):
        if not password.exists():
            with tempfile.NamedTemporaryFile(mode='w', dir=PRIVATE, delete=False) as keyfile:
                keyfile.write(secrets.token_urlsafe(48) + '\n')
                keyfile.flush()
                os.fsync(keyfile.fileno())
            os.replace(keyfile.name, password)
        repo=str(base/'repository')
        argv=['restic','-r',repo,'--password-file',str(password)]
        if not (Path(repo)/'config').exists():run(*argv,'init',timeout=120)
    proc=subprocess.run([*argv,*map(str,args)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,cwd=cwd,timeout=timeout)
    if proc.returncode:raise ValueError(proc.stderr.strip()[-900:] or tr('Backup failed.'))
    return proc.stdout
def snapshots():
    return [dict(id=s['short_id'],time=s['time'],tags=s.get('tags',[])) for s in json.loads(restic('snapshots','--json',timeout=45)) if 'linuxsphere' in s.get('tags',[])]
def backup(a):
    compute();n=name(a['name']);kind=a['kind']
    with locked('guest-'+n,False), tempfile.TemporaryDirectory(dir=ROOT/'backups') as folder:
        d=Path(folder)
        if kind=='vm':
            if vir('domstate',n)!='shut off':raise ValueError(tr('Power off the VM before backing it up.'))
            x=ET.fromstring(vir('dumpxml','--inactive',n))
            if x.find('devices/hostdev') is not None or x.find('devices/tpm') is not None or x.find('os/nvram/source') is not None:
                raise ValueError(tr('Back up TPM, passthrough hardware or managed NVRAM separately.'))
            disks=x.findall('devices/disk[@device="disk"]')
            if not disks:raise ValueError(tr('No VM disk found.'))
            for i,dev in enumerate(disks):
                src=dev.find('source');p=Path((src.get('file') if src is not None else '') or '/')
                if not p.is_file() or p.parent.resolve()!=(DISKS/n).resolve():raise ValueError(tr('Backup supports local guest disks managed by LinuxSphere.'))
                fn=f'disk-{i}.qcow2';run('qemu-img','convert','-O','qcow2',p,d/fn,timeout=14400);src.set('file',fn);dev.find('driver').set('type','qcow2')
            nv=x.find('os/nvram')
            if nv is not None and nv.text:
                nvpath=Path(nv.text)
                if not nvpath.is_file():raise ValueError(tr('The UEFI variable store is missing.'))
                shutil.copyfile(nvpath,d/'nvram.fd');nv.text='nvram.fd'
            if vir('domstate',n)!='shut off':raise ValueError(tr('The VM started during backup. Retry with the VM powered off.'))
            (d/'domain.xml').write_bytes(ET.tostring(x))
        elif kind=='ct':
            if json.loads(inc('list',n,'--format=json'))[0]['status']!='Stopped':raise ValueError(tr('Stop the container first.'))
            inc('export',n,d/'container.tar.gz','--instance-only',timeout=14400)
        else:raise ValueError(tr('Unknown guest type.'))
        (d/'guest.json').write_text(json.dumps({'kind':kind,'name':n}))
        restic('backup','--tag','linuxsphere','--tag',kind,'--tag',n,'.',cwd=d)
    return {'ok':True}
def restore(a):
    compute();sid=str(a['id']);n=name(a['name'])
    if not re.fullmatch(r'[a-f0-9]{8,64}',sid):raise ValueError(tr('Invalid backup ID.'))
    with locked('guest-'+n,False), tempfile.TemporaryDirectory(dir=ROOT/'backups') as folder:
        d=Path(folder);restic('restore',sid,'--target',d)
        if not (d/'guest.json').is_file():raise ValueError(tr('This backup contains no LinuxSphere guest.'))
        spec=json.loads((d/'guest.json').read_text())
        if spec['kind']=='ct':
            inc('import',d/'container.tar.gz',n,timeout=14400)
            try:
                # An imported backup retains the original instance and NIC identities.
                # Assign fresh ones so the restored guest can run beside the source.
                cfg=json.loads(inc('query','/1.0/instances/'+n))['config']
                ident=str(uuid.uuid4())
                changes=['volatile.uuid='+ident, 'volatile.uuid.generation='+ident,
                         'volatile.cloud-init.instance-id='+ident]
                changes.extend(key+'=' for key in cfg if key.startswith('volatile.') and key.endswith('.hwaddr'))
                inc('config','set',n,*changes)
            except Exception:
                inc('delete',n)
                raise
        else:
            if n in vir('list','--all','--name').splitlines():raise ValueError(tr('The destination name is in use.'))
            dest=DISKS/n;dest.mkdir();dest.chmod(0o755)
            try:
                x=ET.parse(d/'domain.xml').getroot();x.find('name').text=n
                for key in ['uuid','genid']:
                    item=x.find(key)
                    if item is not None:x.remove(item)
                for interface in x.findall('devices/interface'):
                    mac=interface.find('mac')
                    if mac is not None:interface.remove(mac)
                for i,dev in enumerate(x.findall('devices/disk[@device="disk"]')):
                    fn=f'disk-{i}.qcow2';shutil.move(d/fn,dest/fn);dev.find('source').set('file',str(dest/fn))
                nv=x.find('os/nvram')
                if nv is not None and (d/'nvram.fd').exists():shutil.move(d/'nvram.fd',dest/'nvram.fd');nv.text=str(dest/'nvram.fd')
                for cd in x.findall('devices/disk[@device="cdrom"]'):
                    src=cd.find('source')
                    if src is not None and not Path(src.get('file','')).is_file():cd.remove(src)
                define(x)
            except Exception:shutil.rmtree(dest);raise
    return {'name':n}
