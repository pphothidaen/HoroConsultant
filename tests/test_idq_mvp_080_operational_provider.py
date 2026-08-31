"""RED contract for the real, bounded IDQ-MVP-080 provider executor.

Skipped: scripts/multiagent_idq_mvp_080_operational.py not yet implemented.
Restore skip markers when implementation is ready.

The future source is deliberately isolated in
``scripts.multiagent_idq_mvp_080_operational``.  These tests use genuine local
QOBS artifacts, capacity leases, and the SQLite durable queue.  The production
boundary remains the module-owned ``subprocess.Popen``; tests monkeypatch that
exact boundary with local pipe-shaped processes.  They never resolve
credentials, invoke a provider, or retain provider streams.

Required public seam::

    execute_idq_mvp_080_operational(
        *, config, authorization, lanes, store, marker_store,
        repository_root, timeout_seconds, now
    )

The batch must validate every lane before the first process start.  A lane is
durably PREPARED, then STARTING immediately before ``Popen``, and RUNNING only
after ``Popen`` returns.  A post-start ambiguity is durable UNKNOWN with one
typed BLOCKED WorkResult and no retry, fallback, substitution, or raw output.
"""

from __future__ import annotations

import sys
import pytest

# pytest.skip(
#     "scripts/multiagent_idq_mvp_080_operational.py not yet implemented",
#     allow_module_level=True,
# )

import hashlib
import importlib
import inspect
import json
import os
import signal
import sqlite3
import stat
import subprocess
import threading
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import asdict, is_dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

import scripts.agent_quota_status_guard as quota
import scripts.multiagent_capacity as capacity
import scripts.multiagent_prompt_command as command
from scripts.multiagent_durable_queue import DurableQueue

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = REPOSITORY_ROOT / "scripts/multiagent_idq_mvp_080_operational.py"
TICKET = "IDQ-MVP-080"
AUTHORIZATION_ID = "IDQ-MVP-080-AUTH-02"
AUTHORIZATION_SCHEMA_VERSION = "idq-mvp-080-auth-v1"
AUTHORIZATION_PROTOCOL_VERSION = 2
AUTHORIZATION_OBJECTIVE = "one bounded read-only repository inventory per alias"
AUTHORIZATION_OWNERSHIP = "no repository files; terminal metadata only"
AUTHORIZATION_RISK_ID = "RISK-IDQ-MVP-080-20260830-02"
ALIASES = {
    "codex1": ("codex", "A"),
    "codex2": ("codex", "A"),
    "agy1": ("agy", "B"),
    "agy2": ("agy", "B"),
}
RAW_SENTINEL = "provider-raw-frame-must-not-persist"
STDERR_SENTINEL = "provider-raw-stderr-must-not-persist"
PROMPT_SENTINEL = "provider-prompt-body-must-not-persist"
INHERITED_ENV_SENTINEL = "inherited-environment-must-not-escape"
TERMINAL_SENTINEL = "terminal-failure-detail-must-not-escape"
PROVIDER_SENTINEL = "provider-identity-detail-must-not-escape"
ACCOUNT_SENTINEL = "account-identity-detail-must-not-escape"
TIMEOUT_SECONDS = 2.0
OUTPUT_CAP_BYTES = command.MAX_PROVIDER_OUTPUT_BYTES
STDERR_CAP_BYTES = 64 * 1024
MAX_READ_CHUNK_BYTES = 64 * 1024
AUTHORIZATION_TTL_SECONDS = 1800
SAFE_PROVIDER_ENV_KEYS = {
    "PATH",
    "LANG",
    "LC_ALL",
    "TMPDIR",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "NO_COLOR",
}

AUTHORIZATION_FIELDS = {
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
}
AUTHORIZATION_BINDING_FIELDS = {
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
}
RECEIPT_FIELDS = {
    "protocol_version",
    "authorization_id",
    "authorization_sha256",
    "risk_id",
    "control_session_nonce_sha256",
    "ticket",
    "request_id",
    "root",
    "alias",
    "provider",
    "attempt",
    "max_attempts",
    "work_mode",
    "objective",
    "ownership",
    "qobs_quota_band",
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
    "repository_snapshot_sha256",
    "adapter",
    "process_or_session_id",
    "started_at",
    "ended_at",
    "exit_code",
    "transport_status",
    "output_bytes",
    "output_sha256",
    "work_result_sha256",
    "evidence_scope",
}
WORK_RESULT_FIELDS = {
    "status",
    "scope_owned",
    "evidence",
    "findings",
    "changed_files",
    "residual_risk",
    "recommended_next_action",
}
WORK_RESULT_EVIDENCE_FIELDS = {"commands", "outcomes", "artifacts"}
REPOSITORY_KINDS = ("normal", "linked")
REPOSITORY_MUTATIONS = (
    "tracked_file",
    "index_only",
    "ref_only",
    "head_only",
    "common_ref",
)


def _operational() -> Any:
    """Import the owned source lazily so the sentinel has a stable red."""

    return importlib.import_module("scripts.multiagent_idq_mvp_080_operational")


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


def _expected_provider_schema(authoritative_path: Path) -> dict[str, object]:
    """Independently derive the closed no-oneOf provider subset."""

    source = json.loads(authoritative_path.read_text(encoding="utf-8"))
    assert source["type"] == "object"
    assert source["additionalProperties"] is False
    assert set(source["required"]) == WORK_RESULT_FIELDS
    assert set(source["properties"]) == WORK_RESULT_FIELDS
    derived = deepcopy(source)
    derived.pop("$schema", None)
    derived.pop("$id", None)
    for field in ("scope_owned", "findings", "changed_files"):
        choices = derived["properties"][field].pop("oneOf")
        arrays = [choice for choice in choices if choice.get("type") == "array"]
        assert len(arrays) == 1
        derived["properties"][field] = arrays[0]

    def reject_one_of(value: object) -> None:
        if isinstance(value, Mapping):
            assert "oneOf" not in value
            for item in value.values():
                reject_one_of(item)
        elif isinstance(value, list):
            for item in value:
                reject_one_of(item)

    reject_one_of(derived)
    return derived


def _timestamp(value: datetime) -> str:
    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _parse_timestamp(value: object) -> datetime:
    assert isinstance(value, str) and value.endswith("Z")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    assert parsed.tzinfo is not None and parsed.utcoffset() == timedelta(0)
    return parsed


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )
    assert completed.returncode == 0, completed.stderr
    return completed


