# WORKFLOW — how we work on this project (PERMANENT RULE)

> **This is a fixed law. No work happens without following it.**
> The six source‑of‑truth files — `ROADMAP.md`, `TASKS.md`, `BUILD_LOG.md`, `WORKFLOW.md`,
> `PROJECT_PLAN.md`, `STATUS.md` — are **mandatory and permanent**. They are reviewed before work,
> updated during work, and reconciled after work. They are the only reliable record of the project.

## 🔒 CORE PRINCIPLE (permanent) — single‑user · local‑only
See **`docs/PRINCIPLES.md`**. No cloud/telemetry/inbound‑remote/LAN‑control/phone‑control/external‑
access/multi‑user — ever. Localhost‑only. Opt‑in outbound exceptions: Web Search + git source push.

## 🔁 PERMANENT RULE — discovery log
**Every error, missing piece, fragility, or edge case discovered MUST be (1) written into the project
files — `docs/honest-state.md` (the running discovery log) + the relevant `TASKS.md` row — and (2) fixed
or, if deferred, marked 🟧 with the exact reason.** No silent gaps. The honest report is re‑run and
updated every substantial session.

---

## The loop (every coding session)

### 1. BEFORE — orient (always)
1. Read **`STATUS.md`** (what's done / fragile / in progress / next).
2. Read **`TASKS.md`**; pick the **highest‑priority** unblocked task (P0 → P3).
3. Skim **`PROJECT_PLAN.md`** (which phase) and **`ARCHITECTURE.md`** (where the code lives + the
   dependency DAG: `config ← core ← services ← api ← server`; nothing imports `server.py`).
4. Mark the chosen task **🟦 IN PROGRESS** in `TASKS.md` and `STATUS.md`.

### 2. DURING — implement (small, safe steps)
1. Make the change in the right layer (service logic in `nova/services/*`, routes in `nova/api/*`).
2. **Test after each meaningful change** — `python scripts/check.py` (pyflakes + node --check + pytest).
3. If the server changed: restart it and run the live suite `python run_tests.py` (must be 42/42).
4. **If anything visual changed: RENDER IT AND LOOK** (Playwright screenshot) — never claim a UI
   change you haven't seen. Static assets are auto cache‑busted (server stamps `?v=<mtime>`).
5. For anything that runs commands / touches the exec surface: assume it's the biggest risk — gate,
   audit, and test the guard.

### 3. AFTER — reconcile the source of truth (every completed task)
1. `TASKS.md`: flip status ⬜/🟦 → ✅ (or 🟧 FRAGILE with the exact issue). Update deps/rollup.
2. `STATUS.md`: move the item between Done / Fragile / In progress; refresh "Next 3 actions".
3. `BUILD_LOG.md`: append a dated entry — **what** changed, **why**, and **how it was verified**.
4. `ROADMAP.md` / `PROJECT_PLAN.md`: update if a feature area or phase advanced.
5. **Commit** to git with a clear message (the pre‑commit hook re‑runs the quality gate).

### 4. BEFORE CLOSING — final check
- All six files reflect reality. Quality gate green. Working tree committed (`git status` clean).

---

## Quality gate (the bar for "done")
A task is **DONE** only when all of these pass:
1. Implemented + self‑reviewed in the correct layer.
2. `pyflakes` clean · `node --check` clean · `pytest` green (`python scripts/check.py`).
3. Live suite `python run_tests.py` → **42/42**; self‑test 13/13.
4. If visual: render‑verified (zero console errors on the page).
5. The six files updated + committed to git.

Anything that "works but has a known issue" is **🟧 FRAGILE**, not DONE — record the issue in
`STATUS.md` and `TASKS.md`.

## Status vocabulary
✅ DONE · 🟧 FRAGILE (works, known issue) · 🟦 IN PROGRESS · ⬜ TODO · 🚫 EXCLUDED (owner decision)

## Priority order (P0 = highest)
- **P0** Security (command‑execution surface, authentication, HTTPS)
- **P0** Real test coverage (unit + integration + smoke)
- **P1** Outcome verification (does the agent actually complete goals?)
- **P1** Stability (watchdog, error recovery, graceful shutdown)
- **P1** AI Screen Vision (Phase 7 — real‑time capture, mouse/keyboard tracking, continuous VLM loop; SV‑1…7)
- **P2** Documentation (keep these six files current)
- **P2** Feature improvements (voice, click‑to‑act, …)
- **P3** Polish (UI, performance, optimization)

## Hard rules (safety)
- Localhost‑only by default. Never enable LAN + `allow_remote_exec` without explicit intent.
- Treat `/api/exec` and the agent's `run_command` as production‑grade risk even though it's local.
- Back up `webui.db` / `control.db` before any irreversible data/schema change.
- Don't delete/recreate things you didn't create (e.g. the OWUI container) without surfacing it first.
- The training scripts in `C:\AI\training` are an **external dependency** — we orchestrate, not own them.
- **AI Screen Vision (SV‑*) is privacy‑sensitive.** Every capture/track path must be **opt‑in and OFF
  by default**, local‑only, pausable, with an on‑screen indicator, and **non‑persistent** unless the
  user explicitly records. Keyboard tracking gets extra gating (redact near password fields, never log
  to disk). Treat its config like a secret; audit enable/disable.

## Commands cheat‑sheet
```
python preflight.py            # first-run / environment check
python scripts/check.py        # quality gate: pyflakes + node --check + pytest
python run_tests.py            # live smoke suite (needs server + Ollama running) → 42/42
python server.py               # run the control center (http://localhost:8900)
python scripts/ci_local.py     # local CI: clean-venv install + gate (proves the lock installs)
python scripts/agent_eval.py --write-doc   # OUT-1 agent goal battery → docs/agent-baseline.md
python scripts/rag_eval.py --write-doc     # OUT-5 RAG retrieval quality → docs/rag-baseline.md
powershell -File watchdog.ps1 -Once        # watchdog self-check (resolves real python + probes)
```
