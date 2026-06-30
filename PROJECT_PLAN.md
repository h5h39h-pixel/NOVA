# PROJECT PLAN — Nova / AI Control Center

High‑level plan: milestones, phases, and the architecture decisions behind them.
Personal single‑user system. Companions: `ROADMAP.md` (features), `TASKS.md` (work),
`WORKFLOW.md` (process), `STATUS.md` (live), `BUILD_LOG.md` (history).

_Last updated: 2026-06-30._ **Update on every session (permanent rule).**

---

## 1. Where it stands (honest)
Feature‑complete in breadth, cleanly architected, under git, fully local — and the original P0→P3 +
Phases 7/8 roadmap is shipped & smoke‑verified. **The honest remaining work (Phase 9 / HON‑1…11,
`docs/honest-state.md`) is the part that matters most: it is under‑guarded and verification‑shallow where
it counts.** Specifically: agent GUI control has no confirmation/kill‑switch (HON‑1), there's no
prompt‑injection defense (HON‑10), and most features are "verified once," not battle‑tested. **Sharp
tool, not a finished appliance.**

## 2. The campaign (phases, by priority)
Foundation is done (Safety Net, modular refactor, UI, OWUI 0.10.1 — BUILD_LOG M28–M41).
The active plan:

| Phase | Goal (priority) | Exit criteria | Status |
|---|---|---|---|
| **P‑1 Security** | P0 — lock down exec surface, auth, HTTPS | exec destructive‑guard + tightened CSP + key encryption + HTTPS turnkey; every exec call‑site audited | ✅ done (M43–M48) |
| **P‑2 Tests** | P0 — real coverage | deep unit + integration + hermetic (no live deps) + agent tests + CI actually runs + clean‑venv install proven | ✅ done (M49–M53) |
| **P‑3 Outcome** | P1 — prove it works | measured agent success baseline; training/generation/`screen_if`/RAG verified end‑to‑end | 🟦 next |
| **P‑4 Stability** | P1 — resilience | watchdog auto‑restart; jobs survive restart; loops recover + surface errors; media backup; WAL | ⬜ |
| **P‑5 Docs** | P2 — upkeep | six files always current; README/SETUP refreshed; training pipeline documented | ✅ ongoing (DOC‑1…3) |
| **P‑6 Features/Polish** | P2/P3 | click‑to‑act reliability, STT, voice; perf budget, a11y, mobile | ✅ done (FEA‑1…4, POL‑1…4) |
| **P‑7 AI Screen Vision** | P1 — core feature | real‑time screen stream + mouse/keyboard tracking + continuous VLM loop, fused into a live "see‑what‑I‑see & act" session; privacy‑first (opt‑in, local, non‑persistent) | 🟦 largely shipped (SV‑1…7) |
| **P‑8 Perception & Control** | P1 — core feature | read & understand (OCR+VLM, files/images/screen) · window‑layout awareness (active/all windows, measurements, DPI) · UI element detection · precise mouse/keyboard control — as agent tools, chat commands, APIs | ✅ shipped (PC‑1…6) |
| **P‑9 Hardening v2 (honest gaps)** | P0/P1 — the real remaining work | guard + kill‑switch for agent GUI control (HON‑1); prompt‑injection defense (HON‑10); real GUI integration test; coverage; honest eval batteries; persistent observability; soak/concurrency; real lockfile + CI on a remote | ⬜ **NEW, top priority** (HON‑1…11) |

Estimates are deliberately omitted — work proceeds **one task at a time, highest priority first,
fully verified** before the next (see `WORKFLOW.md`). Re‑baseline after each phase.

## 3. Architecture decisions (the load‑bearing ones)
- **Strict layered DAG:** `config ← core ← services ← api ← server`. Nothing imports `server.py`.
  Cross‑cutting coupling is broken with **injection hooks** (`set_run_action`, `set_briefing_hook`,
  training hook) rather than back‑imports.
- **Composition root:** `server.py` (~555 lines) wires the app, lifespan, middleware, background
  loops, and includes the 21 routers. Logic lives in `nova/services/*`, routes in `nova/api/*`.
- **Framework‑free SPA:** `static/js/{core,pages,shell}.js`, one global scope, load order matters.
  No bundler. Auto cache‑busting (server stamps `?v=<asset mtime>`).
- **Single SQLite store** (`control.db`) with a `schema_version` migration framework + daily snapshots.
- **Fully local:** vendored fonts + Font Awesome; all model/services traffic proxied through our
  backend; works offline.
