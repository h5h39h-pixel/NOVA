// -*- part of the Nova SPA (framework-free, global scope, load order matters) -*-
// System/insight pages — Nova Brain, Diagnostics, Audit, Open WebUI, Settings.
// Split from the original monolithic pages.js (HON-11). Loaded after core.js, before shell.js.

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
      <label class="f mt" style="display:flex;align-items:center;gap:9px"><button class="sw ${s.agent_can_control!==false?'on':''}" id="sagentctl"></button> 🖱️ Let the autonomous agent control mouse/keyboard (off = agent can't drive the GUI; manual control + panic stop still work)</label>
      <label class="f mt" style="display:flex;align-items:center;gap:9px"><button class="sw ${s.screen_memory_enabled?'on':''}" id="sscrmem"></button> 🧠 Screen memory (opt-in) — OCR snapshots of your screen into the knowledge base so you can ask "what did I see earlier?" (local-only; keeps the newest ${s.screen_memory_keep||50}; schedule the <code>screen_memory</code> automation to capture periodically)</label>
      <button class="btn mt" id="purgescrmem" style="width:100%">🧹 Purge all screen memories</button>
      <label class="f mt">🔊 Voice speed (TTS) <span class="aset-v" id="ttsratev">${(+s.tts_rate||1).toFixed(1)}×</span></label>
      <input type="range" id="sttsrate" min="0.7" max="1.6" step="0.1" value="${+s.tts_rate||1}" style="width:100%">
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
   ${card('Usage Statistics',`<div id="usagebox"></div>`)}
   ${card('🧠 Persistent Memory',`
      <p class="muted" style="font-size:12.5px">Durable facts Nova remembers about you across sessions (local-only). Used to personalise chat &amp; agent answers. The agent can also add facts itself via its <code>remember</code> tool.</p>
      <div class="flex" style="margin-top:8px"><input class="t" id="memin" placeholder="e.g. I prefer concise answers in English" style="flex:1"><button class="btn p" id="memadd">＋ Remember</button></div>
      <div id="membox" style="margin-top:10px"></div>`)}`;
  function mount(){
    (async()=>{const list=await api('/models');$('#sl').innerHTML=list.map(m=>`<option ${m.name===s.default_local_model?'selected':''}>${esc(m.name)}</option>`).join('')})();
    const slite=$('#slite');if(slite)slite.onclick=function(){const on=!this.classList.contains('on');
      if(on)localStorage.setItem('lite','1');else localStorage.removeItem('lite');location.reload()};
    const sconfirm=$('#sconfirm');if(sconfirm)sconfirm.onclick=function(){const on=!this.classList.contains('on');this.classList.toggle('on',on);
      post('/settings',{confirm_exit:on}).then(x=>{State.settings=x});toast('info',on?'Exit confirmation enabled':'Exit confirmation disabled','')};
    const sactl=$('#sagentctl');if(sactl)sactl.onclick=function(){const on=!this.classList.contains('on');this.classList.toggle('on',on);
      post('/settings',{agent_can_control:on}).then(x=>{State.settings=x});toast(on?'info':'success',on?'Agent GUI control enabled':'Agent GUI control disabled',on?'the agent may move the mouse/keyboard':'the agent can no longer drive the GUI')};
    const sscrmem=$('#sscrmem');if(sscrmem)sscrmem.onclick=function(){const on=!this.classList.contains('on');this.classList.toggle('on',on);
      post('/settings',{screen_memory_enabled:on}).then(x=>{State.settings=x});toast(on?'info':'success',on?'Screen memory enabled':'Screen memory disabled',on?'OCR snapshots can now be saved to the KB (opt-in)':'no screen snapshots will be stored')};
    const purgesm=$('#purgescrmem');if(purgesm)purgesm.onclick=async function(){if(!confirm('Delete ALL stored screen memories from the knowledge base?'))return;
      const r=await fetch('/api/vision/screen-memory',{method:'DELETE'}).then(x=>x.json());toast('success','Screen memories purged',`removed ${(r&&r.removed)||0} entries`)};
    {const r=$('#sttsrate');if(r)r.oninput=e=>{const v=+e.target.value;$('#ttsratev').textContent=v.toFixed(1)+'×';clearTimeout(r._t);r._t=setTimeout(()=>post('/settings',{tts_rate:v}).then(x=>{State.settings=x}),400)};}
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
    const loadMem=async()=>{const r=await api('/memory');const items=(r&&r.items)||[];
      $('#membox').innerHTML=items.length?items.map(f=>`<div class="metarow"><span>${f.pinned?'📌 ':''}${esc(f.text)}</span><button class="btn" data-mdel="${f.id}" title="Forget">✕</button></div>`).join(''):'<div class="empty">nothing remembered yet</div>';
      $$('#membox [data-mdel]').forEach(b=>b.onclick=async()=>{await fetch('/api/memory/'+b.dataset.mdel,{method:'DELETE'});loadMem()})};
    const addMem=async()=>{const v=$('#memin').value.trim();if(!v)return;const r=await post('/memory',{text:v});
      if(r&&r.ok){$('#memin').value='';toast('success','Remembered','');loadMem()}else toast('error','Could not save',(r&&r.error)||'')};
    $('#memadd').onclick=addMem;$('#memin').onkeydown=e=>{if(e.key==='Enter')addMem()};loadMem();
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

