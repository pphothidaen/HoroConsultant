#!/usr/bin/env python3
"""Secret-safe quota/status handoff guard for AI agent continuity.

The guard is intentionally conservative: it only acts on an explicit quota
signal supplied by the runtime or by a caller. It never reads secret files and
never prints credential values.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
import yaml

ROOT = Path(__file__).resolve().parents[1]
PROJECT_TASKS = ROOT / "PROJECT_TASKS.md"
PLAN = ROOT / "plans" / "plan.md"
DEFAULT_THRESHOLD = 10.0
POLICY_PATH = ROOT / ".agents" / "config" / "multiagent_model_policy.yaml"

_QOBS_POLICY_KEYS = {
    "schema_version",
    "protocol_version",
    "canonicalization_version",
    "observation_schema",
    "artifact_schema",
    "observation_domain",
    "artifact_domain",
    "maximum_age_seconds",
    "future_tolerance_seconds",
    "threshold_percent",
    "executable_decision_schema_versions",
    "receipt_protocol_version",
}
_SIGNAL_NAMES = (
    "usedPercent",
    "remainingPercent",
    "reached",
    "limit",
    "spend",
    "remaining",
)
_SIGNAL_PATHS = tuple(
    (prefix + (name,))
    for prefix in ((), ("buckets", "primary"), ("buckets", "secondary"))
    for name in _SIGNAL_NAMES
)
_CONSISTENCY_ABS_TOLERANCE = 1e-9

QUOTA_ENV_KEYS = (
    "AGENT_QUOTA_REMAINING_PERCENT",
    "AI_AGENT_QUOTA_REMAINING_PERCENT",
    "CODEX_QUOTA_REMAINING_PERCENT",
    "CODEX_REMAINING_QUOTA_PERCENT",
)


class QuotaObservationError(ValueError):
    """Content-free rejection of an invalid quota observation operation."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class _UniqueKeySafeLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(
    loader: _UniqueKeySafeLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[object, object]:
    mapping: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise QuotaObservationError("POLICY_INVALID") from exc
        if duplicate:
            raise QuotaObservationError("POLICY_INVALID")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _reject_duplicate_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise QuotaObservationError("DUPLICATE_KEY_STATUS")
        result[key] = value
    return result


def _reject_non_finite_constant(_: str) -> None:
    raise QuotaObservationError("NON_FINITE_STATUS")


def strict_json_loads(payload: str | bytes | bytearray) -> object:
    """Decode JSON while rejecting duplicate names and non-finite numbers."""

    try:
        return json.loads(
            payload,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_non_finite_constant,
        )
    except QuotaObservationError:
        raise
    except (json.JSONDecodeError, TypeError, UnicodeDecodeError) as exc:
        raise QuotaObservationError("MALFORMED_STATUS") from exc


def canonical_json_bytes(value: object) -> bytes:
    """Return canonical UTF-8 JSON with sorted keys and minimal separators."""

    try:
        encoded = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return encoded.encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise QuotaObservationError("CANONICALIZATION_ERROR") from exc


def sha256_text(value: str) -> str:
    """Return the SHA-256 digest of one UTF-8 string without retaining it."""

    if not isinstance(value, str):
        raise QuotaObservationError("INVALID_CONTEXT")
    try:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
    except UnicodeEncodeError as exc:
        raise QuotaObservationError("INVALID_CONTEXT") from exc


def canonical_sha256(value: object, *, domain: str) -> str:
    """Hash canonical JSON with an unambiguous UTF-8 domain prefix."""

    if not isinstance(domain, str) or not domain:
        raise QuotaObservationError("CANONICALIZATION_ERROR")
    try:
        domain_bytes = domain.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise QuotaObservationError("CANONICALIZATION_ERROR") from exc
    framed = len(domain_bytes).to_bytes(4, "big") + domain_bytes
    return hashlib.sha256(framed + canonical_json_bytes(value)).hexdigest()


