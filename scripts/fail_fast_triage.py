#!/usr/bin/env python3
"""Run bounded, fail-closed diagnostics for release triage.

The command intentionally emits only ASCII. It checks repository state,
generated agent configuration, the secret scanner, Python syntax, committed
test provenance, and (unless offline) the identities deployed to Vercel and
the canonical Hugging Face Docker backend.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import signal
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REPORT_SCHEMA_VERSION = "fail-fast-triage-report-v1"
DEFAULT_TIMEOUT_SECONDS = 15
MAX_TIMEOUT_SECONDS = 300
MAX_COMMAND_OUTPUT_CHARS = 32_768
MAX_FIELD_CHARS = 2_048
MAX_METADATA_STRING_CHARS = 1_024
MAX_JSON_REPORT_BYTES = 65_536
MAX_HTTP_BODY_BYTES = 65_536
MAX_PYTHON_FILE_BYTES = 8 * 1024 * 1024
MAX_COLLECTION_ITEMS = 64
MAX_JSON_DEPTH = 5
MAX_ARGPARSE_OUTPUT_CHARS = 8_000
HTTP_READ_CHUNK_BYTES = 8_192

VERCEL_VERSION_URL = "https://horo-consultant-psi.vercel.app/version.json"
HF_BACKEND_URL = "https://pphothidaen-horoconsultant-core-backend.hf.space"
RELEASE_IDENTITY_FIELDS = (
    "version",
    "release_source_commit",
    "release_source_revision",
    "release_source_metadata_path",
    "release_source_metadata_sha256",
)
RELEASE_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+\.([0-9a-f]{7,40})$")
RELEASE_COMMIT_RE = re.compile(r"^[0-9a-f]{7,40}$")
RELEASE_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
RELEASE_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

_URL_CREDENTIAL_RE = re.compile(
    r"(?i)(https?://[^\s/:@]+:)([^\s/@]+)(@)"
)
_QUERY_CREDENTIAL_RE = re.compile(
    r"(?i)([?&](?:[a-z0-9]+[_-])*(?:access[_-]?token|auth(?:orization)?|api[_-]?key|"
    r"client[_-]?secret|aws[_-]?secret[_-]?access[_-]?key|token|secret|password|passwd|credential)=)([^&#\s]+)"
)
_NAMED_CREDENTIAL_RE = re.compile(
    r"(?i)\b((?:[a-z0-9]+[_-])*(?:authorization|access[_-]?token|api[_-]?key|client[_-]?secret|"
    r"aws[_-]?secret[_-]?access[_-]?key|token|secret|password|passwd|credential))(\s*[:=]\s*)(?:bearer\s+|basic\s+)?([^\s,;]+)"
)
_QUOTED_CREDENTIAL_RE = re.compile(
    r"(?i)([\"'](?:[a-z0-9]+[_-])*(?:authorization|access[_-]?token|api[_-]?key|client[_-]?secret|"
    r"aws[_-]?secret[_-]?access[_-]?key|token|secret|password|passwd|credential)[\"']\s*:\s*[\"'])(?:bearer\s+|basic\s+)?([^\"']+)([\"'])"
)
_BASIC_AUTH_RE = re.compile(
    r"(?i)\bauthorization\s*[:=]\s*basic\s+[^\s,;'\"]+"
)
_STANDALONE_BASIC_RE = re.compile(
    r"(?i)\bbasic\s+[^\s,;'\"]+"
)
_SENSITIVE_KEY_RE = re.compile(
    r"(?i)(?:authorization|access[_-]?token|api[_-]?key|client[_-]?secret|aws[_-]?secret[_-]?access[_-]?key|secret|token|password|passwd|credential|auth)"
)

_SUBPROCESS_RUN = subprocess.run


@dataclass
class ProbeResult:
    """One bounded diagnostic result."""

    probe_id: str
    name: str
    passed: bool
    details: str
    root_cause: str | None = None
    remediation_command: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TriageReport:
    """Aggregate result in stable probe order."""

    total_probes: int
    passed_probes: int
    failed_probes: int
    overall_status: str
    probes: list[ProbeResult] = field(default_factory=list)


@dataclass
class _SanitizeState:
    truncated: bool = False


def _redact_sensitive_text(raw: str) -> str:
    """Remove common credential forms while retaining diagnostic fingerprints."""
    redacted = _URL_CREDENTIAL_RE.sub(r"\1[REDACTED]\3", raw)
    redacted = _QUERY_CREDENTIAL_RE.sub(r"\1[REDACTED]", redacted)
    redacted = _QUOTED_CREDENTIAL_RE.sub(r"\1[REDACTED]\3", redacted)
    redacted = _NAMED_CREDENTIAL_RE.sub(r"\1\2[REDACTED]", redacted)
    redacted = _BASIC_AUTH_RE.sub(r"Authorization: [REDACTED]", redacted)
    redacted = _STANDALONE_BASIC_RE.sub(r"[REDACTED]", redacted)
    return redacted


def _bounded_ascii(value: object, limit: int = MAX_FIELD_CHARS) -> str:
    """Return deterministic printable ASCII with an explicit size boundary."""
    try:
        raw = str(value)
    except Exception:  # noqa: BLE001 - formatting must never break diagnostics
        raw = "<unprintable>"
    raw = _redact_sensitive_text(raw)
    escaped = raw.encode("ascii", errors="backslashreplace").decode("ascii")
    printable: list[str] = []
    for char in escaped:
        codepoint = ord(char)
        if char == "\n":
            printable.append("\\n")
        elif char == "\r":
            printable.append("\\r")
        elif char == "\t":
            printable.append("\\t")
        elif codepoint < 32 or codepoint == 127:
            printable.append(f"\\x{codepoint:02x}")
        else:
            printable.append(char)
    result = "".join(printable)
    if len(result) <= limit:
        return result
    marker = "...[truncated]"
    return result[: max(0, limit - len(marker))] + marker


def _bounded_ascii_capture(
    value: object,
    limit: int = MAX_COMMAND_OUTPUT_CHARS,
) -> str:
    """Preserve JSON whitespace while making subprocess capture ASCII-only."""
    try:
        raw = str(value)
    except Exception:  # noqa: BLE001 - capture must remain reportable
        raw = "<unprintable>"
    raw = _redact_sensitive_text(raw)
    escaped = raw.encode("ascii", errors="backslashreplace").decode("ascii")
    printable: list[str] = []
    for char in escaped:
        codepoint = ord(char)
        if codepoint < 32 and char not in {"\n", "\r", "\t"}:
            printable.append(f"\\x{codepoint:02x}")
        elif codepoint == 127:
            printable.append("\\x7f")
        else:
            printable.append(char)
    result = "".join(printable)
    if len(result) <= limit:
        return result
    marker = "...[truncated]"
    return result[: max(0, limit - len(marker))] + marker


def _timeout_is_valid(timeout: object) -> bool:
    return (
        isinstance(timeout, int)
        and not isinstance(timeout, bool)
        and 1 <= timeout <= MAX_TIMEOUT_SECONDS
    )


def _timeout_argument(value: str) -> int:
    try:
        timeout = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timeout must be an integer") from exc
    if not _timeout_is_valid(timeout):
        raise argparse.ArgumentTypeError(
            f"timeout must be between 1 and {MAX_TIMEOUT_SECONDS} seconds"
        )
    return timeout


def _failure(
    probe_id: str,
    name: str,
    details: str,
    root_cause: str,
    remediation_command: str,
    *,
    metadata: dict[str, Any] | None = None,
) -> ProbeResult:
    return ProbeResult(
        probe_id=probe_id,
        name=name,
        passed=False,
        details=_bounded_ascii(details),
        root_cause=_bounded_ascii(root_cause),
        remediation_command=_bounded_ascii(remediation_command),
        metadata=metadata or {},
    )


def _timeout_failure(probe_id: str, name: str, timeout: object) -> ProbeResult:
    return _failure(
        probe_id,
        name,
        f"Timeout boundary is invalid or exhausted: {timeout!r}",
        "The probe cannot prove completion inside a bounded positive timeout.",
        f"rerun with --timeout 1..{MAX_TIMEOUT_SECONDS}",
    )


def _find_descendant_pids(parent_pid: int) -> set[int]:
    """Find all descendant pids of a process using ps."""
    descendants: set[int] = set()
    if os.name != "posix":
        return descendants
    try:
        proc = subprocess.run(
            ["ps", "-axo", "pid,ppid"],
            capture_output=True,
            text=True,
            check=False,
            timeout=1,
        )
        if proc.returncode == 0:
            parent_to_children: dict[int, list[int]] = {}
            for line in proc.stdout.splitlines():
                parts = line.strip().split()
                if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                    pid, ppid = int(parts[0]), int(parts[1])
                    parent_to_children.setdefault(ppid, []).append(pid)

            queue = [parent_pid]
            while queue:
                curr = queue.pop()
                for child in parent_to_children.get(curr, []):
                    if child not in descendants:
                        descendants.add(child)
                        queue.append(child)
    except Exception:
        pass
    return descendants


def _terminate_process_tree(proc: subprocess.Popen[Any]) -> None:
    """Best-effort TERM/KILL of the isolated process and every descendant."""
    if os.name == "posix":
        process_group = proc.pid
        descendants = _find_descendant_pids(process_group)
        all_pids = descendants | {process_group}

        for pid in all_pids:
            try:
                os.killpg(pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
            try:
                os.kill(pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
        try:
            proc.wait(timeout=0.2)
        except subprocess.TimeoutExpired:
            pass

        descendants.update(_find_descendant_pids(process_group))
        for pid in descendants | {process_group}:
            try:
                os.killpg(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        try:
            proc.wait(timeout=0.2)
        except subprocess.TimeoutExpired:
            pass
        return

    proc.terminate()
    try:
        proc.wait(timeout=0.2)
    except subprocess.TimeoutExpired:
        proc.kill()


def _read_subprocess_pipes_bounded(
    proc: subprocess.Popen[Any],
    timeout: float,
    limit: int = MAX_COMMAND_OUTPUT_CHARS,
) -> tuple[int, str, str, bool]:
    """Read stdout and stderr concurrently without calling proc.communicate()."""
    import selectors

    deadline = time.monotonic() + timeout
    stdout_buf = bytearray()
    stderr_buf = bytearray()
    stdout_truncated = False
    stderr_truncated = False

    sel = selectors.DefaultSelector()
    stdout_fd = proc.stdout.fileno() if proc.stdout is not None else None
    stderr_fd = proc.stderr.fileno() if proc.stderr is not None else None

    if stdout_fd is not None:
        os.set_blocking(stdout_fd, False)
        sel.register(stdout_fd, selectors.EVENT_READ, "stdout")
    if stderr_fd is not None:
        os.set_blocking(stderr_fd, False)
        sel.register(stderr_fd, selectors.EVENT_READ, "stderr")

    timed_out = False
    chunk_size = 4096

    while sel.get_map():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            timed_out = True
            break
        events = sel.select(timeout=max(0.01, min(remaining, 0.1)))
        for key, _mask in events:
            stream_name = key.data
            try:
                chunk = os.read(key.fd, chunk_size)
            except (BlockingIOError, InterruptedError):
                continue
            except OSError:
                chunk = b""

            if not chunk:
                sel.unregister(key.fd)
                continue

            if stream_name == "stdout":
                if len(stdout_buf) < limit:
                    stdout_buf.extend(chunk[: limit - len(stdout_buf)])
                if len(stdout_buf) + len(chunk) > limit:
                    stdout_truncated = True
            else:
                if len(stderr_buf) < limit:
                    stderr_buf.extend(chunk[: limit - len(stderr_buf)])
                if len(stderr_buf) + len(chunk) > limit:
                    stderr_truncated = True

        if proc.poll() is not None and not events:
            for key in list(sel.get_map().values()):
                stream_name = key.data
                try:
                    while True:
                        chunk = os.read(key.fd, chunk_size)
                        if not chunk:
                            break
                        if stream_name == "stdout":
                            if len(stdout_buf) < limit:
                                stdout_buf.extend(chunk[: limit - len(stdout_buf)])
                            if len(stdout_buf) + len(chunk) > limit:
                                stdout_truncated = True
                        else:
                            if len(stderr_buf) < limit:
                                stderr_buf.extend(chunk[: limit - len(stderr_buf)])
                            if len(stderr_buf) + len(chunk) > limit:
                                stderr_truncated = True
                except (BlockingIOError, OSError):
                    pass
                sel.unregister(key.fd)
            break

    sel.close()

    if timed_out:
        return 124, "", "", True

    stdout_str = stdout_buf.decode("ascii", errors="backslashreplace")
    stderr_str = stderr_buf.decode("ascii", errors="backslashreplace")

    if stdout_truncated:
        marker = "...[truncated]"
        stdout_str = stdout_str[: max(0, limit - len(marker))] + marker
    if stderr_truncated:
        marker = "...[truncated]"
        stderr_str = stderr_str[: max(0, limit - len(marker))] + marker

    returncode = proc.poll() if proc.poll() is not None else 0
    return returncode, stdout_str, stderr_str, False


def _run_cmd(
    cmd: list[str],
    cwd: Path | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[int, str, str]:
    """Run one isolated subprocess and tear down its process tree on timeout."""
    if os.name != "posix" or not callable(getattr(os, "killpg", None)):
        return (
            125,
            "",
            "Unsupported platform: POSIX process groups and os.killpg are required",
        )
    if not _timeout_is_valid(timeout):
        return (
            124,
            "",
            f"Command timeout must be between 1 and {MAX_TIMEOUT_SECONDS} seconds",
        )
    try:
        # Preserve the original injectable subprocess.run seam used by older
        # black-box tests. Production execution uses Popen so the process-group
        # identifier remains available for descendant cleanup.
        if subprocess.run is not _SUBPROCESS_RUN:
            completed = subprocess.run(
                cmd,
                cwd=cwd or ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="backslashreplace",
                timeout=timeout,
                check=False,
            )
            return (
                completed.returncode,
                _bounded_ascii_capture(completed.stdout.strip()),
                _bounded_ascii_capture(completed.stderr.strip()),
            )

        proc = subprocess.Popen(
            cmd,
            cwd=cwd or ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="backslashreplace",
            start_new_session=True,
        )
        try:
            returncode, stdout, stderr, timed_out = _read_subprocess_pipes_bounded(
                proc,
                timeout=timeout,
                limit=MAX_COMMAND_OUTPUT_CHARS,
            )
            if timed_out:
                _terminate_process_tree(proc)
                command = " ".join(_bounded_ascii(part, 256) for part in cmd)
                return 124, "", f"Command timed out after {timeout}s: {command}"
        except BaseException:
            _terminate_process_tree(proc)
            raise
        # A diagnostic command must not leave a redirected background child
        # behind after its direct process exits.
        _terminate_process_tree(proc)
        return (
            proc.returncode if proc.returncode is not None else returncode,
            _bounded_ascii_capture(stdout.strip()),
            _bounded_ascii_capture(stderr.strip()),
        )
    except subprocess.TimeoutExpired:
        command = " ".join(_bounded_ascii(part, 256) for part in cmd)
        return 124, "", f"Command timed out after {timeout}s: {command}"
    except (OSError, TypeError, UnicodeError, ValueError) as exc:
        return 1, "", _bounded_ascii(exc, MAX_FIELD_CHARS)


def probe_git_truth(
    skip_remote: bool = False,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> ProbeResult:
    """Require a clean worktree and, when requested, usable remote truth."""
    probe_id = "git_truth"
    name = "Git Worktree and Remote Truth"
    if not _timeout_is_valid(timeout):
        return _timeout_failure(probe_id, name, timeout)

    ret, stdout, stderr = _run_cmd(
        ["git", "status", "--porcelain=v1"], cwd=ROOT, timeout=timeout
    )
    if ret != 0:
        return _failure(
            probe_id,
            name,
            f"git status failed with exit {ret}: {stderr or stdout}",
            "Repository worktree state could not be established.",
            "git status --short --branch",
        )

    dirty_entries = sorted(line for line in stdout.splitlines() if line.strip())
    if dirty_entries:
        preview = "; ".join(dirty_entries[:10])
        if len(dirty_entries) > 10:
            preview += "; ...[truncated]"
        return _failure(
            probe_id,
            name,
            f"Dirty worktree contains {len(dirty_entries)} entries: {preview}",
            "Release truth is not reproducible while tracked or untracked changes exist.",
            "git status --short && git diff --check",
            metadata={"dirty_count": len(dirty_entries)},
        )

    if skip_remote:
        return ProbeResult(
            probe_id=probe_id,
            name=name,
            passed=True,
            details="Worktree is clean; remote checks were explicitly skipped.",
            metadata={"dirty_count": 0, "remote_status": "skipped"},
        )

    fetch_ret, _fetch_stdout, fetch_stderr = _run_cmd(
        ["git", "fetch", "origin", "--quiet"], cwd=ROOT, timeout=timeout
    )
    if fetch_ret != 0:
        return _failure(
            probe_id,
            name,
            f"git fetch failed with exit {fetch_ret}: {fetch_stderr}",
            "Remote truth is unavailable because origin could not be refreshed.",
            "git fetch origin --prune && git status --short --branch",
        )

    rev_ret, rev_stdout, rev_stderr = _run_cmd(
        ["git", "rev-list", "--left-right", "--count", "HEAD...origin/main"],
        cwd=ROOT,
        timeout=timeout,
    )
    if rev_ret != 0:
        return _failure(
            probe_id,
            name,
            f"Remote comparison failed with exit {rev_ret}: {rev_stderr}",
            "HEAD could not be compared with refreshed origin/main.",
            "git rev-list --left-right --count HEAD...origin/main",
        )
    parts = rev_stdout.split()
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        return _failure(
            probe_id,
            name,
            "Remote comparison produced a malformed ahead/behind result.",
            "Git remote-state evidence is incomplete.",
            "git rev-list --left-right --count HEAD...origin/main",
        )
    ahead, behind = (int(part) for part in parts)
    if behind:
        return _failure(
            probe_id,
            name,
            f"HEAD is ahead by {ahead} and behind origin/main by {behind} commits.",
            "The candidate does not contain the current production branch history.",
            "git rebase origin/main",
            metadata={"ahead": ahead, "behind": behind},
        )
    return ProbeResult(
        probe_id=probe_id,
        name=name,
        passed=True,
        details=f"Worktree is clean; HEAD is ahead by {ahead} and behind by 0 commits.",
        metadata={"dirty_count": 0, "ahead": ahead, "behind": behind},
    )


def probe_agent_ecosystem(timeout: int = DEFAULT_TIMEOUT_SECONDS) -> ProbeResult:
    """Run the repository's read-only ecosystem synchronization check."""
    probe_id = "agent_ecosystem"
    name = "AI Agent Ecosystem Sync"
    if not _timeout_is_valid(timeout):
        return _timeout_failure(probe_id, name, timeout)
    sync_script = ROOT / "scripts" / "sync_ai_agent_ecosystem.py"
    if not sync_script.is_file():
        return _failure(
            probe_id,
            name,
            "Required synchronization checker is missing.",
            "scripts/sync_ai_agent_ecosystem.py is unavailable.",
            "git restore scripts/sync_ai_agent_ecosystem.py",
        )
    ret, stdout, stderr = _run_cmd(
        [sys.executable, str(sync_script), "--check"], cwd=ROOT, timeout=timeout
    )
    if ret != 0:
        detail = stderr or stdout or "no checker output"
        return _failure(
            probe_id,
            name,
            f"Ecosystem check failed with exit {ret}: {detail}",
            "Generated and authoritative agent ecosystem files are not synchronized.",
            "python3 scripts/sync_ai_agent_ecosystem.py --sync",
        )
    return ProbeResult(
        probe_id=probe_id,
        name=name,
        passed=True,
        details="Agent ecosystem synchronization check passed.",
    )


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    parsed: dict[str, object] = {}
    for key, value in pairs:
        if key in parsed:
            raise ValueError("duplicate JSON key")
        parsed[key] = value
    return parsed


