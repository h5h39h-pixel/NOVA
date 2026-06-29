# -*- coding: utf-8 -*-
"""
Event bus — the one-way channel from the backend to every connected dashboard.

`push(msg)` is thread-safe and can be called from any worker thread (agents,
ProcMgr, schedulers); it marshals the broadcast onto the main asyncio loop.
WebSocket handlers register/unregister via the shared `clients` set.
Depends on nothing but the stdlib, so it sits at the bottom with `db`.
"""
import json, asyncio

clients = set()
_main_loop = None

def set_main_loop(loop):
    """Called once at startup (lifespan) so push() can schedule broadcasts."""
    global _main_loop
    _main_loop = loop

def get_loop():
    return _main_loop

async def _send_all(msg):
    dead = []
    for ws in list(clients):
        try: await ws.send_text(json.dumps(msg, default=str))
        except Exception: dead.append(ws)
    for d in dead: clients.discard(d)

def push(msg):
    """Thread-safe broadcast to all connected dashboards."""
    if _main_loop:
        try: asyncio.run_coroutine_threadsafe(_send_all(msg), _main_loop)
        except Exception: pass