def _validate_quota_policy(policy: object) -> dict[str, Any]:
    if not isinstance(policy, dict):
        raise QuotaObservationError("POLICY_INVALID")
    qobs = policy.get("quota_observation")
    if not isinstance(qobs, dict) or set(qobs) != _QOBS_POLICY_KEYS:
        raise QuotaObservationError("POLICY_INVALID")
    expected = {
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
    if qobs != expected or policy.get("policy_version") not in {"2026-08-26.1", "2026-08-26.2", "2026-08-29.1"}:
        raise QuotaObservationError("POLICY_INVALID")
    return policy


def load_quota_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    """Load and validate the locally pinned QOBS policy without external I/O."""

    try:
        loaded = yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueKeySafeLoader)
    except QuotaObservationError:
        raise
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise QuotaObservationError("POLICY_INVALID") from exc
    return _validate_quota_policy(loaded)


def _load_schema(policy_path: Path, relative_path: object) -> dict[str, Any]:
    if not isinstance(relative_path, str):
        raise QuotaObservationError("POLICY_INVALID")
    schema_path = (policy_path.parent / relative_path).resolve()
    try:
        schema = strict_json_loads(schema_path.read_text(encoding="utf-8"))
        if not isinstance(schema, dict):
            raise QuotaObservationError("SCHEMA_INVALID")
        Draft202012Validator.check_schema(schema)
    except QuotaObservationError as exc:
        if exc.code == "SCHEMA_INVALID":
            raise
        raise QuotaObservationError("SCHEMA_INVALID") from exc
    except (OSError, UnicodeError, Exception) as exc:
        # jsonschema uses several exception subclasses across supported releases.
        raise QuotaObservationError("SCHEMA_INVALID") from exc
    return schema


def _schema_validator(
    policy_path: Path,
    policy: dict[str, Any],
    schema_key: str,
) -> Draft202012Validator:
    schema = _load_schema(policy_path, policy["quota_observation"][schema_key])
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _validate_with_schema(
    value: object,
    *,
    policy_path: Path,
    policy: dict[str, Any],
    schema_key: str,
) -> None:
    try:
        errors = list(_schema_validator(policy_path, policy, schema_key).iter_errors(value))
    except QuotaObservationError:
        raise
    except Exception as exc:
        raise QuotaObservationError("SCHEMA_INVALID") from exc
    if errors:
        raise QuotaObservationError("SCHEMA_VALIDATION_FAILED")


def _signal_path_digests() -> list[str]:
    return [sha256_text(".".join(path)) for path in _SIGNAL_PATHS]


def _finite_number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise QuotaObservationError("INVALID_SIGNAL")
    number = float(value)
    if not math.isfinite(number):
        raise QuotaObservationError("INVALID_SIGNAL")
    return number


def _signal_group(signals: dict[str, object], path: tuple[str, ...]) -> dict[str, object]:
    current: object = signals
    for component in path:
        if not isinstance(current, dict) or component not in current:
            raise QuotaObservationError("MISSING_SIGNAL")
        current = current[component]
    if not isinstance(current, dict):
        raise QuotaObservationError("MISSING_SIGNAL")
    if any(name not in current for name in _SIGNAL_NAMES):
        raise QuotaObservationError("MISSING_SIGNAL")
    return current


def _remaining_percent(group: dict[str, object]) -> float:
    used_percent = _finite_number(group["usedPercent"])
    remaining_percent = _finite_number(group["remainingPercent"])
    limit = _finite_number(group["limit"])
    spend = _finite_number(group["spend"])
    remaining = _finite_number(group["remaining"])
    reached = group["reached"]

    if not isinstance(reached, bool):
        raise QuotaObservationError("INVALID_SIGNAL")
    if not 0.0 <= used_percent <= 100.0:
        raise QuotaObservationError("INVALID_SIGNAL")
    if not 0.0 <= remaining_percent <= 100.0:
        raise QuotaObservationError("INVALID_SIGNAL")
    if limit <= 0.0 or spend < 0.0 or remaining < 0.0:
        raise QuotaObservationError("INVALID_SIGNAL")
    if spend > limit or remaining > limit:
        raise QuotaObservationError("INVALID_SIGNAL")

    consistent = (
        math.isclose(
            used_percent + remaining_percent,
            100.0,
            rel_tol=0.0,
            abs_tol=_CONSISTENCY_ABS_TOLERANCE,
        )
        and math.isclose(
            spend + remaining,
            limit,
            rel_tol=0.0,
            abs_tol=_CONSISTENCY_ABS_TOLERANCE,
        )
        and math.isclose(
            used_percent,
            spend / limit * 100.0,
            rel_tol=0.0,
            abs_tol=_CONSISTENCY_ABS_TOLERANCE,
        )
        and math.isclose(
            remaining_percent,
            remaining / limit * 100.0,
            rel_tol=0.0,
            abs_tol=_CONSISTENCY_ABS_TOLERANCE,
        )
        and reached == (remaining == 0.0)
    )
    if not consistent:
        raise QuotaObservationError("CONTRADICTORY_SIGNAL")
    return remaining_percent


