# Architecture

A map of how the AI Control Center is structured, so it can grow safely.

## Layered dependency graph (a strict DAG — no cycles)

```
config.py                  portable paths/endpoints (config.json)
   │
nova/core/db.py            SQLite: connection, schema, settings, history
   │
nova/core/events.py        WebSocket bus: push() → all dashboards
   │
nova/services/audit.py     audit trail            ─┐ business logic
nova/services/notifications.py  notifications+webhooks ┘ (depend on core)
   │
server.py                  composition root: builds the FastAPI app, wires
                           lifespan + middleware, defines the HTTP/WS routes,
                           ProcMgr, agent, metrics, toolkit
   │
static/  (index.html, css/app*.css, js/{core,pages,pages-create,pages-agent,pages-system,shell}.js)   the SPA dashboard
```

**The one rule:** a lower layer never imports a higher one.
`config ← core ← services ← server ← static`. Nothing imports `server.py`.

## What lives where

| Module | Responsibility |
|---|---|
| `config.py` | All paths + endpoints, resolved relative to the folder, overridable in `config.json`. Plus `ensure_cert()` for HTTPS. |
| `nova/core/db.py` | The only place that opens SQLite. Schema, migrations, `get_settings/set_settings`, `add_history`. |
| `nova/core/events.py` | `push(msg)` (thread-safe broadcast) + the `clients` set + `set_main_loop()`. |
| `nova/core/process.py` | Windows **Job Object** (`init_job_object`/`assign_to_job`) + `ps_args()` (UTF-8 PowerShell encoder). |
| `nova/core/http.py` | `http_json` / `http_ok` — tiny clients for Ollama/ComfyUI/Open WebUI. |
| `nova/services/metrics.py` | `collect_metrics()` (CPU/RAM/disk/GPU) + CPU temp + shared `get/set_last_metrics()`. |
| `nova/services/audit.py` | `audit(actor, action, detail, status)` → DB + live stream. |
| `nova/services/notifications.py` | `add_notification(...)`, `send_webhook(...)`, category inference. |
| `nova/services/jobs.py` | `Job` + `ProcMgr` (`PM`): tracked background jobs, stop/pause/resume, output streaming. Training callback injected via `set_training_hook`. |
| `nova/services/screen.py` | Screen capture/record/read/understand + click-to-act (mss + imageio + qwen2.5-VL + pyautogui). |
| `nova/services/chat.py` | Conversation/message store + the streaming chat-send flow (`stream_chat_send`, RAG + compare). |
| `nova/services/ollama.py` | Ollama client — `ollama_models` (with capability tags), `model_caps/tags`, `ollama_chat_once`. |
| `nova/services/owui.py` | Open WebUI integration — runs python in the OWUI container to read/patch webui.db. |
| `nova/services/files.py` | File text extraction (txt/md/pdf/docx/image-OCR) + chunking for embedding. |
| `nova/services/kb.py` | Knowledge base (local RAG) — embed, status, cosine search, ingest. Builds on `files`. |
| `nova/services/browser.py` | Browser automation — headless `browse`, `open_url_default`, persistent on-screen Chromium (`visible_browse`, YouTube). |
| `nova/services/agent.py` | Agent Mode ReAct loop — tool defs, `agent_tool`, `agent_run`, safety guards. `run_action` is injected via `set_run_action()`. |
| `nova/services/training.py` | Continuous-learning datasets + the fine-tune job lifecycle (start/pause/resume/stop, live progress, stats, run recording). |
| `nova/services/schedules.py` | Automation engine — `run_action` dispatcher, schedule execution, workflow runner, A/B testing. |
| `nova/services/settings.py` | Settings + auth — redaction, token hashing, the `token_ok` auth gate, settings-save / login flows. |
| `nova/services/tts.py` | Text-to-speech via the local Piper voice. |
| `nova/services/backup.py` | Full-state export / merge-restore (settings, chats, schedules, workflows, KB, datasets). |
| `nova/services/insights.py` | Proactive tips, the LLM daily briefing, and the co-pilot suggestion (registers the briefing hook). |
| `nova/api/*.py` | 21 `APIRouter`s, each importing only `nova.*` + config: `bugs`, `notifications`, `audit`, `history`, `conversations`, `analytics`, `models`, `owui`, `kb`, `media`, `agent`, `search`, `metrics` (metrics/services/processes), `chat`, `training`, `schedules` (+workflows/abtest), `screen`, `settings` (+auth), `tts`, `backup`, `insights` (+briefing/copilot). |
| `server.py` | Composition root (~495 lines): FastAPI app, lifespan, security middleware, background loops, `include_router(...)` + dependency-injection wiring, and a few misc routes (exec/toolkit, stt, upload, file serving, db-status, selftest, kb-ingest). |

