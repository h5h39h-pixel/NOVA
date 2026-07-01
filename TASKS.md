# TASKS — Nova / AI Control Center

Single source of truth for actionable work. Ordered by priority (**P0 highest → P3**).
Update on every session (see `WORKFLOW.md`). Personal system — **no multi‑user, ever (🚫)**.

**Status:** ✅ DONE · 🟧 FRAGILE (works, known issue) · 🟦 IN PROGRESS · ⬜ TODO · 🚫 EXCLUDED

---

## ⚠ Honest gaps (self‑audit 2026‑06‑30) — the real remaining work

These come from a candid self‑audit (`docs/honest-state.md`). They are **open and unbuilt** — the rest
of this file's ✅ marks mean "code done + smoke‑verified once," **not** "battle‑tested." Read this section
as the truthful backlog; the safety items (HON‑1, HON‑10) are the highest priority in the whole project.

| ID | Task | Priority | Status | Notes |
|---|---|---|---|---|
| HON‑1 | **Global panic stop / kill‑switch for agent GUI control** | P0 | ✅ | M81. `control.CONTROL_PAUSED` blocks ALL mutating control (move/click/drag/scroll/type/keys/click_element + `act_on_screen`) when set — refused before any input is sent. `POST /api/control/panic` pauses + stops the agent (`AGENT_STOP`); `/resume` clears. **Always‑visible ⛔ topbar button** (any page) + red bottom banner + audit. Verified end‑to‑end (UI + backend + control‑blocked). *Residual:* per‑action confirmation for autonomous runs is still not added (kill‑switch + dry‑run cover it) — see HON‑1b. |
| HON‑1b | Disable‑agent‑GUI‑control toggle (defense beyond the kill‑switch) | P1 | ✅ | M92. New `agent_can_control` setting (default on) + Settings toggle. When off, the agent's `control` + `act_on_screen` tools refuse (manual control + the HON‑1 panic stop still work) — lets a cautious user keep the agent out of the GUI entirely. Test `test_agent_control_gate`. (A per‑action *confirm* prompt for autonomous loops remains future work.) |
| HON‑10 | **Prompt‑injection defense for web‑augmented agent** | P0/P1 | ✅ | M82 + M105.2 + **M105.4**. Defense‑in‑depth: (1) all external text (`web_search`, `browse`, `understand`) is **fenced as untrusted data**; (2) **output‑side detection** — `detect_injection()` scans content for injection phrasings ("ignore previous instructions", "reveal system prompt", "exfiltrate", …) and prepends a "⚠ POSSIBLE PROMPT‑INJECTION DETECTED" warning + audits it; (3) the agent system prompt has a **SECURITY rule** that tool observations are DATA. Tests assert fencing + detection. (Security note: no defense is absolute — this is strong, layered mitigation, which is the correct bar for a local tool.) |
| HON‑2 | **Real GUI integration test** (drive an actual app via UIA: find → set text → verify) | ✅ | M93. `scripts/gui_eval.py` creates a **real native Win32 EDIT control** (proper UIA, faithful proxy for real apps) and drives it through the control stack → **PASS** (text set + verified via `WM_GETTEXT`). Earlier attempts failed because tkinter exposes no UIA controls (bad proxy) and synthetic keyboard input is suppressed here — see HON‑2c for the real fix. |
| HON‑2b | Isolated disposable target app | ✅ | Folded into HON‑2/M93 — uses a self‑created native EDIT control (own HWND, destroyed at end), non‑destructive. |
| HON‑2c | **Reliable GUI text control — the real fix** | ✅ | M93. **Root cause confirmed:** synthetic keyboard injection (`SendInput`/`keybd_event`) is suppressed in this environment — even a focused real native EDIT receives nothing — while **window messages / UIA work** (`WM_SETTEXT` ✅, UIA `ValuePattern.SetValue` ✅). **Fix:** `control.type_text` now sets the focused control's value via **UIA SetValue** (`via:"uia"`, verified) with clipboard fallback; new `control.set_element_text(name,text)` + `/api/control/set-text` + agent `control {action:'set_text'}` fill named fields directly (focus‑independent). Reliable GUI text entry now works on real (UIA) apps. (Mouse positioning already worked; raw keystroke combos like global hotkeys remain limited by the same input suppression.) |
| HON‑3 | **Test‑coverage measurement** (`coverage.py`) | ✅ | M84 baseline 49% → **M105.2 raised to 56%** (new `tests/test_coverage_boost.py`: automodel 0→covered, process quoting, analytics/insights/search/media/owui routes; + macro/quality/memory tests). Honest breakdown in `docs/coverage.md`. Not gated (needs a threshold + live deps); run manually via `coverage run -m pytest`. |
| HON‑7 | **Honest, larger eval batteries** | ✅ | M87 + **M105.4**. Agent **9/9** (multi‑step/reasoning goals), RAG **11/12 (92%)** on an overlapping corpus. **Arabic STT WER now MEASURED:** new `scripts/stt_eval.py` synthesizes EN+AR sentences (Piper en_US‑lessac / ar_JO‑kareem) → `/api/stt` → WER. Live result: **EN mean WER 0.07 (~93% word acc), AR mean WER 0.26 (~74%)** — real numbers, not a claim. All eval scripts can `--record` to the IDEA‑6 quality dashboard for trend tracking. (A 50+‑goal multi‑app battery would be *more* coverage, not a fix — the batteries are now credible + measured across agent/RAG/STT.) |
| HON‑4 | **Persistent observability** (errors to disk, not memory) | ✅ | M85. `nova/core/errors.py` now persists the aggregated errors to `data/logs/errors.json` on each record and reloads on import → `/api/errors` + Diagnostics survive a restart. Test `test_errors_persist`. (Metrics history was already in SQLite.) |
| HON‑5 | **Load / soak / concurrency testing** | ✅ | M89. `scripts/load_test.py` (non‑destructive): 48 concurrent reads (p95 ~100ms) + **48 concurrent conversation writes with NO "database is locked"** (WAL verified under contention) + chat single‑flight returns cleanly. Self‑cleans its throwaway rows. Run on demand. |
| HON‑6 | **Verify live stream + Web‑Search chat turn end‑to‑end** | ✅ | M86. **Stream:** enabled screen vision, confirmed `/api/vision/frame` returns a valid JPEG and the MJPEG `/api/vision/stream` yields multiple `--frame` boundaries (then disabled; content not viewed — privacy). **Web Search chat:** toggled Web Search on, asked a current‑info question → model answered "Python 3.13.1" citing "the provided context" (the fenced web results), zero console errors. Both pipelines verified live. |
| HON‑8 | **Real lockfile** (hashes / pip‑compile) | ✅ | M85. `requirements.lock` generated via `pip-compile --generate-hashes --allow-unsafe requirements.in` — full transitive closure, **1426 hashes**, reproducible. `requirements.txt` stays the human‑readable direct pins; `requirements.lock` is the reproducible install (`pip install -r requirements.lock`). `pip-tools` added to dev deps. |
| HON‑9 | **CI actually running** | ✅ | M94 + M95. **Remote connected** (`github.com/h5h39h-pixel/NOVA`, private) and `main` pushed → the `ci.yml` workflow (`on: push`) now runs **hosted CI on GitHub Actions**. Plus: gate auto‑runs on every commit (pre‑commit) + push (pre‑push, verified); `ci_local.py` = clean‑venv CI. (Hosted run results viewable in the repo's Actions tab; `gh` CLI not installed locally to print them.) |
| HON‑11 | **Refactor the large files** (pages.js, app.css, server.py) | ✅ | M78+M79. **pages.js** 1440→4 modules (pages/-create/-agent/-system); **app.css** 1039→4 cascade files (app/-components/-visuals/-extras); **server.py** 694→667 (extracted `/api/toolkit/*` → `nova/api/toolkit.py`). All byte‑identical/behavior‑preserving; all 23 routes + CSS render‑verified, zero new console errors; live 42/42. Cohesive modules (training.py, agent.py) left intact by design. New structure: `docs/frontend-structure.md`. |
| HON‑12 | **OWUI embedded view blocked by our own CSP** | P2 | ✅ | M83. Added `frame-src 'self' http://localhost:3000 http://127.0.0.1:3000` to the CSP (local trusted service only). Verified: `#/owui` now loads the iframe with **no CSP/frame errors** (and the cross‑origin localStorage error cleared too). |

**Honest re‑grading of some ✅ above:** OUT‑1, OUT‑5 (toy batteries) · FEA‑1 (UIA‑only; vision fallback
imprecise) · SV‑1 (stream unwatched) · STB‑2 (survival‑as‑record, not resume) · POL‑3 (viewport‑only) ·
FEA‑2 (now measured — STT WER EN ~93% / AR ~74%, M105.4). They are "done to a smoke‑test bar," not proven
robust — see `docs/honest-state.md`.

### M106 — Unified Event Log + Ops Center (observability)
| ID | Task | Status | Notes |
|---|---|---|---|
| OBS‑1 | **Unified event log** — one store for errors/ops/system/alerts/API | ✅ | `nova/core/eventlog.py`: `event_log` table + indexes, retention‑capped (50k, auto‑prune) + per‑signature error throttle. `log/record_exception/log_request/query/get/stats/prune/clear`. Full design in `docs/observability.md`. |
| OBS‑2 | **Bridge every source into the one store** | ✅ | exceptions (with stack trace via `errors.record`), audit trail (`audit()` category‑mapped), notifications (`alert`), system events (server start/stop, config change), and **all API requests** via the HTTP middleware (`log_request`, polls excluded). Nothing is a separate silo. |
| OBS‑3 | **Event Log explorer UI** | ✅ | `#/events` (`pages-events.js`): full‑text search, category/level/time filters, category chips, **timeline** (errors red), expandable rows with stack trace + context, JSON/CSV export, live updates. |
| OBS‑4 | **Auto issue discovery** | ✅ | `nova/services/issues.py` scans the log + services → recurring errors / failing ops / services‑down as actionable issues (severity + suggestion + deep‑link); `file_issue_as_bug` wires diagnostics → the bug tracker. `/api/issues`, `/api/issues/file`. |
| OBS‑5 | **Merge Bugs + Audit + Diagnostics → Ops Center** | ✅ | `#/diagnostics` is now the hub: Health · Recent Errors · **Discovered Issues** (file‑as‑bug) · Self‑Test · **Event summary + export/report** · **Bug Reports** · Quality Trend. `#/audit` → Event Log, `#/bugs` → Ops Center. |
| OBS‑6 | **Export + full report** | ✅ | `/api/events/export?format=json\|csv` (filtered) + `/api/ops/report` (health + issues + event stats + top errors) — downloadable for external audit/analysis. Tests: `test_eventlog.py` (store, filters, timeline, retention, throttle, request logging, all bridges). |
| SOAK‑ALL | **Comprehensive load+soak of every component** | ✅ | M106.1. `feature_soak.py --load 8` soaks all 16 components (agent, vision/VLM, TTS, image, video, memory, RAG, automation, workflows, notifications, control, **event log**, **diagnostics/audit**, **DB under concurrent load**, **large‑file ingest**, **network‑failure sim**) with concurrent load + resource monitoring (RSS/GPU/CPU) + an auto report (`data/logs/feature_soak_report.md`). **Result: PASS — 0 errors, 0 leaks, 0 slowdowns, 0 dead loops; 11,807 concurrent reqs / 0 errors.** |
| NET‑SIM | **Network‑failure simulation** (disconnect/reconnect) | ✅ | M106.1. `test_network_failure.py`: services down → graceful degradation (http_ok False, embeddings/KB empty, web search empty, status snapshot no‑raise, agent LLM‑down → clear message) → reconnect → recovery. |
| AGENT‑RET | **`agent_run` return bug** (found by soak) | ✅ | M106.1. `agent_run` had no `return` (always None) → `run_action('agent')` never reported results; and returned None when the model was unreachable. Fixed: always returns the final answer / a clear error message. |

### M107 — five reliability features (replay · anomaly · dry‑run diff · budget · restore drill)
| ID | Task | Status | Notes |
|---|---|---|---|
| REL‑1 | **Agent session replay** | ✅ | M107. `nova/services/replay.py` (`list_runs`/`get_run`) reads the `run_id`‑tagged steps `_rlog()` writes to the event log; `GET /api/agent/runs[/{id}]`; Ops‑Center "🎬 Agent Session Replay" card. **Live‑verified**: a real run recorded 8 ordered steps (goal→…→final), retrievable by id. *Fixed a `TypeError` in `_rlog("start", kind=…)` that had silently dropped the goal step.* |
| REL‑2 | **Anomaly alerts from the event log** | ✅ | M107. `nova/services/anomaly.py` + supervised `anomaly_loop` (server.py, 60 s / 60 s warm‑up): error_spike (≥15 errors/10 min), loop_stall (metrics silent >180 s), rss_climb (>40 MB/h over ≥20 min) → notification + `alert` event, 15‑min per‑kind throttle. Read‑only + notify‑only. Tests ×3. |
| REL‑3 | **Dry‑run diff before destructive actions** | ✅ | M107. `nova/services/preview.py` (unified diff for write_file; command + destructive flag for run_command; effect summary for delete/control) → wired into `confirm.gate(…, preview=…)`, shown in the confirmation popup (`.confirm-diff`/`.confirm-will`), and `POST /api/agent/preview`. Never touches disk. **Live‑verified**. Tests ×5. |
| REL‑4 | **Resource budget per agent run** | ✅ | M107. `agent_max_seconds` (default 300) / `agent_max_tokens` (default 0=unlimited) in DEFAULT_SETTINGS; `agent_run` checks both at each step and ends cleanly with a clear "time/token budget reached" final. Tests ×2. |
| REL‑5 | **Backup‑restore drill in CI** | ✅ | M107. `tests/test_backup_restore.py`: seed conversations/chat/schedules/workflows → `make_backup` → wipe → `restore_backup` → assert data returns; plus malformed‑bundle rejection. Guards against backups that never restore. |

### M105.6 — deep tests + safety hardening (from the honest report)
| ID | Task | Status | Notes |
|---|---|---|---|
| DEEP‑1 | **Real tests for dangerous/edge/failure paths** (not smoke) | ✅ | `tests/test_dangerous.py` + `test_edges.py` + `test_failures.py` (38 tests): panic blocks all control, protected‑window guard, credential denylist across all readers, LAN/exec/agent gates, destructive denylist + false‑positive guards, injection catch/miss, retention/÷0/chunking/macro‑cap edges, dependency‑down degradation, bad‑body 500‑guards. Documented in `docs/testing.md`. |
| SEC‑7 | **Credential‑denylist hardening** | ✅ | Found via DEEP‑1: `.git/config` (forward‑slash) + bare `.ssh`/`.aws` dirs bypassed the filter. `is_credential_path` now separator‑agnostic + segment‑aware; list widened (`.gnupg`/`.kube`/`.docker`/gh configs). safety.py coverage 100%. |
| SEC‑8 | **Per‑action control guard (protected windows)** — the report's #1 gap | ✅ | `control._guard()` blocks click/type/keys/drag/scroll/set_text/click_element when the target window looks sensitive (password managers/banking/auth; `control_protected_patterns` tunable). **Hardened after a 4th audit:** fails **closed** on a title‑read error, checks the **window under the click point** (`WindowFromPoint`, not just foreground), **re‑checks before clicking** (TOCTOU), scroll guarded. Audited on block. **Honest:** a title substring check still isn't a sandbox — keep the ⛔ panic stop. |
| VID‑1 | **Verify video generation (LTX) end‑to‑end** | ✅ | M105.6. Ran a real text→video job → produced a valid **574 KB MP4** (`videos/video_061743.mp4`) from the ComfyUI webp. Closes the honest‑report "video unverified" gap. (Output validity confirmed; visual quality not judged.) |
| SOAK‑24H | **Literal 24‑hour soak** | 🟦 running | M105.8/M106.2. `soak_test.py --hours 24` running detached. **Interim ~3.2 h: 79,840 reqs · 0 errors · 0 dead loops · RSS ~76 MB · slope +1.0 MB/h (flat, no leak).** Live progress in `data/logs/soak_progress.json`; hourly checkpoints → quality dashboard (`soak-hourly`); final verdict recorded on completion. |
| SOAK‑1 | **Soak / longevity test** (loops, memory growth, VLM queue) | ✅ | M105.7. `scripts/soak_test.py` (up to `--hours 24`) samples server RSS every 30s → **RSS slope (MB/h)** + loop liveness + error growth + VLM latency → quality dashboard. **30‑min run: 12,520 requests, 0 errors, RSS 94–102 MB, slope −11.4 MB/h (no growth), metrics loop 59/59 alive → no leak.** Honest: 30 min ≠ 24 h, and the VLM queue (`--vlm`) wasn't exercised this run — for the full picture run `soak_test.py --hours 24 --vlm` with screen vision on. |
| VISION‑1 | **Activate + test the full screen‑vision stack live** | ✅ | M105.8. Enabled every opt‑in vision feature and exercised the whole pipeline: `/api/vision/state` ✅, single frame ✅ (117 KB JPEG), MJPEG stream ✅ (8 chunks/428 KB), mouse ✅, keystroke context ✅, **VLM describe ✅** (qwen2.5‑VL described the live desktop in ~11 s), narration loop ✅ (0 errors), screen memory ✅ (2761 chars→4 chunks). Cleaned up + restored privacy defaults (all OFF). Full table in `docs/honest-state.md` M105.8. |
| VLM‑SOAK | **VLM‑queue soak** | ✅ | M105.8b (SOAK‑2). 12‑min `--vlm` soak → **26 describes, 0 errors, p50 28.8 s / max 34.3 s** under load. **Caught a real bug:** `/api/vision/describe` blocked the event loop (metrics loop died during each ~30 s call) → fixed with `asyncio.to_thread`; re‑run shows **loop alive 19/19 samples**. Memory sawtooths 78↔153 MB (per‑describe ~73 MB screenshot buffer, released each time) — **bounded, no leak**. Full detail: honest‑state SOAK‑2. |
| COV‑1 | **Raise `browser`/`screen` coverage with a disposable target app** | ✅ | M105.7. `tests/test_screen_live.py` spawns a **disposable WinForms window** (owned + killed) and drives it via OCR + UIA `find_element` (closes HON‑2b) → `screen.py` **21%→52%**. `tests/test_browser_live.py` drives headless `browse()` against a disposable local HTML page → `browser.py` **17%→25%** (+ hermetic VisibleBrowser thread test). Opt‑in via `NOVA_LIVE_TESTS=1` (they pop windows / grab the screen), so the gate stays hermetic. Full‑suite coverage w/ live = **~59%**. |
| SEC‑9 | **`allow_input_capture` master gate** (keylogger‑class) | ✅ | Default OFF; required for the 🎬 macro recorder AND SV‑4 keystroke context. Settings toggle w/ confirm. Reduces the risk surface I flagged. |
| IDEA‑8b | **Semantic memory recall** | ✅ | Embedding cosine blended with keyword, gated by `memory_semantic` (default OFF → zero hot‑path cost). Facts embed at write (`emb` column + idempotent migration); embeddings never leave the server. Test proves "car"~"vehicle". |
| DEEP‑BUGS | Bugs the deep tests caught & fixed | ✅ | (1) credential bypass [SEC‑7]; (2) `screen_memory_keep:0` clobbered by `or 50`; (3) macro‑save empty‑list fallback; (4) semantic recall disabled by a missing `get_settings` import. All fixed + regression‑tested. |

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
| OUT‑2 | Verify **training** produces a usable nova‑local end‑to‑end | ✅ | M75. `scripts/nova_eval.py` runs identity/knowledge/bilingual checks on the trained model → **`nova-local` 4/4** (identifies as Nova, knows RTX 5090/32GB, knows its domain, answers Arabic in Arabic). `docs/nova-local-eval.md`. The *output* model is verified usable; the fine‑tune *process* itself stays owner‑run (`docs/training-pipeline.md`). |
| OUT‑3 | Verify **image/video generation** actually succeeds (not just job‑starts) | ✅ | M67. `scripts/gen_eval.py` triggers a real generation via the live API + ComfyUI and validates the PNG. **Verified:** SDXL produced a correct 1024×1024 image ("red apple on a white table") in **9.1s** — visually confirmed. `docs/generation-baseline.md`. (Video/LTX uses the same path — slower; verify manually.) |
| OUT‑4 | `screen_if` real‑screen matching test (OCR/vision against live content) | ✅ | M75. `scripts/screen_if_eval.py` OCRs the **real** screen (5024 chars), confirms `screen_if` matches a real on‑screen word → fires the action, and rejects a nonsense string. Verified live (not mocked). |
| OUT‑5 | RAG retrieval quality check (relevance of citations) | ✅ | M58. `scripts/rag_eval.py` seeds an isolated KB with single‑topic docs and checks each paraphrased query retrieves the right one. Baseline `docs/rag-baseline.md`: **precision@1 = 5/5 (100%), MRR = 1.0** (nomic‑embed‑text). |

## P1 — Stability (watchdog · error recovery · graceful shutdown)

| ID | Task | Status | Notes / issue |
|---|---|---|---|
| STB‑1 | **Watchdog/supervisor** to auto‑restart `server.py` on crash | ✅ | M55. Hardened `watchdog.ps1`: **fixed the python‑stub bug** (old `(Get-Command python).Source` resolved to the WindowsApps stub → every restart silently failed) via `Resolve-Python`; added timestamped `watchdog.log`, N‑consecutive‑fail threshold, post‑restart re‑probe, and a `-Once` self‑check. Verified: `-Once` resolves the real Python312 + detects the live server. |
| STB‑2 | Persist/resume training & recording across server restart | ✅ | M66 + M75. Jobs persisted to a `jobs` table; startup `reconcile_interrupted()` marks killed jobs `interrupted` + notifies; **`GET /api/jobs/history`** exposes the persisted history (survives restarts). True auto‑resume of a killed OS process is **not feasible** (Job Object terminates children) — done to the limit of what's possible: nothing is lost or silent. Tests cover reconcile + history. |
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

## P1 — Media-in-chat + Agent Vision (MED / AVL · owner request 2026‑06‑30)

| ID | Task | Status | Notes |
|---|---|---|---|
| MED‑1 | **Image capture / image‑gen / video‑gen from the unified chat** | ✅ | M101 + M104. Composer buttons 📸/🎨/🎬 + natural chat commands (EN+AR). Results render **inline**. **M104 fix:** rewrote `showMedia` to poll **job status** (`/api/processes`) instead of the file URL → **zero console errors** during generation (was: benign 404 retries). Verified end‑to‑end. |
| AVL‑1 | **Agent vision tasks** — "what's on my desktop?" + autonomous game play | ✅ | **All building blocks shipped & live‑verified:** "what's on my desktop?" (see_screen → VLM) ✅, mouse **move/click/drag** all verified live (drag 8,8→40,40 returned ok), UIA text entry ✅, perceive→act→observe loop (AVL‑2) ✅. The agent can watch a game and drive the mouse. **Honest residual (OS limit, not our code):** sustained autonomous game‑play that needs rapid *keystrokes* is bounded by this environment's synthetic‑keyboard suppression (Win11 input lock) — UIA SetValue works for text fields but not game key‑presses. Documented; not a code defect. |
| AVL‑2 | Agent screen‑driven control loop helper (perceive→act→observe) | ✅ | M105. Satisfied by the ReAct controller (`agent_run` iterates up to `max_steps`, each step feeding the prior tool observation back) + the three perception tools (`see_screen`/`screen_awareness`/`find_element`) + `control`/`act_on_screen`, with the AGENT_FOOTER mandating the **LOOK → ACT → LOOK‑AGAIN** loop until the goal is met. The loop *is* the helper; no extra primitive needed. (Sustained game‑play reliability is bounded by AVL‑1's documented OS keyboard‑suppression limit — not the loop.) |
| CORE‑P | **Enforce the single‑user/local‑only CORE PRINCIPLE everywhere** | ✅ | M100. `docs/PRINCIPLES.md` + referenced in CLAUDE/STATUS/ROADMAP/PROJECT_PLAN/WORKFLOW. Permanent discovery‑log rule added to WORKFLOW. |

## P1 — Unified Workspace + Auto model (UWS · owner request)

One page merging Chat + Agent with professional toggle buttons, requested 2026‑06‑30.

| ID | Task | Status | Notes |
|---|---|---|---|
| UWS‑1 | **Merge Chat + Agent into one page** with pro toggle buttons | ✅ | M97. `static/js/pages-workspace.js` → `#/workspace` ("Nova"). Segmented 💬 Chat / 🤖 Agent + pill toggles 🧠 DeepThink · 🌐 Web Search · 🔓 Full Access (agent‑only) · 📎 Attach. `#/chat`+`#/agent` redirect here; single nav entry. Renders chat token streams + agent step cards; mic; Stop. Render‑verified, zero console errors. |
| UWS‑2 | **Attach any file** (images/docs/any format) | ✅ | M97. Drag‑drop or 📎; `/api/upload` handles all formats (OCR + VLM for images); chips; content → chat context. |
| UWS‑3 | **✨ Auto model (intelligent) + manual** | ✅ | M97. `nova/services/automodel.py` + `/api/model/auto`; chat+agent resolve `model:"auto"` per task (coding→qwen3‑coder:30b verified, reasoning/DeepThink→reasoning/larger, vision→VLM, agent→control‑model). UI shows the pick + reason live. Manual select still available. |
| UWS‑4 | **Agent decides screen capture/record/monitor** | ✅ | M97. Agent gets its full toolset (see_screen/read_screen/screenshot/screen_awareness/control + record via automation); the ReAct loop chooses when — no manual wiring. |
| UWS‑5 | DeepThink + Full Access as professional toggles (both surfaces) | ✅ | M97 (workspace) + M62/M72 (chat/agent). Pill buttons, not checkboxes. |
| UWS‑6 | "Select a file and work on it" (Claude‑Desktop‑style) | ✅ | M99. **📂 Open file** in the Workspace: loads a file from disk (`GET /api/file/read`, credential‑denylist gated), shows it as a card, injects its content into context, and after the AI replies a **💾 Save to <file>** button writes the edit back (`POST /api/file/write`, `exec_allowed`‑gated + audited; extracts the first code block or full reply). Verified end‑to‑end (read/write API + frontend card). Side‑by‑side inline‑diff editor = future polish (UWS‑6b). |
| UWS‑7 | Bilingual README (EN + AR) | ✅ | M98. Full English + Arabic (RTL) README: specs, how‑to‑run, features, safety, architecture. |

## P1 — AI Screen Vision (Phase 7 · NEW core feature)

Real‑time perception + control: the AI sees exactly what the user sees and can act on it. Builds on
the existing Screen Studio service (`nova/services/screen.py`: `capture_screenshot`, `read_screen`,
`describe_screen`, `act_on_screen`, `RECORDER`) — extend, don't duplicate. **Privacy‑first:** every
capture/track path is opt‑in, local‑only, pausable, and non‑persistent by default.

| ID | Task | Status | Notes / design |
|---|---|---|---|
| SV‑1 | **Live screen stream** to the dashboard — throttled frames (JPEG over WS or MJPEG endpoint), adjustable FPS/quality, start/stop | ✅ | M61 backend + M63 UI. `GET /api/vision/stream` MJPEG (`mss`→pillow downscale+JPEG, re‑reads FPS/quality each tick); the **Live page** (`#/live`) renders it in an `<img>` with an FPS slider; navigating away stops the stream (router cleanup). |
| SV‑2 | **Continuous AI vision loop** — periodically feed frames to qwen2.5‑VL and stream a running description; on‑demand "what's on my screen now?" | ✅ | M61/M63 + **M105.4**. On‑demand describe + the **continuous narration loop is now implemented**: `narration_loop()` (supervised, opt‑in via `vision_narrate` + interval 10–300s) periodically VLM‑describes the screen and pushes a running narration over the WS bus, rendered live on the Live page. Off by default (VLM cost), gated by `screen_vision_enabled`. Tested (`test_narrate_gate`). |
| SV‑3 | **Mouse tracking** — global cursor position + click events, streamed to the UI + exposed to the agent | ✅ | M61 backend + M63 UI. `GET /api/vision/mouse` (`ctypes GetCursorPos`, gated on `track_mouse`); Live page polls it (200ms) and overlays a glowing cursor marker on the stream. (Click events deferred — position covers the core need.) |
| SV‑4 | **Keyboard tracking** (opt‑in, privacy‑gated) — keystroke / active‑window context for the AI | ✅ | M61 + **M105.4**. `GET /api/vision/context` now returns focused‑window title **+ a short rolling buffer of recently‑typed text** (last ~200 chars) captured via a pynput listener that runs **only while `track_keyboard` is on** — in‑memory only, never persisted, cleared the instant the gate is turned off, with a clear "don't type passwords" warning on the Live page. Tests assert the off‑path starts no listener. Privacy‑first by construction. |
| SV‑5 | **Unified live session** — one view fusing live screen + input + AI vision, wired to `act_on_screen` so the AI can interact with what it sees | ✅ | M63. New **"AI Screen Vision" (`#/live`)** page: live stream + mouse overlay + focused‑window context + on‑demand describe + all privacy toggles + FPS slider, in one view. Render‑verified (nav item, toggles default‑off, zero console errors). The agent already has `act_on_screen` for control; this page is the human‑facing live session. |
| SV‑6 | **Privacy & safety controls** — master opt‑in, per‑capability toggles, pause/redact, status indicator, zero‑persistence default | ✅ | M61. Settings `screen_vision_enabled`/`vision_fps`/`vision_max_width`/`vision_quality`/`track_mouse`/`track_keyboard` (all OFF/safe by default); every route 403s unless its gate is on; stream/describe audited; nothing persisted. |
| SV‑7 | **Tests + outcome verification** — stream lifecycle, throttling, privacy gates default‑off, tracking accuracy | ✅ | M61 backend (6 tests: JPEG grab, gates default‑off, frame when enabled, mouse/keyboard gates) + M63 render‑verified the Live page (nav, toggles off by default, describe button, zero console errors). |

**Rollup:** **Phase 7 complete (M61 backend + M63 UI + M105.4).** SV‑1 ✅ stream · SV‑3 ✅ mouse ·
SV‑5 ✅ Live page · SV‑6 ✅ privacy · SV‑7 ✅ tests · SV‑2 ✅ on‑demand describe **+ opt‑in continuous
narration loop** · SV‑4 ✅ focused‑window **+ opt‑in recent‑keystroke context** (privacy‑gated, in‑memory,
auto‑stops on opt‑out). Optional future polish: click‑event capture in the recorder, wire the Live page
directly to `act_on_screen`.

## 💡 Innovation backlog (IDEA · creative, in‑scope — single‑user/local‑only)

Original, useful ideas aligned with the vision. All ⬜ TODO; build when prioritized. Each is local‑only
and opt‑in where it touches the screen/privacy. (Full descriptions in `ROADMAP.md` → Innovation backlog.)

| ID | Idea | Priority | Status |
|---|---|---|---|
| IDEA‑1 | Visual macro recorder (record/replay UIA+mouse as named macros) | P2 | ✅ M105.2. **Both halves shipped.** *Record:* `nova/services/macro.py` uses **pynput** global listeners to passively capture mouse clicks + typing into control steps (typed chars collapse into a `type` step), user‑initiated, capped at 500 events, `exec_allowed`‑gated. `/api/macro/{state,start,stop,save}` + a "🎬 Macro recorder" panel on the Workflows page. *Replay:* saved as a Workflow of `control` steps (the M105 `control` action). Tests: service (step building) + API (save) ✅; **live‑verified** — a real OS click was captured as `{action:click,x:6,y:6}`, listeners stopped cleanly. Honest: typed text replays via UIA; special‑key replay is limited by this env's synthetic‑keyboard suppression; coords are physical px (record/replay at the same DPI scale). |
| IDEA‑2 | Local screen memory — opt‑in OCR+embed of the screen into the KB ("what did I see earlier?") | P2 | ✅ M105. `remember_screen()` (in `screen_vision.py`) OCRs the screen and indexes the text into the KB via new `kb_ingest_text()`, as a timestamped "screen‑memory" doc. **Strictly opt‑in** (`screen_memory_enabled`, default OFF) + Settings toggle. `POST /api/vision/remember-screen` (403 when off) + `screen_memory` schedule action (for periodic capture). Tests (gate + ingest) + live roundtrip verified (off→403; on→4284 chars/6 chunks; cleaned up). Local‑only. |
| IDEA‑3 | Save a successful agent run as a reusable Workflow/Automation | P2 | ✅ M105. New `agent` action in `run_action` (re-runs `agent_run` with a stored goal/model/flags). `POST /api/agent/save-workflow` persists the run as a one-step workflow. Unified Workspace shows a **"💾 Save as workflow"** button on the agent's final answer. Re-running the workflow replays the goal. API test + live roundtrip verified. |
| IDEA‑4 | Hands‑free voice conversation loop (STT→answer→TTS) | P2 | ✅ M105. Unified Workspace 🎙️ toggle: listens (MediaRecorder + Web‑Audio **silence detection**, 15s cap) → `/api/stt` → sends a chat turn → on reply‑end speaks it via local Piper `/api/tts` → listens again; stops cleanly on page‑leave/error/toggle. All three legs verified (STT M104 round‑trip, chat stream, TTS `ok=True`); renders zero console errors. Implementation complete; the only thing not automatable is the physical microphone (no headless mic) — that's an environment limit, not a code gap. |
| IDEA‑5 | Folder Q&A — index a directory, chat over it with citations | P2 | ✅ M105. `kb_ingest_folder()` walks a directory (recursive, capped 200 files), indexes supported types (txt/md/pdf/docx/code), **skips credential stores** (shared `is_credential_path` in `nova/core/safety.py`) + unsupported types. `POST /api/kb/ingest-folder` (exec_allowed‑gated, audited, threadpool‑offloaded). Knowledge page got a "📁 Index a folder" input. Then chat with RAG (use_rag) cites the folder's files. Service test + live roundtrip (2 files → retrieval correct) verified. |
| IDEA‑6 | Quality dashboard — scheduled eval batteries charted over time | P3 | ✅ M105. `quality_runs` table + `nova/services/quality.py` (`record`/`history`/`summary`/`health_snapshot`) + `/api/quality` (GET history+summary, POST record, POST snapshot). Diagnostics page got a **"📈 Quality Trend"** card (latest % + ▲/▼ delta per suite + "take a health snapshot"). `quality_check` schedule action for periodic snapshots; `agent_eval.py --record` feeds the trend (other evals can POST). Test + live roundtrip (snapshot 4/5, agent record 100%) verified. |
| IDEA‑7 | Region watch → act (pin a screen region; act on text change) | P3 | ✅ M105. Extended `screen_if`: optional `region` [x,y,w,h] pins the watch to a screen region (faster, fewer false positives) + an `absent` flag inverts the trigger (act when the text *disappears*). Automation builder gained region + "act when absent" fields. Test (region passthrough/validation + present/absent logic) ✅ · gate ✅. |
| SCRN‑IF‑FIX | **`screen_if` reacting to other apps + notification spam** (owner report M105.10/.11) | ✅ | Root cause: `screen_if` read the WHOLE desktop and fired on EVERY tick → matched other apps' text ("disk full"/"error") + spammed "Screen matched: …". Fixes: **edge‑triggering** (fires only on a state *change*; `always_notify` opts out), **`window` scoping** (reads only the named window's rect; skips if not open — never full‑screen fallback), **`whole_word`** filter, clearer non‑error text, recursion guard, and the **agent `schedule` tool refuses `screen_if` watchers** + caps intervals ≥30 s. Tests: edge‑no‑spam, window‑scope, whole‑word, agent‑cannot‑schedule‑watcher. |
| IDEA‑8 | Local persistent memory (durable user facts/preferences) | P2 | ✅ M105. `nova/services/memory.py` + `memory` table + `/api/memory` (list/add/recall/delete) + Settings "🧠 Persistent Memory" card. Facts are injected as a system block into **chat** and **agent** prompts (keyword‑ranked, pinned‑first, de‑duped). Agent gained `remember`/`recall` tools. Tests: service + API + UI render. Local‑only. |
| IDEA‑2b | **Screen‑memory retention policy** — auto‑expire old screen‑memory docs + a "purge screen memories" button | P2 | ✅ M105. `_prune_screen_memory()` keeps only the newest `screen_memory_keep` (default 50) after each snapshot; `purge_screen_memory()` + `DELETE /api/vision/screen-memory` + Settings "🧹 Purge all screen memories" button wipe them all. Test (prune 5→3, purge→0, non‑screen docs untouched) + live roundtrip (keep=1 prunes; purge removes) verified. Closes the M105d retention gap. |
| IDEA‑9 | Image edit pipeline (ComfyUI img2img refine from chat) | P3 | ✅ M105. `toolkit/generate.ps1` gained `-InitImage`/`-Denoise` (LoadImage→VAEEncode→KSampler from the init latent). `/api/toolkit/image` accepts `init_image` + `denoise`. Unified Workspace: every generated image gets a **"✨ Refine / edit"** button → re‑runs img2img with a new prompt. Live verified end‑to‑end (base 1.2 MB PNG → refined 1.28 MB PNG, both valid). |
| IDEA‑10 | Self‑healing loops (auto‑restart a dead background loop) | P2 | ✅ M105. `_supervise()` wraps every background loop (metrics/status/scheduler/backup); a hard crash or unexpected return auto‑restarts the loop with exponential backoff (cap 30s), recording the crash to `/api/errors`; `CancelledError` (clean shutdown) still stops it. Unit‑tested (crash → restart once; cancel → stop). |

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
| FEA‑3 | Voice improvements (input UX, TTS voices) | ✅ | M76. **Input:** GPU Whisper + explicit ⏹ Stop (FEA‑2/M62). **Output:** auto language‑aware Piper voice (ar→kareem, en→lessac) + a new **speech‑rate control** — `tts_rate` setting (Settings slider 0.7–1.6×) → Piper `length_scale=1/rate` (verified: 0.7 produced shorter/faster audio). Graceful fallback on older Piper. |
| FEA‑4 | Conditional screen actions UX in Automation page (expose `screen_if`) | ✅ | M74. Automation page now offers "👁 If screen shows… then act": match text/regex + then‑action (notify/speak/command) + with‑text + a "use vision model" toggle → `{match,then_action,then_params,vision}`. Render‑verified. |
| FEA‑E | `screen_if` action · bespoke pages · Nova Brain 2.0 · OWUI 0.10.1 | ✅ | M37/M39/M41. |

## P3 — Polish (UI · performance · optimization)

| ID | Task | Status | Notes |
|---|---|---|---|
| POL‑1 | Performance budget for the animated background (measure FPS; auto‑lite on weak GPUs) | ✅ | M74. `autoLite()` samples real background FPS for ~2s once per machine; if <32fps it switches to lite visuals + persists + toasts. Respects reduced‑motion and explicit user choice. |
| POL‑2 | Accessibility pass (ARIA, keyboard nav, contrast) | ✅ | M71 + **M105.4**. Skip‑to‑content link, `role`/`aria-label` on nav + main, `aria-live="polite"` toasts, `:focus-visible` outlines, `<html lang>` tracks the UI language, and **`aria-label` on all icon‑only buttons** (🎤/🎙️/🎨/🎬/📸). Core keyboard + screen‑reader paths covered. (Formal WCAG‑AA certification is explicitly out of scope for a single‑user local tool — owner decision, not a gap.) |
| POL‑3 | Mobile responsive layout | ✅ | M74. Automated **mobile‑viewport** test (390×844): dashboard renders, hamburger menu present, **zero horizontal overflow**, zero console errors; screenshot confirms a clean stacked layout. **Physical‑phone testing is N/A by the CORE PRINCIPLE** — Nova is single‑user/local‑only with no inbound/LAN/phone access, so it is only ever used from the host machine's browser; the responsive layout is verified for small windows, which is the only relevant case. (Reclassified from "real‑device testing" — that was never in scope.) |
| POL‑4 | 32B throughput re‑benchmark on Ollama/llama.cpp updates | ✅ | M75. `scripts/bench_model.py` (reusable). **qwen2.5:32b on RTX 5090: 11.1 tok/s gen, ~488 tok/s prompt eval, 13.4s load.** `docs/32b-throughput.md`. |

## 🚫 Excluded (owner decision — do not build)
- Multi‑user / accounts / roles / RBAC.
- RTL mirroring (Arabic stays text‑only, fixed layout).
- Cloud hosting / horizontal scaling.

---

### Rollup
- **Original roadmap (P0→P3 + Phases 7/8): all items shipped & smoke‑verified.** BUT see the **⚠ Honest
  gaps (HON‑1…11)** at the top — that is the real remaining work, and it is **not** done.
- **Highest priority now (safety): HON‑1** (confirmation/kill‑switch for agent GUI control) and **HON‑10**
  (prompt‑injection defense). These outrank everything else — the control surface is currently
  unguarded.
- **Then:** HON‑2 (real GUI integration test) · HON‑3 (coverage) · HON‑7 (honest eval batteries) ·
  HON‑4/5/6 (observability, soak, end‑to‑end stream/web) · HON‑8/9/11 (lockfile, CI remote, refactor).
- **Reality check:** ✅ in this file = "built + verified once," not "battle‑tested." Re‑verify before
  trusting unattended. Full truth: `docs/honest-state.md`.
- **Completed foundation:** see `BUILD_LOG.md` milestones M28–M76.
