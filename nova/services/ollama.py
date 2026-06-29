# -*- coding: utf-8 -*-
"""Ollama client — the single place that talks to the local Ollama daemon.

Lists installed models with capability tags (vision/coding/control/…), caches
per-model /api/show capabilities, and runs one-shot chat completions. Depends only
on nova.core.http + config (the OLLAMA endpoint)."""
import json
import urllib.request
from config import OLLAMA
from nova.core.http import http_json

_caps_cache = {}


def model_caps(name):
    """Cache Ollama /api/show capabilities + family for a model (slow first call)."""
    if name in _caps_cache: return _caps_cache[name]
    caps, fam = [], ""
    try:
        info = http_json(f"{OLLAMA}/api/show", body={"name": name}, timeout=8)
        caps = [c.lower() for c in (info.get("capabilities") or [])]
        det = info.get("details") or {}
        fam = ((det.get("family") or "") + " " + " ".join(det.get("families") or [])).lower()
    except Exception: pass
    _caps_cache[name] = (caps, fam)
    return _caps_cache[name]


def model_tags(name):
    """Display-only capability tags. Never renames; auto-applies to any new model."""
    n = name.lower(); caps, fam = model_caps(name); tags = []
    if "embedding" in caps or "embed" in n: return ["embedding"]
    if "vision" in caps or any(k in n for k in ("vl", "vision", "llava", "moondream")): tags.append("vision")
    if any(k in n for k in ("coder", "code", "starcoder", "deepseek-coder")): tags.append("coding")
    if "tools" in caps or any(k in n for k in ("llama3.1", "llama3.2", "qwen2.5:", "qwen2.5-7", "mistral", "command-r", "firefunction", "hermes")):
        tags.append("control")
    if "chat" not in tags and ("completion" in caps or not caps): tags.append("chat")
    if any(k in n for k in ("qwen", "gemma", "aya", "command-r", "llama3", "mistral", "jais")): tags.append("multilingual")
    if any(k in n for k in ("qwen", "aya", "jais", "command-r", "arabic")): tags.append("arabic")
    seen = set(); return [x for x in (["chat"] + tags if not tags else tags) if not (x in seen or seen.add(x))]


def ollama_models():
    try: tags = http_json(f"{OLLAMA}/api/tags").get("models", [])
    except Exception: tags = []
    try: running = {m["name"]: m for m in http_json(f"{OLLAMA}/api/ps").get("models", [])}
    except Exception: running = {}
    out = []
    for m in tags:
        nm = m["name"]; r = running.get(nm)
        out.append({"name": nm, "size_gb": round(m.get("size", 0) / 1e9, 1),
                    "loaded": bool(r), "vram_gb": round(r["size_vram"] / 1e9, 1) if r else 0,
                    "expires": r.get("expires_at") if r else None, "tags": model_tags(nm)})
    out.sort(key=lambda x: (not x["loaded"], x["name"]))
    return out


def ollama_chat_once(model, msgs, temp=0.2):
    data = json.dumps({"model": model, "messages": msgs, "stream": False,
                       "options": {"temperature": temp, "num_predict": 500}}).encode()
    rq = urllib.request.Request(f"{OLLAMA}/api/chat", data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(rq, timeout=180) as r:
        return (json.loads(r.read().decode()).get("message") or {}).get("content", "")
