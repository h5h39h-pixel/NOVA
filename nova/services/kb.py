# -*- coding: utf-8 -*-
"""Knowledge base — local RAG. Embeds text via Ollama (nomic-embed-text), stores
chunks in SQLite, and does cosine-similarity retrieval. Depends on nova.core (db,
http), nova.services.files (extract/chunk), and config (the OLLAMA endpoint)."""
import json
import time
from config import OLLAMA
from nova.core.db import db
from nova.core.http import http_json
from nova.services.files import extract_text, chunk_text

EMBED_MODEL = "nomic-embed-text"


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
