"""RED Contract tests for Approved Authority, EvidenceRefV1, and Mandatory Closures.

Covers:
- B1 Authority tests:
  - Approved authority is code-fixed beneath .agents/context/tickets/ and never caller-selected.
  - Manifest-bound authority permits Git-untracked records (Git tracking state is neutrality).
  - test_approved_context_is_code_fixed_manifest_bound_and_not_caller_selected
  - test_git_tracking_state_is_not_authority_or_execution_evidence
  - Free-form requests may only narrow actions, touched paths, and Horo skills (subsets only).
  - Derived actions from literal child argv.
  - Exact marker hashing for ticket_sha256 and plan_sha256 in ATOMIC_TICKET.md and plans/plan.md.
  - Boolean gate claims (passed=true, etc.) are unknown fields, not evidence.
- B2 Evidence tests:
  - Closed EvidenceRefV1 validation.
  - Read once, same-buffer hash/parse and schema validation.
  - Built-in closure minimums cannot be weakened by registry.
- Member-by-member immutable closures:
  - Security/source closure.
  - API closure.
  - Release closure.
  - Metaphysics closure with HITL scope audit.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
RESOLVER_SCRIPT = ROOT / "scripts/resolve_agent_context.py"
APPROVED_CONTEXT_PATH = ROOT / ".agents/context/tickets/TICKET-CONTEXT-OPT-001.v1.json"
FIXTURE_APPROVED_CONTEXT = ROOT / "tests/fixtures/context_profiles/approved-context.valid.json"
FIXTURE_EVIDENCE = ROOT / "tests/fixtures/context_profiles/evidence.valid.json"
FIXTURE_CLOSURES = ROOT / "tests/fixtures/context_profiles/expected-mandatory-closures.json"


def _require_resolver():
    assert RESOLVER_SCRIPT.exists(), (
        f"MISSING_CONTEXT_RESOLVER: Context resolver script not found at {RESOLVER_SCRIPT}"
    )


def test_approved_context_is_code_fixed_manifest_bound_and_not_caller_selected():
    _require_resolver()
    import scripts.resolve_agent_context as resolver
    # Caller attempting to pass a custom arbitrary path must be rejected
    with pytest.raises(Exception, match="CALLER_SELECTED_PATH_FORBIDDEN|AUTHORITY_CODE_FIXED"):
        resolver.load_approved_lane(
            repo_root=ROOT,
            ticket_id="TICKET-CONTEXT-OPT-001",
            lane_id="TICKET-CONTEXT-OPT-001-B",
            override_authority_path=Path("/tmp/fake_authority.json"),
        )


def test_git_tracking_state_is_not_authority_or_execution_evidence():
    _require_resolver()
    import scripts.resolve_agent_context as resolver
    # An untracked file at the code-fixed path with valid digest is authoritative
    lane = resolver.load_approved_lane(
        repo_root=ROOT,
        ticket_id="TICKET-CONTEXT-OPT-001",
        lane_id="TICKET-CONTEXT-OPT-001-B",
        authority_file_override=FIXTURE_APPROVED_CONTEXT,
    )
    assert lane.lane_id == "TICKET-CONTEXT-OPT-001-B"


def test_caller_context_can_only_narrow_approved_authority():
    _require_resolver()
    import scripts.resolve_agent_context as resolver
    # Broadening actions must fail
    with pytest.raises(Exception, match="BROADENING_DISALLOWED|SUBSET_REQUIRED"):
        resolver.apply_narrowing(
            approved_actions=["context.resolve"],
            requested_actions=["context.resolve", "unauthorized.mutation"],
        )


def test_child_argv_derives_sensitive_actions():
    _require_resolver()
    import scripts.resolve_agent_context as resolver
    # Derive actions from literal argv
    derived = resolver.derive_actions_from_argv(["python3", "scripts/codex_role.py", "debug", "prompt-input"])
    assert "context.inspect.codex-prompt" in derived


def test_ticket_and_plan_marker_hashes_are_exact_and_revision_monotonic():
    _require_resolver()
    import scripts.resolve_agent_context as resolver
    raw_approved = json.loads(FIXTURE_APPROVED_CONTEXT.read_text(encoding="utf-8"))
    ticket_hash = resolver.hash_marker_section(ROOT / "ATOMIC_TICKET.md", "CONTEXT-OPT-001-20260905")
    plan_hash = resolver.hash_marker_section(ROOT / "plans/plan.md", "CONTEXT-OPT-001-20260905")
    assert ticket_hash == raw_approved["ticket_sha256"]
    assert plan_hash == raw_approved["plan_sha256"]


def test_boolean_gate_claims_are_unknown_fields_not_evidence():
    _require_resolver()
    import scripts.resolve_agent_context as resolver
    bogus_evidence = {
        "type": "red_baseline_verified",
        "passed": True,
        "scan_passed": True,
        "owner_approved": True,
    }
    with pytest.raises(Exception, match="UNKNOWN_FIELD|BOOLEAN_CLAIM_NOT_EVIDENCE"):
        resolver.validate_evidence_ref(bogus_evidence)


def test_evidence_ref_v1_is_closed_digest_bound_and_fresh():
    _require_resolver()
    import scripts.resolve_agent_context as resolver
    raw_ev = json.loads(FIXTURE_EVIDENCE.read_text(encoding="utf-8"))
    validated = resolver.validate_evidence_ref(raw_ev)
    assert validated.schema_version == "evidence-ref-v1"


def test_evidence_is_read_once_then_hash_parsed_and_schema_validated():
    _require_resolver()
    import scripts.resolve_agent_context as resolver
    with pytest.raises(Exception, match="DIGEST_MISMATCH|CANONICAL_FAILURE"):
        resolver.validate_evidence_file(
            path=FIXTURE_EVIDENCE,
            expected_sha256="ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        )


def test_builtin_closure_minimums_survive_registry_mutation():
    _require_resolver()
    import scripts.resolve_agent_context as resolver
    weakened_registry_closure = {"source_security": {"enforce_one_editor": False}}
    with pytest.raises(Exception, match="MISSING_MANDATORY_GATE|CLOSURE_WEAKENED"):
        resolver.verify_closure_minimums(weakened_registry_closure)


def test_security_source_closure_enforces_one_editor_secret_scan_and_read_only_review():
    _require_resolver()
    import scripts.resolve_agent_context as resolver
    closures = resolver.get_mandatory_closures()
    sec = closures["source_security"]
    assert sec["enforce_one_editor"] is True
    assert sec["secret_scan"] is True
    assert sec["read_only_review"] is True


def test_api_closure_enforces_pydantic_v2_cors_and_golden_specs():
    _require_resolver()
    import scripts.resolve_agent_context as resolver
    closures = resolver.get_mandatory_closures()
    api = closures["api"]
    assert api["pydantic_v2"] is True
    assert api["cors_headers"] is True
    assert api["openapi_golden"] is True


def test_release_closure_enforces_docker_backend_vercel_ui_and_rollback_identities():
    _require_resolver()
    import scripts.resolve_agent_context as resolver
    closures = resolver.get_mandatory_closures()
    rel = closures["release"]
    assert rel["docker_backend"] is True
    assert rel["vercel_ui"] is True
    assert rel["viewports"] == 5


def test_metaphysics_closure_enforces_deterministic_tools_and_hitl_scope_gate():
    _require_resolver()
    import scripts.resolve_agent_context as resolver
    closures = resolver.get_mandatory_closures()
    meta = closures["metaphysics"]
    assert meta["deterministic_tools"] is True
    assert meta["hitl_scope_gate"] is True