def _portable(value: object) -> object:
    """Return a closed JSON-safe view of every invocation input."""

    if isinstance(value, bytes):
        return {"bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()}
    if is_dataclass(value) and not isinstance(value, type):
        return _portable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _portable(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_portable(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_portable(item) for item in value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return _timestamp(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise AssertionError(f"unsupported fixture input type: {type(value).__name__}")


def _exact_path_snapshot(
    root: Path, *, exclude_top_level: frozenset[str] = frozenset()
) -> dict[str, object]:
    """Capture exact names, modes, link targets, and file bytes under ``root``."""

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
        else:  # pragma: no cover - fixtures create only regular filesystem entries
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


def _git_paths(root: Path) -> tuple[Path, Path]:
    git_dir = Path(_git(root, "rev-parse", "--absolute-git-dir").stdout.strip())
    common_dir = Path(
        _git(
            root,
            "rev-parse",
            "--path-format=absolute",
            "--git-common-dir",
        ).stdout.strip()
    )
    return git_dir.resolve(), common_dir.resolve()


def _git_control_snapshot(root: Path) -> dict[str, object]:
    """Capture Git worktree, gitdir, and common-dir authority byte-for-byte."""

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

    environment = dict(os.environ)
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=root,
        capture_output=True,
        text=False,
        check=False,
        env=environment,
    )
    assert status.returncode == 0, status.stderr.decode("utf-8", errors="replace")
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
    """Hash sorted relative path, mode, and bytes for every non-Git file."""

    return _snapshot_sha256(
        _exact_path_snapshot(root, exclude_top_level=frozenset({".git"}))
    )


def _git_metadata_snapshot(root: Path) -> str:
    """Hash exact linked-worktree gitdir and common refs/HEAD/index content."""

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
    status = _git(root, "status", "--porcelain=v1", "--untracked-files=all").stdout
    return {
        "worktree_sha256": _worktree_snapshot(root),
        "git_status_sha256": hashlib.sha256(status.encode("utf-8")).hexdigest(),
        "git_metadata_sha256": _git_metadata_snapshot(root),
    }


def _repository_snapshot(root: Path) -> str:
    """Bind worktree bytes plus exact Git status/index/refs/HEAD evidence."""

    return _canonical_sha256(_repository_integrity_evidence(root))


def _signals() -> dict[str, object]:
    values = {
        "usedPercent": 90.0,
        "remainingPercent": 10.0,
        "reached": False,
        "limit": 100.0,
        "spend": 90.0,
        "remaining": 10.0,
    }
    return {
        **values,
        "buckets": {"primary": dict(values), "secondary": dict(values)},
    }


def _work_result(alias: str) -> dict[str, object]:
    return {
        "status": "DONE",
        "scope_owned": ["read-only repository inventory"],
        "evidence": {
            "commands": ["provider command executed with argv and raw streams elided"],
            "outcomes": [f"provider-native fixture for {alias}"],
            "artifacts": [f"typed WorkResult v2 for {alias}"],
        },
        "findings": [f"typed result for {alias}"],
        "changed_files": [],
        "residual_risk": "provider streams are intentionally not retained",
        "recommended_next_action": "stop this one-shot alias",
    }


def _unknown_work_result(alias: str) -> dict[str, object]:
    """Return the one fixed raw-free Result Contract v2 UNKNOWN payload."""

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


def _codex_output(alias: str) -> str:
    events = (
        {"type": "thread.started", "thread_id": f"codex-operational-{alias}"},
        {
            "type": "item.started",
            "raw_marker": RAW_SENTINEL,
            "provider_identity": PROVIDER_SENTINEL,
        },
        {
            "type": "item.completed",
            "item": {
                "type": "agent_message",
                "text": json.dumps(_work_result(alias), separators=(",", ":")),
            },
        },
        {"type": "turn.completed", "terminal_detail": TERMINAL_SENTINEL},
    )
    return (
        "\n".join(json.dumps(event, separators=(",", ":")) for event in events) + "\n"
    )


def _agy_output(alias: str) -> str:
    events = (
        {
            "event": "init",
            "conversation_id": f"agy-operational-{alias}",
            "init": {
                "raw_marker": RAW_SENTINEL,
                "provider_identity": PROVIDER_SENTINEL,
            },
        },
        {
            "event": "result",
            "result": {
                "conversation_id": f"agy-operational-{alias}",
                "status": "SUCCESS",
                "structured_output": _work_result(alias),
                "terminal_detail": TERMINAL_SENTINEL,
            },
        },
    )
    return (
        "\n".join(json.dumps(event, separators=(",", ":")) for event in events) + "\n"
    )


def _provider_output_with_exact_bytes(alias: str, target_bytes: int) -> str:
    provider = ALIASES[alias][0]
    payload = _codex_output(alias) if provider == "codex" else _agy_output(alias)
    padding_event = (
        {"type": "item.started", "padding": ""}
        if provider == "codex"
        else {"event": "progress", "padding": ""}
    )
    empty_line = json.dumps(padding_event, separators=(",", ":")) + "\n"
    padding_size = target_bytes - len(payload.encode("utf-8")) - len(
        empty_line.encode("utf-8")
    )
    assert padding_size >= 0
    padding_event["padding"] = "A" * padding_size
    lines = payload.splitlines(keepends=True)
    lines.insert(-1, json.dumps(padding_event, separators=(",", ":")) + "\n")
    padded = "".join(lines)
    assert len(padded.encode("utf-8")) == target_bytes
    return padded


def _invalid_provider_output(alias: str, malformation: str) -> str:
    provider = ALIASES[alias][0]
    valid_result = _work_result(alias)
    competing_result = deepcopy(valid_result)
    competing_result["findings"] = [f"competing typed result for {alias}"]
    schema_invalid_result = deepcopy(valid_result)
    schema_invalid_result["evidence"] = {
        "commands": [],
        "outcomes": "mapping violates WorkResult evidence schema",
        "artifacts": [],
    }
    if provider == "codex":
        start = {"type": "thread.started", "thread_id": f"codex-operational-{alias}"}
        raw = {
            "type": "item.started",
            "raw_marker": RAW_SENTINEL,
            "provider_identity": PROVIDER_SENTINEL,
        }
        valid_item = {
            "type": "item.completed",
            "item": {
                "type": "agent_message",
                "text": json.dumps(valid_result, separators=(",", ":")),
            },
        }
        terminal = {"type": "turn.completed", "terminal_detail": TERMINAL_SENTINEL}
        if malformation == "missing_work_result":
            events = (start, raw, terminal)
        elif malformation == "malformed_work_result":
            malformed_item = deepcopy(valid_item)
            malformed_item["item"]["text"] = "{not-json"
            events = (start, raw, malformed_item, terminal)
        elif malformation == "schema_invalid_mapping":
            invalid_item = deepcopy(valid_item)
            invalid_item["item"]["text"] = json.dumps(
                schema_invalid_result, separators=(",", ":")
            )
            events = (start, raw, invalid_item, terminal)
        elif malformation == "missing_terminal_event":
            events = (start, raw, valid_item)
        elif malformation == "duplicate_terminal_event":
            events = (start, raw, valid_item, terminal, terminal)
        elif malformation == "competing_terminal_work_results":
            competing_item = deepcopy(valid_item)
            competing_item["item"]["text"] = json.dumps(
                competing_result, separators=(",", ":")
            )
            events = (start, raw, valid_item, competing_item, terminal)
        else:  # pragma: no cover - test data is closed above
            raise AssertionError(f"unknown malformation {malformation}")
    else:
        start = {
            "event": "init",
            "conversation_id": f"agy-operational-{alias}",
            "init": {
                "raw_marker": RAW_SENTINEL,
                "provider_identity": PROVIDER_SENTINEL,
            },
        }
        valid_terminal = {
            "event": "result",
            "result": {
                "conversation_id": f"agy-operational-{alias}",
                "status": "SUCCESS",
                "structured_output": valid_result,
                "terminal_detail": TERMINAL_SENTINEL,
            },
        }
        if malformation == "missing_work_result":
            missing_result = deepcopy(valid_terminal)
            missing_result["result"].pop("structured_output")
            events = (start, missing_result)
        elif malformation == "malformed_work_result":
            malformed_result = deepcopy(valid_terminal)
            malformed_result["result"]["structured_output"] = "not-a-work-result"
            events = (start, malformed_result)
        elif malformation == "schema_invalid_mapping":
            invalid_result = deepcopy(valid_terminal)
            invalid_result["result"]["structured_output"] = schema_invalid_result
            events = (start, invalid_result)
        elif malformation == "missing_terminal_event":
            events = (start,)
        elif malformation == "duplicate_terminal_event":
            events = (start, valid_terminal, valid_terminal)
        elif malformation == "competing_terminal_work_results":
            competing_terminal = deepcopy(valid_terminal)
            competing_terminal["result"]["structured_output"] = competing_result
            events = (start, valid_terminal, competing_terminal)
        else:  # pragma: no cover - test data is closed above
            raise AssertionError(f"unknown malformation {malformation}")
    return (
        "\n".join(json.dumps(event, separators=(",", ":")) for event in events) + "\n"
    )


def _agy_stdin(prompt: str) -> str:
    return (
        json.dumps(
            {"event": "user", "message": {"content": prompt}},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n"
    )


class _RecordingQueue(DurableQueue):
    def __init__(self, path: Path) -> None:
        self.events: list[tuple[str, str]] = []
        self.event_lock = threading.Lock()
        self.alias_by_request: dict[str, str] = {}
        super().__init__(path)

    def remember(self, request_id: str, alias: str) -> None:
        self.alias_by_request[request_id] = alias

    def _record(self, request_id: str, event: str) -> None:
        with self.event_lock:
            self.events.append((self.alias_by_request[request_id], event))

    def transition(
        self,
        request_id: str,
        fence: int,
        state: str,
        instance_id: str | None = None,
    ) -> None:
        super().transition(request_id, fence, state, instance_id)
        self._record(request_id, state)

    def complete(self, **kwargs: Any) -> None:
        super().complete(**kwargs)
        self._record(str(kwargs["request_id"]), str(kwargs.get("state", "DONE")))


class _InputSink:
    def __init__(self, process: _FakeProcess) -> None:
        self.process = process
        self.buffer = bytearray()
        self.closed = False

    def write(self, data: bytes) -> int:
        assert not self.closed
        assert isinstance(data, bytes)
        self.buffer.extend(data)
        self.process._record_once("STDIN_WRITE")
        return len(data)

    def flush(self) -> None:
        assert not self.closed

    def close(self) -> None:
        self.closed = True
        self.process._record_once("STDIN_CLOSED")


class _ChunkedBytes:
    def __init__(self, process: _FakeProcess, stream_name: str, payload: bytes) -> None:
        self.process = process
        self.stream_name = stream_name
        self.payload = payload
        self.offset = 0
        self.closed = False

    def read(self, size: int = -1) -> bytes:
        assert 0 < size <= MAX_READ_CHUNK_BYTES, (
            "provider streams must be read incrementally with a bounded chunk"
        )
        assert self.process.factory.all_started.wait(timeout=1.5), (
            "operational provider lanes did not overlap before capture"
        )
        self.process._release_output_barrier()
        assert self.process.factory.outputs_ready.wait(timeout=1.5), (
            "provider fixture output barrier did not release"
        )
        start = self.offset
        stop = min(len(self.payload), start + size)
        chunk = self.payload[start:stop]
        self.offset = stop
        self.process.factory.read_calls.setdefault(self.process.alias, []).append(
            {
                "stream": self.stream_name,
                "requested": size,
                "returned": len(chunk),
            }
        )
        self.process._record_once(f"{self.stream_name.upper()}_READ")
        if not chunk:
            self.process._stream_eof(self.stream_name)
        return chunk

    def read1(self, size: int = -1) -> bytes:
        return self.read(size)

    def close(self) -> None:
        self.closed = True


class _FakeProcess:
    def __init__(
        self, factory: _PopenFactory, alias: str, argv: tuple[str, ...]
    ) -> None:
        self.factory = factory
        self.alias = alias
        self.args = argv
        self.pid = 62000 + tuple(ALIASES).index(alias)
        self.returncode: int | None = None
        self._finished = False
        self._eof_streams: set[str] = set()
        self._events_seen: set[str] = set()
        self.stdin = _InputSink(self)
        self.stdout = _ChunkedBytes(
            self, "stdout", factory.payloads[alias].encode("utf-8")
        )
        self.stderr = _ChunkedBytes(
            self, "stderr", factory.stderr_payloads[alias].encode("utf-8")
        )

    def _record_once(self, event: str) -> None:
        with self.factory.store.event_lock:
            if event not in self._events_seen:
                self._events_seen.add(event)
                self.factory.store.events.append((self.alias, event))

    def _release_output_barrier(self) -> None:
        if self.factory.mutate_alias == self.alias:
            with self.factory.lock:
                if not self.factory.repository_mutated:
                    self.factory.repository_mutated = True
                    assert self.factory.repository_mutation is not None
                    self.factory.repository_mutation()
                    self.factory.outputs_ready.set()
        elif self.factory.mutate_alias is None:
            self.factory.outputs_ready.set()

    def _finish(self, returncode: int) -> None:
        with self.factory.lock:
            if self._finished:
                return
            self.returncode = returncode
            self._finished = True
            self.factory.active -= 1
        self._record_once("EXIT")

    def _stream_eof(self, stream_name: str) -> None:
        self._eof_streams.add(stream_name)
        if (
            self._eof_streams == {"stdout", "stderr"}
            and self.alias != self.factory.timeout_alias
            and self.alias != self.factory.hang_alias
            and not self.factory.batch_start_failed
        ):
            self._finish(self.factory.returncodes.get(self.alias, 0))

    def communicate(self, *_args: object, **_kwargs: object) -> None:
        self.factory.communicate_calls.append(self.alias)
        raise AssertionError("communicate() is an unbounded production boundary")

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        raise AssertionError("cleanup must target the isolated process group")

    def kill(self) -> None:
        raise AssertionError("cleanup must target the isolated process group")

    def wait(self, timeout: float | None = None) -> int:
        self.factory.wait_calls.setdefault(self.alias, []).append(timeout)
        if self.returncode is not None:
            return self.returncode
        if (
            self.alias in {self.factory.timeout_alias, self.factory.hang_alias}
            or self.factory.batch_start_failed
            or (
                self.alias == self.factory.cleanup_requires_kill_alias
                and signal.SIGKILL
                not in self.factory.group_signals.get(self.alias, [])
            )
        ):
            raise subprocess.TimeoutExpired(self.args, timeout)
        self._finish(self.factory.returncodes.get(self.alias, 0))
        assert self.returncode is not None
        return self.returncode

    def on_group_signal(self, sent_signal: signal.Signals) -> None:
        if sent_signal == signal.SIGTERM:
            if self.alias != self.factory.cleanup_requires_kill_alias:
                self._finish(-signal.SIGTERM)
        elif sent_signal == signal.SIGKILL:
            self._finish(-signal.SIGKILL)


class _PopenFactory:
    def __init__(
        self,
        *,
        store: _RecordingQueue,
        executable_aliases: Mapping[str, str],
        timeout_alias: str | None = None,
        popen_failure_alias: str | None = None,
        nonzero_alias: str | None = None,
        hang_alias: str | None = None,
        cleanup_requires_kill_alias: str | None = None,
        cleanup_failure_alias: str | None = None,
        marker_failure_after: int | None = None,
        mutate_alias: str | None = None,
        repository_mutation: Any | None = None,
        marker_store: Path,
    ) -> None:
        self.store = store
        self.executable_aliases = dict(executable_aliases)
        self.timeout_alias = timeout_alias
        self.popen_failure_alias = popen_failure_alias
        self.nonzero_alias = nonzero_alias
        self.hang_alias = hang_alias
        self.cleanup_requires_kill_alias = cleanup_requires_kill_alias
        self.cleanup_failure_alias = cleanup_failure_alias
        self.marker_failure_after = marker_failure_after
        self.mutate_alias = mutate_alias
        self.repository_mutation = repository_mutation
        self.marker_store = marker_store
        self.repository_mutated = False
        self.batch_start_failed = False
        self.lock = threading.Lock()
        self.all_started = threading.Event()
        self.outputs_ready = threading.Event()
        self.calls: dict[str, list[dict[str, Any]]] = {alias: [] for alias in ALIASES}
        self.popen_attempts: list[str] = []
        self.communicate_calls: list[str] = []
        self.read_calls: dict[str, list[dict[str, Any]]] = {}
        self.wait_calls: dict[str, list[float | None]] = {}
        self.group_signals: dict[str, list[signal.Signals]] = {}
        self.marker_write_order: list[str] = []
        self.marker_snapshots: list[dict[str, object]] = []
        self.schema_records: list[dict[str, object]] = []
        self.payloads = {
            alias: _codex_output(alias) if provider == "codex" else _agy_output(alias)
            for alias, (provider, _root) in ALIASES.items()
        }
        self.stderr_payloads = {
            alias: f"{STDERR_SENTINEL}:{alias}\n" for alias in ALIASES
        }
        self.returncodes = {
            alias: 7 if alias == nonzero_alias else 0 for alias in ALIASES
        }
        self.active = 0
        self.max_active = 0
        self.processes: list[_FakeProcess] = []

    def __call__(self, *args: Any, **kwargs: Any) -> _FakeProcess:
        raw_argv = args[0] if args else kwargs.get("args")
        argv = tuple(raw_argv)
        executable = str(argv[0])
        alias = self.executable_aliases[executable]
        self.popen_attempts.append(alias)
        with self.store.event_lock:
            self.store.events.append((alias, "POPEN_ATTEMPT"))
        self.marker_snapshots.append(_exact_path_snapshot(self.marker_store))
        provider = ALIASES[alias][0]
        schema_flag = "--output-schema" if provider == "codex" else "--json-schema"
        assert argv.count(schema_flag) == 1
        schema_path = Path(argv[argv.index(schema_flag) + 1])
        assert schema_path.is_file()
        self.schema_records.append(
            {
                "alias": alias,
                "path": schema_path,
                "bytes": schema_path.read_bytes(),
                "mode": stat.S_IMODE(schema_path.stat().st_mode),
                "parent_mode": stat.S_IMODE(schema_path.parent.stat().st_mode),
            }
        )
        if alias == self.popen_failure_alias:
            self.batch_start_failed = True
            self.all_started.set()
            self.outputs_ready.set()
            raise OSError(
                f"{TERMINAL_SENTINEL}:{PROVIDER_SENTINEL}:{ACCOUNT_SENTINEL}"
            )
        record = {"argv": argv, "kwargs": dict(kwargs)}
        record["kwargs"].pop("args", None)
        with self.lock:
            self.calls[alias].append(record)
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            self.store.events.append((alias, "POPEN"))
            if sum(len(items) for items in self.calls.values()) == len(ALIASES):
                self.all_started.set()
        process = _FakeProcess(self, alias, argv)
        with self.lock:
            self.processes.append(process)
        return process

    def killpg(self, process_group: int, sent_signal: signal.Signals) -> None:
        process = next(process for process in self.processes if process.pid == process_group)
        self.group_signals.setdefault(process.alias, []).append(sent_signal)
        process._record_once(sent_signal.name)
        if process.alias == self.cleanup_failure_alias:
            raise OSError(f"{TERMINAL_SENTINEL}:process-group-cleanup")
        process.on_group_signal(sent_signal)


def _config() -> dict[str, object]:
    return {
        "activation_prohibited": True,
        "dispatcher_execution": "CLOSED",
        "idq_mvp_080": {
            "ticket": TICKET,
            "authorization_contract": {
                "schema_version": AUTHORIZATION_SCHEMA_VERSION,
                "protocol_version": AUTHORIZATION_PROTOCOL_VERSION,
                "authorization_id": AUTHORIZATION_ID,
                "ttl_seconds": AUTHORIZATION_TTL_SECONDS,
                "objective": AUTHORIZATION_OBJECTIVE,
                "ownership": AUTHORIZATION_OWNERSHIP,
                "risk_id": AUTHORIZATION_RISK_ID,
            },
            "provider_output": {
                "stdout_cap_bytes": OUTPUT_CAP_BYTES,
                "stderr_cap_bytes": STDERR_CAP_BYTES,
                "read_chunk_max_bytes": MAX_READ_CHUNK_BYTES,
            },
            "aliases": {
                alias: {
                    "provider": provider,
                    "attempt": 1,
                    "work_mode": "read_only",
                    "automatic_retry": False,
                    "fallback": False,
                }
                for alias, (provider, _root) in ALIASES.items()
            },
        },
    }


def _initialize_repository(
    tmp_path: Path, repository_kind: str
) -> tuple[Path, Path, Path, Path, str]:
    assert repository_kind in REPOSITORY_KINDS
    seed = (
        tmp_path / "repository-common"
        if repository_kind == "linked"
        else tmp_path / "repository"
    )
    seed.mkdir()
    _git(seed, "init", "--quiet")
    _git(seed, "config", "user.name", "IDQ Fixture")
    _git(seed, "config", "user.email", "idq-fixture@example.invalid")
    seed_schema = seed / ".agents/schemas/multiagent-work-result-v2.schema.json"
    seed_schema.parent.mkdir(parents=True)
    seed_schema.write_bytes(
        (
            REPOSITORY_ROOT / ".agents/schemas/multiagent-work-result-v2.schema.json"
        ).read_bytes()
    )
    seed_tracked = seed / "tracked.txt"
    seed_tracked.write_text("immutable repository fixture\n", encoding="utf-8")
    _git(seed, "add", "--all")
    _git(seed, "commit", "--quiet", "-m", "fixture")

    if repository_kind == "linked":
        repository = tmp_path / "repository"
        _git(seed, "worktree", "add", "--quiet", "--detach", str(repository), "HEAD")
    else:
        repository = seed

    head = _git(repository, "rev-parse", "HEAD").stdout.strip()
    tree = _git(repository, "rev-parse", "HEAD^{tree}").stdout.strip()
    alternate_head = _git(
        repository,
        "commit-tree",
        tree,
        "-p",
        head,
        "-m",
        "same-tree alternate HEAD for mutation fixture",
    ).stdout.strip()
    assert alternate_head != head
    return (
        repository,
        seed,
        repository / ".agents/schemas/multiagent-work-result-v2.schema.json",
        repository / "tracked.txt",
        alternate_head,
    )


def _inject_repository_mutation(
    *,
    repository: Path,
    tracked: Path,
    alternate_head: str,
    mutation_kind: str,
) -> None:
    """Inject one bounded Git-authority mutation after every lane has started."""

    assert mutation_kind in REPOSITORY_MUTATIONS
    git_dir, common_dir = _git_paths(repository)
    if mutation_kind == "tracked_file":
        tracked.write_text(
            "provider mutation must invalidate every result\n", encoding="utf-8"
        )
    elif mutation_kind == "index_only":
        _git(repository, "update-index", "--assume-unchanged", "tracked.txt")
    elif mutation_kind == "ref_only":
        ref = git_dir / "refs/worktree/idq-provider-drift"
        ref.parent.mkdir(parents=True, exist_ok=True)
        ref.write_text(f"{alternate_head}\n", encoding="ascii")
    elif mutation_kind == "head_only":
        (git_dir / "HEAD").write_text(f"{alternate_head}\n", encoding="ascii")
    else:
        ref = common_dir / "refs/idq/common-provider-drift"
        ref.parent.mkdir(parents=True, exist_ok=True)
        ref.write_text(f"{alternate_head}\n", encoding="ascii")


def _write_input_file(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_bytes(_portable(value)) + b"\n")


def _fixture(
    tmp_path: Path,
    *,
    failure_alias: str | None = None,
    popen_failure_alias: str | None = None,
    nonzero_alias: str | None = None,
    hang_alias: str | None = None,
    cleanup_requires_kill_alias: str | None = None,
    cleanup_failure_alias: str | None = None,
    marker_failure_after: int | None = None,
    mutate_alias: str | None = None,
    mutation_kind: str = "tracked_file",
    repository_kind: str = "normal",
    qobs_observed_offset_seconds: int = 0,
    authorization_issued_offset_seconds: int = 0,
    authorization_expires_offset_seconds: int | None = None,
    authorization_ttl_seconds: int = AUTHORIZATION_TTL_SECONDS,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    (
        repository,
        repository_seed,
        schema_path,
        tracked,
        alternate_head,
    ) = _initialize_repository(tmp_path, repository_kind)
    provider_root = tmp_path / "providers"
    account_root = tmp_path / "accounts"
    input_store = tmp_path / "inputs"
    provider_root.mkdir()
    account_root.mkdir(mode=0o700)
    input_store.mkdir(mode=0o700)
    executable_aliases: dict[str, str] = {}

    store = _RecordingQueue(tmp_path / "queue/durable.sqlite3")
    marker_store = tmp_path / "markers"
    capacity_store = tmp_path / "capacity"
    policy = json.loads(
        (REPOSITORY_ROOT / ".agents/config/s3_capacity_policy.json").read_text(
            encoding="utf-8"
        )
    )
    config = _config()
    config["idq_mvp_080"]["authorization_contract"][
        "ttl_seconds"
    ] = authorization_ttl_seconds
    lanes: dict[str, dict[str, object]] = {}
    bindings: dict[str, dict[str, object]] = {}
    leases: dict[str, dict[str, object]] = {}

    for alias, (provider, root) in ALIASES.items():
        executable = (provider_root / f"{alias}-{provider}").resolve()
        executable.write_text("fixture executable; never invoked\n", encoding="utf-8")
        executable.chmod(0o700)
        executable_aliases[str(executable)] = alias
        account_home = (account_root / f"{alias}-{ACCOUNT_SENTINEL}").resolve()
        account_home.mkdir(mode=0o700)

        request_id = f"idq-operational-{alias}"
        instance_id = f"root-{root.lower()}-operational"
        lease = capacity.acquire_lease(
            capacity_store,
            account=alias,
            request_id=request_id,
            owner=instance_id,
            lane=1,
            request_budget=1,
            model_quality_floor="gpt-5.6-sol",
            policy=policy,
            now=now.timestamp(),
            ttl_seconds=120,
        )
        qobs_context: dict[str, object] = {
            "alias": alias,
            "provider": provider,
            "account_home": str(account_home),
            "resolved_executable": str(executable),
            "ticket_id": TICKET,
            "attempt_id": 1,
            "policy_version": "2026-08-29.1",
            "nonce": f"idq-operational-{alias}-nonce",
            "observed_at": _timestamp(
                now + timedelta(seconds=qobs_observed_offset_seconds)
            ),
        }
        artifact = quota.probe_quota_observation(_signals(), qobs_context)
        request: dict[str, object] = {
            "ticket": TICKET,
            "authorization_id": AUTHORIZATION_ID,
            "alias": alias,
            "provider": provider,
            "attempt": 1,
            "work_mode": "read_only",
            "automatic_retry": False,
            "fallback": False,
            "objective": AUTHORIZATION_OBJECTIVE,
            "ownership": AUTHORIZATION_OWNERSHIP,
            "risk_id": AUTHORIZATION_RISK_ID,
            "control_session_nonce_sha256": _digest(
                "auth02-control-session-nonce"
            ),
            "decision_sha256": _digest(f"decision:{alias}"),
            "qobs_artifact_sha256": quota.quota_artifact_sha256(artifact),
            "qobs_quota_band": "constrained",
            "nonce_sha256": quota.sha256_text(str(qobs_context["nonce"])),
            "scheduling_snapshot_sha256": _digest(f"snapshot:{alias}"),
            "resolved_executable_sha256": quota.sha256_text(str(executable)),
            "resolved_executable_identity_sha256": _executable_identity_sha256(
                executable
            ),
            "account_identity_sha256": quota.sha256_text(str(account_home)),
            "account_identity_state_sha256": _account_identity_state_sha256(
                account_home
            ),
            "qobs_context_sha256": _canonical_sha256(qobs_context),
            "lease_risk_sha256": _digest(f"risk:{alias}"),
        }
        execution_context = {
            "qobs_artifact": artifact,
            "qobs_expected_context": qobs_context,
            "runtime": (
                {"read_only": True, "sandbox": "read-only"}
                if provider == "codex"
                else {"read_only": True, "mode": "plan", "sandbox": True}
            ),
        }
        lanes[alias] = {
            "job": None,
            "instance_id": instance_id,
            "request": request,
            "execution_context": execution_context,
            "capacity_lease": lease.to_dict(),
            "capacity_store_path": str(capacity_store.resolve()),
            "capacity_policy": policy,
            "prompt_stdin": f"Read-only repository inventory for {alias}; {PROMPT_SENTINEL}",
        }
        leases[alias] = lease.to_dict()
        bindings[alias] = {
            "request_id": request_id,
            "root": root,
            "provider": provider,
            "decision_sha256": request["decision_sha256"],
            "scheduling_snapshot_sha256": request["scheduling_snapshot_sha256"],
            "qobs_artifact_sha256": request["qobs_artifact_sha256"],
            "nonce_sha256": request["nonce_sha256"],
            "resolved_executable_sha256": request["resolved_executable_sha256"],
            "resolved_executable_identity_sha256": request[
                "resolved_executable_identity_sha256"
            ],
            "account_identity_sha256": request["account_identity_sha256"],
            "account_identity_state_sha256": request[
                "account_identity_state_sha256"
            ],
            "qobs_context_sha256": request["qobs_context_sha256"],
            "capacity_lease_sha256": lease.lease_sha256,
            "lease_risk_sha256": request["lease_risk_sha256"],
        }

    capacity_state_sha256 = _snapshot_sha256(_exact_path_snapshot(capacity_store))
    for alias in ALIASES:
        lanes[alias]["request"]["capacity_state_sha256"] = capacity_state_sha256
        bindings[alias]["capacity_state_sha256"] = capacity_state_sha256

    snapshot = _repository_snapshot(repository)
    issued_at = now + timedelta(seconds=authorization_issued_offset_seconds)
    expires_offset = (
        authorization_issued_offset_seconds + authorization_ttl_seconds
        if authorization_expires_offset_seconds is None
        else authorization_expires_offset_seconds
    )
    authorization: dict[str, object] = {
        "schema_version": AUTHORIZATION_SCHEMA_VERSION,
        "protocol_version": AUTHORIZATION_PROTOCOL_VERSION,
        "authorization_id": AUTHORIZATION_ID,
        "ticket": TICKET,
        "status": "UNUSED",
        "issued_at": _timestamp(issued_at),
        "expires_at": _timestamp(now + timedelta(seconds=expires_offset)),
        "ttl_seconds": authorization_ttl_seconds,
        "control_session_nonce_sha256": _digest("auth02-control-session-nonce"),
        "aliases": list(ALIASES),
        "attempt": 1,
        "max_attempts": 1,
        "work_mode": "read_only",
        "automatic_retry": False,
        "fallback": False,
        "substitution": False,
        "objective": AUTHORIZATION_OBJECTIVE,
        "ownership": AUTHORIZATION_OWNERSHIP,
        "risk_id": AUTHORIZATION_RISK_ID,
        "repository_snapshot_sha256": snapshot,
        "marker_store_sha256": _digest(str(marker_store.resolve())),
        "bindings": bindings,
    }
    authorization_sha256 = _canonical_sha256(authorization)

    for alias, (_provider, root) in ALIASES.items():
        request_id = str(bindings[alias]["request_id"])
        instance_id = str(lanes[alias]["instance_id"])
        payload = {
            "schema_version": "idq-mvp-080-job-authority-v1",
            "authorization_id": AUTHORIZATION_ID,
            "authorization_sha256": authorization_sha256,
            "authorization_binding_sha256": _canonical_sha256(bindings[alias]),
            "objective_sha256": _digest(str(authorization["objective"])),
        }
        submitted = store.submit(
            request_id=request_id,
            idempotency_key=request_id,
            payload=payload,
            root=root,
            alias=alias,
            work_mode="read_only",
            attempt=1,
            retry_budget=0,
        )
        assert submitted.state == "QUEUED"
        job = store.claim(root=root, instance_id=instance_id, aliases={alias})
        assert job is not None
        store.remember(request_id, alias)
        lanes[alias]["job"] = job

    _write_input_file(input_store / "config.json", config)
    _write_input_file(input_store / "authorization.json", authorization)
    for alias, lane in lanes.items():
        _write_input_file(input_store / "lanes" / f"{alias}.json", lane)

    repository_mutation = None
    if mutate_alias is not None:
        repository_mutation = lambda: _inject_repository_mutation(
            repository=repository,
            tracked=tracked,
            alternate_head=alternate_head,
            mutation_kind=mutation_kind,
        )
    factory = _PopenFactory(
        store=store,
        executable_aliases=executable_aliases,
        timeout_alias=failure_alias,
        popen_failure_alias=popen_failure_alias,
        nonzero_alias=nonzero_alias,
        hang_alias=hang_alias,
        cleanup_requires_kill_alias=cleanup_requires_kill_alias,
        cleanup_failure_alias=cleanup_failure_alias,
        marker_failure_after=marker_failure_after,
        mutate_alias=mutate_alias,
        repository_mutation=repository_mutation,
        marker_store=marker_store,
    )
    return {
        "now": now,
        "repository": repository,
        "repository_seed": repository_seed,
        "repository_kind": repository_kind,
        "alternate_head": alternate_head,
        "schema_path": schema_path.resolve(),
        "tracked": tracked,
        "snapshot": snapshot,
        "config": config,
        "authorization": authorization,
        "authorization_sha256": authorization_sha256,
        "lanes": lanes,
        "initial_capacity_leases": leases,
        "initial_capacity_state_sha256": capacity_state_sha256,
        "store": store,
        "marker_store": marker_store,
        "capacity_store": capacity_store,
        "input_store": input_store,
        "provider_root": provider_root,
        "account_root": account_root,
        "factory": factory,
    }


def _invocation_arguments(
    fixture: Mapping[str, Any], **overrides: object
) -> dict[str, object]:
    arguments: dict[str, object] = {
        "config": fixture["config"],
        "authorization": fixture["authorization"],
        "lanes": fixture["lanes"],
        "store": fixture["store"],
        "marker_store": fixture["marker_store"],
        "repository_root": fixture["repository"],
        "timeout_seconds": TIMEOUT_SECONDS,
        "now": fixture["now"],
    }
    arguments.update(overrides)
    return arguments


def _run(operational: Any, fixture: Mapping[str, Any], **overrides: object):
    arguments = _invocation_arguments(fixture, **overrides)
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(operational.subprocess, "Popen", fixture["factory"])
        monkeypatch.setattr(operational.os, "killpg", fixture["factory"].killpg)
        monkeypatch.setattr(operational.os, "getpgid", lambda process_id: process_id)
        consume_lease = operational.capacity.consume_lease
        release_lease = operational.capacity.release_lease

        def recording_consume(*args: object, **kwargs: object) -> object:
            lease = args[1] if len(args) > 1 else kwargs["lease"]
            alias = lease.account if hasattr(lease, "account") else lease["account"]
            consumed = consume_lease(*args, **kwargs)
            with fixture["store"].event_lock:
                fixture["store"].events.append((alias, "CAPACITY_CONSUMED"))
            return consumed

        def recording_release(*args: object, **kwargs: object) -> object:
            lease = args[1] if len(args) > 1 else kwargs["lease"]
            alias = lease.account if hasattr(lease, "account") else lease["account"]
            released = release_lease(*args, **kwargs)
            with fixture["store"].event_lock:
                fixture["store"].events.append((alias, "CAPACITY_RELEASED"))
            return released

        monkeypatch.setattr(operational.capacity, "consume_lease", recording_consume)
        monkeypatch.setattr(operational.capacity, "release_lease", recording_release)
        marker_writer = operational._write_single_use_marker

        def recording_marker_writer(
            marker_store: Path, name: str, record: Mapping[str, object]
        ) -> None:
            fixture["factory"].marker_write_order.append(name)
            if (
                fixture["factory"].marker_failure_after is not None
                and len(fixture["factory"].marker_write_order)
                == fixture["factory"].marker_failure_after
            ):
                raise OSError(f"{TERMINAL_SENTINEL}:partial-marker-commit")
            marker_writer(marker_store, name, record)

        monkeypatch.setattr(
            operational, "_write_single_use_marker", recording_marker_writer
        )
        return operational.execute_idq_mvp_080_operational(**arguments)


def _process_call_count(fixture: Mapping[str, Any]) -> int:
    return sum(len(items) for items in fixture["factory"].calls.values())


def _marker_files(fixture: Mapping[str, Any]) -> list[Path]:
    root = fixture["marker_store"]
    return sorted(root.rglob("*.used")) if root.exists() else []


def _expected_marker_records(
    fixture: Mapping[str, Any],
) -> list[tuple[str, dict[str, object]]]:
    authorization = fixture["authorization"]
    authorization_sha256 = fixture["authorization_sha256"]
    records: list[tuple[str, dict[str, object]]] = [
        (
            f"idq-mvp-080-auth-{_digest(AUTHORIZATION_ID)}.used",
            {
                "schema_version": 1,
                "marker_kind": "authorization",
                "authorization_id": AUTHORIZATION_ID,
                "authorization_sha256": authorization_sha256,
                "ticket": TICKET,
                "control_session_nonce_sha256": authorization[
                    "control_session_nonce_sha256"
                ],
                "repository_snapshot_sha256": fixture["snapshot"],
            },
        )
    ]
    for alias in ALIASES:
        binding = authorization["bindings"][alias]
        records.append(
            (
                f"idq-mvp-080-qobs-{binding['nonce_sha256']}.used",
                {
                    "schema_version": 1,
                    "marker_kind": "qobs_nonce",
                    "authorization_id": AUTHORIZATION_ID,
                    "authorization_sha256": authorization_sha256,
                    "alias": alias,
                    "request_id": binding["request_id"],
                    "qobs_artifact_sha256": binding["qobs_artifact_sha256"],
                    "nonce_sha256": binding["nonce_sha256"],
                },
            )
        )
        records.append(
            (
                f"idq-mvp-080-{alias}.used",
                {
                    "schema_version": 1,
                    "marker_kind": "alias_binding",
                    "authorization_id": AUTHORIZATION_ID,
                    "authorization_sha256": authorization_sha256,
                    "alias": alias,
                    "request_id": binding["request_id"],
                    "authorization_binding_sha256": _canonical_sha256(binding),
                    "capacity_lease_sha256": binding["capacity_lease_sha256"],
                },
            )
        )
    return records


def _assert_exact_markers(fixture: Mapping[str, Any]) -> None:
    root = fixture["marker_store"]
    assert root.is_dir()
    assert stat.S_IMODE(root.stat().st_mode) == 0o700
    expected = _expected_marker_records(fixture)
    assert [path.name for path in _marker_files(fixture)] == sorted(
        name for name, _record in expected
    )
    for name, record in expected:
        path = root / name
        assert path.is_file() and not path.is_symlink()
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert path.read_bytes() == _canonical_bytes(record) + b"\n"


def _tree_snapshot(root: Path) -> dict[str, str]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _tree_artifact_bytes(root: Path) -> bytes:
    if not root.exists():
        return b""
    return b"".join(
        path.read_bytes() for path in sorted(root.rglob("*")) if path.is_file()
    )


def _queue_artifact_bytes(fixture: Mapping[str, Any]) -> bytes:
    return _tree_artifact_bytes(fixture["store"].path.parent)


def _capacity_state(fixture: Mapping[str, Any]) -> dict[str, object]:
    path = fixture["capacity_store"] / ".capacity.json"
    state = json.loads(path.read_text(encoding="ascii"))
    return capacity.validate_capacity_state(state, fixture["lanes"]["codex1"]["capacity_policy"])


def _persisted_result_and_receipt(
    fixture: Mapping[str, Any], request_id: str
) -> tuple[dict[str, object], dict[str, object]]:
    database = fixture["store"].path
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    try:
        row = connection.execute(
            "SELECT result, receipt FROM results WHERE request_id = ?",
            (request_id,),
        ).fetchone()
        assert row is not None
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM results WHERE request_id = ?", (request_id,)
            ).fetchone()[0]
            == 1
        )
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM outbox WHERE request_id = ?", (request_id,)
            ).fetchone()[0]
            == 1
        )
        return json.loads(row[0]), json.loads(row[1])
    finally:
        connection.close()


def _assert_capacity_accounting(
    fixture: Mapping[str, Any], *, attempted_aliases: frozenset[str]
) -> None:
    state = _capacity_state(fixture)
    assert state["leases"] == {}
    assert set(state["terminal"]) == {
        lease["lease_id"] for lease in fixture["initial_capacity_leases"].values()
    }
    for alias in ALIASES:
        initial = fixture["initial_capacity_leases"][alias]
        request_id = fixture["authorization"]["bindings"][alias]["request_id"]
        terminal = state["terminal"][initial["lease_id"]]
        assert terminal["status"] == "released"
        assert terminal["terminal_at"] >= fixture["now"].timestamp()
        charged = 1 if alias in attempted_aliases else 0
        ledger = state["daily_ledger"][alias]
        assert ledger["requests"] == charged
        assert ledger["request_ids"] == ({request_id: 1} if charged else {})
        assert set(ledger["request_id_timestamps"]) == set(ledger["request_ids"])
        burn_events = state["burn_events"][alias]
        assert len(burn_events) == charged
        if charged:
            assert burn_events == [
                {
                    "at": fixture["now"].timestamp(),
                    "requests": 1,
                    "lease_id": initial["lease_id"],
                }
            ]
            assert terminal["lease_sha256"] != initial["lease_sha256"]
        else:
            assert terminal["lease_sha256"] == initial["lease_sha256"]


def _assert_no_raw_material(value: object) -> None:
    if isinstance(value, bytes):
        material = value.decode("utf-8", errors="ignore")
    else:
        try:
            material = json.dumps(value, sort_keys=True, default=repr)
        except (TypeError, ValueError):
            material = repr(value)
    for sentinel in (
        RAW_SENTINEL,
        STDERR_SENTINEL,
        PROMPT_SENTINEL,
        INHERITED_ENV_SENTINEL,
        TERMINAL_SENTINEL,
        PROVIDER_SENTINEL,
        ACCOUNT_SENTINEL,
    ):
        assert sentinel not in material


def _captured_bytes(capsys: pytest.CaptureFixture[str]) -> dict[str, bytes]:
    captured = capsys.readouterr()
    return {
        "stdout": captured.out.encode("utf-8"),
        "stderr": captured.err.encode("utf-8"),
    }


def _invocation_input_snapshot(arguments: Mapping[str, object]) -> bytes:
    return _canonical_bytes(
        _portable(
            {
                "config": arguments["config"],
                "authorization": arguments["authorization"],
                "lanes": arguments["lanes"],
                "marker_store": arguments["marker_store"],
                "repository_root": arguments["repository_root"],
                "timeout_seconds": arguments["timeout_seconds"],
                "now": arguments["now"],
            }
        )
    )


def _zero_side_effect_snapshot(
    fixture: Mapping[str, Any],
    arguments: Mapping[str, object],
    captured: Mapping[str, bytes],
) -> dict[str, object]:
    """General byte oracle for every failed four-lane preflight/replay."""

    factory = fixture["factory"]
    store = fixture["store"]
    repository_seed = fixture["repository_seed"]
    seed_worktree = _exact_path_snapshot(
        repository_seed, exclude_top_level=frozenset({".git"})
    )
    return {
        "queue_db_wal_shm": _exact_path_snapshot(store.path.parent),
        "capacity_store": _exact_path_snapshot(fixture["capacity_store"]),
        "marker_store": _exact_path_snapshot(fixture["marker_store"]),
        "input_config_auth_files": _exact_path_snapshot(fixture["input_store"]),
        "provider_input_files": _exact_path_snapshot(fixture["provider_root"]),
        "account_input_files": _exact_path_snapshot(fixture["account_root"]),
        "repository": _git_control_snapshot(fixture["repository"]),
        "common_repository_worktree": seed_worktree,
        "invocation_inputs": _invocation_input_snapshot(arguments),
        "queue_observer": {
            "events": tuple(store.events),
            "alias_by_request": dict(store.alias_by_request),
        },
        "process_observer": {
            "calls": _portable(factory.calls),
            "popen_attempts": tuple(factory.popen_attempts),
            "communicate_calls": tuple(factory.communicate_calls),
            "read_calls": _portable(factory.read_calls),
            "wait_calls": _portable(factory.wait_calls),
            "group_signals": _portable(factory.group_signals),
            "marker_write_order": tuple(factory.marker_write_order),
            "marker_snapshots": _portable(factory.marker_snapshots),
            "schema_records": _portable(factory.schema_records),
            "active": factory.active,
            "max_active": factory.max_active,
            "processes": tuple(
                (
                    process.alias,
                    process.returncode,
                    process._finished,
                    tuple(sorted(process._eof_streams)),
                )
                for process in factory.processes
            ),
            "all_started": factory.all_started.is_set(),
            "outputs_ready": factory.outputs_ready.is_set(),
            "repository_mutated": factory.repository_mutated,
        },
        "captured": dict(captured),
    }


def _assert_rejected_without_side_effect(
    operational: Any,
    fixture: Mapping[str, Any],
    capsys: pytest.CaptureFixture[str],
    **overrides: object,
) -> Exception:
    arguments = _invocation_arguments(fixture, **overrides)
    captured_before = _captured_bytes(capsys)
    assert captured_before == {"stdout": b"", "stderr": b""}
    before = _zero_side_effect_snapshot(fixture, arguments, captured_before)

    with pytest.MonkeyPatch.context() as monkeypatch:
        if hasattr(operational, "subprocess"):
            monkeypatch.setattr(
                operational.subprocess, "Popen", fixture["factory"]
            )
        with pytest.raises(ValueError) as raised:
            operational.execute_idq_mvp_080_operational(**arguments)

    captured_after = _captured_bytes(capsys)
    after = _zero_side_effect_snapshot(fixture, arguments, captured_after)
    assert after == before
    return raised.value


def _assert_work_result_contract(
    result: Mapping[str, Any], *, expected_status: str
) -> None:
    assert set(result) == WORK_RESULT_FIELDS
    assert result["status"] == expected_status
    assert isinstance(result["scope_owned"], list) and result["scope_owned"]
    assert all(isinstance(item, str) and item.strip() for item in result["scope_owned"])
    assert set(result["evidence"]) == WORK_RESULT_EVIDENCE_FIELDS
    for field in WORK_RESULT_EVIDENCE_FIELDS:
        values = result["evidence"][field]
        assert isinstance(values, list) and values
        assert all(isinstance(item, str) and item.strip() for item in values)
    assert isinstance(result["findings"], list) and result["findings"]
    assert all(isinstance(item, str) and item.strip() for item in result["findings"])
    assert result["changed_files"] == []
    assert isinstance(result["residual_risk"], str) and result[
        "residual_risk"
    ].strip()
    assert isinstance(result["recommended_next_action"], str) and result[
        "recommended_next_action"
    ].strip()


def _adapter_and_scope(alias: str, *, status: str) -> tuple[str, str]:
    provider = ALIASES[alias][0]
    adapter = (
        "codex-jsonl-output-schema-v2"
        if provider == "codex"
        else "agy-stream-json-schema-v2"
    )
    if status == "UNKNOWN":
        return adapter, "not validated"
    return adapter, (
        "provider-native validated"
        if provider == "codex"
        else "validated in-process only"
    )


def _assert_exact_outcome_receipt(
    fixture: Mapping[str, Any],
    completed: Mapping[str, Any],
    alias: str,
    *,
    status: str,
) -> None:
    outcome = completed["aliases"][alias]
    assert set(outcome) == {"status", "receipt", "work_result"}
    assert outcome["status"] == status
    result = outcome["work_result"]
    expected_result_status = "DONE" if status == "DONE" else "BLOCKED"
    _assert_work_result_contract(result, expected_status=expected_result_status)
    expected_result = _work_result(alias) if status == "DONE" else _unknown_work_result(alias)
    assert result == expected_result

    receipt = outcome["receipt"]
    provider, root = ALIASES[alias]
    lane = fixture["lanes"][alias]
    binding = fixture["authorization"]["bindings"][alias]
    adapter, evidence_scope = _adapter_and_scope(alias, status=status)
    payload = fixture["factory"].payloads[alias]
    payload_bytes = payload.encode("utf-8")
    processes = [
        process for process in fixture["factory"].processes if process.alias == alias
    ]
    attempted = alias in fixture["factory"].popen_attempts
    if alias in fixture["factory"].calls:
        assert len(processes) == len(fixture["factory"].calls[alias])
    started_at = receipt["started_at"]
    ended_at = receipt["ended_at"]
    if attempted:
        assert _parse_timestamp(ended_at) > _parse_timestamp(started_at)
    else:
        assert started_at is None
        _parse_timestamp(ended_at)
    expected = {
        "protocol_version": 2,
        "authorization_id": AUTHORIZATION_ID,
        "authorization_sha256": fixture["authorization_sha256"],
        "risk_id": fixture["authorization"]["risk_id"],
        "control_session_nonce_sha256": fixture["authorization"][
            "control_session_nonce_sha256"
        ],
        "ticket": TICKET,
        "request_id": lane["job"].request_id,
        "root": root,
        "alias": alias,
        "provider": provider,
        "attempt": 1,
        "max_attempts": 1,
        "work_mode": "read_only",
        "objective": fixture["authorization"]["objective"],
        "ownership": fixture["authorization"]["ownership"],
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
        "repository_snapshot_sha256": fixture["snapshot"],
        "adapter": adapter,
        "process_or_session_id": (
            f"{provider}-operational-{alias}" if status == "DONE" else None
        ),
        "started_at": started_at,
        "ended_at": ended_at,
        "exit_code": 0 if status == "DONE" else None,
        "transport_status": "COMPLETED" if status == "DONE" else "UNKNOWN",
        "output_bytes": len(payload_bytes) if status == "DONE" else 0,
        "output_sha256": hashlib.sha256(
            payload_bytes if status == "DONE" else b""
        ).hexdigest(),
        "work_result_sha256": _canonical_sha256(expected_result),
        "evidence_scope": evidence_scope,
    }
    assert set(receipt) == RECEIPT_FIELDS
    assert receipt == expected
    persisted_result, persisted_receipt = _persisted_result_and_receipt(
        fixture, lane["job"].request_id
    )
    assert persisted_result == expected_result
    assert persisted_receipt == expected
    _assert_no_raw_material(outcome)


def _assert_batch_receipts(
    fixture: Mapping[str, Any],
    completed: Mapping[str, Any],
    *,
    unknown_aliases: frozenset[str] = frozenset(),
) -> None:
    assert set(completed["aliases"]) == set(ALIASES)
    for alias in ALIASES:
        _assert_exact_outcome_receipt(
            fixture,
            completed,
            alias,
            status="UNKNOWN" if alias in unknown_aliases else "DONE",
        )


def _assert_one_shot_bounded_cleanup(fixture: Mapping[str, Any]) -> None:
    factory = fixture["factory"]
    assert _process_call_count(fixture) == len(ALIASES)
    assert all(len(factory.calls[alias]) == 1 for alias in ALIASES)
    assert len(factory.processes) == len(ALIASES)
    assert factory.active == 0
    assert all(process.returncode is not None for process in factory.processes)


def _assert_exact_lane_lifecycle(
    fixture: Mapping[str, Any], alias: str, *, terminal: str
) -> None:
    events = [
        event
        for event_alias, event in fixture["store"].events
        if event_alias == alias
    ]
    core = [
        event
        for event in events
        if event
        in {
            "PREPARED",
            "STARTING",
            "POPEN_ATTEMPT",
            "POPEN",
            "RUNNING",
            "DONE",
            "UNKNOWN",
        }
    ]
    if alias not in fixture["factory"].popen_attempts:
        expected = ["PREPARED", terminal]
    elif not fixture["factory"].calls[alias]:
        expected = ["PREPARED", "STARTING", "POPEN_ATTEMPT", terminal]
    else:
        expected = [
            "PREPARED",
            "STARTING",
            "POPEN_ATTEMPT",
            "POPEN",
            "RUNNING",
            terminal,
        ]
    assert core == expected
    if alias in fixture["factory"].popen_attempts:
        assert events.count("CAPACITY_CONSUMED") == 1
        assert events.index("CAPACITY_CONSUMED") < events.index("POPEN_ATTEMPT")
    else:
        assert "CAPACITY_CONSUMED" not in events
    assert events.count("CAPACITY_RELEASED") == 1
    assert events.index("CAPACITY_RELEASED") < events.index(terminal)


def _assert_schema_cleanup(fixture: Mapping[str, Any]) -> None:
    expected_schema = _expected_provider_schema(fixture["schema_path"])
    for record in fixture["factory"].schema_records:
        assert record["mode"] == 0o600
        assert record["parent_mode"] == 0o700
        assert json.loads(record["bytes"]) == expected_schema
        path = Path(record["path"])
        assert not path.exists()
        assert not path.parent.exists()


def _assert_terminal_safety(
    fixture: Mapping[str, Any],
    completed: Mapping[str, Any],
    capsys: pytest.CaptureFixture[str],
    *,
    attempted_aliases: frozenset[str],
) -> None:
    _assert_exact_markers(fixture)
    assert fixture["factory"].marker_write_order == [
        name for name, _record in _expected_marker_records(fixture)
    ]
    _assert_capacity_accounting(fixture, attempted_aliases=attempted_aliases)
    _assert_schema_cleanup(fixture)
    assert fixture["factory"].communicate_calls == []
    _assert_no_raw_material(completed)
    _assert_no_raw_material(_tree_artifact_bytes(fixture["marker_store"]))
    _assert_no_raw_material(_queue_artifact_bytes(fixture))
    _assert_no_raw_material(_tree_artifact_bytes(fixture["capacity_store"]))
    captured = capsys.readouterr()
    _assert_no_raw_material({"stdout": captured.out, "stderr": captured.err})


def test_operational_entrypoint_exists_before_source() -> None:
    assert ENTRYPOINT.is_file(), "IDQ_MVP_080_OPERATIONAL_ENTRYPOINT_MISSING"


def test_provider_schema_oracle_is_strict_codex_compatible_and_authoritative() -> None:
    schema_path = REPOSITORY_ROOT / ".agents/schemas/multiagent-work-result-v2.schema.json"
    derived = _expected_provider_schema(schema_path)
    assert derived == command._provider_compatible_work_result_schema(schema_path)
    assert derived["type"] == "object"
    assert derived["additionalProperties"] is False
    assert set(derived["required"]) == WORK_RESULT_FIELDS
    assert set(derived["properties"]) == WORK_RESULT_FIELDS
    assert b'"oneOf"' not in _canonical_bytes(derived)


@pytest.mark.parametrize("alias", tuple(ALIASES))
def test_fixed_unknown_work_result_oracle_is_closed_typed_and_nonempty(
    alias: str,
) -> None:
    expected = _unknown_work_result(alias)
    _assert_work_result_contract(expected, expected_status="BLOCKED")
    assert _canonical_sha256(expected) == hashlib.sha256(
        _canonical_bytes(expected)
    ).hexdigest()
    _assert_no_raw_material(expected)


def test_fixture_queue_is_the_closed_authorization_authenticity_anchor(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    for alias, lane in fixture["lanes"].items():
        binding = fixture["authorization"]["bindings"][alias]
        expected_payload = {
            "schema_version": "idq-mvp-080-job-authority-v1",
            "authorization_id": AUTHORIZATION_ID,
            "authorization_sha256": fixture["authorization_sha256"],
            "authorization_binding_sha256": _canonical_sha256(binding),
            "objective_sha256": _digest(AUTHORIZATION_OBJECTIVE),
        }
        actual = fixture["store"].get_job(lane["job"].request_id)
        assert actual is not None
        assert actual.payload == expected_payload
        assert lane["job"].payload == expected_payload


def test_general_zero_side_effect_oracle_accepts_an_exact_clean_rejection(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fixture = _fixture(tmp_path)

    class RejectingOperational:
        @staticmethod
        def execute_idq_mvp_080_operational(**_arguments: object) -> None:
            raise ValueError("closed negative-control rejection")

    error = _assert_rejected_without_side_effect(
        RejectingOperational(), fixture, capsys
    )
    assert str(error) == "closed negative-control rejection"


@pytest.mark.parametrize(
    "surface",
    (
        "queue_db_wal_shm",
        "capacity_store",
        "marker_store",
        "input_config_auth_files",
        "provider_input_files",
        "account_input_files",
        "repository",
        "common_repository_worktree",
        "invocation_inputs",
        "queue_observer",
        "process_observer",
        "captured",
    ),
)
def test_general_zero_side_effect_oracle_detects_every_state_surface(
    tmp_path: Path, surface: str
) -> None:
    fixture = _fixture(tmp_path, repository_kind="linked")
    arguments = _invocation_arguments(fixture)
    empty_capture = {"stdout": b"", "stderr": b""}
    before = _zero_side_effect_snapshot(fixture, arguments, empty_capture)
    captured = empty_capture

    if surface == "queue_db_wal_shm":
        wal = fixture["store"].path.with_name(f"{fixture['store'].path.name}-wal")
        wal.write_bytes(b"negative-control WAL bytes")
    elif surface == "capacity_store":
        (fixture["capacity_store"] / "negative-control").write_bytes(b"changed")
    elif surface == "marker_store":
        fixture["marker_store"].mkdir()
        (fixture["marker_store"] / "negative-control.used").write_bytes(b"changed")
    elif surface == "input_config_auth_files":
        (fixture["input_store"] / "config.json").write_bytes(b"changed")
    elif surface == "provider_input_files":
        next(fixture["provider_root"].iterdir()).write_bytes(b"changed")
    elif surface == "account_input_files":
        account_home = Path(
            fixture["lanes"]["codex1"]["execution_context"][
                "qobs_expected_context"
            ]["account_home"]
        )
        (account_home / "changed").write_bytes(b"changed")
    elif surface == "repository":
        fixture["tracked"].write_bytes(b"changed")
    elif surface == "common_repository_worktree":
        (fixture["repository_seed"] / "tracked.txt").write_bytes(b"changed")
    elif surface == "invocation_inputs":
        changed_config = deepcopy(fixture["config"])
        changed_config["dispatcher_execution"] = "CHANGED"
        arguments = _invocation_arguments(fixture, config=changed_config)
    elif surface == "queue_observer":
        fixture["store"].events.append(("codex1", "CHANGED"))
    elif surface == "process_observer":
        fixture["factory"].communicate_calls.append("codex1")
    else:
        captured = {"stdout": b"changed", "stderr": b""}

    after = _zero_side_effect_snapshot(fixture, arguments, captured)
    assert after != before
    assert after[surface] != before[surface]


@pytest.mark.parametrize("repository_kind", REPOSITORY_KINDS)
@pytest.mark.parametrize("mutation_kind", REPOSITORY_MUTATIONS)
def test_repository_integrity_negative_control_detects_every_git_surface(
    tmp_path: Path, repository_kind: str, mutation_kind: str
) -> None:
    """Prove normal and linked-worktree byte oracles detect every drift class."""

    fixture = _fixture(tmp_path, repository_kind=repository_kind)
    repository = fixture["repository"]
    before_exact = _git_control_snapshot(repository)
    before_digest = _repository_snapshot(repository)
    git_dir, common_dir = _git_paths(repository)
    if repository_kind == "linked":
        assert (repository / ".git").is_file()
        assert git_dir != common_dir
        assert (git_dir / "commondir").is_file()
    else:
        assert (repository / ".git").is_dir()
        assert git_dir == common_dir

    _inject_repository_mutation(
        repository=repository,
        tracked=fixture["tracked"],
        alternate_head=fixture["alternate_head"],
        mutation_kind=mutation_kind,
    )

    after_exact = _git_control_snapshot(repository)
    assert after_exact != before_exact
    assert _repository_snapshot(repository) != before_digest
    changed_surface = {
        "tracked_file": "worktree",
        "index_only": "gitdir_control",
        "ref_only": "gitdir_control",
        "head_only": "gitdir_control",
        "common_ref": "common_control",
    }[mutation_kind]
    assert after_exact[changed_surface] != before_exact[changed_surface]


def test_auth02_is_closed_and_auth01_is_rejected_before_any_process(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path)
    assert set(fixture["authorization"]) == AUTHORIZATION_FIELDS
    assert set(fixture["authorization"]["bindings"]) == set(ALIASES)
    assert all(
        set(binding) == AUTHORIZATION_BINDING_FIELDS
        for binding in fixture["authorization"]["bindings"].values()
    )

    auth01 = deepcopy(fixture["authorization"])
    auth01["authorization_id"] = "IDQ-MVP-080-AUTH-01"
    error = _assert_rejected_without_side_effect(
        operational, fixture, capsys, authorization=auth01
    )
    _assert_no_raw_material(error)

    widened = deepcopy(fixture["authorization"])
    widened["adjacent_authority"] = True
    error = _assert_rejected_without_side_effect(
        operational, fixture, capsys, authorization=widened
    )
    _assert_no_raw_material(error)

    widened_binding = deepcopy(fixture["authorization"])
    widened_binding["bindings"]["codex1"]["raw_account_home"] = "/forbidden"
    error = _assert_rejected_without_side_effect(
        operational, fixture, capsys, authorization=widened_binding
    )
    _assert_no_raw_material(error)

    expired = deepcopy(fixture["authorization"])
    expired["expires_at"] = _timestamp(fixture["now"] - timedelta(seconds=1))
    error = _assert_rejected_without_side_effect(
        operational, fixture, capsys, authorization=expired
    )
    _assert_no_raw_material(error)

    opened = deepcopy(fixture["config"])
    opened["dispatcher_execution"] = "OPEN"
    error = _assert_rejected_without_side_effect(
        operational, fixture, capsys, config=opened
    )
    _assert_no_raw_material(error)

    assert command.effective_activation_state(fixture["config"]) == (True, "CLOSED")


@pytest.mark.parametrize("mutation", ("missing", "tampered"))
@pytest.mark.parametrize("field", tuple(sorted(AUTHORIZATION_FIELDS)))
def test_every_auth02_top_level_field_is_required_and_bound_to_durable_authority(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    mutation: str,
    field: str,
) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path)
    authorization = deepcopy(fixture["authorization"])
    if mutation == "missing":
        authorization.pop(field)
    else:
        values: dict[str, object] = {
            "schema_version": "idq-mvp-080-auth-v2",
            "protocol_version": 3,
            "authorization_id": "IDQ-MVP-080-AUTH-01",
            "ticket": "IDQ-MVP-081",
            "status": "USED",
            "issued_at": _timestamp(fixture["now"] - timedelta(seconds=1)),
            "expires_at": _timestamp(fixture["now"] + timedelta(seconds=1)),
            "ttl_seconds": AUTHORIZATION_TTL_SECONDS - 1,
            "control_session_nonce_sha256": _digest("tampered-control-nonce"),
            "aliases": ["codex1", "codex2", "agy1"],
            "attempt": 2,
            "max_attempts": 2,
            "work_mode": "workspace_write",
            "automatic_retry": True,
            "fallback": True,
            "substitution": True,
            "objective": "tampered objective",
            "ownership": "tampered ownership",
            "risk_id": "RISK-TAMPERED",
            "repository_snapshot_sha256": _digest("tampered-repository"),
            "marker_store_sha256": _digest("tampered-marker-store"),
            "bindings": {},
        }
        authorization[field] = values[field]

    error = _assert_rejected_without_side_effect(
        operational, fixture, capsys, authorization=authorization
    )
    _assert_no_raw_material(error)


@pytest.mark.parametrize(
    "field",
    (
        "schema_version",
        "protocol_version",
        "ticket",
        "issued_at",
        "expires_at",
        "ttl_seconds",
        "control_session_nonce_sha256",
        "objective",
        "ownership",
        "risk_id",
    ),
)
def test_coherent_caller_tamper_is_rejected_by_reloaded_queue_authority(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    field: str,
) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path)
    authorization = deepcopy(fixture["authorization"])
    config = deepcopy(fixture["config"])
    lanes = deepcopy(fixture["lanes"])
    replacements: dict[str, object] = {
        "schema_version": "idq-mvp-080-auth-v2",
        "protocol_version": 3,
        "ticket": "IDQ-MVP-081",
        "issued_at": _timestamp(fixture["now"] - timedelta(seconds=60)),
        "expires_at": _timestamp(
            fixture["now"] + timedelta(seconds=AUTHORIZATION_TTL_SECONDS - 60)
        ),
        "ttl_seconds": AUTHORIZATION_TTL_SECONDS - 60,
        "control_session_nonce_sha256": _digest("coherent-control-tamper"),
        "objective": "coherently tampered objective",
        "ownership": "coherently tampered ownership",
        "risk_id": "RISK-COHERENT-TAMPER",
    }
    authorization[field] = replacements[field]
    if field == "issued_at":
        authorization["expires_at"] = _timestamp(
            fixture["now"] - timedelta(seconds=60)
            + timedelta(seconds=AUTHORIZATION_TTL_SECONDS)
        )
    elif field == "expires_at":
        authorization["ttl_seconds"] = AUTHORIZATION_TTL_SECONDS - 60
    elif field == "ttl_seconds":
        authorization["expires_at"] = _timestamp(
            fixture["now"] + timedelta(seconds=AUTHORIZATION_TTL_SECONDS - 60)
        )
    contract = config["idq_mvp_080"]["authorization_contract"]
    if field in contract:
        contract[field] = authorization[field]
    if field == "expires_at":
        contract["ttl_seconds"] = authorization["ttl_seconds"]
    request_field = {
        "ticket": "ticket",
        "control_session_nonce_sha256": "control_session_nonce_sha256",
        "objective": "objective",
        "ownership": "ownership",
        "risk_id": "risk_id",
    }.get(field)
    if request_field:
        for lane in lanes.values():
            lane["request"][request_field] = authorization[field]

    attacker_sha256 = _canonical_sha256(authorization)
    for alias, lane in lanes.items():
        payload = dict(lane["job"].payload)
        payload["authorization_sha256"] = attacker_sha256
        payload["authorization_binding_sha256"] = _canonical_sha256(
            authorization["bindings"][alias]
        )
        if field == "objective":
            payload["objective_sha256"] = _digest(str(authorization["objective"]))
        lane["job"] = replace(lane["job"], payload=payload)

    error = _assert_rejected_without_side_effect(
        operational,
        fixture,
        capsys,
        authorization=authorization,
        config=config,
        lanes=lanes,
    )
    _assert_no_raw_material(error)


@pytest.mark.parametrize(
    "status", ("SEALED", "ACTIVE", "USED", "EXPIRED", "REVOKED", "")
)
def test_auth02_rejects_every_state_other_than_unused_without_side_effect(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], status: str
) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path)
    authorization = deepcopy(fixture["authorization"])
    authorization["status"] = status

    error = _assert_rejected_without_side_effect(
        operational, fixture, capsys, authorization=authorization
    )

    _assert_no_raw_material(error)


