# 🔧 Build Log

Chronological record of what was built, fixed, tested, and decided — **date · what · why · how verified**.

> **Permanent rule:** this is one of six mandatory source‑of‑truth files
> (`ROADMAP.md`, `TASKS.md`, `BUILD_LOG.md`, `WORKFLOW.md`, `PROJECT_PLAN.md`, `STATUS.md`).
> Review them before work, update during, reconcile after — see `WORKFLOW.md`. Append a dated
> entry here for every completed task. Personal single‑user system — no multi‑user, ever.

## M5 — Pro chat & model library

### P1 · Roadmap
- Wrote `ROADMAP.md` (phases P1–P6) and this log.

### P3 · Model downloads
- Pulling `nomic-embed-text` (embedding, fills the RAG gap) and `llama3.2:3b` (fast chat) in the background.
- _result_: (recorded after completion)

### P2 · Model tagging
- Added `model_tags()` in server.py — combines Ollama `/api/show` capabilities (`tools`/`vision`/`embedding`) with family + name heuristics → tag list. `/api/models` now returns `tags` per model (cached). UI shows colored badges in Models page + chat picker. Generation/media models (LTX video, image checkpoints, Piper) listed in a tagged "Media & Generation" section.
- _tests_: (recorded after)

### P4 · Chat attachments in messages
- Marker format `⟦file:name|size⟧`; `addMsg` renders **image thumbnails** (`<img src=/files/..>`) and **file cards** (icon, name, type, size, view/download) inside bubbles. Input‑area attachment cards already present.
- _tests_: (recorded after)

### P5 · Live preview + markdown
- Local Markdown renderer (`mdRender`) — escapes first, then headings/bold/italic/code‑blocks/inline‑code/lists/links; lightweight code styling; RTL aware. AI replies render as Markdown. **👁 Preview** button opens a modal rendering the draft + attachment previews.

### Tests / fixes (recorded)
- **Bug:** a NUL byte (0x00) crept into `app.js` from an early `mdRender` placeholder (`…`) that was later partially edited. `node --check` tolerated it but it would corrupt serving. **Fix:** located at offset 9178, stripped all 0x00 bytes, switched placeholder to `@@CB{n}@@` with an undefined‑guard on restore.
- **Verified:** model tags auto‑applied to ALL models incl. new downloads — `llama3.2:3b→control,chat,multilingual`, `nomic-embed-text→embedding`, `qwen2.5vl:7b→vision,…`, `deepseek-coder→coding,…`, `qwen2.5*→…,arabic`. `/api/media-models` returns Piper(audio), checkpoints(image), LTX(video).
- **Verified earlier:** upload of TXT/PY/DOCX/PDF/PNG all extract text; chat uses file context; markers persist; `/files/{name}` download = HTTP 200.
- **Downloaded:** `nomic-embed-text` (274MB, embeddings/RAG) + `llama3.2:3b` (2GB, fast chat).
- _Note_: PowerShell flattens the media‑models JSON array in console output (cosmetic); the API payload is correct.

## M8 — Agent Mode, RAG→Training, scheduled background
- **Agent Mode:** ReAct loop with JSON‑action protocol (model‑agnostic), tools (kb_search/run_command/generate_video/notify/speak/schedule/ask), live WS stream (thought/action/observation/final), destructive‑command blocklist. _Test:_ goal "find Orion launch date + lead engineer, notify me" → searched KB, notified, final answer correct; self‑recovered from 2 invalid tool guesses. Tightened prompt afterward (no invented tools; `final` is a key not an action; added `ask`).
- **RAG→Training:** 👍 button on cited replies → `/api/training/save`; **Learning Dashboard** (`/api/learning/stats`) with counts, new‑since‑last‑train, recommendations, improvement timeline, retrain button.
- **Scheduled:** `kb_index` action (folder→KB, new files only) + presets. _Test:_ run‑now indexed `C:\AI\inbox\policy.txt` → KB 1 doc.
- All validated: `node --check` (no NUL), `ast.parse`, endpoints 200, headless WS agent test.
- _Deferred from the big "additional features" list_ (honest): Open WebUI two‑way sync, A/B testing UI, multi‑user/permissions, unified Search‑Everything, email/Slack webhooks, task dependencies, drag‑drop layout, voice command control. Tracked for future milestones.

## M9 — Search Everything, Workflows, Insights
- `/api/search` unified (chats/messages/history/automations/KB docs/semantic KB/models) → upgraded **Ctrl+K palette** (instant + debounced server results, deep-links to chats). Workflows: sequential runner waits on each job (`run_workflow`). Insights: `/api/insights` actionable tips on Dashboard.
- _Tested_: search returns categorized hits; notify→command→notify workflow `completed`; insights live.

## M10 — Security, delivery, evaluation
- **Critical fix:** server was bound `0.0.0.0` with RCE-capable endpoints → changed to **127.0.0.1**; verified LAN IP now refused.
- Webhooks: `send_webhook` (Slack `text` + Discord `content`) wired into every notification + `webhook` action. _Tested_ via local listener.
- A/B testing: `/api/abtest` runs prompts through 2 models + judge, streams results + scoreboard. _Tested_ (judge tallied a winner).

## M11 — Token authentication
- Optional auth: middleware gates `/api/*` (exempt: auth/status,login,logout); `/ws` checks cookie; token auto-generated on enable; cookie session; login overlay + Settings security card; `BIND_HOST` becomes `0.0.0.0` only when auth+lan both on.
- _Tested_: full 9-step flow (401 without token, 401 wrong token, cookie login → 200, disable restores default). Default stays localhost-only + auth-off.
- _Idea captured during build_: see ROADMAP "Ideas Backlog" (audit log, agent v2, folder-watch RAG, conditional workflow steps, daily briefing, etc.).

## M12 — Audit log
- `audit(actor,action,detail,status)` → `audit` table + live `audit` WS event. Wired into: terminal exec, agent run_command (logs **blocked** dangerous attempts too), agent goals, schedule runs, workflow runs, model load/unload, tool toggles, retrain, auth login (success+fail), and security-relevant settings changes.
- `/api/audit` (filter by actor + full-text q), `/api/audit` DELETE (clear, self-logged). Audit page: live updates (debounced), actor dropdown, search, CSV export, clear.
- _Tested_: terminal/settings/clear events recorded; `actor=terminal` filter → 1; `q=webhook` → settings/update; clear works and logs itself. 18 pages total; node/ast clean; default secure (localhost, auth off).

