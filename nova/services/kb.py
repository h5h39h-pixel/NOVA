# -*- coding: utf-8 -*-
"""Knowledge base — local RAG. Embeds text via Ollama (nomic-embed-text), stores
chunks in SQLite, and does cosine-similarity retrieval. Depends on nova.core (db,
http), nova.services.files (extract/chunk), and config (the OLLAMA endpoint)."""
import json
import time
from pathlib import Path
from config import OLLAMA
from nova.core.db import db
from nova.core.http import http_json
from nova.core.safety import is_credential_path
from nova.services.files import extract_text, chunk_text

EMBED_MODEL = "nomic-embed-text"
# file types the extractor understands (IDEA-5 folder Q&A walks a directory for these)
KB_EXTS = (".txt", ".md", ".json", ".csv", ".log", ".py", ".js", ".ps1", ".pdf", ".docx")


def embed(text):
    try:
        r = http_json(f"{OLLAMA}/api/embeddings", body={"model": EMBED_MODEL, "prompt": (text or "")[:8000]}, timeout=60)
        return r.get("embedding") or []
    except Exception:
        return []


def kb_status():
    c = db(); docs = c.execute("SELECT COUNT(*) FROM kb_docs").fetchone()[0]
    chunks = c.execute("SELECT COUNT(*) FROM kb_chunks").fetchone()[0]; c.close()
    try: avail = any(m["name"].startswith(EMBED_MODEL) for m in http_json(f"{OLLAMA}/api/tags").get("models", []))
    except Exception: avail = False
    return {"docs": docs, "chunks": chunks, "embed_model": EMBED_MODEL, "available": avail}


def kb_search(query, k=4):
    qv = embed(query)
    if not qv: return []
    c = db(); rows = c.execute("SELECT c.text, c.emb, d.name FROM kb_chunks c JOIN kb_docs d ON d.id=c.doc_id").fetchall(); c.close()
    if not rows: return []
    import numpy as np
    q = np.asarray(qv, dtype="float32"); q /= (np.linalg.norm(q) + 1e-8); scored = []
    for r in rows:
        try: e = np.asarray(json.loads(r["emb"]), dtype="float32")
        except Exception: continue
        e /= (np.linalg.norm(e) + 1e-8); scored.append((float(np.dot(q, e)), r["text"], r["name"]))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"score": round(s, 3), "text": t, "doc": d} for s, t, d in scored[:k]]


def kb_ingest_file(path):
    """Synchronously index a single file into the KB; returns chunk count."""
    chunks = chunk_text(extract_text(path))
    if not chunks: return 0
    c = db(); did = c.execute("INSERT INTO kb_docs(name,chunks,created) VALUES(?,?,?)", (path.name, 0, time.time())).lastrowid; c.commit()
    n = 0
    for i, ch in enumerate(chunks):
        v = embed(ch)
        if not v: continue
        c.execute("INSERT INTO kb_chunks(doc_id,ord,text,emb) VALUES(?,?,?,?)", (did, i, ch, json.dumps(v))); n += 1
    c.execute("UPDATE kb_docs SET chunks=? WHERE id=?", (n, did)); c.commit(); c.close()
    return n


def kb_ingest_folder(folder, recursive=True, max_files=200):
    """IDEA-5 Folder Q&A — index every supported file in a directory into the KB so you can chat
    over the folder with citations. Skips credential stores and unsupported types. Returns a
    summary dict. Local-only; the path is owner-provided (gated by exec_allowed at the API)."""
    root = Path(folder).expanduser()
    if not root.exists() or not root.is_dir():
        return {"ok": False, "error": f"not a folder: {root}"}
    if is_credential_path(root):
        return {"ok": False, "error": "that folder is a credential store and cannot be indexed"}
    walker = root.rglob("*") if recursive else root.glob("*")
    files, skipped = [], 0
    for p in walker:
        if not p.is_file():
            continue
        if p.suffix.lower() not in KB_EXTS or is_credential_path(p):
            skipped += 1
            continue
        files.append(p)
        if len(files) >= max_files:
            break
    indexed, chunks = 0, 0
    for p in files:
        try:
            n = kb_ingest_file(p)
            if n:
                indexed += 1; chunks += n
        except Exception:
            skipped += 1
    return {"ok": True, "folder": str(root), "files_found": len(files), "indexed": indexed,
            "chunks": chunks, "skipped": skipped,
            "capped": len(files) >= max_files}
