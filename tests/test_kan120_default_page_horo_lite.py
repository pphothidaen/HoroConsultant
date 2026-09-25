"""TDD regression tests for KAN-120: Set Horo Lite as default landing page with bidirectional mode switch."""

from __future__ import annotations

import json
import re
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_vercel_rewrites_root_to_lite():
    """Verify vercel.json rewrites / to /lite.html and /advanced to /index.html."""
    vercel_path = ROOT / "vercel.json"
    assert vercel_path.exists()
    config = json.loads(vercel_path.read_text(encoding="utf-8"))
    rewrites = config.get("rewrites", [])

    rewrite_map = {r.get("source"): r.get("destination") for r in rewrites}
    assert rewrite_map.get("/") == "/lite.html", "vercel.json missing rewrite for '/' -> '/lite.html'"
    assert rewrite_map.get("/advanced") == "/index.html", "vercel.json missing rewrite for '/advanced' -> '/index.html'"


def test_lite_html_has_version_and_switch_button():
    """Verify public/lite.html includes CURRENT_PAGE_VERSION, footer-version-text, and mode switch button."""
    lite_path = ROOT / "public" / "lite.html"
    assert lite_path.exists()
    content = lite_path.read_text(encoding="utf-8")

    assert "window.CURRENT_PAGE_VERSION" in content, "public/lite.html missing window.CURRENT_PAGE_VERSION"
    assert 'id="footer-version-text"' in content, "public/lite.html missing footer-version-text element"
    assert 'href="/advanced"' in content, "public/lite.html missing link to /advanced"
    assert 'id="mode-switch-advanced"' in content, "public/lite.html missing #mode-switch-advanced button"


def test_index_html_has_switch_button():
    """Verify public/index.html has mode switch button linking to / (Horo Lite)."""
    index_path = ROOT / "public" / "index.html"
    assert index_path.exists()
    content = index_path.read_text(encoding="utf-8")

    assert 'id="mode-switch-lite"' in content, "public/index.html missing #mode-switch-lite button"
    assert 'href="/"' in content or 'href="/lite"' in content, "public/index.html missing link to /"


def test_main_py_has_advanced_route():
    """Verify project/main.py has /advanced endpoint serving index.html."""
    main_path = ROOT / "project" / "main.py"
    assert main_path.exists()
    content = main_path.read_text(encoding="utf-8")

    assert '@app.get("/advanced"' in content, "project/main.py missing /advanced route handler"


def test_stamp_version_tracks_lite_html():
    """Verify scripts/stamp_version.py includes lite.html in tracked target files."""
    stamp_path = ROOT / "scripts" / "stamp_version.py"
    assert stamp_path.exists()
    content = stamp_path.read_text(encoding="utf-8")

    assert "lite.html" in content, "scripts/stamp_version.py does not track lite.html"
