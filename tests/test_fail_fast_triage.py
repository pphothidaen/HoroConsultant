"""Black-box release contracts for the Lesson 20 fail-fast triage CLI.

The implementation was already present as an untracked source candidate when
this QA-owned suite was reconstructed.  The clean baseline parent deliberately
does not contain that source file, so the explicit presence test is the red
negative control and the remaining contracts skip until the source lane is
applied.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "fail_fast_triage.py"
REPORT_SCHEMA = "fail-fast-triage-report-v1"
MAX_JSON_REPORT_BYTES = 65_536


def test_lesson20_implementation_is_present() -> None:
    assert MODULE_PATH.is_file(), (
        "Lesson 20 implementation is absent from the clean baseline parent: "
        "scripts/fail_fast_triage.py"
    )


@pytest.fixture
def triage() -> ModuleType:
    if not MODULE_PATH.is_file():
        pytest.skip("Lesson 20 source lane has not been applied to this baseline")

    module_name = "lesson20_fail_fast_triage_contract"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _probe(triage: ModuleType, *, passed: bool, details: str = "details") -> Any:
    return triage.ProbeResult(
        probe_id="contract_probe",
        name="Contract Probe",
        passed=passed,
        details=details,
        root_cause=None if passed else "contract failure",
        remediation_command=None if passed else "fix contract",
        metadata={},
    )


def _report(triage: ModuleType, probe: Any) -> Any:
    return triage.TriageReport(
        total_probes=1,
        passed_probes=1 if probe.passed else 0,
        failed_probes=0 if probe.passed else 1,
        overall_status="PASSED" if probe.passed else "FAILED",
        probes=[probe],
    )


def _release_identity(commit: str = "abc1234") -> dict[str, str]:
    revision = commit + ("0" * (40 - len(commit)))
    version = f"1.0.0.{commit}"
    source_path = "project/static/version.json"
    canonical = json.dumps(
        {
            "release_source_commit": commit,
            "release_source_metadata_path": source_path,
            "release_source_revision": revision,
            "version": version,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "version": version,
        "release_source_commit": commit,
        "release_source_revision": revision,
        "release_source_metadata_path": source_path,
        "release_source_metadata_sha256": hashlib.sha256(canonical).hexdigest(),
    }


def _write_candidate(root: Path, identity: dict[str, str]) -> None:
    target = root / "project" / "static" / "version.json"
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(identity), encoding="utf-8")


class _Response:
    def __init__(self, payload: object, status: int = 200) -> None:
        self.status = status
        self._body = (
            payload.encode("utf-8")
            if isinstance(payload, str)
            else json.dumps(payload).encode("utf-8")
        )

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


def _request_url(request: object) -> str:
    return str(getattr(request, "full_url", request))


def test_cli_timeout_must_be_bounded_positive(triage: ModuleType) -> None:
    parser = triage.build_parser()
    for invalid in ("0", "-1", "301"):
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--timeout", invalid])
        assert exc_info.value.code == 2


def test_fail_fast_and_check_all_are_mutually_exclusive(triage: ModuleType) -> None:
    parser = triage.build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--fail-fast", "--check-all"])
    assert exc_info.value.code == 2


def test_subprocess_timeout_is_reported_without_raising(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def expire(*_args: object, **_kwargs: object) -> None:
        raise subprocess.TimeoutExpired(cmd=["tool"], timeout=3)

    monkeypatch.setattr(triage.subprocess, "run", expire)
    code, stdout, stderr = triage._run_cmd(["tool"], timeout=3)
    assert (code, stdout) == (124, "")
    assert "timed out" in stderr.lower()
    stderr.encode("ascii")


@pytest.mark.parametrize("status", [" M ordinary.py", "?? new.py"])
def test_git_truth_fails_closed_for_any_dirty_entry(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    status: str,
) -> None:
    monkeypatch.setattr(triage, "_run_cmd", MagicMock(return_value=(0, status, "")))
    result = triage.probe_git_truth(skip_remote=True)
    assert result.passed is False
    assert result.root_cause
    assert result.remediation_command


def test_git_truth_fails_closed_when_fetch_fails(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = MagicMock(
        side_effect=[
            (0, "", ""),
            (1, "", "network unavailable"),
        ]
    )
    monkeypatch.setattr(triage, "_run_cmd", runner)
    result = triage.probe_git_truth(skip_remote=False, timeout=7)
    assert result.passed is False
    assert "fetch" in (result.details + " " + (result.root_cause or "")).lower()
    assert runner.call_args_list[1].kwargs.get("timeout") == 7


def test_missing_secret_scanner_is_a_failure(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(triage, "ROOT", tmp_path)
    result = triage.probe_secret_security(timeout=5)
    assert result.passed is False
    assert "scanner" in (result.details + " " + (result.root_cause or "")).lower()


@pytest.mark.parametrize(
    "stdout",
    [
        "scan complete",
        json.dumps({"scanned_files": 5, "secret_leaks_found": 0}),
        json.dumps(
            {
                "scanned_files": 5,
                "secret_leaks_found": 0,
                "findings": [],
                "status": "UNKNOWN",
            }
        ),
    ],
)
def test_malformed_secret_scanner_success_is_a_failure(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    stdout: str,
) -> None:
    scanner = tmp_path / "project" / "core" / "code_reviewer.py"
    scanner.parent.mkdir(parents=True)
    scanner.write_text("# scanner contract fixture\n", encoding="utf-8")
    monkeypatch.setattr(triage, "ROOT", tmp_path)
    monkeypatch.setattr(triage, "_run_cmd", MagicMock(return_value=(0, stdout, "")))
    result = triage.probe_secret_security(timeout=5)
    assert result.passed is False
    assert "malformed" in (result.details + " " + (result.root_cause or "")).lower()


def test_valid_secret_scanner_success_is_accepted(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    scanner = tmp_path / "project" / "core" / "code_reviewer.py"
    scanner.parent.mkdir(parents=True)
    scanner.write_text("# scanner contract fixture\n", encoding="utf-8")
    payload = {
        "scanned_files": 5,
        "secret_leaks_found": 0,
        "findings": [],
        "status": "PASSED",
    }
    monkeypatch.setattr(triage, "ROOT", tmp_path)
    monkeypatch.setattr(
        triage,
        "_run_cmd",
        MagicMock(return_value=(0, json.dumps(payload), "")),
    )
    assert triage.probe_secret_security(timeout=5).passed is True


def test_python_scan_has_a_structured_timeout_boundary(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    target = tmp_path / "scripts" / "one.py"
    target.parent.mkdir(parents=True)
    target.write_text("value = 1\n", encoding="utf-8")
    monkeypatch.setattr(triage, "ROOT", tmp_path)
    result = triage.probe_python_syntax(timeout=0)
    assert result.passed is False
    assert "timeout" in (result.details + " " + (result.root_cause or "")).lower()


def _write_full_manifest(root: Path) -> Path:
    test_path = root / "tests" / "test_contract.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text("def test_contract():\n    assert True\n", encoding="utf-8")
    manifest_path = root / "plans" / "test_provenance" / "fixture.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "test-provenance-v1",
                "ticket_id": "TICKET-FIXTURE-001",
                "sequence": 1,
                "provenance_status": "VERIFIED",
                "baseline_parent": "0" * 40,
                "test_files": [
                    {
                        "path": "tests/test_contract.py",
                        "sha256": hashlib.sha256(test_path.read_bytes()).hexdigest(),
                    }
                ],
                "red_tests": [
                    {
                        "command": ["python3", "-m", "pytest", "-q"],
                        "expected_exit": 1,
                        "failure_fingerprint": "fixture red",
                    }
                ],
                "allowed_source_paths": ["scripts/fixture.py"],
                "test_owner_role": "qa_tester",
                "reviewer_role": "code_reviewer",
                "supersedes": None,
                "correction_reason": None,
                "rationale": "Fixture with valid shape but deliberately invalid history.",
            }
        ),
        encoding="utf-8",
    )
    return manifest_path


def test_provenance_probe_runs_full_history_guard(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _write_full_manifest(tmp_path)
    guard = tmp_path / "scripts" / "test_provenance_guard.py"
    guard.parent.mkdir(parents=True, exist_ok=True)
    guard.write_text("# guard contract fixture\n", encoding="utf-8")
    calls: list[list[str]] = []

    def fail_guard(cmd: list[str], **_kwargs: object) -> tuple[int, str, str]:
        calls.append(cmd)
        return 1, json.dumps({"status": "FAILED", "issues": [{"code": "BAD_HISTORY"}]}), ""

    monkeypatch.setattr(triage, "ROOT", tmp_path)
    monkeypatch.setattr(triage, "_run_cmd", fail_guard)
    result = triage.probe_test_provenance(timeout=5)
    assert result.passed is False
    assert any("test_provenance_guard.py" in " ".join(call) for call in calls)
    assert "BAD_HISTORY" in result.details


def test_provenance_scan_has_a_structured_timeout_boundary(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _write_full_manifest(tmp_path)
    monkeypatch.setattr(triage, "ROOT", tmp_path)
    result = triage.probe_test_provenance(timeout=0)
    assert result.passed is False
    assert "timeout" in (result.details + " " + (result.root_cause or "")).lower()


def test_fail_fast_stops_before_later_probes(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = MagicMock(return_value=_probe(triage, passed=False))
    later = [MagicMock(return_value=_probe(triage, passed=True)) for _ in range(4)]
    monkeypatch.setattr(triage, "probe_git_truth", first)
    monkeypatch.setattr(triage, "probe_agent_ecosystem", later[0])
    monkeypatch.setattr(triage, "probe_secret_security", later[1])
    monkeypatch.setattr(triage, "probe_python_syntax", later[2])
    monkeypatch.setattr(triage, "probe_test_provenance", later[3])
    report = triage.run_triage(fail_fast=True, skip_remote=True, timeout=5)
    assert len(report.probes) == 1
    assert report.failed_probes == 1
    assert all(mock.call_count == 0 for mock in later)


def test_check_all_runs_each_probe_once_in_stable_order(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    def runner(probe_id: str, passed: bool) -> Any:
        events.append(probe_id)
        result = _probe(triage, passed=passed)
        result.probe_id = probe_id
        return result

    monkeypatch.setattr(triage, "probe_git_truth", lambda **_kwargs: runner("git", False))
    monkeypatch.setattr(triage, "probe_agent_ecosystem", lambda **_kwargs: runner("agents", True))
    monkeypatch.setattr(triage, "probe_secret_security", lambda **_kwargs: runner("secrets", True))
    monkeypatch.setattr(triage, "probe_python_syntax", lambda **_kwargs: runner("syntax", True))
    monkeypatch.setattr(triage, "probe_test_provenance", lambda **_kwargs: runner("provenance", True))
    report = triage.run_triage(fail_fast=False, skip_remote=True, timeout=5)
    assert events == ["git", "agents", "secrets", "syntax", "provenance"]
    assert [item.probe_id for item in report.probes] == events
    assert report.failed_probes == 1


def test_human_report_is_ascii_only(
    triage: ModuleType,
    capsys: pytest.CaptureFixture[str],
) -> None:
    probe = _probe(triage, passed=False, details="ความลับ — 🚀")
    triage.print_ascii_report(_report(triage, probe))
    output = capsys.readouterr().out
    output.encode("ascii")
    assert "[ERROR]" in output or "[FAIL]" in output


def test_json_report_is_versioned_and_ascii_only(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    probe = _probe(triage, passed=False, details="ข้อผิดพลาด — 🚀")
    monkeypatch.setattr(triage, "run_triage", lambda **_kwargs: _report(triage, probe))
    assert triage.main(["--skip-remote", "--json"]) == 1
    output = capsys.readouterr().out
    output.encode("ascii")
    payload = json.loads(output)
    assert payload["schema_version"] == REPORT_SCHEMA


def test_json_report_is_bounded_and_marks_truncation(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    probe = _probe(triage, passed=False, details="x" * 200_000)
    probe.metadata = {"raw_error": "y" * 200_000}
    monkeypatch.setattr(triage, "run_triage", lambda **_kwargs: _report(triage, probe))
    assert triage.main(["--skip-remote", "--json"]) == 1
    output = capsys.readouterr().out
    assert len(output.encode("ascii")) <= MAX_JSON_REPORT_BYTES
    assert "truncat" in output.lower()


def _endpoint_responder(
    expected: dict[str, str],
    *,
    ui_identity: dict[str, str] | None = None,
    backend_version: str | None = None,
    backend_commit: str | None = None,
) -> Any:
    def respond(request: object, **_kwargs: object) -> _Response:
        url = _request_url(request)
        if "vercel.app/version.json" in url:
            return _Response(ui_identity or expected)
        if url.endswith("/version.json"):
            return _Response(expected)
        if url.endswith("/health"):
            return _Response(
                {
                    "status": "ok",
                    "version": backend_version or expected["version"],
                    "git_commit": backend_commit or expected["release_source_commit"],
                }
            )
        raise AssertionError(f"unexpected endpoint: {url}")

    return respond


def test_http_200_with_stale_ui_identity_fails_closed(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    expected = _release_identity("abc1234")
    stale = _release_identity("def5678")
    _write_candidate(tmp_path, expected)
    monkeypatch.setattr(triage, "ROOT", tmp_path)
    monkeypatch.setattr(
        triage.urllib.request,
        "urlopen",
        _endpoint_responder(expected, ui_identity=stale),
    )
    result = triage.probe_live_production_endpoints(timeout=5)
    assert result.passed is False
    assert "identity" in (result.details + " " + (result.root_cause or "")).lower()


def test_http_200_with_wrong_backend_version_fails_closed(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    expected = _release_identity("abc1234")
    _write_candidate(tmp_path, expected)
    monkeypatch.setattr(triage, "ROOT", tmp_path)
    monkeypatch.setattr(
        triage.urllib.request,
        "urlopen",
        _endpoint_responder(
            expected,
            backend_version="1.0.0.def5678",
            backend_commit="def5678",
        ),
    )
    result = triage.probe_live_production_endpoints(timeout=5)
    assert result.passed is False
    assert "version" in (result.details + " " + (result.root_cause or "")).lower()


def test_matching_deployed_identity_and_health_pass(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    expected = _release_identity("abc1234")
    _write_candidate(tmp_path, expected)
    monkeypatch.setattr(triage, "ROOT", tmp_path)
    monkeypatch.setattr(
        triage.urllib.request,
        "urlopen",
        _endpoint_responder(expected),
    )
    result = triage.probe_live_production_endpoints(timeout=5)
    assert result.passed is True
    assert result.metadata.get("release_identity_verified") is True
