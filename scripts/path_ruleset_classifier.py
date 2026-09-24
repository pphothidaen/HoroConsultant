#!/usr/bin/env python3
"""Path-based ruleset classifier and CI tiering engine (KAN-100).

Classifies repository changes into operational tiers:
- TIER_LIGHT: Docs, markdown, workflows, and governance metadata.
  Requires Secret Scan and Test Provenance. Skips Rust build and heavy PyTest suite.
- TIER_MEDIUM: Source/test changes with known test mapping.
  Runs affected tests + security + provenance. Skips Rust audit + E2E.
- TIER_STRICT: Source code changes without test mapping, dependency changes, cross-cutting changes.
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
TIER_MEDIUM = "MEDIUM"
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

# Paths that are always STRICT (cross-cutting, dependencies, infrastructure)
STRICT_PREFIXES = (
    "requirements.txt",
    "pyproject.toml",
    "Dockerfile",
    "rust_core/",
    "api/index.js",
    "vercel.json",
    "wrangler.toml",
    ".githooks/",
    "scripts/path_ruleset_classifier.py",
    "scripts/test_provenance_guard.py",
)

# Source-to-test mapping for TIER_MEDIUM tier.
# When a source file matches a glob, the corresponding test globs are run.
# If a source file matches NO entry, the change falls back to TIER_STRICT.
#
# IMPORTANT: Keep mappings surgical. If a prefix would resolve to >20 test files,
# it is too broad — either narrow the prefix or accept TIER_STRICT for that path.
SOURCE_TEST_MAP: list[tuple[str, list[str]]] = [
    # (source_glob_prefix, [test_glob_patterns])
    ("scripts/trigger_all_github_actions.py", [
        "project/tests/test_trigger_inventory_retirement.py",
        "tests/test_trigger_inventory_retirement.py",
    ]),
    ("scripts/jira_api_helper.py", [
        "tests/test_kan122_jira_graceful_failure.py",
    ]),
    ("scripts/run_github_actions_regression.py", [
        "tests/test_github_actions_regression.py",
    ]),
    ("scripts/run_prod_version_e2e.py", [
        "project/tests/test_prod_version_regression.py",
        "project/tests/test_prod_version_e2e_release_identity.py",
    ]),
    ("scripts/run_luopan_e2e_regression.py", [
        "project/tests/test_luopan_dynamic_variance_regression.py",
        "project/tests/test_luopan_dream_engine.py",
    ]),
    ("scripts/run_cloud_architecture_regression.py", [
        "project/tests/test_cloud_architecture_overview_regression.py",
    ]),
    ("project/core/gemini_bridge.py", [
        "project/tests/test_gemini_bridge_*.py",
    ]),
    ("project/core/code_reviewer.py", [
        "project/tests/test_cicd_workflow.py",
        "project/tests/test_ai_agent_ecosystem_sync.py",
        "project/tests/test_codex_client.py",
    ]),
    ("project/routers/", [
        "project/tests/test_v3_router.py",
        "project/tests/test_v3_e2e_consultation.py",
        "tests/test_route_sync.py",
    ]),
    ("project/core/bazi_calculator.py", [
        "project/tests/test_bazi_calculator.py",
        "project/tests/test_bazi_replication.py",
    ]),
]


@dataclasses.dataclass(frozen=True)
class ClassificationResult:
    tier: str
    has_source_changes: bool
    run_security_audit: bool
    run_provenance_check: bool
    run_rust_audit: bool
    run_heavy_pytest: bool
    affected_test_globs: tuple[str, ...] = ()
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
            "affected_test_globs": list(self.affected_test_globs),
            "material_files": list(self.material_files),
            "docs_files": list(self.docs_files),
        }


def tier_policy(tier: str, affected_test_globs: tuple[str, ...] = ()) -> ClassificationResult:
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
    if tier == TIER_MEDIUM:
        return ClassificationResult(
            tier=TIER_MEDIUM,
            has_source_changes=True,
            run_security_audit=True,
            run_provenance_check=True,
            run_rust_audit=False,
            run_heavy_pytest=False,
            affected_test_globs=affected_test_globs,
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


def is_strict_path(path: str) -> bool:
    """Determine if a path is always STRICT (cross-cutting / dependency)."""
    norm = path.strip().replace("\\", "/")
    while norm.startswith("./"):
        norm = norm[2:]

    if any(norm.startswith(prefix) for prefix in STRICT_PREFIXES):
        return True
    return False


def find_test_globs_for_source(source_path: str) -> list[str] | None:
    """Return test globs that cover a source path, or None if unmapped (→ STRICT)."""
    import fnmatch

    norm = source_path.strip().replace("\\", "/")
    while norm.startswith("./"):
        norm = norm[2:]

    matched_globs: list[str] = []
    found_match = False

    for src_pattern, test_globs in SOURCE_TEST_MAP:
        # Support both exact match and glob prefix match
        if fnmatch.fnmatch(norm, src_pattern):
            found_match = True
            matched_globs.extend(test_globs)
        elif norm.startswith(src_pattern):
            found_match = True
            matched_globs.extend(test_globs)

    if found_match:
        return matched_globs
    return None  # Unmapped → STRICT (fail-closed)


def classify_paths(paths: Iterable[str]) -> ClassificationResult:
    """Classify a collection of file paths into TIER_LIGHT, TIER_MEDIUM, or TIER_STRICT.

    Fail-closed: If ANY path is not recognized as light/medium, tier is TIER_STRICT.
    """
    material: list[str] = []
    docs: list[str] = []
    all_test_globs: list[str] = []
    has_unmapped_source = False

    for raw in paths:
        norm = raw.strip().replace("\\", "/")
        while norm.startswith("./"):
            norm = norm[2:]
        if not norm:
            continue

        if is_light_path(norm):
            docs.append(norm)
            continue

        if is_strict_path(norm):
            material.append(norm)
            continue

        # Try to map source → test globs
        test_globs = find_test_globs_for_source(norm)
        if test_globs is None:
            # Unmapped source → STRICT (fail-closed)
            material.append(norm)
            has_unmapped_source = True
        else:
            material.append(norm)
            all_test_globs.extend(test_globs)

    if has_unmapped_source:
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

    if material:
        # All material paths are mapped → TIER_MEDIUM
        # Deduplicate test globs while preserving order
        seen: set[str] = set()
        unique_globs: list[str] = []
        for g in all_test_globs:
            if g not in seen:
                seen.add(g)
                unique_globs.append(g)

        return ClassificationResult(
            tier=TIER_MEDIUM,
            has_source_changes=True,
            run_security_audit=True,
            run_provenance_check=True,
            run_rust_audit=False,
            run_heavy_pytest=False,
            affected_test_globs=tuple(unique_globs),
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
    parser.add_argument("--show-affected-tests", action="store_true", help="Print resolved test file paths for TIER_MEDIUM.")

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

    # Resolve globs to actual files if requested
    resolved_tests: list[str] = []
    if args.show_affected_tests and result.affected_test_globs:
        from pathlib import Path as P
        for glob_pattern in result.affected_test_globs:
            resolved_tests.extend(str(p) for p in P(".").glob(glob_pattern) if p.is_file())

    if args.json:
        out = result.to_dict()
        if resolved_tests:
            out["resolved_test_files"] = resolved_tests
        print(json.dumps(out, indent=2))
        return 0

    if args.github_output:
        lines = [
            f"tier={result.tier}",
            f"has_source_changes={'true' if result.has_source_changes else 'false'}",
            f"run_security_audit={'true' if result.run_security_audit else 'false'}",
            f"run_provenance_check={'true' if result.run_provenance_check else 'false'}",
            f"run_rust_audit={'true' if result.run_rust_audit else 'false'}",
            f"run_heavy_pytest={'true' if result.run_heavy_pytest else 'false'}",
            f"affected_test_globs={' '.join(result.affected_test_globs)}",
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
    if result.affected_test_globs:
        print(f"  Affected Tests:    {', '.join(result.affected_test_globs)}")
    if resolved_tests:
        print(f"  Resolved Files:    {', '.join(resolved_tests)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
