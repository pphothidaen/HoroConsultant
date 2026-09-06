"""Comprehensive unit and integration test suite for Fail-Closed Quota Guard V3.

Covers all 69 test cases (TC-01 through TC-69), 8-rank precedence hierarchy,
4-tier quota scale (GREEN, AMBER, ORANGE, RED), pool isolation, two-phase
concurrency control, QuotaCollector, and QuotaGuardVerdictV3.3 schema conformance
as defined in resume_plan.md (Revision 3.4).

Pure ASCII formatting enforced.
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

import jsonschema
from jsonschema import Draft202012Validator
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
GUARD_SCRIPT = ROOT / "scripts" / "agent_quota_status_guard.py"
FIXTURES_DIR = ROOT / "tests" / "fixtures" / "quota"

# Expected Definitive Exit Code Map as specified in resume_plan.md lines 89-152
EXPECTED_EXIT_CODE_MAP = {
    # Exit Code 1: Quota Exhausted, Rate Limit, or Concurrency / Rank Ceilings
    "QUOTA_DEPLETED": 1,
    "RATE_LIMIT_ACTIVE": 1,
    "CONCURRENCY_LIMIT_REACHED": 1,
    "LANE_RANK_DISALLOWED_IN_AMBER": 1,
    "LANE_NOT_ALLOWED_IN_ORANGE": 1,
    "HOST_QUOTA_INSUFFICIENT": 1,

    # Exit Code 2: Admission Failed, Policy Unapproved, Malformed, Expired
    "POLICY_NOT_APPROVED": 2,
    "POLICY_MALFORMED": 2,
    "SOURCE_ADMISSION_FAILED": 2,
    "CANONICAL_HANDOFF_INVALID": 2,
    "LANE_READINESS_FAILED": 2,
    "OPERATOR_AUTHORIZATION_MISSING": 2,
    "OPERATOR_AUTHORIZATION_INVALID": 2,
    "OPERATOR_AUTHORIZATION_EXPIRED": 2,
    "OPERATOR_AUTHORIZATION_REVOKED": 2,
    "OPERATOR_AUTHORIZATION_SCOPE_MISMATCH": 2,
    "ADMISSION_EVIDENCE_MISSING": 2,
    "ADMISSION_EVIDENCE_INVALID": 2,
    "ADMISSION_EVIDENCE_EXPIRED": 2,
    "VERDICT_LIFETIME_EXPIRED": 2,
    "WORKTREE_DIGEST_MISSING": 2,
    "WORKTREE_DIGEST_INVALID": 2,
    "WORKTREE_DIGEST_MISMATCH": 2,
    "TICKET_ID_MISSING": 2,
    "TICKET_ID_INVALID": 2,
    "LANE_ID_MISSING": 2,
    "LANE_ID_INVALID": 2,
    "ASSIGNED_ROLE_MISSING": 2,
    "ASSIGNED_ROLE_INVALID": 2,
    "LANE_RANK_INVALID": 2,
    "SIMULATION_VERDICT_REJECTED": 2,

    # Exit Code 3: Technical Errors, Corrupt Payload, Identity Mismatch, Malformed Raw Data
    "PAYLOAD_NOT_OBJECT": 3,
    "PAYLOAD_DECODE_ERROR": 3,
    "PROVENANCE_CONTEXT_INVALID": 3,
    "AUTHENTICATED_ACCOUNT_MISMATCH": 3,
    "PAYLOAD_ACCOUNT_MISMATCH": 3,
    "ACCOUNT_IDENTITY_MISMATCH": 3,
    "ACCOUNT_UUID_MALFORMED": 3,
    "HOST_LIMIT_ID_MISMATCH": 3,
    "HOST_POOL_MISSING": 3,
    "HOST_WINDOWS_EMPTY": 3,
    "HOST_WEEKLY_WINDOW_MISSING": 3,
    "HOST_WEEKLY_WINDOW_DUPLICATE": 3,
    "SCHEMA_VALIDATION_FAILED": 3,
    "TIMESTAMP_MALFORMED": 3,
    "TIMESTAMP_IN_FUTURE": 3,
    "OBSERVATION_STALE": 3,
    "COLLECTOR_TIMEOUT": 3,
    "COLLECTOR_AUTH_FAILURE": 3,
    "COLLECTOR_TRANSPORT_ERROR": 3,
    "COLLECTOR_INVALID_RESPONSE": 3,
    "COLLECTOR_OVERSIZED_RESPONSE": 3,
    "COLLECTOR_PROCESS_SPAWN_ERROR": 3,
    "REGISTRY_UNAVAILABLE": 3,
    "REGISTRY_TIMEOUT": 3,
    "REGISTRY_INVALID_RESULT": 3,
    "INTERNAL_EVALUATION_ERROR": 3,
}


def load_fixture_json(filename: str) -> Dict[str, Any]:
    path = FIXTURES_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_fixture_yaml(filename: str) -> Dict[str, Any]:
    path = FIXTURES_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_v3_schema() -> Dict[str, Any]:
    return load_fixture_json("verdict_v3_schema.json")


def load_v3_engine(**kwargs: Any) -> Any:
    """Import and instantiate QuotaGuardEngineV3 from scripts.agent_quota_status_guard."""
    from scripts.agent_quota_status_guard import QuotaGuardEngineV3
    return QuotaGuardEngineV3(**kwargs)


def load_concurrency_registry(**kwargs: Any) -> Any:
    """Import and instantiate AtomicConcurrencyRegistry."""
    from scripts.agent_quota_status_guard import AtomicConcurrencyRegistry
    return AtomicConcurrencyRegistry(**kwargs)


def load_quota_collector(**kwargs: Any) -> Any:
    """Import and instantiate QuotaCollector from scripts.lib.quota_collector."""
    from scripts.lib.quota_collector import QuotaCollector
    return QuotaCollector(**kwargs)


def load_exit_code_map() -> Dict[str, int]:
    """Import EXIT_CODE_MAP from scripts.agent_quota_status_guard."""
    from scripts.agent_quota_status_guard import EXIT_CODE_MAP
    return EXIT_CODE_MAP


# ============================================================================
# Fixture & Schema Baseline Sanity Checks (Passed Baseline)
# ============================================================================

def test_fixture_schema_and_verdicts_are_valid() -> None:
    """Validate that authored JSON and YAML fixtures parse correctly and match Draft202012 schema."""
    schema = get_v3_schema()
    validator = Draft202012Validator(schema)

    # Valid green sample
    sample_green = load_fixture_json("sample_verdict_valid_green.json")
    validator.validate(sample_green)

    # Valid error path sample
    sample_error = load_fixture_json("sample_verdict_error_path.json")
    validator.validate(sample_error)

    # Policy fixtures
    approved_policy = load_fixture_yaml("approved_v3_policy.yaml")
    assert approved_policy["status"] == "APPROVED"
    assert approved_policy["thresholds"]["green"] == 40.0


# ============================================================================
# Section 2 & 8: 4-Tier Quota Scale & Boundary Tests (TC-01 through TC-13)
# ============================================================================

def test_tc_01_green_tier_lower_boundary() -> None:
    """TC-01: GREEN tier lower boundary test: decisive_remaining = 40.1% (> 40.0%)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    obs["pools"]["host_codex"]["windows"][0]["used_percent"] = 59.9
    obs["pools"]["host_codex"]["windows"][0]["remaining_percent"] = 40.1

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["tier"] == "GREEN"
    assert verdict["quota_state"] == "ok"
    assert verdict["freeze_status"] == "UNFROZEN"
    assert verdict["host_resume_allowed"] is True
    assert verdict["exit_code"] == 0
    assert verdict["diagnostics"]["decisive_remaining_percent"] == 40.1


