'use strict';
const SphereCLI = (() => {
    let ui, data = {nodes:[]}, term, channel, fit, observer, opening = false, generation = 0;
    let nodeId = 'local', mode = 'host';
    const t = SphereI18n.t;
    const validGuest = s => typeof s==='string' && /^[A-Za-z0-9_][A-Za-z0-9_.-]{0,126}$/.test(s);
    const hint = {
        host:'The host shell uses your login account. Use sudo for system administration.',
        virsh:'Manage VM definitions and devices in the interactive libvirt shell. Type help for commands.',
        ct:'Opens /bin/sh inside the selected container through Incus.',
        vm:'The guest must have a serial console configured. Press Ctrl+] to disconnect. For a graphical guest, use VM console under Guests.'
    };
    function populate(selector, items) {
        const signature=JSON.stringify(items);
        if(selector.dataset.options===signature) return;
        const old=selector.value;
        selector.replaceChildren(...items.map(([v,label])=>new Option(label,v)));
        if(items.some(([v])=>v===old)) selector.value=old;
        selector.dataset.options=signature;
    }
    function updateControls() {
        const nodes = data.nodes.filter(n=>n.online || n.id==='local');
        if (!nodes.some(n=>n.id==='local')) nodes.unshift({id:'local',host:location.hostname});
        populate(ui.node.c,nodes.map(n=>[n.id,n.host||n.id]));
        nodeId=ui.node.c.value || 'local';
        const remote=nodeId!=='local', node=nodes.find(n=>n.id===nodeId);
        const modes=[['host',t('Host shell')]];
        if (!remote && ['hybrid','worker'].includes(node?.role)) modes.push(['virsh',t('VM management (virsh)')],['ct',t('Container shell')],['vm',t('VM serial console')]);
        populate(ui.mode.c,modes);mode=ui.mode.c.value;
        const needsGuest=mode==='ct'||mode==='vm';
        const guests=(node?.guests||[]).filter(g=>g.kind===mode && g.state==='running' && validGuest(g.name));
        populate(ui.guest.c,guests.map(g=>[g.name,g.name]));
        ui.mode.box.hidden=remote;ui.guest.box.hidden=remote||!needsGuest;
        ui.help.textContent=remote?t('Sign in on the selected node to open its terminal.'):needsGuest&&!guests.length
            ?t(mode==='vm'?'No running VMs on this host.':'No running containers on this host.'):t(hint[mode]);
        const active=Boolean(channel)||opening;
        ui.node.c.disabled=ui.mode.c.disabled=ui.guest.c.disabled=active;
        ui.start.hidden=active;ui.stop.hidden=!active;
        ui.start.disabled=!remote && needsGuest && !guests.length;
        ui.start.textContent=t(remote?'Open node CLI':'Open terminal');
        ui.keys.hidden=!channel;
    }
    function dispose() {
        ++generation;
        const live=channel;channel=null;opening=false;
        if(live?.valid) live.close();
        observer?.disconnect();observer=null;
        term?.dispose();term=null;fit=null;
        ui.screen.replaceChildren();ui.screen.hidden=true;
        updateControls();
    }
    function confirmEnd() {
        modal(t('End session'),[ptext(t('Disconnect this terminal session?'))],t('End session'),async()=>{
            dispose();ui.status.textContent=t('Session ended.');
        });
    }
    function openPeer() {
        const peer=data.nodes.find(n=>n.id===nodeId);
        if(!peer?.address) return;
        const url=new URL('https://'+peer.address);
        url.port='9090';url.pathname='/linuxsphere';url.hash='cli';
        window.open(url.toString(),'_blank','noopener');
    }
    async function start() {
        if(nodeId!=='local') {openPeer();return;}
        if(channel||opening) return;
        const guest=ui.guest.c.value;
        if ((mode==='ct'||mode==='vm') && !validGuest(guest)) throw Error(t('Select a running guest.'));
        const version=++generation;
        opening=true;ui.status.textContent='';updateControls();
        try {
            const [user,locale]=await Promise.all([cockpit.user(),SphereI18n.hostLocale()]);
            if(version!==generation) return;
            const virsh=['/usr/bin/sudo','--','/usr/bin/virsh','--connect','qemu:///system'];
            const commands={
                host:[user.shell||'/bin/bash','-l'],
                virsh,
                ct:['/usr/bin/sudo','--','/usr/bin/incus','exec',guest,'--mode=interactive','--','/bin/sh'],
                vm:[...virsh,'console','--domain',guest]
            };
            term?.dispose();observer?.disconnect();ui.screen.replaceChildren();ui.screen.hidden=false;
            term=new Terminal({cursorBlink:true,scrollback:3500,fontSize:14,fontFamily:'"DejaVu Sans Mono", monospace',
                theme:{background:'#0b141d',foreground:'#e5eef4',cursor:'#92efd0',selectionBackground:'#304958'}});
            fit=new FitAddon.FitAddon();term.loadAddon(fit);term.open(ui.screen);fit.fit();
            channel=cockpit.channel({payload:'stream',spawn:commands[mode],pty:true,binary:true,
                directory:user.home||'/',environ:['TERM=xterm-256color','LANG='+locale,'LC_MESSAGES='+locale,'LANGUAGE='],
                window:{rows:term.rows,cols:term.cols}});
            const c=channel;
            c.addEventListener('message',(_,bytes)=>{if(version===generation)term.write(bytes);});
            c.addEventListener('close',(_,options)=>{
                if(version!==generation)return;
                channel=null;opening=false;
                ui.status.textContent=options?.message||options?.problem||t('Session ended.');
                updateControls();
            });
            const encoder=new TextEncoder();
            term.onData(value=>{if(c.valid)c.send(encoder.encode(value));});
            term.onBinary(value=>{if(c.valid)c.send(Uint8Array.from(value,v=>v.charCodeAt(0)));});
            term.onResize(({rows,cols})=>{if(c.valid)c.control({window:{rows,cols}});});
            observer=new ResizeObserver(()=>{if(!ui.screen.closest('[hidden]')&&fit)fit.fit();});
            observer.observe(ui.screen);term.focus();
        } catch (error) {
            if(version===generation)dispose();
            throw error;
        } finally {
            if(version===generation){opening=false;updateControls();}
        }
    }
    function mount() {
        const root=document.getElementById('terminal-page');
        const box=panel(t('Session')),body=make('div',undefined,'content');
        const node=field(t('Target node'),'select','',[]),type=field(t('Select session type'),'select','',[]),guest=field(t('Guest name'),'select','',[]);
        const selectors=make('div',undefined,'terminal-selectors');selectors.append(node.box,type.box,guest.box);
        const help=ptext(''),status=make('p',undefined,'small');status.setAttribute('role','status');
        const screen=make('div',undefined,'terminal-screen');screen.id='cli-screen';screen.hidden=true;
        screen.setAttribute('aria-label',t('Terminal input'));
        const startButton=button(t('Open terminal'),start,'primary'),stopButton=button(t('End session'),confirmEnd);
        const keys=make('div',undefined,'terminal-keys');keys.setAttribute('aria-label',t('Terminal keys'));
        for(const [key,value] of [['Esc','\x1b'],['Tab','\t'],['Ctrl+C','\x03'],['Ctrl+D','\x04'],['Ctrl+]','\x1d'],['↑','\x1b[A'],['↓','\x1b[B']]){
            keys.append(button(key,()=>{if(channel?.valid){channel.send(new TextEncoder().encode(value));term.focus();}}));
        }
        body.append(selectors,help,buttons(startButton,stopButton),status,screen,keys);box.append(body);
        const ref=panel(t('CLI reference')),guide=make('div',undefined,'content cli-reference');
        for(const [label,cmd] of [
            ['Host configuration, services and packages','sudo nmtui\nsystemctl status\nsudoedit /etc/hosts\napt list --upgradable'],
            ['VM disks, networking, devices and boot order','sudo virsh -c qemu:///system list --all\nsudo virsh -c qemu:///system edit VM_NAME'],
            ['Container configuration, devices and guest shell','sudo incus list\nsudo incus config edit CONTAINER_NAME\nsudo incus exec CONTAINER_NAME -- /bin/sh'],
            ['LinuxSphere nodes and language settings','sudo dsctl nodes\ndsctl language list\nsudo dsctl language set en_US.UTF-8']]){
            const group=make('div');group.append(make('h3',t(label)),make('pre',cmd));guide.append(group);
        }
        ref.append(guide);root.append(box,ref);
        ui={node,mode:type,guest,help,status,screen,keys,start:startButton,stop:stopButton};
        node.c.onchange=type.c.onchange=updateControls;
        window.addEventListener('pagehide',()=>{if(channel)dispose();});
    }
    function show(state) { data=state||data;if(!ui)mount();updateControls(); }
    return {show};
})();
