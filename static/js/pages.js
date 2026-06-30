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

    // ---- send (chat / exec) ----
    const execJobs={};
    async function send(){let v=$('#ci').value.trim();if(!v&&!attached.length)return;
      if(!State.currentCid)await newChat();
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

function Models(){
  const html=`${card('Local Models (Ollama)',`<div id="ml"><div class="empty">…</div></div>`,`<button class="btn sm" id="rf">↻ ${t('refresh')}</button>`)}
   <div class="mt">${card('Media & Generation <span class="tag">image · video · audio</span>',`<div id="mm"><div class="empty">…</div></div>`)}</div>`;
  async function load(){const list=await api('/models');const el=$('#ml');if(!el)return;
    el.innerHTML=list.map(m=>`<div class="row"><span class="name" title="${esc(m.name)}">${esc(m.name)}</span>${tagHTML(m.tags)}<span class="tag">${m.size_gb}GB</span>${m.loaded?`<span class="tag run">${m.vram_gb}GB VRAM</span><button class="btn sm danger" data-u="${esc(m.name)}">${t('unload')}</button>`:`<button class="btn sm" data-l="${esc(m.name)}">${t('load')}</button>`}</div>`).join('');
    $$('#ml [data-l]').forEach(b=>b.onclick=()=>{post('/models/load',{model:b.dataset.l});toast('info','Loading',b.dataset.l)});
    $$('#ml [data-u]').forEach(b=>b.onclick=()=>{post('/models/stop',{model:b.dataset.u});toast('info','Unloading',b.dataset.u)});}
  async function loadMedia(){const list=await api('/media-models');const el=$('#mm');if(!el)return;
    el.innerHTML=list.length?list.map(m=>`<div class="row"><span class="name" title="${esc(m.name)}">${esc(m.name)}</span>${tagHTML(m.tags)}<span class="tag">${m.size_gb}GB</span></div>`).join(''):'<div class="empty">no media models found</div>';}
  function mount(){load();loadMedia();$('#rf').onclick=()=>{load();loadMedia()};const iv=setInterval(load,8000);return [()=>clearInterval(iv),bus.on('models',load)]}
  return {html,mount};
}

function Tools(){
  const html=`<div class="grid g2">
    ${card('Open WebUI Tools',`<div id="tl"><div class="empty">…</div></div>`)}
    ${card('Open WebUI Config',`<div id="oc"><div class="empty">…</div></div>`)}
   </div>
   ${card('Toolkit Quick Actions',`<div class="qa" id="tk"></div>`,'')}`;
  async function loadOwui(){const o=await api('/owui');const tl=$('#tl'),oc=$('#oc');if(!tl)return;
    if(o.error){tl.innerHTML='<div class="empty">OWUI offline</div>';oc.innerHTML='<div class="empty">—</div>';return}
    const att=new Set((o.models.find(m=>m.id==='smart-tools')||{tools:[]}).tools);
    tl.innerHTML=o.tools.map(x=>`<div class="row"><span class="name">${esc(x.name)}</span><button class="sw ${att.has(x.id)?'on':''}" data-t="${x.id}"></button></div>`).join('')||'<div class="empty">no tools</div>';
    $$('#tl [data-t]').forEach(b=>b.onclick=()=>{const on=!b.classList.contains('on');b.classList.toggle('on',on);post('/tools/toggle',{tool_id:b.dataset.t,on})});
    oc.innerHTML=o.models.filter(m=>['smart-tools','tools-assistant'].includes(m.id)).map(m=>
      `<div class="metarow"><span>${esc(m.name)}</span><span class="tag ${m.fc==='native'?'on':'err'}">${m.fc||'default'}</span></div>`).join('')+
      `<div class="metarow"><span class="mut">Code Interpreter</span><span class="tag ${o.code_interpreter?'err':'on'}">${o.code_interpreter?'ON':'off'}</span></div>
       <button class="btn p mt" id="apply" style="width:100%">Apply recommended config</button>`;
    const ap=$('#apply');if(ap)ap.onclick=()=>{toast('info','Applying…','');post('/owui/apply-recommended').then(()=>loadOwui())};}
  async function loadTk(){const items=await api('/toolkit/list');const el=$('#tk');if(!el)return;
    el.innerHTML=items.map(i=>`<button data-k="${i.key}"><span class="qi">${i.icon}</span><span class="qt">${esc(i.name)}</span><span class="qd">${esc(i.desc)}</span></button>`).join('');
    $$('#tk button').forEach(b=>b.onclick=()=>{const k=b.dataset.k;
      if(k==='video'){location.hash='#/video';return}
      const txt=prompt(k==='speak'?'Text to speak:':k==='translate'?'Text to translate:':k==='ocr'?'Image path:':'Argument (optional):','');
      if(txt===null)return;post('/toolkit/'+(k==='speak'?'speak':k),k==='speak'?{text:txt}:{prompt:txt}).then(()=>toast('info',i_name(items,k)+' started',''))});}
  function i_name(items,k){const x=items.find(i=>i.key===k);return x?x.name:k}
  function mount(){loadOwui();loadTk();return []}
  return {html,mount};
}

function Video(){
  const html=`<div class="grid g2">
    ${card('🎬 Generate Video (LTX local)',`
      <label class="f">${t('prompt')}</label><textarea class="t" id="vp" rows="3">a cinematic drone shot over a neon city at night</textarea>
      <div class="grid g2 mt">
        <div><label class="f">${t('model')}</label><select class="t" id="vc"><option value="">LTX 2B (fast)</option><option value="ltxv-13b-0.9.7-dev.safetensors">LTX 13B (HQ)</option></select></div>
        <div><label class="f">${t('frames')}</label><input class="t" id="vl" value="97"></div>
        <div><label class="f">${t('steps')}</label><input class="t" id="vs" value="30"></div>
        <div><label class="f">FPS</label><input class="t" id="vf" value="24"></div>
      </div>
      <button class="btn p mt" id="vg" style="width:100%">🎬 ${t('generate')}</button>`)}
    ${card('🖼️ Generate Image (local)',`
      <label class="f">${t('prompt')}</label><textarea class="t" id="ip" rows="3">a serene mountain lake at sunrise, photorealistic, golden light</textarea>
      <div class="flex mt" style="gap:8px;align-items:flex-end">
        <div style="flex:1"><label class="f">${t('model')}</label><select class="t" id="im"><option value="sdxl">SDXL (balanced)</option><option value="flux-schnell">Flux schnell (fast)</option><option value="flux-dev">Flux dev (HQ)</option></select></div>
        <button class="btn p" id="ig" data-tip="Generate an image locally (ComfyUI)">🖼️ ${t('generate')}</button>
      </div>
      <div id="imgout" class="imgout mt"><div class="empty">your image will appear here</div></div>`)}
   </div>
   <div class="grid g2 mt">
     ${card('ComfyUI Live Status <span class="tag">/queue + output</span>',`<div id="cstat"><div class="empty">…</div></div>`)}
     ${card(t('processes'),`<div id="vproc"><div class="empty">${t('no_proc')}</div></div>`)}
   </div>`;
  async function loadComfy(){const c=await api('/comfy/status');const el=$('#cstat');if(!el)return;
    el.innerHTML=`<div class="metarow"><span class="mut">ComfyUI</span><span class="tag ${c.online?'on':'err'}">${c.online?'online':'offline'}</span></div>`+
      meta('Queue running',c.queue_running)+meta('Queue pending',c.queue_pending)+
      meta('Output files',c.outputs)+meta('Latest output',c.last_output||'—')+
      (c.queue_running>0?`<div class="bar mt"><i style="width:100%;animation:none;background:linear-gradient(90deg,var(--accent),var(--accent3))"></i></div><div class="muted" style="font-size:11px;margin-top:5px">🎬 generating…</div>`:'');}
  async function loadProc(){const list=(await api('/processes')).reverse();const el=$('#vproc');if(!el)return;
    el.innerHTML=list.length?list.map(j=>{const c=['running','starting'].includes(j.status)?'run':j.status==='error'?'err':j.status==='done'?'on':'';
      return `<div class="row"><span class="name" title="${esc(j.name)}">${esc(j.name)}</span><span class="tag ${c}">${j.status}</span>${['running','starting'].includes(j.status)?`<button class="btn sm danger" data-s="${j.id}">${t('stop')}</button>`:''}</div>`}).join(''):`<div class="empty">${t('no_proc')}</div>`;
    $$('#vproc [data-s]').forEach(b=>b.onclick=()=>post('/processes/'+b.dataset.s+'/stop'));}
  function mount(){loadProc();loadComfy();
    $('#vg').onclick=()=>{post('/toolkit/video',{prompt:$('#vp').value,ckpt:$('#vc').value,length:+$('#vl').value,steps:+$('#vs').value,fps:+$('#vf').value});toast('info','Video generation started','watch ComfyUI status & processes')};
    $('#ig').onclick=async()=>{const p=$('#ip').value.trim();if(!p)return;
      const r=await post('/toolkit/image',{prompt:p,model:$('#im').value});
      if(!r||!r.ok)return;
      toast('info','Image generation started',r.model);loadProc();
      const out=$('#imgout');out.innerHTML='<div class="empty"><span class="spin">⏳</span> generating…</div>';
      const url=r.file;let tries=0;
      const poll=setInterval(()=>{tries++;const im=new Image();
        im.onload=()=>{clearInterval(poll);out.innerHTML='';
          const e=document.createElement('img');e.src=url;e.className='genimg';out.appendChild(e);
          const a=document.createElement('a');a.href=url;a.download='nova-image.png';a.className='btn sm mt';a.textContent='⬇ download';out.appendChild(a);};
        im.src=url+'?t='+Date.now();
        if(tries>45){clearInterval(poll);out.innerHTML='<div class="empty">still generating — check Processes below</div>'}},2000);};
    const iv=setInterval(loadProc,4000);const iv2=setInterval(loadComfy,3000);
    return [()=>clearInterval(iv),()=>clearInterval(iv2),bus.on('job',loadProc)]}
  return {html,mount};
}

function Training(){
  const html=`<div class="grid g4" style="margin-bottom:16px">
     ${statCard('s_base',t('base'),'📘')}${statCard('s_learn',t('learned'),'🌱')}${statCard('s_comb',t('combined'),'🧬')}
     <div class="card"><div class="bd"><div class="kpi"><div class="ic">🤖</div><div class="stat"><span class="v" id="s_nova" style="font-size:17px">…</span><span class="l">nova-local · last <span id="s_last">—</span></span></div></div></div></div>
   </div>
   ${card('Training Pipeline <span class="tag" id="trun">idle</span>',`
      <div class="prog-lbl"><span id="pstep">idle</span><span id="ppct">0%</span></div>
      <div class="prog idle" id="pbar"><i style="width:0"></i></div>
      <div id="tsub" class="tsub" style="display:none">
        <div class="prog-lbl"><span id="tsubstep">—</span><span id="tsubeta" class="muted"></span></div>
        <div class="prog" id="tsubbar"><i style="width:0"></i></div>
      </div>
      <div class="tgpu" id="tgpu" style="display:none"></div>
      <div id="terr" class="terr" style="display:none"></div>
      <div class="flex wrap mt" style="gap:8px">
        <button class="btn p" id="hr" data-tip="Harvest new chats, then retrain nova-local">🎓 Start Training</button>
        <button class="btn danger" id="tstop" data-tip="Stop training immediately" style="display:none">⏹ Stop</button>
        <button class="btn" id="tpause" data-tip="Pause (suspend) the training process" style="display:none">⏸ Pause</button>
        <button class="btn p" id="tresume" data-tip="Resume the paused training" style="display:none">▶ Resume</button>
        <button class="btn" id="hv">🌾 ${t('harvest')} only</button>
        <button class="btn" id="upbtn">⬆ Upload dataset (.jsonl)</button>
        <input type="file" id="dsfile" accept=".jsonl" style="display:none">
        <span id="hs" class="muted"></span>
      </div>`)}
   <div class="grid g2 mt">
     ${card('Live Training Log',`<div class="logbox" id="tlog">…</div>`,`<button class="btn sm" id="lr">↻</button>`)}
     ${card('Test nova-local',`<input class="t" id="tq" value="Who are you and what GPU am I using?"><button class="btn p mt" id="tb" style="width:100%">${t('ask')}</button><div class="logbox mt" id="tr" style="max-height:150px">—</div>`)}
   </div>
   ${card('Training History',`<div id="thist"><div class="empty">no runs recorded yet</div></div>`)}`;
  async function loadStatus(){const s=await api('/training/status');set('s_base',s.base);set('s_learn',s.learned);set('s_comb',s.combined);
    const nv=$('#s_nova');if(nv)nv.innerHTML=s.nova_installed?'<span style="color:var(--ok)">installed ✓</span>':'<span style="color:var(--err)">not built</span>'}
  function fmtDur(s){s=Math.max(0,Math.round(s));const m=Math.floor(s/60),h=Math.floor(m/60);if(h)return h+'h '+(m%60)+'m';if(m)return m+'m '+(s%60)+'s';return s+'s'}
  async function loadProgress(){const p=await api('/learn/progress');State.training=(p.status==='running'||p.status==='paused');const bar=$('#pbar');if(!bar)return;
    const MAP={idle:'mut',running:'run',paused:'warn',stopped:'err',completed:'on',error:'err'};const cls=MAP[p.status]||'mut';
    const tr=$('#trun');if(tr){tr.className='tag '+cls+(p.status==='running'?' live':'');tr.textContent=p.status}
    $('#ppct').textContent=p.percent+'%';bar.querySelector('i').style.width=p.percent+'%';
    bar.className='prog'+((p.status==='running'||p.status==='paused')?'':' idle');
    $('#pstep').textContent=p.name?('Step '+p.step+' of '+p.total+' — '+p.name.replace(/^\d+\.\s*/,'')):(p.status==='completed'?'✓ Completed':(p.status==='stopped'?'⏹ Stopped by user':(p.status==='error'?'✕ Error — see log':'idle')));
    const sub=p.train,ts=$('#tsub');
    if(sub&&sub.total&&(p.status==='running'||p.status==='paused')){ts.style.display='';
      $('#tsubbar').querySelector('i').style.width=(sub.percent||0)+'%';
      $('#tsubstep').textContent='🧠 LoRA · step '+sub.step+' / '+sub.total+' ('+(sub.percent||0)+'%)'+(sub.loss!=null?' · loss '+sub.loss:'')+(sub.epoch!=null?' · epoch '+sub.epoch.toFixed(1):'');
      $('#tsubeta').textContent=p.status==='paused'?'paused':(sub.eta!=null?('ETA '+fmtDur(sub.eta)):'');}
    else ts.style.display='none';
    const g=p.gpu,ge=$('#tgpu');
    if(g&&(p.status==='running'||p.status==='paused')){ge.style.display='';
      ge.innerHTML=`<span class="gpuchip">🎮 ${Math.round(g.util)}% util</span><span class="gpuchip">🌡️ ${Math.round(g.temp)}°C</span><span class="gpuchip">💾 ${(g.vram_used/1024).toFixed(1)} / ${(g.vram_total/1024).toFixed(0)} GB</span><span class="gpuchip">⚡ ${Math.round(g.power)}W</span>`;}
    else ge.style.display='none';
    const ee=$('#terr');if(ee){if(p.status==='error'&&p.error){ee.style.display='';ee.textContent='⚠ '+p.error}else ee.style.display='none'}
    const run=p.status==='running',pau=p.status==='paused';
    $('#hr').style.display=(run||pau)?'none':'';
    $('#tstop').style.display=(run||pau)?'':'none';
    $('#tpause').style.display=run?'':'none';
    $('#tresume').style.display=pau?'':'none';}
  async function loadLog(){const r=await api('/training/log?lines=160');const el=$('#tlog');if(el){el.textContent=r.log||'(no log yet)';el.scrollTop=el.scrollHeight}}
  async function loadHist(){const h=await api('/training/history');const el=$('#thist');if(!el)return;
    el.innerHTML=h.length?h.map(r=>`<div class="histitem"><span class="tag ${r.ok?'on':'err'}">${r.ok?'✓':'✗'}</span><span class="mono">${new Date(r.ended*1000).toLocaleString()}</span><span class="spacer"></span><span class="muted">${r.steps}/7 steps · ${r.combined} examples · ${r.note}</span></div>`).join(''):'<div class="empty">no runs recorded yet</div>';
    if(h[0])$('#s_last').textContent=new Date(h[0].ended*1000).toLocaleDateString()}
  function mount(){loadStatus();loadProgress();loadLog();loadHist();
    $('#hv').onclick=async e=>{e.target.disabled=true;$('#hs').innerHTML='<span class="spin"></span> harvesting…';const r=await post('/learn/harvest');$('#hs').textContent=r.ok?`+${(r.result||'').replace('RESULT ','')}`:'failed';e.target.disabled=false;loadStatus()};
    $('#hr').onclick=async()=>{const r=await post('/learn/retrain');if(r.ok){toast('info','Training started','live progress below');usage('train')}else toast('error','Cannot start',r.error||'');setTimeout(()=>{loadProgress();loadLog()},1500)};
    $('#upbtn').onclick=()=>$('#dsfile').click();
    $('#dsfile').onchange=async e=>{const f=e.target.files[0];if(!f)return;const fd=new FormData();fd.append('file',f);
      const r=await fetch('/api/training/upload-dataset',{method:'POST',body:fd}).then(x=>x.json());
      toast(r.ok?'success':'error',r.ok?`Added ${r.added} examples`:'Upload failed',r.skipped?`${r.skipped} skipped`:'');loadStatus()};
    $('#tstop').onclick=async()=>{if(!confirm('Stop the training now? Progress in the current step will be lost.'))return;await post('/learn/stop',{});toast('info','Stopping training','');setTimeout(loadProgress,500)};
    $('#tpause').onclick=async()=>{await post('/learn/pause',{});toast('info','Training paused','resume any time');setTimeout(loadProgress,400)};
    $('#tresume').onclick=async()=>{await post('/learn/resume',{});toast('info','Training resumed','');setTimeout(loadProgress,400)};
    $('#tb').onclick=async()=>{const q=$('#tq').value.trim();if(!q)return;$('#tr').textContent='thinking…';await post('/chat-send',{prompt:q,model:'nova-local'})};
    $('#lr').onclick=loadLog;
    const iv=setInterval(()=>{loadProgress();loadLog()},2000);
    let acc='';const u=bus.on('chat',m=>{if(m.ev==='start'){acc='';$('#tr').textContent=''}else if(m.ev==='token'){acc+=m.text;$('#tr').textContent=acc}});
    const u2=bus.on('training_done',()=>{loadStatus();loadHist();loadProgress();toast('success','Training finished','model updated')});
    return [()=>clearInterval(iv),u,u2];
  }
  return {html,mount};
}
function statCard(id,lbl,ic){return `<div class="card"><div class="bd"><div class="kpi"><div class="ic">${ic}</div><div class="stat"><span class="v" id="${id}">0</span><span class="l">${lbl} examples</span></div></div></div></div>`}

function ScreenStudio(){
  const html=`<div class="grid g2" style="align-items:start">
    ${card('🎥 Record Screen <span class="tag" id="recstate">idle</span>',`
      <div class="flex wrap" style="gap:8px;align-items:flex-end">
        <div><label class="f">Mode</label><select class="t" id="rmode"><option value="full">Full screen</option><option value="region">Region (left,top,w,h)</option></select></div>
        <div><label class="f">FPS</label><input class="t" id="rfps" value="15" style="width:70px"></div>
        <div id="rregwrap" style="display:none"><label class="f">Region</label><input class="t" id="rregion" placeholder="0,0,1280,720"></div>
        <button class="btn p" id="recbtn">⏺ Start recording</button>
      </div>
      <div id="recprev" class="imgout mt" style="display:none"></div>
      <video id="recvideo" class="genimg mt" controls style="display:none;width:100%"></video>`)}
    ${card('🧠 Read & Understand Screen',`
      <div class="flex wrap" style="gap:8px">
        <button class="btn" id="shotbtn">📸 Screenshot</button>
        <button class="btn" id="ocrbtn">🔤 Read text (OCR)</button>
        <button class="btn p" id="seebtn">👁 What's on my screen?</button>
        <label class="atog"><input type="checkbox" id="tokb"> 📚 to KB</label>
      </div>
      <div id="shotout" class="imgout mt" style="display:none"></div>
      <div id="screadout" class="logbox mt" style="display:none;max-height:220px;white-space:pre-wrap"></div>`)}
   </div>
   ${card('🎬 Recordings',`<div id="reclist"><div class="empty">no recordings yet</div></div>`)}`;
  let elapsed=null;
  function setRec(on,secs){const s=$('#recstate');if(s){s.className='tag '+(on?'run live':'');s.textContent=on?('recording '+(secs||0)+'s'):'idle'}
    const b=$('#recbtn');if(b){b.innerHTML=on?'⏹ Stop recording':'⏺ Start recording';b.classList.toggle('danger',on)}}
  async function pollRec(){const st=await api('/screen/record/status');State.recording=!!st.recording;setRec(st.recording,Math.round(st.seconds||0));
    const pv=$('#recprev');if(st.recording&&pv){pv.style.display='';const im=new Image();im.className='genimg';im.onload=()=>{pv.innerHTML='';pv.appendChild(im)};
      const s=await api('/screen/shot').catch(()=>null);if(s&&s.file)im.src=s.file+'?t='+Date.now()}}
  async function loadRecs(){const r=await api('/screen/recordings');const el=$('#reclist');if(!el)return;
    el.innerHTML=(r.items&&r.items.length)?r.items.map(v=>`<div class="row"><span class="name">${esc(v.name)}</span><span class="muted">${v.size_kb}KB</span><button class="btn sm" data-play="${v.file}">▶ play</button><a class="btn sm" href="${v.file}" download>⬇</a></div>`).join(''):'<div class="empty">no recordings yet</div>';
    $$('#reclist [data-play]').forEach(b=>b.onclick=()=>{const v=$('#recvideo');v.style.display='';v.src=b.dataset.play;v.scrollIntoView({behavior:'smooth'});v.play()})}
  function mount(){loadRecs();pollRec();
    $('#rmode').onchange=e=>{$('#rregwrap').style.display=e.target.value==='region'?'':'none'};
    $('#recbtn').onclick=async()=>{const st=await api('/screen/record/status');
      if(st.recording){const r=await post('/screen/record/stop');setRec(false);if(r.file){const v=$('#recvideo');v.style.display='';v.src=r.file+'?t='+Date.now()}$('#recprev').style.display='none';toast('success','Recording saved',r.seconds+'s');loadRecs()}
      else{const mode=$('#rmode').value;const body={mode,fps:+$('#rfps').value};if(mode==='region'){const p=($('#rregion').value||'').split(',').map(x=>+x.trim());if(p.length===4)body.region=p}
        const r=await post('/screen/record/start',body);if(r.ok){setRec(true,0);toast('info','Recording started',mode)}}};
    $('#shotbtn').onclick=async()=>{const r=await post('/screen/shot');if(r.file){const o=$('#shotout');o.style.display='';o.innerHTML='';const im=document.createElement('img');im.className='genimg';im.src=r.file+'?t='+Date.now();o.appendChild(im)}};
    $('#ocrbtn').onclick=async()=>{const o=$('#screadout');o.style.display='';o.textContent='⏳ reading…';const r=await post('/screen/read',{to_kb:$('#tokb').checked});o.textContent=r.text||'(no text found)';if(r.indexed)toast('success','Added to Knowledge Base','')};
    $('#seebtn').onclick=async()=>{const o=$('#screadout');o.style.display='';o.textContent='⏳ looking at your screen…';const r=await post('/screen/describe',{});o.textContent=r.description||('error: '+(r.error||''))};
    const iv=setInterval(()=>{const st=$('#recstate');if(st&&st.textContent.startsWith('recording'))pollRec()},2500);
    return [()=>clearInterval(iv)]}
  return {html,mount};
}

/* ---- AI Screen Vision (Phase 7): live stream + mouse/window tracking + on-demand VLM ---- */
function LiveVision(){
  const AR=State.lang==='ar';
  const html=`<div class="livevision">
    <div class="card"><div class="hd"><h3>👁️ ${t('nav_live')}</h3><span class="pill" id="lvstatus">off</span></div>
      <div class="bd">
        <p class="muted">🔒 ${AR?'كل شيء هنا اختياري ومحلي ولا يُحفظ. أوقفه في أي وقت.':'Privacy: everything here is opt-in, local-only, and never saved. Toggle off any time.'}</p>
        <div class="lvtoggles">
          <label class="lvsw"><input type="checkbox" id="lv_enabled"> <span>${AR?'تفعيل الرؤية الحيّة (بث الشاشة)':'Enable screen vision (live stream)'}</span></label>
          <label class="lvsw"><input type="checkbox" id="lv_mouse"> <span>${AR?'تتبّع مؤشر الفأرة':'Track mouse position'}</span></label>
          <label class="lvsw"><input type="checkbox" id="lv_kbd"> <span>${AR?'تتبّع النافذة النشطة (سياق)':'Track focused window (context)'}</span></label>
          <label class="lvfps">${AR?'إطارات/ث':'FPS'} <input type="range" id="lv_fps" min="1" max="15" value="4"> <b id="lv_fpsv">4</b></label>
        </div>
      </div></div>
    <div class="card"><div class="hd"><h3>${AR?'الشاشة الحيّة':'Live screen'}</h3>
      <span class="muted" id="lv_mousepos"></span><span class="spacer"></span>
      <button class="btn sm p" id="lv_describe">🧠 ${AR?'صف ما على الشاشة':"Describe what's on screen"}</button></div>
      <div class="bd">
        <div class="lvstage"><img id="lv_img" alt="${AR?'فعّل الرؤية بالأعلى':'enable vision above to see the live screen'}"><div id="lv_cursor" class="lvcursor" hidden></div></div>
        <div id="lv_ctx" class="muted" style="margin-top:8px"></div>
        <div id="lv_desc" class="lvdesc"></div>
      </div></div>
  </div>`;
  function mount(){
    let mouseTimer=null, ctxTimer=null;
    async function refresh(){
      let st; try{st=await api('/vision/state')}catch(e){return}
      $('#lv_enabled').checked=st.enabled; $('#lv_mouse').checked=st.track_mouse; $('#lv_kbd').checked=st.track_keyboard;
      $('#lv_fps').value=st.fps; $('#lv_fpsv').textContent=st.fps;
      const badge=$('#lvstatus'); badge.textContent=st.enabled?'LIVE':'off'; badge.classList.toggle('on',st.enabled);
      const img=$('#lv_img');
      if(st.enabled){img.src='/api/vision/stream?t='+Date.now()} else {img.removeAttribute('src')}
      clearInterval(mouseTimer); mouseTimer=null;
      if(st.enabled&&st.track_mouse){mouseTimer=setInterval(pollMouse,200)} else {$('#lv_cursor').hidden=true; $('#lv_mousepos').textContent=''}
      clearInterval(ctxTimer); ctxTimer=null;
      if(st.enabled&&st.track_keyboard){ctxTimer=setInterval(pollCtx,1500); pollCtx()} else {$('#lv_ctx').textContent=''}
    }
    async function pollMouse(){try{const r=await api('/vision/mouse'); if(r&&r.mouse){
      $('#lv_mousepos').textContent='🖱 '+r.mouse.x+', '+r.mouse.y;
      const img=$('#lv_img'), cur=$('#lv_cursor');
      if(img.clientWidth&&(screen.width||0)){cur.hidden=false;
        cur.style.left=(r.mouse.x*img.clientWidth/screen.width)+'px';
        cur.style.top=(r.mouse.y*img.clientHeight/screen.height)+'px'}}}catch(e){}}
    async function pollCtx(){try{const r=await api('/vision/context'); if(r&&r.window)$('#lv_ctx').textContent='🪟 '+(r.window.title||'(no title)')}catch(e){}}
    function save(patch){post('/settings',patch).then(s=>{State.settings=s;refresh()})}
    $('#lv_enabled').onchange=e=>save({screen_vision_enabled:e.target.checked});
    $('#lv_mouse').onchange=e=>save({track_mouse:e.target.checked});
    $('#lv_kbd').onchange=e=>save({track_keyboard:e.target.checked});
    $('#lv_fps').oninput=e=>{$('#lv_fpsv').textContent=e.target.value};
    $('#lv_fps').onchange=e=>save({vision_fps:+e.target.value});
    $('#lv_describe').onclick=async()=>{const d=$('#lv_desc'); d.textContent='⏳ '+(AR?'ينظر…':'looking…');
      const r=await post('/vision/describe',{}); d.innerHTML=(r&&r.description)?mdRender(r.description):('error: '+((r&&r.error)||'vision off'))};
    refresh();
    return ()=>{clearInterval(mouseTimer);clearInterval(ctxTimer);const img=$('#lv_img');if(img)img.removeAttribute('src')};
  }
  return {html,mount};
}

function Bugs(){
  const html=`<div class="grid g2" style="align-items:start">
    ${card('🐞 Report a Bug',`
      <label class="f">Title</label><input class="t" id="btitle" placeholder="Short summary of the issue">
      <label class="f" style="margin-top:10px">Details</label><textarea class="t" id="bdetail" rows="4" placeholder="What happened? Steps to reproduce? What did you expect?"></textarea>
      <div class="flex" style="gap:8px;align-items:flex-end;margin-top:10px">
        <div><label class="f">Severity</label><select class="t" id="bsev"><option>low</option><option selected>normal</option><option>high</option><option>critical</option></select></div>
        <span class="spacer"></span>
        <button class="btn p" id="bsubmit">📨 Submit report</button>
      </div>
      <p class="muted" style="font-size:12px;margin-top:8px">The last 40 lines of the server log are attached automatically.</p>`)}
    ${card('Issues <span class="tag" id="bcount"></span>',`<div id="blist"><div class="empty">no reports yet</div></div>`)}
   </div>`;
  async function load(){const r=await api('/bugs');const el=$('#blist');if(!el)return;
    const cc=$('#bcount');if(cc)cc.textContent=(r.open||0)+' open';
    el.innerHTML=(r.items&&r.items.length)?r.items.map(b=>`<div class="row"><span class="tag ${b.status==='open'?'warn':'on'}">${esc(b.status)}</span><span class="name" title="${esc(b.detail||'')}">${esc(b.title)} <span class="muted" style="font-size:11px">· ${esc(b.severity)}</span></span><button class="btn sm" data-done="${b.id}">${b.status==='open'?'resolve':'reopen'}</button><button class="btn sm danger" data-del="${b.id}">✕</button></div>`).join(''):'<div class="empty">no reports yet 🎉</div>';
    $$('#blist [data-done]').forEach(x=>x.onclick=async()=>{const b=(r.items||[]).find(i=>i.id==x.dataset.done);await post('/bugs/'+x.dataset.done+'/status',{status:(b&&b.status==='open')?'resolved':'open'});load()});
    $$('#blist [data-del]').forEach(x=>x.onclick=async()=>{if(confirm('Delete this report?')){await del('/bugs/'+x.dataset.del);load()}})}
  function mount(){load();
    $('#bsubmit').onclick=async()=>{const t=$('#btitle').value.trim();if(!t){toast('error','Title required','');return}
      const r=await post('/bugs',{title:t,detail:$('#bdetail').value,severity:$('#bsev').value,page:location.hash});
      if(r.ok){toast('success','Bug reported','thank you — logs attached');$('#btitle').value='';$('#bdetail').value='';load()}};
    return []}
  return {html,mount};
}

/* ---- LOCAL speech-to-text: record mic → POST to /api/stt (Whisper) → fill target ---- */
let _mediaRec=null,_sttChunks=[];
function _micUI(btnEl,recording){
  if(!btnEl)return;
  if(recording){btnEl.dataset.icon=btnEl.dataset.icon||btnEl.textContent;btnEl.textContent='⏹ Stop';btnEl.classList.add('rec');btnEl.title='Stop recording & transcribe';}
  else{btnEl.classList.remove('rec');if(btnEl.dataset.icon)btnEl.textContent=btnEl.dataset.icon;btnEl.title='Voice input';}
}
async function dictate(targetSel,btnSel){
  const targetEl=$(targetSel), btnEl=$(btnSel);
  if(!targetEl)return;
  if(_mediaRec&&_mediaRec.state==='recording'){_mediaRec.stop();return}   // manual stop (button is now ⏹ Stop)
  if(!navigator.mediaDevices||!window.MediaRecorder){toast('error','Mic unavailable','This browser cannot record audio');return}
  let stream; try{stream=await navigator.mediaDevices.getUserMedia({audio:true})}catch(e){toast('error','Microphone blocked','Allow microphone access');return}
  _sttChunks=[]; const mr=new MediaRecorder(stream); _mediaRec=mr;
  mr.ondataavailable=e=>{if(e.data&&e.data.size)_sttChunks.push(e.data)};
  mr.onstop=async()=>{stream.getTracks().forEach(t=>t.stop()); _micUI(btnEl,false); _mediaRec=null;
    const blob=new Blob(_sttChunks,{type:'audio/webm'}); if(blob.size<800){toast('info','No audio captured','');return}
    const old=targetEl.value, ph=targetEl.placeholder; targetEl.placeholder='⏳ Transcribing…';
    const fd=new FormData(); fd.append('audio',blob,'rec.webm'); fd.append('lang',State.lang);
    let r; try{r=await fetch('/api/stt',{method:'POST',body:fd}).then(x=>x.json())}catch(e){r={error:String(e)}}
    targetEl.placeholder=ph;
    if(r&&r.text){targetEl.value=(old?old.trim()+' ':'')+r.text; targetEl.dispatchEvent(new Event('input')); targetEl.focus()}
    else toast('error','Could not transcribe',(r&&r.error)||'no speech detected');
  };
  mr.start(); _micUI(btnEl,true); toast('info','🎤 Listening…','Click ⏹ Stop to end & transcribe');
}

function Agent(){
  const AR=State.lang==='ar';
  const A={
    title:AR?'وكيل نوفا':'Nova Agent',
    ready:AR?'جاهز عندما تكون مستعداً — صِف هدفاً وسأخطّط وأنفّذ خطوة بخطوة.':"Ready when you are — describe a goal and I'll plan and act, step by step.",
    idle:AR?'خامل':'idle',
    examples_h:AR?'💡 أهداف مقترحة':'💡 Example goals',
    empty1:AR?'أعطِ نوفا هدفاً وشاهده يفكّر وينفّذ في الوقت الحقيقي.':'Give Nova a goal and watch it reason and act in real time.',
    empty2:AR?'اختر مثالاً من القائمة، أو اكتب هدفك بالأسفل.':'Pick an example on the right, or type your own below.',
    placeholder:AR?'اطلب من نوفا أي شيء…  (Enter للإرسال · Shift+Enter لسطر جديد)':'Ask Nova to do anything…  (Enter to send · Shift+Enter for a new line)',
    full_lbl:AR?'🔓 صلاحية كاملة':'🔓 Full access',
    dry_lbl:AR?'👁 محاكاة':'👁 Dry-run',
    send:AR?'إرسال':'Send', working:AR?'يعمل…':'Working…',
    collapse:AR?'🗂 طيّ الكل':'🗂 Collapse', expand:AR?'🗂 توسيع الكل':'🗂 Expand',
    export:AR?'📤 تصدير':'📤 Export', rerun:AR?'🔁 إعادة':'🔁 Re-run', stop:AR?'⏹ إيقاف':'⏹ Stop',
    creativity:AR?'🌡️ درجة الإبداع':'🌡️ Creativity', maxsteps:AR?'🔢 أقصى خطوات':'🔢 Max steps', enabledtools:AR?'🧰 الأدوات المفعّلة':'🧰 Enabled tools',
    tip_collapse:AR?'طيّ أو توسيع كل الخطوات':'Collapse or expand all steps',
    tip_export:AR?'تصدير السجل كملف نصي':'Export the log as a text file',
    tip_rerun:AR?'إعادة تشغيل آخر هدف':'Re-run the last goal',
    tip_stop:AR?'إيقاف الوكيل':'Stop the agent', tip_settings:AR?'إعدادات الوكيل':'Agent settings',
    tip_model:AR?'اختر النموذج':'Choose the model',
    tip_full:AR?'صلاحيات كاملة — سينفّذ نوفا أي شيء تطلبه':'Full permissions — Nova will attempt anything you ask',
    tip_dry:AR?'محاكاة دون تنفيذ فعلي':'Simulate without executing side effects',
    tip_send:AR?'إرسال الهدف إلى نوفا':'Send the goal to Nova',
    st_starting:AR?'يبدأ…':'starting…', st_running:AR?'يعمل':'running', st_thinking:AR?'يفكّر':'thinking',
    st_acting:AR?'ينفّذ':'acting', st_dry:AR?'محاكاة':'dry-run', st_full:AR?'صلاحية كاملة':'full access',
    st_waiting:AR?'بالانتظار':'waiting', st_done:AR?'تم':'done', st_stopped:AR?'متوقف':'stopped', st_error:AR?'خطأ':'error', st_stopping:AR?'يتوقف…':'stopping…',
    ln_work:AR?'نوفا يباشر العمل…':'Nova is getting to work…', ln_think:AR?'نوفا يفكّر…':'Nova is thinking…',
    ln_reason:AR?'نوفا يحلّل…':'Nova is reasoning…', ln_using:AR?'نوفا يستخدم ':'Nova is using ',
    ln_done:AR?'اكتملت المهمة. أعطني هدفاً آخر!':'Task complete. Give me another goal!',
    ln_wait:AR?'نوفا بانتظار ردّك.':'Nova is waiting for your reply.', ln_stopped:AR?'تم إيقاف الوكيل.':'Agent stopped.',
    ln_error:AR?'حدث خطأ ما — حاول مجدداً.':'Something went wrong — try again.', ln_stopping:AR?'جارٍ إيقاف الوكيل…':'Stopping the agent…',
    s_goal:AR?'الهدف':'Goal', s_dry:AR?' · محاكاة (لا تنفيذ فعلي)':' · DRY-RUN (nothing is executed)', s_fa:AR?' · 🔓 صلاحية كاملة':' · 🔓 full access',
    s_thinking:AR?'تفكير':'Thinking', s_step:AR?' · خطوة ':' · step ', s_using:AR?'يستخدم ':'Using ',
    s_result:AR?'النتيجة':'Result', s_done:AR?'تم':'Done', s_clarify:AR?'نوفا يحتاج توضيحاً':'Nova needs clarification',
    s_stopped:AR?'متوقف':'Stopped', s_stopped_body:AR?'لقد أوقفت الوكيل.':'You stopped the agent.', s_error:AR?'خطأ':'Error',
    prog:AR?'الخطوة':'Step', open_first:AR?' → افتح الأول':' → open first',
    ex_nothing:AR?'لا شيء للتصدير':'Nothing to export', ex_runfirst:AR?'شغّل هدفاً أولاً':'Run a goal first', ex_done:AR?'تم تصدير السجل':'Log exported'};
  const TN={kb_search:AR?'بحث المعرفة':'KB search',run_command:AR?'أمر':'command',browse:AR?'تصفّح':'browse',
    open_url:AR?'فتح رابط':'open URL',see_screen:AR?'رؤية الشاشة':'see screen',read_screen:AR?'قراءة الشاشة':'read screen',screenshot:AR?'لقطة شاشة':'screenshot',act_on_screen:AR?'التحكم بالشاشة':'act on screen',
    generate_video:AR?'فيديو':'video',notify:AR?'تنبيه':'notify',speak:AR?'نطق':'speak',
    read_file:AR?'قراءة ملف':'read file',write_file:AR?'كتابة ملف':'write file',schedule:AR?'جدولة':'schedule',ask:AR?'سؤال':'ask'};
  const tn=k=>TN[k]||k;
  const GROUPS=[
    {cat:AR?'🖥️ النظام':'🖥️ System',items:[
      [AR?'تحقق من استخدام كرت الشاشة وأخبرني إن كان أقل من 50%.':'Check GPU utilization and tell me if it is below 50%.'],
      [AR?'اعرض أكثر 5 عمليات استهلاكاً للذاكرة.':'List the top 5 processes using the most memory.'],
      [AR?'اعرض مساحة القرص ونبّهني لأي قرص تجاوز 90%.':'Show my disk space and warn me about any drive over 90% full.'],
      [AR?'أخبرني باستخدام المعالج والذاكرة وذاكرة كرت الشاشة الآن.':'Tell me my CPU, RAM and VRAM usage right now.']]},
    {cat:AR?'📂 الملفات':'📂 Files',items:[
      [AR?'أنشئ ملفاً نصياً على سطح المكتب باسم notes.txt يحتوي قائمة مهام قصيرة.':'Create a text file on my Desktop called notes.txt with a short to-do list.'],
      [AR?'ابحث عن أكبر 10 ملفات في C:\\AI واعرضها.':'Find the 10 largest files in C:\\AI and list them.'],
      [AR?'أنشئ مجلداً باسم Projects على سطح المكتب.':'Create a folder called Projects on my Desktop.'],
      [AR?'احسب عدد الملفات في مجلد التنزيلات.':'Count how many files are in my Downloads folder.']]},
    {cat:AR?'🌐 الويب':'🌐 Web',items:[
      [AR?'افتح example.com ولخّص لي الصفحة.':'Open example.com and summarize the page for me.'],
      [AR?'تصفّح wikipedia.org وأخبرني بعنوان الصفحة بالضبط.':'Browse to wikipedia.org and tell me its exact page title.'],
      [AR?'افتح news.ycombinator.com واعرض أول 3 عناوين.':'Open news.ycombinator.com and list the first 3 headlines.']]},
    {cat:AR?'📚 المعرفة':'📚 Knowledge',items:[
      [AR?'ابحث في مستنداتي عن الحقائق المهمة ونبّهني بملخص.':'Search my documents for the key facts and notify me with a summary.'],
      [AR?'ابحث عن أي مواعيد نهائية في مستنداتي واقرأها بصوت عالٍ.':'Find any deadlines in my documents and read them aloud.'],
      [AR?'لخّص قاعدة معرفتي في 5 نقاط.':'Summarize my knowledge base in 5 bullet points.']]},
    {cat:AR?'🎥 الإبداع':'🎥 Creation',items:[
      [AR?'ولّد فيديو سينمائياً قصيراً لغروب الشمس فوق البحر.':'Generate a short cinematic video of a sunset over the sea.'],
      [AR?'ولّد فيديو لمدينة نيون ليلاً.':'Generate a video of a neon city at night.']]},
    {cat:AR?'🎓 التدريب':'🎓 Training',items:[
      [AR?'لخّص مستنداتي ثم جدول مهمة جمع يومية.':'Summarize my documents, then schedule a daily harvest automation.'],
      [AR?'جدول تنبيهاً يذكّرني بإعادة التدريب الليلة.':'Schedule a notification to remind me to retrain tonight.']]}];
  const ALL=GROUPS.flatMap(g=>g.items.map(it=>it[0]));
  const TOOLICON={kb_search:'📚',run_command:'⌨️',browse:'🌐',open_url:'🪟',see_screen:'👁',read_screen:'🔤',screenshot:'📸',act_on_screen:'🖱️',generate_video:'🎥',notify:'🔔',speak:'🔊',read_file:'📄',write_file:'💾',schedule:'⏰',ask:'❓'};
  function argSummary(action,a){a=a||{};
    if(action==='run_command')return a.command||'';
    if(action==='browse')return a.search?('🔎 '+a.search+(a.click_first?A.open_first:'')):(a.url||'');
    if(action==='open_url')return a.url||'';
    if(action==='write_file')return a.path||'';
    if(action==='read_file')return a.path||'';
    if(action==='generate_video')return a.prompt||'';
    if(action==='kb_search')return a.query||'';
    if(action==='notify'||action==='speak')return a.text||'';
    if(action==='schedule')return (a.name||'')+' · '+(a.action||'');
    return JSON.stringify(a).slice(0,200);}
  const TOOLS=[['kb_search','📚'],['run_command','⌨️'],['browse','🌐'],['open_url','🪟'],
    ['see_screen','👁'],['read_screen','🔤'],['screenshot','📸'],['act_on_screen','🖱️'],
    ['generate_video','🎥'],['notify','🔔'],['speak','🔊'],['read_file','📄'],['write_file','💾'],['schedule','⏰']];
  const SET=Object.assign({temp:0.2,max:8,tools:TOOLS.map(t=>t[0])},JSON.parse(localStorage.getItem('agent_set')||'{}'));
  const saveSet=()=>localStorage.setItem('agent_set',JSON.stringify(SET));
  let maxSteps=8,lastGoal='',collapsedAll=false,transcript=[];
  const html=`<div class="agentpage" dir="ltr">
    <div class="agentmain">
      <div class="agenthero glass">
        <div class="nova-avatar" id="novav"><span class="halo"></span><span class="nova-core">🤖</span><i></i><i></i><i></i></div>
        <div class="agenthero-txt">
          <h2>${A.title}</h2>
          <p id="astatusline">${A.ready}</p>
          <div class="aprog" id="aprog"><div class="aprog-track"><i id="aprogfill"></i></div><span id="aprogtxt"></span></div>
        </div>
        <span class="tag" id="astatus">${A.idle}</span>
      </div>
      <div class="agenttools">
        <button class="atbtn" id="acollapse" data-tip="${A.tip_collapse}">${A.collapse}</button>
        <button class="atbtn" id="aexport" data-tip="${A.tip_export}">${A.export}</button>
        <button class="atbtn" id="arerun" data-tip="${A.tip_rerun}" disabled>${A.rerun}</button>
        <span class="spacer"></span>
        <button class="atbtn danger" id="astop" data-tip="${A.tip_stop}" style="display:none">${A.stop}</button>
        <button class="atbtn gear" id="agear" data-tip="${A.tip_settings}">⚙️</button>
      </div>
      <div class="asettings glass" id="asettings" hidden>
        <div class="aset-row"><label>${A.creativity} <span class="aset-v" id="atempv">0.2</span></label>
          <input type="range" id="atemp" min="0" max="1.2" step="0.1" value="0.2"></div>
        <div class="aset-row"><label>${A.maxsteps} <span class="aset-v" id="astepv">8</span></label>
          <input type="range" id="amax" min="1" max="20" step="1" value="8"></div>
        <div class="aset-tools"><div class="aset-h">${A.enabledtools}</div><div class="atoolgrid" id="atools"></div></div>
      </div>
      <div class="agentlog" id="alog"><div class="empty">
        <div class="empty-orb">🤖</div>
        <p>${A.empty1}</p>
        <p class="muted" style="font-size:12px">${A.empty2}</p>
      </div></div>
      <div class="agentbar glass">
        <textarea id="agoal" rows="1" placeholder="${A.placeholder}"></textarea>
        <div class="agentbar-row">
          <select class="t" id="amodel" data-tip="${A.tip_model}"></select>
          <label class="atog" data-tip="${A.tip_full}"><input type="checkbox" id="afull" checked> ${A.full_lbl}</label>
          <label class="atog" data-tip="${A.tip_dry}"><input type="checkbox" id="adry"> ${A.dry_lbl}</label>
          <span class="spacer"></span>
          <button class="btn" id="amic" data-tip="${AR?'إدخال صوتي (محلي)':'Voice input (local Whisper)'}">🎤</button>
          <button class="btn p" id="arun" data-tip="${A.tip_send}"><span class="ic">📨</span> ${A.send}</button>
        </div>
      </div>
    </div>
    <aside class="agentside glass">
      <div class="agentside-h">${A.examples_h}</div>
      <div id="aex"></div>
    </aside>
   </div>`;
  function setBusy(b){const av=$('#novav'),btn=$('#arun'),stop=$('#astop');
    if(av)av.classList.toggle('thinking',b);
    if(btn){btn.disabled=b;btn.innerHTML=b?`<span class="spin">⏳</span> ${A.working}`:`<span class="ic">📨</span> ${A.send}`}
    if(stop)stop.style.display=b?'':'none';
    if(!b)removeThinking();}
  function setStatus(cls,txt,line){const st=$('#astatus');if(st){st.className='tag '+cls+(cls==='run'?' live':'');st.textContent=txt}if(line&&$('#astatusline'))$('#astatusline').textContent=line}
  function setProgress(cur,max){const p=$('#aprog');if(!p)return;if(!max){p.classList.remove('on');return}
    p.classList.add('on');$('#aprogfill').style.width=Math.min(100,Math.round((cur/max)*100))+'%';$('#aprogtxt').textContent=A.prog+' '+cur+' / '+max}
  function showThinking(on){removeThinking();if(!on)return;const a=$('#alog');if(!a)return;const e=a.querySelector('.empty');if(e)e.remove();
    const d=document.createElement('div');d.id='athinking';d.className='athinking';
    d.innerHTML=`<span class="adots"><i></i><i></i><i></i></span><span>${A.ln_think}</span>`;a.appendChild(d);a.scrollTop=a.scrollHeight}
  function removeThinking(){const x=$('#athinking');if(x)x.remove()}
  function step(cls,icon,title,body,raw){const a=$('#alog');if(!a)return;const e=a.querySelector('.empty');if(e)e.remove();removeThinking();
    const d=document.createElement('div');d.className='astep '+cls+(collapsedAll?' collapsed':'');
    d.innerHTML=`<div class="ah"><span class="ah-ic">${icon}</span> <b>${esc(title)}</b><span class="ah-chev">▾</span></div>${body?`<div class="ab">${body}</div>`:''}`;
    d.querySelector('.ah').onclick=()=>d.classList.toggle('collapsed');
    a.appendChild(d);a.scrollTop=a.scrollHeight;tw(d);
    transcript.push({title,body:(raw!=null?raw:'')});}
  function exportLog(){if(!transcript.length){toast('info',A.ex_nothing,A.ex_runfirst);return}
    const out=['Nova Agent — '+new Date().toLocaleString(),'Goal: '+(lastGoal||''),''];
    transcript.forEach((s,i)=>{out.push((i+1)+'. '+s.title);if(s.body&&s.body!==s.title)out.push('   '+String(s.body).replace(/\n/g,'\n   '));out.push('')});
    const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([out.join('\n')],{type:'text/plain'}));
    a.download='nova-agent-log.txt';a.click();URL.revokeObjectURL(a.href);toast('success',A.ex_done,'nova-agent-log.txt')}
  function run(){const t=$('#agoal');const g=(t.value||'').trim();if(!g)return;
    lastGoal=g;const rr=$('#arerun');if(rr)rr.disabled=false;collapsedAll=false;transcript=[];
    $('#alog').innerHTML='';setBusy(true);setStatus('run',A.st_starting,A.ln_work);showThinking(true);
    post('/agent',{goal:g,model:$('#amodel').value,dry_run:$('#adry').checked,unrestricted:$('#afull').checked,
      temperature:SET.temp,max_steps:SET.max,tools:SET.tools});usage('agent');}
  function mount(){
    const pg=$('#main')&&$('#main').querySelector('.page');if(pg)pg.setAttribute('dir','ltr');
    $('#aex').innerHTML=GROUPS.map(g=>`<div class="exgroup"><div class="exh">${g.cat}</div>`+
      g.items.map(it=>`<button class="exitem" data-ex="${ALL.indexOf(it[0])}">${esc(it[0])}</button>`).join('')+`</div>`).join('');
    $$('#aex .exitem').forEach(b=>b.onclick=()=>{const t=$('#agoal');t.value=ALL[+b.dataset.ex];t.focus();t.style.height='auto';t.style.height=Math.min(t.scrollHeight,140)+'px';});
    (async()=>{const list=await api('/models');const cur=State.settings.default_local_model;
      const usable=list.filter(m=>(m.tags||[]).includes('control')||(m.tags||[]).includes('chat'));
      $('#amodel').innerHTML=usable.map(m=>`<option value="${esc(m.name)}" ${m.name===cur?'selected':''}>${esc(m.name)}</option>`).join('')})();
    // settings
    $('#atemp').value=SET.temp;$('#atempv').textContent=(+SET.temp).toFixed(1);
    $('#amax').value=SET.max;$('#astepv').textContent=SET.max;
    $('#atools').innerHTML=TOOLS.map(t=>`<label class="atool"><input type="checkbox" data-t="${t[0]}" ${SET.tools.includes(t[0])?'checked':''}> ${t[1]} ${tn(t[0])}</label>`).join('');
    $('#atemp').oninput=e=>{SET.temp=+e.target.value;$('#atempv').textContent=SET.temp.toFixed(1);saveSet()};
    $('#amax').oninput=e=>{SET.max=+e.target.value;$('#astepv').textContent=SET.max;saveSet()};
    $$('#atools input').forEach(c=>c.onchange=()=>{SET.tools=$$('#atools input').filter(x=>x.checked).map(x=>x.dataset.t);saveSet()});
    $('#agear').onclick=()=>{const s=$('#asettings');s.hidden=!s.hidden;$('#agear').classList.toggle('on',!s.hidden)};
    // toolbar
    $('#acollapse').onclick=()=>{collapsedAll=!collapsedAll;$$('#alog .astep').forEach(s=>s.classList.toggle('collapsed',collapsedAll));$('#acollapse').innerHTML=collapsedAll?A.expand:A.collapse};
    $('#aexport').onclick=exportLog;
    $('#arerun').onclick=()=>{if(lastGoal){$('#agoal').value=lastGoal;run()}};
    $('#astop').onclick=()=>{post('/agent/stop',{});setStatus('warn',A.st_stopping,A.ln_stopping)};
    const ta=$('#agoal');
    ta.addEventListener('input',()=>{ta.style.height='auto';ta.style.height=Math.min(ta.scrollHeight,140)+'px'});
    ta.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();run()}});
    $('#arun').onclick=run;
    $('#amic').onclick=()=>dictate('#agoal','#amic');
    const u=bus.on('agent',m=>{
      if(m.ev==='start'){maxSteps=m.max_steps||8;setBusy(true);setProgress(0,maxSteps);
        setStatus(m.dry_run?'warn':'run',m.dry_run?A.st_dry:(m.unrestricted?A.st_full:A.st_running),A.ln_think);
        step('s-start','🎯',A.s_goal+(m.dry_run?A.s_dry:'')+(m.unrestricted?A.s_fa:''),esc(m.goal),m.goal);showThinking(true)}
      else if(m.ev==='thought'){setProgress(m.step||0,maxSteps);setStatus('run',A.st_thinking,A.ln_reason);
        step('s-think','🧠',A.s_thinking+(m.step?A.s_step+m.step:''),esc(m.text||''),m.text)}
      else if(m.ev==='action'){const ic=TOOLICON[m.action]||'⚙️';setStatus('run',A.st_acting,A.ln_using+tn(m.action)+'…');
        const sum=argSummary(m.action,m.args);
        step('s-act',ic,A.s_using+tn(m.action),`<code class="ic">${esc(sum.slice(0,400))}</code>`,m.action+': '+sum);showThinking(true)}
      else if(m.ev==='observation'){step('s-obs','👁',A.s_result,`<pre class="code">${esc((m.text||'').slice(0,1200))}</pre>`,m.text);showThinking(true)}
      else if(m.ev==='ask'){step('s-ask','❓',A.s_clarify,esc(m.text||''),m.text);setBusy(false);setStatus('warn',A.st_waiting,A.ln_wait)}
      else if(m.ev==='final'){step('s-final','✅',A.s_done,mdRender(m.text||''),m.text);setProgress(maxSteps,maxSteps);setStatus('on',A.st_done,A.ln_done)}
      else if(m.ev==='stopped'){step('s-ask','⏹',A.s_stopped,A.s_stopped_body,'Stopped by user');setBusy(false);setStatus('warn',A.st_stopped,A.ln_stopped)}
      else if(m.ev==='error'){step('s-err','❌',A.s_error,esc(m.text||''),m.text);setBusy(false);setStatus('err',A.st_error,A.ln_error)}
      else if(m.ev==='done'){setBusy(false)}});
    return [u];
  }
  return {html,mount};
}
function Learning(){
  const html=`<div class="grid g4" style="margin-bottom:16px">
     <div class="card"><div class="bd"><div class="kpi"><div class="ic">📘</div><div class="stat"><span class="v" id="l_base">0</span><span class="l">base examples</span></div></div></div></div>
     <div class="card"><div class="bd"><div class="kpi"><div class="ic">🌱</div><div class="stat"><span class="v" id="l_learn">0</span><span class="l">learned from you</span></div></div></div></div>
     <div class="card"><div class="bd"><div class="kpi"><div class="ic">🧬</div><div class="stat"><span class="v" id="l_comb">0</span><span class="l">total dataset</span></div></div></div></div>
     <div class="card"><div class="bd"><div class="kpi"><div class="ic">✨</div><div class="stat"><span class="v" id="l_new">0</span><span class="l">new since last train</span></div></div></div></div>
   </div>
   <div class="grid g2">
     ${card('💡 Recommendations',`<div id="lrec"><div class="empty">…</div></div><button class="btn p mt" id="lretrain" style="width:100%">🎓 Retrain now to learn the new examples</button>`)}
     ${card('📈 Improvement Timeline',`<canvas class="spark" id="lspark" style="height:90px"></canvas><div id="lruns" class="mt"></div>`)}
   </div>`;
  async function load(){const s=await api('/learning/stats');
    set('l_base',s.base);set('l_learn',s.learned);set('l_comb',s.combined);set('l_new',s.new_since_last);
    const rec=$('#lrec');if(rec)rec.innerHTML=s.recommendations.map(r=>`<div class="metarow"><span>💡 ${esc(r)}</span></div>`).join('');
    const runs=(s.runs||[]).slice().reverse();
    spark($('#lspark'),runs.map(r=>Math.min(100,(r.combined||0))),'#22c55e');
    const lr=$('#lruns');if(lr)lr.innerHTML=runs.length?runs.slice().reverse().map(r=>`<div class="histitem"><span class="tag ${r.ok?'on':'err'}">${r.ok?'✓':'✗'}</span><span class="mono">${new Date(r.ended*1000).toLocaleDateString()}</span><span class="spacer"></span><span class="muted">${r.combined} examples</span></div>`).join(''):'<div class="empty">no training runs yet</div>';}
  function mount(){load();
    $('#lretrain').onclick=async()=>{const r=await post('/learn/retrain');toast(r.ok?'info':'error',r.ok?'Retraining started':'Cannot start',r.error||'see Training Studio');};
    return [bus.on('training_done',load)];
  }
  return {html,mount};
}
function ABTest(){
  const html=`<div class="grid g2" style="align-items:start">
    ${card('Setup',`
      <div class="grid g2"><div><label class="f">Model A</label><select class="t" id="aba"></select></div><div><label class="f">Model B</label><select class="t" id="abb"></select></div></div>
      <label class="f">AI Judge (optional)</label><select class="t" id="abj"></select>
      <label class="f">Prompts — one per line (up to 10)</label><textarea class="t" id="abp" rows="6">Explain recursion in one sentence.
Write a haiku about the ocean.
What is 17 * 24?</textarea>
      <button class="btn p mt" id="abrun" style="width:100%">🆚 Run A/B test</button>`)}
    ${card('Results <span class="tag" id="abstatus"></span>',`<div id="abscore" class="mt"></div><div id="abres"><div class="empty">run a test to compare two models side by side</div></div>`)}
   </div>`;
  function mount(){
    (async()=>{const list=(await api('/models')).filter(m=>!(m.tags||[]).includes('embedding'));
      const opts=list.map(m=>`<option value="${esc(m.name)}">${esc(m.name)}</option>`).join('');
      $('#aba').innerHTML=opts;$('#abb').innerHTML=opts;$('#abj').innerHTML='<option value="">— no judge —</option>'+opts;
      if(list[1])$('#abb').selectedIndex=1;
      const ix=list.findIndex(m=>(m.tags||[]).includes('control'));if(ix>=0)$('#abj').selectedIndex=ix+1;})();
    $('#abrun').onclick=()=>{const prompts=$('#abp').value.split('\n').map(s=>s.trim()).filter(Boolean);
      if(!prompts.length||$('#aba').value===$('#abb').value){toast('error','Pick two different models with prompts','');return}
      $('#abres').innerHTML='<span class="spin"></span> running…';$('#abscore').innerHTML='';
      post('/abtest',{model_a:$('#aba').value,model_b:$('#abb').value,judge:$('#abj').value||null,prompts});usage('abtest');$('#abrun').disabled=true};
    const u=bus.on('abtest',m=>{const st=$('#abstatus');
      if(m.ev==='start'){if(st){st.className='tag run';st.textContent='running'}$('#abres').innerHTML=''}
      else if(m.ev==='result'){const d=document.createElement('div');d.className='card';d.style.marginBottom='8px';
        d.innerHTML=`<div class="bd"><div class="muted" style="font-size:12px;margin-bottom:6px">${esc(m.prompt)}</div><div class="cmp"><div class="col"><h4>A · ${esc($('#aba').value)}</h4>${mdRender(m.a)}</div><div class="col"><h4>B · ${esc($('#abb').value)}</h4>${mdRender(m.b)}</div></div>${m.verdict?`<div class="mt"><span class="tag on">🏆 judge: ${esc(m.verdict.winner)}</span> <span class="muted" style="font-size:11px">${esc(m.verdict.raw)}</span></div>`:''}</div>`;
        $('#abres').appendChild(d)}
      else if(m.ev==='done'){if(st){st.className='tag on';st.textContent='done'}$('#abrun').disabled=false;
        $('#abscore').innerHTML='<b>Scoreboard:</b> '+Object.entries(m.wins).map(([k,v])=>`<span class="tag ${v>0?'on':''}" style="font-size:13px;padding:5px 11px">${esc(k)}: ${v}</span>`).join(' ')}});
    return [u];
  }
  return {html,mount};
}
function Knowledge(){
  const html=`<div class="grid g4" style="margin-bottom:16px">
     <div class="card"><div class="bd"><div class="kpi"><div class="ic">📚</div><div class="stat"><span class="v" id="kb_docs">0</span><span class="l">documents</span></div></div></div></div>
     <div class="card"><div class="bd"><div class="kpi"><div class="ic">🧩</div><div class="stat"><span class="v" id="kb_chunks">0</span><span class="l">chunks indexed</span></div></div></div></div>
     <div class="card"><div class="bd"><div class="kpi"><div class="ic">🧠</div><div class="stat"><span class="v" id="kb_em" style="font-size:14px">…</span><span class="l">embedding model</span></div></div></div></div>
     <div class="card"><div class="bd" style="display:flex;align-items:center;height:100%"><button class="btn p" id="kbup" style="width:100%">⬆ Add document</button><input type="file" id="kbf" multiple style="display:none" accept=".txt,.md,.json,.csv,.log,.py,.js,.ps1,.pdf,.docx"></div></div>
   </div>
   <div class="grid g2">
     ${card('Library',`<div class="drop" id="kbdrop" style="border:2px dashed var(--line2);border-radius:10px;padding:18px;text-align:center;color:var(--mut);margin-bottom:11px">📥 Drop files here to index them (PDF, DOCX, TXT, code)</div><div id="kblist"><div class="empty">…</div></div>`)}
     ${card('Test Retrieval <span class="tag">cosine search</span>',`<input class="t" id="kbq" placeholder="Ask the knowledge base…"><button class="btn p mt" id="kbsearch" style="width:100%">🔎 Search</button><div id="kbres" class="mt"></div>`)}
   </div>`;
  async function loadStatus(){const s=await api('/kb/status');set('kb_docs',s.docs);set('kb_chunks',s.chunks);
    const e=$('#kb_em');if(e)e.innerHTML=s.available?`<span style="color:var(--ok)">${esc(s.embed_model)} ✓</span>`:`<span style="color:var(--err)">${esc(s.embed_model)} missing</span>`}
  async function loadDocs(){const docs=await api('/kb/docs');const el=$('#kblist');if(!el)return;
    el.innerHTML=docs.length?docs.map(d=>`<div class="row"><span class="name">📄 ${esc(d.name)}</span><span class="tag on">${d.chunks} chunks</span><button class="btn sm danger" data-d="${d.id}">delete</button></div>`).join(''):'<div class="empty">no documents yet — add one to power RAG in chat</div>';
    $$('#kblist [data-d]').forEach(b=>b.onclick=async()=>{if(confirm('Remove this document?')){await del('/kb/docs/'+b.dataset.d);loadDocs();loadStatus()}})}
  function up(file){const fd=new FormData();fd.append('file',file);toast('info','Indexing',file.name);usage('kb-ingest');
    fetch('/api/kb/ingest',{method:'POST',body:fd}).then(x=>x.json()).then(r=>{if(!r.ok)toast('error','Ingest failed',r.error||'')}).then(loadDocs)}
  async function search(){const q=$('#kbq').value.trim();if(!q)return;$('#kbres').innerHTML='<span class="spin"></span>';
    const r=await post('/kb/search',{query:q,k:4});
    $('#kbres').innerHTML=r.results.length?r.results.map(h=>`<div class="card" style="margin-bottom:8px"><div class="bd"><div class="flex between"><span class="tag on">${esc(h.doc)}</span><span class="muted">score ${h.score}</span></div><p style="font-size:12.5px;margin-top:6px;color:var(--txt2)">${esc(h.text.slice(0,280))}…</p></div></div>`).join(''):'<div class="empty">no matches</div>'}
  function mount(){loadStatus();loadDocs();
    $('#kbup').onclick=()=>$('#kbf').click();$('#kbf').onchange=e=>{[...e.target.files].forEach(up);e.target.value=''};
    const dz=$('#kbdrop');dz.addEventListener('dragover',e=>{e.preventDefault();dz.classList.add('over')});
    dz.addEventListener('dragleave',()=>dz.classList.remove('over'));
    dz.addEventListener('drop',e=>{e.preventDefault();dz.classList.remove('over');[...e.dataTransfer.files].forEach(up)});
    $('#kbsearch').onclick=search;$('#kbq').addEventListener('keydown',e=>{if(e.key==='Enter')search()});
    return [bus.on('kb_done',()=>{loadStatus();loadDocs();toast('success','Indexed','added to knowledge base')})];
  }
  return {html,mount};
}
function Automation(){
  const ACTIONS=[['notify','🔔 Notification'],['command','⌨️ PowerShell command'],['browse','🌐 Open website (browser)'],['screen_record','🎥 Record screen'],['harvest','🌾 Harvest chats'],['retrain','🎓 Retrain model'],['video','🎬 Generate video'],['speak','🔊 Speak text'],['kb_search','📚 KB search'],['kb_index','📥 Index folder into KB']];
  const PRESETS=[
    {l:'🌙 Nightly KB index',name:'Nightly KB index',action:'kb_index',pp:'C:\\AI\\inbox',repeat:'86400'},
    {l:'📅 Weekly retrain',name:'Weekly retrain',action:'retrain',pp:'',repeat:'604800'},
    {l:'🌾 Daily harvest',name:'Daily harvest',action:'harvest',pp:'',repeat:'86400'}];
  const html=`<div class="grid g2">
    ${card('New Automation',`
      <div class="chips" id="apresets" style="margin-bottom:8px"></div>
      <label class="f">Name</label><input class="t" id="sname" placeholder="e.g. Nightly retrain">
      <label class="f">Action</label><select class="t" id="saction">${ACTIONS.map(a=>`<option value="${a[0]}">${a[1]}</option>`).join('')}</select>
      <div id="sparams"></div>
      <div class="grid g2 mt">
        <div><label class="f">Repeat</label><select class="t" id="srepeat"><option value="0">Once</option><option value="300">Every 5 min</option><option value="3600">Every hour</option><option value="86400">Every day</option><option value="604800">Every week</option></select></div>
        <div><label class="f">First run in (min)</label><input class="t" id="sdelay" value="1"></div>
      </div>
      <button class="btn p mt" id="screate" style="width:100%">➕ Create automation</button>`)}
    ${card('Scheduled Automations',`<div id="slist"><div class="empty">…</div></div>`)}
   </div>`;
  function paramFields(a){
    if(a==='command')return `<label class="f">Command</label><input class="t" id="pp" placeholder="nvidia-smi">`;
    if(a==='video')return `<label class="f">Prompt</label><input class="t" id="pp" placeholder="a neon city at night">`;
    if(a==='notify'||a==='speak')return `<label class="f">Text</label><input class="t" id="pp" placeholder="message to ${a==='speak'?'speak':'show'}">`;
    if(a==='kb_search')return `<label class="f">Query</label><input class="t" id="pp" placeholder="search the knowledge base">`;
    if(a==='kb_index')return `<label class="f">Folder to index (new files only)</label><input class="t" id="pp" placeholder="C:\\AI\\inbox">`;
    if(a==='browse')return `<label class="f">Website URL</label><input class="t" id="pp" placeholder="https://example.com">`;
    if(a==='screen_record')return `<label class="f">Duration (seconds)</label><input class="t" id="pp" placeholder="10" value="10">`;
    return '<p class="muted mt" style="font-size:12px">No parameters needed.</p>';}
  function buildParams(a){const v=$('#pp')?$('#pp').value:'';return a==='command'?{command:v}:a==='video'?{prompt:v}:(a==='notify'||a==='speak')?{text:v}:a==='kb_search'?{query:v}:a==='kb_index'?{folder:v}:a==='browse'?{url:v}:a==='screen_record'?{seconds:+v||10}:{}}
  async function load(){const rows=await api('/schedules');const el=$('#slist');if(!el)return;
    el.innerHTML=rows.length?rows.map(r=>{const next=r.next_run?new Date(r.next_run*1000).toLocaleString():'—';
      return `<div class="row"><span class="name">${esc(r.name)} <span class="tag">${esc(r.action)}</span></span>
        <span class="muted" style="font-size:11px;white-space:nowrap">${r.interval_sec>0?'every '+Math.round(r.interval_sec/60)+'m':'once'}${r.enabled?' · next '+next:''}${r.last_status?' · '+esc(r.last_status):''}</span>
        <button class="btn sm" data-run="${r.id}">run</button><button class="sw ${r.enabled?'on':''}" data-tg="${r.id}"></button><button class="btn sm danger" data-del="${r.id}">✕</button></div>`}).join(''):'<div class="empty">no automations yet — create one to run tasks on a schedule</div>';
    $$('#slist [data-run]').forEach(b=>b.onclick=()=>post('/schedules/'+b.dataset.run+'/run').then(r=>{toast('info','Ran now',r.status||'');load()}));
    $$('#slist [data-tg]').forEach(b=>b.onclick=()=>post('/schedules/'+b.dataset.tg+'/toggle').then(load));
    $$('#slist [data-del]').forEach(b=>b.onclick=()=>{if(confirm('Delete this automation?'))del('/schedules/'+b.dataset.del).then(load)});}
  function mount(){
    const upd=()=>{const e=$('#sparams');if(e)e.innerHTML=paramFields($('#saction').value)};upd();
    $('#saction').onchange=upd;load();
    $('#apresets').innerHTML=PRESETS.map((p,i)=>`<span class="chip" data-ps="${i}">${p.l}</span>`).join('');
    $$('#apresets [data-ps]').forEach(c=>c.onclick=()=>{const p=PRESETS[+c.dataset.ps];$('#sname').value=p.name;$('#saction').value=p.action;upd();if($('#pp'))$('#pp').value=p.pp;$('#srepeat').value=p.repeat;toast('info','Preset loaded','review & create')});
    $('#screate').onclick=async()=>{const action=$('#saction').value;
      await post('/schedules',{name:$('#sname').value.trim()||'Task',action,params:buildParams(action),interval_sec:+$('#srepeat').value,first_delay_sec:Math.max(0,(+$('#sdelay').value||1))*60});
      toast('success','Automation created','');$('#sname').value='';if($('#pp'))$('#pp').value='';load();usage('automation')};
    return [bus.on('schedule_ran',load)];
  }
  return {html,mount};
}
function Workflows(){
  const ACTIONS=[['notify','🔔 Notify'],['command','⌨️ Command'],['browse','🌐 Browse'],['kb_search','📚 KB search'],['kb_index','📥 Index folder'],['video','🎬 Generate video'],['harvest','🌾 Harvest'],['retrain','🎓 Retrain'],['speak','🔊 Speak']];
  let steps=[];
  const html=`<div class="grid g2" style="align-items:start">
    ${card('Build Workflow',`
      <label class="f">Workflow name</label><input class="t" id="wname" placeholder="e.g. Research → video → notify">
      <label class="f">Add a step</label>
      <div class="flex" style="gap:7px"><select class="t" id="wact" style="width:auto">${ACTIONS.map(a=>`<option value="${a[0]}">${a[1]}</option>`).join('')}</select><input class="t" id="wparam" placeholder="parameter (command / prompt / text / folder / query)"><button class="btn" id="wadd">＋</button></div>
      <div id="wsteps" class="mt"></div>
      <button class="btn p mt" id="wcreate" style="width:100%">💾 Save workflow</button>
      <p class="muted mt" style="font-size:12px">Steps run in sequence — each waits for the previous to finish.</p>`)}
    ${card('Workflows <span class="tag" id="wstatus"></span>',`<div id="wlist"><div class="empty">…</div></div>`)}
   </div>`;
  function pkey(a){return a==='command'?'command':a==='video'?'prompt':a==='kb_search'?'query':a==='kb_index'?'folder':a==='browse'?'url':'text'}
  function renderSteps(){$('#wsteps').innerHTML=steps.length?steps.map((s,i)=>`<div class="row"><span class="tag">${i+1}</span><span class="name">${esc(s.action)}${s.param?' · '+esc(s.param.slice(0,40)):''}</span><button class="btn sm danger" data-rm="${i}">✕</button></div>`).join(''):'<div class="empty">no steps — add some above</div>';
    $$('#wsteps [data-rm]').forEach(b=>b.onclick=()=>{steps.splice(+b.dataset.rm,1);renderSteps()})}
  async function load(){const ws=await api('/workflows');const el=$('#wlist');if(!el)return;
    el.innerHTML=ws.length?ws.map(w=>`<div class="card" style="margin-bottom:8px"><div class="bd"><div class="flex between"><b>${esc(w.name)}</b><span class="flex" style="gap:6px"><button class="btn sm p" data-run="${w.id}">▶ run</button><button class="btn sm danger" data-del="${w.id}">✕</button></span></div><div class="muted" style="font-size:11.5px;margin-top:6px">${(w.steps||[]).map(s=>esc(s.action)).join(' → ')||'no steps'}${w.last_status?' · '+esc(w.last_status):''}</div></div></div>`).join(''):'<div class="empty">no workflows yet — build one on the left</div>';
    $$('#wlist [data-run]').forEach(b=>b.onclick=()=>{post('/workflows/'+b.dataset.run+'/run');toast('info','Workflow running','watch the status badge')});
    $$('#wlist [data-del]').forEach(b=>b.onclick=()=>{if(confirm('Delete workflow?'))del('/workflows/'+b.dataset.del).then(load)})}
  function mount(){renderSteps();load();
    $('#wadd').onclick=()=>{steps.push({action:$('#wact').value,param:$('#wparam').value.trim()});$('#wparam').value='';renderSteps()};
    $('#wparam').addEventListener('keydown',e=>{if(e.key==='Enter')$('#wadd').click()});
    $('#wcreate').onclick=async()=>{if(!steps.length){toast('error','Add steps first','');return}
      const stepObjs=steps.map(s=>({action:s.action,params:s.param?{[pkey(s.action)]:s.param}:{}}));
      await post('/workflows',{name:$('#wname').value.trim()||'Workflow',steps:stepObjs});toast('success','Workflow saved','');steps=[];renderSteps();$('#wname').value='';load();usage('workflow')};
    const u=bus.on('workflow',m=>{const st=$('#wstatus');if(!st)return;
      if(m.ev==='start'){st.className='tag run';st.textContent='running: '+m.name}
      else if(m.ev==='step'&&m.state==='running'){st.textContent='step '+(m.i+1)+': '+m.action}
      else if(m.ev==='done'){st.className='tag '+(m.ok?'on':'err');st.textContent=m.ok?'completed ✓':'failed';load()}});
    return [u];
  }
  return {html,mount};
}
function Batch(){
  const html=card('Batch Queue',`<p class="muted" style="font-size:12.5px">Queue PowerShell commands and run them in sequence. Output appears in the Terminal page & history.</p>
    <div class="inrow mt"><input class="inp" id="bi" placeholder="add a command…"><button class="btn" id="ba">${t('add')}</button></div>
    <div id="bq" class="mt"></div>
    <button class="btn p mt" id="br" style="width:100%">▶ ${t('run_all')}</button>`);
  let q=[];
  function render(){$('#bq').innerHTML=q.length?q.map((c,i)=>`<div class="row"><span class="name mono">${esc(c)}</span><button class="btn sm danger" data-d="${i}">✕</button></div>`).join(''):'<div class="empty">queue empty</div>';
    $$('#bq [data-d]').forEach(b=>b.onclick=()=>{q.splice(+b.dataset.d,1);render()})}
  async function runAll(){if(!q.length)return;toast('info','Running batch',q.length+' commands');for(const c of q){await execCommand(c);await new Promise(r=>setTimeout(r,1200))}q=[];render();toast('success','Batch complete','')}
  function mount(){render();$('#ba').onclick=()=>{const v=$('#bi').value.trim();if(v){q.push(v);$('#bi').value='';render()}};
    $('#bi').addEventListener('keydown',e=>{if(e.key==='Enter')$('#ba').click()});$('#br').onclick=runAll;return []}
  return {html,mount};
}

