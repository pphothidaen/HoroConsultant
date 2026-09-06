"""Context G contract: native skill binding without widening unrelated authority.

The preservation digest freezes the pre-repair registry's semantic content.
Only the new skill and its devops/qa_tester memberships may be added.
Positive resolution tests read the actual canonical contexts and registry.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import resolve_agent_context as resolver


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / ".agents/config/scope_skill_registry.v1.json"
SKILL = "multi-account-agent-orchestration"
SOURCE = f".agents/skills/{SKILL}/SKILL.md"
DESCRIPTION = "Route bounded agent work across accounts with quota evidence and HITL gates."
G_TICKET = "TICKET-CONTEXT-OPT-001-G"
QA_TICKET = "TICKET-CONTEXT-OPT-001"
QA_LANE = "TICKET-CONTEXT-OPT-001-B"
PRE_REPAIR_REGISTRY_SHA256 = "c3b57accafc4b215f10bd9ffcfeae985793ad7c8c9fa70a1d9cb974cf2c10aac"


def context_path(ticket):
    return ROOT / ".agents/context/tickets" / f"{ticket}.v1.json"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_native_orchestration_skill_has_exact_registered_metadata():
    native = (ROOT / SOURCE).read_text(encoding="utf-8")
    assert f"name: {SKILL}\n" in native
    assert f"description: {DESCRIPTION}\n" in native
    expected = {
        "source_path": SOURCE,
        "description": DESCRIPTION,
        "dependencies": [],
        "conflicts": [],
    }
    assert read_json(REGISTRY)["horo_skills"].get(SKILL) == expected, "MISSING_ORCHESTRATION_METADATA"


@pytest.mark.parametrize("role", ["devops", "qa_tester"])
def test_required_roles_allow_orchestration_skill(role):
    allowlist = read_json(REGISTRY)["roles"][role]["allowlist"]
    assert allowlist.count(SKILL) == 1, f"MISSING_ORCHESTRATION_ALLOWLIST: {role}"


def test_registry_preserves_every_unrelated_role_and_permission():
    remaining = copy.deepcopy(read_json(REGISTRY))
    remaining["horo_skills"].pop(SKILL, None)
    for role in ("devops", "qa_tester"):
        remaining["roles"][role]["allowlist"] = [
            item for item in remaining["roles"][role]["allowlist"] if item != SKILL
        ]
    canonical = json.dumps(remaining, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(canonical).hexdigest() == PRE_REPAIR_REGISTRY_SHA256, (
        "UNRELATED_REGISTRY_AUTHORITY_CHANGED"
    )


@pytest.mark.parametrize(
    "ticket,lane_id,role,requested",
    [
        (G_TICKET, G_TICKET, "devops", ["devops-deployment", "hf-static-release-verification", SKILL]),
        (QA_TICKET, QA_LANE, "qa_tester", ["qa-e2e-testing", "agile-governance", SKILL]),
    ],
)
def test_canonical_required_skill_requests_are_preserved(ticket, lane_id, role, requested):
    lane = next(item for item in read_json(context_path(ticket))["lanes"] if item["lane_id"] == lane_id)
    assert lane["role"] == role
    assert lane["requested_horo_skills"] == requested, "REQUIRED_SKILL_REQUEST_CHANGED"


@pytest.mark.parametrize(
    "ticket,lane_id,role",
    [(G_TICKET, G_TICKET, "devops"), (QA_TICKET, QA_LANE, "qa_tester")],
)
def test_canonical_context_resolves_with_required_orchestration(ticket, lane_id, role):
    # Turn a resolver's explicit rejection into a readable contract assertion;
    # unrelated setup/import/file errors remain errors and cannot count as RED.
    error = None
    result = None
    try:
        result = resolver.resolve_context_for_lane(
            registry_path=REGISTRY,
            approved_context_path=context_path(ticket),
            lane_id=lane_id,
            command_argv=("python3", "scripts/resolve_agent_context.py"),
        )
    except ValueError as exc:
        error = str(exc)
    assert error is None, f"REQUIRED_ORCHESTRATION_RESOLUTION_REJECTED: {role}: {error}"
    assert result["role"] == role
    assert SKILL in result["horo_skills"]
    assert set(result["closures"]) >= {"api", "source_security"}
    assert "context.resolve" in result["effective_actions"]


@pytest.mark.parametrize(
    "requested,expected",
    [
        ("unregistered-context-g-capability", "UNKNOWN_CAPABILITY"),
        ("devops-deployment", "UNAUTHORIZED_CAPABILITY"),
    ],
)
def test_resolver_still_rejects_unknown_and_disallowed_capabilities(requested, expected):
    path = context_path(QA_TICKET)
    document = read_json(path)
    lane = next(item for item in document["lanes"] if item["lane_id"] == QA_LANE)
    lane["requested_horo_skills"] = [requested]
    original_read = Path.read_text

    def read_negative_context(file_path, *args, **kwargs):
        # Substitute only this negative input in memory; retain actual registry,
        # parsing and resolver behavior, without editing approved context files.
        if file_path == path:
            return json.dumps(document)
        return original_read(file_path, *args, **kwargs)

    with patch.object(Path, "read_text", read_negative_context):
        with pytest.raises(ValueError, match=rf"^{expected}:.*{requested}"):
            resolver.resolve_context_for_lane(
                registry_path=REGISTRY,
                approved_context_path=path,
                lane_id=QA_LANE,
                command_argv=("python3", "scripts/resolve_agent_context.py"),
            )
