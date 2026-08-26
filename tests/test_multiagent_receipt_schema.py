"""Receipt-schema v2 parity tests for synthetic Codex and AGY executions."""
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

from jsonschema import Draft202012Validator, FormatChecker
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.multiagent_prompt_command as command


def _policy() -> dict[str, object]:
    return command.load_model_policy(ROOT / ".agents/config/multiagent_model_policy.yaml")


def _work_result() -> dict[str, object]:
    return {
        "status": "DONE", "scope_owned": ["tests/schema"],
        "evidence": {"commands": ["pytest"], "outcomes": ["ok"], "artifacts": []},
        "findings": ["schema receipt"], "changed_files": [], "residual_risk": "none",
        "recommended_next_action": "none",
    }


def _stream(provider: str, work_result: dict[str, object]) -> str:
    if provider == "codex":
        events = (
            {"type": "thread.started", "thread_id": "schema-codex"},
            {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(work_result)}},
            {"type": "turn.completed"},
        )
    else:
        events = (
            {"event": "init", "conversation_id": "schema-agy", "init": {}},
            {"event": "step_update", "step_update": {"conversation_id": "schema-agy", "state": "ACTIVE"}},
            {"event": "result", "result": {"conversation_id": "schema-agy", "status": "SUCCESS", "structured_output": work_result}},
        )
    return "\n".join(json.dumps(event, separators=(",", ":")) for event in events) + "\n"


def _isolated_account_homes(tmp_path: Path) -> dict[str, Path]:
    """Create structurally safe account homes without any auth artifacts."""
    homes = {
        "codex": tmp_path / "codex-home",
        "agy": tmp_path / "agy-home",
    }
    for home in homes.values():
        home.mkdir(mode=0o700, exist_ok=True)
        home.chmod(0o700)
    return homes


def _invocation(tmp_path: Path, provider: str) -> command.Invocation:
    policy = _policy()
    homes = _isolated_account_homes(tmp_path)
    is_agy = provider == "agy"
    role = "researcher" if is_agy else "developer"
    ticket = "TICKET-SCHEMA-AGY" if is_agy else "TICKET-SCHEMA-CODEX"
    ownership = "tests/schema/agy.py" if is_agy else "tests/schema/codex.py"
    config = {
        "runtime": {"approved_for_execution": True, "protocol_version": 2},
        "accounts": {
            "codex1": {
                "cli": "codex", "command": "codex", "home_env": "CODEX_HOME",
                "home_path": str(homes["codex"]),
            },
            "agy1": {
                "cli": "agy", "command": "agy", "home_env": "AGY_HOME",
                "home_path": str(homes["agy"]),
            },
        },
        "roles": {
            "developer": {"alias": "codex1", "cli": "codex", "model": "gpt-5.6-luna", "effort": "medium", "sandbox": "read-only"},
            "researcher": {"alias": "agy1", "cli": "agy", "model": "gemini-3.1-pro-high", "effort": "high", "mode": "plan", "sandbox": True},
        },
    }
    route = command.resolve_route(config, role)
    decision = {
        "schema_version": 1, "ticket": ticket, "phase": "implementation", "scope_rank": 2 if is_agy else 1,
        "complexity_rank": 1, "risk_rank": 1, "ambiguity_rank": 1, "evidence_burden_rank": 1,
        "quota_band": "healthy", "work_mode": "read_only", "selected_alias": route.alias,
        "selected_model": route.model, "selected_effort": route.effort, "rationale": "schema parity",
        "policy_version": policy["policy_version"], "planning_to_medium_confirmed": True, "hitl_approved": False,
    }
    snapshot = {"schema_version": 1, "tickets": [{"ticket_id": ticket, "severity": "HIGH", "work_effort": "M", "status": "READY", "dependencies": [], "blockers": [], "owner": role, "ownership": [ownership], "quota_passed": True, "hitl_passed": True, "rule18_decision_valid": True}], "reservations": []}
    runtime = tmp_path / f"{provider}.runtime.yaml"
    runtime.write_text("runtime: true\n", encoding="utf-8")
    return command.build_invocation(
        route, command.render_prompt(objective=f"schema {provider}", ownership=ownership), tmp_path,
        decision=decision, model_policy=policy, objective=f"schema {provider}", ownership=ownership,
        runtime_config_path=runtime, runtime_config_approved=True, scheduling_snapshot=snapshot,
        claim_store_override=str(tmp_path / f"{provider}-ledger"),
    )


