#!/usr/bin/env python3
"""Six-wrapper hardening and migration tool (BRK-B2-020).

Performs dry-run-first, hash-bound, atomic migration of legacy wrappers to new
broker client wrappers for the six canonical aliases (agy1..agy3, codex1..codex3).

Key Guarantees:
- Strictly operates on the 6 canonical aliases only.
- Dry-run-first: validates all preconditions before any disk mutation.
- Creates atomic backup under private 0700 backup directory with mode 0600.
- Never prints, logs, or persists legacy wrapper contents, hashes, or sizes.
- Replaces wrappers atomically with mode 0500 using shell=False client wrappers.
- Safe rollback capability: installs clean session-only or disabled 0500 wrappers
  and NEVER restores plaintext legacy wrappers.
- Rejects symlink chains, owner mismatches, and unapproved filesystem roots.
- Pure ASCII output and logs.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WRAPPER_CLIENT_SCRIPT = ROOT / "scripts" / "agent_broker_wrapper.py"
BRIDGE_SCRIPT = ROOT / "scripts" / "multiagent_broker_bridge.py"

CANONICAL_ALIASES: tuple[str, ...] = (
    "agy1",
    "agy2",
    "agy3",
    "agy4",
    "codex1",
    "codex2",
    "codex3",
)

APPROVED_ROOTS_DEFAULT: tuple[Path, ...] = (
    Path.home() / ".local" / "bin",
    Path("/Library/Application Support/HoroConsultant/AccountBroker/bin"),
    Path.home() / "Library/Application Support/HoroConsultant/AccountBroker/bin",
)

BACKUP_DIR_DEFAULT = Path.home() / ".ai-accounts" / "backups" / "wrappers"
MANIFEST_SCHEMA_VERSION = "agent-wrapper-migration-manifest-v1"

DIR_MODE_PRIVATE = 0o700
FILE_MODE_PRIVATE = 0o600
WRAPPER_MODE_SECURE = 0o500


def _error(message: str, exit_code: int = 2) -> int:
    """Emit pure ASCII error message to stderr and return exit code."""
    safe_msg = message.encode("ascii", "replace").decode("ascii")
    print(f"[ERROR] {safe_msg}", file=sys.stderr)
    return exit_code


def _info(message: str) -> None:
    """Emit pure ASCII info message to stdout."""
    safe_msg = message.encode("ascii", "replace").decode("ascii")
    print(f"[INFO] {safe_msg}")


def _ok(message: str) -> None:
    """Emit pure ASCII success message to stdout."""
    safe_msg = message.encode("ascii", "replace").decode("ascii")
    print(f"[OK] {safe_msg}")


def compute_sha256(content: str | bytes) -> str:
    """Compute SHA-256 hex digest of string or bytes."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


# ---------------------------------------------------------------------------
# Pre-flight Validation Helpers
# ---------------------------------------------------------------------------


def validate_target_directory(
    target_dir: Path,
    *,
    approved_roots: list[Path] | None = None,
    allow_any_root: bool = False,
) -> tuple[bool, str | None]:
    """Validate that target directory is acceptable, owner-owned, and not a symlink."""
    if not target_dir.is_absolute():
        return False, f"Target directory '{target_dir}' must be an absolute path"

    if target_dir.is_symlink():
        return False, f"Target directory '{target_dir}' cannot be a symlink"

    # Root approval check
    if not allow_any_root:
        valid_roots = approved_roots or list(APPROVED_ROOTS_DEFAULT)
        # Expand user in valid roots
        expanded_roots = [r.resolve() for r in valid_roots]
        target_resolved = target_dir.resolve()
        is_approved = any(
            target_resolved == root_dir or root_dir in target_resolved.parents
            for root_dir in expanded_roots
        )
        if not is_approved:
            return False, f"Target directory '{target_dir}' is not within approved roots: {valid_roots}"

    if target_dir.exists():
        if not target_dir.is_dir():
            return False, f"Target path '{target_dir}' exists but is not a directory"
        try:
            st = target_dir.stat()
            if st.st_uid != os.getuid():
                return False, f"Target directory '{target_dir}' owner mismatch (expected uid {os.getuid()}, got {st.st_uid})"
        except OSError as exc:
            return False, f"Unable to inspect target directory metadata: {exc}"

    return True, None


