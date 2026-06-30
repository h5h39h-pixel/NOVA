# ⚡ Nova — AI Control Center

A complete, **100% local** AI command center for Windows + NVIDIA GPUs. One bilingual (English/Arabic)
dashboard that unifies a **Chat + Agent workspace**, screen vision, precise PC control, a RAG knowledge
base, local model training, media generation, automation, and full observability — private, on your own
hardware, no cloud required.

> **English first, العربية below ⬇️** · Built & tested on: Intel Core Ultra 9 285K · 95 GB RAM ·
> RTX 5090 (32 GB) · Windows 11 · Python 3.12.

---

# 🇬🇧 English

## What it is
Nova runs entirely on your machine. It talks to local LLMs (via **Ollama**), generates images/video
(via **ComfyUI**), transcribes speech (**faster‑whisper**), speaks (**Piper**), sees and controls your
screen (UI Automation), and learns from your usage (LoRA fine‑tuning → `nova-local`). The web dashboard
is a dependency‑free SPA served by a FastAPI backend; everything persists to a local SQLite database.

## ✨ Key features
- **Unified "Nova" workspace** (`#/workspace`) — Chat and Agent on **one page** with professional toggle
  buttons:
  - **💬 Chat / 🤖 Agent** mode segmented control.
  - **🧠 DeepThink** — step‑by‑step reasoning.
  - **🌐 Web Search** — live DuckDuckGo results with citations (opt‑in).
  - **🔓 Full Access** (agent mode) — run any command / control the PC.
  - **📎 Attach** — images, PDFs, DOCX, code, any file (OCR + vision for images).
  - **✨ Auto model** — picks the best installed model per task (coding → a code model, reasoning/
    DeepThink → a reasoning/larger model, vision → a VLM, agent → a tool‑capable model), or pick manually.
- **Autonomous Agent** — a ReAct loop that plans, uses tools, and acts: KB/web search, run commands,
  read/write files, **read & understand** any file/image, browse, **see/record/monitor the screen**
  (it decides when), **precise mouse/keyboard control**, generate media, schedule automations. Dry‑run
  preview + Full‑Access mode.
- **AI Screen Vision** (`#/live`) — real‑time screen stream, cursor overlay, focused‑window context, and
  on‑demand "describe what's on screen" (qwen2.5‑VL). Privacy‑first: opt‑in, local, non‑persistent.
- **Perception & Control** — window awareness (active window, all windows, size/position, DPI), UI
  element detection, and **reliable text entry via UI Automation** + pixel‑accurate mouse.
- **Knowledge Base (RAG)** — local embeddings (`nomic-embed-text`) → SQLite vector store → cosine
  retrieval with citations.
- **Training Studio** — one‑click LoRA retrain of `nova-local`, live progress, self‑improving
  RAG→training loop.
- **Media** — local image (SDXL/Flux) and video (LTX) generation via ComfyUI.
- **Voice** — local STT (GPU Whisper, Arabic‑capable) with an explicit ⏹ Stop, and TTS (Piper, adjustable
  speed, auto English/Arabic voice).
- **Trust & ops** — token auth, full audit log, daily DB snapshots + media backup, self‑test, real‑time
  system monitor, and a **⛔ panic kill‑switch** that instantly halts all PC control.

## 🚀 How to run
```powershell
cd C:\AI\agent-workspace\control-center
# 1) install dependencies (reproducible lock recommended)
python -m pip install -r requirements.lock        # or: -r requirements.txt
python -m playwright install chromium             # one-time, for browser automation
# 2) make sure Ollama is running with at least one chat model, e.g.:
ollama pull qwen2.5:14b
# 3) start
python server.py                                  # or double-click start.cmd
```
Open **http://localhost:8900**. Bound to localhost only by default.

**Recommended models** (RTX 5090): `qwen2.5:14b` (default, fast agent), `qwen2.5:32b` (max reasoning),
`qwen3-coder:30b` (coding), `qwen2.5vl:7b` (vision), `nomic-embed-text` (RAG). ✨ Auto uses whatever you
have installed.

## ⚠️ Safety — read before unattended use
- **Keep it on localhost.** The security model is "localhost is trusted." Exposing it on the LAN with
  `allow_remote_exec` lets others run commands and control your mouse/keyboard.
