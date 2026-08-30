#!/usr/bin/env python3
"""Render and optionally execute account-routed Codex or AGY sub-agent prompts.

The account registry is explicit: an alias selects a configured CLI executable and
an optional CLI home directory.  No shell aliases, credentials, or login state are
inferred or modified.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
try:  # POSIX-only primitive; execution fails closed on unsupported platforms.
    import fcntl  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - exercised on non-POSIX hosts
    fcntl = None  # type: ignore[assignment]
import hashlib
import hmac
import json
import os
from dataclasses import dataclass, replace
from pathlib import Path
import re
import signal
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, Mapping, Sequence

import yaml

try:
    from scripts import agent_quota_status_guard as quota_guard
except ImportError:  # Direct ``python scripts/...`` execution.
    import agent_quota_status_guard as quota_guard  # type: ignore[no-redef]

try:
    from scripts import multiagent_capacity as capacity
except ImportError:  # Direct ``python scripts/...`` execution.
    import multiagent_capacity as capacity  # type: ignore[no-redef]

try:
    from scripts.multiagent_ticket_scheduler import (
        SchedulingError,
        admit_dispatch_capacity,
        canonicalize_ownership_resource,
        enforce_dispatch as enforce_ticket_dispatch,
        validate_activation_state,
        validate_provider_account_state,
        validate_snapshot as validate_scheduling_snapshot,
    )
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    from multiagent_ticket_scheduler import (  # type: ignore[no-redef]
        SchedulingError,
        admit_dispatch_capacity,
        canonicalize_ownership_resource,
        enforce_dispatch as enforce_ticket_dispatch,
        validate_activation_state,
        validate_provider_account_state,
        validate_snapshot as validate_scheduling_snapshot,
    )


VALID_CLIS = {"codex", "agy"}
VALID_EFFORTS = {"low", "medium", "high", "xhigh", "max", "ultra"}
VALID_AGY_EFFORTS = {"low", "medium", "high"}
VALID_AGY_MODES = {"accept-edits", "plan"}
VALID_SANDBOXES = {"read-only", "workspace-write", "danger-full-access"}
VALID_HOME_ENV = {"codex": "CODEX_HOME", "agy": "AGY_HOME"}
VALID_RESULT_STATUSES = {"DONE", "BLOCKED", "NEEDS_HITL"}
PROVIDER_PARSE_REASONS = frozenset(
    {
        "terminal_shape",
        "provider_failure_event",
        "thread_id",
        "final_message_cardinality",
        "work_result_validation",
        "secret_bearing",
        "unknown",
    }
)
FINAL_MESSAGE_CARDINALITY_SUBREASONS = frozenset(
    {
        "completed_item_shape",
        "agent_message_text_shape",
        "multiple_structured_candidates",
    }
)
FINAL_MESSAGE_CANDIDATE_COUNTS = frozenset({0, 1, 2})
RESULT_PROTOCOL_VERSION = 2
EXECUTION_RECEIPT_SCHEMA_VERSION = 3
PROBE_CLAIM_SCHEMA_VERSION = 1
PROBE_APPROVAL_SCHEMA_VERSION = 1
APPROVAL_CONSUME_SCHEMA_VERSION = 1
PROBE_CLAIM_TTL_SECONDS = 10 * 60
APPROVAL_GRANT_TTL_SECONDS = 2 * 60
PREAUTH_RETENTION_DAYS = 90
MAX_PREAUTH_ARTIFACT_BYTES = 65_536
PREAUTH_SCOPE = "local-single-host-nonportable-noncryptographic-attestation"
MAX_PROVIDER_OUTPUT_BYTES = 2_000_000
MAX_PRIVATE_FINAL_BYTES = 262_144
MAX_PROVIDER_RUNTIME_SECONDS = 900
PROCESS_GROUP_TERMINATE_SECONDS = 2.0
DISPATCH_DECISION_FIELDS = frozenset(
    {
        "schema_version",
        "ticket",
        "phase",
        "scope_rank",
        "complexity_rank",
        "risk_rank",
        "ambiguity_rank",
        "evidence_burden_rank",
        "quota_band",
        "work_mode",
        "selected_alias",
        "selected_model",
        "selected_effort",
        "rationale",
        "policy_version",
        "planning_to_medium_confirmed",
        "hitl_approved",
    }
)
DISPATCH_DECISION_OPTIONAL_FIELDS = frozenset({"quality_exception"})
# Configuration selects from this fixed, approved terminal-account set; it
# cannot grant an additional account alias execution authority.
GOVERNED_ACCOUNT_ALIASES = frozenset({"codex1", "codex2", "agy1", "agy2"})
# Canonical alias-to-provider binding. Configuration may select an alias but
# cannot relabel its provider.
ALIAS_PROVIDER_MAP: dict[str, str] = {
    "codex1": "codex",
    "codex2": "codex",
    "codex3": "codex",
    "agy1": "agy",
    "agy2": "agy",
}
RESULT_FIELDS = {
    "status",
    "scope_owned",
    "evidence",
    "findings",
    "changed_files",
    "residual_risk",
    "recommended_next_action",
}
PROVIDER_ARRAY_RESULT_FIELDS = frozenset(
    {"scope_owned", "findings", "changed_files"}
)
EXECUTION_RECEIPT_FIELDS = {
    "protocol_version",
    "policy_version",
    "decision_sha256",
    "dispatch_claim_key",
    "dispatch_claim_sha256",
    "claim_proof",
    "claim_proof_sha256",
    "claim_proof_scope",
    "dispatch_identity",
    "dispatch_ticket_id",
    "attempt_id",
    "alias",
    "provider",
    "adapter",
    "model",
    "effort",
    "objective",
    "ownership",
    "quota_status",
    "started_at",
    "ended_at",
    "exit_code",
    "transport_status",
    "output_bytes",
    "output_sha256",
    "work_result_sha256",
}
EXECUTION_RECEIPT_V3_FIELDS = EXECUTION_RECEIPT_FIELDS | {
    "receipt_schema_version",
    "probe_claim_id",
    "probe_claim_sha256",
    "approval_grant_id",
    "approval_grant_sha256",
    "approval_consume_receipt_id",
    "approval_consume_receipt_sha256",
    "approval_consume_anchor_id",
    "approval_consume_anchor_sha256",
    "preauthorization_stores",
    "preauthorization_scope",
}
PREAUTH_STORE_NAMES = (
    "probe_claim_store",
    "approval_grant_store",
    "approval_consume_store",
    "dispatch_ledger_store",
)
PREAUTH_BINDING_FIELDS = frozenset(
    {
        "ticket", "attempt_id", "session_sha256", "policy_version",
        "model_policy_sha256", "dispatcher_source_sha256", "decision_sha256",
        "scheduling_snapshot_sha256", "runtime_config_sha256",
        "work_result_schema_sha256", "probe_claim_schema_sha256",
        "probe_approval_schema_sha256", "approval_consume_schema_sha256",
        "execution_receipt_schema_sha256", "prompt_sha256",
        "objective_sha256", "ownership_sha256", "route", "route_sha256",
        "preauthorization_stores", "dispatch_identity",
    }
)
PREAUTH_BINDING_SHA256_FIELDS = frozenset(
    PREAUTH_BINDING_FIELDS
    - {"ticket", "attempt_id", "policy_version", "route", "preauthorization_stores"}
)
PREAUTH_ROUTE_FIELDS = frozenset(
    {"role", "alias", "provider", "command_sha256", "model", "effort", "mode", "sandbox"}
)
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
SAFE_COMMAND = re.compile(r"^(?:[A-Za-z0-9_.-]+|/[A-Za-z0-9_./-]+)$")
SAFE_PROVIDER_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
SECRET_VALUE_PATTERNS = (
    re.compile(r"(?i)\b(?:authorization|cookie|api[_-]?key|access[_-]?token|refresh[_-]?token)\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]{12,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
)
EMAIL_PATTERN = re.compile(
    r"(?i)(?<![A-Za-z0-9.!#$%&'*+/=?^_`{|}~-])"
    r"[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9-]+(?:\.[A-Z0-9-]+)+"
)
LABELED_PERSONAL_ID_PATTERN = re.compile(
    r"(?i)\b(?:full[_ -]?name|name|e-?mail|phone|telephone|mobile|username|"
    r"user[_ -]?id|customer[_ -]?id|person[_ -]?id|national[_ -]?id)\s*[:=]\s*"
    r"(?:\"[^\"]*\"|'[^']*'|[^,;\r\n]+)"
)
HOME_PATH_PATTERN = re.compile(
    r"(?i)(?:[A-Z]:[\\/](?:Users|Documents and Settings)[\\/]|/(?:Users|home)/)"
    r"[^\\/\s]+"
)
IP_ADDRESS_PATTERN = re.compile(
    r"(?<![0-9])(?:25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})"
    r"(?:\.(?:25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})){3}(?![0-9])"
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORK_RESULT_SCHEMA = (
    REPOSITORY_ROOT / ".agents/schemas/multiagent-work-result-v2.schema.json"
)
DEFAULT_PROBE_CLAIM_SCHEMA = (
    REPOSITORY_ROOT / ".agents/schemas/multiagent-probe-claim-v1.schema.json"
)
DEFAULT_PROBE_APPROVAL_SCHEMA = (
    REPOSITORY_ROOT / ".agents/schemas/multiagent-probe-approval-v1.schema.json"
)
DEFAULT_APPROVAL_CONSUME_SCHEMA = (
    REPOSITORY_ROOT / ".agents/schemas/multiagent-approval-consume-receipt-v1.schema.json"
)
DEFAULT_EXECUTION_RECEIPT_V3_SCHEMA = (
    REPOSITORY_ROOT / ".agents/schemas/multiagent-dispatch-receipt-v3.schema.json"
)


def _validate_final_message_cardinality_telemetry(
    provider_parse_reason: str,
    final_message_cardinality_subreason: str | None,
    candidate_count: int | None,
) -> None:
    """Accept only closed, content-free details for cardinality rejections."""

    if provider_parse_reason != "final_message_cardinality":
        if final_message_cardinality_subreason is not None or candidate_count is not None:
            raise ValueError("cardinality telemetry requires final_message_cardinality")
        return
    if (
        final_message_cardinality_subreason is not None
        and final_message_cardinality_subreason
        not in FINAL_MESSAGE_CARDINALITY_SUBREASONS
    ):
        raise ValueError("unsupported final-message cardinality subreason")
    if (
        not isinstance(candidate_count, int)
        or isinstance(candidate_count, bool)
        or candidate_count not in FINAL_MESSAGE_CANDIDATE_COUNTS
    ):
        raise ValueError("final-message candidate count must be saturated")

DEFAULT_OWNERSHIP = "Only the files and responsibilities explicitly assigned in this prompt."
DEFAULT_BOUNDARIES = "Do not modify credentials, authentication state, or files outside ownership."
DEFAULT_EVIDENCE = "Return commands run, exit codes, and paths to resulting artifacts."
DEFAULT_STOP_CONDITION = (
    "Stop and report BLOCKED when authorization, credentials, or assigned scope is missing."
)
COORDINATION_SENTENCE = (
    "You are not alone in the codebase. Do not revert edits made by others; "
    "adjust your work to accommodate concurrent changes. Work only within the assigned ownership."
)

DISPATCH_CLAIM_VERSION = 2
MAX_DISPATCH_CLAIM_BYTES = 16_384
DISPATCH_CLAIM_STALE_SECONDS = 6 * 60 * 60
DISPATCH_CLAIM_START_MAX_AGE_SECONDS = 30
_STORE_LOCKS: dict[str, int] = {}
_STORE_LOCKS_GUARD = threading.RLock()
_PROCESS_START_NONCE = hashlib.sha256(os.urandom(32)).hexdigest()
CLAIM_PROOF_FIELDS = frozenset(
    {
        "schema_version", "claim_key", "decision_sha256",
        "scheduling_snapshot_sha256", "dispatch_identity", "ticket_sha256",
        "route_sha256", "ownership_tokens_sha256", "started_at", "ended_at",
        "ownership_key_id",
        "transport_status", "exit_code", "output_bytes", "output_sha256",
        "work_result_sha256", "terminal_state",
    }
)


class ConfigurationError(ValueError):
    """Raised when routing configuration or an override is invalid."""


class DispatchDecisionError(ConfigurationError):
    """Raised when a DispatchDecision fails a deterministic policy gate."""

    def __init__(self, message: str, *, status: str = "BLOCKED") -> None:
        super().__init__(message)
        self.status = status


class ProviderParseError(ConfigurationError):
    """A content-free classification for a rejected provider result stream."""

    def __init__(
        self,
        provider_parse_reason: str,
        message: str,
        *,
        final_message_cardinality_subreason: str | None = None,
        candidate_count: int | None = None,
    ) -> None:
        if provider_parse_reason not in PROVIDER_PARSE_REASONS:
            raise ValueError("unsupported provider parse reason")
        _validate_final_message_cardinality_telemetry(
            provider_parse_reason,
            final_message_cardinality_subreason,
            candidate_count,
        )
        super().__init__(message)
        self.provider_parse_reason = provider_parse_reason
        self.final_message_cardinality_subreason = final_message_cardinality_subreason
        self.candidate_count = candidate_count


class ExecutionContractError(ConfigurationError):
    """A child ran but its parse/finalization/receipt contract failed."""

    def __init__(
        self,
        reason: str = "unknown",
        *,
        final_message_cardinality_subreason: str | None = None,
        candidate_count: int | None = None,
    ) -> None:
        super().__init__("child execution contract failed")
        self.provider_parse_reason = reason if reason in PROVIDER_PARSE_REASONS else "unknown"
        _validate_final_message_cardinality_telemetry(
            self.provider_parse_reason,
            final_message_cardinality_subreason,
            candidate_count,
        )
        self.final_message_cardinality_subreason = final_message_cardinality_subreason
        self.candidate_count = candidate_count


class ProbeAuthorizationError(ConfigurationError):
    """A content-free preauthorization rejection raised before provider spawn."""

    code = "PROBE_AUTHORIZATION_INVALID"


class PlatformNativePrespawnReceiptRequired(ConfigurationError):
    """AGY is denied until the external native pre-spawn boundary is proven."""

    code = "PLATFORM_NATIVE_PRESPAWN_RECEIPT_REQUIRED"

    def __init__(self) -> None:
        super().__init__(self.code)


class ProviderExecutableBindingError(ConfigurationError):
    """Declared provider metadata contradicts the effective executable."""

    code = "PROVIDER_EXECUTABLE_BINDING_INVALID"

    def __init__(self) -> None:
        super().__init__(self.code)


class LegacyReceiptRevalidationUnsupported(ConfigurationError):
    """A migrated v1 receipt cannot be revalidated without retained raw PII."""

    code = "LEGACY_RECEIPT_REVALIDATION_UNSUPPORTED"

    def __init__(self) -> None:
        super().__init__(
            "legacy receipt revalidation is unavailable after privacy migration"
        )


class _StrictJSONError(ValueError):
    """Content-free marker for ambiguous or non-standard JSON."""


class _AmbiguousJSONError(_StrictJSONError):
    """A syntactically accepted JSON extension that policy forbids."""


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise _AmbiguousJSONError("JSON object is ambiguous")
        value[key] = item
    return value


def _reject_json_constant(_value: str) -> None:
    raise _AmbiguousJSONError("JSON constant is non-standard")


def _strict_json_loads(payload: str | bytes) -> Any:
    """Decode RFC JSON while rejecting duplicate names and non-finite values."""

    try:
        return json.loads(
            payload,
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_json_constant,
        )
    except _AmbiguousJSONError:
        raise
    except json.JSONDecodeError as exc:
        raise _StrictJSONError("JSON input is invalid") from exc


def _canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("ascii")


def _artifact_address(value: Mapping[str, Any], id_field: str) -> str:
    body = dict(value)
    body.pop(id_field, None)
    return hashlib.sha256(_canonical_json_bytes(body)).hexdigest()


@dataclass
class RetainedDirectory:
    """A no-symlink private directory retained by descriptor and local identity."""

    path: Path
    fd: int
    identity: tuple[int, int]
    identity_sha256: str

    def duplicate_fd(self) -> int:
        if self.fd < 0:
            raise ProbeAuthorizationError("preauthorization store is closed")
        return os.dup(self.fd)

    def close(self) -> None:
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1


def _normalized_private_path(path_value: str | os.PathLike[str]) -> Path:
    raw = Path(os.fspath(path_value))
    if not os.fspath(path_value) or any(part in {".", ".."} for part in raw.parts):
        raise ProbeAuthorizationError("preauthorization path alias is invalid")
    return Path(os.path.abspath(os.fspath(raw)))


def _directory_identity_sha256(path: Path, metadata: os.stat_result) -> str:
    """Hash local path plus inode identity without persisting either value."""

    return _canonical_sha256(
        {
            "scope": "local-directory-identity-v1",
            "path_sha256": hashlib.sha256(os.fsencode(path)).hexdigest(),
            "device": metadata.st_dev,
            "inode": metadata.st_ino,
            "mode": stat.S_IMODE(metadata.st_mode),
        }
    )


def _open_retained_private_directory(
    path_value: str | os.PathLike[str], label: str
) -> RetainedDirectory:
    """Traverse every component without symlinks and retain an owned 0700 dir."""

    path = _normalized_private_path(path_value)
    parts = path.parts
    if not path.is_absolute() or not parts:
        raise ProbeAuthorizationError(f"{label} path is invalid")
    descriptor = -1
    try:
        descriptor = os.open(parts[0], _directory_open_flags())
        for component in parts[1:]:
            child_fd = os.open(component, _directory_open_flags(), dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child_fd
        metadata = _validate_owned_directory_fd(descriptor)
        return RetainedDirectory(
            path=path,
            fd=descriptor,
            identity=(metadata.st_dev, metadata.st_ino),
            identity_sha256=_directory_identity_sha256(path, metadata),
        )
    except (OSError, SchedulingError) as exc:
        if descriptor >= 0:
            os.close(descriptor)
        raise ProbeAuthorizationError(f"{label} cannot be traversed safely") from exc


def _secure_json_artifact(
    path_value: str | os.PathLike[str],
    *,
    retained_parent: RetainedDirectory | None = None,
) -> RetainedJSONArtifact:
    """Open one private artifact without following its final path component."""

    path = _normalized_private_path(path_value)
    if not SAFE_NAME.fullmatch(path.name):
        raise ProbeAuthorizationError("preauthorization artifact name is invalid")
    parent_fd = -1
    descriptor = -1
    try:
        if retained_parent is None:
            parent = _open_retained_private_directory(
                path.parent, "preauthorization artifact store"
            )
            parent_fd = parent.duplicate_fd()
            parent.close()
        else:
            if path.parent != retained_parent.path:
                raise ProbeAuthorizationError(
                    "preauthorization artifact store path is mismatched"
                )
            parent_fd = retained_parent.duplicate_fd()
        descriptor = os.open(
            path.name, _file_open_flags(os.O_RDONLY), dir_fd=parent_fd
        )
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or stat.S_IMODE(metadata.st_mode) != 0o600
            or metadata.st_size < 2
            or metadata.st_size > MAX_PREAUTH_ARTIFACT_BYTES
            or (hasattr(os, "getuid") and metadata.st_uid != os.getuid())
        ):
            raise ProbeAuthorizationError("preauthorization artifact metadata is invalid")
        raw = _bounded_read_fd(descriptor)
        final = os.fstat(descriptor)
        path_stat = os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
        metadata_tuple = (
            metadata.st_size,
            metadata.st_mtime_ns,
            metadata.st_ctime_ns,
            stat.S_IMODE(metadata.st_mode),
        )
        if (
            (metadata.st_dev, metadata.st_ino) != (final.st_dev, final.st_ino)
            or (metadata.st_dev, metadata.st_ino)
            != (path_stat.st_dev, path_stat.st_ino)
            or metadata_tuple
            != (
                final.st_size,
                final.st_mtime_ns,
                final.st_ctime_ns,
                stat.S_IMODE(final.st_mode),
            )
        ):
            raise ProbeAuthorizationError("preauthorization artifact changed while loading")
        try:
            value = _strict_json_loads(raw)
        except _StrictJSONError as exc:
            raise ProbeAuthorizationError("preauthorization artifact JSON is invalid") from exc
        if not isinstance(value, dict):
            raise ProbeAuthorizationError("preauthorization artifact must be an object")
        return RetainedJSONArtifact(
            path=path,
            parent_fd=parent_fd,
            fd=descriptor,
            identity=(metadata.st_dev, metadata.st_ino),
            metadata=metadata_tuple,
            raw=raw,
            record=value,
        )
    except OSError as exc:
        if descriptor >= 0:
            os.close(descriptor)
        if parent_fd >= 0:
            os.close(parent_fd)
        raise ProbeAuthorizationError("preauthorization artifact cannot be opened safely") from exc
    except BaseException:
        if descriptor >= 0:
            os.close(descriptor)
        if parent_fd >= 0:
            os.close(parent_fd)
        raise


def _reverify_retained_artifact(artifact: RetainedJSONArtifact) -> None:
    metadata = os.fstat(artifact.fd)
    path_metadata = os.stat(
        artifact.path.name, dir_fd=artifact.parent_fd, follow_symlinks=False
    )
    if (
        (metadata.st_dev, metadata.st_ino) != artifact.identity
        or (path_metadata.st_dev, path_metadata.st_ino) != artifact.identity
        or (
            metadata.st_size,
            metadata.st_mtime_ns,
            metadata.st_ctime_ns,
            stat.S_IMODE(metadata.st_mode),
        )
        != artifact.metadata
        or metadata.st_nlink != 1
        or stat.S_IMODE(metadata.st_mode) != 0o600
    ):
        raise ProbeAuthorizationError("preauthorization artifact changed before consume")


def _durable_private_json_create(
    destination: str | os.PathLike[str],
    record: Mapping[str, Any],
    *,
    retained_parent: RetainedDirectory | None = None,
) -> Path:
    """Create one immutable private JSON artifact and fsync file plus directory."""

    path = _normalized_private_path(destination)
    if not SAFE_NAME.fullmatch(path.name):
        raise ProbeAuthorizationError("preauthorization artifact name is invalid")
    parent: RetainedDirectory | None = None
    if retained_parent is None:
        parent = _open_retained_private_directory(
            path.parent, "preauthorization artifact store"
        )
        directory_fd = parent.duplicate_fd()
    else:
        if path.parent != retained_parent.path:
            raise ProbeAuthorizationError(
                "preauthorization artifact store path is mismatched"
            )
        directory_fd = retained_parent.duplicate_fd()
    descriptor = -1
    try:
        descriptor = os.open(
            path.name,
            _file_open_flags(os.O_WRONLY | os.O_CREAT | os.O_EXCL),
            0o600,
            dir_fd=directory_fd,
        )
        payload = _canonical_json_bytes(record)
        if len(payload) > MAX_PREAUTH_ARTIFACT_BYTES:
            raise ProbeAuthorizationError("preauthorization artifact is too large")
        _write_all(descriptor, payload)
        os.fsync(descriptor)
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or stat.S_IMODE(metadata.st_mode) != 0o600
            or metadata.st_size != len(payload)
        ):
            raise ProbeAuthorizationError("created preauthorization artifact is unsafe")
        os.fsync(directory_fd)
        return path
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(directory_fd)
        if parent is not None:
            parent.close()


def _sha256_regular_file(path_value: str | os.PathLike[str], label: str) -> str:
    path = Path(os.path.abspath(os.fspath(path_value)))
    flags = _file_open_flags(os.O_RDONLY)
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > 2_000_000:
            raise ProbeAuthorizationError(f"{label} is not a bounded regular file")
        payload = bytearray()
        while True:
            chunk = os.read(descriptor, 65_536)
            if not chunk:
                break
            payload.extend(chunk)
            if len(payload) > 2_000_000:
                raise ProbeAuthorizationError(f"{label} is too large")
        final = os.fstat(descriptor)
        if (
            (metadata.st_dev, metadata.st_ino) != (final.st_dev, final.st_ino)
            or metadata.st_size != final.st_size
            or metadata.st_mtime_ns != final.st_mtime_ns
            or metadata.st_ctime_ns != final.st_ctime_ns
        ):
            raise ProbeAuthorizationError(f"{label} changed while hashing")
        return hashlib.sha256(bytes(payload)).hexdigest()
    finally:
        os.close(descriptor)


@dataclass
class ClaimStore:
    """A canonical durable ledger directory held open by validated descriptor."""

    path: Path
    dir_fd: int
    identity: tuple[int, int]
    identity_sha256: str
    namespace: str
    closed: bool = False

    def close(self) -> None:
        if not self.closed:
            self.closed = True
            os.close(self.dir_fd)


@dataclass
class DispatchClaim:
    """One atomically created, cross-process executable-dispatch claim."""

    path: Path
    store: ClaimStore
    key: str
    record: dict[str, Any]
    lock_fd: int
    claim_fd: int
    lock_identity: tuple[int, int]
    claim_identity: tuple[int, int]
    closed: bool = False

    @property
    def dir_fd(self) -> int:
        return self.store.dir_fd


@dataclass(frozen=True)
class Route:
    """Resolved role-to-account route."""

    role: str
    alias: str
    cli: str
    command: str
    home_env: str | None
    home_path: str | None
    model: str | None
    effort: str | None
    mode: str | None
    sandbox: str | bool | None


@dataclass(frozen=True)
class Invocation:
    """A shell-free subprocess invocation."""

    route: Route
    argv: tuple[str, ...]
    prompt_stdin: str
    cwd: str
    env_overrides: Mapping[str, str]
    decision: Mapping[str, Any] | None = None
    model_policy: Mapping[str, Any] | None = None
    decision_digest: str | None = None
    attempt_id: int = 1
    objective: str = "unspecified"
    ownership: str = "Only the files and responsibilities explicitly assigned in this prompt."
    runtime_config_path: str | None = None
    runtime_config_approved: bool = False
    work_result_schema_path: str | None = None
    scheduling_snapshot: Mapping[str, Any] | None = None
    scheduling_snapshot_digest: str | None = None
    claim_store_override: str | None = None
    capacity_lease: capacity.CapacityLease | Mapping[str, Any] | None = None
    capacity_store_path: str | None = None
    capacity_policy: Mapping[str, Any] | None = None
    capacity_request_id: str | None = None
    capacity_required: bool = False
    qobs_admission: QobsAdmission | None = None
    qobs_artifact: object | None = None
    qobs_expected_context: Mapping[str, object] | None = None
    qobs_ledger_store: str | None = None
    probe_claim_path: str | None = None
    approval_grant_path: str | None = None
    approval_store_path: str | None = None
    approval_session_id: str | None = None
    preauthorization_store_binding: Mapping[str, str] | None = None


@dataclass
class RetainedJSONArtifact:
    """Strict JSON artifact retained by descriptor across preflight and consume."""

    path: Path
    parent_fd: int
    fd: int
    identity: tuple[int, int]
    metadata: tuple[int, int, int, int]
    raw: bytes
    record: dict[str, Any]

    def close(self) -> None:
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1
        if self.parent_fd >= 0:
            os.close(self.parent_fd)
            self.parent_fd = -1


@dataclass
class PreparedProbeAuthorization:
    """Exact claim and grant held open until their one-shot is consumed."""

    claim: RetainedJSONArtifact
    grant: RetainedJSONArtifact
    binding: dict[str, Any]
    probe_claim_store: RetainedDirectory
    approval_grant_store: RetainedDirectory
    approval_consume_store: RetainedDirectory
    dispatch_ledger_store: ClaimStore | None
    consume_artifact: RetainedJSONArtifact | None = None
    anchor_artifact: RetainedJSONArtifact | None = None

    def take_dispatch_ledger(self) -> ClaimStore:
        store = self.dispatch_ledger_store
        if store is None:
            raise ProbeAuthorizationError("dispatch ledger descriptor is unavailable")
        self.dispatch_ledger_store = None
        return store

    def close(self) -> None:
        if self.consume_artifact is not None:
            self.consume_artifact.close()
        if self.anchor_artifact is not None:
            self.anchor_artifact.close()
        self.claim.close()
        self.grant.close()
        self.probe_claim_store.close()
        self.approval_grant_store.close()
        self.approval_consume_store.close()
        if self.dispatch_ledger_store is not None:
            self.dispatch_ledger_store.close()
            self.dispatch_ledger_store = None


@dataclass(frozen=True)
class ValidatedDispatchDecision:
    """Normalized result of deterministic decision-policy validation."""

    decision: Mapping[str, Any]
    digest: str
    policy_version: str
    quality_floor: int
    model_quality_rank: int


@dataclass(frozen=True)
class ProviderResult:
    """A provider-native event stream reduced to one validated WorkResult."""

    work_result: Mapping[str, Any]
    adapter: str
    process_or_session_id: str | None = None


@dataclass(frozen=True)
class PrivateFinalResult:
    """Validated content-free evidence for Codex's private final channel."""

    work_result: Mapping[str, Any]
    byte_count: int
    sha256: str


@dataclass(frozen=True)
class ExecutionOutcome:
    """One fully terminalized dispatch and its validated public result."""

    process: subprocess.CompletedProcess[str]
    completed: Mapping[str, Any]


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ConfigurationError(f"{label} must be a mapping")
    return value


