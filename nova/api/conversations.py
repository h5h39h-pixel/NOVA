# -*- coding: utf-8 -*-
"""Conversation routes — list/create/rename/move/archive/delete chats, read messages,
and the legacy single-history + per-conversation clear. Backed by nova.services.chat."""
from fastapi import APIRouter, Request
from nova.core.db import db
from nova.services.chat import conv_ensure, conv_messages, conv_clear

router = APIRouter()

@router.get("/api/conversations")
def api_conversations(include_archived: int = 0):
    c = db()
    q = "SELECT cv.*, (SELECT COUNT(*) FROM chat WHERE chat.cid=cv.cid) AS msgs FROM conversations cv"
    if not include_archived: q += " WHERE cv.archived=0"
    q += " ORDER BY cv.updated DESC"
    rows = [dict(r) for r in c.execute(q).fetchall()]; c.close()
    return rows

@router.post("/api/conversations")
async def api_conv_create(req: Request):
    b = await req.json()
    cid = conv_ensure(project=b.get("project", "General"), title=b.get("title"))
    return {"ok": True, "cid": cid}

@router.get("/api/conversations/{cid}/messages")
def api_conv_messages(cid: str): return conv_messages(cid, 500)

@router.post("/api/conversations/{cid}/rename")
async def api_conv_rename(cid: str, req: Request):
    b = await req.json()
    c = db(); c.execute("UPDATE conversations SET title=? WHERE cid=?", (b.get("title", "")[:80], cid)); c.commit(); c.close()
    return {"ok": True}

@router.post("/api/conversations/{cid}/project")
async def api_conv_project(cid: str, req: Request):
    b = await req.json()
    c = db(); c.execute("UPDATE conversations SET project=? WHERE cid=?", (b.get("project", "General")[:60], cid)); c.commit(); c.close()
    return {"ok": True}

@router.post("/api/conversations/{cid}/archive")
async def api_conv_archive(cid: str, req: Request):
    b = await req.json()
    c = db(); c.execute("UPDATE conversations SET archived=? WHERE cid=?", (1 if b.get("archived") else 0, cid)); c.commit(); c.close()
    return {"ok": True}

@router.delete("/api/conversations/{cid}")
def api_conv_delete(cid: str):
    c = db(); c.execute("DELETE FROM chat WHERE cid=?", (cid,)); c.execute("DELETE FROM conversations WHERE cid=?", (cid,)); c.commit(); c.close()
    return {"ok": True}

# ---- legacy single-history (kept) + per-conversation clear
@router.get("/api/chat-history")
def api_chat_history(cid: str = ""):
    return conv_messages(cid, 500) if cid else []

@router.post("/api/chat-clear")
async def api_chat_clear(req: Request):
    try: b = await req.json()
    except Exception: b = {}
    if b.get("cid"): conv_clear(b["cid"])
    return {"ok": True}
