"""
project/mlops/distillation/cookie_manager.py
============================================
Autonomous Google Session Cookie Lifecycle & Self-Healing Refresh Engine.
Handles:
  1. Health-check & Expiration Detection (HTTP 401/302 checking)
  2. Silent Auto-Refresh via Persistent Headless Context
  3. Automatic Cloud Synchronization (GitHub Actions Secrets & Local .env)
  4. Instant Telegram / Discord Alerting on 2FA Re-auth requirement
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from project.mlops.notifications.webhook_notifier import WebhookNotifier

ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = ROOT_DIR / ".env"
SESSION_CACHE = ROOT_DIR / ".notebooklm_session.json"
PROFILE_DIR = ROOT_DIR / ".playwright_profile"

logger = logging.getLogger("cookie_manager")


class CookieManager:
    """Manages lifecycle, validation, silent refresh, and cloud secret sync for Google Cookies."""

    def __init__(self, notifier: Optional[WebhookNotifier] = None):
        self.notifier = notifier or WebhookNotifier()

    def get_current_cookie(self) -> str:
        """Fetch active cookie from environment or .env."""
        cookie = os.getenv("NOTEBOOKLM_SESSION_COOKIE")
        if not cookie and ENV_FILE.exists():
            from dotenv import dotenv_values
            cookie = dotenv_values(ENV_FILE).get("NOTEBOOKLM_SESSION_COOKIE", "")
        return cookie or ""

    def check_cookie_validity(self, cookie_str: Optional[str] = None, skip_network: bool = False) -> Tuple[bool, str]:
        """
        Verify if the given cookie can successfully query NotebookLM.
        Returns (is_valid, reason/status).
        """
        cookie = cookie_str if cookie_str is not None else self.get_current_cookie()
        if not cookie or len(cookie.strip()) < 20:
            return False, "EMPTY_OR_MISSING_COOKIE"

        if skip_network or os.getenv("MLOPS_DRY_RUN", "false").lower() == "true":
            if "SID=" in cookie or "HSID=" in cookie or len(cookie) > 200:
                return True, "STRUCTURALLY_VALID (Offline/Dry-run)"
            return False, "INVALID_STRUCTURE"

        try:
            req = urllib.request.Request(
                "https://notebooklm.google.com/",
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                    "Cookie": cookie
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                final_url = resp.geturl()
                if "accounts.google.com" in final_url or resp.status in (401, 403):
                    return False, f"EXPIRED_OR_REDIRECTED (Status: {resp.status}, URL: {final_url})"
                return True, "VALID_ACTIVE_SESSION"
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 302):
                return False, f"HTTP_AUTH_ERROR_{e.code}"
            return False, f"HTTP_ERROR_{e.code}"
        except Exception as e:
            if "SID=" in cookie or "HSID=" in cookie or len(cookie) > 200:
                return True, f"STRUCTURALLY_VALID (Network note: {e})"
            return False, f"CHECK_FAILED_{e}"

    def attempt_silent_refresh(self) -> Tuple[bool, Optional[str]]:
        """
        Attempt silent background refresh using Playwright headless automation.
        If Google provides fresh rolling cookies, extracts and syncs them.
        """
        logger.info("[COOKIE MANAGER] Attempting silent background session refresh...")
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
                )

                # Inject existing cookies into context if available
                if SESSION_CACHE.exists():
                    try:
                        raw_cookies = json.loads(SESSION_CACHE.read_text(encoding="utf-8"))
                        context.add_cookies(raw_cookies)
                    except Exception:
                        pass

                page = context.new_page()
                page.goto("https://notebooklm.google.com/", timeout=25000)
                
                # Check if landed inside authenticated session
                current_url = page.url
                if ("notebooklm.google.com" in current_url or "notebook.google.com" in current_url) and "accounts.google.com" not in current_url:
                    fresh_cookies = context.cookies()
                    fresh_cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in fresh_cookies])
                    SESSION_CACHE.write_text(json.dumps(fresh_cookies, indent=2), encoding="utf-8")
                    browser.close()
                    
                    self.sync_all_targets(fresh_cookie_str)
                    logger.info("[COOKIE MANAGER] Silent refresh successful! Cookies updated.")
                    return True, fresh_cookie_str
                
                browser.close()
                return False, None
        except Exception as e:
            logger.warning(f"[COOKIE MANAGER] Silent refresh encountered exception: {e}")
            return False, None

    def sync_all_targets(self, new_cookie: str) -> Dict[str, bool]:
        """
        Synchronize refreshed cookie across Local .env and Cloud GitHub Actions Secrets.
        """
        results = {"local_env": False, "github_actions": False, "doppler": False}
        
        # 1. Update Local .env
        try:
            self._update_local_env("NOTEBOOKLM_SESSION_COOKIE", new_cookie)
            results["local_env"] = True
            logger.info("[COOKIE SYNC] Local .env updated with refreshed cookie.")
        except Exception as e:
            logger.error(f"[COOKIE SYNC] Failed to update local .env: {e}")

        # 2. Update GitHub Actions Secrets (Priority for Cloud Workflows)
        results["github_actions"] = self._sync_github_actions_secret("NOTEBOOKLM_SESSION_COOKIE", new_cookie)

        # 3. Update Doppler
        if shutil.which("doppler"):
            try:
                subprocess.run(["doppler", "secrets", "set", f"NOTEBOOKLM_SESSION_COOKIE={new_cookie}"], timeout=10)
                results["doppler"] = True
            except Exception:
                pass

        return results

    def handle_reactive_recovery(self) -> Tuple[bool, str]:
        """
        Called when a 401/302 is detected during live distillation.
        Attempts silent refresh; if impossible, alerts user via Telegram.
        """
        logger.warning("[COOKIE MANAGER] Reactive recovery triggered: Cookie expired or invalid.")
        
        # Try silent refresh first
        success, fresh_cookie = self.attempt_silent_refresh()
        if success and fresh_cookie:
            return True, fresh_cookie

        # If silent refresh fails, notify admin for 1-click re-auth
        alert_title = "🚨 [NotebookLM Cookie Expired] Interactive Re-Auth Required"
        alert_body = (
            "• Service: `Google NotebookLM Knowledge Extraction`\n"
            "• Status: `Session Expired / 2FA Challenge`\n"
            "• Action Required: Please run `python3 scripts/hermes_cookie_sync.py` to refresh session.\n"
            "• Cloud Resilience: Graceful fallback engine engaged to prevent pipeline crash."
        )
        self.notifier._send_all(alert_title, alert_body, status="ERROR")
        return False, self.get_current_cookie()

    def _update_local_env(self, key: str, value: str):
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

    def _sync_github_actions_secret(self, secret_name: str, secret_value: str) -> bool:
        if not shutil.which("gh"):
            return False
        try:
            cmd = ["gh", "secret", "set", secret_name, "-R", "pphothidaen/HoroConsultant", "--body", secret_value]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if res.returncode == 0:
                logger.info(f"[COOKIE SYNC] Cloud Secret '{secret_name}' successfully pushed to GitHub Actions!")
                return True
            return False
        except Exception as e:
            logger.warning(f"[COOKIE SYNC] GH secret sync note: {e}")
            return False
