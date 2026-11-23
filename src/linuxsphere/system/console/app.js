'use strict';
const tx=SphereI18n.t;
const $=id=>document.getElementById(id);
const make=(tag,txt,cls)=>{const e=document.createElement(tag);if(txt!==undefined)e.textContent=txt;if(cls)e.className=cls;return e;};
const button=(txt,fn,cls)=>{const e=make('button',txt,cls);e.type='button';e.onclick=()=>Promise.resolve().then(fn).catch(err=>notice(err));return e;};
const roles={hybrid:'Hybrid',manager:'Manager',worker:'Worker',storage:'Storage'};
const pages=['Overview','Guests','Nodes','Backups','SphereLink','SphereFusion','CLI','Language'];
const stateName={'running':'Running','shut off':'Off','stopped':'Off','paused':'Paused','in shutdown':'Shutting down'};
const fmt=n=>new Intl.NumberFormat(SphereI18n.region(),{maximumFractionDigits:1}).format(n);
const bytes=n=>n>=2**40?fmt(n/2**40)+' TiB':n>=2**30?fmt(n/2**30)+' GiB':fmt(n/2**20)+' MiB';
let state={nodes:[],groups:[]},page='Overview',target='local',busy=false,updated=false,dialogBusy=false,dialogAction=null,history=[],records=[],caps=[],phoneMachines=[],phoneCredentials={},capsNode='',recordsNode='';
const getNode=()=>state.nodes.find(n=>n.id===target)||state.nodes[0];
const available=()=>state.nodes.filter(n=>n.online);
const compute=()=>available().filter(n=>['hybrid','worker'].includes(n.role));
const nodeOperation=(op,args={},id=target)=>rpc('node',{node:id,op,args});
function rpc(op,args={}){
 const p=cockpit.spawn(['/usr/local/bin/dsctl','rpc',op],{superuser:'require',err:'message',environ:['LINUXSPHERE_LANGUAGE='+SphereI18n.code()]});
 p.input(JSON.stringify(args));return Promise.resolve(p).then(v=>JSON.parse(v));
}
function notice(s){const e=$('notice');e.hidden=!s;e.textContent=s?(s.message||String(s)):'';}
function tools(...nodes){$('tools').replaceChildren(...nodes.filter(Boolean));}
function options(items){return items.map(x=>Array.isArray(x)?x:[String(x),String(x)]);}
function select(items,value,fn){const e=make('select');for(const [v,t] of options(items)){const o=make('option',t);o.value=v;e.append(o);}e.value=value;e.onchange=()=>fn&&fn(e.value);return e;}
function field(label,type='text',value='',items=[]){const box=make('label',undefined,'field');box.append(make('span',label));const c=type==='select'?select(items,value):make(type==='textarea'?'textarea':'input');if(type!=='select'){if(type!=='textarea')c.type=type;c.value=value;}c.setAttribute('aria-label',label);box.append(c);return {box,c};}
const ptext=t=>make('p',t);
function modal(title,elements,label,action){
 if($('dialog').open)$('dialog').close();
 $('dtitle').textContent=title;$('fields').replaceChildren(...elements.map(e=>e.box||e));$('error').hidden=true;
 $('submit').hidden=!action;$('submit').textContent=label||tx('Apply');$('submit').disabled=false;dialogAction=action;dialogBusy=false;
 $('cancel').disabled=false;$('close').disabled=false;$('dialog').showModal();
}
function output(title,value){const p=make('pre',typeof value==='string'?value:JSON.stringify(value,null,2));modal(title,[p],'',null);}
function close(){if(!dialogBusy)$('dialog').close();}
$('close').onclick=close;$('cancel').onclick=close;
$('dialog').addEventListener('cancel',e=>{if(dialogBusy)e.preventDefault();});
$('form').onsubmit=async e=>{e.preventDefault();if(!dialogAction||dialogBusy)return;dialogBusy=true;const f=dialogAction;
 for(const id of ['submit','cancel','close'])$(id).disabled=true;$('error').hidden=true;
 try{const result=await f();if(result)output(result.title,result.value);else $('dialog').close();await refresh();}
 catch(err){$('error').textContent=err.message||String(err);$('error').hidden=false;}
 finally{dialogBusy=false;for(const id of ['submit','cancel','close'])$(id).disabled=false;}
};
function panel(title,aside){const e=make('section',undefined,'panel'),head=make('div',undefined,'panelhead');head.append(make('h2',title));if(aside)head.append(aside);e.append(head);return e;}
function table(columns,rows,empty){if(!rows.length)return make('p',empty,'empty');const wrap=make('div',undefined,'tablewrap'),t=make('table'),head=make('thead'),hr=make('tr');columns.forEach(c=>hr.append(make('th',c)));head.append(hr);t.append(head);const b=make('tbody');for(const row of rows){const tr=make('tr');row.forEach(x=>{const td=make('td');if(x instanceof Node)td.append(x);else td.textContent=x;tr.append(td);});b.append(tr);}t.append(b);wrap.append(t);return wrap;}
function label(a,b){const t=make('div',undefined,'labelrow');t.append(make('strong',a));if(b)t.append(make('span',b,'small'));return t;}
function tag(t,on){return make('span',t,'tag'+(on?' live':''));}
function buttons(...els){const a=make('div',undefined,'actions');a.append(...els.filter(Boolean));return a;}
function nodeSelect(items=available()){const n=select(items.map(s=>[s.id,s.host||s.id]),target,async id=>{target=id;phoneMachines=[];phoneCredentials={};await loadExtra();render();});n.setAttribute('aria-label',tx('Target node'));return n;}
function nav(){const box=$('nav');box.replaceChildren(...pages.map(t=>{const b=button(tx(t),()=>go(t));b.setAttribute('aria-current',t===page?'page':'false');return b;}));}
async function go(t){if(!pages.includes(t))return;page=t;notice('');nav();render();await loadExtra();render();}
async function loadExtra(){const id=target;if(!getNode()?.online)return;
 if(page==='Backups'){const result=await nodeOperation('backups',{},id);if(id===target){records=result;recordsNode=id;}}
 if(page==='SphereLink'){const result=await nodeOperation('capsules',{},id);if(id===target){caps=result;capsNode=id;}}}
