"""Unit tests for Deterministic Evidence Validator consuming shared fixtures (AT-06)."""

import json
from pathlib import Path
import pytest

from project.core.evidence_validator import EvidenceValidator
from project.core.execution_identity import ExecutionIdentity

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "evidence"


@pytest.fixture
def validator():
    return EvidenceValidator()


@pytest.fixture
def active_identity():
    return ExecutionIdentity(
        execution_id="exec-20260925-001",
        ticket_id="KAN-142",
        attempt=1,
        lease_id="L-8f21",
        fencing_token="fence-100",
        session_id="session-20260925-abc",
        worker_id="worker-herdr-01",
    )


def test_validator_with_valid_fixture(validator, active_identity):
    with open(FIXTURES_DIR / "valid.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    res = validator.validate(data, expected_identity=active_identity)
    assert res.is_valid is True
    assert res.error_code is None


def test_validator_with_missing_git_sha(validator, active_identity):
    with open(FIXTURES_DIR / "missing_git_sha.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    res = validator.validate(data, expected_identity=active_identity)
    assert res.is_valid is False
    assert res.error_code == "SCHEMA_VALIDATION_FAILED"


def test_validator_with_failed_tests(validator, active_identity):
    with open(FIXTURES_DIR / "failed_tests.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    res = validator.validate(data, expected_identity=active_identity)
    assert res.is_valid is False
    assert res.error_code in ("EVIDENCE_HASH_MISMATCH", "TESTS_FAILED")


def test_validator_with_wrong_fencing_token(validator, active_identity):
    with open(FIXTURES_DIR / "wrong_fencing_token.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    res = validator.validate(data, expected_identity=active_identity)
    assert res.is_valid is False
    assert res.error_code in ("EVIDENCE_HASH_MISMATCH", "STALE_FENCING_TOKEN")


def test_validator_with_wrong_attempt(validator, active_identity):
    with open(FIXTURES_DIR / "wrong_attempt.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    res = validator.validate(data, expected_identity=active_identity)
    assert res.is_valid is False
    assert res.error_code in ("EVIDENCE_HASH_MISMATCH", "INVALID_IDENTITY")


def test_validator_with_stale_session(validator, active_identity):
    with open(FIXTURES_DIR / "stale_session.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    res = validator.validate(data, expected_identity=active_identity)
    assert res.is_valid is False
    assert res.error_code in ("EVIDENCE_HASH_MISMATCH", "STALE_SESSION")
