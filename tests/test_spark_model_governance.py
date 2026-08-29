"""Regression test suite for restricted model and Spark governance.

Tests cover fail-closed validation for role-restricted models (e.g. gpt-5.3-codex-spark)
and effort requirements for rank-3 planning under Rule 18 and AI SDLC multi-agent policy.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.multiagent_prompt_command as command


def _policy() -> dict[str, object]:
    return command.load_model_policy(ROOT / ".agents/config/multiagent_model_policy.yaml")


def _decision(**overrides: object) -> dict[str, object]:
    """Return a valid v1 decision for testing."""
    decision: dict[str, object] = {
        "schema_version": 1,
        "ticket": "TICKET-SPARK-GOV-TEST",
        "phase": "release",
        "scope_rank": 3,
        "complexity_rank": 3,
        "risk_rank": 1,
        "ambiguity_rank": 1,
        "evidence_burden_rank": 3,
        "quota_band": "healthy",
        "work_mode": "mutation",
        "selected_alias": "codex1",
        "selected_model": "gpt-5.3-codex-spark",
        "selected_effort": "high",
        "rationale": "spark safety governance test",
        "policy_version": _policy()["policy_version"],
        "planning_to_medium_confirmed": True,
        "hitl_approved": False,
    }
    decision.update(overrides)
    return decision


def _route(
    role: str = "devops",
    alias: str = "codex1",
    model: str = "gpt-5.3-codex-spark",
    effort: str = "high",
) -> command.Route:
    return command.Route(
        role=role,
        alias=alias,
        cli="codex",
        command="codex",
        home_env="CODEX_HOME",
        home_path=None,
        model=model,
        effort=effort,
        mode=None,
        sandbox="workspace-write",
    )


def test_restricted_model_rejected_without_route():
    """Verifies that a model with allowed_roles (like Spark) fails if validated with route=None."""
    policy = _policy()
    decision = _decision()

    with pytest.raises(
        command.DispatchDecisionError,
        match="role-restricted and requires a bound Route",
    ):
        command.validate_dispatch_decision(decision, policy, route=None)


@pytest.mark.parametrize("unauthorized_role", ["developer", "qa_tester", "business_analyst"])
def test_spark_rejected_for_unauthorized_role(unauthorized_role: str):
    """Verifies that an unauthorized role attempting to use gpt-5.3-codex-spark is rejected."""
    policy = _policy()
    route = _route(role=unauthorized_role)
    decision = _decision()

    with pytest.raises(
        command.DispatchDecisionError,
        match=r"restricted to roles: .*; got " + unauthorized_role,
    ):
        command.validate_dispatch_decision(decision, policy, route=route)


@pytest.mark.parametrize("unauthorized_phase", ["planning", "implementation"])
def test_spark_rejected_for_unauthorized_phase(unauthorized_phase: str):
    """Verifies that an unauthorized phase attempting to use gpt-5.3-codex-spark is rejected."""
    policy = _policy()
    route = _route(role="devops")
    decision = _decision(phase=unauthorized_phase)

    with pytest.raises(
        command.DispatchDecisionError,
        match=r"restricted to phases: .*; got " + unauthorized_phase,
    ):
        command.validate_dispatch_decision(decision, policy, route=route)


@pytest.mark.parametrize("role", ["devops", "code_reviewer"])
@pytest.mark.parametrize("phase", ["review", "release", "operations", "qa"])
def test_spark_allowed_for_authorized_role_and_phase(role: str, phase: str):
    """Verifies that devops or code_reviewer in authorized phases is approved."""
    policy = _policy()
    route = _route(role=role)
    decision = _decision(phase=phase)

    validated = command.validate_dispatch_decision(decision, policy, route=route)
    assert validated.quality_floor == 3
    assert validated.model_quality_rank == 3
    assert validated.decision["selected_model"] == "gpt-5.3-codex-spark"
    assert validated.decision["selected_effort"] == "high"
    assert validated.decision["phase"] == phase


def test_developer_rank_3_planning_requires_xhigh():
    """Verifies that rank-3 planning phase enforces xhigh effort for gpt-5.6-sol."""
    policy = _policy()
    route_xhigh = _route(
        role="developer",
        model="gpt-5.6-sol",
        effort="xhigh",
    )

    # Valid xhigh planning succeeds
    planning_xhigh = _decision(
        phase="planning",
        scope_rank=3,
        complexity_rank=3,
        evidence_burden_rank=3,
        selected_model="gpt-5.6-sol",
        selected_effort="xhigh",
        planning_to_medium_confirmed=False,
    )
    validated = command.validate_dispatch_decision(planning_xhigh, policy, route=route_xhigh)
    assert validated.quality_floor == 3
    assert validated.model_quality_rank == 3

    # High effort (quality_rank 3, but not xhigh/max/ultra) is rejected for rank-3 planning
    route_high = replace(route_xhigh, effort="high")
    planning_high = _decision(
        phase="planning",
        scope_rank=3,
        complexity_rank=3,
        evidence_burden_rank=3,
        selected_model="gpt-5.6-sol",
        selected_effort="high",
        planning_to_medium_confirmed=False,
    )
    with pytest.raises(
        command.DispatchDecisionError,
        match="rank-3 planning requires the cataloged planning model with xhigh",
    ):
        command.validate_dispatch_decision(planning_high, policy, route=route_high)

    # Lower efforts (medium, low) are rejected as below quality floor
    for lower_effort in ("medium", "low"):
        route_lower = replace(route_xhigh, effort=lower_effort)
        planning_lower = _decision(
            phase="planning",
            scope_rank=3,
            complexity_rank=3,
            evidence_burden_rank=3,
            selected_model="gpt-5.6-sol",
            selected_effort=lower_effort,
            planning_to_medium_confirmed=False,
        )
        with pytest.raises(command.DispatchDecisionError):
            command.validate_dispatch_decision(planning_lower, policy, route=route_lower)
