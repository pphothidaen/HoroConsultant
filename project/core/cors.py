"""Strict CORS policy shared by the Vercel handler and FastAPI app."""

from __future__ import annotations

import os
from urllib.parse import urlsplit


DEFAULT_CORS_ALLOWED_ORIGIN = "https://horo-consultant-psi.vercel.app"
CORS_ALLOWED_METHODS = ("GET", "POST", "OPTIONS")
CORS_ALLOWED_HEADERS = (
    "Accept",
    "Authorization",
    "Content-Type",
    "X-Request-ID",
    "X-Requested-With",
)


def _normalize_origin(value: str) -> str | None:
    """Return a browser origin, rejecting wildcards and non-origin URL values."""
    candidate = value.strip()
    if not candidate or candidate == "*":
        return None

    parsed = urlsplit(candidate)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        return None

    return f"{parsed.scheme}://{parsed.netloc}".lower()


def get_allowed_origins() -> list[str]:
    """Return the configured, non-wildcard CORS origin allowlist.

    ``CORS_ALLOWED_ORIGINS`` accepts a comma-delimited list of complete HTTP(S)
    origins. Invalid entries (including ``*``) are ignored; an empty valid list
    fails closed to the canonical Vercel frontend origin.
    """
    raw = os.getenv("CORS_ALLOWED_ORIGINS", "")
    candidates = raw.split(",") if raw.strip() else [DEFAULT_CORS_ALLOWED_ORIGIN]

    origins: list[str] = []
    for candidate in candidates:
        origin = _normalize_origin(candidate)
        if origin and origin not in origins:
            origins.append(origin)
    return origins or [DEFAULT_CORS_ALLOWED_ORIGIN]


def get_cors_headers(request_origin: str | None = None) -> dict[str, str]:
    """Build CORS headers only for an explicitly allowed request origin."""
    headers: dict[str, str] = {"Vary": "Origin"} if request_origin else {}
    origin = _normalize_origin(request_origin or "")
    if not origin or origin not in get_allowed_origins():
        return headers

    headers.update(
        {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": ", ".join(CORS_ALLOWED_METHODS),
            "Access-Control-Allow-Headers": ", ".join(CORS_ALLOWED_HEADERS),
        }
    )
    return headers
