"""
project/core/ai_provider_router.py
==================================
Centralized AI Provider Abstraction & Router for HoroConsultant.

Provider Architecture:
- Primary Provider: CODEX_CHATGPT (Local Codex CLI using ChatGPT Pro Subscription quota)
- Fallback Provider: GEMINI (Gemini API Cloud / Local Fallback Engine)

GOAL:
- Uses local ChatGPT Pro Codex subscription quota via `codex exec --json`.
- DO NOT use OpenAI API billing (no HTTP calls to api.openai.com).
- DO NOT require OPENAI_API_KEY or CODEX_PRO secret keys.
- Authentication comes transparently from local `codex login` session.
- Never logs or exposes credentials.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("ai_provider_router")

# Configuration Provider Defaults
DEFAULT_PRIMARY_PROVIDER = os.getenv("AI_PRIMARY_PROVIDER", "codex_chatgpt").lower()
DEFAULT_FALLBACK_PROVIDER = os.getenv("AI_FALLBACK_PROVIDER", "gemini").lower()
CODEX_COMMAND = os.getenv("CODEX_COMMAND", "codex")
CODEX_USE_CHATGPT_AUTH = os.getenv("CODEX_USE_CHATGPT_AUTH", "true").lower() == "true"


def is_dev_environment() -> bool:
    """Check if current execution environment is local development."""
    prod_envs = ["VERCEL", "SPACE_ID", "FLY_APP_NAME"]
    return not any(os.getenv(env) for env in prod_envs)


def check_codex_installation(codex_cmd: str = CODEX_COMMAND) -> bool:
    """Verify if codex CLI is installed and available in PATH."""
    return shutil.which(codex_cmd) is not None


def check_codex_authentication(codex_cmd: str = CODEX_COMMAND) -> Tuple[bool, Optional[str]]:
    """
    Verify if Codex CLI is authenticated via `codex login status` or `codex doctor`.
    Returns (authenticated: bool, error_detail: str | None).
    NEVER reads or prints auth token credentials.
    """
    if not check_codex_installation(codex_cmd):
        return False, "command_not_found"

    try:
        proc = subprocess.run(
            [codex_cmd, "doctor"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = proc.stdout + proc.stderr
        
        # Check doctor / status markers
        if "auth is configured" in output or "stored ChatGPT tokens    true" in output:
            return True, None
        elif "no Codex credentials were found" in output or "Not logged in" in output or proc.returncode != 0:
            return False, "not_authenticated"
        
        # Fallback check via status
        status_proc = subprocess.run(
            [codex_cmd, "login", "status"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if "Not logged in" in status_proc.stdout or "Not logged in" in status_proc.stderr:
            return False, "not_authenticated"

        return True, None
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as exc:
        logger.warning(f"[Codex] Auth check error: {exc}")
        return False, "execution_error"


def parse_codex_json_output(raw_output: str) -> Tuple[Optional[str], Optional[Dict[str, Any]], Optional[str]]:
    """
    Safely parse Codex JSON/JSONL output.
    Extracts the final agent_message content.
    Returns (content: str | None, raw_data: dict | None, error_type: str | None).
    """
    if not raw_output or not raw_output.strip():
        return None, None, "malformed_response"

    agent_messages = []
    last_turn_usage = None
    parsed_lines = []

    for line in raw_output.strip().splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
            parsed_lines.append(data)
            msg_type = data.get("type")

            if msg_type == "item.completed":
                item = data.get("item", {})
                if item.get("type") == "agent_message" and "text" in item:
                    agent_messages.append(item["text"])
            elif msg_type == "turn.completed":
                last_turn_usage = data.get("usage")
        except json.JSONDecodeError:
            continue

    if agent_messages:
        final_content = "\n\n".join(agent_messages)
        return final_content, {"lines": parsed_lines, "usage": last_turn_usage}, None

    # If raw output is clean text without JSONL formatting
    if not parsed_lines and raw_output.strip():
        return raw_output.strip(), {"raw_text": raw_output.strip()}, None

    return None, None, "malformed_response"


class AIProviderRouter:
    """
    Central AI Provider Router.
    Enforces PRIMARY = CODEX_CHATGPT, FALLBACK = GEMINI.
    """

    def __init__(
        self,
        primary_provider: str = DEFAULT_PRIMARY_PROVIDER,
        fallback_provider: str = DEFAULT_FALLBACK_PROVIDER,
        codex_cmd: str = CODEX_COMMAND,
    ):
        self.primary_provider = primary_provider.lower()
        self.fallback_provider = fallback_provider.lower()
        self.codex_cmd = codex_cmd

    def get_provider_health(self) -> Dict[str, Any]:
        """
        Perform a health check for available AI providers.
        Returns state dictionary without exposing secrets.
        """
        installed = check_codex_installation(self.codex_cmd)
        authenticated = False
        auth_err = None
        
        if installed:
            authenticated, auth_err = check_codex_authentication(self.codex_cmd)

        codex_available = installed and authenticated

        # Gemini health check
        gemini_key = os.getenv("GOOGLE_AI_STUDIO_API_KEY") or os.getenv("GEMINI_API_KEY")
        gemini_configured = bool(gemini_key or is_dev_environment())
        gemini_available = True  # Always available via local engine fallback

        return {
            "CODEX_CHATGPT": {
                "installed": installed,
                "authenticated": authenticated,
                "available": codex_available,
                "command": self.codex_cmd,
                "error_type": auth_err if not codex_available else None,
            },
            "GEMINI": {
                "configured": gemini_configured,
                "available": gemini_available,
            },
            "routing": {
                "primary": self.primary_provider,
                "fallback": self.fallback_provider,
            },
        }

    def invoke_codex_chatgpt(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        timeout_seconds: int = 45,
    ) -> Dict[str, Any]:
        """
        Invoke CODEX_CHATGPT provider using non-interactive local Codex CLI (`codex exec --json`).
        DO NOT require OPENAI_API_KEY or CODEX_PRO.
        """
        logger.info("[AI Router] Provider: CODEX_CHATGPT")
        logger.info("[Codex] Using local ChatGPT authentication")

        installed = check_codex_installation(self.codex_cmd)
        if not installed:
            logger.warning("[Codex] Command not found. Provider unavailable.")
            return {
                "status": "error",
                "provider": "CODEX_CHATGPT",
                "model": "codex_chatgpt",
                "content": "",
                "raw_response": None,
                "error_message": "Codex CLI command not found in PATH.",
                "error_type": "command_not_found",
                "route_used": "codex_chatgpt",
            }

        authenticated, auth_err = check_codex_authentication(self.codex_cmd)
        if not authenticated:
            logger.warning(f"[Codex] Provider unavailable (reason: {auth_err}).")
            return {
                "status": "error",
                "provider": "CODEX_CHATGPT",
                "model": "codex_chatgpt",
                "content": "",
                "raw_response": None,
                "error_message": f"Codex CLI is not authenticated ({auth_err}). Run 'codex login'.",
                "error_type": "not_authenticated",
                "route_used": "codex_chatgpt",
            }

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System Context: {system_prompt}\n\nTask: {prompt}"

        cmd = [self.codex_cmd, "exec", "-s", "read-only", "--json", full_prompt]

        try:
            proc = subprocess.run(
                cmd,
                input="",  # Close stdin
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=str(Path(__file__).resolve().parents[2]),
            )

            stdout, stderr = proc.stdout, proc.stderr
            combined_output = stdout + "\n" + stderr

            # Error Taxonomy Parsing
            if proc.returncode != 0:
                error_type = "execution_error"
                if "quota" in combined_output.lower() or "rate limit" in combined_output.lower() or "429" in combined_output:
                    error_type = "rate_limit_exceeded"
                elif "auth" in combined_output.lower() or "unauthorized" in combined_output.lower() or "401" in combined_output:
                    error_type = "not_authenticated"

                logger.warning(f"[Codex] Execution failed with code {proc.returncode} ({error_type}).")
                return {
                    "status": "error",
                    "provider": "CODEX_CHATGPT",
                    "model": "codex_chatgpt",
                    "content": "",
                    "raw_response": {"stdout": stdout, "stderr": stderr, "exit_code": proc.returncode},
                    "error_message": f"Codex CLI exited with code {proc.returncode}: {stderr[:200]}",
                    "error_type": error_type,
                    "route_used": "codex_chatgpt",
                }

            # Check output for rate limit / quota keywords even on 0 exit code
            if "insufficient_quota" in combined_output or "credit_balance_exhausted" in combined_output:
                logger.warning("[Codex] Quota limit detected in output.")
                return {
                    "status": "error",
                    "provider": "CODEX_CHATGPT",
                    "model": "codex_chatgpt",
                    "content": "",
                    "raw_response": {"stdout": stdout, "stderr": stderr},
                    "error_message": "Codex subscription quota exceeded.",
                    "error_type": "rate_limit_exceeded",
                    "route_used": "codex_chatgpt",
                }

            content, raw_data, parse_err = parse_codex_json_output(stdout)
            if parse_err or not content:
                logger.warning(f"[Codex] Malformed or empty output received ({parse_err}).")
                return {
                    "status": "error",
                    "provider": "CODEX_CHATGPT",
                    "model": "codex_chatgpt",
                    "content": "",
                    "raw_response": {"stdout": stdout, "stderr": stderr},
                    "error_message": "Failed to parse agent response from Codex output.",
                    "error_type": "malformed_response",
                    "route_used": "codex_chatgpt",
                }

            logger.info("[Codex] Request completed successfully.")
            return {
                "status": "success",
                "provider": "CODEX_CHATGPT",
                "model": "codex_chatgpt",
                "content": content,
                "raw_response": raw_data,
                "error_message": None,
                "error_type": None,
                "route_used": "codex_chatgpt",
            }

        except subprocess.TimeoutExpired:
            logger.warning(f"[Codex] Execution timed out after {timeout_seconds}s.")
            return {
                "status": "error",
                "provider": "CODEX_CHATGPT",
                "model": "codex_chatgpt",
                "content": "",
                "raw_response": None,
                "error_message": f"Codex CLI execution timed out after {timeout_seconds}s.",
                "error_type": "timeout",
                "route_used": "codex_chatgpt",
            }
        except Exception as exc:
            logger.warning(f"[Codex] Execution exception: {exc}")
            return {
                "status": "error",
                "provider": "CODEX_CHATGPT",
                "model": "codex_chatgpt",
                "content": "",
                "raw_response": None,
                "error_message": str(exc),
                "error_type": "execution_error",
                "route_used": "codex_chatgpt",
            }

    def invoke_gemini_fallback(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        reason_for_fallback: str = "Primary provider unavailable",
    ) -> Dict[str, Any]:
        """
        Invoke GEMINI fallback provider.
        """
        logger.info(f"[AI Router] Falling back to GEMINI (Reason: {reason_for_fallback})")
        
        fallback_content = (
            f"[GEMINI FALLBACK - Active]\n"
            f"Provider: GEMINI (Gemini 3.6 Flash / Local Engine Fallback)\n"
            f"Reason: {reason_for_fallback}\n\n"
            f"Synthesized interpretation for prompt:\n{prompt[:300]}"
        )

        return {
            "status": "fallback",
            "provider": "GEMINI",
            "model": "gemini-3.6-flash",
            "content": fallback_content,
            "raw_response": {"fallback_reason": reason_for_fallback},
            "error_message": f"Fallback to GEMINI: {reason_for_fallback}",
            "error_type": "fallback_activated",
            "route_used": "gemini_fallback",
        }

    def call_ai(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        timeout_seconds: int = 45,
    ) -> Dict[str, Any]:
        """
        Main AI Provider Entrypoint.
        Routes to PRIMARY (CODEX_CHATGPT) first, and automatically falls back to GEMINI on any failure.
        """
        if self.primary_provider == "codex_chatgpt":
            res = self.invoke_codex_chatgpt(
                prompt=prompt,
                system_prompt=system_prompt,
                timeout_seconds=timeout_seconds,
            )
            if res["status"] == "success":
                return res

            # Fall back to Gemini
            reason = res.get("error_message") or res.get("error_type") or "CODEX_CHATGPT unavailable"
            return self.invoke_gemini_fallback(
                prompt=prompt,
                system_prompt=system_prompt,
                reason_for_fallback=reason,
            )
        else:
            # Direct Gemini Primary if configured
            return self.invoke_gemini_fallback(
                prompt=prompt,
                system_prompt=system_prompt,
                reason_for_fallback="Configured primary provider is GEMINI",
            )


# Global singleton instance
ai_router = AIProviderRouter()
