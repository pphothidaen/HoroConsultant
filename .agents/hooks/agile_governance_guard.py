"""Standalone, fail-closed validation for agile lane-governance payloads.

Admission evidence can establish only that a lane may be considered for work.
It is not execution proof and cannot satisfy Definition of Done.  This module
does not inspect a host, contact a provider, or infer any runtime authority.

AGY per-alias cap 3 applies to independent pools with no aggregation. An alias
is unknown until fresh quota proof and isolation proof are supplied.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping


CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "native_lane_capacity.v1.json"
LIFECYCLE = frozenset({"TODO", "READY", "DOING", "BLOCKED", "NEEDS_HITL", "DONE"})
TRANSITIONS = {
    "TODO": frozenset({"READY", "BLOCKED", "NEEDS_HITL"}),
    "READY": frozenset({"DOING", "BLOCKED", "NEEDS_HITL"}),
    "DOING": frozenset({"BLOCKED", "NEEDS_HITL", "DONE"}),
    "BLOCKED": frozenset({"TODO", "NEEDS_HITL"}),
    "NEEDS_HITL": frozenset({"TODO", "BLOCKED"}),
    "DONE": frozenset(),
}
_SENSITIVE_KEY = re.compile(r"(?:credential|password|secret|token|auth)", re.IGNORECASE)
_SENSITIVE_VALUE = re.compile(
    r"(?:authorization\s*:|bearer\s+|api[_-]?key\s*[=:]|secret\s*=|"
    + "key" + "chain" + r")",
    re.IGNORECASE,
)


class AgileGovernanceError(ValueError):
    """Base typed error with a sanitized, machine-readable failure code."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": str(self)}


class AgileGovernanceCapacityError(AgileGovernanceError):
    """Typed capacity exception; fail closed when capacity is not proven."""


@dataclass(frozen=True)
class GovernanceValidationResult:
    """Sanitized result. Admission remains distinct from execution proof."""

    ticket_id: str
    status: str
    admitted: bool
    execution_proven: bool
    native_safety_cap: int
    agy_per_alias_cap: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_capacity_config(path: str | Path = CONFIG_PATH) -> dict[str, Any]:
    """Load and validate closed JSON configuration without external discovery."""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AgileGovernanceError("invalid_config", "capacity configuration is unavailable") from exc
    if not isinstance(raw, dict):
        raise AgileGovernanceError("invalid_config", "capacity configuration must be an object")
    _reject_sensitive(raw)
    if raw.get("schema_version") != "native-lane-capacity-v1":
        raise AgileGovernanceError("invalid_config", "unsupported capacity configuration schema")

    native = _mapping(raw.get("native_platform"), "native_platform")
    observed = _mapping(native.get("runtime_observed"), "runtime_observed")
    observed_cap = _positive_int(observed.get("observed_native_cap"), "observed_native_cap")
    ceiling = _positive_int(native.get("native_observed_ceiling"), "native_observed_ceiling")
    safety_cap = _positive_int(native.get("configurable_safety_cap"), "configurable_safety_cap")
    if ceiling != observed_cap or safety_cap > observed_cap:
        raise AgileGovernanceCapacityError("unsafe_native_cap", "native safety cap exceeds observed ceiling")

    claims = _mapping(raw.get("claims"), "claims")
    if claims.get("theoretical_capacity") != "not proven" or claims.get("provider_capacity") != "not proven":
        raise AgileGovernanceError("invalid_config", "capacity claims must remain not proven")

    agy = _mapping(raw.get("agy"), "agy")
    if _positive_int(agy.get("agy_per_alias_cap"), "agy_per_alias_cap") != 3:
        raise AgileGovernanceCapacityError("invalid_alias_cap", "AGY per-alias cap must be 3")
    return raw


def validate_governance_payload(
    payload: Mapping[str, Any], config: Mapping[str, Any] | None = None
) -> GovernanceValidationResult:
    """Validate lifecycle, ownership, and capacity evidence deterministically."""
    if not isinstance(payload, Mapping):
        raise AgileGovernanceError("invalid_payload", "payload must be an object")
    data = dict(payload)
    _reject_sensitive(data)
    policy = load_capacity_config() if config is None else _validated_config(config)
    ticket_id = _nonempty(data.get("ticket_id"), "ticket_id")
    current = _lifecycle(data.get("current_status"), "current_status")
    target = _lifecycle(data.get("target_status"), "target_status")
    if target not in TRANSITIONS[current]:
        raise AgileGovernanceError("invalid_transition", "strict ticket lifecycle transition rejected")
    if data.get("activity") == "fake_full_capacity_busywork":
        raise AgileGovernanceError("fake_busywork", "no fake full capacity busywork")
    _validate_dependencies(data.get("dependencies", []))
    _validate_editor_ownership(data)
    _validate_ready_and_done(data, target)

    native = _mapping(policy["native_platform"], "native_platform")
    safe_cap = _positive_int(native["configurable_safety_cap"], "configurable_safety_cap")
    active_lanes = _nonnegative_int(data.get("active_native_lanes", 0), "active_native_lanes")
    if active_lanes >= safe_cap:
        raise AgileGovernanceCapacityError("native_capacity_exhausted", "native lane admission not proven")

    admitted = _validate_alias_admission(data, policy)
    execution_proven = bool(data.get("execution_proof", False))
    return GovernanceValidationResult(
        ticket_id=ticket_id,
        status=target,
        admitted=admitted,
        execution_proven=execution_proven,
        native_safety_cap=safe_cap,
        agy_per_alias_cap=3,
    )


