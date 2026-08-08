"""Shared CORS helpers for the Vercel handler and FastAPI app."""

from __future__ import annotations

import os
from typing import Dict, List


def get_allowed_origins() -> List[str]:
    """Return the configured CORS origins from the environment."""
    raw = os.getenv("CORS_ALLOWED_ORIGINS", "*")
    if not raw or raw.strip() == "":
        return ["*"]

    origins = []
    for item in raw.replace(" ", "").split(","):
        if item:
            origins.append(item)
    return origins or ["*"]


def get_cors_headers(request_origin: str | None = None) -> Dict[str, str]:
    """Build CORS headers for a request, echoing the request origin when allowed."""
    allowed_origins = get_allowed_origins()
    if "*" in allowed_origins:
        allow_origin = "*"
    elif request_origin and request_origin in allowed_origins:
        allow_origin = request_origin
    else:
        allow_origin = None

    headers: Dict[str, str] = {
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
    }
    if allow_origin is not None:
        headers["Access-Control-Allow-Origin"] = allow_origin
    if request_origin:
        headers["Vary"] = "Origin"
    return headers