def _reject_nonstandard_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _parse_json_object(raw: str) -> dict[str, Any]:
    """Parse one strict whole-document JSON object with unique keys."""
    value = json.loads(
        raw,
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_nonstandard_json_constant,
    )
    if not isinstance(value, dict):
        raise TypeError("JSON root is not an object")
    return value


def probe_secret_security(timeout: int = DEFAULT_TIMEOUT_SECONDS) -> ProbeResult:
    """Require a present scanner and a strict, successful zero-leak receipt."""
    probe_id = "secret_security"
    name = "Security and Secret Leak Audit"
    if not _timeout_is_valid(timeout):
        return _timeout_failure(probe_id, name, timeout)
    scanner = ROOT / "project" / "core" / "code_reviewer.py"
    if not scanner.is_file():
        return _failure(
            probe_id,
            name,
            "Required secret scanner is missing.",
            "Secret leakage could not be evaluated.",
            "git restore project/core/code_reviewer.py",
        )
    ret, stdout, stderr = _run_cmd(
        [sys.executable, str(scanner), "--scan-secrets"],
        cwd=ROOT,
        timeout=timeout,
    )
    if ret != 0:
        diagnostic = stderr or stdout or "no scanner output"
        return _failure(
            probe_id,
            name,
            f"Secret scanner failed with exit {ret}: {diagnostic}",
            "The scanner reported a failure or could not complete.",
            "python3 project/core/code_reviewer.py --scan-secrets",
        )
    try:
        payload = _parse_json_object(stdout)
    except (json.JSONDecodeError, TypeError, ValueError):
        return _failure(
            probe_id,
            name,
            "Secret scanner returned malformed success output.",
            "A zero exit code was not accompanied by a valid scanner receipt.",
            "python3 project/core/code_reviewer.py --scan-secrets",
        )

    scanned = payload.get("scanned_files")
    leaks = payload.get("secret_leaks_found")
    findings = payload.get("findings")
    status = payload.get("status")
    valid_counts = (
        isinstance(scanned, int)
        and not isinstance(scanned, bool)
        and scanned > 0
        and isinstance(leaks, int)
        and not isinstance(leaks, bool)
        and leaks >= 0
    )
    if not valid_counts or not isinstance(findings, list) or status != "PASSED":
        return _failure(
            probe_id,
            name,
            "Secret scanner returned a malformed or non-passing receipt.",
            "Required status, count, or findings fields are absent or inconsistent.",
            "python3 project/core/code_reviewer.py --scan-secrets",
        )
    if leaks != 0 or findings:
        return _failure(
            probe_id,
            name,
            f"Secret scanner reported {leaks} leaks and {len(findings)} findings.",
            "Potential credentials or sensitive material were detected.",
            "python3 project/core/code_reviewer.py --scan-secrets",
            metadata={"scanned_files": scanned, "secret_leaks_found": leaks},
        )
    return ProbeResult(
        probe_id=probe_id,
        name=name,
        passed=True,
        details=f"Secret scanner passed across {scanned} files with zero findings.",
        metadata={"scanned_files": scanned, "secret_leaks_found": 0},
    )


