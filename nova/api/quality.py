# -*- coding: utf-8 -*-
"""IDEA-6 — quality dashboard routes: record a scored eval run, read history/summary, and trigger a
lightweight health snapshot. Logic in nova.services.quality. Local-only."""
from fastapi import APIRouter, Request
from nova.services import quality as Q

router = APIRouter()


@router.get("/api/quality")
def api_quality(suite: str = "", limit: int = 200):
    return {"summary": Q.summary(), "history": Q.history(suite or None, limit)}


@router.post("/api/quality")
async def api_quality_record(req: Request):
    try:
        b = await req.json()
    except Exception:
        return {"ok": False, "error": "invalid JSON body"}
    if not isinstance(b, dict) or "suite" not in b or "score" not in b or "total" not in b:
        return {"ok": False, "error": "need suite, score, total"}
    try:
        run = Q.record(b["suite"], float(b["score"]), float(b["total"]), b.get("detail", ""))
    except (TypeError, ValueError):
        return {"ok": False, "error": "score and total must be numbers"}
    return {"ok": True, "run": run}


@router.post("/api/quality/snapshot")
def api_quality_snapshot():
    return {"ok": True, "run": Q.health_snapshot()}
