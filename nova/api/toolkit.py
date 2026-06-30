# -*- coding: utf-8 -*-
"""Toolkit quick-action routes — fire-and-forget media jobs (video/image/speak) via the local
toolkit scripts, tracked by the ProcMgr. Extracted from server.py (HON-11). Logic stays thin; the
heavy lifting is the toolkit PowerShell scripts + ComfyUI."""
import uuid
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from config import UPLOAD_DIR, toolkit_script
from nova.core.process import ps_args, _q
from nova.services.jobs import PM
from nova.services.audit import audit

router = APIRouter()


@router.post("/api/toolkit/{tool}")
async def api_toolkit(tool: str, req: Request):
    b = await req.json()
    if tool == "video":
        prompt = b.get("prompt", "a cinematic shot")
        cmd = '& "{}" "{}"'.format(toolkit_script("genvideo.ps1"), prompt.replace('"', '`"'))
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
        cmd = '& "{}" "{}" -Model {} -Out "{}"'.format(toolkit_script("generate.ps1"), prompt.replace('"', '`"'), model, outp)
        init = b.get("init_image")            # IDEA-9 img2img: refine an existing image
        if init:
            name = str(init).replace("\\", "/").split("/")[-1]   # accept "/files/x.png" or a bare name
            initp = UPLOAD_DIR / name
            if not initp.exists():
                return JSONResponse({"ok": False, "error": f"init image not found: {name}"}, status_code=404)
            try: dn = max(0.0, min(float(b.get("denoise", 0.6)), 1.0))
            except Exception: dn = 0.6
            cmd += ' -InitImage "{}" -Denoise {}'.format(initp, dn)
        label = ("refine: " if init else "image: ") + prompt[:40]
        job = PM.start(label, ps_args(cmd), kind="image", source="image")
        audit("image", "refine" if init else "generate", f"{model}: {prompt[:60]}")
        return {"ok": True, "job": job.id, "file": f"/files/{fn}", "model": model}
    if tool == "speak":
        job = PM.start("speak", ps_args(f'& "{toolkit_script("speak.ps1")}" {_q(b.get("text",""))}'),
                       kind="command", source="speak")
        return {"ok": True, "job": job.id}
    return JSONResponse({"error": "unknown tool"}, status_code=400)
