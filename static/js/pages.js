// -*- part of the Nova SPA (framework-free, global scope, load order matters) -*-
// Everyday pages — Dashboard, Monitor, Terminal, Chat + shared dashboard/voice-template helpers.
// Split from the original monolithic pages.js (HON-11). Loaded after core.js, before shell.js.

/* ============================ pages.js ============================
   One function per screen, each returning {html, mount}. Depends on core.js.
   Part of the AI Control Center SPA. Loaded in order: core -> pages -> shell.
   Single shared global scope (no bundler); load order matters. */
/* ============================ PAGES ============================ */
const ACTOR_ICON={terminal:'⌨️',agent:'🤖',automation:'⏰',workflow:'🔗',auth:'🔒',models:'🧩',tools:'🛠️',training:'🎓',settings:'⚙️',kb:'📚',selftest:'🩺'};
function Dashboard(){
  const html=`
   <div class="grid g4" style="margin-bottom:16px">
     ${kpi('gpu','🎮','GPU','v_gpu','%')}${kpi('vram','💾','VRAM','v_vram','%')}
     ${kpi('cpu','🧠','CPU','v_cpu','%')}${kpi('ram','📦','RAM','v_ram','%')}
   </div>
   <div class="copilot" style="margin-bottom:16px"><div class="flex" style="gap:11px;align-items:flex-start">
     <span style="font-size:24px;filter:drop-shadow(0 0 8px var(--accent3))">🧭</span>
     <div style="flex:1"><div style="font-family:var(--head);font-size:11px;letter-spacing:.12em;color:var(--accent3)">NOVA CO-PILOT</div>
       <div class="cpt" id="cptext">Analyzing your system…</div>
       <div id="habits" class="muted" style="font-size:11.5px;margin-top:6px"></div></div>
     <span id="cpapply"></span><button class="btn sm" id="cpre" data-tip="Refresh suggestion">↻</button></div></div>
   <div class="grid g2" style="margin-bottom:16px">
     ${card('🛰️ System Health',`<div class="radar" id="radar"><div class="rin"><b id="rval">—</b><small id="rlbl">checking…</small></div></div><div id="svc" class="mt"></div>`)}
     ${card('📡 Live Activity',`<div class="feed" id="feed"><div class="empty">listening for events…</div></div>`)}
   </div>
   ${card('✨ Insights',`<div id="insights"><div class="empty">…</div></div>`,'<button class="btn sm" id="brief">📰 Daily briefing</button>')}
   <div id="briefcard" style="margin-top:16px"></div>
   <div style="margin-top:16px">${card('🏆 Achievements <span class="tag" id="achsum"></span>',`<div class="achwrap" id="ach"></div>`)}</div>
   <div class="grid g2" style="margin-top:16px">
     ${card(t('quick_actions'),`<div class="qa" id="qa"></div>`)}
     ${card(t('recent_cmds'),`<div id="recent"><div class="empty">…</div></div>`)}
   </div>`;
  function renderRadar(s){const up=['owui','ollama','comfy','ws'].filter(k=>s[k]).length,pct=Math.round(up/4*100);
    const r=$('#radar');if(!r)return;r.style.setProperty('--rv',pct);
    r.style.setProperty('--rc',pct===100?'var(--ok)':pct>=50?'var(--warn)':'var(--err)');
    $('#rval').textContent=pct+'%';$('#rlbl').textContent=`${up}/4 online`}
  function feedAdd(icon,text){const f=$('#feed');if(!f)return;const e=f.querySelector('.empty');if(e)e.remove();
    const d=document.createElement('div');d.className='feeditem';d.innerHTML=`<span class="fi">${icon}</span><span class="ft">${esc(text)}</span><span class="fm">${new Date().toLocaleTimeString().slice(0,5)}</span>`;
    f.insertBefore(d,f.firstChild);while(f.children.length>40)f.removeChild(f.lastChild)}
  async function loadInsights(){const el=$('#insights');if(!el)return;const r=await api('/insights');
    el.innerHTML=r.insights.map(t2=>`<div class="row"><span style="font-size:18px">${t2.icon}</span><span class="name" style="white-space:normal">${esc(t2.text)}</span>${t2.action==='retrain'?`<button class="btn sm p" data-ins="retrain">retrain</button>`:t2.go?`<button class="btn sm" data-go="${t2.go}">open</button>`:''}</div>`).join('');
    $$('#insights [data-go]').forEach(b=>b.onclick=()=>location.hash=b.dataset.go);
    $$('#insights [data-ins=retrain]').forEach(b=>b.onclick=()=>{post('/learn/retrain');toast('info','Retraining started','')});}
  async function loadCopilot(){const r=await api('/copilot').catch(()=>({text:'All systems nominal.'}));
    const t2=$('#cptext');if(t2)t2.textContent=r.text||'All systems nominal.';
    const ap=$('#cpapply');if(ap){ap.innerHTML='';if(r.action){const b=document.createElement('button');b.className='btn p';b.textContent='Apply';
      b.onclick=()=>{if(r.action==='retrain'){post('/learn/retrain');toast('info','Retraining started','')}else if(r.action&&r.action.go)location.hash=r.action.go};ap.appendChild(b)}}
    const h=await api('/habits').catch(()=>({tips:[]}));const hb=$('#habits');if(hb)hb.textContent=(h.tips||[]).slice(0,2).join('   •   ')}
  async function loadAch(){const r=await api('/achievements');const el=$('#ach');if(!el)return;
    el.innerHTML=r.achievements.map(a=>`<div class="ach ${a.unlocked?'':'locked'}"><span class="ae">${a.icon}</span><div><div class="at">${esc(a.title)}</div><div class="ad">${a.have}/${a.goal} ${esc(a.unit)}</div></div></div>`).join('');
    const s=$('#achsum');if(s)s.textContent=`${r.unlocked}/${r.total} unlocked`}
  function mount(){
    if(State.metrics)updateKpis(State.metrics);renderSvc(State.services);renderRadar(State.services);
    renderQuick();loadRecent();loadInsights();loadCopilot();loadAch();
    $('#cpre').onclick=loadCopilot;
    $('#brief').onclick=async()=>{$('#briefcard').innerHTML=card('📰 Daily Briefing','<div id="briefout"><span class="spin"></span> generating…</div>');
      const r=await api('/briefing');const o=$('#briefout');if(o)o.innerHTML=mdRender(r.text||'');usage('briefing')};
    const onS=s=>{renderSvc(s);renderRadar(s)};
    const iv=setInterval(loadRecent,10000),iv2=setInterval(loadInsights,30000),iv3=setInterval(loadAch,60000);
    const subs=[bus.on('metrics',m=>updateKpis(m)),bus.on('services',onS),bus.on('job',loadRecent),
      bus.on('audit',e=>feedAdd(ACTOR_ICON[e.actor]||'⚡',`${e.actor}: ${e.action}${e.detail?' · '+e.detail:''}`)),
      bus.on('notification',n=>feedAdd('🔔',n.title)),
      ()=>clearInterval(iv),()=>clearInterval(iv2),()=>clearInterval(iv3)];
    return subs;
  }
  return {html,mount};
}
function kpi(k,ic,lbl,id,unit){return `<div class="card"><div class="bd"><div class="kpi"><div class="ic">${ic}</div><div class="stat"><span class="v"><span id="${id}">0</span>${unit}</span><span class="l">${lbl}</span></div></div><div class="bar"><i id="${id}_b" style="width:0"></i></div></div></div>`}
function updateKpis(m){
  if(m.gpu){set('v_gpu',Math.round(m.gpu.util));bar('v_gpu_b',m.gpu.util);
    const vp=m.gpu.vram_used/m.gpu.vram_total*100;set('v_vram',Math.round(vp));bar('v_vram_b',vp);}
  set('v_cpu',Math.round(m.cpu));bar('v_cpu_b',m.cpu);set('v_ram',Math.round(m.ram_pct));bar('v_ram_b',m.ram_pct);
}
const set=(id,v)=>{const e=$('#'+id);if(e)e.textContent=v};
const bar=(id,v)=>{const e=$('#'+id);if(e)e.style.width=Math.min(100,v||0)+'%'};
function renderSvc(s){const el=$('#svc');if(!el)return;const row=(n,k)=>`<div class="metarow"><span>${n}</span><span class="tag ${s[k]?'on':'err'}">${s[k]?'online':'offline'}</span></div>`;
  el.innerHTML=row('Open WebUI (3000)','owui')+row('Ollama (11434)','ollama')+row('ComfyUI (8188)','comfy')+row('Live WebSocket','ws')}
