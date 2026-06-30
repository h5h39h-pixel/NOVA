#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Export the FastAPI OpenAPI schema to docs/openapi.json (curated API reference).
The live, interactive docs are always at http://localhost:8900/docs."""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import server  # noqa: E402

out = os.path.join(ROOT, "docs", "openapi.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
schema = server.app.openapi()
with open(out, "w", encoding="utf-8") as f:
    json.dump(schema, f, indent=2)
paths = len(schema.get("paths", {}))
print(f"wrote {out} — {paths} paths, title: {schema.get('info', {}).get('title')}")
