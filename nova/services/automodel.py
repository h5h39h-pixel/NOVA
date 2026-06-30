# -*- coding: utf-8 -*-
"""Auto model selection — pick the best locally-installed model for a task. Used when the user chooses
"✨ Auto" instead of a specific model. Heuristic + capability-tag aware (coding / vision / reasoning /
chat), DeepThink-aware (prefers a reasoning or larger model), and falls back to the configured default.

Intentionally simple + explainable: returns (model_name, reason) so the UI can show *why*."""
import re
from nova.core.db import get_settings

_CODE = re.compile(r"\b(code|function|bug|debug|python|javascript|typescript|sql|regex|api|script|class|stack ?trace|compile|refactor)\b", re.I)
_REASON = re.compile(r"\b(prove|reason|step.by.step|analyz|explain in detail|why|derive|plan|strategy|trade.?off|architect)\b", re.I)


def _models():
    try:
        from nova.services.ollama import ollama_models
        return ollama_models() or []
    except Exception:
        return []


def pick_model(prompt="", deepthink=False, vision=False, mode="chat"):
    """Return (model_name, reason). Never raises; falls back to the default setting."""
    models = _models()
    names = {m["name"]: m for m in models}
    default = get_settings().get("default_local_model", "qwen2.5:14b")

    def by_tag(tag):
        ms = [m for m in models if tag in (m.get("tags") or [])]
        # prefer a loaded one, then larger
        return sorted(ms, key=lambda m: (m.get("loaded", False), m.get("size_gb", 0)), reverse=True)

    p = prompt or ""
    if vision:
        v = by_tag("vision")
        if v: return v[0]["name"], "vision: image/screen understanding"
    if _CODE.search(p):
        c = by_tag("coding")
        if c: return c[0]["name"], "coding task → code-specialized model"
    if deepthink or _REASON.search(p):
        r = by_tag("reasoning")
        if r: return r[0]["name"], "deep reasoning → reasoning model"
        big = by_tag("chat")
        if big: return big[0]["name"], "deep reasoning → largest chat model"
    # agent mode benefits from a strong tool-using 'control'-tagged model
    if mode == "agent":
        ctl = by_tag("control")
        if ctl: return ctl[0]["name"], "agent → tool-capable model"
    if default in names:
        return default, "default model"
    chat = by_tag("chat")
    if chat: return chat[0]["name"], "general chat model"
    return (models[0]["name"] if models else default), "only available model" if models else "fallback default"


def resolve(model, prompt="", deepthink=False, mode="chat"):
    """If `model` is 'auto'/empty, pick one; else return it unchanged. Returns (name, reason|None)."""
    if model and model.lower() != "auto":
        return model, None
    return pick_model(prompt, deepthink=deepthink, mode=mode)
