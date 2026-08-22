"""
project/tests/test_codex_client.py
==================================
Unit tests for project/core/codex_client.py
Verifies Dev Environment scoping guard, native codex auth file / Doppler resolution,
env variable cancellation policy, and dynamic fallback behavior.
"""

import os
from project.core.codex_client import is_dev_environment, call_codex_api, get_codex_auth_token


def _force_local_dev_environment(monkeypatch):
    """Ensure tests run in local-dev guard mode for deterministic assertions."""
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("SPACE_ID", raising=False)
    monkeypatch.delenv("FLY_APP_NAME", raising=False)


def test_is_dev_environment(monkeypatch):
    # In test suite running locally, should return True
    _force_local_dev_environment(monkeypatch)
    assert is_dev_environment() is True


def test_call_codex_api_fallback_without_auth(monkeypatch):
    # When no auth is present, call_codex_api should safely fallback to Gemini
    _force_local_dev_environment(monkeypatch)
    res = call_codex_api(prompt="Write a Python function to calculate BaZi 4 Pillars")
    assert res["status"] in ("success", "fallback")
    assert "content" in res
    assert res["content"] != ""


def test_env_var_cancellation_policy(monkeypatch):
    # Environment variables CODEX_PRO / OPENAI_API_KEY are ignored by get_codex_auth_token
    monkeypatch.setenv("CODEX_PRO", "dummy_env_key")
    monkeypatch.setenv("OPENAI_API_KEY", "dummy_openai_key")
    monkeypatch.delenv("DOPPLER_TOKEN", raising=False)
    
    # Unless ~/.codex/auth.json exists, get_codex_auth_token should return None
    # enforcing cancellation of env vars
    token = get_codex_auth_token()
    # Should not resolve to raw env var dummy_env_key
    assert token != "dummy_env_key"


def test_call_codex_api_prod_safety_guard(monkeypatch):
    # Simulate Vercel production environment
    monkeypatch.setenv("VERCEL", "1")
    assert is_dev_environment() is False
    
    res = call_codex_api(prompt="Test code generation")
    assert res["status"] == "error"
    assert "Production environment safety guard" in res["error_message"]
