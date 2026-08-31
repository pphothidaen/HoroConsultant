#!/usr/bin/env python3
"""Permission remediation and owner-only boundary enforcement tool (BRK-B2-030).

This module enforces strict owner-only POSIX permissions on account homes,
broker state/backup directories, manifests, sensitive credential files, and
executable wrapper binaries.

Security Rules Enforced:
1. Account homes (~/.ai-accounts/{agy,codex}/account{1,2,3}) -> mode 0700 (drwx------).
2. Known sensitive regular files inside account directories -> mode 0600 (-rw-------).
3. Broker state and backup directories -> mode 0700 (drwx------).
4. Broker state, manifest, and backup files -> mode 0600 (-rw-------).
5. Account wrapper binaries (~/.local/bin/{agy1..3,codex1..3}) -> mode 0500 (-r-x------).
6. Fail-closed rejection before mutation on any symlink, foreign UID, ACL anomaly,
   unknown file type (FIFOs, sockets, devices), or unauthorized path traversal.
7. Metadata-only audit without reading or outputting file content.
8. Generates a rollback manifest recording prior modes for reversible remediation.
9. Pure ASCII logging and diagnostics.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import sys
from typing import Any

CANONICAL_PROVIDERS: tuple[str, ...] = ("agy", "codex")
CANONICAL_ACCOUNT_DIRS: tuple[str, ...] = ("account1", "account2", "account3")
CANONICAL_ALIASES: tuple[str, ...] = (
    "agy1",
    "agy2",
    "agy3",
    "codex1",
    "codex2",
    "codex3",
)

MODE_DIR_OWNER_ONLY = 0o700  # rwx------
MODE_FILE_SENSITIVE = 0o600  # rw-------
MODE_WRAPPER_EXEC = 0o500    # r-x------


@dataclass
class PermissionTarget:
    """Represents a discovered filesystem item and its required permission mode."""

    path: str
    relative_path: str
    category: str
    file_type: str
    target_mode: int
    target_mode_octal: str
    current_mode: int
    current_mode_octal: str
    uid: int
    gid: int
    needs_change: bool


@dataclass
class AuditReport:
    """Metadata-only audit summary."""

    root_dir: str
    inspected_count: int
    violations: list[str]
    targets: list[PermissionTarget]
    is_compliant: bool
    needs_remediation_count: int


def _octal_str(mode: int) -> str:
    """Format mode integer as 4-digit octal string (e.g. '0700')."""
    return f"{stat.S_IMODE(mode):04o}"


def _check_security_invariants(
    item_path: Path,
    expected_uid: int,
) -> tuple[bool, str | None, os.stat_result | None]:
    """Inspect file metadata strictly without reading contents.

    Rejects:
    - Symlinks (to prevent link traversal attacks)
    - Foreign UIDs (must match expected UID)
    - Non-regular and non-directory files (FIFOs, sockets, block/char devices)
    - ACL anomalies (setuid / setgid bits)
    """
    try:
        st = item_path.lstat()
    except OSError as err:
        return False, f"Cannot stat path '{item_path}': {err}", None

    # Check for symlink
    if stat.S_ISLNK(st.st_mode):
        return False, f"Symlink rejected at '{item_path}'", st

    # Check owner UID
    if st.st_uid != expected_uid:
        return (
            False,
            f"Foreign UID {st.st_uid} (expected {expected_uid}) at '{item_path}'",
            st,
        )

    # Check file type
    if not (stat.S_ISDIR(st.st_mode) or stat.S_ISREG(st.st_mode)):
        return (
            False,
            f"Unknown or special file type (mode: {_octal_str(st.st_mode)}) at '{item_path}'",
            st,
        )

    # Check for setuid / setgid / sticky bit anomalies on files
    raw_mode = st.st_mode
    if stat.S_ISREG(raw_mode) and (raw_mode & (stat.S_ISUID | stat.S_ISGID)):
        return (
            False,
            f"Anomalous privilege bit (setuid/setgid) at '{item_path}'",
            st,
        )

    return True, None, st


def audit_account_tree(
    accounts_dir: Path,
    root_dir: Path,
    expected_uid: int,
    targets: list[PermissionTarget],
    violations: list[str],
) -> None:
    """Scan and validate ~/.ai-accounts structure and subdirectories."""
    # Validate accounts_dir itself
    ok, err, st = _check_security_invariants(accounts_dir, expected_uid)
    if not ok or st is None:
        violations.append(err or f"Invalid accounts directory: {accounts_dir}")
        return

    current_imode = stat.S_IMODE(st.st_mode)
    targets.append(
        PermissionTarget(
            path=str(accounts_dir),
            relative_path=str(accounts_dir.relative_to(root_dir)),
            category="accounts_root",
            file_type="directory",
            target_mode=MODE_DIR_OWNER_ONLY,
            target_mode_octal=_octal_str(MODE_DIR_OWNER_ONLY),
            current_mode=current_imode,
            current_mode_octal=_octal_str(current_imode),
            uid=st.st_uid,
            gid=st.st_gid,
            needs_change=current_imode != MODE_DIR_OWNER_ONLY,
        )
    )

    try:
        entries = list(os.scandir(accounts_dir))
    except OSError as err:
        violations.append(f"Cannot list accounts directory '{accounts_dir}': {err}")
        return

    for entry in sorted(entries, key=lambda e: e.name):
        entry_path = Path(entry.path)
        ok, err, entry_st = _check_security_invariants(entry_path, expected_uid)
        if not ok or entry_st is None:
            violations.append(err or f"Invalid entry '{entry_path}'")
            continue

        if entry.name in ("broker", ".broker"):
            # Broker state directory under .ai-accounts
            audit_broker_tree(entry_path, root_dir, expected_uid, targets, violations)
            continue

        if entry.name not in CANONICAL_PROVIDERS:
            violations.append(
                f"Unauthorized provider directory '{entry.name}' at '{entry_path}'"
            )
            continue

        # Provider directory (e.g. .ai-accounts/agy)
        provider_imode = stat.S_IMODE(entry_st.st_mode)
        targets.append(
            PermissionTarget(
                path=str(entry_path),
                relative_path=str(entry_path.relative_to(root_dir)),
                category="provider_dir",
                file_type="directory",
                target_mode=MODE_DIR_OWNER_ONLY,
                target_mode_octal=_octal_str(MODE_DIR_OWNER_ONLY),
                current_mode=provider_imode,
                current_mode_octal=_octal_str(provider_imode),
                uid=entry_st.st_uid,
                gid=entry_st.st_gid,
                needs_change=provider_imode != MODE_DIR_OWNER_ONLY,
            )
        )

        try:
            account_entries = list(os.scandir(entry_path))
        except OSError as err:
            violations.append(f"Cannot list provider directory '{entry_path}': {err}")
            continue

        for acct in sorted(account_entries, key=lambda e: e.name):
            acct_path = Path(acct.path)
            ok, err, acct_st = _check_security_invariants(acct_path, expected_uid)
            if not ok or acct_st is None:
                violations.append(err or f"Invalid account directory '{acct_path}'")
                continue

            if acct.name not in CANONICAL_ACCOUNT_DIRS:
                violations.append(
                    f"Unauthorized account directory '{acct.name}' at '{acct_path}'"
                )
                continue

            # Account home directory (e.g. .ai-accounts/agy/account1)
            acct_imode = stat.S_IMODE(acct_st.st_mode)
            targets.append(
                PermissionTarget(
                    path=str(acct_path),
                    relative_path=str(acct_path.relative_to(root_dir)),
                    category="account_home",
                    file_type="directory",
                    target_mode=MODE_DIR_OWNER_ONLY,
                    target_mode_octal=_octal_str(MODE_DIR_OWNER_ONLY),
                    current_mode=acct_imode,
                    current_mode_octal=_octal_str(acct_imode),
                    uid=acct_st.st_uid,
                    gid=acct_st.st_gid,
                    needs_change=acct_imode != MODE_DIR_OWNER_ONLY,
                )
            )

            # Recursively audit files and subdirectories within account home
            _audit_directory_tree(
                acct_path,
                root_dir,
                expected_uid,
                dir_category="account_subdir",
                file_category="sensitive_file",
                targets=targets,
                violations=violations,
            )


def _audit_directory_tree(
    base_dir: Path,
    root_dir: Path,
    expected_uid: int,
    dir_category: str,
    file_category: str,
    targets: list[PermissionTarget],
    violations: list[str],
) -> None:
    """Recursively audit subdirectories and regular files."""
    for dirpath_str, dirnames, filenames in os.walk(str(base_dir)):
        dirpath = Path(dirpath_str)

        # Check subdirectories
        for dname in sorted(dirnames):
            dpath = dirpath / dname
            ok, err, dst = _check_security_invariants(dpath, expected_uid)
            if not ok or dst is None:
                violations.append(err or f"Invalid directory '{dpath}'")
                continue
            dimode = stat.S_IMODE(dst.st_mode)
            targets.append(
                PermissionTarget(
                    path=str(dpath),
                    relative_path=str(dpath.relative_to(root_dir)),
                    category=dir_category,
                    file_type="directory",
                    target_mode=MODE_DIR_OWNER_ONLY,
                    target_mode_octal=_octal_str(MODE_DIR_OWNER_ONLY),
                    current_mode=dimode,
                    current_mode_octal=_octal_str(dimode),
                    uid=dst.st_uid,
                    gid=dst.st_gid,
                    needs_change=dimode != MODE_DIR_OWNER_ONLY,
                )
            )

        # Check files
        for fname in sorted(filenames):
            fpath = dirpath / fname
            ok, err, fst = _check_security_invariants(fpath, expected_uid)
            if not ok or fst is None:
                violations.append(err or f"Invalid file '{fpath}'")
                continue
            fimode = stat.S_IMODE(fst.st_mode)
            targets.append(
                PermissionTarget(
                    path=str(fpath),
                    relative_path=str(fpath.relative_to(root_dir)),
                    category=file_category,
                    file_type="regular_file",
                    target_mode=MODE_FILE_SENSITIVE,
                    target_mode_octal=_octal_str(MODE_FILE_SENSITIVE),
                    current_mode=fimode,
                    current_mode_octal=_octal_str(fimode),
                    uid=fst.st_uid,
                    gid=fst.st_gid,
                    needs_change=fimode != MODE_FILE_SENSITIVE,
                )
            )


def audit_broker_tree(
    broker_dir: Path,
    root_dir: Path,
    expected_uid: int,
    targets: list[PermissionTarget],
    violations: list[str],
) -> None:
    """Scan and validate broker state, migration, runtime, and backup directories."""
    ok, err, st = _check_security_invariants(broker_dir, expected_uid)
    if not ok or st is None:
        violations.append(err or f"Invalid broker directory '{broker_dir}'")
        return

    current_imode = stat.S_IMODE(st.st_mode)
    targets.append(
        PermissionTarget(
            path=str(broker_dir),
            relative_path=str(broker_dir.relative_to(root_dir)),
            category="broker_root",
            file_type="directory",
            target_mode=MODE_DIR_OWNER_ONLY,
            target_mode_octal=_octal_str(MODE_DIR_OWNER_ONLY),
            current_mode=current_imode,
            current_mode_octal=_octal_str(current_imode),
            uid=st.st_uid,
            gid=st.st_gid,
            needs_change=current_imode != MODE_DIR_OWNER_ONLY,
        )
    )

    _audit_directory_tree(
        broker_dir,
        root_dir,
        expected_uid,
        dir_category="broker_dir",
        file_category="broker_manifest",
        targets=targets,
        violations=violations,
    )


def audit_wrappers(
    root_dir: Path,
    expected_uid: int,
    targets: list[PermissionTarget],
    violations: list[str],
) -> None:
    """Scan and validate account wrappers (~/.local/bin/{agy1..3,codex1..3})."""
    candidate_dirs = [
        root_dir / ".local" / "bin",
        root_dir / "wrappers",
        root_dir / "bin",
        root_dir / ".bin",
    ]

    for candidate in candidate_dirs:
        if not candidate.is_dir() or candidate.is_symlink():
            continue

        for alias in CANONICAL_ALIASES:
            wrapper_path = candidate / alias
            if not wrapper_path.exists() and not wrapper_path.is_symlink():
                continue

            ok, err, st = _check_security_invariants(wrapper_path, expected_uid)
            if not ok or st is None:
                violations.append(err or f"Invalid wrapper '{wrapper_path}'")
                continue

            if not stat.S_ISREG(st.st_mode):
                violations.append(
                    f"Wrapper '{wrapper_path}' is not a regular file (mode {_octal_str(st.st_mode)})"
                )
                continue

            current_imode = stat.S_IMODE(st.st_mode)
            targets.append(
                PermissionTarget(
                    path=str(wrapper_path),
                    relative_path=str(wrapper_path.relative_to(root_dir)),
                    category="wrapper",
                    file_type="wrapper",
                    target_mode=MODE_WRAPPER_EXEC,
                    target_mode_octal=_octal_str(MODE_WRAPPER_EXEC),
                    current_mode=current_imode,
                    current_mode_octal=_octal_str(current_imode),
                    uid=st.st_uid,
                    gid=st.st_gid,
                    needs_change=current_imode != MODE_WRAPPER_EXEC,
                )
            )


def audit_permissions(
    root_dir: Path,
    expected_uid: int | None = None,
) -> AuditReport:
    """Perform a metadata-only audit of all security-sensitive boundaries."""
    uid = expected_uid if expected_uid is not None else os.getuid()
    targets: list[PermissionTarget] = []
    violations: list[str] = []

    resolved_root = root_dir.resolve()
    if not resolved_root.is_dir() or resolved_root.is_symlink():
        violations.append(f"Root directory '{resolved_root}' is invalid or symlink")
        return AuditReport(
            root_dir=str(resolved_root),
            inspected_count=0,
            violations=violations,
            targets=[],
            is_compliant=False,
            needs_remediation_count=0,
        )

    # 1. Inspect .ai-accounts if present or root itself if it is .ai-accounts
    accounts_dir = resolved_root / ".ai-accounts"
    if accounts_dir.exists():
        audit_account_tree(accounts_dir, resolved_root, uid, targets, violations)
    elif (resolved_root / "agy").is_dir() or (resolved_root / "codex").is_dir():
        audit_account_tree(resolved_root, resolved_root, uid, targets, violations)
    elif resolved_root.name in CANONICAL_ACCOUNT_DIRS:
        _audit_directory_tree(
            resolved_root,
            resolved_root,
            uid,
            dir_category="account_subdir",
            file_category="sensitive_file",
            targets=targets,
            violations=violations,
        )

    # 2. Inspect Broker directories
    broker_candidates = [
        resolved_root / "Library" / "Application Support" / "HoroConsultant" / "AccountBroker",
        resolved_root / "AccountBroker",
        resolved_root / ".ai-broker",
        resolved_root / ".broker",
    ]
    for bdir in broker_candidates:
        if bdir.exists():
            audit_broker_tree(bdir, resolved_root, uid, targets, violations)

    # 3. Inspect Wrappers
    audit_wrappers(resolved_root, uid, targets, violations)

    # Deduplicate targets by path
    unique_targets: dict[str, PermissionTarget] = {}
    for t in targets:
        unique_targets[t.path] = t
    target_list = list(unique_targets.values())

    needs_change_count = sum(1 for t in target_list if t.needs_change)
    is_compliant = len(violations) == 0 and needs_change_count == 0

    return AuditReport(
        root_dir=str(resolved_root),
        inspected_count=len(target_list),
        violations=violations,
        targets=target_list,
        is_compliant=is_compliant,
        needs_remediation_count=needs_change_count,
    )


def generate_rollback_manifest(
    report: AuditReport,
    action: str,
) -> dict[str, Any]:
    """Generate structured JSON rollback manifest recording prior modes."""
    now_utc = datetime.now(timezone.utc).isoformat()
    entries = []
    for t in report.targets:
        entries.append(
            {
                "path": t.path,
                "relative_path": t.relative_path,
                "category": t.category,
                "file_type": t.file_type,
                "prior_mode": t.current_mode_octal,
                "target_mode": t.target_mode_octal,
                "prior_mode_int": t.current_mode,
                "target_mode_int": t.target_mode,
                "uid": t.uid,
                "gid": t.gid,
                "status": "REMEDIATED" if action == "enforce" else "PROPOSED",
            }
        )

    return {
        "manifest_version": "1.0",
        "action": action,
        "created_at": now_utc,
        "root_dir": report.root_dir,
        "inspected_count": report.inspected_count,
        "remediated_count": report.needs_remediation_count,
        "entries": entries,
    }


def enforce_permissions(
    report: AuditReport,
    rollback_path: Path | None = None,
) -> tuple[bool, str]:
    """Apply required permission remediations in enforce mode.

    Fails closed before modifying anything if any security violation is present.
    """
    if report.violations:
        return (
            False,
            f"Security violations detected ({len(report.violations)}). Remediation aborted.",
        )

    # Generate rollback manifest before modifying
    if rollback_path is not None:
        manifest_data = generate_rollback_manifest(report, action="enforce")
        try:
            rollback_path.parent.mkdir(parents=True, exist_ok=True)
            rollback_path.write_text(
                json.dumps(manifest_data, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            rollback_path.chmod(MODE_FILE_SENSITIVE)
        except OSError as err:
            return False, f"Failed to write rollback manifest: {err}"

    remediated = 0
    for target in report.targets:
        if not target.needs_change:
            continue

        p = Path(target.path)
        try:
            # Re-verify no symlink before chmod
            if p.is_symlink():
                return False, f"Symlink detected during enforcement at '{p}'. Aborting."
            os.chmod(p, target.target_mode)
            remediated += 1
        except OSError as err:
            return False, f"Failed to chmod '{p}' to {target.target_mode_octal}: {err}"

    return True, f"Successfully remediated {remediated} targets to owner-only permissions."


def rollback_from_manifest(manifest_path: Path) -> tuple[bool, str]:
    """Restore previous permissions recorded in a rollback manifest."""
    if manifest_path.is_symlink() or not manifest_path.is_file():
        return False, f"Rollback manifest '{manifest_path}' is not a valid regular file."

    try:
        content = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as err:
        return False, f"Cannot parse rollback manifest: {err}"

    entries = content.get("entries", [])
    restored = 0
    expected_uid = os.getuid()

    for entry in entries:
        p = Path(entry["path"])
        if not p.exists() or p.is_symlink():
            continue
        try:
            st = p.lstat()
            if st.st_uid != expected_uid:
                return (
                    False,
                    f"Foreign UID {st.st_uid} at '{p}' during rollback. Aborting.",
                )
            prior_mode_int = entry["prior_mode_int"]
            os.chmod(p, prior_mode_int)
            restored += 1
        except OSError as err:
            return False, f"Failed to rollback '{p}': {err}"

    return True, f"Successfully restored {restored} targets to prior permissions."


def _build_argument_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Audit and harden AI account and broker permissions (BRK-B2-030).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform metadata-only audit without modifying filesystem.",
    )
    group.add_argument(
        "--enforce",
        action="store_true",
        help="Enforce owner-only permission boundaries.",
    )
    group.add_argument(
        "--rollback",
        action="store_true",
        help="Restore permissions using a rollback manifest.",
    )

    parser.add_argument(
        "--root-dir",
        type=Path,
        default=Path.home(),
        help="Base root directory to inspect (defaults to $HOME).",
    )
    parser.add_argument(
        "--rollback-manifest",
        type=Path,
        default=None,
        help="Path to write or read the rollback manifest JSON.",
    )
    return parser


def main(argv: list[str]) -> int:
    """CLI entrypoint."""
    parser = _build_argument_parser()
    try:
        options = parser.parse_args(argv)
    except SystemExit as err:
        return int(err.code)

    root_dir: Path = options.root_dir
    manifest_path: Path | None = options.rollback_manifest

    if options.rollback:
        if manifest_path is None:
            print(
                "[ERROR] --rollback requires --rollback-manifest <path>",
                file=sys.stderr,
            )
            return 2
        ok, message = rollback_from_manifest(manifest_path)
        if ok:
            print(f"[OK] {message}")
            return 0
        else:
            print(f"[ERROR] {message}", file=sys.stderr)
            return 1

    # Perform metadata-only audit
    report = audit_permissions(root_dir)

    # Print pure ASCII diagnostics
    print(f"[INFO] Root directory: {report.root_dir}")
    print(f"[INFO] Total items inspected: {report.inspected_count}")
    print(f"[INFO] Items requiring remediation: {report.needs_remediation_count}")

    if report.violations:
        print(f"[ERROR] Found {len(report.violations)} security violations:", file=sys.stderr)
        for v in report.violations:
            print(f"  - {v}", file=sys.stderr)
        return 1

    if options.dry_run:
        if manifest_path is not None:
            manifest_data = generate_rollback_manifest(report, action="dry-run")
            try:
                manifest_path.parent.mkdir(parents=True, exist_ok=True)
                manifest_path.write_text(
                    json.dumps(manifest_data, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                print(f"[INFO] Wrote dry-run manifest to: {manifest_path}")
            except OSError as err:
                print(f"[ERROR] Failed to write dry-run manifest: {err}", file=sys.stderr)
                return 1

        if report.is_compliant:
            print("[OK] All permissions compliant with owner-only policy.")
        else:
            print(
                f"[INFO] Dry-run complete. {report.needs_remediation_count} items would be remediated."
            )
        return 0

    if options.enforce:
        ok, msg = enforce_permissions(report, rollback_path=manifest_path)
        if ok:
            if manifest_path is not None:
                print(f"[INFO] Rollback manifest saved to: {manifest_path}")
            print(f"[OK] {msg}")
            return 0
        else:
            print(f"[ERROR] {msg}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
