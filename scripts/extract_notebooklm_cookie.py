"""
scripts/extract_notebooklm_cookie.py
====================================
Interactive Playwright Script to Log In to Google NotebookLM,
extract all authenticated Session Cookies, and save them to .env
for automated Cloud / Headless extraction.

Usage:
------
    python3 scripts/extract_notebooklm_cookie.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from playwright.async_api import async_playwright

ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT_DIR / ".env"
COOKIE_STORE_FILE = ROOT_DIR / ".notebooklm_session.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cookie_extractor")


async def extract_cookie():
    logger.info("🚀 Launching interactive browser for Google NotebookLM Login...")
    logger.info("👉 เมื่อหน้าต่างเบราว์เซอร์เปิดขึ้น กรุณาล็อกอิน Google Account ของท่าน")

    async with async_playwright() as p:
        # Launch headed browser so user can see and complete Google 2FA/Login
        browser = await p.chromium.launch(
            headless=False,
            channel="chrome" if sys.platform == "darwin" else None,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        await page.goto("https://notebooklm.google.com/")

        logger.info("⏳ กำลังรอให้ท่านล็อกอิน Google Account จนถึงหน้าหลักของ NotebookLM...")
        
        # Wait until user reaches the NotebookLM home dashboard (URL or selector check)
        max_wait_seconds = 180
        for sec in range(max_wait_seconds):
            await asyncio.sleep(1)
            current_url = page.url
            if "notebooklm.google.com" in current_url and "accounts.google.com" not in current_url:
                # User has logged in and landed on NotebookLM!
                await asyncio.sleep(3)  # Give time for all auth cookies to be set
                break
            if sec % 15 == 0 and sec > 0:
                logger.info(f"⏳ ยังคงรอการล็อกอิน... ({sec}/{max_wait_seconds}s)")

        # Extract all cookies
        cookies = await context.cookies()
        
        # Format cookies into header string
        cookie_header_parts = []
        for c in cookies:
            cookie_header_parts.append(f"{c['name']}={c['value']}")
        
        cookie_header_str = "; ".join(cookie_header_parts)

        # Save to local session JSON file
        COOKIE_STORE_FILE.write_text(json.dumps(cookies, indent=2), encoding="utf-8")
        logger.info(f"[OK] Raw cookies saved to: {COOKIE_STORE_FILE}")

        # Update .env file with NOTEBOOKLM_SESSION_COOKIE
        if cookie_header_str:
            update_env_variable("NOTEBOOKLM_SESSION_COOKIE", cookie_header_str)
            logger.info("🎉 บันทึก NOTEBOOKLM_SESSION_COOKIE ลงใน .env เรียบร้อยแล้ว!")
            print("\n" + "="*70)
            print("🔑 NOTEBOOKLM_SESSION_COOKIE (สำหรับนำไปใส่ใน GitHub Secrets):")
            print("="*70)
            print(cookie_header_str[:120] + " ... [TRUNCATED FOR DISPLAY]")
            print("="*70 + "\n")
        else:
            logger.warning("[WARNING] ไม่พบคุกกี้หลังการล็อกอิน")

        await browser.close()


def update_env_variable(key: str, value: str):
    """Safely update or add an environment variable in .env file."""
    lines = []
    found = False
    if ENV_FILE.exists():
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()

    new_lines = []
    for line in lines:
        if line.startswith(f"{key}=") or line.startswith(f"export {key}="):
            new_lines.append(f'{key}="{value}"')
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f'{key}="{value}"')

    ENV_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(extract_cookie())
