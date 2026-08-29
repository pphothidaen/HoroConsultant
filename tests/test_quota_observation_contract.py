"""Frozen black-box contract for QuotaObservation v1 artifacts."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
import pytest

import scripts.agent_quota_status_guard as quota


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / ".agents/config/multiagent_model_policy.yaml"
OBSERVATION_SCHEMA_PATH = (
    ROOT / ".agents/schemas/multiagent-quota-observation-v1.schema.json"
)
ARTIFACT_SCHEMA_PATH = (
    ROOT / ".agents/schemas/multiagent-quota-observation-artifact-v1.schema.json"
)
NOW = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


def _context(**overrides: object) -> dict[str, object]:
    context: dict[str, object] = {
        "alias": "codex1",
        "provider": "codex",
        "account_home": "/private/account-one",
        "resolved_executable": "/opt/local/bin/codex",
        "ticket_id": "TICKET-ALIAS-RC2-004-QOBS-01",
        "attempt_id": 1,
        "policy_version": "2026-08-26.1",
        "nonce": "qobs-test-nonce-0001",
        "observed_at": "2026-08-27T12:00:00Z",
    }
    context.update(overrides)
    return context


def _signals(remaining: float = 10.0) -> dict[str, object]:
    def values() -> dict[str, object]:
        return {
            "usedPercent": 100.0 - remaining,
            "remainingPercent": remaining,
            "reached": remaining == 0.0,
            "limit": 100.0,
            "spend": 100.0 - remaining,
            "remaining": remaining,
        }

    return {
        **values(),
        "buckets": {"primary": values(), "secondary": values()},
    }


def _artifact(remaining: float = 10.0) -> dict[str, object]:
    return quota.probe_quota_observation(_signals(remaining), _context())


def _validator(path: Path) -> Draft202012Validator:
    document = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(document)
    return Draft202012Validator(document, format_checker=FormatChecker())


def test_qobs_schemas_are_closed_pinned_draft_2020_12_contracts() -> None:
    observation = json.loads(OBSERVATION_SCHEMA_PATH.read_text(encoding="utf-8"))
    artifact = json.loads(ARTIFACT_SCHEMA_PATH.read_text(encoding="utf-8"))

    for schema in (observation, artifact):
        Draft202012Validator.check_schema(schema)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert schema["$id"].startswith("https://horoconsultant.local/schemas/")


def test_policy_pins_qobs_versions_domains_thresholds_and_nonexecution() -> None:
    policy = quota.load_quota_policy(POLICY_PATH)

    assert policy["quota_observation"] == {
        "schema_version": 1,
        "protocol_version": 1,
        "canonicalization_version": 1,
        "observation_schema": "../schemas/multiagent-quota-observation-v1.schema.json",
        "artifact_schema": "../schemas/multiagent-quota-observation-artifact-v1.schema.json",
        "observation_domain": "horoconsultant.multiagent.quota-observation.v1",
        "artifact_domain": "horoconsultant.multiagent.quota-observation-artifact.v1",
        "maximum_age_seconds": 60,
        "future_tolerance_seconds": 5,
        "threshold_percent": 10,
        "executable_decision_schema_versions": [],
        "receipt_protocol_version": 2,
    }


def test_schema_accepts_canonical_content_free_artifact_and_rejects_unknown_fields() -> None:
    artifact = _artifact()
    observation_validator = _validator(OBSERVATION_SCHEMA_PATH)
    artifact_validator = _validator(ARTIFACT_SCHEMA_PATH)

    assert not list(observation_validator.iter_errors(artifact["observation"]))
    assert not list(artifact_validator.iter_errors(artifact))
    extra_observation = deepcopy(artifact)
    extra_observation["observation"]["raw_status"] = "forbidden"
    assert list(artifact_validator.iter_errors(extra_observation))
    extra_artifact = dict(artifact, unexpected=True)
    assert list(artifact_validator.iter_errors(extra_artifact))


def test_canonical_json_is_utf8_sorted_minimal_and_domain_separated() -> None:
    value = {"z": 1, "a": "\u0e44\u0e17\u0e22"}

    encoded = quota.canonical_json_bytes(value)

    assert encoded == '{"a":"\u0e44\u0e17\u0e22","z":1}'.encode("utf-8")
    artifact = _artifact()
    assert quota.quota_artifact_sha256(artifact) == quota.quota_artifact_sha256(
        json.loads(json.dumps(artifact, sort_keys=False))
    )
    assert quota.quota_artifact_sha256(artifact) != quota.canonical_sha256(
        artifact, domain="a-different-domain"
    )


@pytest.mark.parametrize(
    "payload",
    [
        '{"usedPercent":90,"usedPercent":91}',
        '{"usedPercent":NaN}',
        '{"usedPercent":Infinity}',
        '{"usedPercent":-Infinity}',
    ],
)
def test_strict_json_rejects_duplicate_keys_and_non_finite_numbers(payload: str) -> None:
    with pytest.raises(quota.QuotaObservationError):
        quota.strict_json_loads(payload)


@pytest.mark.parametrize("remaining,expected", [(10.0, "constrained"), (10.0001, "constrained"), (9.9999, "below_10_percent"), (0.0, "below_10_percent")])
def test_exact_ten_percent_boundaries_and_v1_never_healthy(
    remaining: float, expected: str
) -> None:
    observation = _artifact(remaining)["observation"]

    assert observation["quota_band"] == expected
    assert observation["quota_band"] != "healthy"
    assert observation["reason_code"] == "signals_consistent"


def test_probe_output_retains_only_digests_for_paths_and_no_raw_signal_values() -> None:
    artifact = _artifact(37.25)
    serialized = quota.canonical_json_bytes(artifact).decode("utf-8")
    observation = artifact["observation"]

    assert len(observation["signal_path_sha256"]) == 18
    assert len(set(observation["signal_path_sha256"])) == 18
    assert all(len(value) == 64 for value in observation["signal_path_sha256"])
    for forbidden in (
        "/private/account-one",
        "/opt/local/bin/codex",
        "usedPercent",
        "remainingPercent",
        '"spend"',
        '"remaining"',
        "37.25",
        "62.75",
    ):
        assert forbidden not in serialized
    assert observation["account_home_sha256"] == quota.sha256_text(
        "/private/account-one"
    )
    assert observation["resolved_executable_sha256"] == quota.sha256_text(
        "/opt/local/bin/codex"
    )


@pytest.mark.parametrize(
    "payload,reason_code",
    [
        ("not-json", "malformed_status"),
        ('{"usedPercent":90,"usedPercent":91}', "duplicate_key_status"),
        ('{"usedPercent":NaN}', "non_finite_status"),
        ({"unexpected": "shape"}, "missing_signal"),
    ],
)
def test_probe_emits_one_typed_unknown_artifact_for_unusable_input(
    payload: object, reason_code: str
) -> None:
    artifact = quota.probe_quota_observation(payload, _context())

    assert set(artifact) == {
        "schema_version",
        "protocol_version",
        "canonicalization_version",
        "domain",
        "observation_sha256",
        "observation",
    }
    assert artifact["observation"]["quota_band"] == "unknown"
    assert artifact["observation"]["reason_code"] == reason_code
    assert not list(_validator(ARTIFACT_SCHEMA_PATH).iter_errors(artifact))


@pytest.mark.parametrize(
    "mutation,reason_code",
    [
        (lambda data: data.pop("remainingPercent"), "missing_signal"),
        (lambda data: data["buckets"]["primary"].pop("usedPercent"), "missing_signal"),
        (lambda data: data["buckets"]["secondary"].pop("remaining"), "missing_signal"),
        (lambda data: data.update(remainingPercent=101), "invalid_signal"),
        (lambda data: data["buckets"]["primary"].update(usedPercent=-1), "invalid_signal"),
        (lambda data: data.update(remainingPercent=20), "contradictory_signal"),
        (lambda data: data["buckets"]["secondary"].update(reached=True), "contradictory_signal"),
        (lambda data: data["buckets"]["primary"].update(remaining=11), "contradictory_signal"),
    ],
)
def test_every_legacy_and_bucket_signal_fails_closed(
    mutation, reason_code: str
) -> None:
    signals = _signals()
    mutation(signals)

    observation = quota.probe_quota_observation(signals, _context())["observation"]

    assert observation["quota_band"] == "unknown"
    assert observation["reason_code"] == reason_code


@pytest.mark.parametrize(
    "path",
    [
        ("usedPercent",),
        ("remainingPercent",),
        ("reached",),
        ("limit",),
        ("spend",),
        ("remaining",),
        ("buckets", "primary", "usedPercent"),
        ("buckets", "primary", "remainingPercent"),
        ("buckets", "primary", "reached"),
        ("buckets", "primary", "limit"),
        ("buckets", "primary", "spend"),
        ("buckets", "primary", "remaining"),
        ("buckets", "secondary", "usedPercent"),
        ("buckets", "secondary", "remainingPercent"),
        ("buckets", "secondary", "reached"),
        ("buckets", "secondary", "limit"),
        ("buckets", "secondary", "spend"),
        ("buckets", "secondary", "remaining"),
    ],
)
def test_each_required_signal_is_individually_inspected(path: tuple[str, ...]) -> None:
    signals = _signals()
    target = signals
    for component in path[:-1]:
        target = target[component]
    target.pop(path[-1])

    observation = quota.probe_quota_observation(signals, _context())["observation"]

    assert observation["quota_band"] == "unknown"
    assert observation["reason_code"] == "missing_signal"
