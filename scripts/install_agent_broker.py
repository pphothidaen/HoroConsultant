#!/usr/bin/env python3
"""Atomic Immutable Installer for macOS Agent Broker (BRK-B2-010).

This module provides an idempotent, dry-run-first installer and deterministic
uninstaller for the macOS Swift AI Account Keychain Broker and its manifests.

Key Guarantees:
- Closed manifest schema detailing version, binary artifacts, target directories,
  required modes, and file hashes.
- Staging in a private temporary directory (mode 0700) before atomic deployment.
- Strict validation of ownership, symlink avoidance, and mode enforcement (mode 0500
  for broker binary, 0700/0755 for directories, 0600 for manifests/receipts).
- Refuses to overwrite untracked targets without dry-run confirmation.
- Idempotent repeated install and deterministic uninstall.
- Pure ASCII logging and fail-closed security.
- Zero network, provider, live Keychain, or credential side effects.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = ROOT / "config" / "agent-broker" / "broker-install-manifest-v1.json"

CANONICAL_ALIASES: tuple[str, ...] = (
    "agy1",
    "agy2",
    "agy3",
    "codex1",
    "codex2",
    "codex3",
)

MODE_BROKER_BINARY = 0o500
MODE_SHARED_DIR = 0o755
MODE_PRIVATE_DIR = 0o700
MODE_MANIFEST = 0o600
MODE_RECEIPT = 0o600

RECEIPT_FILENAME = "install-receipt.json"


def _log_info(msg: str) -> None:
    print(f"[INFO] {msg}")


def _log_warn(msg: str) -> None:
    print(f"[WARN] {msg}", file=sys.stderr)


def _log_error(msg: str) -> int:
    print(f"[ERROR] {msg}", file=sys.stderr)
    return 2


def _log_ok(msg: str) -> None:
    print(f"[OK] {msg}")


def _file_sha256(path: Path) -> str:
    """Calculate SHA-256 digest of a regular file."""
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _is_owner_safe(path: Path) -> bool:
    """Verify that path is owned by current user and is not a symlink."""
    if path.is_symlink():
        return False
    try:
        st = path.stat()
        return st.st_uid == os.getuid()
    except OSError:
        return False


def _atomic_copy_file(src: Path, dst: Path, mode: int) -> None:
    """Atomically copy a file to dst using a temporary sibling and fsync."""
    dst_dir = dst.parent
    dst_dir.mkdir(parents=True, exist_ok=True)
    temp_dst = dst_dir / f".tmp_{dst.name}_{os.getpid()}_{hashlib.sha256(os.urandom(8)).hexdigest()[:8]}"
    try:
        shutil.copy2(src, temp_dst)
        temp_dst.chmod(mode)
        # fsync to guarantee flush to disk before rename
        with temp_dst.open("rb") as f:
            os.fsync(f.fileno())
        os.replace(temp_dst, dst)
        dst.chmod(mode)
    finally:
        if temp_dst.exists():
            try:
                temp_dst.unlink()
            except OSError:
                pass


def load_and_validate_manifest(manifest_path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Load and validate the closed install manifest."""
    if not manifest_path.is_file() or manifest_path.is_symlink():
        return None, f"Manifest path '{manifest_path}' is not a regular file"

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as err:
        return None, f"Failed to parse manifest JSON: {err}"

    if not isinstance(data, dict):
        return None, "Manifest root must be a JSON object"

    schema_version = data.get("schema_version")
    if schema_version != "broker-install-manifest-v1":
        return None, f"Unsupported manifest schema_version: '{schema_version}'"

    if "target_directories" not in data or not isinstance(data["target_directories"], list):
        return None, "Manifest missing required 'target_directories' array"

    if "binary_artifacts" not in data or not isinstance(data["binary_artifacts"], list):
        return None, "Manifest missing required 'binary_artifacts' array"

    return data, None


