"""Regression tests for Telegram notification secret discovery."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "verify_telegram_connection.py"


def _load_verifier_module():
    spec = importlib.util.spec_from_file_location("verify_telegram_connection", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_get_telegram_creds_falls_back_to_production_env(tmp_path, monkeypatch) -> None:
    module = _load_verifier_module()
    local_env = tmp_path / ".env"
    production_env = tmp_path / ".env.production"
    local_env.write_text("APP_ENV=development\n", encoding="utf-8")
    production_env.write_text(
        "\n".join(
            [
                "TELEGRAM_BOT_TOKEN=123456789:PRODUCTION_TEST_TOKEN",
                "TELEGRAM_CHAT_ID=987654321",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.setattr(module, "PRODUCTION_ENV_FILE", production_env)

    token, chat_id = module.get_telegram_creds(local_env)

    assert token == "123456789:PRODUCTION_TEST_TOKEN"
    assert chat_id == "987654321"


def test_environment_values_override_env_files(tmp_path, monkeypatch) -> None:
    module = _load_verifier_module()
    local_env = tmp_path / ".env"
    local_env.write_text(
        "\n".join(
            [
                "TELEGRAM_BOT_TOKEN=123456789:FILE_TEST_TOKEN",
                "TELEGRAM_CHAT_ID=111111",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456789:ENV_TEST_TOKEN")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "222222")

    token, chat_id = module.get_telegram_creds(local_env)

    assert token == "123456789:ENV_TEST_TOKEN"
    assert chat_id == "222222"
