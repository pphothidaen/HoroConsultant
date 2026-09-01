"""Regression guard against partial alias-registry edits."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "validate_alias_contract.py"


def test_alias_contract_guard_enforces_the_four_agy_aliases() -> None:
    result = subprocess.run(
        [sys.executable, str(GUARD)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[OK] alias contract: agy1,agy2,agy3,agy4" in result.stdout
