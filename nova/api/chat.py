# -*- coding: utf-8 -*-
"""Chat-send route — accepts a prompt (+ optional attached context, second model for
comparison, and RAG toggle) and streams the reply over the WS bus. The heavy lifting
lives in nova.services.chat.stream_chat_send; this just validates and dispatches."""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from nova.core.db import get_settings
from nova.services.chat import conv_ensure, stream_chat_send

router = APIRouter()

@router.post("/api/chat-send")
async def api_chat_send(req: Request):
    b = await req.json(); prompt = (b.get("prompt") or "").strip()
    if not prompt: return JSONResponse({"error": "empty"}, status_code=400)
    model = b.get("model") or get_settings().get("default_local_model", "llama3.1:8b")
    cid = conv_ensure(b.get("cid"))
    stream_chat_send(prompt, model, cid,
                     context=(b.get("context") or "").strip(),
                     target=b.get("target"),
                     use_rag=bool(b.get("rag")),
                     deepthink=bool(b.get("deepthink")),
                     websearch=bool(b.get("websearch")))
    return {"ok": True, "model": model, "cid": cid}
