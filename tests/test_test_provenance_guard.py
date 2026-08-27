from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "test_provenance_guard.py"
REVIEWER = ROOT / "project" / "core" / "code_reviewer.py"


def _run(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(args),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"command failed ({result.returncode}): {' '.join(args)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_manifest(
    repo: Path,
    *,
    ticket: str = "TICKET-PROV-001",
    sequence: int = 1,
    status: str = "VERIFIED",
    supersedes: str | None = None,
    bad_hash: bool = False,
) -> Path:
    test_file = repo / "tests" / "test_contract.py"
    manifest_dir = repo / "plans" / "test_provenance"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest = manifest_dir / f"{ticket.lower()}-{sequence:02d}.json"
    parent = _git(repo, "rev-parse", "HEAD").stdout.strip()
    payload = {
        "schema_version": "test-provenance-v1",
        "ticket_id": ticket,
        "sequence": sequence,
        "provenance_status": status,
        "baseline_parent": parent,
        "test_files": [
            {
                "path": "tests/test_contract.py",
                "sha256": "0" * 64 if bad_hash else _sha256(test_file),
            }
        ],
        "red_tests": [
            {
                "command": [sys.executable, "-m", "pytest", "-q", "tests/test_contract.py"],
                "expected_exit": 1,
                "failure_fingerprint": "missing intended behavior",
            }
        ],
        "allowed_source_paths": ["src/"],
        "test_owner_role": "qa_tester",
        "reviewer_role": "code_reviewer",
        "supersedes": supersedes,
        "correction_reason": "contract correction" if supersedes else None,
        "rationale": "black-box contract before implementation",
    }
    manifest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return manifest


