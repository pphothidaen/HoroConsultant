"""Regression coverage for recovery audit context binding."""

import json

import pytest

from scripts import resolve_agent_context as resolver


def resolve(tmp_path, *, role="ba_auditor", skills=None, revision=1):
    context = {
        "revision": revision,
        "lanes": [{
            "lane_id": "TICKET-META-008-AUDIT",
            "role": role,
            "phase": "review",
            "actions": ["context.resolve"],
            "touched_paths": ["ATOMIC_TICKET.md"],
            "requested_horo_skills": skills or ["qa-regression-provenance"],
        }],
    }
    path = tmp_path / "context.json"
    path.write_text(json.dumps(context), encoding="utf-8")
    return context, resolver.resolve_context_for_lane(
        resolver.REGISTRY_PATH, path, "TICKET-META-008-AUDIT"
    )


def test_recovery_digest_binds_context_and_changes_with_revision(tmp_path):
    context, first = resolve(tmp_path)
    expected = resolver.domain_sha256(resolver.PREFIX_APPROVED_CONTEXT, context)
    assert first["approved_context_sha256"] == expected
    _, second = resolve(tmp_path, revision=2)
    assert second["approved_context_sha256"] != expected


def test_recovery_auditor_retains_requested_skill_and_dependency(tmp_path):
    _, result = resolve(tmp_path)
    assert {"qa-regression-provenance", "agile-governance"} <= set(result["horo_skills"])


def test_unknown_role_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="UNKNOWN_ROLE"):
        resolve(tmp_path, role="unregistered_auditor")


def test_disallowed_skill_is_rejected_instead_of_dropped(tmp_path):
    with pytest.raises(ValueError, match="UNAUTHORIZED_CAPABILITY"):
        resolve(tmp_path, role="developer")


def test_unknown_requested_skill_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="UNKNOWN_CAPABILITY"):
        resolve(tmp_path, skills=["nonexistent-skill"])
