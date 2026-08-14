"""
project/tests/test_cookie_manager.py
====================================
Comprehensive Test Suite for CookieManager, Silent Refresh, and Cloud Secret Sync.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from project.mlops.distillation.cookie_manager import CookieManager
from project.mlops.distillation.notebooklm_client import NotebookLMClient
from project.mlops.notifications.webhook_notifier import WebhookNotifier


def test_cookie_validity_check_empty():
    manager = CookieManager()
    is_valid, reason = manager.check_cookie_validity(cookie_str="", skip_network=True)
    assert is_valid is False
    assert "EMPTY" in reason


def test_cookie_validity_check_with_valid_string():
    manager = CookieManager()
    # Test structurally valid cookie with SID/HSID
    mock_cookie = "SID=valid_sid_token_12345; HSID=valid_hsid_token; SSID=valid_ssid"
    is_valid, reason = manager.check_cookie_validity(cookie_str=mock_cookie, skip_network=True)
    assert is_valid is True
    assert "VALID" in reason


def test_sync_all_targets(tmp_path, monkeypatch):
    mock_env = tmp_path / ".env"
    mock_env.write_text("SOME_VAR=123\n", encoding="utf-8")
    monkeypatch.setattr("project.mlops.distillation.cookie_manager.ENV_FILE", mock_env)

    manager = CookieManager()
    res = manager.sync_all_targets("NOTEBOOKLM_SESSION_COOKIE=new_token_456")
    
    assert res["local_env"] is True
    content = mock_env.read_text(encoding="utf-8")
    assert "NOTEBOOKLM_SESSION_COOKIE" in content


def test_reactive_recovery_triggers_alert():
    mock_notifier = MagicMock(spec=WebhookNotifier)
    manager = CookieManager(notifier=mock_notifier)
    
    with patch.object(manager, "attempt_silent_refresh", return_value=(False, None)):
        recovered, cookie = manager.handle_reactive_recovery()
        assert recovered is False
        mock_notifier._send_all.assert_called_once()
        call_args = mock_notifier._send_all.call_args[0]
        assert "Expired" in call_args[0]


def test_notebooklm_client_integration_with_cookie_manager():
    client = NotebookLMClient(session_cookie="SID=test_token_123")
    res = client.query_notebook("nb_bazi_classics", "ทดสอบการรีเฟรช")
    assert "answer" in res
    assert "citations" in res