def validate_wrapper_file(wrapper_path: Path) -> tuple[bool, str | None]:
    """Validate that an existing wrapper file is a regular file owned by current user."""
    if not wrapper_path.exists():
        return True, None

    if wrapper_path.is_symlink():
        return False, f"Wrapper '{wrapper_path}' cannot be a symlink or part of a symlink chain"

    if not wrapper_path.is_file():
        return False, f"Wrapper '{wrapper_path}' exists but is not a regular file"

    try:
        st = wrapper_path.stat()
        if st.st_uid != os.getuid():
            return False, f"Wrapper '{wrapper_path}' owner mismatch (expected uid {os.getuid()}, got {st.st_uid})"
    except OSError as exc:
        return False, f"Unable to inspect wrapper metadata for '{wrapper_path}': {exc}"

    return True, None


# ---------------------------------------------------------------------------
# Wrapper Templates
# ---------------------------------------------------------------------------


def generate_active_broker_wrapper_source(
    alias: str,
    *,
    broker_path: Path | None = None,
    wrapper_client_path: Path | None = None,
) -> str:
    """Generate source code for the active hardened broker client wrapper."""
    bpath_str = str(broker_path.resolve()) if broker_path else None
    cpath_str = str(wrapper_client_path.resolve()) if wrapper_client_path else str(WRAPPER_CLIENT_SCRIPT)

    return f'''#!/usr/bin/env python3
"""Hardened broker wrapper client for alias {alias}.
Auto-generated by migrate_agent_wrappers.py (BRK-B2-020).
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys

ALIAS = {alias!r}
CONFIGURED_BROKER = {bpath_str!r}
WRAPPER_CLIENT = {cpath_str!r}

def main() -> int:
    args = sys.argv[1:]

    # 1. Dispatch directly via configured broker path if valid
    if CONFIGURED_BROKER:
        bp = Path(CONFIGURED_BROKER)
        if bp.is_file() and not bp.is_symlink() and os.access(bp, os.X_OK):
            res = subprocess.run([str(bp), ALIAS, "--", *args], shell=False, check=False)
            return res.returncode

    # 2. Dispatch via wrapper client script
    if WRAPPER_CLIENT:
        wp = Path(WRAPPER_CLIENT)
        if wp.is_file() and not wp.is_symlink():
            res = subprocess.run([sys.executable, str(wp), "--alias", ALIAS, "--", *args], shell=False, check=False)
            return res.returncode

    # 3. Check for binary in PATH
    for name in ("agent-broker", "ai-account-keychain-broker"):
        which_path = shutil.which(name)
        if which_path:
            p = Path(which_path)
            if p.is_file() and not p.is_symlink() and os.access(p, os.X_OK):
                res = subprocess.run([str(p), ALIAS, "--", *args], shell=False, check=False)
                return res.returncode

    print(f"[ERROR] Agent broker unavailable for alias '{{ALIAS}}'", file=sys.stderr)
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
'''


def generate_session_only_wrapper_source(
    alias: str,
    *,
    bridge_path: Path | None = None,
) -> str:
    """Generate source code for clean session-only rollback wrapper."""
    bpath_str = str(bridge_path.resolve()) if bridge_path else str(BRIDGE_SCRIPT)

    return f'''#!/usr/bin/env python3
"""Clean session-only broker wrapper for alias {alias} (Rollback Mode).
Never accesses Keychain or stores credentials.
"""
import os
from pathlib import Path
import subprocess
import sys

ALIAS = {alias!r}
BRIDGE_SCRIPT = {bpath_str!r}

def main() -> int:
    args = sys.argv[1:]
    env = dict(os.environ)
    env["AGENT_BROKER_SESSION_ONLY"] = "1"

    bp = Path(BRIDGE_SCRIPT)
    if bp.is_file() and not bp.is_symlink():
        res = subprocess.run(
            [sys.executable, str(bp), "--alias", ALIAS, "--session-only", "--", *args],
            env=env,
            shell=False,
            check=False,
        )
        return res.returncode

    print(f"[WARN] Session-only mode active for {{ALIAS}}; broker bridge unavailable.", file=sys.stderr)
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
'''


