"""Executable contracts for the fail-closed production monitor workflow."""

from __future__ import annotations

import hashlib
import json
import runpy
import subprocess
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "production_monitor.yml"
BACKEND_SPACE_ID = "pphothidaen/horoconsultant-core-backend"
BACKEND_URL = "https://pphothidaen-horoconsultant-core-backend.hf.space"
VERCEL_URL = "https://horo-consultant-psi.vercel.app"
SOURCE_COMMIT = "abc1234"
SOURCE_REVISION = "a" * 40
PACKAGING_COMMIT = "b" * 40


def _workflow() -> tuple[str, dict[str, Any]]:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    parsed = yaml.load(text, Loader=yaml.BaseLoader)
    assert isinstance(parsed, dict)
    return text, parsed


def _step(job: dict[str, Any], name: str) -> dict[str, Any]:
    matches = [step for step in job["steps"] if step.get("name") == name]
    assert len(matches) == 1, f"expected exactly one workflow step named {name!r}"
    return matches[0]


def _identity_script() -> str:
    _, workflow = _workflow()
    run = _step(
        workflow["jobs"]["monitor"],
        "Verify exact release identity on backend and UI",
    )["run"]
    prefix = "python3 - <<'PY'\n"
    suffix = "\nPY\n"
    assert run.startswith(prefix) and run.endswith(suffix)
    return run[len(prefix) : -len(suffix)]


def _release_metadata() -> dict[str, str]:
    identity = {
        "release_source_commit": SOURCE_COMMIT,
        "release_source_metadata_path": "project/static/version.json",
        "release_source_revision": SOURCE_REVISION,
        "version": f"1.0.0.{SOURCE_COMMIT}",
    }
    canonical = json.dumps(
        identity,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "version": identity["version"],
        "release_source_commit": SOURCE_COMMIT,
        "release_source_revision": SOURCE_REVISION,
        "release_source_metadata_path": identity["release_source_metadata_path"],
        "release_source_metadata_sha256": hashlib.sha256(canonical).hexdigest(),
    }


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")


class _Response:
    def __init__(self, request: urllib.request.Request, payload: bytes):
        self.status = 200
        self._url = request.full_url
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, limit: int) -> bytes:
        assert limit == 1_048_577
        return self._payload

    def geturl(self) -> str:
        return self._url


def _run_identity_audit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    source_raw: bytes | None = None,
    public_raw: bytes | None = None,
    remote_raw: bytes | None = None,
    ancestry_returncode: int = 0,
    fail_request: int | None = None,
    request_error: Exception | None = None,
) -> tuple[int, dict[str, Any], list[tuple[str, str]]]:
    metadata = _release_metadata()
    source_raw = source_raw if source_raw is not None else _json_bytes(metadata)
    public_raw = public_raw if public_raw is not None else source_raw
    remote_raw = remote_raw if remote_raw is not None else _json_bytes(metadata)

    source_path = tmp_path / "project" / "static" / "version.json"
    public_path = tmp_path / "public" / "version.json"
    source_path.parent.mkdir(parents=True)
    public_path.parent.mkdir(parents=True)
    source_path.write_bytes(source_raw)
    public_path.write_bytes(public_raw)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HF_BACKEND_SPACE_ID", BACKEND_SPACE_ID)
    monkeypatch.setenv("HF_BACKEND_URL", BACKEND_URL)
    monkeypatch.setenv("VERCEL_STATIC_URL", VERCEL_URL)

    def fake_check_output(command, **_kwargs):
        assert command[:2] == ["git", "rev-parse"]
        if command[-1] == "HEAD":
            return PACKAGING_COMMIT
        assert command[-1] == f"{SOURCE_COMMIT}^{{commit}}"
        return SOURCE_REVISION

    def fake_run(command, **_kwargs):
        assert command == [
            "git",
            "merge-base",
            "--is-ancestor",
            SOURCE_REVISION,
            PACKAGING_COMMIT,
        ]
        return SimpleNamespace(returncode=ancestry_returncode)

    requests: list[tuple[str, str]] = []

    def fake_urlopen(request, *, timeout):
        assert timeout == 15
        requests.append((request.full_url, request.get_method()))
        if fail_request == len(requests):
            raise request_error or OSError("simulated unavailable identity surface")
        return _Response(request, remote_raw)

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    script_path = tmp_path / "production-monitor-identity.py"
    script_path.write_text(_identity_script(), encoding="utf-8")
    with pytest.raises(SystemExit) as raised:
        runpy.run_path(str(script_path), run_name="__main__")

    report = json.loads(
        (tmp_path / "production-version-identity.json").read_text(encoding="utf-8")
    )
    return int(raised.value.code), report, requests


