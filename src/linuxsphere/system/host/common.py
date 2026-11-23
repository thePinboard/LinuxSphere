from languages import tr, language, localized_task
import contextlib
import fcntl
import hashlib
import http.client
import ipaddress
import json
import os
import re
import secrets
import ssl
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path('/var/lib/linuxsphere')
PRIVATE = ROOT / 'private'
MEDIA = Path('/var/lib/libvirt/boot/linuxsphere')
DISKS = Path('/var/lib/libvirt/images/linuxsphere')
ROLE = Path('/etc/linuxsphere/role')
GIB = 1 << 30

def run(*args, timeout=60, data=None, env=None):
    try:
        r = subprocess.run(list(map(str,args)), input=data, capture_output=True, text=True,
                           timeout=timeout, env={**os.environ, 'LC_ALL':'C', **(env or {})})
    except subprocess.TimeoutExpired as e:
        raise ValueError(tr('Operation timed out. Check its current state.')) from e
    if r.returncode:
        raise ValueError((r.stderr.strip() or r.stdout.strip() or tr('Operation failed.'))[-1800:])
    return r.stdout.strip()

def jsonread(path, default=None):
    try: return json.loads(path.read_text())
    except FileNotFoundError: return default

def atomic(path, obj):
    path.parent.mkdir(exist_ok=True,parents=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as f:
        json.dump(obj,f,ensure_ascii=False); f.flush(); os.fsync(f.fileno())
    os.replace(f.name,path)

@contextlib.contextmanager
def locked(key, blocking=True):
    with (PRIVATE / ('lock-'+key)).open('a') as f:
        try: fcntl.flock(f,fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        except BlockingIOError as e: raise ValueError(tr('An operation is already in progress.')) from e
        yield

def name(value):
    if not isinstance(value,str) or not re.fullmatch('[a-z][a-z0-9-]{0,39}',value):
        raise ValueError(tr('Start the name with a lowercase letter. Use up to 40 lowercase letters, digits or hyphens.'))
    return value

def number(value, bottom, top, label):
    if isinstance(value,bool) or not re.fullmatch(r'[0-9]{1,12}',str(value)) or not bottom<=int(value)<=top:
        raise ValueError(tr('{label} must be between {bottom} and {top}.', label=label, bottom=bottom, top=top))
    return int(value)

def digest(value): return hashlib.sha256(value.encode()).hexdigest()

def address(value, port=9443):
    raw=str(value).strip()
    if '://' not in raw: raw='https://'+raw
    u=urlsplit(raw)
    if u.scheme!='https' or u.username or u.password or u.query or u.fragment or u.path not in ('','/') or not u.hostname:
        raise ValueError(tr('Enter the HTTPS address of the node.'))
    host=u.hostname
    try: ipaddress.ip_address(host)
    except ValueError:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]{0,251}',host):
            raise ValueError(tr('Invalid host name.'))
    return ('['+host+']' if ':' in host else host)+':'+str(u.port or port)

def connection(addr,pin,timeout=20):
    pin=pin.replace(':','').replace(' ','').lower()
    if not re.fullmatch(r'[a-f0-9]{64}',pin): raise ValueError(tr('Enter a 64-digit hexadecimal SHA-256 fingerprint.'))
    u=urlsplit('https://'+addr)
    ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT);ctx.minimum_version=ssl.TLSVersion.TLSv1_2
    ctx.check_hostname=False;ctx.verify_mode=ssl.CERT_NONE
    c=http.client.HTTPSConnection(u.hostname,u.port,context=ctx,timeout=timeout)
    c.connect()
    actual=hashlib.sha256(c.sock.getpeercert(binary_form=True)).hexdigest()
    if not secrets.compare_digest(actual,pin):
        c.close();raise ValueError(tr('The certificate does not match the trusted fingerprint.'))
    return c

def audit(action, label=''):
    try: run('logger','-t','linuxsphere',action+' '+str(label)[:120],timeout=3)
    except (ValueError,OSError): pass
