// -*- part of the Nova SPA (framework-free, global scope, load order matters) -*-
// Data pages — Learning, A/B Test, Knowledge, Automation, Workflows (+ macro recorder), Batch.
// Loaded after pages-create.js, before pages-brain.js/pages-system.js (see index.html order).

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
     ${card('Library',`<div class="drop" id="kbdrop" style="border:2px dashed var(--line2);border-radius:10px;padding:18px;text-align:center;color:var(--mut);margin-bottom:11px">📥 Drop files here to index them (PDF, DOCX, TXT, code)</div>
       <div class="flex" style="margin-bottom:11px"><input class="t" id="kbfolder" placeholder="📁 Folder Q&amp;A — paste a local folder path to index it all" style="flex:1"><button class="btn" id="kbfolderbtn">Index folder</button></div>
       <div id="kblist"><div class="empty">…</div></div>`)}
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
    const ingestFolder=async()=>{const f=$('#kbfolder').value.trim();if(!f)return;
      toast('info','Indexing folder',f);usage('kb-ingest-folder');
      const r=await post('/kb/ingest-folder',{folder:f});
      if(r&&r.ok){toast('success','Folder indexed',`${r.indexed} files · ${r.chunks} chunks${r.capped?' (capped)':''}`);$('#kbfolder').value='';loadStatus();loadDocs()}
      else toast('error','Folder ingest failed',(r&&r.error)||'')};
    $('#kbfolderbtn').onclick=ingestFolder;$('#kbfolder').addEventListener('keydown',e=>{if(e.key==='Enter')ingestFolder()});
    $('#kbsearch').onclick=search;$('#kbq').addEventListener('keydown',e=>{if(e.key==='Enter')search()});
    return [bus.on('kb_done',()=>{loadStatus();loadDocs();toast('success','Indexed','added to knowledge base')})];
  }
  return {html,mount};
}
function Automation(){
  const ACTIONS=[['notify','🔔 Notification'],['command','⌨️ PowerShell command'],['browse','🌐 Open website (browser)'],['screen_record','🎥 Record screen'],['screen_if','👁 If screen shows… then act'],['harvest','🌾 Harvest chats'],['retrain','🎓 Retrain model'],['video','🎬 Generate video'],['speak','🔊 Speak text'],['kb_search','📚 KB search'],['kb_index','📥 Index folder into KB']];
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
    if(a==='screen_if')return `<label class="f">If the screen contains (text or regex)</label><input class="t" id="pp" placeholder="Build FAILED">
      <div class="grid g2 mt"><div><label class="f">Then do</label><select class="t" id="pp2"><option value="notify">🔔 Notify</option><option value="speak">🔊 Speak</option><option value="command">⌨️ Run command</option></select></div>
      <div><label class="f">With (text / command)</label><input class="t" id="pp3" placeholder="Build failed!"></div></div>
      <label class="f mt">Watch only a region (optional) — x,y,w,h</label><input class="t" id="ppr" placeholder="e.g. 0,0,800,200 (leave empty = whole screen)">
      <label class="atog mt" style="display:inline-flex"><input type="checkbox" id="ppa"> act when the text is <b>&nbsp;ABSENT</b>&nbsp;(disappears) instead of present</label>
      <label class="atog mt" style="display:inline-flex"><input type="checkbox" id="ppv"> use the vision model (read screen via qwen2.5‑VL instead of OCR)</label>`;
    return '<p class="muted mt" style="font-size:12px">No parameters needed.</p>';}
  function buildParams(a){const v=$('#pp')?$('#pp').value:'';
    if(a==='screen_if'){const ta=$('#pp2')?$('#pp2').value:'notify';const tx=$('#pp3')?$('#pp3').value:'';
      const rraw=($('#ppr')&&$('#ppr').value||'').trim();
      const region=rraw?rraw.split(',').map(n=>parseInt(n.trim(),10)).filter(n=>!isNaN(n)):null;
      const p={match:v,then_action:ta,then_params:(ta==='command'?{command:tx}:{text:tx}),vision:!!($('#ppv')&&$('#ppv').checked),absent:!!($('#ppa')&&$('#ppa').checked)};
      if(region&&region.length===4)p.region=region;
      return p;}
    return a==='command'?{command:v}:a==='video'?{prompt:v}:(a==='notify'||a==='speak')?{text:v}:a==='kb_search'?{query:v}:a==='kb_index'?{folder:v}:a==='browse'?{url:v}:a==='screen_record'?{seconds:+v||10}:{}}
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
      <p class="muted mt" style="font-size:12px">Steps run in sequence — each waits for the previous to finish.</p>
      <hr style="border:none;border-top:1px solid var(--line2);margin:14px 0">
      <label class="f">🎬 Macro recorder <span class="tag" id="mrstate"></span></label>
      <p class="muted" style="font-size:12px">Record your mouse clicks &amp; typing, then save it as a replayable workflow. Local-only; records only while active.</p>
      <p class="muted" style="font-size:11px;color:var(--warn,#d97706)">⚠️ While recording, ALL typing on the whole desktop is captured (not just this app) — <b>do not type passwords or secrets</b> until you stop.</p>
      <div class="flex" style="gap:7px"><button class="btn" id="mrec">⏺ Record</button><input class="t" id="mrname" placeholder="macro name"><button class="btn p" id="mrsave" disabled>💾 Save macro</button></div>
      <p class="muted mt" style="font-size:11px">Note: typed text replays via UI Automation; mouse clicks replay by coordinates (record &amp; replay at the same screen scale).</p>`)}
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
    // ---- IDEA-1: macro recorder ----
    let recTimer=null;
    const setRec=on=>{const b=$('#mrec'),s=$('#mrstate'),sv=$('#mrsave');if(!b)return;
      b.textContent=on?'⏹ Stop':'⏺ Record';b.classList.toggle('danger',on);if(sv)sv.disabled=on;
      if(s){s.className='tag '+(on?'run':'');s.textContent=on?'recording…':''}};
    const rec=$('#mrec');if(rec)rec.onclick=async()=>{
      const st=await api('/macro/state');
      if(st&&st.recording){const r=await post('/macro/stop',{});setRec(false);clearInterval(recTimer);
        toast('success','Recording stopped',`${(r&&r.count)||0} steps captured`);}
      else{const r=await post('/macro/start',{});if(r&&r.ok){setRec(true);
        recTimer=setInterval(async()=>{const s=await api('/macro/state');const tg=$('#mrstate');if(tg&&s)tg.textContent=`recording… ${s.count} steps`;},1000);
        toast('warn','🎬 Recording — all typing captured','don\'t type passwords until you stop');}
        else toast('error','Could not start',(r&&r.error)||'');}};
    const mrsave=$('#mrsave');if(mrsave)mrsave.onclick=async()=>{const name=$('#mrname').value.trim()||'macro';
      const r=await post('/macro/save',{name});if(r&&r.ok){toast('success','Macro saved',`${r.steps} steps → workflow`);$('#mrname').value='';load();}
      else toast('error','Save failed',(r&&r.error)||'nothing recorded');};
    return [u,()=>{clearInterval(recTimer);}];
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