async function refresh(){if(busy)return;busy=true;try{state=await rpc('overview');if(!state.nodes.some(n=>n.id===target))target='local';
 const nodes=available(),k=nodes.reduce((s,n)=>s+n.cores,0);if(k)history.push(nodes.reduce((s,n)=>s+n.cpu*n.cores,0)/k);if(history.length>45)history.shift();
 $('connection').textContent=tx('Live')+' · '+new Date().toLocaleTimeString(SphereI18n.region());$('connection').className='connection online';updated=true;notice('');await loadExtra();render();}
 catch(e){$('connection').textContent=tx('Check connection');$('connection').className='connection';if(page!=='CLI'&&page!=='Language')notice((e.message||String(e))+' · '+tx('Enable administrative access in the Cockpit header.'));}
 finally{busy=false;}}
function guestConsole(n){if(n.id==='local')return button(tx('VM console'),()=>cockpit.jump('/machines'));
 const a=make('a',tx('VM console'),'button');const u=new URL('https://'+n.address);u.port='9090';u.pathname='/machines';a.href=u.href;a.target='_blank';a.rel='noopener';return a;}
function nodeRows(){return state.nodes.map(n=>[label(n.host||n.id,n.id==='local'?tx('This server'):n.address),tx(roles[n.role]||'–'),tag(n.online?tx('Online'):tx('Offline'),n.online),n.online?fmt(n.cpu)+' %':'–',n.online?fmt(n.free/1024)+' GiB':'–',n.online?(n.kvm?'KVM':['worker','hybrid'].includes(n.role)?'QEMU · TCG':'–'):'–']);}
function guestRows(only=null,manage=false){return available().filter(n=>!only||n.id===only).flatMap(n=>n.guests.map(g=>{
 const running=g.state==='running',base=[label(g.name,g.kind==='vm'?tx('Virtual machine'):tx('Linux container')),n.host,tag(tx(stateName[g.state]||g.state),running),String(g.cpu),typeof g.ram==='number'?fmt(g.ram)+' MiB':String(g.ram)];
 if(manage)base.push(buttons(button(running?tx('Shut down'):tx('Start'),()=>power(n,g,running)),button(tx('Resources'),()=>resources(n,g)),g.undo?button(tx('Undo'),()=>modal(tx('SafeChange · Restore resources'),[ptext(tx('Restore the previous CPU and RAM allocation for {guest}.',{guest:g.name}))],tx('Reset'),()=>nodeOperation('action',{name:g.name,kind:g.kind,action:'undo-resources'},n.id).then(()=>null))):null,g.kind==='vm'?guestConsole(n):null));return base;}));}
