#!/usr/bin/env python3
"""Immediate typed Python bridge for macOS Agent Broker (BRK-B1-020).

This module translates closed broker requests into typed execution invocations
while preserving Rule 17 receipts and WorkResults.

Key Guarantees:
- Enforces the 6 canonical aliases (agy1..agy3, codex1..codex3).
- Validates requests against agent-broker-request-v1 schema and emits results
  against agent-broker-result-v1 schema.
- Preserves argument arrays without shell interpolation (shell=False).
- Binds request, session, ticket, alias, provider, lease, ownership, and decision digests.
- Fails closed with BROKER_UNAVAILABLE, BROKER_INSTALL_INTEGRITY, or BROKER_ALIAS_UNKNOWN
  with zero direct-provider fallback.
- Supports session-only execution without reading Keychain data.
- Emits pure ASCII logs and structured outputs.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / ".agents" / "config" / "agent_broker.v1.json"
REQUEST_SCHEMA_PATH = ROOT / ".agents" / "schemas" / "agent-broker-request-v1.schema.json"
RESULT_SCHEMA_PATH = ROOT / ".agents" / "schemas" / "agent-broker-result-v1.schema.json"

CANONICAL_ALIASES: tuple[str, ...] = (
    "agy1",
    "agy2",
    "agy3",
    "agy4",
    "codex1",
    "codex2",
    "codex3",
)

PROVIDER_MAPPING: dict[str, str] = {
    "agy1": "agy",
    "agy2": "agy",
    "agy3": "agy",
    "agy4": "agy",
    "codex1": "codex",
    "codex2": "codex",
    "codex3": "codex",
}

ROOT_POOL_MAPPING: dict[str, str] = {
    "agy1": "root_b",
    "agy2": "root_b",
    "agy3": "root_b",
    "agy4": "root_b",
    "codex1": "root_a",
    "codex2": "root_a",
    "codex3": "root_a",
}

DEFAULT_CAPACITIES: dict[str, int] = {
    "agy1": 3,
    "agy2": 3,
    "agy3": 3,
    "agy4": 3,
    "codex1": 2,
    "codex2": 2,
    "codex3": 2,
}

VALID_STATUSES: frozenset[str] = frozenset(
    {"SUCCESS", "FAILED", "REJECTED", "CANCELLED", "TIMEOUT", "CRASHED"}
)

REQUEST_SCHEMA_VERSION = "agent-broker-request-v1"
RESULT_SCHEMA_VERSION = "agent-broker-result-v1"
CONFIG_SCHEMA_VERSION = "agent-broker-config-v1"

_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9_.:-]+$")
_SHA256_HEX = re.compile(r"^[a-f0-9]{64}$")


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class BrokerBridgeError(Exception):
    """Base exception for all Broker Bridge errors."""

    def __init__(self, message: str, error_code: str = "BROKER_BRIDGE_ERROR") -> None:
        super().__init__(f"[{error_code}] {message}")
        self.message = message
        self.error_code = error_code


class BrokerUnavailableError(BrokerBridgeError):
    """Raised when the Swift broker binary is not found, not executable, or unreachable."""

    def __init__(self, message: str = "Broker binary unavailable") -> None:
        super().__init__(message, error_code="BROKER_UNAVAILABLE")


class BrokerInstallIntegrityError(BrokerBridgeError):
    """Raised when the broker binary fails security, permission, or integrity validation."""

    def __init__(self, message: str = "Broker binary failed integrity checks") -> None:
        super().__init__(message, error_code="BROKER_INSTALL_INTEGRITY")


class BrokerAliasUnknownError(BrokerBridgeError):
    """Raised when an alias is outside the canonical six-alias allowlist."""

    def __init__(self, alias: str) -> None:
        super().__init__(
            f"Alias '{alias}' is not in canonical allowlist: {list(CANONICAL_ALIASES)}",
            error_code="BROKER_ALIAS_UNKNOWN",
        )


class BrokerSchemaValidationError(BrokerBridgeError):
    """Raised when a request or result fails closed schema validation."""

    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="SCHEMA_VALIDATION_FAILED")


class DirectProviderFallbackError(BrokerBridgeError):
    """Raised when an attempt is made to bypass the broker and call the provider directly."""

    def __init__(self, message: str = "Direct provider fallback is strictly prohibited") -> None:
        super().__init__(message, error_code="DIRECT_PROVIDER_FALLBACK_PROHIBITED")


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgentBrokerRequest:
    """Closed request representation for the Agent Broker (agent-broker-request-v1)."""

    schema_version: str = REQUEST_SCHEMA_VERSION
    request_id: str = ""
    alias: str = ""
    action: str = "execute"
    command_argv: list[str] = field(default_factory=list)
    lease_id: str | None = None
    timeout_seconds: int | None = None
    caller_context: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "alias": self.alias,
            "action": self.action,
            "command_argv": list(self.command_argv),
        }
        if self.lease_id is not None:
            result["lease_id"] = self.lease_id
        if self.timeout_seconds is not None:
            result["timeout_seconds"] = self.timeout_seconds
        if self.caller_context is not None:
            result["caller_context"] = dict(self.caller_context)
        return result

    def to_json(self, *, indent: int | None = None) -> str:
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            indent=indent,
            ensure_ascii=True,
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> AgentBrokerRequest:
        is_valid, err_code, err_msg = validate_request_dict(dict(data))
        if not is_valid:
            raise BrokerSchemaValidationError(f"{err_code}: {err_msg}")
        return cls(
            schema_version=str(data["schema_version"]),
            request_id=str(data["request_id"]),
            alias=str(data["alias"]),
            action=str(data["action"]),
            command_argv=[str(arg) for arg in data["command_argv"]],
            lease_id=str(data["lease_id"]) if data.get("lease_id") is not None else None,
            timeout_seconds=int(data["timeout_seconds"]) if data.get("timeout_seconds") is not None else None,
            caller_context={str(k): str(v) for k, v in data["caller_context"].items()}
            if isinstance(data.get("caller_context"), dict)
            else None,
        )

    @classmethod
    def from_json(cls, payload: str | bytes) -> AgentBrokerRequest:
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise BrokerSchemaValidationError(f"Invalid JSON payload: {exc}") from exc
        if not isinstance(data, dict):
            raise BrokerSchemaValidationError("Request payload must be a JSON object")
        return cls.from_dict(data)


@dataclass(frozen=True)
class AgentBrokerResult:
    """Closed result representation returned by the Agent Broker (agent-broker-result-v1)."""

    schema_version: str = RESULT_SCHEMA_VERSION
    request_id: str = ""
    status: str = "REJECTED"
    exit_code: int = 1
    sanitized_output_digest: str = "0" * 64
    duration_ms: int = 0
    error_code: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "status": self.status,
            "exit_code": self.exit_code,
            "sanitized_output_digest": self.sanitized_output_digest,
            "duration_ms": self.duration_ms,
        }
        if self.error_code is not None:
            result["error_code"] = self.error_code
        if self.error_message is not None:
            result["error_message"] = self.error_message
        return result

    def to_json(self, *, indent: int | None = None) -> str:
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            indent=indent,
            ensure_ascii=True,
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> AgentBrokerResult:
        is_valid, err_code, err_msg = validate_result_dict(dict(data))
        if not is_valid:
            raise BrokerSchemaValidationError(f"{err_code}: {err_msg}")
        return cls(
            schema_version=str(data["schema_version"]),
            request_id=str(data["request_id"]),
            status=str(data["status"]),
            exit_code=int(data["exit_code"]),
            sanitized_output_digest=str(data["sanitized_output_digest"]),
            duration_ms=int(data["duration_ms"]),
            error_code=str(data["error_code"]) if data.get("error_code") is not None else None,
            error_message=str(data["error_message"]) if data.get("error_message") is not None else None,
        )

    @classmethod
    def from_json(cls, payload: str | bytes) -> AgentBrokerResult:
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise BrokerSchemaValidationError(f"Invalid JSON payload: {exc}") from exc
        if not isinstance(data, dict):
            raise BrokerSchemaValidationError("Result payload must be a JSON object")
        return cls.from_dict(data)


# ---------------------------------------------------------------------------
# Digest Binding Helpers
# ---------------------------------------------------------------------------


def compute_sha256(data: str | bytes) -> str:
    """Compute deterministic pure-ASCII lowercase SHA-256 digest."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def compute_request_digest(request: AgentBrokerRequest) -> str:
    """Compute SHA-256 digest over canonical JSON representation of request."""
    canonical_repr = request.to_json()
    return compute_sha256(canonical_repr)


