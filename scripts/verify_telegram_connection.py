"""
scripts/verify_telegram_connection.py
=====================================
Automated Verification & Interactive Setup Engine for Telegram Bot Integration.
Features:
  1. Real-time API Health Check (getMe validation).
  2. Automatic Chat ID Discovery (listens for /start from user).
  3. Live Verification Test Probe with rich HTML card dispatch.
  4. Auto-sync to local .env and GitHub Actions Secrets.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from dotenv import dotenv_values

ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT_DIR / ".env"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("telegram_verifier")


def get_telegram_creds() -> Tuple[Optional[str], Optional[str]]:
    """Retrieve token and chat id from env or .env file."""
    env_vals = dotenv_values(ENV_FILE) if ENV_FILE.exists() else {}
    token = os.getenv("TELEGRAM_BOT_TOKEN") or env_vals.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID") or env_vals.get("TELEGRAM_CHAT_ID")
    return token, chat_id


def verify_bot_token(token: str) -> Tuple[bool, Dict[str, Any]]:
    """Verify if the bot token is valid via Telegram getMe API."""
    if not token or len(token) < 20 or ":" not in token:
        return False, {"error": "รูปแบบ Token ไม่ถูกต้อง (ต้องประกอบด้วย ID:Hash เช่น 123456789:ABC...)"}

    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        req = urllib.request.Request(url, headers={"User-Agent": "HoroConsultant-Validator"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("ok"):
                return True, data.get("result", {})
            return False, data
    except urllib.error.HTTPError as e:
        return False, {"error": f"HTTP Error {e.code}: Unauthorized token"}
    except Exception as e:
        return False, {"error": f"Network Error: {e}"}


def send_test_probe(token: str, chat_id: str, bot_username: str) -> bool:
    """Send a rich test verification card to the user's Telegram chat."""
    try:
        text = (
            "🎉 <b>[HoroConsultant] เชื่อมต่อ Telegram สำเร็จ 100%!</b>\n\n"
            f"• <b>Bot Username:</b> @{bot_username}\n"
            f"• <b>Chat ID:</b> <code>{chat_id}</code>\n"
            "• <b>Hermes Agent:</b> 🟢 <i>Online & Ready to accept commands</i>\n\n"
            "ลองพิมพ์คำสั่งเหล่านี้เพื่อทดสอบ:\n"
            "• /status — ตรวจสอบสถานะโมเดลและ Dataset\n"
            "• /sample — ดูตัวอย่างเนื้อหาจากการสกัดล่าสุด\n"
            "• /distill bazi — สั่งสกัดความรู้ปาจื่อทันที"
        )
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        logger.error(f"Failed to send test message: {e}")
        return False


def discover_chat_id(token: str, timeout_sec: int = 30) -> Optional[str]:
    """Poll getUpdates to automatically detect chat_id when user sends /start."""
    print(f"\n⏳ กำลังรอให้ท่านส่งข้อความหาบอท... (รอ {timeout_sec} วินาที)")
    print("👉 กรุณาเปิด Telegram ค้นหาบอทของท่าน แล้วกดปุ่ม 'START' หรือพิมพ์ข้อความใดก็ได้ส่งหาบอท")

    url = f"https://api.telegram.org/bot{token}/getUpdates"
    for _ in range(timeout_sec):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                updates = data.get("result", [])
                if updates:
                    last_msg = updates[-1].get("message", {})
                    chat_id = str(last_msg.get("chat", {}).get("id", ""))
                    sender_name = last_msg.get("from", {}).get("first_name", "User")
                    if chat_id:
                        print(f"\n✅ ตรวจพบข้อความจากคุณ {sender_name}! (Chat ID: {chat_id})")
                        return chat_id
        except Exception:
            pass
        import time
        time.sleep(1)
    return None


