"""Fail-closed, content-free admission for the isolated AGY bucket protocol."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from scripts.multiagent_receipt_v3 import ReceiptV3Error, canonical_json


class AdmissionError(ValueError):
    """Raised when an AGY artifact cannot be admitted safely."""


UTC = timezone.utc
PROTOCOL = "horoconsultant.agy-bucket-admission.v1"
_ALIASES = frozenset({"agy1", "agy2", "agy3", "agy4"})
_BUCKETS = frozenset({"gemini-weekly", "gemini-5h", "3p-weekly", "3p-5h"})
_SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_DIGEST = re.compile(r"^[a-f0-9]{64}$")
_RESET_TIMESTAMP = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,15})?Z$"
)
_USED_NONCES: set[str] = set()
_BUCKET_BINDINGS = (
    ("gemini-weekly", "gemini-5h"),
    ("3p-weekly", "3p-5h"),
)


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AdmissionError(f"{label} must be an object")
    return value


def _safe(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _SAFE.fullmatch(value):
        raise AdmissionError(f"invalid {label}")
    return value


def _finite_fraction(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AdmissionError("remaining_fraction must be numeric")
    result = float(value)
    if not math.isfinite(result) or not 0 <= result <= 1:
        raise AdmissionError("remaining_fraction is invalid")
    return result


def _timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise AdmissionError(f"invalid {label}")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise AdmissionError(f"invalid {label}") from exc
    if parsed.tzinfo is None:
        raise AdmissionError(f"invalid {label}")
    return parsed.astimezone(UTC)


def _reset_timestamp(value: Any) -> datetime:
    """Parse the bounded RFC3339 reset timestamp without deriving freshness."""
    if not isinstance(value, str) or not _RESET_TIMESTAMP.fullmatch(value):
        raise AdmissionError("invalid reset_time")
    return _timestamp(value, "reset_time")


def _canonical(value: Any) -> bytes:
    try:
        return canonical_json(value)
    except ReceiptV3Error as exc:
        raise AdmissionError(str(exc)) from exc


def domain_digest(domain: str, value: Any) -> str:
    """Return a domain-separated SHA-256 digest without retaining ``value``."""
    _safe(domain, "digest domain")
    return hashlib.sha256((domain + "\0").encode("ascii") + _canonical(value)).hexdigest()


def parse_json_strict(payload: str | bytes) -> Mapping[str, Any]:
    """Parse JSON while rejecting duplicate keys before any validation occurs."""
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, val in items:
            if key in result:
                raise AdmissionError("duplicate JSON key")
            result[key] = val
        return result
    try:
        value = json.loads(payload, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(AdmissionError("non-finite JSON number")))
    except (json.JSONDecodeError, TypeError) as exc:
        raise AdmissionError("invalid JSON") from exc
    return _mapping(value, "artifact")


def _validate_snapshot(snapshot: Mapping[str, Any], now: datetime, max_age: timedelta) -> tuple[str, str, str, str]:
    allowed = {"protocol", "protocol_version", "alias", "model_id", "buckets", "observed_at", "provenance"}
    if set(snapshot) - allowed:
        raise AdmissionError("unknown snapshot field")
    if "protocol" not in snapshot or "protocol_version" not in snapshot or snapshot["protocol"] != PROTOCOL or snapshot["protocol_version"] != 1:
        raise AdmissionError("wrong AGY bucket protocol")
    alias = snapshot.get("alias")
    model_id = _safe(model_id_value := snapshot.get("model_id"), "model_id")
    if alias not in _ALIASES:
        raise AdmissionError("invalid alias")
    observed = _timestamp(snapshot.get("observed_at"), "observed_at")
    now = now.astimezone(UTC)
    if observed > now or now - observed > max_age:
        raise AdmissionError("stale or future snapshot")
    provenance = _mapping(snapshot.get("provenance"), "provenance")
    if set(provenance) - {"kind", "fresh"} or provenance.get("kind") != "provider_status" or provenance.get("fresh") is not True:
        raise AdmissionError("invalid provenance")
    buckets = _mapping(snapshot.get("buckets"), "buckets")
    if not buckets or set(buckets) - _BUCKETS:
        raise AdmissionError("unknown or missing bucket")
    for name, raw in buckets.items():
        item = _mapping(raw, "bucket")
        if set(item) - {"remaining_fraction", "disabled", "reset_time", "unit"}:
            raise AdmissionError("unknown bucket field")
        _finite_fraction(item.get("remaining_fraction"))
        if not isinstance(item.get("disabled"), bool):
            raise AdmissionError("disabled must be boolean")
        if "unit" in item and item["unit"] != "fraction":
            raise AdmissionError("invalid bucket unit")
        if "reset_time" in item:
            reset = _reset_timestamp(item["reset_time"])
            if reset < observed:
                raise AdmissionError("invalid reset time")
    if model_id.startswith("gemini-"):
        if alias != "agy1" or set(buckets) != {"gemini-weekly", "gemini-5h"}:
            return alias, model_id, "blocked", domain_digest("agy.bucket.observation.v1", snapshot)
        eligible = all(_finite_fraction(buckets[k]["remaining_fraction"]) > 0.10 and not buckets[k]["disabled"] for k in ("gemini-weekly", "gemini-5h"))
    else:
        eligible = False
    return alias, model_id, "available" if eligible else "blocked", domain_digest("agy.bucket.observation.v1", snapshot)


def admit_bucket_snapshot(snapshot: Mapping[str, Any], *, now: datetime, max_age: timedelta = timedelta(minutes=30), model_bucket_map: Mapping[str, tuple[str, str]] | None = None) -> dict[str, str]:
    """Return only the safe admission projection for one structured snapshot."""
    snapshot = _mapping(snapshot, "snapshot")
    # Sensitive/raw top-level material is a boundary violation, not a blocked
    # provider observation: callers must not be able to hide it in a result.
    if set(snapshot) - {"protocol", "protocol_version", "alias", "model_id", "buckets", "observed_at", "provenance"}:
        raise AdmissionError("unknown snapshot field")
    if "protocol" in snapshot and snapshot["protocol"] != PROTOCOL:
        raise AdmissionError("wrong AGY bucket protocol")
    if "protocol_version" in snapshot and snapshot["protocol_version"] != 1:
        raise AdmissionError("wrong AGY bucket protocol version")
    try:
        alias, model_id, availability, digest = _validate_snapshot(snapshot, now, max_age)
        buckets = snapshot["buckets"]
        if not model_id.startswith("gemini-"):
            mapping = (model_bucket_map or {}).get(model_id)
            if not mapping or len(mapping) != 2 or tuple(mapping) != ("3p-weekly", "3p-5h") or set(buckets) != set(mapping):
                availability = "blocked"
            else:
                availability = "available" if all(_finite_fraction(buckets[k]["remaining_fraction"]) > 0 and not buckets[k]["disabled"] for k in mapping) else "blocked"
        return {"alias": alias, "model_id": model_id, "availability": availability, "observed_at": snapshot["observed_at"], "observation_digest": digest, "provenance_digest": digest}
    except AdmissionError:
        return {"alias": str(snapshot.get("alias", "invalid")) if isinstance(snapshot, Mapping) else "invalid", "model_id": "invalid", "availability": "blocked", "observed_at": "invalid", "provenance_digest": domain_digest("agy.bucket.invalid.v1", "invalid")}


def retained_availability(snapshot: Mapping[str, Any], *, now: datetime, max_age: timedelta = timedelta(minutes=30)) -> dict[str, str]:
    result = admit_bucket_snapshot(snapshot, now=now, max_age=max_age)
    return {"digest": domain_digest("agy.bucket.retained.v1", result), "availability": result["availability"], "freshness": "fresh" if result["availability"] != "blocked" else "stale-or-invalid", "provenance": result["provenance_digest"]}


def _request(request: Mapping[str, Any]) -> tuple[str, str, str, str]:
    if set(request) - {"protocol", "protocol_version", "alias", "model_id", "bucket_availability", "receipt_binding", "safe_input"}:
        raise AdmissionError("unknown request field")
    if request.get("protocol") != "receipt-v3" or request.get("protocol_version") != 3:
        raise AdmissionError("wrong protocol")
    alias = request.get("alias")
    model = _safe(request.get("model_id"), "model_id")
    if alias not in _ALIASES or request.get("bucket_availability") != "available":
        raise AdmissionError("bucket admission is not available")
    binding = _mapping(request.get("receipt_binding"), "receipt_binding")
    required_binding = {"protocol", "request_id", "alias", "model_id", "nonce", "artifact_digest", "policy_digest", "observation_digest", "bucket_binding", "decision", "scheduling_snapshot_sha256", "provider_native_result_digest", "work_result_digest"}
    if set(binding) != required_binding:
        raise AdmissionError("unknown receipt binding field")
    if binding.get("protocol") != "receipt-v3":
        raise AdmissionError("receipt-v3 binding required")
    request_id = _safe(binding.get("request_id"), "request_id")
    if not re.fullmatch(r"(?:r|req|request)-[A-Za-z0-9_.:-]+", request_id):
        raise AdmissionError("invalid request_id binding")
    nonce = _safe(binding.get("nonce"), "nonce")
    if len(nonce) < 8:
        raise AdmissionError("nonce is too short")
    if binding["alias"] != alias or binding["model_id"] != model:
        raise AdmissionError("request identity binding mismatch")
    for field in ("artifact_digest", "policy_digest", "observation_digest", "scheduling_snapshot_sha256", "provider_native_result_digest", "work_result_digest"):
        if not isinstance(binding[field], str) or not _DIGEST.fullmatch(binding[field]):
            raise AdmissionError(f"invalid {field}")
    if binding["decision"] not in {"admit", "block"} or binding["decision"] != "admit":
        raise AdmissionError("invalid admission decision")
    buckets = binding["bucket_binding"]
    if not isinstance(buckets, list) or tuple(buckets) not in _BUCKET_BINDINGS:
        raise AdmissionError("invalid bucket binding")
    safe_input = request.get("safe_input", {})
    safe_input = _mapping(safe_input, "safe_input")
    forbidden = {"raw_output", "response_text", "credential", "path", "account", "signals", "synthetic_buckets", "concurrency", "entitlement", "limit", "spend", "usedPercent", "remainingPercent", "reached", "totals", "reset_calculation"}
    if set(safe_input) & forbidden:
        raise AdmissionError("forbidden derived or raw field")
    for key, val in safe_input.items():
        if not isinstance(val, str) or not _DIGEST.fullmatch(val) or not key.endswith("digest"):
            raise AdmissionError("safe_input contains non-digest data")
    return alias, model, request_id, nonce


def consume_nonce(nonce: str, store: str | os.PathLike[str] | None) -> None:
    nonce = _safe(nonce, "nonce")
    if store is None:
        if nonce in _USED_NONCES:
            raise AdmissionError("nonce replay")
        _USED_NONCES.add(nonce)
        return
    directory = Path(store)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / hashlib.sha256(nonce.encode("ascii")).hexdigest()
    try:
        fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
    except FileExistsError as exc:
        raise AdmissionError("nonce replay") from exc


def admit_before_spawn(request: Mapping[str, Any], *, nonce_store: str | os.PathLike[str] | None, runner: Callable[[], Any]) -> Any:
    alias, model, request_id, nonce = _request(_mapping(request, "request"))
    consume_nonce(nonce, nonce_store)
    result = runner()
    return {"alias": alias, "model_id": model, "request_id": request_id, "availability": "available", "provider_result_digest": domain_digest("agy.provider.result.v1", result)}


def admit_and_dispatch(request: Mapping[str, Any], *, nonce_store: str | os.PathLike[str] | None, provider_runner: Callable[[], Any], dispatcher: Callable[[], Any]) -> dict[str, str]:
    result = admit_before_spawn(request, nonce_store=nonce_store, runner=provider_runner)
    dispatcher()
    return {"alias": result["alias"], "model_id": result["model_id"], "request_id": result["request_id"], "availability": "available", "provider_result_digest": result["provider_result_digest"]}
