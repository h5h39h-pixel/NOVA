# -*- coding: utf-8 -*-
"""Conversation & message store + the streaming chat-send flow.

Conversations group messages; messages live in the `chat` table. These helpers are
the single source of truth for creating/touching conversations and reading/clearing
their messages, and `stream_chat_send` runs the live token-streaming turn (optional
RAG retrieval + optional two-model comparison). Routes live in nova/api/conversations.py
and nova/api/chat.py. Depends on nova.core (db/events) + nova.services (kb/notifications)
+ config (the OLLAMA endpoint)."""
import uuid
import time
import json
import threading
import urllib.request
from config import OLLAMA
from nova.core.db import db, add_history
from nova.core.events import push
from nova.services.notifications import add_notification
from nova.services.kb import kb_search

# Serializes local model inference so two chat turns don't fight over the GPU.
chat_lock = threading.Lock()

# One id per server run; groups the messages written during this process lifetime.
SESSION_ID = uuid.uuid4().hex[:12]


def conv_ensure(cid=None, project="General", title=None):
    c = db()
    if cid:
        if c.execute("SELECT 1 FROM conversations WHERE cid=?", (cid,)).fetchone():
            c.close(); return cid
    cid = cid or uuid.uuid4().hex[:12]
    c.execute("INSERT OR IGNORE INTO conversations(cid,project,title,created,updated) VALUES(?,?,?,?,?)",
              (cid, project, title or "New chat", time.time(), time.time()))
    c.commit(); c.close(); return cid


def conv_touch(cid, add_tokens=0, first_user=None):
    c = db()
    c.execute("UPDATE conversations SET updated=?, tokens=tokens+? WHERE cid=?", (time.time(), add_tokens, cid))
    if first_user:
        c.execute("UPDATE conversations SET title=? WHERE cid=? AND (title IS NULL OR title='New chat')",
                  (first_user[:48], cid))
    c.commit(); c.close()


def chat_add(cid, role, content, model=None):
    c = db()
    c.execute("INSERT INTO chat(ts,session_id,cid,role,content,model_used) VALUES(?,?,?,?,?,?)",
              (time.time(), SESSION_ID, cid, role, content, model))
    c.commit()
    n = c.execute("SELECT COUNT(*) FROM chat WHERE cid=?", (cid,)).fetchone()[0]
    c.close(); return n


def conv_messages(cid, limit=200):
    c = db(); rows = c.execute("SELECT role,content FROM chat WHERE cid=? ORDER BY id ASC LIMIT ?", (cid, limit)).fetchall(); c.close()
    return [{"role": r["role"], "content": r["content"]} for r in rows]


def conv_clear(cid):
    c = db(); c.execute("DELETE FROM chat WHERE cid=?", (cid,)); c.execute("UPDATE conversations SET tokens=0 WHERE cid=?", (cid,)); c.commit(); c.close()


def chat_count():
    c = db(); n = c.execute("SELECT COUNT(*) FROM chat").fetchone()[0]; c.close(); return n


def stream_chat_send(prompt, model, cid, context="", target=None, use_rag=False,
                     deepthink=False, websearch=False):
    """Run one chat turn on a background thread, streaming tokens over the WS bus.
    Optionally retrieves RAG context, runs a live web search, enables deep step-by-step
    reasoning, and/or runs a second model for side-by-side compare. Returns immediately."""
    sources = []  # knowledge-base + web retrieval citations
    DEEPTHINK_SYS = ("Think carefully and reason step by step before answering. Work through the "
                     "problem methodically, consider edge cases, then give a clear, well-structured "
                     "final answer.")

    def run_model(mdl, ev_prefix=""):
        msgs = []
        if deepthink:
            msgs.append({"role": "system", "content": DEEPTHINK_SYS})
        if context:
            msgs.append({"role": "system", "content": "Use this attached document as context:\n" + context[:8000]})
        msgs += conv_messages(cid, 40)
        push({"type": "chat", "ev": "start", "model": mdl, "slot": ev_prefix, "cid": cid})
        body = {"model": mdl, "messages": msgs, "stream": True}
        if deepthink:
            body["options"] = {"num_predict": 1536}   # give reasoning room to breathe
        data = json.dumps(body).encode()
        rq = urllib.request.Request(f"{OLLAMA}/api/chat", data=data,
                                    headers={"Content-Type": "application/json"}, method="POST")
        full = ""; toks = 0
        with urllib.request.urlopen(rq, timeout=600) as r:
            for raw in r:
                try: j = json.loads(raw.decode("utf-8"))
                except Exception: continue
                t = (j.get("message") or {}).get("content", "")
                if t: full += t; push({"type": "chat", "ev": "token", "text": t, "slot": ev_prefix})
                if j.get("done"):
                    toks = (j.get("prompt_eval_count", 0) or 0) + (j.get("eval_count", 0) or 0); break
        return full, toks

    def work():
        if not chat_lock.acquire(blocking=False):
            push({"type": "chat", "ev": "error", "text": "model is busy"}); return
        nonlocal context
        t0 = time.time()
        try:
            chat_add(cid, "user", prompt, model)
            conv_touch(cid, first_user=prompt)
            if use_rag:                               # retrieve from the knowledge base
                hits = kb_search(prompt, 4)
                if hits:
                    kb_ctx = "Relevant knowledge from the user's library (cite when used):\n" + "\n---\n".join(h["text"] for h in hits)
                    context = (context + "\n\n" + kb_ctx) if context else kb_ctx
                    seen = set()
                    for h in hits:
                        if h["doc"] not in seen: seen.add(h["doc"]); sources.append({"doc": h["doc"], "score": h["score"]})
            if websearch:                             # live web search (opt-in, online)
                from nova.services.web_search import web_context
                web_ctx, web_src = web_context(prompt, 4)
                if web_ctx:
                    context = (context + "\n\n" + web_ctx) if context else web_ctx
                    sources.extend(web_src)
                else:
                    push({"type": "chat", "ev": "token", "text": "_(web search returned no results / offline)_\n\n"})
            if target and target != model:            # model comparison: run both, save primary
                a_full, a_tok = run_model(model, "A")
                b_full, b_tok = run_model(target, "B")
                saved = chat_add(cid, "assistant", a_full, model)
                conv_touch(cid, add_tokens=a_tok + b_tok)
                push({"type": "chat", "ev": "end", "model": model, "count": saved, "cid": cid, "sources": sources,
                      "compare": {"a": {"model": model, "text": a_full}, "b": {"model": target, "text": b_full}}})
            else:
                full, toks = run_model(model)
                saved = chat_add(cid, "assistant", full, model)
                conv_touch(cid, add_tokens=toks)
                push({"type": "chat", "ev": "end", "model": model, "count": saved, "cid": cid,
                      "tokens": toks, "secs": round(time.time() - t0, 1), "sources": sources})
            add_history(f"[chat:{model}] {prompt[:50]}", 0, time.time() - t0, "", "chat")
        except Exception as e:
            push({"type": "chat", "ev": "error", "text": str(e)})
            add_notification("error", "Chat failed", str(e))
        finally:
            chat_lock.release()

    threading.Thread(target=work, daemon=True).start()
