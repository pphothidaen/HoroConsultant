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
from project.mlops.notifications.telegram_bot import TelegramBotController


@pytest.fixture
def client():
    return TestClient(app)


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


def test_telegram_bot_unknown_command():
    bot = TelegramBotController()
    res = bot.handle_command("/unknown_xyz", "12345")
    assert "ไม่รู้จักคำสั่ง" in res


def test_telegram_webhook_endpoint(client):
    payload = {
        "update_id": 9999,
        "message": {
            "message_id": 1,
            "from": {"id": 12345, "first_name": "Test"},
            "chat": {"id": 12345, "type": "private"},
            "text": "/status"
        }
    }
    res = client.post("/api/v1/mlops/telegram/webhook", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["action"] == "dispatched"
