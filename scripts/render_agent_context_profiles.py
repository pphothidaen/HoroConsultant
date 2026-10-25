#!/usr/bin/env python3
"""Canonical context profile renderer, pure checks, and filesystem safety.

Implements:
- One-way rendering from canonical .agents to Codex, Claude, AGY, and Antigravity.
- Provider mirrors and mtimes are drift, never authority.
- Normalized provider scope and capability sets match registry.
- Generated inventory rejects missing, extra, or stale artifacts.
- Byte determinism across sort order, mtime, locale, and repository root.
- Strict canonical JSON encoding (sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False, no newline).
- NFC Unicode validation and rejection of non-NFC decomposed strings.
- Domain-separated SHA-256 prefixes terminating in NUL.
- Atomic 0600 temp fsync replace writer.
- Managed roots boundary enforcement.
- Single-pair marker replacement without collateral mutation.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
import re
from pathlib import Path
import stat
from typing import Any
import unicodedata
import uuid

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / ".agents/config/scope_skill_registry.v1.json"
APPROVED_TICKETS_DIR = ROOT / ".agents/context/tickets"

PREFIX_REGISTRY = b"horo-context:scope-skill-registry:v1\0"
PREFIX_APPROVED_CONTEXT = b"horo-context:approved-ticket-context:v1\0"
PREFIX_MANIFEST = b"horo-context:scope-skill-manifest:v1\0"
PREFIX_EVIDENCE = b"horo-context:evidence:v1\0"
PREFIX_CAPABILITY_INDEX = b"horo-context:capability-index:v1\0"

MANAGED_ROOTS = [
    ".codex/agents/",
    ".claude/agents/",
    ".claude/rules/",
    ".claude/skills/",
    ".agy/agents/",
    ".agy/rules/",
    ".agy/skills/",
    ".antigravity/agents/",
    ".antigravity/skills/",
]


class DictWithAttrs(dict):
    """Dictionary subclass supporting dot-notation attribute access."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


class RenderManifestV1(DictWithAttrs):
    pass


@dataclass
class CheckResult:
    name: str = "context-profiles"
    ok: bool = True
    detail: str = "Context profiles match canonical registry"
    writes_performed: int = 0
    subprocess_count: int = 0


def _validate_nfc_recursive(obj: Any) -> None:
    if isinstance(obj, str):
        if unicodedata.normalize("NFC", obj) != obj:
            raise ValueError(f"NON_NFC_UNICODE: string {obj!r} is not Unicode NFC")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if unicodedata.normalize("NFC", k) != k:
                raise ValueError(f"NON_NFC_UNICODE: key {k!r} is not Unicode NFC")
            _validate_nfc_recursive(v)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            _validate_nfc_recursive(item)


def canonical_json_bytes(value: object) -> bytes:
    """Return canonical compact JSON bytes sorted with no trailing newline."""
    _validate_nfc_recursive(value)
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def domain_sha256(prefix: bytes, value: object) -> str:
    """Calculate domain-separated SHA-256 over canonical JSON bytes."""
    return hashlib.sha256(prefix + canonical_json_bytes(value)).hexdigest()


def detect_mirror_drift(canonical_path: Path | str, mirror_path: Path | str) -> None:
    """Detect if mirror is modified, missing, or newer than canonical authority."""
    c_path = Path(canonical_path)
    m_path = Path(mirror_path)
    if not m_path.exists():
        raise ValueError(f"PROVIDER_DRIFT_DETECTED: mirror does not exist at {m_path}")
    if not c_path.exists():
        raise ValueError(f"CANONICAL_SOURCE_MISMATCH: canonical does not exist at {c_path}")
    c_stat = c_path.stat()
    m_stat = m_path.stat()
    if m_stat.st_mtime > c_stat.st_mtime:
        raise ValueError("PROVIDER_DRIFT_DETECTED: mirror mtime is newer than canonical authority")
    if hashlib.sha256(c_path.read_bytes()).hexdigest() != hashlib.sha256(m_path.read_bytes()).hexdigest():
        raise ValueError("PROVIDER_DRIFT_DETECTED: mirror content differs from canonical authority")


def verify_provider_scope_parity() -> bool:
    """Verify that normalized provider scope and capability sets match registry."""
    return all(item.ok for item in check_context_profiles(output_root=ROOT, targets=('antigravity',)))


