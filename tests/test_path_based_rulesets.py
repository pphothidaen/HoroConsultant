"""Unit tests for path-based rulesets and CI tiering (KAN-100).

Tests:
1. Classification of changed paths into TIER_LIGHT vs TIER_STRICT.
2. Fail-closed security invariants: secret scan and test provenance required on ALL paths.
3. Heavy test execution (Rust audit, full PyTest suite) skipped for TIER_LIGHT.
4. CLI interface of scripts/path_ruleset_classifier.py (--files, --json, --github-output).
5. Network test exclusion: live-prod tests marked network and excluded from PR CI.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import pytest

from scripts import path_ruleset_classifier as prc

REPO_ROOT = Path(__file__).resolve().parents[1]


# --- Classification unit tests -----------------------------------------------


def test_classify_docs_only_paths_as_light() -> None:
    """Markdown, docs directory, workflows, and metadata are classified as TIER_LIGHT."""
    docs_paths = [
        "docs/INDEX.md",
        "docs/agent-permission-policy.md",
        "README.md",
        "HOWTO.md",
        "SUMMARY.md",
        ".github/workflows/ci.yml",
        ".github/workflows/test_provenance.yml",
        "governance/rulesets.json",
        ".gitignore",
        "LICENSE",
    ]
    result = prc.classify_paths(docs_paths)
    assert result.tier == prc.TIER_LIGHT
    assert not result.has_source_changes
    assert result.run_security_audit is True
    assert result.run_provenance_check is True
    assert result.run_rust_audit is False
    assert result.run_heavy_pytest is False


def test_classify_source_paths_as_strict() -> None:
    """Changes to project core, api, rust_core, or scripts trigger TIER_STRICT."""
    for path in [
        "project/core/engine.py",
        "project/api_router.py",
        "rust_core/src/lib.rs",
        "scripts/stamp_version.py",
        "tests/test_route_sync.py",
        "requirements.txt",
        "Dockerfile",
        "pyproject.toml",
    ]:
        result = prc.classify_paths([path])
        assert result.tier == prc.TIER_STRICT, f"Expected {path} to trigger TIER_STRICT"
        assert result.has_source_changes is True
        assert result.run_security_audit is True
        assert result.run_provenance_check is True
        assert result.run_rust_audit is True
        assert result.run_heavy_pytest is True


def test_mixed_paths_fail_closed_to_strict() -> None:
    """If a PR touches both docs and source files, it must fail closed to TIER_STRICT."""
    mixed_paths = [
        "docs/INDEX.md",
        "README.md",
        "project/main.py",
    ]
    result = prc.classify_paths(mixed_paths)
    assert result.tier == prc.TIER_STRICT
    assert result.has_source_changes is True
    assert result.run_rust_audit is True
    assert result.run_heavy_pytest is True


def test_unknown_or_suspicious_paths_fail_closed_to_strict() -> None:
    """Any unrecognized extension or path must default to TIER_STRICT (fail-closed)."""
    unknown_paths = ["random_binary.bin", "unknown_folder/foo.xyz"]
    result = prc.classify_paths(unknown_paths)
    assert result.tier == prc.TIER_STRICT
    assert result.has_source_changes is True


def test_empty_paths_default_to_light() -> None:
    """No changes default to TIER_LIGHT with no source changes."""
    result = prc.classify_paths([])
    assert result.tier == prc.TIER_LIGHT
    assert not result.has_source_changes


# --- Governance invariants ---------------------------------------------------


def test_all_tiers_require_security_and_provenance() -> None:
    """Fail-closed requirement: every merge path requires test provenance and secret audit."""
    for tier in (prc.TIER_LIGHT, prc.TIER_STRICT):
        decision = prc.tier_policy(tier)
        assert decision.run_security_audit is True, f"Tier {tier} must require security audit"
        assert decision.run_provenance_check is True, f"Tier {tier} must require provenance check"


# --- CLI behavior ------------------------------------------------------------


def test_cli_json_output() -> None:
    """CLI --json outputs valid classification JSON."""
    res = subprocess.run(
        [sys.executable, "-m", "scripts.path_ruleset_classifier", "--files", "docs/INDEX.md", "README.md", "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout)
    assert data["tier"] == "LIGHT"
    assert data["has_source_changes"] is False
    assert data["run_security_audit"] is True
    assert data["run_rust_audit"] is False


def test_cli_github_output() -> None:
    """CLI --github-output outputs key=value lines suitable for GITHUB_OUTPUT."""
    res = subprocess.run(
        [sys.executable, "-m", "scripts.path_ruleset_classifier", "--files", "project/core/engine.py", "--github-output"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    lines = dict(line.split("=", 1) for line in res.stdout.strip().splitlines() if "=" in line)
    assert lines["tier"] == "STRICT"
    assert lines["has_source_changes"] == "true"
    assert lines["run_rust_audit"] == "true"
    assert lines["run_heavy_pytest"] == "true"


# --- Network test segregation ------------------------------------------------


def test_prod_version_regression_has_network_marker() -> None:
    """Live-prod regression tests must be marked with @pytest.mark.network to allow CI exclusion."""
    test_file = REPO_ROOT / "project" / "tests" / "test_prod_version_regression.py"
    assert test_file.exists()
    content = test_file.read_text(encoding="utf-8")
    assert "@pytest.mark.network" in content, "test_prod_version_regression.py must have @pytest.mark.network"
