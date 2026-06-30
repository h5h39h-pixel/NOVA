# -*- coding: utf-8 -*-
"""Local CI runner — runs the SAME steps as .github/workflows/ci.yml, but on this machine
so CI is actually exercised without a GitHub remote (TST-5) and the pinned requirements are
proven to install together from a clean virtualenv (TST-4).

Steps (mirrors the `quality` job):
  1. create a fresh venv
  2. pip install -r requirements.txt -r requirements-dev.txt   (the clean-install proof)
  3. python scripts/check.py                                    (pyflakes + node --check + pytest)

Usage:
  python scripts/ci_local.py                # temp venv, removed afterward
  python scripts/ci_local.py --keep         # keep the venv for inspection
  python scripts/ci_local.py --venv DIR     # use/explicit venv location

Note: GitHub-hosted execution (windows-latest) still requires pushing to a remote; `act`
cannot emulate Windows runners. This runner is the faithful local equivalent.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _run(cmd, label):
    print(f"\n=== {label} ===\n$ {' '.join(str(c) for c in cmd)}", flush=True)
    t = time.time()
    r = subprocess.run(cmd, cwd=str(ROOT))
    dt = time.time() - t
    ok = r.returncode == 0
    print(f"--- {label}: {'OK' if ok else 'FAILED'} ({dt:.1f}s, exit {r.returncode}) ---", flush=True)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--venv", default=None, help="venv directory (default: a temp dir)")
    ap.add_argument("--keep", action="store_true", help="keep the venv afterward")
    args = ap.parse_args()

    tmp_created = False
    if args.venv:
        venv_dir = Path(args.venv).resolve()
    else:
        venv_dir = Path(tempfile.mkdtemp(prefix="nova-ci-")) / "venv"
        tmp_created = True

    scripts = "Scripts" if os.name == "nt" else "bin"
    vpy = venv_dir / scripts / ("python.exe" if os.name == "nt" else "python")

    print(f"Local CI runner - venv: {venv_dir}")
    steps_ok = []
    try:
        steps_ok.append(_run([sys.executable, "-m", "venv", str(venv_dir)], "create venv"))
        if steps_ok[-1]:
            steps_ok.append(_run([str(vpy), "-m", "pip", "install", "--upgrade", "pip"], "upgrade pip"))
            steps_ok.append(_run([str(vpy), "-m", "pip", "install",
                                  "-r", "requirements.txt", "-r", "requirements-dev.txt"],
                                 "install pinned deps (clean-venv / TST-4)"))
            steps_ok.append(_run([str(vpy), "scripts/check.py"], "quality gate (TST-5)"))
    finally:
        if tmp_created and not args.keep:
            shutil.rmtree(venv_dir.parent, ignore_errors=True)
            print(f"\n(removed temp venv {venv_dir.parent})")
        elif args.keep:
            print(f"\n(kept venv at {venv_dir})")

    passed = all(steps_ok) and len(steps_ok) == 4
    print("\n" + "=" * 56)
    print("LOCAL CI PASSED" if passed else "LOCAL CI FAILED")
    print("=" * 56)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
