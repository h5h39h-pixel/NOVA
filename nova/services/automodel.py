# -*- coding: utf-8 -*-
"""Auto model selection — pick the best locally-installed model for a task. Used when the user chooses
"✨ Auto" instead of a specific model. Heuristic + capability-tag aware (coding / vision / reasoning /
chat), DeepThink-aware (prefers a reasoning or larger model), and falls back to the configured default.

Intentionally simple + explainable: returns (model_name, reason) so the UI can show *why*."""
import re
from nova.core.db import get_settings

_CODE = re.compile(r"\b(code|coding|function|bug|debug|python|javascript|typescript|java|rust|go|c\+\+|sql|regex|api|endpoint|script|class|stack ?trace|compile|refactor|unit test|exception|traceback)\b", re.I)
_REASON = re.compile(r"\b(prove|reason|step.by.step|analyz|explain in detail|why\b|derive|plan|strategy|trade.?off|architect|optimi[sz]e|complex|think hard|deep)\b", re.I)
_VISION = re.compile(r"\b(screen|screenshot|image|picture|photo|diagram|look at|see this|what'?s on|describe (the|this) (image|screen|picture)|ocr|read the screen)\b", re.I)
_MATH = re.compile(r"\b(calculate|compute|solve|equation|integral|derivative|matrix|probability|\d+\s*[\+\-\*/x]\s*\d+)\b", re.I)
_ARABIC = re.compile(r"[؀-ۿ]")


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
    # 1) vision (explicit flag or visual keywords) → a VLM
    if vision or _VISION.search(p):
        v = by_tag("vision")
        if v: return v[0]["name"], "vision — image/screen understanding"
    # 2) coding → a code-specialized model
    if _CODE.search(p):
        c = by_tag("coding")
        if c: return c[0]["name"], "coding task → code‑specialized model"
    # 3) deep reasoning / math / explicit DeepThink → reasoning model, else the largest chat model
    if deepthink or _REASON.search(p) or _MATH.search(p):
        r = by_tag("reasoning")
        if r: return r[0]["name"], "deep reasoning → reasoning model"
        big = by_tag("chat")
        if big: return big[0]["name"], "deep reasoning → largest chat model"
    # 4) very long prompt → prefer a larger chat model for context headroom
    if len(p) > 1600:
        big = by_tag("chat")
        if big: return big[0]["name"], "long input → larger‑context model"
    # 5) agent mode → a tool-capable ('control') model
    if mode == "agent":
        ctl = by_tag("control")
        if ctl: return ctl[0]["name"], "agent → tool‑capable model"
    # 6) Arabic / general → the configured default (qwen is multilingual), else any chat model
    why_lang = " (Arabic‑capable)" if _ARABIC.search(p) else ""
    if default in names:
        return default, "default model" + why_lang
    chat = by_tag("chat")
    if chat: return chat[0]["name"], "general chat model" + why_lang
    return (models[0]["name"] if models else default), ("only available model" if models else "fallback default")


def resolve(model, prompt="", deepthink=False, mode="chat"):
    """If `model` is 'auto'/empty, pick one; else return it unchanged. Returns (name, reason|None)."""
    if model and model.lower() != "auto":
        return model, None
    return pick_model(prompt, deepthink=deepthink, mode=mode)
