#!/usr/bin/env python3
"""Fail-closed Stage A validator for governed capacity checkpoints.

This hook validates caller-submitted structure; it is not the authoritative
scheduler, a trusted provider verifier, or proof of native hook interception.
Stage A therefore rejects every actual dispatch after structural validation.
The local SQLite ledger is an owner-only replay/fork aid. It is not resistant
to tampering by another process running as the same OS principal.
"""

from __future__ import annotations

import hashlib
import json
import os
import pwd
import re
import sqlite3
import stat
import sys
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / ".agents" / "config" / "full_capacity_guard.v2.json"
MAX_INPUT_BYTES = 262_144
MAX_TEXT = 512
GOVERNANCE_SCHEMA_VERSION = "full-capacity-governance-v2"
CONFIG_SCHEMA_VERSION = "full-capacity-guard-config-v2"
AUTHORIZATION_SCHEMA_VERSION = "capacity-provider-authorization-v2"
EXPECTED_ALIASES = ("agy1", "agy2", "agy3", "agy4")
GOVERNED_ALIASES = frozenset({"codex1", "codex2", "codex3", *EXPECTED_ALIASES})
ALIAS_PROVIDER = {
    "codex1": "codex",
    "codex2": "codex",
    "codex3": "codex",
    "agy1": "agy",
    "agy2": "agy",
    "agy3": "agy",
    "agy4": "agy",
}
GENESIS_RECORD = "GENESIS"
GENESIS_GLOBAL = "GENESIS"
DEPENDENCY_NAMES = (
    "dispatcher_validator",
    "scheduler_validator",
    "model_policy",
    "governance_schema",
    "rule18_schema",
)
DEPENDENCY_DIGEST_FIELDS = frozenset(
    {
        "dispatcher_validator_sha256",
        "scheduler_validator_sha256",
        "model_policy_sha256",
        "governance_schema_sha256",
        "rule18_schema_sha256",
    }
)
PIN_FIELDS = frozenset({"path", "sha256"})
SCHEMA_PIN_FIELDS = frozenset({"path", "uri", "sha256"})
LEDGER_LIMIT_FIELDS = frozenset(
    {
        "max_rows",
        "max_sessions",
        "max_bytes",
        "retention_seconds",
        "busy_timeout_ms",
    }
)
EXPECTED_DEPENDENCY_PINS = {
    "dispatcher_validator": {
        "path": "scripts/multiagent_prompt_command.py",
        "sha256": "f58fa591e65fbc8d038bc395c204dd44e48b01f460d44b46430ca8fa7fcec604",
    },
    "scheduler_validator": {
        "path": "scripts/multiagent_ticket_scheduler.py",
        "sha256": "86fefe7831b5b51c35c1ee7295a7480fc50ffa7c8ed1b55d681a723e217f4945",
    },
    "model_policy": {
        "path": ".agents/config/multiagent_model_policy.yaml",
        "sha256": "ffe971c46c551e6c02f6f0fb32009bf880633b60ef74ee78b6f7bb92ff987d9f",
    },
    "governance_schema": {
        "path": ".agents/schemas/full-capacity-governance-v2.schema.json",
        "uri": "https://horoconsultant.local/schemas/full-capacity-governance-v2.schema.json",
        "sha256": "90f0c18bec385f83d50fffeb69e136f1b6b21fca4c350bb62778695287dedde9",
    },
    "rule18_schema": {
        "path": ".agents/schemas/multiagent-dispatch-decision-v1.schema.json",
        "uri": "https://horoconsultant.local/schemas/multiagent-dispatch-decision-v1.schema.json",
        "sha256": "fa521294932da91db233c2e253db3efa15b3231a71cf453fcea73216da4ec44f",
    },
}
MATCHED_SCOPES = frozenset(
    {"orchestrator", "multiagent", "multi-agent", "orchestration"}
)
EVENT_TYPES = frozenset(
    {"dispatch", "checkpoint", "agent_completed", "agent_failed", "terminal"}
)
EVENT_TYPE_ALIASES = {
    "orchestrator_dispatch": "dispatch",
    "multiagent_dispatch": "dispatch",
    "orchestrator_checkpoint": "checkpoint",
    "multiagent_checkpoint": "checkpoint",
}
ACTIVE_ACTIONS = frozenset({"DISPATCH", "DECOMPOSE_AND_DISPATCH", "REFILL"})
REPLAN_ACTION = "CAPACITY_VIOLATION_NEEDS_REPLAN"
READY_TICKET_STATES = frozenset({"TODO", "READY"})
TERMINAL_TICKET_STATES = frozenset({"DONE", "BLOCKED"})
KNOWN_TICKET_STATES = READY_TICKET_STATES | TERMINAL_TICKET_STATES | {"DOING"}
LANE_TYPES = frozenset(
    {
        "implementation",
        "qa",
        "verification",
        "review",
        "operations",
        "planning",
        "documentation",
        "fallback",
    }
)
LANE_ROLES = frozenset(
    {
        "SOURCE_EDITOR",
        "DOCS_EDITOR",
        "QA",
        "SHORT_FALLBACK",
        "OTHER",
        "CORE_SOURCE_EDITOR",
        "API_SOURCE_EDITOR",
        "UI_SOURCE_EDITOR",
        "TEST_SOURCE_EDITOR",
        "DOCS_GOVERNANCE_EDITOR",
    }
)
SOURCE_ROLES = frozenset(
    {"SOURCE_EDITOR", "CORE_SOURCE_EDITOR", "API_SOURCE_EDITOR", "UI_SOURCE_EDITOR"}
)
RESIDUAL_EXCEPTION_TYPE = "NO_SAFE_USEFUL_LANE"
PROOF_BOUNDARY_FIELDS = frozenset(
    {
        "authoritative_snapshot",
        "native_hook_interception",
        "natural_exit_enforcement",
        "provider_provenance",
        "provider_runtime",
        "runtime_enforcement",
        "runtime_provenance",
        "wall_clock_enforcement",
    }
)
CONFIG_FIELDS = frozenset(
    {
        "schema_version",
        "governance_schema_version",
        "enabled",
        "normative_short_lane_max_seconds",
        "effective_short_lane_max_seconds",
        "max_slots",
        "max_tickets",
        "ledger_schema_version",
        "ledger_relative_directory",
        "ledger_filename",
        "ledger_limits",
        "policy_path",
        "dependency_pins",
        "provider_aliases",
        "positive_alias_runtime_proof_available",
        "authoritative_snapshot_proof_available",
        "native_hook_interception_proven",
        "provider_runtime_proven",
        "provider_provenance_proven",
        "wall_clock_enforcement_proven",
        "natural_exit_enforcement_proven",
        "feature_flags",
    }
)
FEATURE_FLAG_DEFAULTS = {
    "enable_agy_parity": False,
    "enable_module_level_source_isolation": False,
    "enable_granular_lane_roles": False,
}
CAPACITY_PAYLOAD_FIELDS = frozenset(
    {
        "schema_version",
        "scope",
        "event_type",
        "session_id",
        "checkpoint_sequence",
        "previous_checkpoint_sequence",
        "previous_capacity_record_sha256",
        "max_slots",
        "active_slots",
        "ticket_snapshot",
        "ownership_snapshot",
        "actionable_work",
        "decision",
        "governance_record",
        "capacity_record_sha256",
    }
)
TICKET_FIELDS = frozenset(
    {
        "ticket_id",
        "severity",
        "work_effort",
        "status",
        "dependencies",
        "blockers",
        "owner",
        "ownership",
        "quota_passed",
        "hitl_passed",
        "lane_type",
        "lane_role",
        "required_role",
        "rule18_decision",
        "decision_sha256",
        "policy_version",
        "policy_sha256",
        "execution_window",
        "short_fallback",
        "provider_authorization",
    }
)
OWNERSHIP_SNAPSHOT_FIELDS = frozenset(
    {"ticket_id", "owner", "ownership", "lane_role", "state"}
)
EXECUTION_WINDOW_FIELDS = frozenset(
    {
        "lease_seconds",
        "started_at",
        "deadline_at",
        "termination_mode",
        "preemption_policy",
        "background",
        "daemon",
    }
)
SHORT_FALLBACK_FIELDS = frozenset(
    {
        "work_mode",
        "evidence_bearing",
        "freeze_independent",
        "provider_mode",
        "provider_authorization_id",
        "provider_authorization_sha256",
        "provider_evidence_id",
        "provider_evidence_sha256",
        "lease_seconds",
        "started_at",
        "deadline_at",
        "natural_termination",
        "termination_mode",
        "preemption_policy",
        "background",
        "daemon",
        "wall_clock_enforcement",
        "natural_exit_enforcement",
    }
)
PROVIDER_AUTHORIZATION_FIELDS = frozenset(
    {
        "schema_version",
        "state",
        "authorization_id",
        "authorization_sha256",
        "evidence_id",
        "evidence_sha256",
        "provider",
        "account_alias",
        "session_id",
        "ticket_id",
        "role",
        "ownership_sha256",
        "decision_sha256",
        "policy_version",
        "policy_sha256",
    }
)
DECISION_FIELDS = frozenset(
    {
        "action",
        "recomputed",
        "dispatches",
        "decomposition",
        "capacity_exception",
        "residual_capacity_exception",
    }
)
DISPATCH_FIELDS = frozenset(
    {
        "ticket_id",
        "lane_type",
        "lane_role",
        "required_role",
        "execution_alias",
        "owner",
        "ownership",
        "decision_sha256",
        "policy_version",
        "policy_sha256",
        "execution_window_sha256",
        "short_fallback_sha256",
        "authorization_id",
        "authorization_sha256",
        "provider_evidence_id",
        "provider_evidence_sha256",
    }
)
CAPACITY_EXCEPTION_FIELDS = frozenset(
    {"type", "residual_slots", "reasons", "rejected_candidates", "evidence"}
)
CAPACITY_EXCEPTION_EVIDENCE_FIELDS = frozenset(
    {
        "rejected_candidates",
        "capacity_snapshot_sha256",
        "scheduler_snapshot_sha256",
        "policy_sha256",
    }
)
ALIAS_EVALUATION_FIELDS = frozenset(
    {
        "alias",
        "evaluation",
        "eligibility",
        "dispatched",
        "candidate_ticket_id",
        "reason_codes",
        "authorization_id",
        "authorization_sha256",
        "provider_evidence_id",
        "provider_evidence_sha256",
        "receipt",
    }
)
ALIAS_REASON_CODES = frozenset(
    {
        "ALIAS_DECISION_MISMATCH",
        "CAPACITY_ALIAS_RUNTIME_PROOF_UNAVAILABLE",
        "DEPENDENCY_BLOCKED",
        "EXPLICIT_BLOCKER",
        "HITL_GATE",
        "INVALID_RULE18_DECISION",
        "NO_CANDIDATE_TICKET",
        "NOT_SELECTED_BY_RULE11",
        "OWNERSHIP_CONFLICT",
        "PROVIDER_AUTHORIZATION_NOT_PROVEN",
        "QA_PRIORITY",
        "QUOTA_GATE",
        "STATUS_NOT_READY",
    }
)
FAIRNESS_FIELDS = frozenset(
    {
        "strategy",
        "last_served_sequence",
        "eligible_order",
        "selected_aliases",
        "rule11_selection_sha256",
    }
)
HANDOFF_FIELDS = frozenset(
    {
        "source_ticket_ids",
        "source_state",
        "qa_ticket_id",
        "qa_state",
        "running_fallback_ticket_ids",
        "qa_next_slot_priority",
        "handoff_sha256",
    }
)
GOVERNANCE_FIELDS = frozenset(
    {
        "schema_version",
        "config_sha256",
        "session_id",
        "sequence",
        "previous_sequence",
        "previous_record_sha256",
        "lifecycle_phase",
        "lifecycle_status",
        "tool_name",
        "tool_use_id",
        "tool_input_sha256",
        "pre_dispatch_record_sha256",
        "tool_result_sha256",
        "capacity_snapshot_sha256",
        "scheduler_snapshot_sha256",
        "policy_version",
        "policy_sha256",
        "dependency_digests",
        "dependency_manifest_sha256",
        "decision_sha256",
        "alias_evaluations",
        "fairness",
        "source_qa_handoff",
        "proof_boundaries",
        "record_sha256",
    }
)
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
SAFE_TICKET_ID = re.compile(r"^[\x21-\x7e]{1,128}$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
RFC3339_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")
SECRET_VALUE = re.compile(
    r"(?i)(?:\bbearer\s+[A-Za-z0-9._~+/-]{12,}|\bsk-[A-Za-z0-9_-]{12,}|"
    r"\b(?:authorization|cookie|api[_-]?key|access[_-]?token|refresh[_-]?token)\s*[:=])"
)
SECRET_KEY = re.compile(
    r"(?i)(?:^|_)(?:password|secret|cookie|api_key|access_token|refresh_token)(?:$|_)"
)
FORBIDDEN_CONTROL_KEYS = frozenset(
    {"force_cancel", "cancel", "cancellations", "preempt", "preemptions", "kill"}
)


if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

class CapacityViolation(ValueError):
    """Content-free capacity contract rejection."""

    def __init__(self, code: str) -> None:
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", code):
            raise ValueError("capacity violation code must be uppercase ASCII")
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class DependencyPin:
    name: str
    path: Path
    digest: str
    uri: str | None = None


@dataclass(frozen=True)
class GuardConfig:
    raw: Mapping[str, Any]
    digest: str
    effective_short_lane_max_seconds: int
    max_slots: int
    max_tickets: int
    ledger_schema_version: int
    ledger_relative_directory: tuple[str, ...]
    ledger_filename: str
    ledger_max_rows: int
    ledger_max_sessions: int
    ledger_max_bytes: int
    ledger_retention_seconds: int
    ledger_busy_timeout_ms: int
    policy_path: Path
    dependency_pins: Mapping[str, DependencyPin]
    dependency_digests: Mapping[str, str]
    dependency_manifest_sha256: str
    feature_flags: Mapping[str, bool] = frozenset()


@dataclass(frozen=True)
class PolicyContext:
    policy: Mapping[str, Any]
    version: str
    digest: str
    validator: Any
    scheduler: Any
    schema_registry: Any
    governance_schema_validator: Any
    rule18_schema_validator: Any


@dataclass(frozen=True)
class EventContext:
    lifecycle_phase: str
    tool_name: str | None
    tool_use_id: str | None
    tool_input_sha256: str | None
    pre_dispatch_record_sha256: str | None
    tool_result_sha256: str | None
    provider_executing: bool


@dataclass(frozen=True)
class ValidatedTicket:
    raw: Mapping[str, Any]
    decision: Mapping[str, Any] | None
    decision_sha256: str | None
    execution_window_sha256: str
    short_fallback_sha256: str | None
    authorization: Mapping[str, Any] | None


@dataclass(frozen=True)
class ValidationState:
    config: GuardConfig
    policy: PolicyContext
    event: EventContext
    payload: Mapping[str, Any]
    event_type: str
    tickets: Mapping[str, ValidatedTicket]
    scheduler_snapshot: Any
    scheduler_snapshot_sha256: str
    actionable: tuple[str, ...]
    active_ticket_ids: frozenset[str]
    active_roles: Mapping[str, str]
    active_reserved_resources: tuple[str, ...]
    idle_slots: int
    decision: Mapping[str, Any]
    dispatches: tuple[Mapping[str, Any], ...]
    governance_record: Mapping[str, Any]
    block_code: str | None


def _mapping(value: Any, code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CapacityViolation(code)
    return value


def _exact_fields(value: Mapping[str, Any], fields: frozenset[str], code: str) -> None:
    if set(value) != fields:
        raise CapacityViolation(code)


def _integer(value: Any, code: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CapacityViolation(code)
    if value < minimum or value > maximum:
        raise CapacityViolation(code)
    return value


def _boolean(value: Any, code: str) -> bool:
    if not isinstance(value, bool):
        raise CapacityViolation(code)
    return value


def _safe_id(value: Any, code: str) -> str:
    if not isinstance(value, str) or SAFE_ID.fullmatch(value) is None:
        raise CapacityViolation(code)
    return value


def _ticket_id(value: Any, code: str) -> str:
    if (
        not isinstance(value, str)
        or not value.isascii()
        or SAFE_TICKET_ID.fullmatch(value) is None
    ):
        raise CapacityViolation(code)
    return value


def _valid_sha256(value: Any, code: str) -> str:
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        raise CapacityViolation(code)
    return value


def _sha256(value: Any) -> str:
    try:
        canonical = json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise CapacityViolation("CAPACITY_PAYLOAD_REJECTED") from exc
    return hashlib.sha256(canonical).hexdigest()


def _raw_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CapacityViolation("CAPACITY_PAYLOAD_REJECTED")
        result[key] = value
    return result


def _load_json_bytes(raw: bytes, code: str) -> Mapping[str, Any]:
    try:
        value = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CapacityViolation(code) from exc
    return _mapping(value, code)


def _contains_secret(value: Any, depth: int = 0) -> bool:
    if depth > 16:
        return True
    if isinstance(value, str):
        return len(value) > 16_384 or SECRET_VALUE.search(value) is not None
    if isinstance(value, Mapping):
        if len(value) > 512:
            return True
        return any(
            SECRET_KEY.search(str(key).lower()) is not None
            or _contains_secret(item, depth + 1)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return len(value) > 512 or any(
            _contains_secret(item, depth + 1) for item in value
        )
    return False


def _regular_nonsymlink(path: Path, code: str) -> os.stat_result:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CapacityViolation(code) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise CapacityViolation(code)
    return metadata


def _verified_repository_file(path: Path, expected_digest: str) -> bytes:
    try:
        relative = path.relative_to(ROOT_DIR)
    except ValueError as exc:
        raise CapacityViolation("CAPACITY_DEPENDENCY_INTEGRITY_INVALID") from exc
    current = ROOT_DIR
    for part in relative.parts:
        current = current / part
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise CapacityViolation("CAPACITY_DEPENDENCY_INTEGRITY_INVALID") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise CapacityViolation("CAPACITY_DEPENDENCY_INTEGRITY_INVALID")
    _regular_nonsymlink(path, "CAPACITY_DEPENDENCY_INTEGRITY_INVALID")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise CapacityViolation("CAPACITY_DEPENDENCY_INTEGRITY_INVALID") from exc
    if _raw_sha256(raw) != expected_digest:
        raise CapacityViolation("CAPACITY_DEPENDENCY_INTEGRITY_INVALID")
    return raw


def _load_config() -> GuardConfig:
    _regular_nonsymlink(CONFIG_PATH, "CAPACITY_CONFIG_INVALID")
    try:
        raw_bytes = CONFIG_PATH.read_bytes()
    except OSError as exc:
        raise CapacityViolation("CAPACITY_CONFIG_INVALID") from exc
    raw = _load_json_bytes(raw_bytes, "CAPACITY_CONFIG_INVALID")
    _exact_fields(raw, CONFIG_FIELDS, "CAPACITY_CONFIG_INVALID")
    if (
        raw.get("schema_version") != CONFIG_SCHEMA_VERSION
        or raw.get("governance_schema_version") != GOVERNANCE_SCHEMA_VERSION
        or raw.get("enabled") is not True
        or raw.get("provider_aliases") != list(EXPECTED_ALIASES)
    ):
        raise CapacityViolation("CAPACITY_CONFIG_INVALID")
    normative = _integer(
        raw.get("normative_short_lane_max_seconds"),
        "CAPACITY_CONFIG_INVALID",
        1,
        600,
    )
    if normative != 600:
        raise CapacityViolation("CAPACITY_CONFIG_INVALID")
    configured_effective = _integer(
        raw.get("effective_short_lane_max_seconds"),
        "CAPACITY_CONFIG_INVALID",
        1,
        normative,
    )
    effective = min(configured_effective, normative, 600)
    if effective != 300:
        raise CapacityViolation("CAPACITY_CONFIG_INVALID")
    max_slots = _integer(raw.get("max_slots"), "CAPACITY_CONFIG_INVALID", 1, 64)
    max_tickets = _integer(raw.get("max_tickets"), "CAPACITY_CONFIG_INVALID", 1, 256)
    ledger_schema = _integer(
        raw.get("ledger_schema_version"), "CAPACITY_CONFIG_INVALID", 3, 3
    )
    relative = raw.get("ledger_relative_directory")
    if relative != [
        ".local",
        "state",
        "horoconsultant",
        "full-capacity-guard-v2",
    ]:
        raise CapacityViolation("CAPACITY_CONFIG_INVALID")
    relative_parts = tuple(str(item) for item in relative)
    filename = raw.get("ledger_filename")
    if filename != "lifecycle.sqlite3":
        raise CapacityViolation("CAPACITY_CONFIG_INVALID")
    limits = _mapping(raw.get("ledger_limits"), "CAPACITY_CONFIG_INVALID")
    _exact_fields(limits, LEDGER_LIMIT_FIELDS, "CAPACITY_CONFIG_INVALID")
    expected_limits = {
        "max_rows": 4096,
        "max_sessions": 256,
        "max_bytes": 16_777_216,
        "retention_seconds": 2_592_000,
        "busy_timeout_ms": 2500,
    }
    if limits != expected_limits:
        raise CapacityViolation("CAPACITY_CONFIG_INVALID")
    ledger_max_rows = _integer(
        limits.get("max_rows"), "CAPACITY_CONFIG_INVALID", 1, 100_000
    )
    ledger_max_sessions = _integer(
        limits.get("max_sessions"), "CAPACITY_CONFIG_INVALID", 1, 10_000
    )
    ledger_max_bytes = _integer(
        limits.get("max_bytes"), "CAPACITY_CONFIG_INVALID", 65_536, 1_073_741_824
    )
    ledger_retention_seconds = _integer(
        limits.get("retention_seconds"),
        "CAPACITY_CONFIG_INVALID",
        60,
        31_536_000,
    )
    ledger_busy_timeout_ms = _integer(
        limits.get("busy_timeout_ms"), "CAPACITY_CONFIG_INVALID", 1, 9999
    )
    policy_text = raw.get("policy_path")
    if policy_text != ".agents/config/multiagent_model_policy.yaml":
        raise CapacityViolation("CAPACITY_CONFIG_INVALID")
    raw_pins = _mapping(raw.get("dependency_pins"), "CAPACITY_CONFIG_INVALID")
    if set(raw_pins) != set(DEPENDENCY_NAMES):
        raise CapacityViolation("CAPACITY_CONFIG_INVALID")
    dependency_pins: dict[str, DependencyPin] = {}
    dependency_digests: dict[str, str] = {}
    for name in DEPENDENCY_NAMES:
        pin = _mapping(raw_pins.get(name), "CAPACITY_CONFIG_INVALID")
        expected = EXPECTED_DEPENDENCY_PINS[name]
        fields = SCHEMA_PIN_FIELDS if "schema" in name else PIN_FIELDS
        _exact_fields(pin, fields, "CAPACITY_CONFIG_INVALID")
        if pin != expected:
            raise CapacityViolation("CAPACITY_CONFIG_INVALID")
        digest = _valid_sha256(pin.get("sha256"), "CAPACITY_CONFIG_INVALID")
        path = ROOT_DIR / str(pin.get("path"))
        uri = pin.get("uri")
        if uri is not None and (
            not isinstance(uri, str) or not uri.startswith("https://")
        ):
            raise CapacityViolation("CAPACITY_CONFIG_INVALID")
        dependency_pins[name] = DependencyPin(
            name=name,
            path=path,
            digest=digest,
            uri=str(uri) if uri is not None else None,
        )
        dependency_digests[f"{name}_sha256"] = digest
    if dependency_pins["model_policy"].path != ROOT_DIR / str(policy_text):
        raise CapacityViolation("CAPACITY_CONFIG_INVALID")
    dependency_manifest_sha256 = _sha256(dependency_digests)
    for proof_flag in (
        "positive_alias_runtime_proof_available",
        "authoritative_snapshot_proof_available",
        "native_hook_interception_proven",
        "provider_runtime_proven",
        "provider_provenance_proven",
        "wall_clock_enforcement_proven",
        "natural_exit_enforcement_proven",
    ):
        if raw.get(proof_flag) is not False:
            raise CapacityViolation("CAPACITY_CONFIG_INVALID")
    feature_flags_raw = _mapping(
        raw.get("feature_flags"), "CAPACITY_CONFIG_FEATURE_FLAGS_INVALID"
    )
    _exact_fields(
        feature_flags_raw,
        frozenset(FEATURE_FLAG_DEFAULTS),
        "CAPACITY_CONFIG_FEATURE_FLAGS_INVALID",
    )
    if any(
        type(feature_flags_raw[name]) is not bool  # noqa: E721 - reject int values
        or feature_flags_raw[name] is not expected
        for name, expected in FEATURE_FLAG_DEFAULTS.items()
    ):
        raise CapacityViolation("CAPACITY_CONFIG_FEATURE_FLAGS_INVALID")
    feature_flags = dict(feature_flags_raw)
    return GuardConfig(
        raw=raw,
        digest=_raw_sha256(raw_bytes),
        effective_short_lane_max_seconds=effective,
        max_slots=max_slots,
        max_tickets=max_tickets,
        ledger_schema_version=ledger_schema,
        ledger_relative_directory=relative_parts,
        ledger_filename=str(filename),
        ledger_max_rows=ledger_max_rows,
        ledger_max_sessions=ledger_max_sessions,
        ledger_max_bytes=ledger_max_bytes,
        ledger_retention_seconds=ledger_retention_seconds,
        ledger_busy_timeout_ms=ledger_busy_timeout_ms,
        policy_path=ROOT_DIR / str(policy_text),
        dependency_pins=dependency_pins,
        dependency_digests=dependency_digests,
        dependency_manifest_sha256=dependency_manifest_sha256,
        feature_flags=feature_flags,
    )


def _execute_verified_module(name: str, path: Path, raw: bytes) -> ModuleType:
    module = ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = name.rpartition(".")[0]
    module.__loader__ = None
    module.__spec__ = None
    sys.modules[name] = module
    try:
        code = compile(raw, str(path), "exec", dont_inherit=True)
        exec(code, module.__dict__)  # noqa: S102 - exact pinned local source only
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


@contextmanager
def _verified_scheduler_import(scheduler: ModuleType):
    saved = {
        name: sys.modules.get(name)
        for name in ("scripts", "scripts.multiagent_ticket_scheduler")
    }
    package = ModuleType("scripts")
    package.__package__ = "scripts"
    package.__path__ = [str(ROOT_DIR / "scripts")]  # type: ignore[attr-defined]
    package.multiagent_ticket_scheduler = scheduler  # type: ignore[attr-defined]
    sys.modules["scripts"] = package
    sys.modules["scripts.multiagent_ticket_scheduler"] = scheduler
    try:
        yield
    finally:
        for name, previous in saved.items():
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous


def _schema_references(value: Any) -> tuple[str, ...]:
    references: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key == "$ref" and isinstance(item, str):
                references.append(item)
            else:
                references.extend(_schema_references(item))
    elif isinstance(value, list):
        for item in value:
            references.extend(_schema_references(item))
    return tuple(references)


def _build_local_schema_registry(
    config: GuardConfig, dependency_bytes: Mapping[str, bytes]
) -> tuple[Any, Any, Any]:
    try:
        from urllib.parse import urldefrag, urljoin

        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        from referencing.exceptions import NoSuchResource

        def deny_retrieval(uri: str) -> Any:
            raise NoSuchResource(ref=uri)

        schemas: dict[str, Mapping[str, Any]] = {}
        for name in ("governance_schema", "rule18_schema"):
            schema = _load_json_bytes(
                dependency_bytes[name], "CAPACITY_SCHEMA_REGISTRY_INVALID"
            )
            pin = config.dependency_pins[name]
            if schema.get("$id") != pin.uri:
                raise CapacityViolation("CAPACITY_SCHEMA_REGISTRY_INVALID")
            Draft202012Validator.check_schema(schema)
            schemas[str(pin.uri)] = schema
        allowed_uris = frozenset(schemas)
        for base_uri, schema in schemas.items():
            for reference in _schema_references(schema):
                target, _ = urldefrag(urljoin(base_uri, reference))
                if target != base_uri and target not in allowed_uris:
                    raise CapacityViolation("CAPACITY_SCHEMA_REGISTRY_INVALID")
        registry = Registry(retrieve=deny_retrieval)
        for uri, schema in schemas.items():
            registry = registry.with_resource(uri, Resource.from_contents(schema))
        governance = Draft202012Validator(
            schemas[str(config.dependency_pins["governance_schema"].uri)],
            registry=registry,
        )
        rule18 = Draft202012Validator(
            schemas[str(config.dependency_pins["rule18_schema"].uri)],
            registry=registry,
        )
    except CapacityViolation:
        raise
    except Exception as exc:
        raise CapacityViolation("CAPACITY_SCHEMA_REGISTRY_INVALID") from exc
    return registry, governance, rule18


def _load_policy(config: GuardConfig) -> PolicyContext:
    dependency_bytes = {
        name: _verified_repository_file(pin.path, pin.digest)
        for name, pin in config.dependency_pins.items()
    }
    try:
        scheduler = _execute_verified_module(
            f"_horo_capacity_scheduler_{config.dependency_pins['scheduler_validator'].digest}",
            config.dependency_pins["scheduler_validator"].path,
            dependency_bytes["scheduler_validator"],
        )
        with _verified_scheduler_import(scheduler):
            validator = _execute_verified_module(
                f"_horo_capacity_dispatcher_{config.dependency_pins['dispatcher_validator'].digest}",
                config.dependency_pins["dispatcher_validator"].path,
                dependency_bytes["dispatcher_validator"],
            )
        decoded_policy = dependency_bytes["model_policy"].decode("utf-8")
        policy = validator.yaml.safe_load(decoded_policy) or {}
        if not isinstance(policy, Mapping):
            raise TypeError("model policy must be a mapping")
        registry, governance_schema, rule18_schema = _build_local_schema_registry(
            config, dependency_bytes
        )
    except CapacityViolation:
        raise
    except Exception as exc:
        raise CapacityViolation("CAPACITY_DEPENDENCY_INTEGRITY_INVALID") from exc
    version = policy.get("policy_version")
    if not isinstance(version, str) or not version:
        raise CapacityViolation("CAPACITY_POLICY_INVALID")
    return PolicyContext(
        policy=policy,
        version=version,
        digest=config.dependency_pins["model_policy"].digest,
        validator=validator,
        scheduler=scheduler,
        schema_registry=registry,
        governance_schema_validator=governance_schema,
        rule18_schema_validator=rule18_schema,
    )


def _resource(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > MAX_TEXT
        or not value.isascii()
    ):
        raise CapacityViolation("CAPACITY_OWNERSHIP_INVALID")
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if (
        path.is_absolute()
        or normalized in {"", ".", "..", "/"}
        or any(part in {"", ".", ".."} for part in path.parts)
        or any(ord(character) < 0x20 for character in normalized)
    ):
        raise CapacityViolation("CAPACITY_OWNERSHIP_INVALID")
    return str(path)


def _resources(value: Any, *, allow_empty: bool = False) -> tuple[str, ...]:
    if (
        not isinstance(value, list)
        or (not value and not allow_empty)
        or len(value) > 256
    ):
        raise CapacityViolation("CAPACITY_OWNERSHIP_INVALID")
    normalized = tuple(_resource(item) for item in value)
    if len(normalized) != len(set(normalized)):
        raise CapacityViolation("CAPACITY_OWNERSHIP_INVALID")
    return normalized


def _conflicts(left: str, right: str) -> bool:
    left_parts = PurePosixPath(left).parts
    right_parts = PurePosixPath(right).parts
    common = min(len(left_parts), len(right_parts))
    return left_parts[:common] == right_parts[:common]


def _has_conflict(resources: Sequence[str], reserved: Sequence[str]) -> bool:
    return any(
        _conflicts(resource, existing)
        for resource in resources
        for existing in reserved
    )


def _timestamp(value: Any, code: str) -> datetime:
    if not isinstance(value, str) or RFC3339_UTC.fullmatch(value) is None:
        raise CapacityViolation(code)
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise CapacityViolation(code) from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise CapacityViolation(code)
    return parsed


def _validate_execution_window(
    value: Any, config: GuardConfig
) -> tuple[Mapping[str, Any], str]:
    window = _mapping(value, "CAPACITY_EXECUTION_WINDOW_INVALID")
    _exact_fields(window, EXECUTION_WINDOW_FIELDS, "CAPACITY_EXECUTION_WINDOW_INVALID")
    lease = _integer(
        window.get("lease_seconds"),
        "CAPACITY_SHORT_FALLBACK_LEASE_INVALID",
        1,
        min(config.effective_short_lane_max_seconds, 600),
    )
    started = _timestamp(window.get("started_at"), "CAPACITY_EXECUTION_WINDOW_INVALID")
    deadline = _timestamp(
        window.get("deadline_at"), "CAPACITY_EXECUTION_WINDOW_INVALID"
    )
    if (deadline - started).total_seconds() != lease:
        raise CapacityViolation("CAPACITY_EXECUTION_WINDOW_INVALID")
    if (
        window.get("termination_mode") != "NATURAL_EXIT_ONLY"
        or window.get("preemption_policy") != "NEVER"
        or window.get("background") is not False
        or window.get("daemon") is not False
    ):
        raise CapacityViolation("CAPACITY_ACTIVE_PREEMPTION_FORBIDDEN")
    return window, _sha256(window)


def _validate_short_fallback(
    value: Any,
    *,
    window: Mapping[str, Any],
    config: GuardConfig,
) -> tuple[Mapping[str, Any], str]:
    profile = _mapping(value, "CAPACITY_SHORT_FALLBACK_INVALID")
    _exact_fields(profile, SHORT_FALLBACK_FIELDS, "CAPACITY_SHORT_FALLBACK_INVALID")
    _integer(
        profile.get("lease_seconds"),
        "CAPACITY_SHORT_FALLBACK_LEASE_INVALID",
        1,
        min(config.effective_short_lane_max_seconds, 600),
    )
    if any(
        profile.get(field) != window.get(field)
        for field in (
            "lease_seconds",
            "started_at",
            "deadline_at",
            "termination_mode",
            "preemption_policy",
            "background",
            "daemon",
        )
    ):
        raise CapacityViolation("CAPACITY_SHORT_FALLBACK_INVALID")
    if (
        profile.get("work_mode") != "READ_ONLY"
        or profile.get("evidence_bearing") is not True
        or profile.get("freeze_independent") is not True
        or profile.get("provider_mode") != "NONE"
        or profile.get("natural_termination") is not True
        or profile.get("termination_mode") != "NATURAL_EXIT_ONLY"
        or profile.get("preemption_policy") != "NEVER"
        or profile.get("background") is not False
        or profile.get("daemon") is not False
        or profile.get("wall_clock_enforcement") != "NOT_PROVEN"
        or profile.get("natural_exit_enforcement") != "NOT_PROVEN"
    ):
        raise CapacityViolation("CAPACITY_SHORT_FALLBACK_INVALID")
    for field in (
        "provider_authorization_id",
        "provider_authorization_sha256",
        "provider_evidence_id",
        "provider_evidence_sha256",
    ):
        if profile.get(field) is not None:
            raise CapacityViolation("CAPACITY_PROVIDER_AUTHORIZATION_INVALID")
    return profile, _sha256(profile)


def _validate_rule18_decision(
    value: Any,
    *,
    ticket_id: str,
    claimed_digest: Any,
    policy_version: Any,
    policy_sha256: Any,
    policy: PolicyContext,
) -> tuple[Mapping[str, Any] | None, str | None]:
    if policy_version != policy.version or policy_sha256 != policy.digest:
        raise CapacityViolation("CAPACITY_POLICY_BINDING_INVALID")
    if value is None:
        if claimed_digest is not None:
            raise CapacityViolation("CAPACITY_RULE18_DECISION_INVALID")
        return None, None
    decision = _mapping(value, "CAPACITY_RULE18_DECISION_INVALID")
    try:
        if next(policy.rule18_schema_validator.iter_errors(decision), None) is not None:
            raise CapacityViolation("CAPACITY_RULE18_DECISION_INVALID")
        validated = policy.validator.validate_dispatch_decision(decision, policy.policy)
    except CapacityViolation:
        raise
    except Exception as exc:
        raise CapacityViolation("CAPACITY_RULE18_DECISION_INVALID") from exc
    if validated.decision.get("ticket") != ticket_id:
        raise CapacityViolation("CAPACITY_RULE18_DECISION_INVALID")
    if claimed_digest != validated.digest:
        raise CapacityViolation("CAPACITY_RULE18_DECISION_INVALID")
    return validated.decision, validated.digest


def _authorization_bindings(
    value: Mapping[str, Any] | None,
) -> tuple[Any, Any, Any, Any]:
    if value is None:
        return None, None, None, None
    return (
        value.get("authorization_id"),
        value.get("authorization_sha256"),
        value.get("evidence_id"),
        value.get("evidence_sha256"),
    )


def _validate_provider_authorization(
    value: Any,
    *,
    session_id: str,
    ticket_id: str,
    role: str,
    ownership: tuple[str, ...],
    decision: Mapping[str, Any] | None,
    decision_sha256: str | None,
    policy: PolicyContext,
) -> Mapping[str, Any] | None:
    if value is None:
        return None
    if decision is None or decision_sha256 is None:
        raise CapacityViolation("CAPACITY_PROVIDER_AUTHORIZATION_INVALID")
    authorization = _mapping(value, "CAPACITY_PROVIDER_AUTHORIZATION_INVALID")
    _exact_fields(
        authorization,
        PROVIDER_AUTHORIZATION_FIELDS,
        "CAPACITY_PROVIDER_AUTHORIZATION_INVALID",
    )
    alias = decision.get("selected_alias")
    if alias not in GOVERNED_ALIASES:
        raise CapacityViolation("CAPACITY_PROVIDER_AUTHORIZATION_INVALID")
    if (
        authorization.get("schema_version") != AUTHORIZATION_SCHEMA_VERSION
        or authorization.get("state") != "STRUCTURALLY_BOUND_NOT_PROVEN"
        or authorization.get("provider") != ALIAS_PROVIDER[str(alias)]
        or authorization.get("account_alias") != alias
        or authorization.get("session_id") != session_id
        or authorization.get("ticket_id") != ticket_id
        or authorization.get("role") != role
        or authorization.get("ownership_sha256") != _sha256(list(ownership))
        or authorization.get("decision_sha256") != decision_sha256
        or authorization.get("policy_version") != policy.version
        or authorization.get("policy_sha256") != policy.digest
    ):
        raise CapacityViolation("CAPACITY_PROVIDER_AUTHORIZATION_INVALID")
    _safe_id(
        authorization.get("authorization_id"), "CAPACITY_PROVIDER_AUTHORIZATION_INVALID"
    )
    _safe_id(
        authorization.get("evidence_id"), "CAPACITY_PROVIDER_AUTHORIZATION_INVALID"
    )
    _valid_sha256(
        authorization.get("evidence_sha256"), "CAPACITY_PROVIDER_AUTHORIZATION_INVALID"
    )
    claimed = _valid_sha256(
        authorization.get("authorization_sha256"),
        "CAPACITY_PROVIDER_AUTHORIZATION_INVALID",
    )
    unsigned = dict(authorization)
    unsigned.pop("authorization_sha256", None)
    if _sha256(unsigned) != claimed:
        raise CapacityViolation("CAPACITY_PROVIDER_AUTHORIZATION_INVALID")
    return authorization


def _string_ids(
    value: Any, *, ticket_ids: bool, code: str, max_items: int
) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) > max_items:
        raise CapacityViolation(code)
    validator = _ticket_id if ticket_ids else _safe_id
    items = tuple(validator(item, code) for item in value)
    if len(items) != len(set(items)):
        raise CapacityViolation(code)
    return items


def _validate_tickets(
    payload: Mapping[str, Any],
    *,
    config: GuardConfig,
    policy: PolicyContext,
) -> dict[str, ValidatedTicket]:
    raw_tickets = payload.get("ticket_snapshot")
    if (
        not isinstance(raw_tickets, list)
        or not raw_tickets
        or len(raw_tickets) > config.max_tickets
    ):
        raise CapacityViolation("CAPACITY_TICKET_SNAPSHOT_INVALID")
    session_id = _safe_id(payload.get("session_id"), "CAPACITY_SESSION_MISMATCH")
    result: dict[str, ValidatedTicket] = {}
    dependencies: dict[str, tuple[str, ...]] = {}
    for item in raw_tickets:
        ticket = _mapping(item, "CAPACITY_TICKET_SNAPSHOT_INVALID")
        _exact_fields(ticket, TICKET_FIELDS, "CAPACITY_TICKET_SNAPSHOT_INVALID")
        ticket_id = _ticket_id(
            ticket.get("ticket_id"), "CAPACITY_TICKET_SNAPSHOT_INVALID"
        )
        if ticket_id in result:
            raise CapacityViolation("CAPACITY_DUPLICATE_TICKET")
        severity = ticket.get("severity")
        work_effort = ticket.get("work_effort")
        status = ticket.get("status")
        if severity not in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}:
            raise CapacityViolation("CAPACITY_TICKET_SNAPSHOT_INVALID")
        if work_effort not in {"XS", "S", "M", "L", "XL"}:
            raise CapacityViolation("CAPACITY_TICKET_SNAPSHOT_INVALID")
        if status not in KNOWN_TICKET_STATES:
            raise CapacityViolation("CAPACITY_TICKET_SNAPSHOT_INVALID")
        deps = _string_ids(
            ticket.get("dependencies"),
            ticket_ids=True,
            code="CAPACITY_TICKET_SNAPSHOT_INVALID",
            max_items=config.max_tickets,
        )
        blockers = _string_ids(
            ticket.get("blockers"),
            ticket_ids=False,
            code="CAPACITY_TICKET_SNAPSHOT_INVALID",
            max_items=config.max_tickets,
        )
        if ticket_id in deps:
            raise CapacityViolation("CAPACITY_TICKET_SNAPSHOT_INVALID")
        owner = _safe_id(ticket.get("owner"), "CAPACITY_TICKET_SNAPSHOT_INVALID")
        ownership = _resources(ticket.get("ownership"))
        _boolean(ticket.get("quota_passed"), "CAPACITY_TICKET_SNAPSHOT_INVALID")
        _boolean(ticket.get("hitl_passed"), "CAPACITY_TICKET_SNAPSHOT_INVALID")
        lane_type = ticket.get("lane_type")
        lane_role = ticket.get("lane_role")
        if lane_type not in LANE_TYPES or lane_role not in LANE_ROLES:
            raise CapacityViolation("CAPACITY_LANE_ROLE_INVALID")
        role = _safe_id(ticket.get("required_role"), "CAPACITY_LANE_ROLE_INVALID")
        window, window_sha256 = _validate_execution_window(
            ticket.get("execution_window"), config
        )
        short_sha256: str | None = None
        if lane_role == "SHORT_FALLBACK":
            _, short_sha256 = _validate_short_fallback(
                ticket.get("short_fallback"), window=window, config=config
            )
        elif ticket.get("short_fallback") is not None:
            raise CapacityViolation("CAPACITY_SHORT_FALLBACK_INVALID")
        decision, decision_sha256 = _validate_rule18_decision(
            ticket.get("rule18_decision"),
            ticket_id=ticket_id,
            claimed_digest=ticket.get("decision_sha256"),
            policy_version=ticket.get("policy_version"),
            policy_sha256=ticket.get("policy_sha256"),
            policy=policy,
        )
        authorization = _validate_provider_authorization(
            ticket.get("provider_authorization"),
            session_id=session_id,
            ticket_id=ticket_id,
            role=role,
            ownership=ownership,
            decision=decision,
            decision_sha256=decision_sha256,
            policy=policy,
        )
        if lane_role == "SHORT_FALLBACK" and authorization is not None:
            raise CapacityViolation("CAPACITY_PROVIDER_AUTHORIZATION_INVALID")
        result[ticket_id] = ValidatedTicket(
            raw=ticket,
            decision=decision,
            decision_sha256=decision_sha256,
            execution_window_sha256=window_sha256,
            short_fallback_sha256=short_sha256,
            authorization=authorization,
        )
        dependencies[ticket_id] = deps
        _ = blockers, owner
    known_ids = set(result)
    if any(set(items) - known_ids for items in dependencies.values()):
        raise CapacityViolation("CAPACITY_TICKET_SNAPSHOT_INVALID")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(ticket_id: str) -> None:
        if ticket_id in visiting:
            raise CapacityViolation("CAPACITY_TICKET_SNAPSHOT_INVALID")
        if ticket_id in visited:
            return
        visiting.add(ticket_id)
        for dependency in dependencies[ticket_id]:
            visit(dependency)
        visiting.remove(ticket_id)
        visited.add(ticket_id)

    for ticket_id in sorted(result):
        visit(ticket_id)
    return result


def _validate_ownership_snapshot(
    payload: Mapping[str, Any],
    tickets: Mapping[str, ValidatedTicket],
    *,
    active_slots: int,
    max_slots: int,
) -> tuple[list[dict[str, Any]], frozenset[str], dict[str, str], tuple[str, ...]]:
    raw = payload.get("ownership_snapshot")
    if not isinstance(raw, list) or len(raw) > max_slots or len(raw) != active_slots:
        raise CapacityViolation("CAPACITY_OWNERSHIP_SNAPSHOT_INVALID")
    reservations: list[dict[str, Any]] = []
    active_ids: set[str] = set()
    active_roles: dict[str, str] = {}
    reserved_resources: list[str] = []
    for item in raw:
        lane = _mapping(item, "CAPACITY_OWNERSHIP_SNAPSHOT_INVALID")
        _exact_fields(
            lane, OWNERSHIP_SNAPSHOT_FIELDS, "CAPACITY_OWNERSHIP_SNAPSHOT_INVALID"
        )
        ticket_id = _ticket_id(
            lane.get("ticket_id"), "CAPACITY_OWNERSHIP_SNAPSHOT_INVALID"
        )
        if (
            ticket_id in active_ids
            or ticket_id not in tickets
            or lane.get("state") != "ACTIVE"
        ):
            raise CapacityViolation("CAPACITY_OWNERSHIP_SNAPSHOT_INVALID")
        ticket = tickets[ticket_id].raw
        if ticket.get("status") != "DOING":
            raise CapacityViolation("CAPACITY_OWNERSHIP_SNAPSHOT_INVALID")
        owner = _safe_id(lane.get("owner"), "CAPACITY_OWNERSHIP_SNAPSHOT_INVALID")
        resources = _resources(lane.get("ownership"))
        if (
            owner != ticket.get("owner")
            or resources != _resources(ticket.get("ownership"))
            or lane.get("lane_role") != ticket.get("lane_role")
            or _has_conflict(resources, reserved_resources)
        ):
            raise CapacityViolation("CAPACITY_OWNERSHIP_CONFLICT")
        active_ids.add(ticket_id)
        active_roles[ticket_id] = str(ticket.get("lane_role"))
        reserved_resources.extend(resources)
        reservations.append(
            {"ticket_id": ticket_id, "owner": owner, "ownership": list(resources)}
        )
    doing_ids = {
        ticket_id
        for ticket_id, ticket in tickets.items()
        if ticket.raw.get("status") == "DOING"
    }
    if active_ids != doing_ids:
        raise CapacityViolation("CAPACITY_OWNERSHIP_SNAPSHOT_INVALID")
    return reservations, frozenset(active_ids), active_roles, tuple(reserved_resources)


def _scheduler_state(
    *,
    tickets: Mapping[str, ValidatedTicket],
    reservations: list[dict[str, Any]],
    policy: PolicyContext,
) -> tuple[Any, tuple[str, ...]]:
    snapshot = {
        "schema_version": 1,
        "tickets": [
            {
                "ticket_id": ticket_id,
                "severity": ticket.raw["severity"],
                "work_effort": ticket.raw["work_effort"],
                "status": ticket.raw["status"],
                "dependencies": ticket.raw["dependencies"],
                "blockers": ticket.raw["blockers"],
                "owner": ticket.raw["owner"],
                "ownership": ticket.raw["ownership"],
                "quota_passed": ticket.raw["quota_passed"],
                "hitl_passed": ticket.raw["hitl_passed"],
                "rule18_decision_valid": ticket.decision is not None,
            }
            for ticket_id, ticket in tickets.items()
        ],
        "reservations": reservations,
    }
    try:
        normalized = policy.scheduler.validate_snapshot(snapshot)
        selections = policy.scheduler.select_tickets(
            normalized, capacity=max(1, len(tickets))
        )
    except Exception as exc:
        raise CapacityViolation("CAPACITY_SCHEDULER_SNAPSHOT_INVALID") from exc
    return normalized, tuple(selection.ticket.ticket_id for selection in selections)


def _ticket_rejection_reasons(
    ticket_id: str,
    tickets: Mapping[str, ValidatedTicket],
    reserved_resources: Sequence[str],
) -> tuple[str, ...]:
    ticket = tickets[ticket_id]
    raw = ticket.raw
    reasons: set[str] = set()
    if raw.get("status") not in READY_TICKET_STATES:
        reasons.add("STATUS_NOT_READY")
    statuses = {
        identifier: item.raw.get("status") for identifier, item in tickets.items()
    }
    if any(
        statuses[dependency] != "DONE" for dependency in raw.get("dependencies", [])
    ):
        reasons.add("DEPENDENCY_BLOCKED")
    if raw.get("blockers"):
        reasons.add("EXPLICIT_BLOCKER")
    if raw.get("quota_passed") is not True:
        reasons.add("QUOTA_GATE")
    if raw.get("hitl_passed") is not True:
        reasons.add("HITL_GATE")
    if ticket.decision is None:
        reasons.add("INVALID_RULE18_DECISION")
    if _has_conflict(_resources(raw.get("ownership")), reserved_resources):
        reasons.add("OWNERSHIP_CONFLICT")
    return tuple(sorted(reasons))


def _scan_forbidden_controls(value: Any, depth: int = 0) -> None:
    if depth > 16:
        raise CapacityViolation("CAPACITY_PAYLOAD_REJECTED")
    if isinstance(value, Mapping):
        if any(str(key).lower() in FORBIDDEN_CONTROL_KEYS for key in value):
            raise CapacityViolation("CAPACITY_ACTIVE_PREEMPTION_FORBIDDEN")
        for item in value.values():
            _scan_forbidden_controls(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _scan_forbidden_controls(item, depth + 1)


def _validate_dispatches(
    *,
    decision: Mapping[str, Any],
    tickets: Mapping[str, ValidatedTicket],
    actionable: tuple[str, ...],
    idle_slots: int,
    reserved_resources: Sequence[str],
    policy: PolicyContext,
) -> tuple[tuple[Mapping[str, Any], ...], tuple[str, ...]]:
    raw = decision.get("dispatches")
    if not isinstance(raw, list) or len(raw) > idle_slots:
        raise CapacityViolation("CAPACITY_DISPATCH_INVALID")
    expected_ids = actionable[: min(idle_slots, len(actionable))]
    actual_ids: list[str] = []
    current_reserved = list(reserved_resources)
    for index, item in enumerate(raw):
        lane = _mapping(item, "CAPACITY_DISPATCH_INVALID")
        _exact_fields(lane, DISPATCH_FIELDS, "CAPACITY_DISPATCH_INVALID")
        ticket_id = _ticket_id(lane.get("ticket_id"), "CAPACITY_DISPATCH_INVALID")
        actual_ids.append(ticket_id)
        if index >= len(expected_ids) or ticket_id != expected_ids[index]:
            raise CapacityViolation("CAPACITY_RULE11_ORDER_INVALID")
        ticket = tickets[ticket_id]
        source = ticket.raw
        authorization = ticket.authorization
        selected_alias = (
            ticket.decision.get("selected_alias") if ticket.decision else None
        )
        provider_free_fallback = source.get("lane_role") == "SHORT_FALLBACK"
        expected_execution_alias = (
            "native" if provider_free_fallback else selected_alias
        )
        if not provider_free_fallback and authorization is None:
            raise CapacityViolation("CAPACITY_PROVIDER_AUTHORIZATION_INVALID")
        resources = _resources(lane.get("ownership"))
        expected_auth = _authorization_bindings(authorization)
        if (
            lane.get("lane_type") != source.get("lane_type")
            or lane.get("lane_role") != source.get("lane_role")
            or lane.get("required_role") != source.get("required_role")
            or lane.get("execution_alias") != expected_execution_alias
            or lane.get("owner") != source.get("owner")
            or resources != _resources(source.get("ownership"))
            or lane.get("decision_sha256") != ticket.decision_sha256
            or lane.get("policy_version") != policy.version
            or lane.get("policy_sha256") != policy.digest
            or lane.get("execution_window_sha256") != ticket.execution_window_sha256
            or lane.get("short_fallback_sha256") != ticket.short_fallback_sha256
            or (
                lane.get("authorization_id"),
                lane.get("authorization_sha256"),
                lane.get("provider_evidence_id"),
                lane.get("provider_evidence_sha256"),
            )
            != expected_auth
        ):
            raise CapacityViolation("CAPACITY_DISPATCH_BINDING_INVALID")
        if provider_free_fallback:
            if authorization is not None or any(
                value is not None for value in expected_auth
            ):
                raise CapacityViolation("CAPACITY_PROVIDER_AUTHORIZATION_INVALID")
        elif selected_alias not in GOVERNED_ALIASES:
            raise CapacityViolation("CAPACITY_DISPATCH_BINDING_INVALID")
        if _has_conflict(resources, current_reserved):
            raise CapacityViolation("CAPACITY_OWNERSHIP_CONFLICT")
        current_reserved.extend(resources)
    if tuple(actual_ids) != expected_ids:
        raise CapacityViolation("CAPACITY_REFILL_INCOMPLETE")
    return tuple(_mapping(item, "CAPACITY_DISPATCH_INVALID") for item in raw), tuple(
        current_reserved
    )


def _expected_rejected_candidates(
    *,
    tickets: Mapping[str, ValidatedTicket],
    active_ticket_ids: frozenset[str],
    dispatched_ids: frozenset[str],
    actionable: tuple[str, ...],
    reserved_resources: Sequence[str],
) -> list[dict[str, Any]]:
    expected: list[dict[str, Any]] = []
    for ticket_id in sorted(tickets, key=lambda item: item.encode("ascii")):
        raw = tickets[ticket_id].raw
        if (
            ticket_id in active_ticket_ids
            or ticket_id in dispatched_ids
            or raw.get("status") in TERMINAL_TICKET_STATES
        ):
            continue
        reasons = set(_ticket_rejection_reasons(ticket_id, tickets, reserved_resources))
        if ticket_id not in actionable:
            reasons.add("NOT_SELECTED_BY_RULE11")
        if not reasons:
            raise CapacityViolation("CAPACITY_RESIDUAL_EXCEPTION_INVALID")
        expected.append({"ticket_id": ticket_id, "reason_codes": sorted(reasons)})
    return expected


def _validate_capacity_exception(
    value: Any,
    *,
    residual_slots: int,
    tickets: Mapping[str, ValidatedTicket],
    active_ticket_ids: frozenset[str],
    dispatched_ids: frozenset[str],
    actionable: tuple[str, ...],
    reserved_resources: Sequence[str],
    capacity_snapshot_sha256: str,
    scheduler_snapshot_sha256: str,
    policy_sha256: str,
    code: str,
) -> None:
    exception = _mapping(value, code)
    _exact_fields(exception, CAPACITY_EXCEPTION_FIELDS, code)
    if exception.get("type") != RESIDUAL_EXCEPTION_TYPE:
        raise CapacityViolation(code)
    if _integer(exception.get("residual_slots"), code, 1, 64) != residual_slots:
        raise CapacityViolation(code)
    expected = _expected_rejected_candidates(
        tickets=tickets,
        active_ticket_ids=active_ticket_ids,
        dispatched_ids=dispatched_ids,
        actionable=actionable,
        reserved_resources=reserved_resources,
    )
    if exception.get("rejected_candidates") != expected:
        raise CapacityViolation(code)
    expected_reasons = {"NO_USEFUL_INDEPENDENT_LANE"}
    for item in expected:
        expected_reasons.update(item["reason_codes"])
    if exception.get("reasons") != sorted(expected_reasons):
        raise CapacityViolation(code)
    evidence = _mapping(exception.get("evidence"), code)
    _exact_fields(evidence, CAPACITY_EXCEPTION_EVIDENCE_FIELDS, code)
    if (
        evidence.get("rejected_candidates") != len(expected)
        or evidence.get("capacity_snapshot_sha256") != capacity_snapshot_sha256
        or evidence.get("scheduler_snapshot_sha256") != scheduler_snapshot_sha256
        or evidence.get("policy_sha256") != policy_sha256
    ):
        raise CapacityViolation(code)


def _capacity_snapshot_sha256(payload: Mapping[str, Any], event_type: str) -> str:
    return _sha256(
        {
            "schema_version": payload.get("schema_version"),
            "scope": payload.get("scope"),
            "event_type": event_type,
            "session_id": payload.get("session_id"),
            "checkpoint_sequence": payload.get("checkpoint_sequence"),
            "max_slots": payload.get("max_slots"),
            "active_slots": payload.get("active_slots"),
            "ticket_snapshot": payload.get("ticket_snapshot"),
            "ownership_snapshot": payload.get("ownership_snapshot"),
            "actionable_work": payload.get("actionable_work"),
        }
    )


def _alias_reasons(
    *,
    alias: str,
    candidate_id: str | None,
    tickets: Mapping[str, ValidatedTicket],
    actionable: tuple[str, ...],
    reserved_resources: Sequence[str],
    qa_priority_ticket: str | None,
) -> tuple[str, ...]:
    reasons = {"CAPACITY_ALIAS_RUNTIME_PROOF_UNAVAILABLE"}
    if candidate_id is None:
        reasons.add("NO_CANDIDATE_TICKET")
        return tuple(sorted(reasons))
    ticket = tickets[candidate_id]
    reasons.update(_ticket_rejection_reasons(candidate_id, tickets, reserved_resources))
    if candidate_id not in actionable:
        reasons.add("NOT_SELECTED_BY_RULE11")
        selected_resources = [
            resource
            for selected_id in actionable
            for resource in _resources(tickets[selected_id].raw.get("ownership"))
        ]
        if _has_conflict(_resources(ticket.raw.get("ownership")), selected_resources):
            reasons.add("OWNERSHIP_CONFLICT")
    if ticket.decision is None or ticket.decision.get("selected_alias") != alias:
        reasons.add("ALIAS_DECISION_MISMATCH")
    if ticket.authorization is None:
        reasons.add("PROVIDER_AUTHORIZATION_NOT_PROVEN")
    if (
        qa_priority_ticket is not None
        and ticket.raw.get("lane_role") == "SHORT_FALLBACK"
    ):
        reasons.add("QA_PRIORITY")
    if any(reason not in ALIAS_REASON_CODES for reason in reasons):
        raise CapacityViolation("CAPACITY_ALIAS_REASONS_INVALID")
    return tuple(sorted(reasons))


def _validate_alias_evaluations(
    record: Mapping[str, Any],
    *,
    tickets: Mapping[str, ValidatedTicket],
    actionable: tuple[str, ...],
    reserved_resources: Sequence[str],
    qa_priority_ticket: str | None,
    config: GuardConfig | None = None,
) -> None:
    # Stage A config cannot enable positive AGY semantics. Keep the argument for
    # compatibility with direct validators, but never treat it as runtime proof.
    _ = config
    raw = record.get("alias_evaluations")
    if not isinstance(raw, list) or len(raw) != 2:
        raise CapacityViolation("CAPACITY_ALIAS_EVALUATIONS_INVALID")
    if [
        item.get("alias") if isinstance(item, Mapping) else None for item in raw
    ] != list(EXPECTED_ALIASES):
        raise CapacityViolation("CAPACITY_ALIAS_EVALUATIONS_INVALID")
    for alias, item in zip(EXPECTED_ALIASES, raw, strict=True):
        entry = _mapping(item, "CAPACITY_ALIAS_EVALUATIONS_INVALID")
        _exact_fields(
            entry, ALIAS_EVALUATION_FIELDS, "CAPACITY_ALIAS_EVALUATIONS_INVALID"
        )
        if (
            entry.get("evaluation") != "EVALUATED"
            or entry.get("eligibility") != "NOT_ELIGIBLE"
            or entry.get("dispatched") is not False
            or entry.get("receipt") is not None
        ):
            raise CapacityViolation("CAPACITY_ALIAS_RUNTIME_PROOF_UNAVAILABLE")
        candidate = entry.get("candidate_ticket_id")
        if candidate is not None:
            candidate = _ticket_id(candidate, "CAPACITY_ALIAS_EVALUATIONS_INVALID")
            if candidate not in tickets:
                raise CapacityViolation("CAPACITY_ALIAS_EVALUATIONS_INVALID")
        expected_reasons = _alias_reasons(
            alias=alias,
            candidate_id=candidate,
            tickets=tickets,
            actionable=actionable,
            reserved_resources=reserved_resources,
            qa_priority_ticket=qa_priority_ticket,
        )
        if entry.get("reason_codes") != list(expected_reasons):
            raise CapacityViolation("CAPACITY_ALIAS_REASONS_INVALID")
        authorization = (
            tickets[candidate].authorization if candidate is not None else None
        )
        if (
            entry.get("authorization_id"),
            entry.get("authorization_sha256"),
            entry.get("provider_evidence_id"),
            entry.get("provider_evidence_sha256"),
        ) != _authorization_bindings(authorization):
            raise CapacityViolation("CAPACITY_ALIAS_BINDING_INVALID")
    fairness = _mapping(record.get("fairness"), "CAPACITY_ALIAS_FAIRNESS_INVALID")
    _exact_fields(fairness, FAIRNESS_FIELDS, "CAPACITY_ALIAS_FAIRNESS_INVALID")
    sequence = int(record["sequence"])
    last_served = _mapping(
        fairness.get("last_served_sequence"), "CAPACITY_ALIAS_FAIRNESS_INVALID"
    )
    if set(last_served) != set(EXPECTED_ALIASES):
        raise CapacityViolation("CAPACITY_ALIAS_FAIRNESS_INVALID")
    for alias in EXPECTED_ALIASES:
        _integer(
            last_served.get(alias), "CAPACITY_ALIAS_FAIRNESS_INVALID", 0, sequence - 1
        )
    if (
        fairness.get("strategy") != "LEAST_RECENTLY_SERVED_AFTER_GATES"
        or fairness.get("eligible_order") != []
        or fairness.get("selected_aliases") != []
        or fairness.get("rule11_selection_sha256") != _sha256(list(actionable))
    ):
        raise CapacityViolation("CAPACITY_ALIAS_FAIRNESS_INVALID")


def _validate_handoff(
    record: Mapping[str, Any],
    *,
    tickets: Mapping[str, ValidatedTicket],
    active_ticket_ids: frozenset[str],
    active_roles: Mapping[str, str],
    actionable: tuple[str, ...],
    idle_slots: int,
    dispatches: tuple[Mapping[str, Any], ...],
) -> str | None:
    handoff = _mapping(record.get("source_qa_handoff"), "CAPACITY_QA_HANDOFF_INVALID")
    _exact_fields(handoff, HANDOFF_FIELDS, "CAPACITY_QA_HANDOFF_INVALID")
    claimed_handoff = _valid_sha256(
        handoff.get("handoff_sha256"), "CAPACITY_QA_HANDOFF_INVALID"
    )
    unsigned = dict(handoff)
    unsigned.pop("handoff_sha256", None)
    if _sha256(unsigned) != claimed_handoff:
        raise CapacityViolation("CAPACITY_QA_HANDOFF_INVALID")
    source_ids = _string_ids(
        handoff.get("source_ticket_ids"),
        ticket_ids=True,
        code="CAPACITY_QA_HANDOFF_INVALID",
        max_items=len(tickets),
    )
    if list(source_ids) != sorted(source_ids, key=lambda item: item.encode("ascii")):
        raise CapacityViolation("CAPACITY_QA_HANDOFF_INVALID")
    if any(
        ticket_id not in tickets
        or tickets[ticket_id].raw.get("lane_role") not in SOURCE_ROLES
        for ticket_id in source_ids
    ):
        raise CapacityViolation("CAPACITY_QA_HANDOFF_INVALID")
    active_sources = {
        ticket_id for ticket_id, role in active_roles.items() if role in SOURCE_ROLES
    }
    if not active_sources.issubset(source_ids):
        raise CapacityViolation("CAPACITY_QA_HANDOFF_INVALID")
    if not source_ids:
        source_state = "NONE"
    elif active_sources:
        source_state = "ACTIVE"
    elif all(
        tickets[ticket_id].raw.get("status") == "DONE" for ticket_id in source_ids
    ):
        source_state = "FROZEN"
    else:
        raise CapacityViolation("CAPACITY_QA_HANDOFF_INVALID")
    if handoff.get("source_state") != source_state:
        raise CapacityViolation("CAPACITY_QA_HANDOFF_INVALID")

    qa_ticket_id = handoff.get("qa_ticket_id")
    if qa_ticket_id is None:
        if source_ids:
            raise CapacityViolation("CAPACITY_QA_HANDOFF_INVALID")
        qa_state = "NONE"
    else:
        qa_ticket_id = _ticket_id(qa_ticket_id, "CAPACITY_QA_HANDOFF_INVALID")
        if (
            qa_ticket_id not in tickets
            or tickets[qa_ticket_id].raw.get("lane_role") != "QA"
        ):
            raise CapacityViolation("CAPACITY_QA_HANDOFF_INVALID")
        if qa_ticket_id in active_ticket_ids:
            qa_state = "ACTIVE"
        elif tickets[qa_ticket_id].raw.get("status") in TERMINAL_TICKET_STATES:
            qa_state = "COMPLETE"
        elif qa_ticket_id in actionable:
            qa_state = "ELIGIBLE"
        else:
            qa_state = "WAITING_FOR_SOURCE_FREEZE"
    if handoff.get("qa_state") != qa_state:
        raise CapacityViolation("CAPACITY_QA_HANDOFF_INVALID")
    if source_state == "ACTIVE" and qa_state not in {
        "WAITING_FOR_SOURCE_FREEZE",
        "COMPLETE",
    }:
        raise CapacityViolation("CAPACITY_QA_HANDOFF_INVALID")
    if source_state == "FROZEN" and qa_state == "WAITING_FOR_SOURCE_FREEZE":
        raise CapacityViolation("CAPACITY_QA_HANDOFF_INVALID")

    running_fallbacks = sorted(
        (
            ticket_id
            for ticket_id, role in active_roles.items()
            if role == "SHORT_FALLBACK"
        ),
        key=lambda item: item.encode("ascii"),
    )
    if handoff.get("running_fallback_ticket_ids") != running_fallbacks:
        raise CapacityViolation("CAPACITY_QA_HANDOFF_INVALID")
    priority_required = (
        source_state == "FROZEN" and qa_state == "ELIGIBLE" and idle_slots == 0
    )
    if handoff.get("qa_next_slot_priority") is not priority_required:
        raise CapacityViolation("CAPACITY_QA_PRIORITY_INVALID")
    dispatch_ids = [lane.get("ticket_id") for lane in dispatches]
    if source_state == "ACTIVE" and qa_ticket_id in dispatch_ids:
        raise CapacityViolation("CAPACITY_QA_HANDOFF_INVALID")
    if source_state == "FROZEN" and qa_state == "ELIGIBLE" and idle_slots > 0:
        if qa_ticket_id not in dispatch_ids:
            raise CapacityViolation("CAPACITY_QA_PRIORITY_VIOLATION")
        qa_index = dispatch_ids.index(qa_ticket_id)
        if any(
            lane.get("lane_role") == "SHORT_FALLBACK" for lane in dispatches[:qa_index]
        ):
            raise CapacityViolation("CAPACITY_QA_PRIORITY_VIOLATION")
        return str(qa_ticket_id)
    return str(qa_ticket_id) if priority_required else None


def _normalized_tool_name(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    folded = value.casefold()
    canonical = {
        "task": "Task",
        "bash": "Bash",
        "run_command": "run_command",
        "shell": "shell",
    }.get(folded)
    if canonical is not None:
        return canonical
    return folded if folded.startswith("terminal") else value


def _canonical_envelope_equivalent(left: Any, right: Any) -> bool:
    try:
        return _sha256(left) == _sha256(right)
    except CapacityViolation as exc:
        raise CapacityViolation("CAPACITY_TOOL_ENVELOPE_CONFLICT") from exc


def _resolved_event_tool(
    event: Mapping[str, Any],
) -> tuple[str | None, Mapping[str, Any] | None]:
    top_name_present = "tool_name" in event
    top_input_present = "tool_input" in event
    nested_present = "toolCall" in event
    nested = event.get("toolCall")
    if nested_present and not isinstance(nested, Mapping):
        raise CapacityViolation("CAPACITY_TOOL_ENVELOPE_CONFLICT")

    nested_name_present = isinstance(nested, Mapping) and "name" in nested
    nested_input_present = isinstance(nested, Mapping) and "args" in nested
    top_shape_present = top_name_present or top_input_present
    if top_shape_present and nested_present:
        if not (
            top_name_present
            and top_input_present
            and nested_name_present
            and nested_input_present
        ):
            raise CapacityViolation("CAPACITY_TOOL_ENVELOPE_CONFLICT")
        top_name = _normalized_tool_name(event.get("tool_name"))
        nested_name = _normalized_tool_name(nested.get("name"))
        top_input = event.get("tool_input")
        nested_input = nested.get("args")
        if (
            top_name is None
            or nested_name is None
            or top_name != nested_name
            or not isinstance(top_input, Mapping)
            or not isinstance(nested_input, Mapping)
            or not _canonical_envelope_equivalent(top_input, nested_input)
        ):
            raise CapacityViolation("CAPACITY_TOOL_ENVELOPE_CONFLICT")
        return top_name, top_input

    if nested_present:
        if not nested_name_present or not nested_input_present:
            raise CapacityViolation("CAPACITY_TOOL_ENVELOPE_CONFLICT")
        nested_name = _normalized_tool_name(nested.get("name"))
        nested_input = nested.get("args")
        return (
            nested_name,
            nested_input if isinstance(nested_input, Mapping) else None,
        )

    top_name = _normalized_tool_name(event.get("tool_name"))
    top_input = event.get("tool_input")
    return top_name, top_input if isinstance(top_input, Mapping) else None


def _event_tool_response(event: Mapping[str, Any]) -> Any:
    top_present = "tool_response" in event
    nested_present = "toolResult" in event
    if top_present and nested_present:
        top = event.get("tool_response")
        nested = event.get("toolResult")
        if not _canonical_envelope_equivalent(top, nested):
            raise CapacityViolation("CAPACITY_TOOL_ENVELOPE_CONFLICT")
        return top
    if top_present:
        return event.get("tool_response")
    if nested_present:
        return event.get("toolResult")
    return None


def _provider_executing_tool(tool_name: str | None) -> bool:
    if tool_name == "Task":
        return True
    return tool_name in {"Bash", "run_command", "shell"} or (
        isinstance(tool_name, str) and tool_name.lower().startswith("terminal")
    )


def _provider_executing_event(event: Mapping[str, Any]) -> bool:
    tool_name, _ = _resolved_event_tool(event)
    return _provider_executing_tool(tool_name)


def _nested_capacity(value: Any) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    wrapper = value.get("capacity_decision")
    if not isinstance(wrapper, Mapping):
        return None
    candidate = wrapper.get("full_capacity", wrapper)
    return candidate if isinstance(candidate, Mapping) else None


def _strip_capacity(value: Any) -> Any:
    if not isinstance(value, Mapping):
        return value
    return {key: item for key, item in value.items() if key != "capacity_decision"}


def _record_digest_from_payload(value: Mapping[str, Any]) -> str:
    record = _mapping(
        value.get("governance_record"), "CAPACITY_LIFECYCLE_BINDING_INVALID"
    )
    claimed = _valid_sha256(
        record.get("record_sha256"), "CAPACITY_LIFECYCLE_BINDING_INVALID"
    )
    if value.get("capacity_record_sha256") != claimed:
        raise CapacityViolation("CAPACITY_LIFECYCLE_BINDING_INVALID")
    unsigned = dict(record)
    unsigned.pop("record_sha256", None)
    if _sha256(unsigned) != claimed:
        raise CapacityViolation("CAPACITY_LIFECYCLE_BINDING_INVALID")
    return claimed


def _extract_event(
    event: Mapping[str, Any],
) -> tuple[Mapping[str, Any] | None, EventContext]:
    tool_name, tool_input = _resolved_event_tool(event)
    provider_executing = _provider_executing_tool(tool_name)
    hook_name = event.get("hook_event_name")
    input_payload = _nested_capacity(tool_input)
    direct_payload = _nested_capacity(event)

    if hook_name == "PreToolUse":
        payload = input_payload
        if payload is None:
            if provider_executing:
                raise CapacityViolation("CAPACITY_PROVIDER_EVENT_ENVELOPE_REQUIRED")
            return None, EventContext("CHECKPOINT", None, None, None, None, None, False)
        tool_use_id = _safe_id(
            event.get("tool_use_id"), "CAPACITY_TOOL_USE_BINDING_INVALID"
        )
        if tool_name is None:
            raise CapacityViolation("CAPACITY_TOOL_USE_BINDING_INVALID")
        return payload, EventContext(
            lifecycle_phase="PRE_DISPATCH",
            tool_name=_safe_id(tool_name, "CAPACITY_TOOL_USE_BINDING_INVALID"),
            tool_use_id=tool_use_id,
            tool_input_sha256=_sha256(_strip_capacity(tool_input)),
            pre_dispatch_record_sha256=None,
            tool_result_sha256=None,
            provider_executing=provider_executing,
        )

    if hook_name == "PostToolUse":
        response = _event_tool_response(event)
        response_payload = _nested_capacity(response)
        if input_payload is None or response_payload is None:
            if provider_executing:
                raise CapacityViolation("CAPACITY_PROVIDER_EVENT_ENVELOPE_REQUIRED")
            return None, EventContext("CHECKPOINT", None, None, None, None, None, False)
        tool_use_id = _safe_id(
            event.get("tool_use_id"), "CAPACITY_TOOL_USE_BINDING_INVALID"
        )
        if tool_name is None:
            raise CapacityViolation("CAPACITY_TOOL_USE_BINDING_INVALID")
        return response_payload, EventContext(
            lifecycle_phase="POST_RESULT",
            tool_name=_safe_id(tool_name, "CAPACITY_TOOL_USE_BINDING_INVALID"),
            tool_use_id=tool_use_id,
            tool_input_sha256=_sha256(_strip_capacity(tool_input)),
            pre_dispatch_record_sha256=_record_digest_from_payload(input_payload),
            tool_result_sha256=_sha256(_strip_capacity(response)),
            provider_executing=provider_executing,
        )

    payload = direct_payload
    if payload is None and isinstance(event.get("capacity_decision"), Mapping):
        candidate = event["capacity_decision"]
        payload = candidate.get("full_capacity", candidate)
        if not isinstance(payload, Mapping):
            raise CapacityViolation("CAPACITY_PAYLOAD_REJECTED")
    if payload is None:
        if provider_executing:
            raise CapacityViolation("CAPACITY_PROVIDER_EVENT_ENVELOPE_REQUIRED")
        return None, EventContext("CHECKPOINT", None, None, None, None, None, False)
    return payload, EventContext("CHECKPOINT", None, None, None, None, None, False)


def _normalize_event_type(payload: Mapping[str, Any]) -> str:
    value = payload.get("event_type")
    value = EVENT_TYPE_ALIASES.get(value, value)
    if value not in EVENT_TYPES:
        raise CapacityViolation("CAPACITY_EVENT_INVALID")
    return str(value)


def _validate_governance_record(
    *,
    payload: Mapping[str, Any],
    event: EventContext,
    config: GuardConfig,
    policy: PolicyContext,
    event_type: str,
    scheduler_snapshot_sha256: str,
    decision: Mapping[str, Any],
) -> Mapping[str, Any]:
    record = _mapping(
        payload.get("governance_record"), "CAPACITY_GOVERNANCE_RECORD_REQUIRED"
    )
    _exact_fields(record, GOVERNANCE_FIELDS, "CAPACITY_GOVERNANCE_RECORD_INVALID")
    if (
        record.get("schema_version") != GOVERNANCE_SCHEMA_VERSION
        or record.get("config_sha256") != config.digest
    ):
        raise CapacityViolation("CAPACITY_GOVERNANCE_VERSION_INVALID")
    session_id = _safe_id(record.get("session_id"), "CAPACITY_SESSION_MISMATCH")
    sequence = _integer(
        record.get("sequence"),
        "CAPACITY_CHECKPOINT_STALE_OR_REPLAYED",
        1,
        1_000_000_000,
    )
    previous_sequence = _integer(
        record.get("previous_sequence"),
        "CAPACITY_CHECKPOINT_STALE_OR_REPLAYED",
        0,
        sequence - 1,
    )
    previous_record = record.get("previous_record_sha256")
    if sequence == 1:
        if previous_record != GENESIS_RECORD:
            raise CapacityViolation("CAPACITY_CHECKPOINT_STALE_OR_REPLAYED")
    else:
        _valid_sha256(previous_record, "CAPACITY_CHECKPOINT_STALE_OR_REPLAYED")
    if (
        payload.get("session_id") != session_id
        or payload.get("checkpoint_sequence") != sequence
        or payload.get("previous_checkpoint_sequence") != previous_sequence
        or previous_sequence != sequence - 1
        or payload.get("previous_capacity_record_sha256") != previous_record
    ):
        raise CapacityViolation("CAPACITY_CHECKPOINT_STALE_OR_REPLAYED")
    if (
        record.get("lifecycle_phase") != event.lifecycle_phase
        or record.get("tool_name") != event.tool_name
        or record.get("tool_use_id") != event.tool_use_id
        or record.get("tool_input_sha256") != event.tool_input_sha256
        or record.get("pre_dispatch_record_sha256") != event.pre_dispatch_record_sha256
        or record.get("tool_result_sha256") != event.tool_result_sha256
    ):
        raise CapacityViolation("CAPACITY_LIFECYCLE_BINDING_INVALID")
    capacity_snapshot = _capacity_snapshot_sha256(payload, event_type)
    if record.get("capacity_snapshot_sha256") != capacity_snapshot:
        raise CapacityViolation("CAPACITY_SNAPSHOT_HASH_INVALID")
    if record.get("scheduler_snapshot_sha256") != scheduler_snapshot_sha256:
        raise CapacityViolation("CAPACITY_SCHEDULER_SNAPSHOT_INVALID")
    if (
        record.get("policy_version") != policy.version
        or record.get("policy_sha256") != policy.digest
    ):
        raise CapacityViolation("CAPACITY_POLICY_BINDING_INVALID")
    dependency_digests = _mapping(
        record.get("dependency_digests"), "CAPACITY_DEPENDENCY_BINDING_INVALID"
    )
    _exact_fields(
        dependency_digests,
        DEPENDENCY_DIGEST_FIELDS,
        "CAPACITY_DEPENDENCY_BINDING_INVALID",
    )
    if (
        dependency_digests != config.dependency_digests
        or record.get("dependency_manifest_sha256") != config.dependency_manifest_sha256
    ):
        raise CapacityViolation("CAPACITY_DEPENDENCY_BINDING_INVALID")
    if record.get("decision_sha256") != _sha256(decision):
        raise CapacityViolation("CAPACITY_DECISION_HASH_INVALID")
    boundaries = _mapping(
        record.get("proof_boundaries"), "CAPACITY_RUNTIME_PROOF_OVERCLAIM"
    )
    _exact_fields(boundaries, PROOF_BOUNDARY_FIELDS, "CAPACITY_RUNTIME_PROOF_OVERCLAIM")
    if any(value != "NOT_PROVEN" for value in boundaries.values()):
        raise CapacityViolation("CAPACITY_RUNTIME_PROOF_OVERCLAIM")
    claimed = _valid_sha256(record.get("record_sha256"), "CAPACITY_RECORD_HASH_INVALID")
    unsigned = dict(record)
    unsigned.pop("record_sha256", None)
    if _sha256(unsigned) != claimed or payload.get("capacity_record_sha256") != claimed:
        raise CapacityViolation("CAPACITY_RECORD_HASH_INVALID")
    if previous_record == claimed:
        raise CapacityViolation("CAPACITY_CHECKPOINT_STALE_OR_REPLAYED")
    return record


def _validate_payload(
    payload: Mapping[str, Any], event: EventContext
) -> ValidationState:
    config = _load_config()
    policy = _load_policy(config)
    _exact_fields(payload, CAPACITY_PAYLOAD_FIELDS, "CAPACITY_PAYLOAD_SCHEMA_INVALID")
    if payload.get("schema_version") != GOVERNANCE_SCHEMA_VERSION:
        raise CapacityViolation("CAPACITY_GOVERNANCE_VERSION_INVALID")
    if payload.get("scope") not in MATCHED_SCOPES:
        raise CapacityViolation("CAPACITY_EVENT_INVALID")
    if _contains_secret(payload):
        raise CapacityViolation("CAPACITY_PAYLOAD_REJECTED")
    _scan_forbidden_controls(payload)
    event_type = _normalize_event_type(payload)
    if event.lifecycle_phase == "PRE_DISPATCH" and event_type != "dispatch":
        raise CapacityViolation("CAPACITY_LIFECYCLE_BINDING_INVALID")
    if event.lifecycle_phase == "POST_RESULT" and event_type not in {
        "agent_completed",
        "agent_failed",
    }:
        raise CapacityViolation("CAPACITY_LIFECYCLE_BINDING_INVALID")
    max_slots = _integer(
        payload.get("max_slots"),
        "CAPACITY_SLOT_DECLARATION_INVALID",
        1,
        config.max_slots,
    )
    active_slots = _integer(
        payload.get("active_slots"),
        "CAPACITY_SLOT_DECLARATION_INVALID",
        0,
        max_slots,
    )
    idle_slots = max_slots - active_slots
    tickets = _validate_tickets(payload, config=config, policy=policy)
    reservations, active_ids, active_roles, reserved_resources = (
        _validate_ownership_snapshot(
            payload,
            tickets,
            active_slots=active_slots,
            max_slots=max_slots,
        )
    )
    scheduler_snapshot, actionable = _scheduler_state(
        tickets=tickets, reservations=reservations, policy=policy
    )
    submitted_actionable = _string_ids(
        payload.get("actionable_work"),
        ticket_ids=True,
        code="CAPACITY_ACTIONABLE_WORK_INVALID",
        max_items=config.max_tickets,
    )
    if submitted_actionable != actionable:
        raise CapacityViolation("CAPACITY_ACTIONABLE_WORK_INCOMPLETE")
    decision = _mapping(payload.get("decision"), "CAPACITY_DECISION_INVALID")
    _exact_fields(decision, DECISION_FIELDS, "CAPACITY_DECISION_INVALID")
    action = decision.get("action")
    if not isinstance(action, str):
        raise CapacityViolation("CAPACITY_DECISION_INVALID")
    if (
        event_type in {"agent_completed", "agent_failed"}
        and decision.get("recomputed") is not True
    ):
        raise CapacityViolation("CAPACITY_RECOMPUTE_REQUIRED")
    if not isinstance(decision.get("decomposition"), list):
        raise CapacityViolation("CAPACITY_DECOMPOSITION_INVALID")
    decomposition = _string_ids(
        decision.get("decomposition"),
        ticket_ids=True,
        code="CAPACITY_DECOMPOSITION_INVALID",
        max_items=config.max_tickets,
    )
    if action == "DECOMPOSE_AND_DISPATCH" and not decomposition:
        raise CapacityViolation("CAPACITY_DECOMPOSITION_INVALID")
    if action != "DECOMPOSE_AND_DISPATCH" and decomposition:
        raise CapacityViolation("CAPACITY_DECOMPOSITION_INVALID")

    dispatches: tuple[Mapping[str, Any], ...] = ()
    reserved_after = reserved_resources
    if actionable and idle_slots > 0:
        if action not in ACTIVE_ACTIONS:
            raise CapacityViolation("CAPACITY_ACTION_REQUIRED")
        if event_type in {"agent_completed", "agent_failed"} and action != "REFILL":
            raise CapacityViolation("CAPACITY_REFILL_REQUIRED")
        dispatches, reserved_after = _validate_dispatches(
            decision=decision,
            tickets=tickets,
            actionable=actionable,
            idle_slots=idle_slots,
            reserved_resources=reserved_resources,
            policy=policy,
        )
    elif action in ACTIVE_ACTIONS:
        raise CapacityViolation("CAPACITY_FAKE_OR_DUPLICATE_LANE")
    else:
        raw_dispatches = decision.get("dispatches")
        if raw_dispatches != []:
            raise CapacityViolation("CAPACITY_DISPATCH_INVALID")

    capacity_snapshot = _capacity_snapshot_sha256(payload, event_type)
    dispatched_ids = frozenset(str(lane.get("ticket_id")) for lane in dispatches)
    residual_slots = idle_slots - len(dispatches)
    if action == REPLAN_ACTION:
        if actionable or idle_slots < 1:
            raise CapacityViolation("CAPACITY_ACTION_REQUIRED")
        _validate_capacity_exception(
            decision.get("capacity_exception"),
            residual_slots=idle_slots,
            tickets=tickets,
            active_ticket_ids=active_ids,
            dispatched_ids=frozenset(),
            actionable=actionable,
            reserved_resources=reserved_resources,
            capacity_snapshot_sha256=capacity_snapshot,
            scheduler_snapshot_sha256=scheduler_snapshot.digest,
            policy_sha256=policy.digest,
            code="CAPACITY_REPLAN_EVIDENCE_INVALID",
        )
        if decision.get("residual_capacity_exception") is not None:
            raise CapacityViolation("CAPACITY_RESIDUAL_EXCEPTION_INVALID")
    else:
        if decision.get("capacity_exception") is not None:
            raise CapacityViolation("CAPACITY_REPLAN_EVIDENCE_INVALID")
        if residual_slots > 0 and dispatches:
            _validate_capacity_exception(
                decision.get("residual_capacity_exception"),
                residual_slots=residual_slots,
                tickets=tickets,
                active_ticket_ids=active_ids,
                dispatched_ids=dispatched_ids,
                actionable=actionable,
                reserved_resources=reserved_after,
                capacity_snapshot_sha256=capacity_snapshot,
                scheduler_snapshot_sha256=scheduler_snapshot.digest,
                policy_sha256=policy.digest,
                code="CAPACITY_RESIDUAL_EXCEPTION_INVALID",
            )
        elif decision.get("residual_capacity_exception") is not None:
            raise CapacityViolation("CAPACITY_RESIDUAL_EXCEPTION_INVALID")

    unfinished = any(
        ticket.raw.get("status") not in TERMINAL_TICKET_STATES
        for ticket in tickets.values()
    )
    if not actionable:
        if unfinished and idle_slots > 0 and action != REPLAN_ACTION:
            raise CapacityViolation("CAPACITY_REPLAN_REQUIRED")
        if unfinished and idle_slots == 0 and action != "CONTINUE":
            raise CapacityViolation("CAPACITY_TERMINAL_INVALID")
        if not unfinished and (active_slots != 0 or action != "TERMINAL"):
            raise CapacityViolation("CAPACITY_TERMINAL_INVALID")

    record = _validate_governance_record(
        payload=payload,
        event=event,
        config=config,
        policy=policy,
        event_type=event_type,
        scheduler_snapshot_sha256=scheduler_snapshot.digest,
        decision=decision,
    )
    qa_priority_ticket = _validate_handoff(
        record,
        tickets=tickets,
        active_ticket_ids=active_ids,
        active_roles=active_roles,
        actionable=actionable,
        idle_slots=idle_slots,
        dispatches=dispatches,
    )
    _validate_alias_evaluations(
        record,
        tickets=tickets,
        actionable=actionable,
        reserved_resources=reserved_resources,
        qa_priority_ticket=qa_priority_ticket,
        config=config,
    )

    block_code: str | None = None
    if dispatches:
        if any(lane.get("execution_alias") in EXPECTED_ALIASES for lane in dispatches):
            block_code = "CAPACITY_ALIAS_RUNTIME_PROOF_UNAVAILABLE"
        else:
            block_code = "CAPACITY_AUTHORITATIVE_SNAPSHOT_NOT_PROVEN"
    elif event.provider_executing:
        block_code = "CAPACITY_AUTHORITATIVE_SNAPSHOT_NOT_PROVEN"
    expected_status = {
        "CAPACITY_ALIAS_RUNTIME_PROOF_UNAVAILABLE": "BLOCKED_ALIAS_RUNTIME_PROOF",
        "CAPACITY_AUTHORITATIVE_SNAPSHOT_NOT_PROVEN": "BLOCKED_AUTHORITATIVE_SNAPSHOT",
    }.get(block_code)
    if expected_status is None:
        expected_status = "TERMINAL" if event_type == "terminal" else "OBSERVED"
    if record.get("lifecycle_status") != expected_status:
        raise CapacityViolation("CAPACITY_LIFECYCLE_STATUS_INVALID")

    return ValidationState(
        config=config,
        policy=policy,
        event=event,
        payload=payload,
        event_type=event_type,
        tickets=tickets,
        scheduler_snapshot=scheduler_snapshot,
        scheduler_snapshot_sha256=scheduler_snapshot.digest,
        actionable=actionable,
        active_ticket_ids=active_ids,
        active_roles=active_roles,
        active_reserved_resources=reserved_resources,
        idle_slots=idle_slots,
        decision=decision,
        dispatches=dispatches,
        governance_record=record,
        block_code=block_code,
    )


LEDGER_TABLE_STATEMENTS = {
    "ledger_meta": """
        CREATE TABLE ledger_meta (
            singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
            schema_version INTEGER NOT NULL,
            ledger_id TEXT NOT NULL,
            global_sequence INTEGER NOT NULL,
            record_count INTEGER NOT NULL,
            session_count INTEGER NOT NULL,
            global_head_sha256 TEXT NOT NULL,
            first_recorded_at TEXT,
            last_recorded_at TEXT,
            created_at TEXT NOT NULL
        )
    """,
    "lifecycle_records": """
        CREATE TABLE lifecycle_records (
            global_sequence INTEGER NOT NULL UNIQUE,
            session_id_sha256 TEXT NOT NULL,
            checkpoint_sequence INTEGER NOT NULL,
            previous_record_sha256 TEXT NOT NULL,
            record_sha256 TEXT NOT NULL UNIQUE,
            phase TEXT NOT NULL,
            status TEXT NOT NULL,
            tool_name_sha256 TEXT,
            tool_use_id_sha256 TEXT,
            input_record_sha256 TEXT,
            tool_input_sha256 TEXT,
            tool_result_sha256 TEXT,
            recorded_at TEXT NOT NULL,
            previous_global_sha256 TEXT NOT NULL,
            global_record_sha256 TEXT NOT NULL UNIQUE,
            PRIMARY KEY (session_id_sha256, checkpoint_sequence),
            UNIQUE (session_id_sha256, previous_record_sha256),
            UNIQUE (session_id_sha256, tool_use_id_sha256, phase)
        )
    """,
    "session_heads": """
        CREATE TABLE session_heads (
            session_id_sha256 TEXT PRIMARY KEY,
            checkpoint_sequence INTEGER NOT NULL,
            record_sha256 TEXT NOT NULL,
            phase TEXT NOT NULL,
            status TEXT NOT NULL,
            tool_use_id_sha256 TEXT,
            input_record_sha256 TEXT,
            updated_at TEXT NOT NULL
        )
    """,
}
LEDGER_INDEX_STATEMENTS = {
    "lifecycle_records_session_checkpoint_idx": """
        CREATE INDEX lifecycle_records_session_checkpoint_idx
        ON lifecycle_records (session_id_sha256, checkpoint_sequence DESC)
    """,
    "lifecycle_records_recorded_at_idx": """
        CREATE INDEX lifecycle_records_recorded_at_idx
        ON lifecycle_records (recorded_at)
    """,
}
LEDGER_TRIGGER_STATEMENTS = {
    "lifecycle_records_no_update": """
        CREATE TRIGGER lifecycle_records_no_update
        BEFORE UPDATE ON lifecycle_records BEGIN
            SELECT RAISE(ABORT, 'immutable lifecycle record');
        END
    """,
    "lifecycle_records_no_delete": """
        CREATE TRIGGER lifecycle_records_no_delete
        BEFORE DELETE ON lifecycle_records BEGIN
            SELECT RAISE(ABORT, 'immutable lifecycle record');
        END
    """,
    "ledger_meta_no_delete": """
        CREATE TRIGGER ledger_meta_no_delete
        BEFORE DELETE ON ledger_meta BEGIN
            SELECT RAISE(ABORT, 'immutable ledger metadata');
        END
    """,
    "session_heads_no_delete": """
        CREATE TRIGGER session_heads_no_delete
        BEFORE DELETE ON session_heads BEGIN
            SELECT RAISE(ABORT, 'immutable session head');
        END
    """,
}
LEDGER_OBJECT_STATEMENTS = {
    **LEDGER_TABLE_STATEMENTS,
    **LEDGER_INDEX_STATEMENTS,
    **LEDGER_TRIGGER_STATEMENTS,
}
LEDGER_OBJECT_TYPES = {
    **{name: "table" for name in LEDGER_TABLE_STATEMENTS},
    **{name: "index" for name in LEDGER_INDEX_STATEMENTS},
    **{name: "trigger" for name in LEDGER_TRIGGER_STATEMENTS},
}


def _fixed_state_directory(config: GuardConfig) -> Path:
    try:
        home = Path(pwd.getpwuid(os.getuid()).pw_dir)
    except (KeyError, OSError) as exc:
        raise CapacityViolation("CAPACITY_LEDGER_PATH_INVALID") from exc
    return home.joinpath(*config.ledger_relative_directory)


def _resolved_state_directory(
    config: GuardConfig, internal_test_directory: Path | None
) -> Path:
    if internal_test_directory is None:
        return _fixed_state_directory(config)
    if not internal_test_directory.is_absolute():
        raise CapacityViolation("CAPACITY_LEDGER_PATH_INVALID")
    return internal_test_directory


def _ensure_secure_state_directory(path: Path) -> None:
    if path.exists():
        try:
            metadata = path.lstat()
        except OSError as exc:
            raise CapacityViolation("CAPACITY_LEDGER_PATH_INVALID") from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise CapacityViolation("CAPACITY_LEDGER_PATH_INVALID")
    else:
        try:
            path.mkdir(mode=0o700, parents=True, exist_ok=False)
        except OSError as exc:
            raise CapacityViolation("CAPACITY_LEDGER_PATH_INVALID") from exc
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CapacityViolation("CAPACITY_LEDGER_PATH_INVALID") from exc
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != 0o700
    ):
        raise CapacityViolation("CAPACITY_LEDGER_PATH_INVALID")
    current = path
    while current != current.parent:
        try:
            item = current.lstat()
        except OSError as exc:
            raise CapacityViolation("CAPACITY_LEDGER_PATH_INVALID") from exc
        if stat.S_ISLNK(item.st_mode):
            raise CapacityViolation("CAPACITY_LEDGER_PATH_INVALID")
        current = current.parent


def _database_bytes(connection: sqlite3.Connection) -> int:
    page_count = connection.execute("PRAGMA page_count").fetchone()
    page_size = connection.execute("PRAGMA page_size").fetchone()
    if (
        page_count is None
        or page_size is None
        or not isinstance(page_count[0], int)
        or not isinstance(page_size[0], int)
    ):
        raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED")
    return int(page_count[0]) * int(page_size[0])


def _ledger_connect(
    config: GuardConfig, *, internal_test_directory: Path | None = None
) -> sqlite3.Connection:
    directory = _resolved_state_directory(config, internal_test_directory)
    _ensure_secure_state_directory(directory)
    database = directory / config.ledger_filename
    if database.exists():
        metadata = database.lstat()
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or stat.S_IMODE(metadata.st_mode) != 0o600
        ):
            raise CapacityViolation("CAPACITY_LEDGER_PATH_INVALID")
        if metadata.st_size > config.ledger_max_bytes:
            raise CapacityViolation("CAPACITY_LEDGER_BOUND_EXCEEDED")
    old_umask = os.umask(0o077)
    try:
        connection = sqlite3.connect(
            str(database),
            timeout=config.ledger_busy_timeout_ms / 1000,
            isolation_level=None,
            check_same_thread=False,
        )
    except sqlite3.Error as exc:
        raise CapacityViolation("CAPACITY_LEDGER_FAILURE") from exc
    finally:
        os.umask(old_umask)
    try:
        metadata = database.lstat()
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or stat.S_IMODE(metadata.st_mode) != 0o600
        ):
            raise CapacityViolation("CAPACITY_LEDGER_PATH_INVALID")
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = DELETE")
        connection.execute("PRAGMA synchronous = FULL")
        connection.execute(f"PRAGMA busy_timeout = {config.ledger_busy_timeout_ms}")
        connection.execute("BEGIN IMMEDIATE")
    except CapacityViolation:
        connection.close()
        raise
    except (OSError, sqlite3.Error) as exc:
        connection.close()
        raise CapacityViolation("CAPACITY_LEDGER_FAILURE") from exc
    return connection


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _initialize_ledger(connection: sqlite3.Connection, config: GuardConfig) -> None:
    objects = connection.execute(
        "SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
    ).fetchall()
    if objects:
        return
    try:
        for statement in LEDGER_OBJECT_STATEMENTS.values():
            connection.execute(statement)
        created_at = _utc_now()
        ledger_id = hashlib.sha256(
            f"{created_at}:{os.getpid()}:{os.getuid()}".encode("ascii")
        ).hexdigest()
        connection.execute(
            "INSERT INTO ledger_meta "
            "(singleton, schema_version, ledger_id, global_sequence, record_count, "
            "session_count, global_head_sha256, first_recorded_at, last_recorded_at, "
            "created_at) VALUES (1, ?, ?, 0, 0, 0, ?, NULL, NULL, ?)",
            (config.ledger_schema_version, ledger_id, GENESIS_GLOBAL, created_at),
        )
        connection.execute(f"PRAGMA user_version = {config.ledger_schema_version}")
    except sqlite3.Error as exc:
        raise CapacityViolation("CAPACITY_LEDGER_FAILURE") from exc


def _ledger_global_material(row: Sequence[Any]) -> Mapping[str, Any]:
    return {
        "global_sequence": row[0],
        "session_id_sha256": row[1],
        "checkpoint_sequence": row[2],
        "previous_record_sha256": row[3],
        "record_sha256": row[4],
        "phase": row[5],
        "status": row[6],
        "tool_name_sha256": row[7],
        "tool_use_id_sha256": row[8],
        "input_record_sha256": row[9],
        "tool_input_sha256": row[10],
        "tool_result_sha256": row[11],
        "recorded_at": row[12],
        "previous_global_sha256": row[13],
    }


def _normalized_ddl(value: str) -> str:
    return " ".join(value.strip().rstrip(";").split())


def _validate_ledger_objects(connection: sqlite3.Connection) -> None:
    objects = connection.execute(
        "SELECT type, name, sql FROM sqlite_master "
        "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
    ).fetchall()
    observed = {str(row[1]): (str(row[0]), str(row[2])) for row in objects}
    if set(observed) != set(LEDGER_OBJECT_STATEMENTS):
        raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED")
    for name, statement in LEDGER_OBJECT_STATEMENTS.items():
        kind, sql = observed[name]
        if kind != LEDGER_OBJECT_TYPES[name] or _normalized_ddl(sql) != _normalized_ddl(
            statement
        ):
            raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED")


def _validate_record_row(row: Sequence[Any]) -> str:
    if len(row) != 15:
        raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED")
    if (
        not isinstance(row[0], int)
        or row[0] < 1
        or not isinstance(row[2], int)
        or row[2] < 1
        or SHA256.fullmatch(str(row[1])) is None
        or (row[3] != GENESIS_RECORD and SHA256.fullmatch(str(row[3])) is None)
        or SHA256.fullmatch(str(row[4])) is None
        or row[5] not in {"CHECKPOINT", "PRE_DISPATCH", "POST_RESULT"}
        or row[6]
        not in {
            "OBSERVED",
            "TERMINAL",
            "AUTHORIZED",
            "BLOCKED_ALIAS_RUNTIME_PROOF",
            "BLOCKED_AUTHORITATIVE_SNAPSHOT",
        }
        or any(
            value is not None and SHA256.fullmatch(str(value)) is None
            for value in row[7:12]
        )
        or (row[13] != GENESIS_GLOBAL and SHA256.fullmatch(str(row[13])) is None)
        or SHA256.fullmatch(str(row[14])) is None
    ):
        raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED")
    _timestamp(row[12], "CAPACITY_LEDGER_TAMPER_DETECTED")
    expected = _sha256(_ledger_global_material(row))
    if row[14] != expected:
        raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED")
    return expected


def _read_ledger_meta(
    connection: sqlite3.Connection, config: GuardConfig, *, now: datetime
) -> dict[str, Any]:
    rows = connection.execute(
        "SELECT schema_version, ledger_id, global_sequence, record_count, "
        "session_count, global_head_sha256, first_recorded_at, last_recorded_at, "
        "created_at FROM ledger_meta WHERE singleton = 1"
    ).fetchall()
    if len(rows) != 1:
        raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED")
    row = rows[0]
    meta = {
        "schema_version": row[0],
        "ledger_id": row[1],
        "global_sequence": row[2],
        "record_count": row[3],
        "session_count": row[4],
        "global_head_sha256": row[5],
        "first_recorded_at": row[6],
        "last_recorded_at": row[7],
        "created_at": row[8],
    }
    if (
        meta["schema_version"] != config.ledger_schema_version
        or SHA256.fullmatch(str(meta["ledger_id"])) is None
        or not isinstance(meta["global_sequence"], int)
        or meta["global_sequence"] < 0
        or meta["record_count"] != meta["global_sequence"]
        or not isinstance(meta["session_count"], int)
        or meta["session_count"] < 0
        or meta["session_count"] > meta["record_count"]
    ):
        raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED")
    _timestamp(meta["created_at"], "CAPACITY_LEDGER_TAMPER_DETECTED")
    if meta["record_count"] == 0:
        if (
            meta["global_head_sha256"] != GENESIS_GLOBAL
            or meta["session_count"] != 0
            or meta["first_recorded_at"] is not None
            or meta["last_recorded_at"] is not None
        ):
            raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED")
    else:
        first = _timestamp(meta["first_recorded_at"], "CAPACITY_LEDGER_TAMPER_DETECTED")
        last = _timestamp(meta["last_recorded_at"], "CAPACITY_LEDGER_TAMPER_DETECTED")
        if (
            first > last
            or last > now
            or (now - first).total_seconds() > config.ledger_retention_seconds
        ):
            raise CapacityViolation("CAPACITY_LEDGER_BOUND_EXCEEDED")
        _valid_sha256(meta["global_head_sha256"], "CAPACITY_LEDGER_TAMPER_DETECTED")
    if (
        meta["record_count"] > config.ledger_max_rows
        or meta["session_count"] > config.ledger_max_sessions
        or _database_bytes(connection) > config.ledger_max_bytes
    ):
        raise CapacityViolation("CAPACITY_LEDGER_BOUND_EXCEEDED")
    return meta


def _bounded_ledger_anchor(
    connection: sqlite3.Connection,
    config: GuardConfig,
    *,
    session_sha256: str | None,
    now: datetime,
) -> tuple[dict[str, Any], tuple[Any, ...] | None]:
    _validate_ledger_objects(connection)
    user_version = connection.execute("PRAGMA user_version").fetchone()
    if user_version is None or user_version[0] != config.ledger_schema_version:
        raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED")
    meta = _read_ledger_meta(connection, config, now=now)
    if meta["global_sequence"]:
        last = connection.execute(
            "SELECT global_sequence, session_id_sha256, checkpoint_sequence, "
            "previous_record_sha256, record_sha256, phase, status, tool_name_sha256, "
            "tool_use_id_sha256, input_record_sha256, tool_input_sha256, "
            "tool_result_sha256, recorded_at, previous_global_sha256, "
            "global_record_sha256 FROM lifecycle_records WHERE global_sequence = ?",
            (meta["global_sequence"],),
        ).fetchone()
        if last is None or _validate_record_row(last) != meta["global_head_sha256"]:
            raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED")
    head: tuple[Any, ...] | None = None
    if session_sha256 is not None:
        head = connection.execute(
            "SELECT checkpoint_sequence, record_sha256, phase, status, "
            "tool_use_id_sha256, input_record_sha256 FROM session_heads "
            "WHERE session_id_sha256 = ?",
            (session_sha256,),
        ).fetchone()
        if head is not None:
            record = connection.execute(
                "SELECT global_sequence, session_id_sha256, checkpoint_sequence, "
                "previous_record_sha256, record_sha256, phase, status, "
                "tool_name_sha256, tool_use_id_sha256, input_record_sha256, "
                "tool_input_sha256, tool_result_sha256, recorded_at, "
                "previous_global_sha256, global_record_sha256 FROM lifecycle_records "
                "WHERE session_id_sha256 = ? AND checkpoint_sequence = ?",
                (session_sha256, head[0]),
            ).fetchone()
            if record is None:
                raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED")
            _validate_record_row(record)
            if head != (
                record[2],
                record[4],
                record[5],
                record[6],
                record[8],
                record[9],
            ):
                raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED")
    return meta, head


def _offline_verify_ledger(
    connection: sqlite3.Connection, config: GuardConfig
) -> dict[str, int]:
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if integrity != ("ok",):
            raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED")
        meta, _ = _bounded_ledger_anchor(
            connection,
            config,
            session_sha256=None,
            now=datetime.now(timezone.utc),
        )
        rows = connection.execute(
            "SELECT global_sequence, session_id_sha256, checkpoint_sequence, "
            "previous_record_sha256, record_sha256, phase, status, tool_name_sha256, "
            "tool_use_id_sha256, input_record_sha256, tool_input_sha256, tool_result_sha256, "
            "recorded_at, previous_global_sha256, global_record_sha256 "
            "FROM lifecycle_records ORDER BY global_sequence"
        ).fetchall()
        if len(rows) != meta["record_count"]:
            raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED")
        previous_global = GENESIS_GLOBAL
        sessions: dict[str, tuple[Any, ...]] = {}
        for expected_sequence, row in enumerate(rows, start=1):
            if row[0] != expected_sequence or row[13] != previous_global:
                raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED")
            expected_global = _validate_record_row(row)
            session_id_sha = row[1]
            previous = sessions.get(session_id_sha)
            if previous is None:
                if row[2] != 1 or row[3] != GENESIS_RECORD:
                    raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED")
            elif row[2] != previous[2] + 1 or row[3] != previous[4]:
                raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED")
            sessions[session_id_sha] = row
            previous_global = expected_global
        expected_head = previous_global if rows else GENESIS_GLOBAL
        if meta["global_head_sha256"] != expected_head:
            raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED")
        heads = connection.execute(
            "SELECT session_id_sha256, checkpoint_sequence, record_sha256, phase, status, "
            "tool_use_id_sha256, input_record_sha256, updated_at FROM session_heads"
        ).fetchall()
        if len(heads) != len(sessions) or len(heads) != meta["session_count"]:
            raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED")
        by_session = {row[0]: row for row in heads}
        for session, row in sessions.items():
            head = by_session.get(session)
            if head is None or head[1:7] != (
                row[2],
                row[4],
                row[5],
                row[6],
                row[8],
                row[9],
            ):
                raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED")
        if rows and (
            meta["first_recorded_at"] != rows[0][12]
            or meta["last_recorded_at"] != rows[-1][12]
        ):
            raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED")
        return {"rows": len(rows), "sessions": len(sessions)}
    except CapacityViolation:
        raise
    except sqlite3.Error as exc:
        raise CapacityViolation("CAPACITY_LEDGER_TAMPER_DETECTED") from exc


def _ledger_append(
    state: ValidationState, *, internal_test_directory: Path | None = None
) -> None:
    connection = _ledger_connect(
        state.config, internal_test_directory=internal_test_directory
    )
    committed = False
    try:
        _initialize_ledger(connection, state.config)
        record = state.governance_record
        session_sha = _sha256(str(record["session_id"]))
        sequence = int(record["sequence"])
        previous_record = str(record["previous_record_sha256"])
        record_sha = str(record["record_sha256"])
        phase = str(record["lifecycle_phase"])
        status = str(record["lifecycle_status"])
        tool_name_sha = (
            _sha256(record["tool_name"]) if record["tool_name"] is not None else None
        )
        tool_use_sha = (
            _sha256(record["tool_use_id"])
            if record["tool_use_id"] is not None
            else None
        )
        input_record_sha = record["pre_dispatch_record_sha256"]
        now = datetime.now(timezone.utc)
        meta, head = _bounded_ledger_anchor(
            connection,
            state.config,
            session_sha256=session_sha,
            now=now,
        )
        if meta["record_count"] >= state.config.ledger_max_rows:
            raise CapacityViolation("CAPACITY_LEDGER_BOUND_EXCEEDED")
        if head is None and meta["session_count"] >= state.config.ledger_max_sessions:
            raise CapacityViolation("CAPACITY_LEDGER_BOUND_EXCEEDED")
        if head is None:
            if sequence != 1 or previous_record != GENESIS_RECORD:
                raise CapacityViolation("CAPACITY_CHECKPOINT_STALE_OR_REPLAYED")
        elif sequence != head[0] + 1 or previous_record != head[1]:
            raise CapacityViolation("CAPACITY_CHECKPOINT_STALE_OR_REPLAYED")
        if phase == "POST_RESULT":
            if (
                head is None
                or head[2] != "PRE_DISPATCH"
                or head[3] != "AUTHORIZED"
                or head[4] != tool_use_sha
                or input_record_sha != head[1]
            ):
                raise CapacityViolation("CAPACITY_LIFECYCLE_OUT_OF_ORDER")
        elif input_record_sha is not None:
            raise CapacityViolation("CAPACITY_LIFECYCLE_BINDING_INVALID")
        global_sequence = int(meta["global_sequence"]) + 1
        previous_global = str(meta["global_head_sha256"])
        recorded_at = _utc_now()
        material = {
            "global_sequence": global_sequence,
            "session_id_sha256": session_sha,
            "checkpoint_sequence": sequence,
            "previous_record_sha256": previous_record,
            "record_sha256": record_sha,
            "phase": phase,
            "status": status,
            "tool_name_sha256": tool_name_sha,
            "tool_use_id_sha256": tool_use_sha,
            "input_record_sha256": input_record_sha,
            "tool_input_sha256": record["tool_input_sha256"],
            "tool_result_sha256": record["tool_result_sha256"],
            "recorded_at": recorded_at,
            "previous_global_sha256": previous_global,
        }
        global_record_sha = _sha256(material)
        connection.execute(
            "INSERT INTO lifecycle_records "
            "(global_sequence, session_id_sha256, checkpoint_sequence, previous_record_sha256, "
            "record_sha256, phase, status, tool_name_sha256, tool_use_id_sha256, "
            "input_record_sha256, tool_input_sha256, tool_result_sha256, recorded_at, "
            "previous_global_sha256, global_record_sha256) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                global_sequence,
                session_sha,
                sequence,
                previous_record,
                record_sha,
                phase,
                status,
                tool_name_sha,
                tool_use_sha,
                input_record_sha,
                record["tool_input_sha256"],
                record["tool_result_sha256"],
                recorded_at,
                previous_global,
                global_record_sha,
            ),
        )
        connection.execute(
            "INSERT INTO session_heads "
            "(session_id_sha256, checkpoint_sequence, record_sha256, phase, status, "
            "tool_use_id_sha256, input_record_sha256, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(session_id_sha256) DO UPDATE SET "
            "checkpoint_sequence=excluded.checkpoint_sequence, "
            "record_sha256=excluded.record_sha256, phase=excluded.phase, "
            "status=excluded.status, tool_use_id_sha256=excluded.tool_use_id_sha256, "
            "input_record_sha256=excluded.input_record_sha256, updated_at=excluded.updated_at",
            (
                session_sha,
                sequence,
                record_sha,
                phase,
                status,
                tool_use_sha,
                input_record_sha,
                recorded_at,
            ),
        )
        connection.execute(
            "UPDATE ledger_meta SET global_sequence = ?, record_count = ?, "
            "session_count = ?, global_head_sha256 = ?, "
            "first_recorded_at = COALESCE(first_recorded_at, ?), last_recorded_at = ? "
            "WHERE singleton = 1",
            (
                global_sequence,
                global_sequence,
                int(meta["session_count"]) + (1 if head is None else 0),
                global_record_sha,
                recorded_at,
                recorded_at,
            ),
        )
        if _database_bytes(connection) > state.config.ledger_max_bytes:
            raise CapacityViolation("CAPACITY_LEDGER_BOUND_EXCEEDED")
        connection.execute("COMMIT")
        committed = True
    except CapacityViolation:
        raise
    except sqlite3.IntegrityError as exc:
        raise CapacityViolation("CAPACITY_CHECKPOINT_STALE_OR_REPLAYED") from exc
    except sqlite3.Error as exc:
        raise CapacityViolation("CAPACITY_LEDGER_FAILURE") from exc
    finally:
        if not committed:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.Error:
                pass
        connection.close()


