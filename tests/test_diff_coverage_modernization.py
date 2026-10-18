from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "test_provenance_guard.py"
TRAILER_SCRIPT = ROOT / "scripts" / "commit_msg_trailer.py"
GATE_SCRIPT = ROOT / "scripts" / "tdd_gate.py"

_COVERAGE_UNCOVERED = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<coverage>\n'
    '  <classes>\n'
    '    <class filename="src/app.py" line-rate="0.0">\n'
    '      <lines>\n'
    '        <line number="1" hits="0"/>\n'
    "      </lines>\n"
    "    </class>\n"
    "  </classes>\n"
    "</coverage>\n"
)

_COVERAGE_COVERED = _COVERAGE_UNCOVERED.replace('hits="0"', 'hits="1"').replace(
    'line-rate="0.0"', 'line-rate="1.0"'
)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(*args: str, cwd: Path, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), cwd=cwd, capture_output=True, text=True, check=check)


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return _run("git", *args, cwd=repo, check=check)


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "qa@example.invalid")
    _git(repo, "config", "user.name", "QA Test Owner")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    (repo / "README.md").write_text("fixture\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "chore: initial fixture")
    return repo


def _make_baseline(repo: Path) -> tuple[Path, str]:
    import hashlib

    parent = _git(repo, "rev-parse", "HEAD").stdout.strip()
    (repo / "tests").mkdir(exist_ok=True)
    test_file = repo / "tests" / "test_contract.py"
    test_file.write_text("def test_contract():\n    assert True\n", encoding="utf-8")
    manifest_dir = repo / "plans" / "test_provenance"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest = manifest_dir / "ticket-kan-285-diff-coverage-01.json"
    file_sha = hashlib.sha256(test_file.read_bytes()).hexdigest()
    payload = {
        "schema_version": "test-provenance-v1",
        "ticket_id": "TICKET-KAN-285-DIFF-COVERAGE",
        "sequence": 1,
        "provenance_status": "VERIFIED",
        "baseline_parent": parent,
        "test_files": [
            {"path": "tests/test_contract.py", "sha256": file_sha}
        ],
        "red_tests": [
            {
                "command": [sys.executable, "-m", "pytest", "-q", "tests/test_diff_coverage_modernization.py"],
                "expected_exit": 1,
                "failure_fingerprint": "unrecognized arguments: --enforce-diff-coverage",
            }
        ],
        "allowed_source_paths": ["src/"],
        "test_owner_role": "qa_tester",
        "reviewer_role": "code_reviewer",
        "supersedes": None,
        "correction_reason": None,
        "rationale": "TDD baseline for diff-coverage enforcement and provenance modernization (KAN-285).",
    }
    manifest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "test(provenance): freeze diff-coverage contracts")
    return manifest, _git(repo, "rev-parse", "HEAD").stdout.strip()


