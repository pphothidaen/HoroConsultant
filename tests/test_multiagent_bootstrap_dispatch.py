"""Frozen admission and lifecycle contract for local unsafe bootstrap.

The bootstrap is a narrow queue admission, never a second healthy activation
path.  These tests preserve ordinary CLOSED behavior and bind observations to
one supervisor lifetime, alias, executable, account-home identity, and risk
acceptance.
"""

from __future__ import annotations

import hashlib
import importlib
import os
from pathlib import Path

import pytest


@pytest.fixture
def dispatcher():
    return importlib.import_module("scripts.multiagent_prompt_command")


@pytest.fixture
def executable(tmp_path: Path) -> Path:
    path = tmp_path / "bin" / "provider-cli"
    path.parent.mkdir()
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o700)
    return path


@pytest.fixture
def account_home(tmp_path: Path) -> Path:
    path = tmp_path / "account-home"
    path.mkdir(mode=0o700)
    return path


def _digest(path: Path) -> str:
    if path.is_dir():
        identity = path.stat()
        material = f"{identity.st_dev}:{identity.st_ino}".encode()
    else:
        material = path.read_bytes()
    return hashlib.sha256(material).hexdigest()


def _admission(
    dispatcher,
    executable: Path,
    account_home: Path,
    *,
    quota_band: str = "unknown",
    alias: str = "codex1",
    provider: str = "codex",
    work_mode: str = "read_only",
    attempt: int = 1,
    automatic_retry: bool = False,
    acceptance_id: str | None = "risk-local-001",
    supervisor_instance_id: str = "supervisor-1",
):
    return dispatcher.LocalBootstrapAdmission(
        protocol_version="bootstrap-local-unsafe-v1",
        alias=alias,
        provider=provider,
        observed_at="2026-08-28T12:00:00Z",
        nonce="nonce-001",
        executable_sha256=_digest(executable),
        account_home_sha256=_digest(account_home),
        quota_band=quota_band,
        risk_acceptance_id=acceptance_id,
        supervisor_instance_id=supervisor_instance_id,
        work_mode=work_mode,
        attempt=attempt,
        automatic_retry=automatic_retry,
        evidence_level="bootstrap_unverified",
        warning="Local bootstrap accepts unknown/constrained quota at user risk.",
    )


def _validate(
    dispatcher,
    admission,
    executable: Path,
    account_home: Path,
    **overrides,
):
    arguments = {
        "executable": executable,
        "account_home": account_home,
        "active_supervisor_instance_id": "supervisor-1",
        "bootstrap_open": True,
        "bootstrap_sealed": False,
        "risk_acceptance_exists": True,
        "auth_ready": True,
        "requested_alias": admission.alias,
        "active_aliases": set(),
    }
    arguments.update(overrides)
    return dispatcher.validate_local_bootstrap_admission(admission, **arguments)


def test_ordinary_activation_defaults_remain_byte_compatible_closed(dispatcher) -> None:
    assert dispatcher.effective_activation_state({}) == (True, "CLOSED")
    assert dispatcher.effective_activation_state(
        {"activation_prohibited": True, "dispatcher_execution": "CLOSED"}
    ) == (True, "CLOSED")


def test_unknown_and_constrained_quota_are_admitted_without_health_promotion(
    dispatcher, executable, account_home
) -> None:
    for quota_band in ("unknown", "constrained"):
        admission = _admission(
            dispatcher, executable, account_home, quota_band=quota_band
        )

        validated = _validate(
            dispatcher, admission, executable, account_home
        )

        assert validated is admission
        assert validated.quota_band == quota_band
        assert validated.evidence_level == "bootstrap_unverified"
        assert "warning" not in validated.quota_band.lower()
        assert validated.warning