function svgPlot(){const ns='http://www.w3.org/2000/svg',s=document.createElementNS(ns,'svg');s.setAttribute('viewBox','0 0 600 55');s.setAttribute('preserveAspectRatio','none');s.setAttribute('class','plot');s.setAttribute('aria-label',tx('CPU usage since opening this page'));s.setAttribute('role','img');
 for(const y of [5,27,50]){const l=document.createElementNS(ns,'path');l.setAttribute('d','M0 '+y+' H600');l.setAttribute('stroke','#314653');s.append(l);}
 const d=history.map((v,i)=>[600-(history.length-1-i)*600/44,51-Math.min(100,v)*.46]);if(d.length===1)d.unshift([595,d[0][1]]);
 const line=document.createElementNS(ns,'polyline');line.setAttribute('points',d.map(x=>x.join(',')).join(' '));line.setAttribute('fill','none');line.setAttribute('stroke','#92efd0');line.setAttribute('stroke-width','2.5');s.append(line);return s;}
function dashboard(v){const ns=available();const sum=k=>ns.reduce((a,n)=>a+n[k],0);const all=guestRows(),active=ns.flatMap(n=>n.guests).filter(g=>g.state==='running').length;
 const cards=make('div',undefined,'metrics');const data=[['CPU',sum('cores')?fmt(history.at(-1))+' %':'–',tx('{count} logical CPUs',{count:fmt(sum('cores'))})],[tx('Memory'),bytes((sum('ram')-sum('free'))*2**20),tx('{value} total',{value:bytes(sum('ram')*2**20)})],[tx('Storage used'),bytes(sum('storage')-sum('available')),tx('{value} free',{value:bytes(sum('available'))})],[tx('Active guests'),String(active),tx('{count} configured',{count:fmt(all.length)})]];
 for(const [t,val,s] of data){const c=make('div',undefined,'card');c.append(make('span',t,'type'),make('strong',val,'value'),make('span',s,'meta'));cards.append(c);}v.append(cards);
 const p=panel(tx('CPU history'),make('span',tx('Sampled every 8 seconds'),'small'));const a=make('div',undefined,'content');a.append(svgPlot());p.append(a);v.append(p);
 const n=panel(tx('Nodes'),button(tx('All nodes'),()=>go('Nodes')));n.append(table([tx('Host'),tx('Role'),tx('Connection'),'CPU',tx('Free RAM'),tx('VM acceleration')],nodeRows(),tx('No nodes yet.')));v.append(n);
 const g=panel(tx('Virtual machines and containers'),button(tx('Manage guests'),()=>go('Guests')));g.append(table([tx('Guest'),tx('Nodes'),tx('State'),'vCPU','RAM'],all,tx('Create a VM or container under Guests to get started.')));v.append(g);}
