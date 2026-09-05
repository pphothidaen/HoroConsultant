"""Governance metadata extends shape only; Git provenance stays authoritative."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("governance_guard_under_test", ROOT / "scripts/test_provenance_guard.py")
assert SPEC and SPEC.loader
GUARD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GUARD
SPEC.loader.exec_module(GUARD)
SUPPORTED = (
    "authority_documents", "baseline_state", "canonical_role_json_owner",
    "canonical_role_json_snapshot", "captured_at", "combined_baseline_paths",
    "context_scope_partition", "disjointness_map", "eval_expectation_fixtures",
    "exact_path_count", "interrupted_fingerprints", "manifest_closure",
    "preexisting_uncommitted_entries", "prospective_sources", "provenance_type",
    "quota_observations", "red_runs", "risks", "source_admission", "task_b_status",
    "updated_at", "user_authorizations", "user_exclusions", "worktree_boundary",
)


def manifest():
    return {
        "schema_version": "test-provenance-v1", "ticket_id": "TICKET-EXTENSION-001",
        "sequence": 1, "provenance_status": "VERIFIED", "baseline_parent": "a" * 40,
        "test_files": [{"path": "tests/test_contract.py", "sha256": "b" * 64}],
        "red_tests": [{"command": ["python3", "-m", "pytest", "tests/test_contract.py"],
                       "expected_exit": 1, "failure_fingerprint": "missing behavior"}],
        "allowed_source_paths": ["src/app.py"], "test_owner_role": "qa_tester",
        "reviewer_role": "code_reviewer", "supersedes": None, "correction_reason": None,
        "rationale": "fixture contract",
    }


def issues(payload):
    report = GUARD.Report(command="shape")
    GUARD._validate_manifest_shape(payload, report)
    return {issue["code"] for issue in report.issues}


@pytest.mark.parametrize("key", SUPPORTED)
def test_supported_governance_metadata_does_not_invalidate_contract(key):
    payload = manifest()
    payload[key] = {"context": "annotation, not authorization"}
    assert issues(payload) == set()


def test_unknown_metadata_remains_closed_even_with_supported_fields():
    payload = manifest()
    payload.update({key: {} for key in SUPPORTED})
    payload["unreviewed_policy_override"] = True
    assert "MANIFEST_SCHEMA_MISMATCH" in issues(payload)


@pytest.mark.parametrize("key", tuple(manifest()))
def test_metadata_cannot_replace_missing_required_fields(key):
    payload = manifest()
    payload.update({name: {} for name in SUPPORTED})
    del payload[key]
    assert "MANIFEST_SCHEMA_MISMATCH" in issues(payload)


@pytest.mark.parametrize("key,bad,expected", [
    ("sequence", True, "MANIFEST_SEQUENCE_INVALID"),
    ("baseline_parent", "main", "MANIFEST_PARENT_INVALID"),
    ("test_files", [{"path": "../escape.py", "sha256": "b" * 64}], "MANIFEST_TEST_PATH_INVALID"),
    ("test_files", [{"path": "tests/test_contract.py", "sha256": "invalid"}], "MANIFEST_TEST_HASH_INVALID"),
    ("red_tests", [{"command": [], "expected_exit": 1, "failure_fingerprint": "missing"}], "MANIFEST_RED_TEST_INVALID"),
])
def test_metadata_does_not_weaken_required_field_validation(key, bad, expected):
    payload = manifest()
    payload["source_admission"] = True
    payload[key] = bad
    assert expected in issues(payload)


def git(repo, *args):
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


@pytest.mark.parametrize("fault,expected", [
    ("none", None), ("test_hash", "TEST_HASH_MISMATCH"),
    ("parent", "BASELINE_PARENT_MISMATCH"),
    ("source_path", "SOURCE_PATH_OUTSIDE_MANIFEST"),
])
def test_metadata_cannot_bypass_real_git_hash_history_or_source_scope(tmp_path, fault, expected):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "qa@example.invalid")
    git(repo, "config", "user.name", "QA Fixture")
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("VALUE = 0\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "fixture parent")
    parent = git(repo, "rev-parse", "HEAD")
    (repo / "tests").mkdir()
    test = repo / "tests/test_contract.py"
    test.write_text("def test_contract():\n    assert False\n")
    payload = manifest()
    payload["baseline_parent"] = "0" * 40 if fault == "parent" else parent
    payload["test_files"][0]["sha256"] = hashlib.sha256(test.read_bytes()).hexdigest()
    payload.update({"source_admission": True, "baseline_state": "claimed verified", "authority_documents": {"override": True}})
    path = "plans/test_provenance/fixture.json"
    target = repo / path
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(payload))
    git(repo, "add", ".")
    git(repo, "commit", "-m", "test: baseline")
    baseline = git(repo, "rev-parse", "HEAD")
    if fault == "test_hash":
        test.write_text("def test_contract():\n    assert True\n")
    else:
        output = repo / ("src/other.py" if fault == "source_path" else "src/app.py")
        output.write_text("VALUE = 1\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "source fixture\n\nTest-Baseline: " + baseline)
    report = GUARD.verify_history(repo, path, head_revision="HEAD", baseline_revision=baseline, include_worktree=False)
    codes = {issue["code"] for issue in report.issues}
    if expected is None:
        assert codes == set(), report.issues
    else:
        assert expected in codes, report.issues
