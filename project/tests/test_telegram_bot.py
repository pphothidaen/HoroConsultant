"""
project/tests/test_telegram_bot.py
==================================
Comprehensive Test Suite for Interactive Telegram Bot Controller and Webhook.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from project.main import app
from project.mlops.notifications import telegram_bot as telegram_bot_module
from project.mlops.notifications.telegram_bot import TelegramBotController


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def configured_chat_id(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")


def test_telegram_bot_help_command():
    bot = TelegramBotController()
    res = bot.handle_command("/help", "12345")
    assert "/status" in res
    assert "/distill" in res
    assert "/sample" in res
    assert "/train" in res


def test_telegram_bot_status_command():
    bot = TelegramBotController()
    res = bot.handle_command("/status", "12345")
    assert "pphothidaen/qwen2.5-7b-bazi-instruct-4bit" in res
    assert "Curated Datasets" in res


def test_telegram_bot_sample_command():
    bot = TelegramBotController()
    res = bot.handle_command("/sample", "12345")
    assert "ตัวอย่างเนื้อหา" in res or "โจทย์" in res or "ชุดข้อมูล" in res


def test_telegram_bot_distill_command():
    bot = TelegramBotController()
    res = bot.handle_command("/distill bazi", "12345")
    assert "Hermes Agent" in res
    assert "BAZI" in res


def test_telegram_bot_cookie_command():
    bot = TelegramBotController()
    res = bot.handle_command("/cookie", "12345")
    assert "Google Session Cookie Health" in res
    assert "Cookie Length" in res
    res_alias = bot.handle_command("/cookie_check", "12345")
    assert "Google Session Cookie Health" in res_alias


def test_telegram_bot_kaggle_commands():
    bot = TelegramBotController()
    res_status = bot.handle_command("/kaggle_status", "12345")
    assert "Kaggle GPU Training Status" in res_status

    with patch.object(bot.orchestrator, "trigger_kaggle_training") as mock_train:
        mock_train.return_value = {"status": "RUNNING", "kernel_id": "test/k", "target_model": "m"}
        res_train = bot.handle_command("/finetune", "12345")
        assert "Fine-Tuning" in res_train
        assert "Kaggle GPU" in res_train


def test_telegram_bot_unknown_command():
    bot = TelegramBotController()
    res = bot.handle_command("/unknown_xyz", "12345")
    assert "ไม่รู้จักคำสั่ง" in res


def test_persist_telegram_chat_id_writes_missing_value(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text('TELEGRAM_CHAT_ID=""\n', encoding="utf-8")
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.setattr(telegram_bot_module, "ENV_FILE", env_file)

    assert telegram_bot_module.persist_telegram_chat_id("12345") is True
    assert 'TELEGRAM_CHAT_ID="12345"' in env_file.read_text(encoding="utf-8")


def test_telegram_bot_natural_language_mlops():
    bot = TelegramBotController()
    res = bot.handle_command("เช็คการเทรนบน kaggle หน่อย", "12345")
    assert "Kaggle GPU Training Status" in res

    res_distill = bot.handle_command("ช่วยสกัดความรู้ปาจื่อให้หน่อย", "12345")
    assert "Hermes Agent" in res_distill
    assert "BAZI" in res_distill


def test_telegram_bot_natural_language_consultation():
    from project.mlops.notifications.telegram_controller import telegram_controller
    res = telegram_controller.handle_command("ช่วยวิเคราะห์ดวงจีนให้หน่อย วันนี้ดวงดีไหม", "12345")
    assert "ซินแส AI" in res or "แม่ธาตุ" in res or "Hermes Metaphysics" in res


def test_telegram_bot_access_control_unauthorized(monkeypatch):
    from project.mlops.notifications.telegram_controller import telegram_controller
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    telegram_controller.allowed_chat_id = "12345"
    res = telegram_controller.handle_command("/status", "99999")
    assert "Access Denied" in res
