'use strict';
const SphereI18n = (() => {
    let info, messages = {}, current = 'en', displayRegion = 'en-US', missing = '';
    const normalize = value => String(value || '').split('.')[0].split('@')[0].replaceAll('_','-').toLowerCase();
    const osTag = value => ['c','posix',''].includes(normalize(value)) ? 'en-us' : normalize(value);
    const t = (key, values = {}) => (Object.hasOwn(messages,key) ? messages[key] : String(key))
        .replace(/\{([a-z][a-z0-9_]*)\}/g, (all,k) => Object.hasOwn(values,k) ? String(values[k]) : all);
    function preference() {
        const match = document.cookie.match(/(?:^|;\s*)CockpitLang=([^;]+)/);
        return normalize(match ? decodeURIComponent(match[1]) : localStorage.getItem('cockpit.lang'));
    }
    function syncCockpit(code) {
        document.cookie = 'CockpitLang='+encodeURIComponent(code)+'; Path=/; Max-Age=31536000; SameSite=Lax'+(location.protocol==='https:'?'; Secure':'');
        localStorage.setItem('cockpit.lang',code);
    }
    function reloadConsole() {
        try { window.top.location.reload(); } catch { location.reload(); }
    }
    async function command(args, admin = false) {
        const data = await cockpit.spawn(['/usr/local/bin/dsctl','language',...args],
            {err:'message',...(admin?{superuser:'require'}:{}),environ:['LINUXSPHERE_LANGUAGE='+current]});
        return JSON.parse(data);
    }
    function availableCode(tag) {
        const choices = info.packs.map(p => p.code);
        return [tag,tag.split('-')[0]].find(c => choices.includes(c));
    }
    async function init() {
        info = await command(['list']);
        const cookie = preference(), host = osTag(info.system);
        let follow = localStorage.getItem('linuxsphere.follow-host')==='yes';
        if (follow && cookie && cookie !== localStorage.getItem('linuxsphere.last-host-tag')) {
            localStorage.removeItem('linuxsphere.follow-host');
            follow = false;
        }
        const useHost = follow || !cookie;
        const desired = useHost ? host : cookie;
        if (useHost) {
            localStorage.setItem('linuxsphere.follow-host','yes');
            localStorage.setItem('linuxsphere.last-host-tag',host);
            if (cookie !== host) {
                syncCockpit(host);
                // Cockpit loads translations for its own menus when the top window opens.
                if (normalize(navigator.language)!==host || cookie) {
                    reloadConsole();
                    return;
                }
            }
        }
        current = availableCode(desired) || 'en';
        missing = availableCode(desired) ? '' : desired;
        const pack = await command(['catalog',current]);
        messages = pack.messages;
        try { displayRegion = Intl.getCanonicalLocales(desired)[0] || current; }
        catch { displayRegion = current; }
        document.documentElement.lang = current;
        document.documentElement.dir = ['ar','he','fa','ur'].includes(current.split('-')[0]) ? 'rtl' : 'ltr';
    }
    function setDisplay(code) {
        const follow = !code;
        const tag = follow ? osTag(info.system) : normalize(code);
        localStorage.setItem('linuxsphere.follow-host',follow?'yes':'no');
        localStorage.setItem('linuxsphere.last-host-tag',osTag(info.system));
        syncCockpit(tag);
        reloadConsole();
    }
    function renderPanel(root) {
        if (!info || root.childElementCount) return;
        const browser = panel(t('Web interface'));
        const body = make('div',undefined,'content settings-form');
        const follow = localStorage.getItem('linuxsphere.follow-host')==='yes';
        const ui = field(t('Interface language'),'select',follow?'':current,
            [['',t('Use the host language')],...info.packs.map(p=>[p.code,p.name])]);
        body.append(ui.box,ptext(t('Applies to this browser, including Cockpit. Applying a display language reloads the console and closes its open terminal.')));
        if (missing) body.append(ptext(t('Language pack not installed for {language}. LinuxSphere is displaying English.',{language:missing})));
        body.append(button(t('Use language'),()=>setDisplay(ui.c.value),'primary'));
        browser.append(body);
        const host = panel(t('Host language and region')), box = make('div',undefined,'content settings-form');
        const system = field(t('System locale'),'select',info.system,info.locales);
        const hint = ptext(t('Current default: {locale}',{locale:info.system}));
        const apply = button(t('Set host language'),async()=>{
            apply.disabled=true;
            try {
                const result = await command(['set',system.c.value],true);
                info.system=result.system;
                hint.textContent=t('Current default: {locale}',{locale:result.system});
                if (localStorage.getItem('linuxsphere.follow-host')==='yes') setDisplay('');
            } finally { apply.disabled=false; }
        });
        box.append(system.box,hint,ptext(t('Applies to new logins on this host. Virtual machines and containers use their own operating system settings.')),apply);
        host.append(box);
        const extra=panel(t('Additional languages')), how=make('div',undefined,'content');
        how.append(ptext(t('To add a dashboard language, export the translation template, translate its messages and install it from the host CLI.')),
            make('pre','dsctl language template > my-language.json\nsudo dsctl language install my-language.json'));
        extra.append(how);
        root.append(browser,host,extra);
    }
    return {t,init,render:renderPanel,code:()=>current,region:()=>displayRegion,hostLocale:async()=>(await command(['list'])).system};
})();