def compute_bound_decision_digest(
    request: AgentBrokerRequest,
    *,
    session_id: str | None = None,
    ticket_id: str | None = None,
    ownership: str | None = None,
    lease_id: str | None = None,
    decision: str = "admit",
) -> str:
    """Compute bound decision digest linking request, session, ticket, ownership, and lease."""
    payload = {
        "action": request.action,
        "alias": request.alias,
        "decision": decision,
        "lease_id": lease_id or request.lease_id or "",
        "ownership": ownership or "",
        "provider": PROVIDER_MAPPING.get(request.alias, "unknown"),
        "request_id": request.request_id,
        "session_id": session_id or "",
        "ticket_id": ticket_id or "",
    }
    canonical_json = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return compute_sha256(canonical_json)


def compute_output_digest(output: str | bytes) -> str:
    """Compute SHA-256 digest over output bytes/string."""
    return compute_sha256(output)


# ---------------------------------------------------------------------------
# Strict Closed Schema Validation
# ---------------------------------------------------------------------------


def validate_request_dict(data: dict[str, Any]) -> tuple[bool, str | None, str | None]:
    """Validate a request dictionary against closed agent-broker-request-v1 rules."""
    allowed_keys = {
        "schema_version",
        "request_id",
        "alias",
        "action",
        "command_argv",
        "lease_id",
        "timeout_seconds",
        "caller_context",
    }
    present_keys = set(data.keys())
    unknown_keys = present_keys - allowed_keys
    if unknown_keys:
        return (
            False,
            "SCHEMA_UNKNOWN_PROPERTY",
            f"Unknown properties in request: {sorted(unknown_keys)}",
        )

    required_keys = {"schema_version", "request_id", "alias", "action", "command_argv"}
    missing_keys = required_keys - present_keys
    if missing_keys:
        return (
            False,
            "SCHEMA_MISSING_REQUIRED_PROPERTY",
            f"Missing required properties: {sorted(missing_keys)}",
        )

    if data["schema_version"] != REQUEST_SCHEMA_VERSION:
        return (
            False,
            "SCHEMA_VERSION_MISMATCH",
            f"Expected schema_version '{REQUEST_SCHEMA_VERSION}', got '{data['schema_version']}'",
        )

    if not isinstance(data["request_id"], str) or not data["request_id"].strip():
        return False, "INVALID_REQUEST_ID", "request_id must be a non-empty string"
    if not _SAFE_IDENTIFIER.match(data["request_id"]):
        return (
            False,
            "INVALID_REQUEST_ID_FORMAT",
            f"request_id '{data['request_id']}' contains invalid characters",
        )

    alias = data["alias"]
    if not isinstance(alias, str) or alias not in CANONICAL_ALIASES:
        return (
            False,
            "UNAUTHORIZED_ALIAS",
            f"Alias '{alias}' is not authorized. Must be one of: {list(CANONICAL_ALIASES)}",
        )

    if not isinstance(data["action"], str) or not data["action"].strip():
        return False, "INVALID_ACTION", "action must be a non-empty string"

    if not isinstance(data["command_argv"], list):
        return False, "INVALID_COMMAND_ARGV", "command_argv must be an array of strings"
    for idx, item in enumerate(data["command_argv"]):
        if not isinstance(item, str):
            return (
                False,
                "INVALID_COMMAND_ARGV_ITEM",
                f"command_argv item at index {idx} must be a string",
            )

    if "lease_id" in data and data["lease_id"] is not None:
        if not isinstance(data["lease_id"], str) or not data["lease_id"].strip():
            return False, "INVALID_LEASE_ID", "lease_id must be a non-empty string"

    if "timeout_seconds" in data and data["timeout_seconds"] is not None:
        if not isinstance(data["timeout_seconds"], int) or data["timeout_seconds"] <= 0:
            return (
                False,
                "INVALID_TIMEOUT_SECONDS",
                "timeout_seconds must be a positive integer",
            )

    if "caller_context" in data and data["caller_context"] is not None:
        if not isinstance(data["caller_context"], dict):
            return (
                False,
                "INVALID_CALLER_CONTEXT",
                "caller_context must be a string dictionary",
            )
        for k, v in data["caller_context"].items():
            if not isinstance(k, str) or not isinstance(v, str):
                return (
                    False,
                    "INVALID_CALLER_CONTEXT_ENTRY",
                    f"caller_context entry {k!r} must have string key and value",
                )

    return True, None, None


