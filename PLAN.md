# Nova / AI Control Center — Hardening & Completion Plan

_Formal phased roadmap derived from the honest project assessment (2026-06-30)._
_Companion files: **`TASKS.md`** (actionable backlog) · **`PROJECT_PLAN.md`** (milestones, schedule, risks) · **`ROADMAP.md`** (live feature status)._

---

## 1. Purpose

The product is feature-rich and (as of M37) cleanly modularized on the backend with a polished,
verified UI. This plan addresses the **engineering-maturity gaps** the assessment surfaced — the
things that make the difference between "an impressive local tool" and "a maintainable, trustworthy
product": version control, reproducibility, offline-truth, security of the command surface, tests,
docs, observability, and a few unfinished features.

## 2. Guiding principles

- **Safety net before features.** Nothing new ships until the work is recoverable (git) and
  reproducible (pinned deps).
- **Make the "fully local" claim literally true** (vendor CDN assets).
- **Every change stays green:** `pytest` + live smoke suite + `pyflakes` + `node --check`.
- **Honest status.** A task is "Done" only when verified, not when written.
- **No scope creep into multi-user** (explicitly out of scope, see §6).

## 3. Phases (strategic)

### Phase 0 — Safety Net & Reproducibility  · **P0** · _exit: recoverable, reproducible, offline-capable_
Put the project under version control, pin and complete dependencies, vendor fonts/icons locally,
and add a first-run prerequisite check.
- **Deliverables:** git repo + `.gitignore` + `LICENSE`; pinned `requirements`; local fonts + Font
  Awesome; `setup`/health check that validates prerequisites.
- **Why first:** months of work currently have **no version control** and the install is **not
  reproducible** — these are the highest-risk gaps.

### Phase 1 — Security & Runtime Hardening  · **P1** · _exit: safe to run, robust under restart_
Harden the arbitrary-command surface, make cache-busting automatic, add scheduled DB backups, a
DB-migration helper, performance guards, and secrets hygiene.
- **Deliverables:** consent-gated exec; server-stamped asset versions; rotating DB snapshots;
  `schema_version` + ordered migrations; "Lite visuals" guard; documented/encrypted secrets.

### Phase 2 — Test Coverage & CI  · **P1** · _exit: regressions caught automatically_
Add real `pytest` unit/integration tests over the now-isolated services and routers, a frontend
load-error gate, and a CI/pre-commit pipeline.
- **Deliverables:** `tests/` suite; Playwright page-load check; pre-commit hook (+ optional GitHub
  Actions if/when pushed to a remote).

### Phase 3 — Documentation & Observability  · **P2** · _exit: maintainable & inspectable_
Curate API docs, document the data model, and deepen observability (metrics retention, error
aggregation, server-health panel).
- **Deliverables:** curated OpenAPI + `DATA_MODEL.md`; metrics history + trends; error aggregation in
  Diagnostics.

### Phase 4 — Feature Completion & Quality  · **P2–P3** · _exit: known gaps closed or explicitly parked_
Finish the remaining features and quality items: conditional screen-triggered actions, structured
training-progress output, STT accuracy, click-to-act reliability spike, and per-page UI passes.

## 4. Cross-cutting workstreams
- **Quality gate** (Phase 2 onward): no merge without green tests + linters.
- **Docs sync** (every phase): keep `ROADMAP.md`, `BUILD_LOG.md`, `ARCHITECTURE.md`, `README.md`, and
  these planning files current.

## 5. Definition of Done (per task)
1. Implemented + self-reviewed. 2. `pytest` green (where applicable). 3. Live smoke suite green.
4. `pyflakes` + `node --check` clean. 5. Docs updated. 6. Committed to git with a clear message.

## 6. Explicitly out of scope (by decision)
- **Multi-user accounts / RBAC** — not wanted; the app stays single-user.
- **RTL mirroring** — Arabic is text-only with fixed layout, by request.
- **Cloud hosting / horizontal scaling** — this is a local, single-machine product.

## 7. Coverage map (assessment item → where it's handled)
| Assessment item | Phase / Task |
|---|---|
| Version control (`git init`) | P0 · T-001..004 |
| Pin dependencies | P0 · T-005 |
| Missing deps (pyautogui, pyperclip) | P0 · T-006 |
| Vendor CDN assets (fonts + Font Awesome) | P0 · T-007..009 |
| First-run checks | P0 · T-010 |
| Harden exec surface | P1 · T-011 |
| Auto cache-busting | P1 · T-012 |
| Scheduled DB backups | P1 · T-013 |
| DB migrations | P1 · T-014 |
| Performance guards | P1 · T-015 |
| Secrets hygiene | P1 · T-016 |
| Real tests (pytest) | P2 · T-017..021 |
| Frontend test gate | P2 · T-022 |
| CI | P2 · T-023 |
| API documentation | P3 · T-024 |
| Data model / ERD | P3 · T-025 |
| Observability depth | P3 · T-026..028 |
| Conditional screen actions | P4 · T-029 |
| Training progress robustness | P4 · T-030 |
| STT accuracy | P4 · T-031 |
| Click-to-act reliability | P4 · T-032 |
| Per-page UI passes | P4 · T-033 |
| 32b throughput (upstream) | P4 · T-034 (track only) |
