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
   ['🎬','Generate video','#/video'],['💬','New chat','#/chat'],['🎓','Harvest & Retrain','retrain'],
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

const TEMPLATES=[
 {l:'📝 Summarize',t:'Summarize the following clearly in 5 bullet points:\n'},
 {l:'🌐 Translate AR↔EN',t:'Translate the following between Arabic and English:\n'},
 {l:'💻 Explain code',t:'Explain what this code does, step by step:\n'},
 {l:'🐞 Fix bug',t:'Find and fix the bug in this code and explain the fix:\n'},
 {l:'✉️ Email',t:'Write a short professional email about: '},
 {l:'💡 Brainstorm',t:'Give me 10 creative ideas about: '},
 {l:'⌨️ Top processes',t:'!Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 Name,CPU'},
];
function Chat(){
  const html=`<div class="chatwrap">
    <aside class="convside">
      <button class="btn p" id="newchat" style="width:100%">＋ New chat</button>
      <input class="srch" id="convsrch" placeholder="🔎 search conversations…">
      <div class="convlist" id="convlist"><div class="empty">…</div></div>
    </aside>
    <div class="chatmain">
      <div class="chathd">
        <select class="t" id="cm" style="width:auto;padding:5px 9px;font-size:12px"></select>
        <button class="btn sm" id="cmpbtn" title="Compare two models">⚖</button>
        <button class="btn sm" id="ragbtn" title="Answer from your Knowledge Base (RAG)">📚</button>
        <button class="btn sm" id="dtbtn" title="DeepThink — reason step by step before answering">🧠 DeepThink</button>
        <button class="btn sm" id="wsbtn" title="Web Search — answer with live results from the web">🌐 Search</button>
        <button class="btn sm" id="spkbtn" title="Auto-read replies aloud (Piper TTS)">🔊</button>
        <select class="t" id="cm2" style="width:auto;padding:5px 9px;font-size:12px;display:none"></select>
        <span class="tokbadge" id="tok">0 tokens</span>
        <span class="spacer"></span>
        <input class="srch" id="insrch" placeholder="🔎 in chat" style="width:120px">
        <div class="menu"><button class="btn sm" id="expbtn">⤓ Export</button>
          <div class="pop" id="exppop"><div data-x="txt">as TXT</div><div data-x="md">as Markdown</div><div data-x="json">as JSON</div><div data-x="pdf">as PDF</div></div></div>
        <button class="btn sm danger" id="cc">${t('clear')}</button>
      </div>
      <div id="attachbar"></div>
      <div class="chips" id="chips"></div>
      <div class="chat drop" id="chat"></div>
      <div class="inrow composer">
        <button class="btn" id="attach" title="Attach file (PDF/TXT/DOCX/image)">📎</button>
        <button class="btn" id="mic" title="Voice input">🎤</button>
        <button class="btn" id="prev" title="Live preview (Markdown/code/RTL)">👁</button>
        <input class="inp" id="ci" placeholder="${t('chat_ph')}  ·  !cmd runs PowerShell" autocomplete="off">
        <button class="btn p" id="cs">${t('send')}</button>
      </div>
      <input type="file" id="fileinp" multiple style="display:none" accept=".txt,.md,.json,.csv,.log,.py,.js,.ps1,.pdf,.docx,.png,.jpg,.jpeg,.webp,.bmp">
    </div></div>`;
  let curAI=null,lastUser='',attached=[],comparing=false,ragOn=false,speakOn=false,deepThink=false,webSearch=false;
  function mount(){
    const chat=$('#chat');
    const addMsg=(role,text,user)=>{const d=document.createElement('div');d.className='msg '+role;
      text=text||'';const atts=[];
      text=text.replace(/⟦file:([^|⟧]+)(?:\|(\d+))?⟧\n?/g,(_,n,sz)=>{atts.push([n,+sz||0]);return ''});
      if(atts.length){const aw=document.createElement('div');aw.className='attwrap';
        aw.innerHTML=atts.map(a=>attHTML(a[0],a[1])).join('');d.appendChild(aw)}
      const span=document.createElement('span');
      if(role==='ai'&&text.trim())span.innerHTML=mdRender(text);else span.textContent=text;
      d.appendChild(span);
      if(role==='ai'){d.dataset.user=user||lastUser;const b=document.createElement('span');b.className='save';b.textContent='💾 '+t('save_to_training');
        b.onclick=()=>post('/training/save',{user:d.dataset.user,assistant:span.textContent}).then(r=>toast(r.added?'success':'info',r.added?'Saved to training':'Already saved',''));d.appendChild(b);
        const sb=document.createElement('span');sb.className='save spk';sb.textContent='🔊';sb.title='Read aloud';
        sb.onclick=()=>{post('/tts',{text:span.textContent});toast('info','Speaking…','')};d.appendChild(sb);
        const cp=document.createElement('span');cp.className='save cpy';cp.textContent='📋';cp.title='Copy';
        cp.onclick=()=>{navigator.clipboard.writeText(span.textContent);cp.textContent='✓';setTimeout(()=>cp.textContent='📋',1200)};d.appendChild(cp)}
      chat.appendChild(d);chat.scrollTop=chat.scrollHeight;return d};
    const setTok=n=>{const e=$('#tok');if(e&&n!=null)e.textContent=n+' tokens'};
    async function refreshTok(){const cs=await api('/conversations');const me=cs.find(c=>c.cid===State.currentCid);if(me)setTok(me.tokens)}

    // ---- conversation sidebar ----
    async function loadConvs(){const cs=await api('/conversations');const q=($('#convsrch').value||'').toLowerCase();
      const el=$('#convlist');const groups={};
      cs.filter(c=>!q||(c.title||'').toLowerCase().includes(q)).forEach(c=>{(groups[c.project]=groups[c.project]||[]).push(c)});
      let h='';for(const proj of Object.keys(groups)){h+=`<div class="projhead">${esc(proj)}</div>`;
        h+=groups[proj].map(c=>`<div class="conv ${c.cid===State.currentCid?'active':''}" data-c="${c.cid}"><span class="ct" title="${esc(c.title||'')}">${esc(c.title||'New chat')}</span><span class="ca"><button data-rn="${c.cid}" title="rename">✎</button><button data-ar="${c.cid}" title="archive">🗄</button><button data-dl="${c.cid}" title="delete">🗑</button></span></div>`).join('')}
      el.innerHTML=h||'<div class="empty">no conversations</div>';
      $$('#convlist .conv').forEach(d=>d.querySelector('.ct').onclick=()=>openConv(d.dataset.c));
      $$('#convlist [data-rn]').forEach(b=>b.onclick=async e=>{e.stopPropagation();const t2=prompt('Rename conversation:');if(t2){await post(`/conversations/${b.dataset.rn}/rename`,{title:t2});loadConvs()}});
      $$('#convlist [data-ar]').forEach(b=>b.onclick=async e=>{e.stopPropagation();await post(`/conversations/${b.dataset.ar}/archive`,{archived:true});toast('info','Archived','');loadConvs()});
      $$('#convlist [data-dl]').forEach(b=>b.onclick=async e=>{e.stopPropagation();if(confirm('Delete this conversation?')){await del(`/conversations/${b.dataset.dl}`);if(State.currentCid===b.dataset.dl)State.currentCid=null;loadConvs();if(!State.currentCid)chat.innerHTML=''}});
    }
    async function openConv(cid){State.currentCid=cid;chat.innerHTML='';const ms=await api(`/conversations/${cid}/messages`);
      ms.forEach(m=>m.role==='user'?(lastUser=m.content,addMsg('user',m.content)):addMsg('ai',m.content,lastUser));
      refreshTok();loadConvs();renderChips()}
    async function newChat(){const r=await post('/conversations',{project:'General'});State.currentCid=r.cid;chat.innerHTML='';clearAttach();loadConvs();renderChips();$('#ci').focus()}

    // ---- chips / templates / suggestions ----
    function renderChips(){const empty=chat.children.length===0;
      $('#chips').innerHTML=(empty?TEMPLATES:TEMPLATES.slice(0,4)).map((x,i)=>`<span class="chip" data-tp="${i}">${x.l}</span>`).join('');
      $$('#chips [data-tp]').forEach(c=>c.onclick=()=>{$('#ci').value=TEMPLATES[+c.dataset.tp].t;$('#ci').focus()})}

    // ---- attachments (multi-file, progress bar, download chips) ----
    function clearAttach(){attached=[];renderAttach()}
    function renderAttach(){const el=$('#attachbar');if(!el)return;
      el.innerHTML=attached.map((a,i)=>`<span class="attcard big">${fileIcon(a.filename)} <b>${esc(a.filename)}</b> <span class="muted">${(a.size/1024).toFixed(0)}KB · ${a.chars} chars</span> <span class="x" data-rm="${i}">✕</span></span>`).join('');
      $$('#attachbar [data-rm]').forEach(b=>b.onclick=()=>{attached.splice(+b.dataset.rm,1);renderAttach()})}
    function uploadFile(file){const bar=$('#attachbar');
      const prog=document.createElement('span');prog.className='attcard big';
      prog.innerHTML=`${fileIcon(file.name)} <b>${esc(file.name)}</b> <span class="prog" style="display:inline-block;width:90px;height:8px;vertical-align:middle"><i style="width:0"></i></span> <span class="pp">0%</span>`;
      bar.appendChild(prog);
      const xhr=new XMLHttpRequest();xhr.open('POST','/api/upload');
      xhr.upload.onprogress=e=>{if(e.lengthComputable){const p=Math.round(e.loaded/e.total*100);const i=prog.querySelector('.prog i');if(i)i.style.width=p+'%';const pp=prog.querySelector('.pp');if(pp)pp.textContent=p+'%'}};
      xhr.onload=()=>{try{const r=JSON.parse(xhr.responseText);if(r.ok){attached.push(r);renderAttach();toast('success','File attached',`${r.filename} · ${r.chars} chars`)}else{prog.remove();toast('error','Upload failed',r.error||'')}}catch(e){prog.remove();toast('error','Upload failed','')}};
      xhr.onerror=()=>{prog.remove();toast('error','Upload failed','network error')};
      const fd=new FormData();fd.append('file',file);xhr.send(fd);usage('upload')}
    $('#attach').onclick=()=>$('#fileinp').click();
    $('#fileinp').onchange=e=>{[...e.target.files].forEach(uploadFile);e.target.value=''};
    chat.addEventListener('dragover',e=>{e.preventDefault();chat.classList.add('over')});
    chat.addEventListener('dragleave',()=>chat.classList.remove('over'));
    chat.addEventListener('drop',e=>{e.preventDefault();chat.classList.remove('over');[...e.dataTransfer.files].forEach(uploadFile)});

    // ---- Perception & Control chat commands ("where am i", "move mouse to X,Y", "read this") ----
    async function tryPCCommand(v){
      const s=v.trim().toLowerCase();
      if(/^(where am i|what('?s| is)? open|list windows|active window)\b/.test(s)){
        addMsg('user',v);const r=await api('/control/awareness');
        const t='**Active window:** '+esc(r.active.title)+' ('+r.active.process+')\n\n'+
          '**Open windows ('+r.windows.length+'):**\n'+r.windows.slice(0,15).map(w=>'- '+esc(w.title)+' _('+w.process+')_').join('\n')+
          '\n\n**Screen:** '+r.screen.primary.w+'×'+r.screen.primary.h+' @ '+r.screen.dpi+'dpi (scale '+r.screen.scale+')';
        addMsg('ai',t);return true}
      let m=s.match(/^move (?:the )?(?:mouse|cursor) to \(?(\d+)[ ,]+(\d+)/);
      if(m){addMsg('user',v);await post('/control/mouse',{action:'move',x:+m[1],y:+m[2]});addMsg('ai','🖱 moved mouse to '+m[1]+', '+m[2]);return true}
      m=s.match(/^(double[- ]?)?click (?:at )?\(?(\d+)[ ,]+(\d+)/);
      if(m){addMsg('user',v);await post('/control/mouse',{action:'click',x:+m[2],y:+m[3],double:!!m[1]});addMsg('ai','🖱 '+(m[1]?'double-':'')+'clicked '+m[2]+', '+m[3]);return true}
      m=s.match(/^(?:click|press) (?:the )?["']?(.+?)["']? (?:button|element|link)$/);
      if(m){addMsg('user',v);const r=await post('/control/click-element',{name:m[1]});addMsg('ai',r.ok?('🖱 clicked "'+esc(r.clicked)+'"'):('❌ '+(r.error||'not found')));return true}
      if(/^(read|describe)( this| it)?$/.test(s)&&attached.length){
        addMsg('user',v);const a=attached[0];const out=addMsg('ai','⏳ reading…');
        const r=await post('/understand',{path:a.filename});
        out.firstChild.innerHTML=mdRender(r.description||r.text||'(nothing detected)');attached=[];renderAttach();return true}
      return false}

    // ---- send (chat / exec) ----
    const execJobs={};
    async function send(){let v=$('#ci').value.trim();if(!v&&!attached.length)return;
      if(!State.currentCid)await newChat();
      if(await tryPCCommand(v)){$('#ci').value='';renderChips();return}
      const isAr=/[؀-ۿ]/.test(v);
      if(v.startsWith('!')){const cmd=v.slice(1).split(/&&|\|\|/).map(s=>s.trim().replace(/^!/,'')).filter(Boolean).join(' ; ');addMsg('user',v);$('#ci').value='';
        const out=addMsg('ai','');out.firstChild.textContent='⌨️ $ '+cmd+'\n';
        const r=await execCommand(cmd);
        if(r&&r.job)execJobs[r.job]=out; else out.firstChild.textContent+=(r===null?'(cancelled)':('error: '+((r&&r.error)||'failed')));
        renderChips();return}
      let context='',markers='';
      if(attached.length){
        context=attached.map(a=>`### File: ${a.filename}\n${a.text}`).join('\n\n');
        markers=attached.map(a=>`⟦file:${a.filename}|${a.size}⟧`).join('')+'\n';}
      lastUser=v;addMsg('user',(isAr?'🇸🇦 ':'')+markers+v);$('#ci').value='';
      const body={prompt:markers+v,model:$('#cm').value,cid:State.currentCid};
      if(context)body.context=context;
      if(comparing)body.target=$('#cm2').value;
      if(ragOn)body.rag=true;
      if(deepThink)body.deepthink=true;
      if(webSearch)body.websearch=true;
      post('/chat-send',body);usage('chat');attached=[];renderAttach();renderChips()}
    $('#cs').onclick=send;$('#ci').addEventListener('keydown',e=>{if(e.key==='Enter')send()});

    // ---- model comparison ----
    $('#cmpbtn').onclick=()=>{comparing=!comparing;$('#cm2').style.display=comparing?'':'none';$('#cmpbtn').classList.toggle('p',comparing);toast('info',comparing?'Compare mode on':'Compare mode off','')};
    // ---- RAG toggle ----
    $('#ragbtn').onclick=async()=>{ragOn=!ragOn;$('#ragbtn').classList.toggle('p',ragOn);
      if(ragOn){const st=await api('/kb/status');toast(st.docs?'info':'error',ragOn?'Knowledge Base ON':'',st.docs?`searching ${st.docs} docs · ${st.chunks} chunks`:'No documents yet — add some in Knowledge');}
      else toast('info','Knowledge Base off','')};
    // ---- DeepThink toggle ----
    $('#dtbtn').onclick=()=>{deepThink=!deepThink;$('#dtbtn').classList.toggle('p',deepThink);toast('info',deepThink?'DeepThink on':'DeepThink off',deepThink?'replies reason step by step':'')};
    // ---- Web Search toggle ----
    $('#wsbtn').onclick=()=>{webSearch=!webSearch;$('#wsbtn').classList.toggle('p',webSearch);toast('info',webSearch?'Web Search on':'Web Search off',webSearch?'answers use live web results':'')};
    // ---- voice output toggle ----
    $('#spkbtn').onclick=()=>{speakOn=!speakOn;$('#spkbtn').classList.toggle('p',speakOn);toast('info',speakOn?'Auto-speak on':'Auto-speak off',speakOn?'replies will be read aloud':'')};

    // ---- live preview ----
    $('#prev').onclick=()=>{const v=$('#ci').value;let h='';
      if(attached.length)h+='<div class="attwrap">'+attached.map(a=>attHTML(a.filename,a.size)).join('')+'</div>';
      h+='<div class="msg user" style="max-width:100%;align-self:stretch">'+(v.trim()?mdRender(v):'<span class="muted">(nothing to preview)</span>')+'</div>';
      $('#prevbody').innerHTML=h;$('#preview').classList.add('open')};

    // ---- voice input (LOCAL speech-to-text via Whisper) ----
    $('#mic').onclick=()=>dictate('#ci','#mic');

    // ---- export ----
    $('#expbtn').onclick=()=>$('#exppop').classList.toggle('open');
    $$('#exppop [data-x]').forEach(d=>d.onclick=async()=>{$('#exppop').classList.remove('open');usage('export');
      if(d.dataset.x==='pdf'){window.open('/api/chat-export-pdf/'+State.currentCid,'_blank');return}
      const ms=await api(`/conversations/${State.currentCid}/messages`);let blob,name;
      if(d.dataset.x==='json'){blob=JSON.stringify(ms,null,2);name='chat.json'}
      else if(d.dataset.x==='md'){blob=ms.map(m=>`**${m.role}:** ${m.content}`).join('\n\n');name='chat.md'}
      else{blob=ms.map(m=>`[${m.role}] ${m.content}`).join('\n\n');name='chat.txt'}
      const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([blob],{type:'text/plain'}));a.download=name;a.click();usage('export')});

    // ---- in-chat search ----
    $('#insrch').oninput=e=>{const q=e.target.value.toLowerCase();
      $$('#chat .msg').forEach(m=>{const hit=!q||m.textContent.toLowerCase().includes(q);m.style.display=hit?'':'none';
        m.style.outline=q&&hit?'1px solid var(--accent)':'none'})};

    // ---- clear ----
    $('#cc').onclick=()=>{if(State.currentCid&&confirm('Clear this conversation?'))post('/chat-clear',{cid:State.currentCid}).then(()=>{chat.innerHTML='';renderChips();refreshTok()})};
    $('#newchat').onclick=newChat;
    $('#convsrch').oninput=loadConvs;

    // ---- streaming ----
    const onChat=m=>{if(comparing&&m.compare){const last=chat.lastChild;
        const wrap=addMsg('ai','');wrap.firstChild.remove();
        const div=document.createElement('div');div.className='cmp';
        div.innerHTML=`<div class="col"><h4>${esc(m.compare.a.model)}</h4>${mdRender(m.compare.a.text)}</div><div class="col"><h4>${esc(m.compare.b.model)}</h4>${mdRender(m.compare.b.text)}</div>`;
        wrap.appendChild(div);refreshTok();return}
      if(comparing)return; // ignore slotted streams during compare
      if(m.ev==='start'){curAI=addMsg('ai','');curAI.classList.add('streaming')}
      else if(m.ev==='token'){if(!curAI){curAI=addMsg('ai','');curAI.classList.add('streaming')}curAI.firstChild.textContent+=m.text;chat.scrollTop=chat.scrollHeight}
      else if(m.ev==='end'){if(curAI){curAI.classList.remove('streaming');const sp=curAI.firstChild;const txt=sp.textContent;sp.innerHTML=mdRender(txt);
          if(m.sources&&m.sources.length){const s=document.createElement('div');s.className='sources';
            s.innerHTML='📚 '+m.sources.map(x=>`<span class="tag on">${esc(x.doc)} · ${x.score}</span>`).join(' ')+' ';
            const uq=lastUser,at=txt;const fb=document.createElement('button');fb.className='btn sm';fb.textContent='👍 helpful → train';
            fb.onclick=()=>post('/training/save',{user:uq,assistant:at}).then(r=>{toast(r.added?'success':'info',r.added?'Saved — the model will learn this':'Already in training set','');fb.textContent='✓ added to training';fb.disabled=true});
            s.appendChild(fb);curAI.appendChild(s)}
          if(m.tokens&&m.secs){const st=document.createElement('div');st.className='msgstat';st.textContent=`⚡ ${m.tokens} tokens · ${(m.tokens/m.secs).toFixed(1)} tok/s · ${m.secs}s`;curAI.appendChild(st)}
          if(speakOn&&txt.trim())post('/tts',{text:txt})}
        curAI=null;if(m.tokens)refreshTok();loadConvs()}
      else if(m.ev==='error'){if(curAI)curAI.classList.remove('streaming');addMsg('ai','⚠ '+m.text);curAI=null}};
    const onTerm=m=>{const out=execJobs[m.job];if(out&&!m.line.startsWith('$'))out.firstChild.textContent+=m.line+'\n',chat.scrollTop=chat.scrollHeight};

    // ---- init ----
    (async()=>{const list=await api('/models');const cur=State.settings.default_local_model||'llama3.1:8b';
      const opt=(m,sel)=>`<option value="${esc(m.name)}" ${sel?'selected':''}>${esc(m.name)}${m.tags&&m.tags.length?' · '+m.tags.join(', '):''}</option>`;
      const usable=list.filter(m=>!(m.tags||[]).includes('embedding'));
      $('#cm').innerHTML=usable.map(m=>opt(m,m.name===cur)).join('');
      $('#cm2').innerHTML=usable.map(m=>opt(m,false)).join('');
      const cs=await api('/conversations');
      if(State.currentCid&&cs.find(c=>c.cid===State.currentCid))openConv(State.currentCid);
      else if(cs.length)openConv(cs[0].cid);
      else{await newChat()}
      loadConvs()})();
    return [bus.on('chat',onChat),bus.on('term',onTerm)];
  }
  return {html,mount};
}