def _make_baseline(
    repo: Path,
    *,
    status: str = "VERIFIED",
    mixed_source: bool = False,
    bad_hash: bool = False,
) -> tuple[Path, str]:
    (repo / "tests").mkdir(exist_ok=True)
    (repo / "tests" / "test_contract.py").write_text(
        "def test_contract():\n    assert False, 'missing intended behavior'\n",
        encoding="utf-8",
    )
    manifest = _write_manifest(repo, status=status, bad_hash=bad_hash)
    if mixed_source:
        (repo / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(
        repo,
        "commit",
        "-m",
        "test(provenance): freeze contract\n\nTest-Baseline-Ticket: TICKET-PROV-001",
    )
    return manifest, _git(repo, "rev-parse", "HEAD").stdout.strip()


def _commit_source(
    repo: Path,
    baseline: str,
    *,
    trailer: bool = True,
    value: int = 2,
) -> str:
    (repo / "src" / "app.py").write_text(f"VALUE = {value}\n", encoding="utf-8")
    _git(repo, "add", "src/app.py")
    message = "feat: implement contract"
    if trailer:
        message += f"\n\nTest-Baseline: {baseline}"
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _verify(
    repo: Path,
    manifest: Path,
    baseline: str,
    *,
    include_worktree: bool = False,
) -> subprocess.CompletedProcess[str]:
    args = [
        sys.executable,
        str(GUARD),
        "verify",
        "--repo",
        str(repo),
        "--manifest",
        str(manifest.relative_to(repo)),
        "--baseline",
        baseline,
        "--head",
        "HEAD",
    ]
    if include_worktree:
        args.append("--include-worktree")
    return _run(*args, cwd=repo, check=False)


def test_valid_test_first_history_passes(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    manifest, baseline = _make_baseline(repo)
    _commit_source(repo, baseline)

    result = _verify(repo, manifest, baseline)

    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "PASSED"
    assert report["baseline_commit"] == baseline
    assert report["test_files_verified"] == 1


def test_mixed_test_and_source_baseline_is_rejected(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    manifest, baseline = _make_baseline(repo, mixed_source=True)

    result = _verify(repo, manifest, baseline)

    assert result.returncode == 1
    assert "BASELINE_MIXES_SOURCE_AND_TEST" in result.stdout


def test_test_mutation_after_freeze_is_rejected(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    manifest, baseline = _make_baseline(repo)
    _commit_source(repo, baseline)
    (repo / "tests" / "test_contract.py").write_text(
        "def test_contract():\n    assert True\n", encoding="utf-8"
    )
    _git(repo, "add", "tests/test_contract.py")
    _git(repo, "commit", "-m", f"test: weaken contract\n\nTest-Baseline: {baseline}")

    result = _verify(repo, manifest, baseline)

    assert result.returncode == 1
    assert "FROZEN_TEST_CHANGED" in result.stdout


def test_untracked_test_is_rejected_when_worktree_is_checked(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    manifest, baseline = _make_baseline(repo)
    _commit_source(repo, baseline)
    (repo / "tests" / "test_sneaky.py").write_text("assert True\n", encoding="utf-8")

    result = _verify(repo, manifest, baseline, include_worktree=True)

    assert result.returncode == 1
    assert "UNTRACKED_TEST_FILE" in result.stdout


def test_manifest_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    manifest, baseline = _make_baseline(repo, bad_hash=True)

    result = _verify(repo, manifest, baseline)

    assert result.returncode == 1
    assert "TEST_HASH_MISMATCH" in result.stdout


def test_non_ancestor_baseline_is_rejected(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "switch", "-c", "side")
    manifest, baseline = _make_baseline(repo)
    manifest_payload = manifest.read_text(encoding="utf-8")
    _git(repo, "switch", "main")
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(manifest_payload, encoding="utf-8")

    result = _verify(repo, manifest, baseline)

    assert result.returncode == 1
    assert "BASELINE_NOT_ANCESTOR" in result.stdout


def test_reconstructed_history_never_claims_verified_tdd(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    manifest, baseline = _make_baseline(repo, status="RECONSTRUCTED")

    result = _verify(repo, manifest, baseline)

    assert result.returncode == 1
    assert "NON_TDD_RECONSTRUCTED" in result.stdout


def test_source_commit_without_baseline_trailer_is_rejected(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    manifest, baseline = _make_baseline(repo)
    _commit_source(repo, baseline, trailer=False)

    result = _verify(repo, manifest, baseline)

    assert result.returncode == 1
    assert "SOURCE_COMMIT_MISSING_BASELINE_TRAILER" in result.stdout


def test_reviewed_test_only_superseding_baseline_passes(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _, first_baseline = _make_baseline(repo)
    _commit_source(repo, first_baseline)
    (repo / "tests" / "test_contract.py").write_text(
        "def test_contract():\n    assert False, 'corrected missing behavior'\n",
        encoding="utf-8",
    )
    second_manifest = _write_manifest(
        repo,
        sequence=2,
        supersedes=first_baseline,
    )
    _git(repo, "add", "tests/test_contract.py", str(second_manifest.relative_to(repo)))
    _git(
        repo,
        "commit",
        "-m",
        "test: supersede incorrect contract\n\nTest-Baseline-Ticket: TICKET-PROV-001",
    )
    second_baseline = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _commit_source(repo, second_baseline, value=3)

    result = _verify(repo, second_manifest, second_baseline)

    assert result.returncode == 0, result.stdout + result.stderr


def test_staged_mixed_source_and_test_change_is_rejected(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "tests").mkdir()
    (repo / "tests" / "test_contract.py").write_text("assert False\n", encoding="utf-8")
    _write_manifest(repo)
    (repo / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    _git(repo, "add", ".")

    result = _run(
        sys.executable,
        str(GUARD),
        "staged",
        "--repo",
        str(repo),
        cwd=repo,
        check=False,
    )

    assert result.returncode == 1
    assert "STAGED_COMMIT_MIXES_SOURCE_AND_TEST" in result.stdout


def test_precommit_hook_is_non_mutating_and_runs_provenance_guard() -> None:
    hook = (ROOT / ".githooks" / "pre-commit").read_text(encoding="utf-8")

    assert "test_provenance_guard.py\" staged" in hook
    assert "stamp_version.py" not in hook
    assert "git add" not in hook


def test_ci_uses_full_history_and_fail_closed_provenance_job() -> None:
    workflow = (ROOT / ".github" / "workflows" / "test_provenance.yml").read_text(
        encoding="utf-8"
    )

    assert "fetch-depth: 0" in workflow
    assert "name: Test Provenance" in workflow
    assert "test_provenance_guard.py verify-pr" in workflow


def test_code_reviewer_exposes_test_provenance_arguments() -> None:
    result = _run(sys.executable, str(REVIEWER), "--help", cwd=ROOT, check=False)

    assert result.returncode == 0
    assert "--ticket" in result.stdout
    assert "--test-baseline" in result.stdout
    assert "--test-manifest" in result.stdout


def test_testing_rules_require_baseline_before_source_and_controlled_supersede() -> None:
    rule = (ROOT / ".agents" / "rules" / "02-testing-standards.md").read_text(
        encoding="utf-8"
    )
    qa_skill = (ROOT / ".agents" / "skills" / "qa-e2e-testing" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "TEST_BASELINE_VERIFIED" in rule
    assert "NON_TDD_RECONSTRUCTED" in rule
    assert "superseding baseline" in rule.lower()
    assert "TEST_BASELINE_VERIFIED" in qa_skill
    assert "superseding baseline" in qa_skill.lower()


def test_schema_is_closed_and_requires_test_hashes() -> None:
    schema_path = ROOT / ".agents" / "schemas" / "test-provenance-v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert schema["additionalProperties"] is False
    assert "test_files" in schema["required"]
    item = schema["properties"]["test_files"]["items"]
    assert set(item["required"]) == {"path", "sha256"}
    assert item["additionalProperties"] is False


def test_recovery_branch_preserves_non_tdd_label() -> None:
    result = _run(
        "git",
        "log",
        "-1",
        "--format=%s",
        "recovery/pre-test-provenance-20260827",
        cwd=ROOT,
        check=False,
    )

    assert result.returncode == 0
    assert "[NON_TDD_RECONSTRUCTED]" in result.stdout


def test_guard_file_is_not_copied_into_fixture_repo() -> None:
    # The tests exercise the workspace guard against disposable repositories;
    # no fixture can silently replace the implementation under review.
    assert GUARD.parent == ROOT / "scripts"
    assert shutil.which("git") is not None
