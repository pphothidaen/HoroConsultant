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
import selectors
import signal
import stat
import subprocess
import sys
import time
import uuid

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


BACKEND_CONTROLS = {
    'filesystem': ['owned_read', 'owned_create_update_delete', 'outside_read_denied',
                   'outside_write_delete_denied'],
    'deadline': ['deadline_triggered', 'owned_descendants_reaped'],
    'streams': ['output_limit_triggered', 'owned_descendants_reaped'],
}

# Only these source-bound programs can run. All caller values are data in argv.
# Outside destructive probes use a supervisor-created denied canary, never a
# caller input. It is outside the allowed write subtree, inside our own scratch.
FILESYSTEM_PROGRAM = r'''
my ($w, $denied, $outside, @inputs) = @ARGV;
for my $input (@inputs) {
    open(my $f, '<', $input) or exit 10;
    my $buffer; read($f, $buffer, 1); close($f);
}
my $p = "$w/created";
open(my $f, '>', $p) or exit 11; print $f "one"; close($f);
open($f, '>>', $p) or exit 12; print $f "two"; close($f);
open($f, '<', $p) or exit 13; my $s = <$f>; close($f);
exit 14 unless $s eq "onetwo";
unlink($p) == 1 or exit 15;
for my $p ($outside, $denied) {
    if (open(my $f, '<', $p)) { close($f); exit 16; }
}
if (open(my $f, '+<', $denied)) { close($f); exit 17; }
exit 18 if unlink($denied);
print "FILESYSTEM_OK\n";
'''

LIFECYCLE_PROGRAM = r'''
$| = 1;
my $child = fork(); defined($child) or exit 20;
if ($child == 0) { while (1) { sleep 60; } }
$SIG{TERM} = sub { kill 9, $child; waitpid($child, 0); exit 0; };
print "CHILD $child\n";
if ($ARGV[0] eq 'streams') { while (1) { print 'X' x 4096; print STDERR 'Y' x 4096; } }
while (1) { sleep 60; }
'''


def path_hash(path: Path, maximum: int = MAX_EXECUTABLE) -> str:
    with directory_fd(path.parent) as parent:
        return hash_regular(parent, path.name, maximum)


def backend_spec(request: object) -> tuple[Path, Path]:
    exact(request, {'operation', 'probe_id', 'session_id', 'owned_root', 'owned_manifest',
                    'outside_canary', 'outside_canary_sha256', 'environment', 'limits'})
    require(request['operation'] in ('plan', 'probe'))
    require(type(request['probe_id']) is str and request['probe_id'] in BACKEND_CONTROLS)
    require(re.fullmatch('[A-Za-z0-9_-]{1,128}', text(request['session_id'], 128)) is not None)
    require(request['environment'] == {'LANG': 'C', 'LC_ALL': 'C'}, 'ENVIRONMENT_DENIED')
    limits = exact(request['limits'], {'deadline_seconds', 'stdout_bytes', 'stderr_bytes'})
    integer(limits['deadline_seconds'], 1, 3)
    integer(limits['stdout_bytes'], 1, MAX_STREAM)
    integer(limits['stderr_bytes'], 1, MAX_STREAM)
    manifest = request['owned_manifest']
    require(type(manifest) is dict and 1 <= len(manifest) <= 16)
    require(all(len(text(p, 256)) <= 256 for p in manifest))
    root = absolute_path(request['owned_root'])
    require(len(str(root)) <= 1024)
    outside = absolute_path(request['outside_canary'])
    require(outside.parent == root.parent and not sensitive_name(outside), 'CANARY_SCOPE_DENIED')
    validate_files({'kind': 'files', 'owned_root': str(root), 'shared_workspace': str(PROJECT_ROOT),
                    'sensitive_paths': [str(outside)],
                    'allowlist': [{'path': p, 'sha256': digest_text(h), 'operations': ['read']}
                                  for p, h in manifest.items()],
                    'operations': [{'operation': 'read', 'path': p} for p in manifest]})
    require(path_hash(outside, MAX_FILE) == digest_text(request['outside_canary_sha256']),
            'CANARY_HASH_MISMATCH')
    return root, outside