def test_tc_02_green_tier_nominal() -> None:
    """TC-02: GREEN tier nominal mid/high point: decisive_remaining = 90.0% (> 40.0%)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    obs["pools"]["host_codex"]["windows"][0]["used_percent"] = 10.0
    obs["pools"]["host_codex"]["windows"][0]["remaining_percent"] = 90.0

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["tier"] == "GREEN"
    assert verdict["quota_state"] == "ok"
    assert verdict["freeze_status"] == "UNFROZEN"
    assert verdict["host_resume_allowed"] is True
    assert verdict["exit_code"] == 0


def test_tc_03_green_amber_exact_boundary_40_percent() -> None:
    """TC-03: Boundary edge: decisive_remaining = 40.0% is NOT GREEN, falls into AMBER."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    obs["pools"]["host_codex"]["windows"][0]["used_percent"] = 60.0
    obs["pools"]["host_codex"]["windows"][0]["remaining_percent"] = 40.0

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["tier"] == "AMBER"
    assert verdict["quota_state"] == "constrained"
    assert verdict["freeze_status"] == "AMBER_WARNING"


def test_tc_04_amber_tier_upper_boundary() -> None:
    """TC-04: AMBER tier upper boundary: decisive_remaining = 40.0%."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_amber.json")
    obs["pools"]["host_codex"]["windows"][0]["used_percent"] = 60.0
    obs["pools"]["host_codex"]["windows"][0]["remaining_percent"] = 40.0

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["tier"] == "AMBER"
    assert verdict["quota_state"] == "constrained"
    assert verdict["freeze_status"] == "AMBER_WARNING"
    assert verdict["diagnostics"]["decisive_remaining_percent"] == 40.0


def test_tc_05_amber_tier_nominal() -> None:
    """TC-05: AMBER tier nominal midpoint: decisive_remaining = 30.0%."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_amber.json")

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["tier"] == "AMBER"
    assert verdict["quota_state"] == "constrained"
    assert verdict["freeze_status"] == "AMBER_WARNING"
    assert verdict["diagnostics"]["decisive_remaining_percent"] == 30.0


def test_tc_06_amber_tier_lower_boundary_above_20() -> None:
    """TC-06: AMBER tier lower boundary edge: decisive_remaining = 20.001% (> 20.0%)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_amber.json")
    obs["pools"]["host_codex"]["windows"][0]["used_percent"] = 79.999
    obs["pools"]["host_codex"]["windows"][0]["remaining_percent"] = 20.001

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["tier"] == "AMBER"
    assert verdict["freeze_status"] == "AMBER_WARNING"


def test_tc_07_amber_orange_exact_boundary_20_percent() -> None:
    """TC-07: Boundary edge: decisive_remaining = 20.0% is NOT AMBER, falls into ORANGE."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_amber.json")
    obs["pools"]["host_codex"]["windows"][0]["used_percent"] = 80.0
    obs["pools"]["host_codex"]["windows"][0]["remaining_percent"] = 20.0

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["tier"] == "ORANGE"
    assert verdict["quota_state"] == "constrained"
    assert verdict["freeze_status"] == "ORANGE_CONSTRAINED"


def test_tc_08_orange_tier_upper_boundary() -> None:
    """TC-08: ORANGE tier upper boundary: decisive_remaining = 20.0%."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_orange.json")
    obs["pools"]["host_codex"]["windows"][0]["used_percent"] = 80.0
    obs["pools"]["host_codex"]["windows"][0]["remaining_percent"] = 20.0

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["tier"] == "ORANGE"
    assert verdict["freeze_status"] == "ORANGE_CONSTRAINED"
    assert verdict["diagnostics"]["decisive_remaining_percent"] == 20.0


def test_tc_09_orange_tier_nominal() -> None:
    """TC-09: ORANGE tier midpoint: decisive_remaining = 15.0%."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_orange.json")

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["tier"] == "ORANGE"
    assert verdict["freeze_status"] == "ORANGE_CONSTRAINED"
    assert verdict["diagnostics"]["decisive_remaining_percent"] == 15.0


def test_tc_10_orange_tier_lower_boundary_10_percent() -> None:
    """TC-10: ORANGE tier lower boundary: decisive_remaining = 10.0%."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_orange.json")
    obs["pools"]["host_codex"]["windows"][0]["used_percent"] = 90.0
    obs["pools"]["host_codex"]["windows"][0]["remaining_percent"] = 10.0

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["tier"] == "ORANGE"
    assert verdict["freeze_status"] == "ORANGE_CONSTRAINED"
    assert verdict["diagnostics"]["decisive_remaining_percent"] == 10.0


def test_tc_11_red_tier_boundary_below_10_percent() -> None:
    """TC-11: RED tier upper boundary: decisive_remaining = 9.99% (< 10.0%)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_orange.json")
    obs["pools"]["host_codex"]["windows"][0]["used_percent"] = 90.01
    obs["pools"]["host_codex"]["windows"][0]["remaining_percent"] = 9.99

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["tier"] == "RED"
    assert verdict["quota_state"] == "depleted"
    assert verdict["freeze_status"] == "RED_FREEZE"
    assert verdict["host_resume_allowed"] is False
    assert verdict["reason_code"] == "QUOTA_DEPLETED"
    assert verdict["exit_code"] == 1


def test_tc_12_red_tier_zero_remaining_quota_depleted() -> None:
    """TC-12: RED tier zero remaining: used_percent = 100.0% -> remaining = 0.0%."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_red_depleted.json")

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["tier"] == "RED"
    assert verdict["quota_state"] == "depleted"
    assert verdict["freeze_status"] == "RED_FREEZE"
    assert verdict["host_resume_allowed"] is False
    assert verdict["reason_code"] == "QUOTA_DEPLETED"
    assert verdict["exit_code"] == 1


def test_tc_13_red_tier_triggered_by_rate_limit_active() -> None:
    """TC-13: RED tier triggered by rate_limit_reached signal even if remaining is 80.0%."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_red_rate_limited.json")

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["tier"] == "RED"
    assert verdict["quota_state"] == "depleted"
    assert verdict["freeze_status"] == "RED_FREEZE"
    assert verdict["host_resume_allowed"] is False
    assert verdict["reason_code"] == "RATE_LIMIT_ACTIVE"
    assert verdict["exit_code"] == 1


# ============================================================================
# Section 1 & 8: Pool Isolation (Codex vs Spark) (TC-14 through TC-17)
# ============================================================================

