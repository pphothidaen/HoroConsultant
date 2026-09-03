"""Small, dependency-light Google Gemini SDK adapter."""

from __future__ import annotations

from typing import Any, Callable, Iterable

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


class GeminiSDKError(RuntimeError):
    """Raised when no configured Gemini credential can complete a request."""


def generate_with_gemini(
    prompt: str,
    *,
    api_keys: Iterable[str],
    client_factory: Callable[[str], Any] | None = None,
    model: str = DEFAULT_GEMINI_MODEL,
) -> tuple[str, str]:
    """Try credentials in order and return the first non-empty response."""
    keys = [key for key in api_keys if key]
    if not keys:
        raise GeminiSDKError("Gemini is not configured")
    if client_factory is None:
        try:
            from google import genai
        except ImportError as exc:  # pragma: no cover
            raise GeminiSDKError("Gemini SDK is not installed") from exc
        client_factory = lambda key: genai.Client(api_key=key)

    errors: list[str] = []
    for key in keys:
        try:
            client = client_factory(key)
            response = client.models.generate_content(model=model, contents=prompt)
            text = str(getattr(response, "text", "") or "").strip()
            if text:
                return text, model
        except Exception as exc:  # provider rotation is intentionally fail-closed
            errors.append(type(exc).__name__)
    raise GeminiSDKError("All configured Gemini credentials failed")
