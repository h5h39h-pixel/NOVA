/* ============================ shell.js ============================
   WebSocket bus, toasts, notifications, command palette, theme, auth gate, boot(). Depends on core.js + pages.js. Calls boot() last.
   Part of the AI Control Center SPA. Loaded in order: core -> pages -> shell.
   Single shared global scope (no bundler); load order matters. */
/* ============================ globals: ws, toasts, notifications, palette ============================ */
let ws;
function connect(){
  ws=new WebSocket((location.protocol==='https:'?'wss':'ws')+'://'+location.host+'/ws');
  ws.onopen=()=>{State.services.ws=true;bus.emit('services',State.services);$('#d_ws').classList.add('up')};
  ws.onclose=()=>{State.services.ws=false;bus.emit('services',State.services);$('#d_ws').classList.remove('up');setTimeout(connect,2000)};
  ws.onmessage=e=>{const m=JSON.parse(e.data);
    if(m.type==='metrics'){State.metrics=m;pushBuf(m);updatePills(m);bus.emit('metrics',m)}
    else if(m.type==='services'){Object.assign(State.services,m);updateSvcPills();bus.emit('services',State.services)}
    else if(m.type==='notification'){toast(m.level,m.title,m.body);State.unseen++;updateBell();notifSound();bus.emit('notification',m);if($('#drawer')&&$('#drawer').classList.contains('open'))loadNotifs()}
    else bus.emit(m.type,m)}
}
function pushBuf(m){const b=State.buf;const push=(a,v)=>{a.push(v||0);if(a.length>60)a.shift()};
  push(b.gpu,m.gpu?m.gpu.util:0);push(b.vram,m.gpu?m.gpu.vram_used/m.gpu.vram_total*100:0);push(b.cpu,m.cpu);push(b.ram,m.ram_pct)}
function updatePills(m){if(m.gpu)$('#pill_gpu').textContent=`GPU ${Math.round(m.gpu.util)}% · ${Math.round(m.gpu.temp)}°C`;
  $('#pill_cpu').textContent=`CPU ${Math.round(m.cpu)}%`;$('#pill_ram').textContent=`RAM ${m.ram_pct}%`}
function updateSvcPills(){$('#d_owui').classList.toggle('up',!!State.services.owui);$('#d_ollama').classList.toggle('up',!!State.services.ollama);$('#d_comfy').classList.toggle('up',!!State.services.comfy)}

function toast(level,title,body){const t=document.createElement('div');t.className='toast '+(level||'info');t.innerHTML=`<b>${esc(title)}</b>${body?`<span>${esc(body)}</span>`:''}`;$('#toasts').appendChild(t);setTimeout(()=>t.remove(),5000)}
const NCAT={system:['⚙️','System'],training:['🎓','Training'],agent:['🤖','Agent'],video:['🎬','Video'],automation:['⏰','Automation'],knowledge:['📚','Knowledge'],security:['🔒','Security'],chat:['💬','Chat']};
let notifCat='';
function updateBell(){const b=$('#nbadge');if(!b)return;b.textContent=State.unseen>99?'99+':State.unseen;b.style.display=State.unseen?'grid':'none';const bell=$('#bell');if(bell)bell.classList.toggle('has-unread',State.unseen>0)}
function relTime(ts){const s=Math.max(0,Date.now()/1000-ts);if(s<60)return'now';if(s<3600)return Math.floor(s/60)+'m ago';if(s<86400)return Math.floor(s/3600)+'h ago';return new Date(ts*1000).toLocaleDateString()}
function dayGroup(ts){const d=new Date(ts*1000),now=new Date();const day=new Date(d.getFullYear(),d.getMonth(),d.getDate());const today=new Date(now.getFullYear(),now.getMonth(),now.getDate());const diff=(today-day)/86400000;return diff<=0?'Today':diff<=1?'Yesterday':diff<=7?'This Week':'Earlier'}
function notifSound(){if(localStorage.getItem('notif_mute'))return;try{const C=window.AudioContext||window.webkitAudioContext;const a=new C();const o=a.createOscillator(),g=a.createGain();o.type='sine';o.frequency.setValueAtTime(660,a.currentTime);o.frequency.exponentialRampToValueAtTime(990,a.currentTime+.12);o.connect(g);g.connect(a.destination);g.gain.setValueAtTime(0.0001,a.currentTime);g.gain.exponentialRampToValueAtTime(0.06,a.currentTime+.03);g.gain.exponentialRampToValueAtTime(0.0001,a.currentTime+.4);o.start();o.stop(a.currentTime+.42)}catch(e){}}
async function loadNotifs(){
  const r=await api('/notifications?limit=80'+(notifCat?'&category='+notifCat:'')+(window._nq?'&q='+encodeURIComponent(window._nq):''));
  State.unseen=r.unread||0;updateBell();
  const fl=$('#nfilters');if(fl){const cats=Object.entries(r.categories||{}).filter(([k])=>k);
    fl.innerHTML=`<span class="nchip ${notifCat===''?'on':''}" data-c="">All</span>`+cats.map(([c,n])=>`<span class="nchip ${notifCat===c?'on':''}" data-c="${c}">${(NCAT[c]||['•',c])[0]} ${n}</span>`).join('');
    $$('#nfilters .nchip').forEach(ch=>ch.onclick=()=>{notifCat=ch.dataset.c;loadNotifs()})}
  const el=$('#nlist');if(!el)return;
  if(!(r.items||[]).length){el.innerHTML='<div class="empty">No notifications</div>';return}
  let html='',group='';
  for(const n of r.items){const g=dayGroup(n.ts);if(g!==group){group=g;html+=`<div class="ngroup">${g}</div>`}
    const cat=NCAT[n.category||'system']||['🔔','System'];
    html+=`<div class="ncard ${n.level||''} ${n.seen?'':'unread'}" data-id="${n.id}" data-link="${esc(n.link||'')}">
      <span class="nic">${cat[0]}</span><div class="nbody"><div class="nt">${esc(n.title)}${n.seen?'':'<span class="ndot"></span>'}</div>${n.body?`<div class="nb">${esc(n.body)}</div>`:''}<div class="nm">${cat[1]} · ${relTime(n.ts)}</div></div></div>`}
  el.innerHTML=html;
  $$('#nlist .ncard').forEach(c=>c.onclick=()=>{const id=c.dataset.id,link=c.dataset.link;post('/notifications/'+id+'/seen');c.classList.remove('unread');const dot=c.querySelector('.ndot');if(dot)dot.remove();
    State.unseen=Math.max(0,State.unseen-1);updateBell();
    if(link){location.hash=link;$('#drawer').classList.remove('open')}})}

