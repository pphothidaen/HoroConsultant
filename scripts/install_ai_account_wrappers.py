#!/usr/bin/env python3
"""Install the fixed-alias bridge to the account keychain broker.

The bridge deliberately has no credential, provider, or keychain switches.
It suppresses broker streams so wrapper callers receive admission status only.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import stat
import sys


ALIASES = ("agy1", "agy2", "agy3", "agy4", "codex1", "codex2", "codex3")


def _error(message: str) -> int:
    print(f"[ERROR] {message}", file=sys.stderr)
    return 2


def _owner_only_directory(path: Path) -> bool:
    """Return whether an existing directory is non-symlink and owner-only."""

    if path.is_symlink() or not path.is_dir():
        return False
    details = path.stat()
    return details.st_uid == os.getuid() and stat.S_IMODE(details.st_mode) == 0o700


def _wrapper_source(alias: str, broker_path: Path) -> str:
    """Build an argv-safe Python wrapper without environment assignments."""

    return f'''#!{sys.executable}
import os
import subprocess
import sys

result = subprocess.run(
    [{str(broker_path)!r}, {alias!r}, "--", *sys.argv[1:]],
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    check=False,
)
if result.returncode == 0:
    print("[OK] account admission complete")
else:
    print("[ERROR] account admission unavailable", file=sys.stderr)
raise SystemExit(result.returncode)
'''


def _parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install fixed AI account wrappers.")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--broker-path", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    try:
        options = _parse_arguments(argv)
    except SystemExit as error:
        return int(error.code)

    output_dir = options.output_dir
    broker_path = options.broker_path
    if not output_dir.is_absolute() or not broker_path.is_absolute():
        return _error("absolute output and broker paths are required")
    if output_dir.is_symlink():
        return _error("output directory is not admissible")
    if options.dry_run:
        for alias in ALIASES:
            print(f"[INFO] would install {alias}")
        return 0
    if output_dir.exists():
        if not _owner_only_directory(output_dir):
            return _error("output directory is not owner-only")
    else:
        try:
            output_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
            output_dir.chmod(0o700)
        except OSError:
            return _error("unable to create output directory")
    if broker_path.is_symlink() or not broker_path.is_file() or not os.access(broker_path, os.X_OK):
        return _error("broker path is not an executable regular file")

    for alias in ALIASES:
        wrapper = output_dir / alias
        if wrapper.exists() or wrapper.is_symlink():
            return _error("refusing to replace an existing wrapper")
        try:
            wrapper.write_text(_wrapper_source(alias, broker_path), encoding="utf-8")
            wrapper.chmod(0o700)
        except OSError:
            return _error("unable to install wrapper")
    print("[OK] fixed account wrappers installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