def validate_result_dict(data: dict[str, Any]) -> tuple[bool, str | None, str | None]:
    """Validate a result dictionary against closed agent-broker-result-v1 rules."""
    allowed_keys = {
        "schema_version",
        "request_id",
        "status",
        "exit_code",
        "sanitized_output_digest",
        "duration_ms",
        "error_code",
        "error_message",
    }
    present_keys = set(data.keys())
    unknown_keys = present_keys - allowed_keys
    if unknown_keys:
        return (
            False,
            "SCHEMA_UNKNOWN_PROPERTY",
            f"Unknown properties in result: {sorted(unknown_keys)}",
        )

    required_keys = {
        "schema_version",
        "request_id",
        "status",
        "exit_code",
        "sanitized_output_digest",
        "duration_ms",
    }
    missing_keys = required_keys - present_keys
    if missing_keys:
        return (
            False,
            "SCHEMA_MISSING_REQUIRED_PROPERTY",
            f"Missing required properties: {sorted(missing_keys)}",
        )

    if data["schema_version"] != RESULT_SCHEMA_VERSION:
        return (
            False,
            "SCHEMA_VERSION_MISMATCH",
            f"Expected schema_version '{RESULT_SCHEMA_VERSION}', got '{data['schema_version']}'",
        )

    if not isinstance(data["request_id"], str) or not data["request_id"].strip():
        return False, "INVALID_REQUEST_ID", "request_id must be a non-empty string"

    if data["status"] not in VALID_STATUSES:
        return (
            False,
            "INVALID_STATUS",
            f"status '{data['status']}' must be one of: {sorted(VALID_STATUSES)}",
        )

    if not isinstance(data["exit_code"], int):
        return False, "INVALID_EXIT_CODE", "exit_code must be an integer"

    if not isinstance(data["sanitized_output_digest"], str) or not _SHA256_HEX.match(
        data["sanitized_output_digest"]
    ):
        return (
            False,
            "INVALID_OUTPUT_DIGEST",
            "sanitized_output_digest must be a 64-character lowercase hex string",
        )

    if not isinstance(data["duration_ms"], int) or data["duration_ms"] < 0:
        return False, "INVALID_DURATION_MS", "duration_ms must be a non-negative integer"

    if "error_code" in data and data["error_code"] is not None:
        if not isinstance(data["error_code"], str):
            return False, "INVALID_ERROR_CODE", "error_code must be a string or null"

    if "error_message" in data and data["error_message"] is not None:
        if not isinstance(data["error_message"], str):
            return False, "INVALID_ERROR_MESSAGE", "error_message must be a string or null"

    return True, None, None