function renderQuick(){
  const acts=[
   ['🎬','Generate video','#/video'],['💬','Open Nova','#/workspace'],['🎓','Harvest & Retrain','retrain'],
   ['⌨️','Open terminal','#/terminal'],['🔄','Restart ComfyUI','comfy'],['📊','Monitor','#/monitor']];
  $('#qa').innerHTML=acts.map((a,i)=>`<button data-a="${i}"><span class="qi">${a[0]}</span><span class="qt">${a[1]}</span></button>`).join('');
  $$('#qa button').forEach((b,i)=>b.onclick=()=>{const a=acts[i][2];
    if(a.startsWith('#/'))location.hash=a;
    else if(a==='retrain'){post('/learn/retrain');toast('info','Harvest & Retrain started','see Training Studio')}
    else if(a==='comfy'){post('/services/comfy/restart');toast('info','Restarting ComfyUI','')}});
}
async function loadRecent(){const el=$('#recent');if(!el)return;const rows=await api('/history?limit=8');
  el.innerHTML=rows.length?rows.map(r=>`<div class="row"><span class="mono" style="color:var(--mut)">${fmtTime(r.ts)}</span><span class="name mono">${esc((r.command||'').slice(0,40))}</span><span class="tag ${r.exit_code===0?'on':'err'}">${r.exit_code}</span></div>`).join(''):'<div class="empty">no commands yet</div>'}

