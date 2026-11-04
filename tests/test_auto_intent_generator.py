"""
tests/test_auto_intent_generator.py — Unit tests for Closed-Loop Incident Synthesizer.
"""

import json
import sqlite3
import pytest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from auto_intent_generator import AutoIntentGenerator


@pytest.fixture
def incident_env(tmp_path):
    report_file = tmp_path / "failure_report.json"
    db_file = tmp_path / "ai_sdlc_metrics.db"
    ledger_file = tmp_path / "escapes_ledger.jsonl"
    return {"root": tmp_path, "report": report_file, "db": db_file, "ledger": ledger_file}


def test_fingerprint_normalization_removes_addresses(incident_env):
    payload1 = {"error_trace": "AssertionError at 0x7fff5fbff8c0 line 42 in worker.py"}
    payload2 = {"error_trace": "AssertionError at 0x7fff5fbff9a0 line 99 in worker.py"}

    incident_env["report"].write_text(json.dumps(payload1))
    gen1 = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])

    incident_env["report"].write_text(json.dumps(payload2))
    gen2 = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])

    assert gen1.compute_fingerprint() == gen2.compute_fingerprint()


def test_fingerprint_normalization_removes_timestamps(incident_env):
    payload1 = {"error_trace": "2024-01-15T10:30:45 ERROR Connection failed"}
    payload2 = {"error_trace": "2024-02-20T15:45:00 ERROR Connection failed"}

    incident_env["report"].write_text(json.dumps(payload1))
    gen1 = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])

    incident_env["report"].write_text(json.dumps(payload2))
    gen2 = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])

    assert gen1.compute_fingerprint() == gen2.compute_fingerprint()


def test_severity_triage_detects_security_keywords(incident_env):
    report = {
        "summary": "Team Red breached auth check",
        "category": "security_simulation",
        "error_trace": "Unauthorized access token_leak at endpoint /v1/admin"
    }
    incident_env["report"].write_text(json.dumps(report))
    gen = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])

    assert gen.triage_severity() == "Tier 3"


def test_severity_triage_tier2_for_functional(incident_env):
    report = {
        "summary": "Order price calculation off by discount round",
        "category": "calculation",
        "error_trace": "Expected 100.0 got 99.5"
    }
    incident_env["report"].write_text(json.dumps(report))
    gen = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])

    assert gen.triage_severity() == "Tier 2"


def test_synthesize_tier2_creates_atomic_ticket(incident_env, monkeypatch):
    monkeypatch.chdir(incident_env["root"])
    report = {
        "summary": "Order price calculation off by discount round",
        "category": "calculation",
        "error_trace": "Expected 100.0 got 99.5"
    }
    incident_env["report"].write_text(json.dumps(report))
    gen = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])

    target = gen.synthesize()
    assert target == "ATOMIC_TICKET.md"
    assert (incident_env["root"] / "ATOMIC_TICKET.md").exists()

    content = (incident_env["root"] / "ATOMIC_TICKET.md").read_text()
    assert "**Risk Tier:** Tier 2" in content
    assert "ATOMIC TICKET:" in content


def test_synthesize_tier3_creates_intent_doc(incident_env, monkeypatch):
    monkeypatch.chdir(incident_env["root"])
    report = {
        "summary": "Team Red breached auth check",
        "category": "security_simulation",
        "error_trace": "Unauthorized access token_leak at endpoint /v1/admin"
    }
    incident_env["report"].write_text(json.dumps(report))
    gen = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])

    target = gen.synthesize()
    assert target is not None
    assert "docs/specs/intent-" in target

    intent_path = incident_env["root"] / target
    assert intent_path.exists()

    content = intent_path.read_text()
    assert "**Risk Tier:** Tier 3" in content
    assert "Incident Intent:" in content


def test_deduplication_prevents_duplicate_file_creation(incident_env, monkeypatch):
    monkeypatch.chdir(incident_env["root"])
    report = {
        "summary": "Database lock timeout",
        "category": "database",
        "error_trace": "TimeoutError: lock contention at line 50"
    }
    incident_env["report"].write_text(json.dumps(report))

    gen = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])
    first_res = gen.synthesize()
    assert first_res is not None

    # Second pass with same error should suppress creation
    second_res = gen.synthesize()
    assert second_res is None

    # Verify count incremented in DB
    with sqlite3.connect(incident_env["db"]) as conn:
        row = conn.execute("SELECT occurrence_count FROM post_deploy_escapes").fetchone()
        assert row[0] == 2


