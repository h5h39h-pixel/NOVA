# Nova / AI Control Center — Project Plan

_Milestones, schedule, deliverables, and risks for the hardening & completion effort._
_Plan start: **2026-06-30**. Pace assumption: part-time (~2–3 focused hours/day, AI-paired)._
_See `PLAN.md` (strategy) and `TASKS.md` (task detail)._

> ⚠️ **Estimates, not commitments.** Effort is in focused days (1 d ≈ 6 h). The calendar assumes a
> part-time cadence; compress to ~2 weeks if worked full-time. Re-baseline after Phase 0.

> ✅ **STATUS (2026-06-30): Milestones M-A → M-E delivered + T-033 bespoke UI done.** 33/34 tasks done.
> **Monitoring:** T-034 32B throughput (upstream-gated, `docs/32b-throughput.md`) — 🟡.
> All committed to git; quality gate (pyflakes + node + pytest 24 + live 42/42) green;
> redesigned pages render with zero console errors.
> See `TASKS.md` for per-task status and `BUILD_LOG.md` (M39) for the execution record.

---

## 1. Milestones

| # | Milestone | Phase | Exit criteria | Effort |
|---|---|---|---|---|
| **M-A** | **Safety Net** | 0 | Under git; deps pinned + complete; fonts/icons local (offline works); first-run check passes | ~2.5 d |
| **M-B** | **Hardened Runtime** | 1 | Exec consent-gated; auto cache-bust live; scheduled backups; migrations; perf guards | ~3.5 d |
| **M-C** | **Tested & CI** | 2 | pytest suite over core/services/routers; frontend load gate; pre-commit/CI green | ~5 d |
| **M-D** | **Documented & Observable** | 3 | Curated API docs + data model; metrics history; error aggregation | ~3 d |
| **M-E** | **Feature-Complete & Polished** | 4 | Conditional screen actions; robust training progress; STT option; click-to-act decision; per-page UI | ~6–8 d |

**Total:** ~20–22 focused days (excluding upstream-gated 32b tracking).

## 2. Schedule (suggested, part-time — anchored 2026-06-30)

| Week (from 2026-06-30) | Focus | Tasks | Deliverable |
|---|---|---|---|
| **Week 1** | M-A Safety Net | T-001…T-010 | Recoverable, reproducible, offline-capable install |
| **Week 2** | M-B Hardening (1/2) | T-011, T-012, T-013 | Safe exec, auto cache-bust, daily DB backups |
| **Week 3** | M-B (2/2) + start M-C | T-014, T-015, T-016, T-017 | Migrations, perf guards, secrets; test harness stood up |
| **Week 4** | M-C Tests & CI | T-018, T-019, T-020, T-022, T-023, T-021 | Green pytest + frontend gate + pre-commit/CI |
| **Week 5** | M-D Docs & Observability | T-024…T-028 | API docs, data model, metrics history, error aggregation |
| **Week 6+** | M-E Features & polish | T-029…T-033 (T-034 ongoing) | Conditional screen actions, training/STT/UI improvements |

```
Phase 0 ▓▓▓ (Wk1)
Phase 1     ▓▓▓▓▓ (Wk2–3)
Phase 2          ▓▓▓▓▓ (Wk3–4)
Phase 3                ▓▓▓ (Wk5)
Phase 4                   ▓▓▓▓▓▓ (Wk6+)
```

## 3. Deliverables by milestone
- **M-A:** `.git/`, `.gitignore`, `LICENSE`, pinned `requirements.txt` (+ `requirements.in`), `static/fonts/`, `static/vendor/fa/`, prerequisite-check in `/api/selftest` + CLI.
- **M-B:** consent-gated exec + audit, server asset-versioning, `data/backups/` rotation, `schema_version` + migrations, "Lite visuals" setting.
- **M-C:** `tests/` (unit + integration), Playwright load gate, `.pre-commit`/CI config.
- **M-D:** curated `/docs` + `openapi.json`, `DATA_MODEL.md`, metrics-history API + Diagnostics error panel.
- **M-E:** conditional screen-action engine, structured training progress, STT model option, click-to-act decision doc, refreshed Chat/Training/Screen pages.

## 4. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **No git today → data/work loss** | Med | **Critical** | **M-A T-001..004 first**, before any other change |
| Unpinned deps drift / break install | High | High | Pin in T-005; test fresh install in a clean venv |
| Exec surface abused if auth+LAN enabled | Low–Med | **Critical** | T-011 consent gate; never auto-enable on LAN |
| Offline run fails (CDN down) | Med | Med | Vendor assets (T-007..009); verify offline |
| Tests flaky due to live externals (Ollama/ComfyUI) | Med | Med | Mock externals in unit/integration; isolate live suite (T-021) |
| Migrations corrupt DB | Low | High | Idempotent migrations + auto-backup before migrate (T-013→T-014 ordering) |
| Perf regressions from heavy visuals on weak GPUs | Med | Low–Med | Lite-visuals toggle + pause-on-hidden (T-015) |
| Click-to-act stays unreliable | High | Low | Time-boxed spike (T-032); park as best-effort if no win |
| Windows-only lock-in | High | Med (future) | Document; isolate PowerShell calls already done in services |
| Solo-dev bandwidth | High | Med | Strict priority order; P0/P1 before P2/P3; estimates re-baselined after Phase 0 |

## 5. Governance / working agreement
- **Branch per milestone**, small commits, descriptive messages (once git exists).
- **Quality gate** (Definition of Done in `PLAN.md` §5) enforced from Phase 2 via pre-commit.
- **Docs stay in sync** every change: `ROADMAP.md` (status), `BUILD_LOG.md` (history), `TASKS.md`
  (move ⬜→🟦→✅), `ARCHITECTURE.md` (structure).
- **Re-baseline** the schedule after M-A with real measured velocity.

## 6. Tracking
- Source of truth for **status**: `TASKS.md` (update the Status column as work proceeds).
- Source of truth for **feature state**: `ROADMAP.md`.
- Source of truth for **what happened**: `BUILD_LOG.md` (append a milestone entry per phase).
