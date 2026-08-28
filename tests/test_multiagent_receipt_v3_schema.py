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
    return {
        "schema_version": 3,
        "protocol": "multiagent-dispatch-receipt-v3",
        "request_id": "request-1",
        "alias": "agy1",
        "model_id": "gemini-3.1-pro-high",
        "nonce": "nonce-123456789",
        "artifact_digest": "a" * 64,
        "availability": "available",
        "freshness": "fresh",
        "provenance": "provider-status",
    }


def test_v3_schema_exists_and_is_closed():
    schema_path = ROOT / ".agents/schemas/multiagent-dispatch-receipt-v3.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    assert not list(validator.iter_errors(receipt()))
    extra = dict(receipt(), raw_output="secret", reset_time="2026-08-28T00:00:00Z")
    assert list(validator.iter_errors(extra))


def test_v1_and_v2_are_not_accepted_or_converted():
    for version in (1, 2):
        old = dict(receipt(), schema_version=version)
        with pytest.raises(ReceiptV3Error):
            validate_receipt_v3(old)


@pytest.mark.parametrize("field", ["nonce", "request_id", "alias", "artifact_digest", "availability", "freshness", "provenance"])
def test_v3_binding_fields_are_required_and_tamper_evident(field):
    candidate = copy.deepcopy(receipt())
    candidate.pop(field)
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
        with pytest.raises(ReceiptV3Error):
            validate_receipt_v3(dict(receipt(), **{field: value}))