def test_successful_auth02_cannot_be_replayed_or_consume_another_nonce(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path)
    unused_authorization = deepcopy(fixture["authorization"])

    completed = _run(operational, fixture)
    assert completed["authorization_status"] == "SEALED"
    _assert_batch_receipts(fixture, completed)
    _assert_one_shot_bounded_cleanup(fixture)
    sealed_markers = _tree_snapshot(fixture["marker_store"])
    _assert_exact_markers(fixture)
    captured = _captured_bytes(capsys)
    assert captured == {"stdout": b"", "stderr": b""}

    operational = importlib.reload(operational)
    restarted_store = _RecordingQueue(fixture["store"].path)
    for alias, lane in fixture["lanes"].items():
        restarted_store.remember(lane["job"].request_id, alias)
    restarted_fixture = dict(fixture)
    restarted_fixture["store"] = restarted_store
    error = _assert_rejected_without_side_effect(
        operational,
        restarted_fixture,
        capsys,
        authorization=unused_authorization,
    )

    assert any(
        word in str(error).lower()
        for word in ("authorization", "nonce", "replay", "used", "sealed")
    )
    _assert_no_raw_material(error)
    assert _process_call_count(fixture) == len(ALIASES)
    assert _tree_snapshot(fixture["marker_store"]) == sealed_markers

    rebound_fixture = dict(restarted_fixture)
    rebound_fixture["marker_store"] = tmp_path / "rebound-empty-marker-store"
    error = _assert_rejected_without_side_effect(
        operational,
        rebound_fixture,
        capsys,
        authorization=unused_authorization,
    )
    _assert_no_raw_material(error)
    assert not rebound_fixture["marker_store"].exists()
    _assert_no_raw_material(completed)