def _outcome(tmp_path: Path, monkeypatch, provider: str):
    invocation = _invocation(tmp_path, provider)
    raw = _stream(provider, _work_result())
    monkeypatch.setattr(command, "validate_execution_preflight", lambda _invocation: None)
    monkeypatch.setattr(command.subprocess, "run", lambda argv, **kwargs: subprocess.CompletedProcess(argv, 0, raw, ""))
    return invocation, raw, command.execute_invocation(invocation)


def _validator() -> Draft202012Validator:
    policy = _policy()
    schema_path = (ROOT / ".agents/config" / policy["result_contract"]["receipt_schema"]).resolve()
    assert schema_path.name == "multiagent-dispatch-receipt-v2.schema.json"
    return Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")), format_checker=FormatChecker())


def test_generated_codex_and_agy_receipts_match_policy_selected_v2_schema(tmp_path, monkeypatch):
    validator = _validator()
    for provider in ("codex", "agy"):
        invocation, raw, outcome = _outcome(tmp_path, monkeypatch, provider)
        receipt = outcome.completed["execution_receipt"]
        assert not list(validator.iter_errors(receipt))
        assert receipt["started_at"].endswith("Z") and receipt["ended_at"].endswith("Z")
        assert receipt["claim_proof_scope"] == "digest-integrity-not-authenticity"
        assert command.validate_execution_receipt(receipt, outcome.completed["work_result"], invocation, raw) == receipt
        assert outcome.process.stdout == "[PROVIDER_STDOUT_ELIDED]"


def test_receipt_schema_requires_all_receipt_and_claim_proof_fields_and_rejects_extra_data(tmp_path, monkeypatch):
    validator = _validator()
    _, _, outcome = _outcome(tmp_path, monkeypatch, "codex")
    receipt = outcome.completed["execution_receipt"]
    for field in validator.schema["required"]:
        candidate = dict(receipt)
        candidate.pop(field)
        assert list(validator.iter_errors(candidate)), field
    for field in validator.schema["$defs"]["claimProof"]["required"]:
        candidate = dict(receipt)
        proof = dict(candidate["claim_proof"])
        proof.pop(field)
        candidate["claim_proof"] = proof
        assert list(validator.iter_errors(candidate)), field
    extra = dict(receipt, unexpected="blocked")
    assert list(validator.iter_errors(extra))


def test_receipt_schema_enforces_provider_session_conditionals_and_runtime_digest_tamper_rejection(tmp_path, monkeypatch):
    validator = _validator()
    codex_invocation, codex_raw, codex = _outcome(tmp_path, monkeypatch, "codex")
    agy_invocation, agy_raw, agy = _outcome(tmp_path, monkeypatch, "agy")
    codex_without_session = dict(codex.completed["execution_receipt"])
    codex_without_session.pop("process_or_session_id")
    assert not list(validator.iter_errors(codex_without_session))
    agy_without_session = dict(agy.completed["execution_receipt"])
    agy_without_session.pop("process_or_session_id")
    assert list(validator.iter_errors(agy_without_session))
    bad_pair = dict(codex.completed["execution_receipt"], provider="agy")
    assert list(validator.iter_errors(bad_pair))
    digest_tamper = dict(codex.completed["execution_receipt"])
    digest_tamper["claim_proof_sha256"] = "0" * 64
    assert not list(validator.iter_errors(digest_tamper))
    with pytest.raises(command.ConfigurationError, match="ClaimProof digest"):
        command.validate_execution_receipt(digest_tamper, codex.completed["work_result"], codex_invocation, codex_raw)
    assert command._parse_utc_timestamp("2026-08-26T00:00:00+00:00", "test")
    plus_zero = dict(codex.completed["execution_receipt"], started_at="2026-08-26T00:00:00+00:00")
    assert list(validator.iter_errors(plus_zero))
    assert agy_raw and agy_invocation
