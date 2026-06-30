# Roadmap

_Living document — the single source of truth for what's done, pending, and broken._
_Last updated: 2026-06-30 (M37 Nova Brain 2.0). History of how each item was built lives in `BUILD_LOG.md`._

> **Planning documents (engineering-maturity hardening):**
> - **`PLAN.md`** — formal phased roadmap (strategy, phases, exit criteria).
> - **`TASKS.md`** — actionable backlog (34 tasks: priority · effort · deps · status).
> - **`PROJECT_PLAN.md`** — milestones, schedule, deliverables, risk register.
>
> This `ROADMAP.md` tracks **feature status**; the files above track the **hardening work**
> (git, pinned deps, vendored assets, tests/CI, exec hardening, cache-busting, perf guards, DB
> migrations, first-run checks, API docs, observability, scheduled backups). Multi-user & RTL
> mirroring are explicitly **out of scope**.

## ✅ Done (shipped & tested)

| Area | Status | Notes |
|---|---|---|
| Core dashboard (SPA + FastAPI + SQLite) | ✅ | 22 pages, WS live updates |
| AI Chat (projects, RAG+citations, file upload, compare, export) | ✅ | suite-covered |
| Agent (full-access, side panel, avatar, real-time log, stop/pause, settings) | ✅ | M21/M23 |
| Browser automation (Playwright, visible browser, open_url, YouTube) | ✅ | M20/M22 |
| **Screen Studio (record / OCR / vision / playback / agent / automation / KB)** | ✅ | **M29 — native mss+imageio capture, qwen2.5-VL** |
| Image generation (SDXL/Flux) wired to backend + Studio UI | ✅ | M26 |
| Video generation (LTX 2B/13B) | ✅ | M19 |
| Local TTS (Piper, AR+EN) + local STT (faster-whisper) | ✅ | M26 |
| Training Studio (progress, ETA, GPU, stop/pause/resume, live log) | ✅ | M24 |
| Continuous learning (RAG→training, learning dashboard) | ✅ | M8 |
| Automation (schedules), Workflows, Webhooks, Notifications | ✅ | incl. screen_record action |
| Knowledge Base (RAG: ingest, semantic search, unified search) | ✅ | |
| Security (hashed tokens, rate limiting, headers, audit, optional HTTPS) | ✅ | M26 |
| Observability (rotating logs, global error handler, /api/logs, UI error toasts) | ✅ | M26 |
| Portability (config.py + config.json, setup.ps1, start.cmd, SETUP.md) | ✅ | M27 |
| Professional icons (Font Awesome) + animations | ✅ | M23 |
| Backup & Restore | ✅ | |
| **Foundation refactor — `nova/` package (core/db, core/events, core/process, services/audit, services/notifications, services/jobs, services/screen)** | ✅ | **M28+M30 — ARCHITECTURE.md** |
| **Bug-report system** (table + API + page, auto-attaches recent logs) | ✅ | M30 |
| **Data safety** (graceful shutdown finalizes recordings; browser unload guard while busy) | ✅ | M30 |
| **Responsive / mobile** (off-canvas sidebar drawer, stacked grids, hidden chrome) | ✅ | M30 |
| **Flagship model chosen** (qwen2.5:14b default @120 tok/s; 32b available as max-intelligence) | ✅ | M30 |
| Tests: self-test 13/13 · live suite 42/42 · 62 real-world scenarios | ✅ | SCENARIOS.md |
| Full Arabic translation (layout fixed, all text + tooltips) | ✅ | M23 |
| **Backend fully modularized** (`nova/` package) | ✅ | **M34–M35 — 21 API routers + 18 services + 4 core; server.py 2400→495 lines (composition root). Injection hooks for run_action/build_briefing/training. ARCHITECTURE.md** |
| Frontend split into ordered modules (core/pages/shell.js) | ✅ | M34 |
| **Nova Brain 2.0** — living 3D neural map (force layout, community colors, search/filter, focus, fullscreen) | ✅ | **M37 — vanilla canvas, fully local; verified via headless render** |
| **Engineering hardening** (git, pinned deps, vendored assets, tests+CI, exec gate, cache-bust, backups, migrations, observability) | ✅ | **M38 — Phases 0–4; see PLAN.md/TASKS.md** |
| **Open WebUI 0.10.1** — upgraded; integration made schema-agnostic (config blob→per-key); custom tools/models preserved | ✅ | **M41 — verified, suite 42/42, rollback retained** |
| **Per-page bespoke UI** (Chat→messaging · Training→progress · Screen→preview · Agent→thinking) | ✅ | **M39 — T-033; focused/minimal; render-verified; fixed agent settings-collapse bug** |
| Model evaluation (9 local models benchmarked; picks chosen) | ✅ | M31 — default qwen2.5:14b |
| **Vibrant / living UI** (multi-accent palette, glass depth, aurora+grid+constellation, parallax, 3D card tilt) | ✅ | **M36 — final cascade CSS layer + parallax/tilt JS; reduced-motion safe; Arabic + responsive intact** |

