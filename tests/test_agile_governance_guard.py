"""Frozen fail-closed contract for GOV-M5 Agile governance artifacts.

This QA baseline intentionally targets files owned by later implementation
lanes.  It does not open providers, keychains, or network connections.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ".agents/config/native_lane_capacity.v1.json"
HOOK_PATH = ".agents/hooks/agile_governance_guard.py"
RULE_PATH = ".agents/rules/21-agile-governance.md"
SKILL_PATH = ".agents/skills/agile-governance/SKILL.md"
ORCHESTRATOR_PATH = ".agents/agents/orchestrator/agent.json"
ANALYST_PATH = ".agents/agents/business_analyst/agent.json"
TARGET_PATHS = (
    CONFIG_PATH,
    HOOK_PATH,
    RULE_PATH,
    SKILL_PATH,
    ORCHESTRATOR_PATH,
    ANALYST_PATH,
)

# This is fixture metadata, not provider/quota proof and not a policy default.
CURRENT_RUNTIME_FIXTURE = {
    "native_platform": {
        "admitted_concurrent_lanes": 6,
        "rejected_lane": 7,
        "rejection_reason": "agent thread limit",
        "release_and_refill": "successful",
    },
    "host": {"cpu_count": 10, "memory_gib": 16, "memory_free_percent": 76},
}


def _missing_targets() -> list[str]:
    return [path for path in TARGET_PATHS if not (ROOT / path).is_file()]


def _require_targets() -> None:
    missing = _missing_targets()
    if missing:
        pytest.skip("GOV_M5_002_SOURCE_MISSING: " + ", ".join(missing))


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return " ".join(text.lower().replace("_", " ").replace("-", " ").split())


def _require_terms(text: str, *terms: str) -> None:
    normalized = _normalized(text)
    absent = [term for term in terms if _normalized(term) not in normalized]
    assert not absent, f"missing governance terms: {absent}"


def test_governance_source_contract_exists() -> None:
    """The bounded implementation surface must exist before it can claim compliance."""
    assert not _missing_targets(), "GOV_M5_002_SOURCE_MISSING: " + ", ".join(_missing_targets())


def test_native_runtime_observation_is_not_provider_capacity() -> None:
    """Observed native slots are a configurable safety ceiling, never quota proof."""
    _require_targets()
    config = json.loads(_text(CONFIG_PATH))
    assert config["schema_version"] == "native-lane-capacity-v1"
    normalized = _normalized(json.dumps(config, sort_keys=True))
    _require_terms(
        normalized,
        "runtime observed",
        "theoretical capacity",
        "provider capacity",
        "configurable safety cap",
        "native observed ceiling",
    )
    # The current machine evidence remains test-fixture-only, never config truth.
    assert "memory free percent" not in normalized
    assert "agent thread limit" not in normalized


def test_agy_pools_are_independent_and_unknown_without_fresh_proof() -> None:
    _require_targets()
    policy = "\n".join(_text(path) for path in (HOOK_PATH, RULE_PATH, SKILL_PATH))
    _require_terms(
        policy,
        "agy per alias cap 3",
        "independent pools",
        "no aggregation",
        "alias unknown",
        "fresh quota proof",
        "isolation proof",
    )


def test_atomic_ticket_lifecycle_and_editor_ownership_are_fail_closed() -> None:
    _require_targets()
    policy = "\n".join(_text(path) for path in (HOOK_PATH, RULE_PATH, SKILL_PATH))
    _require_terms(
        policy,
        "TODO",
        "READY",
        "DOING",
        "BLOCKED",
        "NEEDS HITL",
        "DONE",
        "one editor per resource",
        "dependency",
        "definition of ready",
        "definition of done",
        "no fake full capacity busywork",
        "capacity exception",
    )


def test_hook_exposes_typed_capacity_failure_and_separates_admission_execution() -> None:
    _require_targets()
    hook = _text(HOOK_PATH)
    _require_terms(
        hook,
        "class AgileGovernanceCapacityError",
        "admission",
        "execution proof",
        "fail closed",
        "not proven",
    )


def test_agents_bind_their_governance_responsibilities() -> None:
    _require_targets()
    orchestrator = json.loads(_text(ORCHESTRATOR_PATH))
    analyst = json.loads(_text(ANALYST_PATH))
    assert isinstance(orchestrator.get("system_prompt"), str)
    assert isinstance(analyst.get("system_prompt"), str)
    _require_terms(
        orchestrator["system_prompt"],
        "agile governance",
        "capacity exception",
        "one editor per resource",
    )
    _require_terms(
        analyst["system_prompt"],
        "agile governance",
        "definition of ready",
        "definition of done",
        "dependency",
    )


def test_policy_artifacts_cannot_contain_secret_or_keychain_material() -> None:
    _require_targets()
    forbidden = ("keychain", "authorization:", "bearer ", "api_key", "token=", "secret=")
    for path in TARGET_PATHS:
        content = _text(path).lower()
        leaked = [needle for needle in forbidden if needle in content]
        assert not leaked, f"{path} contains forbidden secret/keychain material: {leaked}"
