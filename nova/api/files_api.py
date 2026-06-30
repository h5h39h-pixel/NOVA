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


@router.get("/api/file/read")
def api_file_read(path: str = ""):
    """Open an existing text file to work on it (Claude-Desktop style). Credential stores are denied."""
    from nova.services.agent import safe_read_path
    from pathlib import Path
    p = safe_read_path(path)
    if p is None:
        return JSONResponse({"ok": False, "error": "that path is not readable (credential store)"}, status_code=403)
    p = Path(path)
    if not p.exists() or not p.is_file():
        return JSONResponse({"ok": False, "error": "file not found"}, status_code=404)
    try:
        return {"ok": True, "path": str(p), "name": p.name,
                "content": p.read_text(encoding="utf-8", errors="replace")[:200000]}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)[:160]}, status_code=500)


@router.post("/api/file/write")
async def api_file_write(req: Request):
    """Save edits back to a file. Gated by exec_allowed() (localhost ok; LAN needs opt-in) + audited."""
    from nova.services.settings import exec_allowed
    from nova.services.audit import audit
    from nova.services.agent import safe_read_path
    from pathlib import Path
    if not exec_allowed():
        return JSONResponse({"ok": False, "error": "file write disabled on LAN (enable allow_remote_exec)"}, status_code=403)
    b = await req.json()
    path = (b.get("path") or "").strip()
    if not path or safe_read_path(path) is None:
        return JSONResponse({"ok": False, "error": "bad/forbidden path"}, status_code=400)
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(b.get("content", ""), encoding="utf-8")
        audit("workspace", "file_write", f"{p} ({len(b.get('content',''))} chars)")
        return {"ok": True, "path": str(p), "bytes": p.stat().st_size}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)[:160]}, status_code=500)


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
