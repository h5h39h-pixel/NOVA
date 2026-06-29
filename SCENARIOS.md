# Real-World Scenario Validation

**62 / 62 scenarios passed.** These are *practical* end-to-end runs against the live system
(port 8900) — real LLM calls, real agent loops, real image/video/audio generation, real browser
automation, real training control — not mocked unit tests. Each scenario drove the actual
endpoint/WebSocket the UI uses and verified the real result (file written, citation returned,
GPU paused, window opened, etc.).

## How it was run
- **HTTP/WebSocket battery** (`scenarios.py`): 50 scenarios over the real REST + WS APIs (chat, agent,
  automation, web, files, models, A/B, export, backup, settings, notifications, monitoring, KB, Co-Pilot,
  Nova Brain, workflows, batch, security).
- **Media battery** (`media_scen.ps1`): 7 scenarios using the real toolkit + ComfyUI + Piper (SDXL,
  Flux, LTX-2B video, EN/AR speech-to-WAV, Windows OCR, qwen2.5vl vision).
- **Training control** (`train_ctrl.py`): 5 scenarios on a real LoRA run (start, live progress/ETA/GPU,
  pause, resume, stop).

## Issues found & fixed during testing
No **product** defects were found — every feature worked on the real run. Three issues were in the
**test harness itself** and were fixed, then the affected scenarios re-verified live:
1. Console/script encoding (`→`, Arabic) crashed the Python/PowerShell *runner* → set UTF-8 stdout and
   loaded Arabic from a UTF-8 file. (Arabic TTS then produced a valid 90 KB WAV; the server's own
   `/api/tts` path was always correct — it passes text as UTF-16LE base64.)
2. `load model` called with `{name:…}` instead of `{model:…}` → fixed; endpoint returns `{ok:true}`.
3. Audit parser read key `items` instead of `events` → fixed; `/api/audit` had 271 real events.

## Results

