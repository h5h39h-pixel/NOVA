# Nova / AI Control Center — project rules (auto-loaded)

**Personal, single-user system. No multi-user support, ever.**

## PERMANENT RULE — the six source-of-truth files
Before, during, and after EVERY coding session you MUST review and update these:
`STATUS.md` · `ROADMAP.md` · `TASKS.md` · `PROJECT_PLAN.md` · `BUILD_LOG.md` · `WORKFLOW.md`.

**Start every session by reading `STATUS.md` then `WORKFLOW.md`.** Follow `WORKFLOW.md` exactly:
orient → pick the highest-priority unblocked task (P0→P3) → implement in small steps → test after
each → render any visual change → mark status → append a dated `BUILD_LOG.md` entry → commit.

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
- Excluded forever: multi-user/RBAC, RTL mirroring, cloud/scaling.
