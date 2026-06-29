# -*- coding: utf-8 -*-
"""Media routes — live ComfyUI status (queue + outputs) and the non-Ollama media
model library (image/video checkpoints + Piper voices). Depends on config paths +
nova.core.http only."""
from fastapi import APIRouter
from config import COMFY, COMFY_URL, TOOLKIT
from nova.core.http import http_json, http_ok

router = APIRouter()

@router.get("/api/comfy/status")
def api_comfy_status():
    """Live ComfyUI queue + output folder (real video-generation progress)."""
    online = http_ok(f"{COMFY_URL}/system_stats")
    res = {"online": online, "queue_running": 0, "queue_pending": 0, "outputs": 0, "last_output": None}
    if online:
        try:
            q = http_json(f"{COMFY_URL}/queue", timeout=4)
            res["queue_running"] = len(q.get("queue_running", []))
            res["queue_pending"] = len(q.get("queue_pending", []))
        except Exception: pass
        try:
            outdir = COMFY / "output"
            files = sorted([f for f in outdir.glob("*.*")], key=lambda f: f.stat().st_mtime, reverse=True)
            res["outputs"] = len(files)
            if files: res["last_output"] = files[0].name
        except Exception: pass
    return res

@router.get("/api/media-models")
def api_media_models():
    """Non-Ollama generation/media models (image/video/audio) for a complete library."""
    out = []
    try:
        for f in (COMFY / "models" / "checkpoints").glob("*.safetensors"):
            nm = f.name.lower(); gb = round(f.stat().st_size / 1e9, 1)
            if gb < 0.5: continue
            tag = "video" if "ltx" in nm else "image"
            out.append({"name": f.name, "size_gb": gb, "tags": [tag], "kind": "comfyui"})
    except Exception: pass
    try:
        voices = list((TOOLKIT / "voices").glob("*.onnx"))
        if voices:
            out.append({"name": f"Piper TTS · {len(voices)} voices (AR+EN)",
                        "size_gb": round(sum(v.stat().st_size for v in voices) / 1e9, 2),
                        "tags": ["audio"], "kind": "piper"})
    except Exception: pass
    out.sort(key=lambda x: (x["tags"][0], x["name"]))
    return out
