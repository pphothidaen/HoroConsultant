"""RED contract for the real, bounded IDQ-MVP-080 provider executor.

The future source is deliberately isolated in
``scripts.multiagent_idq_mvp_080_operational``.  These tests use genuine local
QOBS artifacts, capacity leases, and the SQLite durable queue, but inject only
``Popen``-shaped fake processes.  They never resolve credentials, invoke a
provider, or retain provider streams.

Required public seam::

    execute_idq_mvp_080_operational(
        *, config, authorization, lanes, store, marker_store,
        repository_root, popen_factory, timeout_seconds, now
    )

The batch must validate every lane before the first process start.  A lane is
durably PREPARED, then STARTING immediately before ``Popen``, and RUNNING only
after ``Popen`` returns.  A post-start ambiguity is durable UNKNOWN with one
typed BLOCKED WorkResult and no retry, fallback, substitution, or raw output.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import stat
import subprocess
import threading
from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

import scripts.agent_quota_status_guard as quota
import scripts.multiagent_capacity as capacity
import scripts.multiagent_prompt_command as command
from scripts.multiagent_durable_queue import DurableQueue

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = REPOSITORY_ROOT / "scripts/multiagent_idq_mvp_080_operational.py"
TICKET = "IDQ-MVP-080"
AUTHORIZATION_ID = "IDQ-MVP-080-AUTH-02"
ALIASES = {
    "codex1": ("codex", "A"),
    "codex2": ("codex", "A"),
    "agy1": ("agy", "B"),
    "agy2": ("agy", "B"),
}
RAW_SENTINEL = "provider-raw-frame-must-not-persist"
PROMPT_SENTINEL = "provider-prompt-body-must-not-persist"
INHERITED_ENV_SENTINEL = "inherited-environment-must-not-escape"
TIMEOUT_SECONDS = 2.0
SAFE_PROVIDER_ENV_KEYS = {
    "PATH",
    "LANG",
    "LC_ALL",
    "TMPDIR",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "NO_COLOR",
}

AUTHORIZATION_FIELDS = {
    "schema_version",
    "protocol_version",
    "authorization_id",
    "ticket",
    "status",
    "issued_at",
    "expires_at",
    "ttl_seconds",
    "control_session_nonce_sha256",
    "aliases",
    "attempt",
    "max_attempts",
    "work_mode",
    "automatic_retry",
    "fallback",
    "substitution",
    "objective",
    "ownership",
    "risk_id",
    "repository_snapshot_sha256",
    "bindings",
}
AUTHORIZATION_BINDING_FIELDS = {
    "request_id",
    "root",
    "provider",
    "decision_sha256",
    "scheduling_snapshot_sha256",
    "qobs_artifact_sha256",
    "nonce_sha256",
    "resolved_executable_sha256",
    "account_identity_sha256",
    "capacity_lease_sha256",
    "lease_risk_sha256",
}
RECEIPT_FIELDS = {
    "protocol_version",
    "authorization_id",
    "authorization_sha256",
    "risk_id",
    "control_session_nonce_sha256",
    "ticket",
    "request_id",
    "root",
    "alias",
    "provider",
    "attempt",
    "max_attempts",
    "work_mode",
    "objective",
    "ownership",
    "qobs_quota_band",
    "decision_sha256",
    "scheduling_snapshot_sha256",
    "qobs_artifact_sha256",
    "nonce_sha256",
    "resolved_executable_sha256",
    "account_identity_sha256",
    "capacity_lease_sha256",
    "lease_risk_sha256",
    "repository_snapshot_sha256",
    "adapter",
    "process_or_session_id",
    "started_at",
    "ended_at",
    "exit_code",
    "transport_status",
    "output_bytes",
    "output_sha256",
    "work_result_sha256",
    "evidence_scope",
}


def _operational() -> Any:
    """Import the owned source lazily so the sentinel has a stable red."""

    return importlib.import_module("scripts.multiagent_idq_mvp_080_operational")


def _canonical_sha256(value: object) -> str:
    material = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(material).hexdigest()


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def _repository_snapshot(root: Path) -> str:
    """Hash sorted relative path, mode, and bytes for every non-Git file."""

    entries: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if ".git" in relative.parts or not path.is_file():
            continue
        entries.append(
            {
                "path": relative.as_posix(),
                "mode": stat.S_IMODE(path.stat().st_mode),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return _canonical_sha256(entries)


def _signals() -> dict[str, object]:
    values = {
        "usedPercent": 90.0,
        "remainingPercent": 10.0,
        "reached": False,
        "limit": 100.0,
        "spend": 90.0,
        "remaining": 10.0,
    }
    return {
        **values,
        "buckets": {"primary": dict(values), "secondary": dict(values)},
    }


def _work_result(alias: str) -> dict[str, object]:
    return {
        "status": "DONE",
        "scope_owned": ["read-only repository inventory"],
        "evidence": {
            "commands": [],
            "outcomes": [f"provider-native fixture for {alias}"],
            "artifacts": [],
        },
        "findings": [f"typed result for {alias}"],
        "changed_files": [],
        "residual_risk": "provider streams are intentionally not retained",
        "recommended_next_action": "stop this one-shot alias",
    }


def _codex_output(alias: str) -> str:
    events = (
        {"type": "thread.started", "thread_id": f"codex-operational-{alias}"},
        {"type": "item.started", "raw_marker": RAW_SENTINEL},
        {
            "type": "item.completed",
            "item": {
                "type": "agent_message",
                "text": json.dumps(_work_result(alias), separators=(",", ":")),
            },
        },
        {"type": "turn.completed"},
    )
    return "\n".join(json.dumps(event, separators=(",", ":")) for event in events) + "\n"


def _agy_output(alias: str) -> str:
    events = (
        {
            "event": "init",
            "conversation_id": f"agy-operational-{alias}",
            "init": {"raw_marker": RAW_SENTINEL},
        },
        {
            "event": "result",
            "result": {
                "conversation_id": f"agy-operational-{alias}",
                "status": "SUCCESS",
                "structured_output": _work_result(alias),
            },
        },
    )
    return "\n".join(json.dumps(event, separators=(",", ":")) for event in events) + "\n"


def _agy_stdin(prompt: str) -> str:
    return json.dumps(
        {"event": "user", "message": {"content": prompt}},
        ensure_ascii=False,
        separators=(",", ":"),
    ) + "\n"


class _RecordingQueue(DurableQueue):
    def __init__(self, path: Path) -> None:
        self.events: list[tuple[str, str]] = []
        self.event_lock = threading.Lock()
        self.alias_by_request: dict[str, str] = {}
        super().__init__(path)

    def remember(self, request_id: str, alias: str) -> None:
        self.alias_by_request[request_id] = alias

    def _record(self, request_id: str, event: str) -> None:
        with self.event_lock:
            self.events.append((self.alias_by_request[request_id], event))

    def transition(
        self,
        request_id: str,
        fence: int,
        state: str,
        instance_id: str | None = None,
    ) -> None:
        super().transition(request_id, fence, state, instance_id)
        self._record(request_id, state)

    def complete(self, **kwargs: Any) -> None:
        super().complete(**kwargs)
        self._record(str(kwargs["request_id"]), str(kwargs.get("state", "DONE")))


class _FakeProcess:
    def __init__(self, factory: _PopenFactory, alias: str, argv: tuple[str, ...]) -> None:
        self.factory = factory
        self.alias = alias
        self.args = argv
        self.pid = 62000 + tuple(ALIASES).index(alias)
        self.returncode: int | None = None
        self._finished = False
        self._timed_out = False

    def _finish(self) -> None:
        with self.factory.lock:
            if self._finished:
                return
            self._finished = True
            self.factory.active -= 1

    def communicate(self, input: str | None = None, timeout: float | None = None):
        with self.factory.lock:
            self.factory.communicate_calls.setdefault(self.alias, []).append(
                {"input": input, "timeout": timeout}
            )
        if not self.factory.all_started.wait(timeout=1.5):
            raise AssertionError("operational provider lanes did not overlap")

        if self.factory.mutate_alias == self.alias:
            with self.factory.lock:
                if not self.factory.repository_mutated:
                    self.factory.repository_mutated = True
                    assert self.factory.mutate_path is not None
                    self.factory.mutate_path.write_text(
                        "provider mutation must invalidate every result\n", encoding="utf-8"
                    )
                    self.factory.outputs_ready.set()
        elif self.factory.mutate_alias is None:
            self.factory.outputs_ready.set()

        if not self.factory.outputs_ready.wait(timeout=1.5):
            raise AssertionError("provider fixture output barrier did not release")
        with self.factory.store.event_lock:
            self.factory.store.events.append((self.alias, "COMMUNICATE"))

        if self.factory.failure_alias == self.alias and not self._timed_out:
            self._timed_out = True
            raise subprocess.TimeoutExpired(self.args, timeout)
        if self._timed_out:
            self.returncode = -9
            self._finish()
            return "", ""

        self.returncode = 0
        self._finish()
        return self.factory.payloads[self.alias], ""

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        with self.factory.lock:
            self.factory.terminated.append(self.alias)
        self.returncode = -15
        self._finish()

    def kill(self) -> None:
        with self.factory.lock:
            self.factory.killed.append(self.alias)
        self.returncode = -9
        self._finish()

    def wait(self, timeout: float | None = None) -> int:
        del timeout
        if self.returncode is None:
            self.returncode = 0
        self._finish()
        return self.returncode


class _PopenFactory:
    def __init__(
        self,
        *,
        store: _RecordingQueue,
        executable_aliases: Mapping[str, str],
        failure_alias: str | None = None,
        mutate_alias: str | None = None,
        mutate_path: Path | None = None,
    ) -> None:
        self.store = store
        self.executable_aliases = dict(executable_aliases)
        self.failure_alias = failure_alias
        self.mutate_alias = mutate_alias
        self.mutate_path = mutate_path
        self.repository_mutated = False
        self.lock = threading.Lock()
        self.all_started = threading.Event()
        self.outputs_ready = threading.Event()
        self.calls: dict[str, list[dict[str, Any]]] = {alias: [] for alias in ALIASES}
        self.communicate_calls: dict[str, list[dict[str, Any]]] = {}
        self.payloads = {
            alias: _codex_output(alias) if provider == "codex" else _agy_output(alias)
            for alias, (provider, _root) in ALIASES.items()
        }
        self.active = 0
        self.max_active = 0
        self.killed: list[str] = []
        self.terminated: list[str] = []

    def __call__(self, *args: Any, **kwargs: Any) -> _FakeProcess:
        raw_argv = args[0] if args else kwargs.get("args")
        argv = tuple(raw_argv)
        executable = str(argv[0])
        alias = self.executable_aliases[executable]
        record = {"argv": argv, "kwargs": dict(kwargs)}
        record["kwargs"].pop("args", None)
        with self.lock:
            self.calls[alias].append(record)
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            self.store.events.append((alias, "POPEN"))
            if sum(len(items) for items in self.calls.values()) == len(ALIASES):
                self.all_started.set()
        return _FakeProcess(self, alias, argv)


def _config() -> dict[str, object]:
    return {
        "activation_prohibited": True,
        "dispatcher_execution": "CLOSED",
        "idq_mvp_080": {
            "ticket": TICKET,
            "aliases": {
                alias: {
                    "provider": provider,
                    "attempt": 1,
                    "work_mode": "read_only",
                    "automatic_retry": False,
                    "fallback": False,
                }
                for alias, (provider, _root) in ALIASES.items()
            },
        },
    }


def _fixture(
    tmp_path: Path,
    *,
    failure_alias: str | None = None,
    mutate_alias: str | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    repository = tmp_path / "repository"
    schema_path = repository / ".agents/schemas/multiagent-work-result-v2.schema.json"
    schema_path.parent.mkdir(parents=True)
    schema_path.write_bytes(
        (REPOSITORY_ROOT / ".agents/schemas/multiagent-work-result-v2.schema.json").read_bytes()
    )
    tracked = repository / "tracked.txt"
    tracked.write_text("immutable repository fixture\n", encoding="utf-8")

    provider_root = tmp_path / "providers"
    account_root = tmp_path / "accounts"
    provider_root.mkdir()
    account_root.mkdir(mode=0o700)
    executable_aliases: dict[str, str] = {}

    store = _RecordingQueue(tmp_path / "queue/durable.sqlite3")
    marker_store = tmp_path / "markers"
    capacity_store = tmp_path / "capacity"
    policy = json.loads(
        (REPOSITORY_ROOT / ".agents/config/s3_capacity_policy.json").read_text(
            encoding="utf-8"
        )
    )
    config = _config()
    lanes: dict[str, dict[str, object]] = {}
    bindings: dict[str, dict[str, object]] = {}

    for alias, (provider, root) in ALIASES.items():
        executable = (provider_root / f"{alias}-{provider}").resolve()
        executable.write_text("fixture executable; never invoked\n", encoding="utf-8")
        executable.chmod(0o700)
        executable_aliases[str(executable)] = alias
        account_home = (account_root / alias).resolve()
        account_home.mkdir(mode=0o700)

        request_id = f"idq-operational-{alias}"
        instance_id = f"root-{root.lower()}-operational"
        submitted = store.submit(
            request_id=request_id,
            idempotency_key=request_id,
            payload={"objective_sha256": _digest(f"objective:{alias}")},
            root=root,
            alias=alias,
            work_mode="read_only",
            attempt=1,
            retry_budget=0,
        )
        assert submitted.state == "QUEUED"
        job = store.claim(root=root, instance_id=instance_id, aliases={alias})
        assert job is not None
        store.remember(request_id, alias)

        lease = capacity.acquire_lease(
            capacity_store,
            account=alias,
            request_id=request_id,
            owner=instance_id,
            lane=1,
            request_budget=1,
            model_quality_floor="gpt-5.6-sol",
            policy=policy,
            now=now.timestamp(),
            ttl_seconds=120,
        )
        qobs_context: dict[str, object] = {
            "alias": alias,
            "provider": provider,
            "account_home": str(account_home),
            "resolved_executable": str(executable),
            "ticket_id": TICKET,
            "attempt_id": 1,
            "policy_version": "2026-08-29.1",
            "nonce": f"idq-operational-{alias}-nonce",
            "observed_at": _timestamp(now),
        }
        artifact = quota.probe_quota_observation(_signals(), qobs_context)
        request: dict[str, object] = {
            "ticket": TICKET,
            "alias": alias,
            "provider": provider,
            "attempt": 1,
            "work_mode": "read_only",
            "automatic_retry": False,
            "fallback": False,
            "decision_sha256": _digest(f"decision:{alias}"),
            "qobs_artifact_sha256": quota.quota_artifact_sha256(artifact),
            "qobs_quota_band": "constrained",
            "nonce_sha256": quota.sha256_text(str(qobs_context["nonce"])),
            "scheduling_snapshot_sha256": _digest(f"snapshot:{alias}"),
            "resolved_executable_sha256": quota.sha256_text(str(executable)),
            "account_identity_sha256": quota.sha256_text(str(account_home)),
            "lease_risk_sha256": _digest(f"risk:{alias}"),
        }
        execution_context = {
            "qobs_artifact": artifact,
            "qobs_expected_context": qobs_context,
            "runtime": (
                {"read_only": True, "sandbox": "read-only"}
                if provider == "codex"
                else {"read_only": True, "mode": "plan", "sandbox": True}
            ),
        }
        lanes[alias] = {
            "job": job,
            "instance_id": instance_id,
            "request": request,
            "execution_context": execution_context,
            "capacity_lease": lease.to_dict(),
            "capacity_store_path": str(capacity_store.resolve()),
            "capacity_policy": policy,
            "prompt_stdin": f"Read-only repository inventory for {alias}; {PROMPT_SENTINEL}",
        }
        bindings[alias] = {
            "request_id": request_id,
            "root": root,
            "provider": provider,
            "decision_sha256": request["decision_sha256"],
            "scheduling_snapshot_sha256": request["scheduling_snapshot_sha256"],
            "qobs_artifact_sha256": request["qobs_artifact_sha256"],
            "nonce_sha256": request["nonce_sha256"],
            "resolved_executable_sha256": request["resolved_executable_sha256"],
            "account_identity_sha256": request["account_identity_sha256"],
            "capacity_lease_sha256": lease.lease_sha256,
            "lease_risk_sha256": request["lease_risk_sha256"],
        }

    snapshot = _repository_snapshot(repository)
    authorization: dict[str, object] = {
        "schema_version": "idq-mvp-080-auth-v1",
        "protocol_version": 2,
        "authorization_id": AUTHORIZATION_ID,
        "ticket": TICKET,
        "status": "UNUSED",
        "issued_at": _timestamp(now),
        "expires_at": _timestamp(now + timedelta(seconds=1800)),
        "ttl_seconds": 1800,
        "control_session_nonce_sha256": _digest("auth02-control-session-nonce"),
        "aliases": list(ALIASES),
        "attempt": 1,
        "max_attempts": 1,
        "work_mode": "read_only",
        "automatic_retry": False,
        "fallback": False,
        "substitution": False,
        "objective": "one bounded read-only repository inventory per alias",
        "ownership": "no repository files; terminal metadata only",
        "risk_id": "RISK-IDQ-MVP-080-20260830-02",
        "repository_snapshot_sha256": snapshot,
        "bindings": bindings,
    }
    factory = _PopenFactory(
        store=store,
        executable_aliases=executable_aliases,
        failure_alias=failure_alias,
        mutate_alias=mutate_alias,
        mutate_path=tracked if mutate_alias else None,
    )
    return {
        "now": now,
        "repository": repository,
        "schema_path": schema_path.resolve(),
        "tracked": tracked,
        "snapshot": snapshot,
        "config": config,
        "authorization": authorization,
        "lanes": lanes,
        "store": store,
        "marker_store": marker_store,
        "factory": factory,
    }


def _run(operational: Any, fixture: Mapping[str, Any], **overrides: object):
    arguments = {
        "config": fixture["config"],
        "authorization": fixture["authorization"],
        "lanes": fixture["lanes"],
        "store": fixture["store"],
        "marker_store": fixture["marker_store"],
        "repository_root": fixture["repository"],
        "popen_factory": fixture["factory"],
        "timeout_seconds": TIMEOUT_SECONDS,
        "now": fixture["now"],
    }
    arguments.update(overrides)
    return operational.execute_idq_mvp_080_operational(**arguments)


def _process_call_count(fixture: Mapping[str, Any]) -> int:
    return sum(len(items) for items in fixture["factory"].calls.values())


def _marker_files(fixture: Mapping[str, Any]) -> list[Path]:
    root = fixture["marker_store"]
    return sorted(root.glob("*.used")) if root.exists() else []


def _queue_artifact_bytes(fixture: Mapping[str, Any]) -> bytes:
    root = fixture["store"].path.parent
    return b"".join(
        path.read_bytes() for path in sorted(root.rglob("*")) if path.is_file()
    )


def test_operational_entrypoint_exists_before_source() -> None:
    assert ENTRYPOINT.is_file(), "IDQ_MVP_080_OPERATIONAL_ENTRYPOINT_MISSING"


def test_auth02_is_closed_and_auth01_is_rejected_before_any_process(tmp_path: Path) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path)
    assert set(fixture["authorization"]) == AUTHORIZATION_FIELDS
    assert set(fixture["authorization"]["bindings"]) == set(ALIASES)
    assert all(
        set(binding) == AUTHORIZATION_BINDING_FIELDS
        for binding in fixture["authorization"]["bindings"].values()
    )

    auth01 = deepcopy(fixture["authorization"])
    auth01["authorization_id"] = "IDQ-MVP-080-AUTH-01"
    with pytest.raises(ValueError):
        _run(operational, fixture, authorization=auth01)

    widened = deepcopy(fixture["authorization"])
    widened["adjacent_authority"] = True
    with pytest.raises(ValueError):
        _run(operational, fixture, authorization=widened)

    widened_binding = deepcopy(fixture["authorization"])
    widened_binding["bindings"]["codex1"]["raw_account_home"] = "/forbidden"
    with pytest.raises(ValueError):
        _run(operational, fixture, authorization=widened_binding)

    expired = deepcopy(fixture["authorization"])
    expired["expires_at"] = _timestamp(fixture["now"] - timedelta(seconds=1))
    with pytest.raises(ValueError):
        _run(operational, fixture, authorization=expired)

    opened = deepcopy(fixture["config"])
    opened["dispatcher_execution"] = "OPEN"
    with pytest.raises(ValueError):
        _run(operational, fixture, config=opened)

    assert _process_call_count(fixture) == 0
    assert _marker_files(fixture) == []
    assert command.effective_activation_state(fixture["config"]) == (True, "CLOSED")


def test_exact_four_one_shot_read_only_lanes_cannot_retry_or_substitute(tmp_path: Path) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path)
    invalid_authorizations: list[dict[str, object]] = []
    for field, value in (
        ("attempt", 2),
        ("max_attempts", 2),
        ("work_mode", "workspace_write"),
        ("automatic_retry", True),
        ("fallback", True),
        ("substitution", True),
    ):
        changed = deepcopy(fixture["authorization"])
        changed[field] = value
        invalid_authorizations.append(changed)
    missing_alias = deepcopy(fixture["authorization"])
    missing_alias["aliases"] = ["codex1", "codex2", "agy1"]
    invalid_authorizations.append(missing_alias)
    substituted_alias = deepcopy(fixture["authorization"])
    substituted_alias["aliases"] = ["codex1", "codex2", "codex3", "agy1"]
    invalid_authorizations.append(substituted_alias)

    for authorization in invalid_authorizations:
        with pytest.raises(ValueError):
            _run(operational, fixture, authorization=authorization)

    changed_lanes = deepcopy(fixture["lanes"])
    changed_lanes["codex1"]["request"]["attempt"] = 2
    with pytest.raises(ValueError):
        _run(operational, fixture, lanes=changed_lanes)

    incomplete_lanes = dict(fixture["lanes"])
    incomplete_lanes.pop("agy2")
    with pytest.raises(ValueError):
        _run(operational, fixture, lanes=incomplete_lanes)

    assert _process_call_count(fixture) == 0
    assert _marker_files(fixture) == []
    assert {fixture["store"].get_job(lane["job"].request_id).state for lane in fixture["lanes"].values()} == {"CLAIMED"}


def test_all_bindings_preflight_as_one_barrier_before_nonce_or_popen(tmp_path: Path) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path)
    fields = (
        "decision_sha256",
        "scheduling_snapshot_sha256",
        "qobs_artifact_sha256",
        "nonce_sha256",
        "resolved_executable_sha256",
        "account_identity_sha256",
        "capacity_lease_sha256",
        "lease_risk_sha256",
    )
    for field in fields:
        authorization = deepcopy(fixture["authorization"])
        authorization["bindings"]["agy2"][field] = _digest(f"tampered:{field}")
        with pytest.raises(ValueError):
            _run(operational, fixture, authorization=authorization)
        assert _process_call_count(fixture) == 0
        assert _marker_files(fixture) == []

    stale_repository = deepcopy(fixture["authorization"])
    stale_repository["repository_snapshot_sha256"] = _digest("stale repository")
    with pytest.raises(ValueError):
        _run(operational, fixture, authorization=stale_repository)

    assert _process_call_count(fixture) == 0
    assert _marker_files(fixture) == []
    assert {fixture["store"].get_job(lane["job"].request_id).state for lane in fixture["lanes"].values()} == {"CLAIMED"}


def test_operational_batch_uses_isolated_native_popen_and_safe_durable_receipts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path)
    original_config = deepcopy(fixture["config"])
    before_snapshot = _repository_snapshot(fixture["repository"])
    monkeypatch.setenv("IDQ_PROVIDER_SECRET_SENTINEL", INHERITED_ENV_SENTINEL)

    completed = _run(operational, fixture)

    assert set(completed) == {
        "authorization_id",
        "authorization_status",
        "ticket",
        "status",
        "attempt",
        "ordinary_activation",
        "repository_snapshot_sha256",
        "aliases",
    }
    assert completed["authorization_id"] == AUTHORIZATION_ID
    assert completed["authorization_status"] == "SEALED"
    assert completed["ticket"] == TICKET
    assert completed["status"] == "DONE"
    assert completed["attempt"] == 1
    assert completed["ordinary_activation"] == "CLOSED"
    assert completed["repository_snapshot_sha256"] == before_snapshot
    assert set(completed["aliases"]) == set(ALIASES)
    assert fixture["factory"].max_active >= 2

    authorization_sha256 = _canonical_sha256(fixture["authorization"])
    schema_path = str(fixture["schema_path"])
    repository = str(fixture["repository"].resolve())
    for alias, (provider, root) in ALIASES.items():
        assert len(fixture["factory"].calls[alias]) == 1
        process_call = fixture["factory"].calls[alias][0]
        argv = process_call["argv"]
        kwargs = process_call["kwargs"]
        lane = fixture["lanes"][alias]
        context = lane["execution_context"]["qobs_expected_context"]
        executable = context["resolved_executable"]
        account_home = context["account_home"]
        assert os.path.isabs(executable)
        if provider == "codex":
            assert argv == (
                executable,
                "exec",
                "-C",
                repository,
                "-s",
                "read-only",
                "--json",
                "--output-schema",
                schema_path,
                "-",
            )
            expected_stdin = lane["prompt_stdin"]
            home_env = "CODEX_HOME"
            expected_adapter = "codex-jsonl-output-schema-v2"
            expected_scope = "provider-native validated"
        else:
            assert argv == (
                executable,
                "--mode",
                "plan",
                "--sandbox",
                "--print",
                "--input-format",
                "stream-json",
                "--output-format",
                "stream-json",
                "--json-schema",
                schema_path,
            )
            expected_stdin = _agy_stdin(lane["prompt_stdin"])
            home_env = "AGY_HOME"
            expected_adapter = "agy-stream-json-schema-v2"
            expected_scope = "validated in-process only"

        environment = kwargs.pop("env")
        assert kwargs == {
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
            "cwd": repository,
            "shell": False,
        }
        assert environment[home_env] == account_home
        assert set(environment) <= SAFE_PROVIDER_ENV_KEYS | {home_env}
        assert ({"CODEX_HOME", "AGY_HOME"} - {home_env}).isdisjoint(environment)
        assert INHERITED_ENV_SENTINEL not in json.dumps(environment, sort_keys=True)
        communicate = fixture["factory"].communicate_calls[alias]
        assert communicate == [{"input": expected_stdin, "timeout": TIMEOUT_SECONDS}]

        alias_events = [event for event_alias, event in fixture["store"].events if event_alias == alias]
        assert alias_events.index("PREPARED") < alias_events.index("STARTING")
        assert alias_events.index("STARTING") < alias_events.index("POPEN")
        assert alias_events.index("POPEN") < alias_events.index("RUNNING")
        assert alias_events.index("RUNNING") < alias_events.index("COMMUNICATE")
        assert alias_events.index("COMMUNICATE") < alias_events.index("DONE")

        outcome = completed["aliases"][alias]
        assert set(outcome) == {"status", "receipt", "work_result"}
        assert outcome["status"] == "DONE"
        assert outcome["work_result"] == _work_result(alias)
        receipt = outcome["receipt"]
        assert set(receipt) == RECEIPT_FIELDS
        assert receipt["protocol_version"] == 2
        assert receipt["authorization_id"] == AUTHORIZATION_ID
        assert receipt["authorization_sha256"] == authorization_sha256
        assert receipt["risk_id"] == fixture["authorization"]["risk_id"]
        assert (
            receipt["control_session_nonce_sha256"]
            == fixture["authorization"]["control_session_nonce_sha256"]
        )
        assert receipt["ticket"] == TICKET
        assert receipt["request_id"] == lane["job"].request_id
        assert receipt["root"] == root
        assert receipt["alias"] == alias
        assert receipt["provider"] == provider
        assert receipt["attempt"] == receipt["max_attempts"] == 1
        assert receipt["work_mode"] == "read_only"
        assert receipt["qobs_quota_band"] == "constrained"
        assert receipt["adapter"] == expected_adapter
        assert receipt["evidence_scope"] == expected_scope
        assert receipt["exit_code"] == 0
        assert receipt["transport_status"] == "COMPLETED"
        payload = fixture["factory"].payloads[alias]
        assert receipt["output_bytes"] == len(payload.encode("utf-8"))
        assert receipt["output_sha256"] == hashlib.sha256(payload.encode("utf-8")).hexdigest()
        assert receipt["work_result_sha256"] == _canonical_sha256(_work_result(alias))
        for field in (
            "decision_sha256",
            "scheduling_snapshot_sha256",
            "qobs_artifact_sha256",
            "nonce_sha256",
            "resolved_executable_sha256",
            "account_identity_sha256",
            "capacity_lease_sha256",
            "lease_risk_sha256",
        ):
            assert receipt[field] == fixture["authorization"]["bindings"][alias][field]
        assert receipt["repository_snapshot_sha256"] == before_snapshot
        assert RAW_SENTINEL not in json.dumps(receipt, sort_keys=True)
        assert PROMPT_SENTINEL not in json.dumps(receipt, sort_keys=True)
        assert str(account_home) not in json.dumps(receipt, sort_keys=True)
        assert str(executable) not in json.dumps(receipt, sort_keys=True)
        assert fixture["store"].get_job(lane["job"].request_id).state == "DONE"
        assert fixture["store"].get_result(lane["job"].request_id) == _work_result(alias)

    assert len(_marker_files(fixture)) == 9
    persisted = _queue_artifact_bytes(fixture)
    assert RAW_SENTINEL.encode("utf-8") not in persisted
    assert PROMPT_SENTINEL.encode("utf-8") not in persisted
    assert fixture["config"] == original_config
    assert command.effective_activation_state(fixture["config"]) == (True, "CLOSED")
    assert _repository_snapshot(fixture["repository"]) == before_snapshot


def test_post_start_timeout_is_unknown_with_no_retry_or_substitution(tmp_path: Path) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path, failure_alias="agy2")

    completed = _run(operational, fixture)

    assert completed["status"] == "UNKNOWN"
    assert set(completed["aliases"]) == set(ALIASES)
    for alias in ALIASES:
        assert len(fixture["factory"].calls[alias]) == 1
    failed = completed["aliases"]["agy2"]
    assert failed["status"] == "UNKNOWN"
    assert failed["work_result"]["status"] == "BLOCKED"
    assert failed["receipt"]["authorization_id"] == AUTHORIZATION_ID
    assert failed["receipt"]["alias"] == "agy2"
    assert failed["receipt"]["attempt"] == failed["receipt"]["max_attempts"] == 1
    assert failed["receipt"]["transport_status"] == "UNKNOWN"
    assert failed["receipt"]["evidence_scope"] == "not validated"
    request_id = fixture["lanes"]["agy2"]["job"].request_id
    assert fixture["store"].get_job(request_id).state == "UNKNOWN"
    assert fixture["factory"].killed == ["agy2"] or fixture["factory"].terminated == ["agy2"]
    assert all(
        completed["aliases"][alias]["status"] == "DONE"
        for alias in ("codex1", "codex2", "agy1")
    )
    assert len(_marker_files(fixture)) == 9
    assert RAW_SENTINEL.encode("utf-8") not in _queue_artifact_bytes(fixture)


def test_repository_snapshot_drift_invalidates_every_started_result(tmp_path: Path) -> None:
    operational = _operational()
    fixture = _fixture(tmp_path, mutate_alias="codex1")

    completed = _run(operational, fixture)

    assert completed["status"] == "UNKNOWN"
    assert _repository_snapshot(fixture["repository"]) != fixture["snapshot"]
    assert set(completed["aliases"]) == set(ALIASES)
    assert all(item["status"] == "UNKNOWN" for item in completed["aliases"].values())
    assert all(
        item["work_result"]["status"] == "BLOCKED"
        for item in completed["aliases"].values()
    )
    assert all(
        fixture["store"].get_job(lane["job"].request_id).state == "UNKNOWN"
        for lane in fixture["lanes"].values()
    )
    assert all(len(fixture["factory"].calls[alias]) == 1 for alias in ALIASES)
    assert command.effective_activation_state(fixture["config"]) == (True, "CLOSED")