def test_tc_14_pool_isolation_host_codex_red_despite_spark_green() -> None:
    """TC-14: Host Codex is depleted (0.0%), Spark pool is 100% -> Host Codex remains RED."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_spark_isolated.json")

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["tier"] == "RED"
    assert verdict["host_resume_allowed"] is False
    assert verdict["freeze_status"] == "RED_FREEZE"


def test_tc_15_pool_isolation_spark_red_does_not_affect_host_codex() -> None:
    """TC-15: Spark pool is 0.0%, Host Codex is 80.0% -> Host Codex remains GREEN."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_spark_isolated.json")
    obs["pools"]["host_codex"]["windows"][0]["used_percent"] = 20.0
    obs["pools"]["host_codex"]["windows"][0]["remaining_percent"] = 80.0
    obs["pools"]["host_codex"]["windows"][0]["rate_limit_reached_type"] = None
    obs["pools"]["spark"]["windows"][0]["used_percent"] = 100.0
    obs["pools"]["spark"]["windows"][0]["remaining_percent"] = 0.0

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["tier"] == "GREEN"
    assert verdict["host_resume_allowed"] is True
    assert verdict["freeze_status"] == "UNFROZEN"


def test_tc_16_pool_isolation_reject_non_codex_limit_id() -> None:
    """TC-16: Target limitId must be 'codex'; non-codex rejected with HOST_LIMIT_ID_MISMATCH."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    obs["pools"]["host_codex"]["limitId"] = "spark"

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["reason_code"] == "HOST_LIMIT_ID_MISMATCH"
    assert verdict["exit_code"] == 3


def test_tc_17_pool_isolation_reject_missing_host_pool() -> None:
    """TC-17: Observation missing host_codex pool entirely -> HOST_POOL_MISSING (Exit 3)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    del obs["pools"]["host_codex"]

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["reason_code"] == "HOST_POOL_MISSING"
    assert verdict["exit_code"] == 3


# ============================================================================
# Section 1 & 8: Decisive Remaining Math & Windows (TC-18 through TC-23)
# ============================================================================

def test_tc_18_decisive_remaining_math_precision() -> None:
    """TC-18: Decisive remaining math: 100.0 - used_percent float precision handling."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    obs["pools"]["host_codex"]["windows"][0]["used_percent"] = 59.999999999
    obs["pools"]["host_codex"]["windows"][0]["remaining_percent"] = 40.000000001

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["tier"] == "GREEN"
    assert abs(verdict["diagnostics"]["decisive_remaining_percent"] - 40.000000001) < 1e-7


def test_tc_19_decisive_remaining_math_used_exceeds_100_percent() -> None:
    """TC-19: used_percent > 100.0% is clamped to 0.0% decisive remaining -> RED."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    obs["pools"]["host_codex"]["windows"][0]["used_percent"] = 105.0
    obs["pools"]["host_codex"]["windows"][0]["remaining_percent"] = 0.0

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["tier"] == "RED"
    assert verdict["reason_code"] == "QUOTA_DEPLETED"
    assert verdict["diagnostics"]["decisive_remaining_percent"] == 0.0


def test_tc_20_host_windows_empty_rejected() -> None:
    """TC-20: Host windows list is empty -> HOST_WINDOWS_EMPTY (Exit 3)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    obs["pools"]["host_codex"]["windows"] = []

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["reason_code"] == "HOST_WINDOWS_EMPTY"
    assert verdict["exit_code"] == 3


def test_tc_21_host_weekly_window_missing_rejected() -> None:
    """TC-21: Host weekly window (10080 mins) missing -> HOST_WEEKLY_WINDOW_MISSING (Exit 3)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    obs["pools"]["host_codex"]["windows"][0]["window_duration_mins"] = 300

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["reason_code"] == "HOST_WEEKLY_WINDOW_MISSING"
    assert verdict["exit_code"] == 3


def test_tc_22_host_weekly_window_duplicate_rejected() -> None:
    """TC-22: Duplicate weekly windows in host pool -> HOST_WEEKLY_WINDOW_DUPLICATE (Exit 3)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    w = copy.deepcopy(obs["pools"]["host_codex"]["windows"][0])
    obs["pools"]["host_codex"]["windows"].append(w)

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["reason_code"] == "HOST_WEEKLY_WINDOW_DUPLICATE"
    assert verdict["exit_code"] == 3


def test_tc_23_window_math_inconsistent_rejected() -> None:
    """TC-23: Window used + remaining != 100.0% -> WINDOW_MATH_INCONSISTENT (Exit 3)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    obs["pools"]["host_codex"]["windows"][0]["used_percent"] = 50.0
    obs["pools"]["host_codex"]["windows"][0]["remaining_percent"] = 40.0

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["reason_code"] == "WINDOW_MATH_INCONSISTENT"
    assert verdict["exit_code"] == 3


# ============================================================================
# Section 1 & 8: Freshness & Control Plane vs Data Plane (TC-24 through TC-27)
# ============================================================================

def test_tc_24_freshness_timestamp_in_future_rejected() -> None:
    """TC-24: Observation timestamp in future (> now + tolerance) -> TIMESTAMP_IN_FUTURE (Exit 3)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    future_time = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    obs["observed_at"] = future_time

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["reason_code"] == "TIMESTAMP_IN_FUTURE"
    assert verdict["exit_code"] == 3


def test_tc_25_freshness_observation_stale_rejected() -> None:
    """TC-25: Observation stale (> maximum_age_seconds) -> OBSERVATION_STALE (Exit 3)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    past_time = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
    obs["observed_at"] = past_time

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["reason_code"] == "OBSERVATION_STALE"
    assert verdict["exit_code"] == 3


def test_tc_26_freshness_timestamp_malformed_rejected() -> None:
    """TC-26: Timestamp malformed (not ISO-8601) -> TIMESTAMP_MALFORMED (Exit 3)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    obs["observed_at"] = "invalid-date-time-string"

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["reason_code"] == "TIMESTAMP_MALFORMED"
    assert verdict["exit_code"] == 3


def test_tc_27_control_plane_safe_observation_in_red_freeze() -> None:
    """TC-27: Control Plane vs Data Plane: Under RED_FREEZE, inspection passes safely without crash."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_red_depleted.json")
    now_iso = datetime.now(timezone.utc).isoformat()
    obs["observed_at"] = now_iso

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["tier"] == "RED"
    assert verdict["freeze_status"] == "RED_FREEZE"
    assert verdict["host_resume_allowed"] is False
    assert verdict["exit_code"] == 1
    assert verdict["diagnostics"]["concurrency_state"]["active_count"] is not None


# ============================================================================
# Section 2 & 8: Lane Rank Permissions per Tier (TC-28 through TC-35)
# ============================================================================

def test_tc_28_rank_permissions_in_green_ranks_0_to_3_allowed() -> None:
    """TC-28: In GREEN: Ranks 0, 1, 2, 3 are all permitted."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    obs["observed_at"] = datetime.now(timezone.utc).isoformat()
    evidence = load_fixture_json("admission_evidence_valid.json")
    evidence["expires_at"] = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

    for r in [0, 1, 2, 3]:
        evidence["lane_rank"] = r
        verdict = engine.evaluate(observation_payload=obs, evidence=evidence)
        assert verdict["exit_code"] == 0
        assert verdict["host_resume_allowed"] is True


def test_tc_29_rank_permissions_in_amber_ranks_0_and_1_allowed() -> None:
    """TC-29: In AMBER: Ranks 0 and 1 are permitted."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_amber.json")
    obs["observed_at"] = datetime.now(timezone.utc).isoformat()
    evidence = load_fixture_json("admission_evidence_valid.json")
    evidence["expires_at"] = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

    for r in [0, 1]:
        evidence["lane_rank"] = r
        verdict = engine.evaluate(observation_payload=obs, evidence=evidence)
        assert verdict["exit_code"] == 0
        assert verdict["host_resume_allowed"] is True


