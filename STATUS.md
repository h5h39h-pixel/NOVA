# STATUS — Nova / AI Control Center

**Read this first.** Live snapshot of what's done, what's fragile, and what's next.
Personal single‑user system (not a product). Update this file on **every** work session.

_Last updated: 2026-06-30_

**Health gate (must stay green):** `python scripts/check.py` → pyflakes + node --check + pytest (72, hermetic)
· live suite `python run_tests.py` → 42/42 · self‑test 13/13.

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
1. **TST‑6** Frontend interaction tests (beyond the load/zero‑console gate). (P0)
2. **OUT‑1** Agent goal battery — measure real multi‑step success rate. (P1)
3. **STB‑1** Watchdog/supervisor to auto‑restart `server.py` on crash. (P1)

_**P0 Security COMPLETE** ✅ (M43–M48). **P0 Tests:** TST‑1 deep service tests (M49) · TST‑2 hermetic mode (M50) · TST‑3 agent‑loop tests (M51) · TST‑4+5 clean‑venv install + local CI run (M52) — **only TST‑6 left**._

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
| **Agent reliability** | Loop **mechanics now integration‑tested** with a mocked model (TST‑3, M51: dispatch/parse/stop/budget/gating/guards). Real multi‑step success rate with 14B is still **unmeasured** (that's OUT‑1). |
| **Tests are shallow** | Improving: deep per‑service assertions added (TST‑1, M49) + pytest now **hermetic** — 63 pass with network blocked (TST‑2, M50). Still missing: agent‑loop integration tests (TST‑3), CI actually executed (TST‑5), clean‑venv install proof (TST‑4). The live `run_tests.py` (42) still needs the real stack by design. |
| **`screen_if` (conditional screen actions)** | Implemented + unit‑tested **with a mocked screen**; never run against a real screen / real vision matching. |
| **Image/video generation** | Endpoints fire + jobs start; **actual generation success/quality never verified**. |
| **Training pipeline** | The fine‑tune scripts live **outside the repo** in `C:\AI\training` (`learn.ps1`, `train_lora.py`, `harvest_chats.py`). We only orchestrate + parse logs — never verified they produce a good model. |
| **Click‑to‑act** | Best‑effort only — 7B vision grounding imprecise at 4K + Win11 focus rules. Don't rely on it. |
| **STT (Arabic/noisy)** | base/CPU Whisper; weak on Arabic. Size now configurable. |
| **CI** | The CI *commands* now **actually run** locally via `scripts/ci_local.py` (clean‑venv install → gate → PASS, M52). GitHub‑hosted execution still needs a Git remote the owner must create (`act` can't emulate `windows-latest`). |
| **Pinned deps** | **Proven to clean‑install** from a fresh venv (M52, all wheels, no conflicts). Caveat: only *direct* deps are pinned — transitive deps resolve to latest‑compatible at install time (not a full lockfile). |
| **Secrets** | `cloud_api_key` now **encrypted at rest** (SEC‑4, Fernet; key in `.nova_key`); tokens hashed; config.json git‑ignored. (Resolved.) |
| **Background loops** | Swallow exceptions silently (`except: pass`) — a dead loop is invisible except via `/api/health`. |
| **No watchdog** | If `server.py` crashes nothing restarts it; a server restart kills running training/recording (Job Object). |
| **beforeunload text** | Browser shows generic wording + only after interaction (browser limitation, not fixable). |

## In progress 🟦
- _(none active — pick the next from TASKS.md P1)_

See **`TASKS.md`** for the full prioritized, actionable backlog, **`PROJECT_PLAN.md`** for the phase
plan, and **`WORKFLOW.md`** for how we work.
