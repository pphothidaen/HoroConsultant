"""
scripts/monitor_kaggle.py
=========================
Monitor Kaggle kernel execution status and pull output logs when complete.

Usage:
    python3 scripts/monitor_kaggle.py              # One-shot status check
    python3 scripts/monitor_kaggle.py --watch      # Poll every 60s until done
    python3 scripts/monitor_kaggle.py --pull-log   # Pull latest output log
"""

from __future__ import annotations
import os
import sys
import json
import time
import requests
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("kaggle_monitor")

KERNEL_SLUG = "horoconsultant-finetune-pipeline"
KERNEL_DIR = ROOT_DIR / "project" / "kaggle_kernel"


def _load_creds() -> tuple[str, str]:
    """Load Kaggle credentials from kaggle.json."""
    kaggle_dirs = [
        Path.home() / ".agy-account-2" / ".kaggle",
        Path.home() / ".kaggle",
        Path("/Users/kimlenglim/.agy-account-2/.kaggle"),
    ]
    for d in kaggle_dirs:
        f = d / "kaggle.json"
        if f.exists():
            creds = json.loads(f.read_text())
            return creds["username"], creds["key"]
    raise FileNotFoundError("kaggle.json not found in any standard location")


def get_kernel_status(username: str, key: str) -> dict:
    """Get kernel execution status via Kaggle REST API."""
    headers = {"Authorization": f"Bearer {key}"}
    resp = requests.get(
        "https://www.kaggle.com/api/v1/kernels/status",
        headers=headers,
        params={"userName": username, "kernelSlug": KERNEL_SLUG},
        timeout=30,
    )
    if resp.ok:
        return resp.json()
    raise RuntimeError(f"Kaggle API error {resp.status_code}: {resp.text[:200]}")


def get_kernel_info(username: str, key: str) -> dict | None:
    """Get kernel info (version, lastRunTime) from kernels list."""
    headers = {"Authorization": f"Bearer {key}"}
    resp = requests.get(
        "https://www.kaggle.com/api/v1/kernels/list",
        headers=headers,
        params={"pageSize": 50, "user": username},
        timeout=30,
    )
    if resp.ok:
        for k in resp.json():
            if KERNEL_SLUG in k.get("ref", ""):
                return k
    return None


def pull_output_log(username: str, key: str) -> bool:
    """Download the latest train_execution.log from Kaggle kernel output via Kaggle CLI."""
    import subprocess
    env = os.environ.copy()
    env["KAGGLE_USERNAME"] = username
    env["KAGGLE_API_TOKEN"] = key
    env["KAGGLE_KEY"] = key

    cmd = ["kaggle", "kernels", "output", f"{username}/{KERNEL_SLUG}", "-p", str(KERNEL_DIR)]
    logger.info(f"🚀 Downloading output via CLI: {' '.join(cmd)}")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if res.returncode == 0:
            logger.info("✅ Output files downloaded successfully!")
            return True
        else:
            logger.warning(f"⚠️ Kaggle output CLI error ({res.returncode}): {res.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ Output download failed: {e}")
        return False


def send_notification(title: str, message: str, status: str = "info") -> None:
    """Send notification via Webhook (Discord / LINE / Webhook URL) and macOS Desktop Alert."""
    emoji = {"complete": "✅", "error": "❌", "info": "ℹ️"}.get(status, "📢")
    full_text = f"{emoji} [{title}] {message}"
    logger.info(f"[NOTIFY] {full_text}")

    # 1. macOS Desktop Notification
    try:
        if sys.platform == "darwin":
            clean_title = title.replace('"', '\\"').replace("'", "\\'")
            clean_msg = message.replace('"', '\\"').replace("'", "\\'")
            script = f'display notification "{clean_msg}" with title "{clean_title}"'
            subprocess.run(["osascript", "-e", script], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        logger.debug(f"macOS desktop notification skipped: {e}")

    # 2. Discord / Generic Webhook
    webhook_url = os.getenv("WEBHOOK_URL") or os.getenv("DISCORD_WEBHOOK_URL")
    if webhook_url:
        try:
            payload = {
                "username": "HoroConsultant Kaggle Bot",
                "content": full_text,
                "embeds": [
                    {
                        "title": title,
                        "description": message,
                        "color": 65280 if status == "complete" else 16711680,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ],
            }
            requests.post(webhook_url, json=payload, timeout=10)
            logger.info("   [OK] Webhook notification sent successfully.")
        except Exception as e:
            logger.warning(f"   [WARNING] Webhook notification failed: {e}")

    # 3. LINE Notify
    line_token = os.getenv("LINE_NOTIFY_TOKEN")
    if line_token:
        try:
            headers = {"Authorization": f"Bearer {line_token}"}
            requests.post("https://notify-api.line.me/api/notify", headers=headers, data={"message": full_text}, timeout=10)
            logger.info("   [OK] LINE Notify notification sent successfully.")
        except Exception as e:
            logger.warning(f"   [WARNING] LINE Notify failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Monitor Kaggle kernel execution")
    parser.add_argument("--watch", action="store_true", help="Poll until kernel finishes")
    parser.add_argument("--pull-log", action="store_true", help="Pull latest output log")
    parser.add_argument("--interval", type=int, default=60, help="Poll interval in seconds")
    args = parser.parse_args()

    username, key = _load_creds()
    logger.info(f"🔑 Using credentials for: {username}")

    if args.pull_log:
        pull_output_log(username, key)
        return

    terminal_statuses = {"complete", "error", "cancelled"}

    while True:
        try:
            status_data = get_kernel_status(username, key)
            status = status_data.get("status", "unknown")
            fail_msg = status_data.get("failureMessage", "")
            info = get_kernel_info(username, key)
            last_run = info.get("lastRunTime", "N/A") if info else "N/A"

            now = datetime.now().strftime("%H:%M:%S")
            status_emoji = {
                "running": "⏳",
                "queued": "🔄",
                "complete": "✅",
                "error": "❌",
                "cancelled": "🚫",
            }.get(status, "❓")

            logger.info(
                f"{status_emoji} [{now}] Kernel status: {status.upper()}"
                + (f" | Failure: {fail_msg}" if fail_msg else "")
                + f" | Last run: {last_run}"
            )

            if status in terminal_statuses:
                if status == "complete":
                    logger.info("🎉 Kernel completed successfully! Pulling output logs...")
                    pull_output_log(username, key)
                    import subprocess
                    subprocess.run(["git", "add", "project/kaggle_kernel/"], cwd=ROOT_DIR, check=False)
                    subprocess.run(
                        ["git", "commit", "-m", f"feat(kaggle): sync output logs (status: {status})"],
                        cwd=ROOT_DIR, check=False
                    )
                    send_notification(
                        "Kaggle Fine-Tuning Complete 100%",
                        f"Kernel {KERNEL_SLUG} completed successfully (Exit Code 0). Outputs downloaded to project/kaggle_kernel/",
                        status="complete",
                    )
                elif status in ("error", "cancelled"):
                    logger.error(f"❌ Kernel ended with status {status}! Pulling logs...")
                    pull_output_log(username, key)
                    send_notification(
                        f"Kaggle Execution {status.upper()}",
                        f"Kernel {KERNEL_SLUG} ended with status: {status}. Failure msg: {fail_msg or 'N/A'}",
                        status="error",
                    )
                break

        except Exception as e:
            logger.error(f"⚠️ Status check error: {e}")

        if not args.watch:
            break

        logger.info(f"💤 Sleeping {args.interval}s before next check...")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