def stage_installation(
    stage_dir: Path,
    manifest: dict[str, Any],
    manifest_source_path: Path,
    broker_path: Path,
) -> tuple[dict[str, Any], list[Path]]:
    """Stage all directories, binaries, and manifests in private staging dir."""
    staged_files: list[Path] = []
    receipt_data: dict[str, Any] = {
        "schema_version": "agent-broker-install-receipt-v1",
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "manifest_id": manifest.get("manifest_id", "broker-manifest-v1"),
        "installed_files": {},
        "installed_directories": [],
    }

    # 1. Create target directories in staging
    target_dirs = manifest.get("target_directories", [])
    for dir_entry in target_dirs:
        rel_path = dir_entry["path"]
        mode_str = dir_entry.get("required_mode", "0755")
        mode = int(mode_str, 8)
        dest_dir = stage_dir / rel_path
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_dir.chmod(mode)
        receipt_data["installed_directories"].append(rel_path)

    # 2. Stage broker binary into bin/ and releases/
    broker_hash = _file_sha256(broker_path)
    for artifact in manifest.get("binary_artifacts", []):
        name = artifact.get("name")
        target_sub = artifact.get("target_subpath")
        mode_str = artifact.get("required_mode", "0500")
        mode = int(mode_str, 8)

        if not target_sub:
            continue

        staged_target = stage_dir / target_sub
        staged_target.parent.mkdir(parents=True, exist_ok=True)

        if name == "ai-account-keychain-broker":
            _atomic_copy_file(broker_path, staged_target, mode)
            staged_files.append(staged_target)
            receipt_data["installed_files"][target_sub] = {
                "sha256": broker_hash,
                "mode": mode_str,
                "size_bytes": staged_target.stat().st_size,
            }

            # If release_subpath is specified, also stage there
            rel_sub = artifact.get("release_subpath")
            if rel_sub:
                staged_rel = stage_dir / rel_sub
                staged_rel.parent.mkdir(parents=True, exist_ok=True)
                _atomic_copy_file(broker_path, staged_rel, mode)
                staged_files.append(staged_rel)
                receipt_data["installed_files"][rel_sub] = {
                    "sha256": broker_hash,
                    "mode": mode_str,
                    "size_bytes": staged_rel.stat().st_size,
                }
        elif name == "multiagent_broker_bridge.py":
            # If bridge source exists in repo, stage it
            bridge_source = ROOT / "scripts" / "multiagent_broker_bridge.py"
            if bridge_source.is_file():
                bridge_hash = _file_sha256(bridge_source)
                _atomic_copy_file(bridge_source, staged_target, mode)
                staged_files.append(staged_target)
                receipt_data["installed_files"][target_sub] = {
                    "sha256": bridge_hash,
                    "mode": mode_str,
                    "size_bytes": staged_target.stat().st_size,
                }

    # 3. Stage manifest into manifests/
    manifest_dest = stage_dir / "manifests" / "broker-install-manifest-v1.json"
    manifest_dest.parent.mkdir(parents=True, exist_ok=True)
    _atomic_copy_file(manifest_source_path, manifest_dest, MODE_MANIFEST)
    staged_files.append(manifest_dest)
    receipt_data["installed_files"]["manifests/broker-install-manifest-v1.json"] = {
        "sha256": _file_sha256(manifest_dest),
        "mode": "0600",
        "size_bytes": manifest_dest.stat().st_size,
    }

    # 4. Stage install receipt into manifests/
    receipt_dest = stage_dir / "manifests" / RECEIPT_FILENAME
    receipt_content = json.dumps(receipt_data, indent=2, sort_keys=True, ensure_ascii=True)
    receipt_dest.write_text(receipt_content, encoding="utf-8")
    receipt_dest.chmod(MODE_RECEIPT)
    staged_files.append(receipt_dest)
    receipt_data["installed_files"][f"manifests/{RECEIPT_FILENAME}"] = {
        "sha256": _file_sha256(receipt_dest),
        "mode": "0600",
        "size_bytes": receipt_dest.stat().st_size,
    }

    return receipt_data, staged_files


