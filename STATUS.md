# STATUS — Nova / AI Control Center

**Read this first.** Live snapshot of what's done, what's fragile, and what's next.
Personal single‑user system (not a product). Update this file on **every** work session.

_Last updated: 2026-06-30_

**Health gate (must stay green):** `python scripts/check.py` → pyflakes + node --check + pytest (~84 hermetic + 4 live frontend)
· live suite `python run_tests.py` → 42/42 · self‑test 13/13 · local CI `python scripts/ci_local.py` · agent baseline `python scripts/agent_eval.py`.

**Status legend:** ✅ DONE · 🟧 FRAGILE (works but has a known issue) · 🟦 IN PROGRESS · ⬜ TODO · 🚫 EXCLUDED (owner decision)

---

## Where we are right now
The system is **feature‑complete and architecturally clean**, but its **test depth, security
hardening, and real‑world outcome verification lag behind its ambition**. The foundation
(git, pinned deps, vendored assets, CI scaffolding, observability, modular backend) is in place.
The next campaign is hardening, by priority below.

## 🚫 Explicitly excluded (do not build)
- **Multi‑user / accounts / roles / RBAC** — this is a personal single‑user system.
- **RTL mirroring** — Arabic stays text‑only on the fixed LTR layout.
- **Cloud hosting / horizontal scaling** — local single‑machine only.

## Next 3 actions (highest priority)
1. **OUT‑5** RAG retrieval quality check (relevance of citations). (P1)
2. **STB‑2** Persist/resume training & recording across server restart. (P1)
3. **STB‑4** Back up generated media/uploads (only the DB is snapshotted today). (P1)

_**P0 Security + P0 Tests COMPLETE** ✅. **P1 in progress:** OUT‑1 ✅ (agent baseline 5/5 after a real path bugfix, M54) · STB‑1 ✅ (watchdog python‑stub fix, M55) · STB‑3 ✅ (loops surface errors, M56) · STB‑5 ✅ (SQLite WAL, M57). **⚠ Restart `server.py`** to activate M54 + M56 + M57 on the live instance._

---

## Done (high confidence) ✅
- Backend modular `nova/` package (4 core · 18 services · 21 routers); `server.py` ≈ 555 lines.
- Frontend split (core/pages/shell.js); fully local assets (no CDN); auto cache‑busting.
- Vibrant UI + 4 bespoke pages (Chat/Training/Screen/Agent); render‑verified.
- Nova Brain 2.0 (3D neural map). Knowledge base / RAG. Chat (+RAG, compare, export).
- git repo + `.gitignore` + MIT LICENSE + pinned `requirements.txt`/`.in`.
- Exec **LAN gate** (`allow_remote_exec`), security headers, hashed auth tokens, audit log.
- Scheduled DB snapshots, DB migration framework, observability (`/api/health`, `/api/errors`, metrics history).
- pytest suite (24) + live suite (42) + frontend load gate; pre‑commit hook; CI workflow (written).
- Open WebUI upgraded to **0.10.1**; integration made schema‑agnostic; custom tools/models preserved.