def update_env(key: str, value: str):
    """Save variable to .env."""
    lines = []
    if ENV_FILE.exists():
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    new_lines = []
    found = False
    for line in lines:
        if line.startswith(f"{key}=") or line.startswith(f"export {key}="):
            new_lines.append(f'{key}="{value}"')
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f'{key}="{value}"')
    ENV_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def sync_github_secret(secret_name: str, secret_value: str) -> bool:
    """Sync secret to GitHub Actions."""
    if not shutil.which("gh"):
        return False
    try:
        cmd = ["gh", "secret", "set", secret_name, "-R", "pphothidaen/HoroConsultant", "--body", secret_value]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return res.returncode == 0
    except Exception:
        return False


def run_diagnostics(interactive: bool = False):
    print("=" * 70)
    print("🔍 [HoroConsultant] TELEGRAM INTEGRATION HEALTH & VERIFICATION DIAGNOSTICS")
    print("=" * 70)

    token, chat_id = get_telegram_creds()

    if not token:
        print("\n❌ สถานะ: ยังไม่ได้เชื่อมต่อ Telegram Bot Token (TELEGRAM_BOT_TOKEN is MISSING)")
        print("\n📖 วิธีสร้างและตั้งค่า Telegram Bot ใน 2 นาที:")
        print("1. เปิดแอป Telegram แล้วค้นหาบัญชีทางการชื่อ: @BotFather")
        print("2. พิมพ์คำสั่ง /newbot แล้วตั้งชื่อบอท (เช่น HoroConsultant Bot)")
        print("3. ตั้ง Username ที่ลงท้ายด้วย bot (เช่น my_horo_consultant_bot)")
        print("4. BotFather จะมอบ API Token ให้ (ตัวอย่าง: 7123456789:AAFx...)")
        print("5. นำ Token และ Chat ID มาบันทึกลงใน .env หรือรันคำสั่ง:")
        print("   python3 scripts/verify_telegram_connection.py --setup\n")
        return

    # Verify Token
    valid, info = verify_bot_token(token)
    if not valid:
        print(f"\n❌ สถานะ: TELEGRAM_BOT_TOKEN ไม่ถูกต้อง ({info.get('error', 'Unknown error')})")
        print("👉 กรุณาตรวจสอบค่า Token อีกครั้งจาก @BotFather")
        return

    bot_name = info.get("first_name", "Bot")
    bot_username = info.get("username", "unknown_bot")
    print(f"\n✅ ตรวจสอบ Token สำเร็จ! บอทของคุณคือ: {bot_name} (@{bot_username})")

    # Check Chat ID
    if not chat_id:
        print("⚠️ ยังไม่ระบุ TELEGRAM_CHAT_ID")
        if interactive:
            discovered = discover_chat_id(token, timeout_sec=20)
            if discovered:
                chat_id = discovered
                update_env("TELEGRAM_CHAT_ID", chat_id)
                sync_github_secret("TELEGRAM_CHAT_ID", chat_id)
            else:
                print("❌ ไม่พบข้อความใหม่ สามารถค้นหา Chat ID ของท่านได้จากบอท @userinfobot")
                return
        else:
            print("👉 คำแนะนำ: เปิดบอท @userinfobot บน Telegram เพื่อดู Id ของท่าน แล้วใส่ใน .env")
            return

    # Send Probe Message
    print(f"📡 กำลังทดสอบส่งข้อความยืนยันไปยัง Chat ID: {chat_id}...")
    sent = send_test_probe(token, chat_id, bot_username)
    if sent:
        print("\n🎉 การเชื่อมต่อใช้งานได้จริง 100% (LIVE VERIFIED)!")
        print("📱 กรุณาเปิดแอป Telegram จะพบข้อความยืนยันจาก Hermes Agent ส่งถึงท่านแล้วครับ")
    else:
        print("\n❌ ไม่สามารถส่งข้อความได้ กรุณาตรวจสอบว่าท่านได้กด START หรือส่งข้อความหาบอทแล้วหรือยัง")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    is_interactive = "--setup" in sys.argv or "-i" in sys.argv
    run_diagnostics(interactive=is_interactive)
