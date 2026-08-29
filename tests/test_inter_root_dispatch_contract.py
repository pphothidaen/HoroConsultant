"""Provider-free executable checks for the HITL-1 inter-root contract."""
from __future__ import annotations

import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/contracts/inter_root_dispatch_contract.md"

REQUEST_KEYS = {
    "contract", "protocol_version", "hitl_stage", "activation_prohibited",
    "request_id", "idempotency_key", "attempt", "source", "target",
    "objective", "scope", "reservation", "lease", "provider_state", "mode",
    "evidence_boundary",
}
RESPONSE_KEYS = {
    "contract", "protocol_version", "hitl_stage", "activation_prohibited",
    "request_id", "idempotency_key", "attempt", "source", "target", "status",
    "mode", "provider_state", "required_human_review", "reservation", "lease",
    "result", "receipt", "evidence_boundary",
}
BINDING_KEYS = {"root_id", "role", "account", "pool", "provider"}


def _examples() -> list[dict[str, object]]:
    text = CONTRACT.read_text(encoding="utf-8")
    blocks = re.findall(r"```json\n(.*?)\n```", text, flags=re.DOTALL)
    assert len(blocks) == 3
    return [json.loads(block) for block in blocks]


def _assert_binding(binding: dict[str, object], *, root: str, role: str, provider: str) -> None:
    assert set(binding) == BINDING_KEYS
    assert binding["root_id"] == root
    assert binding["role"] == role
    assert binding["provider"] == provider
    assert binding["account"] == binding["pool"]
    assert binding["account"] in {"codex1", "codex2", "agy1", "agy2"}


def test_machine_readable_examples_are_closed_and_share_hitl_boundary() -> None:
    request, response, blocked = _examples()
    assert set(request) == REQUEST_KEYS
    assert set(response) == RESPONSE_KEYS
    assert set(blocked) == RESPONSE_KEYS
    for example in (request, response, blocked):
        assert example["contract"] == "horoconsultant.inter-root-dispatch"
        assert example["protocol_version"] == 1
        assert example["hitl_stage"] == "HITL-1"
        assert example["activation_prohibited"] is True
        assert example["evidence_boundary"] == "validated_in_process_only"


def test_request_binding_reservation_and_lease_are_deterministically_consistent() -> None:
    request, response, _ = _examples()
    _assert_binding(request["source"], root="RootA", role="primary", provider="codex")
    _assert_binding(request["target"], root="RootB", role="secondary", provider="agy")
    assert request["source"] == response["source"]
    assert request["target"] == response["target"]
    assert request["request_id"] == response["request_id"]
    assert request["idempotency_key"] == response["idempotency_key"]
    reservation = request["reservation"]
    lease = request["lease"]
    assert reservation["request_id"] == request["request_id"]
    assert reservation["pool"] == request["target"]["pool"]
    assert lease["request_id"] == request["request_id"]
    assert lease["pool"] == reservation["pool"]
    assert lease["owner"] == reservation["owner"] == "RootB"
    assert lease["expires_at"] == reservation["expires_at"]
    assert lease["requests_used"] <= lease["request_budget"]
    assert request["target"]["role"] == "secondary"
    assert request["target"]["account"] == "agy2"


def test_unknown_provider_state_is_s5_and_cannot_be_admitted_or_drained() -> None:
    _, _, blocked = _examples()
    assert blocked["provider_state"] == "unknown"
    assert blocked["mode"] == "S5"
    assert blocked["status"] == "BLOCKED"
    assert blocked["required_human_review"] is True
    assert blocked["result"] is None
    assert blocked["receipt"] is None
    assert blocked["lease"]["state"] == "NOT_ADMITTED"
    assert blocked["reservation"]["state"] == "HELD_NO_EXECUTION"


def test_retry_key_rule_is_deterministic_and_no_example_claims_execution() -> None:
    request, response, blocked = _examples()
    logical = "roota:case-001"
    assert request["idempotency_key"] == f"{logical}:attempt-1"
    assert response["idempotency_key"] == request["idempotency_key"]
    retry_key = f"{logical}:retry:2"
    assert retry_key != request["idempotency_key"]
    assert all(example["receipt"] is None for example in (response, blocked))
    assert all(example["activation_prohibited"] is True for example in (request, response, blocked))


def test_contract_is_provider_free_and_explicitly_non_activating() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "provider invocation" in lowered
    assert "roota must" in lowered and "not directly spawn" in lowered
    assert "activation_prohibited: true" in lowered
    assert "local validation proves only shape" in lowered
    assert "does not authorize, activate, or prove dispatch" in lowered
    assert "primary -> agy1" in lowered and "secondary -> agy2" in lowered
