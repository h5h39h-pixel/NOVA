# -*- coding: utf-8 -*-
"""
AI Control Center -- backend hub for the local AI assistant.

Integrates: Ollama, ComfyUI (LTX-Video), Open WebUI (Docker), nvidia-smi, psutil,
the toolkit (.ps1), and an SQLite store for settings/history/notifications.

Run:  python server.py   ->  http://localhost:8900
"""
import os, json, time, threading, asyncio, shutil, uuid, secrets, logging, collections
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path

import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# ----------------------------------------------------------------------------- config
# All paths/endpoints are resolved portably in config.py and overridable via config.json.
from config import (TOOLKIT, UPLOAD_DIR, DB_PATH, LOG_DIR, OLLAMA, COMFY_URL,
                    OWUI_URL, PORT, HTTPS_ENABLED, BIND_OVERRIDE,
                    DS_BASE, DS_COMBINED, ensure_cert)
BASE        = Path(__file__).resolve().parent
STATIC      = BASE / "static"
# data layer (SQLite connection, schema, settings, history) — nova.core.db
from nova.core.db import db, init_db, get_settings
# localhost-only unless the user explicitly enables auth + LAN (computed at startup in __main__)
BIND_HOST = "127.0.0.1"

# ----------------------------------------------------------------------------- logging / observability
LOG_DIR.mkdir(parents=True, exist_ok=True)
log = logging.getLogger("nova")
log.setLevel(logging.INFO)
if not log.handlers:
    _fh = RotatingFileHandler(LOG_DIR / "server.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    _fh.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-7s %(message)s"))
    log.addHandler(_fh)

# process ownership (Windows Job Object) — nova.core.process
from nova.core.process import init_job_object, ps_args, _q

# _hash + the auth gate now live in nova/services/settings.py

# ----------------------------------------------------------------------------- local speech-to-text (faster-whisper)
_WHISPER = None
_WHISPER_LOCK = threading.Lock()
_WHISPER_SIZE = None
def get_whisper():
    """Lazily load the local Whisper STT model. Size is configurable via the `stt_model`
    setting (tiny/base/small/medium) — larger = more accurate (esp. Arabic/noisy), slower."""
    global _WHISPER, _WHISPER_SIZE
    size = (get_settings().get("stt_model") or "base").strip()
    if _WHISPER is None or size != _WHISPER_SIZE:
        with _WHISPER_LOCK:
            if _WHISPER is None or size != _WHISPER_SIZE:
                from faster_whisper import WhisperModel
                if size not in ("tiny", "base", "small", "medium", "large-v3"): size = "base"
                _WHISPER = WhisperModel(size, device="cpu", compute_type="int8")
                _WHISPER_SIZE = size
                log.info(f"Whisper STT model loaded ({size} / cpu / int8) — fully local")
    return _WHISPER

# ----------------------------------------------------------------------------- db
# service layer — audit trail + notifications/webhooks (nova.services)
from nova.services.audit import audit
from nova.services.notifications import add_notification

# ----------------------------------------------------------------------------- websocket hub
from nova.core.events import clients, push, _send_all, set_main_loop, get_loop
# last_metrics state now lives in nova/services/metrics.py (get_last_metrics/set_last_metrics)
# chat_lock + the streaming chat-send flow now live in nova/services/chat.py
# Conversation/message store extracted to nova/services/chat.py; imported back here.
from nova.services.chat import SESSION_ID, conv_messages


# ----------------------------------------------------------------------------- http helpers
# http helpers (nova.core.http) + system telemetry (nova.services.metrics)
from nova.core.http import http_ok
from nova.services.metrics import collect_metrics, set_last_metrics, record_history, get_last_metrics

# ----------------------------------------------------------------------------- process manager
# Job + ProcMgr live in nova.services.jobs; the training-done callback is injected below.
from nova.services.jobs import PM

# ps_args extracted to nova/core/process.py; imported above.

# OWUI integration extracted to nova/services/owui.py (used by nova/api/owui.py router).

# ----------------------------------------------------------------------------- ollama helpers
# Ollama client extracted to nova/services/ollama.py; imported back here.
from nova.services.ollama import ollama_models

