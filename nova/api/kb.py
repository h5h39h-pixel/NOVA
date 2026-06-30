# -*- coding: utf-8 -*-
"""Knowledge-base routes — status, list/delete documents, semantic search. Backed by
nova.services.kb. The multipart upload+ingest route stays in server.py (shares UPLOAD_DIR)."""
import asyncio
from fastapi import APIRouter, Request
from nova.core.db import db
from nova.services.kb import kb_status, kb_search, kb_ingest_folder
from nova.services.settings import exec_allowed
from nova.services.audit import audit

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

@router.post("/api/kb/ingest-folder")
async def api_kb_ingest_folder(req: Request):
    """IDEA-5: index a local folder into the KB. exec_allowed-gated (reads arbitrary local paths)
    + audited. Runs synchronously in FastAPI's threadpool (fine for the single-user local case)."""
    if not exec_allowed():
        return {"ok": False, "error": "folder ingest is disabled while exposed on the LAN (enable allow_remote_exec)"}
    b = await req.json()
    folder = (b.get("folder") or "").strip()
    if not folder:
        return {"ok": False, "error": "no folder given"}
    res = await asyncio.to_thread(kb_ingest_folder, folder, bool(b.get("recursive", True)),
                                  int(b.get("max_files", 200)))
    audit("user", "kb_ingest_folder", f"{folder} -> {res.get('indexed', 0)} files")
    return res
