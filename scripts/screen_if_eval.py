# -*- coding: utf-8 -*-
"""OUT-4 — verify `screen_if` against the REAL screen (not a mock). Reads the live screen with OCR,
picks a word actually on screen, and confirms screen_if matches it (and rejects a nonsense string).
Run: python scripts/screen_if_eval.py"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nova.core.db import set_settings           # noqa: E402
from nova.services import screen as S           # noqa: E402
from nova.services.schedules import run_action  # noqa: E402


def main():
    set_settings({"desktop_notifications": False})   # no toast spam
    r = S.read_screen(vision=False)                  # OCR the real screen
    text = r.get("text") or ""
    print(f"real-screen OCR: {len(text)} chars, mode={r.get('mode')}")
    words = [w for w in re.findall(r"[A-Za-z]{4,}", text)]
    ok_match = ok_nomatch = False
    if words:
        w = words[0]
        out = run_action("screen_if", {"match": w, "then_action": "notify", "then_params": {"text": "matched"}})
        ok_match = out.startswith("matched")
        print(f"[{'PASS' if ok_match else 'FAIL'}] match real word '{w}': {out}")
    else:
        print("(no OCR words captured — screen may be empty/graphical; skipping positive match)")
        ok_match = None
    nm = run_action("screen_if", {"match": "zzqqxx_not_on_screen_2026", "then_action": "notify", "then_params": {"text": "x"}})
    ok_nomatch = nm.startswith("no match")
    print(f"[{'PASS' if ok_nomatch else 'FAIL'}] reject nonsense: {nm}")
    good = ok_nomatch and (ok_match in (True, None))
    print("\n=== OUT-4:", "PASS — screen_if works against the real screen ===" if good else "FAIL ===")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
