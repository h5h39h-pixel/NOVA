# -*- coding: utf-8 -*-
"""Preflight — first-run prerequisite check for the AI Control Center.

Run before (or anytime independent of) the server to verify the environment is ready:
  python preflight.py

Checks Python version, required + optional Python packages, the ffmpeg binary, the local
config, and reachability of Ollama (+ required models) / ComfyUI / Open WebUI. Prints a clear
PASS / WARN / FAIL report. Exit code 0 if there are no hard failures, 1 otherwise.
"""
import sys, json, importlib, urllib.request

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

OK, WARN, FAIL = "PASS", "WARN", "FAIL"
rows = []
def add(level, name, detail=""): rows.append((level, name, detail))

# ── Python version ────────────────────────────────────────
v = sys.version_info
add(OK if v >= (3, 10) else FAIL, "Python", f"{v.major}.{v.minor}.{v.micro} (need ≥ 3.10)")

# ── required packages (dist name → import name) ───────────
REQUIRED = {"fastapi": "fastapi", "uvicorn": "uvicorn", "psutil": "psutil",
            "python-multipart": "multipart", "numpy": "numpy", "pypdf": "pypdf",
            "python-docx": "docx", "reportlab": "reportlab", "playwright": "playwright",
            "faster-whisper": "faster_whisper", "cryptography": "cryptography",
            "websockets": "websockets", "mss": "mss", "pillow": "PIL",
            "imageio": "imageio", "imageio-ffmpeg": "imageio_ffmpeg"}
OPTIONAL = {"pyautogui": "pyautogui", "pyperclip": "pyperclip"}  # click-to-act
for dist, mod in REQUIRED.items():
    try: importlib.import_module(mod); add(OK, f"pkg {dist}")
    except Exception: add(FAIL, f"pkg {dist}", "missing — run: pip install -r requirements.txt")
for dist, mod in OPTIONAL.items():
    try: importlib.import_module(mod); add(OK, f"pkg {dist}", "(optional)")
    except Exception: add(WARN, f"pkg {dist}", "optional — needed only for Screen click-to-act")

# ── ffmpeg (for screen recording) ─────────────────────────
try:
    import imageio_ffmpeg
    add(OK, "ffmpeg", imageio_ffmpeg.get_ffmpeg_exe())
except Exception as e:
    add(WARN, "ffmpeg", f"not resolved ({e}) — screen recording may fail")

# ── config ────────────────────────────────────────────────
try:
    import config  # noqa
    add(OK, "config", "config.py loaded")
    OLLAMA = config.OLLAMA; COMFY_URL = config.COMFY_URL; OWUI_URL = config.OWUI_URL
except Exception as e:
    add(FAIL, "config", f"config.py error: {e}")
    OLLAMA = "http://127.0.0.1:11434"; COMFY_URL = "http://127.0.0.1:8188"; OWUI_URL = "http://127.0.0.1:3000"

def _get(url, timeout=4):
    with urllib.request.urlopen(url, timeout=timeout) as r: return r.read().decode("utf-8", "replace")

# ── Ollama + required models ──────────────────────────────
WANT_MODELS = ("qwen2.5:14b", "nomic-embed-text")
try:
    tags = json.loads(_get(f"{OLLAMA}/api/tags"))
    have = [m["name"] for m in tags.get("models", [])]
    add(OK, "Ollama", f"reachable · {len(have)} models")
    for w in WANT_MODELS:
        present = any(h == w or h.startswith(w) for h in have)
        add(OK if present else WARN, f"model {w}", "installed" if present else f"missing — run: ollama pull {w}")
except Exception as e:
    add(FAIL, "Ollama", f"not reachable at {OLLAMA} ({e}) — start Ollama")

# ── optional services ─────────────────────────────────────
for label, url, path in (("ComfyUI", COMFY_URL, "/system_stats"), ("Open WebUI", OWUI_URL, "/")):
    try: _get(url + path); add(OK, label, "reachable")
    except Exception: add(WARN, label, f"not reachable at {url} (optional — image/video & OWUI features)")

# ── report ────────────────────────────────────────────────
icon = {OK: "✓", WARN: "!", FAIL: "✗"}
print("\n  Nova Control Center — preflight check\n  " + "─" * 44)
for level, name, detail in rows:
    print(f"  [{icon[level]}] {level:4}  {name:<22} {detail}")
fails = sum(1 for r in rows if r[0] == FAIL); warns = sum(1 for r in rows if r[0] == WARN)
print("  " + "─" * 44)
print(f"  {len(rows)} checks · {fails} fail · {warns} warn")
print("  READY ✓\n" if not fails else "  NOT READY — resolve the ✗ items above.\n")
sys.exit(1 if fails else 0)
