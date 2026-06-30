/* ============================ core.js ============================
   DOM/api helpers, icon engine, State, event bus, i18n, router, render helpers.
   Part of the AI Control Center SPA. Loaded in order: core -> pages -> shell.
   Single shared global scope (no bundler); load order matters. */
/* ============================ AI Control Center SPA ============================ */
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const api=(p,o)=>fetch('/api'+p,o).then(async r=>{
  let j; try{j=await r.json()}catch(_){j={}}
  if(!r.ok){const m=(j&&j.error)||('HTTP '+r.status);
    if(window.__toast)window.__toast('error',r.status===429?'Rate limited':(r.status===401?'Sign-in required':'Request failed'),m);}
  return j;
}).catch(e=>{if(window.__toast)window.__toast('error','Network error',String((e&&e.message)||e));return {error:String(e)};});
const post=(p,b)=>api(p,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b||{})});
const del=p=>api(p,{method:'DELETE'});
// Run a terminal command, asking for confirmation if the backend flags it destructive (HTTP 409).
// Raw fetch (not the api() wrapper) so the 409 confirm path doesn't show a generic error toast.
async function execCommand(cmd, confirmed){
  let r; try{ r=await fetch('/api/exec',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({command:cmd,confirm:!!confirmed})}).then(x=>x.json()); }catch(e){ r={error:String(e)} }
  if(r&&r.needs_confirm){ return confirm(r.reason||'This command looks destructive. Run it anyway?') ? execCommand(cmd,true) : null; }
  return r;
}
const esc=s=>(s==null?'':String(s)).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
/* ---- Professional icons: map every emoji to a consistent Font Awesome vector icon (whole dashboard) ---- */
const EMOJI_FA={
  '⚡':'fa-solid fa-bolt','📊':'fa-solid fa-chart-column','⌨':'fa-solid fa-keyboard','💬':'fa-solid fa-comment-dots',
  '🤖':'fa-solid fa-robot','🧩':'fa-solid fa-puzzle-piece','🛠':'fa-solid fa-screwdriver-wrench','🎬':'fa-solid fa-clapperboard',
  '🎥':'fa-solid fa-video','🎓':'fa-solid fa-graduation-cap','📈':'fa-solid fa-chart-line','🆚':'fa-solid fa-code-compare',
  '📚':'fa-solid fa-book','🧠':'fa-solid fa-brain','⏰':'fa-solid fa-clock','🔗':'fa-solid fa-link','📦':'fa-solid fa-box',
  '🌐':'fa-solid fa-globe','⚙':'fa-solid fa-gear','🔔':'fa-solid fa-bell','🔕':'fa-solid fa-bell-slash',
  '🔍':'fa-solid fa-magnifying-glass','🔎':'fa-solid fa-magnifying-glass','☀':'fa-solid fa-sun','🌙':'fa-solid fa-moon',
  '🔒':'fa-solid fa-lock','🔓':'fa-solid fa-lock-open','👁':'fa-solid fa-eye','📤':'fa-solid fa-arrow-up-from-bracket',
  '📥':'fa-solid fa-arrow-down-to-bracket','🗂':'fa-solid fa-layer-group','⏹':'fa-solid fa-stop','🔁':'fa-solid fa-rotate-right',
  '📨':'fa-solid fa-paper-plane','🎯':'fa-solid fa-bullseye','✅':'fa-solid fa-circle-check','❌':'fa-solid fa-circle-xmark',
  '❓':'fa-solid fa-circle-question','🔊':'fa-solid fa-volume-high','📄':'fa-solid fa-file-lines','💾':'fa-solid fa-floppy-disk',
  '🪟':'fa-solid fa-window-maximize','🖥':'fa-solid fa-desktop','📂':'fa-solid fa-folder-open','📁':'fa-solid fa-folder',
  '🌡':'fa-solid fa-temperature-half','🔢':'fa-solid fa-list-ol','🧰':'fa-solid fa-toolbox','💡':'fa-solid fa-lightbulb',
  '🚀':'fa-solid fa-rocket','📝':'fa-solid fa-pen-to-square','🌱':'fa-solid fa-seedling','🧬':'fa-solid fa-dna',
  '✨':'fa-solid fa-wand-magic-sparkles','📘':'fa-solid fa-book','🌾':'fa-solid fa-wheat-awn','🎨':'fa-solid fa-palette',
  '🔥':'fa-solid fa-fire','⭐':'fa-solid fa-star','🏆':'fa-solid fa-trophy','📡':'fa-solid fa-satellite-dish',
  '👋':'fa-solid fa-hand','🗑':'fa-solid fa-trash','🔋':'fa-solid fa-battery-full','📋':'fa-solid fa-clipboard',
  '⏳':'fa-solid fa-hourglass-half','📅':'fa-solid fa-calendar','🟢':'fa-solid fa-circle','📁':'fa-solid fa-folder',
  '🎙':'fa-solid fa-microphone','🔧':'fa-solid fa-wrench','💻':'fa-solid fa-laptop-code','📶':'fa-solid fa-signal'};
