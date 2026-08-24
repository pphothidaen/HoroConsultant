"""Unit and contract tests for visual layout auditor."""

import json
from pathlib import Path
import pytest
from scripts.run_visual_layout_audit import (
    VIEWPORT_MATRIX,
    DEFAULT_PAGES,
    DOM_AUDIT_JS,
    build_parser,
)

ROOT = Path(__file__).resolve().parents[1]


def test_viewport_matrix_covers_all_target_devices():
    assert "desktop-4k" in VIEWPORT_MATRIX
    assert "laptop-standard" in VIEWPORT_MATRIX
    assert "tablet-portrait" in VIEWPORT_MATRIX
    assert "mobile-ios" in VIEWPORT_MATRIX
    assert "mobile-compact" in VIEWPORT_MATRIX

    for name, config in VIEWPORT_MATRIX.items():
        assert config["width"] > 0
        assert config["height"] > 0
        assert "category" in config


def test_default_pages_contain_core_views():
    page_names = [p["name"] for p in DEFAULT_PAGES]
    assert "main_dashboard" in page_names
    assert "admin_panel" in page_names


def test_dom_audit_js_contains_overlap_and_overflow_logic():
    assert "scrollWidth" in DOM_AUDIT_JS
    assert "getBoundingClientRect" in DOM_AUDIT_JS
    assert "hasHorizontalOverflow" in DOM_AUDIT_JS
    assert "overlaps" in DOM_AUDIT_JS


def test_cli_parser_defaults_and_options():
    parser = build_parser()
    args = parser.parse_args(["--url", "http://example.com", "--viewports", "desktop-4k", "mobile-ios", "--json"])
    assert args.url == "http://example.com"
    assert args.viewports == ["desktop-4k", "mobile-ios"]
    assert args.json is True