def test_tc_30_rank_permissions_in_amber_rank_2_disallowed() -> None:
    """TC-30: In AMBER: Rank 2 rejected with LANE_RANK_DISALLOWED_IN_AMBER (Exit 1)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_amber.json")
    obs["observed_at"] = datetime.now(timezone.utc).isoformat()
    evidence = load_fixture_json("admission_evidence_valid.json")
    evidence["lane_rank"] = 2
    evidence["expires_at"] = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

    verdict = engine.evaluate(observation_payload=obs, evidence=evidence)
    assert verdict["reason_code"] == "LANE_RANK_DISALLOWED_IN_AMBER"
    assert verdict["exit_code"] == 1
    assert verdict["host_resume_allowed"] is False


def test_tc_31_rank_permissions_in_amber_rank_3_disallowed() -> None:
    """TC-31: In AMBER: Rank 3 rejected with LANE_RANK_DISALLOWED_IN_AMBER (Exit 1)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_amber.json")
    obs["observed_at"] = datetime.now(timezone.utc).isoformat()
    evidence = load_fixture_json("admission_evidence_valid.json")
    evidence["lane_rank"] = 3
    evidence["expires_at"] = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

    verdict = engine.evaluate(observation_payload=obs, evidence=evidence)
    assert verdict["reason_code"] == "LANE_RANK_DISALLOWED_IN_AMBER"
    assert verdict["exit_code"] == 1
    assert verdict["host_resume_allowed"] is False


def test_tc_32_rank_permissions_in_orange_rank_0_recovery_allowed() -> None:
    """TC-32: In ORANGE: Rank 0 (Recovery lane) is allowed."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_orange.json")
    obs["observed_at"] = datetime.now(timezone.utc).isoformat()
    evidence = load_fixture_json("admission_evidence_valid.json")
    evidence["lane_rank"] = 0
    evidence["expires_at"] = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

    verdict = engine.evaluate(observation_payload=obs, evidence=evidence)
    assert verdict["exit_code"] == 0
    assert verdict["host_resume_allowed"] is True


def test_tc_33_rank_permissions_in_orange_rank_1_disallowed() -> None:
    """TC-33: In ORANGE: Rank 1 rejected with LANE_NOT_ALLOWED_IN_ORANGE (Exit 1)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_orange.json")
    obs["observed_at"] = datetime.now(timezone.utc).isoformat()
    evidence = load_fixture_json("admission_evidence_valid.json")
    evidence["lane_rank"] = 1
    evidence["expires_at"] = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

    verdict = engine.evaluate(observation_payload=obs, evidence=evidence)
    assert verdict["reason_code"] == "LANE_NOT_ALLOWED_IN_ORANGE"
    assert verdict["exit_code"] == 1
    assert verdict["host_resume_allowed"] is False


def test_tc_34_rank_permissions_in_orange_ranks_2_and_3_disallowed() -> None:
    """TC-34: In ORANGE: Ranks 2 and 3 rejected with LANE_NOT_ALLOWED_IN_ORANGE (Exit 1)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_orange.json")
    obs["observed_at"] = datetime.now(timezone.utc).isoformat()
    evidence = load_fixture_json("admission_evidence_valid.json")
    evidence["expires_at"] = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

    for r in [2, 3]:
        evidence["lane_rank"] = r
        verdict = engine.evaluate(observation_payload=obs, evidence=evidence)
        assert verdict["reason_code"] == "LANE_NOT_ALLOWED_IN_ORANGE"
        assert verdict["exit_code"] == 1


def test_tc_35_rank_permissions_in_red_all_ranks_disallowed() -> None:
    """TC-35: In RED: All ranks (0-3) disallowed due to QUOTA_DEPLETED (Exit 1)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_red_depleted.json")
    obs["observed_at"] = datetime.now(timezone.utc).isoformat()
    evidence = load_fixture_json("admission_evidence_valid.json")
    evidence["expires_at"] = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

    for r in [0, 1, 2, 3]:
        evidence["lane_rank"] = r
        verdict = engine.evaluate(observation_payload=obs, evidence=evidence)
        assert verdict["reason_code"] == "QUOTA_DEPLETED"
        assert verdict["exit_code"] == 1
        assert verdict["host_resume_allowed"] is False


# ============================================================================
# Section 2, 4 & 8: Concurrency Ceilings & Aggregation (TC-36 through TC-40)
# ============================================================================

def test_tc_36_concurrency_ceiling_green_max_3_slots() -> None:
    """TC-36: In GREEN: Max concurrency is 3 slots; 4th reservation is rejected."""
    registry = load_concurrency_registry()
    account_id = "08a4df52-9b3d-4d09-9bd5-af0f7e0e8043"
    pool_id = "codex"

    # Acquire 3 slots
    res1 = registry.acquire_dispatch_reservation(account_id, pool_id, "lane-1", "TICKET-1", "GREEN", 30)
    res2 = registry.acquire_dispatch_reservation(account_id, pool_id, "lane-2", "TICKET-2", "GREEN", 30)
    res3 = registry.acquire_dispatch_reservation(account_id, pool_id, "lane-3", "TICKET-3", "GREEN", 30)
    assert res1.acquired is True
    assert res2.acquired is True
    assert res3.acquired is True

    # 4th slot rejected
    res4 = registry.acquire_dispatch_reservation(account_id, pool_id, "lane-4", "TICKET-4", "GREEN", 30)
    assert res4.acquired is False
    assert res4.reason == "CONCURRENCY_LIMIT_REACHED"


def test_tc_37_concurrency_ceiling_amber_max_1_slot() -> None:
    """TC-37: In AMBER: Max concurrency is 1 slot; 2nd reservation is rejected."""
    registry = load_concurrency_registry()
    account_id = "08a4df52-9b3d-4d09-9bd5-af0f7e0e8043"
    pool_id = "codex"

    res1 = registry.acquire_dispatch_reservation(account_id, pool_id, "lane-1", "TICKET-1", "AMBER", 30)
    assert res1.acquired is True

    res2 = registry.acquire_dispatch_reservation(account_id, pool_id, "lane-2", "TICKET-2", "AMBER", 30)
    assert res2.acquired is False
    assert res2.reason == "CONCURRENCY_LIMIT_REACHED"


def test_tc_38_concurrency_ceiling_orange_max_1_slot() -> None:
    """TC-38: In ORANGE: Max concurrency is 1 slot; 2nd reservation is rejected."""
    registry = load_concurrency_registry()
    account_id = "08a4df52-9b3d-4d09-9bd5-af0f7e0e8043"
    pool_id = "codex"

    res1 = registry.acquire_dispatch_reservation(account_id, pool_id, "lane-1", "TICKET-1", "ORANGE", 30)
    assert res1.acquired is True

    res2 = registry.acquire_dispatch_reservation(account_id, pool_id, "lane-2", "TICKET-2", "ORANGE", 30)
    assert res2.acquired is False
    assert res2.reason == "CONCURRENCY_LIMIT_REACHED"


