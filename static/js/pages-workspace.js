// -*- part of the Nova SPA (framework-free, global scope, load order matters) -*-
// Unified Workspace — Chat + Agent on ONE page with professional toggle buttons
// (mode, DeepThink, Web Search, Full Access), attach-any-file, and ✨ Auto model selection.
// Loaded after pages-system.js, before shell.js. Reuses global helpers from core.js.

function Workspace(){
  const AR = State.lang === 'ar';
  const L = AR ? {
    chat:'محادثة', agent:'الوكيل', deep:'تفكير عميق', web:'بحث الويب', full:'صلاحية كاملة',
    attach:'إرفاق', send:'إرسال', stop:'إيقاف', clear:'مسح', auto:'✨ تلقائي (ذكي)',
    ph_chat:'اكتب رسالة…  ·  أرفق أي ملف  ·  !cmd لتشغيل أمر',
    ph_agent:'صف هدفاً وسينفّذه الوكيل خطوة بخطوة…', think:'يفكّر…'
  } : {
    chat:'Chat', agent:'Agent', deep:'DeepThink', web:'Web Search', full:'Full Access',
    attach:'Attach', send:'Send', stop:'Stop', clear:'Clear', auto:'✨ Auto (smart)',
    ph_chat:'Message Nova…  ·  attach any file  ·  !cmd runs PowerShell',
    ph_agent:'Describe a goal — the agent plans, uses tools, and acts…', think:'thinking…'
  };
  const html = `
  <div class="wswrap">
    <div class="wshead glass">
      <div class="seg" id="wsmode" role="tablist">
        <button data-m="chat" role="tab">💬 ${L.chat}</button>
        <button data-m="agent" role="tab">🤖 ${L.agent}</button>
      </div>
      <select class="t" id="wsmodel" data-tip="Model (✨ Auto picks the best one per task)"></select>
      <span class="wsauto muted" id="wsautohint"></span>
      <span class="spacer"></span>
      <span class="tokbadge" id="wstok"></span>
      <button class="btn sm danger" id="wsclear">${L.clear}</button>
    </div>

    <div class="wsthread" id="wsthread"><div class="wsempty">
      <div class="empty-orb">✨</div>
      <p>${AR?'مرحباً، أنا نوفا. اسألني أو كلّفني بمهمة.':"Hi, I'm Nova. Ask me anything, or give me a task."}</p>
      <p class="muted" style="font-size:12px">${AR?'بدّل بين المحادثة والوكيل، وفعّل التفكير العميق أو بحث الويب.':'Switch between Chat & Agent, toggle DeepThink or Web Search.'}</p>
    </div></div>

    <div class="wscomposer glass">
      <div id="wsatts" class="wsatts"></div>
      <div class="wstoggles">
        <button class="tgl" id="tg-deep" data-tip="${AR?'تفكير خطوة بخطوة':'Reason step by step'}">🧠 ${L.deep}</button>
        <button class="tgl" id="tg-web" data-tip="${AR?'نتائج ويب مباشرة':'Live web results'}">🌐 ${L.web}</button>
        <button class="tgl agentonly" id="tg-full" data-tip="${AR?'يسمح للوكيل بتشغيل أي أمر/تحكم':'Let the agent run any command / control the PC'}">🔓 ${L.full}</button>
        <button class="tgl" id="tg-attach" data-tip="${AR?'أرفق صوراً/مستندات/أي ملف':'Attach images, documents, any file'}">📎 ${L.attach}</button>
        <button class="tgl" id="tg-open" data-tip="${AR?'افتح ملفاً على القرص واعمل عليه':'Open a file on disk and work on it'}">📂 ${AR?'فتح ملف':'Open file'}</button>
        <button class="tgl" id="tg-shot" aria-label="${AR?'التقط الشاشة في المحادثة':'Capture the screen into the chat'}" data-tip="${AR?'التقط الشاشة في المحادثة':'Capture the screen into the chat'}">📸</button>
        <button class="tgl" id="tg-img" aria-label="${AR?'ولّد صورة':'Generate an image'}" data-tip="${AR?'ولّد صورة':'Generate an image'}">🎨</button>
        <button class="tgl" id="tg-vid" aria-label="${AR?'ولّد فيديو':'Generate a video'}" data-tip="${AR?'ولّد فيديو':'Generate a video'}">🎬</button>
        <span class="spacer"></span>
        <button class="btn" id="wsmic" aria-label="${AR?'إدخال صوتي':'Voice input'}" data-tip="${AR?'إدخال صوتي':'Voice input'}">🎤</button>
        <button class="btn" id="wshf" aria-label="${AR?'محادثة صوتية بدون يدين':'Hands-free voice conversation'}" data-tip="${AR?'محادثة صوتية بدون يدين':'Hands-free voice conversation'}">🎙️</button>
        <button class="btn p" id="wssend">${L.send}</button>
        <button class="btn danger" id="wsstop" style="display:none">⏹ ${L.stop}</button>
      </div>
      <textarea id="wsinput" rows="1" placeholder="${L.ph_chat}"></textarea>
    </div>
    <input type="file" id="wsfile" multiple style="display:none">
  </div>`;

  function mount(){
    const thread = $('#wsthread');
    let mode = localStorage.getItem('ws_mode') || 'chat';
    let attached = [], curAI = null, lastUser = '', busy = false, maxSteps = 8, workingFile = null;
    let lastAgentRun = null;   // IDEA-3: the last agent goal+settings, for "save as workflow"
    const hf = { on:false, waiting:false };   // IDEA-4: hands-free voice conversation loop
    const tg = { deep: localStorage.getItem('ws_deep')==='1', web: localStorage.getItem('ws_web')==='1', full: false };

    // ---- helpers ----
    const clearEmpty = () => { const e = thread.querySelector('.wsempty'); if(e) e.remove(); };
    function addMsg(role, text){
      clearEmpty();
      const d = document.createElement('div'); d.className = 'wsmsg ' + role;
      const span = document.createElement('span'); span.className = 'bub';
      if(role==='ai' && text) span.innerHTML = mdRender(text); else span.textContent = text || '';
      d.appendChild(span); thread.appendChild(d); thread.scrollTop = thread.scrollHeight;
      return { d, span };
    }
    function addStep(icon, title, bodyHtml){
      clearEmpty();
      const d = document.createElement('div'); d.className = 'wsstep';
      d.innerHTML = `<span class="si">${icon}</span><div class="sc"><div class="st">${esc(title)}</div><div class="sb">${bodyHtml||''}</div></div>`;
      thread.appendChild(d); thread.scrollTop = thread.scrollHeight; return d;
    }
    const scroll = () => { thread.scrollTop = thread.scrollHeight; };

    // ---- mode segmented control ----
    function applyMode(){
      $$('#wsmode button').forEach(b => b.classList.toggle('active', b.dataset.m === mode));
      document.querySelector('.wswrap').classList.toggle('agentmode', mode==='agent');
      $('#wsinput').placeholder = mode==='agent' ? L.ph_agent : L.ph_chat;
      localStorage.setItem('ws_mode', mode);
    }
    $$('#wsmode button').forEach(b => b.onclick = () => { if(busy) return; mode = b.dataset.m; applyMode(); });

    // ---- professional toggles ----
    function bindTgl(id, key){
      const el = $('#'+id); if(!el) return;
      el.classList.toggle('on', !!tg[key]);
      el.onclick = () => { tg[key] = !tg[key]; el.classList.toggle('on', tg[key]);
        if(key!=='full') localStorage.setItem('ws_'+key, tg[key]?'1':'0');
        toast('info', `${el.textContent.trim()} ${tg[key]?'on':'off'}`, ''); };
    }
    bindTgl('tg-deep','deep'); bindTgl('tg-web','web'); bindTgl('tg-full','full');

    // ---- model select (with ✨ Auto) ----
    (async () => {
      let list = []; try { list = await api('/models'); } catch(e){}
      const usable = list.filter(m => (m.tags||[]).some(t => ['chat','control','coding','reasoning','vision'].includes(t)));
      const cur = State.settings.default_local_model;
      $('#wsmodel').innerHTML = `<option value="auto">${L.auto}</option>` +
        usable.map(m => `<option value="${esc(m.name)}" ${m.name===cur?'selected':''}>${esc(m.name)}${m.tags&&m.tags.length?' · '+m.tags.join(', '):''}</option>`).join('');
      $('#wsmodel').value = localStorage.getItem('ws_model') || 'auto';
      updateAutoHint();
    })();
    $('#wsmodel').onchange = () => { localStorage.setItem('ws_model', $('#wsmodel').value); updateAutoHint(); };
    async function updateAutoHint(){
      const h = $('#wsautohint'); if(!h) return;
      if($('#wsmodel').value !== 'auto'){ h.textContent=''; return; }
      try { const r = await post('/model/auto', {prompt:$('#wsinput').value, deepthink:tg.deep, mode});
        h.textContent = r.model ? `→ ${r.model} (${r.reason})` : ''; } catch(e){ h.textContent=''; }
    }

    // ---- attachments (any file) ----
    function renderAtts(){
      $('#wsatts').innerHTML = attached.map((a,i)=>`<span class="attcard">${fileIcon(a.filename)} <b>${esc(a.filename)}</b> <span class="muted">${(a.size/1024).toFixed(0)}KB</span> <span class="x" data-rm="${i}">✕</span></span>`).join('');
      $$('#wsatts [data-rm]').forEach(b=>b.onclick=()=>{attached.splice(+b.dataset.rm,1);renderAtts();});
    }
    function uploadFile(file){
      const fd = new FormData(); fd.append('file', file);
      const card = document.createElement('span'); card.className='attcard'; card.textContent='⏳ '+file.name;
      $('#wsatts').appendChild(card);
      fetch('/api/upload',{method:'POST',body:fd}).then(r=>r.json()).then(r=>{
        card.remove();
        if(r.ok){ attached.push(r); renderAtts(); toast('success','Attached', `${r.filename} · ${r.chars} chars`); }
        else toast('error','Upload failed', r.error||''); }).catch(()=>{card.remove();toast('error','Upload failed','');});
    }
    // ---- open a file on disk and work on it (Claude-Desktop style) ----
    $('#tg-open').onclick = async () => {
      const path = prompt(AR?'افتح ملفاً (المسار الكامل):':'Open file (full path):');
      if(!path) return;
      let r; try { r = await api('/file/read?path=' + encodeURIComponent(path)); } catch(e){ r={ok:false,error:String(e)}; }
      if(r && r.ok){ workingFile = {path:r.path, name:r.name, content:r.content};
        clearEmpty();
        const d=document.createElement('div'); d.className='wsfilecard';
        d.innerHTML=`<div class="wsfh">📄 <b>${esc(r.name)}</b> <span class="muted">${(r.content.length/1024).toFixed(0)} KB</span> <span class="x" id="wsfclose">✕</span></div><pre class="code">${esc(r.content.slice(0,2000))}${r.content.length>2000?'\n…':''}</pre>`;
        $('#wsthread').appendChild(d); $('#wsthread').scrollTop=$('#wsthread').scrollHeight;
        $('#wsfclose').onclick=()=>{workingFile=null;d.remove();toast('info','Closed file','');};
        $('#wsinput').placeholder = (AR?'اطلب تعديلاً على ':'Ask to edit ')+r.name+'…';
        toast('success', (AR?'فُتح الملف':'Opened'), r.name+' — '+(AR?'اطلب تعديلاً وسأحفظه':'ask for an edit and save it back'));
      } else toast('error', (AR?'تعذّر الفتح':'Cannot open'), (r&&r.error)||'');
    };
    function saveBtn(aiEl){
      if(!workingFile) return;
      const b=document.createElement('button'); b.className='btn sm p wssave'; b.textContent='💾 '+(AR?'احفظ إلى ':'Save to ')+workingFile.name;
      b.onclick=async ()=>{ const raw=aiEl.span.dataset.raw||aiEl.span.textContent||'';
        const m=raw.match(/```[a-zA-Z0-9]*\n([\s\S]*?)```/); const content=m?m[1]:raw;
        const r=await post('/file/write',{path:workingFile.path, content});
        if(r&&r.ok){ workingFile.content=content; toast('success',(AR?'حُفظ':'Saved'), workingFile.name); b.textContent='✓ '+(AR?'حُفظ':'Saved'); }
        else toast('error',(AR?'تعذّر الحفظ':'Save failed'), (r&&r.error)||''); };
      aiEl.d.appendChild(b);
    }
    $('#tg-attach').onclick = () => $('#wsfile').click();
    // ---- media buttons (capture / image / video) → render in the chat ----
    $('#tg-shot').onclick = async () => { clearEmpty(); addMsg('user', AR?'📸 التقط الشاشة':'📸 Capture screen');
      const r = await post('/screen/shot'); if(r&&r.file) showMedia(r.file, AR?'لقطة الشاشة':'screenshot','shot'); else toast('error','Capture failed',''); };
    $('#tg-img').onclick = async () => { const p = prompt(AR?'صف الصورة المطلوبة:':'Describe the image to generate:'); if(!p) return;
      addMsg('user', '🎨 '+p); const r = await post('/toolkit/image',{prompt:p,model:'sdxl'}); if(r&&r.file) showMedia(r.file, p, 'img', r.job); else toast('error','Image gen failed',''); };
    $('#tg-vid').onclick = async () => { const p = prompt(AR?'صف الفيديو المطلوب:':'Describe the video to generate:'); if(!p) return;
      addMsg('user', '🎬 '+p); const r = await post('/toolkit/video',{prompt:p}); if(r&&r.file){ showMedia(r.file, p, 'video', r.job); toast('info',AR?'توليد فيديو (قد يستغرق دقائق)':'Generating video (may take minutes)',''); } };
    $('#wsfile').onchange = e => { [...e.target.files].forEach(uploadFile); e.target.value=''; };
    thread.addEventListener('dragover', e=>{e.preventDefault();thread.classList.add('over');});
    thread.addEventListener('dragleave', ()=>thread.classList.remove('over'));
    thread.addEventListener('drop', e=>{e.preventDefault();thread.classList.remove('over');[...e.dataTransfer.files].forEach(uploadFile);});

    // ---- busy state ----
    function setBusy(b){ busy=b; $('#wssend').style.display=b?'none':''; $('#wsstop').style.display=(b&&mode==='agent')?'':'none'; }

    // ---- media: render a generated/captured image or video. If a jobId is given, wait on JOB STATUS
    //      (no 404 polling); only load the file once the job is done. ----
    function renderMedia(m, file, label, kind){
      if(kind==='video'){ m.span.innerHTML=`<video class="genvid" controls src="${file}?t=${Date.now()}"></video><div class="muted" style="font-size:11px">${esc(label)}</div>`; }
      else { m.span.innerHTML=`<a href="${file}" target="_blank"><img class="genimg" src="${file}?t=${Date.now()}"></a><div class="muted" style="font-size:11px">${esc(label)}</div>`;
        const rf=document.createElement('button'); rf.className='btn sm'; rf.style.marginTop='6px'; rf.textContent='✨ '+(AR?'تحسين/تعديل':'Refine / edit');
        rf.onclick=async()=>{ const np=prompt(AR?'صف التعديل المطلوب على الصورة:':'Describe how to change this image:', label); if(!np)return;
          const r=await post('/toolkit/image',{prompt:np,model:'sdxl',init_image:file,denoise:0.6}); if(r&&r.file) showMedia(r.file,np,'img',r.job); else toast('error',AR?'فشل التحسين':'Refine failed',(r&&r.error)||''); };
        m.span.appendChild(rf); }
      scroll();
    }
    async function showMedia(file, label, kind, jobId){
      const m = addMsg('ai',''); m.span.innerHTML = `<div class="muted">${kind==='video'?'🎬':kind==='shot'?'📸':'🎨'} ${esc(label)} — ${AR?'جارٍ التحضير…':'generating…'}</div>`;
      if(!jobId){ renderMedia(m, file, label, kind); return; }   // screenshot: instant
      const max = kind==='video'?180:60;
      for(let i=0;i<max;i++){
        await new Promise(r=>setTimeout(r,1000));
        let done=false, ok=true;
        try{ const procs=await api('/processes'); const j=(procs||[]).find(p=>p.id===jobId);
          if(j && (j.status==='done'||j.status==='error'||j.status==='stopped'||j.exit_code!=null)){ done=true; ok=(j.exit_code===0||j.status==='done'); } }catch(e){}
        if(done){ if(ok){ await new Promise(r=>setTimeout(r,400)); renderMedia(m, file, label, kind); }
          else m.span.innerHTML='<span class="muted">⚠️ '+(AR?'فشل التوليد':'generation failed')+'</span>'; return; }
      }
      m.span.innerHTML='<span class="muted">⚠️ '+(AR?'انتهى الوقت':'timed out')+'</span>';
    }
    async function tryMediaCommand(v){
      const s=v.trim();
      // screenshot / what's on screen (chat mode → capture + optionally describe)
      if(/^(take|grab|capture)?\s*(a\s+)?(screenshot|screen ?shot|capture (my )?screen)\b/i.test(s) || /^(خذ |التقط )?(لقطة شاشة|صورة الشاشة)/.test(s)){
        addMsg('user', v); const r=await post('/screen/shot'); if(r&&r.file) showMedia(r.file, AR?'لقطة الشاشة':'screenshot','shot'); else toast('error','Capture failed',''); return true;
      }
      if(/^(what'?s| what is)\b.*\b(on (my )?(screen|desktop))/i.test(s) || /(ما(ذا)?|شو)\s+(على|في)\s+(شاشتي|الشاشة|سطح المكتب)/.test(s)){
        addMsg('user', v); const out=addMsg('ai', AR?'⏳ أنظر إلى شاشتك…':'⏳ looking at your screen…');
        const r=await post('/screen/describe',{}); out.span.innerHTML = mdRender(r.description||('error: '+(r.error||''))); if(r.file){const im=document.createElement('img');im.className='genimg';im.src=r.file+'?t='+Date.now();im.style.marginTop='8px';out.d.appendChild(im);} return true;
      }
      // image generation
      let m=s.match(/^(?:generate|create|make|draw|render|اصنع|ارسم|ولّ?د)\s+(?:an?\s+|me\s+|صورة\s+)?(?:image|picture|photo|drawing|art|صورة|رسم)(?:\s+of)?[:\s]+(.+)/i);
      if(m){ addMsg('user', v);
        const r=await post('/toolkit/image',{prompt:m[1],model:'sdxl'});
        if(r&&r.file) showMedia(r.file, m[1], 'img', r.job); else toast('error','Image gen failed',''); return true; }
      // video generation
      m=s.match(/^(?:generate|create|make|ولّ?د|اصنع)\s+(?:an?\s+|me\s+)?(?:video|clip|animation|movie|فيديو|مقطع)(?:\s+of)?[:\s]+(.+)/i);
      if(m){ addMsg('user', v); const r=await post('/toolkit/video',{prompt:m[1]});
        if(r&&r.file) showMedia(r.file, m[1], 'video', r.job); else { addMsg('ai', AR?'🎬 بدأ توليد الفيديو في الخلفية — سيظهر في الملفات.':'🎬 video generation started in the background — it will appear in /files.'); }
        toast('info', AR?'توليد فيديو':'Generating video', m[1].slice(0,40)); return true; }
      return false;
    }

    // ---- send ----
    // If hands-free is waiting on a turn that won't emit a chat event (media command / !cmd), keep the
    // voice loop alive instead of freezing — resume listening.
    function hfResumeIfWaiting(){ if(hf.on && hf.waiting){ hf.waiting=false; $('#wshf').classList.remove('rec'); hfListenOnce(); } }
    async function send(){
      const v = $('#wsinput').value.trim();
      if((!v && !attached.length) || busy) return;
      if(mode==='chat' && v && !v.startsWith('!') && await tryMediaCommand(v)){ $('#wsinput').value=''; $('#wsinput').style.height='auto'; hfResumeIfWaiting(); return; }
      const model = $('#wsmodel').value || 'auto';
      // chat: !cmd quick exec
      if(mode==='chat' && v.startsWith('!')){
        const cmd=v.slice(1).trim(); addMsg('user', v); $('#wsinput').value='';
        const out=addMsg('ai',''); out.span.textContent='⌨️ $ '+cmd+'\n';
        const r=await execCommand(cmd); if(!(r&&r.job)) out.span.textContent+= (r===null?'(cancelled)':('error: '+((r&&r.error)||'failed'))); hfResumeIfWaiting(); return;
      }
      let context='', markers='';
      if(attached.length){ context=attached.map(a=>`### File: ${a.filename}\n${a.text}`).join('\n\n');
        markers=attached.map(a=>`⟦file:${a.filename}|${a.size}⟧`).join('')+'\n'; }
      if(workingFile){ context=(context?context+'\n\n':'')+`### Working file: ${workingFile.name}\nWhen asked to edit it, reply with the FULL new file content in ONE code block.\n\`\`\`\n${workingFile.content.slice(0,12000)}\n\`\`\``; }
      lastUser=v; addMsg('user', markers+v); $('#wsinput').value=''; $('#wsinput').style.height='auto';
      setBusy(true);
      if(mode==='agent'){
        let tools = SET_TOOLS();   // all agent tools (so it can decide to capture/record/monitor)
        lastAgentRun = { goal:v, model, deepthink:tg.deep, unrestricted:tg.full };  // IDEA-3: enable "save as workflow"
        post('/agent', { goal:v, model, dry_run:false, unrestricted:tg.full,
                         deepthink:tg.deep, tools, websearch:tg.web });
        usage('agent');
      } else {
        const body = { prompt:markers+v, model, cid:State.currentCid, deepthink:tg.deep, websearch:tg.web };
        if(context) body.context=context;
        post('/chat-send', body); usage('chat');
      }
      attached=[]; renderAtts();
    }
    // agent gets the full toolset (incl. screen capture/record/monitor + control) so IT decides when to use them
    function SET_TOOLS(){ try{ const s=JSON.parse(localStorage.getItem('agent_set2')||'{}'); return Array.isArray(s.tools)?s.tools:null; }catch(e){ return null; } }

    $('#wssend').onclick = send;
    $('#wsstop').onclick = () => { post('/agent/stop',{}); post('/control/panic',{}).catch(()=>{}); toast('warn','Stopping…',''); };
    $('#wsclear').onclick = () => { thread.innerHTML='<div class="wsempty"><div class="empty-orb">✨</div><p>'+(AR?'محادثة جديدة':'New conversation')+'</p></div>'; State.currentCid=null; };
    const ta=$('#wsinput');
    ta.addEventListener('input', ()=>{ ta.style.height='auto'; ta.style.height=Math.min(ta.scrollHeight,160)+'px'; clearTimeout(ta._t); ta._t=setTimeout(updateAutoHint,500); });
    ta.addEventListener('keydown', e=>{ if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); send(); } });
    $('#wsmic').onclick = () => dictate('#wsinput','#wsmic');

    // ---- IDEA-4: hands-free voice conversation (listen → STT → chat → TTS → listen again) ----
    // Records a phrase with silence detection, transcribes it, sends it as a chat turn; when the reply
    // finishes (chat 'end' handler below), it's spoken via local Piper TTS and listening resumes.
    async function hfListenOnce(){
      if(!hf.on) return;
      if(!navigator.mediaDevices||!window.MediaRecorder){ toast('error','Mic unavailable',''); hfStop(); return; }
      let stream; try{ stream=await navigator.mediaDevices.getUserMedia({audio:true}); }
      catch(e){ toast('error','Microphone blocked','Allow mic access'); hfStop(); return; }
      const mr=new MediaRecorder(stream); const chunks=[];
      mr.ondataavailable=e=>{ if(e.data&&e.data.size) chunks.push(e.data); };
      // silence detection via Web Audio analyser
      const ac=new (window.AudioContext||window.webkitAudioContext)(); const src=ac.createMediaStreamSource(stream);
      const an=ac.createAnalyser(); an.fftSize=512; src.connect(an); const buf=new Uint8Array(an.fftSize);
      let spoke=false, silence=0; const t0=Date.now();
      const tick=setInterval(()=>{
        an.getByteTimeDomainData(buf); let sum=0; for(let i=0;i<buf.length;i++){ const v=(buf[i]-128)/128; sum+=v*v; }
        const rms=Math.sqrt(sum/buf.length);
        if(rms>0.045){ spoke=true; silence=0; } else if(spoke){ silence+=120; }
        const maxed=Date.now()-t0>15000;          // hard cap 15s
        if((spoke && silence>1300) || maxed){ clearInterval(tick); if(mr.state==='recording') mr.stop(); }
      },120);
      mr.onstop=async()=>{ clearInterval(tick); stream.getTracks().forEach(t=>t.stop()); try{ac.close();}catch(e){}
        const blob=new Blob(chunks,{type:'audio/webm'});
        if(blob.size<800){ if(hf.on) hfListenOnce(); return; }   // nothing said → keep listening
        const fd=new FormData(); fd.append('audio',blob,'rec.webm'); fd.append('lang',State.lang);
        let r; try{ r=await fetch('/api/stt',{method:'POST',body:fd}).then(x=>x.json()); }catch(e){ r={}; }
        if(r&&r.text&&r.text.trim()){ $('#wsinput').value=r.text.trim(); hf.waiting=true; send(); }
        else if(hf.on){ hfListenOnce(); }                        // no speech recognised → listen again
      };
      mr.start(); $('#wshf').classList.add('rec'); toast('info','🎙️ '+(AR?'أستمع…':'Listening…'), AR?'تحدّث ثم توقّف':'speak, then pause');
    }
    function hfStop(){ hf.on=false; hf.waiting=false; const b=$('#wshf'); if(b) b.classList.remove('rec','on'); }
    async function hfSpeakAndContinue(text){     // called from the chat 'end' handler
      hf.waiting=false; $('#wshf').classList.remove('rec');
      if(text){ try{ await post('/tts',{text:text.slice(0,1200)}); }catch(e){} }
      if(hf.on) hfListenOnce();
    }
    $('#wshf').onclick = () => {
      if(hf.on){ hfStop(); toast('info',AR?'أُوقفت المحادثة الصوتية':'Hands-free off',''); return; }
      if(mode!=='chat'){ mode='chat'; applyMode(); }             // hands-free is a chat experience
      hf.on=true; $('#wshf').classList.add('on'); hfListenOnce();
    };

    applyMode();

    // ---- live streams ----
    const subs = [];
    subs.push(bus.on('chat', m => {
      if(m.ev==='start'){ curAI = addMsg('ai',''); curAI.span.dataset.raw=''; }
      else if(m.ev==='token' && curAI){ curAI.span.dataset.raw += (m.text||''); curAI.span.innerHTML = mdRender(curAI.span.dataset.raw); scroll(); }
      else if(m.ev==='end'){ if(curAI){ if(curAI.span.dataset.raw) curAI.span.innerHTML=mdRender(curAI.span.dataset.raw);
          if(m.sources && m.sources.length){ const s=document.createElement('div'); s.className='wssrc';
            s.innerHTML='📎 '+m.sources.map(x=>x.url?`<a href="${esc(x.url)}" target="_blank">${esc(x.doc)}</a>`:esc(x.doc)).join(' · '); curAI.d.appendChild(s);}
          if(workingFile) saveBtn(curAI); }
          if(m.tokens!=null) $('#wstok').textContent=m.tokens+' tok';
          const reply=(curAI&&curAI.span.dataset.raw)||''; curAI=null; setBusy(false);
          if(hf.on && hf.waiting) hfSpeakAndContinue(reply); }   // IDEA-4: speak the reply, then listen again
      else if(m.ev==='error'){ addMsg('ai','⚠️ '+(m.text||'error')); curAI=null; setBusy(false);
          if(hf.on && hf.waiting){ hf.waiting=false; $('#wshf').classList.remove('rec'); hfListenOnce(); } }
    }));
    subs.push(bus.on('agent', m => {
      if(m.ev==='start'){ maxSteps=m.max_steps||8; }
      else if(m.ev==='thought'){ addStep('🧠', (AR?'تفكير':'Thinking')+(m.step?' · '+(AR?'خطوة ':'step ')+m.step:''), esc(m.text||'')); }
      else if(m.ev==='action'){ addStep('⚙️', (AR?'إجراء: ':'Action: ')+esc(m.action||''), `<code class="ic">${esc(JSON.stringify(m.args||{}).slice(0,300))}</code>`); }
      else if(m.ev==='observation'){ addStep('👁', (AR?'النتيجة':'Result'), `<pre class="code">${esc((m.text||'').slice(0,1000))}</pre>`); }
      else if(m.ev==='ask'){ addStep('❓', (AR?'يحتاج توضيحاً':'Needs clarification'), esc(m.text||'')); setBusy(false); }
      else if(m.ev==='final'){ const d=addMsg('ai', m.text||''); setBusy(false);
        if(lastAgentRun){ const run=lastAgentRun; const btn=document.createElement('button');
          btn.className='btn sm'; btn.style.marginTop='8px'; btn.textContent='💾 '+(AR?'حفظ كسير عمل':'Save as workflow');
          btn.onclick=async()=>{ const name=prompt(AR?'اسم سير العمل:':'Workflow name:', run.goal.slice(0,60)); if(!name)return;
            const r=await post('/agent/save-workflow', {...run, name});
            toast(r&&r.ok?'success':'error', r&&r.ok?(AR?'تم الحفظ':'Saved'):(AR?'فشل':'Failed'), r&&r.ok?(AR?'في صفحة سير العمل':'see Workflows'):''); btn.disabled=!!(r&&r.ok); };
          d.span.appendChild(document.createElement('br')); d.span.appendChild(btn); } }
      else if(m.ev==='stopped'){ addStep('⏹', (AR?'تم الإيقاف':'Stopped'), ''); setBusy(false); }
      else if(m.ev==='error'){ addStep('❌', (AR?'خطأ':'Error'), esc(m.text||'')); setBusy(false); }
      else if(m.ev==='done'){ setBusy(false); }
    }));
    subs.push(()=>hfStop());   // IDEA-4: stop hands-free when leaving the page
    return subs;
  }
  return { html, mount };
}
