# Nova / AI Control Center — Task Backlog

_Actionable breakdown of the hardening & completion plan (`PLAN.md`). Updated 2026-06-30._

**Legend**
- **Priority:** P0 (do first / blocking) · P1 (important) · P2 (valuable) · P3 (nice-to-have)
- **Effort:** rough solo-dev-with-AI estimate. `h` = hours, `d` = ~6 focused hours.
- **Status:** ⬜ Pending · 🟦 In Progress · ✅ Done · ⛔ Blocked · ❎ Won't do
- **Deps:** task IDs that must complete first.

---

## Phase 0 — Safety Net & Reproducibility (P0)

| ID | Task | Pri | Effort | Deps | Status |
|---|---|---|---|---|---|
| T-001 | `git init` + `main` branch; identity configured | P0 | 0.5h | — | ✅ |
| T-002 | Add `.gitignore` (data/db/logs/venv/node_modules/secrets/`config.json`) | P0 | 0.5h | T-001 | ✅ |
| T-003 | Add `LICENSE` — **MIT chosen** (permissive default; change anytime) | P0 | 0.25h | T-001 | ✅ |
| T-004 | Initial commit (77 files; verified no secrets/data/caches; tree clean) | P0 | 0.5h | T-001,002 | ✅ |
| T-005 | Pin Python deps → `requirements.txt` (exact `==`) + `requirements.in` (ranges) | P0 | 1h | — | ✅ |
| T-006 | Add `pyautogui` + `pyperclip` to manifest (already installed; imports verified) | P0 | 0.5h | T-005 | ✅ |
| T-007 | Self-host fonts (Inter, JetBrains Mono, Orbitron `.woff2`) → `static/fonts/` + `fonts.css` | P1 | 2h | — | ✅ |
| T-008 | Vendor Font Awesome 6.5.2 (css + webfonts) → `static/vendor/fa/` | P1 | 2h | — | ✅ |
| T-009 | Drop all CDN `<link>`s → local assets; **verified offline** (0 external requests, 0 console errors, render identical) | P1 | 1h | T-007,008 | ✅ |
| T-010 | First-run prerequisite check `preflight.py` (python, deps, ffmpeg, Ollama+models, services) — 26 checks, actionable report | P1 | 4h | T-005,006 | ✅ |

## Phase 1 — Security & Runtime Hardening (P1)

| ID | Task | Pri | Effort | Deps | Status |
|---|---|---|---|---|---|
| T-011 | Exec surface gated: `/api/exec` + agent `run_command` require `allow_remote_exec` when exposed on LAN (always allowed on localhost); audited; `exec_allowed()` in settings service | P0 | 6h | T-004 | ✅ |
| T-012 | Auto cache-busting: `/` handler stamps `?v=<asset-mtime>` into index.html; manual bumps gone | P1 | 3h | — | ✅ |
| T-013 | Scheduled DB backups: daily SQLite online snapshot → `data/backups/` (rotate 14) + `/api/backup/snapshot[s]`; verified | P1 | 4h | — | ✅ |
| T-014 | DB migration framework: `schema_version` + ordered idempotent `run_migrations()` on startup | P1 | 5h | — | ✅ |
| T-015 | Performance guards: "Lite visuals" toggle (Settings), pause particle + Brain loops on hidden tab, skip tilt on lite/touch, DPR capped | P1 | 4h | — | ✅ |
| T-016 | Secrets hygiene: `config.json` git-ignored; `SECURITY.md` documents model + exec surface + secrets; at-rest key encryption noted as follow-up | P2 | 3h | T-002 | ✅ |

## Phase 2 — Test Coverage & CI (P1)