# ---------------------------------------------------------------------------
# Broker Discovery & Integrity
# ---------------------------------------------------------------------------


def load_broker_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load configuration from .agents/config/agent_broker.v1.json."""
    target = config_path or CONFIG_PATH
    if not target.is_file():
        return {}
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return {}


def resolve_broker_binary(config_path: Path | None = None) -> Path | None:
    """Resolve the executable path to the Swift agent broker binary."""
    config = load_broker_config(config_path)
    broker_conf = config.get("broker", {})

    candidates: list[Path] = []
    if "binary_path" in broker_conf:
        candidates.append(ROOT / broker_conf["binary_path"])
    if "fallback_binary_path" in broker_conf:
        candidates.append(ROOT / broker_conf["fallback_binary_path"])

    # Standard candidate locations
    candidates.extend(
        [
            ROOT / "tools" / "agent-broker" / ".build" / "release" / "agent-broker",
            ROOT / "tools" / "agent-broker" / ".build" / "debug" / "agent-broker",
            ROOT / "tools" / "agent-broker" / "agent-broker",
            ROOT / "tools" / "agent-broker" / "bin" / "agent-broker",
        ]
    )

    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate

    # Check PATH
    which_bin = subprocess.run(
        ["which", "agent-broker"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if which_bin.returncode == 0 and which_bin.stdout.strip():
        p = Path(which_bin.stdout.strip())
        if p.is_file() and os.access(p, os.X_OK):
            return p

    return None


def verify_broker_integrity(broker_path: Path) -> tuple[bool, str | None]:
    """Verify that the broker binary is a safe regular executable and not a symlink."""
    if not broker_path.exists():
        return False, "Broker binary does not exist"
    if broker_path.is_symlink():
        return False, "Broker binary cannot be a symlink"
    if not broker_path.is_file():
        return False, "Broker binary must be a regular file"
    if not os.access(broker_path, os.X_OK):
        return False, "Broker binary is not executable"

    try:
        details = broker_path.stat()
        mode = stat.S_IMODE(details.st_mode)
        # Verify mode is reasonable (owner executable, not group/world writable)
        if mode & 0o022 != 0:
            return False, f"Broker binary mode {oct(mode)} is group or world writable"
    except OSError as exc:
        return False, f"Unable to inspect broker file metadata: {exc}"

    return True, None


def prohibit_direct_provider_fallback(
    alias: str, reason: str = "direct provider fallback is forbidden"
) -> None:
    """Strict fail-closed enforcement preventing direct CLI execution of providers."""
    raise DirectProviderFallbackError(
        f"Direct execution for alias '{alias}' is blocked: {reason}"
    )


# ---------------------------------------------------------------------------
# Bridge Execution Core
# ---------------------------------------------------------------------------


def execute_via_broker(
    request: AgentBrokerRequest,
    *,
    broker_path: Path | None = None,
    session_only: bool = True,
    timeout: int | None = None,
) -> AgentBrokerResult:
    """Execute a closed request via the Swift Agent Broker without shell invocation.

    Preserves argv boundaries, validates schemas, enforces 6 canonical aliases,
    and returns a typed AgentBrokerResult.
    """
    start_time = time.time()

    # 1. Enforce Canonical Alias
    if request.alias not in CANONICAL_ALIASES:
        duration_ms = int((time.time() - start_time) * 1000)
        return AgentBrokerResult(
            schema_version=RESULT_SCHEMA_VERSION,
            request_id=request.request_id or "unknown",
            status="REJECTED",
            exit_code=1,
            sanitized_output_digest="0" * 64,
            duration_ms=duration_ms,
            error_code="BROKER_ALIAS_UNKNOWN",
            error_message=f"Alias '{request.alias}' is outside the canonical allowlist",
        )

    # 2. Validate Closed Request Schema
    is_valid, err_code, err_msg = validate_request_dict(request.to_dict())
    if not is_valid:
        duration_ms = int((time.time() - start_time) * 1000)
        return AgentBrokerResult(
            schema_version=RESULT_SCHEMA_VERSION,
            request_id=request.request_id or "unknown",
            status="REJECTED",
            exit_code=1,
            sanitized_output_digest="0" * 64,
            duration_ms=duration_ms,
            error_code=err_code or "SCHEMA_VALIDATION_FAILED",
            error_message=err_msg or "Request schema validation failed",
        )

    # 3. Resolve Broker Binary
    resolved_broker = broker_path or resolve_broker_binary()
    if resolved_broker is None:
        duration_ms = int((time.time() - start_time) * 1000)
        return AgentBrokerResult(
            schema_version=RESULT_SCHEMA_VERSION,
            request_id=request.request_id,
            status="REJECTED",
            exit_code=1,
            sanitized_output_digest="0" * 64,
            duration_ms=duration_ms,
            error_code="BROKER_UNAVAILABLE",
            error_message="Swift Agent Broker binary not found or not executable",
        )

    # 4. Verify Broker Integrity
    integrity_ok, integrity_err = verify_broker_integrity(resolved_broker)
    if not integrity_ok:
        duration_ms = int((time.time() - start_time) * 1000)
        return AgentBrokerResult(
            schema_version=RESULT_SCHEMA_VERSION,
            request_id=request.request_id,
            status="REJECTED",
            exit_code=1,
            sanitized_output_digest="0" * 64,
            duration_ms=duration_ms,
            error_code="BROKER_INSTALL_INTEGRITY",
            error_message=integrity_err or "Broker binary failed integrity checks",
        )

    # 5. Prepare Subprocess Execution (shell=False)
    exec_timeout = timeout or request.timeout_seconds or 60
    request_json = request.to_json()

    clean_env = {
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    }
    if session_only:
        clean_env["AGENT_BROKER_SESSION_ONLY"] = "1"

    try:
        process = subprocess.Popen(
            [str(resolved_broker), "--request", request_json],
            cwd=str(ROOT),
            env=clean_env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            close_fds=True,
            shell=False,
        )
        stdout_data, stderr_data = process.communicate(timeout=exec_timeout)
        duration_ms = int((time.time() - start_time) * 1000)
        exit_code = process.returncode

        # Attempt to parse stdout as AgentBrokerResult JSON
        trimmed_stdout = stdout_data.strip()
        if trimmed_stdout:
            try:
                res_dict = json.loads(trimmed_stdout)
                if isinstance(res_dict, dict) and res_dict.get("schema_version") == RESULT_SCHEMA_VERSION:
                    return AgentBrokerResult.from_dict(res_dict)
            except Exception:
                pass

        # Compute output digest
        combined_output = stdout_data + stderr_data
        out_digest = compute_output_digest(combined_output)

        status_str = "SUCCESS" if exit_code == 0 else "FAILED"
        err_code_val = None if exit_code == 0 else "PROCESS_NONZERO_EXIT"
        err_msg_val = None if exit_code == 0 else (stderr_data.strip() or stdout_data.strip() or None)

        return AgentBrokerResult(
            schema_version=RESULT_SCHEMA_VERSION,
            request_id=request.request_id,
            status=status_str,
            exit_code=exit_code,
            sanitized_output_digest=out_digest,
            duration_ms=duration_ms,
            error_code=err_code_val,
            error_message=err_msg_val,
        )

    except subprocess.TimeoutExpired:
        duration_ms = int((time.time() - start_time) * 1000)
        try:
            process.kill()
            process.communicate()
        except Exception:
            pass
        return AgentBrokerResult(
            schema_version=RESULT_SCHEMA_VERSION,
            request_id=request.request_id,
            status="TIMEOUT",
            exit_code=124,
            sanitized_output_digest="0" * 64,
            duration_ms=duration_ms,
            error_code="EXECUTION_TIMEOUT",
            error_message=f"Broker execution timed out after {exec_timeout} seconds",
        )
    except Exception as exc:
        duration_ms = int((time.time() - start_time) * 1000)
        return AgentBrokerResult(
            schema_version=RESULT_SCHEMA_VERSION,
            request_id=request.request_id,
            status="CRASHED",
            exit_code=1,
            sanitized_output_digest="0" * 64,
            duration_ms=duration_ms,
            error_code="SUBPROCESS_EXECUTION_ERROR",
            error_message=str(exc),
        )


def execute_session_only(
    alias: str,
    command_argv: list[str],
    *,
    request_id: str | None = None,
    ticket_id: str | None = None,
    session_id: str | None = None,
    ownership: str | None = None,
    lease_id: str | None = None,
    timeout_seconds: int = 60,
    broker_path: Path | None = None,
) -> AgentBrokerResult:
    """Execute command in session-only mode without reading Keychain credentials."""
    req_id = request_id or f"req-{int(time.time()*1000)}-{compute_sha256(str(command_argv))[:8]}"
    context: dict[str, str] = {"session_mode": "session-only"}
    if ticket_id:
        context["ticket_id"] = ticket_id
    if session_id:
        context["session_id"] = session_id
    if ownership:
        context["ownership"] = ownership

    req = AgentBrokerRequest(
        schema_version=REQUEST_SCHEMA_VERSION,
        request_id=req_id,
        alias=alias,
        action="execute",
        command_argv=list(command_argv),
        lease_id=lease_id,
        timeout_seconds=timeout_seconds,
        caller_context=context,
    )

    return execute_via_broker(
        req,
        broker_path=broker_path,
        session_only=True,
        timeout=timeout_seconds,
    )


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------


def parse_arguments(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description="Immediate typed Python bridge for macOS Agent Broker."
    )
    parser.add_argument(
        "--request",
        type=str,
        help="JSON string conforming to agent-broker-request-v1 schema",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read request JSON from standard input",
    )
    parser.add_argument(
        "--alias",
        type=str,
        choices=CANONICAL_ALIASES,
        help="Canonical alias to execute",
    )
    parser.add_argument(
        "--request-id",
        type=str,
        default="",
        help="Optional request ID",
    )
    parser.add_argument(
        "--lease-id",
        type=str,
        default=None,
        help="Optional single-use capacity lease ID",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Execution timeout in seconds",
    )
    parser.add_argument(
        "--session-only",
        action="store_true",
        default=True,
        help="Execute in session-only mode without Keychain access",
    )
    parser.add_argument(
        "--broker-path",
        type=Path,
        default=None,
        help="Explicit path to agent-broker binary",
    )
    return parser.parse_known_args(argv)


def main(argv: list[str]) -> int:
    opts, trailing = parse_arguments(argv)

    if opts.request:
        try:
            req = AgentBrokerRequest.from_json(opts.request)
        except BrokerSchemaValidationError as err:
            res = AgentBrokerResult(
                request_id="unknown",
                status="REJECTED",
                exit_code=1,
                sanitized_output_digest="0" * 64,
                duration_ms=0,
                error_code="SCHEMA_VALIDATION_FAILED",
                error_message=str(err),
            )
            print(res.to_json(indent=2))
            return res.exit_code
        res = execute_via_broker(
            req,
            broker_path=opts.broker_path,
            session_only=opts.session_only,
        )
        print(res.to_json(indent=2))
        return res.exit_code

    if opts.stdin:
        input_data = sys.stdin.read()
        try:
            req = AgentBrokerRequest.from_json(input_data)
        except BrokerSchemaValidationError as err:
            res = AgentBrokerResult(
                request_id="unknown",
                status="REJECTED",
                exit_code=1,
                sanitized_output_digest="0" * 64,
                duration_ms=0,
                error_code="SCHEMA_VALIDATION_FAILED",
                error_message=str(err),
            )
            print(res.to_json(indent=2))
            return res.exit_code
        res = execute_via_broker(
            req,
            broker_path=opts.broker_path,
            session_only=opts.session_only,
        )
        print(res.to_json(indent=2))
        return res.exit_code

    if opts.alias:
        # Trailing argv after '--' or positional
        command_args = trailing
        if command_args and command_args[0] == "--":
            command_args = command_args[1:]
        res = execute_session_only(
            alias=opts.alias,
            command_argv=command_args,
            request_id=opts.request_id or None,
            lease_id=opts.lease_id,
            timeout_seconds=opts.timeout,
            broker_path=opts.broker_path,
        )
        print(res.to_json(indent=2))
        return res.exit_code

    # If no valid arguments provided, print usage
    print(
        json.dumps(
            {
                "schema_version": RESULT_SCHEMA_VERSION,
                "request_id": "unknown",
                "status": "REJECTED",
                "exit_code": 2,
                "sanitized_output_digest": "0" * 64,
                "duration_ms": 0,
                "error_code": "EMPTY_REQUEST_PAYLOAD",
                "error_message": "Provide --request, --stdin, or --alias to execute",
            },
            indent=2,
        )
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
