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
| T-017 | `pytest` harness + fixtures: temp SQLite, monkeypatched Ollama/HTTP, FastAPI `TestClient` | P1 | 4h | T-005 | ⬜ |
| T-018 | Unit tests — core (`db`, `events`, `process`/`ps_args`/`_q`, `http`) | P1 | 4h | T-017 | ⬜ |
| T-019 | Unit tests — services (`chat`, `kb`, `training`, `schedules`, `settings`, `backup`, `insights`, `ollama`, `metrics`, `files`) | P1 | 12h | T-017 | ⬜ |
| T-020 | Integration tests — routers via `TestClient` (no live server, mocked externals) | P1 | 8h | T-017 | ⬜ |
| T-021 | Extend/keep live smoke suite `run_tests.py`; tag as "live/e2e" | P2 | 2h | — | ⬜ |
| T-022 | Frontend gate: Playwright load each route, assert **zero console errors** + key elements present | P2 | 4h | — | ⬜ |
| T-023 | CI: pre-commit hook (pyflakes + `node --check` + `pytest`); optional GitHub Actions workflow when a remote exists | P1 | 4h | T-017,018,019,020 | ⬜ |

## Phase 3 — Documentation & Observability (P2)

| ID | Task | Pri | Effort | Deps | Status |
|---|---|---|---|---|---|
| T-024 | Curated API docs: FastAPI tags/summaries per router; polish `/docs`; export `openapi.json` | P2 | 4h | — | ⬜ |
| T-025 | `DATA_MODEL.md`: tables, columns, relationships (ERD-style) | P2 | 3h | — | ⬜ |
| T-026 | Metrics history retention: ring-buffer/table + trend API (CPU/GPU/VRAM over time) | P2 | 5h | T-014 | ⬜ |
| T-027 | Error aggregation: count + last-seen per error signature from logs; surface in Diagnostics | P2 | 5h | — | ⬜ |
| T-028 | Server self-health panel: uptime, background-loop liveness, job queue depth | P3 | 3h | T-026 | ⬜ |

## Phase 4 — Feature Completion & Quality (P2–P3)

| ID | Task | Pri | Effort | Deps | Status |
|---|---|---|---|---|---|
| T-029 | Conditional screen-triggered actions ("if X on screen → do Y"): periodic capture + vision/OCR match → action | P2 | 1–2d | — | ⬜ |
| T-030 | Training progress robustness: emit structured `[PROGRESS] {json}` from training scripts; parse JSON instead of fragile regex | P2 | 6h | — | ⬜ |
| T-031 | STT accuracy: optional larger Whisper model + language hint; expose in Settings | P3 | 4h | T-005 | ⬜ |
| T-032 | Click-to-act reliability spike: evaluate `pywinauto`/UI Automation + AttachThreadInput, or a stronger grounding model; decide fix-or-park | P3 | 1–2d | T-006 | ⬜ |
| T-033 | Per-page UI passes: bespoke layouts for Chat, Training, Screen (beyond the global theme) | P3 | 2–3d | — | ⬜ |
| T-034 | Track 32b throughput: monitor Ollama/llama.cpp Blackwell updates; re-benchmark on upgrade (**upstream-gated, no code**) | P3 | ongoing | — | ⬜ |

## Out of scope (by decision)
| Item | Reason |
|---|---|
| Multi-user accounts / RBAC | Not wanted — app stays single-user |
| RTL mirroring | Arabic is text-only, fixed layout, by request |
| Cloud hosting / scaling | Local single-machine product |

---

### Rollup
- **Total tasks:** 34 (P0: 6 · P1: 13 · P2: 10 · P3: 5) · **Done:** 0
- **Estimated effort:** ~**18–22 focused days** (≈ 110–130 h), excluding upstream-gated T-034.
- **Critical path:** T-001 → T-004 → (everything). Tests (T-017) unlock T-018/019/020/023.
