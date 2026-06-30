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
      <label class="atog mt" style="display:inline-flex"><input type="checkbox" id="ppv"> use the vision model (read screen via qwen2.5‑VL instead of OCR)</label>`;
    return '<p class="muted mt" style="font-size:12px">No parameters needed.</p>';}
  function buildParams(a){const v=$('#pp')?$('#pp').value:'';
    if(a==='screen_if'){const ta=$('#pp2')?$('#pp2').value:'notify';const tx=$('#pp3')?$('#pp3').value:'';
      return {match:v,then_action:ta,then_params:(ta==='command'?{command:tx}:{text:tx}),vision:!!($('#ppv')&&$('#ppv').checked)};}
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