function power(n,g,running){modal(running?tx('Shut down guest'):tx('Start guest'),[ptext(tx('{guest} on {node}',{guest:g.name,node:n.host}))],running?tx('Shut down'):tx('Start'),()=>nodeOperation('action',{kind:g.kind,name:g.name,action:running?'stop':'start'},n.id).then(()=>null));}
function resources(n,g){const c=field('vCPU','number',Number(g.cpu)||1),m=field('RAM (MiB)','number',parseInt(g.ram)||256);
 modal(tx('Edit resources'),[ptext(g.name+' · '+n.host+(g.kind==='vm'?' · '+tx('Power off the VM first.'):'')),c,m],tx('Save allocation'),()=>nodeOperation('action',{name:g.name,kind:g.kind,action:'resources',cpu:c.c.value,ram:m.c.value},n.id).then(()=>null));}
function createGuest(){const ns=compute();if(!ns.length)throw Error(tx('Connect a worker or hybrid node.'));
 const first=ns.find(n=>n.id===target)||ns[0];const node=field(tx('Target node'),'select',first.id,ns.map(n=>[n.id,n.host])),kind=field(tx('Guest type'),'select','vm',[['vm',tx('Virtual machine')],['ct',tx('Linux container')]]),n=field(tx('Name'),'text',''),c=field('vCPU','number','1'),m=field('RAM (MiB)','number','512'),disk=field(tx('System disk (GiB)'),'number','8'),iso=field(tx('Installation media'),'select','',[['',tx('No media')]]),firm=field(tx('Firmware'),'select','bios',[['bios','BIOS'],['efi','UEFI']]),img=field(tx('Incus image'),'text','sphere-mini');
 function set(){const selected=ns.find(x=>x.id===node.c.value),ct=kind.c.value==='ct';iso.c.replaceChildren(...select([['',tx('No media')],...selected.media], '').children);for(const f of [disk,iso,firm])f.box.hidden=ct;img.box.hidden=!ct;}
 kind.c.onchange=set;node.c.onchange=set;set();modal(tx('Create guest'),[node,kind,n,c,m,disk,iso,firm,img],tx('Create'),async()=>{await nodeOperation('create',{kind:kind.c.value,name:n.c.value,cpu:c.c.value,ram:m.c.value,disk:disk.c.value,media:iso.c.value,uefi:firm.c.value==='efi',image:img.c.value},node.c.value);target=node.c.value;});}
function upload(){const ns=compute();if(!ns.length)throw Error(tx('No compute node is available.'));const first=ns.find(n=>n.id===target)||ns[0],id=field(tx('Target node'),'select',first.id,ns.map(n=>[n.id,n.host])),f=field(tx('ISO file'),'file'),bar=make('progress');bar.max=100;bar.value=0;f.c.accept='.iso';const msg=ptext(tx('Select the same file to resume an interrupted upload.'));
 modal(tx('Upload installation media'),[id,f,bar,msg],tx('Upload'),async()=>{const file=f.c.files[0];if(!file)throw Error(tx('Select an ISO file.'));const a={file:file.name,size:file.size,stamp:file.lastModified};let {offset}=await nodeOperation('upload',{...a,probe:true},id.c.value);
 while(offset<file.size){const ar=new Uint8Array(await file.slice(offset,offset+524288).arrayBuffer());let text='';for(let i=0;i<ar.length;i+=8192)text+=String.fromCharCode(...ar.slice(i,i+8192));const r=await nodeOperation('upload',{...a,offset,data:btoa(text)},id.c.value);offset=r.offset;bar.value=100*offset/file.size;msg.textContent=fmt(bar.value)+' % · '+tx('{done} of {total}',{done:bytes(offset),total:bytes(file.size)});}
 });}
