"""Unit tests for Evidence Schema v1.0 and shared fixtures (AT-05)."""

import json
from pathlib import Path

import jsonschema
import pytest

from project.core.evidence_models import WorkerEvidenceV1

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "worker_evidence_v1.json"
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "evidence"


@pytest.fixture
def evidence_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_schema_itself_is_valid(evidence_schema):
    """Verify that schemas/worker_evidence_v1.json is a valid Draft 2020-12 schema."""
    jsonschema.Draft202012Validator.check_schema(evidence_schema)


def test_valid_evidence_fixture(evidence_schema):
    """Verify that valid.json strictly conforms to schema and hash verification."""
    with open(FIXTURES_DIR / "valid.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Must validate against JSON schema
    jsonschema.validate(instance=data, schema=evidence_schema)

    # Must match computed hash
    computed = WorkerEvidenceV1.compute_hash(data)
    assert data["evidence_hash"] == computed


def test_missing_git_sha_fixture_fails_schema(evidence_schema):
    """Verify that missing_git_sha.json fails schema validation."""
    with open(FIXTURES_DIR / "missing_git_sha.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    with pytest.raises(jsonschema.ValidationError, match="'git_sha' is a required property"):
        jsonschema.validate(instance=data, schema=evidence_schema)


def test_invalid_artifact_hash_fails_schema(evidence_schema):
    """Verify that invalid_artifact_hash.json fails regex validation."""
    with open(FIXTURES_DIR / "invalid_artifact_hash.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=data, schema=evidence_schema)


def test_failed_tests_fixture_is_schema_valid_but_fails_tests():
    """Verify failed_tests.json parses structurally but records failed tests."""
    with open(FIXTURES_DIR / "failed_tests.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["tests"]["failed"] > 0
    assert data["acceptance_checks"][0]["status"] == "failed"


def test_hash_tampering_detection():
    """Verify that tampering with any field in valid.json invalidates the evidence hash."""
    with open(FIXTURES_DIR / "valid.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Tamper with test count
    tampered = dict(data)
    tampered["tests"] = {"total": 13, "passed": 13, "failed": 0, "skipped": 0}

    computed = WorkerEvidenceV1.compute_hash(tampered)
    assert computed != data["evidence_hash"]
