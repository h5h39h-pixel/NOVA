# -*- coding: utf-8 -*-
"""Bug-report routes — report issues, list, resolve/reopen, delete. Recent logs auto-attached."""
import time
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from config import LOG_DIR
from nova.core.db import db
from nova.services.audit import audit
from nova.services.notifications import add_notification

router = APIRouter()

@router.get("/api/bugs")
def api_bugs():
    c = db(); rows = [dict(r) for r in c.execute("SELECT * FROM bug_reports ORDER BY id DESC LIMIT 100").fetchall()]; c.close()
    return {"items": rows, "open": sum(1 for r in rows if r.get("status") == "open")}

@router.post("/api/bugs")
async def api_bug_create(req: Request):
    b = await req.json(); title = (b.get("title") or "").strip()
    if not title: return JSONResponse({"error": "title required"}, status_code=400)
    logs = ""
    try:
        p = LOG_DIR / "server.log"
        if p.exists(): logs = "\n".join(p.read_text(encoding="utf-8", errors="replace").splitlines()[-40:])
    except Exception: pass
    c = db(); c.execute("INSERT INTO bug_reports(ts,title,detail,severity,status,page,logs) VALUES(?,?,?,?,?,?,?)",
                        (time.time(), title[:200], (b.get("detail") or "")[:4000], b.get("severity", "normal"),
                         "open", b.get("page", ""), logs)); c.commit(); c.close()
    audit("bug", "report", title[:80]); add_notification("info", "Bug reported", title[:60])
    return {"ok": True}

@router.post("/api/bugs/{bid}/status")
async def api_bug_status(bid: int, req: Request):
    b = await req.json()
    c = db(); c.execute("UPDATE bug_reports SET status=? WHERE id=?", (b.get("status", "open"), bid)); c.commit(); c.close()
    return {"ok": True}

@router.delete("/api/bugs/{bid}")
def api_bug_del(bid: int):
    c = db(); c.execute("DELETE FROM bug_reports WHERE id=?", (bid,)); c.commit(); c.close()
    return {"ok": True}