function showNodes(v){const panel1=panel(tx('Cluster'));panel1.append(table([tx('Host'),tx('Role'),tx('Connection'),'CPU',tx('Free RAM'),tx('VM acceleration')],nodeRows(),tx('No nodes.')));v.append(panel1);
 for(const n of state.nodes){const p=panel(n.host||n.id);const c=make('div',undefined,'content');if(n.online){const d=make('dl',undefined,'detail');for(const [k,val] of [[tx('Model'),n.model],[tx('Kernel'),n.kernel],[tx('Uptime'),tx('{hours} hours',{hours:fmt(n.uptime/3600)})],...n.interfaces.map(i=>[i.name,i.ip.join(' · ')||i.state])])d.append(make('dt',k),make('dd',val));c.append(d);}else c.append(ptext(n.error));
 if(n.id!=='local')c.append(button(tx('Disconnect'),()=>modal(tx('Disconnect node'),[ptext(tx('Remove {node} from this cluster and revoke its authorization.',{node:n.id}))],tx('Disconnect now'),()=>rpc('remove',{alias:n.id}).then(()=>null))));p.append(c);v.append(p);}}
function join(){const alias=field(tx('Node alias in this cluster')),addr=field(tx('Node address')),code=field(tx('Invitation code'),'password');modal(tx('Connect node'),[ptext(tx('Create an invitation on the other LinuxSphere node. Its code includes the certificate fingerprint.')),alias,addr,code],tx('Connect'),()=>rpc('join',{alias:alias.c.value,address:addr.c.value,code:code.c.value}).then(()=>null));}
function invite(){return rpc('invite').then(r=>output(tx('Invitation · valid for 10 minutes'),r.code));}
function backups(v){const n=getNode();const p=panel(tx('Restore points'));p.append(table([tx('Time'),tx('Guest'),'ID',''],(recordsNode===target?records:[]).map(r=>[new Date(r.time).toLocaleString(SphereI18n.region()),r.tags.filter(x=>x!=='linuxsphere').join(' · '),make('code',r.id),button(tx('Restore'),()=>{const nn=field(tx('New guest name'));modal(tx('Restore as a new guest'),[ptext(tx('Backup {id} on {node}',{id:r.id,node:n.host})),nn],tx('Restore'),()=>nodeOperation('restore',{id:r.id,name:nn.c.value}).then(()=>null));})]),tx('This node has no guest backups yet.')));v.append(p);}
function newBackup(){const n=getNode();const gs=(n?.guests||[]).filter(g=>g.managed);if(!gs.length)throw Error(tx('Create a managed guest on this node first.'));const selected=field(tx('Powered-off guest'),'select','0',gs.map((g,i)=>[String(i),g.name+' · '+(tx(stateName[g.state]||g.state))]));
 modal(tx('Back up guest'),[selected,ptext(tx('Restic encrypts the restore point. Keep a separate copy of /var/lib/linuxsphere/private/restic.key to recover backups after losing the host.'))],tx('Back up'),()=>nodeOperation('backup',{name:gs[selected.c.value].name,kind:gs[selected.c.value].kind}).then(()=>null));}
function replica(){const ns=available();if(ns.length<2)throw Error(tx('Two online nodes are required.'));const ids=ns.map(n=>[n.id,n.host]),src=field(tx('Source node'),'select',target,ids),dst=field(tx('Storage target'),'select',ns.find(n=>n.id!==target).id,ids),addr=field(tx('Address of the local storage target')),dir=field(tx('Direction'),'select','send',[['send',tx('Copy backups to the storage target')],['receive',tx('Retrieve backups from the target')]]);function change(){addr.box.hidden=dst.c.value!=='local';}dst.c.onchange=change;change();
 modal(tx('Synchronize backups'),[src,dst,addr,dir],tx('Synchronize'),()=>rpc('vault-sync',{source:src.c.value,destination:dst.c.value,address:addr.c.value,direction:dir.c.value}).then(()=>null));}
function droidConnect(){const a=field(tx('Phone HTTPS address')),pin=field(tx('SHA-256 fingerprint')),code=field(tx('Pairing code'),'password');
 modal(tx('Connect DroidSphere'),[ptext(tx('Enable HTTPS access in DroidSphere to find the address, code and fingerprint.')),a,pin,code],tx('Connect'),async()=>{const info={address:a.c.value,pin:pin.c.value,code:code.c.value};const r=await nodeOperation('droid',{...info,operation:'list'});phoneCredentials=info;phoneMachines=r.machines;});}
