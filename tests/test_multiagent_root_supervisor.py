"""Frozen local lifecycle contract for the independent-root supervisor."""

from __future__ import annotations

import importlib
import json
import os
import stat
from collections.abc import Mapping
from pathlib import Path

import pytest


@pytest.fixture
def supervisor_module():
    return importlib.import_module("scripts.multiagent_root_supervisor")


@pytest.fixture
def dq():
    return importlib.import_module("scripts.multiagent_durable_queue")


@pytest.fixture
def state_dir(tmp_path: Path) -> Path:
    return tmp_path / "xdg" / "horoconsultant" / "repo-digest"


def _field(value: object, name: str):
    if isinstance(value, Mapping):
        return value[name]
    return getattr(value, name)


class FakeProcess:
    _next_pid = 41000

    def __init__(self, root: str, instance_id: str) -> None:
        type(self)._next_pid += 1
        self.pid = type(self)._next_pid
        self.root = root
        self.instance_id = instance_id
        self.alive = True
        self.signals: list[str] = []

    def terminate(self) -> None:
        self.signals.append("terminate")
        self.alive = False

    def kill(self) -> None:
        self.signals.append("kill")
        self.alive = False

    def poll(self):
        return None if self.alive else 0


class ProcessFactory:
    def __init__(self) -> None:
        self.processes: list[FakeProcess] = []

    def __call__(self, *, root: str, instance_id: str, **_kwargs) -> FakeProcess:
        process = FakeProcess(root, instance_id)
        self.processes.append(process)
        return process

    def probe(self, pid: int) -> bool:
        return any(process.pid == pid and process.alive for process in self.processes)


def _supervisor(supervisor_module, state_dir, **kwargs):
    return supervisor_module.RootSupervisor(state_dir=state_dir, **kwargs)


def test_parser_exposes_the_locked_supervisor_command_surface(supervisor_module) -> None:
    parser = supervisor_module.build_parser()
    commands = {
        action.dest: set(action.choices)
        for action in parser._actions
        if getattr(action, "choices", None)
    }

    assert set.union(*commands.values()) >= {
        "doctor",
        "init",
        "start",
        "submit",
        "status",
        "wait",
        "smoke-all",
        "seal-bootstrap",
        "drain",
        "stop",
    }
    assert parser.parse_args(["doctor", "--repair-home-permissions"]).command == "doctor"
    start = parser.parse_args(
        ["start", "--bootstrap-local-unsafe", "--accept-risk", "risk-123"]
    )
    assert start.bootstrap_local_unsafe is True
    assert start.accept_risk == "risk-123"
    assert parser.parse_args(["stop", "--drain"]).drain is True


def test_state_dir_resolution_is_repo_scoped_and_override_must_be_absolute(
    supervisor_module, tmp_path
) -> None:
    repo = tmp_path / "repo"
    xdg = tmp_path / "state"
    repo.mkdir()
    resolved = supervisor_module.resolve_state_dir(
        repo_root=repo,
        environ={"XDG_STATE_HOME": str(xdg)},
    )

    assert resolved.parent.parent == xdg
    assert resolved.parent.name == "horoconsultant"
    assert resolved.name != repo.name
    assert resolved.name.isascii()
    with pytest.raises(supervisor_module.SupervisorError):
        supervisor_module.resolve_state_dir(
            repo_root=repo,
            environ={"HORO_MULTIAGENT_STATE_DIR": "relative/path"},
        )


def test_init_creates_private_state_database_and_is_idempotent(
    supervisor_module, state_dir
) -> None:
    supervisor = _supervisor(supervisor_module, state_dir)

    first = supervisor.init()
    second = supervisor.init()

    assert _field(first, "state_dir") == _field(second, "state_dir") == str(state_dir)
    assert stat.S_IMODE(state_dir.stat().st_mode) == 0o700
    assert stat.S_IMODE(supervisor.queue.path.stat().st_mode) == 0o600


