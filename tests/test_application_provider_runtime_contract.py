"""Black-box contract for the application Codex/Gemini inference chain."""

from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATHS = (
    ROOT / "project" / "api_router.py",
    ROOT / "project" / "core" / "llm_gateway.py",
    ROOT / "project" / "core" / "ai_provider_router.py",
)


def test_codex_provider_is_strict_read_only_and_parses_current_jsonl(monkeypatch) -> None:
    from project.core import codex_cli_provider as codex

    command = codex._build_command("codex1", "prompt")
    assert command[:2] == ["codex1", "exec"]
    assert command[command.index("-s") + 1] == "read-only"
    assert "--ephemeral" in command
    assert "--json" in command

    monkeypatch.setattr(codex.shutil, "which", lambda alias: f"/bin/{alias}")
    with pytest.raises(ValueError, match="unsupported Codex alias"):
        codex._resolve_alias("codex9")

    output = (
        '{"type":"thread.started","thread_id":"thread"}\n'
        '{"type":"item.completed","item":{"type":"agent_message","text":"answer"}}\n'
        '{"type":"turn.completed","usage":{"input_tokens":1,"output_tokens":1}}\n'
    )
    assert codex._parse_codex_jsonl(output) == "answer"


def test_codex_provider_does_not_expose_stderr(monkeypatch) -> None:
    from project.core import codex_cli_provider as codex

    monkeypatch.setattr(codex.shutil, "which", lambda _alias: "/bin/codex1")
    completed = SimpleNamespace(returncode=1, stdout="", stderr="sensitive-provider-output")
    with patch.object(codex.subprocess, "run", return_value=completed):
        with pytest.raises(RuntimeError) as error:
            codex.call_codex_cli("prompt", alias="codex1")
    assert "sensitive-provider-output" not in str(error.value)


def test_gemini_sdk_rotates_keys_and_returns_real_text() -> None:
    gemini = importlib.import_module("project.core.gemini_sdk_provider")
    calls: list[str] = []

    class Models:
        def __init__(self, key: str):
            self.key = key

        def generate_content(self, **_kwargs):
            calls.append(self.key)
            if self.key == "first-key":
                raise RuntimeError("quota")
            return SimpleNamespace(text="Gemini answer")

    def factory(key: str):
        return SimpleNamespace(models=Models(key))

    text, model = gemini.generate_with_gemini(
        "prompt",
        api_keys=["first-key", "second-key"],
        client_factory=factory,
    )
    assert text == "Gemini answer"
    assert model == gemini.DEFAULT_GEMINI_MODEL
    assert calls == ["first-key", "second-key"]

    with pytest.raises(gemini.GeminiSDKError, match="not configured"):
        gemini.generate_with_gemini("prompt", api_keys=[], client_factory=Mock())


def test_application_runtime_has_no_direct_compatible_endpoint() -> None:
    forbidden = (
        "api.openai.com",
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "_call_openai_compatible",
        "/chat/completions",
    )
    for path in RUNTIME_PATHS:
        source = path.read_text(encoding="utf-8")
        for marker in forbidden:
            assert marker not in source, f"{path.name} retains forbidden marker {marker}"


def test_public_admin_finetune_has_no_openai_provider_option() -> None:
    admin_source = (ROOT / "project" / "admin_router.py").read_text(encoding="utf-8")
    adapter_source = (ROOT / "project" / "rag" / "external_finetune.py").read_text(encoding="utf-8")
    assert "'openai'" not in admin_source
    assert '"openai"' not in admin_source
    assert "provider == \"openai\"" not in adapter_source
    assert "import openai" not in adapter_source


def test_shell_runners_do_not_export_compatible_endpoint_credentials() -> None:
    for relative in ("scripts/agentic_pipeline.sh", "scripts/hermes_sdlc_runner.sh"):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert "export OPENAI_BASE_URL" not in source
        assert "export OPENAI_API_KEY" not in source
        assert "CODEX_PRO_BASE_URL" not in source


def test_runtime_routers_wire_codex_then_gemini_then_deterministic(monkeypatch) -> None:
    api_router = importlib.import_module("project.api_router")
    gateway_module = importlib.import_module("project.core.llm_gateway")
    provider_module = importlib.import_module("project.core.ai_provider_router")

    monkeypatch.setattr(api_router, "check_codex_installation", lambda: True)
    monkeypatch.setattr(api_router, "_gemini_keys", lambda: ["gemini-key"])
    route_types = [route["type"] for route in api_router.HybridRouter()._build_routes()]
    assert "codex_cli" in route_types
    assert "gemini" in route_types
    assert "openai" not in route_types

    gateway = gateway_module.LLMGateway()
    assert "codex" in gateway.providers
    assert "gemini" in gateway.providers
    assert "deterministic" in gateway.providers
    assert "openai" not in gateway.providers

    health = provider_module.AIProviderRouter().get_provider_health()
    assert "CODEX_CHATGPT" in health
    assert "GEMINI" in health
    assert "DETERMINISTIC_SAFE_NET" in health
    assert "REASONING_PROXY" not in health


def test_hf_without_codex_still_builds_gemini_route(monkeypatch) -> None:
    api_router = importlib.import_module("project.api_router")
    monkeypatch.setattr(api_router, "check_codex_installation", lambda: False)
    monkeypatch.setattr(api_router, "_gemini_keys", lambda: ["gemini-key"])
    monkeypatch.setenv("SPACE_ID", "owner/space")

    route_types = [route["type"] for route in api_router.HybridRouter()._build_routes()]

    assert "codex_cli" not in route_types
    assert "gemini" in route_types
