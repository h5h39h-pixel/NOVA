#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""One-command HTTPS toggle (SEC-5).

  python scripts/https.py enable     # turn TLS on + generate the self-signed cert now
  python scripts/https.py disable    # turn TLS off (plain HTTP)

Flips `https_enabled` in config.json and (on enable) pre-generates the self-signed cert so the
next server start serves TLS immediately. Restart the server after running this."""
import sys, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
CFG = ROOT / "config.json"

action = (sys.argv[1] if len(sys.argv) > 1 else "enable").lower()
if action not in ("enable", "disable"):
    print("usage: python scripts/https.py [enable|disable]"); sys.exit(2)
on = action == "enable"

cfg = json.loads(CFG.read_text(encoding="utf-8-sig")) if CFG.exists() else {}
cfg["https_enabled"] = on
CFG.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
port = cfg.get("port", 8900)
print(f"config.json: https_enabled = {on}")

if on:
    import config  # reads the just-written config.json
    crt, key = config.ensure_cert()
    print(f"self-signed cert ready:\n  {crt}\n  {key}")
    print(f"\nNow restart the server, then open  https://localhost:{port}")
    print("(your browser will warn once about the self-signed cert — accept it).")
else:
    print(f"\nNow restart the server; it will serve plain HTTP at  http://localhost:{port}")