/* ============================ NOVA BRAIN 2.0 — living 3D neural map ============================
   A dependency-free WebGL-grade visualization on a 2D canvas: 3D force-directed layout,
   depth-projected glowing nodes clustered by community color, additive-glow links, pulsing
   energy, drag-rotate, zoom, hover tooltips, click-to-focus, search, cluster legend filter,
   live polling, and fullscreen. Fully local — no Three.js/CDN. */
const BRAIN_PALETTE=[[34,211,238],[59,130,246],[168,85,247],[251,191,36],[236,72,153],[45,212,191],[251,146,60],[129,140,248]];
function Brain(){
  const html=`
  <div class="brainwrap" id="brainwrap">
    <canvas id="brain"></canvas>
    <div class="bhud bhud-tl">
      <div class="bsearchbox"><i class="fa-solid fa-magnifying-glass"></i><input id="bsearch" placeholder="Search documents…" autocomplete="off"></div>
      <div class="bstats" id="bstats"><span class="spin"></span> mapping…</div>
    </div>
    <div class="bhud bhud-bl" id="blegend"></div>
    <div class="bhud bhud-br bctrls">
      <button class="bbtn" id="brot" data-tip="Pause / resume rotation"><i class="fa-solid fa-pause"></i></button>
      <button class="bbtn" id="bzin" data-tip="Zoom in"><i class="fa-solid fa-plus"></i></button>
      <button class="bbtn" id="bzout" data-tip="Zoom out"><i class="fa-solid fa-minus"></i></button>
      <button class="bbtn" id="breset" data-tip="Reset view"><i class="fa-solid fa-crosshairs"></i></button>
      <button class="bbtn" id="brefresh" data-tip="Rebuild from KB"><i class="fa-solid fa-rotate"></i></button>
      <button class="bbtn" id="bfs" data-tip="Fullscreen"><i class="fa-solid fa-expand"></i></button>
    </div>
    <div class="btip" id="btip"></div>
    <div class="bdetails" id="bdetails"></div>
    <div class="bempty" id="bempty" style="display:none"></div>
  </div>`;
  function mount(){
    const cv=$('#brain'); if(!cv) return [];
    const ctx=cv.getContext('2d'); const wrap=$('#brainwrap');
    let raf=null, poll=null, nodes=[], edges=[], idx={}, clusters=[], hidden=new Set();
    let yaw=0.5, pitch=-0.35, zoom=1, autorot=true, dragging=false, lastX=0, lastY=0;
    let focusId=null, query='', t0=performance.now(), proj=[], dpr=Math.min(2,window.devicePixelRatio||1), lastSig='';
    const col=n=>BRAIN_PALETTE[n.ci%BRAIN_PALETTE.length];
    const rgba=(c,a)=>`rgba(${c[0]},${c[1]},${c[2]},${a})`;
    const size=()=>{const r=cv.getBoundingClientRect();cv.width=Math.max(1,r.width*dpr);cv.height=Math.max(1,r.height*dpr)};

    function layout(prev){ // 3D force-directed; preserves prior positions for incremental adds
      const N=nodes.length; if(!N) return;
      nodes.forEach((n,i)=>{const p=prev&&prev[n.id];
        if(p){n.x=p.x;n.y=p.y;n.z=p.z;}
        else{const th=Math.acos(1-2*(i+0.5)/N),ph=Math.PI*(1+Math.sqrt(5))*i,R=120+Math.random()*30;
          n.x=R*Math.sin(th)*Math.cos(ph);n.y=R*Math.sin(th)*Math.sin(ph);n.z=R*Math.cos(th);}
        n.vx=n.vy=n.vz=0;});
      const REP=9000, SPR=0.02, REST=64, CEN=0.012, DAMP=.86;
      for(let it=0;it<260;it++){
        for(let i=0;i<N;i++){const a=nodes[i];let fx=0,fy=0,fz=0;
          for(let j=0;j<N;j++){if(i===j)continue;const b=nodes[j];
            let dx=a.x-b.x,dy=a.y-b.y,dz=a.z-b.z;let d2=dx*dx+dy*dy+dz*dz+0.01;const f=REP/d2;const d=Math.sqrt(d2);
            fx+=dx/d*f;fy+=dy/d*f;fz+=dz/d*f;}
          fx-=a.x*CEN;fy-=a.y*CEN;fz-=a.z*CEN;a.vx=(a.vx+fx)*DAMP;a.vy=(a.vy+fy)*DAMP;a.vz=(a.vz+fz)*DAMP;}
        edges.forEach(e=>{const a=nodes[idx[e.a]],b=nodes[idx[e.b]];if(!a||!b)return;
          let dx=b.x-a.x,dy=b.y-a.y,dz=b.z-a.z;const d=Math.sqrt(dx*dx+dy*dy+dz*dz)||1;const f=SPR*(d-REST)*(0.4+e.w);
          const ux=dx/d*f,uy=dy/d*f,uz=dz/d*f;a.vx+=ux;a.vy+=uy;a.vz+=uz;b.vx-=ux;b.vy-=uy;b.vz-=uz;});
        for(let i=0;i<N;i++){const a=nodes[i];a.x+=a.vx*0.5;a.y+=a.vy*0.5;a.z+=a.vz*0.5;}
      }
    }
    function cluster(){ // label-propagation community detection -> richer multi-color groups
      const N=nodes.length;clusters=[];if(!N)return;
      const adj=nodes.map(()=>[]);
      edges.forEach(e=>{const a=idx[e.a],b=idx[e.b];if(a==null||b==null)return;adj[a].push(b);adj[b].push(a)});
      let lab=nodes.map((_,i)=>i);
      for(let it=0;it<14;it++){let changed=false;
        const ord=nodes.map((_,i)=>i);
        for(let s=ord.length-1;s>0;s--){const k=(Math.random()*(s+1))|0;const tmp=ord[s];ord[s]=ord[k];ord[k]=tmp;}
        for(const i of ord){if(!adj[i].length)continue;
          const cnt={};let best=lab[i],bc=0;
          for(const j of adj[i]){const l=lab[j];cnt[l]=(cnt[l]||0)+1;if(cnt[l]>bc){bc=cnt[l];best=l}}
          if(lab[i]!==best){lab[i]=best;changed=true}}
        if(!changed)break;}
      const counts={};lab.forEach(l=>counts[l]=(counts[l]||0)+1);
      const big=Object.keys(counts).sort((a,b)=>counts[b]-counts[a]);
      const ci={};big.forEach((l,k)=>ci[l]=k);
      const seen={};
      nodes.forEach((n,i)=>{n.ci=ci[lab[i]];if(!(n.ci in seen)){seen[n.ci]=clusters.length;clusters.push({ci:n.ci,count:0})}clusters[seen[n.ci]].count++;});
      clusters.sort((a,b)=>a.ci-b.ci);
      nodes.forEach(n=>{n.deg=0});edges.forEach(e=>{const a=nodes[idx[e.a]],b=nodes[idx[e.b]];if(a)a.deg++;if(b)b.deg++});
    }
    function renderLegend(){const el=$('#blegend');if(!el)return;
      if(!clusters.length){el.innerHTML='';return}
      el.innerHTML='<div class="bleg-h">Clusters</div>'+clusters.map(c=>{const cc=BRAIN_PALETTE[c.ci%BRAIN_PALETTE.length];
        return `<div class="bleg ${hidden.has(c.ci)?'off':''}" data-ci="${c.ci}"><span class="bdot" style="background:rgba(${cc[0]},${cc[1]},${cc[2]},.95);box-shadow:0 0 8px rgba(${cc[0]},${cc[1]},${cc[2]},.8)"></span>Cluster ${c.ci+1} · ${c.count}</div>`}).join('');
      $$('#blegend .bleg').forEach(d=>d.onclick=()=>{const ci=+d.dataset.ci;hidden.has(ci)?hidden.delete(ci):hidden.add(ci);renderLegend()});
    }
    async function load(force){const r=await api('/brain');
      const sig=(r.nodes||[]).map(n=>n.id).join(',')+'|'+(r.edges||[]).length;
      if(!force&&sig===lastSig&&nodes.length)return;   // unchanged KB → keep current layout/colors (no flicker)
      lastSig=sig;
      const prev={};nodes.forEach(n=>prev[n.id]={x:n.x,y:n.y,z:n.z});
      nodes=(r.nodes||[]).map(n=>({...n}));edges=r.edges||[];idx={};nodes.forEach((n,i)=>idx[n.id]=i);
      const st=$('#bstats');if(st)st.innerHTML=`<b>${nodes.length}</b> documents · <b>${edges.length}</b> links`;
      const emp=$('#bempty');
      if(!nodes.length){if(emp){emp.style.display='flex';emp.innerHTML='<div class="empty-orb">🧠</div><div>No documents indexed yet.<br>Add files in <b>Knowledge</b> to grow Nova’s brain.</div>'}renderLegend();return}
      if(emp)emp.style.display='none';
      cluster();layout(prev);renderLegend();
    }

    function frame(){if(document.hidden){raf=requestAnimationFrame(frame);return}   // perf: pause when tab hidden
      const W=cv.width,H=cv.height,cx=W/2,cy=H/2,now=performance.now(),tt=(now-t0)/1000;
      ctx.clearRect(0,0,W,H);
      // ambient core glow
      const bg=ctx.createRadialGradient(cx,cy,0,cx,cy,Math.max(W,H)*0.6);
      bg.addColorStop(0,'rgba(40,60,140,0.10)');bg.addColorStop(1,'rgba(0,0,0,0)');ctx.fillStyle=bg;ctx.fillRect(0,0,W,H);
      if(autorot&&!dragging)yaw+=0.0022;
      const cy_=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);
      const f=620*dpr, scaleBase=Math.min(W,H)/520*zoom;
      proj=[];
      for(const n of nodes){if(hidden.has(n.ci)){n._v=false;continue}
        let x1=n.x*cy_-n.z*sy, z1=n.x*sy+n.z*cy_;
        let y1=n.y*cp-z1*sp, z2=n.y*sp+z1*cp;
        const persp=f/(f - z2*scaleBase*0.9);
        const sx=cx+x1*scaleBase*persp, syy=cy+y1*scaleBase*persp;
        const depth=(z2+200)/400; // 0 far .. 1 near
        n._sx=sx;n._sy=syy;n._d=depth;n._z=z2;n._v=true;
        const q=query&&!(n.label||'').toLowerCase().includes(query);
        const focusDim=focusId!=null&&n.id!==focusId&&!n._nb;
        n._dim=q||focusDim;
        proj.push(n);}
      proj.sort((a,b)=>a._z-b._z);
      // edges (additive glow)
      ctx.globalCompositeOperation='lighter';
      for(const e of edges){const a=nodes[idx[e.a]],b=nodes[idx[e.b]];if(!a||!b||!a._v||!b._v)continue;
        let al=(0.05+e.w*0.5)*(0.35+0.65*Math.min(a._d,b._d));
        const foc=focusId!=null&&(e.a===focusId||e.b===focusId);
        if(a._dim&&b._dim&&!foc)al*=0.12; if(foc)al=Math.min(1,al+0.4);
        const ca=col(a),cb=col(b);const g=ctx.createLinearGradient(a._sx,a._sy,b._sx,b._sy);
        g.addColorStop(0,rgba(ca,al));g.addColorStop(1,rgba(cb,al));
        ctx.strokeStyle=g;ctx.lineWidth=Math.max(.6,(0.5+e.w*2.2)*((a._d+b._d)/2));
        ctx.beginPath();ctx.moveTo(a._sx,a._sy);ctx.lineTo(b._sx,b._sy);ctx.stroke();}
      // nodes
      for(const n of proj){const c=col(n);const pulse=1+0.10*Math.sin(tt*1.6+n._sx*0.01);
        const base=(5+Math.min(15,(n.chunks||1)*1.5)+Math.min(8,(n.deg||0)))*dpr;
        const r=base*(0.55+0.7*n._d)*zoom*pulse; const a=n._dim?0.22:(0.5+0.5*n._d);
        const g=ctx.createRadialGradient(n._sx,n._sy,0,n._sx,n._sy,r*2.4);
        g.addColorStop(0,rgba(c,0.95*a));g.addColorStop(0.4,rgba(c,0.42*a));g.addColorStop(1,rgba(c,0));
        ctx.fillStyle=g;ctx.beginPath();ctx.arc(n._sx,n._sy,r*2.4,0,6.2832);ctx.fill();
        ctx.fillStyle=rgba([255,255,255],(n._dim?0.4:0.95)*Math.min(1,0.6+n._d));
        ctx.beginPath();ctx.arc(n._sx,n._sy,Math.max(1,r*0.42),0,6.2832);ctx.fill();}
      ctx.globalCompositeOperation='source-over';
      // labels for big/near/hovered/focus nodes
      ctx.textAlign='center';ctx.font=`${12*dpr}px Inter,sans-serif`;
      const showAll=nodes.length<=18;   // small KB → label everything; large → gate by importance
      for(const n of proj){const big=(n.chunks||0)>=4||(n.deg||0)>=3;
        if(n._dim)continue; if(!(showAll||big||n.id===focusId||n.id===hoverId||n._d>0.82))continue;
        ctx.fillStyle=`rgba(235,240,255,${Math.min(1,0.55+n._d)})`;
        ctx.fillText((n.label||'').slice(0,22),n._sx,n._sy+ (16+Math.min(15,(n.chunks||1)*1.5))*dpr*(0.55+0.7*n._d));}
      raf=requestAnimationFrame(frame);
    }

    // ---- interaction ----
    let hoverId=null;
    const pick=(mx,my)=>{let best=null,bd=22*dpr;for(let i=proj.length-1;i>=0;i--){const n=proj[i];
      const dx=n._sx-mx*dpr,dy=n._sy-my*dpr;const d=Math.hypot(dx,dy);const rr=Math.max(8*dpr,(6+Math.min(15,(n.chunks||1)*1.5))*dpr);
      if(d<rr+10){return n}if(d<bd){bd=d;best=n}}return best;};
    cv.addEventListener('mousemove',e=>{const r=cv.getBoundingClientRect();
      if(dragging){yaw+=(e.clientX-lastX)*0.008;pitch+=(e.clientY-lastY)*0.008;pitch=Math.max(-1.4,Math.min(1.4,pitch));lastX=e.clientX;lastY=e.clientY;return}
      const n=pick(e.clientX-r.left,e.clientY-r.top);const tip=$('#btip');hoverId=n?n.id:null;
      cv.style.cursor=n?'pointer':(autorot?'grab':'grab');
      if(n&&tip){const cc=col(n);tip.style.display='block';tip.style.left=(e.clientX-r.left+14)+'px';tip.style.top=(e.clientY-r.top+14)+'px';
        tip.innerHTML=`<div class="btip-t"><span class="bdot" style="background:${rgba(cc,.95)};box-shadow:0 0 8px ${rgba(cc,.8)}"></span>${esc(n.label||'')}</div>
          <div class="btip-m">${n.chunks||0} chunks · ${n.deg||0} connections · cluster ${(n.ci||0)+1}</div>`;}
      else if(tip)tip.style.display='none';});
    cv.addEventListener('mousedown',e=>{dragging=true;lastX=e.clientX;lastY=e.clientY;cv.style.cursor='grabbing'});
    addEventListener('mouseup',()=>{dragging=false});
    cv.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(0.4,Math.min(3.5,zoom*(e.deltaY<0?1.12:0.9)))},{passive:false});
    cv.addEventListener('click',e=>{const r=cv.getBoundingClientRect();const n=pick(e.clientX-r.left,e.clientY-r.top);
      if(!n){focusId=null;nodes.forEach(x=>x._nb=false);$('#bdetails').classList.remove('on');return}
      focusId=n.id;const nb=new Set([n.id]);edges.forEach(e2=>{if(e2.a===n.id)nb.add(e2.b);if(e2.b===n.id)nb.add(e2.a)});
      nodes.forEach(x=>x._nb=nb.has(x.id));
      const neigh=[...nb].filter(id=>id!==n.id).map(id=>nodes[idx[id]]).filter(Boolean).sort((a,b)=>(b.chunks||0)-(a.chunks||0));
      const cc=col(n);const d=$('#bdetails');d.classList.add('on');
      d.innerHTML=`<button class="bclose" id="bdclose"><i class="fa-solid fa-xmark"></i></button>
        <div class="bd-h"><span class="bdot" style="background:${rgba(cc,.95)};box-shadow:0 0 10px ${rgba(cc,.8)}"></span><b>${esc(n.label||'')}</b></div>
        <div class="bd-stats"><div><b>${n.chunks||0}</b><span>chunks</span></div><div><b>${n.deg||0}</b><span>links</span></div><div><b>${(n.ci||0)+1}</b><span>cluster</span></div></div>
        <div class="bd-sub">Connected documents</div>
        <div class="bd-list">${neigh.length?neigh.slice(0,12).map(m=>`<div class="bd-item"><span class="bdot" style="background:${rgba(col(m),.9)}"></span>${esc(m.label||'')}<span class="bd-c">${m.chunks||0}</span></div>`).join(''):'<div class="muted" style="font-size:12px">No connections — an isolated concept.</div>'}</div>`;
      $('#bdclose').onclick=()=>{focusId=null;nodes.forEach(x=>x._nb=false);d.classList.remove('on')};});

    // controls
    $('#brot').onclick=()=>{autorot=!autorot;$('#brot').innerHTML=`<i class="fa-solid fa-${autorot?'pause':'play'}"></i>`};
    $('#bzin').onclick=()=>zoom=Math.min(3.5,zoom*1.2);
    $('#bzout').onclick=()=>zoom=Math.max(0.4,zoom*0.83);
    $('#breset').onclick=()=>{yaw=0.5;pitch=-0.35;zoom=1;focusId=null;nodes.forEach(x=>x._nb=false);$('#bdetails').classList.remove('on')};
    $('#brefresh').onclick=()=>{const b=$('#brefresh');b.classList.add('spinning');load(true).then(()=>setTimeout(()=>b.classList.remove('spinning'),600))};
    $('#bsearch').addEventListener('input',e=>{query=e.target.value.trim().toLowerCase()});
    const fsEl=wrap;
    $('#bfs').onclick=()=>{if(document.fullscreenElement){document.exitFullscreen()}else{fsEl.requestFullscreen&&fsEl.requestFullscreen()}};
    document.addEventListener('fullscreenchange',()=>{wrap.classList.toggle('fs',!!document.fullscreenElement);setTimeout(size,60)});

    const onResize=()=>size();addEventListener('resize',onResize);
    size();load().then(()=>{t0=performance.now();raf=requestAnimationFrame(frame)});
    poll=setInterval(()=>{if(document.hidden)return;load()},12000); // live: pick up new KB docs
    return [()=>{if(raf)cancelAnimationFrame(raf);if(poll)clearInterval(poll);removeEventListener('resize',onResize);
      if(document.fullscreenElement)document.exitFullscreen().catch(()=>{});}];
  }
  return {html,mount};
}
function Diagnostics(){
  const html=`<div class="grid g2">
    ${card('💓 Server Health',`<div id="dghealth"><span class="spin"></span> loading…</div>`)}
    ${card('🐞 Recent Errors <span class="tag" id="dgerrtot"></span>',`<div id="dgerrors"><span class="spin"></span></div>
       <button class="btn sm danger mt" id="dgerrclear">Clear errors</button>`)}
   </div>
   ${card('🩺 System Self-Test <span class="tag" id="dgsum"></span>',`
     <p class="muted" style="font-size:12.5px">Runs a full health check across every subsystem — services, database, embeddings, GPU, safety guards, and more.</p>
     <button class="btn p mt" id="dgrun">▶ Run self-test</button>
     <div id="dglist" class="mt"></div>`)}`;
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
  function mount(){run();loadHealth();loadErrors();$('#dgrun').onclick=run;
    const hv=setInterval(loadHealth,5000);
    const ce=$('#dgerrclear');if(ce)ce.onclick=()=>del('/errors').then(loadErrors);
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
      <label class="f mt">Backup &amp; Restore</label>
      <div class="flex wrap"><button class="btn" id="expset">⤓ Export settings</button><button class="btn" id="impset">⤒ Import settings</button><input type="file" id="impfile" accept=".json" style="display:none"></div>
      <div class="flex wrap" style="margin-top:7px"><button class="btn p" id="backupall">💾 Backup everything</button><button class="btn" id="restoreall">♻ Restore everything</button><input type="file" id="restorefile" accept=".json" style="display:none"></div>
      <p class="muted mt" style="font-size:11px">Backup bundles settings, conversations, knowledge base, automations, workflows &amp; training data into one file.</p>`)}
   </div>
   ${card('🔒 Access & Security',`
      <p class="muted" style="font-size:12.5px">By default the dashboard is <b>localhost-only</b> (most secure). Enable token auth to safely allow access from other devices on your network.</p>
      <label class="f" style="display:flex;align-items:center;gap:9px;margin-top:10px"><button class="sw ${s.auth_enabled?'on':''}" id="sae"></button> Require token authentication</label>
      <label class="f" style="display:flex;align-items:center;gap:9px"><button class="sw ${s.lan_access?'on':''}" id="slan"></button> Allow network (LAN) access — needs auth + restart</label>
      ${s.auth_token?`<label class="f">Your access token (use it to sign in on other devices)</label><input class="t" id="satoken" readonly value="${esc(s.auth_token)}" onclick="this.select()">`:''}
      <button class="btn p mt" id="saveauth" style="width:100%">Save security settings</button>
      ${s.auth_enabled?`<button class="btn mt" id="logout" style="width:100%">Log out</button>`:''}
      <p class="muted mt" style="font-size:11px">Changing LAN access requires restarting the server. On a LAN, traffic is unencrypted (HTTPS is on the roadmap) — use only on trusted networks.</p>`)}
   ${card('Usage Statistics',`<div id="usagebox"></div>`)}`;
  function mount(){
    (async()=>{const list=await api('/models');$('#sl').innerHTML=list.map(m=>`<option ${m.name===s.default_local_model?'selected':''}>${esc(m.name)}</option>`).join('')})();
    const slite=$('#slite');if(slite)slite.onclick=function(){const on=!this.classList.contains('on');
      if(on)localStorage.setItem('lite','1');else localStorage.removeItem('lite');location.reload()};
    const sconfirm=$('#sconfirm');if(sconfirm)sconfirm.onclick=function(){const on=!this.classList.contains('on');this.classList.toggle('on',on);
      post('/settings',{confirm_exit:on}).then(x=>{State.settings=x});toast('info',on?'Exit confirmation enabled':'Exit confirmation disabled','')};
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
      if(s2.auth_enabled&&s2.auth_token){await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:s2.auth_token})})}
      toast('success','Security settings saved',s2.auth_enabled?'Token active — keep it safe; restart for LAN':'Auth disabled');route()};
    const lo=$('#logout');if(lo)lo.onclick=async()=>{await fetch('/api/auth/logout',{method:'POST'});location.reload()};
    $('#le').onclick=()=>setLang('en');$('#la').onclick=()=>setLang('ar');
    const markMode=()=>$$('#pagebody [data-m]').forEach(b=>b.classList.toggle('p',b.dataset.m===State.settings.mode));markMode();
    $$('#pagebody [data-m]').forEach(b=>b.onclick=()=>{State.settings.mode=b.dataset.m;post('/settings',{mode:b.dataset.m});markMode();toast('info','Mode: '+b.dataset.m.toUpperCase(),'')});
    return [];
  }
  return {html,mount};
}

