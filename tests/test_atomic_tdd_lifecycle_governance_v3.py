"""Sequence-3 correction for frozen provenance-manifest tamper admission.

Sequence 2 remains the complete contract.  This file runs that immutable suite
and adds only the owner-approved dynamic post-baseline manifest mutation case.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
V1_BASELINE = "b38d5077057c3852a7e2e21af37376567231f810"
V2_BASELINE = "441a7ed3bddb27110b219df0ee1ffd58e3e547e5"
V1_TEST_SHA256 = "ce7b2c1c5e0428188dc456438bfa3df6e4bb237df92c94c3e5648947f1c86642"
V1_MANIFEST_SHA256 = "f161308ce0edbec280989cee25f3715ae82b2767fd90fe55fe012a85475ad963"
V2_TEST_SHA256 = "8ba0d5a89b3b3053f7532ae2623265777ac29de5baa0c783b8ef91d8d36f1dd7"
V2_MANIFEST_SHA256 = "cffa10368b8bc2968c031cc1f78d383cc8dab15ee7af10cc151a068aff9f2899"
V2_TEST = ROOT / "tests/test_atomic_tdd_lifecycle_governance_v2.py"
V2_MANIFEST = ROOT / "plans/test_provenance/ticket-tdd-gov-qa-017-baseline.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_object_sha256(commit: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    return hashlib.sha256(result.stdout).hexdigest()


def _load_immutable_v2() -> ModuleType:
    spec = importlib.util.spec_from_file_location("atomic_tdd_lifecycle_v2_frozen", V2_TEST)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_retained_sequence_1_and_2_artifacts_are_immutable() -> None:
    assert _git_object_sha256(V1_BASELINE, "tests/test_atomic_tdd_lifecycle_governance.py") == V1_TEST_SHA256
    assert _git_object_sha256(V1_BASELINE, "plans/test_provenance/ticket-tdd-gov-qa-010-baseline.json") == V1_MANIFEST_SHA256
    assert _git_object_sha256(V2_BASELINE, "tests/test_atomic_tdd_lifecycle_governance_v2.py") == V2_TEST_SHA256
    assert _git_object_sha256(V2_BASELINE, "plans/test_provenance/ticket-tdd-gov-qa-017-baseline.json") == V2_MANIFEST_SHA256
    assert _sha256(ROOT / "tests/test_atomic_tdd_lifecycle_governance.py") == V1_TEST_SHA256
    assert _sha256(ROOT / "plans/test_provenance/ticket-tdd-gov-qa-010-baseline.json") == V1_MANIFEST_SHA256
    assert _sha256(V2_TEST) == V2_TEST_SHA256
    assert _sha256(V2_MANIFEST) == V2_MANIFEST_SHA256


def test_immutable_v2_contract_suite_remains_mandatory() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/test_atomic_tdd_lifecycle_governance_v2.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    evidence = "\n".join((result.stdout + result.stderr).splitlines()[-30:])
    assert result.returncode == 0, f"V3_REQUIRES_IMMUTABLE_V2_GREEN\n{evidence}"


def test_post_baseline_manifest_tamper_is_rejected_dynamically(tmp_path: Path) -> None:
    v2 = _load_immutable_v2()
    repo, baseline, _ = v2._history(tmp_path)
    manifest_path = repo / "plans/test_provenance/ticket-orbit-qa-017-baseline.json"
    original = json.loads(manifest_path.read_text(encoding="utf-8"))
    original["rationale"] = "Hostile post-baseline mutation that must never be admitted."
    manifest_path.write_text(json.dumps(original, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    v2._commit(repo, "test: mutate frozen provenance manifest", baseline=baseline)

    result, payload = v2._invoke_core(repo)
    assert result.returncode != 0
    assert payload == {"decision": "deny", "reason_code": "MANIFEST_CHANGED_AFTER_BASELINE"}