| # | Category | Scenario | Result | Evidence / Notes |
|---|----------|----------|--------|------------------|
| 1 | Chat | plain reply (llama3.2:3b) | ✅ PASS | "PONG" |
| 2 | Chat | RAG with citation | ✅ PASS | answered THUNDER-88, 1 source cited |
| 3 | Chat | inline command (!cmd → /api/exec) | ✅ PASS | command dispatched |
| 4 | Chat | file-attachment context | ✅ PASS | answered "12.4 million" from attached doc |
| 5 | Chat | alternate model (qwen2.5:7b) | ✅ PASS | replied |
| 6 | Agent | simple file create+read | ✅ PASS | write_file→read_file, file on disk |
| 7 | Agent | complex KB→notify | ✅ PASS | kb_search→notify, launch date in notification |
| 8 | Agent | web browse | ✅ PASS | reported "Example Domain" |
| 9 | Agent | run command | ✅ PASS | run_command used |
| 10 | Agent | dry-run mode | ✅ PASS | simulated, nothing executed |
| 11 | Agent | tool restriction | ✅ PASS | run_command disabled, not used |
| 12 | Automation | scheduled notify | ✅ PASS | create→run→delete, status=notified |
| 13 | Automation | schedule toggle+delete | ✅ PASS | toggled + deleted |
| 14 | Web | headless browse + screenshot | ✅ PASS | title=Example Domain + screenshot |
| 15 | Web | browse Wikipedia | ✅ PASS | got the article title |
| 16 | Web | open_url default browser | ✅ PASS | opened Google in Edge |
| 17 | Web | Playwright form fill+click | ✅ PASS | "Hello Scenario from Cairo!" |
| 18 | Files | upload + download | ✅ PASS | upload ok, /files GET 200 |
| 19 | Files | KB ingest + delete doc | ✅ PASS | doc added then deleted |
| 20 | Files | rename (conversation) | ✅ PASS | title updated |
| 21 | Models | list + tags | ✅ PASS | 12 models with capability tags |
| 22 | Models | load model | ✅ PASS | /api/models/load → {ok:true} |
| 23 | Models | A/B test + judge | ✅ PASS | 2 models judged, verdict tallied |
| 24 | Voice | TTS English (speak) | ✅ PASS | {ok:true} |
| 25 | Voice | TTS Arabic (speak) | ✅ PASS | {ok:true} |
| 26 | Export | PDF export | ✅ PASS | HTTP 200 PDF |
| 27 | Export | JSON / MD / TXT data | ✅ PASS | messages serializable |
| 28 | Backup | backup bundle | ✅ PASS | full JSON bundle |
| 29 | Backup | restore | ✅ PASS | re-added a schedule from a bundle |
| 30 | Settings | language (ar/en) | ✅ PASS | toggled |
| 31 | Settings | theme (light/dark) | ✅ PASS | toggled |
| 32 | Settings | webhook config | ✅ PASS | URL saved |
| 33 | Notifications | list + mark all seen | ✅ PASS | unread 56→0 |
| 34 | Notifications | clear all | ✅ PASS | emptied |
| 35 | Monitor | live metrics | ✅ PASS | GPU/CPU/RAM telemetry |
| 36 | Monitor | services status | ✅ PASS | ollama/comfy/owui online |
| 37 | Monitor | system processes | ✅ PASS | listed |
| 38 | Knowledge | KB semantic search | ✅ PASS | hits returned |
| 39 | Knowledge | unified search (Ctrl+K) | ✅ PASS | 10 results |
| 40 | Intelligence | Co-Pilot | ✅ PASS | suggestion returned |
| 41 | Intelligence | Nova Brain | ✅ PASS | knowledge map |
| 42 | Intelligence | Insights | ✅ PASS | actionable insights |
| 43 | Intelligence | Habits | ✅ PASS | predictive habits |
| 44 | Intelligence | Achievements | ✅ PASS | achievements |
| 45 | Batch | batch queue (sequential exec) | ✅ PASS | 3 commands run |
| 46 | Workflows | multi-step workflow | ✅ PASS | status=completed |
| 47 | Workflows | workflow with browse step | ✅ PASS | status=completed |
| 48 | Security | audit log | ✅ PASS | 271 events recorded |
| 49 | Security | auth status (default off) | ✅ PASS | required=false (localhost) |
| 50 | Security | token auth round-trip | ✅ PASS | no-token 401 → token 200 → disabled |
| 51 | Image | SDXL generation | ✅ PASS | real 1024² PNG, 1652 KB |
| 52 | Image | Flux-schnell generation | ✅ PASS | real PNG, 1186 KB |
| 53 | Video | LTX-2B generation | ✅ PASS | playable mp4, 696 KB |
| 54 | Voice | TTS English → WAV | ✅ PASS | 131 KB WAV |
| 55 | Voice | TTS Arabic → WAV | ✅ PASS | 90 KB WAV |
| 56 | Vision | OCR (Windows) | ✅ PASS | read "Nova OCR 7788 Test" exactly |
| 57 | Vision | Vision model (qwen2.5vl) | ✅ PASS | read the image text |
| 58 | Training | start | ✅ PASS | job started |
| 59 | Training | live progress (step/ETA/GPU) | ✅ PASS | LoRA 1/33, ETA 1600s, GPU 100% |
| 60 | Training | pause | ✅ PASS | status=paused, GPU 100%→3% |
| 61 | Training | resume | ✅ PASS | status=running, GPU→100% |
| 62 | Training | stop | ✅ PASS | status=stopped, processes killed |

## Manual / by-design
- **Voice input (microphone)** uses the browser's Web Speech API and needs a human mic, so it isn't
  scriptable here; the output half (TTS, EN+AR) is verified above (#24–25, #54–55). The 13B video model
  and visible-browser YouTube flow were verified in prior milestones (M19, M22).

_Re-run anytime: `python scenarios.py` (50), `media_scen.ps1` (7), `python train_ctrl.py` (5)._
