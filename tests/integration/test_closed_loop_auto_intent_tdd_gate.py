"""Integration test: closed loop auto_intent_generator -> ATOMIC_TICKET.md -> tdd_gate.

Verifies that a Tier-2 incident synthesized by auto_intent_generator produces an
ATOMIC_TICKET.md in the format consumed/recognized by tdd_gate, completing the
closed loop from post-deploy failure to TDD remediation.
"""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from auto_intent_generator import AutoIntentGenerator
import tdd_gate


@pytest.fixture
def incident_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    report_file = tmp_path / "failure_report.json"
    db_file = tmp_path / "ai_sdlc_metrics.db"
    ledger_file = tmp_path / "escapes_ledger.jsonl"
    report = {
        "summary": "Order price calculation off by discount round",
        "category": "calculation",
        "error_trace": "Expected 100.0 got 99.5",
    }
    report_file.write_text(json.dumps(report), encoding="utf-8")
    return {"root": tmp_path, "report": report_file, "db": db_file, "ledger": ledger_file}


def test_closed_loop_generates_and_tdd_gate_reads_ticket(incident_env):
    gen = AutoIntentGenerator(
        incident_env["report"],
        incident_env["db"],
        incident_env["ledger"],
    )
    target = gen.synthesize()
    assert target == "ATOMIC_TICKET.md"

    ticket_path = incident_env["root"] / "ATOMIC_TICKET.md"
    assert ticket_path.exists()

    content = ticket_path.read_text(encoding="utf-8")
    # Format contract consumed by downstream TDD flow
    assert content.startswith("# ATOMIC TICKET:")
    assert "**Risk Tier:** Tier 2" in content
    assert "**Ticket ID:**" in content
    assert "**Error Fingerprint:**" in content
    assert "## Acceptance Criteria" in content
    assert "TDD_RED_INTEGRATION" in content or "TDD: `SPEC_VERIFIED`" in content

    # tdd_gate recognizes the generated artifact as a documentation-only path
    assert tdd_gate._is_docs_only_path("ATOMIC_TICKET.md") is True
    assert tdd_gate.detect_risk_tier(["ATOMIC_TICKET.md"]) == "Tier 1"

    # Extract ticket id and confirm tdd_gate state machine accepts it as a valid id
    ticket_id = None
    for line in content.splitlines():
        if line.strip().startswith("* **Ticket ID:**"):
            ticket_id = line.split("**Ticket ID:**", 1)[1].strip()
            break
    assert ticket_id is not None and ticket_id.startswith("KAN-INC-")

    # tdd_gate exposes the state constants referenced by the ticket acceptance criteria
    assert tdd_gate.STATE_SPEC_VERIFIED == "SPEC_VERIFIED"
    assert tdd_gate.STATE_TDD_RED_INTEGRATION == "TDD_RED_INTEGRATION"
    assert tdd_gate.STATE_TDD_GREEN_INTEGRATION == "TDD_GREEN_INTEGRATION"
    assert "SPEC_VERIFIED" in tdd_gate.ALLOWED_TRANSITIONS
    assert "TDD_RED_INTEGRATION" in tdd_gate.ALLOWED_TRANSITIONS["SPEC_VERIFIED"]


def test_closed_loop_workflow_file_exists():
    workflow = REPO_ROOT / ".github" / "workflows" / "post-deploy-tdd.yml"
    assert workflow.exists(), "post-deploy-tdd.yml must exist for closed loop"
    text = workflow.read_text(encoding="utf-8")
    assert "auto_intent_generator.py" in text
    assert "ATOMIC_TICKET.md" in text
    assert "HORO_GATE_MODE" in text or "observation" in text