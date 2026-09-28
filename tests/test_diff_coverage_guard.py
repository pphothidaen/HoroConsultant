from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "test_provenance_guard.py"

# Cobertura coverage.xml fixtures. `src/app.py` has exactly one source line (line 1).
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


def _run(*args: str, cwd: Path, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), cwd=cwd, capture_output=True, text=True, check=check)


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return _run("git", *args, cwd=repo, check=check)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    parent = _git(repo, "rev-parse", "HEAD").stdout.strip()
    (repo / "tests").mkdir(exist_ok=True)
    # Fixture test file (the one the manifest pins). Content is irrelevant to
    # diff-coverage; verify-pr does not execute tests.
    (repo / "tests" / "test_contract.py").write_text(
        "def test_contract():\n    assert True\n", encoding="utf-8"
    )
    manifest_dir = repo / "plans" / "test_provenance"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    test_file = repo / "tests" / "test_contract.py"
    manifest = manifest_dir / "ticket-kan-133-diff-coverage-01.json"
    payload = {
        "schema_version": "test-provenance-v1",
        "ticket_id": "TICKET-KAN-133-DIFF-COVERAGE",
        "sequence": 1,
        "provenance_status": "VERIFIED",
        "baseline_parent": parent,
        "test_files": [
            {"path": "tests/test_contract.py", "sha256": _sha256(test_file)}
        ],
        "red_tests": [
            {
                "command": [sys.executable, "-m", "pytest", "-q", "tests/test_diff_coverage_guard.py"],
                "expected_exit": 1,
                "failure_fingerprint": "unrecognized arguments: --diff-coverage",
            }
        ],
        "allowed_source_paths": ["src/"],
        "test_owner_role": "qa_tester",
        "reviewer_role": "code_reviewer",
        "supersedes": None,
        "correction_reason": None,
        "rationale": "TDD baseline for --diff-coverage WARN feature (KAN-133).",
    }
    manifest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "test(provenance): freeze diff-coverage contracts")
    return manifest, _git(repo, "rev-parse", "HEAD").stdout.strip()


def _commit_source(repo: Path, baseline: str) -> None:
    (repo / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    _git(repo, "add", "src/app.py")
    _git(repo, "commit", "-m", f"feat(kan-133): diff-coverage warn\n\nTest-Baseline: {baseline}")


def _verify_pr(
    repo: Path, base: str, head: str, diff_coverage: bool = False
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
    return _run(*args, cwd=repo, check=False)


def _seed_repo(tmp_path: Path) -> tuple[Path, str, str]:
    repo = _init_repo(tmp_path)
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _git(repo, "update-ref", "refs/remotes/origin/main", base)
    _manifest, baseline = _make_baseline(repo)
    _commit_source(repo, baseline)
    return repo, base, baseline


# --- RED tests: these FAIL until --diff-coverage is implemented in the guard ---


def test_diff_coverage_reports_uncovered_changed_source_line(tmp_path: Path) -> None:
    repo, _base, baseline = _seed_repo(tmp_path)
    (repo / "coverage.xml").write_text(_COVERAGE_UNCOVERED, encoding="utf-8")  # app.py line 1 uncovered
    result = _verify_pr(repo, "origin/main", "HEAD", diff_coverage=True)
    assert result.returncode == 0, result.stdout + result.stderr  # WARN, not FAIL
    report = json.loads(result.stdout)
    assert report["status"] == "PASSED"
    assert any(
        "DIFF_COVERAGE_UNCOVERED" in n and "src/app.py:1" in n for n in report["notes"]
    ), report["notes"]


def test_diff_coverage_notes_covered_changed_line(tmp_path: Path) -> None:
    repo, _base, baseline = _seed_repo(tmp_path)
    (repo / "coverage.xml").write_text(_COVERAGE_COVERED, encoding="utf-8")  # app.py line 1 covered
    result = _verify_pr(repo, "origin/main", "HEAD", diff_coverage=True)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "PASSED"
    assert not any("DIFF_COVERAGE_UNCOVERED" in n for n in report["notes"]), report["notes"]


def test_diff_coverage_warns_when_coverage_xml_missing(tmp_path: Path) -> None:
    repo, _base, baseline = _seed_repo(tmp_path)
    result = _verify_pr(repo, "origin/main", "HEAD", diff_coverage=True)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "PASSED"
    assert any("DIFF_COVERAGE_NO_COVERAGE_XML" in n for n in report["notes"]), report["notes"]


def test_diff_coverage_is_off_by_default(tmp_path: Path) -> None:
    repo, _base, baseline = _seed_repo(tmp_path)
    (repo / "coverage.xml").write_text(_COVERAGE_UNCOVERED, encoding="utf-8")
    result = _verify_pr(repo, "origin/main", "HEAD", diff_coverage=False)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert not any("DIFF_COVERAGE" in n for n in report["notes"]), report["notes"]
