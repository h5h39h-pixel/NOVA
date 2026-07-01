// -*- part of the Nova SPA (framework-free, global scope, load order matters) -*-
// Event Log explorer — the unified log (errors · operations · system events · alerts) in one
// searchable, filterable, timeline view. Reads /api/events. Loaded before shell.js.

const EV_LEVEL_CLASS = { debug: 'mut', info: 'on', warn: 'warn', error: 'err', critical: 'err' };
const EV_CAT_ICON = {
  error: '🔴', exec: '⌨️', file: '📄', network: '🌐', system: '⚙️', action: '▶️',
  agent: '🤖', security: '🛡️', automation: '⏰', media: '🎬', alert: '🔔',
};

function _evTime(ts) {
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString() + ' · ' + d.toLocaleDateString();
}

function EventLog() {
  const AR = State.lang === 'ar';
  let filters = { q: '', level: '', category: '', actor: '', hours: 24 };
  let offset = 0, lastItems = [];

  const html = `<div class="evwrap">
    ${card('🧾 ' + (AR ? 'سجل الأحداث الموحّد' : 'Unified Event Log') + ' <span class="tag" id="ev_total"></span>', `
      <p class="muted" style="font-size:12.5px">${AR
        ? 'كل شيء في مكان واحد: الأخطاء (مع تتبّع المكدس)، والعمليات، وأحداث النظام، والتنبيهات. ابحث وصفِّ واستكشف.'
        : 'Everything in one place: errors (with stack traces), operations, system events & alerts. Search, filter, explore.'}</p>
      <div id="ev_timeline" class="ev-timeline" title="events over time (red = errors)"></div>
      <div class="ev-controls">
        <input class="t" id="ev_q" placeholder="🔎 ${AR ? 'ابحث في الرسائل والمصادر…' : 'search messages & sources…'}" style="flex:2;min-width:180px">
        <select class="t" id="ev_cat" style="width:auto"></select>
        <select class="t" id="ev_lvl" style="width:auto"></select>
        <select class="t" id="ev_hours" style="width:auto">
          <option value="1">1h</option><option value="24" selected>24h</option>
          <option value="168">7d</option><option value="0">${AR ? 'الكل' : 'all'}</option>
        </select>
        <button class="btn" id="ev_refresh">↻</button>
        <button class="btn sm danger" id="ev_clear">${AR ? 'مسح' : 'Clear'}</button>
      </div>
      <div class="ev-cats" id="ev_catbar"></div>
      <div id="ev_list" class="ev-list"><div class="empty">…</div></div>
      <div class="ev-more"><button class="btn" id="ev_more" style="display:none">${AR ? 'المزيد' : 'Load more'}</button></div>
    `)}
  </div>`;

  function levelDot(lv) { return `<span class="ev-dot ${EV_LEVEL_CLASS[lv] || 'mut'}" title="${lv}"></span>`; }

  function renderTimeline(tl) {
    const el = $('#ev_timeline'); if (!el) return;
    const max = Math.max(1, ...tl.map(b => b.total));
    el.innerHTML = tl.map(b => {
      const h = Math.round((b.total / max) * 100);
      const eh = b.total ? Math.round((b.error / b.total) * h) : 0;
      const tip = b.t ? `${new Date(b.t * 1000).toLocaleString()} · ${b.total} events${b.error ? ' · ' + b.error + ' errors' : ''}` : '';
      return `<span class="ev-bar" title="${esc(tip)}"><span class="ev-bar-e" style="height:${eh}%"></span><span class="ev-bar-t" style="height:${h - eh}%"></span></span>`;
    }).join('');
  }

  function renderList(items, append) {
    const el = $('#ev_list'); if (!el) return;
    if (!append) el.innerHTML = '';
    if (!items.length && !append) { el.innerHTML = `<div class="empty">${AR ? 'لا أحداث مطابقة' : 'no matching events'}</div>`; return; }
    for (const e of items) {
      const row = document.createElement('div'); row.className = 'ev-row lvl-' + (e.level || 'info');
      row.innerHTML = `<div class="ev-head">
          ${levelDot(e.level)}<span class="ev-cat">${EV_CAT_ICON[e.category] || '•'} ${esc(e.category)}</span>
          <span class="ev-msg">${esc(e.message || '')}</span>
          <span class="ev-src">${esc(e.source || '')}</span>
          <span class="ev-time">${_evTime(e.ts)}</span></div>`;
      const body = document.createElement('div'); body.className = 'ev-body'; body.hidden = true;
      let bh = '';
      if (e.detail) bh += `<div class="ev-detail">${esc(e.detail)}</div>`;
      if (e.context) bh += `<div class="ev-ctx"><b>context</b> <code>${esc(JSON.stringify(e.context))}</code></div>`;
      if (e.trace) bh += `<pre class="ev-trace">${esc(e.trace)}</pre>`;
      bh += `<div class="ev-meta">actor: ${esc(e.actor || '')} · status: ${esc(e.status || '')} · id: ${e.id}</div>`;
      body.innerHTML = bh || '<div class="muted">no extra detail</div>';
      row.querySelector('.ev-head').onclick = () => { body.hidden = !body.hidden; row.classList.toggle('open', !body.hidden); };
      row.appendChild(body); el.appendChild(row);
    }
  }

  async function loadStats() {
    try {
      const s = await api('/events/stats?hours=' + (filters.hours || 24 * 30) + '&buckets=48');
      renderTimeline(s.timeline || []);
      const cats = s.by_category || {};
      const bar = $('#ev_catbar');
      if (bar) bar.innerHTML = Object.entries(cats).sort((a, b) => b[1] - a[1]).map(([c, n]) =>
        `<button class="ev-chip ${filters.category === c ? 'on' : ''}" data-cat="${c}">${EV_CAT_ICON[c] || '•'} ${esc(c)} <b>${n}</b></button>`).join('')
        || `<span class="muted" style="font-size:12px">${AR ? 'لا أحداث بعد' : 'no events yet'}</span>`;
      $$('#ev_catbar [data-cat]').forEach(b => b.onclick = () => {
        filters.category = filters.category === b.dataset.cat ? '' : b.dataset.cat;
        $('#ev_cat').value = filters.category; offset = 0; load(); loadStats();
      });
    } catch (e) {}
  }

  function qs() {
    const p = new URLSearchParams();
    if (filters.q) p.set('q', filters.q);
    if (filters.level) p.set('level', filters.level);
    if (filters.category) p.set('category', filters.category);
    if (filters.hours) p.set('since', (Date.now() / 1000 - filters.hours * 3600).toFixed(0));
    p.set('limit', '100'); p.set('offset', offset);
    return p.toString();
  }

  async function load(append) {
    const r = await api('/events?' + qs());
    lastItems = r.items || [];
    renderList(lastItems, append);
    const tot = $('#ev_total'); if (tot) tot.textContent = (r.total || 0) + (AR ? ' حدث' : ' events');
    const more = $('#ev_more'); if (more) more.style.display = (offset + 100 < (r.total || 0)) ? '' : 'none';
  }

  function mount() {
    (async () => {
      const meta = await api('/events/meta').catch(() => ({ levels: [], categories: [] }));
      $('#ev_cat').innerHTML = `<option value="">${AR ? 'كل الفئات' : 'all categories'}</option>` +
        (meta.categories || []).map(c => `<option value="${c}">${EV_CAT_ICON[c] || ''} ${c}</option>`).join('');
      $('#ev_lvl').innerHTML = `<option value="">${AR ? 'كل المستويات' : 'all levels'}</option>` +
        (meta.levels || []).map(l => `<option value="${l}">${l}</option>`).join('');
      load(); loadStats();
    })();
    let deb;
    $('#ev_q').oninput = e => { filters.q = e.target.value.trim(); clearTimeout(deb); deb = setTimeout(() => { offset = 0; load(); }, 300); };
    $('#ev_cat').onchange = e => { filters.category = e.target.value; offset = 0; load(); loadStats(); };
    $('#ev_lvl').onchange = e => { filters.level = e.target.value; offset = 0; load(); };
    $('#ev_hours').onchange = e => { filters.hours = +e.target.value; offset = 0; load(); loadStats(); };
    $('#ev_refresh').onclick = () => { offset = 0; load(); loadStats(); };
    $('#ev_more').onclick = () => { offset += 100; load(true); };
    $('#ev_clear').onclick = async () => {
      if (!confirm(AR ? 'مسح كل سجل الأحداث؟' : 'Clear the entire event log?')) return;
      await del('/events'); offset = 0; load(); loadStats(); toast('info', AR ? 'مُسح' : 'Cleared', '');
    };
    // live: any new audit/notification/error stream event → light refresh
    let live; const bump = () => { clearTimeout(live); live = setTimeout(() => { load(); loadStats(); }, 800); };
    const subs = [bus.on('audit', bump), bus.on('notification', bump)];
    return subs;
  }
  return { html, mount };
}