function droidTransfer(op,item){const password=field(tx('Capsule password'),'password');password.c.autocomplete='off';
 modal(op==='pull'?tx('Back up from phone'):tx('Restore on phone'),[ptext(op==='pull'?item.name+' · '+tx('Shut down the VM in DroidSphere first.'):item.name+' · '+tx('DroidSphere restores the capsule as a new guest.')),password],op==='pull'?tx('Retrieve capsule'):tx('Restore'),()=>nodeOperation('droid',{...phoneCredentials,operation:op,id:item.id,file:item.name,password:password.c.value}).then(()=>null));}
function droidView(v){const p=panel(tx('Guests on phone'));p.append(table([tx('Guest'),tx('Architecture'),''],phoneMachines.map(m=>[label(m.name,m.id),m.arch||'–',button(tx('Back up'),()=>droidTransfer('pull',m))]),tx('Connect DroidSphere to list guests on the phone.')));v.append(p);
 const q=panel(tx('Encrypted capsules'));q.append(table([tx('File'),tx('Size'),''],(capsNode===target?caps:[]).map(c=>[c.name,bytes(c.size),buttons(phoneCredentials.code?button(tx('Send to phone'),()=>droidTransfer('push',c)):null,['hybrid','worker'].includes(getNode()?.role)?button(tx('Import as PC VM'),()=>capsuleImport(c)):null)]),tx('No DroidSphere capsules on this node yet.')));v.append(q);}
function fusionNew(){const all=compute().flatMap(n=>n.guests.map(g=>({node:n.id,host:n.host,...g})));const desks=all.filter(g=>g.kind==='vm'),workers=all.filter(g=>g.kind==='ct'&&g.managed);
 if(!desks.length||!workers.length)throw Error(tx('Create a desktop VM and at least one LinuxSphere worker container.'));
 const n=field(tx('Workspace name')),d=field(tx('Desktop VM'),'select','0',desks.map((g,i)=>[String(i),g.host+' / '+g.name])),sel=workers.map(w=>{const label=make('label');const c=make('input');c.type='checkbox';label.append(c,document.createTextNode(' '+w.host+' / '+w.name));return {box:label,c};});
 const ref=o=>({node:o.node,name:o.name});
 modal(tx('Set up workspace'),[n,d,make('h3',tx('Worker containers')),...sel],tx('Create workspace'),()=>rpc('fusion-create',{name:n.c.value,desktop:ref(desks[d.c.value]),workers:workers.filter((_,i)=>sel[i].c.checked).map(ref)}).then(()=>null));}
function fusion(v){const p=panel(tx('Distributed workspaces'));const b=make('div',undefined,'content');b.append(ptext(tx('The desktop VM runs on one host. Its worker containers execute independent jobs on their own nodes.')));p.append(b);
 p.append(table([tx('Workspace'),tx('Desktop VM'),tx('Worker'),''],state.groups.map(g=>[g.name,g.desktop.node+' / '+g.desktop.name,g.workers.map(w=>w.node+' / '+w.name).join(', '),buttons(button(tx('Jobs'),()=>fusionJobs(g)),button(tx('Guest access'),()=>guestKey(g)),button(tx('Dissolve'),()=>modal(tx('Dissolve workspace'),[ptext(tx('Dissolve {name} and revoke its guest key. Its guests will remain available.',{name:g.name}))],tx('Dissolve'),()=>rpc('fusion-delete',{name:g.name}).then(()=>null))))]),tx('No workspaces yet.')));v.append(p);}