# ----------------------------------------------------------------------------- app
@asynccontextmanager
async def lifespan(app: FastAPI):
    set_main_loop(asyncio.get_running_loop())
    init_db()
    init_job_object()
    log.info("AI Control Center starting up")
    psutil.cpu_percent(interval=None)  # prime
    asyncio.create_task(metrics_loop())
    asyncio.create_task(status_loop())
    asyncio.create_task(scheduler_loop())
    asyncio.create_task(backup_loop())
    yield
    # ---- graceful shutdown: finalize in-flight work so nothing is lost ----
    try:
        if screen_svc.RECORDER.is_recording():
            r = screen_svc.RECORDER.stop()
            log.info(f"shutdown: finalized active screen recording -> {r.get('file')}")
    except Exception: pass
    try:
        for j in list(PM.jobs.values()):
            if j.kind == "training" and j.status in ("running", "starting", "paused"):
                log.info(f"shutdown: training job {j.id} still active (children owned by Job Object)")
    except Exception: pass
    log.info("AI Control Center shutting down cleanly")

app = FastAPI(title="AI Control Center", lifespan=lifespan)

# ---- API routers (nova/api/*) — extracted route groups, included before the static mount ----
from nova.api.bugs import router as bugs_router
from nova.api.notifications import router as notifications_router
from nova.api.audit import router as audit_router
from nova.api.history import router as history_router
from nova.api.conversations import router as conversations_router
from nova.api.analytics import router as analytics_router
from nova.api.models import router as models_router
from nova.api.owui import router as owui_router
from nova.api.kb import router as kb_router
from nova.api.media import router as media_router
from nova.api.agent import router as agent_router
from nova.api.search import router as search_router
from nova.api.metrics import router as metrics_router
from nova.api.chat import router as chat_router
from nova.api.training import router as training_router
from nova.api.schedules import router as schedules_router
from nova.api.screen import router as screen_router
from nova.api.settings import router as settings_router
from nova.api.tts import router as tts_router
from nova.api.backup import router as backup_router
from nova.api.insights import router as insights_router
# tags group the routes in the auto-generated API docs at /docs
app.include_router(bugs_router, tags=["bugs"])
app.include_router(notifications_router, tags=["notifications"])
app.include_router(audit_router, tags=["audit"])
app.include_router(history_router, tags=["history"])
app.include_router(conversations_router, tags=["chat"])
app.include_router(analytics_router, tags=["analytics"])
app.include_router(models_router, tags=["models"])
app.include_router(owui_router, tags=["open-webui"])
app.include_router(kb_router, tags=["knowledge"])
app.include_router(media_router, tags=["media"])
app.include_router(agent_router, tags=["agent"])
app.include_router(search_router, tags=["search"])
app.include_router(metrics_router, tags=["system"])
app.include_router(chat_router, tags=["chat"])
app.include_router(training_router, tags=["training"])
app.include_router(schedules_router, tags=["automation"])
app.include_router(screen_router, tags=["screen"])
app.include_router(settings_router, tags=["settings"])
app.include_router(tts_router, tags=["media"])
app.include_router(backup_router, tags=["backup"])
app.include_router(insights_router, tags=["insights"])

# auth gate (token_ok) + AUTH_EXEMPT live in nova/services/settings.py; used by the middleware below
from nova.services.settings import token_ok, AUTH_EXEMPT, exec_allowed
from nova.core.errors import record as record_error
START_TS = time.time()   # process start, for /api/health uptime

# ---- in-memory rate limiter (per IP + path): (max_requests, window_seconds) ----
RATE_RULES = {"/api/auth/login": (10, 60), "/api/exec": (60, 60),
              "/api/agent": (40, 60), "/api/learn/retrain": (6, 60), "/api/browse": (40, 60)}
_RATE = collections.defaultdict(list)
def _rate_ok(ip, path):
    rule = RATE_RULES.get(path)
    if not rule: return True
    limit, win = rule; now = time.time(); q = _RATE[(ip, path)]
    while q and q[0] < now - win: q.pop(0)
    if len(q) >= limit: return False
    q.append(now); return True

