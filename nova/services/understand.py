# -*- coding: utf-8 -*-
"""Unified "read & understand" — one entry point that, given a file, image, screenshot, or the live
screen, returns BOTH the text it contains (OCR / file extraction) AND what it shows (qwen2.5-VL for
images, an LLM summary for documents): the text present, what the content shows, its main purpose, and
notable details.

Powers the chat (attach an image/file and say "read this" / "describe this") and the agent's
`understand` tool. Builds on nova.services.files (extract_text), nova.services.screen (vlm_image,
read_screen, describe_screen). Depends on config + nova.core (db, http)."""
from pathlib import Path
from config import UPLOAD_DIR
from nova.services.files import extract_text
from nova.services import screen as screen_svc

IMG_EXT = (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif")

COMBINED_VLM_PROMPT = (
    "Analyze this image and answer in four short sections with these EXACT headers:\n"
    "TEXT: transcribe all readable text exactly (or 'none').\n"
    "SHOWS: what the image shows — objects, scene, layout, UI elements.\n"
    "PURPOSE: the main content or purpose, in one line.\n"
    "DETAILS: any notable details.")


def _resolve(path):
    """Accept an absolute path, a `/files/<name>` URL, or a bare filename (looked up in UPLOAD_DIR)."""
    s = str(path or "").strip()
    if not s:
        return None
    s = s.replace("/files/", "")
    p = Path(s)
    if not p.is_absolute():
        p = UPLOAD_DIR / p.name
    return p


def understand_image(path, question=None):
    """OCR + VLM understanding of an image file."""
    p = _resolve(path)
    res = {"kind": "image", "file": (p.name if p else None)}
    try:
        res["text"] = extract_text(p)
    except Exception as e:
        res["text"] = f"(ocr failed: {e})"
    try:
        res["description"] = screen_svc.vlm_image(p, question or COMBINED_VLM_PROMPT, num_predict=700)
        res["ok"] = True
    except Exception as e:
        res["description"] = ""; res["ok"] = False; res["error"] = str(e)[:200]
    return res


def summarize_text(text, question=None):
    """One quick local-LLM pass: main content/purpose + notable details of a document."""
    text = (text or "").strip()
    if not text or text.startswith("("):
        return ""
    from nova.core.db import get_settings
    from nova.core.http import http_json
    from config import OLLAMA
    model = get_settings().get("default_local_model", "llama3.1:8b")
    q = question or ("Summarize this document: what is the main content/purpose, and any notable details? "
                     "Be concise.")
    try:
        r = http_json(OLLAMA + "/api/chat", body={"model": model, "stream": False,
                      "messages": [{"role": "user", "content": q + "\n\n---\n" + text[:6000]}]}, timeout=120)
        return ((r.get("message") or {}).get("content") or "").strip()
    except Exception as e:
        return f"(summary unavailable: {e})"


def understand_file(path, question=None):
    """Read & understand any file: images via OCR+VLM, documents via extract + LLM summary."""
    p = _resolve(path)
    if p is None or not p.exists():
        return {"ok": False, "error": "file not found", "file": str(path)}
    if p.suffix.lower() in IMG_EXT:
        return understand_image(p, question)
    text = extract_text(p)
    return {"kind": "file", "file": p.name, "text": text, "ok": True,
            "description": summarize_text(text, question)}


def understand(path=None, region=None, question=None):
    """Unified entry: a file/image path, or the live screen (region=None → whole screen)."""
    if path:
        return understand_file(path, question)
    res = {"kind": "screen"}
    try:
        res["text"] = screen_svc.read_screen(vision=False, region=region).get("text", "")
    except Exception as e:
        res["text"] = f"(ocr failed: {e})"
    d = screen_svc.describe_screen(question or COMBINED_VLM_PROMPT, region)
    res["description"] = d.get("description", ""); res["ok"] = d.get("ok", False); res["file"] = d.get("file")
    return res
