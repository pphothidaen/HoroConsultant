"""Receipt-schema v3 parity tests for synthetic Codex and AGY executions."""
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
    base = command.build_invocation(
        route, command.render_prompt(objective=f"schema {provider}", ownership=ownership), tmp_path,
        decision=decision, model_policy=policy, objective=f"schema {provider}", ownership=ownership,
        runtime_config_path=runtime, runtime_config_approved=True, scheduling_snapshot=snapshot,
        claim_store_override=str(tmp_path / f"{provider}-ledger"),
    )
    claim = tmp_path / f"{provider}-probe-claim.json"
    grant = tmp_path / f"{provider}-approval-grant.json"
    consume = tmp_path / f"{provider}-consume"
    consume.mkdir(mode=0o700, exist_ok=True)
    configured = replace(
        base,
        probe_claim_path=str(claim),
        approval_grant_path=str(grant),
        approval_store_path=str(consume),
        approval_session_id=f"schema-{provider}",
    )
    command.emit_probe_claim(
        configured, claim, session_id=f"schema-{provider}"
    )
    command.emit_probe_approval(
        configured, claim, grant, session_id=f"schema-{provider}"
    )
    return configured


def _outcome(tmp_path: Path, monkeypatch, provider: str):
    invocation = _invocation(tmp_path, provider)
    work_result = _work_result()
    raw = _stream(provider, work_result)
    monkeypatch.setattr(command, "validate_execution_preflight", lambda _invocation: None)

    def fake_run(argv, **kwargs):
        if provider == "codex":
            flag = "--output-last-message" if "--output-last-message" in argv else "-o"
            Path(argv[argv.index(flag) + 1]).write_text(
                json.dumps(work_result), encoding="utf-8"
            )
        return subprocess.CompletedProcess(argv, 0, raw, "")

    monkeypatch.setattr(command, "_run_provider_process", fake_run)
    return invocation, raw, command.execute_invocation(invocation)


def _validator() -> Draft202012Validator:
    policy = _policy()
    schema_path = (ROOT / ".agents/config" / policy["result_contract"]["receipt_schema"]).resolve()
    assert schema_path.name == "multiagent-dispatch-receipt-v3.schema.json"
    return Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")), format_checker=FormatChecker())


def test_v3_policy_references_four_valid_closed_preauthorization_schemas():
    policy = _policy()
    configured = [
        policy["result_contract"]["receipt_schema"],
        policy["preauthorization"]["probe_claim_schema"],
        policy["preauthorization"]["approval_grant_schema"],
        policy["preauthorization"]["approval_consume_schema"],
    ]
    for relative in configured:
        path = (ROOT / ".agents/config" / relative).resolve()
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        assert schema["additionalProperties"] is False
    assert policy["result_contract"]["historical_receipt_v2_schema"].endswith(
        "multiagent-dispatch-receipt-v2.schema.json"
    )


def test_emitted_claim_and_grant_match_their_policy_selected_schemas(tmp_path):
    invocation = _invocation(tmp_path, "codex")
    claim = json.loads(Path(invocation.probe_claim_path).read_text(encoding="ascii"))
    grant = json.loads(Path(invocation.approval_grant_path).read_text(encoding="ascii"))
    policy = _policy()["preauthorization"]
    for configured, value in (
        (policy["probe_claim_schema"], claim),
        (policy["approval_grant_schema"], grant),
    ):
        schema = json.loads(
            (ROOT / ".agents/config" / configured).resolve().read_text(encoding="utf-8")
        )
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        assert not list(validator.iter_errors(value))


def test_generated_codex_receipt_matches_v3_schema_and_agy_generates_no_receipt(
    tmp_path, monkeypatch
):
    validator = _validator()
    invocation, raw, outcome = _outcome(tmp_path, monkeypatch, "codex")
    receipt = outcome.completed["execution_receipt"]
    assert receipt["receipt_schema_version"] == 3
    assert not list(validator.iter_errors(receipt))
    assert receipt["started_at"].endswith("Z") and receipt["ended_at"].endswith("Z")
    assert receipt["claim_proof_scope"] == "digest-integrity-not-authenticity"
    assert command.validate_execution_receipt(
        receipt, outcome.completed["work_result"], invocation, raw
    ) == receipt
    assert outcome.process.stdout == "[PROVIDER_STDOUT_ELIDED]"

    agy_invocation = _invocation(tmp_path, "agy")
    transport_calls = 0

    def forbidden_transport(*args, **kwargs):
        nonlocal transport_calls
        transport_calls += 1
        raise AssertionError("AGY transport must remain unreachable")

    monkeypatch.setattr(command, "_run_provider_process", forbidden_transport)
    with pytest.raises(command.PlatformNativePrespawnReceiptRequired) as exc:
        command.execute_invocation(agy_invocation)
    assert exc.value.code == "PLATFORM_NATIVE_PRESPAWN_RECEIPT_REQUIRED"
    assert transport_calls == 0


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
    codex_without_session = dict(codex.completed["execution_receipt"])
    codex_without_session.pop("process_or_session_id")
    assert not list(validator.iter_errors(codex_without_session))
    static_agy_receipt = dict(
        codex.completed["execution_receipt"],
        alias="agy1",
        provider="agy",
        adapter="agy-stream-json-schema-v2",
        model="gemini-3.1-pro-high",
        effort="high",
        process_or_session_id="schema-agy",
    )
    assert not list(validator.iter_errors(static_agy_receipt))
    agy_without_session = dict(static_agy_receipt)
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
    agy_invocation = _invocation(tmp_path, "agy")
    agy_raw = _stream("agy", _work_result())
    parsed_agy = command.parse_provider_result(agy_invocation, agy_raw)
    assert parsed_agy.adapter == "agy-stream-json-schema-v2"
    assert parsed_agy.process_or_session_id == "schema-agy"
