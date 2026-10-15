"""Pytest wrapper for Production Horo Lite E2E Suite (TICKET-HLITE-014).

Verifies:
  - Success Scenario: 12 topic cards sequence, Thai prediction copy, score gauges,
    past pattern chips, export actions, and screenshot.
  - Failed Scenario: 503 error display, is-error class, retry button accessibility,
    payload retention, and screenshot.
  - Execution Report: JSON report validity and status.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

pytest.importorskip("playwright")
from playwright.async_api import async_playwright

from scripts.run_prod_lite_e2e import (
    DEFAULT_PROD_URL,
    REPORT_PATH,
    SCREENSHOT_DIR,
    TARGET_URL,
    run_failed_scenario,
    run_jack_scenario,
    run_prod_lite_e2e_suite,
    run_success_scenario,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.asyncio
async def test_prod_lite_e2e_success_scenario():
    """Verify live Horo Lite success scenario with Thai prediction copy and interactive controls."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="th-TH",
        )
        page = await context.new_page()
        try:
            result = await run_success_scenario(page, TARGET_URL)
            assert result["status"] == "PASSED"

            check_names = [c["check"] for c in result["checks"]]
            assert "canonical_topic_cards_sequence" in check_names
            assert "prediction_copy_rendered" in check_names
            assert "score_gauges_accessibility" in check_names
            assert "past_pattern_calibration_chips" in check_names
            assert "export_actions_available" in check_names
            assert "success_screenshot" in check_names

            # Verify screenshot exists on disk
            shot_file = SCREENSHOT_DIR / "prod_lite_e2e_success.png"
            assert shot_file.exists() and shot_file.stat().st_size > 0
        finally:
            await page.close()
            await context.close()
            await browser.close()


@pytest.mark.asyncio
async def test_prod_lite_e2e_jack_scenario():
    """Verify live Horo Lite User scenario (Jack: 2026-10-15, unknown_hour=True, 2026 target)."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="th-TH",
        )
        page = await context.new_page()
        try:
            result = await run_jack_scenario(page, TARGET_URL)
            assert result["status"] == "PASSED"

            check_names = [c["check"] for c in result["checks"]]
            assert "canonical_topic_cards_sequence" in check_names
            assert "prediction_copy_rendered" in check_names
            assert "hitl_3_pillar_alert_reassuring" in check_names
            assert "hitl_deep_synthesis_card_below_topics" in check_names
            assert "submit_cooldown_15s_behavior" in check_names
            assert "score_gauges_accessibility" in check_names
            assert "zero_503_error_state" in check_names
            assert "jack_screenshot" in check_names

            # Verify screenshot exists on disk
            shot_file = SCREENSHOT_DIR / "prod_lite_e2e_jack_scenario.png"
            assert shot_file.exists() and shot_file.stat().st_size > 0
        finally:
            await page.close()
            await context.close()
            await browser.close()


@pytest.mark.asyncio
async def test_prod_lite_e2e_failed_scenario():
    """Verify live Horo Lite fail-closed 503 error display and resilient retry recovery."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="th-TH",
        )
        page = await context.new_page()
        try:
            result = await run_failed_scenario(page, TARGET_URL)
            assert result["status"] == "PASSED"

            check_names = [c["check"] for c in result["checks"]]
            assert "fail_closed_error_message" in check_names
            assert "retry_button_accessible" in check_names
            assert "failed_screenshot" in check_names
            assert "retry_payload_retention_and_recovery" in check_names

            # Verify screenshot exists on disk
            shot_file = SCREENSHOT_DIR / "prod_lite_e2e_failed.png"
            assert shot_file.exists() and shot_file.stat().st_size > 0
        finally:
            await page.close()
            await context.close()
            await browser.close()


def test_prod_lite_e2e_report_integrity():
    """Verify execution report exists and confirms ALL_PASSED_READY_FOR_PROD status."""
    assert REPORT_PATH.exists(), f"Missing report file at {REPORT_PATH}"
    report_data = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report_data["ticket_id"] in ("TICKET-HLITE-014", "TICKET-FIX-003-E2E", "TICKET-THAI-005")
    assert report_data["status"] == "ALL_PASSED_READY_FOR_PROD"
    assert len(report_data["scenarios"]) == 3

    # Verify screenshots referenced and exist
    for rel_path in report_data["screenshots"]:
        full_path = ROOT / rel_path
        assert full_path.exists(), f"Referenced screenshot missing: {rel_path}"
        assert full_path.stat().st_size > 0, f"Screenshot file is empty: {rel_path}"
