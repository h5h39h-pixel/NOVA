# Nova / AI Control Center — project rules (auto-loaded)

**Personal, single-user system. No multi-user support, ever.**

## PERMANENT RULE — the six source-of-truth files
Before, during, and after EVERY coding session you MUST review and update these:
`STATUS.md` · `ROADMAP.md` · `TASKS.md` · `PROJECT_PLAN.md` · `BUILD_LOG.md` · `WORKFLOW.md`.

**Start every session by reading `STATUS.md` then `WORKFLOW.md`.** Follow `WORKFLOW.md` exactly:
orient → pick the highest-priority unblocked task (P0→P3) → implement in small steps → test after
each → render any visual change → mark status → append a dated `BUILD_LOG.md` entry → commit.

## ⚠ Honest state (read `docs/honest-state.md`)
The original roadmap is shipped & **smoke‑verified**, NOT battle‑tested. **Real remaining work = HON‑1…11**
in TASKS.md, top priority:
- **HON‑1:** agent GUI control (mouse/keyboard/`control`/`act_on_screen`) has **no confirmation and no
  kill‑switch** — add a guard before adding more capability.
- **HON‑10:** no prompt‑injection defense for the web‑augmented agent.
- Treat ✅ as "verified once." Re‑verify before relying on anything unattended. Eval scripts are the
  regression guardrails — run them after model/dep/prompt changes.

## Priority order (P0 highest)
P0 Security (command-exec surface, auth, HTTPS) · P0 Real tests · P1 Outcome verification ·
P1 Stability · P2 Docs · P2 Features · P3 Polish.

## Quality gate (definition of done)
`python scripts/check.py` (pyflakes + node --check + pytest) green · `python run_tests.py` 42/42 ·
self-test 13/13 · visual changes render-verified · the six files updated + committed.

## Key facts
- Layered DAG: `config ← core ← services ← api ← server`; nothing imports `server.py`.
- Framework-free SPA (`static/js/{core,pages,shell}.js`); auto cache-busting (server stamps `?v=<mtime>`).
- Treat `/api/exec` + agent `run_command` as production-grade risk (it controls the PC).
- Training scripts in `C:\AI\training` are an external dependency (we orchestrate, not own).
- Open WebUI runs as a Docker container; our integration is schema-agnostic.
- Chat has DeepThink + Web Search toggles (`ddgs` dep, DuckDuckGo, opt-in/online) — spec in
  `docs/chat-deepthink-websearch.md`. AI Screen Vision (Phase 7) lives at `#/live` + `nova/services/
  screen_vision.py` + `/api/vision/*` (all privacy-gated, opt-in).
- Read & Understand: `nova/services/understand.py` + `/api/understand` + agent `understand` tool.
  Perception & Control (Phase 8): `nova/services/control.py` + `/api/control/*` + agent
  `screen_awareness`/`find_element`/`control` + chat commands ("where am i", "move mouse to X,Y",
  "read this"); `uiautomation` dep; mutating control is `exec_allowed()`-gated + audited. Spec:
  `docs/perception-control.md`.
- New runtime deps must be pinned in `requirements.txt` AND added to `requirements.in`, then verified
  with `python scripts/ci_local.py` (clean-venv install).
- Excluded forever: multi-user/RBAC, RTL mirroring, cloud/scaling.
