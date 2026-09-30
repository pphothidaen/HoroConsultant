"""
project/core/llm_gateway.py
=============================
Multi-Provider Resilient LLM Gateway with Dynamic Failover & Circuit Breaker.

Tiers:
  Tier 1: Cloudflare Workers AI (@cf/meta/llama-3.1-8b-instruct)
  Tier 2: Google Gemini (gemini-2.5-flash / gemini-1.5-flash)
  Tier 3: AIPASS Bridge (notebook-grounded horo_consult via Gemini Web Bridge MCP)
  Tier 4: Codex CLI (read-only local wrapper)
  Tier 5: Anthropic Claude (claude-3-5-sonnet / claude-3-haiku)
  Tier 6: Local Ollama (qwen2.5:7b-instruct-q4_K_M)
  Tier 7: Deterministic Canonical Synthesizer (Safe Offline Fallback)
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx
from project.core.codex_cli_provider import call_codex_cli, check_codex_installation

logger = logging.getLogger("LLMGateway")

# KAN-208 / api-spec (gemini-web-bridge docs/api-spec.md) §2: the canonical
# scope id of the HoroConsultant NotebookLM notebook that horo_consult grounds
# every answer in. A response that does not carry this scope served the answer
# is not a grounded reading and must be rejected (invariant G-1).
HORO_NOTEBOOK_SCOPE = "notebook:b55f1ee0-384e-4bdf-ab1b-e2ee3b0063a0"

# api-spec §8: the grounding chain (45s attach + 60s type + 120s collect +
# 35s verify) can legitimately take ~260s worst case; the caller-side timeout
# must exceed it or a healthy slow answer is misread as a provider outage.
AIPASS_BRIDGE_TIMEOUT_S = 240.0


@dataclass
class ProviderState:
    key: str
    name: str
    tier: int
    is_configured: bool
    is_healthy: bool = True
    consecutive_failures: int = 0
    total_requests: int = 0
    total_failures: int = 0
    last_latency_ms: float = 0.0
    circuit_broken_until: float = 0.0
    last_error: str = ""


class LLMGateway:
    """Unified multi-model failover gateway."""

    def __init__(self):
        self.providers: Dict[str, ProviderState] = {
            "cloudflare": ProviderState(
                key="cloudflare",
                name="Cloudflare Workers AI",
                tier=1,
                is_configured=bool(os.getenv("CLOUDFLARE_ACCOUNT_ID") and os.getenv("CLOUDFLARE_API_TOKEN")),
            ),
            "gemini": ProviderState(
                key="gemini",
                name="Google Gemini",
                tier=2,
                is_configured=bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
            ),
            "aipass_bridge": ProviderState(
                key="aipass_bridge",
                name="AIPASS Bridge (Notebook-Grounded horo_consult)",
                tier=3,
                is_configured=bool(os.getenv("AIPASS_BRIDGE_BASE_URL"))
                and bool(os.getenv("AIPASS_BRIDGE_API_KEY"))
                and os.getenv("HORO_BRIDGE_CONSENT", "").lower() == "true",
            ),
            "codex": ProviderState(
                key="codex",
                name="Codex CLI",
                tier=4,
                is_configured=check_codex_installation(),
            ),
            "claude": ProviderState(
                key="claude",
                name="Anthropic Claude",
                tier=5,
                is_configured=bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")),
            ),
            "ollama": ProviderState(
                key="ollama",
                name="Local Ollama",
                tier=6,
                is_configured=bool(os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")),
            ),
            "deterministic": ProviderState(
                key="deterministic",
                name="Deterministic Synthesizer",
                tier=7,
                is_configured=True,
            ),
        }
        self.lock = asyncio.Lock()
        # api-spec §9.3: provenance captured by the last successful
        # aipass_bridge call, attached to the generate_text result.
        self._last_aipass_provenance: Optional[Dict[str, Any]] = None

    def _is_circuit_open(self, p: ProviderState) -> bool:
        if time.time() < p.circuit_broken_until:
            return True
        return False

    def _record_success(self, p: ProviderState, latency_ms: float):
        p.total_requests += 1
        p.consecutive_failures = 0
        p.last_latency_ms = latency_ms
        p.is_healthy = True
        p.last_error = ""

    def _record_failure(self, p: ProviderState, error_msg: str):
        p.total_requests += 1
        p.total_failures += 1
        p.consecutive_failures += 1
        p.last_error = error_msg[:200]
        if p.consecutive_failures >= 3:
            # Open circuit for 60 seconds
            p.circuit_broken_until = time.time() + 60.0
            p.is_healthy = False
            logger.warning(f"[CIRCUIT_BREAKER] Tripped circuit for {p.name} until {p.circuit_broken_until}")

    async def _call_cloudflare(self, prompt: str, system_instruction: str) -> str:
        account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        if not account_id or not api_token:
            raise ValueError("Cloudflare credentials missing")

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/meta/llama-3.1-8b-instruct"
        headers = {"Authorization": f"Bearer {api_token}"}
        payload = {
            "messages": [
                {"role": "system", "content": system_instruction or "You are an expert computational metaphysics consultant."},
                {"role": "user", "content": prompt}
            ]
        }
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("result", {}).get("response", "")

    async def _call_gemini(self, prompt: str, system_instruction: str) -> str:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Gemini API key missing")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{system_instruction}\n\n{prompt}" if system_instruction else prompt}]}
            ]
        }
        async with httpx.AsyncClient(timeout=7.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _call_claude(self, prompt: str, system_instruction: str) -> str:
        api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY", "dummy")
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 1024,
            "system": system_instruction or "You are an expert metaphysics consultant.",
            "messages": [{"role": "user", "content": prompt}]
        }
        async with httpx.AsyncClient(timeout=7.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]

    async def _call_codex(self, prompt: str, system_instruction: str) -> str:
        return await asyncio.to_thread(
            call_codex_cli, prompt, system_instruction=system_instruction
        )

    async def _call_ollama(self, prompt: str, system_instruction: str) -> str:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        url = f"{base_url.rstrip('/')}/api/generate"
        payload = {
            "model": "qwen2.5:7b-instruct-q4_K_M",
            "prompt": f"{system_instruction}\n\n{prompt}" if system_instruction else prompt,
            "stream": False
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")

    async def _call_aipass_bridge(
        self,
        prompt: str,
        system_instruction: str,
        birth_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Notebook-grounded consultation via the Gemini Web Bridge MCP server.

        api-spec (gemini-web-bridge docs/api-spec.md) §9: the worker's remote
        MCP endpoint exposes horo_consult, which answers only from the
        HoroConsultant NotebookLM notebook (fail-closed on grounding). This
        provider never streams and never carries a `scope` argument — an
        explicit scope disables the notebook attach (spec §2, invariant G-2).
        """
        base_url = os.getenv("AIPASS_BRIDGE_BASE_URL")
        api_key = os.getenv("AIPASS_BRIDGE_API_KEY")
        if not base_url or not api_key:
            raise ValueError("AIPASS Bridge credentials missing")

        # api-spec §9.2: horo_consult has no system-prompt channel — the
        # domain firewall rides inside the query text. No `scope` is sent:
        # the worker's default notebook attach is the only grounded path.
        query = f"{system_instruction}\n\n{prompt}".strip()
        args: Dict[str, Any] = {"query": query, "response_format": "text"}
        if birth_context:
            args["birth_context"] = birth_context

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "horo_consult", "arguments": args},
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=AIPASS_BRIDGE_TIMEOUT_S) as client:
            resp = await client.post(f"{base_url.rstrip('/')}/mcp", headers=headers, json=payload)
            resp.raise_for_status()
            body = resp.json()

        if body.get("error"):
            raise ValueError(f"aipass_bridge JSON-RPC error {body['error'].get('code')}: {body['error'].get('message', '')[:200]}")

        result = body.get("result") or {}
        text = (result.get("content") or [{}])[0].get("text", "")
        if not text or not text.strip():
            raise ValueError("aipass_bridge returned an empty answer")

        # api-spec invariant G-1 (hard guard): an accepted answer must be
        # notebook-grounded. This also catches the GCP-fallback leak (a
        # successful response with no notebookGrounding field at all).
        grounding = result.get("notebookGrounding") or {}
        scope = (result.get("bridgeScope") or {}).get("used")
        if not grounding.get("verified"):
            raise ValueError(
                f"Rejected ungrounded horo_consult answer (verified={grounding.get('verified')!r}, "
                f"scope={scope!r}) — api-spec invariant G-1"
            )
        if scope != HORO_NOTEBOOK_SCOPE:
            raise ValueError(f"Answer served from unexpected scope {scope!r}, expected {HORO_NOTEBOOK_SCOPE!r}")

        self._last_aipass_provenance = {
            "grounding": scope,
            "grounding_verified": True,
            "citations": grounding.get("citationCount"),
            "cited_sources": grounding.get("citedSources"),
            "model": "gemini-web-notebook",
        }
        return text

    def _call_deterministic(self, prompt: str, system_instruction: str) -> str:
        """Deterministic canonical fallback text."""
        return (
            "【บทสังเคราะห์คำพยากรณ์โหราศาสตร์และเบญจธาตุ (Deterministic Canonical Interpretation)】\n"
            "• โครงสร้างดวงชะตา: ดิถีได้รับพลังเกื้อหนุนตามวงจรเบญจธาตุ ธาตุส่งเสริมมีความสมดุล\n"
            "• ทิศทางมงคล: ทิศใต้ (離) และ ทิศตะวันออก (震) ส่งเสริมพลังอำนาจ เกียรติยศ และความเจริญรุ่งเรือง\n"
            "• คำแนะนำ: มุ่งเน้นการวางแผนรอบคอบ รักษาจริยธรรม และใช้จังหวะเวลาที่เกื้อกูลเพื่อความสำเร็จที่ยั่งยืน"
        )

    async def generate_text(
        self,
        prompt: str,
        system_instruction: str = "",
        preferred_provider: Optional[str] = None,
        birth_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute text generation with multi-tier failover and latency tracking."""
        order = ["cloudflare", "gemini", "aipass_bridge", "codex", "claude", "ollama", "deterministic"]
        if preferred_provider and preferred_provider in self.providers:
            order.remove(preferred_provider)
            order.insert(0, preferred_provider)

        call_map = {
            "cloudflare": self._call_cloudflare,
            "gemini": self._call_gemini,
            "aipass_bridge": self._call_aipass_bridge,
            "codex": self._call_codex,
            "claude": self._call_claude,
            "ollama": self._call_ollama,
        }

        for p_key in order:
            if p_key == "deterministic":
                t0 = time.perf_counter()
                text = self._call_deterministic(prompt, system_instruction)
                lat = (time.perf_counter() - t0) * 1000.0
                p = self.providers["deterministic"]
                self._record_success(p, lat)
                return {
                    "text": text,
                    "provider": "deterministic",
                    "model": "deterministic-canonical-v1",
                    "latency_ms": round(lat, 2),
                    "fallback_triggered": True
                }

            p = self.providers[p_key]
            if not p.is_configured or self._is_circuit_open(p):
                continue

            try:
                t0 = time.perf_counter()
                func = call_map[p_key]
                if p_key == "aipass_bridge":
                    text = await func(prompt, system_instruction, birth_context)
                else:
                    text = await func(prompt, system_instruction)
                lat = (time.perf_counter() - t0) * 1000.0
                if text and len(text.strip()) > 0:
                    self._record_success(p, lat)
                    result = {
                        "text": text.strip(),
                        "provider": p_key,
                        "model": p.name,
                        "latency_ms": round(lat, 2),
                        "fallback_triggered": p_key != order[0]
                    }
                    if p_key == "aipass_bridge" and self._last_aipass_provenance:
                        result["provenance"] = self._last_aipass_provenance
                        self._last_aipass_provenance = None
                    return result
                else:
                    self._record_failure(p, "Empty text response")
            except Exception as exc:
                logger.warning(f"[LLM_FAILOVER] Provider {p.name} failed: {exc}. Rolling over to next tier.")
                self._record_failure(p, str(exc))

        # Absolute guarantee
        return {
            "text": self._call_deterministic(prompt, system_instruction),
            "provider": "deterministic",
            "model": "deterministic-canonical-v1",
            "latency_ms": 0.1,
            "fallback_triggered": True
        }

    def get_providers_status(self) -> Dict[str, Any]:
        """Return real-time health and circuit metrics for all providers."""
        now = time.time()
        return {
            "timestamp": now,
            "providers": [
                {
                    "key": p.key,
                    "name": p.name,
                    "tier": p.tier,
                    "is_configured": p.is_configured,
                    "is_healthy": p.is_healthy,
                    "consecutive_failures": p.consecutive_failures,
                    "total_requests": p.total_requests,
                    "total_failures": p.total_failures,
                    "last_latency_ms": round(p.last_latency_ms, 2),
                    "circuit_open": now < p.circuit_broken_until,
                    "circuit_open_remaining_s": max(0, int(p.circuit_broken_until - now)),
                    "last_error": p.last_error
                }
                for p in self.providers.values()
            ]
        }

    async def test_provider(self, provider_key: str) -> Dict[str, Any]:
        """Test a specific provider directly."""
        if provider_key not in self.providers:
            return {"status": "error", "message": f"Unknown provider '{provider_key}'"}

        p = self.providers[provider_key]
        t0 = time.perf_counter()
        try:
            res = await self.generate_text("Say 'OK' in 1 word", preferred_provider=provider_key)
            lat = (time.perf_counter() - t0) * 1000.0
            return {
                "status": "success",
                "provider": provider_key,
                "latency_ms": round(lat, 2),
                "response_sample": res["text"][:100],
                "actual_provider_used": res["provider"]
            }
        except Exception as exc:
            return {
                "status": "error",
                "provider": provider_key,
                "error": str(exc)
            }


llm_gateway = LLMGateway()
