"""RED schema tests for the mandatory receipt-v3 integration binding."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from scripts.multiagent_receipt_v3 import validate_receipt_v3, ReceiptV3Error


ROOT = Path(__file__).resolve().parents[1]


def receipt():
    digest = "a" * 64
    started_at = "2026-08-31T00:00:00Z"
    ended_at = "2026-08-31T00:00:01Z"
    return {
        "receipt_schema_version": 3,
        "protocol_version": 2,
        "policy_version": "v3",
        "decision_sha256": digest,
        "scheduling_snapshot_sha256": digest,
        "dispatch_claim_key": digest,
        "dispatch_claim_sha256": digest,
        "claim_proof": {
            "schema_version": 1,
            "claim_key": digest,
            "decision_sha256": digest,
            "scheduling_snapshot_sha256": digest,
            "dispatch_identity": digest,
            "ticket_sha256": digest,
            "route_sha256": digest,
            "ownership_tokens_sha256": digest,
            "ownership_key_id": digest,
            "started_at": started_at,
            "ended_at": ended_at,
            "transport_status": "completed",
            "exit_code": 0,
            "output_bytes": 1,
            "output_sha256": digest,
            "work_result_sha256": digest,
            "terminal_state": "completed",
        },
        "claim_proof_sha256": digest,
        "claim_proof_scope": "digest-integrity-not-authenticity",
        "dispatch_identity": digest,
        "dispatch_ticket_id": "RECEIPT-V3-TDD-001",
        "attempt_id": 1,
        "alias": "agy1",
        "provider": "agy",
        "adapter": "agy-stream-json-schema-v2",
        "model": "gemini-3.1-pro-high",
        "effort": "high",
        "objective": "Freeze receipt v3 schema parity.",
        "ownership": "tests/test_multiagent_receipt_v3_schema.py",
        "quota_status": "healthy",
        "started_at": started_at,
        "ended_at": ended_at,
        "exit_code": 0,
        "transport_status": "completed",
        "process_or_session_id": "agy-session-1",
        "output_bytes": 1,
        "output_sha256": digest,
        "work_result_sha256": digest,
        "probe_claim_id": digest,
        "probe_claim_sha256": digest,
        "approval_grant_id": digest,
        "approval_grant_sha256": digest,
        "approval_consume_receipt_id": digest,
        "approval_consume_receipt_sha256": digest,
        "approval_consume_anchor_id": digest,
        "approval_consume_anchor_sha256": digest,
        "preauthorization_stores": {
            "probe_claim_store": digest,
            "approval_grant_store": digest,
            "approval_consume_store": digest,
            "dispatch_ledger_store": digest,
        },
        "preauthorization_scope": "local-single-host-nonportable-noncryptographic-attestation",
    }


def schema_validator():
    schema_path = ROOT / ".agents/schemas/multiagent-dispatch-receipt-v3.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


def test_v3_schema_exists_and_is_closed():
    validator = schema_validator()
    assert not list(validator.iter_errors(receipt()))
    extra = dict(receipt(), raw_output="secret", reset_time="2026-08-28T00:00:00Z")
    assert list(validator.iter_errors(extra))


def test_v1_and_v2_are_not_accepted_or_converted():
    for version in (1, 2):
        old = dict(receipt(), receipt_schema_version=version)
        assert list(schema_validator().iter_errors(old))
        with pytest.raises(ReceiptV3Error):
            validate_receipt_v3(old)


@pytest.mark.parametrize("field", [
    "receipt_schema_version", "protocol_version", "policy_version", "decision_sha256",
    "scheduling_snapshot_sha256", "dispatch_claim_key", "dispatch_claim_sha256", "claim_proof",
    "claim_proof_sha256", "claim_proof_scope", "dispatch_identity", "dispatch_ticket_id",
    "attempt_id", "alias", "provider", "adapter", "model", "effort", "objective", "ownership",
    "quota_status", "started_at", "ended_at", "exit_code", "transport_status", "output_bytes",
    "output_sha256", "work_result_sha256", "probe_claim_id", "probe_claim_sha256",
    "approval_grant_id", "approval_grant_sha256", "approval_consume_receipt_id",
    "approval_consume_receipt_sha256", "approval_consume_anchor_id",
    "approval_consume_anchor_sha256", "preauthorization_stores", "preauthorization_scope",
])
def test_v3_binding_fields_are_required_and_tamper_evident(field):
    candidate = copy.deepcopy(receipt())
    candidate.pop(field)
    assert list(schema_validator().iter_errors(candidate))
    with pytest.raises(ReceiptV3Error):
        validate_receipt_v3(candidate)


def test_v3_rejects_qobs_signals_and_account_or_provider_content():
    for field, value in {
        "concurrency": 2,
        "limit": 10,
        "spend": 1,
        "remainingPercent": 50,
        "raw_stream": "provider output",
        "credential": "secret",
        "account_path": "/private/account",
    }.items():
        candidate = dict(receipt(), **{field: value})
        assert list(schema_validator().iter_errors(candidate))
        with pytest.raises(ReceiptV3Error):
            validate_receipt_v3(candidate)