def _python_candidates(deadline: float) -> tuple[list[Path], bool, str | None]:
    """List governed tracked Python files without traversing the filesystem."""
    excluded = {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "node_modules",
        "target",
        "venv",
    }
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return [], True, None
    ret, stdout, stderr = _run_cmd(
        ["git", "ls-files", "--", "*.py"],
        cwd=ROOT,
        timeout=max(1, math.ceil(remaining)),
    )
    if time.monotonic() >= deadline:
        return [], True, None
    if ret != 0:
        return [], False, stderr or stdout or "git ls-files failed"

    candidates: list[Path] = []
    for raw in stdout.splitlines():
        relative = raw.strip()
        if not relative:
            continue
        relative_path = Path(relative)
        if (
            relative_path.is_absolute()
            or ".." in relative_path.parts
            or any(part in excluded for part in relative_path.parts)
        ):
            return [], False, f"unsafe tracked Python path: {relative}"
        candidates.append(ROOT / relative_path)
    return sorted(candidates, key=lambda path: path.as_posix()), False, None


def _read_python_source(path: Path, deadline: float) -> bytes:
    """Read one tracked file through a root-anchored no-follow descriptor walk."""
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    supports_dir_fd = getattr(os, "supports_dir_fd", set())
    if (
        os.name != "posix"
        or not isinstance(no_follow, int)
        or no_follow == 0
        or not isinstance(directory, int)
        or directory == 0
        or os.open not in supports_dir_fd
    ):
        raise ValueError(
            "root containment cannot be proven without POSIX no-follow dir_fd support"
        )

    root_path = Path(os.path.abspath(os.fspath(ROOT)))
    candidate_path = Path(os.path.abspath(os.fspath(path)))
    try:
        relative_path = candidate_path.relative_to(root_path)
    except ValueError as exc:
        raise ValueError("tracked path is outside root containment") from exc
    components = relative_path.parts
    if not components or any(component in {"", ".", ".."} for component in components):
        raise ValueError("tracked path cannot be proven inside root containment")

    common_flags = os.O_RDONLY | no_follow | getattr(os, "O_CLOEXEC", 0)
    directory_flags = common_flags | directory
    file_flags = common_flags | getattr(os, "O_NONBLOCK", 0)
    directory_descriptors: list[int] = []
    descriptor: int | None = None
    try:
        try:
            root_descriptor = os.open(root_path, directory_flags)
        except OSError as exc:
            raise ValueError(
                f"root containment anchor could not be opened safely: {exc}"
            ) from exc
        directory_descriptors.append(root_descriptor)
        parent_descriptor = root_descriptor

        for component in components[:-1]:
            try:
                next_descriptor = os.open(
                    component,
                    directory_flags,
                    dir_fd=parent_descriptor,
                )
            except OSError as exc:
                raise ValueError(
                    "root containment rejected an intermediate path component: "
                    f"{component}: {exc}"
                ) from exc
            directory_descriptors.append(next_descriptor)
            component_stat = os.fstat(next_descriptor)
            if not stat.S_ISDIR(component_stat.st_mode):
                raise ValueError(
                    "root containment requires every intermediate component "
                    "to be a directory"
                )
            parent_descriptor = next_descriptor

        try:
            descriptor = os.open(
                components[-1],
                file_flags,
                dir_fd=parent_descriptor,
            )
        except OSError as exc:
            raise ValueError(
                "root containment rejected the tracked file component: "
                f"{components[-1]}: {exc}"
            ) from exc
        file_stat = os.fstat(descriptor)
        if not stat.S_ISREG(file_stat.st_mode):
            raise ValueError("tracked path is not a regular file")
        if file_stat.st_size > MAX_PYTHON_FILE_BYTES:
            raise ValueError("file exceeds scan limit")

        source = bytearray()
        while len(source) <= MAX_PYTHON_FILE_BYTES:
            if time.monotonic() >= deadline:
                raise TimeoutError("Python source read exceeded scan deadline")
            read_size = min(65_536, MAX_PYTHON_FILE_BYTES + 1 - len(source))
            chunk = os.read(descriptor, read_size)
            if not chunk:
                break
            source.extend(chunk)
        if len(source) > MAX_PYTHON_FILE_BYTES:
            raise ValueError("file exceeds scan limit")
        return bytes(source)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        for directory_descriptor in reversed(directory_descriptors):
            os.close(directory_descriptor)