const stripVS=s=>s.replace(/️/g,'');
const ICON_LABEL=c=>(c||'').split(/\s+/).pop().replace(/^fa-/,'').replace(/-/g,' ');
const _ekeys=Object.keys(EMOJI_FA).sort((a,b)=>b.length-a.length).map(k=>k.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'\\uFE0F?');
const EMOJI_RE=new RegExp('('+_ekeys.join('|')+')','g');
const _hasEmoji=s=>{for(const k in EMOJI_FA){if(s.indexOf(k)>=0)return true}return false};
const _SKIP={SCRIPT:1,STYLE:1,TEXTAREA:1,INPUT:1,CODE:1,PRE:1,I:1,svg:1,SVG:1};
function faIcons(root){
  if(!root)return;const start=root.nodeType===1?root:root.parentNode;if(!start||!start.ownerDocument)return;
  let walker;try{walker=document.createTreeWalker(start,NodeFilter.SHOW_TEXT,{acceptNode(n){
    if(!n.nodeValue||!_hasEmoji(n.nodeValue))return NodeFilter.FILTER_REJECT;
    let p=n.parentNode;while(p&&p!==start.parentNode){if(_SKIP[p.nodeName])return NodeFilter.FILTER_REJECT;p=p.parentNode;}
    return NodeFilter.FILTER_ACCEPT;}});}catch(e){return}
  const targets=[];let nd;while(nd=walker.nextNode())targets.push(nd);
  targets.forEach(n=>{const s=n.nodeValue;const frag=document.createDocumentFragment();let last=0,mm;EMOJI_RE.lastIndex=0;
    while(mm=EMOJI_RE.exec(s)){if(mm.index>last)frag.appendChild(document.createTextNode(s.slice(last,mm.index)));
      const cls=EMOJI_FA[stripVS(mm[0])];
      if(cls){const i=document.createElement('i');i.className=cls+' emoji-ic';i.setAttribute('role','img');i.setAttribute('aria-label',ICON_LABEL(cls));frag.appendChild(i);}
      else frag.appendChild(document.createTextNode(mm[0]));
      last=mm.index+mm[0].length;}
    if(last<s.length)frag.appendChild(document.createTextNode(s.slice(last)));
    if(frag.childNodes.length)n.parentNode.replaceChild(frag,n);});
}
const tw=faIcons;  // alias (back-compat with existing calls)
function initIcons(){
  faIcons(document.body);
  const obs=new MutationObserver(muts=>{for(const m of muts)for(const n of m.addedNodes){if(n.nodeType===1||n.nodeType===3)faIcons(n);}});
  obs.observe(document.body,{childList:true,subtree:true});
}
const fmtTime=ts=>new Date(ts*1000).toLocaleTimeString();
const State={settings:{},lang:localStorage.getItem('lang')||'en',metrics:null,services:{},
  buf:{gpu:[],vram:[],cpu:[],ram:[]},unseen:0};

/* ---------- pub/sub for websocket ---------- */
const bus=(()=>{const m={};return{
  on(t,f){(m[t]=m[t]||[]).push(f);return()=>{m[t]=m[t].filter(x=>x!==f)}},
  emit(t,d){(m[t]||[]).forEach(f=>{try{f(d)}catch(e){console.warn(e)}})}
}})();

