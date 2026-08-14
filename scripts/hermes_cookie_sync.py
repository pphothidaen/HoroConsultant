"""
scripts/hermes_cookie_sync.py
=============================
Hermes Agent Autonomous Cookie Extractor & Cloud Secret Synchronizer.
Workflow:
  1. Opens interactive Playwright browser for Google Account authentication.
  2. Extracts authenticated Google / NotebookLM cookies.
  3. Writes NOTEBOOKLM_SESSION_COOKIE directly into local .env.
  4. Automatically uploads the secret to GitHub Actions (via `gh secret set`)
     and Doppler (if configured), achieving 100% automated Zero-Manual sync!

Usage:
------
    python3 scripts/hermes_cookie_sync.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

from playwright.async_api import async_playwright

ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT_DIR / ".env"
COOKIE_STORE_FILE = ROOT_DIR / ".notebooklm_session.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hermes_cookie_sync")


async def hermes_extract_and_sync_cookies(email_hint: str | None = None):
    logger.info("🤖 [HERMES AGENT] Starting Autonomous Google Session & Secret Sync Flow...")
    if email_hint:
        logger.info(f"👤 Target Account: {email_hint}")
    logger.info("👉 กำลังเปิดหน้าต่างเบราว์เซอร์ กรุณายืนยันตัวตน Google Account ของท่านเพื่อเชื่อมต่อ NotebookLM")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            channel="chrome" if sys.platform == "darwin" else None,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        target_url = "https://notebooklm.google.com/"
        if email_hint:
            target_url = f"https://accounts.google.com/AccountChooser?Email={email_hint}&continue=https://notebooklm.google.com/"

        await page.goto(target_url)

        logger.info("⏳ [HERMES AGENT] กำลังตรวจจับสถานะการเข้าสู่ระบบ Google Account...")
        
        max_wait_seconds = 180
        logged_in = False
        for sec in range(max_wait_seconds):
            await asyncio.sleep(1)
            current_url = page.url
            if ("notebooklm.google.com" in current_url or "notebook.google.com" in current_url) and "accounts.google.com" not in current_url:
                await asyncio.sleep(3)  # Wait for all token exchanges to settle
                logged_in = True
                break
            if sec % 15 == 0 and sec > 0:
                logger.info(f"⏳ [HERMES AGENT] รอการยืนยันตัวตน... ({sec}/{max_wait_seconds}s)")

        if not logged_in:
            logger.error("[ERROR] หมดเวลารอการเข้าสู่ระบบ กรุณาลองใหม่อีกครั้ง")
            await browser.close()
            return False

        # Extract all cookies
        cookies = await context.cookies()
        COOKIE_STORE_FILE.write_text(json.dumps(cookies, indent=2), encoding="utf-8")
        
        cookie_header_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        await browser.close()

    # Step 1: Update Local .env
    update_local_env("NOTEBOOKLM_SESSION_COOKIE", cookie_header_str)
    logger.info("✅ [1/2] บันทึก NOTEBOOKLM_SESSION_COOKIE ลงใน Local .env เรียบร้อยแล้ว")

    # Step 2: Push to GitHub Actions Secrets via gh CLI
    github_synced = sync_to_github_actions("NOTEBOOKLM_SESSION_COOKIE", cookie_header_str)

    # Step 3: Push to Doppler if Doppler CLI is available
    sync_to_doppler("NOTEBOOKLM_SESSION_COOKIE", cookie_header_str)

    print("\n" + "="*70)
    print("🎉 [HERMES AGENT] การซิงค์ Cookie และความปลอดภัยเสร็จสมบูรณ์ 100%!")
    print("="*70)
    print(f"• Local .env Updated        : ✅ YES")
    print(f"• GitHub Actions Secret Sync : {'✅ YES' if github_synced else '⚠️ กรุณาใช้ gh auth login หรือใส่เองใน GitHub UI'}")
    print("="*70 + "\n")
    return True


def update_local_env(key: str, value: str):
    """Update or append environment variable in .env."""
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


def sync_to_github_actions(secret_name: str, secret_value: str) -> bool:
    """Sync a secret directly to GitHub Repository Secrets using GitHub CLI."""
    if not shutil.which("gh"):
        logger.warning("[GH CLI] ไม่พบคำสั่ง gh (GitHub CLI) ในเครื่อง ข้ามการอัปโหลด Secret ขึ้น GitHub Actions")
        return False

    try:
        cmd = ["gh", "secret", "set", secret_name, "--body", secret_value]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if res.returncode == 0:
            logger.info(f"✅ [2/2] ซิงค์ '{secret_name}' ขึ้นสู่ GitHub Actions Secrets สำเร็จแล้ว!")
            return True
        else:
            logger.warning(f"[GH CLI] ไม่สามารถตั้งค่า Secret ผ่าน gh ได้ ({res.stderr.strip()})")
            return False
    except Exception as e:
        logger.warning(f"[GH CLI] Error setting secret: {e}")
        return False


def sync_to_doppler(secret_name: str, secret_value: str) -> bool:
    """Sync secret to Doppler secret manager if available."""
    if not shutil.which("doppler"):
        return False
    try:
        cmd = ["doppler", "secrets", "set", f"{secret_name}={secret_value}"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if res.returncode == 0:
            logger.info(f"✅ ซิงค์ '{secret_name}' ไปยัง Doppler Secrets เรียบร้อยแล้ว")
            return True
    except Exception:
        pass
    return False


if __name__ == "__main__":
    email_arg = None
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        email_arg = sys.argv[1]
    elif "--email" in sys.argv:
        idx = sys.argv.index("--email")
        if idx + 1 < len(sys.argv):
            email_arg = sys.argv[idx + 1]
    asyncio.run(hermes_extract_and_sync_cookies(email_hint=email_arg))