## 🔜 Remaining (prioritized)

| Priority | Feature | Effort | Notes |
|---|---|---|---|
| P2 | Per-page UI pass | S–M | M36 ships a global theme (palette/glass/background/motion that lift every page). Optional follow-up: bespoke layouts for heavy pages (Dashboard hero, Chat, Training, Screen). |
| P3 | True multi-user accounts | L | users table, per-user scoping, sessions, roles. A data-model program. |
| P3 | RTL mirroring pass | M | **Deferred by design** — user requested layout stay fixed (text-only translation). Revisit only if true RTL mirroring is wanted. |
| 🟡 | On-screen detect + click-to-act (`act_on_screen`/click/type) | M | **Built** (M32): vision-grounding via qwen2.5-VL + pyautogui click/type + agent tool + endpoints. **Best-effort only** — see correction below. |
| 🟡 | Conditional screen-triggered actions ("if X on screen, do Y") | M | recording-on-schedule done; conditional triggers not yet (see "Needs completion"). |

## 🐞 Needs correction (known issues / caveats)

- **Job Object behavior:** training/recording die if the server restarts (correct ownership, but be aware).
- **STT model = base/cpu:** good EN, weaker AR/noisy audio. Upgrade to a larger Whisper for accuracy if needed.
- **Mic & screen capture need an interactive session** (server runs in Session 1 — OK now). Mic over LAN needs HTTPS.
- **Audio in screen recording** is video-only by default (Windows audio-device capture is environment-specific).
- **No HTTPS by default** — opt-in via `config.json` (`https_enabled: true`).
- **Click-to-act is best-effort, not reliable yet.** Two real limits: (1) the 7B vision model's pixel grounding is imprecise at 4K, so located coords can miss; (2) Win11 forbids a background process from stealing foreground focus, so synthetic input may not reach the intended window (the project's own CLAUDE.md documents this). For reliable GUI control, use UI Automation (pywinauto) targeting by control name + AttachThreadInput focus, or a larger grounding model — a future pass.
- **qwen2.5:32b inference is slow here (~5 tok/s)** when the GPU is shared (ComfyUI online + other models resident) — 24 GB leaves little headroom on 32 GB. **qwen2.5:14b @ ~120 tok/s is the default.** Likely VRAM contention and/or a not-yet-Blackwell-optimal llama.cpp build; a future Ollama update may lift 32b throughput. Unload other models / close ComfyUI to give 32b the whole GPU.

## 🚧 Needs completion (partial)

- **Data safety "confirm on exit":** recordings finalize on stop, logs persist, DB is the store, and the Job Object prevents orphans — but a graceful "save & confirm on shutdown" prompt isn't implemented (a headless server has no interactive exit; would be a watchdog/desktop concern).
- **Screen automation acting on content** (e.g., "if X appears, do Y"): recording-on-schedule is done; conditional screen-triggered actions are not yet.

## Process

- Update this file with **every** change (done / remaining / correction / completion).
- Keep `README.md`, `PROJECT_SUMMARY.md`, `BUILD_LOG.md`, `ARCHITECTURE.md`, `SCENARIOS.md` in sync.
- Track hardening work in `TASKS.md` (move status ⬜→🟦→✅); strategy in `PLAN.md`; schedule in `PROJECT_PLAN.md`.
- No feature ships without: `python run_tests.py` green + `pyflakes` clean + `node --check` clean
  (and, from Phase 2, `pytest` green).
