"""Red Team Inversion QA Audit test suite for Program GOV-ROADMAP-20260904 (TICKET-GOV-028).

Verifies:
- Scoped AGENTS.md line budget (<= 50 lines), pure ASCII, and root safeguard precedence.
- Rule 24 size budget (<= 80 lines) and parity across .agents, .claude, and .agy rules.
- Claude rule size budget (<= 40 lines).
- Inversion thinking adversary mindset and TIA 4-tier testing definitions.
- Rayon parallel secret scanner clean state (0 leaks).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCOPED_AGENTS_FILES = [
    ROOT / "project" / "core" / "AGENTS.md",
    ROOT / "project" / "routers" / "AGENTS.md",
    ROOT / "project" / "static" / "AGENTS.md",
    ROOT / "rust_core" / "AGENTS.md",
    ROOT / "scripts" / "AGENTS.md",
]

RULE_24_AGENTS = ROOT / ".agents" / "rules" / "24-red-blue-team-and-selective-testing.md"
RULE_24_CLAUDE = ROOT / ".claude" / "rules" / "selective-testing-and-red-blue.md"
RULE_24_AGY = ROOT / ".agy" / "rules" / "selective-testing-and-red-blue.md"


def test_scoped_agents_files_exist_and_bounded() -> None:
    """Audit the 5 scoped AGENTS.md files for presence, line count <= 50, and ASCII."""
    for path in SCOPED_AGENTS_FILES:
        assert path.is_file(), f"Missing scoped AGENTS.md file: {path.relative_to(ROOT)}"
        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()
        line_count = len(lines)
        assert line_count <= 50, (
            f"{path.relative_to(ROOT)} exceeds 50 lines budget: {line_count} lines"
        )
        assert content.isascii(), (
            f"{path.relative_to(ROOT)} contains non-ASCII characters"
        )
        # Verify root safeguards precedence clause
        assert "Root Universal Safeguards Precedence" in content, (
            f"{path.relative_to(ROOT)} missing Root Universal Safeguards Precedence clause"
        )


def test_rule_24_agents_line_budget_and_adversarial_contract() -> None:
    """Audit Rule 24 in .agents/rules/ for <= 80 lines and key adversarial concepts."""
    assert RULE_24_AGENTS.is_file(), "Rule 24 missing in .agents/rules/"
    content = RULE_24_AGENTS.read_text(encoding="utf-8")
    lines = content.splitlines()
    assert len(lines) <= 80, f"Rule 24 exceeds 80 lines: {len(lines)}"

    # Inversion Thinking & Adversarial contract
    assert "Inversion Thinking" in content
    assert "Assume code is broken until proven otherwise" in content
    assert "qa_tester" in content
    assert "Red Team" in content
    assert "Blue Team" in content
    assert "Test Impact Analysis (TIA)" in content


def test_rule_24_claude_and_agy_mirrors_bounded() -> None:
    """Audit Claude and AGY mirrors for <= 40 lines and parity."""
    for mirror_path, label in [(RULE_24_CLAUDE, "Claude"), (RULE_24_AGY, "AGY")]:
        assert mirror_path.is_file(), f"Rule 24 mirror missing for {label}: {mirror_path}"
        content = mirror_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        assert len(lines) <= 40, f"{label} mirror exceeds 40 lines: {len(lines)}"
        assert "Inversion Thinking" in content
        assert "Test Impact Analysis (TIA)" in content


def test_four_tier_testing_paths_codified() -> None:
    """Audit that Rule 24 codifies all 4 testing paths."""
    content = RULE_24_AGENTS.read_text(encoding="utf-8")
    for tier in ["Atomic Path", "System Path", "Smoke Path", "Happy Path"]:
        assert tier in content, f"Missing tier: {tier} in Rule 24"


def test_zero_secret_leaks_audit() -> None:
    """Audit codebase with secret scanner to ensure 0 leaks."""
    cmd = [sys.executable, str(ROOT / "project" / "core" / "code_reviewer.py"), "--scan-secrets"]
    res = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=True)
    assert res.returncode == 0, f"Secret scanner returned non-zero: {res.stderr}"
    # Parse JSON output from stdout
    output = res.stdout
    start = output.find("{")
    assert start != -1, "No JSON found in secret scanner output"
    data = json.loads(output[start:])
    assert data.get("status") == "PASSED", f"Secret scan status: {data.get('status')}"
    assert data.get("secret_leaks_found") == 0, (
        f"Secret leaks found: {data.get('secret_leaks_found')}"
    )
