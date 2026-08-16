#!/usr/bin/env python3
"""
scripts/hermes_agy_router.py
============================
Resolve AGY routing target from `.agents/config/gemini_parity.yaml`.

This helper is used by shell runners so model + account alias can be selected by:
- role: analysis / implementation / review
- complexity: low / medium / high
with fallback chain metadata.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, Tuple

try:
    import yaml  # type: ignore
    _HAS_YAML = True
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore
    _HAS_YAML = False


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT_DIR / ".agents" / "config" / "gemini_parity.yaml"


def _default_config() -> Dict[str, Any]:
    return {
        "agy_routing": {
            "agents": [
                {
                    "name": "agy1",
                    "routing": {
                        "analysis": {
                            "low": {"model": "Gemini 3.5 Flash Medium Fast O", "time": "fast"},
                            "medium": {"model": "Gemini 3.6 Flash Medium Fast O", "time": "medium"},
                            "high": {"model": "Gemini 3.7 Flash Medium Fast O", "time": "medium"},
                        },
                        "implementation": {
                            "low": {"model": "Gemini 3.6 Flash Medium Fast O", "time": "fast"},
                            "medium": {"model": "Gemini 3.7 Flash Medium Fast O", "time": "medium"},
                            "high": {"model": "GPT-OSS 120B (Medium)", "time": "medium"},
                        },
                        "review": {
                            "low": {"model": "Gemini 3.5 Flash Medium Fast O", "time": "fast"},
                            "medium": {"model": "Claude Sonnet 4.6 (Thinking)", "time": "medium"},
                            "high": {"model": "Claude Opus 4.6 (Thinking)", "time": "high"},
                        },
                    },
                },
                {
                    "name": "agy2",
                    "routing": {
                        "analysis": {
                            "low": {"model": "Gemini 3.5 Flash Medium Fast O", "time": "fast"},
                            "medium": {"model": "Gemini 3.6 Flash Medium Fast O", "time": "medium"},
                            "high": {"model": "Claude Sonnet 4.6 (Thinking)", "time": "high"},
                        },
                        "implementation": {
                            "low": {"model": "Gemini 3.6 Flash Medium Fast O", "time": "fast"},
                            "medium": {"model": "GPT-OSS 120B (Medium)", "time": "medium"},
                            "high": {"model": "Claude Opus 4.6 (Thinking)", "time": "high"},
                        },
                        "review": {
                            "low": {"model": "Gemini 3.6 Flash Medium Fast O", "time": "fast"},
                            "medium": {"model": "Claude Sonnet 4.6 (Thinking)", "time": "medium"},
                            "high": {"model": "Claude Opus 4.6 (Thinking)", "time": "high"},
                        },
                    },
                },
            ],
            "fallback_chain": {
                "sequence": ["agy1", "agy2", "codex_subagent"],
                "codex_fallback": {
                    "via": "CODEX_PRO",
                    "model": "gpt-5.3-codex-spark high",
                },
            },
            "roles": {
                "analysis": {
                    "low": {"model": "Gemini 3.5 Flash Medium Fast O", "time": "fast"},
                    "medium": {"model": "Gemini 3.6 Flash Medium Fast O", "time": "medium"},
                    "high": {"model": "Gemini 3.7 Flash Medium Fast O", "time": "medium"},
                },
                "implementation": {
                    "low": {"model": "Gemini 3.6 Flash Medium Fast O", "time": "fast"},
                    "medium": {"model": "Gemini 3.7 Flash Medium Fast O", "time": "medium"},
                    "high": {"model": "GPT-OSS 120B (Medium)", "time": "medium"},
                },
                "review": {
                    "low": {"model": "Gemini 3.5 Flash Medium Fast O", "time": "fast"},
                    "medium": {"model": "Claude Sonnet 4.6 (Thinking)", "time": "medium"},
                    "high": {"model": "Claude Opus 4.6 (Thinking)", "time": "high"},
                },
            },
        }
    }


def _normalize_role(value: str) -> str:
    return (value or "").strip().lower()


def _normalize_complexity(value: str) -> str:
    normalized = (value or "").strip().lower()
    if normalized in {"low", "medium", "high"}:
        return normalized
    return "medium"


def _build_agent_map(agy_routing: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    agents = {}
    for agent in agy_routing.get("agents", []):
        if isinstance(agent, dict):
            name = str(agent.get("name", "")).strip()
            if name:
                agents[name] = agent
    return agents


def _load_yaml_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return _default_config()

    if not _HAS_YAML:
        return _default_config()

    try:
        with path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
            if isinstance(loaded, dict):
                return loaded
    except Exception:
        return _default_config()

    return _default_config()


def resolve_hermes_route(
    config_path: Path,
    account_alias: str,
    role: str,
    complexity: str,
) -> Tuple[str, str, str, str, str, str, str]:
    config = _load_yaml_config(config_path)
    routing = config.get("agy_routing", {})
    if not isinstance(routing, dict):
        routing = {}

    agents = _build_agent_map(routing)
    fallback_chain = routing.get("fallback_chain", {})
    if not isinstance(fallback_chain, dict):
        fallback_chain = {}
    seq = fallback_chain.get("sequence", []) if isinstance(fallback_chain, dict) else []
    if not isinstance(seq, list) or not seq:
        seq = ["agy1", "agy2", "codex_subagent"]
    fallback_chain_csv = ",".join(str(item) for item in seq)

    role_key = _normalize_role(role)
    if role_key not in {"analysis", "implementation", "review"}:
        role_key = "implementation"
    complexity_key = _normalize_complexity(complexity)

    alias = account_alias or "agy1"
    selected_alias = alias if alias in agents else "agy1"

    role_config = {}
    if selected_alias in agents:
        selected = agents[selected_alias]
        role_config = selected.get("routing", {}).get(role_key, {})
    if not isinstance(role_config, dict) or not role_config:
        role_config = routing.get("roles", {}).get(role_key, {})

    if not isinstance(role_config, dict):
        role_config = {}

    selected_slot = role_config.get(complexity_key) if isinstance(role_config, dict) else None
    if not isinstance(selected_slot, dict):
        selected_slot = role_config.get("medium", {})

    model = str(selected_slot.get("model", "deepseek-v3"))
    time_label = str(selected_slot.get("time", "medium"))
    if not model:
        model = "deepseek-v3"
    if not time_label:
        time_label = "medium"

    codex_fallback = fallback_chain.get("codex_fallback", {})
    if not isinstance(codex_fallback, dict):
        codex_fallback = {}
    codex_fallback_model = str(codex_fallback.get("model", "gpt-5.3-codex-spark high"))
    if not codex_fallback_model:
        codex_fallback_model = "gpt-5.3-codex-spark high"

    return (
        selected_alias,
        role_key,
        complexity_key,
        model,
        time_label,
        fallback_chain_csv,
        codex_fallback_model,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve Hermes AGY routing target.")
    parser.add_argument("--alias", default="agy1")
    parser.add_argument("--role", default="analysis")
    parser.add_argument("--complexity", default="high")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    args = parser.parse_args()

    (
        resolved_alias,
        resolved_role,
        resolved_complexity,
        model,
        time_label,
        fallback_chain,
        codex_fallback_model,
    ) = resolve_hermes_route(
        config_path=Path(args.config),
        account_alias=args.alias,
        role=args.role,
        complexity=args.complexity,
    )

    # shell-safe delimiter output for downstream scripts.
    # Format: model|time|alias|fallback_chain
    print(
        f"{model}|{time_label}|{resolved_alias}|{fallback_chain}|"
        f"{resolved_role}|{resolved_complexity}|{codex_fallback_model}"
    )


if __name__ == "__main__":
    main()