def test_single_use_authorization_marker_rejects_symlink_precreation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path)
    marker_store = fixture["marker_store"]
    marker_store.mkdir(mode=0o700)
    target = tmp_path / "marker-symlink-target"
    target.write_bytes(b"must remain unchanged\n")
    authorization_marker = marker_store / _expected_marker_records(fixture)[0][0]
    authorization_marker.symlink_to(target)
    before_target = target.read_bytes()

    error = _assert_rejected_without_side_effect(
        operational, fixture, capsys
    )

    _assert_no_raw_material(error)
    assert authorization_marker.is_symlink()
    assert target.read_bytes() == before_target


def test_exact_four_one_shot_read_only_lanes_cannot_retry_or_substitute(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path)
    invalid_authorizations: list[dict[str, object]] = []
    for field, value in (
        ("attempt", 2),
        ("max_attempts", 2),
        ("work_mode", "workspace_write"),
        ("automatic_retry", True),
        ("fallback", True),
        ("substitution", True),
    ):
        changed = deepcopy(fixture["authorization"])
        changed[field] = value
        invalid_authorizations.append(changed)
    missing_alias = deepcopy(fixture["authorization"])
    missing_alias["aliases"] = ["codex1", "codex2", "agy1"]
    invalid_authorizations.append(missing_alias)
    substituted_alias = deepcopy(fixture["authorization"])
    substituted_alias["aliases"] = ["codex1", "codex2", "codex3", "agy1"]
    invalid_authorizations.append(substituted_alias)
    extra_alias = deepcopy(fixture["authorization"])
    extra_alias["aliases"] = [*ALIASES, "codex3"]
    invalid_authorizations.append(extra_alias)
    duplicate_alias = deepcopy(fixture["authorization"])
    duplicate_alias["aliases"] = [*ALIASES, "codex1"]
    invalid_authorizations.append(duplicate_alias)
    reordered_aliases = deepcopy(fixture["authorization"])
    reordered_aliases["aliases"] = list(reversed(ALIASES))
    invalid_authorizations.append(reordered_aliases)

    for authorization in invalid_authorizations:
        _assert_rejected_without_side_effect(
            operational, fixture, capsys, authorization=authorization
        )

    changed_lanes = deepcopy(fixture["lanes"])
    changed_lanes["codex1"]["request"]["attempt"] = 2
    _assert_rejected_without_side_effect(
        operational, fixture, capsys, lanes=changed_lanes
    )

    incomplete_lanes = dict(fixture["lanes"])
    incomplete_lanes.pop("agy2")
    _assert_rejected_without_side_effect(
        operational, fixture, capsys, lanes=incomplete_lanes
    )

    extra_lanes = deepcopy(fixture["lanes"])
    extra_lanes["codex3"] = deepcopy(extra_lanes["codex1"])
    _assert_rejected_without_side_effect(
        operational, fixture, capsys, lanes=extra_lanes
    )

    duplicate_identity_lanes = deepcopy(fixture["lanes"])
    duplicate_identity_lanes["agy2"]["job"] = replace(
        duplicate_identity_lanes["agy2"]["job"],
        request_id=duplicate_identity_lanes["codex1"]["job"].request_id,
        alias="codex1",
    )
    _assert_rejected_without_side_effect(
        operational, fixture, capsys, lanes=duplicate_identity_lanes
    )

    activation_allowed = deepcopy(fixture["config"])
    activation_allowed["activation_prohibited"] = False
    _assert_rejected_without_side_effect(
        operational, fixture, capsys, config=activation_allowed
    )

    assert _process_call_count(fixture) == 0
    assert _marker_files(fixture) == []