- **Full‑Access agent can do anything** — run commands, write files, click/type anywhere. Use dry‑run,
  watch it, and keep the **⛔ panic button** handy (top bar). You can also turn off agent GUI control
  entirely (Settings → "agent_can_control").
- **Web‑augmented agent = highest risk** (prompt injection from web pages). Web content is fenced as
  untrusted data, but treat it cautiously.
- The full, honest state of the project (what's solid, what's fragile) is in
  [`docs/honest-state.md`](docs/honest-state.md).

## 🧪 Testing & tools
```powershell
python scripts/check.py        # quality gate: pyflakes + node --check + pytest (also runs on commit/push)
python run_tests.py            # live end-to-end suite (needs server + Ollama) → 42/42
python scripts/ci_local.py     # clean-venv CI (proves the lock installs)
python scripts/agent_eval.py   # agent goal battery   ·   scripts/rag_eval.py  RAG quality
python scripts/gen_eval.py     # image-gen check       ·   scripts/load_test.py concurrency
```
CI also runs on GitHub Actions (`.github/workflows/ci.yml`).

## 🗂️ Architecture
```
control-center/
├── server.py            FastAPI composition root (lifespan, loops, middleware, router includes)
├── config.py            paths + endpoints
├── nova/
│   ├── core/            db · events · process · http · safety · errors · secretbox
│   ├── services/        chat · agent · control · screen · screen_vision · understand · web_search ·
│   │                    automodel · kb · training · jobs · stt · tts · backup · …
│   └── api/             one router per area (chat, agent, control, exec, stt, files_api, toolkit, …)
├── static/
│   ├── index.html
│   ├── css/             app.css → app-components.css → app-visuals.css → app-extras.css (cascade order)
│   └── js/              core.js → pages*.js (dashboard/create/agent/data/system/workspace) → shell.js
├── scripts/             check.py · ci_local.py · eval & benchmark tools
├── docs/                architecture, security, honest-state, feature specs, baselines
└── tests/               hermetic pytest + live frontend gate
```
Layered dependency DAG: `config ← core ← services ← api ← server` (nothing imports `server.py`).
Six source‑of‑truth files (`STATUS.md`, `ROADMAP.md`, `TASKS.md`, `PROJECT_PLAN.md`, `WORKFLOW.md`,
`BUILD_LOG.md`) are kept current every session.

---

<div dir="rtl">

# 🇸🇦 العربية

## ما هو
**نوفا** مركز قيادة للذكاء الاصطناعي يعمل **محلياً 100%** على جهازك (Windows + كرت NVIDIA). يتحدث إلى نماذج
لغوية محلية (عبر **Ollama**)، ويولّد الصور والفيديو (عبر **ComfyUI**)، ويحوّل الكلام إلى نص
(**faster‑whisper**)، وينطق (**Piper**)، ويرى شاشتك ويتحكم بها (UI Automation)، ويتعلّم من استخدامك
(تدريب LoRA → النموذج `nova-local`). الواجهة لوحة تحكم ويب بدون أي اعتماد خارجي، يخدمها خادم FastAPI، وكل
شيء يُحفظ في قاعدة بيانات SQLite محلية. **خاص، بدون سحابة، وبدون إنترنت إلا عند طلبك (بحث الويب).**

## ✨ أهم الميزات
- **مساحة عمل "نوفا" الموحّدة** (`#/workspace`) — المحادثة والوكيل في **صفحة واحدة** مع أزرار تبديل احترافية:
  - مفتاح **💬 محادثة / 🤖 وكيل**.
  - **🧠 تفكير عميق** — استدلال خطوة بخطوة.
  - **🌐 بحث الويب** — نتائج مباشرة من DuckDuckGo مع مصادر (اختياري).
  - **🔓 صلاحية كاملة** (وضع الوكيل) — تشغيل أي أمر والتحكم بالحاسوب.
  - **📎 إرفاق** — صور ومستندات PDF/DOCX وأكواد وأي ملف (OCR ورؤية للصور).
  - **✨ نموذج تلقائي** — يختار أفضل نموذج مثبّت لكل مهمة (برمجة → نموذج أكواد، استدلال/تفكير عميق → نموذج
    استدلال أو أكبر، رؤية → نموذج رؤية، وكيل → نموذج يدعم الأدوات)، أو اختر يدوياً.
