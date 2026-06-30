# STATUS — Nova / AI Control Center

**Read this first.** Live snapshot of what's done, what's fragile, and what's next.
Personal single‑user system (not a product). Update this file on **every** work session.

_Last updated: 2026-06-30_

**Health gate (must stay green):** `python scripts/check.py` → pyflakes + node --check + pytest (~84 hermetic + 4 live frontend)
· live suite `python run_tests.py` → 42/42 · self‑test 13/13 · local CI `python scripts/ci_local.py` · agent baseline `python scripts/agent_eval.py`.

**Status legend:** ✅ DONE · 🟧 FRAGILE (works but has a known issue) · 🟦 IN PROGRESS · ⬜ TODO · 🚫 EXCLUDED (owner decision)

---

## Where we are right now (honest)
The original roadmap (P0→P3 + Phases 7/8) is **built and smoke‑verified**, and the architecture / security
baseline / test scaffolding / feature breadth are genuinely strong. **But** a candid self‑audit
(`docs/honest-state.md`) found the real weakness is **depth of real‑world verification** — the
screen‑control and agent‑reliability features are powerful, **under‑guarded, and proven mostly at the
unit/smoke level**, not in sustained real use. **Most important gap: agent GUI control has NO per‑action
confirmation and no kill‑switch** (HON‑1), and there's **no prompt‑injection defense** for the
web‑augmented agent (HON‑10). Treat this as a **sharp tool, not a finished appliance.** The true backlog
is **HON‑1…11** in `TASKS.md`.

## 🚫 Explicitly excluded (do not build)
- **Multi‑user / accounts / roles / RBAC** — this is a personal single‑user system.
- **RTL mirroring** — Arabic stays text‑only on the fixed LTR layout.
- **Cloud hosting / horizontal scaling** — local single‑machine only.

## Next 3 actions (highest priority) — from the honest self‑audit
1. **HON‑1** Confirmation/guard + global panic stop for agent GUI control (mouse/keyboard/`control`/
   `act_on_screen` are unguarded on localhost). **Top safety priority.**
2. **HON‑10** Prompt‑injection defense for the web‑augmented agent (it holds PC‑control tools while
   reading untrusted web text).
3. **HON‑2 / HON‑3 / HON‑7** Real GUI integration test · coverage measurement · honest larger eval
   batteries (replace the toy OUT‑1/OUT‑5 smoke tests).

_Original roadmap shipped & smoke‑verified (P0/P1/P2/P3 + Phases 7/8). **The honest backlog is HON‑1…11**
(`TASKS.md` top + `docs/honest-state.md`). ✅ here means "built + verified once," not "battle‑tested."_

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
- **Frontend refactored (HON‑11, M78/M79):** `pages.js` (1440)→4 modules · `app.css` (1039)→4 cascade files · `server.py` toolkit routes → `nova/api/toolkit.py`. Behavior‑preserving (byte‑identical), render‑verified. New map: `docs/frontend-structure.md`.

