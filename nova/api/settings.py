# -*- coding: utf-8 -*-
"""Settings & auth routes — read/save settings (secrets redacted) and the optional token
login (status / login / logout). Logic + the auth gate live in nova.services.settings."""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from nova.services.audit import audit
from nova.services.settings import settings_get, settings_save, token_ok, verify_login

router = APIRouter()

# ---- settings
@router.get("/api/settings")
def api_settings(): return settings_get()

@router.post("/api/settings")
async def api_settings_save(req: Request):
    patch = await req.json()
    return settings_save(patch)

# ---- auth (optional token login) ----
@router.get("/api/auth/status")
def api_auth_status(request: Request):
    from nova.core.db import get_settings
    return {"required": bool(get_settings().get("auth_enabled")), "authed": token_ok(request)}

@router.post("/api/auth/login")
async def api_auth_login(req: Request):
    b = await req.json()
    if verify_login(b.get("token", "")):
        r = JSONResponse({"ok": True})
        r.set_cookie("cc_token", str(b.get("token", "")), httponly=True, samesite="lax", max_age=60*60*24*30)
        audit("auth", "login", "successful sign-in")
        return r
    audit("auth", "login", "wrong token", "fail")
    return JSONResponse({"ok": False, "error": "invalid token"}, status_code=401)

@router.post("/api/auth/logout")
def api_auth_logout():
    r = JSONResponse({"ok": True}); r.delete_cookie("cc_token"); return r