def probe_python_syntax(timeout: int = DEFAULT_TIMEOUT_SECONDS) -> ProbeResult:
    """Parse repository Python files under one overall deadline."""
    probe_id = "python_syntax"
    name = "Python AST and Syntax Hygiene"
    if not _timeout_is_valid(timeout):
        return _timeout_failure(probe_id, name, timeout)
    deadline = time.monotonic() + timeout
    candidates, discovery_timed_out, discovery_error = _python_candidates(deadline)
    if discovery_timed_out:
        return _timeout_failure(probe_id, name, timeout)
    if discovery_error:
        return _failure(
            probe_id,
            name,
            f"Tracked Python discovery failed: {discovery_error}",
            "The governed source set could not be established safely.",
            "git ls-files -- '*.py'",
        )

    errors: list[str] = []
    scanned_count = 0
    for path in candidates:
        if time.monotonic() >= deadline:
            return _failure(
                probe_id,
                name,
                f"Python scan timed out after {scanned_count} files.",
                "The AST scan did not complete inside its timeout boundary.",
                f"python3 scripts/fail_fast_triage.py --timeout {timeout}",
                metadata={"scanned_files": scanned_count, "timed_out": True},
            )
        try:
            source = _read_python_source(path, deadline)
            compile(source, str(path), "exec", flags=0, dont_inherit=True)
            scanned_count += 1
        except (
            OSError,
            OverflowError,
            SyntaxError,
            TimeoutError,
            UnicodeError,
            ValueError,
        ) as exc:
            try:
                relative = path.relative_to(ROOT)
            except ValueError:
                relative = path
            errors.append(f"{relative}: {exc}")

    if errors:
        preview = "; ".join(_bounded_ascii(item, 512) for item in errors[:10])
        if len(errors) > 10:
            preview += "; ...[truncated]"
        return _failure(
            probe_id,
            name,
            f"Found {len(errors)} Python syntax/read failures: {preview}",
            "One or more governed tracked Python files could not be compiled safely.",
            "python3 -m compileall -q scripts project tests rust_core TDD-HORO-v3.0",
            metadata={"scanned_files": scanned_count, "error_count": len(errors)},
        )
    return ProbeResult(
        probe_id=probe_id,
        name=name,
        passed=True,
        details=f"Parsed {scanned_count} Python files without syntax errors.",
        metadata={"scanned_files": scanned_count},
    )


