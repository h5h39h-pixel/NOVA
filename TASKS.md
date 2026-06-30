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
| SEC‑4 | Encrypt `cloud_api_key` at rest (use existing `cryptography` dep; key from machine‑local secret) | ⬜ | Stored plaintext in DB today. Low threat (local) but flagged. |
| SEC‑5 | One‑command HTTPS enablement + doc (`https_enabled` + cert) | ⬜ | `ensure_cert()` exists; make turnkey. |
| SEC‑6 | Security review pass of every `subprocess`/exec call site | ⬜ | Audit `run_action`, agent tools, tts, screen, owui. |
| SEC‑E | Exec **LAN gate** (`allow_remote_exec`) + audit + `exec_allowed()` | ✅ | M‑B. Localhost always allowed by design; LAN requires opt‑in. |
| SEC‑E2 | Hashed auth tokens · rate limiting · security headers (baseline) · audit log | ✅ | M26/M‑B. |

## P0 — Real test coverage (unit + integration + smoke)

| ID | Task | Status | Notes / issue |
|---|---|---|---|
| TST‑1 | Deepen **unit tests** per service (real assertions, not "returns 200") | ⬜ | chat, kb, training, schedules, settings, backup, insights, ollama, metrics, files. |
| TST‑2 | **Hermetic test mode** — mock Ollama/ComfyUI so tests don't need them running | ⬜ | Live suite is environment‑coupled today. |
| TST‑3 | Agent‑loop integration tests with a mocked model (tool dispatch, JSON parse, stop) | ⬜ | |
| TST‑4 | Clean‑venv install test — prove pinned `requirements.txt` installs together | 🟧 | Pinned to *installed* versions; never clean‑installed. |
| TST‑5 | Make CI actually run (local `act` or a Git remote) | 🟧 | `.github/workflows/ci.yml` written, **never executed**. |
| TST‑6 | Frontend interaction tests (beyond the load/zero‑console gate) | ⬜ | |
| TST‑E | pytest suite (24) + live suite (42) + Playwright load gate + pre‑commit hook | ✅ | M‑C. Foundation; shallow — see TST‑1. |

## P1 — Outcome verification (does it actually work?)

| ID | Task | Status | Notes / issue |
|---|---|---|---|
| OUT‑1 | **Agent goal battery** — run fixed goals, measure real success rate, record baseline | ⬜ | Loop tested; success rate **unmeasured**. |
| OUT‑2 | Verify **training** produces a usable nova‑local end‑to‑end | 🟧 | External scripts in `C:\AI\training`; only log‑parsing verified. |
| OUT‑3 | Verify **image/video generation** actually succeeds (not just job‑starts) | 🟧 | Plumbing only. |
| OUT‑4 | `screen_if` real‑screen matching test (OCR/vision against live content) | 🟧 | Unit‑tested with a **mocked** screen only. |
| OUT‑5 | RAG retrieval quality check (relevance of citations) | ⬜ | |

## P1 — Stability (watchdog · error recovery · graceful shutdown)

| ID | Task | Status | Notes / issue |
|---|---|---|---|
| STB‑1 | **Watchdog/supervisor** to auto‑restart `server.py` on crash | ⬜ | `watchdog.ps1` exists — verify/own it. |
| STB‑2 | Persist/resume training & recording across server restart | ⬜ | Job Object kills them on restart (by design today). |
| STB‑3 | Error recovery + surfacing in background loops (no silent `except: pass`) | 🟧 | A dead loop is invisible except via `/api/health`. |
| STB‑4 | Back up generated media/uploads (only the DB is snapshotted today) | ⬜ | |
| STB‑5 | SQLite WAL mode + concurrency review | ⬜ | Single‑writer contention under load is untested. |
| STB‑E | Daily DB snapshots (rotate 14) + migration framework + `/api/health` + error aggregation | ✅ | M‑B/M‑D. |

## P2 — Documentation (keep the six files current)

| ID | Task | Status | Notes |
|---|---|---|---|
| DOC‑1 | Update the six source‑of‑truth files **every** session | 🟦 | Permanent rule (`WORKFLOW.md`). |
| DOC‑2 | Refresh `README.md` / `SETUP.md` for current state | ⬜ | |
| DOC‑3 | Document (or vendor) the external training pipeline | ⬜ | `C:\AI\training` scripts. |
| DOC‑E | `ARCHITECTURE.md`, `DATA_MODEL.md`, `SECURITY.md`, `docs/*`, OpenAPI export | ✅ | M‑D. |

## P2 — Feature improvements

| ID | Task | Status | Notes / issue |
|---|---|---|---|
| FEA‑1 | Click‑to‑act reliability (UI Automation / pywinauto + focus) | 🟧 | Best‑effort; plan in `docs/click-to-act.md`. |
| FEA‑2 | STT Arabic/noisy accuracy (larger Whisper default / tuning) | 🟧 | `stt_model` configurable; default weak on Arabic. |
| FEA‑3 | Voice improvements (input UX, TTS voices) | ⬜ | |
| FEA‑4 | Conditional screen actions UX in Automation page (expose `screen_if`) | ⬜ | Backend done (M39); no dedicated UI. |
| FEA‑E | `screen_if` action · bespoke pages · Nova Brain 2.0 · OWUI 0.10.1 | ✅ | M37/M39/M41. |

## P3 — Polish (UI · performance · optimization)

| ID | Task | Status | Notes |
|---|---|---|---|
| POL‑1 | Performance budget for the animated background (measure FPS; auto‑lite on weak GPUs) | ⬜ | "Lite visuals" toggle exists. |
| POL‑2 | Accessibility pass (ARIA, keyboard nav, contrast) | ⬜ | Essentially none today. |
| POL‑3 | Mobile testing on real devices | ⬜ | Responsive CSS untested on hardware. |
| POL‑4 | 32B throughput re‑benchmark on Ollama/llama.cpp updates | 🟧 | `docs/32b-throughput.md` (monitoring). |

## 🚫 Excluded (owner decision — do not build)
- Multi‑user / accounts / roles / RBAC.
- RTL mirroring (Arabic stays text‑only, fixed layout).
- Cloud hosting / horizontal scaling.

---

### Rollup
- **Active priorities:** P0 Security (3 open, SEC‑1/2/3 ✅) · P0 Tests (6 open) · P1 Outcome (5) · P1 Stability (5).
- **Next:** SEC‑4 (encrypt cloud_api_key) → SEC‑5 (HTTPS turnkey) → SEC‑6 (exec call‑site audit) → TST‑1.
- **Completed foundation:** see `BUILD_LOG.md` milestones M28–M41 (modular backend, hardening,
  bespoke UI, Nova Brain, OWUI 0.10.1).