/* ---------- i18n ---------- */
const I18N={
 en:{app:'Control Center',sub:'Local AI command hub',
  nav_dashboard:'Dashboard',nav_monitor:'System Monitor',nav_terminal:'Terminal',nav_chat:'AI Chat',
  nav_models:'Models',nav_tools:'Tools',nav_video:'Video Studio',nav_training:'Training Studio',
  nav_batch:'Batch Queue',nav_owui:'Open WebUI',nav_settings:'Settings',nav_knowledge:'Knowledge',
  nav_automation:'Automation',d_automation:'Schedule tasks to run automatically in the background',
  nav_agent:'Agent',d_agent:'Autonomous multi-step assistant — it plans, uses tools, and acts',
  nav_screen:'Screen Studio',d_screen:'Record, read (OCR/vision) and understand your screen',
  nav_bugs:'Bug Reports',d_bugs:'Report issues and track them — recent logs attached automatically',
  nav_learning:'Learning',d_learning:'How the model improves from your usage',
  nav_workflows:'Workflows',d_workflows:'Chain steps that run in sequence (task dependencies)',
  nav_abtest:'A/B Test',d_abtest:'Compare two models on the same prompts with an AI judge',
  nav_audit:'Audit Log',d_audit:'Every action recorded — commands, agent, automation, auth, config',
  nav_diagnostics:'Diagnostics',d_diagnostics:'One-click health check across every subsystem',
  nav_brain:'Nova Brain',d_brain:'A living map of what your knowledge base has learned',
  d_knowledge:'Your local document library — chat answers from it (RAG)',
  run:'Run',send:'Send',clear:'Clear',save:'Save',refresh:'Refresh',start:'Start',stop:'Stop',
  quick_actions:'Quick Actions',recent_cmds:'Recent Commands',notifications:'Notifications',
  harvest:'Harvest chats',harvest_retrain:'Harvest & Retrain',save_to_training:'save to training',
  d_dashboard:'Overview of your local AI system',d_monitor:'Live hardware telemetry',
  d_terminal:'Real PowerShell on this machine',d_chat:'Talk to your local models — context remembered',
  d_models:'Load, unload and inspect local models',d_tools:'Open WebUI tools & toolkit actions',
  d_video:'Generate video locally with LTX',d_training:'Fine-tune & continuous learning',
  d_batch:'Queue and run commands in sequence',d_owui:'Open WebUI configuration',d_settings:'Preferences',
  mode:'Mode',local:'Local',cloud:'Cloud',auto:'Auto',loaded:'loaded',load:'load',unload:'unload',
  generate:'Generate',prompt:'Prompt',model:'Model',frames:'Frames',steps:'Steps',
  dataset:'Dataset',base:'Base',learned:'Learned',combined:'Combined',training_log:'Training Log',
  test_model:'Test nova-local',ask:'Ask',processes:'Background Processes',no_proc:'No processes yet',
  cmd_ph:'PowerShell command…  (e.g. nvidia-smi, ollama ps)',chat_ph:'Message the model…',
  saved:'saved',health:'System Health',services:'Services',add:'Add to queue',run_all:'Run all',
  language:'Language',default_local:'Default local model',default_cloud:'Default cloud model',
  cloud_key:'Cloud API key',desktop_notif:'Desktop notifications',accent:'Accent color',save_settings:'Save settings'},
 ar:{app:'مركز التحكم',sub:'مركز قيادة الذكاء المحلي',
  nav_dashboard:'الرئيسية',nav_monitor:'مراقبة النظام',nav_terminal:'الطرفية',nav_chat:'المحادثة',
  nav_models:'النماذج',nav_tools:'الأدوات',nav_video:'استوديو الفيديو',nav_training:'استوديو التدريب',
  nav_batch:'قائمة المهام',nav_owui:'واجهة الويب',nav_settings:'الإعدادات',nav_knowledge:'المعرفة',
  nav_automation:'الأتمتة',d_automation:'جدولة المهام لتعمل تلقائياً في الخلفية',
  nav_agent:'الوكيل',d_agent:'مساعد ذاتي متعدد الخطوات — يخطط ويستخدم الأدوات وينفّذ',
  nav_screen:'استوديو الشاشة',d_screen:'سجّل واقرأ (OCR/رؤية) وافهم شاشتك',
  nav_bugs:'بلاغات الأخطاء',d_bugs:'أبلغ عن المشكلات وتابعها — تُرفق السجلات تلقائياً',
  nav_learning:'التعلّم',d_learning:'كيف يتحسّن النموذج من استخدامك',
  nav_workflows:'سير العمل',d_workflows:'ربط خطوات تعمل بالتسلسل (اعتماديات المهام)',
  nav_abtest:'مقارنة A/B',d_abtest:'قارن نموذجين على نفس الأسئلة مع حكم آلي',
  nav_audit:'سجل التدقيق',d_audit:'تسجيل كل إجراء — الأوامر والوكيل والأتمتة والدخول',
  nav_diagnostics:'الفحص',d_diagnostics:'فحص صحة شامل لكل المكونات بنقرة واحدة',
  nav_brain:'دماغ نوفا',d_brain:'خريطة حية لما تعلّمته قاعدة المعرفة',
  d_knowledge:'مكتبة مستنداتك المحلية — المحادثة تجيب منها',
  run:'تشغيل',send:'إرسال',clear:'مسح',save:'حفظ',refresh:'تحديث',start:'تشغيل',stop:'إيقاف',
  quick_actions:'إجراءات سريعة',recent_cmds:'الأوامر الأخيرة',notifications:'الإشعارات',
  harvest:'جمع المحادثات',harvest_retrain:'جمع وإعادة تدريب',save_to_training:'حفظ للتدريب',
  d_dashboard:'نظرة عامة على نظام الذكاء المحلي',d_monitor:'قياسات الأجهزة الحية',
  d_terminal:'PowerShell حقيقي على هذا الجهاز',d_chat:'تحدث مع نماذجك المحلية — مع تذكّر السياق',
  d_models:'تحميل وإلغاء وفحص النماذج المحلية',d_tools:'أدوات واجهة الويب والأدوات المحلية',
  d_video:'توليد فيديو محلياً عبر LTX',d_training:'الضبط الدقيق والتعلّم المستمر',
  d_batch:'جدولة وتشغيل الأوامر بالتسلسل',d_owui:'إعدادات واجهة الويب',d_settings:'التفضيلات',
  mode:'الوضع',local:'محلي',cloud:'سحابي',auto:'تلقائي',loaded:'محمّل',load:'تحميل',unload:'إلغاء',
  generate:'توليد',prompt:'الوصف',model:'النموذج',frames:'الإطارات',steps:'الخطوات',
  dataset:'البيانات',base:'الأساسية',learned:'المُتعلَّمة',combined:'المجمّعة',training_log:'سجل التدريب',
  test_model:'اختبار nova-local',ask:'اسأل',processes:'العمليات الخلفية',no_proc:'لا توجد عمليات',
  cmd_ph:'أمر PowerShell…  (مثل nvidia-smi)',chat_ph:'اكتب رسالتك للنموذج…',
  saved:'محفوظ',health:'صحة النظام',services:'الخدمات',add:'أضف للقائمة',run_all:'تشغيل الكل',
  language:'اللغة',default_local:'النموذج المحلي الافتراضي',default_cloud:'النموذج السحابي الافتراضي',
  cloud_key:'مفتاح السحابة',desktop_notif:'إشعارات سطح المكتب',accent:'لون التمييز',save_settings:'حفظ الإعدادات'}
};
const t=k=>(I18N[State.lang]&&I18N[State.lang][k])||I18N.en[k]||k;

