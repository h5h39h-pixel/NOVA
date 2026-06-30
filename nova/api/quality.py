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
    b = await req.json()
    if "suite" not in b or "score" not in b or "total" not in b:
        return {"ok": False, "error": "need suite, score, total"}
    return {"ok": True, "run": Q.record(b["suite"], b["score"], b["total"], b.get("detail", ""))}


@router.post("/api/quality/snapshot")
def api_quality_snapshot():
    return {"ok": True, "run": Q.health_snapshot()}
