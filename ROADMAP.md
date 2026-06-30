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
1. **Phase 1 — Security** (P0): lock down the command‑execution surface, auth, HTTPS. ✅ done (M43–M48)
2. **Phase 2 — Real tests** (P0): deep unit/integration + hermetic + working CI. ✅ done (M49–M53)
3. **Phase 3 — Outcome verification** (P1): prove the agent/training/generation actually work. 🟦 in progress (OUT‑1 ✅, OUT‑5 ✅)
4. **Phase 4 — Stability** (P1): watchdog, error recovery, job persistence, graceful shutdown. 🟦 in progress (STB‑1/3/4/5 ✅)
5. **Phase 5 — Documentation** (P2): keep the six files + repo docs current.
6. **Phase 6 — Features & polish** (P2/P3): click‑to‑act, voice, accessibility, performance.
7. **Phase 7 — AI Screen Vision** (P1): real‑time screen streaming, mouse/keyboard tracking, and a
   continuous AI vision loop so the AI sees exactly what the user sees and can act on it. 🟦 largely shipped (SV‑1…7)
8. **Phase 8 — Perception & Control** (P1): read & understand anything (OCR+VLM for files/images/screen),
   full window‑layout awareness (active window, all windows, measurements, DPI), UI element detection, and
   precise mouse/keyboard control — as agent tools, chat commands, and APIs. ✅ shipped (PC‑1…6)
9. **Phase 9 — Hardening v2 (honest gaps)** (P0/P1): close the real gaps from the self‑audit — **guard +
   kill‑switch for agent GUI control (HON‑1)**, **prompt‑injection defense (HON‑10)**, real GUI
   integration test, coverage, honest eval batteries, persistent observability, soak/concurrency, real
   lockfile + CI. 🟦 in progress (HON‑11 ✅ refactor done; HON‑12 found). See `docs/honest-state.md`.

**Maintainability (HON‑11, done):** the two frontend monoliths were split — `pages.js` (1440)→4 JS
modules and `app.css` (1039)→4 cascade files — and `server.py` toolkit routes moved to `nova/api/`.
Behavior‑preserving + render‑verified. New structure map: `docs/frontend-structure.md`.

Foundation phases **0 (Safety Net)**, **modular refactor**, **UI**, and the **OWUI 0.10.1 upgrade**
are ✅ complete (see BUILD_LOG M28–M41).

---

## ✅ Done (shipped & tested)
| Area | Notes |
|---|---|
| Core dashboard (SPA + FastAPI + SQLite), ~25 pages, WS live updates | M5+ |
| AI Chat (projects, RAG+citations, upload, compare, export, **DeepThink**, **Web Search**, voice in/out) | suite‑covered; chat UX M62 |
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
| **P1** | Stability: watchdog, job persistence, loop error recovery, media backup, WAL | 🟦 STB‑1/3/4/5 ✅; STB‑2 ⬜ |
| **P1** | **AI Screen Vision** (Phase 7): real‑time capture, mouse/keyboard tracking, continuous AI vision loop, live "see‑what‑I‑see" + act | ⬜ **NEW** (SV‑1…7) |
| **P2** | Docs upkeep + README/SETUP refresh + training‑pipeline docs | 🟦/⬜ (DOC‑1…3) |
| **P2** | Features: click‑to‑act reliability, STT Arabic, voice, screen_if UI | 🟧/⬜ (FEA‑1…4) |
| **P3** | Polish: perf budget, accessibility, mobile testing, 32B re‑bench | ⬜/🟧 (POL‑1…4) |

## 🆕 Core feature — AI Screen Vision (Phase 7, P1)
Real‑time perception + control so the AI sees exactly what the user sees and can act on it. Builds on
the existing Screen Studio (capture / OCR / `describe_screen` / `act_on_screen` / recording) rather
than replacing it. Scope:
- **Live screen stream** to the dashboard (throttled WebSocket/MJPEG frames) — a real‑time preview.
- **Continuous AI vision loop** — periodically feed frames to qwen2.5‑VL and stream a running
  understanding ("narrate / watch my screen"); on‑demand Q&A about the live screen.
- **Mouse tracking** — global cursor position + clicks, streamed to the UI and exposed to the agent.
- **Keyboard tracking** — keystroke / active‑window context (privacy‑gated, opt‑in only).
- **Unified live session** — one view fusing live screen + input + AI vision, wired to `act_on_screen`
  so the AI can interact with what it sees.
- **Privacy & safety first** — all opt‑in, local‑only, pause/redact, no persistence by default
  (keyboard/mouse capture is sensitive; consistent with the single‑user, private‑by‑design posture).

See `TASKS.md` → "AI Screen Vision (SV)" for SV‑1…7 and `PROJECT_PLAN.md` Phase 7 for the design.

