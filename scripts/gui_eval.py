# -*- coding: utf-8 -*-
"""HON-2 / HON-2b — real, SAFE GUI integration test for the Perception & Control stack.

Instead of driving a shared app like Notepad (multi-tab, session-restore, unsafe to close), this
launches an ISOLATED disposable Tkinter window in its own process, types into it via the control stack
(clipboard paste), and verifies the text actually landed by reading what the app received (the app
writes its input to a result file). Fully self-contained: own process (terminated by us, never
taskkill), temp files only, no user data touched.

On-demand only (needs a desktop session; briefly takes focus). Run:  python scripts/gui_eval.py
"""
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nova.services import control as C  # noqa: E402

MARKER = "nova-gui-7731"   # lowercase: avoids shift-key mangling if the keystroke path is used

TARGET_APP = '''
import tkinter as tk, sys, pathlib
out = pathlib.Path(sys.argv[1])
root = tk.Tk(); root.title("NOVA-GUI-TARGET")
root.geometry("460x150+240+240")
e = tk.Entry(root, width=44); e.pack(pady=40)
e.focus_force(); root.lift(); root.attributes("-topmost", True)
def _paste(ev=None):
    try: e.insert("insert", root.clipboard_get())
    except Exception: pass
    return "break"
e.bind("<Control-v>", _paste); e.bind("<Control-V>", _paste)   # accept synthetic Ctrl+V (atomic paste)
def poll():
    v = e.get()
    if v:
        try: out.write_text(v, encoding="utf-8")
        except Exception: pass
    root.after(250, poll)
poll()
root.after(12000, root.destroy)   # self-close after 12s no matter what
root.mainloop()
'''


def main():
    C.resume_control()
    tmp = Path(tempfile.mkdtemp(prefix="nova-gui-"))
    app_py = tmp / "target.py"; result = tmp / "result.txt"
    app_py.write_text(TARGET_APP, encoding="utf-8")
    print("Launching isolated Tkinter target app…")
    proc = subprocess.Popen([sys.executable, str(app_py), str(result)])
    ok = False
    detail = ""
    try:
        time.sleep(2.2)
        aw = C.active_window()
        print(f"active window: {aw.get('title')!r} ({aw.get('process')})")
        # The Entry has focus_force on launch; click directly on it (near top-center where it sits)
        # to satisfy Win11 focus rules WITHOUT defocusing onto the empty window body.
        r = aw.get("rect") or {}
        if r:
            C.click(r["x"] + r["w"] // 2, r["y"] + 55)   # the Entry row (pady=40)
            time.sleep(1.2)            # let focus SETTLE — early keystrokes are dropped otherwise
        C.type_text(MARKER)            # control stack: clipboard paste (atomic — the reliable path)
        for _ in range(20):
            time.sleep(0.3)
            if result.exists() and MARKER in result.read_text(encoding="utf-8", errors="replace"):
                ok = True; break
        detail = f"app received: {result.read_text(encoding='utf-8', errors='replace')[:60]!r}" if result.exists() else "app wrote nothing"
        print("input method: clipboard paste |", detail)
    finally:
        try: proc.terminate()          # terminate OUR app only (safe)
        except Exception: pass
        try: app_py.unlink(); result.unlink(missing_ok=True); tmp.rmdir()
        except Exception: pass
    print("\n=== HON-2:", "PASS — typed text landed in a live GUI app via the control stack ==="
          if ok else f"FAIL/FLAKY — {detail} ===")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
