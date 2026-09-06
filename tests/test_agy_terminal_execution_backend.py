"""Backend006 public CLI: --backend-json, one request/response JSON object.

Request operation=plan is pure and must return PLANNED; operation=probe selects
one fixed provider-free program by probe_id (filesystem, deadline, streams).
No caller argv/program/shell is accepted. Response schema local-os-backend-v1
always says native_proof=false, auth_isolation=NOT_PROVEN. A real probe returns
OBSERVED only with exact observed controls and bound source/helper/program/profile
hashes; unsupported OS returns nonzero UNSUPPORTED, capability UNPROVEN, and no
verified controls. Such rejection passes an error-contract assertion, never an
OS capability gate. No skip, mocked provider, or platform proof is used.

The existing --request-json/run gate remains SANDBOX_NOT_PROVEN. These tests
create only temporary input canaries; a backend may create/remove its own child
scratch directory beneath owned_root, but must preserve original input canaries.
Separate independent QA audits real OS observations before any worker admission.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/agy_terminal_supervisor.py"
CANARY = "HARMLESS_OUTSIDE_CANARY_006"
CONTROLS = {
    "filesystem": {"owned_read", "owned_create_update_delete", "outside_read_denied", "outside_write_delete_denied"},
    "deadline": {"deadline_triggered", "owned_descendants_reaped"},
    "streams": {"output_limit_triggered", "owned_descendants_reaped"},
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(spec, switch="--backend-json"):
    child = subprocess.Popen([sys.executable, str(SOURCE), switch], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                             cwd=ROOT, start_new_session=True,
                             env={"LANG": "C", "LC_ALL": "C", "PYTHONDONTWRITEBYTECODE": "1"})
    try:
        stdout, stderr = child.communicate(json.dumps(spec), timeout=8)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        child.communicate()
        pytest.fail("BACKEND_PROTOCOL_DEADLINE_EXCEEDED")
    try:
        response = json.loads(stdout)
    except ValueError:
        pytest.fail("BACKEND_PROTOCOL_JSON_REQUIRED")
    assert response.get("native_proof") is False
    assert response.get("auth_isolation") == "NOT_PROVEN"
    if switch == "--backend-json":
        assert response.get("schema_version") == "local-os-backend-v1", "BACKEND_PROTOCOL_NOT_IMPLEMENTED"
    assert CANARY not in stdout + stderr, "OUTSIDE_CANARY_LEAKED"
    return child.returncode, response


@pytest.fixture
def spec(tmp_path):
    owned = tmp_path / "owned"
    owned.mkdir()
    (owned / "input.txt").write_text("owned input\n")
    outside = tmp_path / "outside-canary.txt"
    outside.write_text(CANARY)
    return {"operation": "plan", "probe_id": "filesystem", "session_id": "backend-006",
            "owned_root": str(owned), "owned_manifest": {"input.txt": sha(owned / "input.txt")},
            "outside_canary": str(outside), "outside_canary_sha256": sha(outside),
            "environment": {"LANG": "C", "LC_ALL": "C"},
            "limits": {"deadline_seconds": 1, "stdout_bytes": 1024, "stderr_bytes": 1024}}


def snapshot(spec):
    root = Path(spec["owned_root"])
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob("*") if p.is_file()}


def assert_binding(spec, response):
    binding = response.get("binding", {})
    assert binding.get("source_sha256") == sha(SOURCE), "BACKEND_SOURCE_UNBOUND"
    assert binding.get("owned_manifest") == spec["owned_manifest"], "BACKEND_INPUTS_UNBOUND"
    assert binding.get("session_id") == spec["session_id"], "BACKEND_SESSION_UNBOUND"
    for key in ("helper", "program"):
        item = binding.get(key, {})
        path = Path(item.get("path", ""))
        assert path.is_absolute() and path.is_file(), "BACKEND_EXECUTABLE_NOT_PINNED"
        assert item.get("sha256") == sha(path), "BACKEND_EXECUTABLE_HASH_MISMATCH"
        assert path.name not in {"sh", "bash", "zsh", "agy", "gemini", "codex", "claude"}, "SHELL_OR_PROVIDER_PROGRAM_DENIED"
    profile = binding.get("profile", "")
    assert profile and binding.get("profile_sha256") == hashlib.sha256(profile.encode()).hexdigest()
    policy = response.get("policy", {})
    assert policy.get("filesystem_default") == "deny", "GLOBAL_FILESYSTEM_NOT_DENIED"
    assert policy.get("runtime_read_allowlist"), "RUNTIME_WHITELIST_UNSPECIFIED"
    assert policy.get("network") == "deny"
    assert "(deny default)" in profile or "(deny file-read* file-write*)" in profile, "UNCONFINED_DEFAULT_POLICY"
    assert response.get("environment") == spec["environment"], "BACKEND_ENVIRONMENT_EXPANDED"


@pytest.mark.parametrize("probe_id", list(CONTROLS))
def test_backend_plans_fixed_probe_without_execution(spec, probe_id):
    spec["probe_id"] = probe_id
    before = snapshot(spec)
    code, response = invoke(spec)
    assert code == 0 and response.get("status") == "PLANNED", "PURE_BACKEND_PLAN_REJECTED"
    assert response.get("child_started") is False
    assert response.get("capability") == "UNPROVEN"
    assert response.get("verified_controls") == []
    assert_binding(spec, response)
    assert snapshot(spec) == before, "PLANNING_MUTATED_INPUTS"


@pytest.mark.parametrize("mutation", ["argv", "provider", "environment", "deadline", "output", "stale",
                                      "shared", "parent-path", "rename", "outside-hash"])
def test_backend_rejects_unowned_unpinned_or_unbounded_requests(spec, mutation):
    spec["operation"] = "probe"
    if mutation == "argv":
        spec["argv"] = ["/bin/sh", "-c", "echo forbidden"]
    elif mutation == "provider":
        spec["probe_id"] = "agy"
    elif mutation == "environment":
        spec["environment"]["HOME"] = spec["owned_root"]
    elif mutation == "deadline":
        spec["limits"]["deadline_seconds"] = 86400
    elif mutation == "output":
        spec["limits"]["stdout_bytes"] = 1024 * 1024 * 1024
    elif mutation == "stale":
        Path(spec["owned_root"], "input.txt").write_text("stale\n")
    elif mutation == "shared":
        spec["owned_root"] = str(ROOT)
    elif mutation == "parent-path":
        spec["owned_manifest"] = {"../outside-canary.txt": spec["outside_canary_sha256"]}
    elif mutation == "rename":
        spec["rename_to"] = str(ROOT)
    else:
        spec["outside_canary_sha256"] = "0" * 64
    code, response = invoke(spec)
    assert code != 0 and response.get("status") == "REJECTED"
    assert response.get("child_started") is False
    assert response.get("reason_code"), "UNTYPED_REJECTION"


@pytest.mark.parametrize("link", ["symlink", "hardlink"])
def test_backend_rejects_linked_input_before_launch(spec, tmp_path, link):
    spec["operation"] = "probe"
    path = Path(spec["owned_root"], "input.txt")
    if link == "symlink":
        path.unlink()
        path.symlink_to(spec["outside_canary"])
    else:
        os.link(path, tmp_path / "other-owner.txt")
    code, response = invoke(spec)
    assert code != 0 and response.get("status") == "REJECTED"
    assert response.get("child_started") is False


@pytest.mark.parametrize("probe_id", list(CONTROLS))
def test_real_os_probe_observation_or_typed_unsupported(spec, probe_id):
    spec.update(operation="probe", probe_id=probe_id)
    before = snapshot(spec)
    code, response = invoke(spec)
    # No source mock: if an OS backend exists this invokes the fixed real probe.
    if response.get("status") == "UNSUPPORTED":
        assert code != 0, "UNSUPPORTED_MUST_NOT_EXIT_ZERO"
        assert response.get("reason_code") in {"OS_BACKEND_UNAVAILABLE", "SANDBOX_NOT_PROVEN", "CONTROL_NOT_PROVEN"}
        assert response.get("capability") == "UNPROVEN"
        assert response.get("verified_controls") == [], "UNSUPPORTED_IS_NOT_OS_PROOF"
    else:
        assert code == 0 and response.get("status") == "OBSERVED", "PROBE_OUTCOME_UNTYPED"
        assert response.get("child_started") is True
        assert response.get("capability") == "SCOPED_CONTROLS_OBSERVED"
        assert set(response.get("verified_controls", [])) == CONTROLS[probe_id]
        assert_binding(spec, response)
        observation = response.get("observation", {})
        assert observation.get("execution_kind") == "real-os", "MOCK_IS_NOT_OS_OBSERVATION"
        assert observation.get("stdout_bytes", -1) in range(spec["limits"]["stdout_bytes"] + 1)
        assert observation.get("stderr_bytes", -1) in range(spec["limits"]["stderr_bytes"] + 1)
        assert observation.get("owned_processes_remaining") == 0
        assert observation.get("scratch_removed") is True
    assert snapshot(spec) == before, "PROBE_DAMAGED_CALLER_INPUTS"
    assert sha(Path(spec["outside_canary"])) == spec["outside_canary_sha256"], "OUTSIDE_CANARY_CHANGED"


def test_existing_run_gate_cannot_be_bypassed_with_backend_claim():
    code, response = invoke({"kind": "run", "os_capability": "PROVEN", "backend": "local-os-backend-v1"},
                            switch="--request-json")
    assert code != 0 and response.get("reason_code") == "SANDBOX_NOT_PROVEN"
    assert response.get("child_started") is False