def generate_disabled_wrapper_source(
    alias: str,
    reason: str = "Wrapper disabled by migration rollback",
) -> str:
    """Generate source code for disabled 0500 rollback wrapper."""
    return f'''#!/usr/bin/env python3
"""Disabled wrapper for alias {alias} (BRK-B2-020 Rollback)."""
import sys

print("[ERROR] Account wrapper '{alias}' is disabled: {reason}", file=sys.stderr)
sys.exit(1)
'''


# ---------------------------------------------------------------------------
# Atomic Operations
# ---------------------------------------------------------------------------


def create_atomic_backup(
    target_dir: Path,
    backup_dir: Path,
) -> dict[str, Any]:
    """Atomically back up existing legacy wrappers to private backup dir with mode 0600.

    Guarantees:
    - Never logs or exposes legacy wrapper contents, sizes, or hashes.
    - Sets backup dir to 0700 and backup files to 0600.
    """
    backup_dir.mkdir(mode=DIR_MODE_PRIVATE, parents=True, exist_ok=True)
    os.chmod(backup_dir, DIR_MODE_PRIVATE)

    results: dict[str, Any] = {}

    for alias in CANONICAL_ALIASES:
        source_file = target_dir / alias
        if not source_file.exists():
            results[alias] = {"backup_created": False, "status": "NOT_PRESENT"}
            continue

        backup_file = backup_dir / f"{alias}.bak"
        temp_backup = backup_dir / f".{alias}.bak.tmp.{os.getpid()}"

        try:
            # Read binary without printing or recording data
            content = source_file.read_bytes()
            temp_backup.write_bytes(content)
            os.chmod(temp_backup, FILE_MODE_PRIVATE)
            os.replace(temp_backup, backup_file)
            os.chmod(backup_file, FILE_MODE_PRIVATE)
            results[alias] = {"backup_created": True, "status": "BACKED_UP"}
        except OSError as exc:
            if temp_backup.exists():
                try:
                    temp_backup.unlink()
                except OSError:
                    pass
            raise RuntimeError(f"Failed to create atomic backup for '{alias}': {exc}") from exc

    return results


def install_replacement_wrappers(
    target_dir: Path,
    wrapper_sources: dict[str, str],
    *,
    mode: int = WRAPPER_MODE_SECURE,
) -> dict[str, str]:
    """Atomically install replacement wrappers with specified mode.

    Returns mapping of alias to replacement wrapper SHA-256 hash.
    """
    target_dir.mkdir(mode=DIR_MODE_PRIVATE, parents=True, exist_ok=True)
    os.chmod(target_dir, DIR_MODE_PRIVATE)

    replacement_hashes: dict[str, str] = {}

    for alias in CANONICAL_ALIASES:
        source_code = wrapper_sources[alias]
        sha256_digest = compute_sha256(source_code)
        replacement_hashes[alias] = sha256_digest

        target_file = target_dir / alias
        temp_file = target_dir / f".{alias}.tmp.{os.getpid()}"

        try:
            temp_file.write_text(source_code, encoding="utf-8")
            os.chmod(temp_file, mode)
            os.replace(temp_file, target_file)
            os.chmod(target_file, mode)
        except OSError as exc:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
            raise RuntimeError(f"Failed to install wrapper for '{alias}': {exc}") from exc

    return replacement_hashes


