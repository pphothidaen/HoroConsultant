"""RED integration contracts for the AGY bucket admission protocol."""
from __future__ import annotations

import json

import pytest

from scripts.agy_bucket_admission import AdmissionError, admit_and_dispatch


def request():
    return {
        "alias": "agy1",
        "model_id": "gemini-3.1-pro-high",
        "bucket_availability": "available",
        "receipt_binding": {"protocol": "receipt-v3", "request_id": "r-1", "nonce": "nonce-123456789"},
        "safe_input": {"objective_digest": "a" * 64, "scope_digest": "b" * 64},
    }


def test_fake_runner_proves_no_provider_command_or_dispatcher_invocation_on_invalid_artifact(tmp_path):
    calls = []
    bad = request()
    bad["safe_input"]["raw_output"] = "must not cross boundary"
    with pytest.raises(AdmissionError):
        admit_and_dispatch(bad, nonce_store=tmp_path / "nonces", provider_runner=lambda: calls.append("provider"), dispatcher=lambda: calls.append("dispatcher"))
    assert calls == []


@pytest.mark.parametrize("field", ["concurrency", "entitlement", "limit", "spend", "usedPercent", "remainingPercent", "reached", "totals", "reset_calculation"])
def test_forbidden_derived_qobs_and_synthetic_fields_are_rejected(field, tmp_path):
    bad = request()
    bad["safe_input"][field] = 1
    with pytest.raises(AdmissionError):
        admit_and_dispatch(bad, nonce_store=tmp_path / "nonces", provider_runner=lambda: None, dispatcher=lambda: None)


def test_no_qobs_six_signal_or_synthetic_bucket_derivation(tmp_path):
    bad = request()
    bad["safe_input"]["signals"] = [{"name": "remaining", "value": 0.5}] * 6
    bad["safe_input"]["synthetic_buckets"] = ["gemini-weekly"]
    with pytest.raises(AdmissionError):
        admit_and_dispatch(bad, nonce_store=tmp_path / "nonces", provider_runner=lambda: None, dispatcher=lambda: None)


def test_successful_result_retains_only_safe_admission_evidence(tmp_path):
    result = admit_and_dispatch(request(), nonce_store=tmp_path / "nonces", provider_runner=lambda: {"status": "completed"}, dispatcher=lambda: None)
    encoded = json.dumps(result, sort_keys=True).lower()
    for forbidden in ("raw", "credential", "path", "account", "response", "fraction", "reset", "stream"):
        assert forbidden not in encoded
