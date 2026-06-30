# ⚡ AI Control Center

A complete, **100% local** AI command center for Windows + NVIDIA GPUs. One dark, bilingual
(English/Arabic + RTL) dashboard that unifies chat, an autonomous agent, a RAG knowledge base,
local model training, video generation, automation, and full observability — private, on your
own hardware.

> Built and tested on: Intel Core Ultra 9 285K · 95 GB RAM · RTX 5090 (32 GB) · Windows 11.

---

## ✨ Highlights
- **AI Chat** — projects, file upload (PDF/DOCX/TXT/code/images+OCR) with previews, **RAG with
  cited sources**, **DeepThink** (step‑by‑step reasoning) + **Web Search** (live DuckDuckGo results
  with citations, opt‑in) toggles, model comparison, voice in/out (Piper, with an explicit **⏹ Stop**
  mic control), Markdown rendering, live preview, export (TXT/MD/JSON/PDF), generation
  **speed (tok/s)**, and 👍→training. _(spec: `docs/chat-deepthink-websearch.md`)_
- **Agent Mode (v2)** — redesigned page: animated **Nova avatar**, real-time thinking log, a
  categorized example side panel, Send button + Enter-to-send. Autonomous ReAct loop with tools
  (KB search, run command, **read/write files**, **browse the web**, video, notify, speak, schedule),
  **dry‑run preview**, and a **🔓 Full Access** mode (runs any command / writes anywhere; credential
  reads stay denied).
- **Icons** — open-source **Twemoji** SVG icons across the whole UI, with tasteful animations
  (bounce / pulse / ring / wobble / spin); graceful native-emoji fallback offline.
- **Browser automation (Playwright)** — headless Chromium: open a URL, fill forms, click
  selectors, capture page text + screenshot. Available as `POST /api/browse`, an agent tool,
  and a workflow/automation action.
- **Screen Studio** — record the screen to MP4 (native mss + ffmpeg), read it (Windows OCR or
  qwen2.5‑VL vision), understand it in natural language, play recordings back in the dashboard.
  Wired to the **Agent** (`see_screen`/`read_screen`/`screenshot`), Automation, and the KB.
- **AI Screen Vision (Live)** — a real‑time `#/live` page: live screen stream (throttled MJPEG),
  live cursor overlay, focused‑window context, and on‑demand "describe what's on screen" (VLM) —
  so the AI can see exactly what you see. **Privacy‑first:** every capture is opt‑in, local‑only,
  non‑persistent, off by default. _(design: `PROJECT_PLAN.md` Phase 7)_
- **Knowledge Base (RAG)** — local embeddings (`nomic-embed-text`) → SQLite vector store → cosine
  retrieval, drag‑drop indexing, folder auto‑index automation.
- **Training Studio + Learning** — one‑click LoRA retrain of `nova-local`, live progress, dataset
  upload, self‑improving RAG→training loop, recommendations.
- **Automation + Workflows** — background scheduler (cron‑like) and sequential pipelines with
  task dependencies; webhooks (Slack/Discord/ntfy).
- **Creation** — local video (LTX 2B/13B via ComfyUI), capability‑tagged model library.
- **Trust & ops** — token authentication, full **audit log**, one‑click **system self‑test**,
  **backup & restore**, real‑time **system monitor** (GPU/CPU/RAM/VRAM/processes), and
  **Search Everything** (Ctrl/⌘+K).
- **Design** — premium **Apple‑style** UI (refined dark + clean light, single blue accent, SF/Inter
  type, soft shadows + glass blur, rounded corners, calm micro‑animations), bilingual EN/AR + RTL,
  auto theme, command palette, onboarding, keyboard shortcuts (`?`).
- **iOS‑style notification center** — categorized + grouped (Today/Yesterday/This Week), click‑to‑action,
  search/filter, mark‑all‑read, clear, mute, subtle chime, live via WebSocket.
- **Proactive intelligence** — Co‑Pilot suggestions, predictive habits, insights, daily briefing,
  achievements, usage analytics.

## 🚀 Quick start
```powershell
cd C:\AI\agent-workspace\control-center
python -m pip install fastapi "uvicorn[standard]" psutil python-multipart pypdf python-docx reportlab numpy playwright
python -m playwright install chromium      # one-time, for browser automation
python server.py           # or double-click start.cmd
```
Open **http://localhost:8900**. (Bound to localhost only by default — see Security.)

**Recommended local models** (RTX 5090, benchmarked on real command execution):
`qwen2.5:14b` is the default — best speed/accuracy for the agent (5/5 @ ~1.3 s/step).
`qwen2.5:32b` (19 GB, runs 100% on GPU) for maximum reasoning depth and Arabic. Both via `ollama pull`.

## 🧪 Testing
```powershell
python run_tests.py        # intensive end-to-end suite (endpoints, round-trips, live WS flows)
```
Or in‑app: **Diagnostics → Run self‑test** (13 subsystem checks), or `GET /api/selftest`.

## 🔒 Security
- **Localhost‑only by default** — the dashboard can run commands and an autonomous agent, so it
  is never exposed to the network unless you opt in.
- **Optional token auth** (Settings → Access & Security) protects every API + WebSocket; only then
  can LAN access be enabled.
- **Agent guardrails** — destructive shell commands are blocked; file writes are confined to
  `agent-output/`; reads deny credential stores (`.ssh`, `.env`, credentials…).
- **Audit log** records every command, agent action, automation, auth attempt, and config change.

## 🗂️ Architecture
```
control-center/
├── server.py          FastAPI app + agent loop + coupled routes (composition root)
├── nova/              extracted package: core/ (db,events,process,http),
│                      services/ (audit,notifications,jobs,metrics,screen,chat,
│                      ollama,owui,files,kb), api/ (10 routers)
├── static/
│   ├── index.html     SPA shell (sidebar, top bar, overlays)
│   ├── css/app.css    design system (dark/light, RTL)
│   └── js/            core.js (router+i18n+bus) · pages.js (pages) · shell.js (ws+notifs+boot)
├── run_tests.py       one-command intensive test suite
├── start.cmd          launcher (installs deps + runs)
├── ROADMAP.md         milestones M1–M15 + Ideas Backlog
└── BUILD_LOG.md       chronological decisions, fixes, tests
```
- **Backend:** FastAPI; background loops for metrics, service status, and the automation scheduler;
  a thread‑based process manager; everything persists to `C:\AI\agent-workspace\data\control.db`.
- **Frontend:** dependency‑free SPA (no build step) with a WebSocket event bus for live updates.
- **Integrations:** Ollama (11434), ComfyUI (8188), Open WebUI (3000), nvidia‑smi, psutil, the
  local toolkit (`*.ps1`), Piper TTS, and the LoRA training pipeline.

## 📡 Key API (all under `/api`)
`services · metrics · selftest · search?q= · insights · briefing` · `models · models/{load|stop}` ·
`chat-send · conversations… · upload · kb/{status,docs,search,ingest}` · `agent · browse · learn/{harvest,retrain}` ·
`training/{status,history,upload-dataset} · learning/stats` · `schedules… · workflows… · abtest` ·
`audit · auth/{status,login,logout} · backup · restore · tts`.

## 📄 License & privacy
Personal/local use. No data leaves the machine unless you set a cloud key or an outbound webhook.