## 🆕 Unified Workspace + Auto model (UWS, P1) — ✅ shipped M97/M98
Chat + Agent merged into one **"Nova"** page (`#/workspace`) with professional toggle buttons
(mode · DeepThink · Web Search · Full Access · Attach‑any‑file) and **✨ Auto** intelligent model
selection (`automodel.py`). Bilingual README (EN+AR). See `TASKS.md` → UWS‑1…7.

## 🆕 Chat interface improvements (CHAT, P1) — ✅ shipped M62
DeepThink toggle (step‑by‑step reasoning), Web Search toggle (live DuckDuckGo results via `ddgs`, with
citations; opt‑in/online), and an explicit microphone **⏹ Stop** control. See `TASKS.md` → CHAT‑1…3
and the full spec in **`docs/chat-deepthink-websearch.md`**.

## 🟧 Known fragile / caveats (see STATUS.md for the live list; full truth in `docs/honest-state.md`)
- 🔴 **Agent GUI control is unguarded** — no per‑action confirmation, no kill‑switch (HON‑1). Biggest risk.
- 🔴 **No prompt‑injection defense** for the web‑augmented agent (HON‑10).
- 🟠 **Verification is smoke‑deep** — most ✅ are "verified once," not battle‑tested (HON‑2/3/6/7). OUT‑1/OUT‑5 are toy batteries; the live stream was never watched; no full Web‑Search chat turn was run.
- Command‑exec surface unguarded on localhost (by design; now has a destructive confirm‑guard + denylist).
- ~~Tests shallow + CI never executed~~ → **fixed**: deep + hermetic suite, agent‑loop tests, local CI proven (M49–M53).
- Agent success rate ✅ baselined (5/5, M54) + RAG quality ✅ (5/5, M58); **training output + media generation still unverified** (OUT‑2/3).
- `screen_if`, click‑to‑act — best‑effort / mocked‑only.
- ~~No watchdog; loops swallow errors; secrets plaintext; deps not clean‑installed~~ → **fixed**: watchdog (M55), loops surface errors (M56), secrets encrypted (M46), clean‑install proven (M52), WAL (M57), media backup (M59).

## 💡 Innovation backlog (creative, in‑scope — single‑user · local‑only)
Original ideas that extend Nova's vision without breaking the core principle. Tracked as IDEA‑* in
`TASKS.md`. Each is local‑only, opt‑in where it touches the screen/privacy.
1. **Visual macro recorder** — record a sequence of UIA/mouse actions and replay as a named local macro.
2. ✅ **Local screen memory (opt‑in)** (M105) — OCR snapshots of the screen into the KB so you can later
   ask "what was that error I saw earlier?" Strictly opt‑in (default OFF), local‑only; `screen_memory`
   schedule action for periodic capture.
3. ✅ **Save a successful agent run as a reusable Workflow/Automation** (M105) — a "💾 Save as workflow"
   button on the agent's final answer; the `agent` action replays the goal on re-run.
4. ✅ **Hands‑free voice conversation** (M105) — 🎙️ toggle in the Workspace: listen (silence‑detected) →
   STT → chat → speak the reply (local Piper) → listen again. Components verified; live mic loop is
   component‑verified (can't be driven headlessly).
5. ✅ **Folder Q&A** (M105) — point at a folder → auto‑index (recursive, skips secrets) → chat over it
   with citations (RAG over a directory). `/api/kb/ingest-folder` + Knowledge‑page input.
6. ✅ **Quality dashboard** (M105) — `/api/quality` records scored eval/health runs; the Diagnostics
   "Quality Trend" card charts latest % + delta per suite; `quality_check` schedule action + eval
   `--record` feed it. Catches regressions after model/dep/prompt updates.
7. ✅ **Region watch → act** (M105) — pin a screen `region` and/or trigger on text *absence*; extends
   the `screen_if` automation (region + "act when absent" in the builder).
8. ✅ **Local persistent memory** (M105) — durable user facts/preferences recalled across sessions;
   owner‑editable in Settings, injected into chat + agent prompts; local‑only.
9. ✅ **Image edit pipeline** (M105) — generate then iteratively refine images (ComfyUI img2img) from
   the chat via a "✨ Refine / edit" button on every generated image.
10. ✅ **Self‑healing loops** (M105) — every background loop auto‑restarts on a hard crash (`_supervise`,
   exp‑backoff), with the crash recorded to `/api/errors`.

## 🔒 CORE PRINCIPLE (permanent) — single‑user · local‑only
See **`docs/PRINCIPLES.md`**. No cloud/telemetry/inbound‑remote/LAN‑control/phone‑control/external‑
access/multi‑user — ever. Localhost‑only. Opt‑in outbound exceptions: Web Search + git source push.

## 🚫 Excluded (owner decision — never build)
- Multi‑user / accounts / roles / RBAC.
- RTL mirroring.
- Cloud hosting / horizontal scaling.
