"""
scripts/check_cookie_heartbeat.py
=================================
Automated Heartbeat & Health Check for Google NotebookLM Session Cookie.
Checks cookie validity and notifies Telegram on expiration or failure.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from project.mlops.distillation.cookie_manager import CookieManager
from project.mlops.notifications.webhook_notifier import WebhookNotifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cookie_heartbeat")


def run_heartbeat(
    silent_if_ok: bool = True,
    notify_always: bool = False,
    skip_network: bool = False,
) -> dict:
    notifier = WebhookNotifier()
    cookie_mgr = CookieManager(notifier=notifier)

    is_valid, reason = cookie_mgr.check_cookie_validity(skip_network=skip_network)
    cookie_len = len(cookie_mgr.get_current_cookie())

    logger.info(f"[HEARTBEAT] Cookie validity: {is_valid}, Reason: {reason}, Length: {cookie_len}")

    result = {
        "is_valid": is_valid,
        "reason": reason,
        "cookie_length": cookie_len,
        "status": "HEALTHY" if is_valid else "EXPIRED_OR_INVALID",
    }

    if not is_valid:
        logger.info("[HEARTBEAT] Triggering Hermes Agent Autonomous Cloud Auto-Heal...")
        recovery_res = cookie_mgr.handle_autonomous_cloud_recovery()
        if recovery_res.get("recovered") and recovery_res.get("is_valid"):
            result["is_valid"] = True
            result["status"] = "RECOVERED_HEALTHY"
            result["cookie_length"] = recovery_res.get("cookie_length", 0)
            result["reason"] = "RECOVERED_AND_VERIFIED"
    elif notify_always:
        title = "🍪 [NotebookLM Heartbeat] Cookie Active & Healthy"
        body = (
            "• <b>Service:</b> <code>Google NotebookLM Knowledge Extraction</code>\n"
            f"• <b>Status:</b> 🟢 <b>ACTIVE ({reason})</b>\n"
            f"• <b>Cookie Length:</b> <code>{cookie_len} chars</code>\n"
            "• <b>Next Scheduled Run:</b> Monday / Thursday 09:00 AM Bangkok Time"
        )
        notifier._send_all(title, body, status="SUCCESS")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Google NotebookLM Session Cookie Heartbeat Guard")
    parser.add_argument("--silent-if-ok", action="store_true", default=True, help="Do not send Telegram message if healthy")
    parser.add_argument("--notify-always", action="store_true", help="Send Telegram message even if healthy")
    parser.add_argument("--skip-network", action="store_true", help="Perform only structural check without HTTP call")
    parser.add_argument("--warn-only", action="store_true", help="Exit with 0 even if cookie is expired (after notifying)")
    parser.add_argument("--json", action="store_true", help="Output JSON result")

    args = parser.parse_args()
    res = run_heartbeat(
        silent_if_ok=args.silent_if_ok,
        notify_always=args.notify_always,
        skip_network=args.skip_network,
    )

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))

    if args.warn_only:
        return 0
    return 0 if res["is_valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