@app.middleware("http")
async def gate(request: Request, call_next):
    path = request.url.path
    ip = request.client.host if request.client else "?"
    t0 = time.time()
    if path.startswith("/api/"):
        if path not in AUTH_EXEMPT and not token_ok(request):
            return JSONResponse({"error": "authentication required"}, status_code=401)
        if not _rate_ok(ip, path):
            log.warning(f"rate limit: {ip} {path}")
            return JSONResponse({"error": "Too many requests — please slow down."}, status_code=429)
    try:
        resp = await call_next(request)
    except Exception as e:
        log.exception(f"unhandled error: {request.method} {path}")
        record_error(f"{request.method} {path}", e)
        return JSONResponse({"error": "Internal server error", "detail": str(e)[:300]}, status_code=500)
    if path.startswith("/api/"):
        dt = (time.time() - t0) * 1000
        if resp.status_code >= 400 or dt > 1500:
            log.info(f"{request.method} {path} -> {resp.status_code} ({dt:.0f}ms)")
    resp.headers["Content-Security-Policy"] = "frame-ancestors *"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    if "x-frame-options" in resp.headers:
        del resp.headers["x-frame-options"]
    if path == "/" or path.endswith(".html"):
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return resp

async def metrics_loop():
    last_hist = 0.0
    while True:
        try:
            m = await asyncio.get_running_loop().run_in_executor(None, collect_metrics)
            set_last_metrics(m)
            await _send_all(m)
            now = time.time()
            if now - last_hist >= 30:        # persist a trend sample ~every 30s
                last_hist = now
                await asyncio.to_thread(record_history, m)
        except Exception: pass
        await asyncio.sleep(float(get_settings().get("metrics_interval", 1.5)))

async def status_loop():
    while True:
        try:
            st = {"type": "services",
                  "ollama": http_ok(f"{OLLAMA}/api/tags"),
                  "comfy":  http_ok(f"{COMFY_URL}/system_stats"),
                  "owui":   http_ok(f"{OWUI_URL}/")}
            await _send_all(st)
        except Exception: pass
        await asyncio.sleep(5)

async def scheduler_loop():
    """Run due automations every ~15s (proactive background engine)."""
    while True:
        try:
            now = time.time()
            c = db()
            due = [dict(r) for r in c.execute(
                "SELECT * FROM schedules WHERE enabled=1 AND next_run IS NOT NULL AND next_run<=?", (now,)).fetchall()]
            c.close()
            for row in due:
                await asyncio.get_running_loop().run_in_executor(None, run_schedule, row)
        except Exception: pass
        await asyncio.sleep(15)

async def backup_loop():
    """Daily consistent snapshot of the SQLite DB (rotated, last 14 kept)."""
    from nova.services.backup import snapshot_db
    while True:
        try:
            p = await asyncio.to_thread(snapshot_db)
            log.info(f"DB snapshot written: {p}")
        except Exception as e:
            log.warning(f"DB snapshot failed: {e}")
        await asyncio.sleep(24 * 3600)

# ---- websocket
@app.websocket("/ws")
async def ws(ws: WebSocket):
    s = get_settings()
    if s.get("auth_enabled"):
        tok = ws.cookies.get("cc_token", "")
        if not (s.get("auth_token") and secrets.compare_digest(str(tok), str(s["auth_token"]))):
            await ws.close(code=1008); return
    await ws.accept(); clients.add(ws)
    try:
        await ws.send_text(json.dumps(collect_metrics(), default=str))
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        clients.discard(ws)

# settings + auth routes now live in nova/api/settings.py (logic in nova/services/settings.py)

# ---- metrics snapshot
# metrics / services / processes routes now live in nova/api/metrics.py
# model routes now live in nova/api/models.py
# open-webui routes now live in nova/api/owui.py

# ---- terminal / commands
@app.post("/api/exec")
async def api_exec(req: Request):
    if not exec_allowed():
        audit("terminal", "run_command", "blocked (remote exec disabled)", "blocked")
        return JSONResponse({"error": "Command execution is disabled while exposed on the LAN. "
                                      "Enable 'allow_remote_exec' in Settings to permit it."}, status_code=403)
    b = await req.json(); cmd = (b.get("command") or "").strip()
    if not cmd: return JSONResponse({"error": "empty"}, status_code=400)
    # SEC-1: clearly-destructive commands require an explicit confirm (the Terminal asks first).
    if is_dangerous(cmd) and not b.get("confirm"):
        audit("terminal", "run_command", cmd, "needs_confirm")
        return JSONResponse({"needs_confirm": True,
                             "reason": "This looks destructive (e.g. format / rm -rf / shutdown / registry). "
                                       "Run it anyway?"}, status_code=409)
    job = PM.start(cmd, ps_args(cmd), kind="command", source="terminal")
    audit("terminal", "run_command", cmd, "forced" if (is_dangerous(cmd) and b.get("confirm")) else "ok")
    return {"ok": True, "job": job.id}