def test_doctor_reports_home_mode_without_reading_contents(
    supervisor_module, state_dir, tmp_path, monkeypatch
) -> None:
    home = tmp_path / "account-home"
    home.mkdir(mode=0o755)
    secret = home / "credential.json"
    secret.write_text("must-not-be-read", encoding="utf-8")
    reads: list[Path] = []
    original_read_bytes = Path.read_bytes

    def audit_read(path: Path):
        reads.append(path)
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", audit_read)
    supervisor = _supervisor(supervisor_module, state_dir, account_homes={"codex1": home})

    report = supervisor.doctor(repair_home_permissions=False)

    assert _field(report, "ok") is False
    assert _field(report, "code") == "ACCOUNT_HOME_PERMISSIONS"
    assert secret not in reads
    assert stat.S_IMODE(home.stat().st_mode) == 0o755


def test_doctor_repairs_only_owned_non_symlink_home_from_0755_to_0700(
    supervisor_module, state_dir, tmp_path
) -> None:
    home = tmp_path / "account-home"
    home.mkdir(mode=0o755)
    supervisor = _supervisor(supervisor_module, state_dir, account_homes={"codex1": home})

    report = supervisor.doctor(repair_home_permissions=True)

    assert _field(report, "ok") is True
    assert stat.S_IMODE(home.stat().st_mode) == 0o700


def test_doctor_never_repairs_symlink_or_foreign_owner(
    supervisor_module, state_dir, tmp_path, monkeypatch
) -> None:
    real_home = tmp_path / "real-home"
    real_home.mkdir(mode=0o755)
    linked_home = tmp_path / "linked-home"
    linked_home.symlink_to(real_home, target_is_directory=True)
    supervisor = _supervisor(
        supervisor_module, state_dir, account_homes={"codex1": linked_home}
    )

    with pytest.raises(supervisor_module.SupervisorError, match="symlink|owner"):
        supervisor.doctor(repair_home_permissions=True)
    assert stat.S_IMODE(real_home.stat().st_mode) == 0o755


def test_start_requires_explicit_risk_acceptance_for_unsafe_bootstrap(
    supervisor_module, state_dir
) -> None:
    supervisor = _supervisor(supervisor_module, state_dir, process_factory=ProcessFactory())
    supervisor.init()

    with pytest.raises(supervisor_module.SupervisorError, match="risk"):
        supervisor.start(bootstrap_local_unsafe=True, accept_risk=None)


def test_risk_acceptance_is_durable_explicit_and_never_promotes_quota_health(
    supervisor_module, state_dir
) -> None:
    factory = ProcessFactory()
    supervisor = _supervisor(
        supervisor_module,
        state_dir,
        process_factory=factory,
        pid_probe=factory.probe,
    )
    supervisor.init()

    started = supervisor.start(
        bootstrap_local_unsafe=True,
        accept_risk="risk-local-001",
        risk_statement="I accept local unknown/constrained quota risk",
    )
    acceptance = supervisor.queue.get_risk_acceptance("risk-local-001")

    assert _field(started, "bootstrap_mode") == "bootstrap-local-unsafe-v1"
    assert _field(acceptance, "acceptance_id") == "risk-local-001"
    assert _field(acceptance, "accepted_at")
    assert _field(acceptance, "quota_health") is None
    assert _field(acceptance, "warning")


def test_start_detaches_two_independent_roots_with_distinct_identity_and_pid(
    supervisor_module, state_dir
) -> None:
    factory = ProcessFactory()
    supervisor = _supervisor(
        supervisor_module,
        state_dir,
        process_factory=factory,
        pid_probe=factory.probe,
    )
    supervisor.init()

    status = supervisor.start()

    roots = {_field(item, "root"): item for item in _field(status, "roots")}
    assert set(roots) == {"A", "B"}
    assert _field(roots["A"], "pid") != _field(roots["B"], "pid")
    assert _field(roots["A"], "instance_id") != _field(roots["B"], "instance_id")
    assert all(_field(item, "detached") is True for item in roots.values())


