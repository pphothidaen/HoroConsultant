"""
project/core/codex_client.py
=============================
Codex / CODEX_CHATGPT AI Provider Client for HoroConsultant (Dev-Only).
Invokes local Codex CLI (`codex exec --json`) using ChatGPT Pro subscription quota.

GOAL:
- DO NOT use OpenAI API billing (no HTTP calls to api.openai.com).
- DO NOT require OPENAI_API_KEY, CODEX_PRO, or OPENAI_BASE_URL.
- Authentication comes transparently from local `codex login` session.
- Automatic fallback to Gemini on any unavailable condition.
"""

import logging
from typing import Dict, Any, Optional

from project.core.ai_provider_router import (
    ai_router,
    is_dev_environment,
    check_codex_installation,
    check_codex_authentication,
)

logger = logging.getLogger("codex_client")

# Agent Model Mapping Profiles
PROX5_AGENT_MODEL_MAP = {
    "orchestrator": "claude-3-7-sonnet",
    "business_analyst": "o3-mini",
    "developer": "deepseek-v3",
    "code_reviewer": "deepseek-r1",
    "qa_tester": "gpt-4o-mini",
    "devops": "gpt-4o-mini",
    "domain_master": "claude-3-5-sonnet",
}


def get_codex_auth_token() -> Optional[str]:
    """
    Check if local Codex CLI is authenticated via `codex login`.
    Never exposes token credentials.
    """
    authenticated, _ = check_codex_authentication()
    if authenticated:
        return "[AUTHENTICATED_VIA_LOCAL_CODEX_CLI_CHATGPT_SESSION]"
    return None


def get_prox5_base_url() -> str:
    """Return local CLI indicator."""
    return "local://codex-cli"


def call_codex_api(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: str = "codex_chatgpt",
    agent_role: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 4096,
) -> Dict[str, Any]:
    """
    Call CODEX_CHATGPT provider via AIProviderRouter.
    Executes local Codex CLI without requiring API keys or API billing.
    """
    if not is_dev_environment():
        logger.warning("[SAFETY] Codex CLI is scoped to Development Environment only. Blocked in Prod.")
        return {
            "status": "error",
            "provider": "CODEX_CHATGPT",
            "model": model,
            "content": "",
            "raw_response": None,
            "error_message": "Codex execution blocked: Production environment safety guard.",
            "error_type": "production_guard",
            "route_used": "codex_chatgpt",
        }

    return ai_router.call_ai(
        prompt=prompt,
        system_prompt=system_prompt,
        timeout_seconds=45,
    )