def _guard_issue_codes(payload: dict[str, Any]) -> list[str]:
    issues = payload.get("issues")
    if not isinstance(issues, list):
        return ["MALFORMED_GUARD_RECEIPT"]
    codes: list[str] = []
    for issue in issues[:MAX_COLLECTION_ITEMS]:
        if isinstance(issue, dict) and isinstance(issue.get("code"), str):
            codes.append(_bounded_ascii(issue["code"], 128))
        else:
            codes.append("MALFORMED_GUARD_ISSUE")
    return codes


REQUIRED_PROVENANCE_RECEIPT_KEYS = {
    "schema_version",
    "command",
    "status",
    "requested_base",
    "base_commit",
    "requested_head",
    "head_commit",
    "ticket_id",
    "baseline_commit",
    "test_files_verified",
    "issues",
    "notes",
}
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")


def probe_test_provenance(timeout: int = DEFAULT_TIMEOUT_SECONDS) -> ProbeResult:
    """Run one topological PR guard over current committed provenance."""
    probe_id = "test_provenance"
    name = "Test Provenance History"
    if not _timeout_is_valid(timeout):
        return _timeout_failure(probe_id, name, timeout)
    deadline = time.monotonic() + timeout
    manifest_dir = ROOT / "plans" / "test_provenance"
    guard = ROOT / "scripts" / "test_provenance_guard.py"
    if not guard.is_file():
        return _failure(
            probe_id,
            name,
            "Repository provenance guard is missing.",
            "Full Git-history provenance cannot be verified.",
            "git restore scripts/test_provenance_guard.py",
        )
    if not manifest_dir.is_dir():
        return _failure(
            probe_id,
            name,
            "Test provenance directory is missing.",
            "No committed test provenance evidence is available.",
            "mkdir -p plans/test_provenance",
        )
    manifests = sorted(manifest_dir.glob("*.json"), key=lambda path: path.name)
    if not manifests:
        return _failure(
            probe_id,
            name,
            "No test provenance manifests were found.",
            "Test-first history evidence is absent.",
            "python3 scripts/test_provenance_guard.py staged",
        )

    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return _timeout_failure(probe_id, name, timeout)

    resolved_base = "origin/main"
    resolved_head = "HEAD"
    if (ROOT / ".git").exists():
        ret_b, out_b, _ = _run_cmd(
            ["git", "rev-parse", "origin/main"],
            cwd=ROOT,
            timeout=min(timeout, max(1, math.ceil(remaining))),
        )
        if ret_b == 0 and out_b.strip():
            resolved_base = out_b.strip()

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return _timeout_failure(probe_id, name, timeout)

        ret_h, out_h, _ = _run_cmd(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            timeout=min(timeout, max(1, math.ceil(remaining))),
        )
        if ret_h == 0 and out_h.strip():
            resolved_head = out_h.strip()

    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return _timeout_failure(probe_id, name, timeout)

    command = [
        sys.executable,
        str(guard),
        "verify-pr",
        "--repo",
        str(ROOT),
        "--base",
        resolved_base,
        "--head",
        resolved_head,
    ]
    ret, stdout, stderr = _run_cmd(
        command,
        cwd=ROOT,
        timeout=min(timeout, max(1, math.ceil(remaining))),
    )
    if ret == 124:
        return _failure(
            probe_id,
            name,
            "Topological provenance guard timed out.",
            "Current PR provenance could not be bound inside the timeout.",
            "python3 scripts/test_provenance_guard.py verify-pr --help",
            metadata={"timed_out": True, "manifest_count": len(manifests)},
        )
    try:
        payload = _parse_json_object(stdout)
    except (json.JSONDecodeError, TypeError, ValueError):
        diagnostic = stderr or stdout or "no guard output"
        return _failure(
            probe_id,
            name,
            f"Topological provenance guard returned a malformed receipt: {diagnostic}",
            "Current PR provenance receipt did not produce strict machine evidence.",
            "python3 scripts/test_provenance_guard.py verify-pr --help",
        )

    codes = _guard_issue_codes(payload)
    status = payload.get("status")
    if ret != 0 or status != "PASSED" or (isinstance(payload.get("issues"), list) and payload.get("issues")):
        issue_summary = ",".join(codes) if codes else "GUARD_FAILED"
        diagnostic = stderr or issue_summary
        return _failure(
            probe_id,
            name,
            f"Topological PR history guard failed: {issue_summary}; {diagnostic}",
            "The current PR is not valid against committed repository history.",
            "python3 scripts/test_provenance_guard.py verify-pr --base origin/main --head HEAD",
            metadata={
                "manifest_count": len(manifests),
                "test_files_verified": max(
                    0,
                    payload.get("test_files_verified")
                    if isinstance(payload.get("test_files_verified"), int)
                    and not isinstance(payload.get("test_files_verified"), bool)
                    else 0,
                ),
                "notes": [
                    _bounded_ascii(note, 512)
                    for note in payload.get("notes", [])
                    if isinstance(note, str)
                ],
            },
        )

    if set(payload.keys()) != REQUIRED_PROVENANCE_RECEIPT_KEYS:
        return _failure(
            probe_id,
            name,
            "Provenance receipt schema mismatch.",
            "Receipt keys do not match closed test-provenance-report-v2 schema.",
            "python3 scripts/test_provenance_guard.py verify-pr --help",
        )

    if payload.get("schema_version") != "test-provenance-report-v2":
        return _failure(
            probe_id,
            name,
            f"Unsupported provenance receipt schema: {payload.get('schema_version')}",
            "Receipt schema_version must be test-provenance-report-v2.",
            "python3 scripts/test_provenance_guard.py verify-pr --help",
        )

    if payload.get("command") != "verify-pr":
        return _failure(
            probe_id,
            name,
            f"Invalid provenance receipt command: {payload.get('command')}",
            "Receipt command must be verify-pr.",
            "python3 scripts/test_provenance_guard.py verify-pr --help",
        )

    if (
        payload.get("requested_base") != resolved_base
        or payload.get("base_commit") != resolved_base
    ):
        return _failure(
            probe_id,
            name,
            "Provenance receipt base commit mismatch.",
            "Receipt requested_base and base_commit must match resolved base commit.",
            "python3 scripts/test_provenance_guard.py verify-pr --help",
        )

    if (
        payload.get("requested_head") != resolved_head
        or payload.get("head_commit") != resolved_head
    ):
        return _failure(
            probe_id,
            name,
            "Provenance receipt head commit mismatch.",
            "Receipt requested_head and head_commit must match resolved head commit.",
            "python3 scripts/test_provenance_guard.py verify-pr --help",
        )

    ticket_id = payload.get("ticket_id")
    baseline_commit = payload.get("baseline_commit")
    if not isinstance(ticket_id, str) or not ticket_id.strip():
        return _failure(
            probe_id,
            name,
            "Invalid provenance receipt ticket_id.",
            "Receipt ticket_id must be a non-empty string.",
            "python3 scripts/test_provenance_guard.py verify-pr --help",
        )
    if not isinstance(baseline_commit, str) or not GIT_SHA_RE.fullmatch(
        baseline_commit
    ):
        return _failure(
            probe_id,
            name,
            "Invalid provenance receipt baseline_commit.",
            "Receipt baseline_commit must be a full Git SHA.",
            "python3 scripts/test_provenance_guard.py verify-pr --help",
        )

    count = payload.get("test_files_verified")
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        return _failure(
            probe_id,
            name,
            "Invalid provenance receipt test_files_verified count.",
            "Receipt test_files_verified must be a positive integer.",
            "python3 scripts/test_provenance_guard.py verify-pr --help",
        )
    verified_tests = count

    issues = payload.get("issues")
    if not isinstance(issues, list) or not all(
        isinstance(issue, dict) for issue in issues
    ):
        return _failure(
            probe_id,
            name,
            "Invalid provenance receipt issues list.",
            "Receipt issues must be a list of dict objects.",
            "python3 scripts/test_provenance_guard.py verify-pr --help",
        )

    notes_value = payload.get("notes")
    if not isinstance(notes_value, list) or not all(
        isinstance(note, str) for note in notes_value
    ):
        return _failure(
            probe_id,
            name,
            "Invalid provenance receipt notes list.",
            "Receipt notes must be a list of strings.",
            "python3 scripts/test_provenance_guard.py verify-pr --help",
        )
    notes = [_bounded_ascii(note, 512) for note in notes_value[:MAX_COLLECTION_ITEMS]]

    manifest_tickets: list[str] = []
    for mpath in manifests:
        try:
            mjson = _parse_json_object(mpath.read_text(encoding="utf-8"))
            mtick = mjson.get("ticket_id")
            if isinstance(mtick, str):
                manifest_tickets.append(mtick)
        except Exception:
            pass
    if (
        manifest_tickets
        and ticket_id not in manifest_tickets
        and not any(t in ticket_id for t in manifest_tickets)
    ):
        return _failure(
            probe_id,
            name,
            f"Provenance receipt ticket {ticket_id} does not match repository manifests.",
            "Receipt ticket_id is not bound to a valid repository provenance manifest.",
            "python3 scripts/test_provenance_guard.py verify-pr --help",
        )

    note_summary = "; ".join(notes) if notes else "none"
    return ProbeResult(
        probe_id=probe_id,
        name=name,
        passed=True,
        details=(
            f"Topological PR guard verified {verified_tests} test objects in one pass. "
            f"Limitations/notes: {note_summary}"
        ),
        metadata={
            "manifest_count": len(manifests),
            "test_files_verified": verified_tests,
            "base": "origin/main",
            "head": "HEAD",
            "notes": notes,
            "base_commit": payload.get("base_commit"),
            "head_commit": payload.get("head_commit"),
            "baseline_commit": payload.get("baseline_commit"),
            "ticket_id": payload.get("ticket_id"),
        },
    )