@pytest.mark.parametrize("quota_band", ["healthy", "available", "below_10_percent", ""])
def test_bootstrap_accepts_only_honest_unknown_or_constrained_observation(
    dispatcher, executable, account_home, quota_band
) -> None:
    admission = _admission(
        dispatcher, executable, account_home, quota_band=quota_band
    )

    with pytest.raises(dispatcher.LocalBootstrapBlocked, match="quota"):
        _validate(dispatcher, admission, executable, account_home)


def test_bootstrap_requires_explicit_durable_risk_acceptance(
    dispatcher, executable, account_home
) -> None:
    admission = _admission(
        dispatcher, executable, account_home, acceptance_id=None
    )

    with pytest.raises(dispatcher.LocalBootstrapBlocked) as caught:
        _validate(
            dispatcher,
            admission,
            executable,
            account_home,
            risk_acceptance_exists=False,
        )

    assert caught.value.code == "BLOCKED_RISK_ACCEPTANCE"


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"bootstrap_open": False}, "BLOCKED_BOOTSTRAP_CLOSED"),
        ({"bootstrap_sealed": True}, "BLOCKED_BOOTSTRAP_SEALED"),
        (
            {"active_supervisor_instance_id": "replacement-supervisor"},
            "BLOCKED_BOOTSTRAP_EXPIRED",
        ),
    ],
)
def test_bootstrap_is_explicit_ephemeral_and_sealable(
    dispatcher, executable, account_home, overrides, code
) -> None:
    admission = _admission(dispatcher, executable, account_home)

    with pytest.raises(dispatcher.LocalBootstrapBlocked) as caught:
        _validate(dispatcher, admission, executable, account_home, **overrides)

    assert caught.value.code == code


@pytest.mark.parametrize(
    ("work_mode", "attempt", "automatic_retry", "code"),
    [
        ("mutation", 1, False, "BLOCKED_WORK_MODE"),
        ("read_only", 2, False, "BLOCKED_ATTEMPT"),
        ("read_only", 1, True, "BLOCKED_AUTO_RETRY"),
    ],
)
def test_bootstrap_is_read_only_attempt_one_with_no_automatic_retry(
    dispatcher,
    executable,
    account_home,
    work_mode,
    attempt,
    automatic_retry,
    code,
) -> None:
    admission = _admission(
        dispatcher,
        executable,
        account_home,
        work_mode=work_mode,
        attempt=attempt,
        automatic_retry=automatic_retry,
    )

    with pytest.raises(dispatcher.LocalBootstrapBlocked) as caught:
        _validate(dispatcher, admission, executable, account_home)

    assert caught.value.code == code


def test_only_one_active_bootstrap_lane_per_alias(
    dispatcher, executable, account_home
) -> None:
    admission = _admission(dispatcher, executable, account_home, alias="codex1")

    with pytest.raises(dispatcher.LocalBootstrapBlocked) as caught:
        _validate(
            dispatcher,
            admission,
            executable,
            account_home,
            active_aliases={"codex1"},
        )

    assert caught.value.code == "BLOCKED_ALIAS_BUSY"


def test_cross_alias_request_is_blocked_without_fallback(
    dispatcher, executable, account_home
) -> None:
    admission = _admission(dispatcher, executable, account_home, alias="codex1")

    with pytest.raises(dispatcher.LocalBootstrapBlocked) as caught:
        _validate(
            dispatcher,
            admission,
            executable,
            account_home,
            requested_alias="codex2",
        )

    assert caught.value.code == "BLOCKED_ALIAS_MISMATCH"


def test_executable_replacement_between_observation_and_spawn_is_typed_block(
    dispatcher, executable, account_home
) -> None:
    admission = _admission(dispatcher, executable, account_home)
    executable.write_text("#!/bin/sh\nexit 9\n", encoding="utf-8")
    executable.chmod(0o700)

    with pytest.raises(dispatcher.LocalBootstrapBlocked) as caught:
        _validate(dispatcher, admission, executable, account_home)

    assert caught.value.code == "BLOCKED_EXECUTABLE"