@pytest.mark.parametrize("surface", ("authorization_binding", "lane_preflight"))
@pytest.mark.parametrize("alias", tuple(ALIASES))
@pytest.mark.parametrize(
    "field",
    tuple(sorted(AUTHORIZATION_BINDING_FIELDS)),
)
def test_all_bindings_preflight_as_one_barrier_before_nonce_or_popen(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    surface: str,
    alias: str,
    field: str,
) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path)
    if surface == "authorization_binding":
        authorization = deepcopy(fixture["authorization"])
        changed_value = {
            "request_id": f"tampered-request-{alias}",
            "root": "B" if ALIASES[alias][1] == "A" else "A",
            "provider": "agy" if ALIASES[alias][0] == "codex" else "codex",
        }.get(field, _digest(f"tampered:{surface}:{alias}:{field}"))
        authorization["bindings"][alias][field] = changed_value
        overrides = {"authorization": authorization}
    else:
        lanes = deepcopy(fixture["lanes"])
        if field == "request_id":
            lanes[alias]["job"] = replace(
                lanes[alias]["job"], request_id=f"tampered-request-{alias}"
            )
        elif field == "root":
            lanes[alias]["job"] = replace(
                lanes[alias]["job"],
                root="B" if ALIASES[alias][1] == "A" else "A",
            )
        elif field == "provider":
            lanes[alias]["request"]["provider"] = (
                "agy" if ALIASES[alias][0] == "codex" else "codex"
            )
        elif field == "capacity_lease_sha256":
            lanes[alias]["capacity_lease"]["lease_sha256"] = _digest(
                f"tampered:{surface}:{alias}:{field}"
            )
        else:
            lanes[alias]["request"][field] = _digest(
                f"tampered:{surface}:{alias}:{field}"
            )
        overrides = {"lanes": lanes}

    error = _assert_rejected_without_side_effect(
        operational, fixture, capsys, **overrides
    )

    _assert_no_raw_material(error)


