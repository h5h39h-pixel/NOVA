# -*- coding: utf-8 -*-
"""History & log routes — recent action history (list/clear) and the server log tail.
Read-only observability surfaces backed by the DB and the rotating log file."""
from fastapi import APIRouter
from config import LOG_DIR
from nova.core.db import db

router = APIRouter()

@router.get("/api/history")
def api_history(limit: int = 60):
    c = db(); rows = c.execute("SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)).fetchall(); c.close()
    return [dict(r) for r in rows]

@router.delete("/api/history")
def api_history_clear():
    c = db(); c.execute("DELETE FROM history"); c.commit(); c.close(); return {"ok": True}

@router.get("/api/logs")
def api_logs(lines: int = 200):
    p = LOG_DIR / "server.log"
    if not p.exists(): return {"log": ""}
    tail = p.read_text(encoding="utf-8", errors="replace").splitlines()[-min(max(lines, 1), 1000):]
    return {"log": "\n".join(tail)}