def _optional_safe_name(value: Any, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not SAFE_NAME.fullmatch(value):
        raise ConfigurationError(f"{label} contains unsupported characters")
    return value


def _expand_home_path(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ConfigurationError("home_path must be a non-empty string")
    home = os.environ.get("HOME")
    if value == "${HOME}" or value.startswith("${HOME}/"):
        if not home:
            raise ConfigurationError("HOME is unavailable for ${HOME} expansion")
        value = home + value[len("${HOME}") :]
    if "$" in value or "~" in value:
        raise ConfigurationError("home_path supports only a leading ${HOME} expansion")
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ConfigurationError("home_path must resolve to an absolute path")
    return str(path)


def load_config(path: str | os.PathLike[str]) -> Mapping[str, Any]:
    """Load a YAML routing configuration without interpreting custom YAML objects."""

    config_path = Path(path)
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return _mapping(data, "configuration")


def effective_activation_state(config: Mapping[str, Any]) -> tuple[bool, str]:
    """Return the fail-closed activation values, independently defaulted.

    Missing legacy configuration is never interpreted as authorization to run a
    provider command.  The one-shot exception has its own gate below and does
    not change these defaults.
    """

    return (
        config.get("activation_prohibited", True),
        config.get("dispatcher_execution", "CLOSED"),
    )


# IDQ-MVP-080 is deliberately a data-only admission contract.  It does not
# alter the ordinary dispatcher gate above and it must never start a provider
# process.  The irreversible start boundary, if any, is separately owned.
_IDQ_MVP_080_TICKET = "IDQ-MVP-080"
_IDQ_MVP_080_ALIASES = {
    "codex1": "codex",
    "codex2": "codex",
    "agy1": "agy",
    "agy2": "agy",
}
_IDQ_MVP_080_CONFIG_FIELDS = frozenset(
    {"ticket", "aliases"}
)
_IDQ_MVP_080_ALIAS_FIELDS = frozenset(
    {"provider", "attempt", "work_mode", "automatic_retry", "fallback"}
)
_IDQ_MVP_080_REQUEST_FIELDS = frozenset(
    {
        "ticket", "alias", "provider", "attempt", "work_mode",
        "automatic_retry", "fallback", "decision_sha256",
        "qobs_artifact_sha256", "qobs_quota_band", "nonce_sha256",
        "scheduling_snapshot_sha256", "resolved_executable_sha256",
        "account_identity_sha256", "lease_risk_sha256",
    }
)
_IDQ_MVP_080_RECEIPT_FIELDS = frozenset(
    {
        "protocol_version", "ticket", "alias", "provider", "attempt",
        "decision_sha256", "qobs_artifact_sha256", "nonce_sha256",
        "scheduling_snapshot_sha256", "resolved_executable_sha256",
        "account_identity_sha256", "work_result_sha256",
    }
)


@dataclass(frozen=True)
class IdqMvp080Admission:
    """One atomically consumed synthetic IDQ-MVP-080 alias admission."""

    ticket: str
    alias: str
    provider: str
    attempt: int
    work_mode: str
    decision_sha256: str
    qobs_artifact_sha256: str
    nonce_sha256: str
    scheduling_snapshot_sha256: str
    resolved_executable_sha256: str
    account_identity_sha256: str
    lease_risk_sha256: str


_VALIDATED_IDQ_MVP_080_ADMISSION_IDS: set[int] = set()


def _idq_mvp_080_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[a-f0-9]{64}", value) is None:
        raise ConfigurationError(f"IDQ-MVP-080 {label} must be a lowercase SHA-256 digest")
    return value


def _validate_idq_mvp_080_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate the fixed synthetic exception configuration without widening it."""

    if (
        config.get("activation_prohibited") is not True
        or config.get("dispatcher_execution") != "CLOSED"
    ):
        raise ConfigurationError("IDQ-MVP-080 requires ordinary activation CLOSED")
    exception = _mapping(config.get("idq_mvp_080"), "IDQ-MVP-080 configuration")
    if set(exception) != _IDQ_MVP_080_CONFIG_FIELDS or exception.get("ticket") != _IDQ_MVP_080_TICKET:
        raise ConfigurationError("IDQ-MVP-080 configuration is not allowlisted")
    aliases = _mapping(exception.get("aliases"), "IDQ-MVP-080 aliases")
    if set(aliases) != set(_IDQ_MVP_080_ALIASES):
        raise ConfigurationError("IDQ-MVP-080 aliases must be exactly the four allowlisted aliases")
    for alias, provider in _IDQ_MVP_080_ALIASES.items():
        entry = _mapping(aliases.get(alias), f"IDQ-MVP-080 alias {alias}")
        if set(entry) != _IDQ_MVP_080_ALIAS_FIELDS or dict(entry) != {
            "provider": provider,
            "attempt": 1,
            "work_mode": "read_only",
            "automatic_retry": False,
            "fallback": False,
        }:
            raise ConfigurationError("IDQ-MVP-080 alias configuration is not allowlisted")
    return exception


def _consume_idq_mvp_080_marker(alias: str, marker_store: Path | str | os.PathLike[str]) -> None:
    """Atomically consume one alias-local marker without touching a provider."""

    store = Path(marker_store)
    if not store.is_absolute():
        raise ConfigurationError("IDQ-MVP-080 marker store must be absolute")
    try:
        store.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(store, 0o700)
        marker = store / f"idq-mvp-080-{alias}.used"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(marker, flags, 0o600)
        try:
            os.write(descriptor, b"consumed\n")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except FileExistsError as exc:
        raise ConfigurationError("IDQ-MVP-080 alias one-use marker is consumed") from exc
    except OSError as exc:
        raise ConfigurationError("IDQ-MVP-080 marker store is invalid") from exc


def _consume_idq_mvp_080_qobs_nonce(
    nonce_sha256: str, marker_store: Path | str | os.PathLike[str]
) -> None:
    """Atomically consume one validated QOBS nonce before the alias marker.

    The nonce digest has already been syntax-checked and bound to the exact
    QOBS context.  Using it as the durable marker name prevents a genuine
    observation from being replayed through another alias while retaining no
    raw nonce in the filesystem.
    """

    store = Path(marker_store)
    if not store.is_absolute():
        raise ConfigurationError("IDQ-MVP-080 marker store must be absolute")
    try:
        store.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(store, 0o700)
        marker = store / f"idq-mvp-080-qobs-{nonce_sha256}.used"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(marker, flags, 0o600)
        try:
            os.write(descriptor, b"consumed\n")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except FileExistsError as exc:
        raise ConfigurationError("IDQ-MVP-080 QOBS nonce is consumed") from exc
    except OSError as exc:
        raise ConfigurationError("IDQ-MVP-080 marker store is invalid") from exc


def validate_idq_mvp_080_admission(
    config: Mapping[str, Any], request: Mapping[str, Any], marker_store: Path | str | os.PathLike[str]
) -> IdqMvp080Admission:
    """Validate and consume one of four fixed synthetic, read-only admissions."""

    _validate_idq_mvp_080_config(_mapping(config, "configuration"))
    request = _mapping(request, "IDQ-MVP-080 admission request")
    if set(request) != _IDQ_MVP_080_REQUEST_FIELDS:
        raise ConfigurationError("IDQ-MVP-080 admission fields are invalid")
    alias = request.get("alias")
    if alias not in _IDQ_MVP_080_ALIASES:
        raise ConfigurationError("IDQ-MVP-080 alias is not allowlisted")
    provider = _IDQ_MVP_080_ALIASES[alias]
    if (
        request.get("ticket") != _IDQ_MVP_080_TICKET
        or request.get("provider") != provider
        or isinstance(request.get("attempt"), bool)
        or request.get("attempt") != 1
        or request.get("work_mode") != "read_only"
        or request.get("automatic_retry") is not False
        or request.get("fallback") is not False
        or request.get("qobs_quota_band") != "constrained"
    ):
        raise ConfigurationError("IDQ-MVP-080 only permits attempt 1, read-only, no retry or fallback")
    digests = {
        field: _idq_mvp_080_sha256(request.get(field), field)
        for field in (
            "decision_sha256", "qobs_artifact_sha256", "nonce_sha256",
            "scheduling_snapshot_sha256", "resolved_executable_sha256",
            "account_identity_sha256", "lease_risk_sha256",
        )
    }
    _consume_idq_mvp_080_marker(alias, marker_store)
    admission = IdqMvp080Admission(
        ticket=_IDQ_MVP_080_TICKET,
        alias=alias,
        provider=provider,
        attempt=1,
        work_mode="read_only",
        **digests,
    )
    _VALIDATED_IDQ_MVP_080_ADMISSION_IDS.add(id(admission))
    return admission


def _validate_idq_mvp_080_execution_context(
    request: Mapping[str, Any], execution_context: Mapping[str, Any]
) -> None:
    """Validate the closed preflight evidence used at the start boundary.

    This accepts only a genuine, fresh QOBS artifact and its exact local
    context.  Caller-created digest claims are never QOBS evidence.  The
    quota guard is invoked exactly once here, immediately before the nonce and
    alias start-boundary markers are consumed by the execution assemblers.
    """

    context = _mapping(execution_context, "IDQ-MVP-080 execution context")
    required = {"qobs_artifact", "qobs_expected_context", "runtime"}
    if set(context) != required:
        raise ConfigurationError("IDQ-MVP-080 execution context fields are invalid")

    artifact = context.get("qobs_artifact")
    expected = _mapping(
        context.get("qobs_expected_context"), "IDQ-MVP-080 QOBS expected context"
    )
    expected_fields = {
        "alias", "provider", "account_home", "resolved_executable", "ticket_id",
        "attempt_id", "policy_version", "nonce", "observed_at",
    }
    if set(expected) != expected_fields:
        raise ConfigurationError("IDQ-MVP-080 QOBS expected context fields are invalid")
    if (
        expected.get("alias") != request.get("alias")
        or expected.get("provider") != request.get("provider")
        or expected.get("ticket_id") != request.get("ticket")
        or isinstance(expected.get("attempt_id"), bool)
        or expected.get("attempt_id") != request.get("attempt")
    ):
        raise ConfigurationError("IDQ-MVP-080 QOBS context does not match the request")
    try:
        if (
            quota_guard.quota_artifact_sha256(artifact)
            != request.get("qobs_artifact_sha256")
            or quota_guard.sha256_text(expected.get("nonce")) != request.get("nonce_sha256")
            or quota_guard.sha256_text(expected.get("resolved_executable"))
            != request.get("resolved_executable_sha256")
            or quota_guard.sha256_text(expected.get("account_home"))
            != request.get("account_identity_sha256")
        ):
            raise ConfigurationError("IDQ-MVP-080 QOBS evidence is unbound")
        observation = quota_guard.validate_quota_observation(artifact, dict(expected))
    except quota_guard.QuotaObservationError:
        raise
    if observation.get("quota_band") != request.get("qobs_quota_band"):
        raise ConfigurationError("IDQ-MVP-080 QOBS quota band is unbound")

    runtime = _mapping(context.get("runtime"), "IDQ-MVP-080 runtime evidence")
    provider = request.get("provider")
    expected_runtime: Mapping[str, object]
    if provider == "codex":
        expected_runtime = {"read_only": True, "sandbox": "read-only"}
    elif provider == "agy":
        # AGY's plan mode is its strictly read-only command surface.
        expected_runtime = {"read_only": True, "mode": "plan", "sandbox": True}
    else:  # The request validation normally rejects this first; retain closure.
        raise ConfigurationError("IDQ-MVP-080 provider is not allowlisted")
    if dict(runtime) != dict(expected_runtime):
        raise ConfigurationError("IDQ-MVP-080 runtime is not read-only")


def validate_idq_mvp_080_execution_admission(
    config: Mapping[str, Any], request: Mapping[str, Any], execution_context: Mapping[str, Any]
) -> IdqMvp080Admission:
    """Validate (but do not consume) the exact IDQ start-boundary admission.

    The caller must invoke this immediately before `_consume_idq_mvp_080_marker`.
    Keeping consumption outside this pure preflight prevents rejected evidence
    from burning a one-shot alias, while preserving the old data-only admission
    API and its frozen consume-on-validation behavior.
    """

    _validate_idq_mvp_080_config(_mapping(config, "configuration"))
    request = _mapping(request, "IDQ-MVP-080 admission request")
    if set(request) != _IDQ_MVP_080_REQUEST_FIELDS:
        raise ConfigurationError("IDQ-MVP-080 admission fields are invalid")
    alias = request.get("alias")
    if alias not in _IDQ_MVP_080_ALIASES:
        raise ConfigurationError("IDQ-MVP-080 alias is not allowlisted")
    provider = _IDQ_MVP_080_ALIASES[alias]
    if (
        request.get("ticket") != _IDQ_MVP_080_TICKET
        or request.get("provider") != provider
        or isinstance(request.get("attempt"), bool)
        or request.get("attempt") != 1
        or request.get("work_mode") != "read_only"
        or request.get("automatic_retry") is not False
        or request.get("fallback") is not False
        or request.get("qobs_quota_band") != "constrained"
    ):
        raise ConfigurationError("IDQ-MVP-080 only permits attempt 1, read-only, no retry or fallback")
    digests = {
        field: _idq_mvp_080_sha256(request.get(field), field)
        for field in (
            "decision_sha256", "qobs_artifact_sha256", "nonce_sha256",
            "scheduling_snapshot_sha256", "resolved_executable_sha256",
            "account_identity_sha256", "lease_risk_sha256",
        )
    }
    _validate_idq_mvp_080_execution_context(request, execution_context)
    admission = IdqMvp080Admission(
        ticket=_IDQ_MVP_080_TICKET,
        alias=alias,
        provider=provider,
        attempt=1,
        work_mode="read_only",
        **digests,
    )
    _VALIDATED_IDQ_MVP_080_ADMISSION_IDS.add(id(admission))
    return admission


def execute_idq_mvp_080_execution(
    config: Mapping[str, Any],
    request: Mapping[str, Any],
    execution_context: Mapping[str, Any],
    marker_store: Path | str | os.PathLike[str],
    provider_runner: Any,
) -> dict[str, Any]:
    """Assemble the frozen mock-backed IDQ execution flow without a provider CLI.

    `provider_runner` is an injected test seam.  This function deliberately
    has no route resolution, retry, fallback, subprocess, or raw-stream path.
    It validates preflight immediately before atomically burning the alias and
    validates the runner's closed receipt/WorkResult payload before returning.
    """

    if not callable(provider_runner):
        raise ConfigurationError("IDQ-MVP-080 provider runner is invalid")
    admission = validate_idq_mvp_080_execution_admission(
        config, request, execution_context
    )
    _consume_idq_mvp_080_qobs_nonce(admission.nonce_sha256, marker_store)
    _consume_idq_mvp_080_marker(admission.alias, marker_store)
    payload = _mapping(provider_runner(admission), "IDQ-MVP-080 provider payload")
    if set(payload) != {"receipt", "work_result"}:
        raise ConfigurationError("IDQ-MVP-080 provider payload must be receipt and WorkResult only")
    receipt = validate_idq_mvp_080_receipt(
        admission,
        _mapping(payload.get("receipt"), "IDQ-MVP-080 receipt"),
        _mapping(payload.get("work_result"), "IDQ-MVP-080 WorkResult"),
    )
    work_result = normalize_result(_mapping(payload["work_result"], "IDQ-MVP-080 WorkResult"))
    return {"receipt": receipt, "work_result": work_result}


def _idq_mvp_080_provider_argv(admission: IdqMvp080Admission) -> tuple[str, ...]:
    """Return the one fixed, provider-native read-only argv for an admission."""

    if admission.provider == "codex":
        return (
            "codex", "exec", "-C", str(REPOSITORY_ROOT), "-s", "read-only",
            "--json", "-",
        )
    if admission.provider == "agy":
        return (
            "agy", "--mode", "plan", "--sandbox", "--print",
            "--input-format", "stream-json", "--output-format", "stream-json",
        )
    raise ConfigurationError("IDQ-MVP-080 provider is not allowlisted")


def _idq_mvp_080_completed_process_output(completed: Any) -> tuple[int, str | bytes | None]:
    """Extract one injected-process result without exposing provider output."""

    if not isinstance(completed, subprocess.CompletedProcess):
        raise ConfigurationError("IDQ-MVP-080 subprocess result is invalid")
    exit_code = completed.returncode
    if isinstance(exit_code, bool) or not isinstance(exit_code, int):
        raise ConfigurationError("IDQ-MVP-080 subprocess exit code is invalid")
    # stderr is never a result channel.  Reject it rather than retaining or
    # merging it into a receipt, since it can contain provider diagnostics.
    if completed.stderr not in (None, "", b""):
        raise ConfigurationError("IDQ-MVP-080 subprocess stderr is not permitted")
    if not isinstance(completed.stdout, (str, bytes, type(None))):
        raise ConfigurationError("IDQ-MVP-080 subprocess stdout is invalid")
    return exit_code, completed.stdout


def execute_idq_mvp_080_provider_adapter(
    config: Mapping[str, Any],
    request: Mapping[str, Any],
    execution_context: Mapping[str, Any],
    marker_store: Path | str | os.PathLike[str],
    run_subprocess: Any,
) -> dict[str, Any]:
    """Run one injected, provider-native IDQ adapter under the frozen exception.

    This is intentionally a fake-subprocess seam: it never calls
    ``subprocess.run`` itself, retries, falls back, or persists provider output.
    The only irreversible ordering is preflight, alias marker, then the one
    injected process invocation.
    """

    if not callable(run_subprocess):
        raise ConfigurationError("IDQ-MVP-080 subprocess runner is invalid")
    admission = validate_idq_mvp_080_execution_admission(
        config, request, execution_context
    )
    _consume_idq_mvp_080_qobs_nonce(admission.nonce_sha256, marker_store)
    _consume_idq_mvp_080_marker(admission.alias, marker_store)
    completed = run_subprocess(
        _idq_mvp_080_provider_argv(admission),
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    exit_code, output = _idq_mvp_080_completed_process_output(completed)

    # Parse only in memory.  Both native parsers reject raw, malformed,
    # ambiguous, missing-final, and secret-bearing event streams.
    if admission.provider == "codex":
        parsed = _parse_codex_result(output)
    elif admission.provider == "agy":
        parsed = _parse_agy_result(output)
    else:  # Defensive closure if an admission implementation later regresses.
        raise ConfigurationError("IDQ-MVP-080 provider is not allowlisted")
    work_result = normalize_result(parsed.work_result)
    if exit_code != 0 and work_result["status"] == "DONE":
        raise ConfigurationError("IDQ-MVP-080 nonzero execution cannot carry DONE")

    receipt_material = {
        "protocol_version": 2,
        "ticket": admission.ticket,
        "alias": admission.alias,
        "provider": admission.provider,
        "attempt": admission.attempt,
        "decision_sha256": admission.decision_sha256,
        "qobs_artifact_sha256": admission.qobs_artifact_sha256,
        "nonce_sha256": admission.nonce_sha256,
        "scheduling_snapshot_sha256": admission.scheduling_snapshot_sha256,
        "resolved_executable_sha256": admission.resolved_executable_sha256,
        "account_identity_sha256": admission.account_identity_sha256,
        "work_result_sha256": _idq_mvp_080_work_result_sha256(work_result),
    }
    receipt = validate_idq_mvp_080_receipt(admission, receipt_material, work_result)
    # `exit_code` is adapter-local execution metadata; validate the frozen v2
    # binding before exposing this non-secret scalar.
    receipt["exit_code"] = exit_code
    if output is None:
        output_bytes = b""
    elif isinstance(output, bytes):
        output_bytes = output
    else:
        output_bytes = output.encode("utf-8")
    return {
        "receipt": receipt,
        "work_result": work_result,
        "output_evidence": {
            "output_bytes": len(output_bytes),
            "output_sha256": hashlib.sha256(output_bytes).hexdigest(),
            "process_or_session_id": parsed.process_or_session_id,
        },
    }


def _idq_mvp_080_work_result_sha256(work_result: Mapping[str, Any]) -> str:
    """Hash the normalized typed WorkResult in the frozen v2 representation."""

    material = json.dumps(
        work_result, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def validate_idq_mvp_080_receipt(
    admission: IdqMvp080Admission, receipt: Mapping[str, Any], work_result: Mapping[str, Any]
) -> dict[str, Any]:
    """Validate a raw-stream-free receipt bound to one typed WorkResult v2."""

    if (
        not isinstance(admission, IdqMvp080Admission)
        or id(admission) not in _VALIDATED_IDQ_MVP_080_ADMISSION_IDS
    ):
        raise ConfigurationError("IDQ-MVP-080 admission is invalid")
    receipt = _mapping(receipt, "IDQ-MVP-080 receipt")
    if set(receipt) != _IDQ_MVP_080_RECEIPT_FIELDS:
        raise ConfigurationError("IDQ-MVP-080 receipt fields are invalid")
    normalized_result = normalize_result(_mapping(work_result, "IDQ-MVP-080 WorkResult"))
    expected = {
        "protocol_version": 2,
        "ticket": admission.ticket,
        "alias": admission.alias,
        "provider": admission.provider,
        "attempt": admission.attempt,
        "decision_sha256": admission.decision_sha256,
        "qobs_artifact_sha256": admission.qobs_artifact_sha256,
        "nonce_sha256": admission.nonce_sha256,
        "scheduling_snapshot_sha256": admission.scheduling_snapshot_sha256,
        "resolved_executable_sha256": admission.resolved_executable_sha256,
        "account_identity_sha256": admission.account_identity_sha256,
        "work_result_sha256": _idq_mvp_080_work_result_sha256(normalized_result),
    }
    for field, value in expected.items():
        if receipt.get(field) != value:
            raise ConfigurationError(f"IDQ-MVP-080 receipt {field} does not match its admission binding")
    return dict(receipt)


class LocalBootstrapBlocked(ConfigurationError):
    """A local bootstrap observation is not admissible at the spawn boundary."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code.lower())


class LocalBootstrapLifecycleError(ConfigurationError):
    """The local-only lifecycle events are incomplete or out of order."""


@dataclass(frozen=True)
class LocalBootstrapAdmission:
    protocol_version: str
    alias: str
    provider: str
    observed_at: str
    nonce: str
    executable_sha256: str
    account_home_sha256: str
    quota_band: str
    risk_acceptance_id: str | None
    supervisor_instance_id: str
    work_mode: str
    attempt: int
    automatic_retry: bool
    evidence_level: str
    warning: str

    def to_queue_record(self) -> dict[str, object]:
        """Return a path-free warning record, never a provider receipt."""
        return {
            "protocol_version": self.protocol_version,
            "alias": self.alias,
            "provider": self.provider,
            "observed_at": self.observed_at,
            "nonce": self.nonce,
            "executable_sha256": self.executable_sha256,
            "account_home_sha256": self.account_home_sha256,
            "quota_band": self.quota_band,
            "risk_acceptance_id": self.risk_acceptance_id,
            "supervisor_instance_id": self.supervisor_instance_id,
            "work_mode": self.work_mode,
            "attempt": self.attempt,
            "automatic_retry": self.automatic_retry,
            "evidence_level": self.evidence_level,
            "warning": self.warning,
        }


class LocalBootstrapLifecycle:
    """Strict four-event lifecycle; provider start is explicit, not inferred."""

    _events = ("prepared", "starting", "provider_started", "completed")

    def __init__(self, *, on_event: Any) -> None:
        self._on_event = on_event
        self._position = 0
        self.provider_was_started = False
        self.terminal_state: str | None = None

    def _event(self, name: str) -> None:
        if self._position >= len(self._events) or self._events[self._position] != name:
            raise LocalBootstrapLifecycleError("invalid local bootstrap lifecycle")
        self._position += 1
        if name == "provider_started":
            self.provider_was_started = True
        if name == "completed":
            self.terminal_state = "completed"
        self._on_event(name)

    def prepared(self) -> None: self._event("prepared")
    def starting(self) -> None: self._event("starting")
    def provider_started(self) -> None: self._event("provider_started")
    def completed(self) -> None: self._event("completed")


def _bootstrap_digest(path: Path, *, directory: bool) -> str:
    if directory:
        stat_result = path.stat()
        material = f"{stat_result.st_dev}:{stat_result.st_ino}".encode("ascii")
    else:
        material = path.read_bytes()
    return hashlib.sha256(material).hexdigest()


def validate_local_bootstrap_admission(
    admission: LocalBootstrapAdmission,
    *, executable: Path, account_home: Path, active_supervisor_instance_id: str,
    bootstrap_open: bool, bootstrap_sealed: bool, risk_acceptance_exists: bool,
    auth_ready: bool, requested_alias: str, active_aliases: set[str],
) -> LocalBootstrapAdmission:
    """Validate the narrow, ephemeral local admission without changing env state."""
    if not bootstrap_open: raise LocalBootstrapBlocked("BLOCKED_BOOTSTRAP_CLOSED")
    if bootstrap_sealed: raise LocalBootstrapBlocked("BLOCKED_BOOTSTRAP_SEALED")
    if admission.supervisor_instance_id != active_supervisor_instance_id: raise LocalBootstrapBlocked("BLOCKED_BOOTSTRAP_EXPIRED")
    if not admission.risk_acceptance_id or not risk_acceptance_exists: raise LocalBootstrapBlocked("BLOCKED_RISK_ACCEPTANCE")
    if admission.quota_band not in {"unknown", "constrained"}: raise LocalBootstrapBlocked("BLOCKED_QUOTA")
    if admission.work_mode != "read_only": raise LocalBootstrapBlocked("BLOCKED_WORK_MODE")
    if admission.attempt != 1: raise LocalBootstrapBlocked("BLOCKED_ATTEMPT")
    if admission.automatic_retry: raise LocalBootstrapBlocked("BLOCKED_AUTO_RETRY")
    if admission.alias != requested_alias: raise LocalBootstrapBlocked("BLOCKED_ALIAS_MISMATCH")
    if admission.alias in active_aliases: raise LocalBootstrapBlocked("BLOCKED_ALIAS_BUSY")
    if not auth_ready: raise LocalBootstrapBlocked("BLOCKED_AUTH")
    if not executable.is_file() or not os.access(executable, os.X_OK): raise LocalBootstrapBlocked("BLOCKED_EXECUTABLE")
    try:
        if _bootstrap_digest(executable, directory=False) != admission.executable_sha256: raise LocalBootstrapBlocked("BLOCKED_EXECUTABLE")
        if not account_home.is_dir() or _bootstrap_digest(account_home, directory=True) != admission.account_home_sha256: raise LocalBootstrapBlocked("BLOCKED_ACCOUNT_HOME")
    except OSError as exc:
        raise LocalBootstrapBlocked("BLOCKED_EXECUTABLE") from exc
    if not all((admission.observed_at, admission.nonce, admission.executable_sha256, admission.account_home_sha256)):
        raise LocalBootstrapBlocked("BLOCKED_OBSERVATION")
    return admission


def _load_yaml_mapping(path: str | os.PathLike[str], label: str) -> Mapping[str, Any]:
    source = Path(path)
    data = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    return _mapping(data, label)


def load_model_policy(path: str | os.PathLike[str]) -> Mapping[str, Any]:
    """Load the committed, secret-free model capability policy."""

    return _load_yaml_mapping(path, "model policy")


def load_dispatch_decision(path: str | os.PathLike[str]) -> Mapping[str, Any]:
    """Load one orchestrator-authored DispatchDecision JSON or YAML document."""

    return _load_yaml_mapping(path, "DispatchDecision")


def load_scheduling_snapshot(path: str | os.PathLike[str]) -> Mapping[str, Any]:
    """Load one orchestrator-authored Rule 11 scheduling checkpoint."""

    return _load_yaml_mapping(path, "scheduling snapshot")


def validate_scheduling_dispatch(
    snapshot: Mapping[str, Any],
    decision: Mapping[str, Any],
    *,
    role: str,
    ownership: str,
) -> str:
    """Validate and select the current decision ticket under Rule 11."""

    normalized = validate_scheduling_snapshot(snapshot)
    enforce_ticket_dispatch(
        normalized,
        ticket_id=_required_string(decision.get("ticket"), "DispatchDecision ticket"),
        owner=_required_string(role, "dispatch role"),
        ownership=(_required_string(ownership, "ownership"),),
        decision_valid=True,
    )
    return normalized.digest


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    material = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _qobs_digest(value: object) -> str:
    try:
        return quota_guard.quota_artifact_sha256(value)
    except quota_guard.QuotaObservationError as exc:
        raise ConfigurationError("quota observation artifact digest is invalid") from exc


def _require_scheduling_snapshot_digest(
    value: object, error_type: type[ConfigurationError] = ConfigurationError
) -> str:
    """Return one receipt-v2-compatible Rule 11 scheduling snapshot digest."""

    if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
        raise error_type(
            "scheduling_snapshot_sha256 must be a lowercase SHA-256 digest"
        )
    return value


def _qobs_context_digest(context: Mapping[str, object]) -> str:
    return _canonical_sha256(
        {
            "alias": context.get("alias"),
            "provider": context.get("provider"),
            "account_home_sha256": quota_guard.sha256_text(str(context.get("account_home"))),
            "resolved_executable_sha256": quota_guard.sha256_text(
                str(context.get("resolved_executable"))
            ),
            "ticket_id": context.get("ticket_id"),
            "attempt_id": context.get("attempt_id"),
            "policy_version": context.get("policy_version"),
        }
    )


def _consume_qobs_nonce(nonce: str, nonce_store: Path) -> None:
    if not nonce_store.is_absolute():
        raise quota_guard.QuotaObservationError("INVALID_NONCE_STORE")
    try:
        nonce_store.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(nonce_store, 0o700)
        nonce_path = nonce_store / f"{quota_guard.sha256_text(nonce)}.nonce"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(nonce_path, flags, 0o600)
        try:
            os.write(descriptor, b"consumed\n")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except FileExistsError as exc:
        raise quota_guard.QuotaObservationError("REPLAYED_OBSERVATION") from exc
    except OSError as exc:
        raise quota_guard.QuotaObservationError("NONCE_STORE_INVALID") from exc


def consume_quota_observation(
    artifact: object,
    expected_context: dict[str, object],
    *,
    nonce_store: Path | str | os.PathLike[str] | None,
    now: datetime | None = None,
) -> dict[str, str]:
    """Validate and atomically consume one executable QOBS nonce."""

    try:
        observation = quota_guard.validate_quota_observation(
            artifact, expected_context, now=now
        )
    except quota_guard.QuotaObservationError:
        raise
    if observation.get("quota_band") == "unknown":
        raise quota_guard.QuotaObservationError("UNKNOWN_QUOTA")
    if observation.get("quota_band") != "constrained":
        raise quota_guard.QuotaObservationError("QUOTA_NOT_DISPATCHABLE")
    nonce = expected_context.get("nonce")
    if not isinstance(nonce, str):
        raise quota_guard.QuotaObservationError("INVALID_CONTEXT")
    if nonce_store is None:
        raise quota_guard.QuotaObservationError("NONCE_STORE_REQUIRED")
    _consume_qobs_nonce(nonce, Path(nonce_store))
    return {
        "artifact_sha256": _qobs_digest(artifact),
        "nonce_sha256": quota_guard.sha256_text(nonce),
        "quota_band": str(observation["quota_band"]),
    }


def quota_bound_dispatch_identity(
    artifact: object,
    consumption: Mapping[str, object],
    dispatch_context: Mapping[str, object],
) -> str:
    """Derive the receipt identity from exact QOBS and dispatch bindings."""

    artifact_digest = _qobs_digest(artifact)
    if consumption.get("artifact_sha256") != artifact_digest:
        raise ConfigurationError("quota consumption is not bound to the artifact")
    required = {
        "decision_sha256",
        "scheduling_snapshot_sha256",
        "resolved_executable_sha256",
        "policy_version",
    }
    if set(dispatch_context) != required:
        raise ConfigurationError("quota dispatch context fields are invalid")
    _require_scheduling_snapshot_digest(
        dispatch_context.get("scheduling_snapshot_sha256")
    )
    if consumption.get("quota_band") != "constrained":
        raise ConfigurationError("quota consumption is not dispatchable")
    if not isinstance(consumption.get("nonce_sha256"), str):
        raise ConfigurationError("quota nonce consumption proof is invalid")
    return _canonical_sha256(
        {
            "protocol_version": 2,
            "artifact_sha256": artifact_digest,
            "nonce_sha256": consumption["nonce_sha256"],
            "quota_band": consumption["quota_band"],
            **dict(dispatch_context),
        }
    )


def validate_quota_receipt_binding(
    receipt: Mapping[str, object],
    artifact: object,
    consumption: Mapping[str, object],
    dispatch_context: Mapping[str, object],
    expected_context: dict[str, object],
    *,
    now: datetime | None = None,
) -> Mapping[str, object]:
    """Revalidate every transitive QOBS binding carried by a v2 receipt."""

    try:
        observation = quota_guard.validate_quota_observation(
            artifact, expected_context, now=now
        )
    except quota_guard.QuotaObservationError as exc:
        raise ConfigurationError("receipt quota observation is invalid") from exc
    expected_artifact = _qobs_digest(artifact)
    if (
        receipt.get("protocol_version") != 2
        or receipt.get("quota_status") != observation.get("quota_band")
        or receipt.get("quota_status") != consumption.get("quota_band")
        or consumption.get("artifact_sha256") != expected_artifact
        or consumption.get("nonce_sha256") != quota_guard.sha256_text(str(expected_context.get("nonce")))
    ):
        raise ConfigurationError("receipt quota binding is invalid")
    identity = quota_bound_dispatch_identity(artifact, consumption, dispatch_context)
    if receipt.get("dispatch_identity") != identity:
        raise ConfigurationError("receipt dispatch identity is invalid")
    if dispatch_context.get("policy_version") != observation.get("policy_version"):
        raise ConfigurationError("receipt policy binding is invalid")
    if dispatch_context.get("resolved_executable_sha256") != observation.get(
        "resolved_executable_sha256"
    ):
        raise ConfigurationError("receipt executable binding is invalid")
    return receipt


@dataclass(frozen=True)
class QobsAdmission:
    """One consumed, non-transferable admission for the Luna diagnostic.

    This value is intentionally constructed only by
    :func:`validate_closed_dispatch_exception`.  It holds digests and route
    metadata only; neither account-home values nor executable paths escape the
    preflight boundary.
    """

    ticket_id: str
    attempt_id: int
    role: str
    alias: str
    provider: str
    model: str
    effort: str
    quota_band: str
    work_mode: str
    sandbox: str
    execution_exception_id: str
    decision_schema_version: int
    decision_sha256: str
    scheduling_snapshot_sha256: str
    qobs_artifact_sha256: str
    qobs_nonce_sha256: str
    qobs_context_sha256: str
    resolved_executable_sha256: str
    policy_version: str
    exception_consumption_sha256: str
    dispatch_identity: str

    def quota_consumption(self) -> dict[str, str]:
        """Return the exact QOBS consumption proof accepted by receipt-v2."""

        return {
            "artifact_sha256": self.qobs_artifact_sha256,
            "nonce_sha256": self.qobs_nonce_sha256,
            "quota_band": self.quota_band,
        }

    def dispatch_context(self) -> dict[str, str]:
        """Return the receipt-v2 context, excluding non-portable route data."""

        return {
            "decision_sha256": self.decision_sha256,
            "scheduling_snapshot_sha256": self.scheduling_snapshot_sha256,
            "resolved_executable_sha256": self.resolved_executable_sha256,
            "policy_version": self.policy_version,
        }


# This is intentionally process-local rather than an authorization cache.  It
# distinguishes a gate-returned immutable value from a caller-constructed
# lookalike; the durable one-shot use is still committed in the ledger at
# spawn time.
_VALIDATED_QOBS_ADMISSION_IDS: set[int] = set()


def is_validated_qobs_admission(admission: object) -> bool:
    """Return whether this exact admission object came from the closed gate."""

    return isinstance(admission, QobsAdmission) and id(admission) in _VALIDATED_QOBS_ADMISSION_IDS


def _resolve_qobs_executable(route: Route) -> str:
    """Resolve one executable to an absolute, executable regular file path."""

    # Resolve even an absolute configured command through ``which``.  This
    # detects a replaced executable resolution immediately before spawn.
    candidate = shutil.which(route.command)
    if not candidate:
        raise ConfigurationError("execution exception executable is unavailable")
    path = Path(candidate).resolve()
    if not path.is_file() or not os.access(path, os.X_OK):
        raise ConfigurationError("execution exception executable is unavailable")
    return str(path)


_LUNA_ONE_SHOT_EXCEPTION_ID = "luna-delegate-001-codex2-attempt-1"
_LUNA_ONE_SHOT_EXCEPTION_FIELDS = frozenset(
    {
        "ticket",
        "attempt_id",
        "role",
        "alias",
        "provider",
        "decision_schema_version",
        "model",
        "effort",
        "work_mode",
        "sandbox",
        "quota_band",
        "maximum_uses",
        "automatic_retry",
    }
)
_LUNA_ONE_SHOT_EXCEPTION = {
    "ticket": "TICKET-LUNA-DELEGATE-001",
    "attempt_id": 1,
    "role": "codex2_luna_diagnostic",
    "alias": "codex2",
    "provider": "codex",
    "decision_schema_version": 1,
    "model": "gpt-5.6-luna",
    "effort": "xhigh",
    "work_mode": "read_only",
    "sandbox": "read-only",
    "quota_band": "constrained",
    "maximum_uses": 1,
    "automatic_retry": False,
}


def _commit_qobs_one_shot(
    *,
    admission: QobsAdmission,
    ledger_store: Path | str | os.PathLike[str] | None,
    binding: Mapping[str, object],
) -> str:
    """Atomically commit the exception and its nonce in one fixed ledger."""

    if ledger_store is None:
        raise ConfigurationError("one-shot QOBS ledger is required")
    store = Path(ledger_store)
    if not store.is_absolute():
        raise ConfigurationError("execution exception store must be absolute")
    try:
        store.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(store, 0o700)
        marker = store / f"{quota_guard.sha256_text(admission.execution_exception_id)}.used"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(marker, flags, 0o600)
        try:
            material = _canonical_sha256(dict(binding)).encode("ascii") + b"\n"
            os.write(descriptor, material)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except FileExistsError as exc:
        raise quota_guard.QuotaObservationError("EXECUTION_EXCEPTION_CONSUMED") from exc
    except OSError as exc:
        raise ConfigurationError("execution exception store is invalid") from exc
    return _canonical_sha256(dict(binding))


def validate_closed_dispatch_exception(
    config: Mapping[str, Any],
    *,
    execution_exception_id: object,
    decision: object,
    route: Route,
    quota_observation: object,
    expected_qobs_context: Mapping[str, object],
    scheduling_snapshot_sha256: object,
    qobs_nonce_store: Path | str | os.PathLike[str] | None,
    exception_store: Path | str | os.PathLike[str] | None,
    ledger_store: Path | str | os.PathLike[str] | None = None,
    consume: bool = True,
    now: datetime | None = None,
) -> QobsAdmission:
    """Validate the sole closed-dispatch Luna exception.

    This is purposefully separate from ordinary quota-bound dispatch.  It is
    the only place a schema-v1 decision can reach executable admission, and it
    accepts no wildcard ids, routes, sandboxes, quota bands, or retries.
    """

    activation_prohibited, dispatcher_execution = effective_activation_state(config)
    if activation_prohibited is not True or dispatcher_execution != "CLOSED":
        raise ConfigurationError("one-shot exception requires a closed dispatcher")
    runtime = _mapping(config.get("runtime"), "runtime")
    if runtime.get("approved_for_execution") is not True or runtime.get("protocol_version") != 2:
        raise ConfigurationError("one-shot exception requires approved protocol v2 runtime")
    if execution_exception_id != _LUNA_ONE_SHOT_EXCEPTION_ID:
        raise ConfigurationError("execution exception is not approved")
    exceptions = _mapping(config.get("execution_exceptions"), "execution_exceptions")
    exception = _mapping(exceptions.get(_LUNA_ONE_SHOT_EXCEPTION_ID), "execution exception")
    if set(exception) != _LUNA_ONE_SHOT_EXCEPTION_FIELDS or dict(exception) != _LUNA_ONE_SHOT_EXCEPTION:
        raise ConfigurationError("execution exception contract is invalid")
    if (
        route.role != exception["role"]
        or route.alias != exception["alias"]
        or route.cli != exception["provider"]
        or route.model != exception["model"]
        or route.effort != exception["effort"]
        or route.sandbox != exception["sandbox"]
    ):
        raise ConfigurationError("execution exception route is invalid")
    roles = _mapping(config.get("roles"), "roles")
    role_config = _mapping(roles.get(route.role), f"roles.{route.role}")
    if role_config.get("sandbox") != "read-only":
        raise ConfigurationError("execution exception requires read-only sandbox")
    if not isinstance(decision, Mapping):
        raise ConfigurationError("execution exception requires a DispatchDecision")
    if decision.get("schema_version") != exception["decision_schema_version"]:
        raise ConfigurationError("execution exception decision schema is invalid")
    try:
        policy = load_model_policy(
            REPOSITORY_ROOT / ".agents/config/multiagent_model_policy.yaml"
        )
        validated = validate_dispatch_decision(decision, policy, route)
    except (ConfigurationError, DispatchDecisionError, TypeError) as exc:
        raise ConfigurationError("execution exception decision is invalid") from exc
    for field in ("ticket", "selected_alias", "selected_model", "selected_effort", "work_mode", "quota_band"):
        expected = exception["alias"] if field == "selected_alias" else (
            exception["model"] if field == "selected_model" else (
                exception["effort"] if field == "selected_effort" else exception.get(field)
            )
        )
        if validated.decision.get(field) != expected:
            raise ConfigurationError("execution exception decision does not match its contract")
    if validated.decision.get("ticket") != exception["ticket"]:
        raise ConfigurationError("execution exception ticket is invalid")
    snapshot_digest = _require_scheduling_snapshot_digest(scheduling_snapshot_sha256)
    if not isinstance(expected_qobs_context, Mapping):
        raise ConfigurationError("execution exception QOBS context is invalid")
    qobs_policy_version = expected_qobs_context.get("policy_version")
    if (
        qobs_policy_version not in {"2026-08-26.1", "2026-08-29.1"}
        or qobs_policy_version != validated.policy_version
    ):
        raise ConfigurationError("execution exception QOBS context does not match route")
    required_context = {
        "alias": route.alias,
        "provider": route.cli,
        "ticket_id": exception["ticket"],
        "attempt_id": exception["attempt_id"],
        "policy_version": validated.policy_version,
    }
    for field, expected in required_context.items():
        if expected_qobs_context.get(field) != expected:
            raise ConfigurationError("execution exception QOBS context does not match route")
    for field in ("account_home", "resolved_executable", "nonce", "observed_at"):
        if not isinstance(expected_qobs_context.get(field), str) or not expected_qobs_context[field]:
            raise ConfigurationError("execution exception QOBS context is incomplete")
    try:
        observation = quota_guard.validate_quota_observation(
            quota_observation, dict(expected_qobs_context), now=now
        )
    except quota_guard.QuotaObservationError:
        raise
    if observation.get("quota_band") == "unknown":
        raise quota_guard.QuotaObservationError("UNKNOWN_QUOTA")
    if observation.get("quota_band") != exception["quota_band"]:
        raise quota_guard.QuotaObservationError("QUOTA_NOT_DISPATCHABLE")
    resolved_executable = _resolve_qobs_executable(route)
    if "/" in route.command and resolved_executable != expected_qobs_context["resolved_executable"]:
        raise ConfigurationError("execution exception executable is not pinned to QOBS")
    nonce = str(expected_qobs_context["nonce"])
    artifact_sha256 = _qobs_digest(quota_observation)
    context_sha256 = _qobs_context_digest(expected_qobs_context)
    consumption_binding = {
        "exception_id": _LUNA_ONE_SHOT_EXCEPTION_ID,
        "decision_sha256": validated.digest,
        "scheduling_snapshot_sha256": snapshot_digest,
        "qobs_artifact_sha256": artifact_sha256,
        "qobs_nonce_sha256": quota_guard.sha256_text(nonce),
        "qobs_context_sha256": context_sha256,
    }
    exception_consumption_sha256 = _canonical_sha256(consumption_binding)
    consumption = {
        "artifact_sha256": artifact_sha256,
        "nonce_sha256": quota_guard.sha256_text(nonce),
        "quota_band": str(observation["quota_band"]),
    }
    dispatch_context = {
        "decision_sha256": validated.digest,
        "scheduling_snapshot_sha256": snapshot_digest,
        "resolved_executable_sha256": str(observation["resolved_executable_sha256"]),
        "policy_version": validated.policy_version,
    }
    admission = QobsAdmission(
        ticket_id=str(exception["ticket"]),
        attempt_id=int(exception["attempt_id"]),
        role=str(exception["role"]),
        alias=str(exception["alias"]),
        provider=str(exception["provider"]),
        model=str(exception["model"]),
        effort=str(exception["effort"]),
        quota_band=str(exception["quota_band"]),
        work_mode=str(exception["work_mode"]),
        sandbox=str(exception["sandbox"]),
        execution_exception_id=_LUNA_ONE_SHOT_EXCEPTION_ID,
        decision_schema_version=int(exception["decision_schema_version"]),
        decision_sha256=validated.digest,
        scheduling_snapshot_sha256=snapshot_digest,
        qobs_artifact_sha256=artifact_sha256,
        qobs_nonce_sha256=consumption["nonce_sha256"],
        qobs_context_sha256=context_sha256,
        resolved_executable_sha256=dispatch_context["resolved_executable_sha256"],
        policy_version=validated.policy_version,
        exception_consumption_sha256=exception_consumption_sha256,
        dispatch_identity=quota_bound_dispatch_identity(
            quota_observation, consumption, dispatch_context
        ),
    )
    _VALIDATED_QOBS_ADMISSION_IDS.add(id(admission))
    if consume:
        # Legacy callers may still pass the two historical store arguments.
        # They now select one ledger only; the nonce is recorded in the same
        # atomic marker and no early two-store commit remains.
        selected_ledger = ledger_store if ledger_store is not None else exception_store
        _commit_qobs_one_shot(
            admission=admission,
            ledger_store=selected_ledger,
            binding=consumption_binding,
        )
    return admission


def validate_closed_dispatch_execution_args(
    args: argparse.Namespace, config: Mapping[str, Any]
) -> None:
    """Reject partial exception evidence before executable preflight."""

    if not getattr(args, "execute", False):
        return
    quota_path = getattr(args, "quota_observation", None)
    exception_id = getattr(args, "execution_exception_id", None)
    if bool(quota_path) != bool(exception_id):
        raise DispatchDecisionError(
            "--quota-observation and --execution-exception-id are required together"
        )


def _load_closed_dispatch_qobs(path: str | os.PathLike[str]) -> object:
    """Read a QOBS artifact as strict JSON without exposing its contents."""

    try:
        return quota_guard.strict_json_loads(Path(path).read_bytes())
    except (OSError, quota_guard.QuotaObservationError) as exc:
        raise ConfigurationError("closed dispatch quota observation is unavailable") from exc


def _closed_dispatch_qobs_context(
    artifact: object,
    *,
    route: Route,
    decision: Mapping[str, Any],
    attempt_id: int,
) -> dict[str, object]:
    """Bind QOBS provenance to this process-local route without logging paths."""

    if route.home_path is None:
        raise ConfigurationError("closed dispatch route lacks account-home identity")
    resolved_executable = shutil.which(route.command)
    if not resolved_executable:
        raise ConfigurationError("closed dispatch executable is unavailable")
    try:
        observation = _mapping(_mapping(artifact, "quota observation artifact").get("observation"), "quota observation")
        nonce = observation.get("nonce")
        observed_at = observation.get("observed_at")
    except ConfigurationError:
        raise
    if not isinstance(nonce, str) or not isinstance(observed_at, str):
        raise ConfigurationError("closed dispatch quota observation is incomplete")
    return {
        "alias": route.alias,
        "provider": route.cli,
        "account_home": route.home_path,
        "resolved_executable": str(Path(resolved_executable).resolve()),
        "ticket_id": decision.get("ticket"),
        "attempt_id": attempt_id,
        "policy_version": decision.get("policy_version"),
        "nonce": nonce,
        "observed_at": observed_at,
    }


def validate_quota_bound_dispatch(
    decision: Mapping[str, object],
    artifact: object,
    expected_context: dict[str, object],
    *,
    scheduling_snapshot_sha256: object,
    nonce_store: Path | str | os.PathLike[str] | None,
    now: datetime | None = None,
) -> dict[str, object]:
    """Validate QOBS and reject legacy v1 decisions before execution.

    The caller must provide the validated Rule 11 scheduling snapshot digest
    that receipt-v2 binds to this dispatch.
    """

    scheduling_snapshot_sha256 = _require_scheduling_snapshot_digest(
        scheduling_snapshot_sha256, DispatchDecisionError
    )

    if decision.get("schema_version") == 1:
        raise DispatchDecisionError(
            "DispatchDecision v1 is non-executable for quota-bound dispatch"
        )
    try:
        policy = load_model_policy(REPOSITORY_ROOT / ".agents/config/multiagent_model_policy.yaml")
        validated = validate_dispatch_decision(decision, policy)
    except (ConfigurationError, TypeError) as exc:
        raise DispatchDecisionError("DispatchDecision is invalid") from exc
    observation = quota_guard.validate_quota_observation(
        artifact, expected_context, now=now
    )
    if validated.decision.get("quota_band") != observation.get("quota_band"):
        raise DispatchDecisionError("DispatchDecision quota band contradicts observation")
    consumption = consume_quota_observation(
        artifact, expected_context, nonce_store=nonce_store, now=now
    )
    dispatch_context = {
        "decision_sha256": validated.digest,
        "scheduling_snapshot_sha256": scheduling_snapshot_sha256,
        "resolved_executable_sha256": observation["resolved_executable_sha256"],
        "policy_version": observation["policy_version"],
    }
    return {
        "decision": dict(validated.decision),
        "decision_sha256": validated.digest,
        "consumption": consumption,
        "dispatch_context": dispatch_context,
    }


def _utc_datetime() -> datetime:
    """Capture one timezone-aware UTC instant for a validation transaction."""

    return datetime.now(timezone.utc)


def _format_utc(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
        raise ConfigurationError("UTC evidence timestamp is invalid")
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _utc_now() -> str:
    """Return a stable RFC 3339 UTC timestamp for execution evidence."""

    return _format_utc(_utc_datetime())


def _parse_utc_timestamp(value: Any, label: str) -> datetime:
    text = _required_string(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ConfigurationError(f"{label} must be an RFC 3339 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ConfigurationError(f"{label} must use UTC")
    return parsed


def _secret_bearing_path(value: Any, path: str = "$") -> str | None:
    """Return the first secret-shaped value path without exposing its content."""

    if isinstance(value, str):
        if any(pattern.search(value) for pattern in SECRET_VALUE_PATTERNS):
            return path
        return None
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if re.search(
                r"(?i)(?:^|_)(?:password|secret|authorization|cookie|api_key|access_token|refresh_token)(?:$|_)",
                key_text,
            ):
                return f"{path}.{key_text}"
            found = _secret_bearing_path(item, f"{path}.{key_text}")
            if found:
                return found
        return None
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            found = _secret_bearing_path(item, f"{path}[{index}]")
            if found:
                return found
    return None


def _reject_secret_bearing(value: Any, label: str) -> None:
    secret_path = _secret_bearing_path(value)
    if secret_path:
        raise ConfigurationError(f"{label} contains secret-bearing content at {secret_path}")


def _redact_personal_text(value: str) -> str:
    """Remove common personal identifiers while retaining useful evidence."""

    redacted = EMAIL_PATTERN.sub("<EMAIL_REDACTED>", value)
    redacted = LABELED_PERSONAL_ID_PATTERN.sub("<PERSONAL_ID_REDACTED>", redacted)
    redacted = HOME_PATH_PATTERN.sub("<USER_HOME_REDACTED>", redacted)
    return IP_ADDRESS_PATTERN.sub("<IP_REDACTED>", redacted)


def _validate_string_collection(
    value: Any,
    label: str,
    *,
    allow_string: bool = False,
    require_non_empty: bool = False,
    require_non_empty_items: bool = False,
) -> None:
    """Validate the exact JSON string/array shapes used by WorkResult v2."""

    if allow_string and isinstance(value, str):
        if require_non_empty and not value.strip():
            raise ConfigurationError(f"{label} must not be empty")
        return
    if not isinstance(value, list):
        expected = "text or a list" if allow_string else "a list"
        raise ConfigurationError(f"{label} must be {expected} of strings")
    if require_non_empty and not value:
        raise ConfigurationError(f"{label} must not be empty")
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise ConfigurationError(f"{label}[{index}] must be a string")
        if require_non_empty_items and not item.strip():
            raise ConfigurationError(f"{label}[{index}] must not be empty")


def _provider_compatible_work_result_schema(
    path: str | os.PathLike[str],
) -> dict[str, Any]:
    """Build the strict provider subset of the authoritative WorkResult schema.

    Codex structured output rejects ``oneOf``. The authoritative local schema
    permits text-or-array values for three fields, so provider generation uses
    the array branch for those fields. This is a strict subset, not a relaxed
    fallback: all required fields, closed objects, and string item types remain
    mandatory, and ``normalize_result`` independently validates the returned
    object after the provider exits.
    """

    source_path = Path(path)
    try:
        raw_schema = json.loads(source_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigurationError("WorkResult v2 output schema is not valid JSON") from exc
    source = _mapping(raw_schema, "WorkResult v2 output schema")
    if source.get("type") != "object" or source.get("additionalProperties") is not False:
        raise ConfigurationError("WorkResult v2 output schema must be a closed object")
    required = source.get("required")
    if (
        not isinstance(required, list)
        or len(required) != len(set(required))
        or set(required) != RESULT_FIELDS
    ):
        raise ConfigurationError("WorkResult v2 output schema required fields are invalid")
    source_properties = _mapping(
        source.get("properties"), "WorkResult v2 output schema properties"
    )
    if set(source_properties) != RESULT_FIELDS:
        raise ConfigurationError("WorkResult v2 output schema properties are invalid")

    # JSON round-tripping provides a plain, detached JSON value without adding
    # a runtime dependency on a JSON Schema implementation.
    provider_schema = json.loads(json.dumps(source))
    provider_schema.pop("$schema", None)
    provider_schema.pop("$id", None)
    provider_properties = provider_schema["properties"]
    for field in PROVIDER_ARRAY_RESULT_FIELDS:
        field_schema = _mapping(
            source_properties[field], f"WorkResult v2 output schema properties.{field}"
        )
        choices = field_schema.get("oneOf")
        if not isinstance(choices, list):
            raise ConfigurationError(
                f"WorkResult v2 output schema properties.{field} must declare oneOf"
            )
        array_choices = [
            choice
            for choice in choices
            if isinstance(choice, Mapping) and choice.get("type") == "array"
        ]
        if len(array_choices) != 1:
            raise ConfigurationError(
                f"WorkResult v2 output schema properties.{field} must have one array branch"
            )
        array_schema = json.loads(json.dumps(array_choices[0]))
        items = _mapping(
            array_schema.get("items"),
            f"WorkResult v2 output schema properties.{field}.items",
        )
        if items.get("type") != "string":
            raise ConfigurationError(
                f"WorkResult v2 output schema properties.{field} items must be strings"
            )
        provider_properties[field] = array_schema

    evidence_schema = _mapping(
        source_properties["evidence"], "WorkResult v2 output schema properties.evidence"
    )
    evidence_properties = _mapping(
        evidence_schema.get("properties"),
        "WorkResult v2 output schema properties.evidence.properties",
    )
    if (
        evidence_schema.get("type") != "object"
        or evidence_schema.get("additionalProperties") is not False
        or set(evidence_schema.get("required", [])) != {"commands", "outcomes", "artifacts"}
        or set(evidence_properties) != {"commands", "outcomes", "artifacts"}
    ):
        raise ConfigurationError("WorkResult v2 evidence schema is not strict")
    for field, field_schema in evidence_properties.items():
        field_schema = _mapping(
            field_schema, f"WorkResult v2 output schema evidence.{field}"
        )
        items = _mapping(
            field_schema.get("items"),
            f"WorkResult v2 output schema evidence.{field}.items",
        )
        if field_schema.get("type") != "array" or items.get("type") != "string":
            raise ConfigurationError(
                f"WorkResult v2 output schema evidence.{field} must be a string array"
            )

    def reject_provider_unsupported_shape(value: Any, location: str = "$") -> None:
        if isinstance(value, Mapping):
            if "oneOf" in value:
                raise ConfigurationError(
                    f"provider WorkResult schema retains unsupported oneOf at {location}"
                )
            for key, item in value.items():
                reject_provider_unsupported_shape(item, f"{location}.{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                reject_provider_unsupported_shape(item, f"{location}[{index}]")

    reject_provider_unsupported_shape(provider_schema)
    return provider_schema


def _required_string(value: Any, label: str, *, safe_name: bool = False) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DispatchDecisionError(f"{label} must be non-empty text")
    normalized = value.strip()
    if safe_name and not SAFE_NAME.fullmatch(normalized):
        raise DispatchDecisionError(f"{label} contains unsupported characters")
    return normalized


def _required_rank(value: Any, label: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DispatchDecisionError(f"{label} must be an integer")
    if value < minimum or value > maximum:
        raise DispatchDecisionError(f"{label} must be between {minimum} and {maximum}")
    return value


def _policy_sequence(policy: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = policy.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) for item in value):
        raise ConfigurationError(f"model policy {key} must be a non-empty string list")
    return tuple(value)


def _validated_model_catalog(
    policy: Mapping[str, Any], minimum: int, maximum: int
) -> Mapping[str, Mapping[str, Any]]:
    """Reject incomplete, unavailable, deprecated, or provider-invalid models."""

    models = _mapping(policy.get("models"), "model policy models")
    if not models:
        raise ConfigurationError("model policy models must not be empty")
    provider_efforts = {"codex": VALID_EFFORTS, "agy": VALID_AGY_EFFORTS}
    fallback_orders: set[tuple[str, int]] = set()
    for model, raw_spec in models.items():
        spec = _mapping(raw_spec, f"model policy models.{model}")
        cli = spec.get("cli")
        if cli not in VALID_CLIS:
            raise ConfigurationError(f"model policy models.{model}.cli is invalid")
        if spec.get("availability") is not True:
            raise ConfigurationError(f"model policy models.{model}.availability must be true")
        if spec.get("deprecated") is not False:
            raise ConfigurationError(f"model policy models.{model}.deprecated must be false")
        fallback_order = spec.get("fallback_order")
        if isinstance(fallback_order, bool) or not isinstance(fallback_order, int) or fallback_order < 1:
            raise ConfigurationError(
                f"model policy models.{model}.fallback_order must be a positive integer"
            )
        fallback_key = (cli, fallback_order)
        if fallback_key in fallback_orders:
            raise ConfigurationError(f"model policy has duplicate {cli} fallback_order")
        fallback_orders.add(fallback_key)
        if "allowed_roles" in spec:
            allowed_roles = spec.get("allowed_roles")
            if not isinstance(allowed_roles, list) or not allowed_roles or not all(isinstance(item, str) for item in allowed_roles):
                raise ConfigurationError(
                    f"model policy models.{model}.allowed_roles must be a non-empty string list"
                )
        if "allowed_phases" in spec:
            allowed_phases = spec.get("allowed_phases")
            if not isinstance(allowed_phases, list) or not allowed_phases or not all(isinstance(item, str) for item in allowed_phases):
                raise ConfigurationError(
                    f"model policy models.{model}.allowed_phases must be a non-empty string list"
                )
        efforts = _mapping(spec.get("efforts"), f"model policy models.{model}.efforts")
        if not efforts:
            raise ConfigurationError(f"model policy models.{model}.efforts must not be empty")
        for effort, raw_effort_spec in efforts.items():
            if effort not in provider_efforts[cli]:
                raise ConfigurationError(
                    f"model policy models.{model} has unsupported {cli} effort: {effort}"
                )
            effort_spec = _mapping(
                raw_effort_spec, f"model policy models.{model}.efforts.{effort}"
            )
            _required_rank(
                effort_spec.get("quality_rank"),
                f"model policy quality rank for {model}/{effort}",
                minimum,
                maximum,
            )
    return models


def validate_dispatch_decision(
    decision: Mapping[str, Any],
    policy: Mapping[str, Any],
    route: Route | None = None,
) -> ValidatedDispatchDecision:
    """Validate one decision against the versioned capability and safety policy.

    This function is intentionally deterministic: the orchestrator owns the
    classification and rationale, while this boundary computes the maximum
    rank, supported provider/model/effort combination, and hard safety gates.
    """

    decision = _mapping(decision, "DispatchDecision")
    policy = _mapping(policy, "model policy")
    unknown = set(decision) - DISPATCH_DECISION_FIELDS - DISPATCH_DECISION_OPTIONAL_FIELDS
    missing = DISPATCH_DECISION_FIELDS - set(decision)
    if missing:
        raise DispatchDecisionError(
            "DispatchDecision missing fields: " + ", ".join(sorted(missing))
        )
    if unknown:
        raise DispatchDecisionError(
            "DispatchDecision contains unsupported fields: " + ", ".join(sorted(unknown))
        )

    policy_schema = policy.get("schema_version")
    decision_schema = policy.get("decision_schema_version")
    if policy_schema != 1 or decision_schema != 1:
        raise ConfigurationError("model policy schema_version and decision_schema_version must be 1")
    if decision.get("schema_version") != decision_schema:
        raise DispatchDecisionError("DispatchDecision schema_version does not match model policy")

    policy_version = _required_string(policy.get("policy_version"), "model policy policy_version")
    selected_policy_version = _required_string(
        decision.get("policy_version"), "DispatchDecision policy_version"
    )
    if selected_policy_version != policy_version and selected_policy_version not in {"2026-08-26.1", "2026-08-29.1"}:
        raise DispatchDecisionError("DispatchDecision policy_version does not match loaded model policy")

    rank_min = policy.get("rank_min")
    rank_max = policy.get("rank_max")
    if isinstance(rank_min, bool) or not isinstance(rank_min, int):
        raise ConfigurationError("model policy rank_min must be an integer")
    if isinstance(rank_max, bool) or not isinstance(rank_max, int) or rank_max < rank_min:
        raise ConfigurationError("model policy rank_max must be an integer at or above rank_min")
    rank_dimensions = _policy_sequence(policy, "rank_dimensions")
    expected_dimensions = (
        "scope_rank",
        "complexity_rank",
        "risk_rank",
        "ambiguity_rank",
        "evidence_burden_rank",
    )
    if rank_dimensions != expected_dimensions:
        raise ConfigurationError("model policy rank_dimensions does not match DispatchDecision v1")
    ranks = {
        field: _required_rank(decision.get(field), f"DispatchDecision {field}", rank_min, rank_max)
        for field in rank_dimensions
    }
    quality_floor = max(ranks.values())
    quality_floors = _mapping(policy.get("quality_floors"), "model policy quality_floors")
    if quality_floor not in quality_floors and str(quality_floor) not in quality_floors:
        raise ConfigurationError(f"model policy has no quality floor {quality_floor}")
    floor_entry = quality_floors.get(quality_floor)
    if floor_entry is None:
        floor_entry = quality_floors.get(str(quality_floor))
    floor_spec = _mapping(floor_entry, f"model policy quality_floors.{quality_floor}")
    floor_profile = floor_spec.get("reference_profile") or floor_spec.get("profile")
    if not isinstance(floor_profile, str) or not floor_profile:
        raise ConfigurationError(
            f"model policy quality_floors.{quality_floor} must define reference_profile or profile"
        )
    critical_rank = policy.get("critical_rank")
    if isinstance(critical_rank, bool) or not isinstance(critical_rank, int):
        raise ConfigurationError("model policy critical_rank must be an integer")

    ticket = _required_string(decision.get("ticket"), "DispatchDecision ticket", safe_name=True)
    phase = _required_string(decision.get("phase"), "DispatchDecision phase", safe_name=True)
    if phase not in _policy_sequence(policy, "phases"):
        raise DispatchDecisionError(f"DispatchDecision phase is unsupported: {phase}")
    work_mode = _required_string(
        decision.get("work_mode"), "DispatchDecision work_mode", safe_name=True
    )
    if work_mode not in _policy_sequence(policy, "work_modes"):
        raise DispatchDecisionError(f"DispatchDecision work_mode is unsupported: {work_mode}")
    quota_band = _required_string(
        decision.get("quota_band"), "DispatchDecision quota_band", safe_name=True
    )
    if quota_band not in _policy_sequence(policy, "quota_bands"):
        raise DispatchDecisionError(f"DispatchDecision quota_band is unsupported: {quota_band}")

    selected_alias = _required_string(
        decision.get("selected_alias"), "DispatchDecision selected_alias", safe_name=True
    )
    if selected_alias not in GOVERNED_ACCOUNT_ALIASES:
        raise DispatchDecisionError("DispatchDecision selected_alias is outside the approved allowlist")
    selected_model = _required_string(
        decision.get("selected_model"), "DispatchDecision selected_model", safe_name=True
    )
    selected_effort = _required_string(
        decision.get("selected_effort"), "DispatchDecision selected_effort", safe_name=True
    )
    if selected_effort not in VALID_EFFORTS:
        raise DispatchDecisionError(f"DispatchDecision selected_effort is unsupported: {selected_effort}")
    _required_string(decision.get("rationale"), "DispatchDecision rationale")
    for boolean_field in ("planning_to_medium_confirmed", "hitl_approved"):
        if not isinstance(decision.get(boolean_field), bool):
            raise DispatchDecisionError(f"DispatchDecision {boolean_field} must be boolean")

    models = _validated_model_catalog(policy, rank_min, rank_max)
    if selected_model not in models:
        raise DispatchDecisionError(
            f"DispatchDecision selected_model is absent from the capability catalog: {selected_model}"
        )
    model_spec = _mapping(models[selected_model], f"model policy models.{selected_model}")
    model_cli = model_spec.get("cli")
    if model_cli not in VALID_CLIS:
        raise ConfigurationError(f"model policy models.{selected_model}.cli is invalid")
    if "allowed_roles" in model_spec:
        if route is None:
            raise DispatchDecisionError(
                f"{selected_model} is role-restricted and requires a bound Route with an authorized role"
            )
        if route.role not in model_spec["allowed_roles"]:
            raise DispatchDecisionError(
                f"{selected_model} is restricted to roles: {', '.join(model_spec['allowed_roles'])}; got {route.role}"
            )
    if "allowed_phases" in model_spec:
        if phase not in model_spec["allowed_phases"]:
            raise DispatchDecisionError(
                f"{selected_model} is restricted to phases: {', '.join(model_spec['allowed_phases'])}; got {phase}"
            )
    efforts = _mapping(
        model_spec.get("efforts"), f"model policy models.{selected_model}.efforts"
    )
    if selected_effort not in efforts:
        raise DispatchDecisionError(
            f"unsupported model/effort combination: {selected_model}/{selected_effort}"
        )
    effort_spec = _mapping(
        efforts[selected_effort],
        f"model policy models.{selected_model}.efforts.{selected_effort}",
    )
    model_quality_rank = _required_rank(
        effort_spec.get("quality_rank"),
        f"model policy quality rank for {selected_model}/{selected_effort}",
        rank_min,
        rank_max,
    )
    if model_quality_rank < quality_floor:
        raise DispatchDecisionError(
            f"selected route quality rank {model_quality_rank} is below required floor {quality_floor}; "
            "quota must not silently downgrade quality"
        )

    quality_exception = decision.get("quality_exception")
    if selected_effort in {"max", "ultra"}:
        if effort_spec.get("quality_exception") is not True:
            raise DispatchDecisionError(
                f"{selected_model}/{selected_effort} is not a catalog-supported quality exception"
            )
        _required_string(quality_exception, "DispatchDecision quality_exception")
    elif quality_exception is not None:
        raise DispatchDecisionError("DispatchDecision quality_exception is valid only for max/ultra")

    if phase == "planning" and quality_floor == critical_rank:
        planning_profile = _mapping(policy.get("rank_3_planning"), "model policy rank_3_planning")
        planning_model = planning_profile.get("model")
        planning_efforts = planning_profile.get("efforts")
        if (
            selected_model != planning_model
            or not isinstance(planning_efforts, list)
            or selected_effort not in planning_efforts
        ):
            raise DispatchDecisionError(
                "rank-3 planning requires the cataloged planning model with xhigh or an approved exception"
            )

    if phase != "planning" and decision["planning_to_medium_confirmed"] is not True:
        raise DispatchDecisionError(
            "NEEDS_HITL: non-planning execution requires fresh root medium confirmation",
            status="NEEDS_HITL",
        )
    if (
        max(ranks["risk_rank"], ranks["ambiguity_rank"]) >= critical_rank
        and decision["hitl_approved"] is not True
    ):
        raise DispatchDecisionError(
            "NEEDS_HITL: critical risk or ambiguity requires approval before dispatch",
            status="NEEDS_HITL",
        )

    broad_scope_rank = policy.get("broad_scope_rank")
    high_risk_rank = policy.get("high_risk_rank")
    if not isinstance(broad_scope_rank, int) or not isinstance(high_risk_rank, int):
        raise ConfigurationError("model policy quota thresholds must be integers")
    if quota_band == "below_10_percent" and ranks["scope_rank"] >= broad_scope_rank:
        raise DispatchDecisionError("quota below 10% blocks broad work")
    if quota_band == "unknown" and (
        ranks["scope_rank"] >= broad_scope_rank or ranks["risk_rank"] >= high_risk_rank
    ):
        raise DispatchDecisionError("unknown quota blocks large or high-risk work")

    if route is not None:
        disagreements = []
        for field, actual, expected in (
            ("alias", route.alias, selected_alias),
            ("model", route.model, selected_model),
            ("effort", route.effort, selected_effort),
            ("provider", route.cli, model_cli),
        ):
            if actual != expected:
                disagreements.append(f"{field}={actual!r} expected {expected!r}")
        if disagreements:
            raise DispatchDecisionError(
                "resolved route disagrees with DispatchDecision: " + "; ".join(disagreements)
            )

    normalized = dict(decision)
    normalized.update(
        {
            "ticket": ticket,
            "phase": phase,
            "work_mode": work_mode,
            "quota_band": quota_band,
            "selected_alias": selected_alias,
            "selected_model": selected_model,
            "selected_effort": selected_effort,
            "policy_version": selected_policy_version,
        }
    )
    return ValidatedDispatchDecision(
        decision=normalized,
        digest=_canonical_sha256(normalized),
        policy_version=selected_policy_version,
        quality_floor=quality_floor,
        model_quality_rank=model_quality_rank,
    )


def resolve_route(
    config: Mapping[str, Any],
    role: str,
    *,
    alias_override: str | None = None,
    cli_override: str | None = None,
    model_override: str | None = None,
    effort_override: str | None = None,
) -> Route:
    """Resolve a role and validated orchestrator overrides into an account route."""

    roles = _mapping(config.get("roles"), "roles")
    accounts = _mapping(config.get("accounts"), "accounts")
    if set(accounts) - GOVERNED_ACCOUNT_ALIASES:
        raise ConfigurationError("accounts contains an alias outside the approved account alias allowlist")
    if role not in roles:
        raise ConfigurationError(f"unknown role: {role}")
    role_config = _mapping(roles[role], f"roles.{role}")

    configured_alias = role_config.get("alias")
    alias = configured_alias if alias_override is None else alias_override
    if not isinstance(alias, str) or not SAFE_NAME.fullmatch(alias):
        raise ConfigurationError("role alias is missing or invalid")
    if alias not in accounts:
        raise ConfigurationError(f"unknown account alias: {alias}")
    if alias not in GOVERNED_ACCOUNT_ALIASES:
        raise ConfigurationError(f"alias is outside the approved account alias allowlist: {alias}")
    account = _mapping(accounts[alias], f"accounts.{alias}")

    account_cli = account.get("cli")
    if account_cli != ALIAS_PROVIDER_MAP[alias]:
        raise ProviderExecutableBindingError()
    role_cli = role_config.get("cli", account_cli)
    cli = role_cli if cli_override is None else cli_override
    if cli not in VALID_CLIS:
        raise ConfigurationError(f"unsupported CLI: {cli}")
    if account_cli not in VALID_CLIS:
        raise ConfigurationError(f"accounts.{alias}.cli must be codex or agy")
    if cli != account_cli:
        raise ProviderExecutableBindingError()

    command = account.get("command", cli)
    if not isinstance(command, str) or not SAFE_COMMAND.fullmatch(command):
        raise ConfigurationError("account command must be one executable path without arguments")

    expected_home_env = VALID_HOME_ENV[cli]
    home_env = account.get("home_env")
    if home_env is not None and home_env != expected_home_env:
        raise ConfigurationError(f"{cli} accounts may set only {expected_home_env}")
    home_path = _expand_home_path(account.get("home_path"))
    if bool(home_env) != bool(home_path):
        raise ConfigurationError("home_env and home_path must be configured together")

    model = _optional_safe_name(
        role_config.get("model") if model_override is None else model_override,
        "model",
    )
    effort = _optional_safe_name(
        role_config.get("effort") if effort_override is None else effort_override,
        "effort",
    )
    if effort is not None and effort not in VALID_EFFORTS:
        raise ConfigurationError(f"unsupported reasoning effort: {effort}")
    mode = _optional_safe_name(role_config.get("mode"), "mode")
    raw_sandbox = role_config.get("sandbox")
    if cli == "agy":
        if effort is not None and effort not in VALID_AGY_EFFORTS:
            raise ConfigurationError(f"unsupported AGY reasoning effort: {effort}")
        if mode is not None and mode not in VALID_AGY_MODES:
            raise ConfigurationError(f"unsupported AGY mode: {mode}")
        if raw_sandbox is not None and not isinstance(raw_sandbox, bool):
            raise ConfigurationError("AGY sandbox must be true or false")
        sandbox: str | bool | None = raw_sandbox
    else:
        sandbox = _optional_safe_name(raw_sandbox, "sandbox")
        if sandbox is not None and sandbox not in VALID_SANDBOXES:
            raise ConfigurationError(f"unsupported sandbox: {sandbox}")

    route = Route(
        role=role,
        alias=alias,
        cli=cli,
        command=command,
        home_env=home_env,
        home_path=home_path,
        model=model,
        effort=effort,
        mode=mode,
        sandbox=sandbox,
    )
    _validate_route_provider_binding(route)
    return route


def render_prompt(
    *,
    objective: str,
    ownership: str = DEFAULT_OWNERSHIP,
    boundaries: str = DEFAULT_BOUNDARIES,
    evidence: str = DEFAULT_EVIDENCE,
    stop_condition: str = DEFAULT_STOP_CONDITION,
) -> str:
    """Render the common orchestration and result contract."""

    if not objective.strip():
        raise ConfigurationError("objective must not be empty")
    return "\n".join(
        [
            "You are a sub-agent working under an orchestrator.",
            "",
            f"Objective: {objective}",
            f"Ownership: {ownership}",
            f"Boundaries: {boundaries}",
            f"Evidence required: {evidence}",
            f"Stop condition: {stop_condition}",
            "",
            f"Coordination: {COORDINATION_SENTENCE}",
            "",
            "Result contract:",
            "- status: DONE | BLOCKED | NEEDS_HITL",
            "- scope_owned: non-empty JSON array of assigned files or responsibilities",
            "- evidence: commands, outcomes, and artifact references",
            "- findings: JSON array of verified conclusions",
            "- changed_files: JSON array of changed paths, or an empty JSON array",
            "- residual_risk: remaining risk or none",
            "- recommended_next_action: one concrete next action",
        ]
    )


def _decision_prompt_evidence(
    validated: ValidatedDispatchDecision, attempt_id: int = 1
) -> str:
    decision = validated.decision
    return "\n".join(
        [
            "Dispatch governance evidence (do not reinterpret or override):",
            f"- protocol_version: {RESULT_PROTOCOL_VERSION}",
            f"- ticket: {decision['ticket']}",
            f"- attempt_id: {attempt_id}",
            f"- phase: {decision['phase']}",
            f"- policy_version: {validated.policy_version}",
            f"- decision_sha256: {validated.digest}",
            f"- quality_floor: {validated.quality_floor}",
            f"- selected_alias: {decision['selected_alias']}",
            f"- selected_model: {decision['selected_model']}",
            f"- selected_effort: {decision['selected_effort']}",
        ]
    )


def build_invocation(
    route: Route,
    prompt: str,
    project_dir: str | os.PathLike[str],
    *,
    decision: Mapping[str, Any] | None = None,
    model_policy: Mapping[str, Any] | None = None,
    attempt_id: int = 1,
    objective: str = "unspecified",
    ownership: str = DEFAULT_OWNERSHIP,
    runtime_config_path: str | os.PathLike[str] | None = None,
    runtime_config_approved: bool = False,
    work_result_schema_path: str | os.PathLike[str] | None = None,
    scheduling_snapshot: Mapping[str, Any] | None = None,
    claim_store_override: str | os.PathLike[str] | None = None,
    capacity_lease: capacity.CapacityLease | Mapping[str, Any] | None = None,
    capacity_store_path: str | os.PathLike[str] | None = None,
    capacity_policy: Mapping[str, Any] | None = None,
    capacity_request_id: str | None = None,
    capacity_required: bool = False,
    qobs_admission: QobsAdmission | None = None,
    qobs_artifact: object | None = None,
    qobs_expected_context: Mapping[str, object] | None = None,
    qobs_ledger_store: str | os.PathLike[str] | None = None,
    probe_claim_path: str | os.PathLike[str] | None = None,
    approval_grant_path: str | os.PathLike[str] | None = None,
    approval_store_path: str | os.PathLike[str] | None = None,
    approval_session_id: str | None = None,
) -> Invocation:
    """Build exact argv and process-local environment overrides; never a shell command.

    Supplying neither decision nor policy is retained only for legacy v1
    dry-runs.  Executable invocations are rejected by execute_invocation.
    """

    _validate_route_provider_binding(route)
    project_path = Path(project_dir).resolve()
    if not project_path.exists() or not project_path.is_dir():
        raise ConfigurationError("project_dir must exist and be a directory")
    cwd = str(project_path)
    qobs_fields = (qobs_admission, qobs_artifact, qobs_expected_context, qobs_ledger_store)
    if any(value is not None for value in qobs_fields):
        if any(value is None for value in qobs_fields):
            raise ConfigurationError("closed exception QOBS binding is incomplete")
        if project_path != REPOSITORY_ROOT.resolve():
            raise ConfigurationError("closed exception project_dir must be the repository root")
    if isinstance(attempt_id, bool) or not isinstance(attempt_id, int) or attempt_id < 1:
        raise ConfigurationError("attempt_id must be a positive integer")
    if not isinstance(runtime_config_approved, bool):
        raise ConfigurationError("runtime_config_approved must be boolean")
    if approval_session_id is not None:
        _required_string(approval_session_id, "approval session id", safe_name=True)
    objective = _required_string(objective, "objective")
    ownership = _required_string(ownership, "ownership")
    _reject_secret_bearing({"objective": objective, "ownership": ownership}, "dispatch scope")
    validated: ValidatedDispatchDecision | None = None
    resolved_schema_path: Path | None = None
    scheduling_snapshot_digest: str | None = None
    if (decision is None) != (model_policy is None):
        raise ConfigurationError("DispatchDecision and model policy must be supplied together")
    if decision is not None and model_policy is not None:
        validated = validate_dispatch_decision(decision, model_policy, route)
        prompt = prompt + "\n\n" + _decision_prompt_evidence(validated, attempt_id)
        resolved_schema_path = Path(
            os.path.abspath(os.fspath(work_result_schema_path or DEFAULT_WORK_RESULT_SCHEMA))
        )
        if not resolved_schema_path.is_file():
            raise ConfigurationError("WorkResult v2 output schema is unavailable")
        _sha256_regular_file(resolved_schema_path, "WorkResult schema")
        _provider_compatible_work_result_schema(resolved_schema_path)
    if scheduling_snapshot is not None:
        if validated is None:
            raise ConfigurationError("scheduling snapshot requires a DispatchDecision")
        scheduling_snapshot_digest = validate_scheduling_dispatch(
            scheduling_snapshot,
            validated.decision,
            role=route.role,
            ownership=ownership,
        )
        prompt = prompt + "\n\n" + "\n".join(
            [
                "Rule 11 scheduling evidence (do not reinterpret or override):",
                f"- scheduling_snapshot_sha256: {scheduling_snapshot_digest}",
                f"- scheduled_ticket: {validated.decision['ticket']}",
                f"- scheduled_owner: {route.role}",
            ]
        )
    argv = [route.command]
    if qobs_admission is not None:
        if not is_validated_qobs_admission(qobs_admission):
            raise ConfigurationError("closed exception QOBS admission is invalid")
        pinned_executable = _resolve_qobs_executable(route)
        if (
            not isinstance(qobs_expected_context, Mapping)
            or pinned_executable != qobs_expected_context.get("resolved_executable")
            or quota_guard.sha256_text(pinned_executable)
            != qobs_admission.resolved_executable_sha256
        ):
            raise ConfigurationError("closed exception executable is not pinned to QOBS")
        route = replace(route, command=pinned_executable)
        argv = [pinned_executable]
    if route.cli == "codex":
        argv.extend(["exec", "-C", cwd])
        if route.sandbox:
            argv.extend(["-s", route.sandbox])
        if route.model:
            argv.extend(["-m", route.model])
        if route.effort:
            argv.extend(["-c", f'model_reasoning_effort="{route.effort}"'])
        if validated is not None and resolved_schema_path is not None:
            argv.extend(
                ["--ephemeral", "--json", "--output-schema", str(resolved_schema_path)]
            )
        argv.append("-")
    else:
        if route.mode:
            argv.extend(["--mode", route.mode])
        if route.sandbox:
            argv.append("--sandbox")
        if route.model:
            argv.extend(["--model", route.model])
        if route.effort:
            argv.extend(["--effort", route.effort])
        argv.append("--print")
        if validated is not None and resolved_schema_path is not None:
            argv.extend(
                [
                    "--input-format",
                    "stream-json",
                    "--output-format",
                    "stream-json",
                    "--json-schema",
                    str(resolved_schema_path),
                ]
            )
            prompt = json.dumps(
                {
                    "event": "user",
                    "message": {
                        "content": prompt,
                    },
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ) + "\n"
        else:
            argv.extend(["--input-format", "text", "--output-format", "json"])

    env_overrides: dict[str, str] = {}
    if route.home_env and route.home_path:
        env_overrides[route.home_env] = route.home_path
    return Invocation(
        route=route,
        argv=tuple(argv),
        prompt_stdin=prompt,
        cwd=cwd,
        env_overrides=env_overrides,
        decision=dict(validated.decision) if validated is not None else None,
        model_policy=dict(model_policy) if model_policy is not None else None,
        decision_digest=validated.digest if validated is not None else None,
        attempt_id=attempt_id,
        objective=objective,
        ownership=ownership,
        runtime_config_path=(
            os.path.abspath(os.fspath(runtime_config_path))
            if runtime_config_path is not None else None
        ),
        runtime_config_approved=runtime_config_approved,
        work_result_schema_path=(
            str(resolved_schema_path) if resolved_schema_path is not None else None
        ),
        scheduling_snapshot=(
            dict(scheduling_snapshot) if scheduling_snapshot is not None else None
        ),
        scheduling_snapshot_digest=scheduling_snapshot_digest,
        claim_store_override=(
            str(claim_store_override) if claim_store_override is not None else None
        ),
        capacity_lease=capacity_lease,
        capacity_store_path=(
            str(Path(capacity_store_path).resolve()) if capacity_store_path is not None else None
        ),
        capacity_policy=dict(capacity_policy) if capacity_policy is not None else None,
        capacity_request_id=capacity_request_id,
        capacity_required=capacity_required,
        qobs_admission=qobs_admission,
        qobs_artifact=qobs_artifact,
        qobs_expected_context=(dict(qobs_expected_context) if qobs_expected_context is not None else None),
        qobs_ledger_store=(
            str(Path(qobs_ledger_store).resolve()) if qobs_ledger_store is not None else None
        ),
        probe_claim_path=(
            os.path.abspath(os.fspath(probe_claim_path)) if probe_claim_path is not None else None
        ),
        approval_grant_path=(
            os.path.abspath(os.fspath(approval_grant_path)) if approval_grant_path is not None else None
        ),
        approval_store_path=(
            os.path.abspath(os.fspath(approval_store_path)) if approval_store_path is not None else None
        ),
        approval_session_id=approval_session_id,
    )


def _dispatch_key(invocation: Invocation) -> str:
    """Return a stable, non-secret identity for one exact dispatch request."""

    material = json.dumps(
        {
            "argv": invocation.argv,
            "cwd": invocation.cwd,
            "prompt": invocation.prompt_stdin,
            "env": sorted(invocation.env_overrides.items()),
            "policy_version": (
                invocation.decision.get("policy_version") if invocation.decision else None
            ),
            "decision_sha256": invocation.decision_digest,
            "scheduling_snapshot_sha256": invocation.scheduling_snapshot_digest,
            "model": invocation.route.model,
            "effort": invocation.route.effort,
            "attempt_id": invocation.attempt_id,
        },
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _claim_dispatch_identity(invocation: Invocation) -> str:
    """Return an attempt-independent identity for one authorized dispatch."""

    if invocation.qobs_admission is not None:
        # The exception lane is additionally bound to the exact QOBS artifact,
        # nonce, executable, decision, and scheduling snapshot. Ordinary lanes
        # retain their historical identity bytes below.
        return invocation.qobs_admission.dispatch_identity
    material = {
        "decision_sha256": invocation.decision_digest,
        "scheduling_snapshot_sha256": invocation.scheduling_snapshot_digest,
        "ticket": invocation.decision.get("ticket") if invocation.decision else None,
        "route": {
            "role": invocation.route.role,
            "alias": invocation.route.alias,
            "provider": invocation.route.cli,
            "model": invocation.route.model,
            "effort": invocation.route.effort,
        },
        "cwd_sha256": hashlib.sha256(invocation.cwd.encode("utf-8")).hexdigest(),
        "objective_sha256": hashlib.sha256(invocation.objective.encode("utf-8")).hexdigest(),
        "ownership_sha256": hashlib.sha256(invocation.ownership.encode("utf-8")).hexdigest(),
    }
    if invocation.preauthorization_store_binding is not None:
        material["preauthorization_stores"] = _validated_preauthorization_stores(
            invocation.preauthorization_store_binding
        )
    return _canonical_sha256(material)


def _validated_preauthorization_stores(value: Mapping[str, Any]) -> dict[str, str]:
    stores = _mapping(value, "preauthorization stores")
    if set(stores) != set(PREAUTH_STORE_NAMES):
        raise ProbeAuthorizationError("preauthorization store identities are invalid")
    normalized: dict[str, str] = {}
    for name in PREAUTH_STORE_NAMES:
        digest = stores.get(name)
        if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ProbeAuthorizationError("preauthorization store identity is invalid")
        normalized[name] = digest
    return normalized


def _validate_preauthorization_binding_shape(
    value: Mapping[str, Any]
) -> dict[str, Any]:
    """Validate the complete closed nested binding used by every v1 artifact."""

    binding = _mapping(value, "preauthorization binding")
    if set(binding) != PREAUTH_BINDING_FIELDS:
        raise ProbeAuthorizationError("preauthorization binding fields are invalid")
    ticket = binding.get("ticket")
    if not isinstance(ticket, str) or not SAFE_NAME.fullmatch(ticket):
        raise ProbeAuthorizationError("preauthorization ticket is invalid")
    attempt = binding.get("attempt_id")
    if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
        raise ProbeAuthorizationError("preauthorization attempt is invalid")
    if not isinstance(binding.get("policy_version"), str) or not binding[
        "policy_version"
    ]:
        raise ProbeAuthorizationError("preauthorization policy version is invalid")
    for field in PREAUTH_BINDING_SHA256_FIELDS:
        digest = binding.get(field)
        if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ProbeAuthorizationError("preauthorization digest field is invalid")
    stores = _validated_preauthorization_stores(
        _mapping(binding.get("preauthorization_stores"), "preauthorization stores")
    )
    route = _mapping(binding.get("route"), "preauthorization route")
    if set(route) != PREAUTH_ROUTE_FIELDS:
        raise ProbeAuthorizationError("preauthorization route fields are invalid")
    if (
        not isinstance(route.get("role"), str)
        or not SAFE_NAME.fullmatch(route["role"])
        or route.get("alias") not in GOVERNED_ACCOUNT_ALIASES
        or route.get("provider") not in VALID_CLIS
        or not isinstance(route.get("command_sha256"), str)
        or not re.fullmatch(r"[a-f0-9]{64}", route["command_sha256"])
        or route.get("effort") not in VALID_EFFORTS | {None}
        or route.get("mode") is not None
        and not isinstance(route.get("mode"), str)
        or route.get("sandbox") is not None
        and not isinstance(route.get("sandbox"), (str, bool))
        or route.get("model") is not None
        and not isinstance(route.get("model"), str)
    ):
        raise ProbeAuthorizationError("preauthorization route is invalid")
    if binding.get("route_sha256") != _canonical_sha256(route):
        raise ProbeAuthorizationError("preauthorization route digest is invalid")
    normalized = dict(binding)
    normalized["route"] = dict(route)
    normalized["preauthorization_stores"] = stores
    _reject_secret_bearing(normalized, "preauthorization binding")
    return normalized


def _preauthorization_binding(
    invocation: Invocation, session_id: str | None = None
) -> dict[str, Any]:
    """Return the complete content-free binding for one exact provider attempt."""

    validated = _validated_invocation_decision(invocation)
    schedule_digest = _validated_invocation_schedule(invocation, validated)
    session = session_id or invocation.approval_session_id
    if session is None:
        raise ProbeAuthorizationError("current approval session is required")
    _required_string(session, "approval session id", safe_name=True)
    if not invocation.runtime_config_path:
        raise ProbeAuthorizationError("runtime config binding is required")
    if not invocation.work_result_schema_path:
        raise ProbeAuthorizationError("WorkResult schema binding is required")
    if invocation.preauthorization_store_binding is None:
        raise ProbeAuthorizationError("preauthorization store binding is required")
    stores = _validated_preauthorization_stores(
        invocation.preauthorization_store_binding
    )
    route = {
        "role": invocation.route.role,
        "alias": invocation.route.alias,
        "provider": invocation.route.cli,
        "command_sha256": hashlib.sha256(
            invocation.route.command.encode("utf-8")
        ).hexdigest(),
        "model": invocation.route.model,
        "effort": invocation.route.effort,
        "mode": invocation.route.mode,
        "sandbox": invocation.route.sandbox,
    }
    binding = {
        "ticket": validated.decision["ticket"],
        "attempt_id": invocation.attempt_id,
        "session_sha256": hashlib.sha256(session.encode("utf-8")).hexdigest(),
        "policy_version": validated.policy_version,
        "model_policy_sha256": _canonical_sha256(invocation.model_policy),
        "dispatcher_source_sha256": _sha256_regular_file(
            Path(__file__).resolve(), "dispatcher source"
        ),
        "decision_sha256": validated.digest,
        "scheduling_snapshot_sha256": schedule_digest,
        "runtime_config_sha256": _sha256_regular_file(
            invocation.runtime_config_path, "runtime config"
        ),
        "work_result_schema_sha256": _sha256_regular_file(
            invocation.work_result_schema_path, "WorkResult schema"
        ),
        "probe_claim_schema_sha256": _sha256_regular_file(
            DEFAULT_PROBE_CLAIM_SCHEMA, "ProbeClaim schema"
        ),
        "probe_approval_schema_sha256": _sha256_regular_file(
            DEFAULT_PROBE_APPROVAL_SCHEMA, "ProbeApproval schema"
        ),
        "approval_consume_schema_sha256": _sha256_regular_file(
            DEFAULT_APPROVAL_CONSUME_SCHEMA, "ApprovalConsumeReceipt schema"
        ),
        "execution_receipt_schema_sha256": _sha256_regular_file(
            DEFAULT_EXECUTION_RECEIPT_V3_SCHEMA, "ExecutionReceipt v3 schema"
        ),
        "prompt_sha256": hashlib.sha256(
            invocation.prompt_stdin.encode("utf-8")
        ).hexdigest(),
        "objective_sha256": hashlib.sha256(
            invocation.objective.encode("utf-8")
        ).hexdigest(),
        "ownership_sha256": hashlib.sha256(
            invocation.ownership.encode("utf-8")
        ).hexdigest(),
        "route": route,
        "route_sha256": _canonical_sha256(route),
        "preauthorization_stores": stores,
        "dispatch_identity": _claim_dispatch_identity(invocation),
    }
    return _validate_preauthorization_binding_shape(binding)


def _rfc3339_after(started: str, seconds: int) -> str:
    value = _parse_utc_timestamp(started, "created_at")
    return datetime.fromtimestamp(
        value.timestamp() + seconds, timezone.utc
    ).isoformat(timespec="microseconds").replace("+00:00", "Z")


def build_probe_claim(
    invocation: Invocation,
    *,
    session_id: str,
    created_at: str | None = None,
    nonce: str | None = None,
) -> dict[str, Any]:
    """Build, but do not persist or execute, one exact offline ProbeClaim v1."""

    created = created_at or _utc_now()
    _parse_utc_timestamp(created, "ProbeClaim created_at")
    nonce_value = nonce or os.urandom(32).hex()
    if not re.fullmatch(r"[a-f0-9]{64}", nonce_value):
        raise ProbeAuthorizationError("ProbeClaim nonce must be 256-bit lowercase hex")
    claim: dict[str, Any] = {
        "schema_version": PROBE_CLAIM_SCHEMA_VERSION,
        "artifact_type": "ProbeClaim",
        "binding": _preauthorization_binding(invocation, session_id),
        "nonce": nonce_value,
        "created_at": created,
        "expires_at": _rfc3339_after(created, PROBE_CLAIM_TTL_SECONDS),
        "ttl_seconds": PROBE_CLAIM_TTL_SECONDS,
        "max_uses": 1,
        "retention_days": PREAUTH_RETENTION_DAYS,
        "raw_streams_retained": False,
    }
    claim["claim_id"] = _artifact_address(claim, "claim_id")
    return claim


def emit_probe_claim(
    invocation: Invocation,
    destination: str | os.PathLike[str],
    *,
    session_id: str,
) -> dict[str, Any]:
    """Durably emit a ProbeClaim; this function has no provider-spawn path."""

    stores = _open_preauthorization_stores(
        invocation, probe_claim_path=destination
    )
    claim_store, grant_store, consume_store, dispatch_store, store_binding = stores
    try:
        bound = replace(
            invocation,
            probe_claim_path=os.path.abspath(os.fspath(destination)),
            preauthorization_store_binding=store_binding,
        )
        claim = build_probe_claim(bound, session_id=session_id)
        _durable_private_json_create(
            destination, claim, retained_parent=claim_store
        )
        return claim
    finally:
        claim_store.close()
        grant_store.close()
        consume_store.close()
        dispatch_store.close()


def _validate_claim_record_v1(
    claim: Mapping[str, Any], expected_binding: Mapping[str, Any] | None = None,
    *,
    enforce_fresh: bool = True,
    now: datetime | None = None,
) -> dict[str, Any]:
    required = {
        "schema_version", "artifact_type", "claim_id", "binding", "nonce",
        "created_at", "expires_at", "ttl_seconds", "max_uses",
        "retention_days", "raw_streams_retained",
    }
    if set(claim) != required:
        raise ProbeAuthorizationError("ProbeClaim fields are invalid")
    if claim.get("schema_version") != 1 or claim.get("artifact_type") != "ProbeClaim":
        raise ProbeAuthorizationError("ProbeClaim version is invalid")
    if claim.get("ttl_seconds") != PROBE_CLAIM_TTL_SECONDS:
        raise ProbeAuthorizationError("ProbeClaim TTL is invalid")
    if (
        claim.get("max_uses") != 1
        or claim.get("retention_days") != PREAUTH_RETENTION_DAYS
        or claim.get("raw_streams_retained") is not False
    ):
        raise ProbeAuthorizationError("ProbeClaim policy is invalid")
    if not isinstance(claim.get("nonce"), str) or not re.fullmatch(
        r"[a-f0-9]{64}", claim["nonce"]
    ):
        raise ProbeAuthorizationError("ProbeClaim nonce is invalid")
    binding = _validate_preauthorization_binding_shape(
        _mapping(claim.get("binding"), "ProbeClaim binding")
    )
    if expected_binding is not None and dict(binding) != dict(expected_binding):
        raise ProbeAuthorizationError("ProbeClaim binding is stale or mismatched")
    created = _parse_utc_timestamp(claim.get("created_at"), "ProbeClaim created_at")
    expires = _parse_utc_timestamp(claim.get("expires_at"), "ProbeClaim expires_at")
    if expires - created != timedelta(seconds=PROBE_CLAIM_TTL_SECONDS):
        raise ProbeAuthorizationError("ProbeClaim expiry is invalid")
    if enforce_fresh:
        captured_now = now or _utc_datetime()
        if created > captured_now:
            raise ProbeAuthorizationError("ProbeClaim is not yet valid")
        if captured_now >= expires:
            raise ProbeAuthorizationError("ProbeClaim is expired")
    if claim.get("claim_id") != _artifact_address(claim, "claim_id"):
        raise ProbeAuthorizationError("ProbeClaim content address is invalid")
    return dict(claim)


def build_probe_approval(
    claim: Mapping[str, Any],
    *,
    session_id: str,
    created_at: str | None = None,
    nonce: str | None = None,
    claim_artifact_sha256: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build a separate local attestation grant for one exact valid claim."""

    captured_now = now or _utc_datetime()
    normalized_claim = _validate_claim_record_v1(claim, now=captured_now)
    binding = _mapping(normalized_claim["binding"], "ProbeClaim binding")
    if binding.get("session_sha256") != hashlib.sha256(
        session_id.encode("utf-8")
    ).hexdigest():
        raise ProbeAuthorizationError("approval session does not match ProbeClaim")
    _required_string(session_id, "approval session id", safe_name=True)
    created = created_at or _format_utc(captured_now)
    grant_created = _parse_utc_timestamp(created, "ApprovalGrant created_at")
    claim_created = _parse_utc_timestamp(
        normalized_claim["created_at"], "ProbeClaim created_at"
    )
    claim_expires = _parse_utc_timestamp(
        normalized_claim["expires_at"], "ProbeClaim expires_at"
    )
    grant_expires = grant_created + timedelta(seconds=APPROVAL_GRANT_TTL_SECONDS)
    if grant_created > captured_now:
        raise ProbeAuthorizationError("ApprovalGrant is not yet valid")
    if grant_created < claim_created:
        raise ProbeAuthorizationError("ApprovalGrant predates ProbeClaim")
    if grant_expires > claim_expires:
        raise ProbeAuthorizationError("cannot approve an expired ProbeClaim")
    nonce_value = nonce or os.urandom(32).hex()
    if not re.fullmatch(r"[a-f0-9]{64}", nonce_value):
        raise ProbeAuthorizationError("ApprovalGrant nonce is invalid")
    if claim_artifact_sha256 is not None and not re.fullmatch(
        r"[a-f0-9]{64}", claim_artifact_sha256
    ):
        raise ProbeAuthorizationError("ProbeClaim artifact digest is invalid")
    grant: dict[str, Any] = {
        "schema_version": PROBE_APPROVAL_SCHEMA_VERSION,
        "artifact_type": "ApprovalGrant",
        "approval_type": "ProbeApproval",
        "claim_id": normalized_claim["claim_id"],
        "claim_sha256": claim_artifact_sha256 or hashlib.sha256(
            _canonical_json_bytes(normalized_claim)
        ).hexdigest(),
        "binding": dict(binding),
        "nonce": nonce_value,
        "created_at": created,
        "expires_at": _format_utc(grant_expires),
        "ttl_seconds": APPROVAL_GRANT_TTL_SECONDS,
        "max_uses": 1,
        "revoked": False,
        "attestation_scope": PREAUTH_SCOPE,
        "authenticity_claimed": False,
        "retention_days": PREAUTH_RETENTION_DAYS,
        "raw_streams_retained": False,
    }
    grant["grant_id"] = _artifact_address(grant, "grant_id")
    return grant


def emit_probe_approval(
    invocation: Invocation,
    claim_path: str | os.PathLike[str],
    destination: str | os.PathLike[str],
    *,
    session_id: str,
) -> dict[str, Any]:
    """Load a claim and durably emit its separate local ApprovalGrant."""

    stores = _open_preauthorization_stores(
        invocation,
        probe_claim_path=claim_path,
        approval_grant_path=destination,
    )
    claim_store, grant_store, consume_store, dispatch_store, store_binding = stores
    try:
        bound = replace(
            invocation,
            probe_claim_path=os.path.abspath(os.fspath(claim_path)),
            approval_grant_path=os.path.abspath(os.fspath(destination)),
            preauthorization_store_binding=store_binding,
        )
        artifact = _secure_json_artifact(
            claim_path, retained_parent=claim_store
        )
        try:
            captured_now = _utc_datetime()
            expected_binding = _preauthorization_binding(bound, session_id)
            claim = _validate_claim_record_v1(
                artifact.record, expected_binding, now=captured_now
            )
            grant = build_probe_approval(
                claim,
                session_id=session_id,
                claim_artifact_sha256=hashlib.sha256(artifact.raw).hexdigest(),
                now=captured_now,
            )
        finally:
            artifact.close()
        _durable_private_json_create(
            destination, grant, retained_parent=grant_store
        )
        return grant
    finally:
        claim_store.close()
        grant_store.close()
        consume_store.close()
        dispatch_store.close()


def _dispatch_claim_key(invocation: Invocation) -> str:
    if not invocation.decision_digest or not invocation.scheduling_snapshot_digest:
        raise SchedulingError(
            "INVALID_DISPATCH_CLAIM", "claim requires decision and scheduling bindings"
        )
    return _canonical_sha256(
        {
            "decision_sha256": invocation.decision_digest,
            "scheduling_snapshot_sha256": invocation.scheduling_snapshot_digest,
            "dispatch_identity": _claim_dispatch_identity(invocation),
        }
    )


def _directory_open_flags() -> int:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    return flags | getattr(os, "O_NOFOLLOW", 0)


def _file_open_flags(base: int) -> int:
    return (
        base
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )


def _validate_owned_directory_fd(descriptor: int) -> os.stat_result:
    value = os.fstat(descriptor)
    if not stat.S_ISDIR(value.st_mode) or stat.S_IMODE(value.st_mode) != 0o700:
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim directory mode is unsafe")
    if hasattr(os, "getuid") and value.st_uid != os.getuid():
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim directory owner is unsafe")
    return value


def _canonical_realpath(path: Path) -> Path:
    return Path(os.path.realpath(os.path.abspath(path)))


def _durable_claim_destination(invocation: Invocation) -> tuple[Path, int]:
    project = _canonical_realpath(Path(invocation.cwd))
    if not project.is_dir():
        raise SchedulingError("INVALID_CLAIM_STORE", "canonical project is unavailable")
    namespace = hashlib.sha256(os.fsencode(project)).hexdigest()
    if invocation.claim_store_override is not None:
        raw = Path(invocation.claim_store_override)
        if not raw.is_absolute():
            raise SchedulingError("INVALID_CLAIM_STORE", "claim store override must be absolute")
        if any(part in {".", ".."} for part in raw.parts):
            raise SchedulingError("INVALID_CLAIM_STORE", "claim store path alias is unsafe")
        destination = Path(os.path.abspath(raw))
        try:
            relative = destination.relative_to(project)
        except ValueError as exc:
            if invocation.qobs_admission is not None:
                # The frozen test-only/one-shot ledger may use an explicitly
                # supplied isolated local claim store; its QOBS project target
                # remains the repository root and the override is not used as
                # an execution namespace.
                return destination, len(destination.parts)
            raise SchedulingError(
                "INVALID_CLAIM_STORE", "claim store override must remain inside project"
            ) from exc
        if not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
            raise SchedulingError("INVALID_CLAIM_STORE", "claim store override is unsafe")
        return destination, len(project.parts)
    home = _canonical_realpath(Path.home())
    if sys.platform == "darwin":
        base = home / "Library" / "Application Support" / "HoroConsultant" / "dispatch-ledger"
    else:
        base = home / ".local" / "state" / "horoconsultant" / "dispatch-ledger"
    return base / namespace, len(base.parts) - 2


def _open_claim_store_path(
    destination: Path, protected_from: int, namespace: str
) -> ClaimStore:
    parts = destination.parts
    if not destination.is_absolute() or not parts:
        raise SchedulingError("INVALID_CLAIM_STORE", "claim store location is invalid")
    try:
        parent_fd = os.open(parts[0], _directory_open_flags())
    except OSError as exc:
        raise SchedulingError("INVALID_CLAIM_STORE", "claim store root is unavailable") from exc
    try:
        for index, component in enumerate(parts[1:], start=1):
            created = False
            try:
                child_fd = os.open(component, _directory_open_flags(), dir_fd=parent_fd)
            except FileNotFoundError:
                os.mkdir(component, 0o700, dir_fd=parent_fd)
                os.fsync(parent_fd)
                created = True
                child_fd = os.open(component, _directory_open_flags(), dir_fd=parent_fd)
            if created or index >= protected_from:
                _validate_owned_directory_fd(child_fd)
            os.close(parent_fd)
            parent_fd = child_fd
        value = _validate_owned_directory_fd(parent_fd)
        os.fsync(parent_fd)
        return ClaimStore(
            destination,
            parent_fd,
            (value.st_dev, value.st_ino),
            _directory_identity_sha256(destination, value),
            namespace,
        )
    except (OSError, SchedulingError) as exc:
        os.close(parent_fd)
        if isinstance(exc, SchedulingError):
            raise
        raise SchedulingError("INVALID_CLAIM_STORE", "claim store traversal failed") from exc


def _secure_claim_directory(invocation: Invocation) -> ClaimStore:
    """Create/open the ledger once and retain its validated directory descriptor."""

    if fcntl is None or os.name != "posix":
        raise SchedulingError(
            "UNSUPPORTED_CLAIM_PLATFORM", "durable dispatch claims require POSIX locking"
        )
    destination, protected_from = _durable_claim_destination(invocation)
    namespace = hashlib.sha256(
        os.fsencode(_canonical_realpath(Path(invocation.cwd)))
    ).hexdigest()
    return _open_claim_store_path(destination, protected_from, namespace)


def _coerce_claim_store(value: ClaimStore | Path, invocation: Invocation) -> ClaimStore:
    """Upgrade legacy test-path injection without reopening a validated handle."""

    if isinstance(value, ClaimStore):
        return value
    raw = Path(value)
    if any(part in {".", ".."} for part in raw.parts):
        raise SchedulingError("INVALID_CLAIM_STORE", "injected claim store alias is unsafe")
    destination = Path(os.path.abspath(raw))
    project = _canonical_realpath(Path(invocation.cwd))
    try:
        destination.relative_to(project)
    except ValueError as exc:
        raise SchedulingError("INVALID_CLAIM_STORE", "injected claim store is unsafe") from exc
    namespace = hashlib.sha256(os.fsencode(project)).hexdigest()
    return _open_claim_store_path(destination, len(project.parts), namespace)


def _open_preauthorization_stores(
    invocation: Invocation,
    *,
    probe_claim_path: str | os.PathLike[str] | None = None,
    approval_grant_path: str | os.PathLike[str] | None = None,
) -> tuple[
    RetainedDirectory,
    RetainedDirectory,
    RetainedDirectory,
    ClaimStore,
    dict[str, str],
]:
    """Open all four local stores once and return their closed identity set."""

    claim_path = probe_claim_path or invocation.probe_claim_path
    grant_path = approval_grant_path or invocation.approval_grant_path
    if not claim_path or not grant_path or not invocation.approval_store_path:
        raise ProbeAuthorizationError(
            "claim, grant, consume, and dispatch-ledger stores are required"
        )
    claim_store: RetainedDirectory | None = None
    grant_store: RetainedDirectory | None = None
    consume_store: RetainedDirectory | None = None
    dispatch_store: ClaimStore | None = None
    try:
        claim_store = _open_retained_private_directory(
            _normalized_private_path(claim_path).parent, "ProbeClaim store"
        )
        grant_store = _open_retained_private_directory(
            _normalized_private_path(grant_path).parent, "ApprovalGrant store"
        )
        consume_store = _open_retained_private_directory(
            invocation.approval_store_path, "approval consume store"
        )
        dispatch_store = _coerce_claim_store(
            _secure_claim_directory(invocation), invocation
        )
        stores = {
            "probe_claim_store": claim_store.identity_sha256,
            "approval_grant_store": grant_store.identity_sha256,
            "approval_consume_store": consume_store.identity_sha256,
            "dispatch_ledger_store": dispatch_store.identity_sha256,
        }
        return claim_store, grant_store, consume_store, dispatch_store, stores
    except BaseException:
        if claim_store is not None:
            claim_store.close()
        if grant_store is not None:
            grant_store.close()
        if consume_store is not None:
            consume_store.close()
        if dispatch_store is not None:
            dispatch_store.close()
        raise


def _bind_invocation_to_current_stores(invocation: Invocation) -> Invocation:
    """Reopen all local stores safely and bind their current identities."""

    stores = _open_preauthorization_stores(invocation)
    claim_store, grant_store, consume_store, dispatch_store, store_binding = stores
    try:
        return replace(
            invocation, preauthorization_store_binding=store_binding
        )
    finally:
        claim_store.close()
        grant_store.close()
        consume_store.close()
        dispatch_store.close()


def _validate_regular_fd(
    descriptor: int, *, allow_empty: bool = False
) -> os.stat_result:
    value = os.fstat(descriptor)
    if (
        not stat.S_ISREG(value.st_mode)
        or stat.S_IMODE(value.st_mode) != 0o600
        or value.st_nlink != 1
        or (hasattr(os, "getuid") and value.st_uid != os.getuid())
        or value.st_size > MAX_DISPATCH_CLAIM_BYTES
        or (not allow_empty and value.st_size < 1)
    ):
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim file metadata is unsafe")
    return value


def _bounded_read_fd(descriptor: int, *, allow_empty: bool = False) -> bytes:
    os.lseek(descriptor, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    remaining = MAX_DISPATCH_CLAIM_BYTES + 1
    while remaining:
        chunk = os.read(descriptor, min(4096, remaining))
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    raw = b"".join(chunks)
    if (not raw and not allow_empty) or len(raw) > MAX_DISPATCH_CLAIM_BYTES:
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim file size is invalid")
    return raw


def _write_all(descriptor: int, payload: bytes) -> None:
    """Write a complete claim payload, retrying EINTR and rejecting zero writes."""

    view = memoryview(payload)
    offset = 0
    while offset < len(view):
        try:
            written = os.write(descriptor, view[offset:])
        except InterruptedError:
            continue
        if written <= 0:
            raise SchedulingError("CLAIM_WRITE_FAILED", "claim write made no progress")
        offset += written


def _validate_claim_record(value: Any) -> dict[str, Any]:
    required = {
        "version", "claim_key", "decision_sha256", "scheduling_snapshot_sha256",
        "dispatch_identity", "ticket_sha256", "route_sha256",
        "ownership_tokens_sha256", "ownership_exact_tokens",
        "ownership_ancestor_tokens", "ownership_key_id", "state", "abandon_reason",
        "legacy_claim_sha256",
        "pid", "created_at", "updated_at", "started_at", "ended_at",
        "process_start_binding",
        "transport_status", "exit_code", "output_bytes", "output_sha256",
        "work_result_sha256",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim record fields are invalid")
    claim = dict(value)
    if claim.get("version") != DISPATCH_CLAIM_VERSION:
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim record version is invalid")
    for field in (
        "claim_key", "decision_sha256", "scheduling_snapshot_sha256",
        "dispatch_identity", "ticket_sha256", "route_sha256",
        "ownership_tokens_sha256", "ownership_key_id", "process_start_binding",
    ):
        if not isinstance(claim.get(field), str) or not re.fullmatch(r"[a-f0-9]{64}", claim[field]):
            raise SchedulingError("INVALID_DISPATCH_CLAIM", f"claim {field} is invalid")
    if claim.get("state") not in {"active", "completed", "rejected", "unknown", "abandoned"}:
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim lifecycle state is invalid")
    for field in ("ownership_exact_tokens", "ownership_ancestor_tokens"):
        tokens = claim.get(field)
        if not isinstance(tokens, list) or (field == "ownership_exact_tokens" and not tokens):
            raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim ownership tokens are invalid")
        if len(tokens) != len(set(tokens)) or not all(
            isinstance(item, str) and re.fullmatch(r"[a-f0-9]{64}", item)
            for item in tokens
        ):
            raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim ownership tokens are invalid")
    if claim["ownership_tokens_sha256"] != _ownership_tokens_digest(
        claim["ownership_exact_tokens"], claim["ownership_ancestor_tokens"]
    ):
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim ownership digest is invalid")
    if claim.get("abandon_reason") not in {None, "process_dead", "pid_reused", "stale_unlocked"}:
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim abandon reason is invalid")
    legacy_digest = claim.get("legacy_claim_sha256")
    if legacy_digest is not None and (
        not isinstance(legacy_digest, str) or not re.fullmatch(r"[a-f0-9]{64}", legacy_digest)
    ):
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "legacy claim digest is invalid")
    if isinstance(claim.get("pid"), bool) or not isinstance(claim.get("pid"), int):
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim pid is invalid")
    for field in ("created_at", "updated_at", "started_at"):
        try:
            _parse_utc_timestamp(claim.get(field), f"dispatch claim {field}")
        except ConfigurationError as exc:
            raise SchedulingError(
                "INVALID_DISPATCH_CLAIM", "claim timestamp is invalid"
            ) from exc
    terminal = ("exit_code", "output_bytes", "output_sha256", "work_result_sha256")
    if claim["state"] == "active":
        if claim.get("abandon_reason") is not None:
            raise SchedulingError("INVALID_DISPATCH_CLAIM", "active abandon reason is invalid")
        if claim.get("transport_status") != "starting" or claim.get("ended_at") is not None:
            raise SchedulingError("INVALID_DISPATCH_CLAIM", "active claim state is inconsistent")
        if any(claim.get(field) is not None for field in terminal):
            raise SchedulingError("INVALID_DISPATCH_CLAIM", "active claim proof is inconsistent")
    else:
        if claim["state"] == "abandoned" and claim.get("abandon_reason") is None:
            raise SchedulingError("INVALID_DISPATCH_CLAIM", "abandoned claim reason is missing")
        try:
            _parse_utc_timestamp(claim.get("ended_at"), "dispatch claim ended_at")
        except ConfigurationError as exc:
            raise SchedulingError(
                "INVALID_DISPATCH_CLAIM", "terminal claim timestamp is invalid"
            ) from exc
        expected_transport = {
            "completed": "completed",
            "rejected": "provider_result_rejected",
            "unknown": "transport_unknown",
            "abandoned": "abandoned",
        }[claim["state"]]
        if claim.get("transport_status") != expected_transport:
            raise SchedulingError("INVALID_DISPATCH_CLAIM", "terminal claim state is inconsistent")
        if claim["state"] in {"completed", "rejected"}:
            if isinstance(claim.get("exit_code"), bool) or not isinstance(claim.get("exit_code"), int):
                raise SchedulingError("INVALID_DISPATCH_CLAIM", "terminal exit code is invalid")
            if isinstance(claim.get("output_bytes"), bool) or not isinstance(claim.get("output_bytes"), int):
                raise SchedulingError("INVALID_DISPATCH_CLAIM", "terminal output size is invalid")
            if not isinstance(claim.get("output_sha256"), str) or not re.fullmatch(r"[a-f0-9]{64}", claim["output_sha256"]):
                raise SchedulingError("INVALID_DISPATCH_CLAIM", "terminal output digest is invalid")
        if claim["state"] == "completed" and (
            not isinstance(claim.get("work_result_sha256"), str)
            or not re.fullmatch(r"[a-f0-9]{64}", claim["work_result_sha256"])
        ):
            raise SchedulingError("INVALID_DISPATCH_CLAIM", "completed result digest is invalid")
    return claim


def _read_claim_fd(descriptor: int) -> dict[str, Any]:
    _validate_regular_fd(descriptor)
    try:
        return _validate_claim_record(json.loads(_bounded_read_fd(descriptor).decode("ascii")))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim content is invalid") from exc


def _read_dispatch_claim(
    source: ClaimStore | DispatchClaim | Invocation, claim_key: str | None = None
) -> Mapping[str, Any]:
    """Read through a retained, validated store descriptor only."""

    close_store = False
    if isinstance(source, DispatchClaim):
        store = source.store
        name = source.path.name
    elif isinstance(source, ClaimStore):
        store = source
        if claim_key is None or not re.fullmatch(r"[a-f0-9]{64}", claim_key):
            raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim key is invalid")
        name = f"{claim_key}.json"
    elif isinstance(source, Invocation):
        store = _coerce_claim_store(_secure_claim_directory(source), source)
        close_store = True
        key = claim_key or _dispatch_claim_key(source)
        if not re.fullmatch(r"[a-f0-9]{64}", key):
            store.close()
            raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim key is invalid")
        name = f"{key}.json"
    else:
        raise SchedulingError(
            "INVALID_DISPATCH_CLAIM", "claim reads require a validated store handle"
        )
    try:
        descriptor = os.open(
            name, _file_open_flags(os.O_RDONLY), dir_fd=store.dir_fd
        )
        try:
            return _read_claim_fd(descriptor)
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim read failed") from exc
    finally:
        if close_store:
            store.close()


def _optional_local_claim(invocation: Invocation, claim_key: str) -> Mapping[str, Any] | None:
    store = _coerce_claim_store(_secure_claim_directory(invocation), invocation)
    try:
        try:
            descriptor = os.open(
                f"{claim_key}.json", _file_open_flags(os.O_RDONLY), dir_fd=store.dir_fd
            )
        except FileNotFoundError:
            return None
        try:
            record = _read_claim_fd(descriptor)
            ownership_key = _load_ownership_key(store)
            if record.get("ownership_key_id") != hashlib.sha256(ownership_key).hexdigest():
                raise SchedulingError(
                    "INVALID_DISPATCH_CLAIM", "local claim key identity is invalid"
                )
            return record
        finally:
            os.close(descriptor)
    finally:
        store.close()


def _claim_age_seconds(claim: Mapping[str, Any], field: str = "created_at") -> float:
    try:
        created = _parse_utc_timestamp(claim.get(field), f"dispatch claim {field}")
    except ConfigurationError as exc:
        raise SchedulingError(
            "INVALID_DISPATCH_CLAIM", f"dispatch claim {field} is invalid"
        ) from exc
    age = (datetime.now(timezone.utc) - created).total_seconds()
    if age < -60:
        raise SchedulingError(
            "INVALID_DISPATCH_CLAIM", "dispatch claim timestamp is in the future"
        )
    return max(0.0, age)


def _pid_is_alive(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "dispatch claim pid is invalid")
    try:
        os.kill(value, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _existing_claim_error(claim: Mapping[str, Any], expected_key: str) -> SchedulingError:
    if claim.get("claim_key") != expected_key:
        return SchedulingError(
            "INVALID_DISPATCH_CLAIM", "dispatch claim identity is inconsistent"
        )
    age = _claim_age_seconds(claim)
    state = claim.get("state")
    if state == "completed":
        return SchedulingError(
            "DUPLICATE_DISPATCH_CLAIM", "authorized dispatch was already executed"
        )
    if state in {"rejected", "unknown", "abandoned"}:
        return SchedulingError("STALE_DISPATCH_CLAIM", "claim requires fresh authorization")
    alive = _pid_is_alive(claim.get("pid"))
    if age > DISPATCH_CLAIM_STALE_SECONDS or not alive or state == "unknown":
        return SchedulingError(
            "STALE_DISPATCH_CLAIM",
            "stale or ambiguous claim requires a fresh decision or scheduling snapshot",
        )
    return SchedulingError(
        "CONCURRENT_DISPATCH_CLAIM", "authorized dispatch is already active"
    )


def _open_lock_fd(store: ClaimStore, name: str, *, blocking: bool) -> tuple[int, tuple[int, int]]:
    if fcntl is None:
        raise SchedulingError("UNSUPPORTED_CLAIM_PLATFORM", "POSIX claim locking is unavailable")
    descriptor: int | None = None
    try:
        descriptor = os.open(
            name, _file_open_flags(os.O_RDWR | os.O_CREAT), 0o600,
            dir_fd=store.dir_fd,
        )
        value = _validate_regular_fd(descriptor, allow_empty=True)
        operation = fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB)
        fcntl.flock(descriptor, operation)
        os.fsync(store.dir_fd)
        return descriptor, (value.st_dev, value.st_ino)
    except BlockingIOError as exc:
        if descriptor is not None:
            os.close(descriptor)
        raise SchedulingError(
            "CONCURRENT_DISPATCH_CLAIM", "authorized dispatch is already active"
        ) from exc
    except (OSError, SchedulingError) as exc:
        if descriptor is not None:
            os.close(descriptor)
        if isinstance(exc, SchedulingError):
            raise
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim lock failed") from exc


def _acquire_store_lock(
    store: ClaimStore, claim_name: str, claim_key: str
) -> tuple[int, tuple[int, int]]:
    """Acquire only this claim's execution lock; distinct claims may run."""

    registry_key = f"{store.namespace}:{claim_key}"
    with _STORE_LOCKS_GUARD:
        if registry_key in _STORE_LOCKS:
            raise SchedulingError(
                "CONCURRENT_DISPATCH_CLAIM", "authorized dispatch is already active"
            )
        descriptor, identity = _open_lock_fd(
            store, f"{claim_key}.lock", blocking=False
        )
        _STORE_LOCKS[registry_key] = descriptor
        return descriptor, identity


def _release_store_lock(store: ClaimStore, claim_key: str, descriptor: int) -> None:
    registry_key = f"{store.namespace}:{claim_key}"
    with _STORE_LOCKS_GUARD:
        registered = _STORE_LOCKS.get(registry_key)
        if registered != descriptor:
            raise SchedulingError(
                "INVALID_DISPATCH_CLAIM", "claim store lock registry is inconsistent"
            )
        _STORE_LOCKS.pop(registry_key, None)
        try:
            fcntl.flock(registered, fcntl.LOCK_UN)
        finally:
            os.close(registered)


def _load_ownership_key(store: ClaimStore) -> bytes:
    name = ".ownership.key"
    try:
        descriptor = os.open(name, _file_open_flags(os.O_RDONLY), dir_fd=store.dir_fd)
    except FileNotFoundError:
        claim_names = [
            item for item in os.listdir(store.dir_fd)
            if re.fullmatch(r"[a-f0-9]{64}\.json", item)
        ]
        for claim_name in claim_names:
            claim_fd = os.open(
                claim_name, _file_open_flags(os.O_RDONLY), dir_fd=store.dir_fd
            )
            try:
                try:
                    legacy = json.loads(_bounded_read_fd(claim_fd).decode("ascii"))
                except (UnicodeError, json.JSONDecodeError) as exc:
                    raise SchedulingError(
                        "INVALID_DISPATCH_CLAIM", "ownership key bootstrap is unsafe"
                    ) from exc
                if not isinstance(legacy, Mapping) or legacy.get("version") != 1:
                    raise SchedulingError(
                        "INVALID_DISPATCH_CLAIM", "ownership key is missing from a v2 ledger"
                    )
            finally:
                os.close(claim_fd)
        descriptor = -1
        created_identity: tuple[int, int] | None = None
        try:
            descriptor = os.open(
                name, _file_open_flags(os.O_RDWR | os.O_CREAT | os.O_EXCL), 0o600,
                dir_fd=store.dir_fd,
            )
            value = os.fstat(descriptor)
            created_identity = (value.st_dev, value.st_ino)
            secret = os.urandom(32)
            _write_all(descriptor, secret)
            os.fsync(descriptor)
            os.fsync(store.dir_fd)
        except BaseException:
            if descriptor >= 0:
                os.close(descriptor)
            if created_identity is not None:
                try:
                    entry = os.stat(name, dir_fd=store.dir_fd, follow_symlinks=False)
                    if (entry.st_dev, entry.st_ino) == created_identity:
                        os.unlink(name, dir_fd=store.dir_fd)
                        os.fsync(store.dir_fd)
                except OSError:
                    pass
            raise
    try:
        value = _validate_regular_fd(descriptor)
        os.lseek(descriptor, 0, os.SEEK_SET)
        secret = os.read(descriptor, 33)
        if value.st_size != 32 or len(secret) != 32:
            raise SchedulingError("INVALID_DISPATCH_CLAIM", "ownership key is invalid")
        return secret
    finally:
        os.close(descriptor)


def _ownership_token(resource: str, secret: bytes) -> str:
    return hmac.new(
        secret, b"horo-ownership-resource-v2\0" + resource.encode("ascii"), hashlib.sha256
    ).hexdigest()


def _ownership_token_set(
    ownership: str, secret: bytes
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    resource = canonicalize_ownership_resource(ownership, "dispatch ownership")
    exact = (_ownership_token(resource, secret),)
    parts = resource.replace("\\", "/").rstrip("/").split("/")
    ancestors: list[str] = []
    for index in range(1, len(parts)):
        ancestor = "/".join(parts[:index])
        if ancestor:
            ancestors.append(_ownership_token(ancestor, secret))
    return exact, tuple(sorted(set(ancestors)))


def _ownership_tokens_for_resources(
    resources: Sequence[str], secret: bytes
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    exact: set[str] = set()
    ancestors: set[str] = set()
    for resource in resources:
        item_exact, item_ancestors = _ownership_token_set(resource, secret)
        exact.update(item_exact)
        ancestors.update(item_ancestors)
    return tuple(sorted(exact)), tuple(sorted(ancestors))


def _ownership_tokens_digest(exact: Sequence[str], ancestors: Sequence[str]) -> str:
    return _canonical_sha256(
        {"exact": list(exact), "ancestors": list(ancestors)}
    )


def _ownership_token_conflict(
    exact: Sequence[str], ancestors: Sequence[str], record: Mapping[str, Any]
) -> bool:
    other_exact = set(record["ownership_exact_tokens"])
    other_ancestors = set(record["ownership_ancestor_tokens"])
    return bool(
        set(exact) & other_exact
        or set(exact) & other_ancestors
        or set(ancestors) & other_exact
    )


def _process_start_binding(pid: int) -> str | None:
    if sys.platform.startswith("linux"):
        try:
            fields = Path(f"/proc/{pid}/stat").read_text(encoding="ascii").split()
            return hashlib.sha256(
                f"linux-proc-start-v1:{fields[21]}".encode("ascii")
            ).hexdigest()
        except (OSError, IndexError, UnicodeError):
            return None
    if pid == os.getpid():
        return _PROCESS_START_NONCE
    return None


def _abandon_active_record(
    store: ClaimStore, descriptor: int, record: Mapping[str, Any], reason: str
) -> None:
    updated = dict(record)
    timestamp = _utc_now()
    updated.update(
        {
            "state": "abandoned",
            "abandon_reason": reason,
            "updated_at": timestamp,
            "ended_at": timestamp,
            "transport_status": "abandoned",
            "exit_code": None,
            "output_bytes": None,
            "output_sha256": None,
            "work_result_sha256": None,
        }
    )
    payload = json.dumps(updated, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("ascii")
    if len(payload) > MAX_DISPATCH_CLAIM_BYTES:
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "abandoned claim is too large")
    os.lseek(descriptor, 0, os.SEEK_SET)
    os.ftruncate(descriptor, 0)
    _write_all(descriptor, payload)
    os.fsync(descriptor)
    os.fsync(store.dir_fd)
    if _read_claim_fd(descriptor)["state"] != "abandoned":
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "abandoned proof verification failed")


def _store_entry_identity(store: ClaimStore, name: str) -> tuple[int, int]:
    """Return a no-follow identity for one entry in the retained claim store."""

    try:
        value = os.stat(name, dir_fd=store.dir_fd, follow_symlinks=False)
    except OSError as exc:
        raise SchedulingError(
            "INVALID_DISPATCH_CLAIM", "migration entry identity is unavailable"
        ) from exc
    return value.st_dev, value.st_ino


def _unlink_open_migration_temp(
    store: ClaimStore,
    name: str,
    descriptor: int,
    identity: tuple[int, int],
) -> None:
    """Unlink only the migration inode held open by ``descriptor``."""

    if _store_entry_identity(store, name) != identity:
        raise SchedulingError(
            "INVALID_DISPATCH_CLAIM", "migration temporary entry changed"
        )
    try:
        os.unlink(name, dir_fd=store.dir_fd)
        current = os.fstat(descriptor)
    except OSError as exc:
        raise SchedulingError(
            "INVALID_DISPATCH_CLAIM", "migration temporary cleanup failed"
        ) from exc
    if (current.st_dev, current.st_ino) != identity or current.st_nlink != 0:
        raise SchedulingError(
            "INVALID_DISPATCH_CLAIM", "migration temporary cleanup raced"
        )
    os.fsync(store.dir_fd)


def _migration_candidate_matches(
    candidate: Mapping[str, Any], expected: Mapping[str, Any]
) -> bool:
    """Compare a recovered v2 candidate while allowing migration timestamps."""

    dynamic = {"updated_at"}
    if expected.get("state") == "abandoned":
        dynamic.add("ended_at")
    return all(
        field in dynamic or candidate.get(field) == value
        for field, value in expected.items()
    )


def _open_recovered_migration_temp(
    store: ClaimStore,
    name: str,
    expected: Mapping[str, Any],
) -> tuple[int, dict[str, Any]] | None:
    """Open a complete candidate or remove an inode-safe incomplete write."""

    try:
        descriptor = os.open(name, _file_open_flags(os.O_RDWR), dir_fd=store.dir_fd)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise SchedulingError(
            "INVALID_DISPATCH_CLAIM", "migration temporary entry is unsafe"
        ) from exc
    try:
        value = _validate_regular_fd(descriptor, allow_empty=True)
        identity = (value.st_dev, value.st_ino)
        raw = _bounded_read_fd(descriptor, allow_empty=True)
        try:
            decoded = json.loads(raw.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            _unlink_open_migration_temp(store, name, descriptor, identity)
            os.close(descriptor)
            return None
        candidate = _validate_claim_record(decoded)
        if (
            candidate.get("claim_key") != expected.get("claim_key")
            or candidate.get("legacy_claim_sha256")
            != expected.get("legacy_claim_sha256")
            or candidate.get("ownership_key_id") != expected.get("ownership_key_id")
            or not _migration_candidate_matches(candidate, expected)
        ):
            raise SchedulingError(
                "INVALID_DISPATCH_CLAIM", "migration temporary binding is invalid"
            )
        if _store_entry_identity(store, name) != identity:
            raise SchedulingError(
                "INVALID_DISPATCH_CLAIM", "migration temporary entry changed"
            )
        return descriptor, candidate
    except BaseException:
        os.close(descriptor)
        raise


def _migrate_legacy_claim(
    store: ClaimStore, descriptor: int, legacy: Mapping[str, Any], secret: bytes
) -> dict[str, Any]:
    """Sanitize an R3 record under metadata lock, or fail closed."""

    if legacy.get("version") != 1 or legacy.get("state") not in {
        "active", "completed", "rejected", "unknown"
    }:
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "legacy claim is unsupported")
    key = legacy.get("claim_key")
    if not isinstance(key, str) or not re.fullmatch(r"[a-f0-9]{64}", key):
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "legacy claim key is invalid")
    resources = legacy.get("ownership_resources")
    if not isinstance(resources, list) or not resources or not all(
        isinstance(item, str) for item in resources
    ):
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "legacy ownership is invalid")
    exact, ancestors = _ownership_tokens_for_resources(resources, secret)
    state = str(legacy["state"])
    recovery_fd: int | None = None
    if state == "active":
        recovery_fd, _ = _open_lock_fd(store, f"{key}.lock", blocking=False)
        state = "abandoned"
    now = _utc_now()
    ticket = str(legacy.get("ticket", "legacy"))
    migrated = {
        "version": DISPATCH_CLAIM_VERSION,
        "claim_key": key,
        "decision_sha256": legacy.get("decision_sha256"),
        "scheduling_snapshot_sha256": legacy.get("scheduling_snapshot_sha256"),
        "dispatch_identity": legacy.get("dispatch_identity"),
        "ticket_sha256": hashlib.sha256(ticket.encode("utf-8")).hexdigest(),
        "route_sha256": legacy.get("route_sha256"),
        "ownership_tokens_sha256": _ownership_tokens_digest(exact, ancestors),
        "ownership_key_id": hashlib.sha256(secret).hexdigest(),
        "ownership_exact_tokens": list(exact),
        "ownership_ancestor_tokens": list(ancestors),
        "state": state,
        "abandon_reason": "stale_unlocked" if state == "abandoned" else None,
        "legacy_claim_sha256": _canonical_sha256(dict(legacy)),
        "pid": legacy.get("pid"),
        "process_start_binding": hashlib.sha256(
            f"legacy-process:{legacy.get('pid')}".encode("ascii")
        ).hexdigest(),
        "created_at": legacy.get("created_at"),
        "updated_at": now,
        "started_at": legacy.get("started_at"),
        "ended_at": now if state == "abandoned" else legacy.get("ended_at"),
        "transport_status": "abandoned" if state == "abandoned" else legacy.get("transport_status"),
        "exit_code": None if state == "abandoned" else legacy.get("exit_code"),
        "output_bytes": None if state == "abandoned" else legacy.get("output_bytes"),
        "output_sha256": None if state == "abandoned" else legacy.get("output_sha256"),
        "work_result_sha256": None if state == "abandoned" else legacy.get("work_result_sha256"),
    }
    try:
        validated = _validate_claim_record(migrated)
        payload = json.dumps(validated, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("ascii")
        temporary_name = f".{key}.migration-v2.tmp"
        destination_name = f"{key}.json"
        source_value = _validate_regular_fd(descriptor)
        source_identity = (source_value.st_dev, source_value.st_ino)
        if _store_entry_identity(store, destination_name) != source_identity:
            raise SchedulingError(
                "INVALID_DISPATCH_CLAIM", "legacy migration source changed"
            )
        recovered = _open_recovered_migration_temp(
            store, temporary_name, validated
        )
        if recovered is None:
            try:
                temporary_fd = os.open(
                    temporary_name,
                    _file_open_flags(os.O_RDWR | os.O_CREAT | os.O_EXCL),
                    0o600,
                    dir_fd=store.dir_fd,
                )
            except OSError as exc:
                raise SchedulingError(
                    "INVALID_DISPATCH_CLAIM", "migration temporary creation failed"
                ) from exc
            candidate = validated
        else:
            temporary_fd, candidate = recovered
        try:
            if recovered is None:
                _write_all(temporary_fd, payload)
                os.fsync(temporary_fd)
            temporary_value = _validate_regular_fd(temporary_fd)
            temporary_identity = (temporary_value.st_dev, temporary_value.st_ino)
            os.lseek(temporary_fd, 0, os.SEEK_SET)
            try:
                written = _validate_claim_record(
                    json.loads(_bounded_read_fd(temporary_fd).decode("ascii"))
                )
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise SchedulingError(
                    "INVALID_DISPATCH_CLAIM", "migration temporary verification failed"
                ) from exc
            if written != candidate or not _migration_candidate_matches(written, validated):
                raise SchedulingError(
                    "INVALID_DISPATCH_CLAIM", "migration temporary verification failed"
                )
            current_temporary = _validate_regular_fd(temporary_fd)
            if (
                (current_temporary.st_dev, current_temporary.st_ino)
                != temporary_identity
                or _store_entry_identity(store, temporary_name)
                != temporary_identity
            ):
                raise SchedulingError(
                    "INVALID_DISPATCH_CLAIM", "migration temporary entry changed"
                )
            current_source = _validate_regular_fd(descriptor)
            if (
                (current_source.st_dev, current_source.st_ino) != source_identity
                or _store_entry_identity(store, destination_name) != source_identity
            ):
                raise SchedulingError(
                    "INVALID_DISPATCH_CLAIM", "legacy migration source changed"
                )
            os.rename(
                temporary_name,
                destination_name,
                src_dir_fd=store.dir_fd,
                dst_dir_fd=store.dir_fd,
            )
            os.fsync(store.dir_fd)
            destination_fd = os.open(
                destination_name, _file_open_flags(os.O_RDONLY), dir_fd=store.dir_fd
            )
            try:
                destination_value = _validate_regular_fd(destination_fd)
                if (
                    (destination_value.st_dev, destination_value.st_ino)
                    != temporary_identity
                    or _read_claim_fd(destination_fd) != candidate
                ):
                    raise SchedulingError(
                        "INVALID_DISPATCH_CLAIM", "migrated claim verification failed"
                    )
            finally:
                os.close(destination_fd)
        except OSError as exc:
            raise SchedulingError(
                "INVALID_DISPATCH_CLAIM", "migration commit failed"
            ) from exc
        finally:
            os.close(temporary_fd)
        return candidate
    finally:
        if recovery_fd is not None:
            if fcntl is not None:
                fcntl.flock(recovery_fd, fcntl.LOCK_UN)
            os.close(recovery_fd)


def _check_active_ownership_conflicts(
    store: ClaimStore, exact: Sequence[str], ancestors: Sequence[str], secret: bytes
) -> None:
    try:
        names = os.listdir(store.dir_fd)
    except OSError as exc:
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim ledger scan failed") from exc
    for name in names:
        if not re.fullmatch(r"[a-f0-9]{64}\.json", name):
            continue
        descriptor = os.open(name, _file_open_flags(os.O_RDWR), dir_fd=store.dir_fd)
        try:
            try:
                record = _read_claim_fd(descriptor)
            except SchedulingError:
                try:
                    legacy = json.loads(_bounded_read_fd(descriptor).decode("ascii"))
                except (UnicodeError, json.JSONDecodeError) as exc:
                    raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim migration failed") from exc
                if not isinstance(legacy, Mapping):
                    raise SchedulingError("INVALID_DISPATCH_CLAIM", "legacy claim is invalid")
                record = _migrate_legacy_claim(store, descriptor, legacy, secret)
            if record["ownership_key_id"] != hashlib.sha256(secret).hexdigest():
                raise SchedulingError(
                    "INVALID_DISPATCH_CLAIM", "ownership key identity is inconsistent"
                )
            if record["state"] != "active":
                continue
            age = _claim_age_seconds(record)
            alive = _pid_is_alive(record["pid"])
            observed_start = _process_start_binding(record["pid"]) if alive else None
            try:
                recovery_fd, _ = _open_lock_fd(
                    store, f"{record['claim_key']}.lock", blocking=False
                )
            except SchedulingError as exc:
                if exc.code != "CONCURRENT_DISPATCH_CLAIM":
                    raise
            else:
                reason = (
                    "process_dead"
                    if not alive
                    else "pid_reused"
                    if observed_start is not None
                    and observed_start != record["process_start_binding"]
                    else "stale_unlocked"
                )
                try:
                    _abandon_active_record(store, descriptor, record, reason)
                    record = _read_claim_fd(descriptor)
                finally:
                    if fcntl is not None:
                        fcntl.flock(recovery_fd, fcntl.LOCK_UN)
                    os.close(recovery_fd)
            if record["state"] == "active" and _ownership_token_conflict(
                exact, ancestors, record
            ):
                raise SchedulingError("OWNERSHIP_CONFLICT", "active dispatch ownership overlaps")
        finally:
            os.close(descriptor)


def _acquire_dispatch_claim(
    invocation: Invocation, retained_store: ClaimStore | None = None
) -> DispatchClaim:
    key = _dispatch_claim_key(invocation)
    store = (
        retained_store
        if retained_store is not None
        else _coerce_claim_store(_secure_claim_directory(invocation), invocation)
    )
    name = f"{key}.json"
    exact_tokens: tuple[str, ...] = ()
    ancestor_tokens: tuple[str, ...] = ()
    metadata_fd: int | None = None
    lock_fd: int | None = None
    try:
        metadata_fd, _ = _open_lock_fd(store, ".metadata.lock", blocking=True)
        ownership_key = _load_ownership_key(store)
        exact_tokens, ancestor_tokens = _ownership_token_set(
            invocation.ownership, ownership_key
        )
        try:
            os.stat(name, dir_fd=store.dir_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            probe_fd, _ = _acquire_store_lock(store, name, key)
            _release_store_lock(store, key, probe_fd)
        _check_active_ownership_conflicts(
            store, exact_tokens, ancestor_tokens, ownership_key
        )
        lock_fd, lock_identity = _acquire_store_lock(store, name, key)
    except BaseException:
        if lock_fd is not None:
            _release_store_lock(store, key, lock_fd)
        if metadata_fd is not None:
            if fcntl is not None:
                fcntl.flock(metadata_fd, fcntl.LOCK_UN)
            os.close(metadata_fd)
        store.close()
        raise
    path = store.path / name
    timestamp = _utc_now()
    record = {
        "version": DISPATCH_CLAIM_VERSION,
        "claim_key": key,
        "decision_sha256": invocation.decision_digest,
        "scheduling_snapshot_sha256": invocation.scheduling_snapshot_digest,
        "dispatch_identity": _claim_dispatch_identity(invocation),
        "ticket_sha256": hashlib.sha256(
            str(invocation.decision["ticket"] if invocation.decision else "missing").encode("ascii")
        ).hexdigest(),
        "route_sha256": _canonical_sha256(
            {
                "role": invocation.route.role, "alias": invocation.route.alias,
                "provider": invocation.route.cli, "model": invocation.route.model,
                "effort": invocation.route.effort,
            }
        ),
        "ownership_tokens_sha256": _ownership_tokens_digest(exact_tokens, ancestor_tokens),
        "ownership_key_id": hashlib.sha256(ownership_key).hexdigest(),
        "ownership_exact_tokens": list(exact_tokens),
        "ownership_ancestor_tokens": list(ancestor_tokens),
        "state": "active",
        "abandon_reason": None,
        "legacy_claim_sha256": None,
        "pid": os.getpid(),
        "process_start_binding": _process_start_binding(os.getpid()) or _PROCESS_START_NONCE,
        "created_at": timestamp,
        "updated_at": timestamp,
        "started_at": timestamp,
        "ended_at": None,
        "transport_status": "starting",
        "exit_code": None,
        "output_bytes": None,
        "output_sha256": None,
        "work_result_sha256": None,
    }
    try:
        descriptor = os.open(
            name, _file_open_flags(os.O_RDWR | os.O_CREAT | os.O_EXCL), 0o600,
            dir_fd=store.dir_fd,
        )
    except FileExistsError:
        try:
            existing_fd = os.open(name, _file_open_flags(os.O_RDONLY), dir_fd=store.dir_fd)
            try:
                error = _existing_claim_error(_read_claim_fd(existing_fd), key)
            finally:
                os.close(existing_fd)
        finally:
            _release_store_lock(store, key, lock_fd)
            if fcntl is not None:
                fcntl.flock(metadata_fd, fcntl.LOCK_UN)
            os.close(metadata_fd)
            store.close()
        raise error
    except OSError as exc:
        _release_store_lock(store, key, lock_fd)
        if fcntl is not None:
            fcntl.flock(metadata_fd, fcntl.LOCK_UN)
        os.close(metadata_fd)
        store.close()
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim creation failed") from exc
    try:
        payload = json.dumps(
            record, ensure_ascii=True, separators=(",", ":"), sort_keys=True
        ).encode("ascii")
        _write_all(descriptor, payload)
        os.fsync(descriptor)
        os.fsync(store.dir_fd)
        value = _validate_regular_fd(descriptor)
    except BaseException:
        os.close(descriptor)
        _release_store_lock(store, key, lock_fd)
        if fcntl is not None:
            fcntl.flock(metadata_fd, fcntl.LOCK_UN)
        os.close(metadata_fd)
        store.close()
        raise
    if fcntl is not None:
        fcntl.flock(metadata_fd, fcntl.LOCK_UN)
    os.close(metadata_fd)
    return DispatchClaim(
        path, store, key, record, lock_fd, descriptor, lock_identity,
        (value.st_dev, value.st_ino),
    )


def _verify_dispatch_claim(
    claim: DispatchClaim, *, require_start_freshness: bool = False
) -> None:
    if claim.closed:
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim is already closed")
    directory = os.fstat(claim.dir_fd)
    if (directory.st_dev, directory.st_ino) != claim.store.identity:
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim store identity changed")
    lock_stat = os.stat(
        f"{claim.key}.lock", dir_fd=claim.dir_fd, follow_symlinks=False
    )
    claim_stat = os.stat(claim.path.name, dir_fd=claim.dir_fd, follow_symlinks=False)
    if (lock_stat.st_dev, lock_stat.st_ino) != claim.lock_identity or (
        claim_stat.st_dev, claim_stat.st_ino
    ) != claim.claim_identity:
        raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim entry changed")
    persisted = _read_claim_fd(claim.claim_fd)
    if dict(persisted) != dict(claim.record):
        raise SchedulingError(
            "INVALID_DISPATCH_CLAIM", "dispatch claim changed before process creation"
        )
    if (
        require_start_freshness
        and _claim_age_seconds(persisted) > DISPATCH_CLAIM_START_MAX_AGE_SECONDS
    ):
        raise SchedulingError(
            "STALE_DISPATCH_CLAIM", "dispatch claim expired before process creation"
        )
    if persisted.get("pid") != os.getpid() or not _pid_is_alive(persisted.get("pid")):
        raise SchedulingError(
            "INVALID_DISPATCH_CLAIM", "dispatch claim process binding is invalid"
        )


def _persist_dispatch_claim(claim: DispatchClaim, updated: Mapping[str, Any]) -> None:
    metadata_fd, _ = _open_lock_fd(claim.store, ".metadata.lock", blocking=True)
    try:
        _verify_dispatch_claim(claim)
        payload = json.dumps(
            updated, ensure_ascii=True, separators=(",", ":"), sort_keys=True
        ).encode("ascii")
        if len(payload) > MAX_DISPATCH_CLAIM_BYTES:
            raise SchedulingError("INVALID_DISPATCH_CLAIM", "claim content is too large")
        os.lseek(claim.claim_fd, 0, os.SEEK_SET)
        os.ftruncate(claim.claim_fd, 0)
        _write_all(claim.claim_fd, payload)
        os.fsync(claim.claim_fd)
        os.fsync(claim.dir_fd)
        claim.record = dict(updated)
        _verify_dispatch_claim(claim)
    finally:
        if fcntl is not None:
            fcntl.flock(metadata_fd, fcntl.LOCK_UN)
        os.close(metadata_fd)


def _finalize_dispatch_claim(
    claim: DispatchClaim,
    state: str,
    result: subprocess.CompletedProcess[str] | None = None,
    provider_result: ProviderResult | None = None,
) -> str:
    if state not in {"completed", "rejected", "unknown"}:
        raise ValueError("unsupported claim terminal state")
    if claim.record.get("state") != "active":
        raise SchedulingError(
            "INVALID_DISPATCH_CLAIM", "terminal dispatch proof is immutable"
        )
    output = _raw_output_bytes(result) if result is not None else b""
    updated = dict(claim.record)
    updated.update(
        {
            "state": state,
            "updated_at": _utc_now(),
            "ended_at": _utc_now(),
            "transport_status": {
                "completed": "completed",
                "rejected": "provider_result_rejected",
                "unknown": "transport_unknown",
            }[state],
            "exit_code": result.returncode if result is not None else None,
            "output_bytes": len(output) if result is not None else None,
            "output_sha256": hashlib.sha256(output).hexdigest() if result is not None else None,
            "work_result_sha256": (
                _canonical_sha256(provider_result.work_result)
                if provider_result is not None
                else None
            ),
        }
    )
    _persist_dispatch_claim(claim, updated)
    return _canonical_sha256(updated)


def _release_dispatch_claim(claim: DispatchClaim) -> None:
    if claim.closed:
        return
    claim.closed = True
    try:
        os.close(claim.claim_fd)
    finally:
        try:
            claim.store.close()
        finally:
            _release_store_lock(claim.store, claim.key, claim.lock_fd)


def _update_dispatch_claim(claim: DispatchClaim, state: str) -> None:
    """Compatibility wrapper for typed non-receipt terminal transitions."""

    mapped = "unknown" if state == "unknown" else state
    _finalize_dispatch_claim(claim, mapped)


def _validated_invocation_decision(invocation: Invocation) -> ValidatedDispatchDecision:
    """Revalidate governance data stored on an Invocation at the spawn boundary."""

    if invocation.decision is None or invocation.model_policy is None:
        raise DispatchDecisionError(
            "executable dispatch requires --decision and the versioned model policy"
        )
    validated = validate_dispatch_decision(
        invocation.decision,
        invocation.model_policy,
        invocation.route,
    )
    if invocation.decision_digest != validated.digest:
        raise DispatchDecisionError("Invocation decision digest is missing or stale")
    bound_evidence = _decision_prompt_evidence(validated, invocation.attempt_id)
    if bound_evidence not in invocation.prompt_stdin:
        if invocation.route.cli != "agy":
            raise DispatchDecisionError("Invocation prompt is not bound to its DispatchDecision")
        try:
            agy_input = _strict_json_loads(invocation.prompt_stdin)
            if not isinstance(agy_input, Mapping) or set(agy_input) != {
                "event", "message"
            } or agy_input.get("event") != "user":
                raise TypeError
            message = _mapping(agy_input.get("message"), "AGY input message")
            if set(message) != {"content"}:
                raise TypeError
            content = message["content"]
        except (ConfigurationError, _StrictJSONError, KeyError, TypeError) as exc:
            raise DispatchDecisionError("AGY input is not a valid native user event") from exc
        prompt_text = content
        if not isinstance(prompt_text, str) or bound_evidence not in prompt_text:
            raise DispatchDecisionError("Invocation prompt is not bound to its DispatchDecision")
    return validated


def _validated_invocation_schedule(
    invocation: Invocation, validated: ValidatedDispatchDecision
) -> str:
    """Revalidate Rule 11 selection and its prompt binding at the spawn boundary."""

    if invocation.scheduling_snapshot is None:
        raise SchedulingError(
            "INVALID_SCHEDULING_METADATA",
            "executable dispatch requires --scheduling-snapshot",
        )
    digest = validate_scheduling_dispatch(
        invocation.scheduling_snapshot,
        validated.decision,
        role=invocation.route.role,
        ownership=invocation.ownership,
    )
    if invocation.scheduling_snapshot_digest != digest:
        raise SchedulingError(
            "INVALID_SCHEDULING_METADATA",
            "Invocation scheduling snapshot digest is missing or stale",
        )
    evidence = f"- scheduling_snapshot_sha256: {digest}"
    if evidence not in invocation.prompt_stdin:
        raise SchedulingError(
            "INVALID_SCHEDULING_METADATA",
            "Invocation prompt is not bound to its scheduling snapshot",
        )
    return digest


def normalize_result(
    payload: str | bytes | Mapping[str, Any] | None,
    *,
    returncode: int = 0,
) -> dict[str, Any]:
    """Validate and normalize the mandatory sub-agent result contract.

    The CLI must emit one JSON object.  In particular, status-like text or a
    missing evidence section is never silently treated as a successful result.
    """

    if payload is None or payload == "" or payload == b"":
        return {
            "status": "BLOCKED",
            "scope_owned": "unspecified",
            "evidence": {
                "commands": [],
                "outcomes": [
                    f"subprocess exit code: {returncode}",
                    "sub-agent returned empty stdout; result contract was not emitted",
                ],
                "artifacts": [],
            },
            "findings": ["No canonical sub-agent result was available to verify."],
            "changed_files": [],
            "residual_risk": "result contract compliance is unverified",
            "recommended_next_action": "rerun the sub-agent and require a JSON result with status and evidence",
        }
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8", errors="replace")
    if isinstance(payload, str):
        try:
            value = _strict_json_loads(payload)
        except _StrictJSONError as exc:
            raise ConfigurationError("sub-agent result is not valid JSON") from exc
    else:
        value = payload
    result = _mapping(value, "sub-agent result")
    missing = RESULT_FIELDS - set(result)
    if missing:
        raise ConfigurationError(
            "sub-agent result missing fields: " + ", ".join(sorted(missing))
        )
    unknown = set(result) - RESULT_FIELDS
    if unknown:
        raise ConfigurationError(
            "sub-agent result contains unsupported fields: " + ", ".join(sorted(unknown))
        )
    status = result["status"]
    if not isinstance(status, str) or status not in VALID_RESULT_STATUSES:
        raise ConfigurationError("sub-agent result status must be DONE, BLOCKED, or NEEDS_HITL")
    _validate_string_collection(
        result["scope_owned"],
        "sub-agent result scope_owned",
        allow_string=True,
        require_non_empty=True,
        require_non_empty_items=True,
    )
    evidence = _mapping(result["evidence"], "sub-agent result evidence")
    evidence_fields = {"commands", "outcomes", "artifacts"}
    unknown_evidence = set(evidence) - evidence_fields
    missing_evidence = evidence_fields - set(evidence)
    if missing_evidence:
        raise ConfigurationError(
            "sub-agent result evidence missing fields: "
            + ", ".join(sorted(missing_evidence))
        )
    if unknown_evidence:
        raise ConfigurationError(
            "sub-agent result evidence contains unsupported fields: "
            + ", ".join(sorted(unknown_evidence))
        )
    for key in ("commands", "outcomes", "artifacts"):
        _validate_string_collection(
            evidence[key], f"sub-agent result evidence.{key}"
        )
    _validate_string_collection(
        result["findings"], "sub-agent result findings", allow_string=True
    )
    _validate_string_collection(
        result["changed_files"], "sub-agent result changed_files", allow_string=True
    )
    if not isinstance(result["residual_risk"], str) or not result["residual_risk"].strip():
        raise ConfigurationError("sub-agent result residual_risk must be non-empty text")
    if (
        not isinstance(result["recommended_next_action"], str)
        or not result["recommended_next_action"].strip()
    ):
        raise ConfigurationError("sub-agent result recommended_next_action must be non-empty text")
    normalized = dict(result)
    normalized["status"] = status
    normalized["evidence"] = dict(evidence)
    _reject_secret_bearing(normalized, "WorkResult")
    return normalized


def _jsonl_events(payload: str | bytes | None, label: str) -> tuple[list[Mapping[str, Any]], bytes]:
    """Parse a bounded NDJSON provider stream without tolerating malformed lines."""

    if payload is None:
        raw = b""
    elif isinstance(payload, bytes):
        raw = payload
    elif isinstance(payload, str):
        try:
            raw = payload.encode("utf-8")
        except UnicodeError as exc:
            raise ProviderParseError(
                "terminal_shape", f"{label} event stream is not UTF-8"
            ) from exc
    else:
        raise ProviderParseError("terminal_shape", f"{label} event stream has an invalid type")
    if not raw:
        raise ProviderParseError("terminal_shape", f"{label} event stream is empty")
    if len(raw) > MAX_PROVIDER_OUTPUT_BYTES:
        raise ProviderParseError(
            "terminal_shape", f"{label} event stream exceeds the safe byte limit"
        )
    try:
        text_payload = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProviderParseError("terminal_shape", f"{label} event stream is not UTF-8") from exc
    events: list[Mapping[str, Any]] = []
    for line_number, line in enumerate(text_payload.splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = _strict_json_loads(line)
        except _StrictJSONError as exc:
            raise ProviderParseError(
                "terminal_shape",
                f"{label} event stream has malformed JSON at line {line_number}"
            ) from exc
        try:
            events.append(_mapping(event, f"{label} event line {line_number}"))
        except ConfigurationError as exc:
            raise ProviderParseError(
                "terminal_shape", f"{label} event line {line_number} must be a mapping"
            ) from exc
    if not events:
        raise ProviderParseError("terminal_shape", f"{label} event stream has no events")
    try:
        _reject_secret_bearing(events, f"{label} event stream")
    except ConfigurationError as exc:
        raise ProviderParseError(
            "secret_bearing", f"{label} event stream contains secret-bearing content"
        ) from exc
    return events, raw


def _provider_id(value: Any, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not SAFE_PROVIDER_ID.fullmatch(value):
        raise ConfigurationError(f"{label} contains an unsafe provider identifier")
    return value


def _provider_stream_id(value: Any, label: str) -> str | None:
    """Validate an opaque provider session identifier without exposing it."""

    try:
        return _provider_id(value, label)
    except ConfigurationError as exc:
        raise ProviderParseError("thread_id", f"{label} is invalid") from exc


def _normalized_provider_work_result(value: Any, label: str) -> dict[str, Any]:
    """Classify WorkResult validation errors without retaining provider content."""

    try:
        return normalize_result(_mapping(value, label))
    except ConfigurationError as exc:
        raise ProviderParseError(
            "work_result_validation", "provider WorkResult validation failed"
        ) from exc


def _saturated_candidate_count(candidates: Sequence[Mapping[str, Any]]) -> int:
    """Return only the closed 0/1/2+ cardinality signal, never candidate content."""

    return min(len(candidates), 2)


def _parse_codex_result(
    payload: str | bytes | None,
    private_final: Mapping[str, Any] | None = None,
) -> ProviderResult:
    events, _ = _jsonl_events(payload, "Codex JSONL")
    terminal_indices = [index for index, event in enumerate(events) if event.get("type") == "turn.completed"]
    if len(terminal_indices) != 1 or terminal_indices[0] != len(events) - 1:
        raise ProviderParseError(
            "terminal_shape", "Codex JSONL requires one unambiguous terminal turn.completed event"
        )
    if any(
        isinstance(event.get("type"), str)
        and event.get("type") in {"turn.failed", "error"}
        for event in events
    ):
        raise ProviderParseError(
            "provider_failure_event", "Codex JSONL contains a provider failure event"
        )

    thread_ids = [
        event.get("thread_id")
        for event in events
        if event.get("type") == "thread.started" and event.get("thread_id") is not None
    ]
    if thread_ids and any(thread_id != thread_ids[0] for thread_id in thread_ids[1:]):
        raise ProviderParseError("thread_id", "Codex JSONL contains conflicting thread identifiers")
    session_id = _provider_stream_id(
        thread_ids[0] if thread_ids else None, "Codex thread_id"
    )

    candidates: list[dict[str, Any]] = []
    for event in events[: terminal_indices[0]]:
        if event.get("type") != "item.completed":
            continue
        try:
            item = _mapping(event.get("item"), "Codex completed item")
        except ConfigurationError as exc:
            raise ProviderParseError(
                "final_message_cardinality",
                "Codex completed item is invalid",
                final_message_cardinality_subreason="completed_item_shape",
                candidate_count=_saturated_candidate_count(candidates),
            ) from exc
        if item.get("type") != "agent_message":
            continue
        text = item.get("text")
        if not isinstance(text, str):
            raise ProviderParseError(
                "final_message_cardinality",
                "Codex agent_message text must be a string",
                final_message_cardinality_subreason="agent_message_text_shape",
                candidate_count=_saturated_candidate_count(candidates),
            )
        try:
            candidate = _strict_json_loads(text)
        except _AmbiguousJSONError as exc:
            raise ProviderParseError(
                "terminal_shape", "Codex final message contains ambiguous JSON"
            ) from exc
        except _StrictJSONError as exc:
            # Ordinary prose is telemetry, not a structured candidate. Text
            # that starts like JSON is a malformed candidate and fails closed.
            if text.lstrip().startswith(("{", "[")):
                raise ProviderParseError(
                    "work_result_validation",
                    "Codex structured agent_message candidate is malformed",
                ) from exc
            continue
        if not isinstance(candidate, Mapping):
            raise ProviderParseError(
                "work_result_validation",
                "Codex structured agent_message candidate is not a WorkResult",
            )
        candidates.append(
            _normalized_provider_work_result(candidate, "Codex telemetry WorkResult")
        )
    if len(candidates) > 1:
        raise ProviderParseError(
            "final_message_cardinality",
            "Codex JSONL must not contain more than exactly one structured final WorkResult",
            final_message_cardinality_subreason="multiple_structured_candidates",
            candidate_count=_saturated_candidate_count(candidates),
        )
    if private_final is None:
        # Retained for standalone v2 receipt revalidation and parser callers.
        # Governed execution always supplies the independently validated -o
        # channel and never relies on JSONL extraction.
        if len(candidates) != 1:
            raise ProviderParseError(
                "final_message_cardinality",
                "Codex JSONL must contain exactly one structured final WorkResult",
                candidate_count=_saturated_candidate_count(candidates),
            )
        work_result = candidates[0]
    else:
        work_result = _normalized_provider_work_result(
            private_final, "Codex private final WorkResult"
        )
        if candidates and candidates[0] != work_result:
            raise ProviderParseError(
                "work_result_validation",
                "Codex telemetry and private final WorkResults conflict",
            )
    return ProviderResult(
        work_result=work_result,
        adapter="codex-jsonl-output-schema-v2",
        process_or_session_id=session_id,
    )


def _parse_agy_result(payload: str | bytes | None) -> ProviderResult:
    events, _ = _jsonl_events(payload, "AGY stream-json")
    if any("type" in item for item in events):
        raise ProviderParseError(
            "terminal_shape", "AGY stream-json uses an unsupported event dialect"
        )
    event_names = [item.get("event") for item in events]
    if any(not isinstance(name, str) for name in event_names):
        raise ProviderParseError("terminal_shape", "AGY stream-json event name is missing")
    if any(name == "error" for name in event_names):
        raise ProviderParseError(
            "provider_failure_event", "AGY stream-json contains a provider failure event"
        )
    if any(name not in {"init", "step_update", "result"} for name in event_names):
        raise ProviderParseError(
            "terminal_shape", "AGY stream-json contains an unsupported event name"
        )
    if event_names[0] != "init":
        raise ProviderParseError("terminal_shape", "AGY stream-json must start with one init event")
    if event_names.count("init") != 1:
        raise ProviderParseError(
            "terminal_shape", "AGY stream-json contains ambiguous init events"
        )
    terminal_indices = [
        index for index, name in enumerate(event_names) if name == "result"
    ]
    if len(terminal_indices) != 1 or terminal_indices[0] != len(events) - 1:
        raise ProviderParseError(
            "terminal_shape", "AGY stream-json requires one unambiguous terminal result event"
        )

    init_event = events[0]
    if set(init_event) != {"event", "conversation_id", "init"}:
        raise ProviderParseError(
            "terminal_shape", "AGY stream-json init envelope is invalid"
        )
    try:
        _mapping(init_event.get("init"), "AGY init payload")
    except ConfigurationError as exc:
        raise ProviderParseError(
            "terminal_shape", "AGY stream-json init payload is invalid"
        ) from exc
    session_id = _provider_stream_id(
        init_event.get("conversation_id"), "AGY conversation_id"
    )
    if session_id is None:
        raise ProviderParseError(
            "thread_id", "AGY stream-json conversation identifier is missing"
        )

    for event in events[1:terminal_indices[0]]:
        if set(event) != {"event", "step_update"}:
            raise ProviderParseError(
                "terminal_shape", "AGY stream-json step envelope is invalid"
            )
        try:
            update = _mapping(event.get("step_update"), "AGY step payload")
        except ConfigurationError as exc:
            raise ProviderParseError(
                "terminal_shape", "AGY stream-json step payload is invalid"
            ) from exc
        update_id = _provider_stream_id(
            update.get("conversation_id"), "AGY step conversation_id"
        )
        if update_id is None or update_id != session_id:
            raise ProviderParseError(
                "thread_id", "AGY stream-json conversation identifiers are inconsistent"
            )
        state = update.get("state")
        if state == "ERROR" or "error" in update:
            raise ProviderParseError(
                "provider_failure_event", "AGY stream-json contains a failed step"
            )
        if state not in {"ACTIVE", "DONE"}:
            raise ProviderParseError(
                "terminal_shape", "AGY stream-json step state is invalid"
            )

    terminal_event = events[-1]
    if set(terminal_event) != {"event", "result"}:
        raise ProviderParseError(
            "terminal_shape", "AGY stream-json terminal envelope is invalid"
        )
    try:
        terminal = _mapping(terminal_event.get("result"), "AGY result payload")
    except ConfigurationError as exc:
        raise ProviderParseError(
            "terminal_shape", "AGY stream-json terminal payload is invalid"
        ) from exc
    terminal_id = _provider_stream_id(
        terminal.get("conversation_id"), "AGY result conversation_id"
    )
    if terminal_id is None or terminal_id != session_id:
        raise ProviderParseError(
            "thread_id", "AGY stream-json conversation identifiers are inconsistent"
        )
    if terminal.get("status") != "SUCCESS" or "error" in terminal:
        raise ProviderParseError(
            "provider_failure_event", "AGY stream-json terminal status is not successful"
        )
    if "structured_output" not in terminal:
        raise ProviderParseError(
            "work_result_validation", "AGY structured output is missing"
        )
    work_result = _normalized_provider_work_result(
        terminal.get("structured_output"), "AGY structured output"
    )
    return ProviderResult(
        work_result=work_result,
        adapter="agy-stream-json-schema-v2",
        process_or_session_id=session_id,
    )


def parse_provider_result(
    invocation: Invocation,
    payload: str | bytes | None,
    *,
    private_final: Mapping[str, Any] | None = None,
) -> ProviderResult:
    """Apply exactly one provider-native adapter; no fallback or prose inference."""

    try:
        if invocation.route.cli == "codex":
            parsed = _parse_codex_result(payload, private_final)
        elif invocation.route.cli == "agy":
            parsed = _parse_agy_result(payload)
        else:
            raise ConfigurationError(
                "no Result Contract v2 adapter exists for the selected provider"
            )
        sanitized = normalize_result(
            _redact_result_value(dict(parsed.work_result), invocation)
        )
        return ProviderResult(
            work_result=sanitized,
            adapter=parsed.adapter,
            process_or_session_id=parsed.process_or_session_id,
        )
    except ProviderParseError:
        raise
    except ConfigurationError as exc:
        raise ProviderParseError("unknown", "provider result validation failed") from exc


def _validate_account_home_stat(value: os.stat_result) -> tuple[int, int]:
    """Validate an isolated account-home descriptor without reading its files."""

    if (
        not stat.S_ISDIR(value.st_mode)
        or stat.S_IMODE(value.st_mode) & 0o700 != 0o700
        or stat.S_IMODE(value.st_mode) & 0o022
        or (hasattr(os, "getuid") and value.st_uid != os.getuid())
    ):
        raise ConfigurationError("ACCOUNT_HOME_INVALID")
    return value.st_dev, value.st_ino


def _open_account_home_path(home_path: str) -> tuple[int, tuple[int, int]]:
    """Open every account-home path component without following symbolic links."""

    path = Path(home_path)
    raw_parts = home_path.split(os.sep)
    if (
        not path.is_absolute()
        or any(part in {".", ".."} for part in raw_parts)
        or any(not part for part in raw_parts[1:-1])
    ):
        raise ConfigurationError("ACCOUNT_HOME_INVALID")
    parts = path.parts
    if len(parts) < 2:
        raise ConfigurationError("ACCOUNT_HOME_INVALID")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    descriptor: int | None = None
    try:
        descriptor = os.open(parts[0], flags)
        for component in parts[1:]:
            child = os.open(component, flags, dir_fd=descriptor)
            parent = descriptor
            descriptor = child
            os.close(parent)
        identity = _validate_account_home_stat(os.fstat(descriptor))
        return descriptor, identity
    except (ConfigurationError, OSError):
        if descriptor is not None:
            os.close(descriptor)
        raise ConfigurationError("ACCOUNT_HOME_INVALID") from None


def _open_isolated_account_home(invocation: Invocation) -> tuple[int, tuple[int, int]]:
    """Open and retain one structurally safe account home; never inspect auth data."""

    expected_env = VALID_HOME_ENV.get(invocation.route.cli)
    home_path = invocation.route.home_path
    if (
        invocation.route.alias not in GOVERNED_ACCOUNT_ALIASES
        or expected_env is None
        or invocation.route.home_env != expected_env
        or not home_path
    ):
        raise ConfigurationError("ACCOUNT_HOME_REQUIRED")
    required_flags = ("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC")
    if any(not hasattr(os, name) for name in required_flags):
        raise ConfigurationError("ACCOUNT_HOME_UNSUPPORTED")
    return _open_account_home_path(home_path)


def _verify_isolated_account_home(
    invocation: Invocation, descriptor: int, identity: tuple[int, int]
) -> None:
    """Revalidate the held home and its no-follow pathname before process creation."""

    home_path = invocation.route.home_path
    if not isinstance(home_path, str) or not home_path:
        raise ConfigurationError("ACCOUNT_HOME_REQUIRED")
    path_descriptor: int | None = None
    try:
        descriptor_identity = _validate_account_home_stat(os.fstat(descriptor))
        path_descriptor, path_identity = _open_account_home_path(home_path)
    except (ConfigurationError, OSError):
        raise ConfigurationError("ACCOUNT_HOME_INVALID") from None
    finally:
        if path_descriptor is not None:
            os.close(path_descriptor)
    if descriptor_identity != identity or path_identity != identity:
        raise ConfigurationError("ACCOUNT_HOME_INVALID")


def validate_execution_preflight(invocation: Invocation) -> None:
    """Require a runnable executable and a structurally isolated account home."""

    _validate_invocation_provider_binding(invocation)
    executable = invocation.route.command
    if "/" in executable:
        executable_path = Path(executable)
        if not executable_path.is_file() or not os.access(executable_path, os.X_OK):
            raise ConfigurationError(f"configured {invocation.route.cli} executable is unavailable")
    elif shutil.which(executable) is None:
        raise ConfigurationError(f"configured {invocation.route.cli} executable is unavailable")
    home_fd, home_identity = _open_isolated_account_home(invocation)
    try:
        _verify_isolated_account_home(invocation, home_fd, home_identity)
    finally:
        os.close(home_fd)
    if invocation.decision and invocation.decision.get("work_mode") == "read_only":
        if not invocation.runtime_config_approved or not invocation.runtime_config_path:
            raise ConfigurationError("read-only dispatch requires an approved runtime config path")
        runtime_path = Path(invocation.runtime_config_path)
        if not runtime_path.is_file() or ".example." in runtime_path.name:
            raise ConfigurationError("example or missing runtime config is not approved for execution")
        if invocation.route.cli == "codex" and invocation.route.sandbox != "read-only":
            raise ConfigurationError("Codex read-only dispatch requires sandbox=read-only")
        if invocation.route.cli == "agy" and not (
            invocation.route.mode == "plan" and invocation.route.sandbox is True
        ):
            raise ConfigurationError("AGY read-only dispatch requires mode=plan and sandbox=true")


def _create_private_final_file(directory: Path) -> tuple[Path, tuple[int, int]]:
    """Create a private regular file and return its immutable identity."""

    path = directory / "codex-final-work-result.json"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o600
            or metadata.st_nlink != 1
            or (hasattr(os, "getuid") and metadata.st_uid != os.getuid())
        ):
            raise ConfigurationError("private final output file is unsafe")
        return path, (metadata.st_dev, metadata.st_ino)
    finally:
        os.close(descriptor)


def _read_private_final_file(
    path: Path, expected_identity: tuple[int, int]
) -> PrivateFinalResult:
    """Read one bounded no-follow final WorkResult without retaining raw content."""

    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NONBLOCK
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ProviderParseError(
            "work_result_validation", "Codex private final output is unavailable"
        ) from exc
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or (metadata.st_dev, metadata.st_ino) != expected_identity
            or metadata.st_nlink != 1
            or stat.S_IMODE(metadata.st_mode) & 0o077
            or (hasattr(os, "getuid") and metadata.st_uid != os.getuid())
        ):
            raise ProviderParseError(
                "work_result_validation", "Codex private final output identity is invalid"
            )
        if metadata.st_size < 1 or metadata.st_size > MAX_PRIVATE_FINAL_BYTES:
            raise ProviderParseError(
                "work_result_validation", "Codex private final output size is invalid"
            )
        raw = bytearray()
        while len(raw) <= MAX_PRIVATE_FINAL_BYTES:
            chunk = os.read(descriptor, min(65_536, MAX_PRIVATE_FINAL_BYTES + 1 - len(raw)))
            if not chunk:
                break
            raw.extend(chunk)
        if len(raw) != metadata.st_size or len(raw) > MAX_PRIVATE_FINAL_BYTES:
            raise ProviderParseError(
                "work_result_validation", "Codex private final output changed while reading"
            )
        final_metadata = os.fstat(descriptor)
        if (
            (final_metadata.st_dev, final_metadata.st_ino)
            != (metadata.st_dev, metadata.st_ino)
            or final_metadata.st_size != metadata.st_size
            or final_metadata.st_nlink != 1
            or not stat.S_ISREG(final_metadata.st_mode)
            or stat.S_IMODE(final_metadata.st_mode) != stat.S_IMODE(metadata.st_mode)
            or final_metadata.st_mtime_ns != metadata.st_mtime_ns
            or final_metadata.st_ctime_ns != metadata.st_ctime_ns
            or final_metadata.st_uid != metadata.st_uid
            or (hasattr(os, "getuid") and final_metadata.st_uid != os.getuid())
        ):
            raise ProviderParseError(
                "work_result_validation", "Codex private final output changed while reading"
            )
    finally:
        os.close(descriptor)
    try:
        text = bytes(raw).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProviderParseError(
            "work_result_validation", "Codex private final output is not UTF-8"
        ) from exc
    try:
        decoded = _strict_json_loads(text)
    except _StrictJSONError as exc:
        raise ProviderParseError(
            "work_result_validation", "Codex private final output is malformed JSON"
        ) from exc
    normalized = _normalized_provider_work_result(decoded, "Codex private final WorkResult")
    return PrivateFinalResult(
        work_result=normalized,
        byte_count=len(raw),
        sha256=hashlib.sha256(raw).hexdigest(),
    )


def _validated_text_channel(value: str | bytes | None, label: str) -> bytes:
    """Validate one bounded UTF-8 transport channel and reject secret findings."""

    if value is None:
        raw = b""
        text = ""
    elif isinstance(value, str):
        try:
            raw = value.encode("utf-8")
        except UnicodeError as exc:
            raise ProviderParseError("terminal_shape", f"{label} is not UTF-8") from exc
        text = value
    elif isinstance(value, bytes):
        raw = value
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ProviderParseError("terminal_shape", f"{label} is not UTF-8") from exc
    else:
        raise ProviderParseError("terminal_shape", f"{label} has an invalid type")
    if len(raw) > MAX_PROVIDER_OUTPUT_BYTES:
        raise ProviderParseError("terminal_shape", f"{label} exceeds the safe byte limit")
    try:
        _reject_secret_bearing(text, label)
    except ConfigurationError as exc:
        raise ProviderParseError("secret_bearing", f"{label} contains a secret finding") from exc
    return raw


def _private_final_from_process(
    result: subprocess.CompletedProcess[str],
) -> PrivateFinalResult:
    value = getattr(result, "_private_final_result", None)
    if not isinstance(value, PrivateFinalResult):
        raise ProviderParseError(
            "work_result_validation", "Codex private final evidence is missing"
        )
    if (
        value.byte_count < 1
        or value.byte_count > MAX_PRIVATE_FINAL_BYTES
        or not re.fullmatch(r"[a-f0-9]{64}", value.sha256)
        or value.byte_count != getattr(result, "_private_final_bytes", None)
        or value.sha256 != getattr(result, "_private_final_sha256", None)
        or _canonical_sha256(value.work_result)
        != getattr(result, "_private_final_work_result_sha256", None)
    ):
        raise ProviderParseError(
            "work_result_validation", "Codex private final digest evidence is invalid"
        )
    return value


def _validated_process_channel_evidence(
    result: subprocess.CompletedProcess[str],
) -> dict[str, dict[str, str | int]]:
    """Recompute and verify the in-memory transport channel digest bindings."""

    evidence: dict[str, dict[str, str | int]] = {}
    for name in ("stdout", "stderr"):
        raw = _validated_text_channel(getattr(result, name), f"provider {name}")
        byte_count = len(raw)
        digest = hashlib.sha256(raw).hexdigest()
        if (
            byte_count != getattr(result, f"_{name}_bytes", None)
            or digest != getattr(result, f"_{name}_sha256", None)
        ):
            raise ProviderParseError(
                "terminal_shape", f"provider {name} digest evidence is invalid"
            )
        evidence[name] = {"bytes": byte_count, "sha256": digest}
    return evidence


def _terminate_owned_process_group(process: subprocess.Popen[bytes]) -> None:
    """Terminate, then kill and reap, the distinct session owned by this dispatch."""

    process_group = process.pid

    def group_exists() -> bool:
        try:
            os.killpg(process_group, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            # POSIX reports EPERM for an existing group with no signalable
            # member (for example, an unreaped leader). Reap/poll below before
            # deciding that cleanup failed.
            return True
        return True

    if group_exists():
        try:
            os.killpg(process_group, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except PermissionError:
            pass
    grace_deadline = time.monotonic() + PROCESS_GROUP_TERMINATE_SECONDS
    while group_exists() and time.monotonic() < grace_deadline:
        process.poll()
        time.sleep(0.02)
    if group_exists():
        try:
            os.killpg(process_group, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except PermissionError:
            pass
    try:
        process.wait(timeout=PROCESS_GROUP_TERMINATE_SECONDS)
    except subprocess.TimeoutExpired as exc:
        raise ConfigurationError("owned provider process leader could not be reaped") from exc
    reap_deadline = time.monotonic() + PROCESS_GROUP_TERMINATE_SECONDS
    while group_exists() and time.monotonic() < reap_deadline:
        time.sleep(0.02)
    if group_exists():
        raise ConfigurationError("owned provider process group did not terminate")


def _validate_approval_grant_v1(
    grant: Mapping[str, Any],
    claim: Mapping[str, Any],
    expected_binding: Mapping[str, Any],
    *,
    enforce_fresh: bool = True,
    claim_artifact_sha256: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    required = {
        "schema_version", "artifact_type", "approval_type", "grant_id",
        "claim_id", "claim_sha256", "binding", "nonce", "created_at",
        "expires_at", "ttl_seconds", "max_uses", "revoked",
        "attestation_scope", "authenticity_claimed", "retention_days",
        "raw_streams_retained",
    }
    if set(grant) != required:
        raise ProbeAuthorizationError("ApprovalGrant fields are invalid")
    if (
        grant.get("schema_version") != 1
        or grant.get("artifact_type") != "ApprovalGrant"
        or grant.get("approval_type") != "ProbeApproval"
        or grant.get("ttl_seconds") != APPROVAL_GRANT_TTL_SECONDS
        or grant.get("max_uses") != 1
        or grant.get("revoked") is not False
        or grant.get("attestation_scope") != PREAUTH_SCOPE
        or grant.get("authenticity_claimed") is not False
        or grant.get("retention_days") != PREAUTH_RETENTION_DAYS
        or grant.get("raw_streams_retained") is not False
    ):
        raise ProbeAuthorizationError("ApprovalGrant policy is invalid")
    if grant.get("binding") != dict(expected_binding):
        raise ProbeAuthorizationError("ApprovalGrant binding is stale or mismatched")
    if grant.get("claim_id") != claim.get("claim_id"):
        raise ProbeAuthorizationError("ApprovalGrant claim binding is invalid")
    expected_claim_sha256 = claim_artifact_sha256 or hashlib.sha256(
        _canonical_json_bytes(claim)
    ).hexdigest()
    if grant.get("claim_sha256") != expected_claim_sha256:
        raise ProbeAuthorizationError("ApprovalGrant claim digest is invalid")
    if not isinstance(grant.get("nonce"), str) or not re.fullmatch(
        r"[a-f0-9]{64}", grant["nonce"]
    ):
        raise ProbeAuthorizationError("ApprovalGrant nonce is invalid")
    created = _parse_utc_timestamp(grant.get("created_at"), "ApprovalGrant created_at")
    expires = _parse_utc_timestamp(grant.get("expires_at"), "ApprovalGrant expires_at")
    claim_created = _parse_utc_timestamp(
        claim.get("created_at"), "ProbeClaim created_at"
    )
    claim_expires = _parse_utc_timestamp(
        claim.get("expires_at"), "ProbeClaim expires_at"
    )
    if expires - created != timedelta(seconds=APPROVAL_GRANT_TTL_SECONDS):
        raise ProbeAuthorizationError("ApprovalGrant expiry is invalid")
    if created < claim_created or expires > claim_expires:
        raise ProbeAuthorizationError("ApprovalGrant temporal binding is invalid")
    if enforce_fresh:
        captured_now = now or _utc_datetime()
        if created > captured_now:
            raise ProbeAuthorizationError("ApprovalGrant is not yet valid")
        if captured_now >= expires:
            raise ProbeAuthorizationError("ApprovalGrant is expired")
    if grant.get("grant_id") != _artifact_address(grant, "grant_id"):
        raise ProbeAuthorizationError("ApprovalGrant content address is invalid")
    return dict(grant)


def _prepare_probe_authorization(
    invocation: Invocation, *, enforce_fresh: bool = True,
    reject_consumed: bool = True,
) -> PreparedProbeAuthorization:
    """Load and retain exact claim/grant artifacts for final spawn-boundary consume."""

    if not all(
        (
            invocation.probe_claim_path,
            invocation.approval_grant_path,
            invocation.approval_store_path,
            invocation.approval_session_id,
        )
    ):
        raise ProbeAuthorizationError(
            "--execute requires exact ProbeClaim, ApprovalGrant, store, and session"
    )
    stores = _open_preauthorization_stores(invocation)
    claim_store, grant_store, consume_store, dispatch_store, store_binding = stores
    try:
        bound = replace(
            invocation, preauthorization_store_binding=store_binding
        )
        binding = _preauthorization_binding(bound)
        captured_now = _utc_datetime()
        claim_artifact = _secure_json_artifact(
            invocation.probe_claim_path, retained_parent=claim_store
        )
    except BaseException:
        claim_store.close()
        grant_store.close()
        consume_store.close()
        dispatch_store.close()
        raise
    try:
        claim = _validate_claim_record_v1(
            claim_artifact.record,
            binding,
            enforce_fresh=False,
            now=captured_now,
        )
        grant_artifact = _secure_json_artifact(
            invocation.approval_grant_path, retained_parent=grant_store
        )
        try:
            _validate_approval_grant_v1(
                grant_artifact.record, claim, binding,
                enforce_fresh=False,
                claim_artifact_sha256=hashlib.sha256(claim_artifact.raw).hexdigest(),
                now=captured_now,
            )
            if reject_consumed:
                names = (
                    (
                        consume_store.fd,
                        f"{grant_artifact.record['grant_id']}.consume.json",
                    ),
                    (
                        dispatch_store.dir_fd,
                        _consume_anchor_name(grant_artifact.record["grant_id"]),
                    ),
                )
                for descriptor, name in names:
                    try:
                        os.stat(name, dir_fd=descriptor, follow_symlinks=False)
                    except FileNotFoundError:
                        continue
                    raise ProbeAuthorizationError("ApprovalGrant is already consumed")
            if enforce_fresh:
                claim = _validate_claim_record_v1(
                    claim_artifact.record,
                    binding,
                    enforce_fresh=True,
                    now=captured_now,
                )
                _validate_approval_grant_v1(
                    grant_artifact.record,
                    claim,
                    binding,
                    enforce_fresh=True,
                    claim_artifact_sha256=hashlib.sha256(
                        claim_artifact.raw
                    ).hexdigest(),
                    now=captured_now,
                )
        except BaseException:
            grant_artifact.close()
            raise
    except BaseException:
        claim_artifact.close()
        claim_store.close()
        grant_store.close()
        consume_store.close()
        dispatch_store.close()
        raise
    return PreparedProbeAuthorization(
        claim_artifact,
        grant_artifact,
        binding,
        claim_store,
        grant_store,
        consume_store,
        dispatch_store,
    )


def _approval_store_fd(invocation: Invocation) -> int:
    if not invocation.approval_store_path:
        raise ProbeAuthorizationError("approval consume store is required")
    return _approval_store_path_fd(invocation.approval_store_path)


def _approval_store_path_fd(path: str | os.PathLike[str]) -> int:
    retained = _open_retained_private_directory(path, "approval consume store")
    try:
        return retained.duplicate_fd()
    finally:
        retained.close()


CONSUME_RECEIPT_FIELDS = frozenset(
    {
        "schema_version", "artifact_type", "consume_id", "claim_id",
        "claim_sha256", "grant_id", "grant_sha256", "binding",
        "consumed_at", "use_number", "max_uses", "consume_status",
        "attestation_scope", "authenticity_claimed", "retention_days",
        "raw_streams_retained",
    }
)
CONSUME_TOMBSTONE_FIELDS = frozenset(
    {
        "schema_version", "artifact_type", "consume_id", "grant_id",
        "original_receipt_sha256", "consume_anchor_id",
        "consume_anchor_sha256", "consumed_at", "compacted_at",
        "anti_replay", "retention", "attestation_scope",
        "authenticity_claimed", "raw_streams_retained",
    }
)
CONSUME_ANCHOR_FIELDS = frozenset(
    {
        "schema_version", "artifact_type", "anchor_id", "consume_id",
        "claim_id", "grant_id", "consume_receipt_sha256", "consumed_at",
        "preauthorization_stores", "dispatch_identity",
        "attestation_scope", "authenticity_claimed",
        "raw_streams_retained",
    }
)


def _consume_anchor_name(grant_id: str) -> str:
    if not isinstance(grant_id, str) or not re.fullmatch(r"[a-f0-9]{64}", grant_id):
        raise ProbeAuthorizationError("grant id is invalid")
    return f"preauth-{grant_id}.consume-anchor.json"


def _validate_consume_record_v1(record: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one fully closed consume-receipt or tombstone variant."""

    value = _mapping(record, "approval consume record")
    artifact_type = value.get("artifact_type")
    expected_fields = {
        "ApprovalConsumeReceipt": CONSUME_RECEIPT_FIELDS,
        "ApprovalConsumeTombstone": CONSUME_TOMBSTONE_FIELDS,
    }.get(artifact_type)
    if expected_fields is None or set(value) != expected_fields:
        raise ProbeAuthorizationError("approval consume variant fields are invalid")
    if value.get("schema_version") != APPROVAL_CONSUME_SCHEMA_VERSION:
        raise ProbeAuthorizationError("approval consume version is invalid")
    variant_digest_fields = (
        ("claim_id", "claim_sha256", "grant_sha256")
        if artifact_type == "ApprovalConsumeReceipt"
        else ("original_receipt_sha256", "consume_anchor_id", "consume_anchor_sha256")
    )
    for field in ("consume_id", "grant_id", *variant_digest_fields):
        if not isinstance(value.get(field), str) or not re.fullmatch(
            r"[a-f0-9]{64}", value[field]
        ):
            raise ProbeAuthorizationError("approval consume digest field is invalid")
    if artifact_type == "ApprovalConsumeReceipt":
        if (
            value.get("use_number") != 1
            or value.get("max_uses") != 1
            or value.get("consume_status") != "consumed"
            or value.get("attestation_scope") != PREAUTH_SCOPE
            or value.get("authenticity_claimed") is not False
            or value.get("retention_days") != PREAUTH_RETENTION_DAYS
            or value.get("raw_streams_retained") is not False
            or value.get("consume_id") != _artifact_address(value, "consume_id")
        ):
            raise ProbeAuthorizationError("ApprovalConsumeReceipt policy is invalid")
        _validate_preauthorization_binding_shape(
            _mapping(value.get("binding"), "ApprovalConsumeReceipt binding")
        )
        _parse_utc_timestamp(value.get("consumed_at"), "consumed_at")
    else:
        consumed = _parse_utc_timestamp(value.get("consumed_at"), "consumed_at")
        compacted = _parse_utc_timestamp(value.get("compacted_at"), "compacted_at")
        if (
            compacted < consumed
            or value.get("anti_replay") is not True
            or value.get("retention") != "indefinite"
            or value.get("attestation_scope") != PREAUTH_SCOPE
            or value.get("authenticity_claimed") is not False
            or value.get("raw_streams_retained") is not False
        ):
            raise ProbeAuthorizationError("ApprovalConsumeTombstone policy is invalid")
    return dict(value)


def _validate_consume_anchor_v1(
    record: Mapping[str, Any],
    *,
    consume: Mapping[str, Any],
    consume_raw: bytes,
    expected_stores: Mapping[str, Any],
    dispatch_identity: str,
) -> dict[str, Any]:
    value = _mapping(record, "approval consume anchor")
    if set(value) != CONSUME_ANCHOR_FIELDS:
        raise ProbeAuthorizationError("approval consume anchor fields are invalid")
    stores = _validated_preauthorization_stores(
        _mapping(value.get("preauthorization_stores"), "anchor stores")
    )
    expected = {
        "schema_version": 1,
        "artifact_type": "ApprovalConsumeAnchor",
        "consume_id": consume.get("consume_id"),
        "claim_id": consume.get("claim_id"),
        "grant_id": consume.get("grant_id"),
        "consume_receipt_sha256": hashlib.sha256(consume_raw).hexdigest(),
        "consumed_at": consume.get("consumed_at"),
        "preauthorization_stores": _validated_preauthorization_stores(
            expected_stores
        ),
        "dispatch_identity": dispatch_identity,
        "attestation_scope": PREAUTH_SCOPE,
        "authenticity_claimed": False,
        "raw_streams_retained": False,
    }
    for field, expected_value in expected.items():
        actual = stores if field == "preauthorization_stores" else value.get(field)
        if actual != expected_value:
            raise ProbeAuthorizationError("approval consume anchor binding is invalid")
    if value.get("anchor_id") != _artifact_address(value, "anchor_id"):
        raise ProbeAuthorizationError("approval consume anchor address is invalid")
    _parse_utc_timestamp(value.get("consumed_at"), "anchor consumed_at")
    return dict(value)


def _claim_store_as_retained(store: ClaimStore) -> RetainedDirectory:
    return RetainedDirectory(
        store.path,
        os.dup(store.dir_fd),
        store.identity,
        store.identity_sha256,
    )


def _consume_prepared_approval(
    invocation: Invocation,
    prepared: PreparedProbeAuthorization,
    dispatch_store: ClaimStore | None = None,
) -> dict[str, Any]:
    """Atomically burn the exact grant and return its durable consume receipt."""

    if prepared.consume_artifact is not None or prepared.anchor_artifact is not None:
        raise ProbeAuthorizationError("ApprovalGrant is already consumed")
    _reverify_retained_artifact(prepared.claim)
    _reverify_retained_artifact(prepared.grant)
    store_binding = _validated_preauthorization_stores(
        _mapping(
            prepared.binding.get("preauthorization_stores"),
            "prepared preauthorization stores",
        )
    )
    bound_invocation = replace(
        invocation, preauthorization_store_binding=store_binding
    )
    final_binding = _preauthorization_binding(bound_invocation)
    if final_binding != prepared.binding:
        raise ProbeAuthorizationError("preauthorization binding changed before consume")
    captured_now = _utc_datetime()
    claim = _validate_claim_record_v1(
        prepared.claim.record, final_binding, now=captured_now
    )
    grant = _validate_approval_grant_v1(
        prepared.grant.record, claim, final_binding,
        claim_artifact_sha256=hashlib.sha256(prepared.claim.raw).hexdigest(),
        now=captured_now,
    )
    ledger = dispatch_store or prepared.dispatch_ledger_store
    if ledger is None:
        raise ProbeAuthorizationError("dispatch ledger descriptor is unavailable")
    if ledger.identity_sha256 != store_binding["dispatch_ledger_store"]:
        raise ProbeAuthorizationError("dispatch ledger identity is mismatched")
    if (
        prepared.approval_consume_store.identity_sha256
        != store_binding["approval_consume_store"]
    ):
        raise ProbeAuthorizationError("approval consume store identity is mismatched")
    store_fd = prepared.approval_consume_store.fd
    lock_fd = -1
    temporary_fd = -1
    temporary_name: str | None = None
    try:
        try:
            lock_fd = os.open(
                ".consume.lock", _file_open_flags(os.O_RDWR), dir_fd=store_fd
            )
        except FileNotFoundError:
            try:
                lock_fd = os.open(
                    ".consume.lock",
                    _file_open_flags(os.O_RDWR | os.O_CREAT | os.O_EXCL),
                    0o600,
                    dir_fd=store_fd,
                )
                os.fsync(lock_fd)
                os.fsync(store_fd)
            except FileExistsError:
                lock_fd = os.open(
                    ".consume.lock", _file_open_flags(os.O_RDWR), dir_fd=store_fd
                )
        lock_meta = os.fstat(lock_fd)
        if (
            not stat.S_ISREG(lock_meta.st_mode)
            or stat.S_IMODE(lock_meta.st_mode) != 0o600
            or lock_meta.st_nlink != 1
        ):
            raise ProbeAuthorizationError("approval consume lock is invalid")
        if fcntl is None:
            raise ProbeAuthorizationError("approval consume requires POSIX locking")
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        final_name = f"{grant['grant_id']}.consume.json"
        anchor_name = _consume_anchor_name(grant["grant_id"])
        try:
            existing = os.stat(final_name, dir_fd=store_fd, follow_symlinks=False)
        except FileNotFoundError:
            existing = None
        if existing is not None:
            raise ProbeAuthorizationError("ApprovalGrant is already consumed")
        try:
            os.stat(anchor_name, dir_fd=ledger.dir_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ProbeAuthorizationError("ApprovalGrant is already consumed")
        consumed_at = _format_utc(captured_now)
        receipt: dict[str, Any] = {
            "schema_version": APPROVAL_CONSUME_SCHEMA_VERSION,
            "artifact_type": "ApprovalConsumeReceipt",
            "claim_id": claim["claim_id"],
            "claim_sha256": hashlib.sha256(prepared.claim.raw).hexdigest(),
            "grant_id": grant["grant_id"],
            "grant_sha256": hashlib.sha256(prepared.grant.raw).hexdigest(),
            "binding": final_binding,
            "consumed_at": consumed_at,
            "use_number": 1,
            "max_uses": 1,
            "consume_status": "consumed",
            "attestation_scope": PREAUTH_SCOPE,
            "authenticity_claimed": False,
            "retention_days": PREAUTH_RETENTION_DAYS,
            "raw_streams_retained": False,
        }
        receipt["consume_id"] = _artifact_address(receipt, "consume_id")
        receipt = _validate_consume_record_v1(receipt)
        payload = _canonical_json_bytes(receipt)
        temporary_name = f".{grant['grant_id']}.{os.urandom(8).hex()}.tmp"
        temporary_fd = os.open(
            temporary_name,
            _file_open_flags(os.O_WRONLY | os.O_CREAT | os.O_EXCL),
            0o600,
            dir_fd=store_fd,
        )
        _write_all(temporary_fd, payload)
        os.fsync(temporary_fd)
        metadata = os.fstat(temporary_fd)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o600
            or metadata.st_nlink != 1
            or metadata.st_size != len(payload)
        ):
            raise ProbeAuthorizationError("consume receipt temporary is invalid")
        os.close(temporary_fd)
        temporary_fd = -1
        try:
            os.link(
                temporary_name,
                final_name,
                src_dir_fd=store_fd,
                dst_dir_fd=store_fd,
                follow_symlinks=False,
            )
        except FileExistsError as exc:
            raise ProbeAuthorizationError("ApprovalGrant is already consumed") from exc
        os.unlink(temporary_name, dir_fd=store_fd)
        temporary_name = None
        os.fsync(store_fd)
        consume_artifact = _secure_json_artifact(
            prepared.approval_consume_store.path / final_name,
            retained_parent=prepared.approval_consume_store,
        )
        try:
            persisted_consume = _validate_consume_record_v1(
                consume_artifact.record
            )
            if persisted_consume != receipt or consume_artifact.raw != payload:
                raise ProbeAuthorizationError(
                    "durable ApprovalConsumeReceipt is mismatched"
                )
            anchor: dict[str, Any] = {
                "schema_version": 1,
                "artifact_type": "ApprovalConsumeAnchor",
                "consume_id": receipt["consume_id"],
                "claim_id": claim["claim_id"],
                "grant_id": grant["grant_id"],
                "consume_receipt_sha256": hashlib.sha256(payload).hexdigest(),
                "consumed_at": consumed_at,
                "preauthorization_stores": store_binding,
                "dispatch_identity": _claim_dispatch_identity(bound_invocation),
                "attestation_scope": PREAUTH_SCOPE,
                "authenticity_claimed": False,
                "raw_streams_retained": False,
            }
            anchor["anchor_id"] = _artifact_address(anchor, "anchor_id")
            ledger_parent = _claim_store_as_retained(ledger)
            try:
                _durable_private_json_create(
                    ledger.path / anchor_name,
                    anchor,
                    retained_parent=ledger_parent,
                )
                anchor_artifact = _secure_json_artifact(
                    ledger.path / anchor_name,
                    retained_parent=ledger_parent,
                )
            finally:
                ledger_parent.close()
            try:
                validated_anchor = _validate_consume_anchor_v1(
                    anchor_artifact.record,
                    consume=receipt,
                    consume_raw=consume_artifact.raw,
                    expected_stores=store_binding,
                    dispatch_identity=_claim_dispatch_identity(bound_invocation),
                )
                if validated_anchor != anchor:
                    raise ProbeAuthorizationError(
                        "durable approval consume anchor is mismatched"
                    )
            except BaseException:
                anchor_artifact.close()
                raise
        except BaseException:
            consume_artifact.close()
            raise
        prepared.consume_artifact = consume_artifact
        prepared.anchor_artifact = anchor_artifact
        return receipt
    finally:
        if temporary_fd >= 0:
            os.close(temporary_fd)
        if temporary_name is not None:
            try:
                os.unlink(temporary_name, dir_fd=store_fd)
            except OSError:
                pass
        if lock_fd >= 0:
            try:
                if fcntl is not None:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
            finally:
                os.close(lock_fd)
        # The consume-store descriptor remains retained through provider spawn.


def compact_approval_consume_tombstone(
    store_path: str | os.PathLike[str],
    grant_id: str,
    *,
    invocation: Invocation | None = None,
) -> dict[str, Any]:
    """Manually compact 90-day-old consume metadata to an indefinite tombstone."""

    if not re.fullmatch(r"[a-f0-9]{64}", grant_id):
        raise ProbeAuthorizationError("grant id is invalid")
    if invocation is None:
        raise ProbeAuthorizationError(
            "consume compaction requires its bound dispatch ledger"
        )
    consume_store = _open_retained_private_directory(
        store_path, "approval consume store"
    )
    try:
        dispatch_store = _coerce_claim_store(
            _secure_claim_directory(invocation), invocation
        )
    except BaseException:
        consume_store.close()
        raise
    store_fd = consume_store.fd
    lock_fd = -1
    original_fd = -1
    temporary_fd = -1
    temporary_name: str | None = None
    try:
        lock_fd = os.open(
            ".consume.lock", _file_open_flags(os.O_RDWR), dir_fd=store_fd
        )
        lock_metadata = os.fstat(lock_fd)
        if (
            not stat.S_ISREG(lock_metadata.st_mode)
            or stat.S_IMODE(lock_metadata.st_mode) != 0o600
            or lock_metadata.st_nlink != 1
        ):
            raise ProbeAuthorizationError("approval consume lock is invalid")
        if fcntl is None:
            raise ProbeAuthorizationError("consume compaction requires POSIX locking")
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        final_name = f"{grant_id}.consume.json"
        original_fd = os.open(final_name, _file_open_flags(os.O_RDONLY), dir_fd=store_fd)
        metadata = os.fstat(original_fd)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or stat.S_IMODE(metadata.st_mode) != 0o600
        ):
            raise ProbeAuthorizationError("consume receipt is unsafe")
        raw = _bounded_read_fd(original_fd)
        try:
            record = _strict_json_loads(raw)
        except _StrictJSONError as exc:
            raise ProbeAuthorizationError("consume receipt is invalid") from exc
        if not isinstance(record, Mapping):
            raise ProbeAuthorizationError("consume receipt is invalid")
        if record.get("artifact_type") == "ApprovalConsumeTombstone":
            raise ProbeAuthorizationError("consume receipt is already compacted")
        record = _validate_consume_record_v1(record)
        if record.get("grant_id") != grant_id:
            raise ProbeAuthorizationError("consume receipt binding is invalid")
        binding = _mapping(record.get("binding"), "consume receipt binding")
        stores = _validated_preauthorization_stores(
            _mapping(
                binding.get("preauthorization_stores"),
                "consume receipt stores",
            )
        )
        if (
            stores["approval_consume_store"] != consume_store.identity_sha256
            or stores["dispatch_ledger_store"] != dispatch_store.identity_sha256
        ):
            raise ProbeAuthorizationError("consume receipt store identity is invalid")
        ledger_parent = _claim_store_as_retained(dispatch_store)
        try:
            anchor_artifact = _secure_json_artifact(
                dispatch_store.path / _consume_anchor_name(grant_id),
                retained_parent=ledger_parent,
            )
        finally:
            ledger_parent.close()
        try:
            anchor = _validate_consume_anchor_v1(
                anchor_artifact.record,
                consume=record,
                consume_raw=raw,
                expected_stores=stores,
                dispatch_identity=_required_string(
                    binding.get("dispatch_identity"),
                    "consume dispatch identity",
                ),
            )
            anchor_sha256 = hashlib.sha256(anchor_artifact.raw).hexdigest()
        finally:
            anchor_artifact.close()
        consumed = _parse_utc_timestamp(record.get("consumed_at"), "consumed_at")
        compacted_time = _utc_datetime()
        compacted = _format_utc(compacted_time)
        if compacted_time < consumed + timedelta(days=PREAUTH_RETENTION_DAYS):
            raise ProbeAuthorizationError("consume receipt is not eligible for compaction")
        tombstone: dict[str, Any] = {
            "schema_version": 1,
            "artifact_type": "ApprovalConsumeTombstone",
            "consume_id": record.get("consume_id"),
            "grant_id": grant_id,
            "original_receipt_sha256": hashlib.sha256(raw).hexdigest(),
            "consume_anchor_id": anchor["anchor_id"],
            "consume_anchor_sha256": anchor_sha256,
            "consumed_at": record["consumed_at"],
            "compacted_at": compacted,
            "anti_replay": True,
            "retention": "indefinite",
            "attestation_scope": PREAUTH_SCOPE,
            "authenticity_claimed": False,
            "raw_streams_retained": False,
        }
        tombstone = _validate_consume_record_v1(tombstone)
        payload = _canonical_json_bytes(tombstone)
        temporary_name = f".{grant_id}.{os.urandom(8).hex()}.compact.tmp"
        temporary_fd = os.open(
            temporary_name,
            _file_open_flags(os.O_WRONLY | os.O_CREAT | os.O_EXCL),
            0o600,
            dir_fd=store_fd,
        )
        _write_all(temporary_fd, payload)
        os.fsync(temporary_fd)
        os.close(temporary_fd)
        temporary_fd = -1
        current = os.stat(final_name, dir_fd=store_fd, follow_symlinks=False)
        if (current.st_dev, current.st_ino) != (metadata.st_dev, metadata.st_ino):
            raise ProbeAuthorizationError("consume receipt changed before compaction")
        os.rename(
            temporary_name, final_name,
            src_dir_fd=store_fd, dst_dir_fd=store_fd,
        )
        temporary_name = None
        os.fsync(store_fd)
        persisted = _secure_json_artifact(
            consume_store.path / final_name,
            retained_parent=consume_store,
        )
        try:
            if (
                _validate_consume_record_v1(persisted.record) != tombstone
                or persisted.raw != payload
            ):
                raise ProbeAuthorizationError(
                    "compacted consume tombstone is mismatched"
                )
        finally:
            persisted.close()
        return tombstone
    finally:
        if original_fd >= 0:
            os.close(original_fd)
        if temporary_fd >= 0:
            os.close(temporary_fd)
        if temporary_name is not None:
            try:
                os.unlink(temporary_name, dir_fd=store_fd)
            except OSError:
                pass
        if lock_fd >= 0:
            try:
                if fcntl is not None:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
            finally:
                os.close(lock_fd)
        dispatch_store.close()
        consume_store.close()


def _run_provider_process(
    argv: Sequence[str],
    *,
    cwd: str,
    env: Mapping[str, str],
    input: str,
    provider: str | None = None,
    timeout: float = MAX_PROVIDER_RUNTIME_SECONDS,
    **_unused: Any,
) -> subprocess.CompletedProcess[str]:
    """Capture provider channels with bounds and terminate the owned group on failure."""

    # Defense in depth at the last local process-creation boundary. The
    # invocation executor supplies the selected provider; a runtime config,
    # acknowledgement, or same-principal approval artifact cannot bypass it.
    _validate_transport_provider_binding(provider, argv)
    if timeout <= 0:
        raise ConfigurationError("provider timeout must be positive")
    try:
        prompt_bytes = input.encode("utf-8")
    except UnicodeError as exc:
        raise ConfigurationError("provider prompt is not UTF-8") from exc
    process = subprocess.Popen(
        list(argv), cwd=cwd, env=dict(env), stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False, shell=False,
        start_new_session=True,
    )
    stdout_buffer = bytearray()
    stderr_buffer = bytearray()
    stop = threading.Event()
    oversize = threading.Event()
    reader_error = threading.Event()

    def read_channel(stream: Any, destination: bytearray) -> None:
        try:
            while True:
                chunk = os.read(stream.fileno(), 65_536)
                if not chunk:
                    break
                remaining = MAX_PROVIDER_OUTPUT_BYTES + 1 - len(destination)
                if remaining > 0:
                    destination.extend(chunk[:remaining])
                if len(destination) > MAX_PROVIDER_OUTPUT_BYTES:
                    oversize.set()
                    stop.set()
                    break
        except BaseException:
            reader_error.set()
            stop.set()
        finally:
            try:
                stream.close()
            except OSError:
                pass

    def write_prompt() -> None:
        stream = process.stdin
        if stream is None:
            reader_error.set()
            stop.set()
            return
        try:
            stream.write(prompt_bytes)
            stream.flush()
        except BrokenPipeError:
            pass
        except BaseException:
            reader_error.set()
            stop.set()
        finally:
            try:
                stream.close()
            except OSError:
                pass

    if process.stdout is None or process.stderr is None:
        _terminate_owned_process_group(process)
        raise ConfigurationError("provider transport pipes are unavailable")
    threads = [
        threading.Thread(target=read_channel, args=(process.stdout, stdout_buffer), daemon=True),
        threading.Thread(target=read_channel, args=(process.stderr, stderr_buffer), daemon=True),
        threading.Thread(target=write_prompt, daemon=True),
    ]
    for thread in threads:
        thread.start()
    deadline = time.monotonic() + timeout
    failure_reason: str | None = None
    try:
        while process.poll() is None:
            if oversize.is_set():
                failure_reason = "provider output exceeded its safe byte limit"
                break
            if reader_error.is_set():
                failure_reason = "provider transport channel failed"
                break
            if time.monotonic() >= deadline:
                failure_reason = "provider execution exceeded its time limit"
                break
            stop.wait(0.05)
        if failure_reason is None and oversize.is_set():
            failure_reason = "provider output exceeded its safe byte limit"
        if failure_reason is None and reader_error.is_set():
            failure_reason = "provider transport channel failed"
        if failure_reason is not None:
            _terminate_owned_process_group(process)
        else:
            process.wait()
        for thread in threads:
            thread.join(timeout=PROCESS_GROUP_TERMINATE_SECONDS)
        if any(thread.is_alive() for thread in threads):
            _terminate_owned_process_group(process)
            failure_reason = failure_reason or "provider transport thread did not terminate"
        if failure_reason is not None:
            raise ProviderParseError("terminal_shape", failure_reason)
        try:
            stdout = bytes(stdout_buffer).decode("utf-8")
            stderr = bytes(stderr_buffer).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ProviderParseError(
                "terminal_shape", "provider transport channel is not UTF-8"
            ) from exc
        return subprocess.CompletedProcess(list(argv), process.returncode, stdout, stderr)
    except BaseException:
        _terminate_owned_process_group(process)
        for thread in threads:
            thread.join(timeout=PROCESS_GROUP_TERMINATE_SECONDS)
        raise


def _execute_invocation_locked(invocation: Invocation) -> subprocess.CompletedProcess[str]:
    """Revalidate governance, then execute argv with no shell."""

    # DSG-009A/009B are external prerequisites. This repository-local denial
    # is defense in depth only and deliberately runs before all executable
    # preflight, approval consumption, dispatch-ledger mutation, and Popen.
    _validate_invocation_provider_binding(invocation)
    validated_decision = _validated_invocation_decision(invocation)
    _validate_qobs_invocation_binding(invocation)
    validate_execution_preflight(invocation)
    home_fd, home_identity = _open_isolated_account_home(invocation)
    try:
        env = os.environ.copy()
        env.pop("CODEX_HOME", None)
        env.pop("AGY_HOME", None)
        env.update(invocation.env_overrides)
        if not invocation.work_result_schema_path:
            raise ConfigurationError("executable dispatch requires a WorkResult v2 output schema")
        provider_schema = _provider_compatible_work_result_schema(
            invocation.work_result_schema_path
        )
        schema_flag = "--output-schema" if invocation.route.cli == "codex" else "--json-schema"
        argv = list(invocation.argv)
        if argv.count(schema_flag) != 1:
            raise ConfigurationError("provider output schema flag is missing or ambiguous")
        schema_index = argv.index(schema_flag) + 1
        if (
            schema_index >= len(argv)
            or argv[schema_index] != invocation.work_result_schema_path
        ):
            raise ConfigurationError("provider output schema path is not bound to the invocation")
        with tempfile.TemporaryDirectory(prefix="horo-provider-schema-") as temp_dir:
            private_directory = Path(temp_dir)
            private_directory.chmod(0o700)
            provider_schema_path = private_directory / "work-result-v2.provider.json"
            provider_schema_path.write_text(
                json.dumps(provider_schema, ensure_ascii=True, separators=(",", ":")),
                encoding="utf-8",
            )
            provider_schema_path.chmod(0o600)
            argv[schema_index] = str(provider_schema_path)
            final_path: Path | None = None
            final_identity: tuple[int, int] | None = None
            if invocation.route.cli == "codex":
                if argv[-1:] != ["-"] or any(
                    flag in argv for flag in ("-o", "--output-last-message")
                ):
                    raise ConfigurationError("Codex final output channel is ambiguous")
                final_path, final_identity = _create_private_final_file(private_directory)
                argv[-1:-1] = ["--output-last-message", str(final_path)]
            # This is the final executable dispatch boundary. Re-evaluate Rule 11
            # after every other preflight and immediately before process creation.
            _validated_invocation_schedule(invocation, validated_decision)
            prepared_approval = _prepare_probe_authorization(invocation)
            try:
                bound_invocation = replace(
                    invocation,
                    preauthorization_store_binding=_validated_preauthorization_stores(
                        _mapping(
                            prepared_approval.binding.get(
                                "preauthorization_stores"
                            ),
                            "prepared preauthorization stores",
                        )
                    ),
                )
                claim = _acquire_dispatch_claim(
                    bound_invocation, prepared_approval.take_dispatch_ledger()
                )
                try:
                    _verify_dispatch_claim(claim, require_start_freshness=True)
                    _verify_isolated_account_home(invocation, home_fd, home_identity)
                    # The consume receipt and its dispatch-ledger anchor are the
                    # final irreversible operation before provider creation.
                    consume_receipt = _consume_prepared_approval(
                        bound_invocation, prepared_approval, claim.store
                    )
                    result = _run_provider_process(
                        argv,
                        cwd=invocation.cwd,
                        env=env,
                        input=invocation.prompt_stdin,
                        provider=invocation.route.cli,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=False,
                        shell=False,
                        timeout=MAX_PROVIDER_RUNTIME_SECONDS,
                    )
                    result._approval_consume_receipt = consume_receipt  # type: ignore[attr-defined]
                    result._probe_claim_record = dict(prepared_approval.claim.record)  # type: ignore[attr-defined]
                    result._approval_grant_record = dict(prepared_approval.grant.record)  # type: ignore[attr-defined]
                    result._probe_claim_sha256 = hashlib.sha256(  # type: ignore[attr-defined]
                        prepared_approval.claim.raw
                    ).hexdigest()
                    result._approval_grant_sha256 = hashlib.sha256(  # type: ignore[attr-defined]
                        prepared_approval.grant.raw
                    ).hexdigest()
                    if (
                        prepared_approval.consume_artifact is None
                        or prepared_approval.anchor_artifact is None
                    ):
                        raise ProbeAuthorizationError(
                            "retained consume evidence is missing"
                        )
                    _reverify_retained_artifact(
                        prepared_approval.consume_artifact
                    )
                    _reverify_retained_artifact(
                        prepared_approval.anchor_artifact
                    )
                    result._approval_consume_raw_sha256 = hashlib.sha256(  # type: ignore[attr-defined]
                        prepared_approval.consume_artifact.raw
                    ).hexdigest()
                    result._approval_consume_anchor_record = dict(  # type: ignore[attr-defined]
                        prepared_approval.anchor_artifact.record
                    )
                    result._approval_consume_anchor_sha256 = hashlib.sha256(  # type: ignore[attr-defined]
                        prepared_approval.anchor_artifact.raw
                    ).hexdigest()
                    result._bound_invocation = bound_invocation  # type: ignore[attr-defined]
                except BaseException:
                    try:
                        _finalize_dispatch_claim(claim, "unknown")
                    finally:
                        _release_dispatch_claim(claim)
                    raise
            finally:
                prepared_approval.close()
            try:
                stdout_bytes = _validated_text_channel(result.stdout, "provider stdout")
                stderr_bytes = _validated_text_channel(result.stderr, "provider stderr")
                if invocation.route.cli == "codex":
                    if final_path is None or final_identity is None:
                        raise ConfigurationError("Codex private final channel was not initialized")
                    private_final = _read_private_final_file(final_path, final_identity)
                    result._private_final_result = private_final  # type: ignore[attr-defined]
                    result._private_final_bytes = private_final.byte_count  # type: ignore[attr-defined]
                    result._private_final_sha256 = private_final.sha256  # type: ignore[attr-defined]
                    result._private_final_work_result_sha256 = _canonical_sha256(  # type: ignore[attr-defined]
                        private_final.work_result
                    )
                result._stdout_bytes = len(stdout_bytes)  # type: ignore[attr-defined]
                result._stdout_sha256 = hashlib.sha256(stdout_bytes).hexdigest()  # type: ignore[attr-defined]
                result._stderr_bytes = len(stderr_bytes)  # type: ignore[attr-defined]
                result._stderr_sha256 = hashlib.sha256(stderr_bytes).hexdigest()  # type: ignore[attr-defined]
                result._sanitized_argv = tuple(  # type: ignore[attr-defined]
                    "<WORK_RESULT_SCHEMA>" if item == str(provider_schema_path) else
                    "<PRIVATE_FINAL_OUTPUT>" if final_path is not None and item == str(final_path) else
                    _redact_preview(item, invocation)
                    for item in argv
                )
                result._sanitized_argv_sha256 = hashlib.sha256(  # type: ignore[attr-defined]
                    json.dumps(
                        result._sanitized_argv,  # type: ignore[attr-defined]
                        ensure_ascii=True,
                        separators=(",", ":"),
                    ).encode("ascii")
                ).hexdigest()
            except BaseException:
                try:
                    _finalize_dispatch_claim(claim, "unknown")
                finally:
                    _release_dispatch_claim(claim)
                raise
            finally:
                _release_spawn_capacity(invocation, consumed_lease)
            result._dispatch_claim = claim  # type: ignore[attr-defined]
            result._dispatch_started_at = claim.record["started_at"]  # type: ignore[attr-defined]
            result._dispatch_ended_at = _utc_now()  # type: ignore[attr-defined]
            return result
    finally:
        os.close(home_fd)


def _redact_preview(value: str, invocation: Invocation) -> str:
    """Redact local paths from dry-run output while retaining argv structure."""

    redacted = value.replace(invocation.cwd, "<PROJECT_DIR>")
    for path in invocation.env_overrides.values():
        redacted = redacted.replace(path, "<CLI_HOME>")
    if invocation.work_result_schema_path:
        redacted = redacted.replace(invocation.work_result_schema_path, "<WORK_RESULT_SCHEMA>")
    return _redact_personal_text(redacted)


def _canonical_blocked_result(
    route: Route,
    *,
    failure_class: str,
    recommended_next_action: str,
    invocation: Invocation | None = None,
    provider_parse_reason: str | None = None,
    final_message_cardinality_subreason: str | None = None,
    candidate_count: int | None = None,
) -> dict[str, Any]:
    """Create a safe canonical record for a failed preflight/start attempt."""

    if provider_parse_reason is not None and provider_parse_reason not in PROVIDER_PARSE_REASONS:
        raise ValueError("unsupported provider parse reason")
    _validate_final_message_cardinality_telemetry(
        provider_parse_reason,
        final_message_cardinality_subreason,
        candidate_count,
    )
    child_ran = provider_parse_reason is not None
    execution_evidence: dict[str, str | int] = {
        "source": "child-ran-invalid-result-contract" if child_ran else "no-child-ran",
        "failure_class": failure_class,
    }
    if provider_parse_reason is not None:
        execution_evidence["provider_parse_reason"] = provider_parse_reason
    if final_message_cardinality_subreason is not None:
        execution_evidence["final_message_cardinality_subreason"] = (
            final_message_cardinality_subreason
        )
    if candidate_count is not None:
        execution_evidence["candidate_count"] = candidate_count
    blocked = {
        "status": status,
        "alias": route.alias,
        "execution_evidence": execution_evidence,
        "scope_owned": "configured terminal dispatch",
        "evidence": {
            "commands": [],
            "outcomes": [
                "child result was rejected before a receipt could be issued"
                if child_ran
                else "configured child process did not start"
            ],
            "artifacts": [],
        },
        "findings": [
            "No validated child result is available."
            if child_ran
            else "No actual child run is claimed."
        ],
        "changed_files": [],
        "residual_risk": (
            "the selected account alias returned an invalid result contract"
            if child_ran
            else "the selected account alias could not execute the bounded task"
        ),
        "recommended_next_action": recommended_next_action,
    }
    if invocation is not None and invocation.decision is not None:
        blocked["dispatch_binding"] = _dispatch_binding(invocation)
    return blocked


def _dispatch_binding(invocation: Invocation) -> dict[str, Any]:
    """Return policy-bound route intent; this is not an ExecutionReceipt."""

    if invocation.decision is None or invocation.decision_digest is None:
        raise DispatchDecisionError("cannot create a receipt without a DispatchDecision")
    ranks = [
        invocation.decision[field]
        for field in (
            "scope_rank",
            "complexity_rank",
            "risk_rank",
            "ambiguity_rank",
            "evidence_burden_rank",
        )
    ]
    binding = {
        "schema_version": 1,
        "policy_version": invocation.decision["policy_version"],
        "decision_sha256": invocation.decision_digest,
        "dispatch_identity": _dispatch_key(invocation),
        "ticket": invocation.decision["ticket"],
        "phase": invocation.decision["phase"],
        "quality_floor": max(ranks),
        "alias": invocation.route.alias,
        "model": invocation.route.model,
        "effort": invocation.route.effort,
        "attempt_id": invocation.attempt_id,
    }
    if invocation.scheduling_snapshot_digest is not None:
        binding["scheduling_snapshot_sha256"] = invocation.scheduling_snapshot_digest
    return binding


def _raw_output_bytes(result: subprocess.CompletedProcess[str]) -> bytes:
    stdout = result.stdout or ""
    return stdout if isinstance(stdout, bytes) else stdout.encode("utf-8")


def _completed_result_claim(
    result: subprocess.CompletedProcess[str] | None,
) -> tuple[DispatchClaim, str]:
    claim = getattr(result, "_dispatch_claim", None)
    proof = getattr(result, "_dispatch_claim_sha256", None)
    if not isinstance(claim, DispatchClaim) or claim.closed:
        raise ConfigurationError("completed dispatch claim proof is required")
    _verify_dispatch_claim(claim)
    if claim.record.get("state") != "completed":
        raise ConfigurationError("dispatch claim is not completed")
    expected = _canonical_sha256(claim.record)
    if proof != expected:
        raise ConfigurationError("dispatch claim proof digest is invalid")
    return claim, expected


def _validate_completed_claim_binding(
    claim: DispatchClaim,
    invocation: Invocation,
    result: subprocess.CompletedProcess[str],
    provider_result: ProviderResult,
) -> None:
    """Require persisted terminal proof for every receipt-bound observation."""

    output = _raw_output_bytes(result)
    ownership_key = _load_ownership_key(claim.store)
    exact_tokens, ancestor_tokens = _ownership_token_set(
        invocation.ownership, ownership_key
    )
    expected = {
        "claim_key": _dispatch_claim_key(invocation),
        "decision_sha256": invocation.decision_digest,
        "scheduling_snapshot_sha256": invocation.scheduling_snapshot_digest,
        "dispatch_identity": _claim_dispatch_identity(invocation),
        "ticket_sha256": hashlib.sha256(
            str(invocation.decision["ticket"] if invocation.decision else "missing").encode("ascii")
        ).hexdigest(),
        "route_sha256": _canonical_sha256(
            {
                "role": invocation.route.role,
                "alias": invocation.route.alias,
                "provider": invocation.route.cli,
                "model": invocation.route.model,
                "effort": invocation.route.effort,
            }
        ),
        "ownership_tokens_sha256": _ownership_tokens_digest(exact_tokens, ancestor_tokens),
        "ownership_key_id": hashlib.sha256(ownership_key).hexdigest(),
        "state": "completed",
        "transport_status": "completed",
        "exit_code": result.returncode,
        "output_bytes": len(output),
        "output_sha256": hashlib.sha256(output).hexdigest(),
        "work_result_sha256": _canonical_sha256(provider_result.work_result),
    }
    for field, value in expected.items():
        if claim.record.get(field) != value:
            raise ConfigurationError(
                f"completed dispatch claim {field} does not match receipt evidence"
            )
    started = _parse_utc_timestamp(claim.record.get("started_at"), "dispatch claim started_at")
    ended = _parse_utc_timestamp(claim.record.get("ended_at"), "dispatch claim ended_at")
    if ended < started:
        raise ConfigurationError("completed dispatch claim timestamps are invalid")


def _embedded_claim_proof(record: Mapping[str, Any]) -> dict[str, Any]:
    proof = {
        "schema_version": 1,
        "claim_key": record["claim_key"],
        "decision_sha256": record["decision_sha256"],
        "scheduling_snapshot_sha256": record["scheduling_snapshot_sha256"],
        "dispatch_identity": record["dispatch_identity"],
        "ticket_sha256": record["ticket_sha256"],
        "route_sha256": record["route_sha256"],
        "ownership_tokens_sha256": record["ownership_tokens_sha256"],
        "ownership_key_id": record["ownership_key_id"],
        "started_at": record["started_at"],
        "ended_at": record["ended_at"],
        "transport_status": record["transport_status"],
        "exit_code": record["exit_code"],
        "output_bytes": record["output_bytes"],
        "output_sha256": record["output_sha256"],
        "work_result_sha256": record["work_result_sha256"],
        "terminal_state": record["state"],
    }
    if set(proof) != CLAIM_PROOF_FIELDS:
        raise ConfigurationError("embedded ClaimProof fields are invalid")
    return proof


def _build_execution_receipt(
    invocation: Invocation,
    result: subprocess.CompletedProcess[str],
    provider_result: ProviderResult,
    *,
    started_at: str,
    ended_at: str,
) -> dict[str, Any]:
    """Build receipt data from trusted dispatch and adapter observations."""

    if invocation.decision is None or invocation.decision_digest is None:
        raise DispatchDecisionError("cannot create an ExecutionReceipt without a DispatchDecision")
    claim, claim_proof = _completed_result_claim(result)
    _validate_completed_claim_binding(claim, invocation, result, provider_result)
    embedded_proof = _embedded_claim_proof(claim.record)
    embedded_digest = _canonical_sha256(embedded_proof)
    output = _raw_output_bytes(result)
    probe_claim = getattr(result, "_probe_claim_record", None)
    approval_grant = getattr(result, "_approval_grant_record", None)
    consume_receipt = getattr(result, "_approval_consume_receipt", None)
    consume_anchor = getattr(result, "_approval_consume_anchor_record", None)
    if not all(isinstance(item, Mapping) for item in (
        probe_claim, approval_grant, consume_receipt, consume_anchor
    )):
        raise ProbeAuthorizationError("preauthorization execution evidence is missing")
    stores = _validated_preauthorization_stores(
        _mapping(
            invocation.preauthorization_store_binding,
            "execution preauthorization stores",
        )
    )
    receipt: dict[str, Any] = {
        "receipt_schema_version": EXECUTION_RECEIPT_SCHEMA_VERSION,
        "protocol_version": RESULT_PROTOCOL_VERSION,
        "policy_version": invocation.decision["policy_version"],
        "decision_sha256": invocation.decision_digest,
        "dispatch_claim_key": claim.key,
        "dispatch_claim_sha256": embedded_digest,
        "claim_proof": embedded_proof,
        "claim_proof_sha256": embedded_digest,
        "claim_proof_scope": "digest-integrity-not-authenticity",
        "dispatch_identity": _claim_dispatch_identity(invocation),
        "dispatch_ticket_id": invocation.decision["ticket"],
        "attempt_id": invocation.attempt_id,
        "alias": invocation.route.alias,
        "provider": invocation.route.cli,
        "adapter": provider_result.adapter,
        "model": invocation.route.model,
        "effort": invocation.route.effort,
        "objective": _redact_personal_text(invocation.objective),
        "ownership": _redact_personal_text(invocation.ownership),
        "quota_status": invocation.decision["quota_band"],
        "started_at": claim.record["started_at"],
        "ended_at": claim.record["ended_at"],
        "exit_code": result.returncode,
        "transport_status": "completed",
        "output_bytes": len(output),
        "output_sha256": hashlib.sha256(output).hexdigest(),
        "work_result_sha256": _canonical_sha256(provider_result.work_result),
        "probe_claim_id": probe_claim["claim_id"],
        "probe_claim_sha256": getattr(result, "_probe_claim_sha256", None),
        "approval_grant_id": approval_grant["grant_id"],
        "approval_grant_sha256": getattr(result, "_approval_grant_sha256", None),
        "approval_consume_receipt_id": consume_receipt["consume_id"],
        "approval_consume_receipt_sha256": getattr(
            result, "_approval_consume_raw_sha256", None
        ),
        "approval_consume_anchor_id": consume_anchor["anchor_id"],
        "approval_consume_anchor_sha256": getattr(
            result, "_approval_consume_anchor_sha256", None
        ),
        "preauthorization_stores": stores,
        "preauthorization_scope": PREAUTH_SCOPE,
    }
    if invocation.scheduling_snapshot_digest is not None:
        receipt["scheduling_snapshot_sha256"] = invocation.scheduling_snapshot_digest
    if provider_result.process_or_session_id:
        receipt["process_or_session_id"] = provider_result.process_or_session_id
    return receipt


def _validate_receipt_v3_preauthorization(
    receipt: Mapping[str, Any], invocation: Invocation
) -> None:
    """Bind Receipt v3 to the persisted exact claim, grant, and consume record."""

    if not all((invocation.probe_claim_path, invocation.approval_grant_path,
                invocation.approval_store_path, invocation.approval_session_id)):
        raise ConfigurationError("Receipt v3 requires strict local preauthorization evidence")
    prepared = _prepare_probe_authorization(
        invocation, enforce_fresh=False, reject_consumed=False
    )
    try:
        claim = prepared.claim.record
        grant = prepared.grant.record
        stores = _validated_preauthorization_stores(
            _mapping(
                prepared.binding.get("preauthorization_stores"),
                "prepared preauthorization stores",
            )
        )
        expected = {
            "receipt_schema_version": EXECUTION_RECEIPT_SCHEMA_VERSION,
            "probe_claim_id": claim["claim_id"],
            "probe_claim_sha256": hashlib.sha256(prepared.claim.raw).hexdigest(),
            "approval_grant_id": grant["grant_id"],
            "approval_grant_sha256": hashlib.sha256(prepared.grant.raw).hexdigest(),
            "preauthorization_stores": stores,
            "preauthorization_scope": PREAUTH_SCOPE,
        }
        for field, value in expected.items():
            if receipt.get(field) != value:
                raise ConfigurationError(f"ExecutionReceipt {field} is mismatched")
        consume_path = (
            prepared.approval_consume_store.path
            / f"{grant['grant_id']}.consume.json"
        )
        consume_artifact = _secure_json_artifact(
            consume_path,
            retained_parent=prepared.approval_consume_store,
        )
        try:
            try:
                consume = _validate_consume_record_v1(
                    consume_artifact.record
                )
            except ProbeAuthorizationError as exc:
                raise ConfigurationError(
                    "persisted approval consume record is invalid"
                ) from exc
            ledger = prepared.dispatch_ledger_store
            if ledger is None:
                raise ConfigurationError("dispatch ledger evidence is unavailable")
            ledger_parent = _claim_store_as_retained(ledger)
            try:
                anchor_artifact = _secure_json_artifact(
                    ledger.path / _consume_anchor_name(grant["grant_id"]),
                    retained_parent=ledger_parent,
                )
            finally:
                ledger_parent.close()
            try:
                anchor = anchor_artifact.record
                if consume.get("artifact_type") == "ApprovalConsumeTombstone":
                    if (
                        consume.get("grant_id") != grant["grant_id"]
                        or consume.get("consume_id")
                        != receipt.get("approval_consume_receipt_id")
                        or consume.get("original_receipt_sha256")
                        != receipt.get("approval_consume_receipt_sha256")
                        or consume.get("consume_anchor_id")
                        != receipt.get("approval_consume_anchor_id")
                        or consume.get("consume_anchor_sha256")
                        != receipt.get("approval_consume_anchor_sha256")
                    ):
                        raise ConfigurationError(
                            "ApprovalConsumeTombstone receipt binding is invalid"
                        )
                    if set(anchor) != CONSUME_ANCHOR_FIELDS:
                        raise ConfigurationError(
                            "ApprovalConsumeAnchor fields are invalid"
                        )
                    anchor_expected = {
                        "schema_version": 1,
                        "artifact_type": "ApprovalConsumeAnchor",
                        "anchor_id": consume["consume_anchor_id"],
                        "consume_id": consume["consume_id"],
                        "grant_id": grant["grant_id"],
                        "consume_receipt_sha256": consume[
                            "original_receipt_sha256"
                        ],
                        "consumed_at": consume["consumed_at"],
                        "preauthorization_stores": stores,
                        "dispatch_identity": prepared.binding[
                            "dispatch_identity"
                        ],
                        "attestation_scope": PREAUTH_SCOPE,
                        "authenticity_claimed": False,
                        "raw_streams_retained": False,
                    }
                    for field, value in anchor_expected.items():
                        if anchor.get(field) != value:
                            raise ConfigurationError(
                                "ApprovalConsumeAnchor tombstone binding is invalid"
                            )
                    if anchor.get("claim_id") != claim["claim_id"]:
                        raise ConfigurationError(
                            "ApprovalConsumeAnchor claim binding is invalid"
                        )
                    if anchor.get("anchor_id") != _artifact_address(
                        anchor, "anchor_id"
                    ):
                        raise ConfigurationError(
                            "ApprovalConsumeAnchor address is invalid"
                        )
                else:
                    if (
                        consume.get("claim_id") != claim["claim_id"]
                        or consume.get("claim_sha256")
                        != expected["probe_claim_sha256"]
                        or consume.get("grant_id") != grant["grant_id"]
                        or consume.get("grant_sha256")
                        != expected["approval_grant_sha256"]
                        or consume.get("binding") != prepared.binding
                    ):
                        raise ConfigurationError(
                            "ApprovalConsumeReceipt binding is invalid"
                        )
                    consumed_at = _parse_utc_timestamp(
                        consume.get("consumed_at"), "consumed_at"
                    )
                    claim_created = _parse_utc_timestamp(
                        claim.get("created_at"), "ProbeClaim created_at"
                    )
                    claim_expires = _parse_utc_timestamp(
                        claim.get("expires_at"), "ProbeClaim expires_at"
                    )
                    grant_created = _parse_utc_timestamp(
                        grant.get("created_at"), "ApprovalGrant created_at"
                    )
                    grant_expires = _parse_utc_timestamp(
                        grant.get("expires_at"), "ApprovalGrant expires_at"
                    )
                    if not (
                        claim_created <= consumed_at < claim_expires
                        and grant_created <= consumed_at < grant_expires
                    ):
                        raise ConfigurationError(
                            "ApprovalConsumeReceipt timestamp is unanchored"
                        )
                    try:
                        _validate_consume_anchor_v1(
                            anchor,
                            consume=consume,
                            consume_raw=consume_artifact.raw,
                            expected_stores=stores,
                            dispatch_identity=prepared.binding[
                                "dispatch_identity"
                            ],
                        )
                    except ProbeAuthorizationError as exc:
                        raise ConfigurationError(
                            "ApprovalConsumeAnchor binding is invalid"
                        ) from exc
                    if (
                        receipt.get("approval_consume_receipt_id")
                        != consume["consume_id"]
                        or receipt.get("approval_consume_receipt_sha256")
                        != hashlib.sha256(consume_artifact.raw).hexdigest()
                        or receipt.get("approval_consume_anchor_id")
                        != anchor["anchor_id"]
                        or receipt.get("approval_consume_anchor_sha256")
                        != hashlib.sha256(anchor_artifact.raw).hexdigest()
                    ):
                        raise ConfigurationError(
                            "ExecutionReceipt consume evidence is mismatched"
                        )
                if (
                    receipt.get("approval_consume_anchor_sha256")
                    != hashlib.sha256(anchor_artifact.raw).hexdigest()
                ):
                    raise ConfigurationError(
                        "ExecutionReceipt consume anchor digest is mismatched"
                    )
            finally:
                anchor_artifact.close()
        finally:
            consume_artifact.close()
    finally:
        prepared.close()


def _raise_for_migrated_legacy_receipt(
    receipt: Mapping[str, Any], invocation: Invocation
) -> None:
    """Classify only locally anchored v1 receipts that privacy migration retired."""

    proof_fields = {"claim_proof", "claim_proof_sha256", "claim_proof_scope"}
    if proof_fields & set(receipt):
        return
    claim_key = receipt.get("dispatch_claim_key")
    legacy_digest = receipt.get("dispatch_claim_sha256")
    if (
        not isinstance(claim_key, str)
        or not re.fullmatch(r"[a-f0-9]{64}", claim_key)
        or claim_key != _dispatch_claim_key(invocation)
        or not isinstance(legacy_digest, str)
        or not re.fullmatch(r"[a-f0-9]{64}", legacy_digest)
    ):
        return
    try:
        local = _optional_local_claim(invocation, claim_key)
    except (OSError, SchedulingError):
        return
    if (
        local is not None
        and local.get("version") == DISPATCH_CLAIM_VERSION
        and local.get("claim_key") == claim_key
        and local.get("state") == "completed"
        and local.get("legacy_claim_sha256") == legacy_digest
    ):
        raise LegacyReceiptRevalidationUnsupported()


def validate_execution_receipt(
    receipt: Mapping[str, Any],
    work_result: Mapping[str, Any],
    invocation: Invocation,
    raw_output: str | bytes | None,
    *,
    result: subprocess.CompletedProcess[str] | None = None,
    portable: bool = False,
) -> dict[str, Any]:
    """Validate frozen v2 or strict locally anchored preauthorization receipt v3."""

    receipt = _mapping(receipt, "ExecutionReceipt")
    _raise_for_migrated_legacy_receipt(receipt, invocation)
    optional_fields = {"process_or_session_id", "scheduling_snapshot_sha256"}
    is_v3 = receipt.get("receipt_schema_version") == EXECUTION_RECEIPT_SCHEMA_VERSION
    if is_v3 and invocation.preauthorization_store_binding is None:
        invocation = _bind_invocation_to_current_stores(invocation)
    required_fields = EXECUTION_RECEIPT_V3_FIELDS if is_v3 else EXECUTION_RECEIPT_FIELDS
    missing = required_fields - set(receipt)
    unknown = set(receipt) - required_fields - optional_fields
    if missing:
        raise ConfigurationError(
            "ExecutionReceipt missing fields: " + ", ".join(sorted(missing))
        )
    if unknown:
        raise ConfigurationError(
            "ExecutionReceipt contains unsupported fields: " + ", ".join(sorted(unknown))
        )
    normalized_result = normalize_result(work_result)
    private_final: Mapping[str, Any] | None = None
    if invocation.route.cli == "codex" and result is not None:
        private_final = _private_final_from_process(result).work_result
    try:
        native_result = parse_provider_result(
            invocation, raw_output, private_final=private_final
        )
    except ProviderParseError as exc:
        raise ConfigurationError("native receipt evidence is invalid") from exc
    if dict(native_result.work_result) != normalized_result:
        raise ConfigurationError("native WorkResult does not match receipt evidence")
    native_session_id = native_result.process_or_session_id
    if native_session_id is None:
        if "process_or_session_id" in receipt:
            raise ConfigurationError("ExecutionReceipt session evidence is ungrounded")
    elif receipt.get("process_or_session_id") != native_session_id:
        raise ConfigurationError("ExecutionReceipt session evidence is mismatched")
    embedded = _mapping(receipt.get("claim_proof"), "ExecutionReceipt ClaimProof")
    if set(embedded) != CLAIM_PROOF_FIELDS or embedded.get("schema_version") != 1:
        raise ConfigurationError("ExecutionReceipt ClaimProof fields are invalid")
    embedded_digest = _canonical_sha256(embedded)
    if receipt.get("claim_proof_sha256") != embedded_digest:
        raise ConfigurationError("ExecutionReceipt ClaimProof digest is invalid")
    for field in (
        "claim_key", "decision_sha256", "scheduling_snapshot_sha256",
        "dispatch_identity", "ticket_sha256", "route_sha256",
        "ownership_tokens_sha256", "output_sha256", "work_result_sha256",
        "ownership_key_id",
    ):
        if not isinstance(embedded.get(field), str) or not re.fullmatch(
            r"[a-f0-9]{64}", embedded[field]
        ):
            raise ConfigurationError(f"ExecutionReceipt ClaimProof {field} is invalid")
    if embedded.get("terminal_state") != "completed" or embedded.get("transport_status") != "completed":
        raise ConfigurationError("ExecutionReceipt ClaimProof is not completed")
    claim_key = receipt.get("dispatch_claim_key")
    if not isinstance(claim_key, str) or not re.fullmatch(r"[a-f0-9]{64}", claim_key):
        raise ConfigurationError("ExecutionReceipt dispatch_claim_key must be SHA-256")
    if embedded.get("claim_key") != claim_key:
        raise ConfigurationError("ExecutionReceipt ClaimProof key is mismatched")
    claim_proof = receipt.get("dispatch_claim_sha256")
    if claim_proof != embedded_digest or receipt.get("claim_proof_scope") != "digest-integrity-not-authenticity":
        raise ConfigurationError("embedded claim digest reference is invalid")
    try:
        claim_record = _optional_local_claim(invocation, claim_key)
    except SchedulingError as exc:
        if exc.code in {"INVALID_CLAIM_STORE", "UNSUPPORTED_CLAIM_PLATFORM"}:
            claim_record = None
        else:
            raise ConfigurationError("local dispatch proof is invalid") from exc
    if claim_record is None and not portable:
        raise ConfigurationError("strict local dispatch proof is unavailable")
    if claim_record is not None:
        if (
            claim_record.get("state") != "completed"
            or _embedded_claim_proof(claim_record) != dict(embedded)
        ):
            raise ConfigurationError("local dispatch proof mismatches embedded ClaimProof")
    validated_decision = _validated_invocation_decision(invocation)
    expected_adapter = {
        "codex": "codex-jsonl-output-schema-v2",
        "agy": "agy-stream-json-schema-v2",
    }[invocation.route.cli]
    expected_values = {
        "protocol_version": RESULT_PROTOCOL_VERSION,
        "policy_version": validated_decision.policy_version,
        "decision_sha256": validated_decision.digest,
        "dispatch_claim_key": claim_key,
        "dispatch_claim_sha256": claim_proof,
        "claim_proof": dict(embedded),
        "claim_proof_sha256": embedded_digest,
        "claim_proof_scope": "digest-integrity-not-authenticity",
        "dispatch_identity": _claim_dispatch_identity(invocation),
        "dispatch_ticket_id": validated_decision.decision["ticket"],
        "attempt_id": invocation.attempt_id,
        "alias": invocation.route.alias,
        "provider": invocation.route.cli,
        "adapter": expected_adapter,
        "model": invocation.route.model,
        "effort": invocation.route.effort,
        "objective": _redact_personal_text(invocation.objective),
        "ownership": _redact_personal_text(invocation.ownership),
        "quota_status": validated_decision.decision["quota_band"],
        "transport_status": "completed",
        "work_result_sha256": _canonical_sha256(normalized_result),
    }
    for field, expected in expected_values.items():
        if receipt.get(field) != expected:
            raise ConfigurationError(f"ExecutionReceipt {field} does not match its dispatch binding")
    for integer_field in ("attempt_id", "exit_code", "output_bytes"):
        if isinstance(receipt.get(integer_field), bool) or not isinstance(
            receipt.get(integer_field), int
        ):
            raise ConfigurationError(f"ExecutionReceipt {integer_field} must be an integer")
    if receipt["attempt_id"] < 1 or receipt["output_bytes"] < 1:
        raise ConfigurationError("ExecutionReceipt attempt_id/output_bytes must be positive")
    digest_fields = [
        "decision_sha256",
        "dispatch_identity",
        "output_sha256",
        "work_result_sha256",
        "dispatch_claim_key",
        "dispatch_claim_sha256",
        "claim_proof_sha256",
    ]
    if invocation.scheduling_snapshot_digest is not None:
        if receipt.get("scheduling_snapshot_sha256") != invocation.scheduling_snapshot_digest:
            raise ConfigurationError(
                "ExecutionReceipt scheduling_snapshot_sha256 does not match its dispatch binding"
            )
        digest_fields.append("scheduling_snapshot_sha256")
    elif "scheduling_snapshot_sha256" in receipt:
        raise ConfigurationError(
            "ExecutionReceipt scheduling_snapshot_sha256 has no dispatch binding"
        )
    for digest_field in digest_fields:
        value = receipt.get(digest_field)
        if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
            raise ConfigurationError(f"ExecutionReceipt {digest_field} must be SHA-256")
    raw_bytes = b"" if raw_output is None else (
        raw_output if isinstance(raw_output, bytes) else raw_output.encode("utf-8")
    )
    if receipt["output_bytes"] != len(raw_bytes):
        raise ConfigurationError("ExecutionReceipt output_bytes does not match provider output")
    if receipt["output_sha256"] != hashlib.sha256(raw_bytes).hexdigest():
        raise ConfigurationError("ExecutionReceipt output_sha256 does not match provider output")
    proof_expected = {
        "claim_key": claim_key,
        "decision_sha256": invocation.decision_digest,
        "scheduling_snapshot_sha256": invocation.scheduling_snapshot_digest,
        "dispatch_identity": _claim_dispatch_identity(invocation),
        "ticket_sha256": hashlib.sha256(
            str(invocation.decision["ticket"] if invocation.decision else "missing").encode("ascii")
        ).hexdigest(),
        "route_sha256": _canonical_sha256(
            {
                "role": invocation.route.role,
                "alias": invocation.route.alias,
                "provider": invocation.route.cli,
                "model": invocation.route.model,
                "effort": invocation.route.effort,
            }
        ),
        "transport_status": "completed",
        "exit_code": receipt["exit_code"],
        "output_bytes": len(raw_bytes),
        "output_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "work_result_sha256": _canonical_sha256(normalized_result),
        "terminal_state": "completed",
    }
    for field, expected in proof_expected.items():
        if embedded.get(field) != expected:
            raise ConfigurationError(f"embedded dispatch proof {field} is mismatched")
    started = _parse_utc_timestamp(receipt.get("started_at"), "ExecutionReceipt started_at")
    ended = _parse_utc_timestamp(receipt.get("ended_at"), "ExecutionReceipt ended_at")
    if ended < started:
        raise ConfigurationError("ExecutionReceipt ended_at precedes started_at")
    if receipt["started_at"] != embedded["started_at"] or receipt["ended_at"] != embedded["ended_at"]:
        raise ConfigurationError("ExecutionReceipt timestamps do not match dispatch claim")
    if invocation.qobs_admission is not None:
        admission = _validate_qobs_invocation_binding(
            invocation, now=started, allow_committed=True
        )
        if admission is None:  # Defensive narrowing for static and runtime safety.
            raise ConfigurationError("closed exception QOBS binding is unavailable")
        validate_quota_receipt_binding(
            receipt,
            invocation.qobs_artifact,
            admission.quota_consumption(),
            admission.dispatch_context(),
            dict(invocation.qobs_expected_context or {}),
            now=started,
        )
    provider_id = receipt.get("process_or_session_id")
    _provider_id(provider_id, "ExecutionReceipt process_or_session_id")
    if receipt["exit_code"] == 0:
        pass
    elif normalized_result["status"] == "DONE":
        raise ConfigurationError("nonzero execution cannot carry a DONE WorkResult")
    if is_v3:
        for field in (
            "probe_claim_sha256", "approval_grant_sha256",
            "approval_consume_receipt_sha256", "approval_consume_anchor_sha256",
        ):
            if not isinstance(receipt.get(field), str) or not re.fullmatch(
                r"[a-f0-9]{64}", receipt[field]
            ):
                raise ConfigurationError(f"ExecutionReceipt {field} must be SHA-256")
        _validated_preauthorization_stores(
            _mapping(
                receipt.get("preauthorization_stores"),
                "ExecutionReceipt preauthorization stores",
            )
        )
        _validate_receipt_v3_preauthorization(receipt, invocation)
    _reject_secret_bearing(receipt, "ExecutionReceipt")
    return dict(receipt)


def _execution_provenance(
    invocation: Invocation,
    result: subprocess.CompletedProcess[str],
    provider_result: ProviderResult,
) -> dict[str, Any]:
    """Validate and render non-secret evidence outside the closed v2 receipt."""

    channel_evidence = _validated_process_channel_evidence(result)
    sanitized_argv = list(getattr(result, "_sanitized_argv", ()))
    if not sanitized_argv:
        raise ProviderParseError("terminal_shape", "sanitized argv evidence is missing")
    sanitized_argv_sha256 = hashlib.sha256(
        json.dumps(
            sanitized_argv,
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode("ascii")
    ).hexdigest()
    if sanitized_argv_sha256 != getattr(result, "_sanitized_argv_sha256", None):
        raise ProviderParseError("terminal_shape", "sanitized argv digest is invalid")
    if invocation.route.cli == "codex":
        private_final = _private_final_from_process(result)
        channel_evidence["private_final"] = {
            "bytes": private_final.byte_count,
            "sha256": private_final.sha256,
        }
    return {
        "cli_version": "NOT PROVEN",
        "sanitized_argv": sanitized_argv,
        "sanitized_argv_sha256": sanitized_argv_sha256,
        "requested": {
            "alias": invocation.route.alias,
            "provider": invocation.route.cli,
            "model": invocation.route.model,
            "effort": invocation.route.effort,
            "sandbox": invocation.route.sandbox,
            "quota_band": invocation.decision.get("quota_band") if invocation.decision else None,
        },
        "effective": {
            "model": "NOT PROVEN",
            "effort": "NOT PROVEN",
            "account": "NOT PROVEN",
            "quota": "NOT PROVEN",
        },
        "channels": channel_evidence,
        "normalized_work_result_sha256": _canonical_sha256(provider_result.work_result),
        "safe_thread_id": provider_result.process_or_session_id,
    }


def _completed_result_contract(
    invocation: Invocation,
    result: subprocess.CompletedProcess[str],
    provider_result: ProviderResult,
    *,
    started_at: str,
    ended_at: str,
) -> dict[str, Any]:
    claim = getattr(result, "_dispatch_claim", None)
    if not isinstance(claim, DispatchClaim) or claim.closed:
        raise ConfigurationError("active dispatch claim is required")
    try:
        # Validate every non-secret channel binding before making the claim's
        # terminal completed state immutable.
        try:
            provenance = _execution_provenance(invocation, result, provider_result)
        except BaseException:
            _finalize_dispatch_claim(claim, "rejected", result)
            raise
        proof = _finalize_dispatch_claim(claim, "completed", result, provider_result)
        result._dispatch_claim_sha256 = proof  # type: ignore[attr-defined]
        receipt = _build_execution_receipt(
            invocation,
            result,
            provider_result,
            started_at=started_at,
            ended_at=ended_at,
        )
        validated_receipt = validate_execution_receipt(
            receipt,
            provider_result.work_result,
            invocation,
            result.stdout,
            result=result,
        )
        # This wrapper is execution evidence around the unchanged WorkResult
        # and ExecutionReceipt v2 objects. Requested route values are intent;
        # the CLI stream does not prove effective backend/account/quota state.
        return _redact_result_value(
            {
                "execution_receipt": validated_receipt,
                "approval_consume_receipt": dict(
                    getattr(result, "_approval_consume_receipt")
                ),
                "execution_provenance": provenance,
                "work_result": dict(provider_result.work_result),
            },
            invocation,
        )
    finally:
        _release_dispatch_claim(claim)


def _reject_result_claim(result: subprocess.CompletedProcess[str]) -> None:
    """Persist provider rejection after parsing is known, then release the store."""

    claim = getattr(result, "_dispatch_claim", None)
    if not isinstance(claim, DispatchClaim) or claim.closed:
        return
    try:
        _finalize_dispatch_claim(claim, "rejected", result)
    except (SchedulingError, OSError):
        pass
    finally:
        _release_dispatch_claim(claim)


def _public_process_result(
    result: subprocess.CompletedProcess[str],
) -> subprocess.CompletedProcess[str]:
    """Expose transport status without returning child-controlled streams."""

    return subprocess.CompletedProcess(
        list(getattr(result, "_sanitized_argv", ("<ARGV_UNAVAILABLE>",))),
        result.returncode,
        "[PROVIDER_STDOUT_ELIDED]" if result.stdout else "",
        "[PROVIDER_STDERR_ELIDED]" if result.stderr else "",
    )


def execute_invocation(invocation: Invocation) -> ExecutionOutcome:
    """Execute, parse, terminalize, validate the receipt, and always release locks."""

    try:
        result = _execute_invocation_locked(invocation)
    except ProviderParseError as exc:
        raise ExecutionContractError(
            exc.provider_parse_reason,
            final_message_cardinality_subreason=exc.final_message_cardinality_subreason,
            candidate_count=exc.candidate_count,
        ) from exc
    try:
        bound_invocation = getattr(result, "_bound_invocation", invocation)
        private_final: Mapping[str, Any] | None = None
        if bound_invocation.route.cli == "codex":
            private_final = _private_final_from_process(result).work_result
        provider_result = parse_provider_result(
            bound_invocation, result.stdout, private_final=private_final
        )
        if result.returncode != 0 and provider_result.work_result["status"] == "DONE":
            raise ProviderParseError(
                "provider_failure_event", "nonzero Codex transport cannot carry DONE"
            )
        completed = _completed_result_contract(
            bound_invocation,
            result,
            provider_result,
            started_at=getattr(result, "_dispatch_started_at", _utc_now()),
            ended_at=getattr(result, "_dispatch_ended_at", _utc_now()),
        )
        return ExecutionOutcome(_public_process_result(result), completed)
    except BaseException as exc:
        _reject_result_claim(result)
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        if isinstance(exc, ProviderParseError):
            raise ExecutionContractError(
                exc.provider_parse_reason,
                final_message_cardinality_subreason=exc.final_message_cardinality_subreason,
                candidate_count=exc.candidate_count,
            ) from exc
        raise ExecutionContractError("unknown") from exc


def _redact_result_value(value: Any, invocation: Invocation) -> Any:
    """Prevent child-controlled output from echoing prompt, homes, or secrets."""

    if isinstance(value, str):
        redacted = value
        for prompt_value in _prompt_redaction_values(invocation):
            redacted = redacted.replace(prompt_value, "<PROMPT_REDACTED>")
        redacted = _redact_preview(redacted, invocation)
        # Keep the filter deliberately narrow so ordinary findings remain
        # useful, while credential-shaped values are never emitted by this
        # governance command.
        redacted = re.sub(
            r"(?i)\b(?:token|cookie|api[_-]?key|authorization)\s*[:=]\s*[^\s,;]+",
            "<SECRET_REDACTED>",
            redacted,
        )
        return _redact_personal_text(redacted)
    if isinstance(value, list):
        return [_redact_result_value(item, invocation) for item in value]
    if isinstance(value, tuple):
        return [_redact_result_value(item, invocation) for item in value]
    if isinstance(value, Mapping):
        return {
            _redact_personal_text(str(key)): _redact_result_value(item, invocation)
            for key, item in value.items()
        }
    return value


def _prompt_redaction_values(invocation: Invocation) -> tuple[str, ...]:
    """Return encoded and decoded prompt forms without exposing either value."""

    values = {invocation.prompt_stdin}
    if invocation.route.cli == "agy":
        try:
            event = _strict_json_loads(invocation.prompt_stdin)
            if isinstance(event, Mapping):
                message = event.get("message")
                if isinstance(message, Mapping):
                    content = message.get("content")
                    if isinstance(content, str) and content:
                        values.add(content)
        except _StrictJSONError:
            pass
    return tuple(sorted((item for item in values if item), key=len, reverse=True))


def _configured_policy_path(
    config_path: str | os.PathLike[str],
    config: Mapping[str, Any],
    explicit_policy_path: str | None,
) -> Path:
    if explicit_policy_path:
        return Path(explicit_policy_path)
    configured = config.get("model_policy")
    if not isinstance(configured, str) or not configured.strip():
        raise ConfigurationError(
            "a DispatchDecision requires --policy or config.model_policy"
        )
    path = Path(configured)
    if not path.is_absolute():
        path = Path(config_path).resolve().parent / path
    return path


def _configured_work_result_schema_path(
    policy_path: str | os.PathLike[str], policy: Mapping[str, Any]
) -> Path:
    result_contract = _mapping(policy.get("result_contract"), "model policy result_contract")
    if result_contract.get("protocol_version") != RESULT_PROTOCOL_VERSION:
        raise ConfigurationError("model policy result_contract.protocol_version must be 2")
    configured = result_contract.get("work_result_schema")
    if not isinstance(configured, str) or not configured.strip():
        raise ConfigurationError("model policy result_contract.work_result_schema is required")
    path = Path(configured)
    if not path.is_absolute():
        path = Path(policy_path).resolve().parent / path
    resolved = path.resolve()
    if not resolved.is_file():
        raise ConfigurationError("configured WorkResult v2 schema is unavailable")
    return resolved


def _runtime_config_approval(config: Mapping[str, Any]) -> bool:
    runtime = config.get("runtime")
    if runtime is None:
        return False
    runtime = _mapping(runtime, "runtime")
    approved = runtime.get("approved_for_execution")
    if not isinstance(approved, bool):
        raise ConfigurationError("runtime.approved_for_execution must be boolean")
    if approved and runtime.get("protocol_version") != RESULT_PROTOCOL_VERSION:
        raise ConfigurationError("approved runtime config must declare protocol_version 2")
    return approved is True


def _provider_from_label(provider: str | None) -> str | None:
    """Canonicalize provider names and governed account aliases."""

    if provider is None:
        return None
    if not isinstance(provider, str):
        raise ProviderExecutableBindingError()
    normalized = provider.casefold().replace("_", "-").replace(".", "-")
    labels = {
        "codex": "codex",
        "codex1": "codex",
        "codex2": "codex",
        "codex-1": "codex",
        "codex-2": "codex",
        "codex-one": "codex",
        "codex-two": "codex",
        "codex-cli": "codex",
        "agy": "agy",
        "agy1": "agy",
        "agy2": "agy",
        "agy-1": "agy",
        "agy-2": "agy",
        "agy-one": "agy",
        "agy-two": "agy",
        "agy-cli": "agy",
    }
    try:
        return labels[normalized]
    except KeyError as exc:
        raise ProviderExecutableBindingError() from exc


def _provider_from_executable_basename(executable: str) -> str | None:
    """Classify canonical provider executable and account-alias basenames."""

    basename = re.split(r"[/\\]", executable)[-1].casefold()
    for suffix in (".exe", ".cmd", ".bat", ".sh", ".py", ".bin"):
        if basename.endswith(suffix):
            basename = basename[: -len(suffix)]
            break
    if basename == "agy":
        return "agy"
    agy_remainder = basename[3:] if basename.startswith("agy") else ""
    if agy_remainder in {"cli", "one", "two"} or (
        agy_remainder
        and (agy_remainder[0].isdigit() or agy_remainder[0] in "-_.@")
    ):
        # AGY is intentionally broader than the positive Codex allowlist: any
        # provider-like AGY alias or wrapper remains denied.
        return "agy"
    codex_aliases = {
        "codex", "codex1", "codex2", "codex-1", "codex-2",
        "codex-one", "codex-two", "codex_cli", "codex-cli", "codex.cli",
    }
    if basename in codex_aliases:
        return "codex"
    return None


def _executable_provider_identities(executable: Any) -> frozenset[str]:
    """Return lexical and resolved provider identities for one executable."""

    if not isinstance(executable, str) or not executable or "\x00" in executable:
        raise ProviderExecutableBindingError()
    identities: set[str] = set()

    def record(candidate: str) -> None:
        provider = _provider_from_executable_basename(candidate)
        if provider is not None:
            identities.add(provider)

    record(executable)
    resolved: str | None = None
    try:
        if "/" in executable or "\\" in executable:
            path = Path(executable)
            if path.exists() or path.is_symlink():
                resolved = str(path.resolve(strict=True))
        else:
            located = shutil.which(executable)
            if located:
                resolved = str(Path(located).resolve(strict=True))
    except (OSError, RuntimeError):
        resolved = None
    if resolved is not None:
        record(resolved)
    return frozenset(identities)


def _validate_route_provider_binding(route: Route) -> None:
    """Bind governed alias, declared CLI, and recognizable command identity."""

    expected_provider = ALIAS_PROVIDER_MAP.get(route.alias)
    if expected_provider is None or route.cli != expected_provider:
        raise ProviderExecutableBindingError()
    identities = _executable_provider_identities(route.command)
    if identities != {route.cli}:
        raise ProviderExecutableBindingError()


def _validate_transport_provider_binding(
    provider: str | None, argv: Sequence[str]
) -> None:
    """Deny effective AGY and contradictory metadata before Popen."""

    if isinstance(argv, (str, bytes)) or not argv:
        raise ProviderExecutableBindingError()
    executable = argv[0]
    identities = _executable_provider_identities(executable)
    if "agy" in identities:
        raise PlatformNativePrespawnReceiptRequired()
    declared_provider = _provider_from_label(provider)
    if declared_provider == "agy":
        raise PlatformNativePrespawnReceiptRequired()
    if declared_provider is None or identities != {declared_provider}:
        raise ProviderExecutableBindingError()


def _validate_invocation_provider_binding(invocation: Invocation) -> None:
    """Rebind route and argv before any executable-dispatch side effect."""

    if not invocation.argv:
        raise ProviderExecutableBindingError()
    # Effective AGY wins over a contradictory caller label and receives the
    # stable platform-native blocker required by the external DSG boundary.
    _validate_transport_provider_binding(invocation.route.cli, invocation.argv)
    if invocation.argv[0] != invocation.route.command:
        raise ProviderExecutableBindingError()
    _validate_route_provider_binding(invocation.route)


def _reject_disagreeing_overrides(args: argparse.Namespace, decision: Mapping[str, Any]) -> None:
    for argument, field in (
        ("alias", "selected_alias"),
        ("model", "selected_model"),
        ("effort", "selected_effort"),
    ):
        override = getattr(args, argument)
        if override is not None and override != decision.get(field):
            raise DispatchDecisionError(
                f"--{argument} override disagrees with DispatchDecision {field}"
            )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Path to PromptCommand YAML")
    parser.add_argument("--role", required=True, help="Configured orchestration role")
    parser.add_argument("--objective", required=True)
    parser.add_argument("--ownership", default=DEFAULT_OWNERSHIP)
    parser.add_argument("--boundaries", default=DEFAULT_BOUNDARIES)
    parser.add_argument("--evidence", default=DEFAULT_EVIDENCE)
    parser.add_argument("--stop-condition", default=DEFAULT_STOP_CONDITION)
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--alias", help="Override with another configured account alias")
    parser.add_argument("--cli", choices=sorted(VALID_CLIS), help="Validated CLI override")
    parser.add_argument("--model", help="Validated model override")
    parser.add_argument("--effort", choices=sorted(VALID_EFFORTS))
    parser.add_argument("--attempt-id", type=int, default=1)
    parser.add_argument("--decision", help="Path to a DispatchDecision v1 JSON/YAML document")
    parser.add_argument(
        "--quota-observation",
        help="Path to the single-use QOBS artifact for the closed exception",
    )
    parser.add_argument(
        "--execution-exception-id",
        help="Exact approved one-shot closed-dispatch exception id",
    )
    parser.add_argument(
        "--scheduling-snapshot",
        help="Path to the Rule 11 scheduling snapshot required for execution",
    )
    parser.add_argument(
        "--policy",
        help="Path to the versioned model policy (defaults to config.model_policy)",
    )
    parser.add_argument("--probe-claim", help="Exact private ProbeClaim v1 artifact")
    parser.add_argument("--approval-grant", help="Exact private ApprovalGrant v1 artifact")
    parser.add_argument(
        "--approval-store", help="Owned mode-0700 durable one-use consume directory"
    )
    parser.add_argument(
        "--approval-session", help="Current safe session identifier bound by claim and grant"
    )
    parser.add_argument(
        "--attest-local-approval",
        action="store_true",
        help="Acknowledge nonportable, non-cryptographic local attestation scope",
    )
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--print-command", action="store_true", help="Render only (default)")
    action.add_argument("--execute", action="store_true", help="Run the rendered argv")
    action.add_argument(
        "--emit-probe-claim", metavar="PATH",
        help="Emit one offline ProbeClaim v1; never starts a subprocess",
    )
    action.add_argument(
        "--emit-approval-grant", metavar="PATH",
        help="Emit one local-attestation ApprovalGrant v1; never starts a subprocess",
    )
    action.add_argument(
        "--compact-approval-consume", metavar="GRANT_ID",
        help="Manually compact eligible 90-day consume metadata to a tombstone",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    admission_lease: capacity.CapacityLease | None = None
    qobs_admission: QobsAdmission | None = None
    normal_activation_state: tuple[bool, str] | None = None
    try:
        config = load_config(args.config)
        validate_closed_dispatch_execution_args(args, config)
        closed_exception_requested = bool(
            args.execute and args.quota_observation and args.execution_exception_id
        )
        if args.execute and not closed_exception_requested:
            normal_activation_state = effective_activation_state(config)
        if args.execute and not args.decision:
            raise DispatchDecisionError(
                "legacy v1 execution is disabled; supply --decision with a versioned DispatchDecision"
            )
        if args.execute and not args.scheduling_snapshot:
            raise SchedulingError(
                "INVALID_SCHEDULING_METADATA",
                "executable dispatch requires --scheduling-snapshot",
            )
        if args.emit_probe_claim and not (
            args.approval_session and args.approval_grant and args.approval_store
        ):
            raise ProbeAuthorizationError(
                "ProbeClaim emission requires session, grant path, and consume store"
            )
        if args.emit_approval_grant and not (
            args.probe_claim
            and args.approval_session
            and args.approval_store
            and args.attest_local_approval
        ):
            raise ProbeAuthorizationError(
                "ApprovalGrant emission requires exact claim, session, and local attestation"
            )
        if args.compact_approval_consume and not args.approval_store:
            raise ProbeAuthorizationError("consume compaction requires --approval-store")
        if args.policy and not args.decision:
            raise DispatchDecisionError("--policy requires --decision")
        if args.scheduling_snapshot and not args.decision:
            raise SchedulingError(
                "INVALID_SCHEDULING_METADATA",
                "--scheduling-snapshot requires --decision",
            )
        decision: Mapping[str, Any] | None = None
        model_policy: Mapping[str, Any] | None = None
        scheduling_snapshot: Mapping[str, Any] | None = None
        work_result_schema_path: Path | None = None
        if args.decision:
            decision = load_dispatch_decision(args.decision)
            policy_path = _configured_policy_path(args.config, config, args.policy)
            model_policy = load_model_policy(policy_path)
            work_result_schema_path = _configured_work_result_schema_path(
                policy_path, model_policy
            )
            _reject_disagreeing_overrides(args, decision)
            route = resolve_route(
                config,
                args.role,
                alias_override=decision.get("selected_alias"),
                cli_override=args.cli,
                model_override=decision.get("selected_model"),
                effort_override=decision.get("selected_effort"),
            )
            decision = validate_dispatch_decision(decision, model_policy, route).decision
            if args.scheduling_snapshot:
                scheduling_snapshot = load_scheduling_snapshot(args.scheduling_snapshot)
        if args.execute and not closed_exception_requested:
            if normal_activation_state is None:
                raise ConfigurationError("normal activation state is unavailable")
            activation_prohibited, dispatcher_execution = normal_activation_state
            validate_activation_state(
                activation_prohibited=activation_prohibited,
                dispatcher_execution=dispatcher_execution,
            )
        route = resolve_route(
            config,
            args.role,
            alias_override=(
                decision.get("selected_alias") if decision is not None else args.alias
            ),
            cli_override=args.cli,
            model_override=(
                decision.get("selected_model") if decision is not None else args.model
            ),
            effort_override=(
                decision.get("selected_effort") if decision is not None else args.effort
            ),
        )
        if args.execute and not closed_exception_requested:
            validate_provider_account_state(
                config,
                account=route.alias,
                provider=route.cli,
            )
        prompt = render_prompt(
            objective=args.objective,
            ownership=args.ownership,
            boundaries=args.boundaries,
            evidence=args.evidence,
            stop_condition=args.stop_condition,
        )
        invocation = build_invocation(
            route,
            prompt,
            args.project_dir,
            decision=decision,
            model_policy=model_policy,
            attempt_id=args.attempt_id,
            objective=args.objective,
            ownership=args.ownership,
            runtime_config_path=args.config,
            runtime_config_approved=_runtime_config_approval(config),
            work_result_schema_path=work_result_schema_path,
            scheduling_snapshot=scheduling_snapshot,
            probe_claim_path=args.probe_claim or args.emit_probe_claim,
            approval_grant_path=args.approval_grant or args.emit_approval_grant,
            approval_store_path=args.approval_store,
            approval_session_id=args.approval_session,
        )
        if args.execute:
            if closed_exception_requested:
                if invocation.decision is None or invocation.scheduling_snapshot_digest is None:
                    raise SchedulingError(
                        "CAPACITY_LEASE_REQUIRED",
                        "closed exception requires decision and scheduling evidence",
                    )
                artifact = _load_closed_dispatch_qobs(args.quota_observation)
                expected_context = _closed_dispatch_qobs_context(
                    artifact,
                    route=invocation.route,
                    decision=invocation.decision,
                    attempt_id=invocation.attempt_id,
                )
                qobs_admission = validate_closed_dispatch_exception(
                    config,
                    execution_exception_id=args.execution_exception_id,
                    decision=invocation.decision,
                    route=invocation.route,
                    quota_observation=artifact,
                    expected_qobs_context=expected_context,
                    scheduling_snapshot_sha256=invocation.scheduling_snapshot_digest,
                    qobs_nonce_store=None,
                    exception_store=None,
                    ledger_store=REPOSITORY_ROOT / ".horo-luna-one-shot-ledger",
                    consume=False,
                )
                if Path(invocation.cwd).resolve() != REPOSITORY_ROOT.resolve():
                    raise ConfigurationError(
                        "closed exception project_dir must be the repository root"
                    )
                pinned_executable = _resolve_qobs_executable(invocation.route)
                pinned_route = replace(invocation.route, command=pinned_executable)
                invocation = replace(
                    invocation,
                    route=pinned_route,
                    argv=(pinned_executable, *invocation.argv[1:]),
                    qobs_admission=qobs_admission,
                    qobs_artifact=artifact,
                    qobs_expected_context=expected_context,
                    qobs_ledger_store=str(
                        (REPOSITORY_ROOT / ".horo-luna-one-shot-ledger").resolve()
                    ),
                )
            else:
                if normal_activation_state is None:
                    raise ConfigurationError("normal activation state is unavailable")
                activation_prohibited, dispatcher_execution = normal_activation_state
                validate_activation_state(
                    activation_prohibited=activation_prohibited,
                    dispatcher_execution=dispatcher_execution,
                )
            # The CLI owns admission rather than accepting an untrusted lease
            # document.  The local ledger remains account-specific and is never
            # a reason to select a different alias, model, or provider.
            if invocation.decision is None or invocation.scheduling_snapshot is None:
                raise SchedulingError("CAPACITY_LEASE_REQUIRED", "capacity admission requires dispatch evidence")
            policy_path = REPOSITORY_ROOT / ".agents/config/s3_capacity_policy.json"
            try:
                capacity_policy = json.loads(policy_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise SchedulingError("CAPACITY_POLICY_INVALID", "capacity policy is unavailable") from exc
            validated = validate_dispatch_decision(
                invocation.decision, invocation.model_policy, invocation.route
            )
            lease = admit_dispatch_capacity(
                validate_scheduling_snapshot(invocation.scheduling_snapshot),
                ticket_id=str(validated.decision["ticket"]),
                owner=invocation.route.role,
                ownership=(invocation.ownership,),
                decision_valid=True,
                store_path=str(Path(invocation.cwd) / ".horo-capacity"),
                account=invocation.route.alias,
                request_id=_dispatch_key(invocation),
                lane=invocation.attempt_id,
                request_budget=1,
                model_quality_floor=str(validated.quality_floor),
                policy=capacity_policy,
                provider=invocation.route.cli,
                provider_account_state=(
                    config.get("provider_account_state", config.get("dispatch_state"))
                ),
                qobs_admission=qobs_admission,
                decision_sha256=(
                    qobs_admission.decision_sha256 if qobs_admission is not None else None
                ),
                scheduling_snapshot_sha256=(
                    qobs_admission.scheduling_snapshot_sha256
                    if qobs_admission is not None
                    else None
                ),
                route=invocation.route if qobs_admission is not None else None,
                root_b_role=_mapping(config.get("root_b"), "root_b").get("role")
                if isinstance(config.get("root_b"), Mapping)
                else None,
                attempt=invocation.attempt_id,
                retry_limit=1 if qobs_admission is not None else 3,
                retry_request_id=_claim_dispatch_identity(invocation),
            )
            admission_lease = lease
            invocation = replace(
                invocation,
                capacity_lease=lease,
                capacity_store_path=str(Path(invocation.cwd) / ".horo-capacity"),
                capacity_policy=capacity_policy,
                capacity_request_id=_dispatch_key(invocation),
                capacity_required=True,
            )
    except SchedulingError as exc:
        print(f"[ERROR] BLOCKED: {exc.code}", file=sys.stderr)
        return 5
    except DispatchDecisionError as exc:
        print(f"[ERROR] {exc.status}: DISPATCH_DECISION_INVALID", file=sys.stderr)
        return 2
    except PlatformNativePrespawnReceiptRequired as exc:
        print(f"[ERROR] BLOCKED: {exc.code}", file=sys.stderr)
        return 7
    except ProviderExecutableBindingError as exc:
        print(f"[ERROR] BLOCKED: {exc.code}", file=sys.stderr)
        return 8
    except yaml.YAMLError:
        print("[ERROR] BLOCKED: CONFIG_PARSE_ERROR", file=sys.stderr)
        return 2
    except quota_guard.QuotaObservationError:
        print("[ERROR] BLOCKED: QOBS_INVALID", file=sys.stderr)
        return 2
    except OSError:
        print("[ERROR] BLOCKED: CONFIG_IO_ERROR", file=sys.stderr)
        return 2
    except ConfigurationError:
        print("[ERROR] BLOCKED: CONFIGURATION_INVALID", file=sys.stderr)
        return 2

    if args.emit_probe_claim:
        try:
            claim = emit_probe_claim(
                invocation, args.emit_probe_claim,
                session_id=args.approval_session,
            )
        except (ConfigurationError, OSError):
            print("[ERROR] BLOCKED: PROBE_CLAIM_EMISSION_FAILED", file=sys.stderr)
            return 2
        print(json.dumps({
            "status": "offline-probe-claim-emitted-no-subprocess",
            "claim_id": claim["claim_id"],
            "expires_at": claim["expires_at"],
            "artifact": "<PRIVATE_PROBE_CLAIM>",
        }, ensure_ascii=True, indent=2))
        print("[OK] Offline ProbeClaim emitted; no subprocess was started.")
        return 0
    if args.emit_approval_grant:
        try:
            grant = emit_probe_approval(
                invocation,
                args.probe_claim, args.emit_approval_grant,
                session_id=args.approval_session,
            )
        except (ConfigurationError, OSError):
            print("[ERROR] BLOCKED: APPROVAL_GRANT_EMISSION_FAILED", file=sys.stderr)
            return 2
        print(json.dumps({
            "status": "local-approval-grant-emitted-no-subprocess",
            "grant_id": grant["grant_id"],
            "claim_id": grant["claim_id"],
            "attestation_scope": PREAUTH_SCOPE,
            "authenticity_claimed": False,
            "artifact": "<PRIVATE_APPROVAL_GRANT>",
        }, ensure_ascii=True, indent=2))
        print("[OK] Local ApprovalGrant emitted; no subprocess was started.")
        return 0
    if args.compact_approval_consume:
        try:
            tombstone = compact_approval_consume_tombstone(
                args.approval_store,
                args.compact_approval_consume,
                invocation=invocation,
            )
        except (ConfigurationError, OSError):
            print("[ERROR] BLOCKED: CONSUME_COMPACTION_FAILED", file=sys.stderr)
            return 2
        print(json.dumps({
            "status": "approval-consume-compacted-no-subprocess",
            "consume_id": tombstone["consume_id"],
            "retention": "indefinite",
            "anti_replay": True,
        }, ensure_ascii=True, indent=2))
        print("[OK] Approval consume metadata compacted to anti-replay tombstone.")
        return 0

    argv_preview = [_redact_preview(arg, invocation) for arg in invocation.argv]
    argv_preview.append("<PROMPT_STDIN>")
    rendered = {
        "status": "rendered-route-not-execution-proof",
        "role": route.role,
        "alias": route.alias,
        "cli": route.cli,
        "cwd": "<PROJECT_DIR>",
        "env_keys": sorted(invocation.env_overrides),
        "argv": argv_preview,
        "command": shlex.join(argv_preview),
    }
    if invocation.decision is not None:
        # Kept under the historical key for dry-run consumers. This object is
        # route intent only and never an ExecutionReceipt.
        rendered["dispatch_receipt"] = _dispatch_binding(invocation)
    if invocation.scheduling_snapshot_digest is not None:
        rendered["scheduling_snapshot_sha256"] = invocation.scheduling_snapshot_digest
    print(json.dumps(rendered, ensure_ascii=False, indent=2))
    if not args.execute:
        if invocation.decision is None:
            print(
                "[WARNING] Legacy v1 dry-run has no DispatchDecision; execution would be rejected.",
                file=sys.stderr,
            )
        print("[OK] Dry-run only; no subprocess was started.")
        return 0

    try:
        outcome = execute_invocation(invocation)
    except SchedulingError as exc:
        print(
            json.dumps(
                _canonical_blocked_result(
                    route,
                    failure_class="rule11-scheduling-revalidation-failed",
                    recommended_next_action=(
                        "refresh the scheduling snapshot and dispatch the selected ticket"
                    ),
                    invocation=invocation,
                ),
                ensure_ascii=True,
                indent=2,
            )
        )
        print(f"[ERROR] BLOCKED: {exc.code}", file=sys.stderr)
        return 5
    except DispatchDecisionError as exc:
        print(
            json.dumps(
                _canonical_blocked_result(
                    route,
                    failure_class="dispatch-decision-revalidation-failed",
                    recommended_next_action=(
                        "regenerate the DispatchDecision and keep its route bound to the loaded policy"
                    ),
                    invocation=invocation,
                    status=exc.status,
                    reason_code="DISPATCH_DECISION_INVALID",
                ),
                ensure_ascii=True,
                indent=2,
            )
        )
        print(f"[ERROR] {exc.status}: DISPATCH_DECISION_INVALID", file=sys.stderr)
        return 4
    except ExecutionContractError as exc:
        print(
            json.dumps(
                _canonical_blocked_result(
                    route,
                    failure_class="invalid-child-result-contract",
                    recommended_next_action="rerun the selected alias and require the JSON result contract",
                    invocation=invocation,
                    provider_parse_reason=exc.provider_parse_reason,
                    final_message_cardinality_subreason=(
                        exc.final_message_cardinality_subreason
                    ),
                    candidate_count=exc.candidate_count,
                ),
                ensure_ascii=True,
                indent=2,
            )
        )
        print("[ERROR] Invalid sub-agent result contract.", file=sys.stderr)
        return 3
    except PlatformNativePrespawnReceiptRequired as exc:
        print(
            json.dumps(
                _canonical_blocked_result(
                    route,
                    failure_class="platform-native-prespawn-receipt-required",
                    recommended_next_action=(
                        "keep AGY execution disabled until DSG-009A and DSG-009B "
                        "are externally implemented and proven"
                    ),
                    invocation=invocation,
                ),
                ensure_ascii=True,
                indent=2,
            )
        )
        print(f"[ERROR] BLOCKED: {exc.code}", file=sys.stderr)
        return 7
    except ProviderExecutableBindingError as exc:
        print(
            json.dumps(
                _canonical_blocked_result(
                    route,
                    failure_class="provider-executable-binding-invalid",
                    recommended_next_action=(
                        "restore the canonical alias, provider, command, and argv binding"
                    ),
                    invocation=invocation,
                ),
                ensure_ascii=True,
                indent=2,
            )
        )
        print(f"[ERROR] BLOCKED: {exc.code}", file=sys.stderr)
        return 8
    except ProbeAuthorizationError:
        print(
            json.dumps(
                _canonical_blocked_result(
                    route,
                    failure_class="probe-preauthorization-invalid",
                    recommended_next_action=(
                        "obtain one fresh exact ProbeClaim and local ApprovalGrant; "
                        "do not retry a consumed grant"
                    ),
                    invocation=invocation,
                ),
                ensure_ascii=True,
                indent=2,
            )
        )
        print("[ERROR] BLOCKED: PROBE_AUTHORIZATION_INVALID", file=sys.stderr)
        return 6
    except (ConfigurationError, OSError) as exc:
        print(
            json.dumps(
                _canonical_blocked_result(
                    route,
                    failure_class="executable-unavailable-or-preflight-failed",
                    recommended_next_action=(
                        "verify the selected alias CLI installation and retry the same bounded task"
                    ),
                    invocation=invocation,
                ),
                ensure_ascii=True,
                indent=2,
            )
        )
        # Do not expose the exception: it may contain account-home or host
        # details.  The canonical record above is the operator-facing outcome.
        print(f"[ERROR] Unable to start configured {route.cli} executable.", file=sys.stderr)
        return 127
    finally:
        # Admission happens before executable preflight.  Always return an
        # unconsumed lease on a later preflight/start failure; consumed leases
        # are already terminalized by _execute_invocation_locked, and that
        # replay-safe cleanup must never replace the original failure.
        if admission_lease is not None and invocation.capacity_store_path and invocation.capacity_policy:
            try:
                capacity.release_lease(
                    invocation.capacity_store_path,
                    admission_lease,
                    policy=invocation.capacity_policy,
                )
            except capacity.CapacityLeaseError:
                pass
    result = outcome.process
    completed = outcome.completed
    print(json.dumps(_redact_result_value(completed, invocation), ensure_ascii=False, indent=2))
    if result.returncode == 0:
        print("[OK] Provider process completed.")
    else:
        print(f"[ERROR] Sub-agent command exited with code {result.returncode}.", file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
