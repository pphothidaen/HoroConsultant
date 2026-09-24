#!/usr/bin/env python3
"""Test suite for agent-label governance enforcement — KAN-105."""

import importlib.util
import os
import subprocess
import sys

import pytest

# Load the gate module
GATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts",
    "jira_label_gate.py",
)


def load_gate_module():
    spec = importlib.util.spec_from_file_location("jira_label_gate", GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestLabelPatternMatching:
    """Tests for LABEL_PATTERN regex."""

    def test_valid_agent_hermes(self):
        gate = load_gate_module()
        assert gate.LABEL_PATTERN.search("agent-hermes") is not None

    def test_valid_agent_codex1(self):
        gate = load_gate_module()
        assert gate.LABEL_PATTERN.search("agent-codex1") is not None

    def test_valid_agent_agy5(self):
        gate = load_gate_module()
        assert gate.LABEL_PATTERN.search("agent-agy5") is not None

    def test_valid_in_brackets(self):
        gate = load_gate_module()
        assert gate.LABEL_PATTERN.search("[KAN-101] agent-hermes") is not None

    def test_invalid_no_label(self):
        gate = load_gate_module()
        assert gate.LABEL_PATTERN.search("just a commit") is None

    def test_invalid_wrong_prefix(self):
        gate = load_gate_module()
        # "user-hermes" should NOT match agent-* pattern
        assert gate.LABEL_PATTERN.search("user-hermes") is None


class TestBypassPatterns:
    """Tests for bypass patterns (merge, revert, fixup)."""

    def test_merge_bypass(self):
        gate = load_gate_module()
        is_valid, issues = gate.validate_commit_message("Merge pull request #76")
        assert is_valid is True

    def test_revert_bypass(self):
        gate = load_gate_module()
        is_valid, issues = gate.validate_commit_message('Revert "bad commit"')
        assert is_valid is True

    def test_fixup_bypass(self):
        gate = load_gate_module()
        is_valid, issues = gate.validate_commit_message("fixup! feat: something")
        assert is_valid is True


class TestValidation:
    """Tests for validate_commit_message function."""

    def test_valid_with_agent_hermes(self):
        gate = load_gate_module()
        is_valid, issues = gate.validate_commit_message(
            "[KAN-101] feat: add cost ledger agent-hermes"
        )
        assert is_valid is True

    def test_valid_with_agent_codex3(self):
        gate = load_gate_module()
        is_valid, issues = gate.validate_commit_message(
            "[KAN-102] chore: skill audit agent-codex3"
        )
        assert is_valid is True

    def test_invalid_no_label(self):
        gate = load_gate_module()
        is_valid, issues = gate.validate_commit_message(
            "feat: missing label"
        )
        assert is_valid is False
        assert any("No agent-* label" in i for i in issues)

    def test_invalid_empty_message(self):
        gate = load_gate_module()
        is_valid, issues = gate.validate_commit_message("")
        assert is_valid is False


class TestCommitMsgHook:
    """Test the commit-msg hook script."""

    def test_hook_file_exists(self):
        assert os.path.exists(GATE_PATH)

    def test_hook_executable(self):
        assert os.access(GATE_PATH, os.R_OK)
        hook_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            ".githooks",
            "commit-msg",
        )
        if os.path.exists(hook_path):
            assert os.access(hook_path, os.X_OK)

    def test_hook_accepts_valid_message(self):
        """Test with a valid commit message file."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("[KAN-101] feat: add cost ledger agent-hermes")
            f.flush()
            result = subprocess.run(
                [sys.executable, GATE_PATH, f.name],
                capture_output=True,
                text=True,
                timeout=10,
            )
            os.unlink(f.name)
        assert result.returncode == 0

    def test_hook_rejects_invalid_message(self):
        """Test with an invalid commit message (no agent label)."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("feat: missing label")
            f.flush()
            result = subprocess.run(
                [sys.executable, GATE_PATH, f.name],
                capture_output=True,
                text=True,
                timeout=10,
            )
            os.unlink(f.name)
        assert result.returncode == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