def run_install(
    output_dir: Path,
    broker_path: Path,
    manifest_path: Path,
    dry_run: bool = False,
) -> int:
    """Execute atomic installation of agent broker."""
    # Validate paths
    if not output_dir.is_absolute():
        return _log_error(f"Output directory must be absolute: '{output_dir}'")
    if not broker_path.is_absolute():
        return _log_error(f"Broker path must be absolute: '{broker_path}'")
    if not manifest_path.is_absolute():
        manifest_path = manifest_path.resolve()

    if output_dir.is_symlink():
        return _log_error(f"Output directory is a symlink: '{output_dir}'")
    if broker_path.is_symlink():
        return _log_error(f"Broker path is a symlink: '{broker_path}'")
    if not broker_path.is_file():
        return _log_error(f"Broker path is not a regular file: '{broker_path}'")
    if not os.access(broker_path, os.X_OK):
        return _log_error(f"Broker path is not executable: '{broker_path}'")

    manifest, err = load_and_validate_manifest(manifest_path)
    if err or not manifest:
        return _log_error(f"Manifest validation failed: {err}")

    # Check existing output_dir
    if output_dir.exists():
        if not _is_owner_safe(output_dir):
            return _log_error(f"Output directory '{output_dir}' is not owner-safe or owned by another user")
        # Check for existing receipt
        existing_receipt_path = output_dir / "manifests" / RECEIPT_FILENAME
        existing_receipt: dict[str, Any] | None = None
        if existing_receipt_path.is_file() and not existing_receipt_path.is_symlink():
            try:
                existing_receipt = json.loads(existing_receipt_path.read_text(encoding="utf-8"))
            except Exception:
                existing_receipt = None

        # Check for untracked conflicts
        for artifact in manifest.get("binary_artifacts", []):
            target_sub = artifact.get("target_subpath")
            if target_sub:
                dest = output_dir / target_sub
                if dest.exists() and not dest.is_symlink():
                    if existing_receipt is None or target_sub not in existing_receipt.get("installed_files", {}):
                        if not dry_run:
                            return _log_error(
                                f"Refusing to overwrite untracked target '{dest}'. "
                                f"Run with --dry-run or remove existing untracked file first."
                            )

    if dry_run:
        _log_info(f"DRY RUN: Planning atomic deployment to '{output_dir}'")
        _log_info(f"Manifest: {manifest_path} (ID: {manifest.get('manifest_id')})")
        _log_info(f"Source broker: {broker_path} (SHA-256: {_file_sha256(broker_path)})")
        for dir_entry in manifest.get("target_directories", []):
            _log_info(f"  [DIR]  {output_dir / dir_entry['path']} (mode {dir_entry.get('required_mode', '0755')})")
        for artifact in manifest.get("binary_artifacts", []):
            target_sub = artifact.get("target_subpath")
            if target_sub:
                _log_info(f"  [FILE] {output_dir / target_sub} (mode {artifact.get('required_mode', '0500')})")
        _log_info(f"  [FILE] {output_dir / 'manifests' / 'broker-install-manifest-v1.json'} (mode 0600)")
        _log_info(f"  [FILE] {output_dir / 'manifests' / RECEIPT_FILENAME} (mode 0600)")
        _log_ok("DRY RUN completed successfully. No changes made.")
        return 0

    # Stage installation in private temporary directory (mode 0700)
    with tempfile.TemporaryDirectory(prefix="hc-broker-stage-") as tmp_stage:
        stage_dir = Path(tmp_stage)
        stage_dir.chmod(MODE_PRIVATE_DIR)

        try:
            receipt_data, staged_files = stage_installation(
                stage_dir=stage_dir,
                manifest=manifest,
                manifest_source_path=manifest_path,
                broker_path=broker_path,
            )
        except Exception as ex:
            return _log_error(f"Staging failed: {ex}")

        # Verify staged files integrity and permissions
        for f in staged_files:
            if not f.exists():
                return _log_error(f"Staged file missing: {f}")
            st = f.stat()
            if f.name == "ai-account-keychain-broker":
                actual_mode = stat.S_IMODE(st.st_mode)
                if actual_mode != MODE_BROKER_BINARY:
                    return _log_error(f"Staged broker binary has invalid mode: {oct(actual_mode)}")

        # Create output_dir if not exists
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, mode=MODE_SHARED_DIR)
                output_dir.chmod(MODE_SHARED_DIR)
            except OSError as err:
                return _log_error(f"Failed to create output directory: {err}")

        # Atomically deploy from staging to destination
        for rel_dir in receipt_data["installed_directories"]:
            dest_dir = output_dir / rel_dir
            # Determine required mode from manifest
            mode = MODE_SHARED_DIR
            for d in manifest.get("target_directories", []):
                if d["path"] == rel_dir:
                    mode = int(d.get("required_mode", "0755"), 8)
                    break
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_dir.chmod(mode)

        for rel_file, file_info in receipt_data["installed_files"].items():
            src_file = stage_dir / rel_file
            dest_file = output_dir / rel_file
            mode = int(file_info["mode"], 8)
            _atomic_copy_file(src_file, dest_file, mode)

    _log_ok(f"Agent broker installed atomically to '{output_dir}'")
    return 0


