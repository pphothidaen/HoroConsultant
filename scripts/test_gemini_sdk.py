#!/usr/bin/env python3
"""Test Gemini SDK as AGY CLI replacement."""
import os
import sys

# Load .env
from pathlib import Path
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key.strip(), value)

from google import genai

def test_key(name: str, key: str | None) -> bool:
    if not key:
        print(f"  {name}: MISSING")
        return False
    try:
        client = genai.Client(api_key=key)
        resp = client.models.generate_content(
            model="gemini-3.6-flash",
            contents="Reply with exactly: ok",
        )
        text = (resp.text or "").strip()
        print(f"  {name}: OK — {text!r}")
        return True
    except Exception as e:
        print(f"  {name}: FAIL — {e}")
        return False

def main():
    keys = {
        "KEY1": os.environ.get("GOOGLE_AI_STUDIO_API_KEY"),
        "KEY2": os.environ.get("GOOGLE_AI_STUDIO_API_KEY2"),
        "KEY3": os.environ.get("GOOGLE_AI_STUDIO_API_KEY3"),
    }
    print("=== Gemini SDK Test ===")
    ok = 0
    for name, key in keys.items():
        if test_key(name, key):
            ok += 1
    print(f"\n{ok}/3 keys working")

if __name__ == "__main__":
    main()
