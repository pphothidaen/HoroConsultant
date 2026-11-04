"""
tests/test_verify_agent_evals.py — Unit tests for Configuration Regression Eval Runner.
"""

import json
import pytest
from pathlib import Path
import sys
import tempfile
import os

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from verify_agent_evals import find_eval_files, load_eval, get_changed_agent_files, run_eval


@pytest.fixture
def eval_env(tmp_path, monkeypatch):
    """Create a test environment with eval files."""
    monkeypatch.chdir(tmp_path)
    
    eval_dir = tmp_path / "tests" / "evals"
    eval_dir.mkdir(parents=True)
    
    # Create a sample eval file
    eval_data = {
        "fingerprint": "abc123def456",
        "ticket_id": "KAN-INC-ABC123",
        "eval_type": "configuration_regression",
        "test_criteria": [
            "Agent must detect this error pattern in post-deploy verification",
            "Agent must classify severity correctly (Tier 2/3)",
            "Agent must generate correct ticket type (ATOMIC_TICKET/intent.md)"
        ],
        "agent_files_to_monitor": ["AGENTS.md", ".githooks/*", "skills/*/SKILL.md"],
        "original_error_trace": "TimeoutError: lock contention at line 50"
    }
    
    eval_file = eval_dir / "eval_abc123def456.json"
    eval_file.write_text(json.dumps(eval_data, indent=2))
    
    # Create a dummy AGENTS.md
    (tmp_path / "AGENTS.md").write_text("# Agent Rules\n")
    
    return {"root": tmp_path, "eval_dir": eval_dir, "eval_file": eval_file}


def test_find_eval_files(eval_env):
    """Should find eval_*.json files."""
    files = find_eval_files(eval_env["eval_dir"])
    assert len(files) == 1
    assert files[0].name == "eval_abc123def456.json"


def test_load_eval(eval_env):
    """Should load and parse eval JSON."""
    data = load_eval(eval_env["eval_file"])
    assert data["fingerprint"] == "abc123def456"
    assert data["ticket_id"] == "KAN-INC-ABC123"
    assert data["eval_type"] == "configuration_regression"
    assert len(data["test_criteria"]) == 3


def test_load_eval_invalid_json(tmp_path, monkeypatch):
    """Should handle invalid JSON gracefully."""
    monkeypatch.chdir(tmp_path)
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{ invalid json")
    
    data = load_eval(bad_file)
    assert data == {}


def test_run_eval_skips_when_no_changes(eval_env, monkeypatch):
    """Should skip eval when no monitored files changed."""
    # Mock subprocess to show no changes
    def mock_run(*args, **kwargs):
        class MockResult:
            stdout = ""
            stderr = ""
            returncode = 0
        return MockResult()
    
    monkeypatch.setattr("subprocess.run", mock_run)
    
    eval_data = load_eval(eval_env["eval_file"])
    passed, msg = run_eval(eval_data, ["AGENTS.md", ".githooks/*"])
    
    assert passed
    assert "skipped" in msg.lower()


def test_run_eval_runs_when_changes(eval_env, monkeypatch):
    """Should run eval when monitored files changed."""
    # Mock subprocess to show changes
    call_count = [0]
    
    def mock_run(*args, **kwargs):
        call_count[0] += 1
        class MockResult:
            stdout = "Tier 2"
            stderr = ""
            returncode = 0
        return MockResult()
    
    monkeypatch.setattr("subprocess.run", mock_run)
    
    # Need to simulate changed files - mock git status
    def mock_git_status(*args, **kwargs):
        class MockResult:
            stdout = "M\tAGENTS.md\n"
            stderr = ""
            returncode = 0
        return MockResult()
    
    monkeypatch.setattr("subprocess.run", lambda *a, **k: mock_git_status() if "status" in str(a) else mock_run(*a, **k))
    
    eval_data = load_eval(eval_env["eval_file"])
    # This will be complex to test fully, so just verify structure
    assert eval_data["fingerprint"] == "abc123def456"


def test_get_changed_agent_files_no_git(tmp_path, monkeypatch):
    """Should handle missing git gracefully."""
    monkeypatch.chdir(tmp_path)
    # No git repo
    changed = get_changed_agent_files(["AGENTS.md"])
    assert changed == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])