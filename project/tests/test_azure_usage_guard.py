"""Behavior tests for the Azure free-grant fail-closed guard."""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "azure_usage_guard.py"


def _load_guard():
    assert SCRIPT.exists(), f"missing cost guard: {SCRIPT.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location("azure_usage_guard", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _snapshot(**overrides):
    data = {
        "period": datetime.now(timezone.utc).strftime("%Y-%m"),
        "actual_cost": 0.0,
        "currency": "USD",
        "vcpu_seconds": 125_999.0,
        "gib_seconds": 251_999.0,
        "requests": 1_399_999,
        "complete": True,
    }
    data.update(overrides)
    return data


def test_guard_allows_only_complete_current_month_data_below_70_percent():
    guard = _load_guard()

    decision = guard.evaluate_usage(_snapshot(), threshold=0.70)

    assert decision.allowed is True
    assert decision.highest_ratio < 0.70


def test_guard_denies_at_threshold_or_when_any_real_cost_appears():
    guard = _load_guard()

    at_threshold = guard.evaluate_usage(
        _snapshot(vcpu_seconds=126_000.0), threshold=0.70
    )
    charged = guard.evaluate_usage(_snapshot(actual_cost=0.01), threshold=0.70)

    assert at_threshold.allowed is False
    assert "vcpu_seconds" in " ".join(at_threshold.reasons)
    assert charged.allowed is False
    assert "actual_cost" in " ".join(charged.reasons)


def test_guard_fails_closed_for_stale_incomplete_or_malformed_usage():
    guard = _load_guard()

    stale = guard.evaluate_usage(_snapshot(period="2025-01"), threshold=0.70)
    incomplete = guard.evaluate_usage(_snapshot(complete=False), threshold=0.70)
    malformed = guard.evaluate_usage({"period": "invalid"}, threshold=0.70)

    assert stale.allowed is False
    assert incomplete.allowed is False
    assert malformed.allowed is False


def test_denied_enforcement_disables_ingress_without_shell_or_secret_echo():
    guard = _load_guard()
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    decision = guard.evaluate_usage(_snapshot(requests=1_400_000), threshold=0.70)
    guard.enforce_decision(
        decision,
        resource_group="rg-horoconsult",
        app_name="horoconsult-env-new",
        runner=fake_run,
    )

    assert calls == [[
        "az",
        "containerapp",
        "ingress",
        "disable",
        "--resource-group",
        "rg-horoconsult",
        "--name",
        "horoconsult-env-new",
        "--only-show-errors",
    ]]


def test_snapshot_json_is_machine_readable_and_contains_no_credentials(tmp_path):
    guard = _load_guard()
    snapshot_path = tmp_path / "usage.json"
    snapshot_path.write_text(json.dumps(_snapshot()), encoding="utf-8")

    payload = guard.evaluate_file(snapshot_path, threshold=0.70)

    rendered = json.dumps(payload.to_dict(), sort_keys=True)
    assert json.loads(rendered)["decision"] == "ALLOW"
    assert "password" not in rendered.lower()
    assert "token" not in rendered.lower()


def test_new_month_resumes_only_ingress_suspended_by_the_guard():
    guard = _load_guard()
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[:3] == ["az", "tag", "list"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    {
                        "properties": {
                            "tags": {"horoCostGuardSuspendedPeriod": "2026-07"}
                        }
                    }
                ),
                stderr="",
            )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    decision = guard.evaluate_usage(_snapshot(), threshold=0.70)
    resumed = guard.resume_after_reset(
        decision,
        subscription="00000000-0000-0000-0000-000000000000",
        resource_group="rg-horoconsult",
        app_name="horoconsult-env-new",
        runner=fake_run,
    )

    assert resumed is True
    assert any(command[:4] == ["az", "containerapp", "ingress", "enable"] for command in calls)
    assert any(command[:4] == ["az", "tag", "update", "--resource-id"] for command in calls)


def test_guard_never_resumes_a_manual_or_current_period_shutdown():
    guard = _load_guard()
    current_period = datetime.now(timezone.utc).strftime("%Y-%m")

    for tags in (None, {}, {"horoCostGuardSuspendedPeriod": current_period}):
        calls: list[list[str]] = []

        def fake_run(command, _calls=calls, _tags=tags, **kwargs):
            _calls.append(command)
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps({"properties": {"tags": _tags}}),
                stderr="",
            )

        resumed = guard.resume_after_reset(
            guard.evaluate_usage(_snapshot(), threshold=0.70),
            subscription="00000000-0000-0000-0000-000000000000",
            resource_group="rg-horoconsult",
            app_name="horoconsult-env-new",
            runner=fake_run,
        )

        assert resumed is False
        assert not any("enable" in command for command in calls)