def _offline_full_audit(
    config: GuardConfig, *, internal_test_directory: Path | None = None
) -> dict[str, int]:
    directory = _resolved_state_directory(config, internal_test_directory)
    database = directory / config.ledger_filename
    if not database.exists():
        raise CapacityViolation("CAPACITY_LEDGER_FAILURE")
    connection = _ledger_connect(
        config, internal_test_directory=internal_test_directory
    )
    try:
        result = _offline_verify_ledger(connection, config)
        connection.execute("ROLLBACK")
        return result
    except CapacityViolation:
        try:
            connection.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        connection.close()


def offline_full_audit() -> dict[str, int]:
    """Run the non-registered full-chain audit against the fixed local ledger."""

    return _offline_full_audit(_load_config())


def _evaluate_event(
    event: Mapping[str, Any], *, internal_test_directory: Path | None
) -> str | None:
    try:
        payload, event_context = _extract_event(event)
        if payload is None:
            return None
        state = _validate_payload(payload, event_context)
        _ledger_append(state, internal_test_directory=internal_test_directory)
        return state.block_code
    except CapacityViolation as exc:
        return exc.code
    except (TypeError, ValueError, OSError, RecursionError):
        return "CAPACITY_PAYLOAD_REJECTED"
    except Exception:  # noqa: BLE001 - unexpected guard failures fail closed
        return "CAPACITY_GUARD_FAILURE"


