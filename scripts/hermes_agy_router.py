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

# ── SDLC Phase → (role, complexity, account) hardcoded defaults ──────────────
# Mirrors sdlc_phases section in gemini_parity.yaml. Used when --phase is given
# instead of --role + --complexity to avoid per-script complexity management.
SDLC_PHASE_MAP: Dict[str, Dict[str, str]] = {
    "bsa":          {"role": "analysis",       "complexity": "low",    "account": "agy1"},
    "dev":          {"role": "implementation",  "complexity": "medium", "account": "agy2"},
    "qa":           {"role": "review",          "complexity": "low",    "account": "agy1"},
    "reviewer":     {"role": "review",          "complexity": "low",    "account": "agy1"},
    "devops":       {"role": "implementation",  "complexity": "medium", "account": "agy1"},
    "orchestrator": {"role": "analysis",        "complexity": "high",   "account": "agy1"},
}


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
                            "high": {"model": "Gemini 3.7 Flash Medium Fast O", "time": "medium"},  # v2.1: was GPT-OSS
                        },
                        "review": {
                            "low": {"model": "Gemini 3.5 Flash Medium Fast O", "time": "fast"},
                            "medium": {"model": "Gemini 3.7 Flash Medium Fast O", "time": "medium"},
                            "high": {"model": "Claude Opus 4.6 (Thinking)", "time": "high"},  # sole Claude slot
                        },
                    },
                },
                {
                    "name": "agy2",
                    "routing": {
                        "analysis": {
                            "low": {"model": "Gemini 3.5 Flash Medium Fast O", "time": "fast"},
                            "medium": {"model": "Gemini 3.6 Flash Medium Fast O", "time": "medium"},
                            "high": {"model": "Gemini 3.7 Flash Medium Fast O", "time": "medium"},
                        },
                        "implementation": {
                            "low": {"model": "Gemini 3.6 Flash Medium Fast O", "time": "fast"},
                            "medium": {"model": "Gemini 3.7 Flash Medium Fast O", "time": "medium"},  # v2.1: was GPT-OSS
                            "high": {"model": "Gemini 3.7 Flash Medium Fast O", "time": "medium"},    # v2.1: was GPT-OSS
                        },
                        "review": {
                            "low": {"model": "Gemini 3.6 Flash Medium Fast O", "time": "fast"},
                            "medium": {"model": "Gemini 3.7 Flash Medium Fast O", "time": "medium"},
                            "high": {"model": "Gemini 3.7 Flash Medium Fast O", "time": "medium"},   # v2.1: was GPT-OSS
                        },
                    },
                },
                {
                    "name": "agy3",
                    "routing": {
                        "analysis": {
                            "low": {"model": "Gemini 3.5 Flash Medium Fast O", "time": "fast"},
                            "medium": {"model": "Gemini 3.6 Flash Medium Fast O", "time": "medium"},
                            "high": {"model": "Gemini 3.7 Flash Medium Fast O", "time": "medium"},
                        },
                        "implementation": {
                            "low": {"model": "Gemini 3.6 Flash Medium Fast O", "time": "fast"},
                            "medium": {"model": "Gemini 3.6 Flash Medium Fast O", "time": "medium"},
                            "high": {"model": "Gemini 3.7 Flash Medium Fast O", "time": "medium"},
                        },
                        "review": {
                            "low": {"model": "Gemini 3.5 Flash Medium Fast O", "time": "fast"},
                            "medium": {"model": "Gemini 3.6 Flash Medium Fast O", "time": "medium"},
                            "high": {"model": "Gemini 3.7 Flash Medium Fast O", "time": "medium"},
                        },
                    },
                },
            ],
            "fallback_chain": {
                "sequence": ["agy1", "agy2", "agy3", "codex_subagent"],
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
                    "high": {"model": "Gemini 3.7 Flash Medium Fast O", "time": "medium"},   # v2.1: was GPT-OSS
                },
                "review": {
                    "low": {"model": "Gemini 3.5 Flash Medium Fast O", "time": "fast"},
                    "medium": {"model": "Gemini 3.7 Flash Medium Fast O", "time": "medium"},
                    "high": {"model": "Claude Opus 4.6 (Thinking)", "time": "high"},          # sole Claude slot
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


def _resolve_phase_profile(
    phase: str,
    config_path: Path,
) -> tuple[str, str, str]:
    """Resolve (role, complexity, account_alias) for a given SDLC phase name.

    Priority:
      1. sdlc_phases section in gemini_parity.yaml (YAML overrides built-in)
      2. SDLC_PHASE_MAP built-in defaults
    """
    phase_key = phase.strip().lower()

    # Try loading from YAML sdlc_phases section first
    config = _load_yaml_config(config_path)
    yaml_phases = config.get("sdlc_phases", {})
    if isinstance(yaml_phases, dict) and phase_key in yaml_phases:
        phase_cfg = yaml_phases[phase_key]
        if isinstance(phase_cfg, dict):
            role = str(phase_cfg.get("role", "analysis"))
            complexity = str(phase_cfg.get("complexity", "medium"))
            account = str(phase_cfg.get("account", "agy1"))
            return role, complexity, account

    # Fall back to built-in SDLC_PHASE_MAP
    if phase_key in SDLC_PHASE_MAP:
        pm = SDLC_PHASE_MAP[phase_key]
        return pm["role"], pm["complexity"], pm["account"]

    # Unknown phase — safe default (analysis/low on agy1 = cheapest Gemini)
    return "analysis", "low", "agy1"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resolve Hermes AGY routing target.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
SDLC Phase shortcuts (--phase overrides --role/--complexity/--alias):
  bsa          analysis/low/agy1   → Gemini 3.5 Flash (fast)
  dev          implementation/medium/agy2 → GPT-OSS 120B
  qa           review/low/agy1     → Gemini 3.5 Flash (fast)
  reviewer     review/low/agy1     → Gemini 3.5 Flash (fast)
  devops       implementation/medium/agy1 → Gemini 3.7 Flash
  orchestrator analysis/high/agy1  → Gemini 3.7 Flash
""",
    )
    parser.add_argument("--alias", default="agy1", help="AGY account alias (overridden by --phase)")
    parser.add_argument("--role", default="analysis", help="Task role: analysis/implementation/review")
    parser.add_argument("--complexity", default="high", help="Task complexity: low/medium/high")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument(
        "--phase",
        default="",
        help="SDLC phase shortcut: bsa/dev/qa/reviewer/devops/orchestrator. "
             "Overrides --role, --complexity, and --alias.",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    alias = args.alias
    role = args.role
    complexity = args.complexity

    # --phase takes priority — resolve role/complexity/alias from phase map
    if args.phase:
        role, complexity, alias = _resolve_phase_profile(args.phase, config_path)

    (
        resolved_alias,
        resolved_role,
        resolved_complexity,
        model,
        time_label,
        fallback_chain,
        codex_fallback_model,
    ) = resolve_hermes_route(
        config_path=config_path,
        account_alias=alias,
        role=role,
        complexity=complexity,
    )

    # shell-safe delimiter output for downstream scripts.
    # Format: model|time|alias|fallback_chain|role|complexity|codex_fallback_model
    print(
        f"{model}|{time_label}|{resolved_alias}|{fallback_chain}|"
        f"{resolved_role}|{resolved_complexity}|{codex_fallback_model}"
    )


if __name__ == "__main__":
    main()
