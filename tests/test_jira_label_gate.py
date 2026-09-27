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
        # KAN-119: scripts/jira_label_gate.py is a library imported by the
        # real hook (.githooks/commit-msg, 100755) and must stay 100644 to
        # satisfy the HF release payload mode contract. The executable bit
        # belongs to the hook, not the gate module.
        hook_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            ".githooks",
            "commit-msg",
        )
        assert os.access(hook_path, os.X_OK)
        assert not os.access(GATE_PATH, os.X_OK)

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


class TestCmdCheckFailOpen:
    """Tests for the Jira API cmd_check subcommands — KAN-105.

    These verify the fail-open design: when Jira returns 404 (ticket-not-found),
    401/403 (auth), or credentials are missing, cmd_check returns 2 (fail-open)
    rather than 1 (fail-closed).  Only a confirmed ticket LACKING an agent-*
    label triggers fail-closed (exit 1).
    """

    @pytest.fixture
    def _gate(self):
        return load_gate_module()

    def test_404_returns_fail_open(self, _gate):
        """Jira 404 → exit 2 (cannot verify, not a violation)."""
        import unittest.mock as mock
        with mock.patch.object(_gate, "build_client", return_value=("https://x.atlassian.net", {"Authorization": "Bearer t"}, None)):
            with mock.patch.object(_gate, "fetch_issue", return_value=(404, {})):
                rc = _gate.cmd_check({}, "KAN-999")
        assert rc == 2, f"Expected fail-open (2), got {rc}"

    def test_401_returns_fail_open(self, _gate):
        """Jira 401 → exit 2 (auth error, cannot verify)."""
        import unittest.mock as mock
        with mock.patch.object(_gate, "build_client", return_value=("https://x.atlassian.net", {"Authorization": "Bearer t"}, None)):
            with mock.patch.object(_gate, "fetch_issue", return_value=(401, {})):
                rc = _gate.cmd_check({}, "KAN-105")
        assert rc == 2, f"Expected fail-open (2), got {rc}"

    def test_missing_credentials_returns_fail_open(self, _gate):
        """No Jira credentials → exit 2 (fail-open)."""
        rc = _gate.cmd_check({}, "KAN-105")
        assert rc == 2, f"Expected fail-open (2), got {rc}"

    def test_valid_label_returns_pass(self, _gate):
        """Ticket with agent-* label → exit 0 (pass)."""
        import unittest.mock as mock
        fake = {"fields": {"labels": ["agent-hermes"]}}
        with mock.patch.object(_gate, "build_client", return_value=("https://x.atlassian.net", {"Authorization": "Bearer t"}, None)):
            with mock.patch.object(_gate, "fetch_issue", return_value=(200, fake)):
                rc = _gate.cmd_check({}, "KAN-105")
        assert rc == 0, f"Expected pass (0), got {rc}"

    def test_missing_label_returns_fail_closed(self, _gate):
        """Ticket exists but lacks agent-* label → exit 1 (fail-closed)."""
        import unittest.mock as mock
        fake = {"fields": {"labels": ["bug"]}}
        with mock.patch.object(_gate, "build_client", return_value=("https://x.atlassian.net", {"Authorization": "Bearer t"}, None)):
            with mock.patch.object(_gate, "fetch_issue", return_value=(200, fake)):
                rc = _gate.cmd_check({}, "KAN-105")
        assert rc == 1, f"Expected fail-closed (1), got {rc}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