# ---- toolkit quick actions
@app.post("/api/toolkit/{tool}")
async def api_toolkit(tool: str, req: Request):
    b = await req.json()
    if tool == "video":
        prompt = b.get("prompt", "a cinematic shot")
        cmd = '& "{}" "{}"'.format(TOOLKIT / "genvideo.ps1", prompt.replace('"', '`"'))
        if b.get("ckpt"):   cmd += ' -Ckpt "{}"'.format(b["ckpt"])
        if b.get("length"): cmd += ' -Length {}'.format(int(b["length"]))
        if b.get("steps"):  cmd += ' -Steps {}'.format(int(b["steps"]))
        if b.get("fps"):    cmd += ' -Fps {}'.format(int(b["fps"]))
        if b.get("out"):    cmd += ' -Out "{}"'.format(b["out"])
        job = PM.start("video: " + prompt[:40], ps_args(cmd), kind="video", source="video")
        return {"ok": True, "job": job.id}
    if tool == "image":
        prompt = b.get("prompt", "a photorealistic landscape at golden hour")
        model = b.get("model", "sdxl")
        if model not in ("sdxl", "flux-schnell", "flux-dev"): model = "sdxl"
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        fn = f"img_{uuid.uuid4().hex[:8]}.png"; outp = UPLOAD_DIR / fn
        cmd = '& "{}" "{}" -Model {} -Out "{}"'.format(TOOLKIT / "generate.ps1", prompt.replace('"', '`"'), model, outp)
        job = PM.start("image: " + prompt[:40], ps_args(cmd), kind="image", source="image")
        audit("image", "generate", f"{model}: {prompt[:60]}")
        return {"ok": True, "job": job.id, "file": f"/files/{fn}", "model": model}
    if tool == "speak":
        job = PM.start("speak", ps_args(f'& "{TOOLKIT / "speak.ps1"}" {_q(b.get("text",""))}'),
                       kind="command", source="speak")
        return {"ok": True, "job": job.id}
    return JSONResponse({"error": "unknown tool"}, status_code=400)

# logs route now lives in nova/api/history.py (included after `app` is defined)
# bug-report routes now live in nova/api/bugs.py (included after `app` is defined)
@app.post("/api/stt")
async def api_stt(req: Request):
    """Local speech-to-text: accepts a recorded audio blob, returns the transcript (no cloud)."""
    form = await req.form(); f = form.get("audio") or form.get("file")
    if not f: return JSONResponse({"error": "no audio"}, status_code=400)
    lang = (form.get("lang") or "").strip() or None
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    tmp = UPLOAD_DIR / f"stt_{uuid.uuid4().hex[:8]}.webm"
    tmp.write_bytes(await f.read())
    try:
        model = await asyncio.to_thread(get_whisper)
        def run():
            segs, info = model.transcribe(str(tmp), language=lang, vad_filter=True)
            return "".join(s.text for s in segs).strip(), info.language
        text, detected = await asyncio.to_thread(run)
        audit("stt", "transcribe", f"{detected}: {text[:60]}")
        return {"ok": True, "text": text, "language": detected}
    except Exception as e:
        log.exception("stt failed")
        return JSONResponse({"ok": False, "error": str(e)[:200]}, status_code=500)
    finally:
        try: tmp.unlink()
        except Exception: pass

# ---- Screen Studio ----
# Routes extracted to nova/api/screen.py. The service is still imported here so the
# lifespan shutdown can finalize an in-flight recording (see graceful shutdown above).
from nova.services import screen as screen_svc

# ---- processes
# tracked-process routes now live in nova/api/metrics.py

# ---- history
# history routes now live in nova/api/history.py (included after `app` is defined)
# notification-center routes now live in nova/api/notifications.py

# ---- conversations / projects
# conversation + chat-history/clear routes now live in nova/api/conversations.py

# ---- file upload (chat context): extract text from PDF/DOCX/TXT/image
# UPLOAD_DIR now lives in config; file text extraction in nova/services/files.py.
from nova.services.files import extract_text