def test_dry_run_mode_no_files_written(incident_env, monkeypatch):
    monkeypatch.chdir(incident_env["root"])
    report = {
        "summary": "Test dry run",
        "category": "test",
        "error_trace": "Test error"
    }
    incident_env["report"].write_text(json.dumps(report))
    gen = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"], dry_run=True)

    target = gen.synthesize()
    assert target is not None
    # No file should be created in dry-run mode
    assert not (incident_env["root"] / "ATOMIC_TICKET.md").exists()


def test_missing_report_file_handled_gracefully(incident_env, monkeypatch):
    monkeypatch.chdir(incident_env["root"])
    missing_report = incident_env["root"] / "missing.json"
    gen = AutoIntentGenerator(missing_report, incident_env["db"], incident_env["ledger"])

    # Should not crash, just have raw_log with error message
    assert "Report file not found" in gen.data.get("raw_log", "")
    # fingerprint should be computable (uses raw_log)
    fp = gen.compute_fingerprint()
    assert len(fp) == 12


def test_duplicate_different_tier_still_deduped(incident_env, monkeypatch):
    """Even if same error appears with different tier hints, fingerprint matches."""
    monkeypatch.chdir(incident_env["root"])
    report1 = {
        "summary": "Database lock timeout",
        "category": "database",
        "error_trace": "TimeoutError: lock contention at line 50"
    }
    report2 = {
        "summary": "Database lock timeout - SECURITY",
        "category": "security",
        "error_trace": "TimeoutError: lock contention at line 50"
    }
    incident_env["report"].write_text(json.dumps(report1))
    gen1 = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])
    first = gen1.synthesize()
    assert first is not None

    incident_env["report"].write_text(json.dumps(report2))
    gen2 = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])
    second = gen2.synthesize()
    # Should be deduped even though category differs
    assert second is None


# ============ NEW TESTS FOR DAY-2 OPERATIONAL GAPS ============

def test_jsonl_ledger_persists_across_instances(incident_env, monkeypatch):
    """JSONL ledger should persist deduplication across separate generator instances."""
    monkeypatch.chdir(incident_env["root"])
    report = {
        "summary": "Test ledger persistence",
        "category": "test",
        "error_trace": "Test error for ledger"
    }
    incident_env["report"].write_text(json.dumps(report))
    
    # First instance creates incident
    gen1 = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])
    first = gen1.synthesize()
    assert first is not None
    
    # Second instance (simulating new CI run) should see ledger and dedupe
    gen2 = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])
    second = gen2.synthesize()
    assert second is None
    
    # Verify ledger has the entry
    ledger_content = incident_env["ledger"].read_text()
    assert "KAN-INC-" in ledger_content
    assert "OPEN" in ledger_content


def test_resolve_incident_updates_both_sqlite_and_ledger(incident_env, monkeypatch):
    """--resolve should update both SQLite and JSONL ledger."""
    monkeypatch.chdir(incident_env["root"])
    report = {
        "summary": "Test resolve",
        "category": "test",
        "error_trace": "Test error for resolve"
    }
    incident_env["report"].write_text(json.dumps(report))
    
    # Create incident
    gen = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])
    gen.synthesize()
    
    # Get fingerprint
    fingerprint = gen.compute_fingerprint()
    
    # Resolve via new instance
    resolver = AutoIntentGenerator(
        db_path=incident_env["db"],
        ledger_path=incident_env["ledger"],
        action="resolve",
        fingerprint=fingerprint,
        reason="Fixed in PR #123"
    )
    success = resolver.resolve_incident(fingerprint, "Fixed in PR #123")
    assert success
    
    # Verify SQLite updated
    with sqlite3.connect(incident_env["db"]) as conn:
        row = conn.execute("SELECT status, resolution_reason FROM post_deploy_escapes WHERE error_fingerprint = ?", (fingerprint,)).fetchone()
        assert row[0] == "RESOLVED"
        assert row[1] == "Fixed in PR #123"
    
    # Verify ledger updated
    ledger_content = incident_env["ledger"].read_text()
    assert "RESOLVED" in ledger_content
    assert "Fixed in PR #123" in ledger_content


