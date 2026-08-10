"""Security regressions for automation secret handling."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "sync_doppler_secrets.py"


def _load_sync_module():
    spec = importlib.util.spec_from_file_location("sync_doppler_secrets", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_doppler_auth_failure_never_prints_secret_values(
    tmp_path, monkeypatch, caplog, capsys
):
    module = _load_sync_module()
    canary = "CANARY_VALUE_MUST_NEVER_APPEAR"
    env_file = tmp_path / ".env.test"
    env_file.write_text(f"DOCKER_PASSWORD={canary}\n", encoding="utf-8")

    monkeypatch.setattr(module, "sync_github_secrets", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(module, "get_doppler_cli_path", lambda: "doppler")
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=1,
            stdout="",
            stderr=f"must provide a token; rejected value={canary}",
        ),
    )

    success = module.sync_secrets_to_doppler(env_file)
    captured = capsys.readouterr()
    logs = caplog.text

    assert success is False
    assert canary not in captured.out
    assert canary not in captured.err
    assert canary not in logs