- **Security posture:** localhost‑only by default; LAN exposure requires auth **and** explicit
  `allow_remote_exec`; tokens hashed; audit trail. (Hardening continues in Phase 1.)
- **Open WebUI** runs as a Docker container (`ghcr.io/open-webui/open-webui:v0.10.1`); we integrate
  via its `webui.db` and HTTP; our integration is **schema‑agnostic** to survive OWUI upgrades.
- **External dependency:** the fine‑tune pipeline lives in `C:\AI\training` — we orchestrate it, we
  don't own it.

## 4. Milestone history (condensed — full detail in BUILD_LOG.md)
- **M28–M30** foundation refactor, bug reports, data safety, responsive, flagship model.
- **M31–M33** model evaluation, click‑to‑act (best‑effort), API‑layer start.
- **M34–M35** full backend modularization (server.py 2400→~550).
- **M36** vibrant/living UI. **M37** Nova Brain 2.0. **M38** hardening Phases 0–4.
- **M39** bespoke per‑page UI. **M40** close‑tab confirm. **M41** Open WebUI 0.10.1.

## 5. Definition of Done & risks
- **DoD:** see `WORKFLOW.md` quality gate (lint + tests + live suite + render‑if‑visual + docs + commit).
- **Top risks (current, honest):**
  1. 🔴 **Agent GUI control is unguarded** — no confirmation, no kill‑switch; Full‑Access agent can
     click/type/delete anywhere → **Phase 9 / HON‑1**.
  2. 🔴 **Prompt injection** — web‑augmented agent reads untrusted text while holding control tools →
     **HON‑10**.
  3. 🟠 **Verification is smoke‑deep** — most ✅ are "once," not battle‑tested; toy eval batteries →
     **HON‑2/3/7**.
  4. Localhost‑trust security model — anything beyond localhost is dangerous.
  5. Single‑flight chat (`chat_lock`) + in‑memory error log (lost on restart) → HON‑4/5.
  (Historical, now addressed: exec surface hardened, tests scaffolded, outcomes smoke‑verified, watchdog.)

## 6. Phase 7 — AI Screen Vision (design)
A core feature added 2026‑06‑30. Goal: the AI perceives the live screen + input in real time and can
act on it — "it sees exactly what I see."
- **Architecture fit:** a new `nova/services/screen_vision.py` (or extend `screen.py`) owns the
  capture/encode/track loop; routes in a new `nova/api/screen_vision.py`; a new SPA "Live" page.
  Reuses `mss` (grab), `pillow` (downscale+JPEG), qwen2.5‑VL (`describe_screen`), and the existing
  `act_on_screen` for control. Frames stream over the existing WS bus (or a dedicated MJPEG route).
- **Performance:** the live stream and the VLM loop run at **independent, throttled rates** (stream
  ~2–10 FPS; VLM ~1 frame / N sec) so slow vision never stalls the preview. Server‑side downscale +
  JPEG keeps bandwidth/CPU bounded; drop frames under backpressure.
- **Privacy & safety (load‑bearing):** every capability is **opt‑in and OFF by default**, local‑only,
  pausable, with an on‑screen indicator and **no persistence** unless the user explicitly records.
  Keyboard tracking is the most sensitive — extra gating, redaction near password fields, never logged
  to disk. This is consistent with the private, single‑user posture (and the existing credential
  deny‑list). Enable/disable is audited.
- **Risks:** keylogging is sensitive even on a personal box (treat config like a secret); VLM latency;
  CPU under continuous capture. Each is addressed by the gating + throttling above.

## 7. Chat interface improvements (CHAT — shipped M62)
Owner‑requested chat UX, 2026‑06‑30:
- **DeepThink** toggle → backend prepends a step‑by‑step reasoning system message and raises
  `num_predict`; model‑agnostic (works with any local model).
- **Web Search** toggle → new `nova/services/web_search.py` using the `ddgs` library (DuckDuckGo, no
  API key) injects top results + URL citations into the turn. This is the one deliberately **online**
  feature: opt‑in per message, off by default, degrades gracefully offline (the rest stays local).
- **Microphone stop** → the mic button becomes an explicit **⏹ Stop** while recording (the stop logic
  existed; the affordance was unclear). `web_search` is the first new runtime dependency since the
  pinning (`ddgs` added to `requirements.txt`/`.in`).
- **Full spec:** `docs/chat-deepthink-websearch.md` (behavioral spec, implementation, dependencies,
  extension ideas).

## 🚫 Out of scope (permanent): multi‑user/RBAC, RTL mirroring, cloud/scaling.
