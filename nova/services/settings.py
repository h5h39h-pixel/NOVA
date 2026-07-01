# -*- coding: utf-8 -*-
"""Settings & auth — secret redaction, token hashing, the auth gate (`token_ok`, used by
the server's security middleware), and the settings-save / login flows. Tokens are stored
only as SHA-256 hashes; the raw token is shown to the user exactly once on enable. Depends
on nova.core (db/events) + nova.services.audit."""
import hashlib
import secrets
from nova.core.db import get_settings, set_settings
from nova.core.events import push
from nova.core.secretbox import encrypt_secret, decrypt_secret
from nova.services.audit import audit

SECRET_KEYS = ("auth_token", "auth_token_hash", "cloud_api_key")
AUTH_EXEMPT = {"/api/auth/login", "/api/auth/status", "/api/auth/logout"}


def _hash(t):
    return hashlib.sha256(str(t).encode("utf-8")).hexdigest()


def _redact(s):
    return {k: ("***" if k == "cloud_api_key" and v else v) for k, v in s.items() if k not in ("auth_token", "auth_token_hash")}


def token_ok(request):
    """True if the request is authorized (auth disabled, or a valid token cookie/header)."""
    s = get_settings()
    if not s.get("auth_enabled"): return True
    tok = request.cookies.get("cc_token") or request.headers.get("x-auth-token", "")
    h = s.get("auth_token_hash") or ""
    if h:
        return bool(tok) and secrets.compare_digest(_hash(tok), h)
    real = s.get("auth_token", "")  # legacy plaintext fallback
    return bool(real) and secrets.compare_digest(str(tok), str(real))


def settings_get():
    return _redact(get_settings())


def get_cloud_api_key():
    """Decrypted cloud API key for use by callers (empty string if unset)."""
    return decrypt_secret(get_settings().get("cloud_api_key", "")) or ""


def settings_save(patch):
    """Apply a settings patch; on first auth-enable, mint a one-time token (returned once)."""
    cur = get_settings(); new_token = None
    if patch.get("auth_enabled") and not cur.get("auth_token_hash"):
        new_token = secrets.token_hex(16)                 # shown to the user exactly once
        patch["auth_token_hash"] = _hash(new_token)
        patch["auth_token"] = ""                            # never store the raw token (supersede legacy)
    if patch.get("cloud_api_key"):                         # SEC-4: encrypt the cloud key at rest
        patch["cloud_api_key"] = encrypt_secret(patch["cloud_api_key"])
    s = set_settings(patch)
    sec = [k for k in patch if k in ("auth_enabled", "lan_access", "webhook_enabled", "webhook_url", "cloud_api_key")]
    changed = ", ".join(k + "=" + str(patch[k] if k not in SECRET_KEYS else "***") for k in patch)
    audit("settings", "update", changed if not sec else "security: " + ", ".join(sec))
    try:                                          # explicit config-change event with the changed keys
        from nova.core import eventlog
        eventlog.log("system", "config changed", level="warn" if sec else "info",
                     source="settings.save", actor="user", detail=changed,
                     context={"keys": list(patch.keys())})
    except Exception:
        pass
    push({"type": "settings", "settings": {k: v for k, v in _redact(s).items() if k in patch}})
    out = _redact(s)
    if new_token: out["new_token"] = new_token             # one-time reveal for the user to save
    return out


def exec_allowed():
    """Whether arbitrary command execution (/api/exec, agent run_command) is permitted.
    Always allowed on localhost (that is the product's purpose). When the server is exposed
    on the LAN (auth + lan_access), it requires the explicit `allow_remote_exec` opt-in."""
    s = get_settings()
    if s.get("auth_enabled") and s.get("lan_access"):   # reachable beyond this machine
        return bool(s.get("allow_remote_exec"))
    return True


def verify_login(tok):
    """True if the token is valid for sign-in (hash or legacy plaintext)."""
    s = get_settings(); tok = str(tok or "")
    h = s.get("auth_token_hash") or ""
    return bool(s.get("auth_enabled") and tok and (
        (h and secrets.compare_digest(_hash(tok), h)) or
        (not h and s.get("auth_token") and secrets.compare_digest(tok, str(s["auth_token"])))))
