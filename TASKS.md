# TASKS — Nova / AI Control Center

Single source of truth for actionable work. Ordered by priority (**P0 highest → P3**).
Update on every session (see `WORKFLOW.md`). Personal system — **no multi‑user, ever (🚫)**.

**Status:** ✅ DONE · 🟧 FRAGILE (works, known issue) · 🟦 IN PROGRESS · ⬜ TODO · 🚫 EXCLUDED

---

## P0 — Security (command‑execution surface · auth · HTTPS)

| ID | Task | Status | Notes / issue |
|---|---|---|---|
| SEC‑1 | Terminal `/api/exec` destructive‑command **confirm‑guard** (block clearly‑destructive cmds unless `confirm:true`) | ✅ | M43. 409 `needs_confirm` for destructive cmds; `execCommand()` asks before resending; audited (`needs_confirm`/`forced`); unit + live tested. |
| SEC‑2 | Centralize + strengthen the destructive‑command denylist (shared by agent + terminal) | ✅ | M44. New `nova/core/safety.py` — regex + command‑boundary aware (catches piped deletes/aliases/flag variants; avoids FPs like `echo "format…"`, `format-table`). Shared by Terminal + agent; 24 unit tests. |
| SEC‑3 | Tighten HTTP security headers (CSP `default-src 'self'`, `frame-ancestors 'self'`, Permissions‑Policy) | ✅ | M45. Strict CSP (local‑only, `object-src 'none'`, `frame-ancestors 'self'`), `X-Frame-Options`, `Permissions-Policy` (mic=self). Verified: all 11 routes render with zero console/CSP errors + header test. |
| SEC‑4 | Encrypt `cloud_api_key` at rest (use existing `cryptography` dep; key from machine‑local secret) | ✅ | M46. `nova/core/secretbox.py` (Fernet; key in git‑ignored `<data>/.nova_key`, not in DB). Encrypt‑on‑save (`enc:…`), transparent decrypt via `get_cloud_api_key()`; legacy plaintext still readable. 4 tests. |
| SEC‑5 | One‑command HTTPS enablement + doc (`https_enabled` + cert) | ✅ | M47. `scripts/https.py enable|disable` flips config + pre‑generates the self‑signed cert; documented in SECURITY.md. Round‑trip verified. |
| SEC‑6 | Security review pass of every `subprocess`/exec call site | ✅ | M48. `docs/exec-audit.md` — no `shell=True`, all argv‑form. **Fixed** a real injection: `screen.py` OCR `lang` was interpolated unquoted into a `-Command` (LAN bypass of the exec gate) → now allowlisted (`_valid_lang`, tested). |
| SEC‑E | Exec **LAN gate** (`allow_remote_exec`) + audit + `exec_allowed()` | ✅ | M‑B. Localhost always allowed by design; LAN requires opt‑in. |
| SEC‑E2 | Hashed auth tokens · rate limiting · security headers (baseline) · audit log | ✅ | M26/M‑B. |

## P0 — Real test coverage (unit + integration + smoke)

| ID | Task | Status | Notes / issue |
|---|---|---|---|
| TST‑1 | Deepen **unit tests** per service (real assertions, not "returns 200") | ✅ | M49. `tests/test_services_deep.py` — 10 tests with real assertions: audit, notifications+category, metrics history, chat conv_touch/count, run_schedule DB update, run_action webhook/kb branches (mocked), backup↔restore round-trip, ollama_models (mocked), learning_stats (mocked), files.extract_text. |
| TST‑2 | **Hermetic test mode** — mock Ollama/ComfyUI so tests don't need them running | ✅ | M50. `conftest.py` autouse `_no_network` fixture blocks real outbound HTTP at the one chokepoint (`urllib.request.urlopen`); `http_ok`→False, `http_json` raises so callers degrade; service‑level tests mock above it. Full pytest suite (63) passes with **network fully blocked** — no Ollama/ComfyUI required. (Live `run_tests.py` is still environment‑coupled by design — it tests the running stack.) |
| TST‑3 | Agent‑loop integration tests with a mocked model (tool dispatch, JSON parse, stop) | ✅ | M51. `tests/test_agent_loop.py` — 9 tests driving `agent_run` with a scripted `ollama_chat_once`: parse_action (nested/garbage), tool dispatch→observation→final, reformat recovery on non‑JSON, step‑budget termination, mid‑run Stop (no dispatch), tool gating, `ask` path, + `agent_tool` destructive‑command block & confined‑write block. No model/network/side effects. |
| TST‑4 | Clean‑venv install test — prove pinned `requirements.txt` installs together | ✅ | M52. `scripts/ci_local.py` builds a fresh venv and installs `requirements.txt`+`requirements-dev.txt`. **Proven 2026‑06‑30:** all pins resolved to cp312 win_amd64 **wheels — no source builds, no conflicts**; gate passed inside the clean venv. Caveat: only *direct* deps are pinned (transitive deps install at latest‑compatible). |
| TST‑5 | Make CI actually run (local `act` or a Git remote) | ✅ | M52. `scripts/ci_local.py` runs the **exact workflow steps** (clean‑venv install → `scripts/check.py`) on this machine → **LOCAL CI PASSED**. `act` can't emulate the `windows-latest` runner, so GitHub‑hosted execution still needs a remote (documented in the script). The CI *commands* are now verified to pass on a clean environment. |
| TST‑6 | Frontend interaction tests (beyond the load/zero‑console gate) | ✅ | M53. `tests/test_frontend.py` +4 live Playwright interaction tests: nav‑click routing (title/active/hash/body), deep‑link routing (`#/brain`), theme toggle (light↔dark, reversible), command palette (Ctrl+K → filter → Escape). Auto‑skip without a server (like the load gate). |
| TST‑E | pytest suite (24) + live suite (42) + Playwright load gate + pre‑commit hook | ✅ | M‑C. Foundation; shallow — see TST‑1. |

