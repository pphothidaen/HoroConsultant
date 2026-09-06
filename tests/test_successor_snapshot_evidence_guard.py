"""Public contract for evidence integrity only, never TDD or release admission.

All evidence is synthetic and lives in tmp_path. Git operations are confined to
that disposable repository; no real historical evidence is rewritten. The CLI
uses independently supplied parent/HEAD and an external receipt (not a self-hash).
Receipt freshness is evaluated against an explicit --now for deterministic QA.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts/successor_snapshot_evidence_guard.py"
SCHEMA = ROOT / ".agents/schemas/successor-snapshot-evidence-v1.schema.json"
NOW = "2026-09-05T16:30:00Z"
FLAGS = (
    "historical_combined_compliance", "combined_test_baseline_verified",
    "successor_verified", "source_admission", "commit_authorized",
    "successor_commit_authorized", "release_authorized",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def git(repo: Path, *args: str) -> str:
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_AUTHOR_DATE="2026-09-05T16:00:00Z",
               GIT_COMMITTER_DATE="2026-09-05T16:00:00Z")
    # Never inherit a caller's index/worktree overrides into the disposable repo.
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(key, None)
    result = subprocess.run(["git", "-C", str(repo), *args], env=env,
                            text=True, capture_output=True, check=True)
    return result.stdout.strip()


@pytest.fixture
def evidence(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Snapshot Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    paths = ["scripts/engine.py", ".agents/config.json",
             "plans/test_provenance/predecessor.json"]
    paths += [f"tests/case_{i:02}.py" for i in range(36)]
    for index, name in enumerate(paths):
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"fixture {index}\n")
    git(repo, "add", "--", *paths)
    git(repo, "-c", "core.hooksPath=/dev/null", "commit", "-qm", "fixture parent")
    head = git(repo, "rev-parse", "HEAD")
    old_hashes = {p: sha((repo / p).read_bytes()) for p in paths}
    changed = paths[-1]
    (repo / changed).write_text("prospectively adopted existing test bytes\n")
    patch_hash = sha(subprocess.run(
        ["git", "-C", str(repo), "diff", "--binary", "HEAD", "--", changed],
        capture_output=True, check=True).stdout)
    inventory = [{"path": p, "sha256": sha((repo / p).read_bytes()),
                  "head_sha256": old_hashes[p], "changed_against_head": p == changed,
                  "classification": "NON_TDD_RECONSTRUCTED"} for p in paths]
    snapshot = [{"path": row["path"], "sha256": row["sha256"],
                 "kind": "source" if row["path"].startswith("scripts/") else
                         "config" if row["path"].startswith(".agents/") else
                         "test" if row["path"].startswith("tests/") else "evidence"}
                for row in inventory]
    manifest = {
        "schema_version": "successor-snapshot-evidence-v1",
        "ticket_id": "TICKET-SNAPSHOT-FIXTURE-001", "parent_ticket_id": "TICKET-META-008",
        "baseline_parent": head, "observed_head": head,
        "provenance_status": "NON_TDD_RECONSTRUCTED", "disposition": "BLOCKED",
        "inventory_path_count": 39, "candidate_inventory": inventory,
        "actual_proposed_commit_delta": {
            "against_head": head,
            "inventory_delta": [{"path": changed, "change": "M",
                                 "sha256": inventory[-1]["sha256"]}],
            "changed_path_allowlist": [changed],
        },
        "source_config_test_snapshot": {"name": "fixture-adoption-snapshot", "files": snapshot},
        "predecessors": [{"path": paths[2], "sha256": old_hashes[paths[2]], "commit": head}],
        "ownership_transfer": {
            "path": changed, "former_owner": "fixture-former-owner", "prospective_owner": "qa_tester",
            "parent_accepted": True, "scope": "inventory/freeze/evidence only; no test edits",
            "classification": "NON_TDD_RECONSTRUCTED", "authorship": "UNVERIFIED",
            "worktree_sha256": inventory[-1]["sha256"], "head_sha256": old_hashes[changed],
            "diff_sha256": patch_hash, "reachable_commit": None,
        },
        "acceptance_gates": {"canonical_sync": "FAILED", "codex3_remediation": "PENDING",
                             "isolated_nine_file_qa": "FAILED", "combined_nine_file_qa": "FAILED",
                             "independent_review": "PENDING"},
        "flags": dict.fromkeys(FLAGS, False),
    }
    manifest_path = repo / "snapshot.json"
    receipt_path = tmp_path / "receipt.json"
    receipt = {
        "schema_version": "successor-snapshot-receipt-v1",
        "manifest_path": "snapshot.json", "manifest_sha256": "",
        "ticket_id": manifest["ticket_id"], "baseline_parent": head, "observed_head": head,
        "inventory_paths": paths, "snapshot_name": "fixture-adoption-snapshot",
        "observed_at": "2026-09-05T16:29:30Z", "expires_at": "2026-09-05T16:31:00Z",
    }
    value = dict(repo=repo, manifest=manifest, receipt=receipt, manifest_path=manifest_path,
                 receipt_path=receipt_path, head=head, paths=paths, changed=changed)
    persist(value)
    return value


def persist(value, *, bind=True):
    write_json(value["manifest_path"], value["manifest"])
    if bind:
        value["receipt"]["manifest_sha256"] = sha(value["manifest_path"].read_bytes())
    write_json(value["receipt_path"], value["receipt"])


def run_guard(value):
    assert GUARD.is_file(), "SNAPSHOT_VALIDATOR_MISSING: required standalone evidence CLI"
    result = subprocess.run(
        [sys.executable, str(GUARD), "verify", "--repo", str(value["repo"]),
         "--manifest", str(value["manifest_path"]), "--receipt", str(value["receipt_path"]),
         "--expected-parent", value["head"], "--expected-head", value["head"], "--now", NOW],
        text=True, capture_output=True, timeout=30,
    )
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"CLI must emit JSON, exit={result.returncode}: {result.stdout!r} {result.stderr!r}")
    assert isinstance(report, dict)
    assert report["provenance_status"] == "NON_TDD_RECONSTRUCTED"
    assert report["acceptance_status"] == "BLOCKED"
    assert report["flags"] == dict.fromkeys(FLAGS, False)
    return result, report


def assert_rejected(value):
    result, report = run_guard(value)
    assert result.returncode != 0
    assert report["integrity_status"] == "FAILED"
    assert report["issues"], "invalid evidence needs actionable diagnostic issues"


def test_valid_blocked_adoption_is_integrity_only_and_read_only(evidence):
    def state():
        return {str(p.relative_to(evidence["repo"])): sha(p.read_bytes())
                for p in evidence["repo"].rglob("*") if p.is_file()}
    before = state()
    receipt_before = evidence["receipt_path"].read_bytes()
    first, report = run_guard(evidence)
    second, _ = run_guard(evidence)
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout, "fixed input and clock must produce deterministic JSON"
    assert report["integrity_status"] == "PASSED"
    assert report["inventory_path_count"] == 39
    assert report["actual_delta_path_count"] == 1
    assert report["issues"] == []
    assert state() == before
    assert evidence["receipt_path"].read_bytes() == receipt_before


@pytest.mark.parametrize("gate", ["canonical_sync", "codex3_remediation", "isolated_nine_file_qa",
                                  "combined_nine_file_qa", "independent_review"])
def test_each_unmet_gate_preserves_blocked_acceptance(evidence, gate):
    gates = evidence["manifest"]["acceptance_gates"]
    gates.update(dict.fromkeys(gates, "PASSED"))
    gates[gate] = "PENDING"
    persist(evidence)
    result, report = run_guard(evidence)
    assert result.returncode == 0
    assert report["integrity_status"] == "PASSED"


@pytest.mark.parametrize("case", [
    "hash_tamper", "missing_file", "missing_inventory", "extra_inventory", "duplicate_path",
    "wrong_parent", "wrong_head", "delta_anchor", "unauthorized_delta", "delta_omitted",
    "inventory_is_not_delta", "changed_flag_lie", "head_hash_lie", "snapshot_tamper",
    "snapshot_missing_source", "snapshot_missing_config", "snapshot_missing_test",
    "predecessor_hash", "predecessor_commit", "ownership_missing", "ownership_not_accepted",
    "ownership_patch_hash", "ownership_file_hash", "reachable_history_claim",
    "promotion", "per_path_promotion", "ownership_promotion", "self_hash", "unknown_key",
    "receipt_stale", "receipt_future", "receipt_hash", "receipt_path", "receipt_head",
    "receipt_parent", "receipt_ticket", "receipt_snapshot", "receipt_inventory", "receipt_missing",
])
def test_invalid_evidence_fails_closed(evidence, case):
    m, r = evidence["manifest"], evidence["receipt"]
    rows = m["candidate_inventory"]
    delta = m["actual_proposed_commit_delta"]
    if case == "hash_tamper":
        (evidence["repo"] / evidence["paths"][0]).write_text("tampered\n")
    elif case == "missing_file": (evidence["repo"] / evidence["paths"][0]).unlink()
    elif case == "missing_inventory": rows.pop()
    elif case == "extra_inventory": rows.append(dict(rows[0], path="tests/extra.py"))
    elif case == "duplicate_path": rows[-1] = copy.deepcopy(rows[0])
    elif case == "wrong_parent": m["baseline_parent"] = "0" * 40
    elif case == "wrong_head": m["observed_head"] = "0" * 40
    elif case == "delta_anchor": delta["against_head"] = "0" * 40
    elif case == "unauthorized_delta": delta["changed_path_allowlist"] = []
    elif case == "delta_omitted": delta["inventory_delta"] = []
    elif case == "inventory_is_not_delta":
        delta["inventory_delta"].append({"path": rows[0]["path"], "change": "M", "sha256": rows[0]["sha256"]})
        delta["changed_path_allowlist"].append(rows[0]["path"])
    elif case == "changed_flag_lie": rows[0]["changed_against_head"] = True
    elif case == "head_hash_lie": rows[0]["head_sha256"] = "0" * 64
    elif case == "snapshot_tamper": m["source_config_test_snapshot"]["files"][0]["sha256"] = "0" * 64
    elif case.startswith("snapshot_missing_"):
        kind = case.removeprefix("snapshot_missing_")
        files = m["source_config_test_snapshot"]["files"]
        m["source_config_test_snapshot"]["files"] = [f for f in files if f["kind"] != kind]
    elif case == "predecessor_hash": m["predecessors"][0]["sha256"] = "0" * 64
    elif case == "predecessor_commit": m["predecessors"][0]["commit"] = "0" * 40
    elif case == "ownership_missing": del m["ownership_transfer"]
    elif case == "ownership_not_accepted": m["ownership_transfer"]["parent_accepted"] = False
    elif case == "ownership_patch_hash": m["ownership_transfer"]["diff_sha256"] = "0" * 64
    elif case == "ownership_file_hash": m["ownership_transfer"]["worktree_sha256"] = "0" * 64
    elif case == "reachable_history_claim": m["ownership_transfer"]["reachable_commit"] = evidence["head"]
    elif case == "promotion": m["provenance_status"] = "VERIFIED"
    elif case == "per_path_promotion": rows[0]["classification"] = "VERIFIED"
    elif case == "ownership_promotion": m["ownership_transfer"]["classification"] = "VERIFIED"
    elif case == "self_hash": m["manifest_sha256"] = sha(evidence["manifest_path"].read_bytes())
    elif case == "unknown_key": m["unexpected"] = True
    elif case == "receipt_stale": r["expires_at"] = "2026-09-05T16:29:59Z"
    elif case == "receipt_future": r["observed_at"] = "2026-09-05T16:30:01Z"
    elif case == "receipt_hash": r["manifest_sha256"] = "0" * 64
    elif case == "receipt_path": r["manifest_path"] = "other.json"
    elif case == "receipt_head": r["observed_head"] = "0" * 40
    elif case == "receipt_parent": r["baseline_parent"] = "0" * 40
    elif case == "receipt_ticket": r["ticket_id"] = "TICKET-OTHER-001"
    elif case == "receipt_snapshot": r["snapshot_name"] = "different-snapshot"
    elif case == "receipt_inventory": r["inventory_paths"][-1] = "tests/other.py"
    elif case == "receipt_missing": pass
    else: raise AssertionError(f"unhandled test case {case}")
    persist(evidence, bind=case != "receipt_hash")
    if case == "receipt_missing": evidence["receipt_path"].unlink()
    assert_rejected(evidence)


@pytest.mark.parametrize("flag", FLAGS)
def test_no_true_admission_flags_are_accepted(evidence, flag):
    evidence["manifest"]["flags"][flag] = True
    persist(evidence)
    assert_rejected(evidence)


@pytest.mark.parametrize("unsafe", ["../escape.py", "/tmp/escape.py", "tests/../escape.py",
                                   "tests\\escape.py", "./tests/escape.py"])
def test_inventory_paths_must_be_safe_and_canonical(evidence, unsafe):
    evidence["manifest"]["candidate_inventory"][0]["path"] = unsafe
    persist(evidence)
    assert_rejected(evidence)


def test_manifest_mutation_invalidates_unmodified_external_receipt(evidence):
    evidence["manifest"]["source_config_test_snapshot"]["name"] = "new-name"
    persist(evidence, bind=False)
    assert_rejected(evidence)


@pytest.mark.parametrize("target", ["manifest_path", "receipt_path"])
def test_malformed_json_is_a_structured_failure(evidence, target):
    evidence[target].write_text("{invalid json")
    assert_rejected(evidence)


def test_symlink_cannot_substitute_snapshot_bytes(evidence, tmp_path):
    target = evidence["repo"] / evidence["paths"][0]
    outside = tmp_path / "outside.py"
    outside.write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(outside)
    assert_rejected(evidence)


def test_schema_is_valid_closed_and_accepts_blocked_fixture(evidence):
    assert SCHEMA.is_file(), "SNAPSHOT_SCHEMA_MISSING: required closed evidence schema"
    schema = json.loads(SCHEMA.read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema)
    assert list(validator.iter_errors(evidence["manifest"])) == []
    for field, value in [("unexpected", True), ("provenance_status", "VERIFIED"),
                         ("schema_version", "test-provenance-v1")]:
        invalid = copy.deepcopy(evidence["manifest"])
        invalid[field] = value
        assert list(validator.iter_errors(invalid)), field
    for key in evidence["manifest"]:
        invalid = copy.deepcopy(evidence["manifest"])
        del invalid[key]
        assert list(validator.iter_errors(invalid)), f"required field {key}"
    for field in FLAGS:
        invalid = copy.deepcopy(evidence["manifest"])
        invalid["flags"][field] = True
        assert list(validator.iter_errors(invalid)), field
