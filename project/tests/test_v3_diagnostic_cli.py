"""Tests for the Horo v3.0 diagnostic CLI."""

import json
import subprocess
import sys
from pathlib import Path

from scripts.v3_diagnostic_cli import build_parser


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts" / "v3_diagnostic_cli.py"


def _meaningful_stderr(stderr: str) -> str:
    """Ignore Doppler's credential fallback warnings on credential-less CI runners."""
    return "\n".join(
        line for line in stderr.splitlines() if "[WARNING] Secret" not in line
    ).strip()


def test_cli_argument_parsing_defaults_and_overrides():
    args = build_parser().parse_args(["--birth-date", "1990-05-15", "--birth-time", "14:30"])
    assert args.lat == 13.7563
    assert args.lon == 100.493
    assert args.intent == "STRATEGIC_TIMING_ACTION"
    assert args.as_json is False

    custom = build_parser().parse_args([
        "--birth-date", "1990-05-15", "--birth-time", "14:30",
        "--lat", "1.5", "--lon", "2.5", "--intent", "NATAL_CHARACTER_PATH", "--json",
    ])
    assert (custom.lat, custom.lon, custom.intent, custom.as_json) == (1.5, 2.5, "NATAL_CHARACTER_PATH", True)


def test_cli_execution_prints_diagnostic_sections():
    completed = subprocess.run(
        [sys.executable, str(CLI), "--birth-date", "1990-05-15", "--birth-time", "14:30"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    assert "HORO v3.0 INTERACTIVE DIAGNOSTIC CLI" in completed.stdout
    assert "10-DOMAIN CALCULATION SUMMARY" in completed.stdout
    assert "AUDIT METRICS" in completed.stdout
    assert "TRI-GRAPH DERIVATION SUMMARY" in completed.stdout
    assert _meaningful_stderr(completed.stderr) == ""


def test_cli_json_is_pure_structured_output():
    completed = subprocess.run(
        [sys.executable, str(CLI), "--birth-date", "1990-05-15", "--birth-time", "14:30", "--json"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    payload = json.loads(completed.stdout)
    assert len(payload["domains"]) == 10
    assert payload["audit"]["verdict"].startswith("AUDIT_")
    assert payload["composer"]["has_epistemic_disclaimer"] is True
    assert _meaningful_stderr(completed.stderr) == ""
