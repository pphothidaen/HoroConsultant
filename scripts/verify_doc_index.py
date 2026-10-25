#!/usr/bin/env python3
"""
Verify that all docs/ .md files are referenced in docs/INDEX.md.

Exit code 0: All docs indexed.
Exit code 1: Missing references found.
"""

from pathlib import Path
import sys


def main():
    docs_dir = Path("docs")
    index_path = docs_dir / "INDEX.md"

    if not index_path.exists():
        print("ERROR: docs/INDEX.md does not exist!")
        return 1

    # Collect all .md files (excluding INDEX.md itself)
    md_files = sorted([
        str(p.relative_to(docs_dir))
        for p in docs_dir.rglob("*.md")
        if p.name != "INDEX.md"
    ])

    if not md_files:
        print("No .md files found in docs/ (excluding INDEX.md)")
        return 0

    index_content = index_path.read_text(encoding="utf-8")
    missing = []

    for doc_path in md_files:
        # Check if the file path appears anywhere in INDEX.md
        if doc_path not in index_content:
            missing.append(doc_path)

    if missing:
        print(f"ERROR: {len(missing)} document(s) not referenced in INDEX.md:")
        for m in missing:
            print(f"  - docs/{m}")
        print("\nRun .github/workflows/update-index.yml or manually update INDEX.md")
        return 1
    else:
        print(f"OK: All {len(md_files)} docs are referenced in INDEX.md")
        return 0


if __name__ == "__main__":
    sys.exit(main())