def _load_release_identity(path: Path) -> dict[str, str]:
    try:
        if path.stat().st_size > MAX_HTTP_BODY_BYTES:
            raise ValueError("release identity file exceeds size limit")
        payload = _parse_json_object(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ValueError("release identity is unavailable or malformed") from exc
    if set(payload) != set(RELEASE_IDENTITY_FIELDS):
        raise ValueError("release identity does not use the closed schema")
    if not all(
        isinstance(payload.get(field), str) for field in RELEASE_IDENTITY_FIELDS
    ):
        raise ValueError("release identity fields must be strings")
    identity = {field: str(payload[field]) for field in RELEASE_IDENTITY_FIELDS}
    version = identity["version"]
    commit = identity["release_source_commit"]
    revision = identity["release_source_revision"]
    source_path = identity["release_source_metadata_path"]
    digest = identity["release_source_metadata_sha256"]
    version_match = RELEASE_VERSION_RE.fullmatch(version)
    if (
        version_match is None
        or RELEASE_COMMIT_RE.fullmatch(commit) is None
        or version_match.group(1) != commit
        or RELEASE_REVISION_RE.fullmatch(revision) is None
        or not revision.startswith(commit)
        or source_path != "project/static/version.json"
        or RELEASE_DIGEST_RE.fullmatch(digest) is None
    ):
        raise ValueError("release identity fields are inconsistent")
    canonical = json.dumps(
        {
            "release_source_commit": commit,
            "release_source_metadata_path": source_path,
            "release_source_revision": revision,
            "version": version,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if hashlib.sha256(canonical).hexdigest() != digest:
        raise ValueError("release identity digest mismatch")
    return identity


def _remaining_deadline_seconds(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("HTTP probe exceeded its total monotonic deadline")
    return remaining


def _set_response_read_timeout(response: Any, timeout: float) -> None:
    """Best-effort tightening of urllib's connected socket read timeout."""
    candidates = [response]
    for attribute in ("fp", "raw", "_sock", "sock"):
        expanded: list[Any] = []
        for candidate in candidates:
            nested = getattr(candidate, attribute, None)
            if nested is not None:
                expanded.append(nested)
        candidates.extend(expanded)
    for candidate in reversed(candidates):
        setter = getattr(candidate, "settimeout", None)
        if callable(setter):
            try:
                setter(timeout)
            except (OSError, TypeError, ValueError):
                pass
            return


def _read_http_body(response: Any, deadline: float) -> bytes:
    reader = response.read
    body = bytearray()
    sized_reader = True
    while len(body) <= MAX_HTTP_BODY_BYTES:
        remaining = _remaining_deadline_seconds(deadline)
        _set_response_read_timeout(response, remaining)
        read_size = min(
            HTTP_READ_CHUNK_BYTES,
            MAX_HTTP_BODY_BYTES + 1 - len(body),
        )
        try:
            chunk = reader(read_size)
        except TypeError:
            if body:
                raise TypeError("HTTP reader does not support bounded reads") from None
            # Compatibility for deterministic test doubles. urllib HTTPResponse
            # supports sized reads in production; the result remains size-checked.
            chunk = reader()
            sized_reader = False
        _remaining_deadline_seconds(deadline)
        if not isinstance(chunk, bytes):
            raise TypeError("HTTP body is not bytes")
        body.extend(chunk)
        if len(body) > MAX_HTTP_BODY_BYTES:
            raise ValueError("HTTP body exceeds size limit")
        if not chunk or not sized_reader:
            break
    return bytes(body)


def _fetch_json(url: str, deadline: float) -> tuple[int, dict[str, Any]]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "HoroFailFastTriage/1.0"},
    )
    with urllib.request.urlopen(
        request,
        timeout=_remaining_deadline_seconds(deadline),
    ) as response:
        status = response.status
        if not isinstance(status, int):
            raise TypeError("HTTP status is malformed")
        body = _read_http_body(response, deadline)
    _remaining_deadline_seconds(deadline)
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("HTTP body is not UTF-8 JSON") from exc
    return status, _parse_json_object(text)


def _release_revision_error(
    expected: dict[str, str],
    deadline: float,
) -> str | None:
    """Return an error unless the declared source is an ancestor of HEAD."""
    if not (ROOT / ".git").exists():
        return "local Git repository metadata (.git) is missing"
    revision = expected["release_source_revision"]
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return "release revision proof exceeded the total deadline"
    ret, _stdout, stderr = _run_cmd(
        ["git", "cat-file", "-e", f"{revision}^{{commit}}"],
        cwd=ROOT,
        timeout=max(1, math.ceil(remaining)),
    )
    if ret != 0:
        return f"release source revision does not exist: {stderr or 'missing commit'}"

    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return "release revision ancestry proof exceeded the total deadline"
    ret, _stdout, stderr = _run_cmd(
        ["git", "merge-base", "--is-ancestor", revision, "HEAD"],
        cwd=ROOT,
        timeout=max(1, math.ceil(remaining)),
    )
    if ret != 0:
        return (
            "release source revision is not an ancestor of packaging HEAD: "
            f"{stderr or 'ancestry check returned non-zero'}"
        )
    return None


def probe_live_production_endpoints(
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> ProbeResult:
    """Bind Vercel and HF responses to the committed candidate identity."""
    probe_id = "live_endpoints"
    name = "Live Production Release Identity"
    if not _timeout_is_valid(timeout):
        return _timeout_failure(probe_id, name, timeout)
    if not (ROOT / ".git").exists():
        return _failure(
            probe_id,
            name,
            "Git repository metadata (.git) is missing.",
            "Local Git provenance cannot be established without git repository metadata.",
            "git status",
        )
    deadline = time.monotonic() + timeout
    try:
        expected = _load_release_identity(ROOT / "project" / "static" / "version.json")
    except ValueError:
        return _failure(
            probe_id,
            name,
            "Approved local release identity is missing or invalid.",
            "Remote identity cannot be evaluated without a canonical local candidate.",
            "python3 scripts/stamp_version.py --help",
        )
    revision_error = _release_revision_error(expected, deadline)
    if revision_error:
        return _failure(
            probe_id,
            name,
            revision_error,
            "The packaged identity is not bound to reachable committed source history.",
            "git cat-file -e '<revision>^{commit}' && git merge-base --is-ancestor '<revision>' HEAD",
        )

    checks: list[tuple[str, str, str]] = [
        ("Vercel UI", VERCEL_VERSION_URL, "identity"),
        ("HF backend", f"{HF_BACKEND_URL}/version.json", "identity"),
        ("HF backend health", f"{HF_BACKEND_URL}/health", "health"),
    ]
    failures: list[str] = []
    metadata_checks: list[dict[str, Any]] = []
    for label, url, kind in checks:
        try:
            status, payload = _fetch_json(url, deadline)
            if status != 200:
                failures.append(f"{label} returned HTTP {status}")
                metadata_checks.append(
                    {"name": label, "status": status, "verified": False}
                )
                continue
            if kind == "identity":
                try:
                    actual = _load_identity_payload(payload)
                except ValueError:
                    failures.append(f"{label} release identity is malformed")
                    metadata_checks.append(
                        {"name": label, "status": status, "verified": False}
                    )
                    continue
                if actual != expected:
                    failures.append(
                        f"{label} release identity does not match candidate"
                    )
                    metadata_checks.append(
                        {"name": label, "status": status, "verified": False}
                    )
                    continue
            else:
                health_status = payload.get("status")
                version = payload.get("version")
                commit = payload.get("git_commit")
                if not isinstance(health_status, str) or health_status.lower() not in {
                    "ok",
                    "healthy",
                }:
                    failures.append(f"{label} status is not healthy")
                    metadata_checks.append(
                        {"name": label, "status": status, "verified": False}
                    )
                    continue
                if (
                    version != expected["version"]
                    or commit != expected["release_source_commit"]
                ):
                    failures.append(
                        f"{label} version or commit identity does not match candidate"
                    )
                    metadata_checks.append(
                        {"name": label, "status": status, "verified": False}
                    )
                    continue
            metadata_checks.append({"name": label, "status": status, "verified": True})
        except urllib.error.HTTPError as exc:
            failures.append(f"{label} returned HTTP {exc.code}")
            metadata_checks.append(
                {"name": label, "status": exc.code, "verified": False}
            )
        except (
            OSError,
            urllib.error.URLError,
            json.JSONDecodeError,
            TypeError,
            ValueError,
        ) as exc:
            failures.append(f"{label} probe error: {_bounded_ascii(exc, 256)}")
            metadata_checks.append(
                {"name": label, "status": "ERROR", "verified": False}
            )

    if failures:
        return _failure(
            probe_id,
            name,
            "; ".join(failures),
            "HTTP availability did not prove the expected production release identity.",
            "python3 scripts/run_live_health_verification.py",
            metadata={"checks": metadata_checks, "release_identity_verified": False},
        )
    return ProbeResult(
        probe_id=probe_id,
        name=name,
        passed=True,
        details="Vercel and HF version/health responses match the local candidate identity.",
        metadata={"checks": metadata_checks, "release_identity_verified": True},
    )


def _load_identity_payload(payload: dict[str, Any]) -> dict[str, str]:
    if set(payload) != set(RELEASE_IDENTITY_FIELDS):
        raise ValueError("release identity does not use the closed schema")
    if not all(
        isinstance(payload.get(field), str) for field in RELEASE_IDENTITY_FIELDS
    ):
        raise ValueError("release identity fields must be strings")
    identity = {field: str(payload[field]) for field in RELEASE_IDENTITY_FIELDS}
    version_match = RELEASE_VERSION_RE.fullmatch(identity["version"])
    commit = identity["release_source_commit"]
    revision = identity["release_source_revision"]
    if (
        version_match is None
        or RELEASE_COMMIT_RE.fullmatch(commit) is None
        or version_match.group(1) != commit
        or RELEASE_REVISION_RE.fullmatch(revision) is None
        or not revision.startswith(commit)
        or identity["release_source_metadata_path"] != "project/static/version.json"
        or RELEASE_DIGEST_RE.fullmatch(identity["release_source_metadata_sha256"])
        is None
    ):
        raise ValueError("release identity fields are inconsistent")
    canonical = json.dumps(
        {
            "release_source_commit": commit,
            "release_source_metadata_path": identity["release_source_metadata_path"],
            "release_source_revision": revision,
            "version": identity["version"],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if (
        hashlib.sha256(canonical).hexdigest()
        != identity["release_source_metadata_sha256"]
    ):
        raise ValueError("release identity digest mismatch")
    return identity


def run_triage(
    fail_fast: bool = True,
    skip_remote: bool = False,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> TriageReport:
    """Execute probes in stable order and convert unexpected errors to failures."""
    probes: list[tuple[str, str, Callable[[], ProbeResult]]] = [
        (
            "git_truth",
            "Git Worktree and Remote Truth",
            lambda: probe_git_truth(skip_remote=skip_remote, timeout=timeout),
        ),
        (
            "agent_ecosystem",
            "AI Agent Ecosystem Sync",
            lambda: probe_agent_ecosystem(timeout=timeout),
        ),
        (
            "secret_security",
            "Security and Secret Leak Audit",
            lambda: probe_secret_security(timeout=timeout),
        ),
        (
            "python_syntax",
            "Python AST and Syntax Hygiene",
            lambda: probe_python_syntax(timeout=timeout),
        ),
        (
            "test_provenance",
            "Test Provenance History",
            lambda: probe_test_provenance(timeout=timeout),
        ),
    ]
    if not skip_remote:
        probes.append(
            (
                "live_endpoints",
                "Live Production Release Identity",
                lambda: probe_live_production_endpoints(timeout=timeout),
            )
        )

    results: list[ProbeResult] = []
    for probe_id, name, runner in probes:
        try:
            result = runner()
        except Exception as exc:  # noqa: BLE001 - each probe must fail closed
            result = _failure(
                probe_id,
                name,
                f"Probe raised an unexpected error: {_bounded_ascii(exc, 512)}",
                "The diagnostic did not produce a trustworthy result.",
                "python3 scripts/fail_fast_triage.py --check-all --skip-remote",
            )
        results.append(result)
        if fail_fast and not result.passed:
            break

    passed = sum(result.passed for result in results)
    failed = len(results) - passed
    return TriageReport(
        total_probes=len(probes),
        passed_probes=passed,
        failed_probes=failed,
        overall_status="PASSED" if failed == 0 else "FAILED",
        probes=results,
    )


def _sanitize_json(
    value: object,
    state: _SanitizeState,
    *,
    depth: int = 0,
    is_sensitive_key: bool = False,
) -> object:
    if depth > MAX_JSON_DEPTH:
        state.truncated = True
        return "[truncated:depth]"
    if is_sensitive_key and not isinstance(value, (dict, list, tuple, set)):
        return "[REDACTED]"
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        return _bounded_ascii(value, 64)
    if isinstance(value, str):
        sanitized = _bounded_ascii(value, MAX_METADATA_STRING_CHARS)
        if len(_bounded_ascii(value, MAX_COMMAND_OUTPUT_CHARS)) > len(sanitized):
            state.truncated = True
        return sanitized
    if isinstance(value, dict):
        result: dict[str, object] = {}
        entries = sorted(value.items(), key=lambda item: _bounded_ascii(item[0], 256))
        if len(entries) > MAX_COLLECTION_ITEMS:
            state.truncated = True
        for raw_key, item in entries[:MAX_COLLECTION_ITEMS]:
            key = _bounded_ascii(raw_key, 128)
            if key in result:
                state.truncated = True
                continue
            sensitive = bool(_SENSITIVE_KEY_RE.search(str(raw_key)))
            result[key] = _sanitize_json(
                item, state, depth=depth + 1, is_sensitive_key=sensitive
            )
        return result
    if isinstance(value, (list, tuple, set)):
        items = list(value)
        if isinstance(value, set):
            items.sort(key=lambda item: _bounded_ascii(item, 256))
        if len(items) > MAX_COLLECTION_ITEMS:
            state.truncated = True
        return [
            _sanitize_json(
                item, state, depth=depth + 1, is_sensitive_key=is_sensitive_key
            )
            for item in items[:MAX_COLLECTION_ITEMS]
        ]
    return _bounded_ascii(value, MAX_METADATA_STRING_CHARS)


def _report_payload(report: TriageReport) -> dict[str, object]:
    state = _SanitizeState()
    probes: list[dict[str, object]] = []
    if len(report.probes) > MAX_COLLECTION_ITEMS:
        state.truncated = True
    for probe in report.probes[:MAX_COLLECTION_ITEMS]:
        probes.append(
            {
                "probe_id": _bounded_ascii(probe.probe_id, 128),
                "name": _bounded_ascii(probe.name, 256),
                "passed": bool(probe.passed),
                "details": _sanitize_json(probe.details, state),
                "root_cause": _sanitize_json(probe.root_cause, state),
                "remediation_command": _sanitize_json(probe.remediation_command, state),
                "metadata": _sanitize_json(probe.metadata, state),
            }
        )
    payload: dict[str, object] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "total_probes": report.total_probes,
        "passed_probes": report.passed_probes,
        "failed_probes": report.failed_probes,
        "overall_status": _bounded_ascii(report.overall_status, 64),
        "probes": probes,
        "truncated": state.truncated,
    }
    return payload


def _serialize_report(report: TriageReport) -> str:
    payload = _report_payload(report)
    serialized = json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True)
    if len(serialized.encode("ascii")) < MAX_JSON_REPORT_BYTES:
        return serialized

    fallback_probes = []
    for probe in report.probes[:16]:
        fallback_probes.append(
            {
                "probe_id": _bounded_ascii(probe.probe_id, 64),
                "passed": bool(probe.passed),
                "details": _bounded_ascii(probe.details, 256),
                "metadata": {"truncated": True},
            }
        )
    fallback = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "total_probes": report.total_probes,
        "passed_probes": report.passed_probes,
        "failed_probes": report.failed_probes,
        "overall_status": _bounded_ascii(report.overall_status, 64),
        "probes": fallback_probes,
        "truncated": True,
    }
    serialized = json.dumps(
        fallback, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    )
    if len(serialized.encode("ascii")) >= MAX_JSON_REPORT_BYTES:
        raise RuntimeError("bounded JSON fallback exceeded its fixed budget")
    return serialized


def print_ascii_report(report: TriageReport) -> None:
    """Print a bounded human report containing printable ASCII only."""
    lines = [
        "+======================================================================+",
        "| HORO FAIL-FAST ROOT-CAUSE DIAGNOSTIC TRIAGE                         |",
        "+======================================================================+",
        f"[START] Executed {len(report.probes)}/{report.total_probes} probes.",
    ]
    for index, probe in enumerate(report.probes, 1):
        tag = "[OK]" if probe.passed else "[ERROR]"
        lines.append(
            f"[CHECK {index}/{report.total_probes}] "
            f"{_bounded_ascii(probe.name, 256)} -> {tag}"
        )
        lines.append(f"  Details: {_bounded_ascii(probe.details)}")
        if probe.root_cause:
            lines.append(f"  [ROOT-CAUSE] {_bounded_ascii(probe.root_cause)}")
        if probe.remediation_command:
            lines.append(f"  [ACTION] {_bounded_ascii(probe.remediation_command)}")
    lines.append(
        "+----------------------------------------------------------------------+"
    )
    if report.overall_status == "PASSED":
        lines.append(
            f"[SUMMARY] PASSED - {report.passed_probes}/{report.total_probes} probes green."
        )
    else:
        lines.append(
            f"[SUMMARY] FAILED - {report.failed_probes} executed probe(s) failed."
        )
    lines.append(
        "+======================================================================+"
    )
    sys.stdout.write("\n".join(_bounded_ascii(line, 4_096) for line in lines) + "\n")


class _AsciiArgumentParser(argparse.ArgumentParser):
    """Argument parser whose help and failures are bounded printable ASCII."""

    def _print_message(self, message: str | None, file: Any = None) -> None:
        if not message:
            return
        stream = file if file is not None else sys.stderr
        stream.write(_bounded_ascii_capture(message, MAX_ARGPARSE_OUTPUT_CHARS))

    def error(self, message: str) -> None:
        rendered = f"{self.format_usage()}{self.prog}: error: {message}\n"
        self.exit(2, _bounded_ascii_capture(rendered, MAX_ARGPARSE_OUTPUT_CHARS))


def build_parser() -> argparse.ArgumentParser:
    parser = _AsciiArgumentParser(
        description=(
            "Horo fail-fast root-cause diagnostic triage. "
            "POSIX-only execution using os.killpg for process group isolation; "
            "unsupported platforms fail closed before subprocess execution."
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--fail-fast",
        action="store_true",
        help="stop on the first failure (the default)",
    )
    mode.add_argument(
        "--check-all",
        "--all",
        action="store_true",
        help="run every selected probe in stable order",
    )
    parser.add_argument(
        "--skip-remote",
        "--offline",
        action="store_true",
        help="skip git fetch and live deployment probes",
    )
    parser.add_argument("--json", action="store_true", help="emit bounded JSON")
    parser.add_argument(
        "--timeout",
        type=_timeout_argument,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"per-probe timeout in seconds (1..{MAX_TIMEOUT_SECONDS})",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run_triage(
        fail_fast=not args.check_all,
        skip_remote=args.skip_remote,
        timeout=args.timeout,
    )
    if args.json:
        sys.stdout.write(_serialize_report(report) + "\n")
    else:
        print_ascii_report(report)
    return 0 if report.overall_status == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
