#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Local quality gate — pyflakes + node --check + pytest. Used by the git pre-commit
hook (.githooks/pre-commit) and CI. Exit code 0 only if everything passes."""
import subprocess, sys, shutil, glob, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
PY = sys.executable
fails = []

def run(label, cmd):
    print(f"\n=== {label} ===")
    try:
        if subprocess.run(cmd).returncode != 0:
            fails.append(label)
    except Exception as e:
        print(f"  error: {e}"); fails.append(label)

# 1) pyflakes over all Python
pyfiles = ["server.py", "config.py", "preflight.py"]
pyfiles += glob.glob("nova/**/*.py", recursive=True) + glob.glob("tests/*.py") + glob.glob("scripts/*.py")
run("pyflakes", [PY, "-m", "pyflakes", *pyfiles])

# 2) node --check over the SPA modules
node = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
if os.path.exists(node):
    for f in sorted(glob.glob("static/js/*.js")):
        run(f"node --check {os.path.basename(f)}", [node, "--check", f])
else:
    print("\n=== node --check ===\n  node not found — skipping JS syntax check")

# 3) pytest (frontend gate auto-skips when no server is running)
run("pytest", [PY, "-m", "pytest", "-q"])

print("\n" + "=" * 48)
if fails:
    print("QUALITY GATE FAILED: " + ", ".join(fails)); sys.exit(1)
print("QUALITY GATE PASSED"); sys.exit(0)
