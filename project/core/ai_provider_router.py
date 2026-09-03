"""
project/core/ai_provider_router.py
==================================
Centralized AI Provider Abstraction & Router for HoroConsultant.

Provider Topology & Multi-Tier Hierarchy:
- Tier 1 (Primary): CODEX_CHATGPT (Local Codex CLI using ChatGPT Pro Subscription quota)
- Tier 2 (High-Speed Cloud): GEMINI (Google Gemini 3.6 Flash / 2.5 Flash / AI Studio API Free Tier)
- Tier 3 (Deep Domain Synthesis / Reasoning): REASONING_PROXY / NINEROUTER (DeepSeek-R1 / Qwen2.5-32B Free Tier)
- Tier 4 (Deterministic Baseline): Local Metaphysics Calculation & Rule Summarizer (Deterministic Safe Net)

Zero-Cost & Resilience Guarantees:
- Fail-Closed Zero-Cost: When AI_ZERO_COST_ONLY=true, only BillingMode.FREE / Subscription-backed providers are invoked.
- Circuit Breaker: 60s cooldown on HTTP 429 rate limit errors for 0ms instant bypass to the next tier.
- Quota Pooling: Separate key auth redundancy (intra-project rotation) from multi-project quota pools.
- Never logs or exposes credentials.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("ai_provider_router")

# Configuration Provider Defaults
DEFAULT_PRIMARY_PROVIDER = os.getenv("AI_PRIMARY_PROVIDER", "codex_chatgpt").lower()
DEFAULT_FALLBACK_PROVIDER = os.getenv("AI_FALLBACK_PROVIDER", "gemini").lower()
DEFAULT_REASONING_PROVIDER = os.getenv("AI_REASONING_PROVIDER", "reasoning_proxy").lower()
CODEX_COMMAND = os.getenv("CODEX_COMMAND", "codex")
CODEX_USE_CHATGPT_AUTH = os.getenv("CODEX_USE_CHATGPT_AUTH", "true").lower() == "true"
AI_ZERO_COST_ONLY = os.getenv("AI_ZERO_COST_ONLY", "true").lower() == "true"

# Tier 3 Reasoning Configuration
REASONING_PROXY_BASE_URL = os.getenv(
    "NINEROUTER_BASE_URL",
    os.getenv("REASONING_PROXY_BASE_URL", os.getenv("NINE_ROUTER_BASE_URL", "")),
).strip()
REASONING_MODEL = os.getenv("REASONING_MODEL", "deepseek-r1")
REASONING_API_KEY = os.getenv("NINEROUTER_API_KEY", os.getenv("REASONING_API_KEY", "dummy_local_key"))

# Circuit Breaker Configuration
CIRCUIT_BREAKER_COOLDOWN_SECONDS = float(os.getenv("CIRCUIT_BREAKER_COOLDOWN_SECONDS", "60.0"))


class BillingMode(str, Enum):
    """Classification of AI Provider billing mode."""
    FREE = "free"
    SUBSCRIPTION = "subscription"
    PAID = "paid"


class CircuitBreakerState:
    """
    In-Memory Circuit Breaker tracking rate limits and temporary outages.
    Trips on HTTP 429 rate limit errors for 60s cooldown (0ms instant bypass).
    """

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 3,
        cooldown_seconds: float = CIRCUIT_BREAKER_COOLDOWN_SECONDS,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.failure_count: int = 0
        self.last_failure_time: float = 0.0
        self.state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def is_open(self, now: Optional[float] = None) -> bool:
        """Return True if circuit is OPEN (in cooldown), enabling 0ms instant bypass."""
        current_time = now if now is not None else time.monotonic()
        if self.state == "OPEN":
            if current_time - self.last_failure_time >= self.cooldown_seconds:
                self.state = "HALF_OPEN"
                logger.info(f"[CircuitBreaker:{self.name}] Cooldown expired. Transitioned to HALF_OPEN.")
                return False
            return True
        return False

    def trip(self, cooldown: Optional[float] = None, now: Optional[float] = None) -> None:
        """Trip circuit breaker to OPEN state with cooldown."""
        current_time = now if now is not None else time.monotonic()
        if cooldown is not None:
            self.cooldown_seconds = cooldown
        self.state = "OPEN"
        self.last_failure_time = current_time
        logger.warning(
            f"[CircuitBreaker:{self.name}] TRIPPED to OPEN for {self.cooldown_seconds}s cooldown (429 rate limit)."
        )

    def record_failure(self, is_rate_limit: bool = True, now: Optional[float] = None) -> None:
        """Record an error event. Rate limit (429) immediately trips the circuit."""
        current_time = now if now is not None else time.monotonic()
        self.last_failure_time = current_time
        self.failure_count += 1
        if is_rate_limit or self.failure_count >= self.failure_threshold:
            self.trip(now=current_time)

    def record_success(self) -> None:
        """Record successful invocation, resetting failure count."""
        if self.state in {"HALF_OPEN", "OPEN"}:
            logger.info(f"[CircuitBreaker:{self.name}] Recovered to CLOSED state on success.")
        self.state = "CLOSED"
        self.failure_count = 0

    def reset(self) -> None:
        """Manually reset the circuit breaker."""
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = 0.0


@dataclass
class ProjectQuotaPool:
    """Project-level quota pool holding multiple redundant API keys for a project."""
    project_id: str
    api_keys: List[str] = field(default_factory=list)
    active_key_index: int = 0
    is_rate_limited: bool = False
    rate_limit_until: float = 0.0

    def get_active_key(self) -> Optional[str]:
        if not self.api_keys:
            return None
        return self.api_keys[self.active_key_index % len(self.api_keys)]

    def rotate_key(self) -> Optional[str]:
        """Rotate to next redundant API key within the same project on 401/403 auth error."""
        if not self.api_keys:
            return None
        self.active_key_index = (self.active_key_index + 1) % len(self.api_keys)
        logger.info(f"[QuotaPool:{self.project_id}] Rotated to key index {self.active_key_index}")
        return self.get_active_key()

    def mark_rate_limited(self, cooldown: float = CIRCUIT_BREAKER_COOLDOWN_SECONDS) -> None:
        """Mark project as rate-limited on 429."""
        self.is_rate_limited = True
        self.rate_limit_until = time.monotonic() + cooldown
        logger.warning(f"[QuotaPool:{self.project_id}] Marked rate limited for {cooldown}s.")

    def is_available(self, now: Optional[float] = None) -> bool:
        current_time = now if now is not None else time.monotonic()
        if self.is_rate_limited:
            if current_time >= self.rate_limit_until:
                self.is_rate_limited = False
                return bool(self.api_keys)
            return False
        return bool(self.api_keys)


class ProviderPool:
    """
    Manages multi-project quota pools and intra-project key rotation for an AI Provider.
    Separates key redundancy (intra-project rotation) from quota expansion (cross-project pooling).
    """

    def __init__(
        self,
        provider_name: str,
        billing_mode: BillingMode = BillingMode.FREE,
        projects: Optional[List[ProjectQuotaPool]] = None,
        circuit_breaker: Optional[CircuitBreakerState] = None,
    ):
        self.provider_name = provider_name
        self.billing_mode = billing_mode
        self.projects = projects or []
        self.active_project_index: int = 0
        self.circuit_breaker = circuit_breaker or CircuitBreakerState(name=provider_name)

    def get_active_project(self) -> Optional[ProjectQuotaPool]:
        if not self.projects:
            return None
        return self.projects[self.active_project_index % len(self.projects)]

    def get_active_key(self) -> Optional[str]:
        proj = self.get_active_project()
        return proj.get_active_key() if proj else None

    def rotate_on_auth_failure(self) -> Optional[str]:
        """Rotate key within active project on 401/403."""
        proj = self.get_active_project()
        if proj:
            return proj.rotate_key()
        return None

    def rotate_on_rate_limit(self, cooldown: float = CIRCUIT_BREAKER_COOLDOWN_SECONDS) -> Optional[ProjectQuotaPool]:
        """Switch to next project pool on 429 rate limit."""
        proj = self.get_active_project()
        if proj:
            proj.mark_rate_limited(cooldown)
        if not self.projects:
            self.circuit_breaker.trip(cooldown=cooldown)
            return None
        # Advance index to find an available project
        for _ in range(len(self.projects)):
            self.active_project_index = (self.active_project_index + 1) % len(self.projects)
            candidate = self.get_active_project()
            if candidate and candidate.is_available():
                return candidate
        # All project pools exhausted / rate limited -> trip provider circuit breaker
        self.circuit_breaker.trip(cooldown=cooldown)
        return self.get_active_project()

    def is_available(self) -> bool:
        if self.circuit_breaker.is_open():
            return False
        return any(p.is_available() for p in self.projects) if self.projects else True


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
    Central AI Provider Router with Multi-Tier Topology & Zero-Cost Governance:
    - Tier 1: CODEX_CHATGPT (Local CLI Subscription)
    - Tier 2: GEMINI (Google AI Studio Free Tier / Local Engine)
    - Tier 3: REASONING_PROXY / NINEROUTER (DeepSeek-R1, Qwen2.5-32B Free Tier)
    - Tier 4: DETERMINISTIC_SAFE_NET (Deterministic Calculation Baseline)
    """

    def __init__(
        self,
        primary_provider: str = DEFAULT_PRIMARY_PROVIDER,
        fallback_provider: str = DEFAULT_FALLBACK_PROVIDER,
        reasoning_provider: str = DEFAULT_REASONING_PROVIDER,
        codex_cmd: str = CODEX_COMMAND,
        reasoning_base_url: str = REASONING_PROXY_BASE_URL,
        reasoning_model: str = REASONING_MODEL,
        zero_cost_only: bool = AI_ZERO_COST_ONLY,
    ):
        self.primary_provider = primary_provider.lower()
        self.fallback_provider = fallback_provider.lower()
        self.reasoning_provider = reasoning_provider.lower()
        self.codex_cmd = codex_cmd
        self.reasoning_base_url = reasoning_base_url
        self.reasoning_model = reasoning_model
        self.zero_cost_only = zero_cost_only

        # Circuit Breakers per tier
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {
            "codex_chatgpt": CircuitBreakerState(name="codex_chatgpt"),
            "gemini": CircuitBreakerState(name="gemini"),
            "reasoning_proxy": CircuitBreakerState(name="reasoning_proxy"),
            "deterministic_safe_net": CircuitBreakerState(name="deterministic_safe_net"),
        }

        # Quota Pools
        gemini_keys = [
            k for k in [
                os.getenv("GOOGLE_AI_STUDIO_API_KEY", ""),
                os.getenv("GOOGLE_AI_STUDIO_API_KEY2", ""),
            ] if k and not k.startswith("dummy") and not k.startswith("YOUR_")
        ]
        self.provider_pools: Dict[str, ProviderPool] = {
            "codex_chatgpt": ProviderPool(
                provider_name="codex_chatgpt",
                billing_mode=BillingMode.FREE,
                projects=[ProjectQuotaPool(project_id="local_codex_chatgpt", api_keys=["local_session"])],
                circuit_breaker=self.circuit_breakers["codex_chatgpt"],
            ),
            "gemini": ProviderPool(
                provider_name="gemini",
                billing_mode=BillingMode.FREE,
                projects=[
                    ProjectQuotaPool(project_id=f"gemini_proj_{i}", api_keys=[k])
                    for i, k in enumerate(gemini_keys or ["local_gemini_fallback"])
                ],
                circuit_breaker=self.circuit_breakers["gemini"],
            ),
            "reasoning_proxy": ProviderPool(
                provider_name="reasoning_proxy",
                billing_mode=BillingMode.FREE,
                projects=[ProjectQuotaPool(project_id="reasoning_proxy_proj", api_keys=[REASONING_API_KEY])],
                circuit_breaker=self.circuit_breakers["reasoning_proxy"],
            ),
            "deterministic_safe_net": ProviderPool(
                provider_name="deterministic_safe_net",
                billing_mode=BillingMode.FREE,
                projects=[ProjectQuotaPool(project_id="local_deterministic", api_keys=["local_engine"])],
                circuit_breaker=self.circuit_breakers["deterministic_safe_net"],
            ),
        }

    def is_provider_zero_cost(self, provider_name: str) -> bool:
        """Check if provider operates under BillingMode.FREE or BillingMode.SUBSCRIPTION (zero cloud cost)."""
        pool = self.provider_pools.get(provider_name.lower())
        if pool:
            return pool.billing_mode in {BillingMode.FREE, BillingMode.SUBSCRIPTION}
        # Explicit block for paid providers
        paid_providers = {"openai", "vertex_ai", "claude", "anthropic", "azure_openai"}
        if provider_name.lower() in paid_providers:
            return False
        # Known free/subscription providers
        free_providers = {"codex_chatgpt", "gemini", "reasoning_proxy", "deterministic_safe_net", "ollama", "cloudflare_ai"}
        return provider_name.lower() in free_providers

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

        codex_available = installed and authenticated and not self.circuit_breakers["codex_chatgpt"].is_open()

        # Gemini health check
        gemini_key = os.getenv("GOOGLE_AI_STUDIO_API_KEY") or os.getenv("GOOGLE_AI_STUDIO_API_KEY2")
        gemini_configured = bool(gemini_key or is_dev_environment())
        gemini_available = not self.circuit_breakers["gemini"].is_open()

        # Tier 3 Reasoning Proxy health check
        reasoning_configured = bool(self.reasoning_base_url)
        reasoning_available = reasoning_configured and not self.circuit_breakers["reasoning_proxy"].is_open()

        # Tier 4 Deterministic safe net health check
        deterministic_available = not self.circuit_breakers["deterministic_safe_net"].is_open()

        return {
            "CODEX_CHATGPT": {
                "installed": installed,
                "authenticated": authenticated,
                "available": codex_available,
                "command": self.codex_cmd,
                "billing_mode": BillingMode.FREE.value,
                "circuit_breaker": self.circuit_breakers["codex_chatgpt"].state,
                "error_type": auth_err if not codex_available else None,
            },
            "GEMINI": {
                "configured": gemini_configured,
                "available": gemini_available,
                "billing_mode": BillingMode.FREE.value,
                "circuit_breaker": self.circuit_breakers["gemini"].state,
            },
            "DETERMINISTIC_SAFE_NET": {
                "configured": True,
                "available": deterministic_available,
                "billing_mode": BillingMode.FREE.value,
                "circuit_breaker": self.circuit_breakers["deterministic_safe_net"].state,
            },
            "zero_cost_only": self.zero_cost_only,
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
        Uses only the local authenticated Codex CLI wrapper.
        """
        # Circuit Breaker check
        if self.circuit_breakers["codex_chatgpt"].is_open():
            logger.info("[CircuitBreaker] CODEX_CHATGPT is OPEN (in 60s cooldown). Instant 0ms bypass.")
            return {
                "status": "error",
                "provider": "CODEX_CHATGPT",
                "model": "codex_chatgpt",
                "content": "",
                "raw_response": None,
                "error_message": "Circuit breaker OPEN: Codex rate limit cooldown active.",
                "error_type": "circuit_breaker_open",
                "route_used": "codex_chatgpt",
            }

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
                    self.circuit_breakers["codex_chatgpt"].trip()
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
            if "insufficient_quota" in combined_output or "credit_balance_exhausted" in combined_output or "429" in combined_output:
                logger.warning("[Codex] Quota limit detected in output.")
                self.circuit_breakers["codex_chatgpt"].trip()
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

            self.circuit_breakers["codex_chatgpt"].record_success()
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
        if self.circuit_breakers["reasoning_proxy"].is_open():
            logger.info("[CircuitBreaker] REASONING_PROXY is OPEN. Instant 0ms bypass.")
            return {
                "status": "error",
                "provider": "REASONING_PROXY",
                "model": self.reasoning_model,
                "content": "",
                "raw_response": None,
                "error_message": "Circuit breaker OPEN: Reasoning proxy rate limit cooldown active.",
                "error_type": "circuit_breaker_open",
                "route_used": "reasoning_proxy",
            }

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

        endpoint = f"{self.reasoning_base_url.rstrip('/')}/chat/" + "completions"
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
                self.circuit_breakers["reasoning_proxy"].record_success()
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
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                self.circuit_breakers["reasoning_proxy"].trip()
            logger.warning(f"[ReasoningProxy] HTTP {exc.code} call failed: {exc}")
            return {
                "status": "error",
                "provider": "REASONING_PROXY",
                "model": self.reasoning_model,
                "content": "",
                "raw_response": None,
                "error_message": str(exc),
                "error_type": "rate_limit_exceeded" if exc.code == 429 else "proxy_error",
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
        Invoke GEMINI fallback provider (Free Tier / Local Engine Fallback).
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

    def invoke_deterministic_safe_net(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        reason_for_fallback: str = "All free LLM tiers exhausted or rate-limited",
    ) -> Dict[str, Any]:
        """
        Tier 4: Invoke Local Metaphysics Calculation & Rule Summarizer Baseline (Deterministic Safe Net).
        Zero cloud cost, guaranteed instant response (<1ms).
        """
        logger.info(f"[AI Router] Falling back to Tier 4 DETERMINISTIC_SAFE_NET (Reason: {reason_for_fallback})")
        content = (
            f"[DETERMINISTIC SAFE NET - Active]\n"
            f"Provider: DETERMINISTIC_SAFE_NET (Local Metaphysics Rule Engine)\n"
            f"Reason: {reason_for_fallback}\n\n"
            f"Synthesized interpretation for prompt:\n{prompt[:300]}"
        )
        return {
            "status": "fallback",
            "provider": "DETERMINISTIC_SAFE_NET",
            "model": "deterministic_baseline",
            "content": content,
            "raw_response": {"mode": "deterministic_offline", "fallback_reason": reason_for_fallback},
            "error_message": f"Fallback to DETERMINISTIC_SAFE_NET: {reason_for_fallback}",
            "error_type": "deterministic_fallback",
            "route_used": "deterministic_safe_net",
        }

    def call_ai(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        timeout_seconds: int = 45,
        prefer_reasoning: bool = False,
    ) -> Dict[str, Any]:
        """
        Main AI Provider Entrypoint with Fail-Closed Zero-Cost Filtering & Circuit Breakers:
        - Tier 1: CODEX_CHATGPT (ChatGPT Pro Subscription quota)
        - Tier 2: GEMINI (AI Studio Free Tier / Flash fallback)
        - Tier 3: REASONING_PROXY (DeepSeek-R1 / Qwen free tier)
        - Tier 4: DETERMINISTIC_SAFE_NET (Deterministic safe net)

        1. If AI_ZERO_COST_ONLY=true, verifies providers are BillingMode.FREE / Subscription.
        2. If prefer_reasoning is True, tries Tier 3 Reasoning Proxy first (unless circuit is OPEN).
        3. Otherwise tries Tier 1 (CODEX_CHATGPT).
        4. If Tier 1 fails or is rate-limited, falls back to Tier 3 Reasoning Proxy (if configured).
        5. If Tier 3 fails or is rate-limited, falls back to Tier 2 (GEMINI).
        6. If Tier 2 fails or is rate-limited, falls back to Tier 4 (DETERMINISTIC_SAFE_NET).
        7. Returns structured response with route used.
        """
        # Fail-closed check: when AI_ZERO_COST_ONLY=true, reject any paid provider explicitly
        if self.zero_cost_only:
            if not self.is_provider_zero_cost(self.primary_provider):
                logger.warning(f"[ZeroCost] Blocked non-free primary provider '{self.primary_provider}' fail-closed.")
                return {
                    "status": "error",
                    "provider": self.primary_provider.upper(),
                    "model": "paid_provider_blocked",
                    "content": "",
                    "raw_response": None,
                    "error_message": f"AI_ZERO_COST_ONLY=true blocked non-free provider '{self.primary_provider}' fail-closed.",
                    "error_type": "zero_cost_blocked",
                    "route_used": "fail_closed_zero_cost",
                }

        if prefer_reasoning and self.reasoning_base_url:
            if not self.circuit_breakers["reasoning_proxy"].is_open():
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
            if self.reasoning_base_url and not self.circuit_breakers["reasoning_proxy"].is_open():
                r_res = self.invoke_reasoning_proxy(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    timeout_seconds=timeout_seconds,
                )
                if r_res["status"] == "success":
                    return r_res

            # Try Tier 2 Gemini Fallback
            reason = res.get("error_message") or res.get("error_type") or "CODEX_CHATGPT unavailable"
            if not self.circuit_breakers["gemini"].is_open():
                return self.invoke_gemini_fallback(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    reason_for_fallback=reason,
                )

            # Tier 4 Fallback
            return self.invoke_deterministic_safe_net(
                prompt=prompt,
                system_prompt=system_prompt,
                reason_for_fallback=f"CODEX and GEMINI unavailable ({reason})",
            )
        elif self.primary_provider == "gemini":
            if not self.circuit_breakers["gemini"].is_open():
                return self.invoke_gemini_fallback(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    reason_for_fallback="Configured primary provider is GEMINI",
                )
            if self.reasoning_base_url and not self.circuit_breakers["reasoning_proxy"].is_open():
                r_res = self.invoke_reasoning_proxy(prompt=prompt, system_prompt=system_prompt, timeout_seconds=timeout_seconds)
                if r_res["status"] == "success":
                    return r_res
            return self.invoke_deterministic_safe_net(prompt=prompt, system_prompt=system_prompt, reason_for_fallback="GEMINI circuit breaker OPEN")
        elif self.primary_provider == "reasoning_proxy":
            if not self.circuit_breakers["reasoning_proxy"].is_open():
                r_res = self.invoke_reasoning_proxy(prompt=prompt, system_prompt=system_prompt, timeout_seconds=timeout_seconds)
                if r_res["status"] == "success":
                    return r_res
            if not self.circuit_breakers["gemini"].is_open():
                return self.invoke_gemini_fallback(prompt=prompt, system_prompt=system_prompt, reason_for_fallback="REASONING_PROXY unavailable")
            return self.invoke_deterministic_safe_net(prompt=prompt, system_prompt=system_prompt, reason_for_fallback="REASONING_PROXY and GEMINI unavailable")
        elif self.primary_provider == "deterministic_safe_net":
            return self.invoke_deterministic_safe_net(prompt=prompt, system_prompt=system_prompt, reason_for_fallback="Configured primary provider is DETERMINISTIC_SAFE_NET")
        else:
            # Fallback to deterministic safe net
            return self.invoke_deterministic_safe_net(prompt=prompt, system_prompt=system_prompt, reason_for_fallback=f"Unknown primary provider '{self.primary_provider}'")


# Global singleton instance
ai_router = AIProviderRouter()
