"""Regression contract for the parity script's HF Docker payload Git mode."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = "scripts/sync_claude_agy_parity.py"


def test_committed_parity_script_is_a_regular_100644_payload_source() -> None:
    record = subprocess.check_output(
        ["git", "ls-tree", "HEAD", "--", SOURCE_PATH],
        cwd=ROOT,
        text=True,
    ).strip()

    assert record.startswith("100644 blob "), (
        f"committed {SOURCE_PATH} must be a regular 100644 blob; got {record!r}"
    )
