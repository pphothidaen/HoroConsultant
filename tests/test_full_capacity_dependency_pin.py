"""Ensure the guarded dispatcher pin matches the committed validator."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from importlib.util import module_from_spec, spec_from_file_location


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".agents" / "config" / "full_capacity_guard.v2.json"
HOOK = ROOT / ".agents" / "hooks" / "full_capacity_guard.py"
DISPATCHER = ROOT / "scripts" / "multiagent_prompt_command.py"


def _load_guard():
    spec = spec_from_file_location("full_capacity_guard_dependency_pin", HOOK)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_full_capacity_dispatcher_pin_matches_current_dispatcher() -> None:
    digest = hashlib.sha256(DISPATCHER.read_bytes()).hexdigest()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    guard = _load_guard()
    assert config["dependency_pins"]["dispatcher_validator"]["sha256"] == digest
    assert guard.EXPECTED_DEPENDENCY_PINS["dispatcher_validator"]["sha256"] == digest