def backend_plan(request: dict, root: Path, scratch: Path) -> dict:
    helper, program = Path('/usr/bin/sandbox-exec'), Path('/usr/bin/perl')
    require(sys.platform == 'darwin' and helper.is_file() and program.is_file(),
            'OS_BACKEND_UNAVAILABLE')
    # Exact root-directory access is needed by libignition's openat bootstrap.
    # No user/home, /private/var, or broad /System read exception is present.
    runtime_trees = ['/usr/lib', '/System/Library', '/System/Cryptexes/OS',
                     '/System/Volumes/Preboot/Cryptexes/OS']
    runtime_files = ['/', str(program), '/dev/null']
    quote = lambda p: json.dumps(str(p), ensure_ascii=False)
    runtime = ' '.join('(subpath ' + quote(p) + ')' for p in runtime_trees)
    runtime += ' ' + ' '.join('(literal ' + quote(p) + ')' for p in runtime_files)
    inputs = ' '.join('(literal ' + quote(root / p) + ')' for p in sorted(request['owned_manifest']))
    profile = ('(version 1)\n(deny default)\n(deny network*)\n'
               '(allow process-fork)\n(allow process-exec (literal ' + quote(program) + '))\n'
               '(allow signal (target children))\n(allow sysctl-read)\n'
               '(allow file-read* file-map-executable ' + runtime + ')\n'
               '(allow file-read* ' + inputs + ')\n'
               '(allow file-read* file-write* (subpath ' + quote(scratch / 'writable') + '))\n')
    code = FILESYSTEM_PROGRAM if request['probe_id'] == 'filesystem' else LIFECYCLE_PROGRAM
    binding = {'source_sha256': path_hash(Path(__file__).resolve()),
               'session_id': request['session_id'], 'owned_manifest': request['owned_manifest'],
               'owned_root': str(root), 'outside_canary_sha256': request['outside_canary_sha256'],
               'helper': {'path': str(helper), 'sha256': path_hash(helper)},
               'program': {'path': str(program), 'sha256': path_hash(program)},
               'fixed_program_sha256': hashlib.sha256(code.encode()).hexdigest(),
               'profile': profile, 'profile_sha256': hashlib.sha256(profile.encode()).hexdigest()}
    return {'binding': binding, 'policy': {'filesystem_default': 'deny', 'network': 'deny',
            'runtime_read_allowlist': runtime_trees + runtime_files,
            'runtime_directory_reads': ['/'], 'writable_subtree': str(scratch / 'writable')},
            'environment': request['environment']}


