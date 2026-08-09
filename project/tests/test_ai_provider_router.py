"""
project/tests/test_ai_provider_router.py
=========================================
Comprehensive Test Suite for AIProviderRouter & CODEX_CHATGPT Provider Integration.

Tests Requirements 19:
A. Codex available -> CODEX_CHATGPT used
B. Codex unavailable -> Gemini fallback
C. Codex not authenticated -> Gemini fallback
D. Codex command error -> Gemini fallback
E. Malformed Codex output -> Gemini fallback
F. No OpenAI API key is required for CODEX_CHATGPT
"""

import os
import pytest
from project.core.ai_provider_router import (
    AIProviderRouter,
    parse_codex_json_output,
    check_codex_installation,
    check_codex_authentication,
)


def test_provider_health_check():
    """Verify health check dictionary structure."""
    router = AIProviderRouter()
    health = router.get_provider_health()
    
    assert "CODEX_CHATGPT" in health
    assert "GEMINI" in health
    assert "routing" in health
    assert health["routing"]["primary"] == "codex_chatgpt"
    assert health["routing"]["fallback"] == "gemini"


def test_parse_codex_json_output_success():
    """Verify parsing agent_message from JSONL output."""
    raw_jsonl = (
        '{"type":"thread.started","thread_id":"123"}\n'
        '{"type":"turn.started"}\n'
        '{"type":"item.completed","item":{"id":"item_0","type":"agent_message","text":"CODEX_CHATGPT_OK"}}\n'
        '{"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":5}}\n'
    )
    content, raw_data, err = parse_codex_json_output(raw_jsonl)
    assert err is None
    assert content == "CODEX_CHATGPT_OK"
    assert raw_data["usage"]["input_tokens"] == 10


def test_parse_codex_json_output_malformed():
    """Verify handling of empty or invalid output (Test E)."""
    content, raw_data, err = parse_codex_json_output("")
    assert err == "malformed_response"
    assert content is None


def test_requirement_f_no_openai_api_key_required(monkeypatch):
    """Requirement F: No OPENAI_API_KEY or CODEX_PRO key is required for CODEX_CHATGPT."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CODEX_PRO", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("CODEX_PRO_BASE_URL", raising=False)

    router = AIProviderRouter()
    # Health check should not depend on API keys
    health = router.get_provider_health()
    assert health["CODEX_CHATGPT"]["installed"] is True


def test_requirement_a_codex_available_and_invoked(monkeypatch):
    """Requirement A: When Codex is available, CODEX_CHATGPT provider is used."""
    router = AIProviderRouter()
    
    # Mock invoke_codex_chatgpt to return success
    def mock_codex(*args, **kwargs):
        return {
            "status": "success",
            "provider": "CODEX_CHATGPT",
            "model": "codex_chatgpt",
            "content": "CODEX_CHATGPT_RESPONSE",
            "raw_response": None,
            "error_message": None,
            "error_type": None,
            "route_used": "codex_chatgpt",
        }
    
    monkeypatch.setattr(router, "invoke_codex_chatgpt", mock_codex)
    res = router.call_ai(prompt="Hello")
    assert res["status"] == "success"
    assert res["provider"] == "CODEX_CHATGPT"
    assert res["content"] == "CODEX_CHATGPT_RESPONSE"


def test_requirement_b_codex_unavailable_fallback(monkeypatch):
    """Requirement B: When Codex is unavailable, automatically fall back to Gemini."""
    router = AIProviderRouter(codex_cmd="non_existent_codex_bin_xyz")
    res = router.call_ai(prompt="Test prompt")
    
    assert res["status"] == "fallback"
    assert res["provider"] == "GEMINI"
    assert "not found" in res["error_message"].lower() or "unavailable" in res["error_message"].lower()


def test_requirement_c_codex_not_authenticated_fallback(monkeypatch):
    """Requirement C: When Codex is not authenticated, fall back to Gemini."""
    router = AIProviderRouter()
    
    def mock_auth(cmd):
        return False, "not_authenticated"
    
    monkeypatch.setattr("project.core.ai_provider_router.check_codex_authentication", mock_auth)
    res = router.call_ai(prompt="Test prompt")
    
    assert res["status"] == "fallback"
    assert res["provider"] == "GEMINI"
    assert "not_authenticated" in res["error_message"] or "login" in res["error_message"]


def test_requirement_d_codex_command_error_fallback(monkeypatch):
    """Requirement D: When Codex returns non-zero exit code / command error, fall back to Gemini."""
    router = AIProviderRouter()
    
    def mock_codex_fail(*args, **kwargs):
        return {
            "status": "error",
            "provider": "CODEX_CHATGPT",
            "model": "codex_chatgpt",
            "content": "",
            "raw_response": None,
            "error_message": "Codex CLI exited with code 1",
            "error_type": "execution_error",
            "route_used": "codex_chatgpt",
        }
        
    monkeypatch.setattr(router, "invoke_codex_chatgpt", mock_codex_fail)
    res = router.call_ai(prompt="Test prompt")
    
    assert res["status"] == "fallback"
    assert res["provider"] == "GEMINI"
    assert "exited with code 1" in res["error_message"]


def test_requirement_e_malformed_codex_output_fallback(monkeypatch):
    """Requirement E: When Codex output is malformed, fall back to Gemini."""
    router = AIProviderRouter()
    
    def mock_codex_malformed(*args, **kwargs):
        return {
            "status": "error",
            "provider": "CODEX_CHATGPT",
            "model": "codex_chatgpt",
            "content": "",
            "raw_response": None,
            "error_message": "Failed to parse agent response from Codex output.",
            "error_type": "malformed_response",
            "route_used": "codex_chatgpt",
        }
        
    monkeypatch.setattr(router, "invoke_codex_chatgpt", mock_codex_malformed)
    res = router.call_ai(prompt="Test prompt")
    
    assert res["status"] == "fallback"
    assert res["provider"] == "GEMINI"
    assert "malformed" in res["error_message"].lower() or "parse" in res["error_message"].lower()
