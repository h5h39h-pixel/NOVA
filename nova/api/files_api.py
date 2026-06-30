# -*- coding: utf-8 -*-
"""File upload (chat context) + static file serving. Upload extracts text from PDF/DOCX/TXT/code, and
for images includes a VLM description + OCR so chat "read this / describe this" works. `/files/{name}`
serves uploaded/generated media. Extracted from server.py (HON-11)."""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, FileResponse
from config import UPLOAD_DIR
from nova.services.files import extract_text

router = APIRouter()

_IMG = (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif")


@router.post("/api/upload")
async def api_upload(req: Request):
    form = await req.form()
    f = form.get("file")
    if not f:
        return JSONResponse({"error": "no file"}, status_code=400)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / f.filename
    dest.write_bytes(await f.read())
    # Images: include BOTH a VLM description and OCR text so chat "read this / describe this" works.
    if dest.suffix.lower() in _IMG:
        try:
            from nova.services.understand import understand_image
            u = understand_image(dest)
            parts = []
            if u.get("description"): parts.append("[What the image shows]\n" + u["description"])
            if u.get("text") and not str(u["text"]).startswith("("): parts.append("[Text in the image]\n" + u["text"])
            text = "\n\n".join(parts) or extract_text(dest)
        except Exception:
            text = extract_text(dest)
    else:
        text = extract_text(dest)
    return {"ok": True, "filename": f.filename, "size": dest.stat().st_size, "chars": len(text),
            "text": text[:8000], "truncated": len(text) > 8000, "url": f"/files/{f.filename}"}


@router.get("/files/{name}")
def api_file(name: str):
    p = (UPLOAD_DIR / name)
    try:
        if UPLOAD_DIR.resolve() not in p.resolve().parents:
            return JSONResponse({"error": "bad path"}, status_code=400)
    except Exception:
        return JSONResponse({"error": "bad path"}, status_code=400)
    if not p.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(str(p))