def _commit_source(repo: Path, baseline: str) -> None:
    (repo / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    _git(repo, "add", "src/app.py")
    _git(repo, "commit", "-m", f"feat(kan-285): diff-coverage enforce\n\nTest-Baseline: {baseline}")


def _verify_pr(
    repo: Path, base: str, head: str, diff_coverage: bool = False, enforce_diff_coverage: bool = False
) -> subprocess.CompletedProcess:
    args = [
        sys.executable,
        str(GUARD),
        "verify-pr",
        "--repo", str(repo),
        "--base", base,
        "--head", head,
    ]
    if diff_coverage:
        args.append("--diff-coverage")
    if enforce_diff_coverage:
        args.append("--enforce-diff-coverage")
    return _run(*args, cwd=repo, check=False)


def test_rust_core_tests_recognized_as_test_prefix():
    """Pin contract: rust_core/tests/ must be recognized as test paths by commit_msg_trailer."""
    trailer = _load_module(TRAILER_SCRIPT, "commit_msg_trailer")
    assert "rust_core/tests/" in trailer.TEST_PREFIXES
    assert trailer._is_test_path("rust_core/tests/test_installed_wheel.py") is True
    assert trailer._is_governed_path("rust_core/tests/test_installed_wheel.py") is False


def test_tdd_gate_matches_combined_manifest_and_validates_shape(tmp_path: Path):
    """Pin contract: tdd_gate must find combined ticket manifests like KAN-132 in 131-132 and fail on invalid manifest."""
    from unittest.mock import MagicMock, patch

    gate = _load_module(GATE_SCRIPT, "tdd_gate")

    p = tmp_path / "plans" / "test_provenance"
    p.mkdir(parents=True)
    # Manifest has combined filename without 'kan-132', only 'kan-131-132'
    combined_manifest = p / "ticket-kan-131-132-ci-cd-hardening.json"
    combined_manifest.write_text(json.dumps({
        "schema_version": "test-provenance-v1",
        "ticket_id": "TICKET-KAN-131-KAN-132-CI-CD-HARDENING",
        "sequence": 1,
        "provenance_status": "VERIFIED",
        "baseline_parent": "0000000000000000000000000000000000000000",
        "test_files": [{"path": "tests/test_contract.py", "sha256": "0" * 64}],
        "allowed_source_paths": ["scripts/"],
    }))

    # Corrupted manifest
    corrupted_manifest = p / "ticket-kan-999-corrupted.json"
    corrupted_manifest.write_text('{"schema_version": "test-provenance-v1", "test_files": []}')

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="All passed")
            # Should locate combined manifest when searching for KAN-132
            ok_combined, msg_combined = gate.check_green_state("KAN-132", test_target="dummy.py")
            assert ok_combined is True, f"Expected KAN-132 to match combined manifest, got: {msg_combined}"
            assert "ticket-kan-131-132-ci-cd-hardening.json" in msg_combined

            # Should fail closed on empty / corrupted test_files
            ok_corrupt, msg_corrupt = gate.check_green_state("KAN-999", test_target="dummy.py")
            assert ok_corrupt is False
            assert "empty test_files" in msg_corrupt or "invalid" in msg_corrupt.lower() or "missing" in msg_corrupt.lower()
    finally:
        os.chdir(old_cwd)


def test_diff_coverage_enforce_mode_fails_on_uncovered_line(tmp_path: Path):
    """Pin contract: --enforce-diff-coverage must fail gate (exit 1) on uncovered changed source line with file:line pointer."""
    repo = _init_repo(tmp_path)
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _git(repo, "update-ref", "refs/remotes/origin/main", base)
    _manifest, baseline = _make_baseline(repo)
    _commit_source(repo, baseline)

    (repo / "coverage.xml").write_text(_COVERAGE_UNCOVERED, encoding="utf-8")
    result = _verify_pr(repo, "origin/main", "HEAD", diff_coverage=True, enforce_diff_coverage=True)

    assert result.returncode != 0, f"Expected non-zero exit code, got {result.returncode}. stdout: {result.stdout}"
    report = json.loads(result.stdout)
    assert report["status"] == "FAILED"
    assert any(
        issue.get("code") == "DIFF_COVERAGE_UNCOVERED" and "src/app.py:1" in issue.get("message", "")
        for issue in report.get("issues", [])
    ), f"Expected DIFF_COVERAGE_UNCOVERED issue, got {report.get('issues')}"


def test_diff_coverage_enforce_mode_passes_on_covered_line(tmp_path: Path):
    """Pin contract: --enforce-diff-coverage must pass (exit 0) when all changed source lines are covered."""
    repo = _init_repo(tmp_path)
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _git(repo, "update-ref", "refs/remotes/origin/main", base)
    _manifest, baseline = _make_baseline(repo)
    _commit_source(repo, baseline)

    (repo / "coverage.xml").write_text(_COVERAGE_COVERED, encoding="utf-8")
    result = _verify_pr(repo, "origin/main", "HEAD", diff_coverage=True, enforce_diff_coverage=True)

    assert result.returncode == 0, f"Expected zero exit code, got {result.returncode}. stdout: {result.stdout}"
    report = json.loads(result.stdout)
    assert report["status"] == "PASSED"
    assert not any(issue.get("code") == "DIFF_COVERAGE_UNCOVERED" for issue in report.get("issues", []))