def _classify_signals(payload: object, threshold: float) -> tuple[str, str]:
    if not isinstance(payload, dict):
        raise QuotaObservationError("MISSING_SIGNAL")
    percentages = [
        _remaining_percent(_signal_group(payload, path))
        for path in ((), ("buckets", "primary"), ("buckets", "secondary"))
    ]
    quota_band = (
        "below_10_percent" if min(percentages) < threshold else "constrained"
    )
    return quota_band, "signals_consistent"


def _context_observation_fields(context: object) -> dict[str, object]:
    if not isinstance(context, dict):
        raise QuotaObservationError("INVALID_CONTEXT")
    required = {
        "alias",
        "provider",
        "account_home",
        "resolved_executable",
        "ticket_id",
        "attempt_id",
        "policy_version",
        "nonce",
        "observed_at",
    }
    if not required.issubset(context):
        raise QuotaObservationError("INVALID_CONTEXT")
    for key in (
        "alias",
        "provider",
        "account_home",
        "resolved_executable",
        "ticket_id",
        "policy_version",
        "nonce",
        "observed_at",
    ):
        if not isinstance(context[key], str):
            raise QuotaObservationError("INVALID_CONTEXT")
    if isinstance(context["attempt_id"], bool) or not isinstance(
        context["attempt_id"], int
    ):
        raise QuotaObservationError("INVALID_CONTEXT")
    return {
        "alias": context["alias"],
        "provider": context["provider"],
        "account_home_sha256": sha256_text(context["account_home"]),
        "resolved_executable_sha256": sha256_text(context["resolved_executable"]),
        "ticket_id": context["ticket_id"],
        "attempt_id": context["attempt_id"],
        "policy_version": context["policy_version"],
        "nonce": context["nonce"],
        "observed_at": context["observed_at"],
    }


def probe_quota_observation(
    status: object,
    context: dict[str, object],
    *,
    policy_path: Path = POLICY_PATH,
) -> dict[str, object]:
    """Build exactly one content-free QOBS artifact without dispatch or retry."""

    policy = load_quota_policy(policy_path)
    qobs = policy["quota_observation"]
    fields = _context_observation_fields(context)
    reason_code = "signals_consistent"
    quota_band = "unknown"

    try:
        decoded = strict_json_loads(status) if isinstance(
            status, (str, bytes, bytearray)
        ) else status
        quota_band, reason_code = _classify_signals(
            decoded, float(qobs["threshold_percent"])
        )
    except QuotaObservationError as exc:
        reason_code = {
            "MALFORMED_STATUS": "malformed_status",
            "DUPLICATE_KEY_STATUS": "duplicate_key_status",
            "NON_FINITE_STATUS": "non_finite_status",
            "MISSING_SIGNAL": "missing_signal",
            "INVALID_SIGNAL": "invalid_signal",
            "CONTRADICTORY_SIGNAL": "contradictory_signal",
        }.get(exc.code, "invalid_signal")

    observation: dict[str, object] = {
        "schema_version": qobs["schema_version"],
        "protocol_version": qobs["protocol_version"],
        "canonicalization_version": qobs["canonicalization_version"],
        "domain": qobs["observation_domain"],
        **fields,
        "quota_band": quota_band,
        "reason_code": reason_code,
        "signal_path_sha256": _signal_path_digests(),
    }
    artifact: dict[str, object] = {
        "schema_version": qobs["schema_version"],
        "protocol_version": qobs["protocol_version"],
        "canonicalization_version": qobs["canonicalization_version"],
        "domain": qobs["artifact_domain"],
        "observation_sha256": canonical_sha256(
            observation, domain=str(qobs["observation_domain"])
        ),
        "observation": observation,
    }
    _validate_with_schema(
        artifact,
        policy_path=policy_path,
        policy=policy,
        schema_key="artifact_schema",
    )
    return artifact


