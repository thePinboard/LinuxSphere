#!/usr/bin/python3
"""Administer LinuxSphere from a command line or an authenticated Cockpit session."""
import argparse
import getpass
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,'/usr/lib/linuxsphere/host')
import languages
from languages import tr
from control import control

def require_admin():
    if os.geteuid()!=0:
        raise ValueError(tr('Run dsctl with sudo to administer this host.'))

def parser():
    p=argparse.ArgumentParser(description=tr('Manage local and connected LinuxSphere nodes.'))
    sub=p.add_subparsers(dest='cmd',required=True)
    for cmd,helptext in [('status','Show host resources and guests'),('nodes','Show the cluster overview'),
                         ('invite','Create a single-use invitation valid for ten minutes'),('revoke-all','Revoke all inbound manager grants'),
                         ('rpc','Read JSON arguments from standard input')]:
        s=sub.add_parser(cmd,help=tr(helptext))
        if cmd=='rpc':s.add_argument('operation')
    s=sub.add_parser('join',help=tr('Connect a node using its invitation'))
    s.add_argument('alias');s.add_argument('address')
    s=sub.add_parser('run',help=tr('Submit jobs to a SphereFusion group'))
    s.add_argument('group');s.add_argument('file')
    lang=sub.add_parser('language',help=tr('Language settings and translation packs'))
    choices=lang.add_subparsers(dest='action',required=True)
    for cmd,helptext,arg in [('list','Show supported locales and installed language packs',None),
                            ('catalog','Print a language pack','code'),('set','Set the default locale for new logins','locale'),
                            ('template','Export the complete translation template',None),('install','Install a translated JSON language pack','file')]:
        s=choices.add_parser(cmd,help=tr(helptext))
        if arg:s.add_argument(arg)
    return p

def execute(a):
    if a.cmd=='language':
        if a.action=='list':return languages.status()
        if a.action=='catalog':return languages.pack(a.code)
        if a.action=='template':return languages.template()
        require_admin()
        if a.action=='set':return languages.set_system(a.locale)
        path=Path(a.file)
        if path.stat().st_size>2**20:raise ValueError(tr('Invalid language pack.'))
        return languages.install(json.loads(path.read_text()))
    require_admin()
    if a.cmd=='status':return control('node',{'op':'status'})
    if a.cmd=='nodes':return control('overview',{})
    if a.cmd in ('invite','revoke-all'):return control(a.cmd,{})
    if a.cmd=='join':return control('join',{'alias':a.alias,'address':a.address,'code':getpass.getpass(tr('Invitation code: '))})
    if a.cmd=='run':return control('fusion-run',{'name':a.group,'jobs':json.loads(Path(a.file).read_text())})
    return control(a.operation,json.load(sys.stdin))

if __name__=='__main__':
    try:
        args=parser().parse_args()
        print(json.dumps(execute(args),ensure_ascii=False,indent=None if args.cmd=='rpc' else 2))
    except (Exception,KeyboardInterrupt) as e:
        print(str(e) or tr('Cancelled.'),file=sys.stderr)
        sys.exit(1)