- **وكيل ذاتي** — حلقة ReAct تخطّط وتستخدم الأدوات وتنفّذ: بحث في المعرفة والويب، تشغيل أوامر، قراءة/كتابة
  ملفات، **قراءة وفهم** أي ملف أو صورة، تصفّح، **رؤية/تسجيل/مراقبة الشاشة** (يقرر هو متى)، **تحكم دقيق
  بالفأرة ولوحة المفاتيح**، توليد وسائط، جدولة مهام. مع معاينة تجريبية ووضع صلاحية كاملة.
- **رؤية الشاشة بالذكاء** (`#/live`) — بث مباشر للشاشة، مؤشر الفأرة، سياق النافذة النشطة، ووصف فوري لما على
  الشاشة (qwen2.5‑VL). الخصوصية أولاً: اختياري ومحلي ولا يُحفظ.
- **الإدراك والتحكم** — معرفة النوافذ (النشطة وكلها، الحجم والموضع، DPI)، واكتشاف عناصر الواجهة، و**إدخال
  نص موثوق عبر UI Automation** وفأرة بدقة البكسل.
- **قاعدة المعرفة (RAG)** — تضمينات محلية (`nomic-embed-text`) ومتجر متجهات في SQLite واسترجاع بالتشابه مع
  ذكر المصادر.
- **استوديو التدريب** — إعادة تدريب `nova-local` بنقرة، تقدّم مباشر، وحلقة تعلّم ذاتية (المعرفة → التدريب).
- **الوسائط** — توليد صور (SDXL/Flux) وفيديو (LTX) محلياً عبر ComfyUI.
- **الصوت** — تحويل كلام إلى نص محلي (Whisper على كرت الشاشة، يدعم العربية) مع زر **⏹ إيقاف** واضح، ونطق
  (Piper، سرعة قابلة للتعديل، صوت عربي/إنجليزي تلقائي).
- **الثقة والتشغيل** — مصادقة برمز، سجل تدقيق كامل، نسخ احتياطي يومي لقاعدة البيانات والوسائط، فحص ذاتي،
  مراقبة نظام لحظية، و**زر إيقاف طوارئ ⛔** يوقف كل تحكم بالحاسوب فوراً.

## 🚀 كيفية التشغيل
```powershell
cd C:\AI\agent-workspace\control-center
# 1) تثبيت الاعتماديات (يُفضّل ملف القفل القابل للتكرار)
python -m pip install -r requirements.lock
python -m playwright install chromium
# 2) تأكد أن Ollama يعمل مع نموذج محادثة واحد على الأقل:
ollama pull qwen2.5:14b
# 3) التشغيل
python server.py
```
افتح **http://localhost:8900** (مرتبط بـ localhost فقط افتراضياً). للعربية: زر اللغة (ع) في الأعلى.

## ⚠️ السلامة — اقرأ قبل التشغيل دون إشراف
- **أبقِه على localhost.** نموذج الأمان مبني على "الثقة بـ localhost". تعريضه على الشبكة مع
  `allow_remote_exec` يتيح لآخرين تشغيل أوامر والتحكم بفأرتك ولوحة مفاتيحك.
- **الوكيل بصلاحية كاملة يمكنه فعل أي شيء** — تشغيل أوامر، كتابة ملفات، النقر/الكتابة في أي مكان. استخدم
  المعاينة التجريبية، وراقبه، وأبقِ **زر الطوارئ ⛔** جاهزاً (الشريط العلوي). يمكنك أيضاً إيقاف تحكم الوكيل
  بالواجهة تماماً (الإعدادات → `agent_can_control`).
- **الوكيل مع بحث الويب = الأعلى خطورة** (حقن التعليمات من صفحات الويب). محتوى الويب يُعامَل كبيانات غير
  موثوقة، لكن توخَّ الحذر.
- الحالة الصادقة الكاملة للمشروع في [`docs/honest-state.md`](docs/honest-state.md).

## 🗂️ البنية
نفس الشجرة الموضّحة في القسم الإنجليزي: خادم FastAPI (`server.py`) كجذر تركيب، حزمة `nova/`
(core/services/api)، وواجهة SPA في `static/`. سلسلة الاعتماد: `config ← core ← services ← api ← server`.
ستة ملفات مرجعية (STATUS · ROADMAP · TASKS · PROJECT_PLAN · WORKFLOW · BUILD_LOG) تُحدَّث كل جلسة.

</div>

---
_License: MIT. A personal, single‑user system — no multi‑user/RBAC, no cloud, no telemetry._
