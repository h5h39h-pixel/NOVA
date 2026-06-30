// -*- part of the Nova SPA (framework-free, global scope, load order matters) -*-
// Agent + data pages — Agent, Learning, A/B Test, Knowledge, Automation, Workflows, Batch.
// Split from the original monolithic pages.js (HON-11). Loaded after core.js, before shell.js.

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
  const TN={kb_search:AR?'بحث المعرفة':'KB search',web_search:AR?'بحث الويب':'web search',run_command:AR?'أمر':'command',browse:AR?'تصفّح':'browse',
    open_url:AR?'فتح رابط':'open URL',understand:AR?'اقرأ وافهم':'understand',see_screen:AR?'رؤية الشاشة':'see screen',read_screen:AR?'قراءة الشاشة':'read screen',screenshot:AR?'لقطة شاشة':'screenshot',act_on_screen:AR?'التحكم بالشاشة':'act on screen',
    screen_awareness:AR?'وعي النوافذ':'window awareness',find_element:AR?'إيجاد عنصر':'find element',control:AR?'تحكّم دقيق':'precise control',
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
  const TOOLS=[['kb_search','📚'],['web_search','🌐'],['run_command','⌨️'],['browse','🧭'],['open_url','🪟'],
    ['understand','🔎'],['see_screen','👁'],['read_screen','🔤'],['screenshot','📸'],['act_on_screen','🖱️'],
    ['screen_awareness','🪟'],['find_element','🎯'],['control','🎮'],
    ['generate_video','🎥'],['notify','🔔'],['speak','🔊'],['read_file','📄'],['write_file','💾'],['schedule','⏰']];
  // key bumped to v2 so the new Phase 8 tools (understand/control/web_search/…) default to enabled.
  const SET=Object.assign({temp:0.2,max:8,tools:TOOLS.map(t=>t[0])},JSON.parse(localStorage.getItem('agent_set2')||'{}'));
  const saveSet=()=>localStorage.setItem('agent_set2',JSON.stringify(SET));
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
          <label class="atog" data-tip="${AR?'تفكير عميق — خطوة بخطوة':'DeepThink — reason step by step'}"><input type="checkbox" id="adeep"> 🧠 ${AR?'تفكير عميق':'DeepThink'}</label>
          <label class="atog" data-tip="${AR?'بحث ويب مباشر':'Live web search'}"><input type="checkbox" id="aweb"> 🌐 ${AR?'بحث':'Web'}</label>
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
    let tools=SET.tools;
    if($('#aweb')&&$('#aweb').checked&&Array.isArray(tools)&&!tools.includes('web_search'))tools=[...tools,'web_search'];
    post('/agent',{goal:g,model:$('#amodel').value,dry_run:$('#adry').checked,unrestricted:$('#afull').checked,
      temperature:SET.temp,max_steps:SET.max,tools,deepthink:($('#adeep')&&$('#adeep').checked)});usage('agent');}
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
