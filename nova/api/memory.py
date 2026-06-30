# -*- coding: utf-8 -*-
"""IDEA-8 — local persistent memory routes: list / add / recall / forget durable user facts.
Local-only; no external surface. Logic lives in nova.services.memory."""
from fastapi import APIRouter
from pydantic import BaseModel
from nova.services import memory as M

router = APIRouter()


class MemIn(BaseModel):
    text: str
    kind: str = "fact"
    tags: str = ""
    pinned: bool = False


@router.get("/api/memory")
def api_memory_list(q: str = "", limit: int = 200):
    return {"items": M.recall(q) if q else M.all_facts(limit), "count": len(M.all_facts())}


@router.post("/api/memory")
def api_memory_add(m: MemIn):
    try:
        return {"ok": True, "item": M.remember(m.text, kind=m.kind, tags=m.tags, pinned=m.pinned)}
    except ValueError as e:
        return {"ok": False, "error": str(e)}


@router.delete("/api/memory/{mid}")
def api_memory_forget(mid: int):
    return {"ok": M.forget(mid)}
