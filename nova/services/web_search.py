# -*- coding: utf-8 -*-
"""Web search — DuckDuckGo via the `ddgs` library (no API key). Powers the chat "Web Search"
toggle: fetch the top results for a query so the model can answer with current, cited information.

This is the one deliberately ONLINE feature; it's opt-in per message (the Web Search toggle) and
degrades gracefully to [] when offline, so the rest of the app stays offline-capable."""


def web_search(query, k=4):
    """Return up to k results: [{title, url, snippet}]. Empty list on any failure (offline, etc.)."""
    q = (query or "").strip()
    if not q:
        return []
    try:
        from ddgs import DDGS
    except Exception:
        return []
    try:
        with DDGS() as d:
            raw = list(d.text(q, max_results=k))
    except Exception:
        return []
    out = []
    for r in raw[:k]:
        out.append({
            "title": (r.get("title") or "").strip(),
            "url": (r.get("href") or r.get("url") or "").strip(),
            "snippet": (r.get("body") or r.get("snippet") or "").strip(),
        })
    return out


def web_context(query, k=4):
    """Format search results as a context block + citation list for injection into a chat turn."""
    res = web_search(query, k)
    if not res:
        return "", []
    block = "Live web search results (cite the source URL when you use one):\n" + "\n---\n".join(
        f"[{i+1}] {r['title']}\n{r['snippet']}\nSource: {r['url']}" for i, r in enumerate(res))
    sources = [{"doc": r["title"] or r["url"], "url": r["url"]} for r in res]
    return block, sources