def test_tc_39_concurrency_ceiling_red_max_0_slots() -> None:
    """TC-39: In RED: Max concurrency is 0 slots; any reservation is rejected."""
    registry = load_concurrency_registry()
    account_id = "08a4df52-9b3d-4d09-9bd5-af0f7e0e8043"
    pool_id = "codex"

    res = registry.acquire_dispatch_reservation(account_id, pool_id, "lane-1", "TICKET-1", "RED", 30)
    assert res.acquired is False
    assert res.reason in ("QUOTA_DEPLETED", "CONCURRENCY_LIMIT_REACHED")


def test_tc_40_cross_tier_aggregation_active_leases_and_reservations() -> None:
    """TC-40: Cross-tier aggregation: total_active = active_leases + active_reservations."""
    registry = load_concurrency_registry()
    account_id = "08a4df52-9b3d-4d09-9bd5-af0f7e0e8043"
    pool_id = "codex"

    # Acquire reservation 1 and convert to lease
    res1 = registry.acquire_dispatch_reservation(account_id, pool_id, "lane-1", "TICKET-1", "GREEN", 30)
    assert res1.acquired is True
    lease = registry.convert_reservation_to_execution_lease(res1.reservation_id)
    assert lease is not None

    # Acquire reservation 2 (still in reservation state)
    res2 = registry.acquire_dispatch_reservation(account_id, pool_id, "lane-2", "TICKET-2", "GREEN", 30)
    assert res2.acquired is True

    # Active count should be 1 lease + 1 reservation = 2
    assert registry.get_active_count(account_id, pool_id) == 2


# ============================================================================
# Section 3 & 8: Account Identity & Precedence (TC-41 through TC-44)
# ============================================================================

def test_tc_41_identity_payload_account_mismatch() -> None:
    """TC-41: PAYLOAD_ACCOUNT_MISMATCH: expected == auth, but payload != expected (Exit 3)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    expected_acc = "08a4df52-9b3d-4d09-9bd5-af0f7e0e8043"
    auth_acc = "08a4df52-9b3d-4d09-9bd5-af0f7e0e8043"
    obs["account_id"] = "11111111-2222-3333-4444-555555555555"

    verdict = engine.evaluate(
        observation_payload=obs,
        authenticated_account_id=auth_acc,
        expected_account_id=expected_acc,
    )
    assert verdict["reason_code"] == "PAYLOAD_ACCOUNT_MISMATCH"
    assert verdict["exit_code"] == 3


def test_tc_42_identity_authenticated_account_mismatch() -> None:
    """TC-42: AUTHENTICATED_ACCOUNT_MISMATCH: auth != expected (Exit 3)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    expected_acc = "08a4df52-9b3d-4d09-9bd5-af0f7e0e8043"
    auth_acc = "99999999-8888-7777-6666-555555555555"

    verdict = engine.evaluate(
        observation_payload=obs,
        authenticated_account_id=auth_acc,
        expected_account_id=expected_acc,
    )
    assert verdict["reason_code"] == "AUTHENTICATED_ACCOUNT_MISMATCH"
    assert verdict["exit_code"] == 3


def test_tc_43_identity_account_mismatch_overall() -> None:
    """TC-43: ACCOUNT_IDENTITY_MISMATCH: 3-way identity mismatch (Exit 3)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    obs["account_id"] = "11111111-1111-1111-1111-111111111111"
    expected_acc = "22222222-2222-2222-2222-222222222222"
    auth_acc = "33333333-3333-3333-3333-333333333333"

    verdict = engine.evaluate(
        observation_payload=obs,
        authenticated_account_id=auth_acc,
        expected_account_id=expected_acc,
    )
    assert verdict["reason_code"] in ("AUTHENTICATED_ACCOUNT_MISMATCH", "ACCOUNT_IDENTITY_MISMATCH")
    assert verdict["exit_code"] == 3


def test_tc_44_identity_account_uuid_malformed() -> None:
    """TC-44: ACCOUNT_UUID_MALFORMED: Target account is not a valid UUID (Exit 3)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    obs["account_id"] = "not-a-valid-uuid"

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["reason_code"] == "ACCOUNT_UUID_MALFORMED"
    assert verdict["exit_code"] == 3


# ============================================================================
# Section 4 & 8: Concurrency Contention & Lifetime Boundary (TC-45 through TC-48)
# ============================================================================

def test_tc_45_concurrency_slot_contention_in_amber() -> None:
    """TC-45: Concurrent slot contention in AMBER: Req 1 acquires (0), Req 2 denied (Exit 1)."""
    registry = load_concurrency_registry()
    account_id = "08a4df52-9b3d-4d09-9bd5-af0f7e0e8043"
    pool_id = "codex"

    req1 = registry.acquire_dispatch_reservation(account_id, pool_id, "lane-1", "TICKET-1", "AMBER", 30)
    assert req1.acquired is True
    assert req1.reservation_id is not None

    req2 = registry.acquire_dispatch_reservation(account_id, pool_id, "lane-2", "TICKET-2", "AMBER", 30)
    assert req2.acquired is False
    assert req2.reason == "CONCURRENCY_LIMIT_REACHED"


def test_tc_46_lifetime_boundary_valid_until_minimum_remaining() -> None:
    """TC-46: Lifetime boundary: obs_age = 59s, evidence remaining = 100s -> valid_until = now + 1s."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    now = datetime.now(timezone.utc)
    obs["observed_at"] = (now - timedelta(seconds=59)).isoformat()
    evidence = load_fixture_json("admission_evidence_valid.json")
    evidence["expires_at"] = (now + timedelta(seconds=100)).isoformat()

    verdict = engine.evaluate(observation_payload=obs, evidence=evidence)
    valid_until_dt = datetime.fromisoformat(verdict["valid_until"])
    assert abs((valid_until_dt - (now + timedelta(seconds=1))).total_seconds()) <= 1.0


def test_tc_47_tier_downgrade_protection_running_leases_preserved() -> None:
    """TC-47: Tier Downgrade Protection: 2 active leases in GREEN; quota drops to AMBER; leases preserved."""
    registry = load_concurrency_registry()
    account_id = "08a4df52-9b3d-4d09-9bd5-af0f7e0e8043"
    pool_id = "codex"

    r1 = registry.acquire_dispatch_reservation(account_id, pool_id, "lane-1", "TICKET-1", "GREEN", 30)
    r2 = registry.acquire_dispatch_reservation(account_id, pool_id, "lane-2", "TICKET-2", "GREEN", 30)
    l1 = registry.convert_reservation_to_execution_lease(r1.reservation_id)
    l2 = registry.convert_reservation_to_execution_lease(r2.reservation_id)
    assert l1 is not None and l2 is not None

    # Tier drops to AMBER (ceiling 1), but active jobs (2) must NOT be terminated
    assert registry.get_active_count(account_id, pool_id) == 2
    # New reservation attempt is rejected
    r3 = registry.acquire_dispatch_reservation(account_id, pool_id, "lane-3", "TICKET-3", "AMBER", 30)
    assert r3.acquired is False
    assert r3.reason == "CONCURRENCY_LIMIT_REACHED"


def test_tc_48_two_phase_concurrency_reservation_conversion_to_lease() -> None:
    """TC-48: Reservation is single-use and converts to lease; second conversion fails."""
    registry = load_concurrency_registry()
    account_id = "08a4df52-9b3d-4d09-9bd5-af0f7e0e8043"
    pool_id = "codex"

    res = registry.acquire_dispatch_reservation(account_id, pool_id, "lane-1", "TICKET-1", "GREEN", 30)
    lease = registry.convert_reservation_to_execution_lease(res.reservation_id)
    assert lease is not None
    assert lease.lease_id is not None

    # Second conversion with same reservation must fail
    second_lease = registry.convert_reservation_to_execution_lease(res.reservation_id)
    assert second_lease is None


# ============================================================================
# Section 5 & 8: Schema Validation & Multi-window Accumulation (TC-49A, 49B, 50, 51)
# ============================================================================

def test_tc_49a_schema_validation_failure_window_duration_string() -> None:
    """TC-49A: Window duration is string 'invalid' -> SCHEMA_VALIDATION_FAILED (Exit 3)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_schema_invalid.json")

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["reason_code"] == "SCHEMA_VALIDATION_FAILED"
    assert verdict["exit_code"] == 3