def validate_payload(payload: Mapping[str, Any], config: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Compatibility entry point returning a sanitized typed result mapping."""
    return validate_governance_payload(payload, config).as_dict()


def _validated_config(config: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(config, Mapping):
        raise AgileGovernanceError("invalid_config", "capacity configuration must be an object")
    temporary = dict(config)
    _reject_sensitive(temporary)
    # Reuse the exact closed validation logic without accepting external state.
    if temporary.get("schema_version") != "native-lane-capacity-v1":
        raise AgileGovernanceError("invalid_config", "unsupported capacity configuration schema")
    native = _mapping(temporary.get("native_platform"), "native_platform")
    observed = _mapping(native.get("runtime_observed"), "runtime_observed")
    observed_cap = _positive_int(observed.get("observed_native_cap"), "observed_native_cap")
    if _positive_int(native.get("native_observed_ceiling"), "native_observed_ceiling") != observed_cap:
        raise AgileGovernanceCapacityError("unsafe_native_cap", "native observed ceiling mismatch")
    if _positive_int(native.get("configurable_safety_cap"), "configurable_safety_cap") > observed_cap:
        raise AgileGovernanceCapacityError("unsafe_native_cap", "native safety cap exceeds observed ceiling")
    claims = _mapping(temporary.get("claims"), "claims")
    if claims.get("theoretical_capacity") != "not proven" or claims.get("provider_capacity") != "not proven":
        raise AgileGovernanceError("invalid_config", "capacity claims must remain not proven")
    if _positive_int(_mapping(temporary.get("agy"), "agy").get("agy_per_alias_cap"), "agy_per_alias_cap") != 3:
        raise AgileGovernanceCapacityError("invalid_alias_cap", "AGY per-alias cap must be 3")
    return temporary


def _validate_dependencies(value: Any) -> None:
    if not isinstance(value, list):
        raise AgileGovernanceError("invalid_dependencies", "dependency list is required")
    for dependency in value:
        item = _mapping(dependency, "dependency")
        if _lifecycle(item.get("status"), "dependency status") != "DONE":
            raise AgileGovernanceError("dependency_incomplete", "dependency is not done")


def _validate_editor_ownership(data: Mapping[str, Any]) -> None:
    editor = _nonempty(data.get("editor"), "editor")
    resources = data.get("resources")
    owners = _mapping(data.get("resource_owners", {}), "resource_owners")
    if not isinstance(resources, list) or not resources:
        raise AgileGovernanceError("invalid_resources", "one editor per resource requires resources")
    if len(resources) != len(set(resources)):
        raise AgileGovernanceError("resource_conflict", "one editor per resource")
    for resource in resources:
        name = _nonempty(resource, "resource")
        owner = owners.get(name)
        if owner is not None and owner != editor:
            raise AgileGovernanceError("resource_conflict", "one editor per resource")


def _validate_ready_and_done(data: Mapping[str, Any], target: str) -> None:
    if target in {"READY", "DOING"} and data.get("definition_of_ready") is not True:
        raise AgileGovernanceError("definition_of_ready_missing", "Definition of Ready is required")
    if target == "DONE":
        if data.get("definition_of_done") is not True:
            raise AgileGovernanceError("definition_of_done_missing", "Definition of Done is required")
        if data.get("execution_proof") is not True:
            raise AgileGovernanceError("execution_not_proven", "admission is not execution proof")


def _validate_alias_admission(data: Mapping[str, Any], policy: Mapping[str, Any]) -> bool:
    alias = _nonempty(data.get("agy_alias"), "agy_alias")
    counts = _mapping(data.get("active_agy_by_alias", {}), "active_agy_by_alias")
    agy = _mapping(policy["agy"], "agy")
    cap = _positive_int(agy["agy_per_alias_cap"], "agy_per_alias_cap")
    if _nonnegative_int(counts.get(alias, 0), "active_agy_by_alias") >= cap:
        raise AgileGovernanceCapacityError("alias_capacity_exhausted", "AGY per-alias cap reached")
    evidence = _mapping(data.get("admission_evidence"), "admission_evidence")
    alias_evidence = evidence.get(alias)
    if not isinstance(alias_evidence, Mapping):
        raise AgileGovernanceCapacityError(
            "alias_unknown", "alias unknown: fresh quota proof and isolation proof required"
        )
    if alias_evidence.get("fresh_quota_proof") is not True or alias_evidence.get("isolation_proof") is not True:
        raise AgileGovernanceCapacityError("alias_unknown", "alias unknown: fresh quota proof and isolation proof required")
    return True


def _reject_sensitive(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if _SENSITIVE_KEY.search(str(key)):
                raise AgileGovernanceError("unsafe_value", "credential-shaped field rejected")
            _reject_sensitive(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_sensitive(nested)
    elif isinstance(value, str) and _SENSITIVE_VALUE.search(value):
        raise AgileGovernanceError("unsafe_value", "credential-shaped value rejected")


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AgileGovernanceError("invalid_payload", f"{field} must be an object")
    return value


def _nonempty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AgileGovernanceError("invalid_payload", f"{field} must be a non-empty string")
    return value.strip()


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise AgileGovernanceError("invalid_config", f"{field} must be a positive integer")
    return value


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise AgileGovernanceError("invalid_payload", f"{field} must be a non-negative integer")
    return value


def _lifecycle(value: Any, field: str) -> str:
    status = _nonempty(value, field)
    if status not in LIFECYCLE:
        raise AgileGovernanceError("invalid_lifecycle", "strict ticket lifecycle rejected")
    return status