/* ---------- routes ---------- */
const ROUTES=[
 ['dashboard','⚡',()=>Dashboard()],
 ['monitor','📊',()=>Monitor()],
 ['terminal','⌨️',()=>Terminal()],
 ['chat','💬',()=>Chat()],
 ['agent','🤖',()=>Agent()],
 ['screen','🖥️',()=>ScreenStudio()],
 ['bugs','🐞',()=>Bugs()],
 ['models','🧩',()=>Models()],
 ['tools','🛠️',()=>Tools()],
 ['video','🎬',()=>Video()],
 ['training','🎓',()=>Training()],
 ['learning','📈',()=>Learning()],
 ['abtest','🆚',()=>ABTest()],
 ['knowledge','📚',()=>Knowledge()],
 ['brain','🧠',()=>Brain()],
 ['automation','⏰',()=>Automation()],
 ['workflows','🔗',()=>Workflows()],
 ['batch','📋',()=>Batch()],
 ['owui','🌐',()=>Owui()],
 ['audit','🛡️',()=>AuditPage()],
 ['diagnostics','🩺',()=>Diagnostics()],
 ['settings','⚙️',()=>Settings()],
];
let cleanup=[];
function renderNav(){
  $('#nav').innerHTML=ROUTES.map(([id,ic])=>
    `<a href="#/${id}" data-r="${id}"><span class="ic">${ic}</span><span data-i18n="nav_${id}">${t('nav_'+id)}</span></a>`).join('');
}
function route(){
  const id=(location.hash.replace('#/','')||'dashboard');
  const r=ROUTES.find(x=>x[0]===id)||ROUTES[0];
  cleanup.forEach(f=>{try{f()}catch(e){}});cleanup=[];
  $$('#nav a').forEach(a=>a.classList.toggle('active',a.dataset.r===r[0]));
  const page=r[2]();usage(r[0]);
  $('#main').innerHTML=`<div class="page"><div class="page-head"><h2>${t('nav_'+r[0])}</h2><span class="d">${t('d_'+r[0])}</span></div><div id="pagebody"></div></div>`;
  $('#pagebody').innerHTML=page.html;
  if(page.mount){const u=page.mount();if(Array.isArray(u))cleanup.push(...u);else if(u)cleanup.push(u);}
}