def test_dismiss_incident_updates_both_sqlite_and_ledger(incident_env, monkeypatch):
    """--dismiss should update both SQLite and JSONL ledger with reason."""
    monkeypatch.chdir(incident_env["root"])
    report = {
        "summary": "Test dismiss",
        "category": "test",
        "error_trace": "Test error for dismiss"
    }
    incident_env["report"].write_text(json.dumps(report))
    
    # Create incident
    gen = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])
    gen.synthesize()
    
    # Get fingerprint
    fingerprint = gen.compute_fingerprint()
    
    # Dismiss via new instance
    dismisser = AutoIntentGenerator(
        db_path=incident_env["db"],
        ledger_path=incident_env["ledger"],
        action="dismiss",
        fingerprint=fingerprint,
        reason="False alarm - flaky test"
    )
    success = dismisser.dismiss_incident(fingerprint, "False alarm - flaky test")
    assert success
    
    # Verify SQLite updated
    with sqlite3.connect(incident_env["db"]) as conn:
        row = conn.execute("SELECT status, resolution_reason FROM post_deploy_escapes WHERE error_fingerprint = ?", (fingerprint,)).fetchone()
        assert row[0] == "DISMISSED"
        assert row[1] == "False alarm - flaky test"
    
    # Verify ledger updated
    ledger_content = incident_env["ledger"].read_text()
    assert "DISMISSED" in ledger_content
    assert "False alarm - flaky test" in ledger_content


def test_dismissed_incident_suppresses_new_occurrence(incident_env, monkeypatch):
    """After dismiss, same error should be SUPPRESSED (noise reduction per AI-Native SDLC).
    
    DISMISSED = false alarm/flaky test → suppress future occurrences to reduce noise.
    """
    monkeypatch.chdir(incident_env["root"])
    report = {
        "summary": "Test dismissed suppression",
        "category": "test",
        "error_trace": "Test error for dismissed suppression"
    }
    incident_env["report"].write_text(json.dumps(report))
    
    # Create and dismiss
    gen = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])
    gen.synthesize()
    fingerprint = gen.compute_fingerprint()
    
    dismisser = AutoIntentGenerator(
        db_path=incident_env["db"],
        ledger_path=incident_env["ledger"],
        action="dismiss",
        fingerprint=fingerprint,
        reason="False alarm"
    )
    dismisser.dismiss_incident(fingerprint, "False alarm")
    
    # New occurrence should be SUPPRESSED (not create new ticket)
    gen2 = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])
    result = gen2.synthesize()
    assert result is None  # Suppressed
    
    # Should have two entries in ledger: OPEN then DISMISSED
    ledger_content = incident_env["ledger"].read_text()
    assert "DISMISSED" in ledger_content
    open_count = ledger_content.count('"status": "OPEN"')
    assert open_count == 1  # Original OPEN entry (DISMISSED overwrites it in place)


def test_resolved_incident_allows_regression_reopen(incident_env, monkeypatch):
    """After resolve, same error should create NEW ticket marked as REGRESSION.
    
    RESOLVED = fixed & deployed → allow re-occurrence as REGRESSION (bug returned).
    This is a lagging indicator for Repeat Incidents.
    """
    monkeypatch.chdir(incident_env["root"])
    report = {
        "summary": "Test resolved regression",
        "category": "test",
        "error_trace": "Test error for resolved regression"
    }
    incident_env["report"].write_text(json.dumps(report))
    
    # Create and resolve
    gen = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])
    gen.synthesize()
    fingerprint = gen.compute_fingerprint()
    original_ticket = f"KAN-INC-{fingerprint[:6].upper()}"
    
    resolver = AutoIntentGenerator(
        db_path=incident_env["db"],
        ledger_path=incident_env["ledger"],
        action="resolve",
        fingerprint=fingerprint,
        reason="Fixed in PR #123"
    )
    resolver.resolve_incident(fingerprint, "Fixed in PR #123")
    
    # New occurrence should create new ticket (REGRESSION)
    gen2 = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])
    result = gen2.synthesize()
    assert result is not None  # New ticket created
    
    # Should be marked as REGRESSION
    content = (incident_env["root"] / result).read_text()
    assert "REGRESSION" in content
    assert original_ticket in content
    
    # Should have OPEN entry in ledger (new occurrence)
    ledger_content = incident_env["ledger"].read_text()
    open_count = ledger_content.count('"status": "OPEN"')
    assert open_count == 2  # Original + new REGRESSION


