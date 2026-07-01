# -*- coding: utf-8 -*-
"""Dry-run diff — show what a dangerous action WOULD change before it executes. Surfaced in the
confirmation popup (Confirm mode) and via /api/agent/preview, so Full-Access isn't a black box.

- write_file  → a unified diff (existing file) or "would CREATE (N bytes)"
- run_command → the command + whether it matches a destructive pattern
- delete_file → what would be removed
Read-only; never touches disk. Depends only on stdlib + nova.core.safety."""
import difflib
from pathlib import Path


def preview_action(name, args):
    a = args or {}
    if name == "write_file":
        return _preview_write(a.get("path", ""), a.get("content", ""))
    if name == "run_command":
        return _preview_command(a.get("command", ""))
    if name == "delete_file":
        p = a.get("path", "")
        exists = False
        try: exists = Path(p).exists()
        except Exception: pass
        return {"kind": "delete", "path": p, "will": ("DELETE existing file" if exists else "nothing (not found)")}
    if name == "control":
        return {"kind": "control", "will": f"{a.get('action','')} {a.get('x','')},{a.get('y','')} "
                                            f"{str(a.get('text',''))[:60]}".strip()}
    return {"kind": name, "will": str(a)[:200]}


def _preview_write(path, content):
    content = content or ""
    p = None
    try: p = Path(path)
    except Exception: pass
    if p and p.exists() and p.is_file():
        try:
            old = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            old = ""
        diff = list(difflib.unified_diff(
            old.splitlines(), content.splitlines(),
            fromfile=f"{path} (current)", tofile=f"{path} (new)", lineterm="", n=2))
        added = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
        removed = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))
        return {"kind": "overwrite", "path": path, "diff": "\n".join(diff[:400]),
                "added": added, "removed": removed,
                "will": f"OVERWRITE {path}  (+{added}/-{removed} lines)"}
    return {"kind": "create", "path": path, "diff": "",
            "will": f"CREATE {path}  ({len(content)} bytes, {content.count(chr(10)) + 1} lines)"}


def _preview_command(cmd):
    from nova.core.safety import danger_reason
    reason = danger_reason(cmd)
    return {"kind": "command", "command": cmd[:400], "destructive": bool(reason),
            "will": (f"⚠ DESTRUCTIVE ({reason}): " if reason else "run: ") + cmd[:200]}
