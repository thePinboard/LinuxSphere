"""Replication between one compute host and a paired LinuxSphere storage host."""
import hashlib
import os
import re
import pwd
from urllib.parse import urlsplit
from common import *
import backup

def identity(_):
    key=PRIVATE/'vault_ed25519'
    with locked('vault-key'):
        if not key.exists():run('ssh-keygen','-q','-t','ed25519','-N','','-f',key)
    return {'public':key.with_suffix('.pub').read_text().strip().split(' ',2)[:2]}
def provision(a):
    if ROLE.read_text().strip() not in ('storage','hybrid'):raise ValueError(tr('Choose a storage or hybrid node as the backup target.'))
    pub=a['public']
    if not isinstance(pub,list) or len(pub)!=2 or pub[0]!='ssh-ed25519' or not re.fullmatch('[A-Za-z0-9+/]{60,80}={0,2}',pub[1]):raise ValueError(tr('Invalid backup key.'))
    acc='lsv-'+digest(pub[1])[:16];home=ROOT/'vault'/acc
    with locked('vault-provision'):
        home.mkdir(mode=0o755,parents=True,exist_ok=True);home.parent.chmod(0o755);home.chmod(0o755)
        try:u=pwd.getpwnam(acc)
        except KeyError:
            run('useradd','-M','-d',home,'-g','linuxsphere-vault','-s','/usr/sbin/nologin','-p','*',acc);u=pwd.getpwnam(acc)
        if Path(u.pw_dir)!=home:raise ValueError(tr('Storage account name conflict.'))
        data=home/'data';data.mkdir(exist_ok=True);os.chown(data,u.pw_uid,u.pw_gid)
        ssh=home/'.ssh';ssh.mkdir(mode=0o755,exist_ok=True);ssh.chmod(0o755)
        auth=ssh/'authorized_keys';auth.write_text('restrict '+' '.join(pub)+'\n');auth.chmod(0o644)
    return {'user':acc,'hostkey':Path('/etc/ssh/ssh_host_ed25519_key.pub').read_text().strip().split(' ',2)[:2]}
def copy(a):
    import tempfile
    host=urlsplit('https://'+address(a['target'])).hostname
    account=a['user'];key=a['hostkey']
    if not re.fullmatch(r'lsv-[0-9a-f]{16}',account) or not isinstance(key,list) or len(key)!=2 or key[0]!='ssh-ed25519' or not re.fullmatch('[A-Za-z0-9+/]{60,80}={0,2}',key[1]):raise ValueError(tr('Invalid storage target.'))
    remote='sftp:ls-vault:/data/repository'
    with locked('vault-transfer',False),tempfile.TemporaryDirectory(dir=PRIVATE) as tmp:
        folder=Path(tmp);kh=folder/'known_hosts';kh.write_text('ls-vault '+' '.join(key)+'\n')
        cfg=folder/'ssh_config';cfg.write_text(f'Host ls-vault\n HostName {host}\n HostKeyAlias ls-vault\n User {account}\n IdentityFile {PRIVATE}/vault_ed25519\n IdentitiesOnly yes\n BatchMode yes\n StrictHostKeyChecking yes\n UserKnownHostsFile {kh}\n ConnectTimeout 12\n')
        opt=['-o',f'sftp.command=ssh -F {cfg} -s ls-vault sftp']
        backup.restic('snapshots','--json')
        password=PRIVATE/'restic.key';local=ROOT/'backups/repository'
        # Initialize only if the pinned SFTP peer explicitly reports an absent config.
        args=['restic',*opt,'-r',remote,'--password-file',password]
        try:run(*args,'cat','config',timeout=50)
        except ValueError as e:
            msg=str(e).lower()
            if not any(t in msg for t in ('does not exist','no such file','not exist','file does not exist','repository not found')):raise
            run(*args,'init',timeout=80)
        if a.get('direction')=='receive':
            run('restic',*opt,'-r',local,'--password-file',password,'copy','--from-repo',remote,'--from-password-file',password,timeout=14400)
        else:run(*args,'copy','--from-repo',local,'--from-password-file',password,timeout=14400)
    return {'ok':True}

def synchronize(a):
    from cluster import call,PEERS
    src=name(a['source']);dest=name(a['destination'])
    if src==dest:raise ValueError(tr('Choose two different nodes.'))
    host=jsonread(PEERS,{}).get(dest,{}).get('address')
    if dest=='local':
        host=a.get('address','')
        if not host:raise ValueError(tr('Enter the local storage address reachable from the source node.'))
    if not host:raise ValueError(tr('Storage target is not connected.'))
    identity_data=call(src,'vault-identity',{});target=call(dest,'vault-provision',identity_data)
    return call(src,'vault-copy',{'target':host,'direction':a.get('direction','send'),**target},14400)