function setLang(l){State.lang=l;localStorage.setItem('lang',l);document.documentElement.dir='ltr';document.documentElement.lang=l;
  $('#brandsub').textContent=t('sub');$('#langlbl').textContent=l==='ar'?'EN':'ع';renderNav();route()}

/* ---------- theme / usage / settings io / onboarding ---------- */
function applyTheme(){let m=localStorage.getItem('theme')||'dark';if(m==='auto'){const h=new Date().getHours();m=(h>=7&&h<18)?'light':'dark'}
  const lt=m==='light';document.body.classList.toggle('light',lt);const b=$('#themebtn');if(b)b.textContent=lt?'🌙':'☀️'}
function toggleTheme(){localStorage.setItem('theme',localStorage.getItem('theme')==='light'?'dark':'light');applyTheme()}
function initParticles(){const cv=$('#particles');if(!cv)return;
  if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;   // respect user motion pref
  const ctx=cv.getContext('2d');let W,H,pts=[];
  // node tints cycle through the cyan/blue/purple accent family for a constellation feel
  const TINT=[[34,211,238],[59,130,246],[168,85,247]];
  const resize=()=>{W=cv.width=innerWidth;H=cv.height=innerHeight;const n=Math.min(72,Math.floor(W*H/26000));
    pts=Array.from({length:n},(_,i)=>({x:Math.random()*W,y:Math.random()*H,vx:(Math.random()-.5)*.24,vy:(Math.random()-.5)*.24,c:TINT[i%TINT.length],r:Math.random()*1.4+.7}))};
  resize();addEventListener('resize',resize);
  (function loop(){ctx.clearRect(0,0,W,H);
    for(const p of pts){p.x+=p.vx;p.y+=p.vy;if(p.x<0||p.x>W)p.vx*=-1;if(p.y<0||p.y>H)p.vy*=-1}
    for(let i=0;i<pts.length;i++)for(let j=i+1;j<pts.length;j++){const a=pts[i],b=pts[j],dx=a.x-b.x,dy=a.y-b.y,d=dx*dx+dy*dy;
      if(d<16000){ctx.strokeStyle='rgba(120,150,255,'+(0.14*(1-d/16000))+')';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke()}}
    for(const p of pts){ctx.fillStyle='rgba('+p.c[0]+','+p.c[1]+','+p.c[2]+',.85)';ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,6.2832);ctx.fill()}
    requestAnimationFrame(loop)})()}

