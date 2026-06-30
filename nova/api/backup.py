# -*- coding: utf-8 -*-
"""Backup & restore routes — download a full-state JSON bundle and merge one back in.
Logic lives in nova.services.backup."""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from nova.services.backup import make_backup, restore_backup, snapshot_db, list_snapshots, backup_media

router = APIRouter()

@router.get("/api/backup/snapshots")
def api_snapshots():
    return {"items": list_snapshots()}

@router.post("/api/backup/snapshot")
def api_snapshot_now():
    return {"ok": True, "file": snapshot_db(), "media": backup_media()}

@router.get("/api/backup")
def api_backup():
    return JSONResponse(make_backup(), headers={"Content-Disposition": "attachment; filename=control-center-backup.json"})

@router.post("/api/restore")
async def api_restore(req: Request):
    b = await req.json()
    added = restore_backup(b)
    if added is None: return JSONResponse({"error": "unrecognized backup file"}, status_code=400)
    return {"ok": True, "added": added}
