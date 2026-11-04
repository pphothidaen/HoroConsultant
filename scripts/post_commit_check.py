#!/usr/bin/env python3
"""
Post-commit / Post-merge verification hook — HoroConsultant SDLC.

Trigger (registered as .githooks/post-commit and post-merge):
  - Run after `git commit` (post-commit)
  - Run after `git merge` / `git pull` (post-merge)

Non-blocking read-only gate:
  - NEVER edit or stage repository files
  - Never push, tag, or deploy
  - Exit 0 = verified; non-zero = report issues (console only, no hard block)

Scope:
  1. When `docs/**/*.md` changed -> verify `docs/INDEX.md` consistency
  2. When source changed -> run doc/code drift detection (KAN-308 4D)
  3. When no docs changed -> pass with "no-doc-change" status
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parent.parent
VERIFY_INDEX = REPO_ROOT / "scripts" / "verify_doc_index.py"
DOC_SYNC = REPO_ROOT / "scripts" / "doc_sync.py"
INDEX_PATH = REPO_ROOT / "docs" / "INDEX.md"

DOC_EXT = ".md"
DOC_DIRS = ("docs", "plans", "RELEASE_NOTES.md", "plans/archive", "plans/intake")

# Paths that are documentation-only and safe to sync without test provenance
DOC_ONLY_PATHS = {"README.md", "HOWTO.md", "ATOMIC_TICKET.md", "plans/plan.md"}


def run_cmd(cmd: List[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run a command, return (returncode, stdout, stderr)."""
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd or REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "TIMEOUT"
    except Exception as exc:  # pragma: no cover
        return 1, "", str(exc)


def get_last_commit_files(limit: int = 1) -> List[str]:
    """Return list of files changed in the last `limit` commits (single commit)."""
    cmd = ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"]
    rc, out, err = run_cmd(cmd)
    if rc != 0:
        return []
    return [f for f in out.strip().splitlines() if f.strip()]


def get_diff_files(base: str, head: str) -> List[str]:
    """Return files changed between two commits."""
    cmd = ["git", "diff", "--name-only", f"{base}..{head}"]
    rc, out, err = run_cmd(cmd)
    if rc != 0:
        return []
    return [f for f in out.strip().splitlines() if f.strip()]


def is_doc_file(path: str) -> bool:
    """Return True if the path is a documentation file."""
    if not path.endswith(DOC_EXT):
        return False
    if path.startswith((".git", ".venv", "node_modules")):
        return False
    return True


def collect_doc_related_files(file_list: List[str]) -> List[str]:
    """Filter to only documentation-related files."""
    docs = []
    for f in file_list:
        if is_doc_file(f):
            docs.append(f)
    return docs


def check_index_consistency() -> tuple[bool, str]:
    """
    Verify docs/INDEX.md consistency.
    Returns (all_indexed, message).
    """
    if not INDEX_PATH.exists():
        return False, f"❌ docs/INDEX.md not found at {INDEX_PATH}"

    content = INDEX_PATH.read_text(encoding="utf-8")
    md_files = []
    for p in (REPO_ROOT / "docs").rglob("*.md"):
        if p.name == "INDEX.md":
            continue
        rel = p.relative_to(REPO_ROOT / "docs")
        md_files.append(str(rel))

    missing = [m for m in md_files if m not in content]
    if missing:
        return False, (
            f"❌ {len(missing)} document(s) not referenced in INDEX.md: "
            f"{', '.join(missing[:10])}{'...' if len(missing) > 10 else ''}"
        )
    return True, f"✅ All {len(md_files)} docs referenced in INDEX.md"


def check_doc_sync_drift() -> tuple[bool, str]:
    """
    Run doc/code drift detection (KAN-308 4D).
    """
    if not DOC_SYNC.exists():
        return False, f"❌ scripts/doc_sync.py not found at {DOC_SYNC}"

    rc, out, err = run_cmd(["python3", str(DOC_SYNC), "--root", str(REPO_ROOT), "drift"])
    if rc == 0:
        return True, "✅ Doc/code drift check PASSED"
    # If drift found, report issues (non-fatal, this is a verification hook)
    combined = f"{out}\n{err}".strip()
    return False, f"⚠️ Doc sync drift detected:\n{combined[:800]}"


def check_no_doc_change() -> tuple[bool, str]:
    """No doc changes — pass through."""
    return True, "✅ No documentation changes detected in this commit — skip doc-index check"


def main() -> int:
    """
    Main entry point.
    Determines changed files and runs appropriate checks.
    """
    print("[INFO] Post-commit/merge verification — HoroConsultant SDLC")
    print(f"[INFO] REPO_ROOT: {REPO_ROOT}")

    # Get changed files
    changed = get_last_commit_files()
    if not changed:
        print("[INFO] No changed files detected (empty commit or root).")
        return 0

    doc_related = collect_doc_related_files(changed)
    doc_changed = bool(doc_related)
    code_changed = any(not is_doc_file(f) for f in changed)

    print(f"[INFO] Changed files ({len(changed)}):")
    for f in changed:
        print(f"    - {f}")

    # Branch-poll check for push context
    branch = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"])[1].strip()
    print(f"[INFO] Branch: {branch}")

    if doc_changed:
        print(f"[INFO] Documentation files changed ({len(doc_related)}): {', '.join(doc_related[:5])}")
        all_ok, msg = check_index_consistency()
        print(f"[INFO] >>> {msg}")
        if not all_ok:
            print(f"[WARN] docs/INDEX.md consistency check FAILED — run: python3 scripts/verify_doc_index.py")
            return 1
        return 0

    if code_changed:
        print("[INFO] Source files changed — running doc/code drift check (KAN-308 4D)...")
        all_ok, msg = check_doc_sync_drift()
        print(f"[INFO] >>> {msg}")
        if not all_ok:
            print(f"[WARN] Doc/code drift detected. Review before merge to main.")
            return 1
        return 0

    return check_no_doc_change()[0]


if __name__ == "__main__":
    sys.exit(main())