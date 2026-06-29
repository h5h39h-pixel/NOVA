# -*- coding: utf-8 -*-
"""Knowledge-base routes — status, list/delete documents, semantic search. Backed by
nova.services.kb. The multipart upload+ingest route stays in server.py (shares UPLOAD_DIR)."""
from fastapi import APIRouter, Request
from nova.core.db import db
from nova.services.kb import kb_status, kb_search

router = APIRouter()

@router.get("/api/kb/status")
def api_kb_status(): return kb_status()

@router.get("/api/kb/docs")
def api_kb_docs():
    c = db(); rows = [dict(r) for r in c.execute("SELECT * FROM kb_docs ORDER BY id DESC").fetchall()]; c.close()
    return rows

@router.delete("/api/kb/docs/{doc_id}")
def api_kb_del(doc_id: int):
    c = db(); c.execute("DELETE FROM kb_chunks WHERE doc_id=?", (doc_id,)); c.execute("DELETE FROM kb_docs WHERE id=?", (doc_id,)); c.commit(); c.close()
    return {"ok": True}

@router.post("/api/kb/search")
async def api_kb_search(req: Request):
    b = await req.json(); return {"results": kb_search(b.get("query", ""), int(b.get("k", 4)))}
