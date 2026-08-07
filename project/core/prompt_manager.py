"""
project/core/prompt_manager.py — Externalized YAML Prompt Loader Utility
Computational Metaphysics Engine
"""

from __future__ import annotations

import os
import yaml
from functools import lru_cache
from typing import Dict, Any, Optional

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "prompts")


class PromptManager:
    """
    Centralized loader for YAML system prompts.
    Provides fast cached retrieval and dynamic template formatting.
    """

    def __init__(self, config_dir: str = CONFIG_DIR):
        self.config_dir = config_dir

    @lru_cache(maxsize=16)
    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        path = os.path.join(self.config_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Prompt configuration file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def get_domain_prompt(self, domain_key: str) -> Dict[str, Any]:
        """Fetch system prompt configuration for a specific domain master."""
        data = self._load_yaml("domain_agents.yaml")
        if domain_key not in data:
            raise KeyError(f"Domain prompt key '{domain_key}' not found in domain_agents.yaml")
        return data[domain_key]

    def get_debate_prompt(self, key: str = "debate_orchestrator") -> Dict[str, Any]:
        """Fetch system prompt for debate orchestrator."""
        data = self._load_yaml("debate_orchestration.yaml")
        if key not in data:
            raise KeyError(f"Debate prompt key '{key}' not found in debate_orchestration.yaml")
        return data[key]


# Singleton instance
prompt_manager = PromptManager()