def test_monitor_has_canonical_targets_get_only_permissions_and_pinned_actions():
    text, workflow = _workflow()
    job = workflow["jobs"]["monitor"]

    assert set(workflow["on"]) == {"schedule", "workflow_dispatch"}
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["concurrency"] == {
        "group": "production-synthetic-monitor",
        "cancel-in-progress": "true",
    }
    assert job["env"] == {
        "HF_BACKEND_SPACE_ID": BACKEND_SPACE_ID,
        "HF_BACKEND_URL": BACKEND_URL,
        "VERCEL_STATIC_URL": VERCEL_URL,
        "HF_STATIC_SPACE_ID": "",
    }

    action_refs = {step["uses"] for step in job["steps"] if "uses" in step}
    assert action_refs == {
        "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683",
        "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    }
    checkout = _step(job, "Checkout monitored source")
    assert checkout["with"] == {
        "fetch-depth": "0",
        "persist-credentials": "false",
    }

    assert 'method="GET"' in text
    assert 'method="POST"' not in text
    assert "scripts/run_luopan_e2e_regression.py" not in text
    assert "${{ secrets." not in text
    assert "${{ vars." not in text
    assert "doppler" not in text.lower()
    assert "azure" not in text.lower()
    assert "flyctl" not in text.lower()
    assert "--dry-run" in _step(job, "Resolve monitor targets without network")["run"]


def test_identity_script_statically_enforces_every_provenance_boundary():
    script = _identity_script()

    for marker in (
        "object_pairs_hook=reject_duplicate_keys",
        "committed release metadata mirrors differ",
        'required = (\n        "version",\n        "release_source_commit"',
        'for key in ("commit", "packaging_commit")',
        "release version and source commit disagree",
        "hashlib.sha256(canonical).hexdigest()",
        '["git", "rev-parse", "--verify", f"{source_commit}^{{commit}}"]',
        '["git", "rev-parse", "HEAD"]',
        '["git", "merge-base", "--is-ancestor"',
        '"packaging_commit": packaging_commit',
        'if deployed != source:',
        'len(report["surfaces"]) != 2',
        'raise SystemExit(0 if report["success"] else 1)',
    ):
        assert marker in script


def test_canonical_identity_passes_with_two_get_surfaces_and_packaging_evidence(
    monkeypatch,
    tmp_path,
):
    exit_code, report, requests = _run_identity_audit(monkeypatch, tmp_path)

    assert exit_code == 0
    assert report["success"] is True
    assert report["backend_target"] == BACKEND_SPACE_ID
    assert report["backend_sdk"] == "docker"
    assert report["vercel_ui_target"] == VERCEL_URL
    assert report["release_source_commit"] == SOURCE_COMMIT
    assert report["release_source_revision"] == SOURCE_REVISION
    assert report["release_source_metadata_path"] == "project/static/version.json"
    assert report["release_source_metadata_sha256"] == (
        _release_metadata()["release_source_metadata_sha256"]
    )
    assert report["packaging_commit"] == PACKAGING_COMMIT
    assert requests == [
        (f"{BACKEND_URL}/version.json", "GET"),
        (f"{VERCEL_URL}/version.json", "GET"),
    ]
    assert [surface["target"] for surface in report["surfaces"]] == [
        "hf_docker_backend",
        "vercel_ui",
    ]
    assert all(surface["matched"] is True for surface in report["surfaces"])
    assert all("response_sha256" in surface for surface in report["surfaces"])


@pytest.mark.parametrize(
    ("scenario", "expected_error_class", "expected_surface_count"),
    (
        ("duplicate", "ContractError", 0),
        ("mirror_drift", "ContractError", 0),
        ("bad_digest", "ContractError", 0),
        ("legacy_identity", "ContractError", 0),
        ("not_ancestor", "ContractError", 0),
        ("deployed_drift", "ContractError", 0),
        ("missing_surface", "OSError", 1),
    ),
)
def test_identity_audit_fails_closed_for_metadata_and_surface_drift(
    monkeypatch,
    tmp_path,
    scenario,
    expected_error_class,
    expected_surface_count,
):
    metadata = _release_metadata()
    options: dict[str, Any] = {}

    if scenario == "duplicate":
        raw = _json_bytes(metadata).decode("utf-8").replace(
            f'"release_source_commit": "{SOURCE_COMMIT}"',
            (
                f'"release_source_commit": "{SOURCE_COMMIT}", '
                '"release_source_commit": "fffffff"'
            ),
        )
        options["source_raw"] = raw.encode("utf-8")
        options["public_raw"] = options["source_raw"]
    elif scenario == "mirror_drift":
        public = dict(metadata)
        public["status"] = "stale"
        options["public_raw"] = _json_bytes(public)
    elif scenario == "bad_digest":
        bad_digest = dict(metadata)
        bad_digest["release_source_metadata_sha256"] = "0" * 64
        options["source_raw"] = _json_bytes(bad_digest)
        options["public_raw"] = options["source_raw"]
    elif scenario == "legacy_identity":
        legacy = dict(metadata)
        legacy["commit"] = SOURCE_COMMIT
        options["source_raw"] = _json_bytes(legacy)
        options["public_raw"] = options["source_raw"]
    elif scenario == "not_ancestor":
        options["ancestry_returncode"] = 1
    elif scenario == "deployed_drift":
        stale = dict(metadata)
        stale["status"] = "stale"
        options["remote_raw"] = _json_bytes(stale)
    elif scenario == "missing_surface":
        options["fail_request"] = 2

    exit_code, report, _requests = _run_identity_audit(
        monkeypatch,
        tmp_path,
        **options,
    )

    assert exit_code == 1
    assert report["success"] is False
    assert report["error_class"] == expected_error_class
    assert len(report["surfaces"]) == expected_surface_count


def test_failure_report_and_artifact_hook_elide_sensitive_error_content(
    monkeypatch,
    tmp_path,
    capsys,
):
    sensitive = "hf_NOT_A_REAL_TOKEN_1234567890"
    exit_code, report, _requests = _run_identity_audit(
        monkeypatch,
        tmp_path,
        fail_request=1,
        request_error=RuntimeError(sensitive),
    )

    rendered = json.dumps(report, sort_keys=True)
    captured = capsys.readouterr()
    assert exit_code == 1
    assert report["error_class"] == "RuntimeError"
    assert sensitive not in rendered
    assert sensitive not in captured.out
    assert "error_message" not in report

    _, workflow = _workflow()
    upload = _step(workflow["jobs"]["monitor"], "Upload sanitized monitor evidence")
    assert upload["if"] == "always()"
    assert upload["uses"] == (
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02"
    )
    assert upload["with"]["if-no-files-found"] == "warn"
    assert set(upload["with"]["path"].splitlines()) == {
        "production-version-identity.json",
        "production-verification.json",
        "synthetic-health.json",
    }
    assert not any(
        forbidden in upload["with"]["path"].lower()
        for forbidden in ("token", "secret", "credential", ".env", ".log")
    )