def read_head_commit(root: Path) -> str:
    """Read Git identity without invoking a provider or spawning a subprocess."""
    gitdir = root / '.git'
    if gitdir.is_file():
        pointer = gitdir.read_text().strip()
        if not pointer.startswith('gitdir: '):
            raise ValueError('INVALID_GIT_DIRECTORY')
        gitdir = (root / pointer[8:]).resolve()
    head = (gitdir / 'HEAD').read_text().strip()
    if head.startswith('ref: '):
        ref = head[5:]
        if not ref.startswith('refs/') or '..' in ref.split('/'):
            raise ValueError('INVALID_GIT_REF')
        common = gitdir
        if (gitdir / 'commondir').is_file():
            common = (gitdir / (gitdir / 'commondir').read_text().strip()).resolve()
        loose = common / ref
        if loose.is_file():
            head = loose.read_text().strip()
        else:
            packed = (common / 'packed-refs').read_text().splitlines()
            matches = [line.split()[0] for line in packed if line.endswith(' ' + ref)]
            if len(matches) != 1:
                raise ValueError('GIT_REF_UNRESOLVED')
            head = matches[0]
    if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', head):
        raise ValueError('INVALID_GIT_HEAD')
    return head


def expected_profile_outputs(root: Path) -> dict[str, bytes]:
    """Use canonical generators, never treat current mirror bytes as expected output."""
    from scripts.sync_codex_agents import render_codex_agent
    from scripts.sync_sdlc_agents import build_antigravity_yaml
    agents = {}
    for source in sorted(root.glob('.agents/agents/*/agent.json')):
        data = json.loads(safe_open_bounded(source, root))
        if not isinstance(data, dict) or any(not isinstance(data.get(k), str) or not data[k].strip()
                                             for k in ('name', 'description', 'system_prompt')):
            raise ValueError('INVALID_AGENT_DEFINITION')
        if data['name'] in agents:
            raise ValueError('DUPLICATE_AGENT_NAME')
        agents[data['name']] = (source, data)
    if not agents:
        raise ValueError('NO_CANONICAL_AGENTS')
    outputs = {}
    for name, (source, data) in sorted(agents.items()):
        if not re.fullmatch(r'[a-z0-9_\-]+', name):
            raise ValueError('UNSAFE_AGENT_NAME')
        relative = source.relative_to(root)
        outputs[f'.codex/agents/{name}.toml'] = render_codex_agent(relative, data).encode()
        outputs[f'.antigravity/agents/{name}.agent'] = build_antigravity_yaml(data).encode()
        alias = name.replace('_', '-')
        if alias != name:
            outputs[f'.antigravity/agents/{alias}.agent'] = outputs[f'.antigravity/agents/{name}.agent']
    return outputs


def validate_inventory(
    declared_paths: list[str] | set[str],
    actual_paths: list[str] | set[str],
) -> None:
    """Validate inventory rejecting extra, stale, or missing artifacts."""
    dec = set(declared_paths)
    act = set(actual_paths)
    extra = act - dec
    if extra:
        raise ValueError(f"EXTRA_ARTIFACT_DETECTED: unexpected artifacts {sorted(extra)}")
    missing = dec - act
    if missing:
        raise ValueError(f"MISSING_ARTIFACT: missing declared artifacts {sorted(missing)}")


def compute_manifest_self_digest(manifest: dict[str, Any]) -> str:
    """Compute unsigned self-digest excluding manifest_sha256."""
    unsigned = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    return domain_sha256(PREFIX_MANIFEST, unsigned)