/* depth: subtle mouse parallax on background layers + a 3D tilt on hovered cards */
function initDepth(){
  if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;
  if(matchMedia('(pointer: coarse)').matches)return;   // skip on touch devices
  const aurora=$('.bg-aurora'),parts=$('#particles');
  let raf=0,mx=0,my=0;
  addEventListener('mousemove',e=>{
    mx=(e.clientX/innerWidth-.5);my=(e.clientY/innerHeight-.5);
    if(raf)return;raf=requestAnimationFrame(()=>{raf=0;
      if(aurora)aurora.style.transform='translate3d('+(mx*-22)+'px,'+(my*-16)+'px,0)';
      if(parts)parts.style.transform='translate3d('+(mx*12)+'px,'+(my*9)+'px,0)';
    });
  },{passive:true});
  // 3D tilt via event delegation (survives re-renders); one card at a time
  let tilted=null,traf=0,lx=0,ly=0;
  const clear=()=>{if(tilted){tilted.style.transform='';tilted=null}};
  document.addEventListener('pointermove',e=>{
    const c=e.target.closest&&e.target.closest('.card');
    if(c!==tilted){clear();tilted=c}
    if(!c)return;lx=e.clientX;ly=e.clientY;
    if(traf)return;traf=requestAnimationFrame(()=>{traf=0;if(!tilted)return;
      const r=tilted.getBoundingClientRect();
      const rx=((ly-r.top)/r.height-.5)*-5, ry=((lx-r.left)/r.width-.5)*5;   // max ~5deg
      tilted.style.transform='perspective(900px) rotateX('+rx.toFixed(2)+'deg) rotateY('+ry.toFixed(2)+'deg) translateY(-3px)';
    });
  },{passive:true});
  document.addEventListener('pointerleave',clear,true);
  document.addEventListener('scroll',clear,true);
}
function usage(f){try{const u=JSON.parse(localStorage.getItem('usage')||'{}');u[f]=(u[f]||0)+1;localStorage.setItem('usage',JSON.stringify(u))}catch(e){}}
function getUsage(){try{return JSON.parse(localStorage.getItem('usage')||'{}')}catch(e){return{}}}
function exportSettings(){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(State.settings,null,2)],{type:'application/json'}));a.download='control-center-settings.json';a.click()}
function importSettings(file){const r=new FileReader();r.onload=()=>{try{const o=JSON.parse(r.result);post('/settings',o).then(s=>{State.settings=s;toast('success','Settings imported','')})}catch(e){toast('error','Invalid file','')}};r.readAsText(file)}
function maybeOnboard(){if(localStorage.getItem('onboarded'))return;const o=$('#onb');if(o)o.classList.add('open')}
function closeOnboard(){localStorage.setItem('onboarded','1');const o=$('#onb');if(o)o.classList.remove('open')}

/* command palette (Ctrl/⌘+K) */
function initPalette(){
  const baseCmds=()=>ROUTES.map(([id,ic])=>({ic,name:t('nav_'+id),sub:'page',act:()=>location.hash='#/'+id}))
    .concat([{ic:'🎓',name:t('harvest_retrain'),sub:'action',act:()=>{post('/learn/retrain');toast('info','Harvest & Retrain started','')}},
             {ic:'🔄',name:'Restart ComfyUI',sub:'action',act:()=>{post('/services/comfy/restart');toast('info','Restarting ComfyUI','')}},
             {ic:'☀️',name:'Toggle theme',sub:'action',act:toggleTheme}]);
  let sel=0,items=[],timer=null;
  const render=()=>{$('#palres').innerHTML=items.length?items.map((c,i)=>`<div class="${i===sel?'sel':''}" data-i="${i}"><span class="ic">${c.ic}</span><span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(c.name)}</span>${c.sub?`<span class="muted" style="font-size:11px;white-space:nowrap">${esc(c.sub)}</span>`:''}</div>`).join(''):'<div class="empty">no matches</div>';
    $$('#palres [data-i]').forEach(d=>d.onclick=()=>{items[+d.dataset.i].act();closeP()})};
  async function update(q){
    const cl=baseCmds().filter(c=>!q||c.name.toLowerCase().includes(q.toLowerCase()));
    items=cl;sel=0;render();
    if(q.length>=2){try{const r=await api('/search?q='+encodeURIComponent(q));
      const sr=(r.results||[]).map(x=>({ic:x.icon||'🔎',name:x.label,sub:x.sub,act:()=>{if(x.cid)State.currentCid=x.cid;location.hash=x.go}}));
      if($('#palette').classList.contains('open')){items=cl.concat(sr);render()}}catch(e){}}}
  const openP=()=>{$('#palette').classList.add('open');$('#palin').value='';update('');$('#palin').focus()};
  const closeP=()=>$('#palette').classList.remove('open');
  window.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();openP()}
    if(e.key==='Escape')closeP()});
  $('#palin').addEventListener('input',e=>{clearTimeout(timer);const q=e.target.value;timer=setTimeout(()=>update(q),250)});
  $('#palin').addEventListener('keydown',e=>{if(e.key==='ArrowDown'){e.preventDefault();sel=Math.min(sel+1,items.length-1);render()}else if(e.key==='ArrowUp'){e.preventDefault();sel=Math.max(sel-1,0);render()}else if(e.key==='Enter'&&items[sel]){items[sel].act();closeP()}});
  $('#palette').onclick=e=>{if(e.target.id==='palette')closeP()};
}