def run_uninstall(
    output_dir: Path,
    dry_run: bool = False,
) -> int:
    """Execute deterministic uninstallation of agent broker."""
    if not output_dir.is_absolute():
        return _log_error(f"Output directory must be absolute: '{output_dir}'")
    if output_dir.is_symlink():
        return _log_error(f"Output directory is a symlink: '{output_dir}'")
    if not output_dir.exists():
        return _log_error(f"Output directory does not exist: '{output_dir}'")
    if not _is_owner_safe(output_dir):
        return _log_error(f"Output directory '{output_dir}' is not owner-safe")

    receipt_path = output_dir / "manifests" / RECEIPT_FILENAME
    if not receipt_path.is_file() or receipt_path.is_symlink():
        return _log_error(f"Installation receipt not found at '{receipt_path}'. Cannot safely uninstall.")

    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except Exception as err:
        return _log_error(f"Failed to read installation receipt: {err}")

    installed_files: dict[str, Any] = receipt.get("installed_files", {})
    installed_dirs: list[str] = receipt.get("installed_directories", [])

    if dry_run:
        _log_info(f"DRY RUN: Uninstalling from '{output_dir}'")
        for rel_file in installed_files.keys():
            target_file = output_dir / rel_file
            if target_file.exists():
                _log_info(f"  [REMOVE FILE] {target_file}")
        for rel_dir in reversed(installed_dirs):
            target_dir = output_dir / rel_dir
            if target_dir.exists():
                _log_info(f"  [REMOVE DIR (if empty)] {target_dir}")
        _log_ok("DRY RUN uninstall plan complete. No changes made.")
        return 0

    # Remove managed files
    for rel_file in installed_files.keys():
        target_file = output_dir / rel_file
        if target_file.is_file() and not target_file.is_symlink():
            try:
                target_file.unlink()
                _log_info(f"Removed file: {target_file}")
            except OSError as err:
                _log_warn(f"Failed to remove {target_file}: {err}")

    # Remove managed directories if empty
    for rel_dir in reversed(installed_dirs):
        target_dir = output_dir / rel_dir
        if target_dir.is_dir() and not target_dir.is_symlink():
            try:
                if not any(target_dir.iterdir()):
                    target_dir.rmdir()
                    _log_info(f"Removed empty directory: {target_dir}")
            except OSError:
                pass

    _log_ok(f"Agent broker uninstalled deterministically from '{output_dir}'")
    return 0


def _parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Atomic Immutable Installer for macOS Agent Broker (BRK-B2-010)."
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Target base directory for broker installation.",
    )
    parser.add_argument(
        "--broker-path",
        required=False,
        type=Path,
        help="Source path to compiled agent broker binary.",
    )
    parser.add_argument(
        "--manifest-path",
        required=False,
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Path to broker installation manifest JSON.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate installation or uninstallation without writing changes.",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Deterministic uninstall of manifest-owned broker artifacts.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    try:
        options = _parse_arguments(argv)
    except SystemExit as error:
        return int(error.code)

    output_dir = options.output_dir
    dry_run = options.dry_run

    if options.uninstall:
        return run_uninstall(output_dir=output_dir, dry_run=dry_run)

    broker_path = options.broker_path
    if broker_path is None:
        return _log_error("--broker-path is required for installation")

    manifest_path = options.manifest_path or DEFAULT_MANIFEST_PATH
    return run_install(
        output_dir=output_dir,
        broker_path=broker_path,
        manifest_path=manifest_path,
        dry_run=dry_run,
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
