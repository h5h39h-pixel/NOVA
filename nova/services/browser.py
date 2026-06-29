# -*- coding: utf-8 -*-
"""Browser automation — headless page fetch (`browse`), opening URLs in the user's
default browser (`open_url_default`), and a persistent on-screen Chromium driven by
Playwright (`visible_browse`, incl. YouTube search/play). Playwright is imported
lazily so the server runs without it installed. Depends only on config (UPLOAD_DIR)."""
import os
import re
import queue
import threading
import subprocess
import urllib.parse
import uuid
from config import UPLOAD_DIR


def _norm_url(url):
    url = (url or "").strip()
    if url and not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", url):
        url = "https://" + url
    return url


def browse(url, fill=None, click=None, wait=None, screenshot=True, timeout=30000):
    """Open a real web page in headless Chromium; optionally fill fields + click,
    then capture title, visible text, and a screenshot. Runs sync Playwright — call
    only from a worker thread (no asyncio loop), e.g. via asyncio.to_thread or the agent thread."""
    from playwright.sync_api import sync_playwright
    url = _norm_url(url)
    result = {"url": url, "actions": []}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        try:
            pg = br.new_page()
            pg.goto(url, timeout=timeout, wait_until="domcontentloaded")
            if fill:
                items = fill.items() if isinstance(fill, dict) else fill
                for sel, val in items:
                    pg.fill(sel, str(val), timeout=timeout); result["actions"].append(f"filled {sel}")
            if click:
                for sel in ([click] if isinstance(click, str) else click):
                    pg.click(sel, timeout=timeout); result["actions"].append(f"clicked {sel}")
            if wait:
                pg.wait_for_timeout(min(int(wait), 15000))
            result["title"] = pg.title()
            result["final_url"] = pg.url
            try: result["text"] = (pg.inner_text("body") or "")[:2000]
            except Exception: result["text"] = ""
            if screenshot:
                UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
                fn = f"browse_{uuid.uuid4().hex[:8]}.png"
                pg.screenshot(path=str(UPLOAD_DIR / fn))
                result["screenshot"] = f"/files/{fn}"
        finally:
            br.close()
    return result


def open_url_default(url):
    """Open a URL in the user's DEFAULT browser (Chrome/Edge) — a real, visible window."""
    url = _norm_url(url)
    if not url:
        return ""
    try:
        os.startfile(url)  # Windows shell → default http(s) handler = default browser
    except Exception:
        subprocess.Popen(["cmd", "/c", "start", "", url], shell=False)
    return url


class VisibleBrowser:
    """A persistent, on-screen Chromium controlled by Playwright. All Playwright calls run on a
    single dedicated thread (sync API is thread-affine); the window is left OPEN so the user can
    watch and interact. Lazily launched on first use; auto-recovers if the window was closed."""
    def __init__(self):
        self.q = queue.Queue()
        self.thread = None
        self.pw = self.browser = self.ctx = self.page = None

    def _ensure(self):
        if self.pw is None:
            from playwright.sync_api import sync_playwright
            self.pw = sync_playwright().start()
        if self.browser is None or not self.browser.is_connected():
            self.browser = self.pw.chromium.launch(headless=False, args=[
                "--start-maximized", "--autoplay-policy=no-user-gesture-required",
                "--disable-blink-features=AutomationControlled"])
            self.ctx = self.page = None
        if self.ctx is None:
            self.ctx = self.browser.new_context(no_viewport=True)
        if self.page is None or self.page.is_closed():
            pages = self.ctx.pages
            self.page = pages[0] if pages else self.ctx.new_page()

    def _loop(self):
        while True:
            fn, fut = self.q.get()
            if fn is None:
                break
            try:
                self._ensure()
                self.page.bring_to_front()
                fut["result"] = fn(self.page)
            except Exception as e:
                fut["error"] = e
            finally:
                fut["event"].set()

    def submit(self, fn, timeout=90):
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()
        fut = {"event": threading.Event()}
        self.q.put((fn, fut))
        if not fut["event"].wait(timeout):
            raise TimeoutError("visible browser operation timed out")
        if "error" in fut:
            raise fut["error"]
        return fut.get("result")


VB = VisibleBrowser()


def _dismiss_consent(page):
    for sel in ('button[aria-label*="Accept all"]', 'button[aria-label*="Accept the use of cookies"]',
                'tp-yt-paper-button:has-text("Accept all")', 'button:has-text("Accept all")',
                'form[action*="consent"] button'):
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible():
                el.click(timeout=2500); page.wait_for_timeout(800); return
        except Exception:
            pass


def _youtube(page, query, click_first):
    page.goto("https://www.youtube.com/results?search_query=" + urllib.parse.quote(query),
              wait_until="domcontentloaded", timeout=45000)
    _dismiss_consent(page)
    try: page.wait_for_selector("a#video-title", timeout=15000)
    except Exception: pass
    vids = []
    for el in page.locator("a#video-title").all()[:6]:
        t = (el.get_attribute("title") or el.inner_text() or "").strip()
        h = el.get_attribute("href") or ""
        if h and t:
            vids.append({"title": t, "url": ("https://www.youtube.com" + h) if h.startswith("/") else h})
    out = {"query": query, "results": vids}
    if click_first and vids:
        try:
            page.locator("a#video-title").first.click(timeout=10000)
            page.wait_for_timeout(3000)
            try: page.keyboard.press("k")  # ensure playback starts
            except Exception: pass
            out["opened"] = {"title": page.title(), "url": page.url}
        except Exception as e:
            out["click_error"] = str(e)
    return out


def visible_browse(url=None, search=None, click_first=False, fill=None, click=None):
    """Open / drive the on-screen browser. If `search` is given, search YouTube (and open the
    first video when click_first). Otherwise navigate to `url`. The window stays open."""
    def op(page):
        if search:
            return _youtube(page, search, click_first)
        u = _norm_url(url)
        page.goto(u, wait_until="domcontentloaded", timeout=45000)
        if fill:
            for sel, val in (fill.items() if isinstance(fill, dict) else fill):
                try: page.fill(sel, str(val), timeout=8000)
                except Exception: pass
        if click:
            for sel in ([click] if isinstance(click, str) else click):
                try: page.click(sel, timeout=8000)
                except Exception: pass
        page.wait_for_timeout(1200)
        return {"title": page.title(), "url": page.url}
    return VB.submit(op, timeout=120)