@app.post("/api/upload")
async def api_upload(req: Request):
    form = await req.form()
    f = form.get("file")
    if not f: return JSONResponse({"error": "no file"}, status_code=400)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / f.filename
    dest.write_bytes(await f.read())
    text = extract_text(dest)
    return {"ok": True, "filename": f.filename, "size": dest.stat().st_size, "chars": len(text),
            "text": text[:8000], "truncated": len(text) > 8000, "url": f"/files/{f.filename}"}

@app.get("/files/{name}")
def api_file(name: str):
    p = (UPLOAD_DIR / name)
    try:
        if UPLOAD_DIR.resolve() not in p.resolve().parents:
            return JSONResponse({"error": "bad path"}, status_code=400)
    except Exception:
        return JSONResponse({"error": "bad path"}, status_code=400)
    if not p.exists(): return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(str(p))

@app.get("/api/db-status")
def api_db_status():
    """Self-diagnostic: counts per table + the last saved conversation turns."""
    c = db()
    def cnt(t):
        try: return c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except Exception: return None
    tables = {"chat": cnt("chat"), "history": cnt("history"),
              "settings": cnt("settings"), "notifications": cnt("notifications")}
    last = [{"id": r["id"], "ts": r["ts"], "session_id": r["session_id"],
             "role": r["role"], "model_used": r["model_used"],
             "content": (r["content"] or "")[:160]}
            for r in c.execute("SELECT * FROM chat ORDER BY id DESC LIMIT 6").fetchall()]
    last.reverse()
    try: sessions = c.execute("SELECT COUNT(DISTINCT session_id) FROM chat").fetchone()[0]
    except Exception: sessions = None
    c.close()
    size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    return {
        "ok": True,
        "db_path": str(DB_PATH),
        "db_size_kb": round(size / 1024, 1),
        "current_session": SESSION_ID,
        "chat_messages": tables["chat"],
        "chat_sessions": sessions,
        "tables": tables,
        "last_conversation": last,
    }

# chat-send (streaming) route now lives in nova/api/chat.py (worker in nova/services/chat.py)

# ---- training studio + continuous learning ----
# Fully extracted to nova/services/training.py + nova/api/training.py + nova/services/insights.py.

# /api/processes/system route now lives in nova/api/metrics.py

# comfy/status + media-models routes now live in nova/api/media.py

@app.get("/api/toolkit/list")
def api_toolkit_list():
    items = [
        {"key": "video", "icon": "🎬", "name": "Generate Video", "desc": "LTX 2B/13B local video"},
        {"key": "speak", "icon": "🔊", "name": "Speak (TTS)", "desc": "Piper neural, AR+EN"},
        {"key": "see", "icon": "📸", "name": "Screenshot+Vision", "desc": "capture & describe screen"},
        {"key": "ocr", "icon": "🔤", "name": "OCR", "desc": "extract text from image"},
        {"key": "translate", "icon": "🌐", "name": "Translate", "desc": "AR <-> EN"},
        {"key": "netspeed", "icon": "📶", "name": "Net Speed", "desc": "measure throughput"},
    ]
    return items

# ---- knowledge base (local RAG via nomic-embed-text) ----
# KB service extracted to nova/services/kb.py; imported back here. Routes that are
# pure CRUD live in nova/api/kb.py; the multipart ingest stays here (shares UPLOAD_DIR).
from nova.services.kb import embed, chunk_text, kb_search

@app.post("/api/kb/ingest")
async def api_kb_ingest(req: Request):
    form = await req.form(); f = form.get("file")
    if not f: return JSONResponse({"error": "no file"}, status_code=400)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / f.filename; dest.write_bytes(await f.read())
    chunks = chunk_text(extract_text(dest))
    if not chunks: return JSONResponse({"error": "no text extracted"}, status_code=400)
    name = f.filename
    def work():
        c = db(); did = c.execute("INSERT INTO kb_docs(name,chunks,created) VALUES(?,?,?)", (name, 0, time.time())).lastrowid; c.commit()
        n = 0
        for i, ch in enumerate(chunks):
            v = embed(ch)
            if not v: continue
            c.execute("INSERT INTO kb_chunks(doc_id,ord,text,emb) VALUES(?,?,?,?)", (did, i, ch, json.dumps(v))); n += 1
        c.execute("UPDATE kb_docs SET chunks=? WHERE id=?", (n, did)); c.commit(); c.close()
        add_notification("success", "Document indexed", f"{name} · {n} chunks")
        push({"type": "kb_done", "name": name, "chunks": n})
    threading.Thread(target=work, daemon=True).start()
    add_notification("info", "Indexing document", f"{name} · {len(chunks)} chunks")
    return {"ok": True, "name": name, "chunks_planned": len(chunks)}