def collect_probe(argv: list[str], environment: dict, limits: dict, response: dict) -> dict:
    """Drain both pipes continuously; signal only our fixed owned process group.

    The fixed leader reaps its one non-detaching descendant on TERM. Failure to
    observe group disappearance is unsupported, never an invented cleanup PASS.
    Raw output is retained only up to the declared caps and never returned.
    """
    with subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, cwd='/', env=environment,
                          close_fds=True, start_new_session=True) as child:
        response['child_started'] = True
        outputs = {'stdout': bytearray(), 'stderr': bytearray()}
        started = time.monotonic()
        stop_at = None
        trigger = None
        killed = False
        with selectors.DefaultSelector() as selector:
            for name, pipe in (('stdout', child.stdout), ('stderr', child.stderr)):
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, name)
            try:
                while selector.get_map() or child.poll() is None:
                    now = time.monotonic()
                    if trigger is None and now - started >= limits['deadline_seconds']:
                        trigger, stop_at = 'deadline', now
                        if child.poll() is None:
                            child.send_signal(signal.SIGTERM)
                    if stop_at is not None and now - stop_at > 0.5 and not killed:
                        try:
                            os.killpg(child.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        killed = True
                    if now - started > limits['deadline_seconds'] + 1.5:
                        break
                    for key, _ in selector.select(0.02):
                        chunk = os.read(key.fileobj.fileno(), 4096)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        name = key.data
                        remaining = limits[name + '_bytes'] - len(outputs[name])
                        outputs[name].extend(chunk[:remaining])
                        if len(chunk) > remaining and trigger is None:
                            trigger, stop_at = 'streams', time.monotonic()
                            if child.poll() is None:
                                child.send_signal(signal.SIGTERM)
            finally:
                if child.poll() is None:
                    try:
                        os.killpg(child.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                child.wait(timeout=1)
        remaining = 1
        try:
            os.killpg(child.pid, 0)
        except ProcessLookupError:
            remaining = 0
        return {'exit_code': child.returncode, 'trigger': trigger,
                'stdout': bytes(outputs['stdout']), 'stderr': bytes(outputs['stderr']),
                'owned_processes_remaining': remaining}


def backend(request: object, response: dict) -> int:
    response.update(schema_version='local-os-backend-v1', status='REJECTED',
                    capability='UNPROVEN', verified_controls=[])
    root, outside = backend_spec(request)
    name = '.horo-probe-' + uuid.uuid4().hex
    scratch = root / name
    try:
        plan = backend_plan(request, root, scratch)
    except Rejected as exc:
        if str(exc) != 'OS_BACKEND_UNAVAILABLE':
            raise
        response.update(status='UNSUPPORTED', reason_code='OS_BACKEND_UNAVAILABLE')
        return 1
    response.update(plan)
    if request['operation'] == 'plan':
        response['status'] = 'PLANNED'
        return 0
    code = FILESYSTEM_PROGRAM if request['probe_id'] == 'filesystem' else LIFECYCLE_PROGRAM
    # Anchor creation/removal to open no-follow descriptors. Never recursively
    # remove caller paths or accept caller-selected scratch/helper/program bytes.
    with directory_fd(root) as parent:
        original_root = identity(os.fstat(parent))
        backend_spec(request)
        require(identity(root.stat(follow_symlinks=False)) == original_root, 'ROOT_CHANGED')
        os.mkdir(name, mode=0o700, dir_fd=parent)
        try:
            with directory_fd(scratch) as owned:
                os.mkdir('writable', mode=0o700, dir_fd=owned)
                fd = os.open('denied', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=owned)
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(b'LOCAL_SYNTHETIC_DENIED_CANARY\n')
                argv = [plan['binding']['helper']['path'], '-p', plan['binding']['profile'],
                        plan['binding']['program']['path'], '-e', code, '--']
                if request['probe_id'] == 'filesystem':
                    argv += [str(scratch / 'writable'), str(scratch / 'denied'), str(outside)]
                    argv += [str(root / p) for p in sorted(request['owned_manifest'])]
                else:
                    argv += [request['probe_id']]
                # Recheck all bindings immediately before the one fixed launch.
                backend_spec(request)
                require(backend_plan(request, root, scratch) == plan, 'BINDING_CHANGED')
                observed = collect_probe(argv, request['environment'], request['limits'], response)
                backend_spec(request)
                require(hash_regular(owned, 'denied', MAX_FILE) ==
                        hashlib.sha256(b'LOCAL_SYNTHETIC_DENIED_CANARY\n').hexdigest(), 'CANARY_CHANGED')
        finally:
            with directory_fd(scratch / 'writable') as writable:
                # The one fixed filesystem program creates only this filename.
                try:
                    os.unlink('created', dir_fd=writable)
                except FileNotFoundError:
                    pass
            with directory_fd(scratch) as owned:
                os.unlink('denied', dir_fd=owned)
                os.rmdir('writable', dir_fd=owned)
            os.rmdir(name, dir_fd=parent)
    group_gone = observed['owned_processes_remaining'] == 0
    if request['probe_id'] == 'filesystem':
        success = observed['exit_code'] == 0 and observed['trigger'] is None and \
                  observed['stdout'] == b'FILESYSTEM_OK\n' and not observed['stderr'] and group_gone
    else:
        success = observed['trigger'] == request['probe_id'] and group_gone and \
                  observed['exit_code'] == 0 and re.match(rb'CHILD [0-9]+\n', observed['stdout']) is not None
    response['observation'] = {'execution_kind': 'real-os', 'stdout_bytes': len(observed['stdout']),
                               'stderr_bytes': len(observed['stderr']),
                               'exit_code': observed['exit_code'], 'trigger': observed['trigger'],
                               'owned_processes_remaining': observed['owned_processes_remaining'],
                               'scratch_removed': True}
    if not success:
        response.update(status='UNSUPPORTED', reason_code='CONTROL_NOT_PROVEN')
        return 1
    response.update(status='OBSERVED', capability='SCOPED_CONTROLS_OBSERVED',
                    verified_controls=BACKEND_CONTROLS[request['probe_id']])
    return 0


def main() -> int:
    response = {'decision': 'REJECTED', 'native_proof': False,
                'os_capability': 'UNKNOWN', 'auth_isolation': 'NOT_PROVEN',
                'child_started': False}
    try:
        backend_mode = sys.argv[1:] == ['--backend-json']
        if backend_mode:
            response.pop('decision')
            response.update(schema_version='local-os-backend-v1', status='REJECTED',
                            capability='UNPROVEN', verified_controls=[])
        require(backend_mode or sys.argv[1:] == ['--request-json'], 'REQUEST_JSON_REQUIRED')
        raw = sys.stdin.buffer.read(MAX_REQUEST + 1)
        require(0 < len(raw) <= MAX_REQUEST, 'REQUEST_SIZE_INVALID')
        request = parse_json(raw.decode('utf-8'))
        if backend_mode:
            code = backend(request, response)
        else:
            response.update(decision(request))
            response['decision'] = 'VALIDATED'
            code = 0
    except Rejected as exc:
        response['reason_code'] = str(exc)
        if response.get('child_started') and response.get('schema_version') == 'local-os-backend-v1':
            response.update(status='UNSUPPORTED', reason_code='CONTROL_NOT_PROVEN')
        code = 1
    except (OSError, ValueError, TypeError, KeyError, RecursionError, OverflowError,
            subprocess.SubprocessError):
        # Do not print exceptions: decoder/filesystem errors can contain secrets.
        response['reason_code'] = 'INVALID_OR_UNSAFE_REQUEST'
        if response.get('binding'):
            response.update(status='UNSUPPORTED', reason_code='CONTROL_NOT_PROVEN')
        code = 1
    encoded = json.dumps(response, ensure_ascii=True, separators=(',', ':')) + '\n'
    if len(encoded) > MAX_STREAM:
        response = {'schema_version': 'local-os-backend-v1', 'status': 'REJECTED',
                    'reason_code': 'RESPONSE_SIZE_INVALID', 'native_proof': False,
                    'auth_isolation': 'NOT_PROVEN', 'capability': 'UNPROVEN',
                    'verified_controls': [], 'child_started': response['child_started']}
        encoded = json.dumps(response, separators=(',', ':')) + '\n'
        code = 1
    sys.stdout.write(encoded)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
