"""Unit and contract tests for visual layout auditor."""

import json
from pathlib import Path
import pytest
from scripts.run_visual_layout_audit import (
    DEFAULT_PAGES,
    DOM_AUDIT_JS,
    SCENARIO_DEFINITIONS,
    V3_CONSENSUS_FIXTURE,
    VIEWPORT_MATRIX,
    build_parser,
    summary_exit_code,
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
    assert "elA.parentElement !== elB.parentElement" in DOM_AUDIT_JS
    assert "outOfBounds" in DOM_AUDIT_JS
    assert "clippedElements" in DOM_AUDIT_JS


def test_dom_audit_js_contains_wcag_and_gradient_manual_review_logic():
    assert "contrastRatio" in DOM_AUDIT_JS
    assert "requiredRatio" in DOM_AUDIT_JS
    assert "gradient_or_background_image" in DOM_AUDIT_JS
    assert "contrastIndeterminate" in DOM_AUDIT_JS


def test_v3_consensus_scenario_is_deterministic_and_scoped_to_selected_card():
    scenario = SCENARIO_DEFINITIONS["v3-consensus"]
    assert scenario["scope_selector"] == "#interpretation-card"
    assert scenario["color_scheme"] == "dark"
    assert scenario["theme"] == "dark"
    assert scenario["pages"] == [
        {"name": "horo_v3_consensus", "path": "/", "setup": "v3-consensus"}
    ]
    assert V3_CONSENSUS_FIXTURE["audit_verdict"] == "AUDIT_PASS"
    assert V3_CONSENSUS_FIXTURE["lciw"] == pytest.approx(0.9125)
    assert V3_CONSENSUS_FIXTURE["rniw"] == pytest.approx(0.0875)


def test_default_scenario_remains_backward_compatible():
    assert SCENARIO_DEFINITIONS["default"]["pages"] is DEFAULT_PAGES
    assert SCENARIO_DEFINITIONS["default"]["scope_selector"] == "body"


def test_visual_audit_exit_code_blocks_warning_reports():
    assert summary_exit_code({"overall_status": "PASSED"}) == 0
    assert summary_exit_code({"overall_status": "WARNING"}) == 1
    assert summary_exit_code({"overall_status": "FAILED"}) == 1


def test_cli_parser_defaults_and_options():
    parser = build_parser()
    args = parser.parse_args(["--url", "http://example.com", "--viewports", "desktop-4k", "mobile-ios", "--json"])
    assert args.url == "http://example.com"
    assert args.viewports == ["desktop-4k", "mobile-ios"]
    assert args.json is True
    assert args.scenario == "default"

    v3_args = parser.parse_args(["--scenario", "v3-consensus"])
    assert v3_args.scenario == "v3-consensus"
