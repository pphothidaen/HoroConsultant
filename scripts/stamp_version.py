#!/usr/bin/env python3
"""
scripts/stamp_version.py
========================
Stamp one immutable Git source revision into all version-sensitive source files.

Targets:
  - project/static/version.json & public/version.json
  - project/static/app.js & public/app.js (CLIENT_APP_VERSION)
  - project/static/sw.js & public/sw.js (CACHE_VERSION)
  - project/static/index.html & public/index.html (footer text + cache-busting query params)

Usage:
  python3 scripts/stamp_version.py              # stamp all local files
  python3 scripts/stamp_version.py --check      # dry-run: report mismatches only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE_SOURCE_METADATA_PATH = "project/static/version.json"
SHORT_COMMIT_RE = re.compile(r"[0-9a-f]{7}")
FULL_REVISION_RE = re.compile(r"[0-9a-f]{40}")


def get_git_revision(reference: str = "HEAD") -> str:
    """Resolve one commit reference to its immutable full Git revision."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"{reference}^{{commit}}"],
            capture_output=True,
            text=True,
            cwd=ROOT,
            check=False,
        )
        revision = result.stdout.strip()
        if result.returncode == 0 and FULL_REVISION_RE.fullmatch(revision):
            return revision
        return "unknown"
    except OSError:
        return "unknown"


def get_git_short_hash() -> str:
    """Return the first seven characters of the current Git revision."""
    revision = get_git_revision()
    return revision[:7] if revision != "unknown" else "unknown"


def build_version(commit: str) -> str:
    """Build the full version string like 1.0.0.abc1234."""
    return f"1.0.0.{commit}"


def build_release_metadata(
    version: str,
    commit: str,
    revision: str,
) -> dict[str, str]:
    """Build the publisher's closed immutable source-provenance object."""
    if (
        SHORT_COMMIT_RE.fullmatch(commit) is None
        or FULL_REVISION_RE.fullmatch(revision) is None
        or not revision.startswith(commit)
        or version != build_version(commit)
    ):
        raise ValueError("invalid immutable release source identity")
    source_identity = {
        "release_source_commit": commit,
        "release_source_metadata_path": RELEASE_SOURCE_METADATA_PATH,
        "release_source_revision": revision,
        "version": version,
    }
    canonical = json.dumps(
        source_identity,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return {
        "version": version,
        "release_source_commit": commit,
        "release_source_revision": revision,
        "release_source_metadata_path": RELEASE_SOURCE_METADATA_PATH,
        "release_source_metadata_sha256": hashlib.sha256(canonical).hexdigest(),
    }


def stamp_version_json(
    path: Path,
    version: str,
    commit: str,
    revision: str,
    *,
    dry_run: bool = False,
) -> bool:
    """Write closed release provenance metadata. Returns True if changed."""
    new_data = build_release_metadata(version, commit, revision)

    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing == new_data:
                return False
        except json.JSONDecodeError:
            pass

    if dry_run:
        return True

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(new_data, indent=2) + "\n", encoding="utf-8")
    return True


def stamp_app_js(path: Path, version: str, *, dry_run: bool = False) -> bool:
    """Update CLIENT_APP_VERSION in app.js. Returns True if changed."""
    if not path.exists():
        return False

    text = path.read_text(encoding="utf-8")
    pattern = r'const CLIENT_APP_VERSION = ["\'][^"\']+["\'];'
    replacement = f'const CLIENT_APP_VERSION = "{version}";'

    if re.search(pattern, text) is None:
        return False

    new_text = re.sub(pattern, replacement, text)
    if new_text == text:
        return False

    if dry_run:
        return True

    path.write_text(new_text, encoding="utf-8")
    return True


def stamp_sw_js(path: Path, version: str, *, dry_run: bool = False) -> bool:
    """Update CACHE_VERSION in sw.js. Returns True if changed."""
    if not path.exists():
        return False

    text = path.read_text(encoding="utf-8")
    pattern = r"const CACHE_VERSION = ['\"][^'\"]+['\"];"
    replacement = f"const CACHE_VERSION = 'v{version}';"

    if re.search(pattern, text) is None:
        return False

    new_text = re.sub(pattern, replacement, text)
    if new_text == text:
        return False

    if dry_run:
        return True

    path.write_text(new_text, encoding="utf-8")
    return True


