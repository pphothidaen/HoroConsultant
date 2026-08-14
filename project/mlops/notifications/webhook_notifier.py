"""
project/mlops/notifications/webhook_notifier.py
================================================
Unified Webhook & Notification Engine for Telegram, Discord, and Slack.
Sends real-time alerts for scheduled extraction runs, dataset milestones, and training statuses.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("webhook_notifier")


class WebhookNotifier:
    """Dispatches formatted alerts to configured messaging webhooks."""

    def __init__(
        self,
        telegram_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        discord_webhook_url: Optional[str] = None
    ):
        self.telegram_token = telegram_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = telegram_chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.discord_webhook_url = discord_webhook_url or os.getenv("DISCORD_WEBHOOK_URL")

    def notify_distillation_complete(self, stats: Dict[str, Any], sample_preview: Optional[Dict[str, Any]] = None) -> bool:
        """Send rich notification when knowledge distillation finishes, including sample preview."""
        title = "📚 [HoroConsultant MLOps] Knowledge Distillation Finished"
        body_lines = [
            f"• <b>Output Dataset:</b> <code>{stats.get('output_path', 'N/A')}</code>",
            f"• <b>Total Extracted:</b> <code>{stats.get('total_input', 0)}</code>",
            f"• <b>Validated & Deduped:</b> <code>{stats.get('final_unique_count', 0)}</code>",
            f"• <b>Format:</b> <code>{stats.get('format', 'chatml')}</code>",
            f"• <b>Timestamp:</b> <code>{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</code>"
        ]

        if sample_preview:
            instr = sample_preview.get("instruction") or (sample_preview.get("messages", [{}])[1].get("content") if "messages" in sample_preview else "")
            out = sample_preview.get("output") or (sample_preview.get("messages", [{}])[2].get("content") if "messages" in sample_preview else "")
            body_lines.append("\n🔍 <b>Latest Mined Sample Preview:</b>")
            body_lines.append(f"<b>Q:</b> <i>{instr[:150]}...</i>" if len(instr) > 150 else f"<b>Q:</b> <i>{instr}</i>")
            body_lines.append(f"<b>A:</b> <i>{out[:220]}...</i>" if len(out) > 220 else f"<b>A:</b> <i>{out}</i>")

        body = "\n".join(body_lines)
        return self._send_all(title, body, status="SUCCESS")

    def notify_training_status(self, kernel_id: str, status: str, details: str = "") -> bool:
        """Send notification regarding Kaggle GPU training status."""
        title = f"⚡ [HoroConsultant MLOps] Fine-Tuning: {status.upper()}"
        body = (
            f"• <b>Target Model:</b> <code>pphothidaen/qwen2.5-7b-bazi-instruct-4bit</code>\n"
            f"• <b>Kaggle Kernel:</b> <code>{kernel_id}</code>\n"
            f"• <b>Status:</b> <b>{status}</b>\n"
            f"• <b>Details:</b> {details or 'N/A'}\n"
            f"• <b>Timestamp:</b> <code>{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</code>"
        )
        return self._send_all(title, body, status=status)

    def notify_error(self, step_name: str, error_message: str) -> bool:
        """Send urgent error alert with truncated error message."""
        title = f"🚨 [HoroConsultant MLOps Error] Failure in {step_name}"
        body = (
            f"• <b>Step:</b> <code>{step_name}</code>\n"
            f"• <b>Error Snippet:</b> <code>{error_message[:400]}</code>\n"
            f"• <b>Action:</b> Pipeline fallback engaged."
        )
        return self._send_all(title, body, status="ERROR")

    def send_direct_message(self, message: str, chat_id: Optional[str] = None) -> bool:
        """Send a direct message to a specific Telegram chat."""
        target_chat = chat_id or self.telegram_chat_id
        if not self.telegram_token or not target_chat:
            return False

        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                "chat_id": target_chat,
                "text": message,
                "parse_mode": "HTML"
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except Exception as e:
            logger.warning(f"[TELEGRAM] Direct send failed: {e}")
            return False

    def _send_all(self, title: str, body: str, status: str = "INFO") -> bool:
        """Dispatch to Telegram and Discord if configured."""
        success = True
        logger.info(f"[NOTIFIER] [{status}] {title}\n{body}")

        if self.telegram_token and self.telegram_chat_id:
            try:
                tg_msg = f"<b>{title}</b>\n\n{body}"
                url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
                payload = {
                    "chat_id": self.telegram_chat_id,
                    "text": tg_msg,
                    "parse_mode": "HTML"
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status != 200:
                        logger.warning(f"[TELEGRAM] Response code: {resp.status}")
            except Exception as e:
                logger.warning(f"[TELEGRAM] Failed to send telegram message: {e}")
                success = False

        if self.discord_webhook_url:
            try:
                color = 0x00FF00 if status == "SUCCESS" else (0xFF0000 if status == "ERROR" else 0x3498DB)
                payload = {
                    "embeds": [{
                        "title": title,
                        "description": body.replace("<b>", "**").replace("</b>", "**").replace("<code>", "`").replace("</code>", "`").replace("<i>", "*").replace("</i>", "*"),
                        "color": color,
                        "footer": {"text": "HoroConsultant Autonomous MLOps Pipeline"}
                    }]
                }
                req = urllib.request.Request(
                    self.discord_webhook_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status not in (200, 204):
                        logger.warning(f"[DISCORD] Response code: {resp.status}")
            except Exception as e:
                logger.warning(f"[DISCORD] Failed to send discord message: {e}")
                success = False

        return success