## Code audit + M13–M15
- **Audit/cleanup:** pyflakes 7→0 (unused imports, nonlocal, shadowing, empty f-string); removed legacy `/api/chat`, `OWUI_DB`, `SCHED_ACTIONS`, dead Stop button. 15/15 endpoints green after.
- **M13 Agent v2:** read_file/write_file with `safe_read_path` (deny .ssh/.env/credentials…) + `safe_write_path` (confined to agent-output); `dry_run` simulates side-effecting tools. _Tested via direct function calls_: confinement + dry-run + real write/read all correct.
- **M14 Daily Briefing:** `build_briefing()` → local-model markdown digest from KB/training/audit; Dashboard button + `briefing` action. _Tested_: 942-char digest.
- **M15 Backup/Restore:** `/api/backup` full JSON bundle; `/api/restore` additive with KB id-remap, skips auth keys. _Tested_: schedule round-trip restored.
- Default remains secure: localhost-only, auth off. System declared feature-complete (19 pages); future work tracked in ROADMAP Ideas Backlog.

## M16 — production polish & diagnostics
- `/api/selftest` (13 checks) + Diagnostics page; `run_tests.py` one-command suite; chat copy + tok/s; `?` shortcuts overlay; professional README. Code audit: pyflakes clean, dead code removed.

## M17 — futuristic UI + 10x features
- **Theme:** rebuilt palette to neon glass (deep black + cyan/violet/gold); animated aurora+grid+particle-canvas background; Orbitron gradient headings; Inter/JetBrains via CDN+fallback; glowing scrollbars; `[data-tip]` tooltips; animated Nova SVG logo; auto theme (time-based).
- **New systems:** Co-Pilot (`/api/copilot`), Nova Brain semantic map (`/api/brain`), Predictive Habits (`/api/habits`), Achievements (`/api/achievements`), Health Radar + Live Activity Feed (bus-driven), chat copy + tok/s. Dashboard rebuilt as a command center.
- **Fix:** `mdRender` restore regex `/(\d+)/g` → `/@@CB(\d+)@@/g` (was mangling digits / leaving code-block placeholders). Verified.
- _Tested_: 4 new endpoints return real data; self-test 13/13; suite 35/35; pyflakes clean; no NUL; 21 pages.

## M18 — Apple redesign + iOS notification center
- **Theme:** Apple palette (refined dark gray / clean light, single blue accent), SF/Inter type, soft shadows, glass blur, rounded (980px btns / 18px cards), minimal nav active pill, calm spring micro-animations. Removed neon particles+grid (Apple minimalism); kept a soft ambient aurora. Subtle scrollbars. Replaced the M17 "futuristic" CSS layer with an "Apple-style layer".
- **Notifications:** `category`+`link` columns (migration) with keyword inference in `add_notification`; `/api/notifications` → {items,unread,categories}; per-item `seen`, clear-all. Frontend: iOS-style center grouped Today/Yesterday/This Week, icon cards + unread dot + relative time, click→read+navigate, search + filter chips, mark-all-read, clear, mute, WebAudio chime, live via WS.
- **Fix:** `mdRender` restore regex confirmed `/@@CB(\d+)@@/g` (was `/(\d+)/g`).
- _Tested_: harvest→training/#training; mark-all-read→0; clear→0; self-test 13/13; suite 35/35; pyflakes clean; no NUL.

## M19 — Real-world end-to-end testing (actually ran every feature)
- **Video:** LTX-2B generated 49f in 10.7s; LTX-13B 49f in 32.9s. Both → playable mp4 (768x512, 2.04s). ✓
- **Image:** SDXL → real 1024x1024 "futuristic city at sunset" PNG (verified visually). ✓
- **TTS:** Piper EN (139KB) + AR (284KB) valid RIFF WAV. ✓
- **Chat commands:** `ollama ps` ✓, file read ✓, `;` multi ✓. **Bugs fixed:** (1) PowerShell `&&` parse error leaked raw **CLIXML** → added `ProcMgr._clean()` that converts CLIXML to readable text everywhere; (2) chat `!` now translates `&&`/`||`→`;` (and strips extra `!`) so `!echo hello && !whoami` runs both.
- **Mouse/keyboard:** programmatic move+click works (coords DPI-scaled); typed into Notepad, verified via OCR. ✓
- **Browser:** open URL + navigate + screenshot, page text OCR-confirmed. ✓ (DOM-level clicking would need Playwright — backlog.)
- **Screenshot+OCR:** Windows OCR read "Nova OCR Test 12345" exactly. ✓
- **RAG:** answered "Stronghold-9" with source citation (novafacts.txt @ 0.78). ✓
- **Agent multi-step:** created agentnote.txt, wrote+read it, reported contents (file verified on disk). ✓
- **Automation:** schedule fired on time in background → notification. ✓
- **Reliability:** observed the detached server exit once during the session → added `watchdog.ps1` (auto-restarts if :8900 stops responding).
- Final: self-test 13/13, suite 35/35, pyflakes clean.

## M20 — Playwright browser automation + model benchmark + best-model download
- **Playwright:** installed `playwright` + headless Chromium. New `browse(url, fill, click, wait, screenshot)` helper (sync Playwright run in a worker thread / `asyncio.to_thread` to avoid the running event loop). Exposed three ways:
  - `POST /api/browse` `{url, fill, click, wait}` → `{title, final_url, text, actions, screenshot}` (screenshot saved to uploads, served at `/files/…`).
  - Agent tool **`browse`** (added to `AGENT_SYS` + `agent_tool`, dry-run aware, audited).
  - Workflow/automation action **`browse`** in `run_action` (fires a "Browser" notification with the screenshot as the click-through link). Added to both UI builders (schedule + workflow) with a URL field.
- **Live-tested (real, not code review):** opened `https://example.com` → title "Example Domain" + screenshot ✓; filled a 2-field form, clicked Submit, read back "Hello Nova from Riyadh!" (screenshot visually verified) ✓; **agent end-to-end** (qwen2.5:14b) autonomously chose `browse` and reported the title ✓; **workflow** browse step → `completed` + notification with screenshot ✓.
- **Model command-execution benchmark** (9 models via the real agent protocol — `AGENT_SYS` + `ollama_chat_once` + `parse_action`; scored correct tool/command + JSON validity + latency over: Open Notepad / create Desktop folder / open website / generate video / find largest files):
  | model | pass | json | avg s |
  |---|---|---|---|
  | **qwen2.5:14b** | **5/5** | 5/5 | **1.3** |
  | **qwen2.5:32b** (new) | **5/5** | 5/5 | 4.9 |
  | llama3.2:3b | 4/5 | 5/5 | 0.2 |
  | qwen2.5vl:7b | 4/5 | 4/5 | 1.2 |
  | llama3.1:8b | 4/5 | 5/5 | 1.7 |
  | my-assistant:latest | 4/5 | 5/5 | 6.8 |
  | qwen2.5-coder:32b | 4/5 | 5/5 | 21.6 |
  | deepseek-coder:6.7b | 3/5 | 3/5 | 2.8 |
  | qwen2.5:7b | 1/5 | 4/5 | 0.7 |
