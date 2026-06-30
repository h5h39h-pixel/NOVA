# -*- coding: utf-8 -*-
"""Toolkit quick-action routes — fire-and-forget media jobs (video/image/speak) via the local
toolkit scripts, tracked by the ProcMgr. Extracted from server.py (HON-11). Logic stays thin; the
heavy lifting is the toolkit PowerShell scripts + ComfyUI."""
import uuid
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from config import TOOLKIT, UPLOAD_DIR
from nova.core.process import ps_args, _q
from nova.services.jobs import PM
from nova.services.audit import audit

router = APIRouter()


@router.post("/api/toolkit/{tool}")
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
