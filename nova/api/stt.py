# -*- coding: utf-8 -*-
"""Speech-to-text route — accepts a recorded audio blob, returns the transcript (fully local Whisper).
Extracted from server.py (HON-11); model loading lives in nova.services.stt."""
import asyncio
import logging
import uuid
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from config import UPLOAD_DIR
from nova.services.stt import get_whisper
from nova.services.audit import audit

router = APIRouter()
log = logging.getLogger("nova")


@router.post("/api/stt")
async def api_stt(req: Request):
    form = await req.form(); f = form.get("audio") or form.get("file")
    if not f:
        return JSONResponse({"error": "no audio"}, status_code=400)
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
