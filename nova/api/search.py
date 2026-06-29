# -*- coding: utf-8 -*-
"""Unified search route — searches conversations, messages, command history, schedules,
KB documents, models, and (for longer queries) semantic KB. Backed by db + the ollama
and kb services. Powers the command palette's live results."""
from fastapi import APIRouter
from nova.core.db import db
from nova.services.ollama import ollama_models
from nova.services.kb import kb_search

router = APIRouter()

@router.get("/api/search")
def api_search(q: str = ""):
    q = (q or "").strip()
    if len(q) < 2: return {"results": []}
    like = f"%{q}%"; ql = q.lower(); out = []
    c = db()
    try:
        for r in c.execute("SELECT cid,title FROM conversations WHERE title LIKE ? ORDER BY updated DESC LIMIT 6", (like,)):
            out.append({"type": "chat", "icon": "💬", "label": r["title"] or "Chat", "sub": "conversation", "go": "#/chat", "cid": r["cid"]})
        for r in c.execute("SELECT cid,content FROM chat WHERE content LIKE ? ORDER BY id DESC LIMIT 6", (like,)):
            out.append({"type": "message", "icon": "💬", "label": (r["content"] or "")[:90], "sub": "message", "go": "#/chat", "cid": r["cid"]})
        for r in c.execute("SELECT command FROM history WHERE command LIKE ? ORDER BY id DESC LIMIT 5", (like,)):
            out.append({"type": "command", "icon": "⌨️", "label": (r["command"] or "")[:90], "sub": "command history", "go": "#/terminal"})
        for r in c.execute("SELECT name,action FROM schedules WHERE name LIKE ? LIMIT 5", (like,)):
            out.append({"type": "automation", "icon": "⏰", "label": r["name"], "sub": "automation · " + r["action"], "go": "#/automation"})
        for r in c.execute("SELECT id,name FROM kb_docs WHERE name LIKE ? LIMIT 5", (like,)):
            out.append({"type": "doc", "icon": "📄", "label": r["name"], "sub": "knowledge document", "go": "#/knowledge"})
    except Exception: pass
    c.close()
    try:
        for m in ollama_models():
            if ql in m["name"].lower():
                out.append({"type": "model", "icon": "🧩", "label": m["name"], "sub": "model · " + ", ".join(m.get("tags", [])), "go": "#/models"})
    except Exception: pass
    if len(q) >= 4:                         # semantic KB search (embeds the query)
        try:
            for h in kb_search(q, 3):
                out.append({"type": "kb", "icon": "📚", "label": h["text"][:90],
                            "sub": f"knowledge · {h['doc']} ({h['score']})", "go": "#/knowledge"})
        except Exception: pass
    return {"results": out[:30]}
