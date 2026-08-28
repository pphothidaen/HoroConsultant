"""RED guard tests for pre-subprocess AGY admission and one-use binding."""
from __future__ import annotations

import copy

import pytest

from scripts.agy_bucket_admission import AdmissionError, admit_before_spawn, consume_nonce


def valid_request():
    return {
        "alias": "agy1",
        "model_id": "gemini-3.1-pro-high",
        "bucket_availability": "available",
        "receipt_binding": {
            "protocol": "receipt-v3",
            "request_id": "req-1",
            "alias": "agy1",
            "model_id": "gemini-3.1-pro-high",
            "nonce": "nonce-123456789",
            "artifact_digest": "a" * 64,
            "policy_digest": "b" * 64,
            "observation_digest": "c" * 64,
            "bucket_binding": ["gemini-weekly", "gemini-5h"],
            "decision": "admit",
            "scheduling_snapshot_sha256": "d" * 64,
            "provider_native_result_digest": "e" * 64,
            "work_result_digest": "f" * 64,
        },
    }


def test_qobs_v1_and_receipt_v2_are_rejected_without_conversion(tmp_path):
    for artifact in ({"schema_version": 1, "domain": "quota-observation-v1"}, {"schema_version": 2, "domain": "dispatch-receipt-v2"}):
        with pytest.raises(AdmissionError):
            admit_before_spawn(artifact, nonce_store=tmp_path / "nonces", runner=lambda: None)


def test_receipt_v3_binding_is_mandatory():
    request = valid_request()
    request.pop("receipt_binding")
    with pytest.raises(AdmissionError):
        admit_before_spawn(request, nonce_store=None, runner=lambda: None)


@pytest.mark.parametrize("bad", [
    {"nonce": "bad"},
    {"request_id": "different"},
    {"alias": "agy2"},
])
def test_invalid_nonce_or_binding_is_rejected_before_runner(tmp_path, bad):
    request = valid_request()
    request["receipt_binding"].update(bad)
    invoked = []
    with pytest.raises(AdmissionError):
        admit_before_spawn(request, nonce_store=tmp_path / "nonces", runner=lambda: invoked.append(True))
    assert invoked == []


def test_invalid_input_does_not_consume_nonce(tmp_path):
    store = tmp_path / "nonces"
    request = valid_request()
    request["bucket_availability"] = "blocked"
    with pytest.raises(AdmissionError):
        admit_before_spawn(request, nonce_store=store, runner=lambda: None)
    assert not list(store.glob("*")) if store.exists() else True


def test_duplicate_replay_fails_closed_and_runner_runs_once(tmp_path):
    store = tmp_path / "nonces"
    invoked = []
    request = valid_request()
    admit_before_spawn(request, nonce_store=store, runner=lambda: invoked.append(True))
    with pytest.raises(AdmissionError):
        admit_before_spawn(copy.deepcopy(request), nonce_store=store, runner=lambda: invoked.append(True))
    assert invoked == [True]


def test_direct_nonce_consume_is_atomic_and_replay_rejected(tmp_path):
    store = tmp_path / "nonces"
    consume_nonce("nonce-123456789", store)
    with pytest.raises(AdmissionError):
        consume_nonce("nonce-123456789", store)