def test_resolve_creates_eval_stub(incident_env, monkeypatch):
    """--resolve should create Configuration Regression Eval stub at tests/evals/eval_<fingerprint>.json."""
    monkeypatch.chdir(incident_env["root"])
    report = {
        "summary": "Test eval stub creation",
        "category": "test",
        "error_trace": "Test error for eval stub"
    }
    incident_env["report"].write_text(json.dumps(report))
    
    gen = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])
    gen.synthesize()
    fingerprint = gen.compute_fingerprint()
    
    resolver = AutoIntentGenerator(
        db_path=incident_env["db"],
        ledger_path=incident_env["ledger"],
        action="resolve",
        fingerprint=fingerprint,
        reason="Fixed in PR #456"
    )
    resolver.resolve_incident(fingerprint, "Fixed in PR #456")
    
    # Verify eval stub created
    eval_path = incident_env["root"] / "tests" / "evals" / f"eval_{fingerprint}.json"
    assert eval_path.exists()
    
    eval_data = json.loads(eval_path.read_text())
    assert eval_data["fingerprint"] == fingerprint
    assert eval_data["resolution_reason"] == "Fixed in PR #456"
    assert eval_data["eval_type"] == "configuration_regression"
    assert "AGENTS.md" in eval_data["agent_files_to_monitor"]
    assert "skills/*/SKILL.md" in eval_data["agent_files_to_monitor"]
    assert ".githooks/*" in eval_data["agent_files_to_monitor"]


def test_resolve_creates_eval_stub_even_dry_run(incident_env, monkeypatch):
    """--resolve in dry-run mode should still show eval stub preview (no file write)."""
    monkeypatch.chdir(incident_env["root"])
    report = {
        "summary": "Test eval stub dry-run",
        "category": "test",
        "error_trace": "Test error for eval stub dry-run"
    }
    incident_env["report"].write_text(json.dumps(report))
    
    gen = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])
    gen.synthesize()
    fingerprint = gen.compute_fingerprint()
    
    # Dry-run resolve
    resolver = AutoIntentGenerator(
        db_path=incident_env["db"],
        ledger_path=incident_env["ledger"],
        action="resolve",
        fingerprint=fingerprint,
        reason="Dry-run fix",
        dry_run=True
    )
    resolver.resolve_incident(fingerprint, "Dry-run fix")
    
    # Eval stub should NOT be created in dry-run
    eval_path = incident_env["root"] / "tests" / "evals" / f"eval_{fingerprint}.json"
    assert not eval_path.exists()


def test_check_duplicate_returns_correct_reason(incident_env, monkeypatch):
    """check_duplicate should return correct suppression reason for each status."""
    monkeypatch.chdir(incident_env["root"])
    report = {
        "summary": "Test check_duplicate reasons",
        "category": "test",
        "error_trace": "Test error for check_duplicate"
    }
    incident_env["report"].write_text(json.dumps(report))
    
    gen = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])
    gen.synthesize()
    fingerprint = gen.compute_fingerprint()
    
    # OPEN → duplicate, reason="open"
    is_dup, ticket, reason = gen.check_duplicate(fingerprint)
    assert is_dup
    assert reason == "open"
    
    # Dismiss
    dismisser = AutoIntentGenerator(
        db_path=incident_env["db"],
        ledger_path=incident_env["ledger"],
        action="dismiss",
        fingerprint=fingerprint,
        reason="Flaky test"
    )
    dismisser.dismiss_incident(fingerprint, "Flaky test")
    
    # DISMISSED → duplicate, reason="dismissed"
    gen2 = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])
    is_dup, ticket, reason = gen2.check_duplicate(fingerprint)
    assert is_dup
    assert reason == "dismissed"
    
    # Resolve
    resolver = AutoIntentGenerator(
        db_path=incident_env["db"],
        ledger_path=incident_env["ledger"],
        action="resolve",
        fingerprint=fingerprint,
        reason="Fixed"
    )
    resolver.resolve_incident(fingerprint, "Fixed")
    
    # RESOLVED → NOT duplicate, reason="resolved"
    gen3 = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])
    is_dup, ticket, reason = gen3.check_duplicate(fingerprint)
    assert not is_dup
    assert reason == "resolved"


def test_resolve_requires_fingerprint_and_reason(incident_env):
    """--resolve should fail without fingerprint or reason."""
    gen = AutoIntentGenerator(
        db_path=incident_env["db"],
        ledger_path=incident_env["ledger"],
        action="resolve",
        fingerprint=None,
        reason="test"
    )
    assert not gen.resolve_incident("", "test")
    
    gen2 = AutoIntentGenerator(
        db_path=incident_env["db"],
        ledger_path=incident_env["ledger"],
        action="resolve",
        fingerprint="abc123",
        reason=None
    )
    assert not gen2.resolve_incident("abc123", None)


