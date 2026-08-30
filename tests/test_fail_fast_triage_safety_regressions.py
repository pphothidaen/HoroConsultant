"""Security regression contracts for the Lesson 20 fail-fast triage CLI.

These tests intentionally exercise public probes and the command-line boundary
with local repositories, stub executables, and deterministic HTTP/time fakes.
They never contact a provider or require credentials.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "fail_fast_triage.py"
PROVENANCE_REPORT_SCHEMA = "test-provenance-report-v2"
PROVENANCE_RECEIPT_KEYS = {
    "schema_version",
    "command",
    "status",
    "requested_base",
    "base_commit",
    "requested_head",
    "head_commit",
    "ticket_id",
    "baseline_commit",
    "test_files_verified",
    "issues",
    "notes",
}


@pytest.fixture(scope="module")
def triage() -> ModuleType:
    module_name = "lesson20_fail_fast_triage_safety_contract"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _git(repo: Path, *args: str, input_text: str | None = None) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        input=input_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=5,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def _read_fixture_pid(path: Path) -> int | None:
    try:
        raw = path.read_text(encoding="ascii").strip()
        pid = int(raw)
    except (OSError, ValueError):
        return None
    return pid if pid > 1 else None


def _pid_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _terminate_fixture_process_tree(
    proc: subprocess.Popen[str],
    retained_pids: set[int],
    *,
    isolated_process_group: bool,
) -> list[int]:
    """Boundedly reap a test-owned process tree after every exit path."""
    owned_pids = {pid for pid in retained_pids | {proc.pid} if pid > 1}
    for sig, wait_seconds in ((signal.SIGTERM, 0.75), (signal.SIGKILL, 1.25)):
        if isolated_process_group:
            try:
                os.killpg(proc.pid, sig)
            except ProcessLookupError:
                pass
        for pid in sorted(owned_pids):
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                pass
        deadline = time.monotonic() + wait_seconds
        while time.monotonic() < deadline:
            if proc.poll() is not None and not any(
                _pid_is_alive(pid) for pid in owned_pids - {proc.pid}
            ):
                break
            time.sleep(0.02)
    try:
        proc.wait(timeout=0.25)
    except subprocess.TimeoutExpired:
        pass
    return sorted(pid for pid in owned_pids if _pid_is_alive(pid))


def _init_repo(repo: Path) -> str:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Lesson 20 QA")
    _git(repo, "config", "user.email", "lesson20-qa@example.invalid")
    (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "seed.txt")
    _git(repo, "commit", "-q", "-m", "seed")
    _git(repo, "branch", "-M", "main")
    revision = _git(repo, "rev-parse", "HEAD")
    _git(repo, "update-ref", "refs/remotes/origin/main", revision)
    return revision


def _commit_all(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _identity(revision: str) -> dict[str, str]:
    short_commit = revision[:7]
    version = f"1.0.0.{short_commit}"
    source_path = "project/static/version.json"
    canonical = json.dumps(
        {
            "release_source_commit": short_commit,
            "release_source_metadata_path": source_path,
            "release_source_revision": revision,
            "version": version,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "version": version,
        "release_source_commit": short_commit,
        "release_source_revision": revision,
        "release_source_metadata_path": source_path,
        "release_source_metadata_sha256": hashlib.sha256(canonical).hexdigest(),
    }


def _write_identity(repo: Path, identity: dict[str, str], raw: str | None = None) -> None:
    path = repo / "project" / "static" / "version.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(raw if raw is not None else json.dumps(identity), encoding="utf-8")


def _release_repo(tmp_path: Path, mode: str = "valid") -> tuple[Path, dict[str, str]]:
    repo = tmp_path / "repo"
    source_revision = _init_repo(repo)
    if mode == "missing":
        declared_revision = "f" * 40
        assert declared_revision != source_revision
    elif mode == "non_ancestor":
        tree = _git(repo, "rev-parse", "HEAD^{tree}")
        declared_revision = _git(
            repo,
            "commit-tree",
            tree,
            "-m",
            "unrelated source",
        )
        assert declared_revision != source_revision
    else:
        assert mode == "valid"
        declared_revision = source_revision
    identity = _identity(declared_revision)
    _write_identity(repo, identity)
    packaging_commit = _commit_all(repo, "package candidate")
    _git(repo, "update-ref", "refs/remotes/origin/main", packaging_commit)
    return repo, identity


def _url(request: object) -> str:
    return str(getattr(request, "full_url", request))


class _Response:
    def __init__(
        self,
        payload: object,
        *,
        clock: "_Clock | None" = None,
        read_sizes: list[int] | None = None,
        read_chunks: list[int] | None = None,
    ) -> None:
        self.status = 200
        if isinstance(payload, bytes):
            self._body = payload
        elif isinstance(payload, str):
            self._body = payload.encode("utf-8")
        else:
            self._body = json.dumps(payload).encode("utf-8")
        self._clock = clock
        self._read_sizes = read_sizes
        self.read_chunks = read_chunks if read_chunks is not None else []
        self._offset = 0

    def read(self, size: int = -1) -> bytes:
        if self._read_sizes is not None:
            self._read_sizes.append(size)
        if self._clock is not None:
            self._clock.advance(0.9)
        end = len(self._body) if size < 0 else self._offset + size
        chunk = self._body[self._offset : end]
        self._offset += len(chunk)
        self.read_chunks.append(len(chunk))
        return chunk

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


def _matching_response(identity: dict[str, str], request: object) -> _Response:
    url = _url(request)
    if url.endswith("/health"):
        return _Response(
            {
                "status": "ok",
                "version": identity["version"],
                "git_commit": identity["release_source_commit"],
            }
        )
    return _Response(identity)


class _Clock:
    def __init__(self) -> None:
        self.now = 100.0

    def monotonic(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class _NoCommunicateProxy:
    """Expose a real Popen except for the unbounded communicate shortcut."""

    def __init__(self, process: subprocess.Popen[str]) -> None:
        self._process = process
        self.communicate_calls = 0

    @property
    def pid(self) -> int:
        return self._process.pid

    @property
    def stdout(self) -> Any:
        return self._process.stdout

    @property
    def stderr(self) -> Any:
        return self._process.stderr

    @property
    def returncode(self) -> int | None:
        return self._process.returncode

    def communicate(self, *_args: object, **_kwargs: object) -> tuple[str, str]:
        self.communicate_calls += 1
        raise AssertionError("unbounded subprocess.communicate capture is forbidden")

    def __getattr__(self, name: str) -> Any:
        return getattr(self._process, name)


def _report(triage: ModuleType, result: Any) -> Any:
    return triage.TriageReport(
        total_probes=1,
        passed_probes=1 if result.passed else 0,
        failed_probes=0 if result.passed else 1,
        overall_status="PASSED" if result.passed else "FAILED",
        probes=[result],
    )


def _render_both_reports(
    triage: ModuleType,
    result: Any,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> tuple[str, str]:
    report = _report(triage, result)
    triage.print_ascii_report(report)
    human = capsys.readouterr().out
    monkeypatch.setattr(triage, "run_triage", lambda **_kwargs: report)
    expected_exit = 0 if result.passed else 1
    assert triage.main(["--skip-remote", "--json"]) == expected_exit
    machine = capsys.readouterr().out
    json.loads(machine)
    human.encode("ascii")
    machine.encode("ascii")
    assert len(human.encode("ascii")) <= triage.MAX_JSON_REPORT_BYTES
    assert len(machine.encode("ascii")) <= triage.MAX_JSON_REPORT_BYTES
    return human, machine


def _json_variant(identity: dict[str, str], variant: str) -> str:
    document = json.dumps(identity, sort_keys=True)
    if variant == "prefix":
        return "external diagnostic prefix\n" + document
    if variant == "suffix":
        return document + "\nexternal diagnostic suffix"
    assert variant == "duplicate"
    return document[:-1] + ",\"version\":" + json.dumps(identity["version"]) + "}"


def _provenance_receipt_repo(
    tmp_path: Path,
    *,
    variant: str = "valid",
) -> tuple[Path, str, str, str, Path]:
    """Build one governed PR and a deterministic guard-receipt test double."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    manifest_dir = repo / "plans" / "test_provenance"
    manifest_dir.mkdir(parents=True)
    (manifest_dir / "old.json").write_text(
        json.dumps(
            {
                "schema_version": "test-provenance-v1",
                "ticket_id": "TICKET-LESSON20-OLD",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    base = _commit_all(repo, "old provenance on base")
    _git(repo, "update-ref", "refs/remotes/origin/main", base)

    ticket = "TICKET-LESSON20-GOVERNED"
    (manifest_dir / "current.json").write_text(
        json.dumps(
            {
                "schema_version": "test-provenance-v1",
                "ticket_id": ticket,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    head = _commit_all(repo, "current governed baseline")

    receipt: dict[str, object] = {
        "schema_version": PROVENANCE_REPORT_SCHEMA,
        "command": "verify-pr",
        "status": "PASSED",
        "requested_base": base,
        "base_commit": base,
        "requested_head": head,
        "head_commit": head,
        "ticket_id": ticket,
        "baseline_commit": head,
        "test_files_verified": 2,
        "issues": [],
        "notes": [
            "NON_TDD_RECONSTRUCTED limitation retained at preserved cutoff; "
            "superseded history is not a current failure"
        ],
    }
    if variant == "schema_version":
        receipt["schema_version"] = "test-provenance-report-v1"
    elif variant == "command":
        receipt["command"] = "verify"
    elif variant == "requested_base":
        receipt["requested_base"] = "origin/main"
    elif variant == "base_commit":
        receipt["base_commit"] = head
    elif variant == "requested_head":
        receipt["requested_head"] = "HEAD"
    elif variant == "head_commit":
        receipt["head_commit"] = base
    elif variant == "ticket_id":
        receipt["ticket_id"] = "NOT-A-GOVERNED-TICKET"
    elif variant == "baseline_commit":
        receipt["baseline_commit"] = "not-a-full-git-sha"
    elif variant == "test_files_verified":
        receipt["test_files_verified"] = True
    elif variant == "issues":
        receipt["issues"] = "not-an-array"
    elif variant == "notes":
        receipt["notes"] = ["valid note", 42]
    elif variant == "incomplete":
        for field in (
            "requested_base",
            "base_commit",
            "requested_head",
            "head_commit",
            "ticket_id",
            "baseline_commit",
        ):
            receipt.pop(field)
    elif variant == "extra":
        receipt["untrusted_extension"] = "forged"
    else:
        assert variant == "valid"

    guard = repo / "scripts" / "test_provenance_guard.py"
    guard.parent.mkdir(parents=True)
    call_log = repo / "guard-calls.jsonl"
    guard.write_text(
        "import json, pathlib, sys\n"
        f"log = pathlib.Path({str(call_log)!r})\n"
        "with log.open('a', encoding='utf-8') as stream:\n"
        "    stream.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        f"print({json.dumps(receipt, sort_keys=True)!r})\n",
        encoding="utf-8",
    )
    return repo, base, head, ticket, call_log


def test_provenance_uses_one_topological_pr_guard_and_preserves_limitations(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo, base, head, ticket, call_log = _provenance_receipt_repo(tmp_path)
    monkeypatch.setattr(triage, "ROOT", repo)

    result = triage.probe_test_provenance(timeout=5)

    calls = [json.loads(line) for line in call_log.read_text(encoding="utf-8").splitlines()]
    assert result.passed is True
    assert len(calls) == 1, "provenance must not verify every historical manifest against HEAD"
    argv = calls[0]
    assert argv[0] == "verify-pr"
    assert argv[argv.index("--base") + 1] == base
    assert argv[argv.index("--head") + 1] == head
    rendered = result.details + json.dumps(result.metadata, sort_keys=True)
    assert "NON_TDD_RECONSTRUCTED" in rendered
    assert "superseded history" in rendered
    assert result.metadata["base_commit"] == base
    assert result.metadata["head_commit"] == head
    assert result.metadata["ticket_id"] == ticket
    assert result.metadata["baseline_commit"] == head


@pytest.mark.parametrize(
    "variant",
    [
        "schema_version",
        "command",
        "requested_base",
        "base_commit",
        "requested_head",
        "head_commit",
        "ticket_id",
        "baseline_commit",
        "test_files_verified",
        "issues",
        "notes",
        "incomplete",
        "extra",
    ],
)
def test_provenance_rejects_forged_stale_or_incomplete_receipt(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    variant: str,
) -> None:
    repo, _base, _head, _ticket, _call_log = _provenance_receipt_repo(
        tmp_path,
        variant=variant,
    )
    monkeypatch.setattr(triage, "ROOT", repo)

    result = triage.probe_test_provenance(timeout=5)

    assert result.passed is False
    diagnostic = " ".join(
        part
        for part in (result.details, result.root_cause, result.remediation_command)
        if part
    ).lower()
    assert "provenance" in diagnostic or "receipt" in diagnostic


def test_timeout_terminates_descendant_process_tree(
    tmp_path: Path,
) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    marker = tmp_path / "descendant-survived.txt"
    direct_pid_file = tmp_path / "direct.pid"
    pid_file = tmp_path / "descendant.pid"
    checker = scripts / "sync_ai_agent_ecosystem.py"
    descendant = (
        "import os, pathlib, time; "
        f"pathlib.Path({str(pid_file)!r}).write_text(str(os.getpid()), encoding='ascii'); "
        "time.sleep(1.35); "
        f"pathlib.Path({str(marker)!r}).write_text('survived', encoding='ascii')"
    )
    checker.write_text(
        "import os, pathlib, subprocess, sys, time\n"
        f"pathlib.Path({str(direct_pid_file)!r}).write_text(str(os.getpid()), encoding='ascii')\n"
        f"child = {descendant!r}\n"
        "subprocess.Popen(\n"
        "    [sys.executable, '-c', child],\n"
        "    stdin=subprocess.DEVNULL,\n"
        "    stdout=subprocess.DEVNULL,\n"
        "    stderr=subprocess.DEVNULL,\n"
        "    close_fds=True,\n"
        ")\n"
        "time.sleep(60)\n",
        encoding="utf-8",
    )
    child_code = (
        "import importlib.util, json, pathlib, sys; "
        f"module_path=pathlib.Path({str(MODULE_PATH)!r}); "
        "spec=importlib.util.spec_from_file_location('tree_timeout_probe', module_path); "
        "module=importlib.util.module_from_spec(spec); "
        "sys.modules['tree_timeout_probe']=module; "
        "spec.loader.exec_module(module); "
        f"module.ROOT=pathlib.Path({str(tmp_path)!r}); "
        "result=module.probe_agent_ecosystem(timeout=1); "
        "print(json.dumps({"
        "'passed': result.passed, 'details': result.details, "
        "'root_cause': result.root_cause}), flush=True)"
    )
    supports_process_groups = os.name == "posix" and hasattr(os, "killpg")
    proc = subprocess.Popen(
        [sys.executable, "-c", child_code],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="backslashreplace",
        start_new_session=supports_process_groups,
    )
    retained_pids = {proc.pid}
    cleanup_remaining: list[int] = []
    try:
        stdout, stderr = proc.communicate(timeout=5)
        assert proc.returncode == 0, stderr
        result = json.loads(stdout)
        marker_deadline = time.monotonic() + 1.0
        while time.monotonic() < marker_deadline and not marker.exists():
            time.sleep(0.02)
        descendant_survived = marker.exists()
    finally:
        direct_pid = _read_fixture_pid(direct_pid_file)
        descendant_pid = _read_fixture_pid(pid_file)
        retained_pids.update(
            pid for pid in (direct_pid, descendant_pid) if pid is not None
        )
        cleanup_remaining = _terminate_fixture_process_tree(
            proc,
            retained_pids,
            isolated_process_group=supports_process_groups,
        )

    assert direct_pid is not None, "fixture direct child did not publish its PID"
    assert descendant_pid is not None, "fixture descendant did not publish its PID"
    assert not cleanup_remaining, f"test cleanup left fixture PIDs alive: {cleanup_remaining}"
    assert result["passed"] is False
    diagnostic = result["details"] + " " + (result["root_cause"] or "")
    assert "timed out" in diagnostic.lower()
    assert not descendant_survived, "timed-out direct child left a live descendant process"


def test_timeout_reaps_explicit_posix_setsid_descendant(
    tmp_path: Path,
) -> None:
    """Cover one observed direct POSIX setsid child, not arbitrary daemons."""
    if os.name != "posix" or not hasattr(os, "killpg") or not hasattr(os, "getsid"):
        pytest.skip("new-session descendant cleanup requires POSIX session primitives")

    scripts = tmp_path / "scripts"
    scripts.mkdir()
    marker = tmp_path / "new-session-descendant-survived.txt"
    direct_pid_file = tmp_path / "new-session-direct.pid"
    direct_sid_file = tmp_path / "new-session-direct.sid"
    descendant_pid_file = tmp_path / "new-session-descendant.pid"
    descendant_sid_file = tmp_path / "new-session-descendant.sid"
    checker = scripts / "sync_ai_agent_ecosystem.py"
    descendant = (
        "import os, pathlib, time; "
        f"pathlib.Path({str(descendant_pid_file)!r}).write_text(str(os.getpid()), encoding='ascii'); "
        f"pathlib.Path({str(descendant_sid_file)!r}).write_text(str(os.getsid(0)), encoding='ascii'); "
        "time.sleep(1.50); "
        f"pathlib.Path({str(marker)!r}).write_text('survived', encoding='ascii'); "
        "time.sleep(60)"
    )
    checker.write_text(
        "import os, pathlib, subprocess, sys, time\n"
        f"pathlib.Path({str(direct_pid_file)!r}).write_text(str(os.getpid()), encoding='ascii')\n"
        f"pathlib.Path({str(direct_sid_file)!r}).write_text(str(os.getsid(0)), encoding='ascii')\n"
        f"child = {descendant!r}\n"
        "subprocess.Popen(\n"
        "    [sys.executable, '-c', child],\n"
        "    stdin=subprocess.DEVNULL,\n"
        "    stdout=subprocess.DEVNULL,\n"
        "    stderr=subprocess.DEVNULL,\n"
        "    close_fds=True,\n"
        "    start_new_session=True,\n"
        ")\n"
        "time.sleep(60)\n",
        encoding="utf-8",
    )
    child_code = (
        "import importlib.util, json, pathlib, sys; "
        f"module_path=pathlib.Path({str(MODULE_PATH)!r}); "
        "spec=importlib.util.spec_from_file_location('new_session_timeout_probe', module_path); "
        "module=importlib.util.module_from_spec(spec); "
        "sys.modules['new_session_timeout_probe']=module; "
        "spec.loader.exec_module(module); "
        f"result=module._run_cmd([sys.executable, {str(checker)!r}], cwd=pathlib.Path({str(tmp_path)!r}), timeout=1); "
        "print(json.dumps({'returncode': result[0], 'stdout': result[1], 'stderr': result[2]}), flush=True)"
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", child_code],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="backslashreplace",
        start_new_session=True,
    )
    retained_pids = {proc.pid}
    cleanup_remaining: list[int] = []
    direct_pid: int | None = None
    descendant_pid: int | None = None
    direct_sid: int | None = None
    descendant_sid: int | None = None
    try:
        stdout, stderr = proc.communicate(timeout=5)
        assert proc.returncode == 0, stderr
        result = json.loads(stdout)
        marker_deadline = time.monotonic() + 1.25
        while time.monotonic() < marker_deadline and not marker.exists():
            time.sleep(0.02)
        descendant_survived = marker.exists()
    finally:
        direct_pid = _read_fixture_pid(direct_pid_file)
        descendant_pid = _read_fixture_pid(descendant_pid_file)
        direct_sid = _read_fixture_pid(direct_sid_file)
        descendant_sid = _read_fixture_pid(descendant_sid_file)
        retained_pids.update(
            pid for pid in (direct_pid, descendant_pid) if pid is not None
        )
        cleanup_remaining = _terminate_fixture_process_tree(
            proc,
            retained_pids,
            isolated_process_group=True,
        )

    assert direct_pid is not None, "fixture direct child did not publish its PID"
    assert descendant_pid is not None, "fixture descendant did not publish its PID"
    assert direct_sid == direct_pid, "direct child was not the expected session leader"
    assert descendant_sid == descendant_pid, "descendant did not create a new session"
    assert descendant_sid != direct_sid, "fixture did not escape the direct process session"
    assert not cleanup_remaining, f"test cleanup left fixture PIDs alive: {cleanup_remaining}"
    assert result["returncode"] == 124
    assert "timed out" in result["stderr"].lower()
    assert not descendant_survived, "new-session descendant escaped timeout cleanup"


def test_subprocess_capture_is_bounded_before_communicate(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    if os.name != "posix" or not hasattr(os, "killpg"):
        pytest.skip("bounded dual-pipe capture contract requires POSIX process groups")

    real_popen = subprocess.Popen
    proxies: list[_NoCommunicateProxy] = []

    def guarded_popen(*args: object, **kwargs: object) -> _NoCommunicateProxy:
        process = real_popen(*args, **kwargs)
        proxy = _NoCommunicateProxy(process)
        proxies.append(proxy)
        return proxy

    monkeypatch.setattr(triage.subprocess, "Popen", guarded_popen)
    repetitions = (triage.MAX_COMMAND_OUTPUT_CHARS * 5 // 1_024) + 1
    child = (
        "import os; "
        f"[(os.write(1, b'O' * 1024), os.write(2, b'E' * 1024)) for _ in range({repetitions})]"
    )

    try:
        returncode, stdout, stderr = triage._run_cmd(
            [sys.executable, "-c", child],
            cwd=tmp_path,
            timeout=5,
        )
    finally:
        for proxy in proxies:
            process = proxy._process
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=1)

    assert proxies, "subprocess capture fixture was not invoked"
    assert proxies[0].communicate_calls == 0
    assert returncode == 0
    assert len(stdout) <= triage.MAX_COMMAND_OUTPUT_CHARS
    assert len(stderr) <= triage.MAX_COMMAND_OUTPUT_CHARS
    assert "[truncated]" in stdout
    assert "[truncated]" in stderr


def test_posix_subprocess_probe_contract_remains_supported(
    triage: ModuleType,
) -> None:
    if os.name != "posix":
        pytest.skip("POSIX subprocess support requires a POSIX test host")

    returncode, stdout, stderr = triage._run_cmd(
        [
            sys.executable,
            "-c",
            "import sys; sys.stdout.write('POSIX-PROBE-SUPPORTED')",
        ],
        cwd=ROOT,
        timeout=5,
    )

    assert returncode == 0, stderr
    assert stdout == "POSIX-PROBE-SUPPORTED"
    assert stderr == ""


def test_non_posix_subprocess_boundary_is_stable_and_fails_before_spawn(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    forbidden_popen = MagicMock(
        side_effect=AssertionError("subprocess.Popen crossed non-POSIX boundary")
    )
    forbidden_run = MagicMock(
        side_effect=AssertionError("subprocess.run crossed non-POSIX boundary")
    )
    monkeypatch.setattr(triage.os, "name", "nt")
    monkeypatch.setattr(triage.subprocess, "Popen", forbidden_popen)
    monkeypatch.setattr(triage.subprocess, "run", forbidden_run)

    first = triage._run_cmd(["must-not-run"], cwd=tmp_path, timeout=1)
    second = triage._run_cmd(["must-not-run"], cwd=tmp_path, timeout=1)

    assert first == second, "unsupported-platform failure must be stable"
    returncode, stdout, stderr = first
    assert returncode != 0
    assert stdout == ""
    stderr.encode("ascii")
    diagnostic = stderr.lower()
    assert "unsupported" in diagnostic
    assert "platform" in diagnostic
    assert "posix" in diagnostic
    assert forbidden_popen.call_count == 0
    assert forbidden_run.call_count == 0


def test_non_posix_report_and_cli_fail_closed_without_spawning(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    forbidden_popen = MagicMock(
        side_effect=AssertionError("subprocess.Popen crossed non-POSIX boundary")
    )
    forbidden_run = MagicMock(
        side_effect=AssertionError("subprocess.run crossed non-POSIX boundary")
    )
    monkeypatch.setattr(triage.os, "name", "nt")
    monkeypatch.setattr(triage.subprocess, "Popen", forbidden_popen)
    monkeypatch.setattr(triage.subprocess, "run", forbidden_run)

    report = triage.run_triage(fail_fast=True, skip_remote=True, timeout=1)

    assert report.overall_status == "FAILED"
    assert report.failed_probes == 1
    assert len(report.probes) == 1
    assert report.probes[0].passed is False
    report_diagnostic = (
        report.probes[0].details + " " + (report.probes[0].root_cause or "")
    ).lower()
    assert "unsupported" in report_diagnostic
    assert "platform" in report_diagnostic
    assert "posix" in report_diagnostic

    exit_code = triage.main(["--skip-remote", "--json", "--timeout", "1"])
    rendered = capsys.readouterr().out
    rendered.encode("ascii")
    payload = json.loads(rendered)

    assert exit_code != 0
    assert payload["overall_status"] == "FAILED"
    assert payload["failed_probes"] == 1
    assert payload["probes"][0]["passed"] is False
    cli_diagnostic = (
        payload["probes"][0]["details"]
        + " "
        + (payload["probes"][0]["root_cause"] or "")
    ).lower()
    assert "unsupported" in cli_diagnostic
    assert "platform" in cli_diagnostic
    assert "posix" in cli_diagnostic
    assert forbidden_popen.call_count == 0
    assert forbidden_run.call_count == 0


def test_http_connect_and_body_share_one_monotonic_deadline(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo, identity = _release_repo(tmp_path)
    clock = _Clock()
    open_timeouts: list[float] = []
    read_sizes: list[int] = []

    def respond(request: object, *, timeout: float) -> _Response:
        open_timeouts.append(float(timeout))
        clock.advance(1.2)
        url = _url(request)
        payload: object = identity
        if url.endswith("/health"):
            payload = {
                "status": "ok",
                "version": identity["version"],
                "git_commit": identity["release_source_commit"],
            }
        return _Response(payload, clock=clock, read_sizes=read_sizes)

    monkeypatch.setattr(triage, "ROOT", repo)
    monkeypatch.setattr(triage, "time", SimpleNamespace(monotonic=clock.monotonic))
    monkeypatch.setattr(triage.urllib.request, "urlopen", respond)

    result = triage.probe_live_production_endpoints(timeout=5)

    assert result.passed is False
    assert len(open_timeouts) >= 2
    assert all(later < earlier for earlier, later in zip(open_timeouts, open_timeouts[1:]))
    assert read_sizes
    assert all(0 <= size <= triage.MAX_HTTP_BODY_BYTES + 1 for size in read_sizes)
    diagnostic = result.details + " " + (result.root_cause or "")
    assert "deadline" in diagnostic.lower() or "timeout" in diagnostic.lower()


def test_http_body_processing_has_a_per_response_byte_cap(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo, _identity_value = _release_repo(tmp_path)
    oversized = b'{"padding":"' + b"x" * (triage.MAX_HTTP_BODY_BYTES + 1)
    responses: list[_Response] = []

    def respond(*_args: object, **_kwargs: object) -> _Response:
        response = _Response(oversized)
        responses.append(response)
        return response

    monkeypatch.setattr(triage, "ROOT", repo)
    monkeypatch.setattr(triage.urllib.request, "urlopen", respond)

    result = triage.probe_live_production_endpoints(timeout=5)

    assert result.passed is False
    assert responses
    assert all(
        sum(response.read_chunks) <= triage.MAX_HTTP_BODY_BYTES + 1
        for response in responses
    )
    assert "size" in result.details.lower() or "body" in result.details.lower()


@pytest.mark.parametrize("root_name", ["rust_core", "TDD-HORO-v3.0"])
def test_python_scan_covers_each_governed_tracked_root(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    root_name: str,
) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    invalid = repo / root_name / "governed_invalid.py"
    invalid.parent.mkdir(parents=True)
    invalid.write_text("def broken(:\n    pass\n", encoding="utf-8")
    _commit_all(repo, f"track {root_name}")
    monkeypatch.setattr(triage, "ROOT", repo)

    result = triage.probe_python_syntax(timeout=5)

    assert result.passed is False
    assert root_name in result.details


@pytest.mark.parametrize(
    "invalid_source",
    ["return\n", "break\n", "continue\n", "await value\n"],
)
def test_python_scan_uses_compile_semantics_for_module_control_flow(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    invalid_source: str,
) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    invalid = repo / "scripts" / "invalid_control_flow.py"
    invalid.parent.mkdir(parents=True)
    invalid.write_text(invalid_source, encoding="utf-8")
    _commit_all(repo, "track compile-invalid module")
    monkeypatch.setattr(triage, "ROOT", repo)

    result = triage.probe_python_syntax(timeout=5)

    assert result.passed is False
    assert "invalid_control_flow.py" in result.details


def test_python_scan_does_not_follow_tracked_symlink_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    outside = tmp_path / "outside.py"
    outside.write_text("outside_value = 1\n", encoding="utf-8")
    link = repo / "scripts" / "outside_link.py"
    link.parent.mkdir(parents=True)
    link.symlink_to(outside)
    _commit_all(repo, "track symlink")
    child_code = f"""
import importlib.util
import json
import os
import pathlib
import sys

module_path = pathlib.Path({str(MODULE_PATH)!r})
spec = importlib.util.spec_from_file_location("symlink_safety_probe", module_path)
module = importlib.util.module_from_spec(spec)
sys.modules["symlink_safety_probe"] = module
spec.loader.exec_module(module)
module.ROOT = pathlib.Path({str(repo)!r})

link_path = os.path.abspath({str(link)!r})
outside_path = os.path.abspath({str(outside)!r})
unsafe_accesses = []
original_stat = os.stat


class UnsafeExternalTargetAccess(RuntimeError):
    pass


def lexical_path(value):
    try:
        return os.path.abspath(os.fspath(value))
    except TypeError:
        return None


def reject_access(api, candidate):
    unsafe_accesses.append(f"{{api}}:{{candidate}}")
    raise UnsafeExternalTargetAccess(f"{{api}} attempted external symlink access")


def guarded_stat(path, *args, **kwargs):
    candidate = lexical_path(path)
    follows = kwargs.get("follow_symlinks", True)
    if candidate == outside_path or (candidate == link_path and follows):
        reject_access("os.stat", candidate)
    return original_stat(path, *args, **kwargs)


def audit(event, args):
    if event != "open" or not args:
        return
    candidate = lexical_path(args[0])
    if candidate not in {{link_path, outside_path}}:
        return
    flags = args[2] if len(args) > 2 else 0
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if candidate == link_path and nofollow and isinstance(flags, int) and flags & nofollow:
        return
    reject_access("open", candidate)


os.stat = guarded_stat
sys.addaudithook(audit)
payload = {{"unsafe_accesses": unsafe_accesses, "error": None}}
try:
    result = module.probe_python_syntax(timeout=5)
    payload["passed"] = result.passed
    payload["details"] = result.details
    payload["root_cause"] = result.root_cause
except BaseException as exc:
    payload["error"] = f"{{type(exc).__name__}}: {{exc}}"
print(json.dumps(payload, sort_keys=True), flush=True)
"""
    completed = subprocess.run(
        [sys.executable, "-c", child_code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="backslashreplace",
        timeout=5,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["unsafe_accesses"] == [], (
        "governed scan dereferenced or opened a tracked external symlink target: "
        f"{payload['unsafe_accesses']}"
    )
    assert payload["error"] is None, (
        "tracked final symlinks must return a fail-closed ProbeResult, not raise: "
        f"{payload['error']}"
    )
    assert payload["passed"] is False


def test_python_scan_rejects_intermediate_parent_symlink_escape(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    tracked_parent = repo / "scripts" / "nested"
    tracked_parent.mkdir(parents=True)
    escaped_path = tracked_parent / "escaped.py"
    escaped_path.write_text("inside_value = 1\n", encoding="utf-8")
    _commit_all(repo, "track nested governed module")

    outside_parent = tmp_path / "outside-parent"
    outside_parent.mkdir()
    outside_path = outside_parent / escaped_path.name
    outside_path.write_text("outside_value = 1\n", encoding="utf-8")
    escaped_path.unlink()
    tracked_parent.rmdir()
    tracked_parent.symlink_to(outside_parent, target_is_directory=True)
    assert _git(repo, "ls-files", "--", "scripts/nested/escaped.py") == (
        "scripts/nested/escaped.py"
    )

    child_code = f"""
import importlib.util
import json
import os
import pathlib
import sys

module_path = pathlib.Path({str(MODULE_PATH)!r})
spec = importlib.util.spec_from_file_location("parent_symlink_safety_probe", module_path)
module = importlib.util.module_from_spec(spec)
sys.modules["parent_symlink_safety_probe"] = module
spec.loader.exec_module(module)
module.ROOT = pathlib.Path({str(repo)!r})

escaped_path = os.path.abspath({str(escaped_path)!r})
outside_path = os.path.abspath({str(outside_path)!r})
unsafe_accesses = []
original_lstat = os.lstat
original_stat = os.stat


class UnsafeExternalTraversal(RuntimeError):
    pass


def lexical_path(value):
    try:
        return os.path.abspath(os.fspath(value))
    except TypeError:
        return None


def reject_access(api, candidate):
    unsafe_accesses.append(f"{{api}}:{{candidate}}")
    raise UnsafeExternalTraversal(f"{{api}} traversed an intermediate symlink")


def guarded_lstat(path, *args, **kwargs):
    candidate = lexical_path(path)
    if candidate in {{escaped_path, outside_path}}:
        reject_access("os.lstat", candidate)
    return original_lstat(path, *args, **kwargs)


def guarded_stat(path, *args, **kwargs):
    candidate = lexical_path(path)
    if candidate in {{escaped_path, outside_path}}:
        reject_access("os.stat", candidate)
    return original_stat(path, *args, **kwargs)


def audit(event, args):
    if event != "open" or not args:
        return
    candidate = lexical_path(args[0])
    if candidate in {{escaped_path, outside_path}}:
        reject_access("open", candidate)


os.lstat = guarded_lstat
os.stat = guarded_stat
sys.addaudithook(audit)
payload = {{"unsafe_accesses": unsafe_accesses, "error": None}}
try:
    result = module.probe_python_syntax(timeout=5)
    payload["passed"] = result.passed
    payload["details"] = result.details
    payload["root_cause"] = result.root_cause
except BaseException as exc:
    payload["error"] = f"{{type(exc).__name__}}: {{exc}}"
print(json.dumps(payload, sort_keys=True), flush=True)
"""
    completed = subprocess.run(
        [sys.executable, "-c", child_code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="backslashreplace",
        timeout=5,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["unsafe_accesses"] == [], (
        "scanner traversed a tracked path through an intermediate parent symlink: "
        f"{payload['unsafe_accesses']}"
    )
    assert payload["error"] is None, (
        "an intermediate parent symlink must return a fail-closed ProbeResult: "
        f"{payload['error']}"
    )
    assert payload["passed"] is False
    diagnostic = (payload["details"] + " " + (payload["root_cause"] or "")).lower()
    assert any(term in diagnostic for term in ("symlink", "outside", "contain", "root"))


def test_python_scan_never_blocks_on_special_files(tmp_path: Path) -> None:
    if not hasattr(os, "mkfifo"):
        pytest.skip("FIFO process probe requires POSIX")
    repo = tmp_path / "repo"
    _init_repo(repo)
    scripts = repo / "scripts"
    scripts.mkdir(parents=True)
    fifo = scripts / "special.py"
    fifo.write_text("tracked_value = 1\n", encoding="utf-8")
    _commit_all(repo, "track governed FIFO candidate")
    fifo.unlink()
    os.mkfifo(fifo)
    assert _git(repo, "ls-files", "--", "scripts/special.py") == "scripts/special.py"
    child_code = (
        "import importlib.util, json, pathlib, sys; "
        f"module_path=pathlib.Path({str(MODULE_PATH)!r}); "
        "spec=importlib.util.spec_from_file_location('fifo_safety_probe', module_path); "
        "module=importlib.util.module_from_spec(spec); "
        "sys.modules['fifo_safety_probe']=module; "
        "spec.loader.exec_module(module); "
        f"module.ROOT=pathlib.Path({str(repo)!r}); "
        "payload={'error': None}; "
        "\ntry:\n"
        " result=module.probe_python_syntax(timeout=1); "
        " payload.update({'passed': result.passed, 'details': result.details, "
        "'root_cause': result.root_cause})\n"
        "except BaseException as exc:\n"
        " payload['error']=f'{type(exc).__name__}: {exc}'\n"
        "print(json.dumps(payload, sort_keys=True), flush=True)"
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", child_code],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="backslashreplace",
        start_new_session=True,
    )
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=3)
    except subprocess.TimeoutExpired:
        timed_out = True
    finally:
        cleanup_remaining = _terminate_fixture_process_tree(
            proc,
            {proc.pid},
            isolated_process_group=True,
        )
    if timed_out:
        stdout, stderr = proc.communicate(timeout=2)

    assert not cleanup_remaining, f"test cleanup left FIFO probe PIDs alive: {cleanup_remaining}"
    assert not timed_out, "syntax probe blocked on FIFO special file beyond 3 seconds"
    assert proc.returncode == 0, stderr
    payload = json.loads(stdout)
    assert payload["error"] is None
    assert payload["passed"] is False
    diagnostic = (payload["details"] + " " + (payload["root_cause"] or "")).lower()
    assert "special.py" in diagnostic
    assert any(term in diagnostic for term in ("fifo", "special", "regular", "file type"))


@pytest.mark.parametrize("revision_mode", ["missing", "non_ancestor"])
def test_release_identity_revision_must_exist_and_ancestor_packaging_commit(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    revision_mode: str,
) -> None:
    repo, identity = _release_repo(tmp_path, revision_mode)
    opener = MagicMock(side_effect=lambda request, **_kwargs: _matching_response(identity, request))
    monkeypatch.setattr(triage, "ROOT", repo)
    monkeypatch.setattr(triage.urllib.request, "urlopen", opener)

    result = triage.probe_live_production_endpoints(timeout=5)

    assert result.passed is False
    assert opener.call_count == 0, "remote equality ran before local revision ancestry proof"
    evidence = result.details + " " + (result.root_cause or "")
    assert "revision" in evidence.lower() or "ancestor" in evidence.lower()


def test_release_identity_without_git_metadata_fails_closed_before_http(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "candidate-without-git"
    root.mkdir()
    identity = _identity("a" * 40)
    _write_identity(root, identity)
    calls: list[str] = []

    def respond(request: object, **_kwargs: object) -> _Response:
        calls.append(_url(request))
        return _matching_response(identity, request)

    monkeypatch.setattr(triage, "ROOT", root)
    monkeypatch.setattr(triage.urllib.request, "urlopen", respond)

    result = triage.probe_live_production_endpoints(timeout=5)

    assert result.passed is False
    assert calls == [], "remote equality checks ran without local Git provenance"
    diagnostic = (result.details + " " + (result.root_cause or "")).lower()
    assert "git" in diagnostic
    assert "metadata" in diagnostic or "repository" in diagnostic


@pytest.mark.parametrize("variant", ["prefix", "suffix", "duplicate"])
def test_local_machine_input_is_one_strict_json_document(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    variant: str,
) -> None:
    repo, identity = _release_repo(tmp_path)
    _write_identity(repo, identity, _json_variant(identity, variant))
    opener = MagicMock()
    monkeypatch.setattr(triage, "ROOT", repo)
    monkeypatch.setattr(triage.urllib.request, "urlopen", opener)

    result = triage.probe_live_production_endpoints(timeout=5)

    assert result.passed is False
    assert opener.call_count == 0
    assert "malformed" in result.details.lower() or "invalid" in result.details.lower()


@pytest.mark.parametrize("variant", ["prefix", "suffix", "duplicate"])
def test_http_machine_input_is_one_strict_json_document(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    variant: str,
) -> None:
    repo, identity = _release_repo(tmp_path)
    bad_document = _json_variant(identity, variant)

    def respond(request: object, **_kwargs: object) -> _Response:
        url = _url(request)
        if "vercel.app/version.json" in url:
            return _Response(bad_document)
        return _matching_response(identity, request)

    monkeypatch.setattr(triage, "ROOT", repo)
    monkeypatch.setattr(triage.urllib.request, "urlopen", respond)

    result = triage.probe_live_production_endpoints(timeout=5)

    assert result.passed is False
    assert "Vercel UI" in result.details


def test_argparse_error_is_ascii_for_arbitrary_unicode_argument() -> None:
    completed = subprocess.run(
        [sys.executable, str(MODULE_PATH), "--unknown-\u0e04\u0e27\u0e32\u0e21\u0e25\u0e31\u0e1a-\U0001f680"],
        cwd=ROOT,
        capture_output=True,
        timeout=5,
        check=False,
    )

    assert completed.returncode == 2
    completed.stdout.decode("ascii")
    completed.stderr.decode("ascii")
    assert len(completed.stdout) + len(completed.stderr) <= 8_192


def test_git_diagnostic_redacts_secrets_but_keeps_fingerprint(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_git = fake_bin / "git"
    diagnostic = (
        "fatal GIT-E42 https://alice:git-pass@example.invalid/repo"
        "?access_token=query-secret Authorization: Bearer bearer-secret"
    )
    fake_git.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        f"sys.stderr.write({diagnostic!r} + '\\n')\n"
        "raise SystemExit(1)\n",
        encoding="utf-8",
    )
    fake_git.chmod(0o755)
    monkeypatch.setenv("PATH", str(fake_bin) + os.pathsep + os.environ["PATH"])
    monkeypatch.setattr(triage, "ROOT", tmp_path)

    result = triage.probe_git_truth(skip_remote=True, timeout=5)
    human, machine = _render_both_reports(triage, result, monkeypatch, capsys)
    rendered = human + machine

    assert "GIT-E42" in rendered
    for secret in ("git-pass", "query-secret", "bearer-secret"):
        assert secret not in rendered


def test_scanner_diagnostic_redacts_secrets_but_keeps_fingerprint(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    scanner = tmp_path / "project" / "core" / "code_reviewer.py"
    scanner.parent.mkdir(parents=True)
    diagnostic = "SCAN-E17 token=scanner-secret api_key=scanner-key"
    scanner.write_text(
        "import sys\n"
        f"sys.stderr.write({diagnostic!r} + '\\n')\n"
        "raise SystemExit(1)\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(triage, "ROOT", tmp_path)

    result = triage.probe_secret_security(timeout=5)
    human, machine = _render_both_reports(triage, result, monkeypatch, capsys)
    rendered = human + machine

    assert "SCAN-E17" in rendered
    for secret in ("scanner-secret", "scanner-key"):
        assert secret not in rendered


def test_http_diagnostic_redacts_secrets_but_keeps_fingerprint(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    repo, _identity_value = _release_repo(tmp_path)
    diagnostic = (
        "HTTP-E29 GET https://bob:http-pass@example.invalid/version.json"
        "?token=http-query Authorization=Bearer http-bearer"
    )

    def fail_http(*_args: object, **_kwargs: object) -> Any:
        raise urllib.error.URLError(diagnostic)

    monkeypatch.setattr(triage, "ROOT", repo)
    monkeypatch.setattr(triage.urllib.request, "urlopen", fail_http)

    result = triage.probe_live_production_endpoints(timeout=5)
    human, machine = _render_both_reports(triage, result, monkeypatch, capsys)
    rendered = human + machine

    assert "HTTP-E29" in rendered
    for secret in ("http-pass", "http-query", "http-bearer"):
        assert secret not in rendered


def test_basic_aws_and_sensitive_metadata_canaries_are_fully_redacted(
    triage: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    basic_canary = "".join(("basic", "-", "runtime", "-", "canary"))
    aws_canary = "".join(("aws", "-", "runtime", "-", "canary"))
    nested_basic_canary = "".join(("nested", "-", "basic", "-", "canary"))
    nested_secret_canary = "".join(("nested", "-", "secret", "-", "canary"))
    result = triage.ProbeResult(
        probe_id="redaction_contract",
        name="Redaction Contract",
        passed=False,
        details=(
            f"AUTH-E91 Authorization: Basic {basic_canary}; "
            f"AWS_SECRET_ACCESS_KEY={aws_canary}"
        ),
        root_cause="credential-shaped diagnostics must be sanitized",
        remediation_command="inspect sanitized report",
        metadata={
            "AWS_SECRET_ACCESS_KEY": aws_canary,
            "nested": {
                "authorization": f"Basic {nested_basic_canary}",
                "client_secret": nested_secret_canary,
            },
        },
    )

    human, machine = _render_both_reports(triage, result, monkeypatch, capsys)
    rendered = human + machine

    assert "AUTH-E91" in rendered
    assert "[REDACTED]" in rendered
    for canary in (
        basic_canary,
        aws_canary,
        nested_basic_canary,
        nested_secret_canary,
    ):
        assert canary not in rendered
    assert "Basic " not in rendered


def test_posix_only_cli_and_operational_docs_state_the_closed_contract() -> None:
    completed = subprocess.run(
        [sys.executable, str(MODULE_PATH), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=5,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    help_text = " ".join(completed.stdout.split())
    help_text.encode("ascii")
    missing: list[str] = []
    for label, fragment in {
        "CLI: POSIX-only": "posix-only",
        "CLI: os.killpg": "os.killpg",
        "CLI: fail-closed unsupported platform": (
            "unsupported platforms fail closed before subprocess execution"
        ),
    }.items():
        if fragment not in help_text.lower():
            missing.append(label)
    for relative in ("README.md", "HOWTO.md"):
        document = " ".join((ROOT / relative).read_text(encoding="utf-8").split())
        lowered = document.lower()
        required_fragments = {
            "POSIX-only": "posix-only",
            "os.killpg": "os.killpg",
            "verify-pr command": "test_provenance_guard.py verify-pr",
            "immutable base": "git rev-parse origin/main",
            "immutable head": "git rev-parse head",
            "base argument": "--base",
            "head argument": "--head",
        }
        for label, fragment in required_fragments.items():
            if fragment not in lowered:
                missing.append(f"{relative}: {label}")
    assert not missing, "missing operational contract: " + ", ".join(missing)
