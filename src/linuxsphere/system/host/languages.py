"""Language packs, request-local translations and Debian system locale management."""
from contextlib import contextmanager
from contextvars import ContextVar
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

BUILTIN = Path(__file__).resolve().parent.parent / 'i18n'
CUSTOM = Path('/etc/linuxsphere/languages')
LOCALE_FILES = (Path('/etc/locale.conf'), Path('/etc/default/locale'))
selected = ContextVar('linuxsphere_language', default=None)
CODE = re.compile(r'[a-z]{2,3}(?:-[a-z0-9]{2,8}){0,2}')
FIELD = re.compile(r'\{([a-z][a-z0-9_]*)\}')
_cache = {}

def system_locale():
    for path in LOCALE_FILES:
        if path.is_file():
            match = re.search(r'^LANG=["\']?([^\s"\']+)', path.read_text(), re.M)
            if match:
                return match[1]
    return 'en_US.UTF-8'

def normalized(value):
    return str(value).split(',', 1)[0].split(';', 1)[0].split('.', 1)[0].split('@', 1)[0].replace('_','-').lower()

def language():
    return normalized(selected.get() or os.getenv('LINUXSPHERE_LANGUAGE') or os.getenv('LC_ALL') or
                      os.getenv('LC_MESSAGES') or os.getenv('LANG') or system_locale())

@contextmanager
def using(value):
    token = selected.set(normalized(value) if value else None)
    try:
        yield
    finally:
        selected.reset(token)

def localized_task(func):
    request_language = language()
    def wrapped(*args):
        with using(request_language):
            return func(*args)
    return wrapped

def pack(code, fallback=False):
    code = normalized(code)
    candidates = [code, code.split('-')[0], 'en'] if fallback else [code]
    for candidate in candidates:
        if not CODE.fullmatch(candidate):
            continue
        for directory in (CUSTOM, BUILTIN):
            path = directory / (candidate + '.json')
            try:
                stamp = path.stat().st_mtime_ns
            except FileNotFoundError:
                continue
            entry = _cache.get(path)
            if entry is None or entry[0] != stamp:
                entry = (stamp, json.loads(path.read_text()))
                _cache[path] = entry
            return entry[1]
    raise ValueError(tr('Language pack not found.'))

def tr(message, **values):
    code = language()
    translated = message if code in ('en','c','posix') else pack(code, fallback=True)['messages'].get(message, message)
    return FIELD.sub(lambda m: str(values.get(m[1], m[0])), translated)

def locales():
    supported = Path('/usr/share/i18n/SUPPORTED').read_text().splitlines()
    return sorted({row.split()[0] for row in supported if row and row.split()[-1]=='UTF-8'} | {'C.UTF-8'})

def status():
    names = {p.stem for directory in (BUILTIN, CUSTOM) for p in directory.glob('*.json')}
    choices = [{k:pack(code)[k] for k in ('code','name','locale')} for code in sorted(names) if CODE.fullmatch(code)]
    return {'system':system_locale(),'packs':choices,'locales':locales()}

def write_file(path, text, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', dir=path.parent, delete=False) as f:
        temporary = Path(f.name)
        try:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
            os.fchmod(f.fileno(),mode)
            os.replace(temporary,path)
        finally:
            temporary.unlink(missing_ok=True)

def template():
    return {'code':'xx','name':'Your language','locale':'en_US.UTF-8','messages':dict(pack('en')['messages'])}

def install(data):
    if not isinstance(data,dict) or not isinstance(data.get('code'),str) or not CODE.fullmatch(data['code']):
        raise ValueError(tr('Invalid language code.'))
    if not isinstance(data.get('name'),str) or not 1<=len(data['name'])<=70 or not data['name'].isprintable() or data.get('locale') not in locales():
        raise ValueError(tr('Invalid language pack.'))
    texts = data.get('messages')
    keys = set(json.loads((BUILTIN/'en.json').read_text())['messages'])
    if not isinstance(texts,dict) or set(texts)!=keys or any(
        not isinstance(v,str) or not v.strip() or len(v)>4000 or not v.isprintable() or
        set(FIELD.findall(k))!=set(FIELD.findall(v)) for k,v in texts.items()):
        raise ValueError(tr('The translation must contain every message and preserve its placeholders.'))
    clean = {k:data[k] for k in ('code','name','locale','messages')}
    write_file(CUSTOM/(data['code']+'.json'),json.dumps(clean,ensure_ascii=False,indent=2)+'\n')
    return {'code':data['code'],'name':data['name']}

def banner():
    with using(system_locale()):
        msg = tr('Sign in with the account created during installation.')
    write_file(Path('/etc/issue.d/60-linuxsphere.issue'), 'LinuxSphere VE 0.2   |   https://\\4:9090/linuxsphere\n'+msg+'\n')

def set_system(value):
    if value not in locales():
        raise ValueError(tr('Unsupported UTF-8 locale.'))
    with open('/run/lock/linuxsphere-locale','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if value != 'C.UTF-8':
            path=Path('/etc/locale.gen')
            text=path.read_text()
            line=value+' UTF-8'
            if line not in [r.strip() for r in text.splitlines()]:
                write_file(path,text.rstrip()+'\n'+line+'\n')
            result=subprocess.run(['locale-gen','--keep-existing'],capture_output=True,text=True,timeout=300)
            probe=subprocess.run(['locale','charmap'],env={**os.environ,'LC_ALL':value},
                                 capture_output=True,text=True,timeout=10)
            if result.returncode or probe.returncode or probe.stderr.strip() or probe.stdout.strip()!='UTF-8':
                raise ValueError(tr('Locale generation failed.'))
        subprocess.run(['update-locale','LANG='+value,'LANGUAGE','LC_MESSAGES','LC_ALL'],check=True,
                       capture_output=True,text=True,timeout=30)
        banner()
    return {'system':system_locale()}
