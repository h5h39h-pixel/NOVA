// -*- part of the Nova SPA (framework-free, global scope, load order matters) -*-
// System/insight pages — Diagnostics, Audit, Open WebUI, Settings. (Nova Brain moved to pages-brain.js.)
// Split from the original monolithic pages.js (HON-11). Loaded after core.js, before shell.js.

function Diagnostics(){
  const html=`<div class="grid g2">
    ${card('💓 Server Health',`<div id="dghealth"><span class="spin"></span> loading…</div>`)}
    ${card('🐞 Recent Errors <span class="tag" id="dgerrtot"></span>',`<div id="dgerrors"><span class="spin"></span></div>
       <button class="btn sm danger mt" id="dgerrclear">Clear errors</button>`)}
   </div>
   ${card('🩺 System Self-Test <span class="tag" id="dgsum"></span>',`
     <p class="muted" style="font-size:12.5px">Runs a full health check across every subsystem — services, database, embeddings, GPU, safety guards, and more.</p>
     <button class="btn p mt" id="dgrun">▶ Run self-test</button>
     <div id="dglist" class="mt"></div>`)}
   ${card('📈 Quality Trend <span class="tag" id="dgqtag"></span>',`
     <p class="muted" style="font-size:12.5px">Scored eval/health runs over time — watch for regressions after model, dependency, or prompt changes. Eval scripts can POST results to <code>/api/quality</code>; schedule the <code>quality_check</code> automation for periodic health snapshots.</p>
     <button class="btn p mt" id="dgqsnap">📸 Take a health snapshot now</button>
     <div id="dgquality" class="mt"></div>`)}`;
  async function run(){const el=$('#dglist');if(!el)return;el.innerHTML='<span class="spin"></span> running checks…';
    const r=await api('/selftest');const s=$('#dgsum');if(s){s.className='tag '+(r.ok?'on':'err');s.textContent=`${r.passed}/${r.total} passed`}
    el.innerHTML=r.checks.map(c=>`<div class="row"><span style="font-size:16px">${c.ok?'✅':'❌'}</span><span class="name">${esc(c.name)}</span><span class="muted" style="font-size:11.5px">${esc(c.detail)}</span></div>`).join('')}
  const fmtUp=s=>{s=Math.floor(s);const d=Math.floor(s/86400),h=Math.floor(s%86400/3600),m=Math.floor(s%3600/60);return (d?d+'d ':'')+(h?h+'h ':'')+m+'m'};
  async function loadHealth(){const el=$('#dghealth');if(!el)return;const h=await api('/health');
    el.innerHTML=[['Uptime',fmtUp(h.uptime_sec)],['Metrics loop',h.metrics_loop_alive?'🟢 alive':'🔴 stalled'],
      ['Background jobs',h.jobs_running+' running · '+h.jobs_total+' total'],['Live clients',h.ws_clients],
      ['Errors logged',h.errors_total]].map(([k,v])=>`<div class="metarow"><span class="mut">${k}</span><span>${v}</span></div>`).join('')}
  async function loadErrors(){const el=$('#dgerrors');if(!el)return;const r=await api('/errors');const tot=$('#dgerrtot');if(tot)tot.textContent=(r.total||0)+' total';
    el.innerHTML=(r.errors&&r.errors.length)?r.errors.map(e=>`<div class="row"><span class="tag err">${e.count}×</span><span class="name" title="${esc(e.signature)}">${esc(e.signature)}</span><span class="muted" style="font-size:11px">${esc(e.where||'')}</span></div>`).join(''):'<div class="empty">No errors recorded 🎉</div>'}
  async function loadQuality(){const el=$('#dgquality');if(!el)return;const r=await api('/quality');
    const sum=(r&&r.summary)||[];const tag=$('#dgqtag');if(tag)tag.textContent=sum.length?sum.length+' suites':'no runs yet';
    if(!sum.length){el.innerHTML='<div class="empty">no quality runs yet — take a snapshot or run an eval script</div>';return}
    el.innerHTML=sum.map(s=>{const d=s.delta;const arrow=d==null?'':(d>0?`<span style="color:var(--ok)">▲ +${d}</span>`:(d<0?`<span style="color:var(--err)">▼ ${d}</span>`:'<span class="mut">→ 0</span>'));
      return `<div class="metarow"><span>${esc(s.suite)}</span><span><b>${s.latest}%</b> ${arrow}</span></div>`}).join('')}
  function mount(){run();loadHealth();loadErrors();loadQuality();$('#dgrun').onclick=run;
    const hv=setInterval(loadHealth,5000);
    const ce=$('#dgerrclear');if(ce)ce.onclick=()=>del('/errors').then(loadErrors);
    const qs=$('#dgqsnap');if(qs)qs.onclick=async()=>{qs.disabled=true;const r=await post('/quality/snapshot',{});
      toast('info','Health snapshot',r&&r.run?`${r.run.score}/${r.run.total} (${r.run.pct}%)`:'recorded');qs.disabled=false;loadQuality()};
    return [()=>clearInterval(hv)]}
  return {html,mount};
}
function AuditPage(){
  const html=`${card('🛡️ Audit Log <span class="tag" id="autotal"></span>',`
     <div class="flex wrap" style="gap:8px;margin-bottom:10px">
       <select class="t" id="aufilter" style="width:auto"><option value="">all actors</option></select>
       <input class="srch" id="ausearch" placeholder="🔎 search actions / details" style="width:220px">
       <span class="spacer"></span>
       <button class="btn sm" id="auexport">⤓ export CSV</button><button class="btn sm danger" id="auclear">clear</button>
     </div>
     <div style="max-height:64vh;overflow:auto"><table id="autable"><tbody></tbody></table></div>`)}`;
  let actorFilter='',q='';
  function rowHtml(e){const cls=e.status==='fail'?'err':e.status==='blocked'?'warn':'on';
    return `<tr><td class="mono" style="white-space:nowrap;color:var(--mut)">${new Date(e.ts*1000).toLocaleString()}</td><td><span class="tag">${esc(e.actor)}</span></td><td>${esc(e.action)}</td><td class="mono" style="font-size:11px">${esc((e.detail||'').slice(0,90))}</td><td><span class="tag ${cls}">${esc(e.status)}</span></td></tr>`}
  async function load(){const r=await api('/audit?limit=300'+(actorFilter?'&actor='+encodeURIComponent(actorFilter):'')+(q?'&q='+encodeURIComponent(q):''));
    const t=$('#autable');if(!t)return;t.querySelector('tbody').innerHTML='<tr><th>time</th><th>actor</th><th>action</th><th>detail</th><th>status</th></tr>'+(r.events.length?r.events.map(rowHtml).join(''):'<tr><td colspan=5><div class="empty">no events yet</div></td></tr>');
    $('#autotal').textContent=r.total+' events';
    const sel=$('#aufilter');if(sel&&sel.options.length<=1&&r.actors.length){sel.innerHTML='<option value="">all actors</option>'+r.actors.map(a=>`<option ${a===actorFilter?'selected':''}>${esc(a)}</option>`).join('')}}
  function mount(){load();
    $('#aufilter').onchange=e=>{actorFilter=e.target.value;load()};
    $('#ausearch').addEventListener('input',e=>{q=e.target.value;clearTimeout(window._aut);window._aut=setTimeout(load,250)});
    $('#auexport').onclick=async()=>{const r=await api('/audit?limit=5000');
      const rows=[['time','actor','action','detail','status']].concat(r.events.map(e=>[new Date(e.ts*1000).toISOString(),e.actor,e.action,(e.detail||'').replace(/[\r\n]+/g,' '),e.status]));
      const csv=rows.map(row=>row.map(c=>'"'+String(c).replace(/"/g,'""')+'"').join(',')).join('\n');
      const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));a.download='audit-log.csv';a.click()};
    $('#auclear').onclick=()=>{if(confirm('Clear the entire audit log? This cannot be undone.'))del('/audit').then(load)};
    let t2=null;const u=bus.on('audit',()=>{clearTimeout(t2);t2=setTimeout(load,400)});
    return [u];
  }
  return {html,mount};
}
function Owui(){
  const html=card('Open WebUI',`<p class="muted">Local chat stack on port 3000 (Docker). Configuration is managed from the Tools page.</p>
    <div class="flex mt"><a class="btn p" href="http://localhost:3000" target="_blank">Open in new tab ↗</a><button class="btn" id="rs">🔄 Restart container</button></div>
    <iframe src="http://localhost:3000" style="width:100%;height:60vh;border:1px solid var(--line);border-radius:10px;margin-top:14px"></iframe>`);
  function mount(){$('#rs').onclick=()=>{post('/services/owui/restart');toast('info','Restarting Open WebUI','')};return []}
  return {html,mount};
}

function Settings(){
  const s=State.settings;
  const html=`<div class="grid g2">
    ${card(t('d_settings'),`
      <label class="f">${t('default_local')}</label><select class="t" id="sl"></select>
      <label class="f">${t('default_cloud')}</label><input class="t" id="scl" value="${esc(s.default_cloud_model||'')}">
      <label class="f">${t('cloud_key')}</label><input class="t" id="sk" type="password" placeholder="${s.cloud_api_key?'••••••••':'(optional)'}">
      <label class="f" style="display:flex;align-items:center;gap:9px;margin-top:14px"><button class="sw ${s.desktop_notifications?'on':''}" id="sn"></button> ${t('desktop_notif')}</label>
      <label class="f">Webhook URL (Slack / Discord / ntfy)</label><input class="t" id="swh" value="${esc(s.webhook_url||'')}" placeholder="https://hooks.slack.com/...">
      <label class="f" style="display:flex;align-items:center;gap:9px;margin-top:10px"><button class="sw ${s.webhook_enabled?'on':''}" id="swe"></button> Send notifications to webhook</label>
      <button class="btn p mt" id="sv" style="width:100%">${t('save_settings')}</button>`)}
    ${card(t('language')+' / '+t('mode'),`
      <label class="f">${t('language')}</label>
      <div class="flex"><button class="btn ${State.lang==='en'?'p':''}" id="le">English</button><button class="btn ${State.lang==='ar'?'p':''}" id="la">العربية</button></div>
      <label class="f mt">${t('mode')}</label>
      <div class="flex"><button class="btn" data-m="local">🏠 ${t('local')}</button><button class="btn" data-m="cloud">☁ ${t('cloud')}</button><button class="btn" data-m="auto">⚡ ${t('auto')}</button></div>
      <label class="f mt">Theme</label>
      <div class="flex"><button class="btn" id="thd">🌙 Dark</button><button class="btn" id="thl">☀️ Light</button><button class="btn" id="tha">🌗 Auto</button></div>
      <label class="f mt" style="display:flex;align-items:center;gap:9px"><button class="sw ${localStorage.getItem('lite')?'on':''}" id="slite"></button> Lite visuals — reduce background animations (low-end GPUs)</label>
      <label class="f mt" style="display:flex;align-items:center;gap:9px"><button class="sw ${s.confirm_exit!==false?'on':''}" id="sconfirm"></button> Confirm before closing the tab (warn while Nova is running)</label>
      <label class="f mt" style="display:flex;align-items:center;gap:9px"><button class="sw ${s.agent_can_control!==false?'on':''}" id="sagentctl"></button> 🖱️ Let the autonomous agent control mouse/keyboard (off = agent can't drive the GUI; manual control + panic stop still work)</label>
      <label class="f mt" style="display:flex;align-items:center;gap:9px"><button class="sw ${s.screen_memory_enabled?'on':''}" id="sscrmem"></button> 🧠 Screen memory (opt-in) — OCR snapshots of your screen into the knowledge base so you can ask "what did I see earlier?" (local-only; keeps the newest ${s.screen_memory_keep||50}; schedule the <code>screen_memory</code> automation to capture periodically)</label>
      <button class="btn mt" id="purgescrmem" style="width:100%">🧹 Purge all screen memories</button>
      <label class="f mt">🔊 Voice speed (TTS) <span class="aset-v" id="ttsratev">${(+s.tts_rate||1).toFixed(1)}×</span></label>
      <input type="range" id="sttsrate" min="0.7" max="1.6" step="0.1" value="${+s.tts_rate||1}" style="width:100%">
      <label class="f mt">Backup &amp; Restore</label>
      <div class="flex wrap"><button class="btn" id="expset">⤓ Export settings</button><button class="btn" id="impset">⤒ Import settings</button><input type="file" id="impfile" accept=".json" style="display:none"></div>
      <div class="flex wrap" style="margin-top:7px"><button class="btn p" id="backupall">💾 Backup everything</button><button class="btn" id="restoreall">♻ Restore everything</button><input type="file" id="restorefile" accept=".json" style="display:none"></div>
      <p class="muted mt" style="font-size:11px">Backup bundles settings, conversations, knowledge base, automations, workflows &amp; training data into one file.</p>`)}
   </div>
   ${card('🔒 Access & Security',`
      <p class="muted" style="font-size:12.5px">By default the dashboard is <b>localhost-only</b> (most secure). Enable token auth to safely allow access from other devices on your network.</p>
      <label class="f" style="display:flex;align-items:center;gap:9px;margin-top:10px"><button class="sw ${s.auth_enabled?'on':''}" id="sae"></button> Require token authentication</label>
      <label class="f" style="display:flex;align-items:center;gap:9px"><button class="sw ${s.lan_access?'on':''}" id="slan"></button> Allow network (LAN) access — needs auth + restart</label>
      ${s.auth_enabled?`<p class="muted" style="font-size:11.5px">🔑 Token auth is ON. The access token is shown only once when first enabled (it's stored hashed, never re-served). If you've lost it, turn auth off &amp; on again to mint a new one.</p>`:''}
      <button class="btn p mt" id="saveauth" style="width:100%">Save security settings</button>
      ${s.auth_enabled?`<button class="btn mt" id="logout" style="width:100%">Log out</button>`:''}
      <p class="muted mt" style="font-size:11px">Changing LAN access requires restarting the server. On a LAN, traffic is unencrypted (HTTPS is on the roadmap) — use only on trusted networks.</p>`)}
   ${card('Usage Statistics',`<div id="usagebox"></div>`)}
   ${card('🧠 Persistent Memory',`
      <p class="muted" style="font-size:12.5px">Durable facts Nova remembers about you across sessions (local-only). Used to personalise chat &amp; agent answers. The agent can also add facts itself via its <code>remember</code> tool.</p>
      <div class="flex" style="margin-top:8px"><input class="t" id="memin" placeholder="e.g. I prefer concise answers in English" style="flex:1"><button class="btn p" id="memadd">＋ Remember</button></div>
      <div id="membox" style="margin-top:10px"></div>`)}`;
  function mount(){
    (async()=>{const list=await api('/models');$('#sl').innerHTML=list.map(m=>`<option ${m.name===s.default_local_model?'selected':''}>${esc(m.name)}</option>`).join('')})();
    const slite=$('#slite');if(slite)slite.onclick=function(){const on=!this.classList.contains('on');
      if(on)localStorage.setItem('lite','1');else localStorage.removeItem('lite');location.reload()};
    const sconfirm=$('#sconfirm');if(sconfirm)sconfirm.onclick=function(){const on=!this.classList.contains('on');this.classList.toggle('on',on);
      post('/settings',{confirm_exit:on}).then(x=>{State.settings=x});toast('info',on?'Exit confirmation enabled':'Exit confirmation disabled','')};
    const sactl=$('#sagentctl');if(sactl)sactl.onclick=function(){const on=!this.classList.contains('on');this.classList.toggle('on',on);
      post('/settings',{agent_can_control:on}).then(x=>{State.settings=x});toast(on?'info':'success',on?'Agent GUI control enabled':'Agent GUI control disabled',on?'the agent may move the mouse/keyboard':'the agent can no longer drive the GUI')};
    const sscrmem=$('#sscrmem');if(sscrmem)sscrmem.onclick=function(){const on=!this.classList.contains('on');this.classList.toggle('on',on);
      post('/settings',{screen_memory_enabled:on}).then(x=>{State.settings=x});toast(on?'info':'success',on?'Screen memory enabled':'Screen memory disabled',on?'OCR snapshots can now be saved to the KB (opt-in)':'no screen snapshots will be stored')};
    const purgesm=$('#purgescrmem');if(purgesm)purgesm.onclick=async function(){if(!confirm('Delete ALL stored screen memories from the knowledge base?'))return;
      const r=await fetch('/api/vision/screen-memory',{method:'DELETE'}).then(x=>x.json());toast('success','Screen memories purged',`removed ${(r&&r.removed)||0} entries`)};
    {const r=$('#sttsrate');if(r)r.oninput=e=>{const v=+e.target.value;$('#ttsratev').textContent=v.toFixed(1)+'×';clearTimeout(r._t);r._t=setTimeout(()=>post('/settings',{tts_rate:v}).then(x=>{State.settings=x}),400)};}
    $('#thd').onclick=()=>{localStorage.setItem('theme','dark');applyTheme()};
    $('#thl').onclick=()=>{localStorage.setItem('theme','light');applyTheme()};
    $('#tha').onclick=()=>{localStorage.setItem('theme','auto');applyTheme();toast('info','Auto theme','light by day, dark by night')};
    $('#expset').onclick=exportSettings;
    $('#impset').onclick=()=>$('#impfile').click();$('#impfile').onchange=e=>{if(e.target.files[0])importSettings(e.target.files[0])};
    $('#backupall').onclick=()=>{window.open('/api/backup','_blank');toast('info','Backup downloading','full system bundle')};
    $('#restoreall').onclick=()=>$('#restorefile').click();
    $('#restorefile').onchange=e=>{const f=e.target.files[0];if(!f)return;const rd=new FileReader();
      rd.onload=async()=>{try{const data=JSON.parse(rd.result);const r=await post('/restore',data);
        toast(r.ok?'success':'error',r.ok?'Restored':'Restore failed',r.ok?('added '+JSON.stringify(r.added)):(r.error||''));}
        catch(err){toast('error','Invalid backup file','')}};rd.readAsText(f)};
    const loadMem=async()=>{const r=await api('/memory');const items=(r&&r.items)||[];
      $('#membox').innerHTML=items.length?items.map(f=>`<div class="metarow"><span>${f.pinned?'📌 ':''}${esc(f.text)}</span><button class="btn" data-mdel="${f.id}" title="Forget">✕</button></div>`).join(''):'<div class="empty">nothing remembered yet</div>';
      $$('#membox [data-mdel]').forEach(b=>b.onclick=async()=>{await fetch('/api/memory/'+b.dataset.mdel,{method:'DELETE'});loadMem()})};
    const addMem=async()=>{const v=$('#memin').value.trim();if(!v)return;const r=await post('/memory',{text:v});
      if(r&&r.ok){$('#memin').value='';toast('success','Remembered','');loadMem()}else toast('error','Could not save',(r&&r.error)||'')};
    $('#memadd').onclick=addMem;$('#memin').onkeydown=e=>{if(e.key==='Enter')addMem()};loadMem();
    const u=getUsage();const ent=Object.entries(u).sort((a,b)=>b[1]-a[1]);
    $('#usagebox').innerHTML=ent.length?ent.map(([k,v])=>`<div class="metarow"><span>${esc(k)}</span><span class="tag">${v}</span></div>`).join(''):'<div class="empty">no usage yet</div>';
    $('#sn').onclick=function(){this.classList.toggle('on')};
    $('#swe').onclick=function(){this.classList.toggle('on')};
    $('#sv').onclick=()=>{const p={default_local_model:$('#sl').value,default_cloud_model:$('#scl').value,desktop_notifications:$('#sn').classList.contains('on'),webhook_url:$('#swh').value.trim(),webhook_enabled:$('#swe').classList.contains('on')};
      const k=$('#sk').value;if(k)p.cloud_api_key=k;post('/settings',p).then(x=>{State.settings=x;toast('success','Settings saved','')})};
    const sae=$('#sae'),slan=$('#slan');if(sae)sae.onclick=function(){this.classList.toggle('on')};if(slan)slan.onclick=function(){this.classList.toggle('on')};
    const sa=$('#saveauth');if(sa)sa.onclick=async()=>{
      const body={auth_enabled:sae.classList.contains('on'),lan_access:slan.classList.contains('on')};
      const s2=await post('/settings',body);State.settings=s2;
      // the raw token is returned exactly once as `new_token` (never stored/re-served) — auto-login with it
      // and show it to the user so they can save it for other devices.
      const tok=s2.new_token;
      if(s2.auth_enabled&&tok){await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:tok})});
        prompt('Your access token (save it now — it is shown only once, for signing in on other devices):',tok);}
      toast('success','Security settings saved',s2.auth_enabled?'Token active — keep it safe; restart for LAN':'Auth disabled');route()};
    const lo=$('#logout');if(lo)lo.onclick=async()=>{await fetch('/api/auth/logout',{method:'POST'});location.reload()};
    $('#le').onclick=()=>setLang('en');$('#la').onclick=()=>setLang('ar');
    const markMode=()=>$$('#pagebody [data-m]').forEach(b=>b.classList.toggle('p',b.dataset.m===State.settings.mode));markMode();
    $$('#pagebody [data-m]').forEach(b=>b.onclick=()=>{State.settings.mode=b.dataset.m;post('/settings',{mode:b.dataset.m});markMode();toast('info','Mode: '+b.dataset.m.toUpperCase(),'')});
    return [];
  }
  return {html,mount};
}