## The "extract → re-import" pattern (how this refactor stays safe)

When a primitive moves into a module, `server.py` imports the name back into its
own namespace:

```python
from nova.core.db import db, get_settings, set_settings, add_history
from nova.core.events import clients, push, set_main_loop, get_loop
from nova.services.audit import audit
from nova.services.notifications import add_notification, send_webhook
```

So the ~2000 lines of route code keep calling `db()`, `push()`, `audit()` unchanged.
Each extraction is verified with `python run_tests.py` (40 checks) **before** the next.

## Adding a new feature (the recipe)

1. **Data** it needs → add a table in `nova/core/db.py` (`init_db`) + accessors.
2. **Logic** → a function/class in `nova/services/<feature>.py` (import from core only).
3. **HTTP/WS** → add the route in `server.py` (or, as routers are extracted, a
   `nova/api/<feature>.py` `APIRouter` included by `server.py`).
4. **UI** → a page function in the matching `static/js/pages-*.js` + a `ROUTES` entry in `core.js`; styles in the appropriate `css/app-*.css` (see `docs/frontend-structure.md`).
5. **Verify** → `python run_tests.py` stays green; add a check for the new surface.

## Frontend

The SPA is split into ordered modules loaded sequentially (shared global scope,
no bundler — load order matters). After the HON‑11 refactor (M78/M79) the page code is
modular — full map in `docs/frontend-structure.md`:

- `static/js/core.js` — DOM/`api` helpers, the icon engine (Font Awesome via a
  MutationObserver), `State`, the WebSocket-fed event `bus`, the `I18N` table + `t()`,
  the hash router (`ROUTES`, `route`, `renderNav`), and render helpers.
- `static/js/pages.js` · `pages-create.js` · `pages-agent.js` · `pages-system.js` — page
  builders (one `function Page()` → `{html, mount}` per screen), grouped by domain.
- `static/js/shell.js` — WebSocket connect, toasts, notification center, command
  palette, theme, auth gate, `autoLite`, and `boot()` (called last).
- CSS is likewise split into `css/app.css` → `app-components.css` → `app-visuals.css` →
  `app-extras.css` (cascade order preserved).

This is intentionally framework-free and CDN-light; it can be migrated to a
component framework page-by-page because each page is already an isolated unit.

## Refactor status

The monolith is fully decomposed: **21 API routers + 18 service modules + 4 core modules**,
with `server.py` down from ~2400 lines to **~495** — now essentially a composition root
(app/lifespan/middleware/`include_router`, the background loops, and a few small misc routes:
exec/toolkit, stt, upload, file serving, db-status, selftest, kb-ingest). Each group was moved
one at a time with `python run_tests.py` green (42/42) and self-test 13/13 after every step.

**Dependency injection keeps the DAG acyclic** where logic is genuinely cross-cutting:
- `run_action` (the ProcMgr-backed automation dispatcher, in `services/schedules.py`) is
  injected into `services/agent.py` via `set_run_action()`.
- `build_briefing` (in `services/insights.py`) is injected into `services/schedules.py` via
  `set_briefing_hook()` so the automation engine can render a briefing without importing the
  insights layer.
- `record_training_run` self-registers as the ProcMgr training hook from `services/training.py`.
- live metrics are shared via `services/metrics.py` `get/set_last_metrics()` (the server's
  metrics loop publishes; routes and insights read).

So no service imports `server.py`, and the layering `config ← core ← services ← api ← server`
holds with zero cycles.

## Run & test

```
setup.ps1        # one-time: deps + browser + config
start.cmd        # launch → http://localhost:8900
python run_tests.py   # 40-check live suite
```
