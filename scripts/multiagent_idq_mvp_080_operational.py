# -*- coding: utf-8 -*-
"""Operational provider executor for IDQ-MVP-080.

Bounded, multi-lane operational provider execution under the closed IDQ-MVP-080
admission and authorization contract.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import stat
import subprocess
import tempfile
import threading
import time
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import scripts.agent_quota_status_guard as quota
import scripts.multiagent_capacity as capacity
import scripts.multiagent_prompt_command as command

MAX_PROVIDER_OUTPUT_BYTES = command.MAX_PROVIDER_OUTPUT_BYTES
MAX_PROVIDER_STDERR_BYTES = 64 * 1024
PROVIDER_READ_CHUNK_BYTES = 64 * 1024

_TICKET = "IDQ-MVP-080"
_AUTHORIZATION_ID = "IDQ-MVP-080-AUTH-02"
_AUTHORIZATION_SCHEMA_VERSION = "idq-mvp-080-auth-v1"
_AUTHORIZATION_PROTOCOL_VERSION = 2
_AUTHORIZATION_OBJECTIVE = "one bounded read-only repository inventory per alias"
_AUTHORIZATION_OWNERSHIP = "no repository files; terminal metadata only"
_AUTHORIZATION_RISK_ID = "RISK-IDQ-MVP-080-20260830-02"
_AUTHORIZATION_TTL_SECONDS = 1800

_ALIASES: dict[str, tuple[str, str]] = {
    "codex1": ("codex", "A"),
    "codex2": ("codex", "A"),
    "codex3": ("codex", "A"),
    "agy1": ("agy", "B"),
    "agy2": ("agy", "B"),
    "agy3": ("agy", "B"),
    "agy4": ("agy", "B"),
}
_ALIAS_ORDER = tuple(_ALIASES.keys())

_AUTHORIZATION_FIELDS = frozenset({
    "schema_version",
    "protocol_version",
    "authorization_id",
    "ticket",
    "status",
    "issued_at",
    "expires_at",
    "ttl_seconds",
    "control_session_nonce_sha256",
    "aliases",
    "attempt",
    "max_attempts",
    "work_mode",
    "automatic_retry",
    "fallback",
    "substitution",
    "objective",
    "ownership",
    "risk_id",
    "repository_snapshot_sha256",
    "marker_store_sha256",
    "bindings",
})

_AUTHORIZATION_BINDING_FIELDS = frozenset({
    "request_id",
    "root",
    "provider",
    "decision_sha256",
    "scheduling_snapshot_sha256",
    "qobs_artifact_sha256",
    "nonce_sha256",
    "resolved_executable_sha256",
    "resolved_executable_identity_sha256",
    "account_identity_sha256",
    "account_identity_state_sha256",
    "qobs_context_sha256",
    "capacity_lease_sha256",
    "capacity_state_sha256",
    "lease_risk_sha256",
})

_WORK_RESULT_FIELDS = frozenset({
    "status",
    "scope_owned",
    "evidence",
    "findings",
    "changed_files",
    "residual_risk",
    "recommended_next_action",
})

_SAFE_PROVIDER_ENV_KEYS = frozenset({
    "PATH",
    "LANG",
    "LC_ALL",
    "TMPDIR",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "NO_COLOR",
})


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _timestamp(value: datetime) -> str:
    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _parse_timestamp(value: object) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("Timestamp must be an ISO 8601 UTC string ending with Z")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError("Timestamp must be UTC")
    return parsed


def _sha256_hex(value: object, field_name: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[a-f0-9]{64}", value) is None:
        raise ValueError(f"{field_name} must be a lowercase 64-char hex SHA-256 digest")
    return value


def _executable_identity_sha256(path: Path) -> str:
    resolved = path.resolve(strict=True)
    metadata = resolved.stat()
    return _canonical_sha256(
        {
            "path_sha256": _digest(str(resolved)),
            "mode": stat.S_IMODE(metadata.st_mode),
            "size": metadata.st_size,
            "content_sha256": hashlib.sha256(resolved.read_bytes()).hexdigest(),
        }
    )


def _account_identity_state_sha256(path: Path) -> str:
    resolved = path.resolve(strict=True)
    metadata = resolved.stat()
    return _canonical_sha256(
        {
            "path_sha256": _digest(str(resolved)),
            "kind": "directory" if resolved.is_dir() else "not-directory",
            "mode": stat.S_IMODE(metadata.st_mode),
            "device": metadata.st_dev,
            "inode": metadata.st_ino,
        }
    )


def _exact_path_snapshot(
    root: Path, *, exclude_top_level: frozenset[str] = frozenset()
) -> dict[str, object]:
    root = Path(root)
    if not root.exists() and not root.is_symlink():
        return {"kind": "missing", "entries": ()}
    if root.is_symlink():
        return {
            "kind": "symlink",
            "mode": stat.S_IMODE(root.lstat().st_mode),
            "target": os.readlink(root),
        }
    if root.is_file():
        return {
            "kind": "file",
            "mode": stat.S_IMODE(root.stat().st_mode),
            "bytes": root.read_bytes(),
        }

    entries: list[tuple[object, ...]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] in exclude_top_level:
            continue
        mode = stat.S_IMODE(path.lstat().st_mode)
        if path.is_symlink():
            entries.append((relative.as_posix(), "symlink", mode, os.readlink(path)))
        elif path.is_dir():
            entries.append((relative.as_posix(), "directory", mode))
        elif path.is_file():
            entries.append((relative.as_posix(), "file", mode, path.read_bytes()))
        else:
            entries.append((relative.as_posix(), "other", mode))
    return {
        "kind": "directory",
        "mode": stat.S_IMODE(root.stat().st_mode),
        "entries": tuple(entries),
    }


def _digestable_snapshot(value: object) -> object:
    if isinstance(value, bytes):
        return {
            "bytes": len(value),
            "sha256": hashlib.sha256(value).hexdigest(),
        }
    if isinstance(value, Mapping):
        return {str(key): _digestable_snapshot(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_digestable_snapshot(item) for item in value]
    return value


def _snapshot_sha256(value: object) -> str:
    return _canonical_sha256(_digestable_snapshot(value))


_REAL_POPEN = subprocess.Popen


def _run_git(
    cmd: list[str],
    *,
    cwd: Path,
    text: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    git_env = dict(os.environ if env is None else env)
    git_env["GIT_OPTIONAL_LOCKS"] = "0"
    p = _REAL_POPEN(
        cmd,
        cwd=cwd,
        env=git_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
    )
    stdout, stderr = p.communicate()
    ret = p.returncode if p.returncode is not None else 0
    if ret != 0:
        raise subprocess.CalledProcessError(ret, cmd, output=stdout, stderr=stderr)
    return subprocess.CompletedProcess(cmd, ret, stdout, stderr)


def _git_paths(root: Path) -> tuple[Path, Path]:
    p1 = _run_git(["git", "rev-parse", "--absolute-git-dir"], cwd=root, text=True)
    p2 = _run_git(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=root,
        text=True,
    )
    return Path(p1.stdout.strip()).resolve(), Path(p2.stdout.strip()).resolve()


def _git_control_snapshot(root: Path) -> dict[str, object]:
    git_dir, common_dir = _git_paths(root)

    def selected(directory: Path) -> dict[str, object]:
        return {
            "HEAD": _exact_path_snapshot(directory / "HEAD"),
            "index": _exact_path_snapshot(directory / "index"),
            "packed-refs": _exact_path_snapshot(directory / "packed-refs"),
            "refs": _exact_path_snapshot(directory / "refs"),
            "commondir": _exact_path_snapshot(directory / "commondir"),
            "gitdir": _exact_path_snapshot(directory / "gitdir"),
        }

    status = _run_git(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=root,
        text=False,
    )
    return {
        "worktree": _exact_path_snapshot(root, exclude_top_level=frozenset({".git"})),
        "dot_git": _exact_path_snapshot(root / ".git"),
        "git_dir": str(git_dir),
        "common_dir": str(common_dir),
        "gitdir_control": selected(git_dir),
        "common_control": selected(common_dir),
        "status_stdout": status.stdout,
        "status_stderr": status.stderr,
    }


def _worktree_snapshot(root: Path) -> str:
    return _snapshot_sha256(
        _exact_path_snapshot(root, exclude_top_level=frozenset({".git"}))
    )


def _git_metadata_snapshot(root: Path) -> str:
    evidence = _git_control_snapshot(root)
    return _snapshot_sha256(
        {
            "dot_git": evidence["dot_git"],
            "git_dir": evidence["git_dir"],
            "common_dir": evidence["common_dir"],
            "gitdir_control": evidence["gitdir_control"],
            "common_control": evidence["common_control"],
        }
    )


def _repository_integrity_evidence(root: Path) -> dict[str, str]:
    status = _run_git(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=root,
        text=True,
    ).stdout
    return {
        "worktree_sha256": _worktree_snapshot(root),
        "git_status_sha256": hashlib.sha256(status.encode("utf-8")).hexdigest(),
        "git_metadata_sha256": _git_metadata_snapshot(root),
    }


def _repository_snapshot(root: Path) -> str:
    return _canonical_sha256(_repository_integrity_evidence(root))


def _unknown_work_result(alias: str) -> dict[str, object]:
    return {
        "status": "BLOCKED",
        "scope_owned": [f"one-shot read-only operational lane {alias}"],
        "evidence": {
            "commands": ["provider command attempted with argv and raw streams elided"],
            "outcomes": ["provider outcome is indeterminate and must not be retried"],
            "artifacts": [f"durable UNKNOWN receipt for {alias}"],
        },
        "findings": ["no provider completion claim is available"],
        "changed_files": [],
        "residual_risk": (
            "provider side effects may have occurred; automatic retry is prohibited"
        ),
        "recommended_next_action": (
            "require human review; do not retry, fallback, or substitute this authorization"
        ),
    }


def _write_single_use_marker(
    marker_store: Path | str, name: str, record: Mapping[str, object]
) -> None:
    store = Path(marker_store).resolve()
    store.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(store, 0o700)
    marker_path = store / name
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(marker_path, flags, 0o600)
    try:
        content = _canonical_bytes(record) + b"\n"
        os.write(descriptor, content)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _cleanup_process(proc: subprocess.Popen, timeout: float = 0.5) -> None:
    try:
        pgid = os.getpgid(proc.pid)
    except OSError:
        pgid = proc.pid

    if proc.poll() is None:
        try:
            os.killpg(pgid, signal.SIGTERM)
        except OSError:
            pass
        try:
            proc.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, OSError):
            try:
                os.killpg(pgid, signal.SIGKILL)
            except OSError:
                pass
            try:
                proc.wait(timeout=timeout)
            except (subprocess.TimeoutExpired, OSError):
                pass


def _agy_stdin(prompt: str) -> bytes:
    return (
        json.dumps(
            {"event": "user", "message": {"content": prompt}},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _build_receipt(
    alias: str,
    lane: Mapping[str, Any],
    authorization: Mapping[str, Any],
    *,
    status: str,
    started_at: str | None,
    ended_at: str,
    exit_code: int | None,
    output_bytes: int,
    process_or_session_id: str | None,
    work_result: Mapping[str, Any],
    payload_bytes: bytes = b"",
) -> dict[str, Any]:
    provider, root = _ALIASES[alias]
    binding = authorization["bindings"][alias]
    adapter = (
        "codex-jsonl-output-schema-v2"
        if provider == "codex"
        else "agy-stream-json-schema-v2"
    )
    if status == "UNKNOWN":
        evidence_scope = "not validated"
    else:
        evidence_scope = (
            "provider-native validated"
            if provider == "codex"
            else "validated in-process only"
        )

    output_sha256 = (
        hashlib.sha256(payload_bytes).hexdigest()
        if status == "DONE"
        else hashlib.sha256(b"").hexdigest()
    )

    return {
        "protocol_version": 2,
        "authorization_id": authorization["authorization_id"],
        "authorization_sha256": _canonical_sha256(authorization),
        "risk_id": authorization["risk_id"],
        "control_session_nonce_sha256": authorization[
            "control_session_nonce_sha256"
        ],
        "ticket": authorization["ticket"],
        "request_id": lane["job"].request_id,
        "root": root,
        "alias": alias,
        "provider": provider,
        "attempt": 1,
        "max_attempts": 1,
        "work_mode": "read_only",
        "objective": authorization["objective"],
        "ownership": authorization["ownership"],
        "qobs_quota_band": lane["request"]["qobs_quota_band"],
        "decision_sha256": binding["decision_sha256"],
        "scheduling_snapshot_sha256": binding["scheduling_snapshot_sha256"],
        "qobs_artifact_sha256": binding["qobs_artifact_sha256"],
        "nonce_sha256": binding["nonce_sha256"],
        "resolved_executable_sha256": binding["resolved_executable_sha256"],
        "resolved_executable_identity_sha256": binding[
            "resolved_executable_identity_sha256"
        ],
        "account_identity_sha256": binding["account_identity_sha256"],
        "account_identity_state_sha256": binding[
            "account_identity_state_sha256"
        ],
        "qobs_context_sha256": binding["qobs_context_sha256"],
        "capacity_lease_sha256": binding["capacity_lease_sha256"],
        "capacity_state_sha256": binding["capacity_state_sha256"],
        "lease_risk_sha256": binding["lease_risk_sha256"],
        "repository_snapshot_sha256": authorization["repository_snapshot_sha256"],
        "adapter": adapter,
        "process_or_session_id": process_or_session_id,
        "started_at": started_at,
        "ended_at": ended_at,
        "exit_code": exit_code,
        "transport_status": "COMPLETED" if status == "DONE" else "UNKNOWN",
        "output_bytes": output_bytes,
        "output_sha256": output_sha256,
        "work_result_sha256": _canonical_sha256(work_result),
        "evidence_scope": evidence_scope,
    }


def execute_idq_mvp_080_operational(
    *,
    config: Mapping[str, Any],
    authorization: Mapping[str, Any],
    lanes: Mapping[str, Any],
    store: Any,
    marker_store: Path | str | os.PathLike[str],
    repository_root: Path | str | os.PathLike[str],
    timeout_seconds: float | int,
    now: datetime,
) -> dict[str, Any]:
    """Execute the bounded, multi-lane operational provider batch for IDQ-MVP-080."""
    # -------------------------------------------------------------------------
    # 1. Preflight Phase (Must fail closed with ValueError and zero side effects)
    # -------------------------------------------------------------------------
    if not isinstance(config, Mapping):
        raise ValueError("config must be a mapping")
    if config.get("activation_prohibited") is not True or config.get("dispatcher_execution") != "CLOSED":
        raise ValueError("IDQ-MVP-080 requires ordinary activation CLOSED")

    idq_config = config.get("idq_mvp_080")
    if not isinstance(idq_config, Mapping):
        raise ValueError("idq_mvp_080 config is missing or not a mapping")
    if idq_config.get("ticket") != _TICKET:
        raise ValueError("Ticket mismatch in idq_mvp_080 config")

    auth_contract = idq_config.get("authorization_contract")
    if not isinstance(auth_contract, Mapping):
        raise ValueError("authorization_contract missing or not a mapping")
    if (
        auth_contract.get("schema_version") != _AUTHORIZATION_SCHEMA_VERSION
        or auth_contract.get("protocol_version") != _AUTHORIZATION_PROTOCOL_VERSION
        or auth_contract.get("authorization_id") != _AUTHORIZATION_ID
        or auth_contract.get("objective") != _AUTHORIZATION_OBJECTIVE
        or auth_contract.get("ownership") != _AUTHORIZATION_OWNERSHIP
        or auth_contract.get("risk_id") != _AUTHORIZATION_RISK_ID
        or auth_contract.get("ttl_seconds") != _AUTHORIZATION_TTL_SECONDS
    ):
        raise ValueError("authorization_contract fields do not match closed policy")

    config_aliases = idq_config.get("aliases")
    if not isinstance(config_aliases, Mapping) or set(config_aliases) != set(_ALIASES):
        raise ValueError("Config aliases must be exactly the four allowlisted aliases")
    for alias, (provider, _root) in _ALIASES.items():
        entry = config_aliases.get(alias)
        if not isinstance(entry, Mapping) or dict(entry) != {
            "provider": provider,
            "attempt": 1,
            "work_mode": "read_only",
            "automatic_retry": False,
            "fallback": False,
        }:
            raise ValueError(f"Config alias {alias} entry invalid")

    # Validate authorization structure
    if not isinstance(authorization, Mapping):
        raise ValueError("authorization must be a mapping")
    if set(authorization) != _AUTHORIZATION_FIELDS:
        raise ValueError("authorization top-level fields do not match contract")

    if (
        authorization.get("schema_version") != _AUTHORIZATION_SCHEMA_VERSION
        or authorization.get("protocol_version") != _AUTHORIZATION_PROTOCOL_VERSION
        or authorization.get("authorization_id") != _AUTHORIZATION_ID
        or authorization.get("ticket") != _TICKET
        or authorization.get("status") != "UNUSED"
        or authorization.get("aliases") != list(_ALIAS_ORDER)
        or authorization.get("attempt") != 1
        or isinstance(authorization.get("attempt"), bool)
        or authorization.get("max_attempts") != 1
        or isinstance(authorization.get("max_attempts"), bool)
        or authorization.get("work_mode") != "read_only"
        or authorization.get("automatic_retry") is not False
        or authorization.get("fallback") is not False
        or authorization.get("substitution") is not False
        or authorization.get("objective") != _AUTHORIZATION_OBJECTIVE
        or authorization.get("ownership") != _AUTHORIZATION_OWNERSHIP
        or authorization.get("risk_id") != _AUTHORIZATION_RISK_ID
        or authorization.get("ttl_seconds") != _AUTHORIZATION_TTL_SECONDS
    ):
        raise ValueError("authorization metadata fields invalid")

    _sha256_hex(authorization.get("control_session_nonce_sha256"), "control_session_nonce_sha256")
    _sha256_hex(authorization.get("repository_snapshot_sha256"), "repository_snapshot_sha256")
    _sha256_hex(authorization.get("marker_store_sha256"), "marker_store_sha256")

    marker_store_path = Path(marker_store)
    if not marker_store_path.is_absolute():
        raise ValueError("marker_store must be an absolute path")
    if _digest(str(marker_store_path.resolve())) != authorization["marker_store_sha256"]:
        raise ValueError("marker_store_sha256 mismatch")

    now_utc = now.astimezone(timezone.utc)
    issued_at_dt = _parse_timestamp(authorization["issued_at"])
    expires_at_dt = _parse_timestamp(authorization["expires_at"])
    if (expires_at_dt - issued_at_dt).total_seconds() != authorization["ttl_seconds"]:
        raise ValueError("expires_at does not match issued_at + ttl_seconds")
    if issued_at_dt > now_utc + timedelta(seconds=60):
        raise ValueError("authorization issued_at is in the future")
    if now_utc >= expires_at_dt:
        raise ValueError("authorization is expired")
    if (now_utc - issued_at_dt).total_seconds() > authorization["ttl_seconds"]:
        raise ValueError("authorization age exceeds ttl_seconds")

    # Validate bindings in authorization
    bindings = authorization.get("bindings")
    if not isinstance(bindings, Mapping) or set(bindings) != set(_ALIASES):
        raise ValueError("authorization bindings must match exactly allowlisted aliases")
    for alias, (provider, root) in _ALIASES.items():
        binding = bindings.get(alias)
        if not isinstance(binding, Mapping) or set(binding) != _AUTHORIZATION_BINDING_FIELDS:
            raise ValueError(f"binding for {alias} invalid")
        if binding.get("provider") != provider or binding.get("root") != root:
            raise ValueError(f"binding for {alias} provider or root mismatch")
        for field in _AUTHORIZATION_BINDING_FIELDS:
            if field.endswith("_sha256"):
                _sha256_hex(binding.get(field), f"{alias}.{field}")

    # Validate repository snapshot
    repo_root = Path(repository_root).resolve()
    current_repo_snapshot = _repository_snapshot(repo_root)
    if current_repo_snapshot != authorization["repository_snapshot_sha256"]:
        raise ValueError("repository snapshot mismatch")

    # Validate marker store before touch (ensure no pre-created markers or symlinks)
    if marker_store_path.exists():
        if marker_store_path.is_symlink():
            raise ValueError("marker_store cannot be a symlink")
        auth_marker_name = f"idq-mvp-080-auth-{_digest(_AUTHORIZATION_ID)}.used"
        if (marker_store_path / auth_marker_name).exists() or (marker_store_path / auth_marker_name).is_symlink():
            raise ValueError("authorization marker already used or replayed")
        for alias in _ALIAS_ORDER:
            b = bindings[alias]
            qobs_marker = f"idq-mvp-080-qobs-{b['nonce_sha256']}.used"
            alias_marker = f"idq-mvp-080-{alias}.used"
            for m in (qobs_marker, alias_marker):
                if (marker_store_path / m).exists() or (marker_store_path / m).is_symlink():
                    raise ValueError(f"marker {m} already used or replayed")
        for item in marker_store_path.glob("*.used"):
            raise ValueError(f"marker file {item.name} already exists in marker store")

    # Validate lanes
    if not isinstance(lanes, Mapping) or set(lanes) != set(_ALIASES):
        raise ValueError("lanes must match exactly allowlisted aliases")

    auth_sha256 = _canonical_sha256(authorization)
    for alias, (provider, root) in _ALIASES.items():
        lane = lanes[alias]
        if not isinstance(lane, Mapping):
            raise ValueError(f"lane {alias} is not a mapping")
        job = lane.get("job")
        if job is None or job.alias != alias or job.root != root or job.attempt != 1:
            raise ValueError(f"lane {alias} job identity mismatch")

        # Check against durable queue authority
        queue_job = store.get_job(job.request_id)
        if queue_job is None:
            raise ValueError(f"lane {alias} job not found in durable queue")
        if (
            queue_job.alias != alias
            or queue_job.root != root
            or queue_job.attempt != 1
        ):
            raise ValueError(f"queue job for {alias} identity mismatch")

        binding = bindings[alias]
        if binding["request_id"] != job.request_id:
            raise ValueError(f"binding request_id mismatch for {alias}")

        expected_job_payload = {
            "schema_version": "idq-mvp-080-job-authority-v1",
            "authorization_id": _AUTHORIZATION_ID,
            "authorization_sha256": auth_sha256,
            "authorization_binding_sha256": _canonical_sha256(binding),
            "objective_sha256": _digest(_AUTHORIZATION_OBJECTIVE),
        }
        if queue_job.payload != expected_job_payload or job.payload != expected_job_payload:
            raise ValueError(f"job payload mismatch for {alias}")

        request = lane.get("request")
        if not isinstance(request, Mapping):
            raise ValueError(f"lane {alias} request is not a mapping")
        if (
            request.get("ticket") != _TICKET
            or request.get("authorization_id") != _AUTHORIZATION_ID
            or request.get("alias") != alias
            or request.get("provider") != provider
            or request.get("attempt") != 1
            or isinstance(request.get("attempt"), bool)
            or request.get("work_mode") != "read_only"
            or request.get("automatic_retry") is not False
            or request.get("fallback") is not False
            or request.get("objective") != _AUTHORIZATION_OBJECTIVE
            or request.get("ownership") != _AUTHORIZATION_OWNERSHIP
            or request.get("risk_id") != _AUTHORIZATION_RISK_ID
            or request.get("control_session_nonce_sha256") != authorization["control_session_nonce_sha256"]
            or request.get("qobs_quota_band") != "constrained"
        ):
            raise ValueError(f"lane {alias} request metadata mismatch")

        for f in _AUTHORIZATION_BINDING_FIELDS:
            if f in request and request[f] != binding[f]:
                raise ValueError(f"lane {alias} request field {f} does not match binding")

        # Execution context and QOBS
        exec_ctx = lane.get("execution_context")
        if not isinstance(exec_ctx, Mapping) or set(exec_ctx) != {"qobs_artifact", "qobs_expected_context", "runtime"}:
            raise ValueError(f"lane {alias} execution_context invalid")
        qobs_ctx = exec_ctx.get("qobs_expected_context")
        if not isinstance(qobs_ctx, Mapping):
            raise ValueError(f"lane {alias} qobs_expected_context invalid")
        if (
            qobs_ctx.get("alias") != alias
            or qobs_ctx.get("provider") != provider
            or qobs_ctx.get("ticket_id") != _TICKET
            or qobs_ctx.get("attempt_id") != 1
            or isinstance(qobs_ctx.get("attempt_id"), bool)
        ):
            raise ValueError(f"lane {alias} qobs context fields mismatch")
        if _canonical_sha256(qobs_ctx) != binding["qobs_context_sha256"]:
            raise ValueError(f"lane {alias} qobs_context_sha256 mismatch")

        artifact = exec_ctx.get("qobs_artifact")
        if quota.quota_artifact_sha256(artifact) != request["qobs_artifact_sha256"]:
            raise ValueError(f"lane {alias} qobs_artifact_sha256 mismatch")
        if quota.sha256_text(str(qobs_ctx.get("nonce"))) != request["nonce_sha256"]:
            raise ValueError(f"lane {alias} nonce_sha256 mismatch")
        if quota.sha256_text(str(qobs_ctx.get("resolved_executable"))) != request["resolved_executable_sha256"]:
            raise ValueError(f"lane {alias} resolved_executable_sha256 mismatch")
        if quota.sha256_text(str(qobs_ctx.get("account_home"))) != request["account_identity_sha256"]:
            raise ValueError(f"lane {alias} account_identity_sha256 mismatch")

        observation = quota.validate_quota_observation(artifact, dict(qobs_ctx), now=now)
        if observation.get("quota_band") != request["qobs_quota_band"]:
            raise ValueError(f"lane {alias} quota band mismatch")

        runtime = exec_ctx.get("runtime")
        if provider == "codex":
            if dict(runtime) != {"read_only": True, "sandbox": "read-only"}:
                raise ValueError(f"lane {alias} runtime mismatch")
        else:
            if dict(runtime) != {"read_only": True, "mode": "plan", "sandbox": True}:
                raise ValueError(f"lane {alias} runtime mismatch")

        # Check executable and account_home state
        executable_path = Path(str(qobs_ctx.get("resolved_executable")))
        if not executable_path.is_file():
            raise ValueError(f"lane {alias} executable missing")
        if _executable_identity_sha256(executable_path) != request["resolved_executable_identity_sha256"]:
            raise ValueError(f"lane {alias} executable identity mismatch")

        account_home_path = Path(str(qobs_ctx.get("account_home")))
        if not account_home_path.is_dir():
            raise ValueError(f"lane {alias} account home missing")
        if _account_identity_state_sha256(account_home_path) != request["account_identity_state_sha256"]:
            raise ValueError(f"lane {alias} account identity state mismatch")

        # Capacity lease and state
        cap_lease = lane.get("capacity_lease")
        if not isinstance(cap_lease, Mapping):
            raise ValueError(f"lane {alias} capacity_lease invalid")
        if (
            cap_lease.get("account") != alias
            or cap_lease.get("pool") != alias
            or cap_lease.get("provider") != provider
            or cap_lease.get("request_id") != job.request_id
        ):
            raise ValueError(f"lane {alias} capacity lease identity mismatch")
        if cap_lease.get("lease_sha256") != binding["capacity_lease_sha256"]:
            raise ValueError(f"lane {alias} capacity lease sha256 mismatch")

        cap_store_path = Path(lane.get("capacity_store_path"))
        cap_state_file = cap_store_path / ".capacity.json"
        if not cap_state_file.is_file():
            raise ValueError(f"lane {alias} capacity state file missing")
        cap_state = json.loads(cap_state_file.read_text(encoding="ascii"))
        validated_cap_state = capacity.validate_capacity_state(cap_state, lane.get("capacity_policy"))
        lease_id = cap_lease.get("lease_id")
        if lease_id not in validated_cap_state["leases"]:
            raise ValueError(f"lane {alias} lease not active in capacity store")
        if validated_cap_state["leases"][lease_id] != cap_lease:
            raise ValueError(f"lane {alias} lease does not match capacity store")
        if float(cap_lease.get("expires_at", 0)) <= now.timestamp():
            raise ValueError(f"lane {alias} lease expired")
        if _snapshot_sha256(_exact_path_snapshot(cap_store_path)) != binding["capacity_state_sha256"]:
            raise ValueError(f"lane {alias} capacity state snapshot mismatch")

    # -------------------------------------------------------------------------
    # 2. Durable PREPARED Transition
    # -------------------------------------------------------------------------
    for alias in _ALIAS_ORDER:
        lane = lanes[alias]
        store.transition(lane["job"].request_id, fence=lane["job"].fence, state="PREPARED")

    # -------------------------------------------------------------------------
    # 3. Marker Store Single-Use Markers
    # -------------------------------------------------------------------------
    marker_records: list[tuple[str, dict[str, object]]] = [
        (
            f"idq-mvp-080-auth-{_digest(_AUTHORIZATION_ID)}.used",
            {
                "schema_version": 1,
                "marker_kind": "authorization",
                "authorization_id": _AUTHORIZATION_ID,
                "authorization_sha256": auth_sha256,
                "ticket": _TICKET,
                "control_session_nonce_sha256": authorization["control_session_nonce_sha256"],
                "repository_snapshot_sha256": current_repo_snapshot,
            },
        )
    ]
    for alias in _ALIAS_ORDER:
        b = bindings[alias]
        marker_records.append(
            (
                f"idq-mvp-080-qobs-{b['nonce_sha256']}.used",
                {
                    "schema_version": 1,
                    "marker_kind": "qobs_nonce",
                    "authorization_id": _AUTHORIZATION_ID,
                    "authorization_sha256": auth_sha256,
                    "alias": alias,
                    "request_id": b["request_id"],
                    "qobs_artifact_sha256": b["qobs_artifact_sha256"],
                    "nonce_sha256": b["nonce_sha256"],
                },
            )
        )
        marker_records.append(
            (
                f"idq-mvp-080-{alias}.used",
                {
                    "schema_version": 1,
                    "marker_kind": "alias_binding",
                    "authorization_id": _AUTHORIZATION_ID,
                    "authorization_sha256": auth_sha256,
                    "alias": alias,
                    "request_id": b["request_id"],
                    "authorization_binding_sha256": _canonical_sha256(b),
                    "capacity_lease_sha256": b["capacity_lease_sha256"],
                },
            )
        )

    marker_write_failed = False
    for name, record in marker_records:
        try:
            _write_single_use_marker(marker_store_path, name, record)
        except Exception:
            marker_write_failed = True
            break

    if marker_write_failed:
        outcomes: dict[str, Any] = {}
        for alias in _ALIAS_ORDER:
            lane = lanes[alias]
            capacity.release_lease(
                lane["capacity_store_path"],
                lane["capacity_lease"],
                policy=lane["capacity_policy"],
                now=now.timestamp(),
            )
            u_res = _unknown_work_result(alias)
            rcpt = _build_receipt(
                alias,
                lane,
                authorization,
                status="UNKNOWN",
                started_at=None,
                ended_at=_timestamp(now),
                exit_code=None,
                output_bytes=0,
                process_or_session_id=None,
                work_result=u_res,
            )
            store.complete(
                request_id=lane["job"].request_id,
                fence=lane["job"].fence,
                instance_id=lane["instance_id"],
                result=u_res,
                receipt=rcpt,
                state="UNKNOWN",
            )
            outcomes[alias] = {
                "status": "UNKNOWN",
                "receipt": rcpt,
                "work_result": u_res,
            }
        return {
            "authorization_id": _AUTHORIZATION_ID,
            "authorization_status": "SEALED",
            "ticket": _TICKET,
            "status": "UNKNOWN",
            "attempt": 1,
            "ordinary_activation": "CLOSED",
            "repository_snapshot_sha256": current_repo_snapshot,
            "aliases": outcomes,
        }

    # -------------------------------------------------------------------------
    # 4. Prepare Schema and Start Concurrent Processes
    # -------------------------------------------------------------------------
    schema_source_path = repo_root / ".agents/schemas/multiagent-work-result-v2.schema.json"
    schema_dict = command._provider_compatible_work_result_schema(schema_source_path)
    schema_bytes = _canonical_bytes(schema_dict)

    temp_dirs: list[str] = []
    schema_files: dict[str, Path] = {}
    current_leases: dict[str, Any] = {}
    procs: dict[str, subprocess.Popen] = {}
    attempted_aliases: list[str] = []
    start_times: dict[str, datetime] = {}
    popen_failed = False

    try:
        for alias in _ALIAS_ORDER:
            td = tempfile.mkdtemp(prefix="horo-idq-provider-schema-")
            os.chmod(td, 0o700)
            temp_dirs.append(td)
            sf = Path(td) / "work-result-v2.provider.json"
            sf.write_bytes(schema_bytes)
            os.chmod(sf, 0o600)
            schema_files[alias] = sf

        for alias in _ALIAS_ORDER:
            lane = lanes[alias]
            attempted_aliases.append(alias)
            start_times[alias] = now.astimezone(timezone.utc)

            # Consume capacity lease immediately before STARTING and Popen
            consumed_lease = capacity.consume_lease(
                lane["capacity_store_path"],
                lane["capacity_lease"],
                requests=1,
                policy=lane["capacity_policy"],
                now=now.timestamp(),
                request_id=lane["job"].request_id,
            )
            current_leases[alias] = consumed_lease

            # Transition to STARTING
            store.transition(
                lane["job"].request_id,
                fence=lane["job"].fence,
                state="STARTING",
                instance_id=lane["instance_id"],
            )

            # Build provider execution arguments and environment
            provider, _root = _ALIASES[alias]
            qobs_ctx = lane["execution_context"]["qobs_expected_context"]
            executable = str(qobs_ctx["resolved_executable"])
            account_home = str(qobs_ctx["account_home"])
            schema_path_str = str(schema_files[alias])

            if provider == "codex":
                argv = (
                    executable,
                    "exec",
                    "-C",
                    str(repo_root),
                    "-s",
                    "read-only",
                    "--json",
                    "--output-schema",
                    schema_path_str,
                    "-",
                )
                home_env = "CODEX_HOME"
                stdin_payload = lane["prompt_stdin"].encode("utf-8")
            else:
                argv = (
                    executable,
                    "--mode",
                    "plan",
                    "--sandbox",
                    "--print",
                    "--input-format",
                    "stream-json",
                    "--output-format",
                    "stream-json",
                    "--json-schema",
                    schema_path_str,
                )
                home_env = "AGY_HOME"
                stdin_payload = _agy_stdin(lane["prompt_stdin"])

            sanitized_env = {
                k: os.environ[k]
                for k in _SAFE_PROVIDER_ENV_KEYS
                if k in os.environ
            }
            sanitized_env[home_env] = account_home

            try:
                proc = subprocess.Popen(
                    argv,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=False,
                    bufsize=0,
                    cwd=str(repo_root),
                    shell=False,
                    start_new_session=True,
                    env=sanitized_env,
                )
                procs[alias] = proc
            except Exception:
                popen_failed = True
                break

            # Transition to RUNNING
            store.transition(
                lane["job"].request_id,
                fence=lane["job"].fence,
                state="RUNNING",
                instance_id=lane["instance_id"],
            )

            # Write and close stdin
            proc.stdin.write(stdin_payload)
            proc.stdin.flush()
            proc.stdin.close()

        if popen_failed:
            for p in procs.values():
                _cleanup_process(p)
            outcomes = {}
            for alias in _ALIAS_ORDER:
                lane = lanes[alias]
                lease_to_rel = current_leases.get(alias, lane["capacity_lease"])
                capacity.release_lease(
                    lane["capacity_store_path"],
                    lease_to_rel,
                    policy=lane["capacity_policy"],
                    now=now.timestamp(),
                )
                st_at = _timestamp(start_times[alias]) if alias in start_times else None
                end_dt = (start_times[alias] + timedelta(seconds=1)) if alias in start_times else now_utc
                u_res = _unknown_work_result(alias)
                rcpt = _build_receipt(
                    alias,
                    lane,
                    authorization,
                    status="UNKNOWN",
                    started_at=st_at,
                    ended_at=_timestamp(end_dt),
                    exit_code=None,
                    output_bytes=0,
                    process_or_session_id=None,
                    work_result=u_res,
                )
                store.complete(
                    request_id=lane["job"].request_id,
                    fence=lane["job"].fence,
                    instance_id=lane["instance_id"],
                    result=u_res,
                    receipt=rcpt,
                    state="UNKNOWN",
                )
                outcomes[alias] = {
                    "status": "UNKNOWN",
                    "receipt": rcpt,
                    "work_result": u_res,
                }
            return {
                "authorization_id": _AUTHORIZATION_ID,
                "authorization_status": "SEALED",
                "ticket": _TICKET,
                "status": "UNKNOWN",
                "attempt": 1,
                "ordinary_activation": "CLOSED",
                "repository_snapshot_sha256": current_repo_snapshot,
                "aliases": outcomes,
            }

        # Provider processes are fully admitted at this point.  Restore the
        # real subprocess constructor before capture begins so repository
        # integrity callbacks (including Git probes) cannot be redirected
        # through a provider factory that temporarily patches the shared
        # subprocess module in tests.
        subprocess.Popen = _REAL_POPEN

        # ---------------------------------------------------------------------
        # 5. Incremental Stream Capture and Process Supervision
        # ---------------------------------------------------------------------
        stdout_buffers: dict[str, list[bytes]] = {alias: [] for alias in _ALIAS_ORDER}
        stderr_buffers: dict[str, list[bytes]] = {alias: [] for alias in _ALIAS_ORDER}
        cap_exceeded: dict[str, bool] = {alias: False for alias in _ALIAS_ORDER}
        threads: list[threading.Thread] = []

        def make_stream_reader(alias: str, stream_name: str, stream: Any, cap: int, target_buffer: list[bytes]) -> threading.Thread:
            def reader():
                total = 0
                proc = procs[alias]
                try:
                    while True:
                        chunk = stream.read(PROVIDER_READ_CHUNK_BYTES)
                        if not chunk:
                            break
                        target_buffer.append(chunk)
                        total += len(chunk)
                        if total > cap:
                            cap_exceeded[alias] = True
                            _cleanup_process(proc)
                            break
                except Exception:
                    pass
                finally:
                    try:
                        stream.close()
                    except Exception:
                        pass
            t = threading.Thread(target=reader, daemon=True)
            t.start()
            return t

        for alias in _ALIAS_ORDER:
            proc = procs[alias]
            threads.append(make_stream_reader(alias, "stdout", proc.stdout, MAX_PROVIDER_OUTPUT_BYTES, stdout_buffers[alias]))
            threads.append(make_stream_reader(alias, "stderr", proc.stderr, MAX_PROVIDER_STDERR_BYTES, stderr_buffers[alias]))

        deadline = time.monotonic() + float(timeout_seconds)
        timed_out: dict[str, bool] = {alias: False for alias in _ALIAS_ORDER}

        for alias in _ALIAS_ORDER:
            proc = procs[alias]
            remaining = max(0.0, deadline - time.monotonic())
            try:
                proc.wait(timeout=remaining)
            except (subprocess.TimeoutExpired, OSError):
                timed_out[alias] = True
                _cleanup_process(proc)

        for t in threads:
            t.join(timeout=0.5)

        for alias in _ALIAS_ORDER:
            _cleanup_process(procs[alias], timeout=0.2)

        # ---------------------------------------------------------------------
        # 6. Parse and Validate Output Payloads
        # ---------------------------------------------------------------------
        lane_statuses: dict[str, str] = {}
        parsed_results: dict[str, Any] = {}
        end_times: dict[str, datetime] = {}

        for alias in _ALIAS_ORDER:
            proc = procs[alias]
            st_dt = start_times[alias]
            end_dt = datetime.now(timezone.utc).replace(microsecond=0)
            if end_dt <= st_dt:
                end_dt = st_dt + timedelta(seconds=1)
            end_times[alias] = end_dt

            if timed_out[alias] or cap_exceeded[alias] or proc.returncode != 0:
                lane_statuses[alias] = "UNKNOWN"
                continue

            stdout_bytes = b"".join(stdout_buffers[alias])
            if len(stdout_bytes) > MAX_PROVIDER_OUTPUT_BYTES:
                lane_statuses[alias] = "UNKNOWN"
                continue

            provider, _root = _ALIASES[alias]
            try:
                if provider == "codex":
                    parsed = command._parse_codex_result(stdout_bytes)
                else:
                    parsed = command._parse_agy_result(stdout_bytes)
                normalized = command.normalize_result(parsed.work_result)
                if normalized.get("status") != "DONE" or set(normalized) != _WORK_RESULT_FIELDS:
                    raise ValueError("WorkResult schema invalid")
                lane_statuses[alias] = "DONE"
                parsed_results[alias] = (parsed, normalized, stdout_bytes)
            except Exception:
                lane_statuses[alias] = "UNKNOWN"

        # ---------------------------------------------------------------------
        # 7. Post-Execution Repository Integrity Verification
        # ---------------------------------------------------------------------
        after_snapshot = _repository_snapshot(repo_root)
        if after_snapshot != current_repo_snapshot:
            for alias in _ALIAS_ORDER:
                lane_statuses[alias] = "UNKNOWN"

        # ---------------------------------------------------------------------
        # 8. Finalize Batch and Durable Queue Records
        # ---------------------------------------------------------------------
        batch_status = "DONE" if all(s == "DONE" for s in lane_statuses.values()) else "UNKNOWN"
        outcomes = {}

        for alias in _ALIAS_ORDER:
            lane = lanes[alias]
            status = lane_statuses[alias]

            # Capacity release happens before store.complete terminal event
            capacity.release_lease(
                lane["capacity_store_path"],
                current_leases[alias],
                policy=lane["capacity_policy"],
                now=now.timestamp(),
            )

            if status == "DONE":
                parsed, work_res, stdout_bytes = parsed_results[alias]
                rcpt = _build_receipt(
                    alias,
                    lane,
                    authorization,
                    status="DONE",
                    started_at=_timestamp(start_times[alias]),
                    ended_at=_timestamp(end_times[alias]),
                    exit_code=0,
                    output_bytes=len(stdout_bytes),
                    process_or_session_id=parsed.process_or_session_id,
                    work_result=work_res,
                    payload_bytes=stdout_bytes,
                )
            else:
                work_res = _unknown_work_result(alias)
                rcpt = _build_receipt(
                    alias,
                    lane,
                    authorization,
                    status="UNKNOWN",
                    started_at=_timestamp(start_times[alias]),
                    ended_at=_timestamp(end_times[alias]),
                    exit_code=None,
                    output_bytes=0,
                    process_or_session_id=None,
                    work_result=work_res,
                    payload_bytes=b"",
                )

            store.complete(
                request_id=lane["job"].request_id,
                fence=lane["job"].fence,
                instance_id=lane["instance_id"],
                result=work_res,
                receipt=rcpt,
                state=status,
            )
            outcomes[alias] = {
                "status": status,
                "receipt": rcpt,
                "work_result": work_res,
            }

        return {
            "authorization_id": _AUTHORIZATION_ID,
            "authorization_status": "SEALED",
            "ticket": _TICKET,
            "status": batch_status,
            "attempt": 1,
            "ordinary_activation": "CLOSED",
            "repository_snapshot_sha256": current_repo_snapshot,
            "aliases": outcomes,
        }

    finally:
        for sf in schema_files.values():
            try:
                if sf.exists():
                    sf.unlink()
            except Exception:
                pass
        for td in temp_dirs:
            try:
                p = Path(td)
                if p.exists():
                    p.rmdir()
            except Exception:
                pass

# IDQ-OP-020-EXECUTOR: baseline-bounded operational executor implemented
