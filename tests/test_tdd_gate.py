"""Unit tests for TDD State Transition Gate Enforcer — scripts/tdd_gate.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from tdd_gate import (
    ALLOWED_TRANSITIONS,
    check_green_state,
    check_red_state,
    verify_transition,
)


def test_allowed_transitions_structure():
    """Verify standard transition graph completeness."""
    assert "TDD RED" in ALLOWED_TRANSITIONS["Backlog"]
    assert "TDD GREEN" in ALLOWED_TRANSITIONS["TDD RED"]
    assert "Review" in ALLOWED_TRANSITIONS["TDD GREEN"]
    assert "Done" in ALLOWED_TRANSITIONS["Review"]
    assert ALLOWED_TRANSITIONS["Done"] == []


def test_verify_transition_invalid_jump():
    """Verify illegal transitions are rejected."""
    ok, msg = verify_transition("Backlog", "Done", "KAN-105")
    assert not ok
    assert "Invalid transition" in msg

    ok, msg = verify_transition("TDD RED", "Review", "KAN-105")
    assert not ok
    assert "Invalid transition" in msg


def test_verify_transition_unknown_status():
    """Verify unhandled or misspelled statuses fail gracefully."""
    ok, msg = verify_transition("UnknownState", "TDD RED", "KAN-105")
    assert not ok
    assert "Unknown source status" in msg


@patch("subprocess.run")
def test_check_red_state_blocked_when_tests_pass(mock_run):
    """TDD RED must fail if all tests already pass."""
    mock_run.return_value = MagicMock(returncode=0, stdout="All passed")
    ok, msg = check_red_state("tests/dummy.py")
    assert not ok
    assert "requires at least one failing test" in msg


@patch("subprocess.run")
def test_check_red_state_approved_when_tests_fail(mock_run):
    """TDD RED approved when tests produce non-zero exit code."""
    mock_run.return_value = MagicMock(returncode=1, stdout="1 failed")
    ok, msg = check_red_state("tests/dummy.py")
    assert ok
    assert "Failing test verified" in msg


@patch("subprocess.run")
def test_check_green_state_blocked_when_tests_fail(mock_run):
    """TDD GREEN must fail if any test is failing."""
    mock_run.return_value = MagicMock(returncode=1, stdout="1 failed")
    ok, msg = check_green_state("KAN-105", "tests/dummy.py")
    assert not ok
    assert "requires all tests to pass" in msg


@patch("subprocess.run")
@patch("glob.glob")
def test_check_green_state_blocked_missing_manifest(mock_glob, mock_run):
    """TDD GREEN requires provenance manifest to exist."""
    mock_run.return_value = MagicMock(returncode=0, stdout="All passed")
    mock_glob.return_value = []
    ok, msg = check_green_state("KAN-105", "tests/dummy.py")
    assert not ok
    assert "Missing test provenance manifest" in msg


@patch("subprocess.run")
@patch("glob.glob")
def test_check_green_state_approved(mock_glob, mock_run):
    """TDD GREEN approved when tests pass and provenance manifest is present."""
    mock_run.return_value = MagicMock(returncode=0, stdout="All passed")
    mock_glob.return_value = ["plans/test_provenance/ticket-kan-105-label-governance-001.json"]
    ok, msg = check_green_state("KAN-105", "tests/dummy.py")
    assert ok
    assert "All tests passed and provenance manifest verified" in msg