def stamp_index_html(path: Path, version: str, commit: str, *, dry_run: bool = False) -> bool:
    """Update footer version text and cache-busting query params in index.html. Returns True if changed."""
    if not path.exists():
        return False

    text = path.read_text(encoding="utf-8")
    original = text

    # Update window.CURRENT_PAGE_VERSION in <head>
    text = re.sub(
        r'(window\.CURRENT_PAGE_VERSION\s*=\s*["\'])[^"\']+(["\'])',
        f'\\g<1>{version}\\g<2>',
        text,
    )

    # Update footer version text
    text = re.sub(
        r'(Computational Metaphysics Engine v)[\d.]+[a-f0-9]*',
        f'\\g<1>{version}',
        text,
    )

    # Cache-busting: update ?v= query params on static assets
    for asset in ["style.css", "i18n.js", "voice_engine.js", "app.js"]:
        escaped = re.escape(asset)
        text = re.sub(
            rf'({escaped}\?v=)[^"\'&\s]+',
            f'\\g<1>{commit}',
            text,
        )

    if text == original:
        return False

    if dry_run:
        return True

    path.write_text(text, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(description="Stamp git version into all local source files")
    parser.add_argument("--check", action="store_true", help="Dry-run: report mismatches only, exit 1 if any found")
    parser.add_argument(
        "--commit",
        type=str,
        default=None,
        help="Explicit source commit to resolve and stamp",
    )
    parser.add_argument("--version", type=str, default=None, help="Explicit version string (e.g. 1.0.0.abc1234)")
    args = parser.parse_args()

    revision = get_git_revision(args.commit or "HEAD")
    if revision == "unknown":
        print("❌ Cannot resolve an immutable source commit.")
        sys.exit(1)

    commit = revision[:7]
    version = args.version or build_version(commit)
    if version != build_version(commit):
        print("❌ Explicit version does not match the resolved source commit.")
        sys.exit(1)
    dry_run = args.check

    print(
        f"{'🔍 Checking' if dry_run else '📌 Stamping'} version: "
        f"{version} (source: {revision})"
    )

    targets = {
        "version.json": [
            ROOT / "project" / "static" / "version.json",
            ROOT / "public" / "version.json",
        ],
        "app.js": [
            ROOT / "project" / "static" / "app.js",
            ROOT / "public" / "app.js",
        ],
        "sw.js": [
            ROOT / "project" / "static" / "sw.js",
            ROOT / "public" / "sw.js",
        ],
        "index.html": [
            ROOT / "project" / "static" / "index.html",
            ROOT / "public" / "index.html",
        ],
    }

    any_changed = False
    results = []

    for file_type, paths in targets.items():
        for path in paths:
            rel = path.relative_to(ROOT)
            if file_type == "version.json":
                changed = stamp_version_json(
                    path,
                    version,
                    commit,
                    revision,
                    dry_run=dry_run,
                )
            elif file_type == "app.js":
                changed = stamp_app_js(path, version, dry_run=dry_run)
            elif file_type == "sw.js":
                changed = stamp_sw_js(path, version, dry_run=dry_run)
            elif file_type == "index.html":
                changed = stamp_index_html(path, version, commit, dry_run=dry_run)
            else:
                changed = False

            status = "⚠️  STALE" if changed else "✅ OK"
            if not path.exists():
                status = "⏭️  SKIP (not found)"
            results.append((str(rel), status))
            if changed:
                any_changed = True

    print()
    print("=" * 60)
    print(f"  VERSION STAMP {'CHECK' if dry_run else 'RESULT'}")
    print("=" * 60)
    for rel, status in results:
        print(f"  {status:20s}  {rel}")
    print("=" * 60)

    if dry_run:
        if any_changed:
            print("\n⚠️  Some files need stamping. Run: python3 scripts/stamp_version.py")
            sys.exit(1)
        else:
            print(f"\n✅ All files are up to date with commit {commit}")
            sys.exit(0)
    else:
        if any_changed:
            print(f"\n✅ Stamped all files with version {version}")
        else:
            print(f"\n✅ All files already up to date with commit {commit}")
        sys.exit(0)


if __name__ == "__main__":
    main()
