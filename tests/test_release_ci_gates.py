"""Offline release admission tests: only the HTTP transport is replaced."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/verify_release_ci_gates.py"
REPO = "example/horoconsultant"
SHA = "a" * 40
TOKEN = "test-token-never-print"
FILES = ("ci.yml", "lint.yml", "ai_agent_ecosystem_sync.yml", "test_provenance.yml", "ai_cicd.yml")


def _module():
    assert SOURCE.is_file(), "checked-in release CI verifier is missing"
    spec = importlib.util.spec_from_file_location("release_ci_under_test", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeHTTP:
    """GitHub REST response fixtures; no policy behavior is mocked."""
    def __init__(self):
        self.identities = {
            name: {"id": i, "path": f".github/workflows/{name}", "state": "active"}
            for i, name in enumerate(FILES, 1)
        }
        self.runs = {
            i: [{"id": 100 + i, "workflow_id": i, "path": f".github/workflows/{name}",
                 "run_number": 10, "run_attempt": 1, "head_sha": SHA, "head_branch": "main",
                 "event": "push", "status": "completed", "conclusion": "success",
                 "repository": {"full_name": REPO}, "head_repository": {"full_name": REPO}}]
            for i, name in enumerate(FILES, 1)
        }
        self.headers = {}
        self.total_count = None
        self.main_shas = [SHA, SHA]
        self.main_reads = 0
        self.error = None

    def __call__(self, url, token):
        assert token == TOKEN
        parts = urlsplit(url)
        assert parts.scheme == "https" and parts.netloc == "api.github.com"
        prefix = f"/repos/{REPO}/"
        assert parts.path.startswith(prefix)
        if self.error:
            raise self.error
        relative = parts.path[len(prefix):]
        if relative == "commits/main":
            value = self.main_shas[min(self.main_reads, len(self.main_shas) - 1)]
            self.main_reads += 1
            return {"sha": value}, {}
        stem = "actions/workflows/"
        assert relative.startswith(stem)
        workflow = relative[len(stem):]
        if workflow.endswith("/runs"):
            workflow_id = int(workflow[:-5])
            query = parse_qs(parts.query)
            assert query.get("head_sha") == [SHA]
            assert query.get("branch") == ["main"]
            assert query.get("event") == ["push"]
            assert query.get("per_page") == ["100"]
            values = deepcopy(self.runs[workflow_id])
            return {"total_count": len(values) if self.total_count is None else self.total_count,
                    "workflow_runs": values}, dict(self.headers)
        assert workflow in self.identities
        return deepcopy(self.identities[workflow]), {}


def test_all_five_workflows_accept_exact_source_and_emit_sanitized_evidence():
    gate = _module()
    http = FakeHTTP()
    result = gate.verify_release(REPO, SHA, TOKEN, request_json=http)
    assert result["status"] == "PASSED"
    assert result["source_sha"] == SHA
    assert len(result["workflows"]) == 5
    assert {row["workflow_id"] for row in result["workflows"]} == {1, 2, 3, 4, 5}
    for row in result["workflows"]:
        assert row["run_id"] == 100 + row["workflow_id"]
        assert row["run_attempt"] == 1
        assert row["source_sha"] == SHA and row["conclusion"] == "success"
    assert http.main_reads >= 2
    assert TOKEN not in json.dumps(result)


@pytest.mark.parametrize("status,conclusion", [
    ("queued", None), ("in_progress", None), ("completed", "failure"),
    ("completed", "cancelled"), ("completed", "skipped"),
    ("completed", "timed_out"), ("completed", "neutral"), ("completed", None),
])
def test_any_required_workflow_not_success_blocks(status, conclusion):
    gate = _module()
    http = FakeHTTP()
    http.runs[5][0].update(status=status, conclusion=conclusion)
    with pytest.raises(gate.GateError):
        gate.verify_release(REPO, SHA, TOKEN, request_json=http)


@pytest.mark.parametrize("field,value", [
    ("head_sha", "b" * 40), ("head_branch", "feature"), ("event", "pull_request"),
    ("event", "workflow_dispatch"), ("workflow_id", 999),
    ("repository", {"full_name": "attacker/fork"}),
    ("head_repository", {"full_name": "attacker/fork"}),
    ("path", ".github/workflows/untrusted.yml"),
])
def test_untrusted_run_identity_blocks_even_when_successful(field, value):
    gate = _module()
    http = FakeHTTP()
    http.runs[1][0][field] = value
    with pytest.raises(gate.GateError):
        gate.verify_release(REPO, SHA, TOKEN, request_json=http)


@pytest.mark.parametrize("kind", ["missing", "duplicate_run", "duplicate_workflow", "wrong_workflow_path", "disabled_workflow", "incomplete_count", "pagination"])
def test_missing_or_ambiguous_evidence_blocks(kind):
    gate = _module()
    http = FakeHTTP()
    if kind == "missing":
        http.runs[3] = []
    elif kind == "duplicate_run":
        http.runs[1] *= 2
    elif kind == "duplicate_workflow":
        http.identities["lint.yml"]["id"] = 1
    elif kind == "wrong_workflow_path":
        http.identities["lint.yml"]["path"] = ".github/workflows/fake.yml"
    elif kind == "disabled_workflow":
        http.identities["lint.yml"]["state"] = "disabled_manually"
    elif kind == "incomplete_count":
        http.total_count = 101
    else:
        http.headers = {"Link": '<https://api.github.com/next>; rel="next"'}
    with pytest.raises(gate.GateError):
        gate.verify_release(REPO, SHA, TOKEN, request_json=http)


@pytest.mark.parametrize("newer_kind", ["run", "attempt"])
@pytest.mark.parametrize("latest_success", [False, True])
def test_latest_run_and_attempt_control_admission_not_old_success(newer_kind, latest_success):
    gate = _module()
    http = FakeHTTP()
    old = http.runs[1][0]
    newer = deepcopy(old)
    if newer_kind == "run":
        newer.update(id=200, run_number=11)
    else:
        newer["run_attempt"] = 2
    newer["conclusion"] = "success" if latest_success else "failure"
    old["conclusion"] = "failure" if latest_success else "success"
    http.runs[1] = [old, newer]
    if latest_success:
        result = gate.verify_release(REPO, SHA, TOKEN, request_json=http)
        row = next(row for row in result["workflows"] if row["workflow_id"] == 1)
        assert row["run_id"] == newer["id"] and row["run_attempt"] == newer["run_attempt"]
    else:
        with pytest.raises(gate.GateError):
            gate.verify_release(REPO, SHA, TOKEN, request_json=http)


@pytest.mark.parametrize("main_shas", [["b" * 40], [SHA, "b" * 40]])
def test_stale_selection_or_main_moving_during_gate_blocks(main_shas):
    gate = _module()
    http = FakeHTTP()
    http.main_shas = main_shas
    with pytest.raises(gate.GateError):
        gate.verify_release(REPO, SHA, TOKEN, request_json=http)


def test_api_failure_is_typed_and_never_leaks_transport_secret():
    gate = _module()
    http = FakeHTTP()
    http.error = OSError("HTTP 403 " + TOKEN)
    with pytest.raises(gate.GateError) as error:
        gate.verify_release(REPO, SHA, TOKEN, request_json=http)
    assert TOKEN not in str(error.value)


@pytest.mark.parametrize("valid", [True, False])
def test_cli_returns_fail_closed_exit_and_sanitized_output(monkeypatch, capsys, valid):
    gate = _module()
    http = FakeHTTP()
    monkeypatch.setenv("GH_TOKEN", TOKEN)
    if not valid:
        http.error = OSError("HTTP 403 " + TOKEN)
    exit_code = gate.main(["--repository", REPO, "--source-sha", SHA], request_json=http)
    assert exit_code == (0 if valid else 1)
    captured = capsys.readouterr()
    assert TOKEN not in captured.out + captured.err
    if valid:
        assert json.loads(captured.out)["status"] == "PASSED"


def _workflow(name):
    # BaseLoader preserves GitHub's YAML 'on' key instead of YAML 1.1 boolean conversion.
    return yaml.load((ROOT / ".github/workflows" / name).read_text(), Loader=yaml.BaseLoader)


@pytest.mark.parametrize("event", ["workflow_run", "workflow_dispatch"])
def test_both_release_entry_paths_gate_exact_source_before_publication(event):
    workflow = _workflow("hf_backend_deploy.yml")
    assert event in workflow["on"]
    job = workflow["jobs"]["publish-and-verify"]
    steps = job["steps"]
    gates = [(i, step) for i, step in enumerate(steps) if "scripts/verify_release_ci_gates.py" in step.get("run", "")]
    assert gates, "both release entry paths require checked-in CI gate"
    publish = next(i for i, step in enumerate(steps) if "scripts/publish_space_hf.py" in step.get("run", "") and "--dry-run" not in step["run"])
    assert any(i < publish for i, _ in gates)
    for i, step in gates:
        assert not step.get("if"), "gate must cover both event paths unconditionally"
        assert step.get("continue-on-error", "false") == "false"
        run = step["run"]
        assert "--repository" in run and "--source-sha" in run
        assert "github.repository" in json.dumps(step)
        assert "steps.source.outputs.sha" in json.dumps(step)
        assert "GH_TOKEN" in step.get("env", {})
        assert "|| true" not in run
    # Revalidate close to mutation, after preparation, not only at job startup.
    assert "scripts/verify_release_ci_gates.py" in steps[publish].get("run", "") or (
        publish > 0 and "scripts/verify_release_ci_gates.py" in steps[publish - 1].get("run", "")
    )
    permissions = dict(workflow.get("permissions", {}))
    permissions.update(job.get("permissions", {}))
    assert permissions.get("actions") == "read"
    assert all(value in ("read", "none") for value in permissions.values())


def test_ai_safety_push_always_runs_on_main_for_required_gate():
    push = _workflow("ai_cicd.yml")["on"]["push"]
    assert "main" in push["branches"]
    assert "paths" not in push and "paths-ignore" not in push


@pytest.mark.parametrize("bad", [True, False, 0, -1, "1", None])
@pytest.mark.parametrize("field", ["identity_id", "id", "workflow_id", "run_number", "run_attempt"])
def test_ids_and_ordering_require_positive_integers_without_coercion(field, bad):
    gate = _module()
    http = FakeHTTP()
    if field == "identity_id":
        http.identities["ci.yml"]["id"] = bad
    else:
        http.runs[1][0][field] = bad
    with pytest.raises(gate.GateError):
        gate.verify_release(REPO, SHA, TOKEN, request_json=http)


@pytest.mark.parametrize("bad", [True, False, -1, "1", None])
def test_total_count_requires_nonnegative_integer_without_coercion(bad):
    gate = _module()
    http = FakeHTTP()

    def transport(url, token):
        payload, headers = http(url, token)
        if "/runs?" in url:
            payload["total_count"] = bad
        return payload, headers

    with pytest.raises(gate.GateError):
        gate.verify_release(REPO, SHA, TOKEN, request_json=transport)


@pytest.mark.parametrize("endpoint", ["commits", "workflow", "runs"])
@pytest.mark.parametrize("bad", [None, [], "unexpected", {}])
def test_malformed_api_payloads_fail_with_typed_gate_error(endpoint, bad):
    gate = _module()
    http = FakeHTTP()

    def transport(url, token):
        payload, headers = http(url, token)
        matched = (
            endpoint == "commits" and "/commits/main" in url
            or endpoint == "runs" and "/runs?" in url
            or endpoint == "workflow" and url.endswith("/workflows/ci.yml")
        )
        return (bad if matched else payload), headers

    with pytest.raises(gate.GateError):
        gate.verify_release(REPO, SHA, TOKEN, request_json=transport)


@pytest.mark.parametrize("kind", ["same_number_different_id", "same_id_different_number"])
def test_conflicting_run_identity_and_sequence_are_ambiguous(kind):
    gate = _module()
    http = FakeHTTP()
    conflicting = deepcopy(http.runs[1][0])
    if kind == "same_number_different_id":
        conflicting["id"] = 999
    else:
        conflicting["run_number"] = 11
    http.runs[1].append(conflicting)
    with pytest.raises(gate.GateError):
        gate.verify_release(REPO, SHA, TOKEN, request_json=http)


@pytest.mark.parametrize("repository,source_sha,token", [
    ("../attacker", SHA, TOKEN), ("https://example.com/repo", SHA, TOKEN),
    (REPO, "main", TOKEN), (REPO, "A" * 40, TOKEN), (REPO, SHA, ""),
])
def test_invalid_request_identity_rejected_before_transport(repository, source_sha, token):
    gate = _module()

    def forbidden_transport(*args):
        pytest.fail("invalid release identity reached HTTP transport")

    with pytest.raises(gate.GateError):
        gate.verify_release(repository, source_sha, token, request_json=forbidden_transport)


@pytest.mark.parametrize("bad_headers", [None, [], "unexpected"])
def test_malformed_response_headers_fail_closed(bad_headers):
    gate = _module()
    http = FakeHTTP()

    def transport(url, token):
        payload, _ = http(url, token)
        return payload, bad_headers

    with pytest.raises(gate.GateError):
        gate.verify_release(REPO, SHA, TOKEN, request_json=transport)


@pytest.mark.parametrize("suffix", ["@main", "@refs/heads/main"])
def test_run_path_allows_only_trusted_main_ref_suffixes(suffix):
    gate = _module()
    http = FakeHTTP()
    http.runs[1][0]["path"] += suffix
    assert gate.verify_release(REPO, SHA, TOKEN, request_json=http)["status"] == "PASSED"


@pytest.mark.parametrize("suffix", ["@feature", "@refs/pull/1/merge", "@main/extra"])
def test_run_path_rejects_untrusted_ref_suffixes(suffix):
    gate = _module()
    http = FakeHTTP()
    http.runs[1][0]["path"] += suffix
    with pytest.raises(gate.GateError):
        gate.verify_release(REPO, SHA, TOKEN, request_json=http)
