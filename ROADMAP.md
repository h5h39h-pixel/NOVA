# ROADMAP — Nova / AI Control Center

Complete feature roadmap, phases, and long‑term vision. **Personal single‑user system.**
This file = feature/area status. Granular work lives in `TASKS.md`; process in `WORKFLOW.md`;
phases in `PROJECT_PLAN.md`; live snapshot in `STATUS.md`; history in `BUILD_LOG.md`.

_Last updated: 2026-06-30._ **Update on every session (permanent rule).**

**Status:** ✅ DONE · 🟧 FRAGILE · 🟦 IN PROGRESS · ⬜ TODO · 🚫 EXCLUDED

---

## Vision
A fully‑local, single‑user AI command center for one RTX‑5090 workstation: chat + RAG, an
autonomous agent that can drive the PC, screen capture/understanding, media generation, and
continuous learning — private, offline‑capable, and owned end‑to‑end. The goal now is to make it
**trustworthy** (secure, tested, verified, resilient), not bigger.

## Phases (the campaign — see PROJECT_PLAN.md)
1. **Phase 1 — Security** (P0): lock down the command‑execution surface, auth, HTTPS. 🟦 next
2. **Phase 2 — Real tests** (P0): deep unit/integration + hermetic + working CI.
3. **Phase 3 — Outcome verification** (P1): prove the agent/training/generation actually work.
4. **Phase 4 — Stability** (P1): watchdog, error recovery, job persistence, graceful shutdown.
5. **Phase 5 — Documentation** (P2): keep the six files + repo docs current.
6. **Phase 6 — Features & polish** (P2/P3): click‑to‑act, voice, accessibility, performance.

Foundation phases **0 (Safety Net)**, **modular refactor**, **UI**, and the **OWUI 0.10.1 upgrade**
are ✅ complete (see BUILD_LOG M28–M41).

---

## ✅ Done (shipped & tested)
| Area | Notes |
|---|---|
| Core dashboard (SPA + FastAPI + SQLite), ~25 pages, WS live updates | M5+ |
| AI Chat (projects, RAG+citations, upload, compare, export) | suite‑covered |
| Agent Mode (full‑access, tools, live log, stop/pause, settings) | M21/M23 (reliability: see 🟧 OUT‑1) |
| Browser automation (Playwright visible browser, open_url, YouTube) | M20/M22 |
| Screen Studio (record / OCR / vision / playback / KB) | M29 (mss+imageio, qwen2.5‑VL) |
| Image (SDXL/Flux) + Video (LTX) generation wired to ComfyUI | M19/M26 (success unverified: 🟧 OUT‑3) |
| Local TTS (Piper) + STT (faster‑whisper) | M26 (STT Arabic weak: 🟧 FEA‑2) |
| Training Studio + continuous learning (RAG→training) | M8/M24 (pipeline external: 🟧 OUT‑2) |
| Automation (schedules incl. `screen_if`), Workflows, Webhooks, Notifications | M8/M39 |
| Knowledge Base (RAG ingest, semantic + unified search) | |
| Nova Brain 2.0 — 3D neural map | M37 |
| Vibrant UI + bespoke pages (Chat/Training/Screen/Agent) | M36/M39 |
| Fully local assets (vendored fonts + Font Awesome), auto cache‑busting | M‑A/M‑B |
| Backend modularized (`nova/`: 4 core · 18 services · 21 routers) | M34–M35 |
| git + .gitignore + MIT LICENSE + pinned deps + preflight | M‑A |
| Security baseline (hashed tokens, rate limit, headers, audit, exec LAN gate) | M26/M‑B |
| Observability (`/api/health`, `/api/errors`, metrics history) + DB snapshots + migrations | M‑B/M‑D |
| Tests: pytest (24) + live suite (42) + frontend gate + pre‑commit + CI(written) | M‑C |
| Open WebUI 0.10.1 (integration schema‑agnostic; custom tools/models preserved) | M41 |
| Full Arabic translation (text‑only, fixed layout) | M23 |
| Close‑tab confirmation ("Nova is still running") | M40 |

## 🔜 Remaining (by priority — details in TASKS.md)
| Priority | Area | Status |
|---|---|---|
| **P0** | Security: exec confirm‑guard, denylist, CSP, key encryption, HTTPS turnkey, audit | ⬜ (SEC‑1…6) |
| **P0** | Real test coverage: deep units, hermetic mode, agent tests, clean install, run CI | ⬜/🟧 (TST‑1…6) |
| **P1** | Outcome verification: agent battery, training, generation, `screen_if`, RAG quality | ⬜/🟧 (OUT‑1…5) |
| **P1** | Stability: watchdog, job persistence, loop error recovery, media backup, WAL | ⬜/🟧 (STB‑1…5) |
| **P2** | Docs upkeep + README/SETUP refresh + training‑pipeline docs | 🟦/⬜ (DOC‑1…3) |
| **P2** | Features: click‑to‑act reliability, STT Arabic, voice, screen_if UI | 🟧/⬜ (FEA‑1…4) |
| **P3** | Polish: perf budget, accessibility, mobile testing, 32B re‑bench | ⬜/🟧 (POL‑1…4) |

## 🟧 Known fragile / caveats (see STATUS.md for the live list)
- Command‑exec surface unguarded on localhost (by design, but no confirm/kill‑switch).
- Tests shallow + environment‑coupled; CI never executed.
- Agent success rate, training output, media generation — **unverified**.
- `screen_if`, click‑to‑act — best‑effort / mocked‑only.
- No watchdog; background loops swallow errors; secrets plaintext; deps not clean‑installed.

## 🚫 Excluded (owner decision — never build)
- Multi‑user / accounts / roles / RBAC.
- RTL mirroring.
- Cloud hosting / horizontal scaling.
