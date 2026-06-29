# -*- coding: utf-8 -*-
"""Model routes — list installed Ollama models (with capability tags) and load/unload
them. Backed by nova.services.ollama + nova.core.http; pushes a live model refresh."""
import threading
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from config import OLLAMA
from nova.core.http import http_json
from nova.core.events import push
from nova.services.audit import audit
from nova.services.notifications import add_notification
from nova.services.ollama import ollama_models

router = APIRouter()

@router.get("/api/models")
def api_models(): return ollama_models()

@router.post("/api/models/{action}")
async def api_model_action(action: str, req: Request):
    body = await req.json(); model = body.get("model")
    if not model: return JSONResponse({"error": "model required"}, status_code=400)
    audit("models", action, model)
    keep = "30m" if action == "load" else 0
    def work():
        try:
            http_json(f"{OLLAMA}/api/generate",
                      body={"model": model, "prompt": "", "keep_alive": keep, "stream": False}, timeout=120)
            add_notification("success", f"Model {action}ed", model)
        except Exception as e:
            add_notification("error", f"Model {action} failed", str(e))
        push({"type": "models", "models": ollama_models()})
    threading.Thread(target=work, daemon=True).start()
    return {"ok": True}
