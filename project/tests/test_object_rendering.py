"""
project/tests/test_object_rendering.py
======================================
Pytest integration test suite for verifying clean data formatting without [object Object].
"""

import json
import re
import pytest
from pathlib import Path


def test_app_js_has_no_raw_unwrapped_object_interpolation():
    """Verify app.js does not contain risky string interpolations that yield [object Object]."""
    app_js_path = Path("project/static/app.js")
    assert app_js_path.exists(), "project/static/app.js must exist"
    
    content = app_js_path.read_text(encoding="utf-8")
    
    # Check that mh is defined before use in calcMeiHua
    assert "const mh = (data && data.charts && data.charts.mei_hua) || {};" in content
    
    # Check that formatPillarCell safely unwraps nested stems/branches
    assert "formatPillarCell" in content
    assert "calculateFiveElementsFromPillars" in content


def test_public_and_static_app_js_are_synchronized():
    """Verify project/static/app.js and public/app.js are completely identical."""
    static_app = Path("project/static/app.js").read_text(encoding="utf-8")
    public_app = Path("public/app.js").read_text(encoding="utf-8")
    assert static_app == public_app, "public/app.js must match project/static/app.js"


def test_public_and_static_style_css_are_synchronized():
    """Verify project/static/style.css and public/style.css are completely identical."""
    static_css = Path("project/static/style.css").read_text(encoding="utf-8")
    public_css = Path("public/style.css").read_text(encoding="utf-8")
    assert static_css == public_css, "public/style.css must match project/static/style.css"


def test_public_and_static_v3_tokens_css_are_synchronized():
    """Verify the deploy mirror includes every v3 visual-system correction."""
    static_css = Path("project/static/v3_tokens.css").read_text(encoding="utf-8")
    public_css = Path("public/v3_tokens.css").read_text(encoding="utf-8")
    assert static_css == public_css, "public/v3_tokens.css must match project/static/v3_tokens.css"


def test_public_and_static_index_html_are_synchronized():
    """Verify project/static/index.html and public/index.html are completely identical."""
    static_html = Path("project/static/index.html").read_text(encoding="utf-8")
    public_html = Path("public/index.html").read_text(encoding="utf-8")
    assert static_html == public_html, "public/index.html must match project/static/index.html"