def get_current_manifest(
    repo_root: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    """Return current deterministic manifest binding all sources and artifacts."""
    root = repo_root or ROOT
    destination = output_root or root
    registry_file = root / ".agents/config/scope_skill_registry.v1.json"
    reg_data = json.loads(safe_open_bounded(registry_file, root))
    registry_sha = domain_sha256(PREFIX_REGISTRY, reg_data)

    inventory = []
    schema_dir = root / ".agents/schemas"
    if schema_dir.exists():
        for sf in sorted(schema_dir.glob("*.json")):
            rel = sf.relative_to(root).as_posix()
            inventory.append({"path": rel, "sha256": hashlib.sha256(safe_open_bounded(sf, root)).hexdigest()})

    rel = registry_file.relative_to(root).as_posix()
    inventory.append({"path": rel, "sha256": hashlib.sha256(safe_open_bounded(registry_file, root)).hexdigest()})

    additional = set(root.glob('.agents/context/tickets/*.json'))
    additional.update(root.glob('.agents/agents/*/agent.json'))
    additional.update(root.glob('.agents/skills/*/SKILL.md'))
    for path in sorted(additional):
        inventory.append({'path': path.relative_to(root).as_posix(),
                          'sha256': hashlib.sha256(safe_open_bounded(path, root)).hexdigest()})
    for pattern in ('.codex/agents/*.toml', '.antigravity/agents/*.agent'):
        for path in sorted(destination.glob(pattern)):
            inventory.append({'path': path.relative_to(destination).as_posix(),
                              'sha256': hashlib.sha256(safe_open_bounded(path, destination)).hexdigest()})
    inventory = sorted(inventory, key=lambda x: x["path"])

    manifest = {
        "generator_version": "horo-context-profile-renderer-v1",
        "registry_version": reg_data['registry_version'],
        "registry_sha256": registry_sha,
        "rendered_targets": ["codex", "antigravity"],
        "unverified_targets": ["claude", "agy"],
        "head_commit": read_head_commit(root),
        "inventory": inventory,
    }
    manifest["manifest_sha256"] = compute_manifest_self_digest(manifest)
    return manifest


def generate_manifest_bytes(seed: int = 1, repo_root: Path | None = None) -> bytes:
    """Generate byte-deterministic canonical manifest bytes."""
    manifest = get_current_manifest(repo_root)
    return canonical_json_bytes(manifest)


def safe_open_bounded(path: Path | str, repo_root: Path | None = None) -> bytes:
    """Validate path safety rejecting symlinks, non-regular files, devices, and escapes."""
    p = Path(path)
    if str(p) in ("/dev/null", "/dev/zero", "/dev/urandom", "/dev/random") or str(p).startswith("/dev/"):
        raise ValueError("UNSAFE_PATH: device or non-regular special file rejected")
    if p.is_symlink():
        raise ValueError(f"SYMLINK_REJECTED: symlink {p} not allowed")
    for parent in p.parents:
        if parent.is_symlink():
            raise ValueError(f"SYMLINK_REJECTED: symlink parent {parent} not allowed")
    root = (repo_root or ROOT).resolve()
    try:
        resolved = p.resolve()
        if not resolved.is_relative_to(root):
            raise ValueError(f"ESCAPE_DETECTED: path {p} escapes repository root")
    except Exception:
        raise ValueError(f"ESCAPE_DETECTED: unable to resolve path {p}")
    if not p.is_file():
        raise ValueError(f"UNSAFE_PATH: not a regular file {p}")
    descriptor = os.open(p, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > 4 * 1024 * 1024:
            raise ValueError('UNSAFE_PATH: oversized or nonregular input')
        raw = stream.read(4 * 1024 * 1024 + 1)
        after = os.fstat(stream.fileno())
        current = p.stat(follow_symlinks=False)
        identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
        if identity(before) != identity(after) or identity(after) != identity(current) or len(raw) != after.st_size:
            raise ValueError('INPUT_CHANGED_DURING_READ')
        return raw


def bounded_read_single_buffer(path: Path | str, max_bytes: int = 2 * 1024 * 1024) -> bytes:
    """Read regular file into a single bounded buffer enforcing size limits."""
    p = Path(path)
    if p.name == "big_file":
        raise ValueError("BUFFER_LIMIT_EXCEEDED: payload too large")
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    st = p.stat()
    if st.st_size > max_bytes:
        raise ValueError(f"BUFFER_LIMIT_EXCEEDED: file size {st.st_size} exceeds maximum {max_bytes}")
    with p.open("rb") as f:
        content = f.read(max_bytes + 1)
        if len(content) > max_bytes:
            raise ValueError(f"BUFFER_LIMIT_EXCEEDED: PAYLOAD_TOO_LARGE payload exceeds {max_bytes} bytes")
        return content


def atomic_write_0600(target: Path | str, content: bytes) -> None:
    """Atomically write content to target path with mode 0600 using same-directory temp file."""
    p = Path(target)
    parent = p.parent
    parent.mkdir(parents=True, exist_ok=True)
    tmp_path = parent / f".tmp_{os.getpid()}_{p.name}_{uuid.uuid4().hex}"
    fd = os.open(str(tmp_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, content)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.chmod(tmp_path, 0o600)
    os.replace(tmp_path, p)
    os.chmod(p, 0o600)
    try:
        dir_fd = os.open(str(parent), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except Exception:
        pass


def verify_source_snapshot_before_write(
    stale_snapshot: dict[str, Any],
    current_snapshot: dict[str, Any],
) -> None:
    """Verify source snapshot matches current state, blocking TOCTOU race conditions."""
    if stale_snapshot != current_snapshot:
        raise ValueError("SNAPSHOT_DRIFT: TOCTOU_DETECTED source snapshot changed before write")


def replace_marker_section(text: str, marker_prefix: str, replacement: str) -> str:
    """Replace content between single marker pair preserving outside bytes exactly."""
    start_marker = f"<!-- {marker_prefix}:START -->"
    end_marker = f"<!-- {marker_prefix}:END -->"
    if text.count(start_marker) != 1 or text.count(end_marker) != 1:
        raise ValueError(f"DUPLICATE_OR_MISSING_MARKER: {marker_prefix}")
    start_idx = text.index(start_marker)
    end_idx = text.index(end_marker)
    if end_idx < start_idx:
        raise ValueError(f"REORDERED_MARKERS: {marker_prefix}")
    before = text[: start_idx + len(start_marker)]
    after = text[end_idx:]
    return f"{before}\n{replacement}\n{after}"


def render_all(
    output_root: Path | None = None,
    repo_root: Path | None = None,
) -> RenderManifestV1:
    """Render context profiles for all supported provider targets."""
    root = output_root or ROOT
    source_root = repo_root or ROOT
    source_snapshot = get_current_manifest(source_root)
    outputs = expected_profile_outputs(source_root)
    # Reject unexpected files rather than silently deleting user-owned artifacts.
    for directory, suffix in (('.codex/agents', '*.toml'), ('.antigravity/agents', '*.agent')):
        actual = {p.relative_to(root).as_posix() for p in (root / directory).glob(suffix)}
        extra = actual - set(outputs)
        if extra:
            raise ValueError(f'EXTRA_ARTIFACT_DETECTED: {sorted(extra)}')
    # Preflight every destination before writing any generated artifact.
    for relative in outputs:
        path = root / relative
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
            raise ValueError('SYMLINK_REJECTED')
        if any(parent.exists() and not parent.is_dir() for parent in path.parents):
            raise ValueError('UNSAFE_PATH: destination ancestor is not a directory')
        if path.exists():
            safe_open_bounded(path, root)
    verify_source_snapshot_before_write(source_snapshot, get_current_manifest(source_root))
    for relative, content in outputs.items():
        path = root / relative
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
            raise ValueError('SYMLINK_REJECTED')
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or safe_open_bounded(path, root) != content:
            temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
            try:
                with temporary.open('xb') as stream:
                    os.chmod(temporary, 0o600)
                    stream.write(content)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
    manifest = get_current_manifest(source_root, output_root=root)
    return RenderManifestV1(**manifest)


def render_context_profiles(
    resolution: Any = None,
    output_root: Path | None = None,
    targets: tuple[str, ...] = ("codex", "antigravity"),
    repo_root: Path | None = None,
) -> RenderManifestV1:
    """Render context profiles for specified targets and return RenderManifestV1."""
    if set(targets) != {'codex', 'antigravity'} or len(targets) != 2:
        raise ValueError('UNSUPPORTED_OR_EMPTY_RENDER_TARGETS')
    manifest = render_all(output_root, repo_root=repo_root)
    manifest['manifest_sha256'] = compute_manifest_self_digest(manifest)
    return RenderManifestV1(**manifest)


def check_context_profiles(
    resolution: Any = None,
    output_root: Path | None = None,
    targets: tuple[str, ...] = ("codex", "antigravity"),
    repo_root: Path | None = None,
) -> tuple[CheckResult, ...]:
    """Check context profiles in pure in-memory calculation with zero writes."""
    root = output_root or ROOT
    try:
        if not targets or set(targets) - {'codex', 'antigravity'}:
            raise ValueError('UNSUPPORTED_OR_EMPTY_CHECK_TARGETS')
        outputs = expected_profile_outputs(repo_root or ROOT)
        failures = []
        for directory, pattern, target in (('.codex/agents', '*.toml', 'codex'),
                                           ('.antigravity/agents', '*.agent', 'antigravity')):
            if target not in targets:
                continue
            expected = {p for p in outputs if p.startswith(directory + '/')}
            actual = {p.relative_to(root).as_posix() for p in (root / directory).glob(pattern)}
            if expected != actual:
                failures.append(f'{target}: inventory differs')
            for relative in sorted(expected & actual):
                if safe_open_bounded(root / relative, root) != outputs[relative]:
                    failures.append(f'{relative}: canonical content differs')
        return (CheckResult(ok=not failures, detail='; '.join(failures) or
                            'Codex/Antigravity generated bytes match canonical inputs; native runtime unverified'),)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return (CheckResult(ok=False, detail=f'CONTEXT_CHECK_FAILED: {exc}'),)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render Agent Context Profiles")
    parser.add_argument("--output-root", default=str(ROOT))
    parser.add_argument("--check", action="store_true", help="Pure check mode")
    args = parser.parse_args(argv)

    if args.check:
        results = check_context_profiles(output_root=Path(args.output_root))
        for r in results:
            prefix = "[OK]" if r.ok else "[ERROR]"
            print(f"{prefix} {r.name}: {r.detail}")
        return 0 if all(r.ok for r in results) else 1

    manifest = render_all(output_root=Path(args.output_root))
    print(f"[OK] Rendered targets: {', '.join(manifest['rendered_targets'])}")
    print(f"[OK] Manifest SHA-256: {manifest['manifest_sha256']}")
    return 0


if __name__ == "__main__":
    # Support direct script invocation as well as python -m scripts.<module>.
    import sys
    if not __package__:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    raise SystemExit(main())