@pytest.mark.parametrize("alias", tuple(ALIASES))
@pytest.mark.parametrize(
    "identity_surface",
    (
        "job_alias",
        "request_alias",
        "qobs_alias",
        "qobs_provider",
        "lease_account",
        "lease_pool",
        "lease_provider",
        "lease_request_id",
    ),
)
def test_every_actual_lane_identity_is_bound_before_group_start(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    alias: str,
    identity_surface: str,
) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path)
    lanes = deepcopy(fixture["lanes"])
    lane = lanes[alias]
    other_alias = next(candidate for candidate in ALIASES if candidate != alias)
    other_provider = "agy" if ALIASES[alias][0] == "codex" else "codex"
    mutations = {
        "job_alias": lambda: lane.update(
            {"job": replace(lane["job"], alias=other_alias)}
        ),
        "request_alias": lambda: lane["request"].update({"alias": other_alias}),
        "qobs_alias": lambda: lane["execution_context"]["qobs_expected_context"].update(
            {"alias": other_alias}
        ),
        "qobs_provider": lambda: lane["execution_context"][
            "qobs_expected_context"
        ].update({"provider": other_provider}),
        "lease_account": lambda: lane["capacity_lease"].update(
            {"account": other_alias}
        ),
        "lease_pool": lambda: lane["capacity_lease"].update({"pool": other_alias}),
        "lease_provider": lambda: lane["capacity_lease"].update(
            {"provider": other_provider}
        ),
        "lease_request_id": lambda: lane["capacity_lease"].update(
            {"request_id": f"tampered-lease-request-{alias}"}
        ),
    }
    mutations[identity_surface]()

    error = _assert_rejected_without_side_effect(
        operational, fixture, capsys, lanes=lanes
    )
    _assert_no_raw_material(error)


