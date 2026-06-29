# -*- coding: utf-8 -*-
"""Tiny HTTP helpers for talking to local services (Ollama, ComfyUI, Open WebUI). Stdlib only."""
import json, urllib.request

def http_json(url, method=None, body=None, timeout=8):
    data = json.dumps(body).encode() if body is not None else None
    method = method or ("POST" if data is not None else "GET")
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode() or "{}")

def http_ok(url, timeout=3):
    try:
        urllib.request.urlopen(url, timeout=timeout); return True
    except Exception:
        return False