def test_dismiss_requires_fingerprint_and_reason(incident_env):
    """--dismiss should fail without fingerprint or reason."""
    gen = AutoIntentGenerator(
        db_path=incident_env["db"],
        ledger_path=incident_env["ledger"],
        action="dismiss",
        fingerprint=None,
        reason="test"
    )
    assert not gen.dismiss_incident("", "test")
    
    gen2 = AutoIntentGenerator(
        db_path=incident_env["db"],
        ledger_path=incident_env["ledger"],
        action="dismiss",
        fingerprint="abc123",
        reason=None
    )
    assert not gen2.dismiss_incident("abc123", None)


def test_resolve_nonexistent_fingerprint_returns_false(incident_env):
    """Resolving non-existent fingerprint should return False."""
    gen = AutoIntentGenerator(
        db_path=incident_env["db"],
        ledger_path=incident_env["ledger"],
        action="resolve",
        fingerprint="nonexistent123",
        reason="test"
    )
    assert not gen.resolve_incident("nonexistent123", "test")


def test_ledger_entry_contains_required_fields(incident_env, monkeypatch):
    """Ledger entries should have all required fields for auditing."""
    monkeypatch.chdir(incident_env["root"])
    report = {
        "summary": "Test ledger fields",
        "category": "test",
        "error_trace": "Test error"
    }
    incident_env["report"].write_text(json.dumps(report))
    
    gen = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])
    gen.synthesize()
    
    ledger_content = incident_env["ledger"].read_text()
    entry = json.loads(ledger_content.strip())
    
    assert "ticket_id" in entry
    assert "error_fingerprint" in entry
    assert "severity" in entry
    assert "summary" in entry
    assert "status" in entry
    assert "created_at" in entry
    assert entry["status"] == "OPEN"


def test_cli_resolve_command(incident_env, monkeypatch):
    """Test CLI --resolve command."""
    monkeypatch.chdir(incident_env["root"])
    report = {
        "summary": "CLI resolve test",
        "category": "test",
        "error_trace": "CLI test error"
    }
    incident_env["report"].write_text(json.dumps(report))
    
    # Create incident first
    gen = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])
    gen.synthesize()
    fingerprint = gen.compute_fingerprint()
    
    # Call resolve via main()
    sys.argv = ["auto_intent_generator.py", "--db", str(incident_env["db"]), "--ledger", str(incident_env["ledger"]), "--resolve", fingerprint, "--reason", "Fixed via CLI"]
    
    # Import and call main
    import auto_intent_generator
    result = auto_intent_generator.main()
    assert result == 0


def test_cli_dismiss_command(incident_env, monkeypatch):
    """Test CLI --dismiss command."""
    monkeypatch.chdir(incident_env["root"])
    report = {
        "summary": "CLI dismiss test",
        "category": "test",
        "error_trace": "CLI test error"
    }
    incident_env["report"].write_text(json.dumps(report))
    
    # Create incident first
    gen = AutoIntentGenerator(incident_env["report"], incident_env["db"], incident_env["ledger"])
    gen.synthesize()
    fingerprint = gen.compute_fingerprint()
    
    # Call dismiss via main()
    sys.argv = ["auto_intent_generator.py", "--db", str(incident_env["db"]), "--ledger", str(incident_env["ledger"]), "--dismiss", fingerprint, "--reason", "Flaky test via CLI"]
    
    import auto_intent_generator
    result = auto_intent_generator.main()
    assert result == 0


def test_cli_synthesize_requires_report(incident_env, monkeypatch):
    """CLI synthesize should fail without --report."""
    sys.argv = ["auto_intent_generator.py", "--db", str(incident_env["db"]), "--ledger", str(incident_env["ledger"])]
    
    import auto_intent_generator
    result = auto_intent_generator.main()
    assert result == 1


def test_cli_resolve_requires_reason(incident_env, monkeypatch):
    """CLI --resolve should fail without --reason."""
    sys.argv = ["auto_intent_generator.py", "--db", str(incident_env["db"]), "--ledger", str(incident_env["ledger"]), "--resolve", "abc123"]
    
    import auto_intent_generator
    result = auto_intent_generator.main()
    assert result == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])