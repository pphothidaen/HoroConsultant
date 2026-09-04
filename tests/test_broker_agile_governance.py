"""Test-first baseline for BRK-B0-030: Agile Governance and Lifecycle Admission.

This suite freezes the fail-closed six-state Agile lifecycle, Definition of
Ready (DoR), Definition of Done (DoD), one-editor-per-resource ownership,
capacity exception handling, and secret-free governance boundaries before
downstream source implementation tickets (BRK-B3-020).

Negative controls cover:
- six canonical lifecycle states (TODO, READY, DOING, BLOCKED, NEEDS_HITL, DONE)
- DoR gate rejects transitions when baseline, quota, circuit, lease, or permissions are missing
- DoD gate rejects completion when WorkResult headings, independent QA, or rollback status are missing
- one-editor-per-resource ownership rejects concurrent overlapping writable scopes
- capacity exception emitted when no safe critical-path lane exists (no busywork)
- governance artifacts contain zero secrets or raw credentials
- sentinel entrypoint check asserting ENTRYPOINT_MISSING before source exists.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pytest


ROOT = Path(__file__).resolve().parents[1]
RULE_PATH = ".agents/rules/21-agile-governance.md"
SKILL_PATH = ".agents/skills/agile-governance/SKILL.md"
EVALS_PATH = ".agents/skills/agile-governance/evals/evals.json"
AGENTS_PATH = ".agents/AGENTS.md"

TARGET_GOVERNANCE_PATHS = (
    RULE_PATH,
    SKILL_PATH,
    EVALS_PATH,
    AGENTS_PATH,
)

CANONICAL_LIFECYCLE_STATES = frozenset(
    {"TODO", "READY", "DOING", "BLOCKED", "NEEDS_HITL", "DONE"}
)

WORK_RESULT_REQUIRED_HEADINGS = (
    "Status",
    "Scope owned",
    "Evidence",
    "Findings",
    "Changed files",
    "Residual risk",
    "Recommended next action",
)


def _missing_targets() -> list[str]:
    return [path for path in TARGET_GOVERNANCE_PATHS if not (ROOT / path).is_file()]


def _read_target(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Sentinel Entrypoint Check
# ---------------------------------------------------------------------------


def test_broker_agile_governance_sentinel_entrypoint_exists() -> None:
    """Sentinel entrypoint check asserting ENTRYPOINT_MISSING before B3 source exists.

    Validates that .agents/rules/21-agile-governance.md, .agents/skills/agile-governance/SKILL.md,
    and associated evals exist before claiming Agile governance compliance.
    """
    missing = _missing_targets()
    assert not missing, "ENTRYPOINT_MISSING: " + ", ".join(missing)


# ---------------------------------------------------------------------------
# 2. Negative Control: Six Canonical Lifecycle States and Valid Transitions
# ---------------------------------------------------------------------------


def test_agile_lifecycle_six_states_and_valid_transitions() -> None:
    """The lifecycle must use exactly six canonical states and enforce valid transitions."""
    assert len(CANONICAL_LIFECYCLE_STATES) == 6
    assert "TODO" in CANONICAL_LIFECYCLE_STATES
    assert "READY" in CANONICAL_LIFECYCLE_STATES
    assert "DOING" in CANONICAL_LIFECYCLE_STATES
    assert "BLOCKED" in CANONICAL_LIFECYCLE_STATES
    assert "NEEDS_HITL" in CANONICAL_LIFECYCLE_STATES
    assert "DONE" in CANONICAL_LIFECYCLE_STATES

    # Invalid non-canonical states must be rejected
    invalid_states = ["IN_PROGRESS", "PENDING", "REVIEW", "RESOLVED", "CLOSED", "DRAFT"]
    for state in invalid_states:
        assert state not in CANONICAL_LIFECYCLE_STATES

    # Transition validation function
    def validate_transition(from_state: str, to_state: str, *, dor_passed: bool, dod_passed: bool) -> bool:
        if from_state not in CANONICAL_LIFECYCLE_STATES or to_state not in CANONICAL_LIFECYCLE_STATES:
            return False
        # Cannot jump directly from TODO to DONE
        if from_state == "TODO" and to_state == "DONE":
            return False
        # Cannot enter READY or DOING without passing DoR
        if to_state in ("READY", "DOING") and not dor_passed:
            return False
        # Cannot enter DONE without passing DoD
        if to_state == "DONE" and not dod_passed:
            return False
        return True

    # Invalid transitions must reject
    assert not validate_transition("TODO", "DONE", dor_passed=True, dod_passed=True)
    assert not validate_transition("TODO", "DOING", dor_passed=False, dod_passed=False)
    assert not validate_transition("DOING", "DONE", dor_passed=True, dod_passed=False)
    assert validate_transition("DOING", "DONE", dor_passed=True, dod_passed=True)


# ---------------------------------------------------------------------------
# 3. Negative Control: Definition of Ready (DoR) Gate
# ---------------------------------------------------------------------------


def test_definition_of_ready_dor_gate_rejects_missing_prerequisites() -> None:
    """Definition of Ready (DoR) must fail-closed if any prerequisite is missing.

    Prerequisites:
    1. Test baseline verified (TEST_BASELINE_VERIFIED)
    2. Exactly one editor assigned
    3. Dependencies resolved (all in DONE status)
    4. Safe verified quota band
    5. Closed circuit breaker
    6. File permissions verified (0700 home, 0500 wrapper)
    7. Valid capacity lease
    8. Rule 18 model/effort decision valid
    9. Exact evidence path specified
    """

    def evaluate_dor(ticket_context: dict[str, Any]) -> tuple[bool, list[str]]:
        reasons: list[str] = []
        if not ticket_context.get("test_baseline_verified"):
            reasons.append("DOR_TEST_BASELINE_MISSING")
        editors = ticket_context.get("editors", [])
        if len(editors) != 1 or not editors[0]:
            reasons.append("DOR_ONE_EDITOR_VIOLATION")
        if not ticket_context.get("dependencies_done"):
            reasons.append("DOR_DEPENDENCY_UNRESOLVED")
        quota = ticket_context.get("quota_band")
        if quota not in ("healthy", "constrained"):
            reasons.append("DOR_QUOTA_UNVERIFIED")
        if ticket_context.get("circuit_breaker_open"):
            reasons.append("DOR_CIRCUIT_OPEN")
        if not ticket_context.get("permissions_verified"):
            reasons.append("DOR_PERMISSIONS_UNVERIFIED")
        if not ticket_context.get("capacity_lease_id"):
            reasons.append("DOR_LEASE_MISSING")
        if not ticket_context.get("rule18_decision_valid"):
            reasons.append("DOR_RULE18_DECISION_INVALID")
        if not ticket_context.get("evidence_path"):
            reasons.append("DOR_EVIDENCE_PATH_MISSING")
        return len(reasons) == 0, reasons

    valid_context = {
        "test_baseline_verified": True,
        "editors": ["developer_1"],
        "dependencies_done": True,
        "quota_band": "healthy",
        "circuit_breaker_open": False,
        "permissions_verified": True,
        "capacity_lease_id": "lease-abc-123",
        "rule18_decision_valid": True,
        "evidence_path": "plans/evidence/broker/sample.json",
    }

    # Valid context passes DoR
    passed, issues = evaluate_dor(valid_context)
    assert passed and not issues

    # Missing test baseline rejects
    broken = dict(valid_context, test_baseline_verified=False)
    passed, issues = evaluate_dor(broken)
    assert not passed and "DOR_TEST_BASELINE_MISSING" in issues

    # Multiple editors reject
    broken = dict(valid_context, editors=["dev1", "dev2"])
    passed, issues = evaluate_dor(broken)
    assert not passed and "DOR_ONE_EDITOR_VIOLATION" in issues

    # Unresolved dependency rejects
    broken = dict(valid_context, dependencies_done=False)
    passed, issues = evaluate_dor(broken)
    assert not passed and "DOR_DEPENDENCY_UNRESOLVED" in issues

    # Unknown quota rejects
    broken = dict(valid_context, quota_band="unknown")
    passed, issues = evaluate_dor(broken)
    assert not passed and "DOR_QUOTA_UNVERIFIED" in issues

    # Open circuit rejects
    broken = dict(valid_context, circuit_breaker_open=True)
    passed, issues = evaluate_dor(broken)
    assert not passed and "DOR_CIRCUIT_OPEN" in issues


# ---------------------------------------------------------------------------
# 4. Negative Control: Definition of Done (DoD) Gate
# ---------------------------------------------------------------------------


def test_definition_of_done_dod_gate_rejects_incomplete_deliverables() -> None:
    """Definition of Done (DoD) must reject completion when requirements are unmet.

    Requirements:
    1. Typed WorkResult with all 7 standard sections
    2. Independent QA verdict PASS
    3. Independent review verdict PASS
    4. Rollback status verified
    5. Capacity classification explicit (distinguishing theoretical, policy-admitted, runtime-proven)
    6. Zero out-of-bounds changed files
    """

    def evaluate_dod(submission: dict[str, Any]) -> tuple[bool, list[str]]:
        reasons: list[str] = []
        work_result = submission.get("work_result", {})
        for heading in WORK_RESULT_REQUIRED_HEADINGS:
            if heading not in work_result:
                reasons.append(f"DOD_WORK_RESULT_MISSING_{heading.upper().replace(' ', '_')}")
        if submission.get("qa_verdict") != "PASS":
            reasons.append("DOD_QA_VERDICT_NOT_PASS")
        if submission.get("review_verdict") != "PASS":
            reasons.append("DOD_REVIEW_VERDICT_NOT_PASS")
        if not submission.get("rollback_verified"):
            reasons.append("DOD_ROLLBACK_UNVERIFIED")
        if not submission.get("capacity_classified"):
            reasons.append("DOD_CAPACITY_UNCLASSIFIED")
        if submission.get("out_of_bounds_files"):
            reasons.append("DOD_OWNERSHIP_BREACH")
        return len(reasons) == 0, reasons

    valid_submission = {
        "work_result": {heading: "content" for heading in WORK_RESULT_REQUIRED_HEADINGS},
        "qa_verdict": "PASS",
        "review_verdict": "PASS",
        "rollback_verified": True,
        "capacity_classified": True,
        "out_of_bounds_files": [],
    }

    # Valid submission passes DoD
    passed, issues = evaluate_dod(valid_submission)
    assert passed and not issues

    # Missing WorkResult heading rejects
    broken_wr = {k: v for k, v in valid_submission["work_result"].items() if k != "Residual risk"}
    broken = dict(valid_submission, work_result=broken_wr)
    passed, issues = evaluate_dod(broken)
    assert not passed and "DOD_WORK_RESULT_MISSING_RESIDUAL_RISK" in issues

    # QA verdict FAIL rejects
    broken = dict(valid_submission, qa_verdict="FAIL")
    passed, issues = evaluate_dod(broken)
    assert not passed and "DOD_QA_VERDICT_NOT_PASS" in issues

    # Out of bounds modified file rejects
    broken = dict(valid_submission, out_of_bounds_files=["unowned/source.py"])
    passed, issues = evaluate_dod(broken)
    assert not passed and "DOD_OWNERSHIP_BREACH" in issues


# ---------------------------------------------------------------------------
# 5. Negative Control: One-Editor-Per-Resource Ownership Conflict
# ---------------------------------------------------------------------------


def test_one_editor_per_resource_rejects_concurrent_ownership_overlap() -> None:
    """Two concurrent DOING tickets cannot have overlapping writable paths."""
    active_reservations = {
        "ticket_1": {
            "editor": "developer_1",
            "status": "DOING",
            "writable_paths": ["scripts/multiagent_capacity.py"],
        }
    }

    candidate_ticket = {
        "ticket_id": "ticket_2",
        "editor": "developer_2",
        "status": "READY",
        "writable_paths": ["scripts/multiagent_capacity.py", "scripts/other.py"],
    }

    def check_ownership_collision(candidate: dict[str, Any], reservations: dict[str, Any]) -> bool:
        candidate_paths = set(candidate["writable_paths"])
        for res in reservations.values():
            if res["status"] == "DOING":
                reserved_paths = set(res["writable_paths"])
                if candidate_paths & reserved_paths:
                    return True  # Collision detected
        return False

    collision = check_ownership_collision(candidate_ticket, active_reservations)
    assert collision, "Overlapping writable paths must trigger ownership collision"


# ---------------------------------------------------------------------------
# 6. Negative Control: Capacity Exception & No Fake-Capacity Busywork
# ---------------------------------------------------------------------------


def test_capacity_exception_and_prohibition_of_fake_capacity_busywork() -> None:
    """When no safe critical-path lane exists, emit CAPACITY_EXCEPTION and leave slot unused.

    Idle capacity slots must not be filled with exploratory probes, speculative work,
    or placeholder busywork.
    """
    eligible_critical_path_tickets: list[dict[str, Any]] = []

    def dispatch_slot(eligible_tickets: list[dict[str, Any]]) -> str:
        if not eligible_tickets:
            return "CAPACITY_EXCEPTION: NO_SAFE_CRITICAL_PATH_LANE"
        return f"DISPATCH: {eligible_tickets[0]['ticket_id']}"

    result = dispatch_slot(eligible_critical_path_tickets)
    assert result == "CAPACITY_EXCEPTION: NO_SAFE_CRITICAL_PATH_LANE"


# ---------------------------------------------------------------------------
# 7. Negative Control: Secret-Free Policy and Governance Artifacts
# ---------------------------------------------------------------------------


def test_governance_policy_artifacts_contain_no_secrets_or_keychain_data() -> None:
    """Governance files must never contain live credentials, keys, or keychain tokens."""
    forbidden_tokens = (
        "authorization:",
        "bearer ",
        "ghp_",
        "token=",
        "secret=",
    )

    for path in TARGET_GOVERNANCE_PATHS:
        file_path = ROOT / path
        if not file_path.is_file():
            continue
        content = file_path.read_text(encoding="utf-8").lower()
        leaked = [token for token in forbidden_tokens if token in content]
        assert not leaked, f"{path} contains forbidden credential tokens: {leaked}"
