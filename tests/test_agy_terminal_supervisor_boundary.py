"""Phase-1 local-only CLI boundary, independent of native AGY dispatch.

Public contract: python3 scripts/agy_terminal_supervisor.py --request-json reads
one JSON object on stdin and returns one JSON decision on stdout. Pure validated
requests return exit 0 / decision VALIDATED; rejected requests return nonzero /
decision REJECTED / nonempty reason_code. Kinds: files, command, result, run,
describe_probe. Validation never executes argv or mutates files. run remains
SANDBOX_NOT_PROVEN until independently verified real OS controls exist.

The supervisor does not exist at baseline: assertion RED demonstrates an absent
public protocol, not an observed insecure runtime. No import fallback, provider,
credential, native-proof or mocked-sandbox success is used. OS probe description
is a specification only, not execution or capability evidence.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / "scripts/agy_terminal_supervisor.py"
HARMLESS_ARGV = [str(Path(sys.executable).resolve()), "-c", "print('horo-local-probe')"]
CANARY = "QA_TEMP_SECRET_CANARY_005"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def call(request):
    # This child is the requested local validator, never the request's argv.
    completed = subprocess.run(
        [sys.executable, str(SUPERVISOR), "--request-json"],
        input=json.dumps(request), capture_output=True, text=True, timeout=5,
        cwd=ROOT, env={"PATH": os.defpath, "LANG": "C", "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert completed.stdout.strip(), "LOCAL_PROTOCOL_NO_RESPONSE: structured decision required"
    try:
        response = json.loads(completed.stdout)
    except ValueError:
        pytest.fail("LOCAL_PROTOCOL_MALFORMED_RESPONSE")
    assert isinstance(response, dict), "LOCAL_PROTOCOL_RESPONSE_NOT_OBJECT"
    assert response.get("native_proof") is False, "LOCAL_VALIDATION_IS_NOT_NATIVE_PROOF"
    assert response.get("os_capability") == "UNKNOWN", "NO_OS_PROBE_HAS_RUN"
    assert response.get("auth_isolation") == "NOT_PROVEN", "AUTH_ISOLATION_NOT_PROVEN"
    return completed, response


def expect(request, valid, reason=None):
    completed, response = call(request)
    assert response.get("decision") == ("VALIDATED" if valid else "REJECTED"), "WRONG_BOUNDARY_DECISION"
    assert (completed.returncode == 0) is valid, "BOUNDARY_EXIT_MISMATCH"
    if not valid:
        assert response.get("reason_code"), "MISSING_REJECTION_REASON"
    if reason:
        assert response["reason_code"] == reason
    return response


@pytest.fixture
def file_request(tmp_path):
    owned = tmp_path / "owned"
    owned.mkdir()
    path = owned / "owned.txt"
    path.write_text("baseline\n")
    return {"kind": "files", "owned_root": str(owned), "shared_workspace": str(ROOT),
            "sensitive_paths": [str(tmp_path / "sensitive-canary.txt")],
            "allowlist": [{"path": "owned.txt", "sha256": sha(path),
                           "operations": ["read", "update", "delete"]},
                          {"path": "new.txt", "sha256": None, "operations": ["write"]}],
            "operations": [{"operation": "read", "path": "owned.txt"}]}


@pytest.mark.parametrize("operation,path", [("read", "owned.txt"), ("update", "owned.txt"),
                                             ("delete", "owned.txt"), ("write", "new.txt")])
def test_owned_exact_hash_operations_validate_without_mutation(file_request, operation, path):
    root = Path(file_request["owned_root"])
    before = {p.name: sha(p) for p in root.iterdir()}
    file_request["operations"] = [{"operation": operation, "path": path}]
    expect(file_request, True)
    assert {p.name: sha(p) for p in root.iterdir()} == before, "PURE_VALIDATION_MUTATED_FILES"


@pytest.mark.parametrize("mutation", ["unlisted", "parent", "absolute", "root", "stale",
                                      "permission", "shared-root", "rename", "duplicate"])
def test_path_and_authority_negatives(file_request, mutation):
    if mutation in {"unlisted", "parent", "absolute", "root"}:
        file_request["operations"][0]["path"] = {
            "unlisted": "not-owned.txt", "parent": "../escape.txt", "absolute": "/tmp/escape.txt", "root": "."
        }[mutation]
    elif mutation == "stale":
        Path(file_request["owned_root"], "owned.txt").write_text("changed after approval")
    elif mutation == "permission":
        file_request["operations"][0]["operation"] = "write"
    elif mutation == "shared-root":
        file_request["owned_root"] = str(ROOT)
    elif mutation == "rename":
        file_request["operations"][0].update(operation="rename", destination="../escape.txt")
    else:
        file_request["allowlist"].append(copy.deepcopy(file_request["allowlist"][0]))
    expect(file_request, False)


@pytest.mark.parametrize("kind", ["symlink", "ancestor-symlink", "hardlink", "directory", "fifo"])
def test_links_and_nonregular_files_are_rejected(file_request, tmp_path, kind):
    root = Path(file_request["owned_root"])
    path = root / "owned.txt"
    if kind == "ancestor-symlink":
        alias = tmp_path / "alias"
        alias.symlink_to(root, target_is_directory=True)
        file_request["owned_root"] = str(alias)
    elif kind == "hardlink":
        os.link(path, tmp_path / "other-owner.txt")
    else:
        path.unlink()
        if kind == "symlink":
            outside = tmp_path / "outside.txt"
            outside.write_text("baseline\n")
            path.symlink_to(outside)
        elif kind == "directory":
            path.mkdir()
        else:
            os.mkfifo(path)
    expect(file_request, False)


def test_sensitive_canary_read_denied_even_if_allowlisted(file_request, tmp_path):
    canary = Path(file_request["owned_root"]) / "sensitive-canary.txt"
    canary.write_text(CANARY)
    file_request["sensitive_paths"] = [str(canary)]
    file_request["allowlist"].append({"path": canary.name, "sha256": sha(canary), "operations": ["read"]})
    file_request["operations"] = [{"operation": "read", "path": canary.name}]
    response = expect(file_request, False)
    assert CANARY not in json.dumps(response), "SENSITIVE_READ_LEAKED"


def command_request():
    return {"kind": "command", "argv": HARMLESS_ARGV, "pinned_argv": HARMLESS_ARGV,
            "executable_sha256": sha(Path(HARMLESS_ARGV[0])), "environment": {"LANG": "C", "LC_ALL": "C"},
            "deadline_seconds": 2, "max_stdout_bytes": 1024, "max_stderr_bytes": 1024,
            "descendant_policy": "owned-group-deadline-cleanup", "shell": False}


def test_harmless_pinned_command_spec_validates_without_execution():
    response = expect(command_request(), True)
    assert response.get("child_started") is False, "SPEC_VALIDATION_LAUNCHED_CHILD"


@pytest.mark.parametrize("mutation", ["shell", "argv", "digest", "env", "deadline", "stdout", "stderr", "descendants", "unbounded-deadline", "unbounded-stream"])
def test_command_must_be_harmless_pinned_and_bounded(mutation):
    request = command_request()
    if mutation == "shell":
        request.update(argv=["/bin/sh", "-c", "echo hi"], pinned_argv=["/bin/sh", "-c", "echo hi"], shell=True)
    elif mutation == "argv":
        request["argv"] = HARMLESS_ARGV + ["unexpected"]
    elif mutation == "digest":
        request["executable_sha256"] = "0" * 64
    elif mutation == "env":
        request["environment"]["CREDENTIAL_CANARY"] = CANARY
    elif mutation == "deadline":
        request["deadline_seconds"] = 0
    elif mutation == "unbounded-deadline":
        request["deadline_seconds"] = 86400
    elif mutation == "unbounded-stream":
        request["max_stdout_bytes"] = 1024 * 1024 * 1024
    elif mutation in {"stdout", "stderr"}:
        request[f"max_{mutation}_bytes"] = 0
    else:
        request["descendant_policy"] = "ignore"
    expect(request, False)


def result_request():
    result = {"schema_version": "local-work-result-v1", "session_id": "session-005", "status": "DONE",
              "changed_paths": ["owned.txt"], "summary": "Completed local fixture work"}
    return {"kind": "result", "session_id": "session-005", "exit_code": 0,
            "timed_out": False, "cancelled": False, "descendants_remaining": 0,
            "allowed_paths": ["owned.txt"], "sensitive_canaries": [CANARY], "max_output_bytes": 1024,
            "stream": json.dumps(result)}


def test_single_matching_done_result_is_valid():
    expect(result_request(), True)


@pytest.mark.parametrize("mutation", ["missing", "malformed", "duplicate-frame", "duplicate-key", "session",
                                      "secret", "secret-key", "nonzero", "timeout", "cancelled", "descendant", "outside", "oversize"])
def test_result_and_lifecycle_fail_closed(mutation):
    request = result_request()
    result = json.loads(request["stream"])
    if mutation in {"missing", "malformed", "duplicate-frame", "duplicate-key", "oversize"}:
        request["stream"] = {"missing": "", "malformed": "{", "duplicate-frame": request["stream"] + "\n" + request["stream"],
                             "duplicate-key": request["stream"].replace('"status": "DONE"', '"status": "FAILED", "status": "DONE"'),
                             "oversize": "X" * 1025}[mutation]
    elif mutation in {"session", "secret", "secret-key", "outside"}:
        if mutation == "session":
            result["session_id"] = "different-session"
        elif mutation == "secret":
            result["summary"] = CANARY
        elif mutation == "secret-key":
            result["token"] = "synthetic-only"
        else:
            result["changed_paths"] = ["../outside.txt"]
        request["stream"] = json.dumps(result)
    else:
        field = {"nonzero": "exit_code", "timeout": "timed_out", "cancelled": "cancelled", "descendant": "descendants_remaining"}[mutation]
        request[field] = 1 if mutation in {"nonzero", "descendant"} else True
    response = expect(request, False)
    assert CANARY not in json.dumps(response), "RESULT_VALIDATION_LEAKED_CANARY"


def test_run_cannot_promote_self_asserted_os_capability():
    request = command_request()
    request.update(kind="run", os_capability="PROVEN", auth_isolation="PROVEN")
    response = expect(request, False, "SANDBOX_NOT_PROVEN")
    assert response.get("child_started") is False, "UNPROVEN_RUN_STARTED_CHILD"


def test_harmless_real_os_probe_spec_is_not_capability_evidence():
    response = expect({"kind": "describe_probe"}, True)
    assert response.get("provider_free") is True
    assert response.get("child_started") is False
    assert set(response.get("required_controls", [])) >= {
        "owned_path_enforcement", "sensitive_canary_read_denial", "descendant_deadline_cleanup", "bounded_streams"
    }, "REAL_OS_PROBE_CONTROLS_UNSPECIFIED"
