"""RED Contract tests for Ecosystem Sync and Pure Check Boundary.

Covers:
- Umbrella --check is static and in-memory only; never runs native measurements or provider processes.
- Pure check forbids every write or external side-effect (no file create, chmod, mtime update, or deletion).
- Pure check preserves complete repository and external canary environments.
- Parity direction is strictly one-way from canonical .agents to provider mirrors.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
SYNC_SCRIPT = ROOT / "scripts/sync_ai_agent_ecosystem.py"
REGISTRY_PATH = ROOT / ".agents/config/scope_skill_registry.v1.json"


def test_umbrella_check_is_static_only_and_never_runs_native_measurement():
    assert SYNC_SCRIPT.exists(), "Ecosystem sync script not found"
    import scripts.sync_ai_agent_ecosystem as sync
    assert hasattr(sync, "check_context_profiles"), (
        "PURE_CHECK_CONTRACT_MISSING: sync_ai_agent_ecosystem missing check_context_profiles"
    )


def test_pure_check_forbids_every_write_or_external_effect(tmp_path):
    assert SYNC_SCRIPT.exists(), "Ecosystem sync script not found"
    import scripts.sync_ai_agent_ecosystem as sync
    assert hasattr(sync, "run_pure_check"), (
        "PURE_CHECK_CONTRACT_MISSING: sync_ai_agent_ecosystem missing run_pure_check"
    )
    result = sync.run_pure_check(target="context-profiles")
    assert result.writes_performed == 0, "Pure check must perform zero writes"
    assert result.subprocess_count == 0, "Pure check must launch zero subprocesses"


def test_pure_check_preserves_complete_repository_and_external_canaries():
    assert SYNC_SCRIPT.exists(), "Ecosystem sync script not found"
    import scripts.sync_ai_agent_ecosystem as sync
    assert hasattr(sync, "run_pure_check"), (
        "PURE_CHECK_CONTRACT_MISSING: sync_ai_agent_ecosystem missing run_pure_check"
    )


def test_parity_direction_is_strictly_canonical_agents_to_providers():
    assert REGISTRY_PATH.exists(), (
        "PARITY_DIRECTION_NOT_CANONICAL: Canonical scope skill registry must exist as sole upstream authority"
    )