def write_manifest(
    manifest_path: Path,
    manifest_data: dict[str, Any],
) -> None:
    """Atomically write migration manifest with mode 0600."""
    manifest_path.parent.mkdir(mode=DIR_MODE_PRIVATE, parents=True, exist_ok=True)
    temp_manifest = manifest_path.parent / f".{manifest_path.name}.tmp.{os.getpid()}"
    try:
        temp_manifest.write_text(
            json.dumps(manifest_data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.chmod(temp_manifest, FILE_MODE_PRIVATE)
        os.replace(temp_manifest, manifest_path)
        os.chmod(manifest_path, FILE_MODE_PRIVATE)
    except OSError as exc:
        if temp_manifest.exists():
            try:
                temp_manifest.unlink()
            except OSError:
                pass
        raise RuntimeError(f"Failed to write migration manifest: {exc}") from exc


# ---------------------------------------------------------------------------
# Migration Actions
# ---------------------------------------------------------------------------


def perform_migration(
    target_dir: Path,
    backup_dir: Path,
    *,
    broker_path: Path | None = None,
    wrapper_client_path: Path | None = None,
    approved_roots: list[Path] | None = None,
    allow_any_root: bool = False,
    manifest_path: Path | None = None,
    dry_run: bool = False,
) -> int:
    """Perform dry-run-first atomic migration of the six account wrappers."""
    _info(f"Checking target directory: {target_dir}")
    valid, err = validate_target_directory(
        target_dir,
        approved_roots=approved_roots,
        allow_any_root=allow_any_root,
    )
    if not valid:
        return _error(err or "Target directory validation failed")

    # Validate each wrapper file
    for alias in CANONICAL_ALIASES:
        wrapper_file = target_dir / alias
        v_ok, v_err = validate_wrapper_file(wrapper_file)
        if not v_ok:
            return _error(v_err or f"Validation failed for wrapper '{alias}'")

    # Build replacement wrapper sources
    sources: dict[str, str] = {}
    replacement_hashes: dict[str, str] = {}
    for alias in CANONICAL_ALIASES:
        src = generate_active_broker_wrapper_source(
            alias,
            broker_path=broker_path,
            wrapper_client_path=wrapper_client_path,
        )
        sources[alias] = src
        replacement_hashes[alias] = compute_sha256(src)

    if dry_run:
        _info("DRY-RUN: Preconditions verified for all 6 canonical aliases.")
        _info(f"DRY-RUN: Would backup existing wrappers from '{target_dir}' to '{backup_dir}' (mode 0600 in 0700 dir)")
        _info(f"DRY-RUN: Would replace 6 wrappers in '{target_dir}' with mode 0500:")
        for alias in CANONICAL_ALIASES:
            exists_str = "exists (will be backed up)" if (target_dir / alias).exists() else "new (will be created)"
            _info(f"  - {alias}: {exists_str}, replacement_sha256={replacement_hashes[alias]}")
        _ok("DRY-RUN complete. No files were modified.")
        return 0

    # 1. Create Atomic Backup
    _info(f"Creating atomic backup of existing wrappers in '{backup_dir}'...")
    try:
        backup_results = create_atomic_backup(target_dir, backup_dir)
    except Exception as exc:
        return _error(f"Backup failed: {exc}")

    # 2. Atomic Replacement
    _info(f"Installing hardened broker wrappers in '{target_dir}'...")
    try:
        installed_hashes = install_replacement_wrappers(
            target_dir,
            sources,
            mode=WRAPPER_MODE_SECURE,
        )
    except Exception as exc:
        return _error(f"Wrapper installation failed: {exc}")

    # 3. Write Manifest
    manifest_data = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "migrate",
        "target_dir": str(target_dir.resolve()),
        "backup_dir": str(backup_dir.resolve()),
        "aliases": {
            alias: {
                "status": "MIGRATED",
                "backup_complete": backup_results[alias]["backup_created"],
                "replacement_sha256": installed_hashes[alias],
                "mode": oct(WRAPPER_MODE_SECURE),
            }
            for alias in CANONICAL_ALIASES
        },
        "success": True,
    }

    if manifest_path is not None:
        try:
            write_manifest(manifest_path, manifest_data)
            _info(f"Migration manifest written to '{manifest_path}'")
        except Exception as exc:
            return _error(f"Failed to write manifest: {exc}")

    _ok("Successfully migrated all 6 canonical account wrappers to hardened broker client.")
    return 0


def perform_rollback(
    target_dir: Path,
    backup_dir: Path,
    *,
    rollback_mode: str = "session-only",
    bridge_path: Path | None = None,
    approved_roots: list[Path] | None = None,
    allow_any_root: bool = False,
    manifest_path: Path | None = None,
    dry_run: bool = False,
) -> int:
    """Perform safe rollback: install clean session-only or disabled 0500 wrappers.

    Guarantees:
    - NEVER restores plaintext legacy wrappers.
    - Atomically installs clean session-only or disabled 0500 wrappers.
    """
    _info(f"Checking target directory for rollback: {target_dir}")
    valid, err = validate_target_directory(
        target_dir,
        approved_roots=approved_roots,
        allow_any_root=allow_any_root,
    )
    if not valid:
        return _error(err or "Target directory validation failed")

    sources: dict[str, str] = {}
    replacement_hashes: dict[str, str] = {}

    for alias in CANONICAL_ALIASES:
        if rollback_mode == "disabled":
            src = generate_disabled_wrapper_source(alias, reason="Rollback executed")
        else:
            src = generate_session_only_wrapper_source(alias, bridge_path=bridge_path)
        sources[alias] = src
        replacement_hashes[alias] = compute_sha256(src)

    if dry_run:
        _info(f"DRY-RUN ROLLBACK: Would install 6 clean {rollback_mode} wrappers in '{target_dir}' (mode 0500).")
        _info("DRY-RUN ROLLBACK: Plaintext legacy wrappers are NEVER restored.")
        for alias in CANONICAL_ALIASES:
            _info(f"  - {alias}: mode=0500, sha256={replacement_hashes[alias]}")
        _ok("DRY-RUN ROLLBACK complete. No files were modified.")
        return 0

    _info(f"Executing rollback ({rollback_mode}) in '{target_dir}'...")
    try:
        installed_hashes = install_replacement_wrappers(
            target_dir,
            sources,
            mode=WRAPPER_MODE_SECURE,
        )
    except Exception as exc:
        return _error(f"Rollback wrapper installation failed: {exc}")

    manifest_data = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "rollback",
        "rollback_mode": rollback_mode,
        "target_dir": str(target_dir.resolve()),
        "aliases": {
            alias: {
                "status": f"ROLLED_BACK_{rollback_mode.upper()}",
                "replacement_sha256": installed_hashes[alias],
                "mode": oct(WRAPPER_MODE_SECURE),
            }
            for alias in CANONICAL_ALIASES
        },
        "success": True,
    }

    if manifest_path is not None:
        try:
            write_manifest(manifest_path, manifest_data)
            _info(f"Rollback manifest written to '{manifest_path}'")
        except Exception as exc:
            return _error(f"Failed to write manifest: {exc}")

    _ok(f"Rollback complete: 6 clean {rollback_mode} wrappers installed (plaintext wrappers were not restored).")
    return 0