/* ---------- helpers ---------- */
function card(title,body,extra=''){return `<div class="card"><div class="hd"><h3>${title}</h3>${extra}</div><div class="bd">${body}</div></div>`}
function ringHTML(id,label,unit){return `<div class="gauge"><div class="ring" id="${id}"><b>0<small>${unit}</small></b></div><div class="lbl">${label}</div><div class="sub" id="${id}_s">—</div></div>`}
function setRing(id,val,sub){const r=$('#'+id);if(!r)return;r.style.setProperty('--v',Math.min(100,val||0));r.querySelector('b').firstChild.textContent=Math.round(val||0);if(sub!=null){const s=$('#'+id+'_s');if(s)s.textContent=sub}}
function spark(cv,data,color){if(!cv)return;const ctx=cv.getContext('2d'),w=cv.width=cv.clientWidth,h=cv.height=cv.clientHeight;ctx.clearRect(0,0,w,h);if(data.length<2)return;const mx=100,st=w/(data.length-1);ctx.beginPath();data.forEach((v,i)=>{const x=i*st,y=h-(v/mx)*(h-6)-3;i?ctx.lineTo(x,y):ctx.moveTo(x,y)});ctx.strokeStyle=color;ctx.lineWidth=2;ctx.stroke();const g=ctx.createLinearGradient(0,0,0,h);g.addColorStop(0,color+'55');g.addColorStop(1,color+'00');ctx.lineTo(w,h);ctx.lineTo(0,h);ctx.closePath();ctx.fillStyle=g;ctx.fill()}

/* ---------- file + markdown helpers (module scope) ---------- */
const fileIcon=n=>{const e=(String(n).split('.').pop()||'').toLowerCase();
  return ({pdf:'📕',docx:'📘',txt:'📄',md:'📄',json:'🧾',csv:'📊',log:'📄',
    png:'🖼️',jpg:'🖼️',jpeg:'🖼️',webp:'🖼️',bmp:'🖼️',gif:'🖼️',py:'🐍',js:'📜',ps1:'⌨️'})[e]||'📎'};
const IMG_EXT=['png','jpg','jpeg','webp','bmp','gif'];
function attHTML(name,size){
  const ext=(name.split('.').pop()||'').toLowerCase(),url='/files/'+encodeURIComponent(name);
  const sz=size?` · ${(size/1024).toFixed(0)} KB`:'';
  if(IMG_EXT.includes(ext)) return `<a class="att-img" href="${url}" target="_blank"><img src="${url}" alt="${esc(name)}"><span>${esc(name)}${sz}</span></a>`;
  return `<a class="att-file" href="${url}" target="_blank"><span class="fi">${fileIcon(name)}</span><span class="fmeta"><b>${esc(name)}</b><small>${ext.toUpperCase()}${sz} · view ↗</small></span></a>`;
}
function mdRender(src){
  const blocks=[];let s=esc(src||'');
  s=s.replace(/```(\w*)\n?([\s\S]*?)```/g,(m,lang,code)=>{blocks.push(`<pre class="code"><code>${code.replace(/\n+$/,'')}</code></pre>`);return `@@CB${blocks.length-1}@@`});
  s=s.replace(/`([^`\n]+)`/g,'<code class="ic">$1</code>');
  s=s.replace(/^### (.*)$/gm,'<h4>$1</h4>').replace(/^## (.*)$/gm,'<h3>$1</h3>').replace(/^# (.*)$/gm,'<h2>$1</h2>');
  s=s.replace(/\*\*([^*]+)\*\*/g,'<b>$1</b>').replace(/(^|[^*])\*([^*\n]+)\*/g,'$1<i>$2</i>');
  s=s.replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g,'<a href="$2" target="_blank">$1</a>');
  s=s.replace(/^\s*[-*] (.+)$/gm,'<li>$1</li>').replace(/(<li>(?:(?!<\/li>)[\s\S])*<\/li>\s*)+/g,m=>`<ul>${m}</ul>`);
  s=s.replace(/\n/g,'<br>');
  s=s.replace(/@@CB(\d+)@@/g,(m,i)=>blocks[+i]!==undefined?blocks[+i]:m);
  return s;
}
function tagHTML(tags){return (tags||[]).map(t=>`<span class="mtag mtag-${t}">${t}</span>`).join('')}