## Fragile — works but needs improvement 🟧
| Item | The issue |
|---|---|
| **Command‑exec surface** | Hardened (P0 Security complete): confirm‑guard (SEC‑1) + centralized denylist (SEC‑2) + strict CSP/headers (SEC‑3) + at‑rest key encryption (SEC‑4) + HTTPS turnkey (SEC‑5) + call‑site audit incl. the `screen lang` injection fix (SEC‑6). Residual by design: localhost exec is unrestricted (the product's purpose) — gated on LAN. No global kill‑switch (optional). |
| **Agent reliability** | Loop **mechanics integration‑tested** (TST‑3, M51) **and a real success baseline measured** (OUT‑1, M54: **5/5** with qwen2.5:14b after fixing a write/read path bug the battery caught). Baseline is a small safe‑tool battery — broader/destructive‑adjacent goals still unmeasured. Live server needs a restart to pick up the path fix. |
| **Tests** | **P0 Tests complete** (M49–M53): deep per‑service assertions, **hermetic** pytest (network‑blocked), agent‑loop integration tests, clean‑venv install proof + local CI runner, and live frontend interaction tests. Suite = 72 hermetic + 4 live. Remaining test‑adjacent gap is **outcome verification** (does the agent/training/generation actually succeed?) — that's the P1 Outcome phase, not unit tests. |
| **`screen_if` (conditional screen actions)** | Implemented + unit‑tested **with a mocked screen**; never run against a real screen / real vision matching. |
| **Image/video generation** | Endpoints fire + jobs start; **actual generation success/quality never verified**. |
| **Training pipeline** | The fine‑tune scripts live **outside the repo** in `C:\AI\training` (`learn.ps1`, `train_lora.py`, `harvest_chats.py`). We only orchestrate + parse logs — never verified they produce a good model. |
| **Click‑to‑act** | Best‑effort only — 7B vision grounding imprecise at 4K + Win11 focus rules. Don't rely on it. |
| **STT (Arabic/noisy)** | base/CPU Whisper; weak on Arabic. Size now configurable. |
| **CI** | The CI *commands* now **actually run** locally via `scripts/ci_local.py` (clean‑venv install → gate → PASS, M52). GitHub‑hosted execution still needs a Git remote the owner must create (`act` can't emulate `windows-latest`). |
| **Pinned deps** | **Proven to clean‑install** from a fresh venv (M52, all wheels, no conflicts). Caveat: only *direct* deps are pinned — transitive deps resolve to latest‑compatible at install time (not a full lockfile). |
| **Secrets** | `cloud_api_key` now **encrypted at rest** (SEC‑4, Fernet; key in `.nova_key`); tokens hashed; config.json git‑ignored. (Resolved.) |
| **Background loops** | **Fixed (STB‑3, M56):** metrics/status/scheduler/backup loops now `record_error(...)` → visible in `/api/errors` + Diagnostics (deduped). They still recover next tick rather than crash. |
| **Watchdog** | **Fixed (STB‑1, M55):** `watchdog.ps1` now resolves a real python (was the WindowsApps stub → restarts silently failed), logs, and uses a fail threshold. Still: a server restart kills running training/recording (Job Object) — STB‑2 will address resume. |
| **beforeunload text** | Browser shows generic wording + only after interaction (browser limitation, not fixable). |

## 🆕 Chat interface improvements (CHAT, P1) — ✅ shipped M62
DeepThink toggle (step‑by‑step reasoning), Web Search toggle (live DuckDuckGo via `ddgs`, cited;
opt‑in/online), and an explicit microphone **⏹ Stop** control. Render‑verified; live suite 42/42.
New dependency: `ddgs` (pinned). Tracked as CHAT‑1…3 in `TASKS.md`.

## 🆕 New core feature — AI Screen Vision (Phase 7, P1)
Added 2026‑06‑30 by owner request. Real‑time screen stream + mouse/keyboard tracking + a continuous
AI vision loop, fused into a live "see‑what‑I‑see & act" session — builds on the existing Screen
Studio. **Privacy‑first:** opt‑in, local‑only, non‑persistent by default. Tracked as **SV‑1…7** in
`TASKS.md`; design in `PROJECT_PLAN.md` Phase 7. **Status: backend done (M61)** — `/api/vision/*`
(stream/frame/mouse/context/describe) + privacy gates (SV‑6 ✅) + 6 tests; **frontend "Live" page
(SV‑5) + continuous narration (SV‑2 UI) pending.**

## In progress 🟦
- _(none active — pick the next from TASKS.md P1: SV‑1 or STB‑2)_

See **`TASKS.md`** for the full prioritized, actionable backlog, **`PROJECT_PLAN.md`** for the phase
plan, and **`WORKFLOW.md`** for how we work.
