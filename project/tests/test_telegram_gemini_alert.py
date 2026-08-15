"""
project/tests/test_telegram_gemini_alert.py
============================================
Unit tests for Telegram Outage Alerts when Google Gemini API fails.
"""

from unittest.mock import MagicMock, patch
from project.mlops.notifications.webhook_notifier import WebhookNotifier
from project.api_router import _trigger_gemini_telegram_alert


def test_notify_gemini_outage_formats_and_sends():
    notifier = WebhookNotifier(telegram_token="123456:ABC-DEF-MOCK", telegram_chat_id="987654321")

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        success = notifier.notify_gemini_outage(
            attempted_models=["gemini-3.5-flash-lite", "gemini-flash-latest", "gemini-3.6-flash"],
            reason="403_blocked / 429",
            details="All keys exhausted"
        )

        assert success is True
        assert mock_urlopen.call_count == 1
        req = mock_urlopen.call_args[0][0]
        assert "api.telegram.org" in req.full_url
        data = req.data.decode("utf-8")
        assert "Google Gemini API Outage" in data
        assert "gemini-3.5-flash-lite" in data
        assert "987654321" in data


def test_trigger_gemini_telegram_alert_cooldown():
    attempted = [
        {"route": "cloud:gemini-3.5-flash-lite[...key1]", "reason": "403_blocked", "latency_ms": 150},
        {"route": "cloud:gemini-flash-latest[...key1]", "reason": "timeout", "latency_ms": 8000},
    ]

    with patch("project.mlops.notifications.webhook_notifier.WebhookNotifier.notify_gemini_outage") as mock_notify:
        import project.api_router
        project.api_router._last_gemini_alert_time = 0.0

        _trigger_gemini_telegram_alert(attempted)
        assert mock_notify.call_count == 1

        # Second call immediately should be suppressed by cooldown
        _trigger_gemini_telegram_alert(attempted)
        assert mock_notify.call_count == 1