def quota_artifact_sha256(
    artifact: object,
    *,
    policy_path: Path = POLICY_PATH,
) -> str:
    """Return the pinned domain-separated digest of an exact QOBS artifact."""

    policy = load_quota_policy(policy_path)
    return canonical_sha256(
        artifact, domain=str(policy["quota_observation"]["artifact_domain"])
    )


def _utc_datetime(value: object) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise QuotaObservationError("INVALID_OBSERVED_AT")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise QuotaObservationError("INVALID_OBSERVED_AT") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise QuotaObservationError("INVALID_OBSERVED_AT")
    return parsed


def validate_quota_observation(
    artifact: object,
    expected_context: dict[str, object],
    *,
    now: datetime | None = None,
    policy_path: Path = POLICY_PATH,
) -> dict[str, object]:
    """Validate schema, digest, provenance, policy pins, and freshness."""

    policy = load_quota_policy(policy_path)
    qobs = policy["quota_observation"]
    _validate_with_schema(
        artifact,
        policy_path=policy_path,
        policy=policy,
        schema_key="artifact_schema",
    )
    if not isinstance(artifact, dict) or not isinstance(
        artifact.get("observation"), dict
    ):
        raise QuotaObservationError("SCHEMA_VALIDATION_FAILED")
    observation = artifact["observation"]
    _validate_with_schema(
        observation,
        policy_path=policy_path,
        policy=policy,
        schema_key="observation_schema",
    )

    pinned = {
        "schema_version": qobs["schema_version"],
        "protocol_version": qobs["protocol_version"],
        "canonicalization_version": qobs["canonicalization_version"],
        "domain": qobs["artifact_domain"],
    }
    if any(artifact.get(key) != value for key, value in pinned.items()):
        raise QuotaObservationError("VERSION_MISMATCH")
    observation_pinned = dict(pinned)
    observation_pinned["domain"] = qobs["observation_domain"]
    if any(observation.get(key) != value for key, value in observation_pinned.items()):
        raise QuotaObservationError("VERSION_MISMATCH")
    allowed_policy_versions = {"2026-08-26.1", "2026-08-26.2", "2026-08-29.1"}
    if (
        observation.get("policy_version") not in allowed_policy_versions
        or policy.get("policy_version") not in allowed_policy_versions
    ):
        raise QuotaObservationError("PROVENANCE_MISMATCH")

    expected_digest = canonical_sha256(
        observation, domain=str(qobs["observation_domain"])
    )
    if artifact.get("observation_sha256") != expected_digest:
        raise QuotaObservationError("DIGEST_MISMATCH")

    expected_fields = _context_observation_fields(expected_context)
    if any(observation.get(key) != value for key, value in expected_fields.items()):
        raise QuotaObservationError("PROVENANCE_MISMATCH")
    if observation.get("signal_path_sha256") != _signal_path_digests():
        raise QuotaObservationError("PROVENANCE_MISMATCH")

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise QuotaObservationError("INVALID_OBSERVED_AT")
    current = current.astimezone(timezone.utc)
    observed = _utc_datetime(observation.get("observed_at"))
    age_seconds = (current - observed).total_seconds()
    if age_seconds > float(qobs["maximum_age_seconds"]):
        raise QuotaObservationError("STALE_OBSERVATION")
    if age_seconds < -float(qobs["future_tolerance_seconds"]):
        raise QuotaObservationError("FUTURE_OBSERVATION")
    return observation