function guestKey(g){const h=field(tx('Manager address reachable from the desktop (HTTPS)'), 'text','https://'+((state.nodes[0]?.ips||[])[0]||'manager')+':9443');modal(tx('Desktop VM access'),[h,ptext(tx('A new key replaces the previous key. Save the output as ~/.config/linuxsphere/fusion.json in the guest with permissions 0600. The sphere-run client is on the ISO under linuxsphere/system/host/.'))],tx('Generate key'),async()=>{const u=new URL(h.c.value);if(u.protocol!=='https:')throw Error(tx('Enter an HTTPS address.'));const k=await rpc('fusion-key',{name:g.name});return {title:tx('Guest configuration · confidential'),value:JSON.stringify({url:u.origin,group:k.group,pin:k.pin,key:k.key},null,2)};});}
function fusionJobs(g){const a=field(tx('Jobs as JSON'),'textarea','[\n  {"argv":["/bin/hostname"]},\n  {"argv":["/bin/uname","-m"]}\n]');modal(tx('Distribute jobs'),[ptext(tx('Start the worker containers first. Jobs run as an unprivileged user.')),a],tx('Run'),async()=>({title:tx('Job results'),value:(await rpc('fusion-run',{name:g.name,jobs:JSON.parse(a.c.value)})).results}));}
function render(){nav();$('heading').textContent=tx(page);$('context').textContent=state.nodes[0]?.host||'LinuxSphere VE';const v=$('view'); v.replaceChildren(); $('terminal-page').hidden=page!=='CLI'; $('language-page').hidden=page!=='Language';
 if(page==='CLI'){tools();SphereCLI.show(state);return;}
 if(page==='Language'){tools();SphereI18n.render($('language-page'));return;}
 if(!updated){tools(button(tx('Reload'),refresh));v.append(ptext(tx('Loading host data…')));return;}
 if(page==='Overview'){tools(button(tx('Create guest'),createGuest,'primary'));dashboard(v);}
 if(page==='Guests'){const n=getNode();tools(nodeSelect(),button(tx('Upload ISO'),upload),button(tx('Create guest'),createGuest,'primary'));const p=panel(tx('Guests on {node}',{node:n.host||n.id}));p.append(table([tx('Guest'),tx('Nodes'),tx('State'),'vCPU','RAM',tx('Actions')],guestRows(target,true),tx('There are no guests on this node.')));v.append(p);
 const med=panel(tx('Installation images'));med.append(table([tx('ISO file')],(n.media||[]).map(m=>[m]),tx('No ISO files uploaded yet.')));v.append(med);}
 if(page==='Nodes'){tools(button(tx('Create invitation'),invite),button(tx('Connect node'),join,'primary'));showNodes(v);}
 if(page==='Backups'){tools(nodeSelect(),button(tx('Synchronize'),replica),button(tx('Back up guest'),newBackup,'primary'));backups(v);}
 if(page==='SphereLink'){tools(nodeSelect(),button(tx('Connect DroidSphere'),droidConnect,'primary'));droidView(v);}
 if(page==='SphereFusion'){tools(button(tx('Create workspace'),fusionNew,'primary'));fusion(v);}
 for(const n of available()){for(const msg of n.warnings||[])v.append(make('p',n.host+' · '+msg,'warn'));}
}
async function startConsole(){
 await SphereI18n.init();
 for(const e of document.querySelectorAll('[data-t]'))e.textContent=tx(e.dataset.t);
 for(const e of document.querySelectorAll('[data-t-label]'))e.setAttribute('aria-label',tx(e.dataset.tLabel));
 if(location.hash.toLowerCase().includes('cli'))page='CLI';
 window.addEventListener('hashchange',()=>{if(location.hash.toLowerCase().includes('cli'))go('CLI');});
 nav();render();refresh();
}
startConsole().catch(notice);setInterval(()=>{if(!document.hidden&&!$('dialog').open)refresh();},8000);

function capsuleImport(item){const n=field(tx('New VM name')),c=field('vCPU','number','1'),m=field('RAM (MiB)','number','512'),pwd=field(tx('Capsule password'),'password');
 modal(tx('Import PC capsule as a VM'),[ptext(item.name+' · '+tx('For x86 BIOS or UEFI PC profiles. UEFI uses a fresh variable store. The imported VM starts powered off.')),n,c,m,pwd],tx('Import'),()=>nodeOperation('capsule-import',{name:n.c.value,file:item.name,cpu:c.c.value,ram:m.c.value,password:pwd.c.value}).then(()=>null));}
