"""Closed validation and construction helpers for AGY-bound receipt-v3."""
from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import timedelta
from typing import Any, Mapping


class ReceiptV3Error(ValueError):
    pass


_SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_DIGEST = re.compile(r"^[a-f0-9]{64}$")
_REQUIRED = {"schema_version", "protocol", "request_id", "alias", "model_id", "nonce", "artifact_digest", "availability", "freshness", "provenance", "policy_digest", "observation_digest", "bucket_binding", "decision", "scheduling_snapshot_sha256", "provider_native_result_digest", "work_result_digest"}
_ALLOWED = _REQUIRED
_BUCKET_BINDINGS = (
    ("gemini-weekly", "gemini-5h"),
    ("3p-weekly", "3p-5h"),
)


def _digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise ReceiptV3Error(f"invalid {field}")
    return value


def canonical_json(value: Any) -> bytes:
    """Canonicalize JSON-safe values; reject duplicate/non-finite/unsupported data."""
    def check(item: Any) -> None:
        if item is None or isinstance(item, (str, bool, int)):
            return
        if isinstance(item, float):
            if not math.isfinite(item):
                raise ReceiptV3Error("non-finite canonical value")
            return
        if isinstance(item, list):
            for child in item:
                check(child)
            return
        if isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                raise ReceiptV3Error("non-string canonical key")
            for key, child in item.items():
                check(key)
                check(child)
            return
        raise ReceiptV3Error("unsupported canonical value")
    check(value)
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as exc:
        raise ReceiptV3Error("invalid canonical value") from exc


def parse_json_strict(payload: str | bytes) -> Mapping[str, Any]:
    """Parse receipt JSON without silently accepting duplicate keys."""
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ReceiptV3Error("duplicate JSON key")
            result[key] = value
        return result
    try:
        value = json.loads(payload, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ReceiptV3Error("non-finite JSON value")))
    except (json.JSONDecodeError, TypeError) as exc:
        raise ReceiptV3Error("invalid receipt JSON") from exc
    if not isinstance(value, dict):
        raise ReceiptV3Error("receipt JSON must be an object")
    return value


def validate_receipt_v3(receipt: Mapping[str, Any], *, observation: Any | None = None) -> Mapping[str, Any]:
    if not isinstance(receipt, Mapping) or set(receipt) - _ALLOWED or set(receipt) != _REQUIRED:
        raise ReceiptV3Error("receipt-v3 is closed")
    if receipt.get("schema_version") != 3 or receipt.get("protocol") != "multiagent-dispatch-receipt-v3":
        raise ReceiptV3Error("receipt-v1/v2 and cross-protocol receipts are rejected")
    for field in ("request_id", "alias", "model_id", "nonce"):
        value = receipt.get(field)
        if not isinstance(value, str) or not _SAFE.fullmatch(value):
            raise ReceiptV3Error(f"invalid {field}")
    if not 8 <= len(receipt["nonce"]) <= 128:
        raise ReceiptV3Error("invalid nonce length")
    if receipt["alias"] not in {"agy1", "agy2", "agy3", "agy4"}:
        raise ReceiptV3Error("receipt-v3 AGY alias required")
    if receipt.get("availability") not in {"available", "blocked"} or receipt.get("freshness") not in {"fresh", "stale-or-invalid"} or not isinstance(receipt.get("provenance"), str) or not _SAFE.fullmatch(receipt["provenance"]):
        raise ReceiptV3Error("invalid admission controls")
    _digest(receipt.get("artifact_digest"), "artifact_digest")
    for field in ("policy_digest", "observation_digest", "scheduling_snapshot_sha256", "provider_native_result_digest", "work_result_digest"):
        _digest(receipt[field], field)
    binding = receipt["bucket_binding"]
    if not isinstance(binding, list) or tuple(binding) not in _BUCKET_BINDINGS:
        raise ReceiptV3Error("invalid bucket binding")
    if receipt["decision"] not in {"admit", "block"}:
        raise ReceiptV3Error("invalid decision")
    if observation is not None and receipt["observation_digest"] != _validated_observation_digest(observation):
        raise ReceiptV3Error("observation digest mismatch")
    return dict(receipt)


def _validated_observation_digest(observation: Any) -> str:
    """Digest one canonical, validated AGY observation without retaining it."""
    if not isinstance(observation, Mapping):
        raise ReceiptV3Error("observation must be an object")
    # Keep the protocol validator as the single observation contract owner;
    # import lazily because the admission module imports canonical_json here.
    try:
        from scripts.agy_bucket_admission import _timestamp, _validate_snapshot

        observed_at = _timestamp(observation.get("observed_at"), "observed_at")
        _validate_snapshot(observation, observed_at, timedelta(days=365000))
    except (ImportError, KeyError, TypeError, ValueError) as exc:
        raise ReceiptV3Error("invalid observation") from exc
    return hashlib.sha256(b"agy.bucket.observation.v1\0" + canonical_json(dict(observation))).hexdigest()


def build_receipt_v3(*, request_id: str, alias: str, model_id: str, nonce: str, artifact: Any, observation: Any | None = None, availability: str, freshness: str, provenance: str, policy_digest: str, bucket_binding: tuple[str, str], decision: str, scheduling_snapshot_digest: str, provider_native_result: Any, work_result: Any) -> dict[str, Any]:
    def digest(domain: str, value: Any) -> str:
        return hashlib.sha256(domain.encode("ascii") + b"\0" + canonical_json(value)).hexdigest()
    exact_observation = artifact if observation is None else observation
    observation_digest = _validated_observation_digest(exact_observation)
    result = {"schema_version": 3, "protocol": "multiagent-dispatch-receipt-v3", "request_id": request_id, "alias": alias, "model_id": model_id, "nonce": nonce, "artifact_digest": digest("agy.receipt.artifact.v3", artifact), "availability": availability, "freshness": freshness, "provenance": provenance, "policy_digest": _digest(policy_digest, "policy_digest"), "observation_digest": observation_digest, "bucket_binding": list(bucket_binding), "decision": decision, "scheduling_snapshot_sha256": _digest(scheduling_snapshot_digest, "scheduling_snapshot_sha256"), "provider_native_result_digest": digest("agy.receipt.provider-result.v3", provider_native_result), "work_result_digest": digest("agy.receipt.work-result.v3", work_result)}
    return dict(validate_receipt_v3(result))
