"""
api_router.py — Hybrid API Routing & Fallback System
=====================================================
LOCAL-FIRST architecture: Ollama models are PRIMARY routes.
Gemini API (dual-key) is used only as cloud fallback.

Route order:
  1. Ollama PRIMARY_LOCAL_MODEL  (qwen2.5:7b   — best for BaZi/Thai/Chinese)
  2. Ollama SECONDARY_LOCAL_MODEL (qwen2.5-coder:7b)
  3. Ollama TERTIARY_LOCAL_MODEL  (llama3:8b)
  4. Gemini KEY1 → Gemini KEY2   (cloud fallback, all configured models)
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger("api_router")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OLLAMA_BASE_URL         = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
PRIMARY_LOCAL_MODEL     = os.getenv("OLLAMA_PRIMARY_MODEL",   "qwen2.5-bazi")
SECONDARY_LOCAL_MODEL   = os.getenv("OLLAMA_SECONDARY_MODEL", "qwen2.5:7b")
TERTIARY_LOCAL_MODEL    = os.getenv("OLLAMA_TERTIARY_MODEL",  "qwen2.5-coder:7b")


GEMINI_BASE_URL         = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_GEMINI_ROTATION = [
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
    "gemini-3.6-flash",
]

GEMINI_PRIMARY_MODEL    = os.getenv("PRIMARY_MODEL",   "gemini-3.5-flash-lite")
GEMINI_SECONDARY_MODEL  = os.getenv("SECONDARY_MODEL", "gemini-flash-latest")
GEMINI_TERTIARY_MODEL   = os.getenv("TERTIARY_MODEL",  "gemini-3.6-flash")

GEMINI_MODELS_ROTATION: list[str] = []
for m in [GEMINI_PRIMARY_MODEL, GEMINI_SECONDARY_MODEL, GEMINI_TERTIARY_MODEL, *DEFAULT_GEMINI_ROTATION]:
    if m and m not in GEMINI_MODELS_ROTATION:
        GEMINI_MODELS_ROTATION.append(m)

GEMINI_MODEL_FALLBACK_CANDIDATES: dict[str, list[str]] = {
    "gemini-3.5-flash-lite": ["gemini-2.0-flash-lite", "gemini-2.0-flash", "gemini-1.5-flash"],
    "gemini-flash-latest": ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash-latest"],
    "gemini-3.6-flash": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-2.0-flash-lite"],
    "gemini-3.7-flash": ["gemini-2.0-flash", "gemini-1.5-pro"],
}

OPENAI_API_KEY          = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL            = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TOGETHER_API_KEY        = os.getenv("TOGETHER_API_KEY", "")
TOGETHER_MODEL          = os.getenv("TOGETHER_MODEL", "Qwen/Qwen2.5-7B-Instruct-Turbo")

TIMEOUT_LOCAL_S         = float(os.getenv("LOCAL_TIMEOUT_SECONDS", "3.0"))
TIMEOUT_CLOUD_S         = float(os.getenv("API_TIMEOUT_SECONDS",   "8.0"))
RETRY_DELAY_S           = 2.0


def _gemini_keys() -> list[str]:
    """Return all unique, valid, non-placeholder Google AI Studio API keys from env."""
    raw = [
        os.getenv("GOOGLE_AI_STUDIO_API_KEY",  ""),
        os.getenv("GOOGLE_AI_STUDIO_API_KEY2", ""),
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

        logger.info(f"[Ollama:{model_label}] ✅ OK ({elapsed}ms)")
        return text, "ok"

    except httpx.ConnectError:
        logger.error(f"[Ollama:{model_label}] Cannot connect — is Ollama running?")
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
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 8192},
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
            logger.info(f"[Gemini:{candidate}][{key_tag}] ✅ OK ({elapsed}ms)")
            return text, "ok"

        except httpx.TimeoutException:
            logger.warning(f"[Gemini:{candidate}][{key_tag}] Connection timeout")
            return None, "timeout"
        except Exception as exc:
            logger.warning(f"[Gemini:{candidate}][{key_tag}] Exception: {exc}")
            return None, "exception"

    return None, last_reason


# ---------------------------------------------------------------------------
# OpenAI / Together caller (cloud external providers)
# ---------------------------------------------------------------------------

def _call_openai_compatible(
    provider_name:      str,
    base_url:           str,
    api_key:            str,
    model:              str,
    prompt:             str,
    system_instruction: str = "",
) -> tuple[str | None, str]:
    """Call an OpenAI-compatible API endpoint."""
    if not api_key:
        return None, "no_key"

    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 4096,
    }

    key_tag = f"...{api_key[-6:]}" if len(api_key) >= 6 else "key"
    try:
        with httpx.Client(timeout=TIMEOUT_CLOUD_S) as client:
            t0 = time.monotonic()
            res = client.post(url, json=payload, headers=headers)
            elapsed = round((time.monotonic() - t0) * 1000)

        if res.status_code == 429:
            logger.warning(f"[{provider_name}:{model}][{key_tag}] 429 rate-limited")
            return None, "429"
        if res.status_code != 200:
            logger.warning(f"[{provider_name}:{model}][{key_tag}] HTTP {res.status_code}")
            return None, f"error:{res.status_code}"

        choices = res.json().get("choices", [])
        if not choices:
            return None, "empty"

        text = choices[0].get("message", {}).get("content", "").strip()
        logger.info(f"[{provider_name}:{model}][{key_tag}] ✅ OK ({elapsed}ms)")
        return text, "ok"

    except httpx.TimeoutException:
        logger.warning(f"[{provider_name}:{model}][{key_tag}] Timeout")
        return None, "timeout"
    except Exception as exc:
        logger.warning(f"[{provider_name}:{model}][{key_tag}] Exception: {exc}")
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
      CLOUD:   Gemini models × all keys (gemini-3.5-flash-lite ➔ gemini-flash-latest ➔ gemini-3.6-flash)
      CLOUD:   OpenAI & Together AI external providers
    """

    def _build_routes(self) -> list[dict[str, Any]]:
        routes: list[dict[str, Any]] = []

        disable_local = os.getenv("DISABLE_LOCAL_OLLAMA", "").lower() in ("true", "1", "yes")
        ollama_url_lower = OLLAMA_BASE_URL.lower().strip()
        is_disabled_url = ollama_url_lower in ("disabled", "none", "false", "")
        is_cloud = _is_cloud_environment()

        # On cloud platforms (Vercel/HF/Fly), put Gemini cloud routes first if local Ollama is unreachable
        if is_cloud:
            for model in GEMINI_MODELS_ROTATION:
                for key in _gemini_keys():
                    routes.append({"type": "gemini", "model": model, "key": key})

        # 1. Primary Route: Ollama / GGUF Local Engine (if not disabled and not on pure cloud)
        if not disable_local and not is_disabled_url and not is_cloud:
            for model in [PRIMARY_LOCAL_MODEL, SECONDARY_LOCAL_MODEL, TERTIARY_LOCAL_MODEL]:
                routes.append({"type": "ollama", "model": model, "key": None})

        # 2. Fallback Route: Gemini Cloud Engine (if not already added above)
        if not is_cloud:
            for model in GEMINI_MODELS_ROTATION:
                for key in _gemini_keys():
                    routes.append({"type": "gemini", "model": model, "key": key})

        # 3. External AI Providers Fallback (OpenAI & Together AI)
        if OPENAI_API_KEY:
            routes.append({"type": "openai", "model": OPENAI_MODEL, "key": OPENAI_API_KEY})
        if TOGETHER_API_KEY:
            routes.append({"type": "together", "model": TOGETHER_MODEL, "key": TOGETHER_API_KEY})

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
            f"[Router] Starting — {sum(1 for r in routes if r['type']=='ollama')} local "
            f"+ {sum(1 for r in routes if r['type']=='gemini')} cloud routes"
        )

        for route in routes:
            rtype = route["type"]
            model = route["model"]
            key   = route["key"]
            label = (
                f"local:{model}" if rtype == "ollama"
                else f"cloud:{model}[...{key[-6:]}]" if key and len(key) >= 6
                else f"cloud:{model}"
            )

            t0 = time.monotonic()
            if rtype == "ollama":
                text, reason = _call_ollama(model, prompt, system_instruction)
            elif rtype == "gemini":
                text, reason = _call_gemini(model, key, prompt, system_instruction)
            elif rtype == "openai":
                text, reason = _call_openai_compatible("OpenAI", "https://api.openai.com/v1", key, model, prompt, system_instruction)
            elif rtype == "together":
                text, reason = _call_openai_compatible("Together", "https://api.together.xyz/v1", key, model, prompt, system_instruction)
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
                logger.info(f"[Router] ✅ {label} ({latency_ms}ms)")
                return {
                    "text":             text,
                    "model_used":       model,
                    "route":            rtype,
                    "latency_ms":       latency_ms,
                    "reason":           reason,
                    "attempted_routes": attempted,
                }

            attempted.append({"route": label, "reason": reason, "latency_ms": latency_ms})
            logger.warning(f"[Router] ❌ {label} → {reason}")

            if reason == "429":
                time.sleep(RETRY_DELAY_S)

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