| ID | Task | Pri | Effort | Deps | Status |
|---|---|---|---|---|---|
| T-017 | `pytest` harness + fixtures (`tests/conftest.py`): temp SQLite, TestClient, mocked externals | P1 | 4h | T-005 | ✅ |
| T-018 | Unit tests — core (settings/history/schema_version, `ps_args`/`_q`, events) `test_core.py` | P1 | 4h | T-017 | ✅ |
| T-019 | Unit tests — services (chat, settings, training, ollama, kb, backup, schedules) `test_services.py` | P1 | 12h | T-017 | ✅ |
| T-020 | Integration tests — routers via `TestClient` `test_api.py` (settings/history/notifs/audit/bug CRUD/conv CRUD/selftest/cache-bust) | P1 | 8h | T-017 | ✅ |
| T-021 | Live smoke suite `run_tests.py` retained (42 checks) — complements pytest | P2 | 2h | — | ✅ |
| T-022 | Frontend gate `test_frontend.py`: Playwright loads 11 routes, asserts **zero console errors**; auto-skips w/o server | P2 | 4h | — | ✅ |
| T-023 | CI: `scripts/check.py` (pyflakes+node+pytest) · `.githooks/pre-commit` (active) · `.github/workflows/ci.yml` (windows) · `requirements-dev.txt` | P1 | 4h | T-017..020 | ✅ |

## Phase 3 — Documentation & Observability (P2)

| ID | Task | Pri | Effort | Deps | Status |
|---|---|---|---|---|---|
| T-024 | API docs: router `tags` group `/docs` by domain; `scripts/export_openapi.py` → `docs/openapi.json` (99 paths) | P2 | 4h | — | ✅ |
| T-025 | `DATA_MODEL.md`: all tables, columns, relationships | P2 | 3h | — | ✅ |
| T-026 | Metrics history: `metrics_history` table + `record_history` (~30s, last ~2880) + `/api/metrics/history` | P2 | 5h | T-014 | ✅ |
| T-027 | Error aggregation: `nova/core/errors.py` (bounded/deduped) hooked into middleware; `/api/errors` + Diagnostics panel | P2 | 5h | — | ✅ |
| T-028 | Server health: `/api/health` (uptime, loop liveness, jobs, ws clients, errors) + Diagnostics panel | P3 | 3h | T-026 | ✅ |

## Phase 4 — Feature Completion & Quality (P2–P3)

| ID | Task | Pri | Effort | Deps | Status |
|---|---|---|---|---|---|
| T-029 | Conditional screen actions: `screen_if` automation action (match text on screen → run `then_action`); unit-tested | P2 | 1–2d | — | ✅ |
| T-030 | Training progress: parser prefers structured `[PROGRESS] {json}` → key=value → tqdm; unit-tested | P2 | 6h | — | ✅ |
| T-031 | STT accuracy: `stt_model` setting (tiny…large-v3), hot-swap in `get_whisper`, lang hint | P3 | 4h | T-005 | ✅ |
| T-032 | Click-to-act spike: `docs/click-to-act.md` evaluates UIA(pywinauto) vs grounding → **decision: park best-effort, hybrid plan documented** | P3 | 1–2d | T-006 | ✅ |
| T-033 | Per-page bespoke UI (Chat→messaging app w/ glass composer · Training→progress/control hero · Screen→preview/record · Agent→thinking/interaction + **fixed settings-collapse bug**). Each verified by render; focused/minimal per guidance; suite green | P3 | 2–3d | — | ✅ |
| T-034 | 32b throughput — baseline + watch-list + re-benchmark steps in `docs/32b-throughput.md` (**upstream-gated, no code**) | P3 | ongoing | — | 🟡 Monitoring |

## Out of scope (by decision)
| Item | Reason |
|---|---|
| Multi-user accounts / RBAC | Not wanted — app stays single-user |
| RTL mirroring | Arabic is text-only, fixed layout, by request |
| Cloud hosting / scaling | Local single-machine product |

---

### Rollup
- **Total tasks:** 34 · **Done: 33 ✅** · **Monitoring: 1 🟡** (T-034 upstream-gated).
- **Phases 0–5 delivered** (M-A…M-E hardening + T-033 bespoke UI). Each step committed to git; quality gate green throughout.
- **Excluded by decision:** multi-user/RBAC, RTL mirroring.
- **Verification:** `python scripts/check.py` → pyflakes + node --check + **pytest 24** ; live suite **42/42** ; self-test **13/13** ; all redesigned pages render with **zero console errors**.
