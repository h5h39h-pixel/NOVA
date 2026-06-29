# -*- coding: utf-8 -*-
"""Notification-center routes — list (filter by category/search), mark seen, clear.
Creation lives in nova.services.notifications; these are the read/state endpoints."""
from fastapi import APIRouter
from nova.core.db import db

router = APIRouter()

@router.get("/api/notifications")
def api_notifications(limit: int = 80, category: str = "", q: str = ""):
    sql = "SELECT * FROM notifications"; where = []; args = []
    if category: where.append("category=?"); args.append(category)
    if q: where.append("(title LIKE ? OR body LIKE ?)"); args += [f"%{q}%", f"%{q}%"]
    if where: sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC LIMIT ?"; args.append(int(limit))
    c = db()
    items = [dict(r) for r in c.execute(sql, args).fetchall()]
    unread = c.execute("SELECT COUNT(*) FROM notifications WHERE seen=0").fetchone()[0]
    cats = {r[0] or "system": r[1] for r in c.execute("SELECT category, COUNT(*) FROM notifications GROUP BY category").fetchall()}
    c.close()
    return {"items": items, "unread": unread, "categories": cats}

@router.post("/api/notifications/seen")
def api_notifications_seen():
    c = db(); c.execute("UPDATE notifications SET seen=1"); c.commit(); c.close(); return {"ok": True}

@router.post("/api/notifications/{nid}/seen")
def api_notification_seen_one(nid: int):
    c = db(); c.execute("UPDATE notifications SET seen=1 WHERE id=?", (nid,)); c.commit(); c.close(); return {"ok": True}

@router.delete("/api/notifications")
def api_notifications_clear():
    c = db(); c.execute("DELETE FROM notifications"); c.commit(); c.close(); return {"ok": True}