def test_tc_49b_multi_window_semantic_math_error_accumulation() -> None:
    """TC-49B: Multi-window semantic math: Window 1 (50+45=95%) and Window 2 (20+70=90%) both accumulated."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_multi_window_inconsistent.json")

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["exit_code"] == 3
    assert len(verdict["diagnostics"]["validation_errors"]) >= 2


def test_tc_50_verdict_schema_conformance_valid_verdict() -> None:
    """TC-50: Full QuotaGuardVerdictV3.3 schema conformance on valid GREEN verdict."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    obs["observed_at"] = datetime.now(timezone.utc).isoformat()
    evidence = load_fixture_json("admission_evidence_valid.json")
    evidence["expires_at"] = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

    verdict = engine.evaluate(observation_payload=obs, evidence=evidence)
    schema = get_v3_schema()
    Draft202012Validator(schema).validate(verdict)


def test_tc_51_verdict_schema_conformance_denied_verdict_nulls() -> None:
    """TC-51: Full schema conformance on early failure with null optional fields."""
    engine = load_v3_engine()
    # Non-dict payload triggers early exit 3
    verdict = engine.evaluate(observation_payload="bad-string-payload")
    schema = get_v3_schema()
    Draft202012Validator(schema).validate(verdict)
    assert verdict["exit_code"] == 3
    assert verdict["target_account"] is None
    assert verdict["observation_ref"] is None


# ============================================================================
# Section 5 & 8: Policy Admission & Validation (TC-52 through TC-55)
# ============================================================================

def test_tc_52_policy_pending_authorization_rejected() -> None:
    """TC-52: Policy has status PENDING_AUTHORIZATION -> POLICY_NOT_APPROVED (Exit 2)."""
    engine = load_v3_engine(policy_path=str(FIXTURES_DIR / "pending_policy.yaml"))
    obs = load_fixture_json("observation_green.json")

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["reason_code"] == "POLICY_NOT_APPROVED"
    assert verdict["exit_code"] == 2
    assert verdict["tier"] == "UNKNOWN"


def test_tc_53_admission_evidence_expired_rejected() -> None:
    """TC-53: evidence_expires_at <= now -> ADMISSION_EVIDENCE_EXPIRED (Exit 2)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    obs["observed_at"] = datetime.now(timezone.utc).isoformat()
    expired_evidence = load_fixture_json("admission_evidence_expired.json")

    verdict = engine.evaluate(observation_payload=obs, evidence=expired_evidence)
    assert verdict["reason_code"] == "ADMISSION_EVIDENCE_EXPIRED"
    assert verdict["exit_code"] == 2


def test_tc_54_lease_preserved_across_verdict_expiry() -> None:
    """TC-54: Active execution lease preserved across verdict expiry."""
    registry = load_concurrency_registry()
    account_id = "08a4df52-9b3d-4d09-9bd5-af0f7e0e8043"
    pool_id = "codex"

    res = registry.acquire_dispatch_reservation(account_id, pool_id, "lane-1", "TICKET-1", "GREEN", ttl_seconds=1)
    lease = registry.convert_reservation_to_execution_lease(res.reservation_id, heartbeat_ttl_seconds=600)

    # Simulate verdict expiring after 2 seconds
    time.sleep(1.1)
    assert registry.is_lease_active(lease.lease_id) is True
    assert registry.get_active_count(account_id, pool_id) == 1


def test_tc_55_policy_malformed_missing_concurrency_key() -> None:
    """TC-55: Policy missing max_concurrency_green -> POLICY_MALFORMED (Exit 2)."""
    engine = load_v3_engine(policy_path=str(FIXTURES_DIR / "malformed_missing_key_policy.yaml"))
    obs = load_fixture_json("observation_green.json")

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["reason_code"] == "POLICY_MALFORMED"
    assert verdict["exit_code"] == 2


# ============================================================================
# Section 8: Sanitization, Precedence & Simulation (TC-56 through TC-59)
# ============================================================================

def test_tc_56_lane_rank_invalid_sanitized_to_null() -> None:
    """TC-56: lane_rank = 9 sanitized to null in verdict and rejected with LANE_RANK_INVALID (Exit 2)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    obs["observed_at"] = datetime.now(timezone.utc).isoformat()
    evidence = load_fixture_json("admission_evidence_valid.json")
    evidence["lane_rank"] = 9
    evidence["expires_at"] = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

    verdict = engine.evaluate(observation_payload=obs, evidence=evidence)
    assert verdict["lane_binding"]["lane_rank"] is None
    assert verdict["reason_code"] == "LANE_RANK_INVALID"
    assert verdict["exit_code"] == 2


def test_tc_57_target_worktree_digest_invalid_sanitized_to_null() -> None:
    """TC-57: target_worktree_digest = 'abc' sanitized to null -> WORKTREE_DIGEST_INVALID (Exit 2)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    obs["observed_at"] = datetime.now(timezone.utc).isoformat()
    evidence = load_fixture_json("admission_evidence_valid.json")
    evidence["target_worktree_digest"] = "abc"
    evidence["expires_at"] = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

    verdict = engine.evaluate(observation_payload=obs, evidence=evidence)
    assert verdict["lane_binding"]["target_worktree_digest"] is None
    assert verdict["reason_code"] == "WORKTREE_DIGEST_INVALID"
    assert verdict["exit_code"] == 2


def test_tc_58_precedence_quota_depleted_over_source_admission() -> None:
    """TC-58: Quota depleted (Rank 6) outranks source admission failure (Rank 8) -> QUOTA_DEPLETED (Exit 1)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_red_depleted.json")
    obs["observed_at"] = datetime.now(timezone.utc).isoformat()
    evidence = load_fixture_json("admission_evidence_valid.json")
    # Both quota depleted AND admission invalid
    evidence["expires_at"] = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()

    verdict = engine.evaluate(observation_payload=obs, evidence=evidence)
    assert verdict["reason_code"] == "QUOTA_DEPLETED"
    assert verdict["exit_code"] == 1