function Monitor(){
  const html=`
   ${card('Live Gauges',`<div class="gauges">${ringHTML('m_gpu','GPU Util','%')}${ringHTML('m_vram','VRAM','%')}${ringHTML('m_cpu','CPU','%')}${ringHTML('m_ram','RAM','%')}</div>`)}
   <div class="grid g2 mt">
     ${card('GPU & VRAM history',`<canvas class="spark" id="h_gpu" style="height:120px"></canvas>`)}
     ${card('CPU & RAM history',`<canvas class="spark" id="h_cpu" style="height:120px"></canvas>`)}
   </div>
   <div class="grid g2 mt">
     ${card('Details <span class="tag">nvidia-smi + psutil</span>',`<div id="mdet"></div>`,'')}
     ${card('Top Processes <span class="tag">psutil live</span>',`<div id="mproc"><div class="empty">…</div></div>`)}
   </div>`;
  function mount(){
    const upd=m=>{
      if(m.gpu){setRing('m_gpu',m.gpu.util,`${Math.round(m.gpu.temp)}°C · ${Math.round(m.gpu.power)}W`);
        const vp=m.gpu.vram_used/m.gpu.vram_total*100;setRing('m_vram',vp,`${(m.gpu.vram_used/1024).toFixed(1)}/${(m.gpu.vram_total/1024).toFixed(0)} GB`);}
      setRing('m_cpu',m.cpu,`${m.cpu_cores} cores`);setRing('m_ram',m.ram_pct,`${m.ram_used}/${m.ram_total} GB`);
      spark($('#h_gpu'),State.buf.gpu,'#8b5cf6');spark($('#h_cpu'),State.buf.cpu,'#6366f1');
      const g=m.gpu||{};const md=$('#mdet');if(md)md.innerHTML=
        meta('GPU (nvidia-smi)',g.name||'—')+meta('GPU util',`${Math.round(g.util||0)} %`)+
        meta('GPU temp',`${Math.round(g.temp||0)} °C`)+meta('GPU power',`${Math.round(g.power||0)} / ${Math.round(g.power_limit||0)} W`)+
        meta('VRAM',`${((g.vram_used||0)/1024).toFixed(1)} / ${((g.vram_total||0)/1024).toFixed(0)} GB`)+
        meta('CPU (psutil)',`${Math.round(m.cpu)} % · ${m.cpu_cores} cores`)+
        meta('CPU/system temp',m.cpu_temp!=null?`${m.cpu_temp} °C`:'N/A (no sensor exposed)')+
        meta('RAM (psutil)',`${m.ram_used} / ${m.ram_total} GB (${m.ram_pct}%)`)+
        meta('Disk C: (psutil)',m.disk_pct!=null?`${m.disk_pct}% used · ${m.disk_free} GB free`:'—');
    };
    if(State.metrics)upd(State.metrics);
    async function loadProc(){const r=await api('/processes/system?limit=8');const el=$('#mproc');if(!el)return;
      el.innerHTML=`<table><tr><th>process</th><th>PID</th><th>CPU%</th><th>RAM MB</th></tr>`+
        r.top.map(p=>`<tr><td class="mono">${esc(p.name)}</td><td class="mono">${p.pid}</td><td>${p.cpu}</td><td>${p.mem_mb}</td></tr>`).join('')+
        `</table><div class="muted" style="font-size:11px;margin-top:8px">${r.count} total processes</div>`;}
    loadProc();const iv=setInterval(loadProc,3000);
    return [bus.on('metrics',upd),()=>clearInterval(iv)];
  }
  return {html,mount};
}
const meta=(k,v)=>`<div class="metarow"><span class="mut">${k}</span><span>${esc(v)}</span></div>`;

function Terminal(){
  const html=card('PowerShell',`<div class="term" id="term"></div>
    <div class="inrow"><input class="inp" id="cmd" placeholder="${t('cmd_ph')}" autocomplete="off"><button class="btn p" id="rb">${t('run')} ▸</button></div>`,
    `<button class="btn sm" id="cl">${t('clear')}</button>`);
  function mount(){
    const term=$('#term');
    const line=(l)=>{const d=document.createElement('div');d.className=l.startsWith('$')?'cmd':(/error|exception/i.test(l)?'err':l.startsWith('[')?'sys':'');d.textContent=l;term.appendChild(d);
      if(/is not recognized as the name of a cmdlet/i.test(l)){const h=document.createElement('div');h.className='sys';h.textContent='💡 PowerShell terminal — to chat with a model use the AI Chat page.';term.appendChild(h)}
      while(term.children.length>800)term.removeChild(term.firstChild);term.scrollTop=term.scrollHeight};
    const run=()=>{const v=$('#cmd').value.trim();if(!v)return;execCommand(v);$('#cmd').value=''};
    $('#rb').onclick=run;$('#cl').onclick=()=>term.innerHTML='';
    $('#cmd').addEventListener('keydown',e=>{if(e.key==='Enter')run()});$('#cmd').focus();
    return [bus.on('term',m=>line(m.line))];
  }
  return {html,mount};
}
