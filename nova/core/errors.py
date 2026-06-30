# -*- coding: utf-8 -*-
"""In-memory error aggregation — dedupes exceptions by signature with counts, first/last
seen, and a short traceback sample. Bounded so it can't grow without limit. Surfaced via
/api/errors and the Diagnostics page. Stdlib-only; no DB writes on the hot path."""
import time
import json
import traceback

_errors = {}      # signature -> {count, first, last, where, sample}
_MAX = 200

# HON-4: persist the aggregated errors to disk so /api/errors + Diagnostics survive a restart.
try:
    from config import LOG_DIR as _LOG_DIR
    _FILE = _LOG_DIR / "errors.json"
except Exception:
    _FILE = None


def _save():
    if not _FILE:
        return
    try:
        _FILE.parent.mkdir(parents=True, exist_ok=True)
        _FILE.write_text(json.dumps(_errors), encoding="utf-8")
    except Exception:
        pass


def _load():
    global _errors
    if not _FILE or not _FILE.exists():
        return
    try:
        data = json.loads(_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            _errors = data
    except Exception:
        pass


_load()   # restore on import


def record(where, exc):
    """Record one exception occurrence (keyed by type + message)."""
    try:
        sig = f"{type(exc).__name__}: {str(exc)[:140]}"
        now = time.time()
        e = _errors.get(sig)
        if e:
            e["count"] += 1; e["last"] = now; e["where"] = where
        else:
            if len(_errors) >= _MAX:                       # drop least-recent to stay bounded
                oldest = min(_errors, key=lambda k: _errors[k]["last"])
                _errors.pop(oldest, None)
            _errors[sig] = {"count": 1, "first": now, "last": now, "where": where,
                            "sample": traceback.format_exc()[-700:]}
        _save()   # HON-4: persist so it survives restart
    except Exception:
        pass


def snapshot(limit=50):
    items = sorted(_errors.items(), key=lambda kv: kv[1]["last"], reverse=True)[:limit]
    return [{"signature": s, "count": d["count"], "first": d["first"], "last": d["last"],
             "where": d["where"], "sample": d["sample"]} for s, d in items]


def clear():
    _errors.clear()
    _save()


def total():
    return sum(d["count"] for d in _errors.values())