def test_status_fails_closed_on_stale_pid_and_fences_stale_instance(
    supervisor_module, state_dir
) -> None:
    factory = ProcessFactory()
    supervisor = _supervisor(
        supervisor_module,
        state_dir,
        process_factory=factory,
        pid_probe=factory.probe,
    )
    supervisor.init()
    supervisor.start()
    factory.processes[1].alive = False

    status = supervisor.status()
    root_b = next(item for item in _field(status, "roots") if _field(item, "root") == "B")

    assert _field(root_b, "state") == "STALE"
    assert _field(root_b, "fenced") is True
    assert _field(status, "healthy") is False


def test_submit_and_wait_survive_supervisor_object_restart(
    supervisor_module, state_dir, tmp_path
) -> None:
    first = _supervisor(supervisor_module, state_dir)
    first.init()
    objective = tmp_path / "objective.txt"
    objective.write_text("inspect repository read-only", encoding="utf-8")
    submitted = first.submit(alias="codex1", ticket="IDQ-SMOKE-1", objective_file=objective)
    request_id = _field(submitted, "request_id")
    first.queue.record_fixture_result(
        request_id,
        result={"status": "DONE", "findings": []},
        receipt={"protocol_version": 2},
    )

    restarted = _supervisor(supervisor_module, state_dir)
    result = restarted.wait(request_id=request_id, timeout=1)

    assert _field(result, "request_id") == request_id
    assert _field(result, "status") == "DONE"


def test_drain_stops_new_claims_then_stop_preserves_database(
    supervisor_module, state_dir
) -> None:
    factory = ProcessFactory()
    supervisor = _supervisor(
        supervisor_module,
        state_dir,
        process_factory=factory,
        pid_probe=factory.probe,
    )
    supervisor.init()
    supervisor.start()
    database = supervisor.queue.path

    drain = supervisor.drain()
    stopped = supervisor.stop(drain=True)

    assert _field(drain, "accepting_submissions") is False
    assert _field(stopped, "running") is False
    assert database.exists()
    assert all(not process.alive for process in factory.processes)


def test_bootstrap_expires_on_stop_and_ordinary_restart_is_closed(
    supervisor_module, state_dir
) -> None:
    factory = ProcessFactory()
    supervisor = _supervisor(
        supervisor_module,
        state_dir,
        process_factory=factory,
        pid_probe=factory.probe,
    )
    supervisor.init()
    supervisor.start(
        bootstrap_local_unsafe=True,
        accept_risk="risk-local-001",
        risk_statement="accepted",
    )
    supervisor.stop(drain=True)

    restarted = supervisor.start()

    assert _field(restarted, "bootstrap_mode") == "CLOSED"
    assert _field(restarted, "risk_acceptance_id") is None


def test_seal_prevents_bootstrap_reuse_even_with_old_acceptance(
    supervisor_module, state_dir
) -> None:
    factory = ProcessFactory()
    supervisor = _supervisor(
        supervisor_module,
        state_dir,
        process_factory=factory,
        pid_probe=factory.probe,
    )
    supervisor.init()
    supervisor.start(
        bootstrap_local_unsafe=True,
        accept_risk="risk-local-001",
        risk_statement="accepted",
    )
    sealed = supervisor.seal_bootstrap()
    supervisor.stop(drain=True)

    assert _field(sealed, "sealed") is True
    with pytest.raises(supervisor_module.SupervisorError, match="sealed"):
        supervisor.start(
            bootstrap_local_unsafe=True,
            accept_risk="risk-local-001",
            risk_statement="accepted",
        )


def test_status_json_is_secret_free_and_marks_bootstrap_unverified(
    supervisor_module, state_dir
) -> None:
    factory = ProcessFactory()
    supervisor = _supervisor(
        supervisor_module,
        state_dir,
        process_factory=factory,
        pid_probe=factory.probe,
    )
    supervisor.init()
    supervisor.start(
        bootstrap_local_unsafe=True,
        accept_risk="risk-local-001",
        risk_statement="accepted",
    )

    encoded = json.dumps(supervisor.status(as_json=True), sort_keys=True)

    assert '"evidence_level": "bootstrap_unverified"' in encoded
    assert "warning" in encoded.lower()
    for forbidden in ("token", "cookie", "password", "raw_stream", "stdout", "stderr"):
        assert forbidden not in encoded.lower()