def evaluate_event(event: Mapping[str, Any]) -> str | None:
    """Validate one registered-hook event using only the fixed production ledger."""

    return _evaluate_event(event, internal_test_directory=None)


def _evaluate_event_for_test(
    event: Mapping[str, Any], state_directory: Path
) -> str | None:
    """Internal harness entry; never called by the registered hook executable."""

    return _evaluate_event(event, internal_test_directory=state_directory)


def _read_event() -> Mapping[str, Any]:
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES or not raw.strip():
        raise CapacityViolation("CAPACITY_PAYLOAD_REJECTED")
    return _load_json_bytes(raw, "CAPACITY_PAYLOAD_REJECTED")


def _emit(violation: str) -> None:
    print(
        json.dumps(
            {
                "decision": "deny",
                "reason": f"[BLOCKED] FULL_CAPACITY_GUARD: {violation}",
            },
            ensure_ascii=True,
        )
    )


def main() -> int:
    if sys.argv[1:]:
        if sys.argv[1:] != ["--offline-audit"]:
            _emit("CAPACITY_PAYLOAD_REJECTED")
            return 2
        try:
            result = offline_full_audit()
        except CapacityViolation as exc:
            _emit(exc.code)
            return 2
        print(json.dumps({"status": "[OK]", **result}, ensure_ascii=True))
        return 0
    try:
        event = _read_event()
    except (CapacityViolation, OSError, ValueError, RecursionError) as exc:
        _emit(
            exc.code
            if isinstance(exc, CapacityViolation)
            else "CAPACITY_PAYLOAD_REJECTED"
        )
        return 2
    violation = evaluate_event(event)
    if violation is None:
        print(json.dumps({}))
        return 0
    _emit(violation)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
