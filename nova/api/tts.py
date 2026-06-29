# -*- coding: utf-8 -*-
"""Text-to-speech route — speak text aloud via the local Piper voice. Logic in
nova.services.tts."""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from nova.services.tts import speak

router = APIRouter()

@router.post("/api/tts")
async def api_tts(req: Request):
    b = await req.json(); text = (b.get("text") or "").strip()[:1200]
    if not text: return JSONResponse({"error": "empty"}, status_code=400)
    try:
        speak(text)
        return {"ok": True}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
