# -*- coding: utf-8 -*-
"""LIVE browser tests — exercise nova/services/browser.py against a DISPOSABLE local HTML page in
headless Chromium (real Playwright, no external network, no visible window). Skipped in the normal
gate; run with NOVA_LIVE_TESTS=1 (and Playwright installed) to raise browser coverage:

    NOVA_LIVE_TESTS=1 python -m coverage run -m pytest tests/test_browser_live.py
"""
import os
import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("NOVA_LIVE_TESTS"),
                                reason="live browser test (set NOVA_LIVE_TESTS=1)")

TEST_HTML = """<!doctype html><html><head><title>Nova Browse Target</title></head>
<body>
  <h1 id="hdr">Disposable Target Page</h1>
  <p>The magic token is NOVA-BROWSE-7788.</p>
  <form>
    <input id="q" name="q" type="text">
    <button id="go" type="button" onclick="document.getElementById('out').innerText='clicked:'+document.getElementById('q').value">Go</button>
  </form>
  <div id="out">idle</div>
</body></html>"""


def _url(tmp_path):
    f = tmp_path / "browse_target.html"
    f.write_text(TEST_HTML, encoding="utf-8")
    return f.as_uri()   # file:/// URL


def test_norm_url():
    from nova.services.browser import _norm_url
    assert _norm_url("example.com") == "https://example.com"
    assert _norm_url("http://x.com") == "http://x.com"
    assert _norm_url("file:///c:/x.html").startswith("file:")
    assert _norm_url("  ") == ""


def test_browse_reads_page(tmp_path):
    import importlib.util
    if importlib.util.find_spec("playwright") is None:
        pytest.skip("playwright not installed")
    from nova.services.browser import browse
    r = browse(_url(tmp_path))
    assert r["title"] == "Nova Browse Target"
    assert "NOVA-BROWSE-7788" in r["text"]
    assert r.get("screenshot", "").startswith("/files/")   # screenshot captured


def test_browse_fill_and_click(tmp_path):
    import importlib.util
    if importlib.util.find_spec("playwright") is None:
        pytest.skip("playwright not installed")
    from nova.services.browser import browse
    r = browse(_url(tmp_path), fill={"#q": "hello"}, click="#go", wait=300)
    assert "filled #q" in r["actions"] and "clicked #go" in r["actions"]
    assert "clicked:hello" in r["text"]                    # the JS ran → our fill+click worked


def test_browse_bad_url_raises_handled(tmp_path):
    import importlib.util
    if importlib.util.find_spec("playwright") is None:
        pytest.skip("playwright not installed")
    from nova.services.browser import browse
    with pytest.raises(Exception):                         # navigation to a dead host raises (caller handles)
        browse("http://127.0.0.1:9/nope", timeout=3000)


def test_open_url_default_empty():
    from nova.services.browser import open_url_default
    assert open_url_default("") == ""                      # empty → no-op, no window opened
