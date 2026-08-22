#!/usr/bin/env python3
"""Optional Gemini Vision adapter for Mian Xiang face-feature extraction.

The deterministic physiognomy engine remains the source of interpretation. This
module only turns an image into a small, validated feature dictionary. Images are
read in memory, never written to logs, and the Gemini call is opt-in via an API
key or ``GOOGLE_AI_STUDIO_API_KEY``.
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import mimetypes
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger("mian_xiang_vision")
DEFAULT_MODEL = "gemini-2.0-flash"
MAX_IMAGE_BYTES = 12 * 1024 * 1024
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
FEATURE_KEYS = {
    "face_shape",
    "forehead",
    "eyebrows",
    "eyes",
    "nose",
    "mouth",
    "ears",
    "chin",
    "moles",
}

VISION_PROMPT = """You are a careful Mian Xiang feature extractor. Return JSON only.
Do not identify the person and do not infer medical, legal, or sensitive traits.
Extract only visible, coarse features for a classical physiognomy calculator:
face_shape (round, oval, square, long, pointed, or unknown), forehead
(wide, narrow, average, or unknown), eyebrows, eyes, nose, mouth, ears, chin,
and moles as an array of {location, size}. Use unknown when unclear.
"""


def _json_from_text(text: str) -> dict[str, Any]:
    """Parse a model response containing a JSON object or fenced JSON."""
    candidate = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", candidate, re.DOTALL | re.IGNORECASE)
    if fenced:
        candidate = fenced.group(1)
    else:
        start, end = candidate.find("{"), candidate.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("Vision response did not contain a JSON object")
        candidate = candidate[start : end + 1]
    value = json.loads(candidate)
    if not isinstance(value, dict):
        raise ValueError("Vision response JSON must be an object")
    return value


def normalize_features(value: dict[str, Any]) -> dict[str, Any]:
    """Keep only the Mian Xiang feature contract and normalize unsafe values."""
    result: dict[str, Any] = {}
    for key in FEATURE_KEYS - {"moles"}:
        item = value.get(key)
        if isinstance(item, str):
            result[key] = item.strip().lower()[:80] or "unknown"
        else:
            result[key] = "unknown"
    moles = value.get("moles", [])
    if not isinstance(moles, list):
        moles = []
    result["moles"] = [
        {
            "location": str(item.get("location", "unknown"))[:80],
            "size": str(item.get("size", "unknown"))[:40],
        }
        for item in moles
        if isinstance(item, dict)
    ][:20]
    return result


def _image_payload(image_path: Path) -> tuple[str, str]:
    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")
    if image_path.stat().st_size > MAX_IMAGE_BYTES:
        raise ValueError(f"Image exceeds {MAX_IMAGE_BYTES} byte safety limit")
    mime = mimetypes.guess_type(image_path.name)[0] or ""
    if mime not in ALLOWED_MIME_TYPES:
        raise ValueError(f"Unsupported image type: {mime or 'unknown'}")
    return mime, base64.b64encode(image_path.read_bytes()).decode("ascii")


def analyze_image(
    image_path: str | Path,
    *,
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
    timeout: float = 20.0,
) -> dict[str, Any]:
    """Extract coarse features locally or through Gemini when configured."""
    path = Path(image_path)
    mime, encoded = _image_payload(path)
    key = (api_key or os.getenv("GOOGLE_AI_STUDIO_API_KEY", "")).strip()
    if not key:
        return {
            "status": "needs_api_key",
            "source": "none",
            "features": normalize_features({}),
            "message": "Set GOOGLE_AI_STUDIO_API_KEY or pass --api-key to run Vision extraction.",
        }

    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{urllib.parse.quote(model, safe='')}:generateContent?key={urllib.parse.quote(key)}"
    )
    body = {
        "contents": [{"parts": [{"text": VISION_PROMPT}, {"inline_data": {"mime_type": mime, "data": encoded}}]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
        return {"status": "ok", "source": "gemini_vision", "model": model, "features": normalize_features(_json_from_text(text))}
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError, ValueError) as exc:
        LOGGER.warning("[WARNING] Vision extraction unavailable: %s", type(exc).__name__)
        return {"status": "error", "source": "gemini_vision", "model": model, "features": normalize_features({}), "error": type(exc).__name__}


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract coarse Mian Xiang features from an image")
    parser.add_argument("image", type=Path)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()
    try:
        result = analyze_image(args.image, api_key=args.api_key, model=args.model)
    except (FileNotFoundError, ValueError) as exc:
        result = {"status": "invalid_input", "source": "none", "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result)
    return 0 if result.get("status") in {"ok", "needs_api_key"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