@pytest.mark.parametrize("offset_seconds", (-601, 61))
def test_fully_digest_coherent_qobs_still_requires_live_freshness(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    offset_seconds: int,
) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path, qobs_observed_offset_seconds=offset_seconds)

    error = _assert_rejected_without_side_effect(
        operational, fixture, capsys
    )
    _assert_no_raw_material(error)


@pytest.mark.parametrize(
    "fixture_options",
    (
        {
            "authorization_issued_offset_seconds": 61,
            "authorization_expires_offset_seconds": AUTHORIZATION_TTL_SECONDS + 61,
        },
        {
            "authorization_issued_offset_seconds": -AUTHORIZATION_TTL_SECONDS - 1,
            "authorization_expires_offset_seconds": -1,
        },
        {"authorization_expires_offset_seconds": AUTHORIZATION_TTL_SECONDS - 1},
        {
            "authorization_expires_offset_seconds": AUTHORIZATION_TTL_SECONDS - 1,
            "authorization_ttl_seconds": AUTHORIZATION_TTL_SECONDS - 1,
        },
    ),
    ids=("future-issued", "expired", "ttl-relation", "noncanonical-ttl"),
)
def test_digest_coherent_authorization_still_enforces_time_relations_and_freshness(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    fixture_options: dict[str, int],
) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path, **fixture_options)

    error = _assert_rejected_without_side_effect(
        operational, fixture, capsys
    )
    _assert_no_raw_material(error)


@pytest.mark.parametrize(
    "surface",
    (
        "executable_bytes",
        "executable_mode",
        "account_mode",
        "account_inode",
        "capacity_expired",
        "capacity_released",
    ),
)
def test_actual_executable_account_capacity_and_lease_state_are_revalidated(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    surface: str,
) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path)
    alias = "codex1"
    lane = fixture["lanes"][alias]
    context = lane["execution_context"]["qobs_expected_context"]
    overrides: dict[str, object] = {}
    if surface == "executable_bytes":
        Path(context["resolved_executable"]).write_bytes(b"coherent replacement\n")
    elif surface == "executable_mode":
        Path(context["resolved_executable"]).chmod(0o600)
    elif surface == "account_mode":
        Path(context["account_home"]).chmod(0o755)
    elif surface == "account_inode":
        account_home = Path(context["account_home"])
        replaced = account_home.with_name(f"{account_home.name}.replaced")
        account_home.rename(replaced)
        account_home.mkdir(mode=0o700)
    elif surface == "capacity_expired":
        overrides["now"] = fixture["now"] + timedelta(seconds=121)
    else:
        capacity.release_lease(
            fixture["capacity_store"],
            lane["capacity_lease"],
            policy=lane["capacity_policy"],
            now=fixture["now"].timestamp(),
        )

    error = _assert_rejected_without_side_effect(
        operational, fixture, capsys, **overrides
    )
    _assert_no_raw_material(error)


def test_repository_binding_is_preflighted_before_nonce_or_popen(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path)

    stale_repository = deepcopy(fixture["authorization"])
    stale_repository["repository_snapshot_sha256"] = _digest("stale repository")
    error = _assert_rejected_without_side_effect(
        operational, fixture, capsys, authorization=stale_repository
    )

    _assert_no_raw_material(error)


def test_operational_batch_uses_isolated_native_popen_and_safe_durable_receipts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path)
    original_config = deepcopy(fixture["config"])
    before_integrity = _repository_integrity_evidence(fixture["repository"])
    before_snapshot = _repository_snapshot(fixture["repository"])
    authoritative_schema_bytes = fixture["schema_path"].read_bytes()
    monkeypatch.setenv("IDQ_PROVIDER_SECRET_SENTINEL", INHERITED_ENV_SENTINEL)

    parameters = inspect.signature(
        operational.execute_idq_mvp_080_operational
    ).parameters
    assert "popen_factory" not in parameters
    assert operational.subprocess is subprocess
    assert operational.MAX_PROVIDER_OUTPUT_BYTES == OUTPUT_CAP_BYTES
    assert operational.MAX_PROVIDER_STDERR_BYTES == STDERR_CAP_BYTES
    assert 0 < operational.PROVIDER_READ_CHUNK_BYTES <= MAX_READ_CHUNK_BYTES

    completed = _run(operational, fixture)

    assert set(completed) == {
        "authorization_id",
        "authorization_status",
        "ticket",
        "status",
        "attempt",
        "ordinary_activation",
        "repository_snapshot_sha256",
        "aliases",
    }
    assert completed["authorization_id"] == AUTHORIZATION_ID
    assert completed["authorization_status"] == "SEALED"
    assert completed["ticket"] == TICKET
    assert completed["status"] == "DONE"
    assert completed["attempt"] == 1
    assert completed["ordinary_activation"] == "CLOSED"
    assert completed["repository_snapshot_sha256"] == before_snapshot
    assert set(completed["aliases"]) == set(ALIASES)
    assert fixture["factory"].max_active >= 2
    assert fixture["factory"].popen_attempts == list(ALIASES)
    assert fixture["factory"].communicate_calls == []
    assert fixture["factory"].group_signals == {}
    expected_marker_order = [name for name, _record in _expected_marker_records(fixture)]
    assert fixture["factory"].marker_write_order == expected_marker_order
    _assert_exact_markers(fixture)
    final_marker_snapshot = _exact_path_snapshot(fixture["marker_store"])
    assert fixture["factory"].marker_snapshots == [
        final_marker_snapshot
    ] * len(ALIASES)

    repository = str(fixture["repository"].resolve())
    for alias, (provider, root) in ALIASES.items():
        assert len(fixture["factory"].calls[alias]) == 1
        process_call = fixture["factory"].calls[alias][0]
        argv = process_call["argv"]
        kwargs = process_call["kwargs"]
        lane = fixture["lanes"][alias]
        context = lane["execution_context"]["qobs_expected_context"]
        executable = context["resolved_executable"]
        account_home = context["account_home"]
        schema_record = next(
            record
            for record in fixture["factory"].schema_records
            if record["alias"] == alias
        )
        temporary_schema = str(schema_record["path"])
        assert temporary_schema != str(fixture["schema_path"])
        assert not Path(temporary_schema).is_relative_to(fixture["repository"])
        assert Path(temporary_schema).name == "work-result-v2.provider.json"
        assert Path(temporary_schema).parent.name.startswith(
            "horo-idq-provider-schema-"
        )
        assert schema_record["mode"] == 0o600
        assert schema_record["parent_mode"] == 0o700
        assert json.loads(schema_record["bytes"]) == _expected_provider_schema(
            fixture["schema_path"]
        )
        assert os.path.isabs(executable)
        if provider == "codex":
            assert argv == (
                executable,
                "exec",
                "-C",
                repository,
                "-s",
                "read-only",
                "--json",
                "--output-schema",
                temporary_schema,
                "-",
            )
            expected_stdin = lane["prompt_stdin"].encode("utf-8")
            home_env = "CODEX_HOME"
        else:
            assert argv == (
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
                temporary_schema,
            )
            expected_stdin = _agy_stdin(lane["prompt_stdin"]).encode("utf-8")
            home_env = "AGY_HOME"

        environment = kwargs.pop("env")
        assert kwargs == {
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": False,
            "bufsize": 0,
            "cwd": repository,
            "shell": False,
            "start_new_session": True,
        }
        assert environment[home_env] == account_home
        assert set(environment) <= SAFE_PROVIDER_ENV_KEYS | {home_env}
        assert ({"CODEX_HOME", "AGY_HOME"} - {home_env}).isdisjoint(environment)
        assert INHERITED_ENV_SENTINEL not in json.dumps(environment, sort_keys=True)
        process = next(
            process
            for process in fixture["factory"].processes
            if process.alias == alias
        )
        assert bytes(process.stdin.buffer) == expected_stdin
        assert process.stdin.closed
        reads = fixture["factory"].read_calls[alias]
        assert {item["stream"] for item in reads} == {"stdout", "stderr"}
        assert all(0 < item["requested"] <= MAX_READ_CHUNK_BYTES for item in reads)
        assert all(item["returned"] <= item["requested"] for item in reads)
        raw_stderr = fixture["factory"].stderr_payloads[alias]
        assert raw_stderr.strip()
        assert STDERR_SENTINEL in raw_stderr

        alias_events = [
            event
            for event_alias, event in fixture["store"].events
            if event_alias == alias
        ]
        core_events = [
            event
            for event in alias_events
            if event
            in {"PREPARED", "STARTING", "POPEN_ATTEMPT", "POPEN", "RUNNING", "DONE"}
        ]
        assert core_events == [
            "PREPARED",
            "STARTING",
            "POPEN_ATTEMPT",
            "POPEN",
            "RUNNING",
            "DONE",
        ]
        assert alias_events.index("RUNNING") < alias_events.index("STDIN_WRITE")
        assert alias_events.index("STDIN_CLOSED") < alias_events.index("DONE")
        assert alias_events.index("STDOUT_READ") < alias_events.index("DONE")
        assert alias_events.index("STDERR_READ") < alias_events.index("DONE")
        assert alias_events.index("EXIT") < alias_events.index("DONE")
        _assert_exact_lane_lifecycle(fixture, alias, terminal="DONE")

        _assert_exact_outcome_receipt(fixture, completed, alias, status="DONE")
        outcome = completed["aliases"][alias]
        receipt = outcome["receipt"]
        _assert_no_raw_material(receipt)
        _assert_no_raw_material(outcome)
        assert str(account_home) not in json.dumps(receipt, sort_keys=True)
        assert str(executable) not in json.dumps(receipt, sort_keys=True)
        assert fixture["store"].get_job(lane["job"].request_id).state == "DONE"
        assert fixture["store"].get_result(lane["job"].request_id) == _work_result(
            alias
        )

    _assert_one_shot_bounded_cleanup(fixture)
    _assert_capacity_accounting(
        fixture, attempted_aliases=frozenset(ALIASES)
    )
    assert fixture["schema_path"].read_bytes() == authoritative_schema_bytes
    assert all(
        not Path(record["path"]).exists()
        and not Path(record["path"]).parent.exists()
        for record in fixture["factory"].schema_records
    )
    _assert_no_raw_material(_tree_artifact_bytes(fixture["marker_store"]))
    _assert_no_raw_material(_queue_artifact_bytes(fixture))
    _assert_no_raw_material(_tree_artifact_bytes(fixture["capacity_store"]))
    _assert_no_raw_material(completed)
    captured = capsys.readouterr()
    _assert_no_raw_material({"stdout": captured.out, "stderr": captured.err})
    assert fixture["config"] == original_config
    assert command.effective_activation_state(fixture["config"]) == (True, "CLOSED")
    assert _repository_snapshot(fixture["repository"]) == before_snapshot
    assert _repository_integrity_evidence(fixture["repository"]) == before_integrity


