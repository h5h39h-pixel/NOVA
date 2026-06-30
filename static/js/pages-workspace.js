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
        <span class="spacer"></span>
        <button class="btn" id="wsmic" data-tip="${AR?'إدخال صوتي':'Voice input'}">🎤</button>
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
    let attached = [], curAI = null, lastUser = '', busy = false, maxSteps = 8;
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
    $('#tg-attach').onclick = () => $('#wsfile').click();
    $('#wsfile').onchange = e => { [...e.target.files].forEach(uploadFile); e.target.value=''; };
    thread.addEventListener('dragover', e=>{e.preventDefault();thread.classList.add('over');});
    thread.addEventListener('dragleave', ()=>thread.classList.remove('over'));
    thread.addEventListener('drop', e=>{e.preventDefault();thread.classList.remove('over');[...e.dataTransfer.files].forEach(uploadFile);});

    // ---- busy state ----
    function setBusy(b){ busy=b; $('#wssend').style.display=b?'none':''; $('#wsstop').style.display=(b&&mode==='agent')?'':'none'; }

    // ---- send ----
    async function send(){
      const v = $('#wsinput').value.trim();
      if((!v && !attached.length) || busy) return;
      const model = $('#wsmodel').value || 'auto';
      // chat: !cmd quick exec
      if(mode==='chat' && v.startsWith('!')){
        const cmd=v.slice(1).trim(); addMsg('user', v); $('#wsinput').value='';
        const out=addMsg('ai',''); out.span.textContent='⌨️ $ '+cmd+'\n';
        const r=await execCommand(cmd); if(!(r&&r.job)) out.span.textContent+= (r===null?'(cancelled)':('error: '+((r&&r.error)||'failed'))); return;
      }
      let context='', markers='';
      if(attached.length){ context=attached.map(a=>`### File: ${a.filename}\n${a.text}`).join('\n\n');
        markers=attached.map(a=>`⟦file:${a.filename}|${a.size}⟧`).join('')+'\n'; }
      lastUser=v; addMsg('user', markers+v); $('#wsinput').value=''; $('#wsinput').style.height='auto';
      setBusy(true);
      if(mode==='agent'){
        let tools = SET_TOOLS();   // all agent tools (so it can decide to capture/record/monitor)
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

    applyMode();

    // ---- live streams ----
    const subs = [];
    subs.push(bus.on('chat', m => {
      if(m.ev==='start'){ curAI = addMsg('ai',''); curAI.span.dataset.raw=''; }
      else if(m.ev==='token' && curAI){ curAI.span.dataset.raw += (m.text||''); curAI.span.innerHTML = mdRender(curAI.span.dataset.raw); scroll(); }
      else if(m.ev==='end'){ if(curAI){ if(curAI.span.dataset.raw) curAI.span.innerHTML=mdRender(curAI.span.dataset.raw);
          if(m.sources && m.sources.length){ const s=document.createElement('div'); s.className='wssrc';
            s.innerHTML='📎 '+m.sources.map(x=>x.url?`<a href="${esc(x.url)}" target="_blank">${esc(x.doc)}</a>`:esc(x.doc)).join(' · '); curAI.d.appendChild(s);} }
          if(m.tokens!=null) $('#wstok').textContent=m.tokens+' tok'; curAI=null; setBusy(false); }
      else if(m.ev==='error'){ addMsg('ai','⚠️ '+(m.text||'error')); curAI=null; setBusy(false); }
    }));
    subs.push(bus.on('agent', m => {
      if(m.ev==='start'){ maxSteps=m.max_steps||8; }
      else if(m.ev==='thought'){ addStep('🧠', (AR?'تفكير':'Thinking')+(m.step?' · '+(AR?'خطوة ':'step ')+m.step:''), esc(m.text||'')); }
      else if(m.ev==='action'){ addStep('⚙️', (AR?'إجراء: ':'Action: ')+esc(m.action||''), `<code class="ic">${esc(JSON.stringify(m.args||{}).slice(0,300))}</code>`); }
      else if(m.ev==='observation'){ addStep('👁', (AR?'النتيجة':'Result'), `<pre class="code">${esc((m.text||'').slice(0,1000))}</pre>`); }
      else if(m.ev==='ask'){ addStep('❓', (AR?'يحتاج توضيحاً':'Needs clarification'), esc(m.text||'')); setBusy(false); }
      else if(m.ev==='final'){ const d=addMsg('ai', m.text||''); setBusy(false); }
      else if(m.ev==='stopped'){ addStep('⏹', (AR?'تم الإيقاف':'Stopped'), ''); setBusy(false); }
      else if(m.ev==='error'){ addStep('❌', (AR?'خطأ':'Error'), esc(m.text||'')); setBusy(false); }
      else if(m.ev==='done'){ setBusy(false); }
    }));
    return subs;
  }
  return { html, mount };
}
