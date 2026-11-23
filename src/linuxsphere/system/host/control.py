import json
import socket
from concurrent.futures import ThreadPoolExecutor
from common import *
import backup
import cluster
import droid
import guests
import vault
import capsule

def local(op,a):
    actions={'status':lambda _:guests.status(),'create':guests.create,'action':guests.action,'upload':guests.upload,
             'backup':backup.backup,'restore':backup.restore,'backups':lambda _:backup.snapshots(),'task':cluster.task_cmd,
             'vault-identity':vault.identity,'vault-provision':vault.provision,'vault-copy':vault.copy,'capsule-import':capsule.import_vm,'droid':droid.talk,'capsules':lambda _:droid.library()}
    if op not in actions:raise ValueError(tr('Operation unavailable.'))
    result=actions[op](a)
    if op not in ('status','backups','capsules','upload','task'):audit(op,a.get('name',a.get('operation','')))
    return result

def control(op,a):
    if not isinstance(a,dict):raise ValueError(tr('Expected a JSON object.'))
    if op=='overview':
        nodes=[{'id':'local','address':''}]+cluster.peer_list()
        def get(p):
            try:return {**p,**cluster.call(p['id'],'status',{},18),'online':True}
            except Exception as e:return {**p,'online':False,'error':str(e)[:360]}
        with ThreadPoolExecutor(min(12,len(nodes))) as ex: return {'nodes':list(ex.map(localized_task(get),nodes)),'groups':cluster.group_list()}
    if op=='vault-sync':return vault.synchronize(a)
    if op=='invite':return cluster.invite()
    if op=='join':return cluster.add(a)
    if op=='remove':return cluster.remove(a)
    if op=='revoke-all':
        with locked('grants'):
            atomic(cluster.GRANTS,{});(PRIVATE/'invite.json').unlink(missing_ok=True)
        return {'ok':True}
    if op.startswith('fusion-') and ROLE.read_text().strip() not in ('manager','hybrid'):
        raise ValueError(tr('SphereFusion requires a manager or hybrid node.'))
    if op=='fusion-create':return cluster.fusion_save(a)
    if op=='fusion-key':return cluster.group_key(a)
    if op=='fusion-delete':return cluster.group_delete(a)
    if op=='fusion-run':return cluster.batch(a)
    if op=='node':
        operation=a['op'];target=a.get('node','local');args=a.get('args',{})
        return cluster.call(target,operation,args,14400 if operation in ('backup','restore','droid') else 600)
    raise ValueError(tr('Unknown management command.'))
