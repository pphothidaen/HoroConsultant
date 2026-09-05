#!/usr/bin/env python3
"""Local phase-one specification validator; never a worker execution backend.

One bounded JSON request produces one ASCII JSON decision. VALIDATED describes
only the supplied specification at validation time, not ownership authorization,
sandbox enforcement, authentication isolation, or a measured child lifecycle.
File hashes are read without writes; command/result validation starts no child.
No returned decision can authorize a later execution or shared-workspace edit.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys

MAX_REQUEST = 256 * 1024
MAX_STREAM = 64 * 1024
MAX_FILE = 16 * 1024 * 1024
MAX_EXECUTABLE = 64 * 1024 * 1024
MAX_ITEMS = 128
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROBE_CODE = "print('horo-local-probe')"
OPERATIONS = {"read", "write", "update", "delete"}


class Rejected(ValueError):
    """Carries only a fixed public reason code, never request material."""


def require(condition: bool, reason: str = "INVALID_REQUEST") -> None:
    if not condition:
        raise Rejected(reason)


def exact(value: object, keys: set[str]) -> dict:
    require(type(value) is dict and set(value) == keys)
    return value


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, "DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def invalid_constant(_: str) -> None:
    raise Rejected("NONFINITE_JSON")


def finite_float(raw: str) -> float:
    value = float(raw)
    require(math.isfinite(value), 'NONFINITE_JSON')
    return value


def parse_json(raw: str) -> object:
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=invalid_constant, parse_float=finite_float)


def text(value: object, maximum: int = 4096) -> str:
    require(type(value) is str and 0 < len(value) <= maximum)
    require(not any(ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF for c in value))
    return value


def items(value: object, *, empty: bool = False) -> list:
    require(type(value) is list and (0 if empty else 1) <= len(value) <= MAX_ITEMS)
    return value


def integer(value: object, minimum: int, maximum: int) -> int:
    require(type(value) is int and minimum <= value <= maximum, "INVALID_BOUND")
    return value


def relative_path(value: object) -> str:
    value = text(value)
    require(not value.startswith('/') and '\\' not in value and ':' not in value,
            "UNSAFE_PATH")
    require(all(part not in ('', '.', '..') for part in value.split('/')), "UNSAFE_PATH")
    return value


def absolute_path(value: object) -> Path:
    value = text(value)
    require(value.startswith('/') and '\\' not in value, "UNSAFE_PATH")
    require(all(part not in ('', '.', '..') for part in value.split('/')[1:]), "UNSAFE_PATH")
    return Path(value)


def overlaps(left: Path, right: Path) -> bool:
    return left.is_relative_to(right) or right.is_relative_to(left)


def sensitive_name(path: Path) -> bool:
    """Deny credential/config stores even when omitted from caller exclusions."""
    names = {'.git', '.ssh', '.aws', '.azure', '.config', '.codex', '.claude',
             '.gemini', '.ai-accounts', 'credentials', 'credentials.json',
             'secrets', 'secrets.json', 'token', 'tokens.json', 'id_rsa', 'id_ed25519'}
    return any(part.lower() in names or part.lower().startswith('.env') or
               part.lower().endswith(('.pem', '.key', '.p12', '.pfx')) for part in path.parts)


@contextmanager
def directory_fd(path: Path):
    """Walk absolute directories with no-follow descriptors, closing every fd."""
    require(hasattr(os, 'O_NOFOLLOW') and hasattr(os, 'O_DIRECTORY'),
            "SAFE_FILE_READ_UNAVAILABLE")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open('/', flags)
    try:
        for component in path.parts[1:]:
            following = os.open(component, flags, dir_fd=fd)
            os.close(fd)
            fd = following
        yield fd
    finally:
        os.close(fd)


def identity(info: os.stat_result) -> tuple:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def hash_regular(parent: int, name: str, maximum: int) -> str:
    """Bound reads; reject links/special files and recheck descriptor identity."""
    before = os.stat(name, dir_fd=parent, follow_symlinks=False)
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
            before.st_size <= maximum, "UNSAFE_FILE")
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    try:
        require(identity(before) == identity(os.fstat(fd)), "FILE_CHANGED")
        digest = hashlib.sha256()
        count = 0
        while True:
            chunk = os.read(fd, min(65536, maximum + 1 - count))
            if not chunk:
                break
            count += len(chunk)
            require(count <= maximum, "FILE_TOO_LARGE")
            digest.update(chunk)
        require(count == before.st_size and identity(before) == identity(os.fstat(fd)) and
                identity(before) == identity(os.stat(name, dir_fd=parent, follow_symlinks=False)),
                "FILE_CHANGED")
        return digest.hexdigest()
    finally:
        os.close(fd)


def digest_text(value: object) -> str:
    require(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None,
            "INVALID_DIGEST")
    return value


def validate_files(request: dict) -> None:
    exact(request, {'kind', 'owned_root', 'shared_workspace', 'sensitive_paths',
                    'allowlist', 'operations'})
    root = absolute_path(request['owned_root'])
    shared = absolute_path(request['shared_workspace'])
    # tempfile.gettempdir() probes by creating files; validation must not do that.
    temporary_roots = [Path('/tmp').resolve(), Path('/var/tmp').resolve()]
    if sys.platform == 'darwin':
        # macOS per-user temporary directories remain here with TMPDIR stripped.
        temporary_roots.append(Path('/private/var/folders'))
    require(any(root != temporary and root.is_relative_to(temporary)
                for temporary in temporary_roots), "TEMP_FIXTURE_REQUIRED")
    require(not overlaps(root, PROJECT_ROOT) and not overlaps(root, shared), "SHARED_WORKSPACE_DENIED")
    sensitive = [absolute_path(p) for p in items(request['sensitive_paths'], empty=True)]
    require(not sensitive_name(root), "SENSITIVE_PATH_DENIED")
    allowed = {}
    # Check all declared paths before opening any content, including unused rows.
    for row in items(request['allowlist']):
        exact(row, {'path', 'sha256', 'operations'})
        name = relative_path(row['path'])
        require(name not in allowed, "DUPLICATE_ALLOWED_PATH")
        path = root / name
        require(not sensitive_name(path) and not any(overlaps(path, p) for p in sensitive),
                "SENSITIVE_PATH_DENIED")
        operations = items(row['operations'])
        require(all(type(op) is str and op in OPERATIONS for op in operations))
        require(len(set(operations)) == len(operations))
        if row['sha256'] is None:
            require(operations == ['write'], "MISSING_BASE_HASH")
        else:
            digest_text(row['sha256'])
            require('write' not in operations, "WRITE_REQUIRES_ABSENT_PATH")
        allowed[name] = row
    seen = set()
    for operation in items(request['operations']):
        exact(operation, {'operation', 'path'})
        name = relative_path(operation['path'])
        op = text(operation['operation'], 16)
        require(name in allowed and op in allowed[name]['operations'], "OPERATION_NOT_ALLOWED")
        require(name not in seen, "DUPLICATE_OPERATION_PATH")
        seen.add(name)
    with directory_fd(root):
        pass
    for name, row in allowed.items():
        path = root / name
        with directory_fd(path.parent) as parent:
            if row['sha256'] is None:
                try:
                    os.stat(path.name, dir_fd=parent, follow_symlinks=False)
                except FileNotFoundError:
                    continue
                raise Rejected('WRITE_REQUIRES_ABSENT_PATH')
            require(hash_regular(parent, path.name, MAX_FILE) == row['sha256'], 'STALE_BASE_HASH')


def validate_command(request: dict) -> None:
    exact(request, {'kind', 'argv', 'pinned_argv', 'executable_sha256', 'environment',
                    'deadline_seconds', 'max_stdout_bytes', 'max_stderr_bytes',
                    'descendant_policy', 'shell'})
    # This is a fixed provider-free probe, not a caller-extensible command runner.
    executable = Path(sys.executable).resolve()
    expected = [str(executable), '-c', PROBE_CODE]
    require(request['argv'] == expected and request['pinned_argv'] == expected,
            'COMMAND_NOT_HARMLESS_PINNED_PROBE')
    require(request['shell'] is False, 'SHELL_DENIED')
    env = request['environment']
    require(type(env) is dict and set(env) <= {'LANG', 'LC_ALL'} and
            all(value == 'C' for value in env.values()), 'ENVIRONMENT_DENIED')
    integer(request['deadline_seconds'], 1, 30)
    integer(request['max_stdout_bytes'], 1, MAX_STREAM)
    integer(request['max_stderr_bytes'], 1, MAX_STREAM)
    require(request['descendant_policy'] == 'owned-group-deadline-cleanup',
            'DESCENDANT_POLICY_REQUIRED')
    digest = digest_text(request['executable_sha256'])
    with directory_fd(executable.parent) as parent:
        require(hash_regular(parent, executable.name, MAX_EXECUTABLE) == digest, 'EXECUTABLE_HASH_MISMATCH')


def validate_result(request: dict) -> None:
    exact(request, {'kind', 'session_id', 'exit_code', 'timed_out', 'cancelled',
                    'descendants_remaining', 'allowed_paths', 'sensitive_canaries',
                    'max_output_bytes', 'stream'})
    session = text(request['session_id'], 128)
    require(re.fullmatch('[A-Za-z0-9_-]+', session) is not None, 'INVALID_SESSION')
    require(type(request['exit_code']) is int and request['exit_code'] == 0 and
            request['timed_out'] is False and request['cancelled'] is False and
            type(request['descendants_remaining']) is int and request['descendants_remaining'] == 0,
            'LIFECYCLE_NOT_SUCCESSFUL')
    paths = [relative_path(p) for p in items(request['allowed_paths'], empty=True)]
    require(len(set(paths)) == len(paths), 'DUPLICATE_ALLOWED_PATH')
    canaries = [text(c) for c in items(request['sensitive_canaries'], empty=True)]
    maximum = integer(request['max_output_bytes'], 1, MAX_STREAM)
    stream = request['stream']
    require(type(stream) is str and 0 < len(stream.encode('utf-8')) <= maximum, 'RESULT_SIZE_INVALID')
    result = parse_json(stream)
    exact(result, {'schema_version', 'session_id', 'status', 'changed_paths', 'summary'})
    require(result['schema_version'] == 'local-work-result-v1' and
            result['session_id'] == session and result['status'] == 'DONE', 'INVALID_WORK_RESULT')
    changed = [relative_path(p) for p in items(result['changed_paths'], empty=True)]
    require(len(set(changed)) == len(changed) and set(changed) <= set(paths), 'RESULT_PATH_DENIED')
    text(result['summary'], MAX_STREAM)
    # Scan decoded JSON too, so Unicode escapes cannot hide a supplied canary.
    decoded = json.dumps(result, ensure_ascii=False)
    require(not any(c in stream or c in decoded for c in canaries), 'SENSITIVE_RESULT_DENIED')


def decision(request: object) -> dict:
    require(type(request) is dict, 'REQUEST_NOT_OBJECT')
    kind = request.get('kind')
    if kind == 'run':
        raise Rejected('SANDBOX_NOT_PROVEN')
    if kind == 'files':
        validate_files(request)
    elif kind == 'command':
        validate_command(request)
    elif kind == 'result':
        validate_result(request)
    elif kind == 'describe_probe':
        exact(request, {'kind'})
        return {'provider_free': True, 'required_controls': [
            'owned_path_enforcement', 'sensitive_canary_read_denial',
            'descendant_deadline_cleanup', 'bounded_streams']}
    else:
        raise Rejected('UNKNOWN_REQUEST_KIND')
    return {}


def main() -> int:
    response = {'decision': 'REJECTED', 'native_proof': False,
                'os_capability': 'UNKNOWN', 'auth_isolation': 'NOT_PROVEN',
                'child_started': False}
    try:
        require(sys.argv[1:] == ['--request-json'], 'REQUEST_JSON_REQUIRED')
        raw = sys.stdin.buffer.read(MAX_REQUEST + 1)
        require(0 < len(raw) <= MAX_REQUEST, 'REQUEST_SIZE_INVALID')
        response.update(decision(parse_json(raw.decode('utf-8'))))
        response['decision'] = 'VALIDATED'
        code = 0
    except Rejected as exc:
        response['reason_code'] = str(exc)
        code = 1
    except (OSError, ValueError, TypeError, KeyError, RecursionError, OverflowError):
        # Do not print exceptions: decoder/filesystem errors can contain secrets.
        response['reason_code'] = 'INVALID_OR_UNSAFE_REQUEST'
        code = 1
    sys.stdout.write(json.dumps(response, ensure_ascii=True, separators=(',', ':')) + '\n')
    return code


if __name__ == '__main__':
    raise SystemExit(main())
