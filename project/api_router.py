"""
api_router.py - Hybrid API Routing & Fallback System
=====================================================
LOCAL-FIRST architecture: Ollama models are PRIMARY routes.
Cloud platforms are used only when local routes are unavailable.

Route order:
  1. Ollama PRIMARY_LOCAL_MODEL  (qwen2.5:7b - best for BaZi/Thai/Chinese)
  2. Ollama SECONDARY_LOCAL_MODEL (qwen2.5-coder:7b)
  3. Ollama TERTIARY_LOCAL_MODEL  (llama3:8b)
  4. Cloudflare AI, Gemini KEY1/KEY2 (cloud fallback, all configured routes)
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx
from dotenv import load_dotenv
from project.core.codex_cli_provider import call_codex_cli, check_codex_installation

load_dotenv(override=True)

logger = logging.getLogger("api_router")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OLLAMA_BASE_URL         = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
PRIMARY_LOCAL_MODEL     = os.getenv("OLLAMA_PRIMARY_MODEL",   "qwen2.5-bazi")
SECONDARY_LOCAL_MODEL   = os.getenv("OLLAMA_SECONDARY_MODEL", "qwen2.5:7b")
TERTIARY_LOCAL_MODEL    = os.getenv("OLLAMA_TERTIARY_MODEL",  "qwen2.5-coder:7b")
GOOGLE_AI_STUDIO_API_KEY = os.getenv("GOOGLE_AI_STUDIO_API_KEY", "")
GOOGLE_AI_STUDIO_API_KEY2 = os.getenv("GOOGLE_AI_STUDIO_API_KEY2", "")


GEMINI_BASE_URL         = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_GEMINI_ROTATION = [
    "gemini-flash-latest",
    "gemma-4-26b-a4b-it",
    "gemma-4-31b-it",
    "gemini-2.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
]

GEMINI_PRIMARY_MODEL    = os.getenv("PRIMARY_MODEL",   "gemini-flash-latest")
GEMINI_SECONDARY_MODEL  = os.getenv("SECONDARY_MODEL", "gemma-4-26b-a4b-it")
GEMINI_TERTIARY_MODEL   = os.getenv("TERTIARY_MODEL",  "gemma-4-31b-it")

GEMINI_MODELS_ROTATION: list[str] = []
for m in [GEMINI_PRIMARY_MODEL, GEMINI_SECONDARY_MODEL, GEMINI_TERTIARY_MODEL, *DEFAULT_GEMINI_ROTATION]:
    if m and m not in GEMINI_MODELS_ROTATION:
        GEMINI_MODELS_ROTATION.append(m)

GEMINI_MODEL_FALLBACK_CANDIDATES: dict[str, list[str]] = {
    "gemma-4-31b-it": ["gemma-4-26b-a4b-it", "gemini-2.5-flash", "gemini-flash-latest"],
    "gemma-4-26b-a4b-it": ["gemma-4-31b-it", "gemini-2.5-flash", "gemini-flash-latest"],
    "gemini-2.5-flash": ["gemma-4-31b-it", "gemma-4-26b-a4b-it", "gemini-flash-latest"],
    "gemini-3.5-flash-lite": ["gemma-4-31b-it", "gemma-4-26b-a4b-it", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"],
    "gemini-flash-latest": ["gemma-4-31b-it", "gemma-4-26b-a4b-it", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash-latest"],
    "gemini-3.6-flash": ["gemma-4-31b-it", "gemma-4-26b-a4b-it", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-2.0-flash-lite"],
    "gemini-3.7-flash": ["gemma-4-31b-it", "gemma-4-26b-a4b-it", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"],
}

CLOUDFLARE_ACCOUNT_ID   = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
CLOUDFLARE_AI_TOKEN     = os.getenv("CLOUDFLARE_AI_TOKEN", "")
CLOUDFLARE_AI_MODEL     = os.getenv("CLOUDFLARE_AI_MODEL", "@cf/meta/llama-3.1-8b-instruct")

TIMEOUT_LOCAL_S         = float(os.getenv("LOCAL_TIMEOUT_SECONDS", "3.0"))
TIMEOUT_CLOUD_S         = float(os.getenv("API_TIMEOUT_SECONDS",   "12.0"))
RETRY_DELAY_S           = 2.0

# ---------------------------------------------------------------------------
# Rate Limit (429) Circuit Breaker
# ---------------------------------------------------------------------------
_ROUTE_CIRCUIT_BREAKER: dict[str, float] = {}
CIRCUIT_BREAKER_COOLDOWN_SECONDS: float = 60.0


def _is_route_circuit_open(route_key: str) -> bool:
    """Return True if route recently failed with 429 rate limit and is in cooldown."""
    cooldown_until = _ROUTE_CIRCUIT_BREAKER.get(route_key, 0.0)
    return time.monotonic() < cooldown_until


def _trip_route_circuit(route_key: str, cooldown: float = CIRCUIT_BREAKER_COOLDOWN_SECONDS) -> None:
    """Trip circuit breaker for a rate-limited route to avoid latency bottlenecks."""
    _ROUTE_CIRCUIT_BREAKER[route_key] = time.monotonic() + cooldown
    logger.info(f"[CircuitBreaker] Tripped route '{route_key}' for {cooldown}s cooldown.")


def _gemini_keys() -> list[str]:
    """Return all unique, valid, non-placeholder Google AI Studio API keys from env."""
    raw = [
        os.getenv("GOOGLE_AI_STUDIO_API_KEY", GOOGLE_AI_STUDIO_API_KEY),
        os.getenv("GOOGLE_AI_STUDIO_API_KEY2", GOOGLE_AI_STUDIO_API_KEY2),
    ]
    seen = set()
    valid = []
    invalid_prefixes = ("REPLACE", "your_", "YOUR_", "dummy", "DUMMY", "YOUR_GEMINI")
    for k in raw:
        k = k.strip()
        if k and not any(k.startswith(p) for p in invalid_prefixes) and k not in seen:
            seen.add(k)
            valid.append(k)
    return valid





# ---------------------------------------------------------------------------
# Ollama caller
# ---------------------------------------------------------------------------

def _call_ollama(
    model:              str,
    prompt:             str,
    system_instruction: str = "",
) -> tuple[str | None, str]:
    """
    Call a local Ollama model.
    Returns (text, reason): reason = "ok" | "connect_error" | "error:<code>" | "exception"
    """
    payload: dict[str, Any] = {
        "model":  model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 4096},
    }
    if system_instruction:
        payload["system"] = system_instruction

    model_label = model
    try:
        with httpx.Client(timeout=TIMEOUT_LOCAL_S) as client:
            t0  = time.monotonic()
            res = client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
            elapsed = round((time.monotonic() - t0) * 1000)

        if res.status_code != 200:
            logger.warning(f"[Ollama:{model_label}] HTTP {res.status_code}")
            return None, f"error:{res.status_code}"

        text = res.json().get("response", "").strip()
        if not text:
            return None, "empty"

        logger.info(f"[Ollama:{model_label}] [OK] ({elapsed}ms)")
        return text, "ok"

    except httpx.ConnectError:
        logger.error(f"[Ollama:{model_label}] Cannot connect - is Ollama running?")
        return None, "connect_error"
    except httpx.TimeoutException:
        logger.warning(f"[Ollama:{model_label}] Timeout after {TIMEOUT_LOCAL_S}s")
        return None, "timeout"
    except Exception as exc:
        logger.error(f"[Ollama:{model_label}] Unexpected: {exc}")
        return None, "exception"


# ---------------------------------------------------------------------------
# Gemini caller (cloud fallback)
# ---------------------------------------------------------------------------

def _call_gemini(
    model:              str,
    api_key:            str,
    prompt:             str,
    system_instruction: str = "",
) -> tuple[str | None, str]:
    """
    Call Gemini via Google AI Studio.
    Supports dynamic alias resolution and candidate model fallbacks if a model name is not available on v1beta.
    Returns (text, reason): reason = "ok" | "429" | "403_blocked" | "timeout" | "error:<code>"
    """
    if not api_key:
        return None, "no_key"

    candidate_models = [model]
    for alt in GEMINI_MODEL_FALLBACK_CANDIDATES.get(model, []):
        if alt not in candidate_models:
            candidate_models.append(alt)

    key_tag = f"...{api_key[-6:]}" if len(api_key) >= 6 else "key"
    last_reason = "error"

    for candidate in candidate_models:
        url = f"{GEMINI_BASE_URL}/models/{candidate}:generateContent?key={api_key}"
        payload: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048},
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        try:
            with httpx.Client(timeout=TIMEOUT_CLOUD_S) as client:
                t0 = time.monotonic()
                res = client.post(url, json=payload)
                elapsed = round((time.monotonic() - t0) * 1000)

            if res.status_code == 429:
                logger.warning(f"[Gemini:{candidate}][{key_tag}] 429 rate-limited")
                return None, "429"
            if res.status_code == 403:
                logger.warning(f"[Gemini:{candidate}][{key_tag}] 403 forbidden / key blocked")
                return None, "403_blocked"
            if res.status_code in (400, 404):
                logger.warning(
                    f"[Gemini:{candidate}][{key_tag}] HTTP {res.status_code} "
                    f"(model not available), attempting fallback candidate..."
                )
                last_reason = f"error:{res.status_code}"
                continue
            if res.status_code != 200:
                logger.warning(f"[Gemini:{candidate}][{key_tag}] HTTP {res.status_code}")
                return None, f"error:{res.status_code}"
            if elapsed > TIMEOUT_CLOUD_S * 1000:
                logger.warning(f"[Gemini:{candidate}][{key_tag}] Latency {elapsed}ms")
                return None, "timeout"

            cands = res.json().get("candidates", [])
            if not cands:
                return None, "empty"

            text = cands[0]["content"]["parts"][0]["text"]
            logger.info(f"[Gemini:{candidate}][{key_tag}] [OK] ({elapsed}ms)")
            return text, "ok"

        except httpx.TimeoutException:
            logger.warning(f"[Gemini:{candidate}][{key_tag}] Connection timeout")
            return None, "timeout"
        except Exception as exc:
            logger.warning(f"[Gemini:{candidate}][{key_tag}] Exception: {exc}")
            return None, "exception"

    # All model candidates exhausted (all returned 400/404 and continued)
    return None, last_reason

# ---------------------------------------------------------------------------
# Vertex AI caller (direct Service Account Bearer Token)
# ---------------------------------------------------------------------------

def _get_vertex_ai_credentials() -> tuple[str | None, str | None]:
    """
    Load project ID and generate fresh OAuth2 Bearer token from Service Account JSON if available.
    """
    from pathlib import Path
    import base64
    import json
    import urllib.request
    import urllib.parse
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.serialization import load_pem_private_key

    sa_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    if not sa_path or not Path(sa_path).exists():
        default_p = Path(__file__).resolve().parent.parent / "gen-lang-client-0821704500-6831370efa0e.json"
        if default_p.exists():
            sa_path = str(default_p)

    if not sa_path or not Path(sa_path).exists():
        return None, None

    try:
        sa_data = json.loads(Path(sa_path).read_text(encoding="utf-8"))
        project_id = sa_data.get("project_id")
        client_email = sa_data.get("client_email")
        token_uri = sa_data.get("token_uri", "https://oauth2.googleapis.com/token")
        pk = load_pem_private_key(sa_data["private_key"].encode("utf-8"), password=None)

        def b64url(d):
            if isinstance(d, str):
                d = d.encode("utf-8")
            return base64.urlsafe_b64encode(d).decode("utf-8").rstrip("=")

        now = int(time.time())
        jwt_header = {"alg": "RS256", "typ": "JWT"}
        jwt_payload = {
            "iss": client_email,
            "scope": "https://www.googleapis.com/auth/cloud-platform",
            "aud": token_uri,
            "exp": now + 3600,
            "iat": now,
        }
        signing_input = f"{b64url(json.dumps(jwt_header))}.{b64url(json.dumps(jwt_payload))}".encode("utf-8")
        sig = pk.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
        signed_jwt = f"{signing_input.decode('utf-8')}.{b64url(sig)}"

        req = urllib.request.Request(
            token_uri,
            data=urllib.parse.urlencode({
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": signed_jwt,
            }).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            token_res = json.loads(resp.read().decode("utf-8"))
            return project_id, token_res.get("access_token")
    except Exception as exc:
        logger.debug(f"Vertex AI token generation note: {exc}")
        return None, None


def _call_vertex_ai(
    model: str,
    project_id: str,
    bearer_token: str,
    prompt: str,
    system_instruction: str = "",
    location: str = "us-central1",
) -> tuple[str | None, str]:
    """Call Google Cloud Vertex AI generateContent endpoint with OAuth2 Bearer token."""
    if not bearer_token or not project_id:
        return None, "no_auth"

    v_model = "gemini-1.5-flash" if "flash" in model else "gemini-1.5-pro"
    url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{v_model}:generateContent"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 8192},
    }
    if system_instruction:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

    try:
        with httpx.Client(timeout=TIMEOUT_CLOUD_S) as client:
            t0 = time.monotonic()
            res = client.post(url, json=payload, headers=headers)
            elapsed = round((time.monotonic() - t0) * 1000)

        if res.status_code == 200:
            cands = res.json().get("candidates", [])
            if cands:
                text = cands[0]["content"]["parts"][0]["text"]
                logger.info(f"[VertexAI:{v_model}] [OK] ({elapsed}ms)")
                return text, "ok"
            return None, "empty"
        elif res.status_code == 429:
            logger.warning(f"[VertexAI:{v_model}] 429 rate-limited")
            return None, "429"
        else:
            logger.warning(f"[VertexAI:{v_model}] HTTP {res.status_code}")
            return None, f"error:{res.status_code}"
    except httpx.TimeoutException:
        return None, "timeout"
    except Exception as exc:
        logger.warning(f"[VertexAI:{v_model}] Exception: {exc}")
        return None, "exception"


# ---------------------------------------------------------------------------
# External paid-provider callers are intentionally absent from this router.
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# Cloudflare Workers AI caller (REST API)
# ---------------------------------------------------------------------------

def _call_cloudflare_ai(
    account_id:         str,
    ai_token:           str,
    model:              str,
    prompt:             str,
    system_instruction: str = "",
) -> tuple[str | None, str]:
    """
    Call Cloudflare Workers AI via REST API.
    Returns (text, reason): reason = \"ok\" | \"429\" | \"error:<code>\" | \"timeout\" | \"exception\"
    Supports chat-completion models: @cf/qwen/qwen1.5-7b-chat-awq, @cf/meta/llama-3-8b-instruct, etc.
    """
    if not account_id or not ai_token:
        return None, "no_auth"

    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
    headers = {
        "Authorization": f"Bearer {ai_token}",
        "Content-Type": "application/json",
    }
    messages: list[dict] = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    payload: dict = {"messages": messages, "max_tokens": 2048}

    try:
        with httpx.Client(timeout=TIMEOUT_CLOUD_S) as client:
            t0  = time.monotonic()
            res = client.post(url, json=payload, headers=headers)
            elapsed = round((time.monotonic() - t0) * 1000)

        if res.status_code == 200:
            data = res.json()
            text = data.get("result", {}).get("response", "").strip()
            if text:
                logger.info(f"[CloudflareAI:{model}] [OK] ({elapsed}ms)")
                return text, "ok"
            return None, "empty"
        elif res.status_code == 429:
            logger.warning(f"[CloudflareAI:{model}] 429 rate-limited")
            return None, "429"
        else:
            logger.warning(f"[CloudflareAI:{model}] HTTP {res.status_code}")
            return None, f"error:{res.status_code}"
    except httpx.TimeoutException:
        logger.warning(f"[CloudflareAI:{model}] Timeout after {TIMEOUT_CLOUD_S}s")
        return None, "timeout"
    except Exception as exc:
        logger.warning(f"[CloudflareAI:{model}] Exception: {exc}")
        return None, "exception"


# ---------------------------------------------------------------------------
def _is_cloud_environment() -> bool:
    """Detect if running on cloud platform (Vercel, Hugging Face, Fly.io)."""
    return any(
        os.getenv(k) for k in [
            "VERCEL", "VERCEL_ENV", "SPACE_ID", "FLY_APP_NAME",
            "HF_SPACE_ID", "RAILWAY_STATIC_URL"
        ]
    ) or os.getenv("ENVIRONMENT", "").lower() in ("production", "prod", "cloud")


_last_gemini_alert_time: float = 0.0
GEMINI_ALERT_COOLDOWN_SECONDS: float = 300.0


def _trigger_gemini_telegram_alert(attempted_routes: list[dict[str, Any]]) -> None:
    """Send Telegram outage alert when all Gemini models/keys fail."""
    global _last_gemini_alert_time
    now = time.time()
    if now - _last_gemini_alert_time < GEMINI_ALERT_COOLDOWN_SECONDS:
        return
    _last_gemini_alert_time = now

    gemini_failures = [
        r for r in attempted_routes
        if "gemini" in r.get("route", "").lower() or "cloud:" in r.get("route", "").lower()
    ]
    if not gemini_failures:
        return

    models = list({
        r.get("route", "").split(":")[1].split("[")[0]
        for r in gemini_failures if ":" in r.get("route", "")
    })
    reasons = list({r.get("reason", "error") for r in gemini_failures})
    reason_str = ", ".join(reasons) or "403_blocked/timeout"

    try:
        from project.mlops.notifications.webhook_notifier import WebhookNotifier
        notifier = WebhookNotifier()
        notifier.notify_gemini_outage(
            attempted_models=models,
            reason=reason_str,
            details=f"Failed {len(gemini_failures)} Gemini attempts across all rotated keys/models."
        )
        logger.info("[Telegram Alert] Dispatched Gemini API outage alert to Telegram.")
    except Exception as e:
        logger.warning(f"[Telegram Alert] Failed to dispatch alert: {e}")


class HybridRouter:
    """
    Local-First Hybrid Router.

    Priority:
      LOCAL 1: qwen2.5:7b          (best Chinese/Thai/BaZi understanding)
      LOCAL 2: qwen2.5-coder:7b    (capable fallback)
      LOCAL 3: llama3:8b           (English fallback)
      CLOUD:   Gemini models x all keys (gemini-3.5-flash-lite -> gemini-flash-latest -> gemini-3.6-flash)
      CLOUD:   Cloudflare AI and Gemini (zero-cost fallback chain)
    """

    def __init__(self, zero_cost_only: bool | None = None) -> None:
        self.zero_cost_only: bool = (
            zero_cost_only if zero_cost_only is not None
            else (os.getenv("AI_ZERO_COST_ONLY", "false").lower() == "true")
        )

    def _build_routes(self) -> list[dict[str, Any]]:
        routes: list[dict[str, Any]] = []

        disable_local = os.getenv("DISABLE_LOCAL_OLLAMA", "").lower() in ("true", "1", "yes")
        ollama_url_lower = OLLAMA_BASE_URL.lower().strip()
        is_disabled_url = ollama_url_lower in ("disabled", "none", "false", "")
        is_cloud = _is_cloud_environment()

        # === CLOUD MODE (Vercel / HF Spaces / Fly.io) ===
        # Priority chain: Gemini -> Cloudflare AI
        if is_cloud:
            # Codex CLI is the primary governed cloud route when an approved
            # local wrapper is installed; Gemini remains the zero-cost fallback.
            if check_codex_installation():
                routes.append({"type": "codex_cli", "model": "codex-cli", "key": None})
            # Route 1: Gemini Cloud (key rotation)
            for model in GEMINI_MODELS_ROTATION:
                for key in _gemini_keys():
                    routes.append({"type": "gemini", "model": model, "key": key})

            # Route 2: Cloudflare Workers AI (@cf/qwen/qwen1.5-7b-chat-awq)
            if CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_AI_TOKEN:
                routes.append({
                    "type": "cloudflare_ai",
                    "model": CLOUDFLARE_AI_MODEL,
                    "key": CLOUDFLARE_AI_TOKEN,
                    "account_id": CLOUDFLARE_ACCOUNT_ID,
                })

        # === LOCAL DEV MODE ===
        # Route 1: Ollama local models (if not disabled)
        if not disable_local and not is_disabled_url and not is_cloud:
            for model in [PRIMARY_LOCAL_MODEL, SECONDARY_LOCAL_MODEL, TERTIARY_LOCAL_MODEL]:
                routes.append({"type": "ollama", "model": model, "key": None})

            # Route 2 (local): Cloudflare AI
            if CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_AI_TOKEN:
                routes.append({
                    "type": "cloudflare_ai",
                    "model": CLOUDFLARE_AI_MODEL,
                    "key": CLOUDFLARE_AI_TOKEN,
                    "account_id": CLOUDFLARE_ACCOUNT_ID,
                })

            # Route 3 (local): Gemini cloud fallback
            for model in GEMINI_MODELS_ROTATION:
                for key in _gemini_keys():
                    routes.append({"type": "gemini", "model": model, "key": key})

            logger.info("[Router] Zero-cost policy active: excluded paid endpoints.")

        return routes



    def generate(
        self,
        prompt:             str,
        system_instruction: str = "",
    ) -> dict[str, Any]:
        """
        Execute prompt through route chain. Returns on first success.

        Returns
        -------
        dict: text, model_used, route, latency_ms, reason, attempted_routes
        """
        routes    = self._build_routes()
        attempted = []

        logger.info(
            f"[Router] Starting - {sum(1 for r in routes if r['type']=='ollama')} local "
            f"+ {sum(1 for r in routes if r['type'] in ('gemini', 'vertex_ai'))} cloud routes"
        )

        for route in routes:
            rtype = route["type"]
            model = route["model"]
            key   = route["key"]
            label = (
                f"local:{model}" if rtype == "ollama"
                else f"cloud:vertex_ai:{model}" if rtype == "vertex_ai"
                else f"cloud:{model}[...{key[-6:]}]" if key and len(key) >= 6
                else f"cloud:{model}"
            )

            # Fast Circuit Breaker check - skip recently rate-limited route immediately (0ms)
            if _is_route_circuit_open(label):
                logger.debug(f"[Router] [CIRCUIT OPEN] Skipping '{label}' (cooldown active)")
                continue

            t0 = time.monotonic()
            if rtype == "ollama":
                text, reason = _call_ollama(model, prompt, system_instruction)
            elif rtype == "codex_cli":
                try:
                    text = call_codex_cli(prompt, system_instruction=system_instruction, model=model)
                    reason = "ok"
                except Exception:
                    text, reason = None, "error"
            elif rtype == "gemini":
                text, reason = _call_gemini(model, key, prompt, system_instruction)
            elif rtype == "vertex_ai":
                proj_id = route.get("project_id", "")
                text, reason = _call_vertex_ai(model, proj_id, key, prompt, system_instruction)
            elif rtype == "cloudflare_ai":
                account_id = route.get("account_id", "")
                text, reason = _call_cloudflare_ai(account_id, key, model, prompt, system_instruction)
            else:
                text, reason = None, "unknown_route"
            latency_ms = round((time.monotonic() - t0) * 1000)

            # Record Observability LLM telemetry
            try:
                from project.core.observability import observability_manager
                observability_manager.record_llm_inference(
                    provider=f"{rtype}:{model}",
                    status="ok" if text is not None else reason,
                    duration=latency_ms / 1000.0,
                )
            except Exception:
                pass

            if text is not None:
                logger.info(f"[Router] [OK] {label} ({latency_ms}ms)")
                return {
                    "text":             text,
                    "model_used":       model,
                    "route":            rtype,
                    "latency_ms":       latency_ms,
                    "reason":           reason,
                    "attempted_routes": attempted,
                }

            attempted.append({"route": label, "reason": reason, "latency_ms": latency_ms})
            logger.warning(f"[Router] [FAIL] {label} -> {reason}")

            # Trip circuit breaker on rate limit for immediate bypass on next calls
            if reason == "429":
                _trip_route_circuit(label)

        # Trigger Telegram alert if all Gemini cloud routes failed
        if any("cloud:" in r.get("route", "") for r in attempted):
            _trigger_gemini_telegram_alert(attempted)

        return {
            "text":             None,
            "model_used":       None,
            "route":            "exhausted",
            "latency_ms":       0,
            "reason":           "all_routes_failed",
            "attempted_routes": attempted,
            "error":            "All local + cloud routes failed",
        }

    def health_check(self) -> dict[str, Any]:
        """Check all local models and cloud keys."""
        result: dict[str, Any] = {"local": [], "cloud": {}}

        # Check each local model
        for model in [PRIMARY_LOCAL_MODEL, SECONDARY_LOCAL_MODEL, TERTIARY_LOCAL_MODEL]:
            try:
                with httpx.Client(timeout=5.0) as client:
                    r = client.post(
                        f"{OLLAMA_BASE_URL}/api/generate",
                        json={"model": model, "prompt": "ping", "stream": False,
                              "options": {"num_predict": 1}},
                    )
                result["local"].append({
                    "model":  model,
                    "status": "ready" if r.status_code == 200 else "error",
                    "http":   r.status_code,
                })
            except httpx.ConnectError:
                result["local"].append({"model": model, "status": "ollama_offline"})
            except Exception as e:
                result["local"].append({"model": model, "status": "error", "detail": str(e)})

        # Check cloud keys
        gemini_keys = _gemini_keys()
        key_statuses = []
        for i, key in enumerate(gemini_keys, 1):
            try:
                with httpx.Client(timeout=5.0) as client:
                    r = client.get(f"{GEMINI_BASE_URL}/models?key={key}&pageSize=1")
                key_statuses.append({
                    "key_index": i,
                    "key_hint":  f"...{key[-6:]}",
                    "status":    "reachable" if r.status_code == 200 else "error",
                    "http":      r.status_code,
                })
            except Exception as e:
                key_statuses.append({"key_index": i, "status": "unreachable", "error": str(e)})

        result["cloud"] = {
            "total_keys": len(gemini_keys),
            "keys":       key_statuses,
            "models":     [GEMINI_PRIMARY_MODEL, GEMINI_SECONDARY_MODEL],
        }
        return result


# Global HybridRouter Instance
router = HybridRouter()


# ---------------------------------------------------------------------------
# FastAPI Route Handlers for 16 Metaphysics Disciplines, MCP, Focus, & Debate
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Body, HTTPException, Query, Request
from fastapi.responses import JSONResponse

api_router = APIRouter(tags=["Metaphysics & MCP API"])
metaphysics_api_router = api_router

from project.mcp_server import HoroMCPTools, call_tool, get_mcp_manifest
from project.schemas.mcp_tools_v1 import (
    BaZiCalculateParams,
    IChingCalculateParams,
    LiuRenCalculateParams,
    LiuYaoCalculateParams,
    MCPCallToolRequest,
    MCPCallToolResponse,
    MeiHuaCalculateParams,
    MetaphysicsDebateParams,
    MianXiangAnalyzeParams,
    NumerologyCalculateParams,
    QiMenCalculateParams,
    QiZhengCalculateParams,
    QuestionFocusRouteParams,
    SanHeCalculateParams,
    TaiYiCalculateParams,
    ThaiVedicCalculateParams,
    WesternCalculateParams,
    XuanKongCalculateParams,
    ZeJiCalculateParams,
    ZiWeiCalculateParams,
)


@api_router.get("/api/mcp/manifest")
@api_router.get("/mcp/manifest")
async def mcp_manifest() -> dict[str, Any]:
    """Return full MCP server tool manifest with all 36+ tools."""
    return get_mcp_manifest()


@api_router.post("/api/mcp/call")
@api_router.post("/mcp/call")
async def mcp_call_tool(request: MCPCallToolRequest) -> dict[str, Any]:
    """Execute an MCP tool via JSON-RPC dispatcher."""
    result = call_tool(request.tool_name, request.arguments)
    return result


@api_router.post("/api/route/focus")
@api_router.post("/route/focus")
async def route_focus_post(params: QuestionFocusRouteParams) -> dict[str, Any]:
    """Classify user query into 6 domains and produce engine focus directives."""
    lang_val = params.language.value if hasattr(params.language, "value") else str(params.language)
    return HoroMCPTools.question_focus_route(
        query=params.query,
        context=params.context,
        language=lang_val,
    )


@api_router.get("/api/route/focus")
@api_router.get("/route/focus")
async def route_focus_get(query: str, language: str = "th") -> dict[str, Any]:
    """Classify user query via GET query parameters."""
    return HoroMCPTools.question_focus_route(query=query, language=language)


@api_router.post("/api/debate/synthesize")
@api_router.post("/debate/synthesize")
async def debate_synthesize(params: MetaphysicsDebateParams) -> dict[str, Any]:
    """Execute 8-Master Peer Debate, Consensus Matrix & Orchestrator Synthesis."""
    lang_val = params.language.value if hasattr(params.language, "value") else str(params.language)
    return HoroMCPTools.metaphysics_debate(
        query=params.query,
        birth_datetime=params.birth_datetime,
        longitude=params.longitude,
        utc_offset_hours=params.utc_offset_hours,
        unknown_hour=params.unknown_hour,
        language=lang_val,
        force_hitl=params.force_hitl,
        active_masters=params.active_masters,
    )


# ---------------------------------------------------------------------------
# Universal Calculation Route for all 16 Disciplines
# ---------------------------------------------------------------------------

DISCIPLINE_TOOL_MAP: dict[str, str] = {
    "bazi": "bazi_calculate",
    "ziwei": "ziwei_calculate",
    "zi_wei": "ziwei_calculate",
    "qimen": "qimen_calculate",
    "qi_men": "qimen_calculate",
    "liuren": "liuren_calculate",
    "liu_ren": "liuren_calculate",
    "daliuren": "liuren_calculate",
    "da_liu_ren": "liuren_calculate",
    "taiyi": "tai_yi_calculate",
    "tai_yi": "tai_yi_calculate",
    "iching": "iching_calculate",
    "i_ching": "iching_calculate",
    "liuyao": "liu_yao_calculate",
    "liu_yao": "liu_yao_calculate",
    "meihua": "mei_hua_calculate",
    "mei_hua": "mei_hua_calculate",
    "xuankong": "xuankong_calculate",
    "xuan_kong": "xuankong_calculate",
    "sanhe": "san_he_calculate",
    "san_he": "san_he_calculate",
    "zeji": "zeji_calculate",
    "ze_ji": "zeji_calculate",
    "mianxiang": "mian_xiang_analyze",
    "mian_xiang": "mian_xiang_analyze",
    "physiognomy": "mian_xiang_analyze",
    "thaivedic": "thaivedic_calculate",
    "thai_vedic": "thaivedic_calculate",
    "western": "western_calculate",
    "western_uranian": "western_calculate",
    "uranian": "western_calculate",
    "numerology": "numerology_calculate",
    "satta_lek": "numerology_calculate",
    "qizheng": "qi_zheng_calculate",
    "qi_zheng": "qi_zheng_calculate",
    "qizhengsiyu": "qi_zheng_calculate",
    "qi_zheng_si_yu": "qi_zheng_calculate",
}


@api_router.post("/api/calculate/{discipline}")
@api_router.post("/calculate/{discipline}")
async def calculate_discipline_post(discipline: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    """Universal POST calculation endpoint for all 16 Metaphysics disciplines."""
    disc_norm = discipline.lower().replace("-", "_").strip()
    if disc_norm not in DISCIPLINE_TOOL_MAP:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown discipline '{discipline}'. Supported: {sorted(set(DISCIPLINE_TOOL_MAP.keys()))}",
        )
    tool_name = DISCIPLINE_TOOL_MAP[disc_norm]
    res = call_tool(tool_name, payload)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Calculation failed"))
    return res.get("result")  # type: ignore[return-value]


@api_router.get("/api/calculate/{discipline}")
@api_router.get("/calculate/{discipline}")
async def calculate_discipline_get(discipline: str, request: Request) -> dict[str, Any]:
    """Universal GET calculation endpoint for quick browser testing via query params."""
    query_params = dict(request.query_params)
    payload: dict[str, Any] = {}
    for k, v in query_params.items():
        if v.isdigit():
            payload[k] = int(v)
        else:
            try:
                payload[k] = float(v)
            except ValueError:
                if v.lower() in ("true", "false"):
                    payload[k] = (v.lower() == "true")
                else:
                    payload[k] = v
    return await calculate_discipline_post(discipline, payload)


# ---------------------------------------------------------------------------
# Dedicated Endpoints for each of the 16 Metaphysics Disciplines
# ---------------------------------------------------------------------------

@api_router.post("/api/calculate/bazi")
@api_router.post("/calculate/bazi")
async def calculate_bazi_endpoint(params: BaZiCalculateParams) -> dict[str, Any]:
    return HoroMCPTools.bazi_calculate(**params.model_dump())


@api_router.post("/api/calculate/ziwei")
@api_router.post("/calculate/ziwei")
async def calculate_ziwei_endpoint(params: ZiWeiCalculateParams) -> dict[str, Any]:
    return HoroMCPTools.ziwei_calculate(**params.model_dump())


@api_router.post("/api/calculate/qimen")
@api_router.post("/calculate/qimen")
async def calculate_qimen_endpoint(params: QiMenCalculateParams) -> dict[str, Any]:
    return HoroMCPTools.qimen_calculate(**params.model_dump())


@api_router.post("/api/calculate/liuren")
@api_router.post("/calculate/liuren")
async def calculate_liuren_endpoint(params: LiuRenCalculateParams) -> dict[str, Any]:
    return HoroMCPTools.liuren_calculate(**params.model_dump())


@api_router.post("/api/calculate/taiyi")
@api_router.post("/calculate/taiyi")
async def calculate_taiyi_endpoint(params: TaiYiCalculateParams) -> dict[str, Any]:
    return HoroMCPTools.tai_yi_calculate(**params.model_dump())


@api_router.post("/api/calculate/iching")
@api_router.post("/calculate/iching")
async def calculate_iching_endpoint(params: IChingCalculateParams) -> dict[str, Any]:
    return HoroMCPTools.iching_calculate(**params.model_dump())


@api_router.post("/api/calculate/liuyao")
@api_router.post("/calculate/liuyao")
async def calculate_liuyao_endpoint(params: LiuYaoCalculateParams) -> dict[str, Any]:
    return HoroMCPTools.liu_yao_calculate(**params.model_dump())


@api_router.post("/api/calculate/meihua")
@api_router.post("/calculate/meihua")
async def calculate_meihua_endpoint(params: MeiHuaCalculateParams) -> dict[str, Any]:
    return HoroMCPTools.mei_hua_calculate(**params.model_dump())


@api_router.post("/api/calculate/xuankong")
@api_router.post("/calculate/xuankong")
async def calculate_xuankong_endpoint(params: XuanKongCalculateParams) -> dict[str, Any]:
    return HoroMCPTools.xuankong_calculate(**params.model_dump())


@api_router.post("/api/calculate/sanhe")
@api_router.post("/calculate/sanhe")
async def calculate_sanhe_endpoint(params: SanHeCalculateParams) -> dict[str, Any]:
    return HoroMCPTools.san_he_calculate(**params.model_dump())


@api_router.post("/api/calculate/zeji")
@api_router.post("/calculate/zeji")
async def calculate_zeji_endpoint(params: ZeJiCalculateParams) -> dict[str, Any]:
    return HoroMCPTools.zeji_calculate(**params.model_dump())


@api_router.post("/api/calculate/mianxiang")
@api_router.post("/calculate/mianxiang")
async def calculate_mianxiang_endpoint(params: MianXiangAnalyzeParams) -> dict[str, Any]:
    return HoroMCPTools.mian_xiang_analyze(**params.model_dump())


@api_router.post("/api/calculate/thaivedic")
@api_router.post("/calculate/thaivedic")
async def calculate_thaivedic_endpoint(params: ThaiVedicCalculateParams) -> dict[str, Any]:
    return HoroMCPTools.thaivedic_calculate(**params.model_dump())


@api_router.post("/api/calculate/western")
@api_router.post("/calculate/western")
async def calculate_western_endpoint(params: WesternCalculateParams) -> dict[str, Any]:
    return HoroMCPTools.western_calculate(**params.model_dump())


@api_router.post("/api/calculate/numerology")
@api_router.post("/calculate/numerology")
async def calculate_numerology_endpoint(params: NumerologyCalculateParams) -> dict[str, Any]:
    return HoroMCPTools.numerology_calculate(**params.model_dump())


@api_router.post("/api/calculate/qizheng")
@api_router.post("/calculate/qizheng")
async def calculate_qizheng_endpoint(params: QiZhengCalculateParams) -> dict[str, Any]:
    return HoroMCPTools.qi_zheng_calculate(**params.model_dump())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    import json
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")

    router = HybridRouter()

    print("=== Health Check ===")
    h = router.health_check()
    print(json.dumps(h, indent=2, ensure_ascii=False))

    print("\n=== Generate Test ===")
    res = router.generate(
        prompt             = "Reply with exactly this JSON: {\"status\":\"ok\",\"source\":\"local\"}",
        system_instruction = "Reply only with valid JSON. No explanation.",
    )
    print(f"Route   : {res['route']} / {res['model_used']}")
    print(f"Latency : {res['latency_ms']}ms")
    print(f"Text    : {(res['text'] or '')[:120]}")
