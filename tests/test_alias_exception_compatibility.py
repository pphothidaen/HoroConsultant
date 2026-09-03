"""Keep expanded account routing separate from closed safety exceptions."""

from __future__ import annotations

import json
from pathlib import Path

from scripts import multiagent_prompt_command as command


ROOT = Path(__file__).resolve().parents[1]
FULL_CAPACITY_CONFIG = ROOT / ".agents" / "config" / "full_capacity_guard.v2.json"


def test_full_capacity_config_matches_the_guarded_agy_alias_set() -> None:
    config = json.loads(FULL_CAPACITY_CONFIG.read_text(encoding="utf-8"))
    assert config["provider_aliases"] == ["agy1", "agy2"]


def test_idq_mvp_080_remains_the_closed_four_alias_exception() -> None:
    assert command._IDQ_MVP_080_ALIASES == {
        "codex1": "codex",
        "codex2": "codex",
        "agy1": "agy",
        "agy2": "agy",
    }