## Fragile — works but needs improvement 🟧
| Item | The issue |
|---|---|
| 🔴 **Agent GUI control is UNGUARDED** (HON‑1) | Mouse/keyboard/`control`/`act_on_screen` are gated only by `exec_allowed()` (always true on localhost) with **no per‑action confirmation and no kill‑switch**. A Full‑Access agent can click/type/delete anywhere on the PC unsupervised. **Highest‑priority risk.** |
| 🔴 **No prompt‑injection defense** (HON‑10) | The agent reads untrusted web text (Web Search / browse) **while holding PC‑control tools**. A malicious page could try to steer it. No mitigation today. |
| 🟠 **Verification is smoke‑deep** (HON‑2/3/6/7) | Most ✅ are "verified once," not battle‑tested: no real GUI‑drive integration test, no coverage number, the live stream was never watched streaming, no full Web‑Search chat turn run, OUT‑1/OUT‑5 are toy batteries. |
| **Command‑exec surface** | Hardened (P0 Security complete): confirm‑guard (SEC‑1) + centralized denylist (SEC‑2) + strict CSP/headers (SEC‑3) + at‑rest key encryption (SEC‑4) + HTTPS turnkey (SEC‑5) + call‑site audit incl. the `screen lang` injection fix (SEC‑6). Residual by design: localhost exec is unrestricted (the product's purpose) — gated on LAN. No global kill‑switch (HON‑1). |
| **Agent reliability** | Loop mechanics integration‑tested (TST‑3). OUT‑1 baseline is **5/5 on a tiny 5‑goal SAFE battery** — a smoke test, **not** a reliability measure. Real success on hard/ambiguous/multi‑app goals is **unknown** (HON‑7). |
| **Tests** | **P0 Tests complete** (M49–M53): deep per‑service assertions, **hermetic** pytest (network‑blocked), agent‑loop integration tests, clean‑venv install proof + local CI runner, and live frontend interaction tests. Suite ≈ 88 hermetic + 4 live. **Gaps:** no coverage measurement (HON‑3), no real GUI‑drive integration test (HON‑2), no soak/concurrency test (HON‑5); eval batteries are toy‑sized (HON‑7). |
| **`screen_if` (conditional screen actions)** | Verified on the **real** screen (OUT‑4, M75: OCR'd 5024 chars, matched a real word → fired) + exposed in the Automation UI (FEA‑4). Vision‑mode matching (VLM instead of OCR) still lightly tested. |
| **Image/video generation** | **Image verified (OUT‑3, M67):** SDXL produced a correct 1024×1024 image in 9.1s via the live API+ComfyUI (visually confirmed; `scripts/gen_eval.py`). Video (LTX) uses the same path but is not yet auto‑verified (slower). |
| **Training pipeline** | The fine‑tune scripts live **outside the repo** in `C:\AI\training` (`learn.ps1`, `train_lora.py`, `harvest_chats.py`). We only orchestrate + parse logs — never verified they produce a good model. |
| **Click‑to‑act** | **Improved (FEA‑1, M70):** `act_on_screen` tries precise UI‑Automation element detection first (exact center) → vision only as fallback. Reliable where apps expose UIA names; vision fallback still imprecise at 4K for custom‑drawn UIs. |
| **STT (Arabic/noisy)** | **Improved (FEA‑2, M73):** runs on **GPU (CUDA/float16)** with CPU fallback; default `small` (good Arabic), up to `large-v3` in Settings. GPU path verified. |
| **CI** | The CI *commands* now **actually run** locally via `scripts/ci_local.py` (clean‑venv install → gate → PASS, M52). GitHub‑hosted execution still needs a Git remote the owner must create (`act` can't emulate `windows-latest`). |
| **Pinned deps** | **Proven to clean‑install** from a fresh venv (M52, all wheels, no conflicts). Caveat: only *direct* deps are pinned — transitive deps resolve to latest‑compatible at install time (not a full lockfile). |
| **Secrets** | `cloud_api_key` now **encrypted at rest** (SEC‑4, Fernet; key in `.nova_key`); tokens hashed; config.json git‑ignored. (Resolved.) |
| **Background loops** | **Fixed (STB‑3, M56):** metrics/status/scheduler/backup loops now `record_error(...)` → visible in `/api/errors` + Diagnostics (deduped). They still recover next tick rather than crash. |
| **Watchdog** | **Fixed (STB‑1, M55):** `watchdog.ps1` resolves a real python (was the WindowsApps stub → restarts silently failed), logs, fail‑threshold. |
| **Jobs across restart** | **Improved (STB‑2, M66):** jobs persist to a `jobs` table; on startup, ones left running are marked **interrupted** + the user is notified (no silent loss). A killed training/recording still can't auto‑resume (Job Object terminates children) — surfaced, not resumed. |
| **beforeunload text** | Browser shows generic wording + only after interaction (browser limitation, not fixable). |

## 🆕 Perception & Control (Phase 8, P1) — in progress
Owner request: read & understand anything (OCR+VLM), full window‑layout awareness, UI element detection,
and precise mouse/keyboard control — as agent tools, chat commands, and APIs. **COMPLETE ✅** (M68
PC‑1 + M69 PC‑2…6): unified **Read & Understand** (`/api/understand`, agent `understand`, auto‑enriched
image uploads); **window/screen awareness** (DPI‑aware — true 4K), **element detection** (`uiautomation`),
**precise mouse/keyboard control** (`/api/control/*`, agent `control`, chat commands like "where am i" /
"move mouse to X,Y" / "read this"). Live‑verified. Full spec: `docs/perception-control.md`.

## 🆕 Chat interface improvements (CHAT, P1) — ✅ shipped M62
DeepThink toggle (step‑by‑step reasoning), Web Search toggle (live DuckDuckGo via `ddgs`, cited;
opt‑in/online), and an explicit microphone **⏹ Stop** control. Render‑verified; live suite 42/42.
New dependency: `ddgs` (pinned). Tracked as CHAT‑1…3 in `TASKS.md`.

## 🆕 New core feature — AI Screen Vision (Phase 7, P1)
Added 2026‑06‑30 by owner request. Real‑time screen stream + mouse/keyboard tracking + a continuous
AI vision loop, fused into a live "see‑what‑I‑see & act" session — builds on the existing Screen
Studio. **Privacy‑first:** opt‑in, local‑only, non‑persistent by default. Tracked as **SV‑1…7** in
`TASKS.md`; design in `PROJECT_PLAN.md` Phase 7. **Status: largely shipped** — backend `/api/vision/*`
(M61) + the **"AI Screen Vision" Live page** (`#/live`, M63: live stream, mouse overlay, focused‑window
context, on‑demand describe, privacy toggles, FPS slider; render‑verified). SV‑1/3/5/6/7 ✅; SV‑2
(continuous narration) + SV‑4 (full keystroke capture) intentionally deferred — see TASKS rollup.

## In progress 🟦
- _(none active — pick the next from TASKS.md P1: SV‑1 or STB‑2)_

See **`TASKS.md`** for the full prioritized, actionable backlog, **`PROJECT_PLAN.md`** for the phase
plan, and **`WORKFLOW.md`** for how we work.