def test_tc_59_simulation_verdict_when_context_ambiguous() -> None:
    """TC-59: Context missing or ambiguous -> verdict_kind: 'simulation', recovery_proven: false."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")

    verdict = engine.evaluate(observation_payload=obs, is_simulation=True)
    assert verdict["verdict_kind"] == "simulation"
    assert verdict["quota_recovery_proven"] is False


# ============================================================================
# Section 8: Policy Edge Cases & Sub-second Lifetime (TC-60 through TC-64)
# ============================================================================

def test_tc_60_policy_malformed_negative_or_nan_ttl() -> None:
    """TC-60: Policy TTL is negative or NaN -> POLICY_MALFORMED (Exit 2)."""
    engine = load_v3_engine(policy_path=str(FIXTURES_DIR / "malformed_nan_ttl_policy.yaml"))
    obs = load_fixture_json("observation_green.json")

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["reason_code"] == "POLICY_MALFORMED"
    assert verdict["exit_code"] == 2


def test_tc_61_policy_malformed_fractional_concurrency() -> None:
    """TC-61: Concurrency in policy is fractional 1.5 -> POLICY_MALFORMED (Exit 2)."""
    engine = load_v3_engine(policy_path=str(FIXTURES_DIR / "malformed_fractional_concurrency_policy.yaml"))
    obs = load_fixture_json("observation_green.json")

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["reason_code"] == "POLICY_MALFORMED"
    assert verdict["exit_code"] == 2


def test_tc_62_policy_malformed_swapped_threshold_order() -> None:
    """TC-62: Threshold order in policy swapped (green < amber) -> POLICY_MALFORMED (Exit 2)."""
    engine = load_v3_engine(policy_path=str(FIXTURES_DIR / "malformed_swapped_thresholds_policy.yaml"))
    obs = load_fixture_json("observation_green.json")

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["reason_code"] == "POLICY_MALFORMED"
    assert verdict["exit_code"] == 2


def test_tc_63_sub_second_verdict_lifetime_handling() -> None:
    """TC-63: Sub-second verdict lifetime: ttl = 0.5s accepted as float or triggers VERDICT_LIFETIME_EXPIRED."""
    registry = load_concurrency_registry()
    account_id = "08a4df52-9b3d-4d09-9bd5-af0f7e0e8043"
    pool_id = "codex"

    res = registry.acquire_dispatch_reservation(account_id, pool_id, "lane-1", "TICKET-1", "GREEN", ttl_seconds=0.5)
    assert res.acquired is True
    time.sleep(0.6)
    # Once expired after 0.6s, cannot convert to lease
    lease = registry.convert_reservation_to_execution_lease(res.reservation_id)
    assert lease is None


def test_tc_64_operator_authorization_revoked_at_dispatch() -> None:
    """TC-64: Operator authorization token revoked before dispatch -> OPERATOR_AUTHORIZATION_REVOKED (Exit 2)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    obs["observed_at"] = datetime.now(timezone.utc).isoformat()
    evidence = load_fixture_json("admission_evidence_valid.json")
    evidence["expires_at"] = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

    verdict = engine.evaluate(
        observation_payload=obs,
        evidence=evidence,
        is_authorization_revoked=True,
    )
    assert verdict["reason_code"] == "OPERATOR_AUTHORIZATION_REVOKED"
    assert verdict["exit_code"] == 2


# ============================================================================
# Section 8: Concurrency Idempotency, Registry Faults & Subprocess Lifecycle (TC-65 through TC-69)
# ============================================================================

def test_tc_65_idempotent_duplicate_reservation_requests() -> None:
    """TC-65: Duplicate reservation request ID idempotently returns existing reservation without consuming extra slot."""
    registry = load_concurrency_registry()
    account_id = "08a4df52-9b3d-4d09-9bd5-af0f7e0e8043"
    pool_id = "codex"

    res1 = registry.acquire_dispatch_reservation(
        account_id, pool_id, "lane-1", "TICKET-1", "AMBER", ttl_seconds=30, request_id="REQ-DUPLICATE-001"
    )
    assert res1.acquired is True

    # Same request_id repeats
    res2 = registry.acquire_dispatch_reservation(
        account_id, pool_id, "lane-1", "TICKET-1", "AMBER", ttl_seconds=30, request_id="REQ-DUPLICATE-001"
    )
    assert res2.acquired is True
    assert res2.reservation_id == res1.reservation_id
    assert registry.get_active_count(account_id, pool_id) == 1


def test_tc_66_concurrency_registry_timeout_fail_closed() -> None:
    """TC-66: Concurrency registry timeout -> REGISTRY_UNAVAILABLE (Exit 3)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    obs["observed_at"] = datetime.now(timezone.utc).isoformat()
    evidence = load_fixture_json("admission_evidence_valid.json")
    evidence["expires_at"] = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

    verdict = engine.evaluate(
        observation_payload=obs,
        evidence=evidence,
        simulate_registry_timeout=True,
    )
    assert verdict["reason_code"] == "REGISTRY_UNAVAILABLE"
    assert verdict["exit_code"] == 3


def test_tc_67_runner_releases_reservation_on_spawn_failure() -> None:
    """TC-67: Runner releases reservation on subprocess spawn failure -> slot returned immediately."""
    registry = load_concurrency_registry()
    account_id = "08a4df52-9b3d-4d09-9bd5-af0f7e0e8043"
    pool_id = "codex"

    res = registry.acquire_dispatch_reservation(account_id, pool_id, "lane-1", "TICKET-1", "AMBER", ttl_seconds=30)
    assert registry.get_active_count(account_id, pool_id) == 1

    # Runner fails to spawn subagent process, calls release_reservation
    released = registry.release_reservation(res.reservation_id)
    assert released is True
    assert registry.get_active_count(account_id, pool_id) == 0


def test_tc_68_heartbeat_lost_suspect_status_with_slot_held() -> None:
    """TC-68: Worker heartbeat lost -> lease marked suspect, but slot remains held."""
    registry = load_concurrency_registry()
    account_id = "08a4df52-9b3d-4d09-9bd5-af0f7e0e8043"
    pool_id = "codex"

    res = registry.acquire_dispatch_reservation(account_id, pool_id, "lane-1", "TICKET-1", "GREEN", ttl_seconds=30)
    lease = registry.convert_reservation_to_execution_lease(res.reservation_id, heartbeat_ttl_seconds=1)

    # Miss heartbeat beyond TTL
    time.sleep(1.1)
    registry.check_heartbeats()
    lease_status = registry.get_lease_status(lease.lease_id)
    assert lease_status == "suspect"
    # Slot is STILL held to avoid race condition
    assert registry.get_active_count(account_id, pool_id) == 1


def test_tc_69_payload_not_object_non_dict_rejected() -> None:
    """TC-69: Payload is non-dict (string or list) -> PAYLOAD_NOT_OBJECT (Exit 3)."""
    engine = load_v3_engine()

    # Test with string payload
    v_str = engine.evaluate(observation_payload="just a string")
    assert v_str["reason_code"] == "PAYLOAD_NOT_OBJECT"
    assert v_str["exit_code"] == 3

    # Test with list payload
    v_list = engine.evaluate(observation_payload=[1, 2, 3])
    assert v_list["reason_code"] == "PAYLOAD_NOT_OBJECT"
    assert v_list["exit_code"] == 3


# ============================================================================
# Section 3: Precedence Hierarchy Ranks 1 through 8 Tests
# ============================================================================

def test_precedence_hierarchy_rank1_collector_over_rank2_identity() -> None:
    """Precedence: Rank 1 (Collector Error) outranks Rank 2 (Identity Mismatch)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_green.json")
    obs["account_id"] = "wrong-account-id"

    verdict = engine.evaluate(
        observation_payload=obs,
        simulate_collector_error="COLLECTOR_TIMEOUT",
    )
    assert verdict["reason_code"] == "COLLECTOR_TIMEOUT"
    assert verdict["exit_code"] == 3


