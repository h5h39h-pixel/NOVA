# -*- coding: utf-8 -*-
"""Frontend smoke gate — load each route in headless Chromium and assert zero console
errors. Requires a live server on :8900 and Playwright; auto-skips otherwise (so CI and
offline unit runs aren't blocked)."""
import socket
import pytest

BASE = "http://127.0.0.1:8900"
ROUTES = ["dashboard", "monitor", "workspace", "knowledge", "brain", "models",
          "training", "screen", "live", "automation", "settings"]


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


# ---- TST-6: real interaction tests (clicks, routing, controls) ----

@pytest.fixture(scope="module")
def browser():
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        pytest.skip("playwright not installed")
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        yield br
        br.close()


@pytest.fixture
def page(browser):
    pg = browser.new_page()
    pg.add_init_script("localStorage.setItem('onboarded','1')")
    pg.goto(f"{BASE}/#/dashboard", wait_until="networkidle", timeout=30000)
    pg.wait_for_selector("#nav a[data-r='dashboard']", timeout=10000)
    yield pg
    pg.close()


def test_nav_click_routing(page):
    """Clicking sidebar links swaps the page, sets the title, marks the link active, updates the hash."""
    for rid, title in [("workspace", "Nova"), ("monitor", "System Monitor"), ("settings", "Settings")]:
        page.click(f"#nav a[data-r='{rid}']")
        page.wait_for_function(
            "t => document.querySelector('#main .page-head h2') "
            "&& document.querySelector('#main .page-head h2').textContent === t",
            arg=title, timeout=8000)
        assert page.eval_on_selector(f"#nav a[data-r='{rid}']",
                                     "el => el.classList.contains('active')")
        assert page.evaluate("location.hash") == f"#/{rid}"
        assert page.eval_on_selector("#pagebody", "el => el.innerHTML.length > 0")


def test_deep_link_routing(page):
    """A direct hash URL renders the right page (not just the default dashboard)."""
    page.goto(f"{BASE}/#/brain", wait_until="networkidle", timeout=30000)
    page.wait_for_selector("#main .page-head h2", timeout=8000)
    assert "Nova Brain" in page.text_content("#main .page-head h2")
    assert page.eval_on_selector("#nav a[data-r='brain']", "el => el.classList.contains('active')")


def test_theme_toggle(page):
    """The theme button flips light/dark on <body> and is reversible."""
    before = page.eval_on_selector("body", "el => el.classList.contains('light')")
    page.click("#themebtn")
    page.wait_for_timeout(150)
    after = page.eval_on_selector("body", "el => el.classList.contains('light')")
    assert after != before
    page.click("#themebtn")                                   # restore
    page.wait_for_timeout(150)
    assert page.eval_on_selector("body", "el => el.classList.contains('light')") == before


def test_command_palette(page):
    """Ctrl+K opens the palette, typing filters results, Escape closes it."""
    page.keyboard.press("Control+k")
    page.wait_for_selector("#palette.open", timeout=5000)
    page.fill("#palin", "settings")
    page.wait_for_timeout(500)                                # debounce (250ms) + render
    matches = page.eval_on_selector_all("#palres [data-i]", "els => els.map(e => e.textContent)")
    assert any("Settings" in m for m in matches), f"palette results: {matches}"
    page.keyboard.press("Escape")
    page.wait_for_timeout(150)
    assert not page.eval_on_selector("#palette", "el => el.classList.contains('open')")