# ---- export a conversation to PDF (reportlab) ----
@app.get("/api/chat-export-pdf/{cid}")
def api_chat_pdf(cid: str):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas as _cv
    from reportlab.lib.utils import simpleSplit
    msgs = conv_messages(cid, 500)
    out = UPLOAD_DIR / f"chat_{cid}.pdf"; UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    c = _cv.Canvas(str(out), pagesize=A4); W, H = A4; y = H - 2 * cm
    c.setFont("Helvetica-Bold", 14); c.drawString(2 * cm, y, "AI Control Center — Conversation"); y -= 1 * cm
    for m in msgs:
        c.setFont("Helvetica-Bold", 10); c.setFillColorRGB(0.3, 0.3, 0.6)
        c.drawString(2 * cm, y, ("You" if m["role"] == "user" else "Assistant") + ":"); y -= 0.5 * cm
        c.setFont("Helvetica", 10); c.setFillColorRGB(0, 0, 0)
        for line in simpleSplit(m["content"].encode("ascii", "replace").decode(), "Helvetica", 10, W - 4 * cm):
            if y < 2 * cm: c.showPage(); y = H - 2 * cm; c.setFont("Helvetica", 10)
            c.drawString(2 * cm, y, line); y -= 0.45 * cm
        y -= 0.3 * cm
    c.save()
    return FileResponse(str(out), filename="conversation.pdf", media_type="application/pdf")

# ---- voice output (Piper TTS) ----
# tts route now lives in nova/api/tts.py (logic in nova/services/tts.py)

# ---- automation engine (scheduler) ----
# run_action / run_schedule / schedules routes extracted to
# nova/services/schedules.py + nova/api/schedules.py.

# Browser automation lives in nova/services/browser.py (used by schedules/agent services).

# ---- Agent Mode + browser routes extracted to nova/services/agent.py + nova/api/agent.py.
from nova.services.agent import set_run_action, safe_read_path, safe_write_path, is_dangerous  # safe_*/is_dangerous used by /api/selftest + exec guard
from nova.services.schedules import run_action, run_schedule
set_run_action(run_action)   # inject the ProcMgr-backed dispatcher into the agent service

# ---- Search Everything (unified) ----
# search route now lives in nova/api/search.py

# insights / briefing / copilot routes now live in nova/api/insights.py
# Workflows + A/B testing extracted to nova/services/schedules.py + nova/api/schedules.py.

# ---- Audit log ----
# audit routes now live in nova/api/audit.py (included after `app` is defined)

# Daily Briefing extracted to nova/services/insights.py (self-registers the briefing hook)

# ---- Backup & Restore (full export/import) ----
# backup / restore routes now live in nova/api/backup.py (logic in nova/services/backup.py)

# ---- System Self-Test (diagnostics) ----
@app.get("/api/selftest")
def api_selftest():
    checks = []
    def chk(name, fn):
        try:
            ok, detail = fn(); checks.append({"name": name, "ok": bool(ok), "detail": str(detail)[:140]})
        except Exception as e:
            checks.append({"name": name, "ok": False, "detail": f"error: {e}"[:140]})
    def t_db():
        c = db(); names = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}; c.close()
        need = {"settings", "history", "notifications", "chat", "conversations", "training_runs",
                "kb_docs", "kb_chunks", "schedules", "workflows", "audit"}
        miss = need - names; return (not miss, "all 11 tables present" if not miss else f"missing {miss}")
    chk("Database schema", t_db)
    chk("Ollama service", lambda: (http_ok(f"{OLLAMA}/api/tags"), "reachable on 11434"))
    chk("ComfyUI service", lambda: (http_ok(f"{COMFY_URL}/system_stats"), "reachable on 8188"))
    chk("Open WebUI service", lambda: (http_ok(f"{OWUI_URL}/"), "reachable on 3000"))
    chk("Embeddings (nomic-embed-text)", lambda: (len(embed("self test")) == 768, f"{len(embed('self test'))} dims"))
    chk("KB retrieval", lambda: (isinstance(kb_search("test", 1), list), "search returns results list"))
    chk("GPU metrics (nvidia-smi)", lambda: ((collect_metrics().get("gpu") is not None),
                                             (collect_metrics().get("gpu") or {}).get("name", "n/a")))
    chk("Models list (Ollama)", lambda: (len(ollama_models()) > 0, f"{len(ollama_models())} models tagged"))
    def t_audit():
        audit("selftest", "probe", "diagnostic write")
        c = db(); n = c.execute("SELECT COUNT(*) FROM audit WHERE actor='selftest'").fetchone()[0]; c.close()
        return (n > 0, "audit log writable")
    chk("Audit log", t_audit)
    chk("Agent safety guards", lambda: (safe_write_path(r"C:\Windows\x.txt") is None and safe_read_path(r"C:\x\.ssh\id_rsa") is None, "write confinement + read denylist active"))
    chk("Disk space", lambda: (shutil.disk_usage("C:\\").free / 1e9 > 5, f"{shutil.disk_usage('C:/').free/1e9:.0f} GB free"))
    chk("Training datasets", lambda: (DS_BASE.exists() or DS_COMBINED.exists(), "present"))
    chk("Scheduler loop", lambda: (get_loop() is not None, "background loops running"))
    passed = sum(1 for c in checks if c["ok"])
    return {"checks": checks, "passed": passed, "total": len(checks), "ok": passed == len(checks), "ts": time.time()}

