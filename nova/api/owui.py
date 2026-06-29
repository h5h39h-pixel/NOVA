# -*- coding: utf-8 -*-
"""Open WebUI routes — read its tool/model config and toggle tools / apply the
recommended setup. Backed by nova.services.owui (talks to the OWUI container)."""
import json
from fastapi import APIRouter, Request
from nova.services.audit import audit
from nova.services.notifications import add_notification
from nova.services.owui import owui_py, OWUI_LIST, owui_toggle_code, OWUI_APPLY

router = APIRouter()

@router.get("/api/owui")
def api_owui():
    raw = owui_py(OWUI_LIST)
    try: return json.loads(raw.strip().splitlines()[-1])
    except Exception: return {"error": raw}

@router.post("/api/tools/toggle")
async def api_tools_toggle(req: Request):
    b = await req.json()
    raw = owui_py(owui_toggle_code(b["tool_id"], bool(b["on"])))
    audit("tools", "enable" if b["on"] else "disable", b["tool_id"])
    add_notification("info", f"Tool {'enabled' if b['on'] else 'disabled'}", b["tool_id"])
    return {"ok": "ok" in raw, "raw": raw}

@router.post("/api/owui/apply-recommended")
def api_owui_apply():
    raw = owui_py(OWUI_APPLY)
    try: res = json.loads(raw.strip().splitlines()[-1])
    except Exception: res = {"raw": raw}
    add_notification("success", "Applied recommended OWUI config",
                     "native function calling, temp 0, forced tool prompt, code interpreter off")
    return res