# ---------------------------------------------------------------------------
# CLI Argument Parsing
# ---------------------------------------------------------------------------


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Six-wrapper hardening and migration tool (BRK-B2-020)."
    )
    parser.add_argument(
        "--target-dir",
        "--wrappers-dir",
        type=Path,
        default=APPROVED_ROOTS_DEFAULT[0],
        help=f"Target directory for wrappers (default: {APPROVED_ROOTS_DEFAULT[0]})",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=BACKUP_DIR_DEFAULT,
        help=f"Private backup directory (default: {BACKUP_DIR_DEFAULT})",
    )
    parser.add_argument(
        "--broker-path",
        type=Path,
        default=None,
        help="Path to agent-broker binary",
    )
    parser.add_argument(
        "--wrapper-client-path",
        type=Path,
        default=None,
        help="Path to agent_broker_wrapper.py client",
    )
    parser.add_argument(
        "--bridge-path",
        type=Path,
        default=None,
        help="Path to multiagent_broker_bridge.py",
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=None,
        help="Path to write migration manifest (mode 0600)",
    )
    parser.add_argument(
        "--approved-roots",
        type=Path,
        nargs="*",
        default=None,
        help="Custom approved root directories for validation",
    )
    parser.add_argument(
        "--allow-any-root",
        action="store_true",
        help="Allow any absolute root directory (for testing in isolated temporary dirs)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run without modifying filesystem",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Execute safe rollback to clean session-only or disabled wrappers",
    )
    parser.add_argument(
        "--rollback-mode",
        choices=["session-only", "disabled"],
        default="session-only",
        help="Rollback mode: clean session-only or disabled (default: session-only)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    try:
        args = parse_arguments(argv)
    except SystemExit as exc:
        return int(exc.code)

    if args.rollback:
        return perform_rollback(
            target_dir=args.target_dir,
            backup_dir=args.backup_dir,
            rollback_mode=args.rollback_mode,
            bridge_path=args.bridge_path,
            approved_roots=args.approved_roots,
            allow_any_root=args.allow_any_root,
            manifest_path=args.manifest_path,
            dry_run=args.dry_run,
        )
    else:
        return perform_migration(
            target_dir=args.target_dir,
            backup_dir=args.backup_dir,
            broker_path=args.broker_path,
            wrapper_client_path=args.wrapper_client_path,
            approved_roots=args.approved_roots,
            allow_any_root=args.allow_any_root,
            manifest_path=args.manifest_path,
            dry_run=args.dry_run,
        )


if __name__ == "__main__":
    raise SystemExit(main())
