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
| T-001 | `git init` + choose default branch; do **not** commit secrets/data yet | P0 | 0.5h | — | ⬜ |
| T-002 | Add `.gitignore` (`data/`, `__pycache__/`, `*.db`, `*.log`, `data/logs/`, `data/certs/`, `data/uploads/`, `.venv/`, `node_modules/`, model dirs, `config.json` if it holds secrets) | P0 | 0.5h | T-001 | ⬜ |
| T-003 | Add `LICENSE` (**decision needed:** MIT / Apache-2.0 / proprietary) | P0 | 0.25h | T-001 | ⬜ |
| T-004 | Initial commit of full codebase; verify `git status` clean | P0 | 0.5h | T-001,002 | ⬜ |
| T-005 | Pin Python deps: capture exact working versions → `requirements.txt` (keep `requirements.in` for ranges); document `pip install -r` | P0 | 1h | — | ⬜ |
| T-006 | Add missing runtime deps used by click-to-act: `pyautogui`, `pyperclip` (verify imports) | P0 | 0.5h | T-005 | ⬜ |
| T-007 | Vendor fonts locally: download Inter, JetBrains Mono, Orbitron `.woff2`; add `@font-face` in `app.css`; drop into `static/fonts/` | P1 | 2h | — | ⬜ |
| T-008 | Vendor Font Awesome locally (CSS + webfonts under `static/vendor/fa/`); subset if size matters | P1 | 2h | — | ⬜ |
| T-009 | Remove CDN `<link>`s from `index.html`; point to local assets; **verify offline render** (DevTools offline) | P1 | 1h | T-007,008 | ⬜ |
| T-010 | First-run prerequisite check (`/api/selftest` extension + CLI): Ollama reachable, required models present, optional deps importable, `ffmpeg` present; clear actionable report | P1 | 4h | T-005,006 | ⬜ |

## Phase 1 — Security & Runtime Hardening (P1)

| ID | Task | Pri | Effort | Deps | Status |
|---|---|---|---|---|---|
| T-011 | Harden exec surface: gate `/api/exec` + agent `run_command` behind explicit per-session "danger mode"; stronger allow/deny rules; full audit; **never** implicitly available when auth+LAN enabled | P0 | 6h | T-004 | ⬜ |
| T-012 | Auto cache-busting: server stamps asset URLs with file mtime/hash (inject into served `index.html`); remove manual `?v=N` | P1 | 3h | — | ⬜ |
| T-013 | Scheduled DB backups: daily snapshot of `control.db` → `data/backups/` with rotation/retention; surfaced in Settings | P1 | 4h | — | ⬜ |
| T-014 | DB migration helper: `schema_version` table + ordered, idempotent migrations; run on startup | P1 | 5h | — | ⬜ |
| T-015 | Performance guards: pause particle/Brain render loops when tab hidden or page inactive; "Lite visuals" toggle in Settings; cap DPR; honor existing reduced-motion | P1 | 4h | — | ⬜ |
| T-016 | Secrets hygiene: gitignore `config.json` if it holds secrets; document plaintext risk; optional at-rest encryption for `cloud_api_key` | P2 | 3h | T-002 | ⬜ |

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
