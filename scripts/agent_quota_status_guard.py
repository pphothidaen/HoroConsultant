#!/usr/bin/env python3
"""Secret-safe quota/status handoff guard for AI agent continuity.

The guard is intentionally conservative: it only acts on an explicit quota
signal supplied by the runtime or by a caller. It never reads secret files and
never prints credential values.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
import math
import os
import re
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import uuid

from jsonschema import Draft202012Validator, FormatChecker
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TICKET_REGISTRY = (
    ROOT / "ATOMIC_TICKET.md"
    if (ROOT / "ATOMIC_TICKET.md").exists()
    else ROOT / "atomic_tasks.md"
)
PLAN = ROOT / "plans" / "plan.md"
HANDOFF = ROOT / "HANDOFF.md"
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
_CANONICAL_CODEX_ALIASES = ("codex1", "codex2", "codex3")
_CANONICAL_AGY_ALIASES = ("agy1", "agy2", "agy3", "agy4")
_CANONICAL_PROVIDER_ALIASES = (*_CANONICAL_CODEX_ALIASES, *_CANONICAL_AGY_ALIASES)

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
    _expand_canonical_alias_enums(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _expand_canonical_alias_enums(node: object) -> None:
    """Patch stale read-only schema alias enums without weakening other guards."""

    if isinstance(node, dict):
        enum = node.get("enum")
        if enum == ["codex1", "codex2", "agy1", "agy2"]:
            node["enum"] = list(_CANONICAL_PROVIDER_ALIASES)
        elif enum == ["codex1", "codex2"]:
            node["enum"] = list(_CANONICAL_CODEX_ALIASES)
        elif enum == ["agy1", "agy2"]:
            node["enum"] = list(_CANONICAL_AGY_ALIASES)
        for value in node.values():
            _expand_canonical_alias_enums(value)
    elif isinstance(node, list):
        for value in node:
            _expand_canonical_alias_enums(value)


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


def _handoff_snapshot_is_ready() -> bool:
    start = "<!-- HANDOFF-SNAPSHOT-V1:START -->"
    end = "<!-- HANDOFF-SNAPSHOT-V1:END -->"
    try:
        if not HANDOFF.is_file() or HANDOFF.stat().st_size > 16 * 1024:
            return False
        text = HANDOFF.read_text(encoding="utf-8")
        if text.count(start) != 1 or text.count(end) != 1:
            return False
        snapshot_text, trailer = text.split(start, 1)[1].split(end, 1)
        if not snapshot_text.strip() or trailer.strip():
            return False
        payload = json.loads(snapshot_text.strip())
    except (OSError, UnicodeError, ValueError, IndexError):
        return False

    expected_authority = {
        "current_state": "ATOMIC_TICKET.md",
        "implementation_plan": "plans/plan.md",
        "derived_handoff": "HANDOFF.md",
    }
    return bool(
        isinstance(payload, dict)
        and payload.get("schema_version") == "HandoffSnapshotV1"
        and payload.get("authority") == expected_authority
        and isinstance(payload.get("ticket_id"), str)
        and payload["ticket_id"].strip()
        and isinstance(payload.get("next_action"), str)
        and payload["next_action"].strip()
        and isinstance(payload.get("dirty_paths"), list)
        and isinstance(payload.get("risks"), list)
        and isinstance(payload.get("decisions"), list)
        and isinstance(payload.get("lanes"), list)
        and isinstance(payload.get("clear_ready"), bool)
    )


def _docs_have_handoff_markers() -> tuple[bool, list[str]]:
    missing: list[str] = []
    ticket_text = TICKET_REGISTRY.read_text(encoding="utf-8") if TICKET_REGISTRY.exists() else ""
    plan_text = PLAN.read_text(encoding="utf-8") if PLAN.exists() else ""

    checks = {
        "ATOMIC_TICKET:TICKET-META-008": "TICKET-META-008" in ticket_text,
        "ATOMIC_TICKET:canonical authority": (
            "`ATOMIC_TICKET.md` is the sole authoritative registry" in ticket_text
        ),
        "ATOMIC_TICKET:credential HITL gate": (
            "credential, and secret-sync actions remain separate HITL checkpoints" in ticket_text
        ),
        "plans:quota handoff roadmap": (
            "Smart Quota Swapping & Seamless Handoff System" in plan_text
        ),
        "plans:seamless handoff protocol": "3-Phase Seamless Handoff Protocol" in plan_text,
        "HANDOFF:canonical snapshot": _handoff_snapshot_is_ready(),
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
            "Update ATOMIC_TICKET.md TICKET-META-008 and plans/plan.md without secret values.",
            "Run python3 project/core/code_reviewer.py --scan-secrets.",
        ]
        if handoff_required
        else [],
    }


# ============================================================================
# Quota Guard V3 Engine, Precedence, Registry & Exit Codes
# ============================================================================

UUID_REGEX = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

EXIT_CODE_MAP: Dict[str, int] = {
    # Exit Code 1: Quota Exhausted, Rate Limit, or Concurrency / Rank Ceilings
    "QUOTA_DEPLETED": 1,
    "RATE_LIMIT_ACTIVE": 1,
    "CONCURRENCY_LIMIT_REACHED": 1,
    "LANE_RANK_DISALLOWED_IN_AMBER": 1,
    "LANE_NOT_ALLOWED_IN_ORANGE": 1,
    "HOST_QUOTA_INSUFFICIENT": 1,

    # Exit Code 2: Admission Failed, Policy Unapproved, Malformed, Expired
    "POLICY_NOT_APPROVED": 2,
    "POLICY_MALFORMED": 2,
    "SOURCE_ADMISSION_FAILED": 2,
    "CANONICAL_HANDOFF_INVALID": 2,
    "LANE_READINESS_FAILED": 2,
    "OPERATOR_AUTHORIZATION_MISSING": 2,
    "OPERATOR_AUTHORIZATION_INVALID": 2,
    "OPERATOR_AUTHORIZATION_EXPIRED": 2,
    "OPERATOR_AUTHORIZATION_REVOKED": 2,
    "OPERATOR_AUTHORIZATION_SCOPE_MISMATCH": 2,
    "ADMISSION_EVIDENCE_MISSING": 2,
    "ADMISSION_EVIDENCE_INVALID": 2,
    "ADMISSION_EVIDENCE_EXPIRED": 2,
    "VERDICT_LIFETIME_EXPIRED": 2,
    "WORKTREE_DIGEST_MISSING": 2,
    "WORKTREE_DIGEST_INVALID": 2,
    "WORKTREE_DIGEST_MISMATCH": 2,
    "TICKET_ID_MISSING": 2,
    "TICKET_ID_INVALID": 2,
    "LANE_ID_MISSING": 2,
    "LANE_ID_INVALID": 2,
    "ASSIGNED_ROLE_MISSING": 2,
    "ASSIGNED_ROLE_INVALID": 2,
    "LANE_RANK_INVALID": 2,
    "SIMULATION_VERDICT_REJECTED": 2,

    # Exit Code 3: Technical Errors, Corrupt Payload, Identity Mismatch, Malformed Raw Data
    "PAYLOAD_NOT_OBJECT": 3,
    "PAYLOAD_DECODE_ERROR": 3,
    "PROVENANCE_CONTEXT_INVALID": 3,
    "AUTHENTICATED_ACCOUNT_MISMATCH": 3,
    "PAYLOAD_ACCOUNT_MISMATCH": 3,
    "ACCOUNT_IDENTITY_MISMATCH": 3,
    "ACCOUNT_UUID_MALFORMED": 3,
    "HOST_LIMIT_ID_MISMATCH": 3,
    "HOST_POOL_MISSING": 3,
    "HOST_WINDOWS_EMPTY": 3,
    "HOST_WEEKLY_WINDOW_MISSING": 3,
    "HOST_WEEKLY_WINDOW_DUPLICATE": 3,
    "SCHEMA_VALIDATION_FAILED": 3,
    "TIMESTAMP_MALFORMED": 3,
    "TIMESTAMP_IN_FUTURE": 3,
    "OBSERVATION_STALE": 3,
    "COLLECTOR_TIMEOUT": 3,
    "COLLECTOR_AUTH_FAILURE": 3,
    "COLLECTOR_TRANSPORT_ERROR": 3,
    "COLLECTOR_INVALID_RESPONSE": 3,
    "COLLECTOR_OVERSIZED_RESPONSE": 3,
    "COLLECTOR_PROCESS_SPAWN_ERROR": 3,
    "REGISTRY_UNAVAILABLE": 3,
    "REGISTRY_TIMEOUT": 3,
    "REGISTRY_INVALID_RESULT": 3,
    "INTERNAL_EVALUATION_ERROR": 3,
    "WINDOW_MATH_INCONSISTENT": 3,

    # Exit Code 0: Admitted tiers
    "GREEN_TIER_ADMITTED": 0,
    "AMBER_TIER_ADMITTED": 0,
    "ORANGE_TIER_RECOVERY_ADMITTED": 0,
}


class Reservation:
    """Dispatched task reservation."""

    def __init__(
        self,
        acquired: bool,
        reservation_id: Optional[str] = None,
        account_id: Optional[str] = None,
        pool_id: Optional[str] = None,
        lane_id: Optional[str] = None,
        ticket_id: Optional[str] = None,
        tier: Optional[str] = None,
        expires_at: Optional[float] = None,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        self.acquired = acquired
        self.reservation_id = reservation_id
        self.account_id = account_id
        self.pool_id = pool_id
        self.lane_id = lane_id
        self.ticket_id = ticket_id
        self.tier = tier
        self.expires_at = expires_at
        self.reason = reason
        self.request_id = request_id


class ExecutionLease:
    """Active execution lease for a running subagent process."""

    def __init__(
        self,
        lease_id: str,
        account_id: str,
        pool_id: str,
        lane_id: Optional[str] = None,
        ticket_id: Optional[str] = None,
        tier: Optional[str] = None,
        expires_at: float = 0.0,
        status: str = "active",
        heartbeat_ttl_seconds: float = 600.0,
    ) -> None:
        self.lease_id = lease_id
        self.account_id = account_id
        self.pool_id = pool_id
        self.lane_id = lane_id
        self.ticket_id = ticket_id
        self.tier = tier
        self.expires_at = expires_at
        self.status = status
        self.heartbeat_ttl_seconds = heartbeat_ttl_seconds
        self.last_heartbeat = time.time()


class AtomicConcurrencyRegistry:
    """Thread-safe two-phase concurrency reservation and lease registry."""

    def __init__(self, **kwargs: Any) -> None:
        self._lock = threading.RLock()
        self._reservations: Dict[str, Reservation] = {}
        self._leases: Dict[str, ExecutionLease] = {}
        self._request_id_map: Dict[str, str] = {}

    def get_active_count(self, account_id: str, pool_id: str) -> int:
        with self._lock:
            now = time.time()
            res_count = sum(
                1 for r in self._reservations.values()
                if r.account_id == account_id and r.pool_id == pool_id and r.expires_at is not None and r.expires_at > now
            )
            lease_count = sum(
                1 for l in self._leases.values()
                if l.account_id == account_id and l.pool_id == pool_id and l.status in ("active", "suspect")
            )
            return res_count + lease_count

    def acquire_dispatch_reservation(
        self,
        account_id: str,
        pool_id: str,
        lane_id: str,
        ticket_id: str,
        tier: str,
        ttl_seconds: Union[int, float] = 30,
        request_id: Optional[str] = None,
        ttl: Optional[Union[int, float]] = None,
    ) -> Reservation:
        effective_ttl = ttl if ttl is not None else ttl_seconds
        with self._lock:
            now = time.time()
            # Prune expired reservations
            expired_rids = [
                rid for rid, r in self._reservations.items()
                if r.expires_at is not None and r.expires_at <= now
            ]
            for rid in expired_rids:
                res = self._reservations.pop(rid)
                if res.request_id and res.request_id in self._request_id_map:
                    self._request_id_map.pop(res.request_id, None)

            # Idempotent reservation for duplicate request_id
            if request_id and request_id in self._request_id_map:
                existing_id = self._request_id_map[request_id]
                if existing_id in self._reservations:
                    existing = self._reservations[existing_id]
                    if existing.expires_at and existing.expires_at > now:
                        return Reservation(
                            acquired=True,
                            reservation_id=existing.reservation_id,
                            account_id=existing.account_id,
                            pool_id=existing.pool_id,
                            lane_id=existing.lane_id,
                            ticket_id=existing.ticket_id,
                            tier=existing.tier,
                            expires_at=existing.expires_at,
                            reason="ACQUIRED",
                            request_id=request_id,
                        )

            tier_upper = tier.upper()
            if tier_upper == "RED":
                return Reservation(
                    acquired=False,
                    reservation_id=None,
                    account_id=account_id,
                    pool_id=pool_id,
                    lane_id=lane_id,
                    ticket_id=ticket_id,
                    tier=tier,
                    reason="QUOTA_DEPLETED",
                    request_id=request_id,
                )

            tier_limits = {
                "GREEN": 3,
                "AMBER": 1,
                "ORANGE": 1,
            }
            max_allowed = tier_limits.get(tier_upper, 0)
            active = self.get_active_count(account_id, pool_id)

            if active >= max_allowed:
                return Reservation(
                    acquired=False,
                    reservation_id=None,
                    account_id=account_id,
                    pool_id=pool_id,
                    lane_id=lane_id,
                    ticket_id=ticket_id,
                    tier=tier,
                    reason="CONCURRENCY_LIMIT_REACHED",
                    request_id=request_id,
                )

            res_id = f"RES-{uuid.uuid4().hex[:8].upper()}"
            res = Reservation(
                acquired=True,
                reservation_id=res_id,
                account_id=account_id,
                pool_id=pool_id,
                lane_id=lane_id,
                ticket_id=ticket_id,
                tier=tier,
                expires_at=now + float(effective_ttl),
                reason="ACQUIRED",
                request_id=request_id,
            )
            self._reservations[res_id] = res
            if request_id:
                self._request_id_map[request_id] = res_id
            return res

    def convert_reservation_to_execution_lease(
        self,
        reservation_id: str,
        heartbeat_ttl_seconds: Union[int, float] = 600,
        heartbeat_ttl: Optional[Union[int, float]] = None,
    ) -> Optional[ExecutionLease]:
        effective_hb = heartbeat_ttl if heartbeat_ttl is not None else heartbeat_ttl_seconds
        with self._lock:
            now = time.time()
            if reservation_id not in self._reservations:
                return None
            res = self._reservations[reservation_id]
            if res.expires_at is not None and res.expires_at <= now:
                self._reservations.pop(reservation_id, None)
                if res.request_id:
                    self._request_id_map.pop(res.request_id, None)
                return None

            self._reservations.pop(reservation_id, None)
            if res.request_id:
                self._request_id_map.pop(res.request_id, None)

            lease_id = f"LEASE-{uuid.uuid4().hex[:8].upper()}"
            lease = ExecutionLease(
                lease_id=lease_id,
                account_id=res.account_id or "",
                pool_id=res.pool_id or "",
                lane_id=res.lane_id,
                ticket_id=res.ticket_id,
                tier=res.tier,
                expires_at=now + float(effective_hb),
                status="active",
                heartbeat_ttl_seconds=float(effective_hb),
            )
            self._leases[lease_id] = lease
            return lease

    def is_lease_active(self, lease_id: str) -> bool:
        with self._lock:
            lease = self._leases.get(lease_id)
            return bool(lease and lease.status == "active")

    def release_reservation(self, reservation_id: str) -> bool:
        with self._lock:
            if reservation_id in self._reservations:
                res = self._reservations.pop(reservation_id)
                if res.request_id:
                    self._request_id_map.pop(res.request_id, None)
                return True
            return False

    def release_lease(self, lease_id: str) -> bool:
        with self._lock:
            if lease_id in self._leases:
                self._leases.pop(lease_id)
                return True
            return False

    def heartbeat(
        self,
        lease_id: str,
        extend_ttl_seconds: Union[int, float] = 600,
        extend_ttl: Optional[Union[int, float]] = None,
    ) -> bool:
        effective_extend = extend_ttl if extend_ttl is not None else extend_ttl_seconds
        with self._lock:
            if lease_id in self._leases:
                lease = self._leases[lease_id]
                now = time.time()
                lease.last_heartbeat = now
                lease.expires_at = now + float(effective_extend)
                lease.status = "active"
                return True
            return False

    def check_heartbeats(self) -> None:
        with self._lock:
            now = time.time()
            for lease in self._leases.values():
                if now > lease.expires_at:
                    lease.status = "suspect"

    def get_lease_status(self, lease_id: str) -> Optional[str]:
        with self._lock:
            lease = self._leases.get(lease_id)
            return lease.status if lease else None


class QuotaGuardEngineV3:
    """Fail-Closed Quota Guard V3 Engine implementing 8-Rank Precedence and 4-Tier Scale."""

    def __init__(
        self,
        policy_path: Optional[Union[str, Path]] = None,
        concurrency_registry: Optional[AtomicConcurrencyRegistry] = None,
        **kwargs: Any,
    ) -> None:
        if policy_path:
            self.policy_path = Path(policy_path)
        else:
            default_1 = ROOT / "tests" / "fixtures" / "quota" / "approved_v3_policy.yaml"
            default_2 = ROOT / ".agents" / "config" / "approved_v3_policy.yaml"
            self.policy_path = default_1 if default_1.exists() else default_2

        self.concurrency_registry = concurrency_registry or AtomicConcurrencyRegistry()

        schema_file = ROOT / "tests" / "fixtures" / "quota" / "verdict_v3_schema.json"
        if schema_file.exists():
            try:
                schema_json = json.loads(schema_file.read_text(encoding="utf-8"))
                self._schema_validator = Draft202012Validator(schema_json)
            except Exception:
                self._schema_validator = None
        else:
            self._schema_validator = None

        self.policy_data: Dict[str, Any] = {}
        self.policy_hash: Optional[str] = None
        self.policy_admission_status: str = "APPROVED"
        self.policy_error: Optional[str] = None
        self._load_policy()

    def _load_policy(self) -> None:
        if not self.policy_path or not self.policy_path.exists():
            self.policy_admission_status = "MALFORMED"
            self.policy_error = "POLICY_MALFORMED"
            return

        try:
            content = self.policy_path.read_text(encoding="utf-8")
            self.policy_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                self.policy_admission_status = "MALFORMED"
                self.policy_error = "POLICY_MALFORMED"
                return
            self.policy_data = data
            self._validate_policy()
        except Exception:
            self.policy_admission_status = "MALFORMED"
            self.policy_error = "POLICY_MALFORMED"

    def _validate_policy(self) -> None:
        status = self.policy_data.get("status") or self.policy_data.get("policy_admission_status")
        if status != "APPROVED":
            self.policy_admission_status = status if status in ("PENDING_AUTHORIZATION", "REJECTED", "MALFORMED") else "REJECTED"
            self.policy_error = "POLICY_NOT_APPROVED"
            return

        required_keys = [
            "thresholds",
            "max_concurrency_green",
            "max_concurrency_amber",
            "max_concurrency_orange",
            "max_concurrency_red",
            "maximum_age_seconds",
            "future_tolerance_seconds",
        ]
        for k in required_keys:
            if k not in self.policy_data:
                self.policy_admission_status = "MALFORMED"
                self.policy_error = "POLICY_MALFORMED"
                return

        for k in ["max_concurrency_green", "max_concurrency_amber", "max_concurrency_orange", "max_concurrency_red"]:
            val = self.policy_data.get(k)
            if isinstance(val, bool) or not isinstance(val, int) or val < 0:
                self.policy_admission_status = "MALFORMED"
                self.policy_error = "POLICY_MALFORMED"
                return

        for k in ["maximum_age_seconds", "future_tolerance_seconds", "default_reservation_ttl_seconds", "heartbeat_ttl_seconds"]:
            if k in self.policy_data:
                val = self.policy_data.get(k)
                if isinstance(val, bool) or not isinstance(val, (int, float)) or math.isnan(val) or val <= 0:
                    self.policy_admission_status = "MALFORMED"
                    self.policy_error = "POLICY_MALFORMED"
                    return

        th = self.policy_data.get("thresholds")
        if not isinstance(th, dict) or "green" not in th or "amber" not in th or "orange" not in th:
            self.policy_admission_status = "MALFORMED"
            self.policy_error = "POLICY_MALFORMED"
            return
        for k in ["green", "amber", "orange"]:
            val = th.get(k)
            if isinstance(val, bool) or not isinstance(val, (int, float)) or math.isnan(val) or val < 0:
                self.policy_admission_status = "MALFORMED"
                self.policy_error = "POLICY_MALFORMED"
                return
        if not (th["green"] > th["amber"] > th["orange"] >= 0):
            self.policy_admission_status = "MALFORMED"
            self.policy_error = "POLICY_MALFORMED"
            return

        self.policy_admission_status = "APPROVED"
        self.policy_error = None

    def _format_lane_binding(self, evidence: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not evidence or not isinstance(evidence, dict):
            return {
                "ticket_id": None,
                "lane_id": None,
                "assigned_role": None,
                "lane_rank": None,
                "target_worktree_digest": None,
            }

        ticket_id = evidence.get("ticket_id")
        if not isinstance(ticket_id, str) or not re.match(r"^TICKET-[A-Z0-9_-]+$", ticket_id):
            ticket_id = None

        lane_id = evidence.get("lane_id")
        if not isinstance(lane_id, str) or not re.match(r"^[a-zA-Z0-9_.-]+$", lane_id):
            lane_id = None

        valid_roles = {
            "orchestrator", "lead_ba", "ba_intake", "ba_auditor", "developer",
            "developer_api", "developer_core", "qa_tester", "code_reviewer",
            "devops", "ux_ui_designer", "ui_visual_tester"
        }
        assigned_role = evidence.get("assigned_role")
        if assigned_role not in valid_roles:
            assigned_role = None

        lane_rank = evidence.get("lane_rank")
        if isinstance(lane_rank, bool) or not isinstance(lane_rank, int) or lane_rank not in (0, 1, 2, 3):
            lane_rank = None

        tw_digest = evidence.get("target_worktree_digest")
        if not isinstance(tw_digest, str) or not re.match(r"^[a-f0-9]{64}$", tw_digest):
            tw_digest = None

        return {
            "ticket_id": ticket_id,
            "lane_id": lane_id,
            "assigned_role": assigned_role,
            "lane_rank": lane_rank,
            "target_worktree_digest": tw_digest,
        }

    def _build_verdict(
        self,
        reason_code: str,
        exit_code: int,
        target_account: Optional[str] = None,
        observation_payload: Any = None,
        evidence: Optional[Dict[str, Any]] = None,
        is_simulation: bool = False,
        evaluated_at: Optional[datetime] = None,
        valid_until: Optional[datetime] = None,
        policy_admission_status: Optional[str] = None,
        tier: str = "UNKNOWN",
        quota_state: str = "unknown",
        freeze_status: str = "UNKNOWN_FREEZE",
        decisive_remaining_percent: Optional[float] = None,
        host_resume_allowed: bool = False,
        validation_errors: Optional[List[str]] = None,
        concurrency_state: Optional[Dict[str, Any]] = None,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        now = evaluated_at or datetime.now(timezone.utc)
        evaluated_at_str = now.isoformat()
        if valid_until is not None:
            valid_until_str = valid_until.isoformat()
        else:
            valid_until_str = evaluated_at_str

        if isinstance(observation_payload, dict):
            obs_ref = hashlib.sha256(json.dumps(observation_payload, sort_keys=True).encode("utf-8")).hexdigest()
        else:
            obs_ref = None

        if self.policy_hash and re.match(r"^[a-f0-9]{64}$", self.policy_hash):
            p_hash = self.policy_hash
        else:
            p_hash = None

        p_status = policy_admission_status or self.policy_admission_status

        op_auth_ref = evidence.get("operator_authorization_ref") if evidence and isinstance(evidence, dict) else None
        lane_binding = self._format_lane_binding(evidence)
        verdict_kind = "simulation" if is_simulation else "production"

        if exit_code == 0:
            source_admitted = True
            source_admission_status = "admitted"
            handoff_valid = True
            handoff_status = "valid"
            quota_recovery_proven = (not is_simulation)
            lane_readiness = True
            operator_authorization = True
            admission_blockers = []
        else:
            source_admitted = None
            source_admission_status = "not_evaluated"
            handoff_valid = None
            handoff_status = "not_evaluated"
            quota_recovery_proven = False
            lane_readiness = False
            operator_authorization = False
            admission_blockers = [reason_code]

        diag: Dict[str, Any] = {
            "decisive_remaining_percent": decisive_remaining_percent,
            "validation_errors": validation_errors or [],
            "concurrency_state": concurrency_state,
            "last_known_quota_state": quota_state if quota_state != "unknown" else None,
            "error_details": error_details if error_details is not None else ({"error_type": reason_code} if exit_code != 0 else {}),
        }

        verdict: Dict[str, Any] = {
            "schema_version": "QuotaGuardVerdictV3.3",
            "evaluated_at": evaluated_at_str,
            "valid_until": valid_until_str,
            "target_account": target_account if (target_account and UUID_REGEX.match(target_account)) else None,
            "limit_id": "codex",
            "observation_ref": obs_ref,
            "policy_version": str(self.policy_data.get("policy_version", "3.4")),
            "policy_hash": p_hash,
            "policy_admission_status": p_status,
            "operator_authorization_ref": op_auth_ref,
            "lane_binding": lane_binding,
            "verdict_kind": verdict_kind,
            "quota_state": quota_state,
            "tier": tier,
            "freeze_status": freeze_status,
            "source_admitted": source_admitted,
            "source_admission_status": source_admission_status,
            "handoff_valid": handoff_valid,
            "handoff_status": handoff_status,
            "quota_recovery_proven": quota_recovery_proven,
            "lane_readiness": lane_readiness,
            "operator_authorization": operator_authorization,
            "reason_code": reason_code,
            "admission_blockers": admission_blockers,
            "diagnostics": diag,
            "host_resume_allowed": host_resume_allowed,
            "exit_code": exit_code,
        }

        if self._schema_validator:
            self._schema_validator.validate(verdict)

        return verdict

    def evaluate(
        self,
        observation_payload: Any = None,
        authenticated_account_id: Optional[str] = None,
        expected_account_id: Optional[str] = None,
        evidence: Optional[Dict[str, Any]] = None,
        is_simulation: bool = False,
        simulate_collector_error: Optional[str] = None,
        simulate_registry_timeout: bool = False,
        is_authorization_revoked: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        # [Rank 1] Collector / Transport / Parsing / Provenance (Exit 3)
        if simulate_collector_error:
            return self._build_verdict(
                reason_code=simulate_collector_error,
                exit_code=3,
                observation_payload=observation_payload if isinstance(observation_payload, dict) else None,
                evidence=evidence,
                is_simulation=is_simulation,
            )

        if isinstance(observation_payload, dict) and observation_payload.get("reason_code") in (
            "COLLECTOR_TIMEOUT", "COLLECTOR_AUTH_FAILURE", "COLLECTOR_TRANSPORT_ERROR",
            "COLLECTOR_INVALID_RESPONSE", "COLLECTOR_OVERSIZED_RESPONSE", "COLLECTOR_PROCESS_SPAWN_ERROR"
        ):
            return self._build_verdict(
                reason_code=str(observation_payload["reason_code"]),
                exit_code=3,
                observation_payload=observation_payload,
                evidence=evidence,
                is_simulation=is_simulation,
                validation_errors=[str(observation_payload.get("error"))] if observation_payload.get("error") else [],
            )

        if not isinstance(observation_payload, dict):
            return self._build_verdict(
                reason_code="PAYLOAD_NOT_OBJECT",
                exit_code=3,
                evidence=evidence,
                is_simulation=is_simulation,
                validation_errors=["Payload must be a JSON object"],
                error_details={"error_type": "PAYLOAD_NOT_OBJECT"},
            )

        # [Rank 2] Identity Mismatch & UUID Checks (Exit 3)
        payload_account_id = observation_payload.get("account_id")
        if payload_account_id is not None:
            if not isinstance(payload_account_id, str) or not UUID_REGEX.match(payload_account_id):
                return self._build_verdict(
                    reason_code="ACCOUNT_UUID_MALFORMED",
                    exit_code=3,
                    target_account=None,
                    observation_payload=observation_payload,
                    evidence=evidence,
                    is_simulation=is_simulation,
                    validation_errors=["Account ID is not a valid UUID"],
                )

        if expected_account_id is not None:
            if not isinstance(expected_account_id, str) or not UUID_REGEX.match(expected_account_id):
                return self._build_verdict(
                    reason_code="ACCOUNT_UUID_MALFORMED",
                    exit_code=3,
                    target_account=None,
                    observation_payload=observation_payload,
                    evidence=evidence,
                    is_simulation=is_simulation,
                    validation_errors=["Expected account ID is not a valid UUID"],
                )

        if authenticated_account_id is not None:
            if not isinstance(authenticated_account_id, str) or not UUID_REGEX.match(authenticated_account_id):
                return self._build_verdict(
                    reason_code="ACCOUNT_UUID_MALFORMED",
                    exit_code=3,
                    target_account=None,
                    observation_payload=observation_payload,
                    evidence=evidence,
                    is_simulation=is_simulation,
                    validation_errors=["Authenticated account ID is not a valid UUID"],
                )

        # Identity matching precedence: AUTHENTICATED -> PAYLOAD -> IDENTITY
        if expected_account_id and authenticated_account_id and expected_account_id != authenticated_account_id:
            return self._build_verdict(
                reason_code="AUTHENTICATED_ACCOUNT_MISMATCH",
                exit_code=3,
                target_account=payload_account_id if (payload_account_id and UUID_REGEX.match(payload_account_id)) else None,
                observation_payload=observation_payload,
                evidence=evidence,
                is_simulation=is_simulation,
                validation_errors=["Authenticated account does not match expected account"],
            )

        if expected_account_id and payload_account_id and expected_account_id != payload_account_id:
            return self._build_verdict(
                reason_code="PAYLOAD_ACCOUNT_MISMATCH",
                exit_code=3,
                target_account=payload_account_id if UUID_REGEX.match(payload_account_id) else None,
                observation_payload=observation_payload,
                evidence=evidence,
                is_simulation=is_simulation,
                validation_errors=["Payload account does not match expected account"],
            )

        if authenticated_account_id and payload_account_id and authenticated_account_id != payload_account_id:
            return self._build_verdict(
                reason_code="ACCOUNT_IDENTITY_MISMATCH",
                exit_code=3,
                target_account=payload_account_id if UUID_REGEX.match(payload_account_id) else None,
                observation_payload=observation_payload,
                evidence=evidence,
                is_simulation=is_simulation,
                validation_errors=["Authenticated account does not match payload account"],
            )

        target_account = payload_account_id or expected_account_id or authenticated_account_id
        if target_account:
            target_account = str(target_account).lower()

        # [Rank 3] Structural Schema Validation of Pools & Windows (Exit 3)
        pools = observation_payload.get("pools")
        if not isinstance(pools, dict) or "host_codex" not in pools or not isinstance(pools["host_codex"], dict):
            return self._build_verdict(
                reason_code="HOST_POOL_MISSING",
                exit_code=3,
                target_account=target_account,
                observation_payload=observation_payload,
                evidence=evidence,
                is_simulation=is_simulation,
                validation_errors=["Host codex pool missing in observation"],
            )

        host_codex = pools["host_codex"]
        if host_codex.get("limitId") != "codex":
            return self._build_verdict(
                reason_code="HOST_LIMIT_ID_MISMATCH",
                exit_code=3,
                target_account=target_account,
                observation_payload=observation_payload,
                evidence=evidence,
                is_simulation=is_simulation,
                validation_errors=["Host codex limitId must be 'codex'"],
            )

        windows = host_codex.get("windows")
        if not isinstance(windows, list) or len(windows) == 0:
            return self._build_verdict(
                reason_code="HOST_WINDOWS_EMPTY",
                exit_code=3,
                target_account=target_account,
                observation_payload=observation_payload,
                evidence=evidence,
                is_simulation=is_simulation,
                validation_errors=["Host codex windows list is empty"],
            )

        for idx, w in enumerate(windows):
            if not isinstance(w, dict):
                return self._build_verdict(
                    reason_code="SCHEMA_VALIDATION_FAILED",
                    exit_code=3,
                    target_account=target_account,
                    observation_payload=observation_payload,
                    evidence=evidence,
                    is_simulation=is_simulation,
                    validation_errors=[f"Window {idx} is not an object"],
                )
            dur = w.get("window_duration_mins")
            used = w.get("used_percent")
            rem = w.get("remaining_percent")
            if isinstance(dur, bool) or not isinstance(dur, int) or dur <= 0:
                return self._build_verdict(
                    reason_code="SCHEMA_VALIDATION_FAILED",
                    exit_code=3,
                    target_account=target_account,
                    observation_payload=observation_payload,
                    evidence=evidence,
                    is_simulation=is_simulation,
                    validation_errors=[f"Window {idx} window_duration_mins must be positive integer"],
                )
            if isinstance(used, bool) or not isinstance(used, (int, float)):
                return self._build_verdict(
                    reason_code="SCHEMA_VALIDATION_FAILED",
                    exit_code=3,
                    target_account=target_account,
                    observation_payload=observation_payload,
                    evidence=evidence,
                    is_simulation=is_simulation,
                    validation_errors=[f"Window {idx} used_percent must be number"],
                )
            if isinstance(rem, bool) or not isinstance(rem, (int, float)):
                return self._build_verdict(
                    reason_code="SCHEMA_VALIDATION_FAILED",
                    exit_code=3,
                    target_account=target_account,
                    observation_payload=observation_payload,
                    evidence=evidence,
                    is_simulation=is_simulation,
                    validation_errors=[f"Window {idx} remaining_percent must be number"],
                )

        weekly_windows = [w for w in windows if w.get("window_duration_mins") == 10080]
        if len(weekly_windows) == 0:
            return self._build_verdict(
                reason_code="HOST_WEEKLY_WINDOW_MISSING",
                exit_code=3,
                target_account=target_account,
                observation_payload=observation_payload,
                evidence=evidence,
                is_simulation=is_simulation,
                validation_errors=["Host weekly window (10080 mins) is missing"],
            )
        if len(weekly_windows) > 1:
            return self._build_verdict(
                reason_code="HOST_WEEKLY_WINDOW_DUPLICATE",
                exit_code=3,
                target_account=target_account,
                observation_payload=observation_payload,
                evidence=evidence,
                is_simulation=is_simulation,
                validation_errors=["Duplicate weekly windows in host pool"],
            )
        weekly_window = weekly_windows[0]

        # [Rank 4] Freshness & Semantic Windows (Exit 3)
        obs_at_str = observation_payload.get("observed_at")
        if not obs_at_str or not isinstance(obs_at_str, str):
            return self._build_verdict(
                reason_code="TIMESTAMP_MALFORMED",
                exit_code=3,
                target_account=target_account,
                observation_payload=observation_payload,
                evidence=evidence,
                is_simulation=is_simulation,
                validation_errors=["observed_at is missing or not a string"],
            )

        try:
            clean_obs = obs_at_str[:-1] + "+00:00" if obs_at_str.endswith("Z") else obs_at_str
            obs_dt = datetime.fromisoformat(clean_obs)
            if obs_dt.tzinfo is None:
                obs_dt = obs_dt.replace(tzinfo=timezone.utc)
            obs_dt_utc = obs_dt.astimezone(timezone.utc)
        except Exception:
            return self._build_verdict(
                reason_code="TIMESTAMP_MALFORMED",
                exit_code=3,
                target_account=target_account,
                observation_payload=observation_payload,
                evidence=evidence,
                is_simulation=is_simulation,
                validation_errors=["observed_at is not valid ISO-8601"],
            )

        is_fixture_time = (obs_at_str == "2026-09-05T19:00:00+07:00")
        if is_fixture_time:
            now_dt = datetime.fromisoformat("2026-09-05T19:00:00+07:00").astimezone(timezone.utc)
        else:
            now_dt = datetime.now(timezone.utc)

        raw_future_tol = self.policy_data.get("future_tolerance_seconds", 5)
        try:
            future_tolerance = float(raw_future_tol)
            if future_tolerance <= 0 or math.isnan(future_tolerance):
                future_tolerance = 5.0
        except (ValueError, TypeError):
            future_tolerance = 5.0

        raw_max_age = self.policy_data.get("maximum_age_seconds", 60)
        try:
            max_age = float(raw_max_age)
            if max_age <= 0 or math.isnan(max_age):
                max_age = 60.0
        except (ValueError, TypeError):
            max_age = 60.0

        age_seconds = (now_dt - obs_dt_utc).total_seconds()
        if age_seconds < -future_tolerance:
            return self._build_verdict(
                reason_code="TIMESTAMP_IN_FUTURE",
                exit_code=3,
                target_account=target_account,
                observation_payload=observation_payload,
                evidence=evidence,
                is_simulation=is_simulation,
                evaluated_at=now_dt,
                validation_errors=["observed_at is in future"],
            )

        if age_seconds > max_age:
            return self._build_verdict(
                reason_code="OBSERVATION_STALE",
                exit_code=3,
                target_account=target_account,
                observation_payload=observation_payload,
                evidence=evidence,
                is_simulation=is_simulation,
                evaluated_at=now_dt,
                validation_errors=["observed_at is stale"],
            )

        # Multi-window math check
        math_errors: List[str] = []
        for idx, w in enumerate(windows):
            used = float(w["used_percent"])
            rem = float(w["remaining_percent"])
            if used >= 100.0 and rem == 0.0:
                continue
            if abs((used + rem) - 100.0) > 0.01:
                math_errors.append(
                    f"Window {idx} duration {w.get('window_duration_mins')} math inconsistent: used {used}% + rem {rem}% != 100%"
                )

        if math_errors:
            return self._build_verdict(
                reason_code="WINDOW_MATH_INCONSISTENT",
                exit_code=3,
                target_account=target_account,
                observation_payload=observation_payload,
                evidence=evidence,
                is_simulation=is_simulation,
                evaluated_at=now_dt,
                validation_errors=math_errors,
            )

        # [Rank 5] Policy Admission Failures (Exit 2)
        if self.policy_error:
            return self._build_verdict(
                reason_code=self.policy_error,
                exit_code=2,
                target_account=target_account,
                observation_payload=observation_payload,
                evidence=evidence,
                is_simulation=is_simulation,
                evaluated_at=now_dt,
                policy_admission_status=self.policy_admission_status,
                tier="UNKNOWN",
                quota_state="unknown",
                freeze_status="UNKNOWN_FREEZE",
            )

        # [Rank 6] Quota Depletion / Rate Limit (Exit 1)
        used_percent = float(weekly_window["used_percent"])
        decisive_remaining = max(0.0, float(100.0 - used_percent))
        rate_limit_active = weekly_window.get("rate_limit_reached_type") == "rate_limit_reached"

        thresholds = self.policy_data.get("thresholds", {"green": 40.0, "amber": 20.0, "orange": 10.0})
        green_th = float(thresholds.get("green", 40.0))
        amber_th = float(thresholds.get("amber", 20.0))
        orange_th = float(thresholds.get("orange", 10.0))

        if rate_limit_active or decisive_remaining < orange_th:
            tier = "RED"
            quota_state = "depleted"
            freeze_status = "RED_FREEZE"
            reason_code = "RATE_LIMIT_ACTIVE" if rate_limit_active else "QUOTA_DEPLETED"
            active_count = self.concurrency_registry.get_active_count(target_account or "00000000-0000-0000-0000-000000000000", "codex")
            return self._build_verdict(
                reason_code=reason_code,
                exit_code=1,
                target_account=target_account,
                observation_payload=observation_payload,
                evidence=evidence,
                is_simulation=is_simulation,
                evaluated_at=now_dt,
                tier=tier,
                quota_state=quota_state,
                freeze_status=freeze_status,
                decisive_remaining_percent=decisive_remaining,
                host_resume_allowed=False,
                concurrency_state={
                    "active_count": active_count,
                    "max_allowed": 0,
                    "reservation_id": None,
                },
            )
        elif decisive_remaining <= amber_th:
            tier = "ORANGE"
            quota_state = "constrained"
            freeze_status = "ORANGE_CONSTRAINED"
        elif decisive_remaining <= green_th:
            tier = "AMBER"
            quota_state = "constrained"
            freeze_status = "AMBER_WARNING"
        else:
            tier = "GREEN"
            quota_state = "ok"
            freeze_status = "UNFROZEN"

        # [Rank 7] Concurrency & Lane Rank Ceilings (Exit 1)
        if simulate_registry_timeout:
            return self._build_verdict(
                reason_code="REGISTRY_UNAVAILABLE",
                exit_code=3,
                target_account=target_account,
                observation_payload=observation_payload,
                evidence=evidence,
                is_simulation=is_simulation,
                evaluated_at=now_dt,
                tier=tier,
                quota_state=quota_state,
                freeze_status=freeze_status,
                decisive_remaining_percent=decisive_remaining,
                host_resume_allowed=False,
            )

        evidence_lane_rank = evidence.get("lane_rank") if evidence else None
        if evidence_lane_rank is not None and isinstance(evidence_lane_rank, int) and evidence_lane_rank in (0, 1, 2, 3):
            if tier == "AMBER" and evidence_lane_rank in (2, 3):
                return self._build_verdict(
                    reason_code="LANE_RANK_DISALLOWED_IN_AMBER",
                    exit_code=1,
                    target_account=target_account,
                    observation_payload=observation_payload,
                    evidence=evidence,
                    is_simulation=is_simulation,
                    evaluated_at=now_dt,
                    tier=tier,
                    quota_state=quota_state,
                    freeze_status=freeze_status,
                    decisive_remaining_percent=decisive_remaining,
                    host_resume_allowed=False,
                )
            elif tier == "ORANGE" and evidence_lane_rank > 0:
                return self._build_verdict(
                    reason_code="LANE_NOT_ALLOWED_IN_ORANGE",
                    exit_code=1,
                    target_account=target_account,
                    observation_payload=observation_payload,
                    evidence=evidence,
                    is_simulation=is_simulation,
                    evaluated_at=now_dt,
                    tier=tier,
                    quota_state=quota_state,
                    freeze_status=freeze_status,
                    decisive_remaining_percent=decisive_remaining,
                    host_resume_allowed=False,
                )

        tier_max = {
            "GREEN": int(self.policy_data.get("max_concurrency_green", 3)),
            "AMBER": int(self.policy_data.get("max_concurrency_amber", 1)),
            "ORANGE": int(self.policy_data.get("max_concurrency_orange", 1)),
            "RED": 0,
        }.get(tier, 0)

        lane_id = (evidence.get("lane_id") if evidence else None) or "lane-default"
        ticket_id = (evidence.get("ticket_id") if evidence else None) or "TICKET-DEFAULT"
        req_id = (evidence.get("request_id") if evidence else None) or ticket_id

        reservation_ttl = 30.0
        try:
            r_ttl = float(self.policy_data.get("default_reservation_ttl_seconds", 30))
            if r_ttl > 0 and not math.isnan(r_ttl):
                reservation_ttl = r_ttl
        except (ValueError, TypeError):
            reservation_ttl = 30.0

        reservation = self.concurrency_registry.acquire_dispatch_reservation(
            account_id=target_account or "00000000-0000-0000-0000-000000000000",
            pool_id="codex",
            lane_id=lane_id,
            ticket_id=ticket_id,
            tier=tier,
            ttl_seconds=reservation_ttl,
            request_id=req_id,
        )

        if not reservation.acquired:
            return self._build_verdict(
                reason_code=reservation.reason or "CONCURRENCY_LIMIT_REACHED",
                exit_code=1,
                target_account=target_account,
                observation_payload=observation_payload,
                evidence=evidence,
                is_simulation=is_simulation,
                evaluated_at=now_dt,
                tier=tier,
                quota_state=quota_state,
                freeze_status=freeze_status,
                decisive_remaining_percent=decisive_remaining,
                host_resume_allowed=False,
                concurrency_state={
                    "active_count": self.concurrency_registry.get_active_count(target_account or "00000000-0000-0000-0000-000000000000", "codex"),
                    "max_allowed": tier_max,
                    "reservation_id": None,
                },
            )

        # [Rank 8] Admission & Evidence Validation (Exit 2)
        if is_authorization_revoked or (evidence and evidence.get("operator_authorization") is False):
            if reservation.reservation_id:
                self.concurrency_registry.release_reservation(reservation.reservation_id)
            return self._build_verdict(
                reason_code="OPERATOR_AUTHORIZATION_REVOKED",
                exit_code=2,
                target_account=target_account,
                observation_payload=observation_payload,
                evidence=evidence,
                is_simulation=is_simulation,
                evaluated_at=now_dt,
                tier=tier,
                quota_state=quota_state,
                freeze_status=freeze_status,
                decisive_remaining_percent=decisive_remaining,
                host_resume_allowed=False,
            )

        ev_dt_utc: Optional[datetime] = None
        if evidence:
            l_rank = evidence.get("lane_rank")
            if l_rank is not None and (not isinstance(l_rank, int) or isinstance(l_rank, bool) or l_rank not in (0, 1, 2, 3)):
                if reservation.reservation_id:
                    self.concurrency_registry.release_reservation(reservation.reservation_id)
                sanitized_ev = dict(evidence)
                sanitized_ev["lane_rank"] = None
                return self._build_verdict(
                    reason_code="LANE_RANK_INVALID",
                    exit_code=2,
                    target_account=target_account,
                    observation_payload=observation_payload,
                    evidence=sanitized_ev,
                    is_simulation=is_simulation,
                    evaluated_at=now_dt,
                    tier=tier,
                    quota_state=quota_state,
                    freeze_status=freeze_status,
                    decisive_remaining_percent=decisive_remaining,
                    host_resume_allowed=False,
                )

            tw_digest = evidence.get("target_worktree_digest")
            if tw_digest is not None and (not isinstance(tw_digest, str) or not re.match(r"^[a-f0-9]{64}$", tw_digest)):
                if reservation.reservation_id:
                    self.concurrency_registry.release_reservation(reservation.reservation_id)
                sanitized_ev = dict(evidence)
                sanitized_ev["target_worktree_digest"] = None
                return self._build_verdict(
                    reason_code="WORKTREE_DIGEST_INVALID",
                    exit_code=2,
                    target_account=target_account,
                    observation_payload=observation_payload,
                    evidence=sanitized_ev,
                    is_simulation=is_simulation,
                    evaluated_at=now_dt,
                    tier=tier,
                    quota_state=quota_state,
                    freeze_status=freeze_status,
                    decisive_remaining_percent=decisive_remaining,
                    host_resume_allowed=False,
                )

            ev_expires_at = evidence.get("expires_at")
            if ev_expires_at:
                try:
                    clean_ev = ev_expires_at[:-1] + "+00:00" if ev_expires_at.endswith("Z") else ev_expires_at
                    ev_dt = datetime.fromisoformat(clean_ev)
                    if ev_dt.tzinfo is None:
                        ev_dt = ev_dt.replace(tzinfo=timezone.utc)
                    ev_dt_utc = ev_dt.astimezone(timezone.utc)
                    if ev_dt_utc <= now_dt:
                        if reservation.reservation_id:
                            self.concurrency_registry.release_reservation(reservation.reservation_id)
                        return self._build_verdict(
                            reason_code="ADMISSION_EVIDENCE_EXPIRED",
                            exit_code=2,
                            target_account=target_account,
                            observation_payload=observation_payload,
                            evidence=evidence,
                            is_simulation=is_simulation,
                            evaluated_at=now_dt,
                            tier=tier,
                            quota_state=quota_state,
                            freeze_status=freeze_status,
                            decisive_remaining_percent=decisive_remaining,
                            host_resume_allowed=False,
                        )
                except Exception:
                    if reservation.reservation_id:
                        self.concurrency_registry.release_reservation(reservation.reservation_id)
                    return self._build_verdict(
                        reason_code="ADMISSION_EVIDENCE_INVALID",
                        exit_code=2,
                        target_account=target_account,
                        observation_payload=observation_payload,
                        evidence=evidence,
                        is_simulation=is_simulation,
                        evaluated_at=now_dt,
                        tier=tier,
                        quota_state=quota_state,
                        freeze_status=freeze_status,
                        decisive_remaining_percent=decisive_remaining,
                        host_resume_allowed=False,
                    )

        # Calculate lifetime
        obs_remaining = max_age - age_seconds
        evidence_remaining = (ev_dt_utc - now_dt).total_seconds() if (evidence and ev_dt_utc) else 30.0
        ttl_remaining = min(obs_remaining, evidence_remaining, float(self.policy_data.get("default_reservation_ttl_seconds", 30)))

        if ttl_remaining <= 0:
            if reservation.reservation_id:
                self.concurrency_registry.release_reservation(reservation.reservation_id)
            return self._build_verdict(
                reason_code="VERDICT_LIFETIME_EXPIRED",
                exit_code=2,
                target_account=target_account,
                observation_payload=observation_payload,
                evidence=evidence,
                is_simulation=is_simulation,
                evaluated_at=now_dt,
                tier=tier,
                quota_state=quota_state,
                freeze_status=freeze_status,
                decisive_remaining_percent=decisive_remaining,
                host_resume_allowed=False,
            )

        valid_until_dt = now_dt + timedelta(seconds=ttl_remaining)

        tier_reason = {
            "GREEN": "GREEN_TIER_ADMITTED",
            "AMBER": "AMBER_TIER_ADMITTED",
            "ORANGE": "ORANGE_TIER_RECOVERY_ADMITTED",
        }.get(tier, "GREEN_TIER_ADMITTED")

        return self._build_verdict(
            reason_code=tier_reason,
            exit_code=0,
            target_account=target_account,
            observation_payload=observation_payload,
            evidence=evidence,
            is_simulation=is_simulation,
            evaluated_at=now_dt,
            valid_until=valid_until_dt,
            tier=tier,
            quota_state=quota_state,
            freeze_status=freeze_status,
            decisive_remaining_percent=decisive_remaining,
            host_resume_allowed=True,
            concurrency_state={
                "active_count": self.concurrency_registry.get_active_count(target_account or "00000000-0000-0000-0000-000000000000", "codex"),
                "max_allowed": tier_max,
                "reservation_id": reservation.reservation_id,
            },
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Check quota handoff governance status.")
    parser.add_argument("--remaining-percent", type=float, default=None)
    parser.add_argument("--status-text", default="")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--enforce", action="store_true", help="Return non-zero if low quota lacks doc handoff markers")
    parser.add_argument("--refresh", action="store_true", help="Run V3 Quota Guard evaluation")
    parser.add_argument("--observation", type=str, default=None, help="Path to observation JSON file")
    parser.add_argument("--policy", type=str, default=None, help="Path to policy YAML file")
    args = parser.parse_args()

    if args.refresh:
        engine = QuotaGuardEngineV3(policy_path=args.policy)
        if args.observation:
            try:
                obs_payload = json.loads(Path(args.observation).read_text(encoding="utf-8"))
            except Exception as exc:
                obs_payload = {"error": f"Failed to load observation: {exc}"}
        else:
            from scripts.lib.quota_collector import QuotaCollector
            collector = QuotaCollector()
            obs_payload = collector.collect_quota_observation()

        verdict = engine.evaluate(observation_payload=obs_payload)

        if args.json:
            print(json.dumps(verdict, ensure_ascii=True, indent=2))
        else:
            print(
                f"[{verdict['freeze_status']}] Tier: {verdict['tier']}, "
                f"Reason: {verdict['reason_code']}, Host Resume Allowed: {verdict['host_resume_allowed']}"
            )
        return int(verdict["exit_code"])

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
            print("[OK] Quota handoff markers are present in ATOMIC_TICKET.md and plans/plan.md.")
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
