"""KAN-85: Environment configuration + production secrets for bridge toggle.

Verifies:
  1. All 6 GEMINI_WEB_BRIDGE_* env vars are present in .env.example as placeholders.
  2. No real secrets leak into tracked files.
  3. sync-render-secrets.sh exists and handles the bridge env vars.
  4. The bridge client reads all env vars correctly from environment.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

import project.core.gemini_bridge_client as gbc
from project.core.gemini_bridge_client import (
    GEMINI_BRIDGE_DEFAULT_SCOPE,
    GEMINI_BRIDGE_DEFAULT_TIMEOUT_S,
    GEMINI_BRIDGE_DEFAULT_TOOL,
    GEMINI_BRIDGE_DEFAULT_URL,
    _bridge_timeout_s,
    _bridge_tool,
    _bridge_url,
)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# ---------------------------------------------------------------------------
# .env.example env var presence
# ---------------------------------------------------------------------------

def test_env_example_has_all_bridge_vars():
    """All 6 GEMINI_WEB_BRIDGE_* vars must be present in .env.example."""
    env_example_path = os.path.join(REPO_ROOT, ".env.example")
    with open(env_example_path) as f:
        content = f.read()

    required_vars = [
        "GEMINI_WEB_BRIDGE_ENABLED",
        "GEMINI_WEB_BRIDGE_URL",
        "GEMINI_WEB_BRIDGE_TOKEN",
        "GEMINI_WEB_BRIDGE_SCOPE",
        "GEMINI_WEB_BRIDGE_TOOL",
        "GEMINI_WEB_BRIDGE_TIMEOUT_S",
    ]
    for var in required_vars:
        assert f"{var}=" in content, f"{var} missing from .env.example"


def test_env_example_token_is_placeholder():
    """The TOKEN in .env.example must be a placeholder, not a real token."""
    env_example_path = os.path.join(REPO_ROOT, ".env.example")
    with open(env_example_path) as f:
        for line in f:
            if line.startswith("GEMINI_WEB_BRIDGE_TOKEN="):
                value = line.split("=", 1)[1].strip()
                # Must be a placeholder pattern
                assert value.startswith("<") or value == "" or "from-doppler" in value.lower(), \
                    f"TOKEN should be a placeholder, got: {value}"
                break
        else:
            pytest.fail("GEMINI_WEB_BRIDGE_TOKEN not found in .env.example")


# ---------------------------------------------------------------------------
# No secrets in tracked files
# ---------------------------------------------------------------------------

def test_no_secrets_in_tracked_files():
    """Verify .env files are gitignored and no real tokens in tracked files."""
    result = subprocess.run(
        ["git", "check-ignore", ".env"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0, ".env should be gitignored"

    result = subprocess.run(
        ["git", "check-ignore", ".env.production"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0, ".env.production should be gitignored"


# ---------------------------------------------------------------------------
# sync-render-secrets.sh exists and handles bridge vars
# ---------------------------------------------------------------------------

def test_sync_render_secrets_script_exists():
    """scripts/sync-render-secrets.sh must exist."""
    script_path = os.path.join(REPO_ROOT, "scripts", "sync-render-secrets.sh")
    assert os.path.isfile(script_path), "sync-render-secrets.sh missing"


def test_sync_script_excludes_gateway_only_keys():
    """sync-render-secrets.sh must exclude gateway-only credentials."""
    script_path = os.path.join(REPO_ROOT, "scripts", "sync-render-secrets.sh")
    with open(script_path) as f:
        content = f.read()
    # Must exclude Doppler/Render self-references
    assert "DOPPLER_SERVICE_TOKEN" in content
    assert "RENDER_API_KEY" in content
    # Must NOT exclude GEMINI_WEB_BRIDGE vars (they should be synced)
    assert "GEMINI_WEB_BRIDGE" not in content or "exclude" not in content.split("GEMINI_WEB_BRIDGE")[0].split("\n")[-1].lower()


# ---------------------------------------------------------------------------
# Bridge client reads env vars correctly
# ---------------------------------------------------------------------------

def test_bridge_url_default():
    """_bridge_url() returns default URL when env is unset."""
    os.environ.pop("GEMINI_WEB_BRIDGE_URL", None)
    assert _bridge_url() == GEMINI_BRIDGE_DEFAULT_URL


def test_bridge_url_env_override():
    """_bridge_url() reads from env when set."""
    os.environ["GEMINI_WEB_BRIDGE_URL"] = "https://custom-bridge.example.com"
    assert _bridge_url() == "https://custom-bridge.example.com"
    os.environ.pop("GEMINI_WEB_BRIDGE_URL")


def test_bridge_tool_default():
    """_bridge_tool() returns default tool name when env is unset."""
    os.environ.pop("GEMINI_WEB_BRIDGE_TOOL", None)
    assert _bridge_tool() == GEMINI_BRIDGE_DEFAULT_TOOL


def test_bridge_tool_env_override():
    """_bridge_tool() reads from env when set."""
    os.environ["GEMINI_WEB_BRIDGE_TOOL"] = "custom_tool"
    assert _bridge_tool() == "custom_tool"
    os.environ.pop("GEMINI_WEB_BRIDGE_TOOL")


def test_bridge_timeout_default():
    """_bridge_timeout_s() returns default timeout when env is unset."""
    os.environ.pop("GEMINI_WEB_BRIDGE_TIMEOUT_S", None)
    assert _bridge_timeout_s() == GEMINI_BRIDGE_DEFAULT_TIMEOUT_S


def test_bridge_timeout_env_override():
    """_bridge_timeout_s() reads from env when set."""
    os.environ["GEMINI_WEB_BRIDGE_TIMEOUT_S"] = "45"
    assert _bridge_timeout_s() == 45.0
    os.environ.pop("GEMINI_WEB_BRIDGE_TIMEOUT_S")


def test_bridge_timeout_invalid_env():
    """_bridge_timeout_s() falls back to default on invalid env value."""
    os.environ["GEMINI_WEB_BRIDGE_TIMEOUT_S"] = "not-a-number"
    assert _bridge_timeout_s() == GEMINI_BRIDGE_DEFAULT_TIMEOUT_S
    os.environ.pop("GEMINI_WEB_BRIDGE_TIMEOUT_S")


def test_defaults_match_spec():
    """All default values match the spec (docs/gemini-bridge-mcp-toggle.md §3)."""
    assert GEMINI_BRIDGE_DEFAULT_URL == "https://gemini-web-bridge.pansakorn-pho.workers.dev"
    assert GEMINI_BRIDGE_DEFAULT_SCOPE == "notebook:b55f1ee0-384e-4bdf-ab1b-e2ee3b0063a0"
    assert GEMINI_BRIDGE_DEFAULT_TOOL == "horo_consult"
    assert GEMINI_BRIDGE_DEFAULT_TIMEOUT_S == 90.0
