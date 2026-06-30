// -*- part of the Nova SPA (framework-free, global scope, load order matters) -*-
// Creation/media + screen pages — Models, Tools, Video, Training, Screen Studio, Live Vision, Bugs + STT voice helpers.
// Split from the original monolithic pages.js (HON-11). Loaded after core.js, before shell.js.

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
          <label class="lvsw"><input type="checkbox" id="lv_kbd"> <span>${AR?'تتبّع النافذة + سياق الكتابة (اختياري)':'Track focused window + recent typing (context)'}</span></label>
          <label class="lvsw"><input type="checkbox" id="lv_narrate"> <span>${AR?'سرد مستمر بالذكاء (دوري)':'Continuous AI narration (periodic)'}</span></label>
          <label class="lvfps">${AR?'إطارات/ث':'FPS'} <input type="range" id="lv_fps" min="1" max="15" value="4"> <b id="lv_fpsv">4</b></label>
          <label class="lvfps" id="lv_narrwrap" hidden>${AR?'كل (ث)':'every (s)'} <input type="range" id="lv_narrint" min="10" max="300" step="5" value="30"> <b id="lv_narrintv">30</b></label>
        </div>
        <p class="muted" id="lv_kbdwarn" hidden style="font-size:11px;color:var(--warn,#d97706)">⚠️ ${AR?'أثناء التفعيل تُلتقط الكتابة على كامل النظام (مؤقتاً، بالذاكرة فقط). لا تكتب كلمات السر.':'While on, typing across the whole desktop is captured (in-memory only, capped). Don\'t type passwords.'}</p>
      </div></div>
    <div class="card"><div class="hd"><h3>${AR?'الشاشة الحيّة':'Live screen'}</h3>
      <span class="muted" id="lv_mousepos"></span><span class="spacer"></span>
      <button class="btn sm p" id="lv_describe">🧠 ${AR?'صف ما على الشاشة':"Describe what's on screen"}</button></div>
      <div class="bd">
        <div class="lvstage"><img id="lv_img" alt="${AR?'فعّل الرؤية بالأعلى':'enable vision above to see the live screen'}"><div id="lv_cursor" class="lvcursor" hidden></div></div>
        <div id="lv_ctx" class="muted" style="margin-top:8px"></div>
        <div id="lv_narration" class="lvdesc" style="margin-top:6px"></div>
        <div id="lv_desc" class="lvdesc"></div>
      </div></div>
  </div>`;
  function mount(){
    let mouseTimer=null, ctxTimer=null;
    async function refresh(){
      let st; try{st=await api('/vision/state')}catch(e){return}
      $('#lv_enabled').checked=st.enabled; $('#lv_mouse').checked=st.track_mouse; $('#lv_kbd').checked=st.track_keyboard;
      $('#lv_narrate').checked=!!st.narrate; $('#lv_narrint').value=st.narrate_interval||30; $('#lv_narrintv').textContent=st.narrate_interval||30;
      $('#lv_narrwrap').hidden=!st.narrate; $('#lv_kbdwarn').hidden=!st.track_keyboard;
      $('#lv_fps').value=st.fps; $('#lv_fpsv').textContent=st.fps;
      const badge=$('#lvstatus'); badge.textContent=st.enabled?(st.narrate?'LIVE · narrating':'LIVE'):'off'; badge.classList.toggle('on',st.enabled);
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
    async function pollCtx(){try{const r=await api('/vision/context'); if(!r)return;
      let s='🪟 '+((r.window&&r.window.title)||'(no title)');
      if(r.recent_text)s+=' · ⌨ "'+r.recent_text.slice(-60).replace(/\n/g,'⏎')+'"';
      $('#lv_ctx').textContent=s}catch(e){}}
    function save(patch){post('/settings',patch).then(s=>{State.settings=s;refresh()})}
    $('#lv_enabled').onchange=e=>save({screen_vision_enabled:e.target.checked});
    $('#lv_mouse').onchange=e=>save({track_mouse:e.target.checked});
    $('#lv_kbd').onchange=e=>save({track_keyboard:e.target.checked});
    $('#lv_narrate').onchange=e=>save({vision_narrate:e.target.checked});
    $('#lv_narrint').oninput=e=>{$('#lv_narrintv').textContent=e.target.value};
    $('#lv_narrint').onchange=e=>save({vision_narrate_interval:+e.target.value});
    $('#lv_fps').oninput=e=>{$('#lv_fpsv').textContent=e.target.value};
    $('#lv_fps').onchange=e=>save({vision_fps:+e.target.value});
    $('#lv_describe').onclick=async()=>{const d=$('#lv_desc'); d.textContent='⏳ '+(AR?'ينظر…':'looking…');
      const r=await post('/vision/describe',{}); d.innerHTML=(r&&r.description)?mdRender(r.description):('error: '+((r&&r.error)||'vision off'))};
    const narr=[]; const unsub=bus.on('vision_narration',m=>{ if(!m||!m.text)return;
      narr.unshift('🗣 '+m.text); if(narr.length>8)narr.pop();
      const el=$('#lv_narration'); if(el)el.innerHTML=narr.map(x=>`<div class="muted" style="font-size:12px">${esc(x)}</div>`).join(''); });
    refresh();
    return [()=>{clearInterval(mouseTimer);clearInterval(ctxTimer);const img=$('#lv_img');if(img)img.removeAttribute('src')}, unsub];
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