/* ============================ auth gate ============================ */
function showLogin(){
  document.documentElement.dir='ltr';
  const lg=$('#login');lg.classList.add('open');$('#logintoken').focus();
  const tryLogin=async()=>{const r=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:$('#logintoken').value})}).then(x=>x.json()).catch(()=>({ok:false}));
    if(r.ok){location.reload()}else{$('#loginerr').textContent='Invalid token. Try again.'}};
  $('#loginbtn').onclick=tryLogin;$('#logintoken').addEventListener('keydown',e=>{if(e.key==='Enter')tryLogin()});
}

/* ============================ boot ============================ */
async function boot(){
  window.__toast=toast;
  // data-safety: warn before closing if a recording or training is in progress
  window.addEventListener('beforeunload',e=>{if(State.recording||State.training){e.preventDefault();e.returnValue='Work in progress (recording/training). Leave anyway?';return e.returnValue}});
  document.documentElement.dir='ltr';document.documentElement.lang=State.lang;
  const auth=await api('/auth/status').catch(()=>({required:false,authed:true}));
  if(auth.required && !auth.authed){ showLogin(); return; }
  State.settings=await api('/settings').catch(()=>({}));
  $('#brandsub').textContent=t('sub');$('#langlbl').textContent=State.lang==='ar'?'EN':'ع';
  renderNav();initPalette();connect();loadNotifs();applyTheme();initParticles();initDepth();maybeOnboard();initIcons();
  // mobile: off-canvas sidebar drawer
  let backdrop=document.getElementById('sidebackdrop');
  if(!backdrop){backdrop=document.createElement('div');backdrop.id='sidebackdrop';document.body.appendChild(backdrop)}
  const closeSide=()=>{const s=document.querySelector('.side');if(s)s.classList.remove('open');backdrop.classList.remove('show')};
  const mb=$('#menubtn');if(mb)mb.onclick=()=>{const s=document.querySelector('.side');const open=!s.classList.contains('open');s.classList.toggle('open',open);backdrop.classList.toggle('show',open)};
  backdrop.onclick=closeSide;
  const navEl=$('#nav');if(navEl)navEl.addEventListener('click',e=>{if(e.target.closest('a'))closeSide()});
  window.addEventListener('hashchange',route);
  if(!location.hash)location.hash='#/dashboard';route();
  $('#langbtn').onclick=()=>setLang(State.lang==='ar'?'en':'ar');
  const tb=$('#themebtn');if(tb)tb.onclick=toggleTheme;
  const oc=$('#onbclose');if(oc)oc.onclick=closeOnboard;
  const sc=$('#scclose');if(sc)sc.onclick=()=>$('#shortcuts').classList.remove('open');
  const scov=$('#shortcuts');if(scov)scov.onclick=e=>{if(e.target.id==='shortcuts')scov.classList.remove('open')};
  window.addEventListener('keydown',e=>{
    if(e.key==='?'&&!/INPUT|TEXTAREA|SELECT/.test((document.activeElement||{}).tagName||'')){e.preventDefault();$('#shortcuts').classList.toggle('open')}
    if(e.key==='Escape'){const s=$('#shortcuts');if(s)s.classList.remove('open')}});
  const pc=$('#prevclose');if(pc)pc.onclick=()=>$('#preview').classList.remove('open');
  const pv=$('#preview');if(pv)pv.onclick=e=>{if(e.target.id==='preview')pv.classList.remove('open')};
  $('#bell').onclick=()=>{const d=$('#drawer');d.classList.toggle('open');if(d.classList.contains('open'))loadNotifs()};
  $('#dclose').onclick=()=>$('#drawer').classList.remove('open');
  const muteBtn=$('#nmute');const setMute=()=>{if(muteBtn)muteBtn.textContent=localStorage.getItem('notif_mute')?'🔕':'🔔'};setMute();
  if(muteBtn)muteBtn.onclick=()=>{localStorage.getItem('notif_mute')?localStorage.removeItem('notif_mute'):localStorage.setItem('notif_mute','1');setMute()};
  const rd=$('#nread');if(rd)rd.onclick=()=>post('/notifications/seen').then(loadNotifs);
  const cl=$('#nclear');if(cl)cl.onclick=()=>{if(confirm('Clear all notifications?'))del('/notifications').then(loadNotifs)};
  const ns=$('#nsearch');if(ns)ns.addEventListener('input',e=>{window._nq=e.target.value;clearTimeout(window._nt);window._nt=setTimeout(loadNotifs,250)});
  loadNotifs();
  setInterval(()=>$('#clock').textContent=new Date().toLocaleTimeString(),1000);
}
boot();
