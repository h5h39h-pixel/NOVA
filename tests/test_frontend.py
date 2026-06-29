# -*- coding: utf-8 -*-
"""Frontend smoke gate — load each route in headless Chromium and assert zero console
errors. Requires a live server on :8900 and Playwright; auto-skips otherwise (so CI and
offline unit runs aren't blocked)."""
import socket
import pytest

BASE = "http://127.0.0.1:8900"
ROUTES = ["dashboard", "monitor", "chat", "agent", "knowledge", "brain", "models",
          "training", "screen", "automation", "settings"]


def _server_up():
    try:
        with socket.create_connection(("127.0.0.1", 8900), timeout=1):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(not _server_up(), reason="no live server on :8900")


def test_routes_have_no_console_errors():
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        pytest.skip("playwright not installed")
    failures = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        pg = br.new_page()
        pg.add_init_script("localStorage.setItem('onboarded','1')")
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        for r in ROUTES:
            errs.clear()
            pg.goto(f"{BASE}/#/{r}", wait_until="networkidle", timeout=30000)
            pg.wait_for_timeout(900)
            real = [e for e in errs if "favicon" not in e.lower()]
            if real:
                failures[r] = real[:3]
        br.close()
    assert not failures, f"console errors: {failures}"
