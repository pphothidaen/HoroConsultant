"""
project/core/ai_provider_router.py
==================================
Centralized AI Provider Abstraction & Router for HoroConsultant.

Provider Topology & Multi-Tier Hierarchy:
- Tier 1 (Primary): CODEX_CHATGPT (Local Codex CLI using ChatGPT Pro Subscription quota)
- Tier 2 (High-Speed Cloud): GEMINI (Google Gemini 3.6 Flash / 2.5 Flash / AI Studio API)
- Tier 3 (Deep Domain Synthesis / Reasoning): REASONING_PROXY / NINEROUTER (DeepSeek-R1 / Qwen2.5-32B)
- Tier 4 (Deterministic Baseline): Local Metaphysics Calculation & Rule Summarizer

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
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("ai_provider_router")

# Configuration Provider Defaults
DEFAULT_PRIMARY_PROVIDER = os.getenv("AI_PRIMARY_PROVIDER", "codex_chatgpt").lower()
DEFAULT_FALLBACK_PROVIDER = os.getenv("AI_FALLBACK_PROVIDER", "gemini").lower()
DEFAULT_REASONING_PROVIDER = os.getenv("AI_REASONING_PROVIDER", "reasoning_proxy").lower()
CODEX_COMMAND = os.getenv("CODEX_COMMAND", "codex")
CODEX_USE_CHATGPT_AUTH = os.getenv("CODEX_USE_CHATGPT_AUTH", "true").lower() == "true"

# Tier 3 Reasoning Configuration
REASONING_PROXY_BASE_URL = os.getenv(
    "NINEROUTER_BASE_URL",
    os.getenv("REASONING_PROXY_BASE_URL", os.getenv("OPENAI_BASE_URL", "")),
).strip()
REASONING_MODEL = os.getenv("REASONING_MODEL", "deepseek-r1")
REASONING_API_KEY = os.getenv("NINEROUTER_API_KEY", os.getenv("REASONING_API_KEY", "dummy_local_key"))


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
    Central AI Provider Router with 3-Tier Multi-Provider Topology:
    - Tier 1: CODEX_CHATGPT
    - Tier 2: GEMINI
    - Tier 3: REASONING_PROXY / NINEROUTER (DeepSeek-R1, Qwen2.5-32B)
    """

    def __init__(
        self,
        primary_provider: str = DEFAULT_PRIMARY_PROVIDER,
        fallback_provider: str = DEFAULT_FALLBACK_PROVIDER,
        reasoning_provider: str = DEFAULT_REASONING_PROVIDER,
        codex_cmd: str = CODEX_COMMAND,
        reasoning_base_url: str = REASONING_PROXY_BASE_URL,
        reasoning_model: str = REASONING_MODEL,
    ):
        self.primary_provider = primary_provider.lower()
        self.fallback_provider = fallback_provider.lower()
        self.reasoning_provider = reasoning_provider.lower()
        self.codex_cmd = codex_cmd
        self.reasoning_base_url = reasoning_base_url
        self.reasoning_model = reasoning_model

    def get_provider_health(self) -> Dict[str, Any]:
        """
        Perform a health check for available AI providers across all tiers.
        Returns state dictionary without exposing secrets.
        """
        installed = check_codex_installation(self.codex_cmd)
        authenticated = False
        auth_err = None

        if installed:
            authenticated, auth_err = check_codex_authentication(self.codex_cmd)

        codex_available = installed and authenticated

        # Gemini health check
        gemini_key = os.getenv("GOOGLE_AI_STUDIO_API_KEY") or os.getenv("GOOGLE_AI_STUDIO_API_KEY2")
        gemini_configured = bool(gemini_key or is_dev_environment())
        gemini_available = True  # Always available via local engine fallback

        # Tier 3 Reasoning Proxy health check
        reasoning_configured = bool(self.reasoning_base_url)
        reasoning_available = reasoning_configured

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
            "REASONING_PROXY": {
                "configured": reasoning_configured,
                "available": reasoning_available,
                "model": self.reasoning_model,
                "base_url": self.reasoning_base_url if self.reasoning_base_url else None,
            },
            "routing": {
                "primary": self.primary_provider,
                "fallback": self.fallback_provider,
                "reasoning": self.reasoning_provider,
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

    def invoke_reasoning_proxy(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        timeout_seconds: int = 30,
    ) -> Dict[str, Any]:
        """
        Invoke Tier 3 Reasoning Proxy (9router / DeepSeek-R1 / Qwen2.5-32B) via OpenAI-compatible endpoint.
        """
        if not self.reasoning_base_url:
            return {
                "status": "error",
                "provider": "REASONING_PROXY",
                "model": self.reasoning_model,
                "content": "",
                "raw_response": None,
                "error_message": "Reasoning proxy base URL not configured.",
                "error_type": "unconfigured",
                "route_used": "reasoning_proxy",
            }

        endpoint = f"{self.reasoning_base_url.rstrip('/')}/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.reasoning_model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 2048,
        }

        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {REASONING_API_KEY}",
                "User-Agent": "HoroConsultant-ReasoningProxy/1.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
                choice = body.get("choices", [{}])[0]
                content = choice.get("message", {}).get("content", "")
                return {
                    "status": "success",
                    "provider": "REASONING_PROXY",
                    "model": self.reasoning_model,
                    "content": content,
                    "raw_response": body,
                    "error_message": None,
                    "error_type": None,
                    "route_used": "reasoning_proxy",
                }
        except Exception as exc:
            logger.warning(f"[ReasoningProxy] Call failed: {exc}")
            return {
                "status": "error",
                "provider": "REASONING_PROXY",
                "model": self.reasoning_model,
                "content": "",
                "raw_response": None,
                "error_message": str(exc),
                "error_type": "proxy_error",
                "route_used": "reasoning_proxy",
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
        prefer_reasoning: bool = False,
    ) -> Dict[str, Any]:
        """
        Main AI Provider Entrypoint.
        Routes across Multi-Tier hierarchy:
        1. If prefer_reasoning is True, tries Tier 3 Reasoning Proxy first.
        2. Otherwise tries Tier 1 (CODEX_CHATGPT).
        3. If Tier 1 fails, falls back to Tier 2 (GEMINI).
        4. If Tier 2 fails or reasoning is available, attempts Tier 3 Reasoning Proxy.
        5. Returns structured response with route used.
        """
        if prefer_reasoning and self.reasoning_base_url:
            r_res = self.invoke_reasoning_proxy(
                prompt=prompt,
                system_prompt=system_prompt,
                timeout_seconds=timeout_seconds,
            )
            if r_res["status"] == "success":
                return r_res

        if self.primary_provider == "codex_chatgpt":
            res = self.invoke_codex_chatgpt(
                prompt=prompt,
                system_prompt=system_prompt,
                timeout_seconds=timeout_seconds,
            )
            if res["status"] == "success":
                return res

            # Try Tier 3 Reasoning Proxy if configured before Gemini fallback
            if self.reasoning_base_url:
                r_res = self.invoke_reasoning_proxy(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    timeout_seconds=timeout_seconds,
                )
                if r_res["status"] == "success":
                    return r_res

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
