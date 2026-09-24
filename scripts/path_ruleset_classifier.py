#!/usr/bin/env python3
"""Path-based ruleset classifier and CI tiering engine (KAN-100).

Classifies repository changes into operational tiers:
- TIER_LIGHT: Docs, markdown, workflows, and governance metadata.
  Requires Secret Scan and Test Provenance. Skips Rust build and heavy PyTest suite.
- TIER_STRICT: Source code (project/, rust_core/, api/, scripts/, tests/, dependencies).
  Requires all verification gates (Rust audit, PyTest suite, E2E regression, Security, Provenance).

Fail-closed: Any unrecognized file or path defaults to TIER_STRICT.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Sequence

TIER_LIGHT = "LIGHT"
TIER_STRICT = "STRICT"

# Files and prefixes that qualify as lightweight (docs, workflows, metadata)
LIGHT_PREFIXES = (
    "docs/",
    ".github/workflows/",
    "governance/",
    ".hermes/skills/",
    "plans/docs/",
)

LIGHT_EXACT_FILES = {
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    "LICENSE",
    "SUMMARY.md",
    "README.md",
    "HOWTO.md",
    "version.json",
}


@dataclasses.dataclass(frozen=True)
class ClassificationResult:
    tier: str
    has_source_changes: bool
    run_security_audit: bool
    run_provenance_check: bool
    run_rust_audit: bool
    run_heavy_pytest: bool
    material_files: tuple[str, ...] = ()
    docs_files: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "tier": self.tier,
            "has_source_changes": self.has_source_changes,
            "run_security_audit": self.run_security_audit,
            "run_provenance_check": self.run_provenance_check,
            "run_rust_audit": self.run_rust_audit,
            "run_heavy_pytest": self.run_heavy_pytest,
            "material_files": list(self.material_files),
            "docs_files": list(self.docs_files),
        }


def tier_policy(tier: str) -> ClassificationResult:
    """Return the governance gate policy for a given tier."""
    if tier == TIER_LIGHT:
        return ClassificationResult(
            tier=TIER_LIGHT,
            has_source_changes=False,
            run_security_audit=True,
            run_provenance_check=True,
            run_rust_audit=False,
            run_heavy_pytest=False,
        )
    return ClassificationResult(
        tier=TIER_STRICT,
        has_source_changes=True,
        run_security_audit=True,
        run_provenance_check=True,
        run_rust_audit=True,
        run_heavy_pytest=True,
    )


def is_light_path(path: str) -> bool:
    """Determine if a single path qualifies for the lightweight tier."""
    norm = path.strip().replace("\\", "/")
    while norm.startswith("./"):
        norm = norm[2:]

    if not norm:
        return True

    # Any markdown file anywhere in the repo is lightweight
    if norm.endswith(".md"):
        return True

    # Exact known metadata files
    if norm in LIGHT_EXACT_FILES:
        return True

    # Prefixes for docs, workflows, governance
    if any(norm.startswith(prefix) for prefix in LIGHT_PREFIXES):
        return True

    return False


def classify_paths(paths: Iterable[str]) -> ClassificationResult:
    """Classify a collection of file paths into TIER_LIGHT or TIER_STRICT.
    
    Fail-closed: If ANY path is not recognized as light, tier is TIER_STRICT.
    """
    material: list[str] = []
    docs: list[str] = []

    for raw in paths:
        norm = raw.strip().replace("\\", "/")
        while norm.startswith("./"):
            norm = norm[2:]
        if not norm:
            continue

        if is_light_path(norm):
            docs.append(norm)
        else:
            material.append(norm)

    if material:
        return ClassificationResult(
            tier=TIER_STRICT,
            has_source_changes=True,
            run_security_audit=True,
            run_provenance_check=True,
            run_rust_audit=True,
            run_heavy_pytest=True,
            material_files=tuple(material),
            docs_files=tuple(docs),
        )

    return ClassificationResult(
        tier=TIER_LIGHT,
        has_source_changes=False,
        run_security_audit=True,
        run_provenance_check=True,
        run_rust_audit=False,
        run_heavy_pytest=False,
        material_files=(),
        docs_files=tuple(docs),
    )


def get_git_diff_paths(base: str, head: str, cwd: Path | None = None) -> list[str]:
    """Retrieve changed file paths between two Git revisions."""
    try:
        res = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...{head}"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return [p.strip() for p in res.stdout.splitlines() if p.strip()]
    except subprocess.CalledProcessError:
        # Fallback to direct two-dot diff
        res = subprocess.run(
            ["git", "diff", "--name-only", base, head],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return [p.strip() for p in res.stdout.splitlines() if p.strip()]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify PR changed paths into CI tiers.")
    parser.add_argument("--files", nargs="*", help="Explicit list of changed files.")
    parser.add_argument("--base", help="Git base commit or ref.")
    parser.add_argument("--head", help="Git head commit or ref.")
    parser.add_argument("--json", action="store_true", help="Output JSON result.")
    parser.add_argument("--github-output", action="store_true", help="Output GitHub Actions step outputs.")

    args = parser.parse_args(argv)

    paths: list[str] = []
    if args.files is not None:
        paths = args.files
    elif args.base and args.head:
        paths = get_git_diff_paths(args.base, args.head)
    else:
        # Default: unstaged + staged + uncommitted against HEAD
        try:
            res = subprocess.run(["git", "diff", "--name-only", "HEAD"], capture_output=True, text=True, check=True)
            paths = [p.strip() for p in res.stdout.splitlines() if p.strip()]
        except Exception:
            paths = []

    result = classify_paths(paths)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return 0

    if args.github_output:
        lines = [
            f"tier={result.tier}",
            f"has_source_changes={'true' if result.has_source_changes else 'false'}",
            f"run_security_audit={'true' if result.run_security_audit else 'false'}",
            f"run_provenance_check={'true' if result.run_provenance_check else 'false'}",
            f"run_rust_audit={'true' if result.run_rust_audit else 'false'}",
            f"run_heavy_pytest={'true' if result.run_heavy_pytest else 'false'}",
        ]
        gh_output_path = os.environ.get("GITHUB_OUTPUT")
        if gh_output_path and os.path.exists(gh_output_path):
            with open(gh_output_path, "a", encoding="utf-8") as f:
                for line in lines:
                    f.write(f"{line}\n")
        for line in lines:
            print(line)
        return 0

    print(f"Tier: {result.tier} (has_source_changes={result.has_source_changes})")
    print(f"  Security Audit:    {'REQUIRED' if result.run_security_audit else 'SKIPPED'}")
    print(f"  Provenance Check:  {'REQUIRED' if result.run_provenance_check else 'SKIPPED'}")
    print(f"  Rust Core Audit:   {'REQUIRED' if result.run_rust_audit else 'SKIPPED'}")
    print(f"  Heavy PyTest:      {'REQUIRED' if result.run_heavy_pytest else 'SKIPPED'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
