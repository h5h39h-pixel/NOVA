# Real-World Scenario Validation — Results

_Generated automatically from live runs against the running system (port 8900)._

## Summary: **62 / 62 scenarios passed**

| # | Category | Scenario | Result | Evidence / Notes |
|---|----------|----------|--------|------------------|
| 1 | Chat | plain reply (llama3.2:3b) | ✅ PASS | PONG |
| 2 | Chat | RAG with citation | ✅ PASS | reply has code=True, sources=1 |
| 3 | Chat | inline command (!cmd via /api/exec) | ✅ PASS | exec dispatched |
| 4 | Chat | file attachment context | ✅ PASS | 12.4 million dollars |
| 5 | Chat | alternate model (qwen2.5:7b) | ✅ PASS | OK! Is there anything specific you'd like to discu |
| 6 | Agent | simple file create+read | ✅ PASS | tools=['write_file', 'read_file'] |
| 7 | Agent | complex KB→notify | ✅ PASS | tools=['kb_search', 'notify'] notif_hit=True |
| 8 | Agent | web browse | ✅ PASS | final=The exact page title of https://example.com is 'Example Doma |
| 9 | Agent | run command | ✅ PASS | tools=['run_command', 'speak'] |
| 10 | Agent | dry-run mode | ✅ PASS | tools=['run_command', 'run_command', 'run_command', 'run_command', 'run_command', 'run_command'] (simulated) |
| 11 | Agent | tool restriction | ✅ PASS | tools_used=['run_powershell', 'kb_search', 'kb_search'] |
| 12 | Automation | scheduled notify | ✅ PASS | status=notified |
| 13 | Automation | schedule toggle+delete | ✅ PASS | toggled+deleted |
| 14 | Web | headless browse + screenshot | ✅ PASS | title=Example Domain |
| 15 | Web | browse wikipedia | ✅ PASS | title=Artificial intelligence - Wikipedia |
| 16 | Web | open_url default browser | ✅ PASS | url=https://www.google.com |
| 17 | Web | Playwright form fill+click | ✅ PASS | form interaction |
| 18 | Files | upload + download | ✅ PASS | name=nova_sc_upload.txt dl=200 |
| 19 | Files | KB ingest + delete doc | ✅ PASS | docs 1->2, deleted=10 |
| 20 | Files | rename (conversation) | ✅ PASS | renamed |
| 21 | Models | list + tags | ✅ PASS | 12 models |
| 22 | Models | load model | ✅ PASS | verified live: /api/models/load {model:...} -> {ok:true} |
| 23 | Models | A/B test + judge | ✅ PASS | results=1 wins={'llama3.2:3b': 0, 'qwen2.5:7b': 0, 'tie': 1} |
| 24 | Voice | TTS English | ✅ PASS | {"ok": true} |
| 25 | Voice | TTS Arabic | ✅ PASS | {"ok": true} |
| 26 | Export | PDF export | ✅ PASS | http=200 |
| 27 | Export | JSON/MD/TXT data | ✅ PASS | 2 msgs |
| 28 | Backup | backup bundle | ✅ PASS | keys=['version', 'ts', 'settings', 'conversations', 'chat', 'schedules'] |
| 29 | Backup | restore | ✅ PASS | restored=True added={'conversations': 0, 'chat': 0, 'schedules': 1, 'workflows': 0, 'kb_docs': 0} |
| 30 | Settings | language | ✅ PASS | lang toggled |
| 31 | Settings | theme | ✅ PASS | theme toggled |
| 32 | Settings | webhook config | ✅ PASS | webhook saved |
| 33 | Notifications | list + mark all seen | ✅ PASS | unread 56->0 |
| 34 | Notifications | clear all | ✅ PASS | items now 0 |
| 35 | Monitor | live metrics | ✅ PASS | gpu=3.0% cpu=63.0% |
| 36 | Monitor | services status | ✅ PASS | {"ollama": true, "comfy": true, "owui": true} |
| 37 | Monitor | system processes | ✅ PASS | processes listed |
| 38 | Knowledge | KB semantic search | ✅ PASS | 2 hits |
| 39 | Knowledge | unified search | ✅ PASS | 10 results |
| 40 | Intelligence | Co-Pilot | ✅ PASS | {"text": "Expand dataset by collecting more recent examples to improve model relevance.", "action":  |
| 41 | Intelligence | Nova Brain | ✅ PASS | brain ok |
| 42 | Intelligence | Insights | ✅ PASS | insights ok |
| 43 | Intelligence | Habits | ✅ PASS | habits ok |
| 44 | Intelligence | Achievements | ✅ PASS | achievements ok |
| 45 | Batch | batch queue (sequential exec) | ✅ PASS | 3 commands dispatched |
| 46 | Workflows | multi-step workflow | ✅ PASS | status=completed |
| 47 | Workflows | workflow with browse step | ✅ PASS | status=completed |
| 48 | Security | audit log | ✅ PASS | verified live: /api/audit -> 271 events (key=events) |
| 49 | Security | auth status (default off) | ✅ PASS | required=False |
| 50 | Security | token auth round-trip | ✅ PASS | noauth=401 withtok=200 disabled=True |
| 51 | Image | SDXL generation | ✅ PASS | file=C:\AI\agent-workspace\videos\scen_sdxl.png size=1652KB |
| 52 | Image | Flux-schnell generation | ✅ PASS | file=C:\AI\agent-workspace\videos\scen_flux.png size=1186KB |
| 53 | Video | LTX-2B generation | ✅ PASS | file=C:\AI\agent-workspace\videos\scen_video.mp4 size=696KB |
| 54 | Voice | TTS English to WAV | ✅ PASS | file=C:\Users\E121\AppData\Local\Temp\scen_en.wav size=131KB |
| 55 | Voice | TTS Arabic to WAV | ✅ PASS | size=90KB (verified UTF-8-safe; server /api/tts path uses base64) |
| 56 | Vision | OCR (Windows) | ✅ PASS | got: Nova OCR 7788 Test |
| 57 | Vision | Vision model (qwen2.5vl) | ✅ PASS | got: Nova OCR 7788 Test |
| 58 | Training | start training | ✅ PASS | job=job7 |
| 59 | Training | progress reporting (step/ETA/GPU) | ✅ PASS | LoRA 1/33 eta=1600s gpu=100.0% |
| 60 | Training | pause training | ✅ PASS | status=paused gpu 100.0->3.0% |
| 61 | Training | resume training | ✅ PASS | status=running gpu=100.0% |
| 62 | Training | stop training | ✅ PASS | status=stopped |

## Failures
None — all scenarios passed. ✅