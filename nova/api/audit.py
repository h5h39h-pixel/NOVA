# -*- coding: utf-8 -*-
"""Audit-trail routes — list (filter by actor/search) and clear. The audit() writer
lives in nova.services.audit; these expose the recorded events to the dashboard."""
from fastapi import APIRouter
from nova.core.db import db
from nova.services.audit import audit

router = APIRouter()

@router.get("/api/audit")
def api_audit(limit: int = 200, actor: str = "", q: str = ""):
    sql = "SELECT * FROM audit"; where = []; args = []
    if actor: where.append("actor=?"); args.append(actor)
    if q: where.append("(action LIKE ? OR detail LIKE ?)"); args += [f"%{q}%", f"%{q}%"]
    if where: sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC LIMIT ?"; args.append(int(limit))
    c = db(); rows = [dict(r) for r in c.execute(sql, args).fetchall()]
    actors = [r[0] for r in c.execute("SELECT DISTINCT actor FROM audit").fetchall()]
    total = c.execute("SELECT COUNT(*) FROM audit").fetchone()[0]; c.close()
    return {"events": rows, "actors": sorted(actors), "total": total}

@router.delete("/api/audit")
def api_audit_clear():
    c = db(); c.execute("DELETE FROM audit"); c.commit(); c.close()
    audit("settings", "audit_cleared", "audit log cleared")
    return {"ok": True}
