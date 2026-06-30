# -*- coding: utf-8 -*-
"""Agent + browser routes — start/stop the autonomous agent, and the browser endpoints
(headless fetch, visible browser, open-in-default-browser). Backed by nova.services.agent
and nova.services.browser."""
import asyncio
import threading
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from nova.core.db import get_settings
from nova.services.audit import audit
from nova.services.agent import agent_run, AGENT_STOP
from nova.services.browser import browse, visible_browse, open_url_default

router = APIRouter()

@router.post("/api/agent")
async def api_agent(req: Request):
    b = await req.json(); goal = (b.get("goal") or "").strip()
    if not goal: return JSONResponse({"error": "empty goal"}, status_code=400)
    model = b.get("model") or get_settings().get("default_local_model", "llama3.1:8b")
    if str(model).lower() == "auto":          # ✨ Auto: pick the best tool-capable model
        from nova.services.automodel import resolve
        model, _ = resolve("auto", goal, deepthink=bool(b.get("deepthink")), mode="agent")
    tools = b.get("tools") if isinstance(b.get("tools"), list) else None
    threading.Thread(target=agent_run, args=(goal, model, bool(b.get("dry_run")), bool(b.get("unrestricted")),
                     b.get("temperature", 0.2), b.get("max_steps", 8), tools),
                     kwargs={"deepthink": bool(b.get("deepthink"))}, daemon=True).start()
    return {"ok": True, "model": model}

@router.post("/api/agent/stop")
def api_agent_stop():
    AGENT_STOP.set()
    audit("agent", "stop", "user requested stop")
    return {"ok": True}

@router.post("/api/browse")
async def api_browse(req: Request):
    b = await req.json(); url = (b.get("url") or "").strip()
    search = b.get("search")
    if not url and not search: return JSONResponse({"error": "empty url"}, status_code=400)
    try:
        if b.get("visible") or search:
            r = await asyncio.to_thread(visible_browse, url or None, search,
                                        bool(b.get("click_first")), b.get("fill"), b.get("click"))
        else:
            r = await asyncio.to_thread(browse, url, b.get("fill"), b.get("click"), b.get("wait"))
        audit("browser", "browse", search or url)
        return r
    except Exception as e:
        audit("browser", "browse", f"{search or url}: {e}", "fail")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/api/open-url")
async def api_open_url(req: Request):
    b = await req.json(); url = (b.get("url") or "").strip()
    if not url: return JSONResponse({"error": "empty url"}, status_code=400)
    try:
        u = await asyncio.to_thread(open_url_default, url)
        audit("browser", "open_url", u)
        return {"ok": True, "url": u}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