@pytest.mark.parametrize("alias", ("codex1", "agy1"))
@pytest.mark.parametrize(
    "malformation",
    (
        "missing_work_result",
        "malformed_work_result",
        "schema_invalid_mapping",
        "missing_terminal_event",
        "duplicate_terminal_event",
        "competing_terminal_work_results",
    ),
)
def test_malformed_or_missing_work_result_and_terminal_events_are_rejected(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    alias: str,
    malformation: str,
) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path)
    fixture["factory"].payloads[alias] = _invalid_provider_output(alias, malformation)

    completed = _run(operational, fixture)

    assert completed["authorization_status"] == "SEALED"
    assert completed["status"] == "UNKNOWN"
    _assert_batch_receipts(fixture, completed, unknown_aliases=frozenset({alias}))
    _assert_one_shot_bounded_cleanup(fixture)
    for lane_alias in ALIASES:
        _assert_exact_lane_lifecycle(
            fixture,
            lane_alias,
            terminal="UNKNOWN" if lane_alias == alias else "DONE",
        )
    assert (
        fixture["store"].get_job(fixture["lanes"][alias]["job"].request_id).state
        == "UNKNOWN"
    )
    _assert_terminal_safety(
        fixture,
        completed,
        capsys,
        attempted_aliases=frozenset(ALIASES),
    )


@pytest.mark.parametrize("alias", ("codex1", "agy1"))
@pytest.mark.parametrize("stream", ("stdout", "stderr"))
@pytest.mark.parametrize("delta", (0, 1))
def test_incremental_provider_capture_enforces_exact_stream_caps(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    alias: str,
    stream: str,
    delta: int,
) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path, hang_alias=alias if delta else None)
    cap = OUTPUT_CAP_BYTES if stream == "stdout" else STDERR_CAP_BYTES
    target = cap + delta
    if stream == "stdout":
        fixture["factory"].payloads[alias] = _provider_output_with_exact_bytes(
            alias, target
        )
    else:
        prefix = f"{STDERR_SENTINEL}:{alias}:".encode()
        assert len(prefix) <= target
        fixture["factory"].stderr_payloads[alias] = (
            prefix + (b"E" * (target - len(prefix)))
        ).decode("ascii")

    completed = _run(operational, fixture)

    unknown = frozenset({alias}) if delta else frozenset()
    assert completed["status"] == ("UNKNOWN" if delta else "DONE")
    _assert_batch_receipts(fixture, completed, unknown_aliases=unknown)
    _assert_one_shot_bounded_cleanup(fixture)
    for lane_alias in ALIASES:
        _assert_exact_lane_lifecycle(
            fixture,
            lane_alias,
            terminal="UNKNOWN" if lane_alias in unknown else "DONE",
        )
    reads = [
        item
        for item in fixture["factory"].read_calls[alias]
        if item["stream"] == stream
    ]
    assert reads
    assert all(0 < item["requested"] <= MAX_READ_CHUNK_BYTES for item in reads)
    assert sum(item["returned"] for item in reads) <= cap + MAX_READ_CHUNK_BYTES
    if delta:
        assert fixture["factory"].group_signals[alias][0] == signal.SIGTERM
    _assert_terminal_safety(
        fixture,
        completed,
        capsys,
        attempted_aliases=frozenset(ALIASES),
    )


@pytest.mark.parametrize("alias", ("codex1", "agy1"))
@pytest.mark.parametrize("branch", ("partial_output", "nonzero_exit"))
def test_partial_output_and_nonzero_exit_are_fixed_unknown_without_raw_echo(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    alias: str,
    branch: str,
) -> None:
    operational = _operational()
    fixture = _fixture(
        tmp_path, nonzero_alias=alias if branch == "nonzero_exit" else None
    )
    if branch == "partial_output":
        payload = fixture["factory"].payloads[alias]
        fixture["factory"].payloads[alias] = payload[: len(payload) // 2]

    completed = _run(operational, fixture)

    assert completed["status"] == "UNKNOWN"
    _assert_batch_receipts(fixture, completed, unknown_aliases=frozenset({alias}))
    _assert_one_shot_bounded_cleanup(fixture)
    for lane_alias in ALIASES:
        _assert_exact_lane_lifecycle(
            fixture,
            lane_alias,
            terminal="UNKNOWN" if lane_alias == alias else "DONE",
        )
    _assert_terminal_safety(
        fixture,
        completed,
        capsys,
        attempted_aliases=frozenset(ALIASES),
    )


def test_partial_batch_popen_failure_seals_all_lanes_and_cleans_started_groups(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path, popen_failure_alias="agy1")

    completed = _run(operational, fixture)

    assert completed["status"] == "UNKNOWN"
    assert fixture["factory"].popen_attempts == ["codex1", "codex2", "agy1"]
    assert _process_call_count(fixture) == 2
    _assert_batch_receipts(fixture, completed, unknown_aliases=frozenset(ALIASES))
    for alias in ALIASES:
        _assert_exact_lane_lifecycle(fixture, alias, terminal="UNKNOWN")
    for alias in ("codex1", "codex2"):
        assert fixture["factory"].group_signals[alias][0] == signal.SIGTERM
    assert fixture["factory"].active == 0
    _assert_terminal_safety(
        fixture,
        completed,
        capsys,
        attempted_aliases=frozenset({"codex1", "codex2", "agy1"}),
    )


def test_partial_marker_commit_seals_without_start_and_cannot_be_cleaned_for_retry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path, marker_failure_after=4)
    expected_markers = _expected_marker_records(fixture)

    completed = _run(operational, fixture)

    assert completed["authorization_status"] == "SEALED"
    assert completed["status"] == "UNKNOWN"
    assert fixture["factory"].popen_attempts == []
    assert fixture["factory"].marker_write_order == [
        name for name, _record in expected_markers[:4]
    ]
    assert [path.name for path in _marker_files(fixture)] == sorted(
        name for name, _record in expected_markers[:3]
    )
    for name, record in expected_markers[:3]:
        path = fixture["marker_store"] / name
        assert path.read_bytes() == _canonical_bytes(record) + b"\n"
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert fixture["factory"].schema_records == []
    _assert_batch_receipts(fixture, completed, unknown_aliases=frozenset(ALIASES))
    for alias in ALIASES:
        _assert_exact_lane_lifecycle(fixture, alias, terminal="UNKNOWN")
    _assert_capacity_accounting(fixture, attempted_aliases=frozenset())
    _assert_no_raw_material(completed)
    _assert_no_raw_material(_tree_artifact_bytes(fixture["marker_store"]))
    _assert_no_raw_material(_queue_artifact_bytes(fixture))
    _assert_no_raw_material(_tree_artifact_bytes(fixture["capacity_store"]))
    captured = capsys.readouterr()
    _assert_no_raw_material({"stdout": captured.out, "stderr": captured.err})


def test_post_start_timeout_is_unknown_with_no_retry_or_substitution(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    operational = _operational()
    fixture = _fixture(
        tmp_path,
        failure_alias="agy2",
        cleanup_requires_kill_alias="agy2",
    )

    completed = _run(operational, fixture)

    assert completed["status"] == "UNKNOWN"
    _assert_batch_receipts(fixture, completed, unknown_aliases=frozenset({"agy2"}))
    _assert_one_shot_bounded_cleanup(fixture)
    request_id = fixture["lanes"]["agy2"]["job"].request_id
    assert fixture["store"].get_job(request_id).state == "UNKNOWN"
    assert fixture["factory"].group_signals["agy2"] == [
        signal.SIGTERM,
        signal.SIGKILL,
    ]
    assert all(
        completed["aliases"][alias]["status"] == "DONE"
        for alias in ("codex1", "codex2", "agy1")
    )
    for alias in ALIASES:
        _assert_exact_lane_lifecycle(
            fixture,
            alias,
            terminal="UNKNOWN" if alias == "agy2" else "DONE",
        )
    _assert_terminal_safety(
        fixture,
        completed,
        capsys,
        attempted_aliases=frozenset(ALIASES),
    )


def test_process_group_cleanup_failure_is_durable_unknown_and_non_echoing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    operational = _operational()
    fixture = _fixture(
        tmp_path,
        failure_alias="agy2",
        cleanup_failure_alias="agy2",
    )

    completed = _run(operational, fixture)

    assert completed["status"] == "UNKNOWN"
    _assert_batch_receipts(fixture, completed, unknown_aliases=frozenset({"agy2"}))
    for alias in ALIASES:
        _assert_exact_lane_lifecycle(
            fixture,
            alias,
            terminal="UNKNOWN" if alias == "agy2" else "DONE",
        )
    assert fixture["factory"].group_signals["agy2"]
    assert fixture["factory"].active == 1
    _assert_terminal_safety(
        fixture,
        completed,
        capsys,
        attempted_aliases=frozenset(ALIASES),
    )


@pytest.mark.parametrize("repository_kind", REPOSITORY_KINDS)
@pytest.mark.parametrize("mutation_kind", REPOSITORY_MUTATIONS)
def test_repository_snapshot_drift_invalidates_every_started_result(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    repository_kind: str,
    mutation_kind: str,
) -> None:
    operational = _operational()
    fixture = _fixture(
        tmp_path,
        mutate_alias="codex1",
        mutation_kind=mutation_kind,
        repository_kind=repository_kind,
    )

    completed = _run(operational, fixture)

    assert completed["status"] == "UNKNOWN"
    assert _repository_snapshot(fixture["repository"]) != fixture["snapshot"]
    _assert_batch_receipts(fixture, completed, unknown_aliases=frozenset(ALIASES))
    assert all(
        fixture["store"].get_job(lane["job"].request_id).state == "UNKNOWN"
        for lane in fixture["lanes"].values()
    )
    _assert_one_shot_bounded_cleanup(fixture)
    for alias in ALIASES:
        _assert_exact_lane_lifecycle(fixture, alias, terminal="UNKNOWN")
    _assert_terminal_safety(
        fixture,
        completed,
        capsys,
        attempted_aliases=frozenset(ALIASES),
    )
    assert command.effective_activation_state(fixture["config"]) == (True, "CLOSED")


@pytest.mark.parametrize("repository_kind", REPOSITORY_KINDS)
def test_git_worktree_index_refs_and_head_metadata_remain_exactly_immutable(
    tmp_path: Path, repository_kind: str
) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path, repository_kind=repository_kind)
    repository = fixture["repository"]
    before_evidence = _repository_integrity_evidence(repository)
    before_status = _git(
        repository, "status", "--porcelain=v1", "--untracked-files=all"
    ).stdout
    assert before_status == ""

    completed = _run(operational, fixture)

    after_status = _git(
        repository, "status", "--porcelain=v1", "--untracked-files=all"
    ).stdout
    after_evidence = _repository_integrity_evidence(repository)
    assert completed["status"] == "DONE"
    _assert_batch_receipts(fixture, completed)
    _assert_one_shot_bounded_cleanup(fixture)
    assert completed["repository_snapshot_sha256"] == fixture["snapshot"]
    assert after_status == before_status
    assert after_evidence == before_evidence