def test_precedence_hierarchy_rank2_identity_over_rank3_schema() -> None:
    """Precedence: Rank 2 (Identity Mismatch) outranks Rank 3 (Schema Validation Failed)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_schema_invalid.json")
    expected_acc = "08a4df52-9b3d-4d09-9bd5-af0f7e0e8043"
    auth_acc = "08a4df52-9b3d-4d09-9bd5-af0f7e0e8043"
    obs["account_id"] = "11111111-2222-3333-4444-555555555555"

    verdict = engine.evaluate(
        observation_payload=obs,
        authenticated_account_id=auth_acc,
        expected_account_id=expected_acc,
    )
    assert verdict["reason_code"] == "PAYLOAD_ACCOUNT_MISMATCH"
    assert verdict["exit_code"] == 3


def test_precedence_hierarchy_rank3_schema_over_rank4_freshness() -> None:
    """Precedence: Rank 3 (Schema Validation Failed) outranks Rank 4 (Observation Stale)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_schema_invalid.json")
    obs["observed_at"] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["reason_code"] == "SCHEMA_VALIDATION_FAILED"
    assert verdict["exit_code"] == 3


def test_precedence_hierarchy_rank4_freshness_over_rank5_policy() -> None:
    """Precedence: Rank 4 (Observation Stale) outranks Rank 5 (Policy Unapproved)."""
    engine = load_v3_engine(policy_path=str(FIXTURES_DIR / "pending_policy.yaml"))
    obs = load_fixture_json("observation_green.json")
    obs["observed_at"] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["reason_code"] == "OBSERVATION_STALE"
    assert verdict["exit_code"] == 3


def test_precedence_hierarchy_rank5_policy_over_rank6_quota() -> None:
    """Precedence: Rank 5 (Policy Unapproved) outranks Rank 6 (Quota Depleted)."""
    engine = load_v3_engine(policy_path=str(FIXTURES_DIR / "pending_policy.yaml"))
    obs = load_fixture_json("observation_red_depleted.json")
    obs["observed_at"] = datetime.now(timezone.utc).isoformat()

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["reason_code"] == "POLICY_NOT_APPROVED"
    assert verdict["exit_code"] == 2


def test_precedence_hierarchy_rank6_quota_over_rank7_concurrency() -> None:
    """Precedence: Rank 6 (Quota Depleted) outranks Rank 7 (Concurrency Limit Reached)."""
    engine = load_v3_engine()
    obs = load_fixture_json("observation_red_depleted.json")
    obs["observed_at"] = datetime.now(timezone.utc).isoformat()

    verdict = engine.evaluate(observation_payload=obs)
    assert verdict["reason_code"] == "QUOTA_DEPLETED"
    assert verdict["exit_code"] == 1


def test_precedence_hierarchy_rank7_concurrency_over_rank8_admission() -> None:
    """Precedence: Rank 7 (Concurrency Limit Reached) outranks Rank 8 (Admission Expired)."""
    registry = load_concurrency_registry()
    account_id = "08a4df52-9b3d-4d09-9bd5-af0f7e0e8043"
    pool_id = "codex"

    # Fill AMBER slot
    registry.acquire_dispatch_reservation(account_id, pool_id, "lane-1", "TICKET-1", "AMBER", 30)

    engine = load_v3_engine(concurrency_registry=registry)
    obs = load_fixture_json("observation_amber.json")
    obs["observed_at"] = datetime.now(timezone.utc).isoformat()
    evidence = load_fixture_json("admission_evidence_expired.json")

    verdict = engine.evaluate(observation_payload=obs, evidence=evidence)
    assert verdict["reason_code"] == "CONCURRENCY_LIMIT_REACHED"
    assert verdict["exit_code"] == 1


def test_exit_code_map_completeness_and_exact_mappings() -> None:
    """Validate completeness and exact mappings of EXIT_CODE_MAP against resume_plan.md."""
    exit_map = load_exit_code_map()
    for code, expected_exit in EXPECTED_EXIT_CODE_MAP.items():
        assert code in exit_map, f"Missing code in EXIT_CODE_MAP: {code}"
        assert exit_map[code] == expected_exit, f"Mismatch for {code}: expected {expected_exit}, got {exit_map[code]}"


# ============================================================================
# QuotaCollector Tests: Process Group, 64 KB Limit & Timeouts
# ============================================================================

def test_collector_process_group_termination() -> None:
    """Collector manages process group and cleanly terminates child process tree."""
    collector = load_quota_collector()
    # Execute a probe that times out and ensure child process group is terminated
    result = collector.collect_quota_observation(timeout_seconds=1, command=["sleep", "60"])
    assert result["reason_code"] == "COLLECTOR_TIMEOUT"
    assert result["exit_code"] == 3


def test_collector_stream_limit_64kb_protection() -> None:
    """Collector enforces 64 KB stream limit and rejects oversized stdio output."""
    collector = load_quota_collector()
    # Generate 70 KB of output to trigger stream limit protection
    oversized_cmd = [sys.executable, "-c", "import sys; sys.stdout.write('X' * 70000)"]
    result = collector.collect_quota_observation(timeout_seconds=5, command=oversized_cmd)
    assert result["reason_code"] == "COLLECTOR_OVERSIZED_RESPONSE"
    assert result["exit_code"] == 3


def test_collector_timeout_handling() -> None:
    """Collector handles subprocess timeout fail-closed -> COLLECTOR_TIMEOUT (Exit 3)."""
    collector = load_quota_collector()
    result = collector.collect_quota_observation(timeout_seconds=1, command=["sleep", "10"])
    assert result["reason_code"] == "COLLECTOR_TIMEOUT"
    assert result["exit_code"] == 3


def test_collector_auth_failure_handling() -> None:
    """Collector detects authentication failure on stdio -> COLLECTOR_AUTH_FAILURE (Exit 3)."""
    collector = load_quota_collector()
    auth_fail_cmd = [
        sys.executable,
        "-c",
        "import sys; sys.stdout.write('{\"error\": \"authentication_failed\", \"status\": 401}')",
    ]
    result = collector.collect_quota_observation(timeout_seconds=5, command=auth_fail_cmd)
    assert result["reason_code"] == "COLLECTOR_AUTH_FAILURE"
    assert result["exit_code"] == 3


# ============================================================================
# Integration CLI Tests: --refresh and Status Subcommand
# ============================================================================

def test_cli_refresh_command_with_red_observation() -> None:
    """CLI integration: python3 scripts/agent_quota_status_guard.py --refresh exits with 1 on RED."""
    result = subprocess.run(
        [
            sys.executable,
            str(GUARD_SCRIPT),
            "--refresh",
            "--observation",
            str(FIXTURES_DIR / "observation_red_depleted.json"),
            "--json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["exit_code"] == 1
    assert payload["tier"] == "RED"
    assert payload["host_resume_allowed"] is False
