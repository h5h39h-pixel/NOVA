# -*- coding: utf-8 -*-
"""Unified read & understand route — POST /api/understand with a file/image path (or nothing for the
live screen) → returns the text it contains + what it shows + its purpose. Logic in
nova.services.understand."""
from fastapi import APIRouter, Request
from nova.services.understand import understand
from nova.services.audit import audit

router = APIRouter()


@router.post("/api/understand")
async def api_understand(req: Request):
    b = {}
    try:
        b = await req.json()
    except Exception:
        pass
    r = understand(path=b.get("path"), region=b.get("region"), question=b.get("question"))
    audit("understand", r.get("kind", "?"), str(b.get("path") or "screen")[:60])
    return r
