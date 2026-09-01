from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(ROOT))

import scripts.multiagent_prompt_command as command


RUNTIME_CONFIG = (
    ROOT / ".agents/config/multiagent_prompt_command.runtime-readonly-v3.yaml"
)


def test_agy4_requires_explicit_runtime_account_and_role_route():
    config = command.load_config(RUNTIME_CONFIG)
    accounts = config["accounts"]
    routes = {
        role: definition["alias"]
        for role, definition in config["roles"].items()
    }

    assert "agy4" in accounts, "AGY4 runtime account registration is required"
    assert "agy4" in routes.values(), "AGY4 runtime role route is required"


def test_agy_transport_stays_denied_without_native_prespawn_receipt(tmp_path, monkeypatch):
    transport_calls = 0

    def forbidden_popen(*_args, **_kwargs):
        nonlocal transport_calls
        transport_calls += 1
        raise AssertionError("provider transport must remain unreachable")

    monkeypatch.setattr(command.subprocess, "Popen", forbidden_popen)

    with pytest.raises(command.PlatformNativePrespawnReceiptRequired) as exc:
        command._run_provider_process(
            ["agy4"], cwd=str(tmp_path), env={}, input="", provider="agy"
        )

    assert exc.value.code == "PLATFORM_NATIVE_PRESPAWN_RECEIPT_REQUIRED"
    assert transport_calls == 0
