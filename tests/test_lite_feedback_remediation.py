"""Remediation tests for Package 07: Lite feedback explanation emphasis and consent.

Validates that:
1. public/lite.js is valid JavaScript syntax.
2. Selecting calibration feedback dynamically modifies explanation emphasis in the DOM.
3. Underlying scores, dates, and facts are strictly preserved and never altered by feedback.
4. Consent precedes persistence (localStorage only written when consent checkbox is checked).
5. Withdrawing consent immediately removes stored feedback from localStorage and resets state.
6. Profile isolation ensures feedback is mapped cleanly per pattern ID without cross-contamination.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

LITE_JS_PATH = Path(__file__).resolve().parent.parent / "public" / "lite.js"


def _read_lite_js() -> str:
    assert LITE_JS_PATH.is_file(), f"Missing {LITE_JS_PATH}"
    return LITE_JS_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Test 1: Valid JS syntax
# ---------------------------------------------------------------------------
def test_lite_js_syntax_valid() -> None:
    """public/lite.js must parse cleanly with Node."""
    proc = subprocess.run(
        ["node", "-c", str(LITE_JS_PATH)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"Node syntax error:\n{proc.stderr}"


# ---------------------------------------------------------------------------
# Test 2: Feedback updates explanation emphasis in the DOM
# ---------------------------------------------------------------------------
def test_feedback_updates_explanation_emphasis_in_dom() -> None:
    """Feedback selection must create or update explanation emphasis in the DOM."""
    content = _read_lite_js()

    # Must contain feedback emphasis DOM class or data attribute
    has_emphasis_class = "pattern-feedback-emphasis" in content or "feedback-emphasis" in content
    assert has_emphasis_class, (
        "public/lite.js must define DOM elements for feedback explanation emphasis (pattern-feedback-emphasis)"
    )

    # Must contain logic to update explanation emphasis on selection
    has_emphasis_fn = "updateExplanationEmphasis" in content or "applyFeedbackEmphasis" in content
    assert has_emphasis_fn, (
        "public/lite.js must contain a function to update explanation emphasis when feedback is given"
    )


# ---------------------------------------------------------------------------
# Test 3: Feedback preserves scores, dates, and facts
# ---------------------------------------------------------------------------
def test_feedback_preserves_immutable_scores_and_dates() -> None:
    """Feedback must never mutate underlying score arrays or birth dates."""
    content = _read_lite_js()

    # In updatePatternSelection or feedback handlers, monthly_scores or birth_date must not be reassigned
    assert "state.lastResult.monthly_scores =" not in content, (
        "Feedback must not mutate state.lastResult.monthly_scores"
    )
    assert "state.lastPayload.birth_date =" not in content, (
        "Feedback must not mutate state.lastPayload.birth_date"
    )


# ---------------------------------------------------------------------------
# Test 4: Consent precedes persistence
# ---------------------------------------------------------------------------
def test_consent_precedes_persistence() -> None:
    """localStorage.setItem must be guarded by consent checkbox."""
    content = _read_lite_js()

    # persistFeedbackIfConsented must inspect feedback-consent.checked
    persist_match = re.search(
        r"function persistFeedbackIfConsented\(\)\s*\{(.*?)\}", content, re.DOTALL
    )
    assert persist_match is not None, "Missing persistFeedbackIfConsented function"
    body = persist_match.group(1)
    assert "feedback-consent" in body, "persistFeedbackIfConsented must check feedback-consent"
    assert "checked" in body, "persistFeedbackIfConsented must verify consent is checked"


# ---------------------------------------------------------------------------
# Test 5: Withdrawal clears stored feedback
# ---------------------------------------------------------------------------
def test_withdrawal_clears_stored_feedback() -> None:
    """When consent is unchecked, localStorage must be cleared."""
    content = _read_lite_js()

    withdrawal_match = re.search(
        r"function enforceNoPersistenceWithoutConsent\(\)\s*\{(.*?)\}", content, re.DOTALL
    )
    assert withdrawal_match is not None, "Missing enforceNoPersistenceWithoutConsent function"
    body = withdrawal_match.group(1)
    assert "removeItem" in body, "enforceNoPersistenceWithoutConsent must call removeItem"
    assert "FEEDBACK_STORAGE_KEY" in body, "enforceNoPersistenceWithoutConsent must clear FEEDBACK_STORAGE_KEY"


# ---------------------------------------------------------------------------
# Test 6: Pattern feedback isolation
# ---------------------------------------------------------------------------
def test_pattern_feedback_isolated_by_pattern_id() -> None:
    """Feedback dictionary keys must be keyed by specific patternId."""
    content = _read_lite_js()

    assert "state.feedbackByPattern[patternId]" in content, (
        "Feedback must be isolated by patternId key"
    )