def _parse_percent(raw: str | None) -> float | None:
    if raw is None:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*%?", str(raw))
    if not match:
        return None
    value = float(match.group(1))
    if value < 0:
        return None
    return min(value, 100.0)


def _quota_from_env() -> tuple[float | None, str]:
    for key in QUOTA_ENV_KEYS:
        value = _parse_percent(os.getenv(key))
        if value is not None:
            return value, key
    return None, "none"


def _quota_from_status_text(text: str | None) -> float | None:
    if not text:
        return None
    patterns = (
        r"(?:quota|โควต้า)[^\d]{0,40}(\d+(?:\.\d+)?)\s*%",
        r"(\d+(?:\.\d+)?)\s*%[^\n]{0,40}(?:remaining|left|เหลือ)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return _parse_percent(match.group(1))
    return None


def _docs_have_handoff_markers() -> tuple[bool, list[str]]:
    missing: list[str] = []
    project_text = PROJECT_TASKS.read_text(encoding="utf-8") if PROJECT_TASKS.exists() else ""
    plan_text = PLAN.read_text(encoding="utf-8") if PLAN.exists() else ""

    checks = {
        "PROJECT_TASKS:TICKET-META-008": "TICKET-META-008" in project_text,
        "PROJECT_TASKS:safe resume commands": "Safe Resume Commands" in project_text,
        "PROJECT_TASKS:credential status": "GitHub CLI" in project_text and "Doppler CLI" in project_text,
        "plans:quota migration guard": "Quota Exhaustion / Account Migration Guard" in plan_text,
        "plans:account migration continuity": "Account Migration Continuity" in plan_text,
    }
    for name, passed in checks.items():
        if not passed:
            missing.append(name)
    return not missing, missing


def evaluate(
    remaining_percent: float | None,
    source: str,
    threshold: float = DEFAULT_THRESHOLD,
) -> dict[str, Any]:
    docs_ok, missing = _docs_have_handoff_markers()
    signal_present = remaining_percent is not None
    handoff_required = bool(signal_present and remaining_percent < threshold)
    return {
        "signal_present": signal_present,
        "source": source,
        "remaining_percent": remaining_percent,
        "threshold_percent": threshold,
        "handoff_required": handoff_required,
        "docs_ok": docs_ok,
        "missing_markers": missing,
        "recommended_actions": [
            "Run /status or runtime status check.",
            "Summarize current objective, commits, dirty files, verified checks, blockers, and next safe command.",
            "Update PROJECT_TASKS.md TICKET-META-008 and plans/plan.md without secret values.",
            "Run python3 project/core/code_reviewer.py --scan-secrets.",
        ]
        if handoff_required
        else [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check quota handoff governance status.")
    parser.add_argument("--remaining-percent", type=float, default=None)
    parser.add_argument("--status-text", default="")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--enforce", action="store_true", help="Return non-zero if low quota lacks doc handoff markers")
    args = parser.parse_args()

    remaining = args.remaining_percent
    source = "argument"
    if remaining is None:
        remaining = _quota_from_status_text(args.status_text)
        source = "status-text" if remaining is not None else source
    if remaining is None:
        remaining, source = _quota_from_env()

    result = evaluate(remaining, source, args.threshold)

    if args.json:
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    elif not result["signal_present"]:
        print("[OK] Quota guard: no quota signal present; no handoff threshold evaluated.")
    elif result["handoff_required"]:
        print(
            "[WARNING] Quota guard: remaining quota "
            f"{result['remaining_percent']:.1f}% is below {result['threshold_percent']:.1f}%."
        )
        if result["docs_ok"]:
            print("[OK] Quota handoff markers are present in PROJECT_TASKS.md and plans/plan.md.")
        else:
            print("[ERROR] Missing quota handoff markers: " + ", ".join(result["missing_markers"]))
    else:
        print(
            "[OK] Quota guard: remaining quota "
            f"{result['remaining_percent']:.1f}% is above threshold {result['threshold_percent']:.1f}%."
        )

    if args.enforce and result["handoff_required"] and not result["docs_ok"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
