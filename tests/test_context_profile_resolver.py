"""RED Contract tests for Context Resolver.

Covers:
- Set equation: root + role + phase + every action + every touched path + broad-to-narrow ancestors + transitive dependencies + immutable closures.
- Broad-to-narrow ancestor application.
- Multi-path union without cross-path subtraction.
- Strengthen-only descendant precedence (no root/closure policy weakening).
- Rejection of unknown, ambiguous, or escaping paths.
- Rejection of unknown or unauthorized capabilities.
- Binding of exact ticket, plan, and registry digests.
- Mandatory injection of immutable closures.
- Canonical ordering and secret-free output contract.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
RESOLVER_SCRIPT = ROOT / "scripts/resolve_agent_context.py"
REGISTRY_PATH = ROOT / ".agents/config/scope_skill_registry.v1.json"
FIXTURE_REGISTRY = ROOT / "tests/fixtures/context_profiles/registry.valid.json"
FIXTURE_APPROVED_CONTEXT = ROOT / "tests/fixtures/context_profiles/approved-context.valid.json"
FIXTURE_EXPECTED_DEV = ROOT / "tests/fixtures/context_profiles/expected-root-developer.json"
FIXTURE_EXPECTED_MULTI = ROOT / "tests/fixtures/context_profiles/expected-multi-path.json"


def _require_resolver():
    assert RESOLVER_SCRIPT.exists(), (
        f"MISSING_CONTEXT_RESOLVER: Context resolver script not found at {RESOLVER_SCRIPT}"
    )


def test_resolver_unions_root_role_phase_action_every_path_and_dependencies():
    _require_resolver()
    import scripts.resolve_agent_context as resolver
    res = resolver.resolve_context_for_lane(
        registry_path=FIXTURE_REGISTRY,
        approved_context_path=FIXTURE_APPROVED_CONTEXT,
        lane_id="TICKET-CONTEXT-OPT-001-D",
        command_argv=("python3", "scripts/resolve_agent_context.py"),
    )
    expected = json.loads(FIXTURE_EXPECTED_DEV.read_text(encoding="utf-8"))
    assert set(res["horo_skills"]) == set(expected["horo_skills"])
    assert set(res["provider_plugins"]) == set(expected["provider_plugins"])


def test_resolver_applies_every_ancestor_broad_to_narrow():
    _require_resolver()
    import scripts.resolve_agent_context as resolver
    res = resolver.resolve_path_hierarchy(ROOT / "project/routers/v1/auth.py")
    expected_ancestors = ["root", "project", "project/routers"]
    for ancestor in expected_ancestors:
        assert ancestor in res["scopes"], f"Ancestor {ancestor} must be present in resolved scopes"


def test_multi_path_ticket_receives_union_without_cross_path_subtraction():
    _require_resolver()
    import scripts.resolve_agent_context as resolver
    res = resolver.resolve_multi_paths(
        paths=["project/core/engine.py", "project/routers/auth.py"]
    )
    expected = json.loads(FIXTURE_EXPECTED_MULTI.read_text(encoding="utf-8"))
    assert "project/core" in res["normalized_scopes"]
    assert "project/routers" in res["normalized_scopes"]
    assert "root" in res["normalized_scopes"]


def test_descendant_scope_may_strengthen_but_never_remove_root_policy():
    _require_resolver()
    import scripts.resolve_agent_context as resolver
    with pytest.raises(Exception, match="ROOT_POLICY_WEAKENING|BLOCKED"):
        resolver.apply_descendant_override(
            root_policy={"enforce_one_editor": True, "secret_scan": True},
            descendant_policy={"enforce_one_editor": False},
        )


def test_resolver_rejects_unknown_ambiguous_or_escaping_paths():
    _require_resolver()
    import scripts.resolve_agent_context as resolver
    unsafe_paths = [
        "../outside",
        "/etc/passwd",
        "project/../..",
        "project/core/\0nullbyte",
        "project\\core\\backslash",
    ]
    for p in unsafe_paths:
        with pytest.raises(Exception, match="UNSAFE_PATH|ESCAPE|INVALID_PATH"):
            resolver.normalize_and_validate_path(p, repo_root=ROOT)


def test_resolver_rejects_unknown_or_unauthorized_capability():
    _require_resolver()
    import scripts.resolve_agent_context as resolver
    with pytest.raises(Exception, match="UNKNOWN_CAPABILITY|UNAUTHORIZED"):
        resolver.resolve_capability("unregistered-super-power", registry_path=FIXTURE_REGISTRY)


def test_ticket_and_registry_digests_are_required_and_exact():
    _require_resolver()
    import scripts.resolve_agent_context as resolver
    with pytest.raises(Exception, match="DIGEST_MISMATCH|MISSING_DIGEST"):
        resolver.validate_context_digests(
            approved_context_path=FIXTURE_APPROVED_CONTEXT,
            expected_ticket_sha256="badhash0000000000000000000000000000000000000000000000000000000000",
        )


def test_required_closure_is_injected_and_cannot_be_omitted():
    _require_resolver()
    import scripts.resolve_agent_context as resolver
    res = resolver.resolve_context_for_lane(
        registry_path=FIXTURE_REGISTRY,
        approved_context_path=FIXTURE_APPROVED_CONTEXT,
        lane_id="TICKET-CONTEXT-OPT-001-D",
        command_argv=("python3", "scripts/resolve_agent_context.py"),
    )
    assert "source_security" in res["closures"], "source_security closure must be injected"
    assert "api" in res["closures"], "api closure must be injected"


def test_resolver_output_is_canonical_ordered_and_secret_free():
    _require_resolver()
    import scripts.resolve_agent_context as resolver
    res = resolver.resolve_context_for_lane(
        registry_path=FIXTURE_REGISTRY,
        approved_context_path=FIXTURE_APPROVED_CONTEXT,
        lane_id="TICKET-CONTEXT-OPT-001-D",
        command_argv=("python3", "scripts/resolve_agent_context.py"),
    )
    # Validate canonical ordering of list fields
    for field in ("horo_skills", "provider_plugins", "runtime_tools", "normalized_scopes", "closures"):
        items = res.get(field, [])
        assert items == sorted(items), f"Field {field} must be lexicographically sorted"
    # Ensure no token/secret leaked into output
    text_dump = json.dumps(res)
    for secret_word in ("bearer", "ghp_", "sk-", "password", "secret"):
        assert secret_word not in text_dump.lower(), f"Potential secret leak in resolver output: {secret_word}"
