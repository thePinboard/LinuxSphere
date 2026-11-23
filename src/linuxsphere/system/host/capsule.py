"""Import a checked DroidSphere VE 2 PC capsule as an independent, stopped VM."""
import hashlib
import json
import re
import shutil
import struct
import tempfile
import zipfile
from pathlib import Path
from common import *
from guests import compute,define,el,verify_limits,vir,vm_xml

def decrypt(src,dest,password):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.exceptions import InvalidTag
    with src.open('rb') as f,dest.open('xb') as out:
        h=f.read(32)
        if len(h)!=32 or h[:8]!=b'DSVECAP\x02':raise ValueError(tr('Unknown capsule format.'))
        aes=AESGCM(hashlib.pbkdf2_hmac('sha256',password.encode(),h[8:24],310000,32));index=0;total=0
        while True:
            frame=f.read(4)
            if len(frame)!=4:raise ValueError(tr('Incomplete capsule.'))
            length=int.from_bytes(frame,'big');total+=length
            if length>262144 or total>100*GIB:raise ValueError(tr('Invalid capsule size.'))
            ct=f.read(length+16)
            if len(ct)!=length+16:raise ValueError(tr('Incomplete capsule.'))
            idx=index.to_bytes(4,'big')
            try:data=aes.decrypt(h[24:]+idx,ct,h+idx+frame)
            except InvalidTag as e:raise ValueError(tr('Incorrect capsule password or modified data.')) from e
            if not length:
                if f.read(1):raise ValueError(tr('Unexpected data after the capsule.'))
                return
            out.write(data);index+=1

def unpack(archive,folder):
    allowed={'vm.json','integrity.json','standalone.qcow2','install.iso','efi.fd','exchange.img','userdata.qcow2'}
    with zipfile.ZipFile(archive) as z:
        files=z.infolist();names={e.filename for e in files}
        if len(files)>32 or len(files)!=len(names) or not {'vm.json','integrity.json','standalone.qcow2'}<=names:raise ValueError(tr('Invalid backup contents.'))
        if any(n not in allowed and not re.fullmatch('data-[0-9a-f]{12}\\.qcow2',n) for n in names):raise ValueError(tr('Unknown backup entry.'))
        total=sum(e.file_size for e in files)
        if total>100*GIB or total+128*2**20>shutil.disk_usage(folder).free:raise ValueError(tr('Insufficient space for import.'))
        def metadata(n):
            if z.getinfo(n).file_size>65536:raise ValueError(tr('Metadata is too large.'))
            return json.loads(z.read(n))
        manifest=metadata('integrity.json');cfg=metadata('vm.json')
        if cfg.get('kind') not in ('pciso','pcdisk','efiiso','efidisk'):raise ValueError(tr('Host import supports x86 BIOS and UEFI DroidSphere PC profiles. Restore this capsule on DroidSphere.'))
        hashes=manifest.get('sha256',{})
        if manifest.get('version')!=2 or set(hashes)!=names-{'integrity.json'}:raise ValueError(tr('Invalid checksum manifest.'))
        for item in files:
            fn=item.filename
            if fn=='integrity.json':continue
            if item.file_size>64*GIB:raise ValueError(tr('Backup entry is too large.'))
            h=hashlib.sha256()
            with z.open(item) as inp,(folder/fn).open('xb') as out:
                while block:=inp.read(1048576):out.write(block);h.update(block)
            if h.hexdigest()!=hashes[fn]:raise ValueError(tr('Checksum mismatch for {file}.', file=fn))
    return cfg

def qcow(p):
    with p.open('rb') as f:h=f.read(104)
    if len(h)<72 or h[:4]!=b'QFI\xfb' or int.from_bytes(h[4:8],'big') not in (2,3) or any(h[8:20]) or (h[7]==3 and int.from_bytes(h[72:80],'big')&4):
        raise ValueError(tr('Import requires standalone QCOW2 disks.'))
    run('qemu-img','check','-f','qcow2',p,timeout=3600)

def import_vm(a):
    compute();n=name(a['name']);fn=str(a['file'])
    if not re.fullmatch(r'[A-Za-z0-9-]+\.dscap',fn):raise ValueError(tr('Invalid filename.'))
    src=ROOT/'droid'/fn
    if not src.is_file() or src.stat().st_size+128*2**20>shutil.disk_usage(DISKS).free:raise ValueError(tr('The capsule is missing or disk space is insufficient.'))
    c,m=verify_limits(a)
    with locked('guest-'+n,False),tempfile.TemporaryDirectory(dir=DISKS) as tmp:
        work=Path(tmp);archive=work/'payload.zip';decrypt(src,archive,a['password'])
        cfg=unpack(archive,work);archive.unlink()
        data=cfg.get('dataDisks',[])
        if not isinstance(data,list) or len(data)>8 or len(set(data))!=len(data) or any(not isinstance(f,str) or not re.fullmatch(r'data-[0-9a-f]{12}\.qcow2|userdata\.qcow2',f) for f in data):raise ValueError(tr('Invalid data disk list.'))
        for fn in ['standalone.qcow2',*data]:qcow(work/fn)
        if n in vir('list','--all','--name').splitlines():raise ValueError(tr('VM name is in use.'))
        dest=DISKS/n;dest.mkdir();dest.chmod(0o755)
        try:
            # Keep original ISO, exchange and detached volumes together with the converted VM.
            for f in work.iterdir():
                if f.name!='vm.json':f.rename(dest/('system.qcow2' if f.name=='standalone.qcow2' else f.name))
            iso=dest/'install.iso'
            x=vm_xml(n,c,m,dest/'system.qcow2',iso if iso.is_file() else None,cfg['kind'].startswith('efi'),'pc',bool(cfg.get('media')))
            devices=x.find('devices')
            for i,fn in enumerate(data):
                d=el(devices,'disk',type='file',device='disk');el(d,'driver',name='qemu',type='qcow2');el(d,'source',file=dest/fn);el(d,'target',dev='vd'+chr(ord('b')+i),bus='virtio')
            if (dest/'exchange.img').is_file():
                d=el(devices,'disk',type='file',device='disk');el(d,'driver',name='qemu',type='raw');el(d,'source',file=dest/'exchange.img');el(d,'target',dev='sda',bus='usb')
            define(x)
        except Exception:shutil.rmtree(dest);raise
    return {'name':n}