# Nova Co-Pilot route now lives in nova/api/insights.py
# brain / habits / achievements routes now live in nova/api/analytics.py

# ---- server health + error aggregation (observability) ----
@app.get("/api/health")
def api_health():
    m = get_last_metrics() or {}
    age = (time.time() - m["ts"]) if m.get("ts") else None
    jobs = list(PM.jobs.values())
    return {
        "ok": True,
        "uptime_sec": round(time.time() - START_TS),
        "metrics_loop_alive": bool(age is not None and age < 15),   # fresh sample → loop running
        "last_metrics_age_sec": round(age, 1) if age is not None else None,
        "jobs_total": len(jobs),
        "jobs_running": sum(1 for j in jobs if j.status in ("running", "starting")),
        "ws_clients": len(clients),
        "errors_total": _errors_total(),
    }

@app.get("/api/errors")
def api_errors():
    from nova.core.errors import snapshot
    return {"errors": snapshot(), "total": _errors_total()}

@app.delete("/api/errors")
def api_errors_clear():
    from nova.core.errors import clear
    clear(); return {"ok": True}

def _errors_total():
    from nova.core.errors import total
    return total()

# ---- static dashboard
# index.html is served through a small handler that stamps every ?v=… asset URL with the
# newest asset mtime → automatic cache-busting (no manual version bumps, no stale CSS/JS).
import re as _re
_INDEX = STATIC / "index.html"
def _asset_version():
    paths = [STATIC / "css/app.css", STATIC / "js/core.js", STATIC / "js/pages.js",
             STATIC / "js/shell.js", STATIC / "fonts/fonts.css", STATIC / "vendor/fa/css/all.min.css"]
    try: return str(int(max(p.stat().st_mtime for p in paths if p.exists())))
    except Exception: return "1"
@app.get("/", response_class=HTMLResponse)
def index():
    try:
        html = _INDEX.read_text(encoding="utf-8")
        return HTMLResponse(_re.sub(r"\?v=[0-9]+", "?v=" + _asset_version(), html))
    except Exception:
        return HTMLResponse("<h1>index.html missing</h1>", status_code=500)
app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    init_db()
    _s = get_settings()
    BIND_HOST = BIND_OVERRIDE or ("0.0.0.0" if (_s.get("auth_enabled") and _s.get("lan_access")) else "127.0.0.1")
    ssl_kw = {}
    scheme = "http"
    if HTTPS_ENABLED:
        try:
            crt, key = ensure_cert()
            ssl_kw = {"ssl_certfile": crt, "ssl_keyfile": key}; scheme = "https"
        except Exception as e:
            log.warning(f"HTTPS requested but cert setup failed ({e}); falling back to HTTP")
    mode = "LAN + token auth" if BIND_HOST == "0.0.0.0" else "localhost-only"
    print(f"\n  AI Control Center  ->  {scheme}://localhost:{PORT}   (bound to {BIND_HOST}, {mode})\n")
    log.info(f"serving {scheme}://{BIND_HOST}:{PORT}")
    uvicorn.run(app, host=BIND_HOST, port=PORT, log_level="warning", **ssl_kw)