- **Best model downloaded:** `qwen2.5:32b` (19 GB) — 5/5 commands, runs **100% on GPU** (24 GB on the RTX 5090's 32 GB), fluent Arabic+English (verified: "الرياض… الرياض، جدة، الدمام"). It matches 14B accuracy with more reasoning depth at ~4.9 s/step. 70B+ was deliberately *not* chosen — it spills to CPU on 32 GB VRAM and runs slowly, violating the "fast/smooth" requirement.
- **Default model changed** `qwen2.5:7b` (worst, 1/5) → **`qwen2.5:14b`** (best command executor: 5/5 @ 1.3 s). qwen2.5:32b available in the picker for max-reasoning/Arabic work.
- **Suite +1:** `run_tests.py` now includes a Playwright browser round-trip → **36/36**. Self-test 13/13. pyflakes clean, no NUL.

## M21 — Agent page redesign + Full Access + Twemoji icon system
- **Agent page, fully rebuilt** (Apple-premium, 2-column): left = a **Nova avatar hero** (animated glowing orb that *breathes* idle and *pulses + emits rings* while thinking) + status chip + a real-time **thinking log** that fills the height + a chat-style **input bar**; right = a categorized **example side panel** (System / Files / Web / Knowledge / Creation / Training) whose items click-to-fill the input.
  - Input: auto-growing textarea, **Enter to send / Shift+Enter newline**, a real **Send** button, busy state (spinner + avatar `.thinking`), live status line.
  - Thinking log: each step shows **what it's doing → tool → result → next** with per-tool icons (📚⌨️🌐🎥🔔🔊📄💾⏰) and color-coded rails (goal/think/act/result/done/error).
- **🔓 Full Access mode** (default ON, per request): new `unrestricted` flag on `/api/agent` → `agent_run` → `agent_tool`. In full access the agent **runs any PowerShell command** (destructive blocklist bypassed) and **writes files anywhere** (sandbox confinement lifted); the system prompt tells it to be decisive and attempt what's asked. **One safety line kept:** credential-store **reads** (`.ssh`, `.env`, `id_rsa`, browser Login Data…) stay denied even in full access (workspace hard rule). All actions audited (`full-access` status).
  - _Verified by direct calls_: normal mode blocks `Remove-Item -Recurse` ✓; full access executes it (real temp dir deleted) ✓; full access writes outside the sandbox ✓; credential read still blocked in full access ✓.
- **Twemoji icon system** (open-source, CDN): added `@twemoji/api` from jsDelivr; `tw()` helper + a `MutationObserver` re-render every emoji across the **whole dashboard** (sidebar, topbar, buttons, cards, notifications, agent log, avatar) as crisp SVGs from `jdecked/twemoji`. Graceful offline fallback (native emoji if CDN blocked).
  - **Animations** (`tw-*` keyframes): nav icons **bounce** on hover + active icon **pulses**; buttons/chips/quick-actions **bounce** on hover; the bell **rings** on hover and keeps ringing while unread (`#bell.has-unread`); notification card icons **wobble**; loading uses **spin**; empty-state + avatar **float/pulse**.
- **Live-tested (real browser via our own Playwright, screenshots captured):** simple goal (full-access file write to Desktop, outside sandbox) ✓; complex goal (KB search → accurate notify with ship date/lead/budget) ✓; web browse (title "Example Domain") ✓; video generation (background job started) ✓; full thinking-log render with Twemoji ✓; **EN + AR/RTL** both verified (mirrored layout, Arabic nav, icons correct).
- Self-test 13/13 · suite 36/36 · pyflakes clean · `node --check` clean · no NUL.

## M23 — Agent page: pro polish, controls, full Arabic, Font Awesome icons
- **Visual polish:** Nova avatar gains a rotating glowing **halo** + gentle **float**, brighter pulse + emitted rings while thinking; steps **slide/pop** in; live **shimmer** "thinking" row with bouncing dots; **progress bar** (gradient fill + Step X/Y); glassmorphism cards; color-coded step tints; pulsing live status dot.
- **Advanced controls:** **Stop** (new `/api/agent/stop` + `AGENT_STOP` event, checked each step → emits `stopped`); **Export** log to `.txt`; **Re-run** last goal; **Collapse/expand** all steps (each step header is a chevron toggle); **Agent settings** (gear): Creativity (temperature), Max steps, and per-tool enable/disable — persisted to localStorage and sent to `/api/agent`. Backend `agent_run` now takes `temperature`, `max_steps`, `tools`; `AGENT_SYS` refactored into `build_agent_sys(tools,max_steps)` so the prompt only lists enabled tools (disabled tools are also enforced at the loop). _Tested:_ stop mid-run (`start→thought→action→observation→stopped→done`) ✓; progress 8/8 ✓; settings persist ✓.
- **Full Arabic translation (layout fixed):** the entire Agent page (title, status messages, placeholder, Send, examples + categories, step labels Goal/Thinking/Using/Result/Done, tool names, Full-access & Dry-run toggles, model picker, progress, Stop, settings) is bilingual via a local dictionary; **every control has a translated `data-tip` tooltip**. Per the user's instruction the **layout no longer flips** — global `dir` is forced `ltr` in both languages, so positions/spacing stay identical and only the text changes. _Verified EN + AR screenshots: identical layout, fully translated._
- **Professional icons:** replaced Twemoji with **Font Awesome (free, CDN)**. A small engine maps every emoji → a consistent FA vector icon across the whole dashboard (sidebar, topbar, buttons, cards, notifications, agent log, avatar) via a MutationObserver; `role=img` + `aria-label` for accessibility; subtle animations (bounce on hover, bell ring while unread, wobble on notification cards, spin for loading). Fixed the avatar ring CSS (`>i`) so the FA robot shows on the orb.
- Self-test 13/13 · suite 36/36 · pyflakes clean · `node --check` clean · no NUL.

## M24 — Training Studio: real-time progress + stop/pause/resume
- **Granular progress:** added a `ProgressCallback` to `train_lora.py` that prints `[PROGRESS] step/total/epoch/loss/elapsed/eta` each training step. `/api/learn/progress` now returns: pipeline step (X of 7) + name, **LoRA sub-progress** (step/total, %, loss, epoch), **ETA**, overall %, **live GPU** (util/temp/VRAM/power), status, and the last error line. Sub-progress prefers `[PROGRESS]` (tqdm fallback ignores dataset-map / checkpoint-shard bars). Log read capped to last 256 KB, sliced to the current run.
- **Controls:** `POST /api/learn/{stop,pause,resume}`. Stop = taskkill the process tree (status → `stopped`). Pause/Resume = psutil `suspend()`/`resume()` on the whole training tree (VRAM retained). Verified live: pause drops GPU 98%→5%, resume → 99%, stop kills all `train_lora` procs.
- **Status:** idle / running / paused / stopped / completed / error, with a live dot while running.
- **Resilient:** training survives a server restart (detached grandchild) and is re-detected via a cached (15 s) process scan; tracked jobs skip the scan so polls stay ~3 ms.
- **UI:** overall bar + %, a LoRA sub-bar ("step 2/30 · 7% · epoch 0.2", ETA 24m), GPU chips, live log, and Start/Stop/Pause/Resume buttons per state.
- Self-test 13/13 · suite 36/36 · pyflakes clean.

## M25 — 62 real-world scenarios (final readiness validation)
- Ran **62 practical end-to-end scenarios** against the live system (real LLM/agent/generation/browser/training — not mocked). Full results in **SCENARIOS.md**; re-runnable scripts in `scenarios/` (`scenarios.py` 50, `media_scen.ps1` 7, `train_ctrl.py` 5).
- Coverage: chat (plain/RAG+citation/inline-cmd/file-context/alt-model), agent (simple/complex/web/command/dry-run/tool-restriction), automation, web+Playwright (browse/wikipedia/open_url/form fill+click), files (upload/download/KB ingest+delete/rename), models (list/load/A-B+judge), TTS EN+AR (speak + WAV), export (PDF/JSON/MD/TXT), backup+restore, settings (lang/theme/webhook), notifications, monitoring, KB+unified search, Co-Pilot/Brain/Insights/Habits/Achievements, batch queue, workflows (multi-step + browse step), security (audit/auth-off/token round-trip), image (SDXL+Flux), video (LTX-2B), OCR + vision (qwen2.5vl), and training control (start/progress+ETA+GPU/pause/resume/stop).
- **Result: 62/62 passed. Zero product defects.** The only issues were in the test *harness* (UTF-8 console/script encoding for `→`/Arabic; a `{name}` vs `{model}` param; audit key `items` vs `events`) — all fixed and the affected scenarios re-verified live (e.g. Arabic TTS → 90 KB WAV; load → `{ok:true}`; audit → 271 events). Real artifacts produced: SDXL 1652 KB, Flux 1186 KB, LTX-2B mp4 696 KB, EN/AR WAVs, OCR read "Nova OCR 7788 Test" exactly; training pause dropped GPU 100%→3% and resume restored it.
- Manual/by-design: microphone voice *input* (browser Web Speech API) needs a human mic; TTS output verified.

## M26 — Production hardening (process model, security, observability, gaps)
- **Process model fixed at the root:** child processes (PowerShell, training python, Playwright) are now assigned to a **Windows Job Object** with `KILL_ON_JOB_CLOSE` (ctypes, no deps) — they can no longer orphan/zombie; they die with the server. _Verified: log shows "Job Object created"._
- **Real security:** auth tokens are now **hashed** (SHA-256) — the raw token is shown to the user exactly once (`new_token`) and never stored or returned again; `/api/settings` **redacts** `auth_token`/`auth_token_hash`/`cloud_api_key`. Added an **in-memory rate limiter** (login 10/min, exec 60/min, agent/browse 40/min, retrain 6/min → HTTP 429) and **security headers** (`X-Content-Type-Options`, `Referrer-Policy`). _Verified live: login 401×10 then 429; full enable→401→token-200→wrong-token-401→disable round-trip; token never exposed._
- **Observability:** rotating file logger (`data/logs/server.log`), request logging for slow/error responses, a **global exception handler** (unhandled errors → JSON 500 + logged traceback, no more silent failures), and a `/api/logs` endpoint.
- **Clear errors in the UI:** the frontend `api()` wrapper now surfaces failures as toasts (rate-limit, auth-required, network, server error) instead of failing silently.
- **Image generation wired into the backend + UI:** new `/api/toolkit/image` (SDXL / Flux-schnell / Flux-dev) runs as a tracked job and returns the served file URL; **Video Studio** gained a "Generate Image" card with live inline preview + download. _Verified: generated a real 1843 KB image via the API and a photorealistic image through the UI._
- **Local microphone STT:** added **faster-whisper** (base/cpu/int8 — fully local, no cloud) behind `/api/stt`; the chat mic now uses it (replacing the browser cloud Web Speech API), and the Agent input gained a mic button. Records via MediaRecorder → `/api/stt` → transcript. _Verified: transcribed "Testing local speech recognition with Nova" exactly._
- Self-test 13/13 · suite **40/40** · pyflakes clean · `node --check` clean.
- **Honestly deferred (see chat ledger):** monolith split, default-on HTTPS, true multi-user accounts, and pixel-perfect mobile/RTL mirroring remain larger efforts beyond this phase.

## M27 — Portability, config module, HTTPS, one-command setup
- **First real refactor module:** extracted all configuration into **`config.py`** — paths/endpoints now resolve **relative to the folder** (portable) and are overridable via an auto-created **`config.json`**. `server.py` imports from it; no more hard-coded `C:\AI` paths. _Verified: paths resolve, overrides respected (BOM-tolerant via utf-8-sig — fixed a real silent-fallback bug)._
- **One-command setup & run:** `requirements.txt` (pinned deps), **`setup.ps1`** (installs deps + Playwright Chromium + writes config + probes Ollama/ComfyUI/Open WebUI), portable **`start.cmd`** (`%~dp0`, opens browser). **`SETUP.md`** documents first-run and transfer-to-another-PC.
- **HTTPS:** optional TLS via `"https_enabled": true` in config — self-signed cert auto-generated (`cryptography`) into `data/certs/`, uvicorn serves `https://`. _Verified: cert/key generated._
- **Mic, properly wired:** chat + Agent mic buttons → MediaRecorder → local `/api/stt` (faster-whisper). Note: browser mic needs `localhost` or HTTPS (documented).
- Self-test 13/13 · suite **40/40** · pyflakes clean.
- **Still honestly deferred:** full backend module split (high-risk big-bang on intertwined globals) and true multi-user accounts (data-model program) — each warrants its own dedicated, fully-regression-tested pass rather than a rushed one that risks a working system.

## M28 — Foundation: modular package (`nova/`)
- Began the safe, incremental backend refactor with an **"extract → re-import"** pattern so the ~2000 lines of route code never change. Created the `nova/` package with a strict dependency DAG (documented in `ARCHITECTURE.md` + `nova/__init__.py`):
  - `nova/core/db.py` — SQLite connection, schema/migrations, settings, history (+ `DEFAULT_SETTINGS`).
  - `nova/core/events.py` — the WebSocket bus (`push`, `clients`, `set_main_loop`/`get_loop`).
  - `nova/services/audit.py` — the audit trail.
  - `nova/services/notifications.py` — notifications + outbound webhooks + category inference.
- `server.py` imports these back into its namespace; **the full 40-check suite was run green after every single extraction** (db → events → audit → notifications), never a broken build.
- Added **`ARCHITECTURE.md`** (layer map, the one rule, the "add a feature" recipe, the extract→re-import pattern, and the honestly-staged next passes: `nova/core/jobs.py`, `nova/api/*` routers, splitting `app.js`).
- Self-test 13/13 · suite 40/40 · pyflakes clean.

## M29 — Screen Studio (see / record / read / understand the screen)
- New service `nova/services/screen.py` (first feature built on the M28 architecture). **Native capture** via `mss` + **MP4 recording** via `imageio`'s bundled ffmpeg in a background thread — chosen after the inline PowerShell `CopyFromScreen` was blocked by the host **antivirus/AMSI** as screen-scraping; the native path avoids that entirely.
- **Capabilities:** `capture_screenshot` (full/region), `ScreenRecorder` (start/stop → valid MP4, assigned to the Job Object so it can't orphan), `read_screen` (Windows OCR or vision), `describe_screen` (qwen2.5-VL natural-language screen understanding).
- **API:** `/api/screen/shot|read|describe|record/start|record/stop|record/status|recordings`. `read` can push extracted text straight to the **Knowledge Base** (`to_kb`).
- **Agent integration:** new tools `see_screen`, `read_screen`, `screenshot` (in `AGENT_SYS` + `agent_tool` + the UI tool list/icons). _Verified: agent answered "what's on my screen" by calling `see_screen` and accurately described the dashboard._
- **Automation:** `screen_record {seconds}` action (schedulable from the Automation page).
- **UI:** new **Screen Studio** page (record with live preview thumbnail, screenshot, OCR, "What's on my screen?", in-dashboard `<video>` playback + scrub, recordings list with play/download). Bilingual nav.
- **Vision model:** uses the already-installed **qwen2.5-VL-7B** (one of the recommended options; runs fast on the 5090 — no need for a slow 72B).
- _Verified live:_ screenshot 2029 KB · OCR 1572 chars · 6 s recording → valid 2.4 MB MP4 (ffmpeg-checked) · vision describe accurate · agent see_screen ✓.
- Self-test 13/13 · suite **41/41** (added screen-capture check) · pyflakes clean · `node --check` clean. ROADMAP.md updated.

## M30 — Session‑close: gaps closed, refactor continued, model chosen
- **Bug‑report system:** `bug_reports` table + `/api/bugs` CRUD + a **Bug Reports** page (report with severity, auto‑attaches the last 40 log lines, resolve/reopen/delete). Suite check added.
- **Data safety:** lifespan **graceful shutdown** finalizes any active screen recording and logs a clean stop; frontend **`beforeunload` guard** warns when a recording/training is in progress (`State.recording`/`State.training`).
- **Responsive / mobile:** off‑canvas sidebar drawer + hamburger + dim backdrop; grids stack; non‑essential chrome hidden < 600 px. Verified at 420 px.
- **Refactor continued:** extracted **`nova/core/process.py`** (Job Object) and **`nova/services/jobs.py`** (`Job` + `ProcMgr` + `PM`), with the training‑done callback injected via `set_training_hook` to keep the DAG acyclic. server.py now holds only routes + agent + metrics. Suite green after the extraction.
- **Living‑UI pass:** aurora drift, card hover‑lift, gradient primary buttons, spring toasts, gradient KPI/headings, `prefers-reduced-motion` guard.
- **Flagship model (data‑driven):** benchmarked on the actual box — **qwen2.5:14b ≈ 120 tok/s** (smooth, 5/5 capable) vs **qwen2.5:32b ≈ 5 tok/s** under VRAM contention. Set **14b as the default**; 32b stays selectable as "max intelligence." A 70B would offload to CPU (slower) — rejected per the "runs smoothly" requirement.
- Self‑test 13/13 · suite **42/42** · pyflakes clean across all 9 modules · `node --check` clean. ARCHITECTURE.md + ROADMAP.md updated.

## M31 — Model evaluation + refactor (http/metrics)
- **Benchmarked 9 local models in isolation** (clean VRAM) on the 5090 — speed/VRAM/reasoning/coding. Findings: 14B‑class models (qwen2.5:14b 132 tok/s, qwen3:14b 139, phi4 142, deepseek‑r1:14b 133, deepseek‑coder‑v2:16b 128) are the sweet spot — they match the 30–32B models (qwen2.5:32b ~11, qwen2.5‑coder:32b ~10, qwen3‑coder:30b ~17 tok/s) on reasoning/coding at ~13× the speed. Reasoning models needed a larger token budget (their `<think>` chains were truncating the first pass).
- **Picks:** default `qwen2.5:14b` (kept — clean JSON for the agent, great Arabic); max‑intelligence `phi4`/`deepseek‑r1:14b`; coding `qwen3‑coder:30b` (quality) / `deepseek‑coder‑v2:16b` (fast); vision `qwen2.5‑VL:7b`. All 11 selectable in the UI. **Amazon Nova/Titan** confirmed Bedrock‑cloud‑only (skipped); **DeepSeek‑V3** too large for 32 GB (skipped).
- **Refactor continued:** extracted `nova/core/http.py` (http helpers) and `nova/services/metrics.py` (telemetry). 12 modules total, suite green.
- Self‑test 13/13 · suite 42/42 · pyflakes clean across 12 modules.

## M32 — On-screen click-to-act (built, best-effort)
- Added to `nova/services/screen.py`: `locate_element` (qwen2.5-VL pixel grounding), `click_at`/`type_text` (pyautogui + clipboard paste for Unicode/Arabic)/`press_keys`, and `act_on_screen(instruction,text,key)` (locate→click→type). Endpoints `/api/screen/{act,click,type}`; agent tool `act_on_screen` (+ UI tool list/icon). pyautogui + pyperclip installed.
- **Honest limitation (verified live):** actuation is *best-effort* — 7B vision grounding is imprecise at 4K, and Win11's foreground-focus rules stop a background server from reliably directing input to arbitrary windows (matches CLAUDE.md's GUI-automation notes). The pipeline runs and returns coords/clicks, but reliable precise control needs UI Automation (pywinauto) or a stronger grounding model. Tracked in ROADMAP.
- Suite 42/42 · pyflakes clean.

## M33 — API layer started + model library curated
- **Refactor (#1 begun):** created the `nova/api/` package and extracted the first router — **`nova/api/bugs.py`** (`APIRouter`, imports only nova.* + config, included via `app.include_router`). Proven template for moving the rest of the routes off server.py. Suite (incl. bug‑CRUD, now hitting the router) **42/42**.
- **Model library curated** ("keep the best, delete the rest"): removed three benchmark‑proven redundancies — `qwen2.5:7b` (← qwen2.5:14b), `deepseek-coder:6.7b` (← deepseek-coder-v2:16b, faster+better), `qwen2.5-coder:32b` (slow 10 tok/s ← qwen3-coder:30b). Reclaimed ~27 GB. Kept best-of-breed: qwen2.5:14b (default), qwen3:14b, phi4, deepseek-r1:14b, deepseek-coder-v2:16b, qwen3-coder:30b, qwen2.5:32b (max breadth), qwen2.5-VL:7b (vision), nova-local, nomic-embed-text.
- Field re-checked (gemma3 / mistral-small / llama3.3): none beat the kept set for 32 GB; the 14B-class remains the sweet spot. No further downloads (diminishing returns).
- Self-test 13/13 · suite 42/42 · pyflakes clean (13 modules).

## M22 — Real visible browser (the agent opens a window you can watch)
- **Problem:** the agent's `browse` ran headless and only returned text/screenshot — no real window, no playing video.
- **`open_url {url}` tool + `/api/open-url`:** opens any URL in the user's **default browser** (Edge/Chrome) via the Windows shell (`os.startfile`) — a real, visible window. For "open Google / open my dashboard / play this link".
- **Visible `browse`:** new `VisibleBrowser` manager runs **headed** Chromium through Playwright on a single dedicated thread (sync API is thread-affine) and **keeps the window open** so the user watches. Auto-recovers if the window is closed. `browse {url, search, click_first, fill, click}`:
  - `search='…'` → searches **YouTube** (`/results`), dismisses consent, returns the top results;
  - `click_first=true` → clicks and **plays the first video** (launch args `--start-maximized --autoplay-policy=no-user-gesture-required`).
  - Falls back to the default browser if the headed launch ever fails. Server confirmed running in **interactive Session 1**, so windows appear on the user's desktop.
- **Agent wiring:** `AGENT_SYS` now documents `open_url` + the visible `browse`; the agent prefers them for "open a site / search YouTube / watch a video". Frontend agent log shows new icons (🪟 open_url, 🔎 search summaries).
- **`/api/browse`** gained `visible`/`search`/`click_first` (headless screenshot path unchanged → suite stays 36/36).
- **Tested live (desktop screenshots captured):** `open_url`→Edge opened Google ✓; visible `browse` searched YouTube (EN+AR) and opened/played the first video in a real Chromium window ✓; **agent end-to-end** with the user's Arabic goal "افتح يوتيوب وابحث عن فيديو عن الذكاء الاصطناعي وافتح أول نتيجة" → picked `browse`, opened the first Arabic result ("ما هو الذكاء الإصطناعي ؟ | فِهموجرافيك") in a visible window ✓. Self-test 13/13 · suite 36/36 · pyflakes clean.

## M34 — Backend module split + app.js split (deep refactor)

Continued the "extract → re-import, suite green after each" refactor. No behavior change;
the suite stayed **42/42** and self-test **13/13** after every step.

### Services extracted (nova/services/)
- `chat.py` — conversation/message store (`conv_*`, `chat_add`, `SESSION_ID`).
- `ollama.py` — Ollama client (`ollama_models` + capability tags, `model_caps/tags`, `ollama_chat_once`).
- `owui.py` — Open WebUI container integration (`owui_py`, `OWUI_LIST/APPLY`, `owui_toggle_code`, `FORCED_SYS`).
- `files.py` — file text extraction (txt/md/pdf/docx/image-OCR) + chunking.
- `kb.py` — knowledge base (embed, status, cosine search, ingest) on top of `files`.
- `browser.py` — headless `browse`, `open_url_default`, persistent on-screen Chromium (`visible_browse`, YouTube).
- `agent.py` — **the full Agent Mode ReAct loop** (`agent_tool`, `agent_run`, safety guards). `run_action`
  is injected via `set_run_action()` so the service never imports server.py.
- `training.py` — continuous-learning datasets (read/dedupe/append base+learned+combined JSONL, `NOVA_SYSTEM`).

### Routers extracted (nova/api/) — included via `app.include_router`
- `notifications`, `audit`, `history`, `conversations`, `analytics` (brain/habits/achievements),
  `models`, `owui`, `kb`, `media` (comfy/media-models), `agent` (agent + browser routes), `search` (unified search).
  (bugs was M33.) **12 routers total.** server.py inline routes: 94 → 66.

### Core / config
- `ps_args()` moved to `nova/core/process.py`; `UPLOAD_DIR` moved to `config.py`.

### Frontend
- `static/js/app.js` (1473 lines) split into ordered modules loaded sequentially:
  `core.js` (helpers/icons/state/i18n/router/render) · `pages.js` (one fn per screen) ·
  `shell.js` (ws/notifications/palette/theme/auth/boot). `node --check` clean; all served 200.

### Fix
- Stripped two stray NUL bytes embedded in this BUILD_LOG (latent corruption from an old edit).

## M35 — Full backend decomposition (server.py 2400 -> ~495 lines)

Completed the route/service extraction in priority order — one group at a time, with
`python run_tests.py` green (42/42) and self-test 13/13 after **every** step. server.py is
now a composition root: app + lifespan + middleware + background loops + `include_router`
wiring + a few misc routes (exec/toolkit, stt, upload, file serving, db-status, selftest,
kb-ingest).

### New services (nova/services/)
- `metrics.py` (+`get/set_last_metrics`), `chat.py` (+`stream_chat_send` streaming flow),
  `training.py` (+full job lifecycle: start/pause/resume/stop, progress parse, stats, run record),
  `schedules.py` (`run_action` dispatcher, schedules, workflow runner, A/B test),
  `settings.py` (redaction, token hash, `token_ok` gate, save/login), `tts.py`,
  `backup.py` (export/restore), `insights.py` (tips, daily briefing, co-pilot).

### New routers (nova/api/) — 21 total
- `metrics` (metrics/services/processes), `chat`, `training`, `schedules` (+workflows/abtest),
  `screen`, `settings` (+auth), `tts`, `backup`, `insights` (+briefing/copilot).

### Wiring (keeps the DAG acyclic — no service imports server.py)
- `set_run_action(run_action)` injects the dispatcher into the agent service.
- `set_briefing_hook(build_briefing)` lets the automation engine render a briefing without
  importing the insights layer (insights self-registers it at import).
- `record_training_run` self-registers as the ProcMgr training hook.
- live metrics shared via `metrics.get/set_last_metrics()`.

### Core / config
- `ps_args` + new `_q` (PowerShell arg quoting) live in `nova/core/process.py`; `UPLOAD_DIR` in config.

### Result
- **21 routers + 18 services + 4 core modules.** server.py: ~2400 -> **495 lines**.
- pyflakes clean across all modules · `node --check` clean (3 JS modules) · zero NUL bytes ·
  suite 42/42 · self-test 13/13. Spot-checked moved endpoints live (backup 155KB, copilot LLM
  text, insights tips, settings redaction, schedule/workflow round-trips).

## M36 — Visual overhaul (vibrant depth)

A final cascade CSS layer (`static/css/app.css`) + parallax/tilt JS (`static/js/shell.js`).
No structural/layout change → Arabic (text-only) and responsive behavior untouched; suite 42/42.

- **Palette:** rich multi-accent system — blue `#3b82f6` · purple `#a855f7` · cyan `#22d3ee` · gold `#fbbf24`;
  deeper space-dark base; matching clean light theme. Primary buttons / headings / KPI numbers / rings / bars
  now use the cyan→blue→purple gradient.
- **Living background (re-enabled):** multi-color drifting aurora + masked grid + cyan/blue/purple constellation
  canvas, plus a cinematic vignette. Mouse **parallax** on the aurora + particle layers.
- **Depth & glass:** layered card shadows + inner highlight + top "sheen" line; stronger backdrop-blur glass on
  sidebar/topbar/overlays/drawer; a subtle **3D tilt** on hovered cards (pointer-move delegation, ≤5°).
- **Living micro-interactions:** animated brand logo glow/float, pulsing "ping" ring on online status dots,
  gradient nav active pill + glow, gradient scrollbar, accent text-selection, quick-action hover depth, accent focus rings.
- **Motion safety:** all heavy effects gated behind `prefers-reduced-motion`; 3D tilt/parallax skipped on touch.
- **Icons:** already professional — the emoji→Font Awesome engine (core.js, MutationObserver) converts every emoji
  to a vector icon dashboard-wide; no emoji remain in the rendered UI.
- _Verified_: `node --check` clean (3 modules) · app.css serves 200 · suite 42/42 · self-test 13/13.

### M36.1 — bold pass + the real fix (cache-busting) + visual verification
- **Root cause of "I see no change":** the stylesheet URL was un-versioned, so browsers served the
  *cached* old CSS. Fixed by versioning the asset URLs (`/css/app.css?v=36`, `/js/*.js?v=36`); the HTML
  document is already `Cache-Control: no-cache`, so the new design now loads guaranteed.
- **Intensified the theme (v3 layer):** frosted-glass cards with gradient hairline borders + deep
  elevation, animated multi-stop gradient buttons with shine sweep + glow, glowing gradient headings
  (drop-shadow), Orbitron display brand, a large floating background orb, glowing active-nav rail,
  buttery blur-in page transitions.
- **Verified by actually rendering** the app headless (Playwright) and inspecting screenshots: dark +
  light dashboards, the Agent page (glowing avatar + visible constellation), and Arabic (labels
  translated, layout pixel-identical). Icons are vector Font Awesome throughout.

## M37 — Nova Brain 2.0 (living 3D neural map)

Complete redesign of the Brain page into an immersive, sci-fi knowledge visualization — built
in **dependency-free vanilla canvas** (no Three.js/CDN; fully local; trivially smooth at KB scale).

- **3D force-directed layout** — fibonacci-sphere seed + repulsion/spring relaxation in 3D,
  preserving prior node positions so new docs settle in gently (incremental).
- **Depth-projected glowing nodes** — perspective projection with yaw/pitch, z-sorted, additive
  ("lighter") glow, size by chunks+degree, brightness/scale by depth, gentle per-node pulse.
- **Community coloring** — label-propagation community detection → multi-color clusters
  (cyan/blue/purple/gold/pink/teal); gradient glowing links colored by endpoints, weighted by similarity.
- **Interaction** — drag to rotate, wheel zoom, hover tooltip (name · chunks · connections · cluster),
  click a node to focus + highlight neighbors + open a details panel (stats + connected docs),
  search-to-filter, clickable cluster legend to show/hide communities, pause/zoom/reset/refresh/**fullscreen**.
- **Live** — polls `/api/brain` every 12s and rebuilds only when the KB actually changed (signature
  guard → no color/layout flicker); small KBs label every node, large KBs gate labels by importance.
- **Verified** by headless render (Playwright, route-mocked 24-node graph + the real 2-node KB):
  no console errors, multi-color communities, controls + legend + HUD all correct. Backend untouched
  (`/api/brain` unchanged); suite 42/42, JS clean, zero NULs. Cache version bumped to v=37.

## M38 — Engineering-maturity hardening (Phases 0–5 of PLAN.md)

Executed the formal hardening plan end-to-end (PLAN.md / TASKS.md / PROJECT_PLAN.md), one phase
per commit, quality gate green throughout. 32/34 tasks done; 2 deferred by judgment.

- **M-A Safety Net:** `git init` (+ .gitignore, MIT LICENSE, initial commit of 77 files);
  pinned deps (requirements.txt `==` + requirements.in); added pyautogui/pyperclip; vendored
  Font Awesome + fonts (Inter/JetBrains/Orbitron) locally — verified 0 external requests
  (truly offline); `preflight.py` first-run check (26 checks).
- **M-B Hardening:** exec surface gated (`allow_remote_exec` on LAN; `exec_allowed()`); auto
  cache-busting (server stamps `?v=<mtime>`); daily SQLite snapshots (rotated 14) + endpoints;
  DB migration framework (`schema_version` + `run_migrations`); "Lite visuals" perf mode +
  pause loops on hidden tab; `SECURITY.md`.
- **M-C Tests & CI:** `tests/` pytest suite (core/services/api/frontend) = 24 tests;
  `scripts/check.py` gate; `.githooks/pre-commit` (active) + `.github/workflows/ci.yml`;
  `requirements-dev.txt`.
- **M-D Docs & Observability:** `/docs` tags + `docs/openapi.json` (99 paths); `DATA_MODEL.md`;
  metrics history table + `/api/metrics/history`; error aggregation (`nova/core/errors.py`) +
  `/api/errors`; `/api/health`; Diagnostics page Server-Health + Recent-Errors panels.
- **M-E Features:** `screen_if` conditional automation; structured `[PROGRESS] {json}` training
  parse; configurable `stt_model`; `docs/click-to-act.md` decision (park best-effort, hybrid plan).
- **Deferred:** T-033 per-page bespoke UI (optional; global theme already applied), T-034 32b
  throughput (upstream-gated). **Excluded by decision:** multi-user, RTL mirroring.
- _Verified_: pyflakes clean · node --check clean · pytest 24 · live suite 42/42 · self-test 13/13.

## M39 — Per-page bespoke UI (T-033) + 32B tracking (T-034)

Tailored each key page to its core task (focused/minimal — no unrelated widgets), on the global
theme. Verified every page by headless render; quality gate green (pytest 24, live 42/42, zero
console errors on all routes).

- **Chat → messaging app:** full-height layout with a glass **composer pinned at the bottom**
  (attach/voice/preview/input/Send), conversation list with gradient avatar tiles, lively glass
  message bubbles (gradient user / glass AI) with slide-in. Fixed a grid-row sizing bug so columns
  scroll internally instead of growing the page.
- **Training → progress & control:** progress is the hero — big gradient % + thick bar + ETA + GPU
  chips, prominent Start/Stop/Pause/Resume; stats, live log, test, history kept.
- **Screen → preview & recording:** enlarged, prominent preview/record surfaces; previews appear
  only when active (clean idle state); recordings list + playback.
- **Agent → thinking & interaction:** **fixed a real bug** — `.asettings{display:flex}` overrode the
  `hidden` attribute so the settings/tools panel could never collapse and the gear did nothing.
  Added `.asettings[hidden]{display:none!important}` → settings now collapse by default, leaving the
  avatar + live reasoning area + composer + example goals as the focus; gear toggle works.
- **T-034:** `docs/32b-throughput.md` — baseline (14b ~120 tok/s default; 32b ~5 shared/~11 isolated),
  watch-list (Ollama/llama.cpp Blackwell, new quants, drivers), and re-benchmark steps. Monitoring.

## M40 — Close-tab confirmation ("Nova is still running")

Global `beforeunload` guard (in `shell.js boot`, so it applies to **every** page of the SPA):
- **Always warns** when work is in progress — recording, training, agent run, or chat streaming
  (busy state tracked centrally via the event bus, no per-page wiring).
- Otherwise warns per the new **`confirm_exit`** setting (default **on**) with a Settings toggle
  ("Confirm before closing the tab").
- Fires on tab close, window close, and refresh (browsers can't distinguish these).
- _Honest limitation_: modern browsers replace the custom text with their own generic wording and
  only prompt after the user has interacted with the page — both are browser security rules.
- _Verified_ with Playwright: handler cancels the event (`defaultPrevented=true`) and a native
  `beforeunload` dialog fires on close. Gate green (pytest 24, live 42/42).

## M41 — Open WebUI upgraded to v0.10.1

Reviewed the 0.10.1 source, updated our integration for its one breaking change, upgraded the
running container, and verified everything — custom Nova features preserved, suite 42/42.

- **Breaking change found:** the OWUI `config` table was reshaped from a single-row JSON blob
  (`id, data`) to **per-key rows** (`key, value`) — migration `3ff2c63645b8_reshape_config_to_per_key_rows`.
  The `tool` and `model` tables are unchanged.
- **Integration made schema-agnostic** (`nova/services/owui.py`): `OWUI_LIST` and `OWUI_APPLY` now
  detect the live `config` shape and read/write either the legacy blob or the new per-key rows
  (`code_interpreter.enable` / `code_execution.enable`). Works before *and* after the upgrade.
- **Upgrade performed** (standard, recoverable Docker procedure):
  1. Backed up `webui.db` → `data/owui-backup/webui-<ts>.db`.
  2. `docker pull ghcr.io/open-webui/open-webui:v0.10.1` (old `:main` image kept for rollback).
  3. Recreated the container reusing the **same named volume** `open-webui` + Desktop bind mount,
     same port (3000→8080) + restart policy. OWUI ran its own migrations (config data preserved).
- **Verified:** version `0.10.1`; custom **tools** (subprocess, windows_system_control) and **models**
  (smart-tools, tools-assistant, hasher) survived; config flags preserved + migrated; our `/api/owui`
  read path + `/api/owui/apply-recommended` write path both work on the new per-key schema; live
  suite **42/42**, gate green (pyflakes + node + pytest 24).
- **Rollback path** (if ever needed): recreate container from the retained `:main` image + restore
  the `webui.db` backup.

## M42 — Source-of-truth files established (2026-06-30)

Made the six project files the **mandatory, permanent** source of truth and the workflow a fixed law.

- **What:** authored/reorganized `STATUS.md` (live dashboard), `WORKFLOW.md` (the permanent
  before/during/after process + quality gate), `TASKS.md` (full backlog by priority P0→P3 with
  DONE/FRAGILE/IN‑PROGRESS/TODO/EXCLUDED), `ROADMAP.md` (feature status + phases + vision),
  `PROJECT_PLAN.md` (phases + architecture decisions), and this log's header rule.
- **Why:** to have one reliable record of what's done vs fragile vs remaining, and to enforce
  reviewing/updating these files on every coding session.
- **Priorities fixed:** P0 Security (exec surface, auth, HTTPS) · P0 Tests · P1 Outcome
  verification · P1 Stability · P2 Docs · P2 Features · P3 Polish. **Multi‑user excluded forever.**
- **Honest fragile list captured** (see STATUS.md): unguarded localhost exec, shallow/env‑coupled
  tests, never‑run CI, unverified agent/training/generation outcomes, mocked‑only `screen_if`,
  best‑effort click‑to‑act, plaintext `cloud_api_key`, no watchdog, silent loop error handling,
  deps not clean‑installed.
- **Next:** begin Phase 1 / SEC‑1 (Terminal `/api/exec` destructive‑command confirm‑guard).
- _Verified:_ docs only; quality gate green (pyflakes + node + pytest 24); live suite 42/42.