def test_missing_or_non_executable_binary_is_typed_block(
    dispatcher, executable, account_home
) -> None:
    admission = _admission(dispatcher, executable, account_home)
    executable.chmod(0o600)

    with pytest.raises(dispatcher.LocalBootstrapBlocked) as caught:
        _validate(dispatcher, admission, executable, account_home)

    assert caught.value.code == "BLOCKED_EXECUTABLE"


def test_account_home_replacement_between_observation_and_spawn_is_blocked(
    dispatcher, executable, account_home, tmp_path
) -> None:
    admission = _admission(dispatcher, executable, account_home)
    old_home = tmp_path / "old-account-home"
    account_home.rename(old_home)
    account_home.mkdir(mode=0o700)

    with pytest.raises(dispatcher.LocalBootstrapBlocked) as caught:
        _validate(dispatcher, admission, executable, account_home)

    assert caught.value.code == "BLOCKED_ACCOUNT_HOME"


def test_auth_failure_is_typed_and_cannot_be_bypassed(
    dispatcher, executable, account_home
) -> None:
    admission = _admission(dispatcher, executable, account_home)

    with pytest.raises(dispatcher.LocalBootstrapBlocked) as caught:
        _validate(
            dispatcher,
            admission,
            executable,
            account_home,
            auth_ready=False,
        )

    assert caught.value.code == "BLOCKED_AUTH"


def test_lifecycle_hooks_are_ordered_and_provider_start_is_explicit(dispatcher) -> None:
    observed: list[str] = []
    lifecycle = dispatcher.LocalBootstrapLifecycle(on_event=observed.append)

    lifecycle.prepared()
    lifecycle.starting()
    lifecycle.provider_started()
    lifecycle.completed()

    assert observed == ["prepared", "starting", "provider_started", "completed"]
    assert lifecycle.provider_was_started is True
    assert lifecycle.terminal_state == "completed"


@pytest.mark.parametrize(
    "events",
    [
        ("starting",),
        ("prepared", "provider_started"),
        ("prepared", "starting", "completed", "provider_started"),
        ("prepared", "prepared"),
    ],
)
def test_lifecycle_rejects_missing_out_of_order_or_duplicate_events(
    dispatcher, events
) -> None:
    lifecycle = dispatcher.LocalBootstrapLifecycle(on_event=lambda _event: None)

    with pytest.raises(dispatcher.LocalBootstrapLifecycleError):
        for event in events:
            getattr(lifecycle, event)()


def test_queue_record_is_warning_only_secret_free_and_never_a_provider_receipt(
    dispatcher, executable, account_home
) -> None:
    admission = _admission(dispatcher, executable, account_home)

    record = admission.to_queue_record()

    assert record["evidence_level"] == "bootstrap_unverified"
    assert record["warning"]
    assert record["quota_band"] == "unknown"
    assert "receipt" not in record
    assert "healthy" not in record.values()
    serialized = repr(record).lower()
    for forbidden in (
        str(executable).lower(),
        str(account_home).lower(),
        "stdout",
        "stderr",
        "raw_stream",
        "token",
        "cookie",
        "password",
    ):
        assert forbidden not in serialized


def test_bootstrap_observation_requires_nonce_timestamp_and_identity_digests(
    dispatcher, executable, account_home
) -> None:
    valid = _admission(dispatcher, executable, account_home)
    for field in (
        "observed_at",
        "nonce",
        "executable_sha256",
        "account_home_sha256",
    ):
        values = dict(vars(valid))
        values[field] = ""
        malformed = dispatcher.LocalBootstrapAdmission(**values)
        with pytest.raises(dispatcher.LocalBootstrapBlocked):
            _validate(dispatcher, malformed, executable, account_home)


def test_validation_does_not_mutate_process_environment(
    dispatcher, executable, account_home, monkeypatch
) -> None:
    monkeypatch.setenv("CODEX_HOME", "sentinel-codex-home")
    before = dict(os.environ)
    admission = _admission(dispatcher, executable, account_home)

    _validate(dispatcher, admission, executable, account_home)

    assert dict(os.environ) == before