## P1 — Outcome verification (does it actually work?)

| ID | Task | Status | Notes / issue |
|---|---|---|---|
| OUT‑1 | **Agent goal battery** — run fixed goals, measure real success rate, record baseline | ✅ | M54. `scripts/agent_eval.py` runs 5 safe verifiable goals through the real loop + model; baseline in `docs/agent-baseline.md`. **First run 2/5 exposed a real bug** (relative `write_file` paths nested a doubled `agent-output/`; `read_file` resolved against CWD → agent couldn't read back what it wrote). Fixed (`_strip_output_prefix` + `resolve_read_path`, regression‑tested) → **5/5 with qwen2.5:14b**. |
| OUT‑2 | Verify **training** produces a usable nova‑local end‑to‑end | 🟧 | External scripts in `C:\AI\training`; only log‑parsing verified. |
| OUT‑3 | Verify **image/video generation** actually succeeds (not just job‑starts) | ✅ | M67. `scripts/gen_eval.py` triggers a real generation via the live API + ComfyUI and validates the PNG. **Verified:** SDXL produced a correct 1024×1024 image ("red apple on a white table") in **9.1s** — visually confirmed. `docs/generation-baseline.md`. (Video/LTX uses the same path — slower; verify manually.) |
| OUT‑4 | `screen_if` real‑screen matching test (OCR/vision against live content) | 🟧 | Unit‑tested with a **mocked** screen only. |
| OUT‑5 | RAG retrieval quality check (relevance of citations) | ✅ | M58. `scripts/rag_eval.py` seeds an isolated KB with single‑topic docs and checks each paraphrased query retrieves the right one. Baseline `docs/rag-baseline.md`: **precision@1 = 5/5 (100%), MRR = 1.0** (nomic‑embed‑text). |

## P1 — Stability (watchdog · error recovery · graceful shutdown)

| ID | Task | Status | Notes / issue |
|---|---|---|---|
| STB‑1 | **Watchdog/supervisor** to auto‑restart `server.py` on crash | ✅ | M55. Hardened `watchdog.ps1`: **fixed the python‑stub bug** (old `(Get-Command python).Source` resolved to the WindowsApps stub → every restart silently failed) via `Resolve-Python`; added timestamped `watchdog.log`, N‑consecutive‑fail threshold, post‑restart re‑probe, and a `-Once` self‑check. Verified: `-Once` resolves the real Python312 + detects the live server. |
| STB‑2 | Persist/resume training & recording across server restart | 🟧 | M66. Jobs are now **persisted** to a `jobs` table (start + finish); on startup `reconcile_interrupted()` marks any left `running/starting/paused` as **`interrupted`** and notifies the user — so a killed training/recording no longer vanishes silently. **True auto‑resume of a killed OS process is not done** (not feasible — the Job Object terminates children); this surfaces it instead. Test `test_reconcile_interrupted_jobs`. |
| STB‑3 | Error recovery + surfacing in background loops (no silent `except: pass`) | ✅ | M56. `metrics_loop`/`status_loop`/`scheduler_loop` now `record_error(...)` (deduped, bounded — won't flood) so failures appear in `/api/errors` + Diagnostics instead of vanishing; `backup_loop` also records; shutdown finalizers `log.warning` instead of `pass`. Loops still don't crash (recover next tick). |
| STB‑4 | Back up generated media/uploads (only the DB is snapshotted today) | ✅ | M59. `backup_media()` incremental mirror of `UPLOAD_DIR` → `data/backups/media` (copies new/changed by size; deleted‑source files survive). Wired into `backup_loop`; manual `/api/backup/snapshot` now also mirrors media. Test `test_backup_media_mirror`. |
| STB‑5 | SQLite WAL mode + concurrency review | ✅ | M57. `db()` now opens with `timeout=5s` + `PRAGMA busy_timeout=5000` + `synchronous=NORMAL`; `init_db` sets persistent `journal_mode=WAL` (readers no longer block the writer; fewer "database is locked" under the concurrent loops). Backup uses the online `src.backup()` API → WAL‑safe. WAL sidecars git‑ignored. Test: `test_db_wal_and_busy_timeout`. |
| STB‑E | Daily DB snapshots (rotate 14) + migration framework + `/api/health` + error aggregation | ✅ | M‑B/M‑D. |

## P1 — Perception & Control (PC · owner request, Phase 8)

The system should **read & understand** anything on screen / in files, have **perfect awareness** of the
window layout, and **precisely control** mouse + keyboard. Built on Windows APIs (ctypes, pygetwindow,
pyautogui) + UI Automation (pywinauto/uiautomation) + the existing OCR/VLM. Exposed three ways: **agent
tools**, **chat commands** ("read this", "where am I?", "move mouse to 500,300"), and **API endpoints**.

| ID | Task | Status | Notes |
|---|---|---|---|
| PC‑1 | **Read & Understand** — OCR + VLM for files/images/screenshots/screen; text + what it shows + purpose + details | ✅ | M68. `nova/services/understand.py` (`understand`/`understand_image`/`understand_file`) reusing `extract_text` + `screen.vlm_image`; `POST /api/understand`; agent tool `understand {path}`; **image chat uploads auto‑enriched** with VLM description + OCR (so "read/describe this" works). Verified live on a generated image. |
| PC‑2 | **Window & screen awareness** — active window (title/process/rect), all visible windows, screen resolution + DPI, precise measurements | ✅ | M69. `control.active_window/list_windows/screen_info/awareness` via ctypes Win32 + psutil; **per‑monitor DPI‑aware** (reports true 3840×2160 @144dpi vs non‑aware 2560×1440). `GET /api/control/{active,windows,screen,awareness}`. |
| PC‑3 | **Element detection** — find UI elements by name/text/partial match | ✅ | M69. `control.find_element` via **`uiautomation`** (UIA tree walk); returns name, type, bounding rect + click center. `POST /api/control/find`. `click_element(name)` finds + clicks. |
| PC‑4 | **Precise mouse control** — move to exact X/Y, click, double/right‑click, drag, scroll | ✅ | M69. `control.move_mouse/click/drag/scroll` (pyautogui, DPI‑aware coords). `POST /api/control/mouse`. Verified safely (no‑op move). |
| PC‑5 | **Precise keyboard control** — key presses with modifiers, accurate text typing | ✅ | M69. `control.press_keys` ('ctrl+s' / lists) + `type_text` (clipboard‑paste, Unicode/Arabic). `POST /api/control/key`. |
| PC‑6 | **Surfaces + tests** — agent tools, chat commands, API endpoints, hermetic tests | ✅ | M69. Agent tools `screen_awareness`/`find_element`/`control`; **chat commands** ("where am i", "list windows", "move mouse to X,Y", "click X,Y", "click the Save button", "read/describe this"); `/api/control/*`; 3 tests. "where am i" render‑verified live. |

**Rollup:** **PC COMPLETE ✅** (M68 PC‑1 + M69 PC‑2…6). New dep `uiautomation` (pinned + in requirements.in).
Mutating control is gated by `exec_allowed()` (localhost ok; LAN needs opt‑in) and audited. Full spec:
`docs/perception-control.md`.

## P1 — AI Screen Vision (Phase 7 · NEW core feature)

Real‑time perception + control: the AI sees exactly what the user sees and can act on it. Builds on
the existing Screen Studio service (`nova/services/screen.py`: `capture_screenshot`, `read_screen`,
`describe_screen`, `act_on_screen`, `RECORDER`) — extend, don't duplicate. **Privacy‑first:** every
capture/track path is opt‑in, local‑only, pausable, and non‑persistent by default.

| ID | Task | Status | Notes / design |
|---|---|---|---|
| SV‑1 | **Live screen stream** to the dashboard — throttled frames (JPEG over WS or MJPEG endpoint), adjustable FPS/quality, start/stop | ✅ | M61 backend + M63 UI. `GET /api/vision/stream` MJPEG (`mss`→pillow downscale+JPEG, re‑reads FPS/quality each tick); the **Live page** (`#/live`) renders it in an `<img>` with an FPS slider; navigating away stops the stream (router cleanup). |
| SV‑2 | **Continuous AI vision loop** — periodically feed frames to qwen2.5‑VL and stream a running description; on‑demand "what's on my screen now?" | 🟧 | M61/M63: **on‑demand** "Describe what's on screen" done (`POST /api/vision/describe` → VLM, rendered on the Live page). Automatic continuous narration loop is optional/deferred (VLM cost) — on‑demand covers the need. |
| SV‑3 | **Mouse tracking** — global cursor position + click events, streamed to the UI + exposed to the agent | ✅ | M61 backend + M63 UI. `GET /api/vision/mouse` (`ctypes GetCursorPos`, gated on `track_mouse`); Live page polls it (200ms) and overlays a glowing cursor marker on the stream. (Click events deferred — position covers the core need.) |
| SV‑4 | **Keyboard tracking** (opt‑in, privacy‑gated) — keystroke / active‑window context for the AI | 🟧 | M61: implemented the **privacy‑light** form — `GET /api/vision/context` returns the focused‑window title (`track_keyboard` gate). Full keystroke capture intentionally deferred (needs `pynput`; high privacy risk) — documented decision. |
| SV‑5 | **Unified live session** — one view fusing live screen + input + AI vision, wired to `act_on_screen` so the AI can interact with what it sees | ✅ | M63. New **"AI Screen Vision" (`#/live`)** page: live stream + mouse overlay + focused‑window context + on‑demand describe + all privacy toggles + FPS slider, in one view. Render‑verified (nav item, toggles default‑off, zero console errors). The agent already has `act_on_screen` for control; this page is the human‑facing live session. |
| SV‑6 | **Privacy & safety controls** — master opt‑in, per‑capability toggles, pause/redact, status indicator, zero‑persistence default | ✅ | M61. Settings `screen_vision_enabled`/`vision_fps`/`vision_max_width`/`vision_quality`/`track_mouse`/`track_keyboard` (all OFF/safe by default); every route 403s unless its gate is on; stream/describe audited; nothing persisted. |
| SV‑7 | **Tests + outcome verification** — stream lifecycle, throttling, privacy gates default‑off, tracking accuracy | ✅ | M61 backend (6 tests: JPEG grab, gates default‑off, frame when enabled, mouse/keyboard gates) + M63 render‑verified the Live page (nav, toggles off by default, describe button, zero console errors). |

**Rollup:** **largely shipped (M61 backend + M63 UI).** SV‑1 ✅ stream · SV‑3 ✅ mouse · SV‑5 ✅ Live
page · SV‑6 ✅ privacy · SV‑7 ✅ tests · SV‑2 🟧 on‑demand describe (continuous loop optional) · SV‑4 🟧
focused‑window context (full keystroke capture deferred by privacy decision). Optional follow‑ups:
auto‑narration loop, click‑event capture, wire the Live page directly to `act_on_screen`.

## P2 — Documentation (keep the six files current)

| ID | Task | Status | Notes |
|---|---|---|---|
| DOC‑1 | Update the six source‑of‑truth files **every** session | 🟦 | Permanent rule (`WORKFLOW.md`). |
| DOC‑2 | Refresh `README.md` / `SETUP.md` for current state | ✅ | M65. README highlights updated: chat DeepThink/Web Search/⏹ mic, and the new **AI Screen Vision (Live)** entry, with doc links. |
| DOC‑3 | Document (or vendor) the external training pipeline | ✅ | M65. `docs/training-pipeline.md` — full map of `C:\AI\training` (learn.ps1/run_all.ps1/train_lora.py/harvest_chats.py/Modelfile), data flow, how the Control Center integrates, requirements, and the OUT‑2 verification boundary. |
| DOC‑E | `ARCHITECTURE.md`, `DATA_MODEL.md`, `SECURITY.md`, `docs/*`, OpenAPI export | ✅ | M‑D. |

## P1 — Chat interface improvements (CHAT · owner request)

Core chat UX, requested 2026‑06‑30. Toggle buttons styled like the existing RAG/compare toggles.
**Full spec:** `docs/chat-deepthink-websearch.md` (what/why/how + implementation + deps).

| ID | Task | Status | Notes |
|---|---|---|---|
| CHAT‑1 | **DeepThink toggle** — reason step by step before answering | ✅ | M62 (chat) + **M72 (agent)**. Chat `#dtbtn`; **Agent `#adeep` toggle** → `agent_run(deepthink=True)` adds a reasoning directive to the agent system prompt. Both render‑verified. Test `test_agent_deepthink_in_prompt`. |
| CHAT‑2 | **Web Search toggle** — answer with live web results | ✅ | M62 (chat) + **M72 (agent)**. Chat `#wsbtn`; **Agent `#aweb` toggle + `web_search` tool** (`nova/services/web_search.py`, `ddgs`). Both surfaces + the agent grid. Tests `test_web_search_mocked`, `test_agent_web_search_tool`. |
| CHAT‑3 | **Microphone stop control** — end voice input manually | ✅ | M62. Mic button now swaps to **"⏹ Stop"** (red pulse) while recording and reverts to 🎤 — explicit, obvious stop (the toggle existed but the affordance was unclear). Applies to chat + agent mics via `_micUI`. |

## P2 — Feature improvements

| ID | Task | Status | Notes / issue |
|---|---|---|---|
| FEA‑1 | Click‑to‑act reliability (UI Automation / pywinauto + focus) | ✅ | M70. `act_on_screen` now tries **precise UI‑Automation element detection first** (exact pixel center via `control.find_element`, reduced from natural instructions by `_core_term`) and only falls back to vision grounding when there's no UIA name. Returns `via:"uia"|"vision"`. Much more reliable on real apps. |
| FEA‑2 | STT Arabic/noisy accuracy (larger Whisper default / tuning) | ✅ | M73. `get_whisper` now loads on **CUDA/float16 (RTX 5090)** with CPU/int8 fallback — far faster, so larger models are practical; default bumped `base`→`small` (much better Arabic). GPU path verified (tiny loaded on cuda). Users can pick up to `large-v3` in Settings. |
| FEA‑3 | Voice improvements (input UX, TTS voices) | ⬜ | |
| FEA‑4 | Conditional screen actions UX in Automation page (expose `screen_if`) | ⬜ | Backend done (M39); no dedicated UI. |
| FEA‑E | `screen_if` action · bespoke pages · Nova Brain 2.0 · OWUI 0.10.1 | ✅ | M37/M39/M41. |

## P3 — Polish (UI · performance · optimization)

| ID | Task | Status | Notes |
|---|---|---|---|
| POL‑1 | Performance budget for the animated background (measure FPS; auto‑lite on weak GPUs) | ⬜ | "Lite visuals" toggle exists. |
| POL‑2 | Accessibility pass (ARIA, keyboard nav, contrast) | 🟧 | M71. Skip‑to‑content link, `role`/`aria-label` on nav + main, `aria-live="polite"` toasts (screen‑reader announcements), and `:focus-visible` keyboard outlines. Icon buttons already carry `title`s. Not a full WCAG audit (single‑user tool) but the core keyboard/SR gaps are closed. |
| POL‑3 | Mobile testing on real devices | ⬜ | Responsive CSS untested on hardware. |
| POL‑4 | 32B throughput re‑benchmark on Ollama/llama.cpp updates | 🟧 | `docs/32b-throughput.md` (monitoring). |

## 🚫 Excluded (owner decision — do not build)
- Multi‑user / accounts / roles / RBAC.
- RTL mirroring (Arabic stays text‑only, fixed layout).
- Cloud hosting / horizontal scaling.

---

### Rollup
- **P0 Security: COMPLETE ✅** · **P0 Tests: COMPLETE ✅** · P1 Outcome (OUT‑1 ✅; 4 open) · P1 Stability (STB‑1 ✅ STB‑3 ✅ STB‑5 ✅; 2 open).
- **Next:** OUT‑5 (RAG quality) → STB‑2 (jobs survive restart) → STB‑4 (media backup).
- **Pending restart:** M54 (agent path fix) + M56 (loop error surfacing) + M57 (WAL) activate on the next `server.py` restart.
- **Completed foundation:** see `BUILD_LOG.md` milestones M28–M41 (modular backend, hardening,
  bespoke UI, Nova Brain, OWUI 0.10.1).
