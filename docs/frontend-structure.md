# Frontend structure (after the HON‑11 refactor)

The SPA is **framework‑free**: plain ES in classic `<script>` tags sharing one global scope, loaded in
order, no bundler. The big monoliths were split for maintainability (M78/M79) **without changing
behavior** — every split was byte‑identical and render‑verified.

## JavaScript — load order matters
Loaded by `static/index.html` in this exact order (all share one global scope; page builders run only
after every file loads, so cross‑file function/`const` references resolve at call time):

| File | Lines | Owns |
|---|---|---|
| `js/core.js` | ~223 | DOM/api helpers, icon engine, `State`, event bus, i18n, **router + `ROUTES`**, render helpers (`card`, `ringHTML`, `mdRender`, …). |
| `js/pages.js` | ~145 | Everyday pages: Dashboard, Monitor, Terminal + shared dashboard helpers (`kpi`, `updateKpis`, `renderSvc`). |
| `js/pages-create.js` | ~329 | Creation/media + screen: Models, Tools, Video, Training, Screen Studio, Live Vision, Bugs + the STT voice helpers (`dictate`, `_micUI`). |
| `js/pages-data.js` | ~199 | Data pages: Learning, A/B Test, Knowledge, Automation (incl. `screen_if`), Workflows, Batch. |
| `js/pages-system.js` | ~337 | System/insight: Nova Brain (3D map + `BRAIN_PALETTE`), Diagnostics, Audit, Open WebUI, Settings. |
| `js/pages-workspace.js` | ~250 | **The unified "Nova" page** — Chat + Agent merged, pro toggles, ✨Auto model, attach/open files, media (capture/image/video) in chat. (Replaced the old separate Chat + `pages-agent.js`, which were removed.) |
| `js/shell.js` | ~213 | WebSocket bus, toasts, notifications, command palette, theme, auth gate, `autoLite`, `boot()` (calls `route()` last). |

**Rule:** new pages go in the matching `pages-*.js`; `ROUTES` (in `core.js`) maps a route id → page
builder. A page builder returns `{html, mount}`; `mount` returns cleanup fns. Anything new added to
`index.html` is auto‑cache‑busted (the `/` handler globs `js/*.js` + `css/*.css` and stamps `?v=<mtime>`).

## CSS — cascade order matters
Loaded after the fonts/FA in this order (later files override earlier — preserved exactly from the split):

| File | Lines | Owns |
|---|---|---|
| `css/app.css` | ~334 | Base: palette vars, app shell, light‑theme tweaks, chat workspace. |
| `css/app-components.css` | ~315 | Apple layer, iOS notification center, Agent page, Twemoji/FA icons, living UI, responsive/mobile. |
| `css/app-visuals.css` | ~354 | Visual overhaul: multi‑accent palette, living background, glass chrome, gradients, light‑theme readability. |
| `css/app-extras.css` | ~37 | Lite‑visuals perf mode, reduced‑motion, Live (Screen Vision) page, accessibility focus. |

## Backend — layered DAG (unchanged)
`config ← core ← services ← api ← server`; nothing imports `server.py`. Routes live in `nova/api/*`
(now incl. `toolkit.py`, `control.py`, `screen_vision.py`, `understand.py`, `exec.py`, `stt.py`,
`files_api.py`, **`memory.py`** [IDEA‑8]); logic in `nova/services/*` (now incl. `stt.py` for the
Whisper loader and **`memory.py`** for local persistent memory). `server.py` also gained `_supervise()`
[IDEA‑10] which auto‑restarts any background loop that crashes hard. After the
M96 extraction, `server.py` is **~576 lines** — closer to a pure composition root (lifespan, loops,
middleware, router includes + a small set of app‑state‑coupled routes: ws, health/errors, selftest,
db‑status, chat‑export, kb/ingest).

## Lessons from the refactor
- **Split the genuine monoliths, not everything.** pages.js (1440) and app.css (1039) were real
  maintainability problems; cohesive single‑responsibility modules (`training.py` 366, `agent.py` 357)
  were left intact — fragmenting them would hurt readability, not help.
- **Behavior‑preserving splits must be byte‑identical.** Both JS and CSS were split by exact line ranges
  at section/function boundaries and asserted equal to the original; then render‑verified across all 23
  routes. Don't "refactor and tidy" in the same step — split first, verify, *then* tidy separately.
- **Order is load‑bearing.** Classic‑script global scope means JS load order + CSS cascade order must be
  preserved exactly. The split kept the original order; `index.html` lists the files in that order.
- **A render sweep catches what unit tests can't** — it surfaced HON‑12 (OWUI iframe blocked by our CSP).
