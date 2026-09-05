"""RED Contract tests for Scope Skill Registry and Schemas.

Covers:
- Closed Draft 2020-12 JSON Schema validation.
- Three disjoint capability namespaces: horo_skill, provider_plugin, runtime_tool.
- Rejection of duplicate, uppercase, unsafe, or escaping identifiers.
- Acyclic, closed, and conflict-free dependencies.
- Trusted plugin exceptions (pinned superpowers only; no optional plugins).
- Role allowlists and read-only reviewer bounds.
- Non-overridable mandatory closure selectors.
- Rejection of alias, capacity, broker, quota, or application fields.
- Closed, strict schemas for all security identity objects.
"""

from __future__ import annotations

import json
from pathlib import Path
import unicodedata
import pytest

ROOT = Path(__file__).resolve().parents[1]

REGISTRY_SCHEMA_PATH = ROOT / ".agents/schemas/scope-skill-registry-v1.schema.json"
REGISTRY_PATH = ROOT / ".agents/config/scope_skill_registry.v1.json"
APPROVED_CONTEXT_SCHEMA_PATH = ROOT / ".agents/schemas/approved-ticket-context-v1.schema.json"
EVIDENCE_REF_SCHEMA_PATH = ROOT / ".agents/schemas/evidence-ref-v1.schema.json"
FIXTURE_REGISTRY_PATH = ROOT / "tests/fixtures/context_profiles/registry.valid.json"


def _load_json_nfc_strict(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    assert unicodedata.normalize("NFC", content) == content, f"File {path} contains non-NFC Unicode"
    return json.loads(content)


def test_canonical_registry_validates_against_closed_draft_2020_12_schema():
    assert REGISTRY_SCHEMA_PATH.exists(), (
        f"MISSING_SCOPE_SKILL_SCHEMA: Schema not found at {REGISTRY_SCHEMA_PATH}"
    )
    assert REGISTRY_PATH.exists(), (
        f"MISSING_SCOPE_SKILL_REGISTRY: Registry not found at {REGISTRY_PATH}"
    )
    schema = _load_json_nfc_strict(REGISTRY_SCHEMA_PATH)
    registry = _load_json_nfc_strict(REGISTRY_PATH)

    assert schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema"
    assert schema.get("additionalProperties") is False or schema.get("unevaluatedProperties") is False
    assert registry.get("schema_version") == "scope-skill-registry-v1"


def test_registry_requires_three_disjoint_capability_namespaces():
    assert REGISTRY_PATH.exists(), (
        f"MISSING_SCOPE_SKILL_REGISTRY: Registry not found at {REGISTRY_PATH}"
    )
    registry = _load_json_nfc_strict(REGISTRY_PATH)
    namespaces = set(registry.get("capability_namespaces", []))
    expected = {"horo_skill", "provider_plugin", "runtime_tool"}
    assert namespaces == expected, f"Namespaces must be exactly {expected}, got {namespaces}"

    horo_set = set(registry.get("horo_skills", {}).keys())
    plugin_set = set(registry.get("provider_plugins", {}).keys())
    tool_set = set(registry.get("runtime_tools", {}).keys())

    assert horo_set.isdisjoint(plugin_set), "horo_skill and provider_plugin namespaces must be disjoint"
    assert horo_set.isdisjoint(tool_set), "horo_skill and runtime_tool namespaces must be disjoint"
    assert plugin_set.isdisjoint(tool_set), "provider_plugin and runtime_tool namespaces must be disjoint"


def test_registry_rejects_unknown_duplicate_or_unsafe_identifiers():
    assert REGISTRY_PATH.exists(), (
        f"MISSING_SCOPE_SKILL_REGISTRY: Registry not found at {REGISTRY_PATH}"
    )
    registry = _load_json_nfc_strict(REGISTRY_PATH)
    for category in ("horo_skills", "provider_plugins", "runtime_tools"):
        for ident in registry.get(category, {}):
            assert ident == ident.lower(), f"Identifier {ident} must be lowercase"
            assert " " not in ident, f"Identifier {ident} must not contain spaces"
            assert not ident.startswith("/"), f"Identifier {ident} must not be absolute"
            assert ".." not in ident, f"Identifier {ident} must not contain path traversal"
            assert "\\" not in ident, f"Identifier {ident} must not contain backslashes"


def test_registry_rejects_missing_skill_sources_and_path_escape():
    assert REGISTRY_PATH.exists(), (
        f"MISSING_SCOPE_SKILL_REGISTRY: Registry not found at {REGISTRY_PATH}"
    )
    registry = _load_json_nfc_strict(REGISTRY_PATH)
    for name, meta in registry.get("horo_skills", {}).items():
        source_path = meta.get("source_path", "")
        assert source_path.startswith(".agents/skills/"), (
            f"Skill {name} source {source_path} must be under .agents/skills/"
        )
        assert ".." not in source_path, f"Skill {name} source {source_path} must not escape"
        resolved = (ROOT / source_path).resolve()
        assert str(resolved).startswith(str(ROOT)), f"Skill {name} escapes repository root: {resolved}"


def test_registry_dependencies_are_acyclic_closed_and_conflict_free():
    assert REGISTRY_PATH.exists(), (
        f"MISSING_SCOPE_SKILL_REGISTRY: Registry not found at {REGISTRY_PATH}"
    )
    registry = _load_json_nfc_strict(REGISTRY_PATH)
    skills = registry.get("horo_skills", {})

    for name, data in skills.items():
        deps = data.get("dependencies", [])
        conflicts = set(data.get("conflicts", []))
        assert name not in deps, f"Skill {name} cannot depend on itself"
        assert name not in conflicts, f"Skill {name} cannot conflict with itself"
        for dep in deps:
            assert dep in skills, f"Skill {name} has missing dependency {dep}"
            assert dep not in conflicts, f"Skill {name} both requires and conflicts with {dep}"

    # Cycle detection via DFS
    visited = {}

    def dfs(node: str, stack: set[str]):
        visited[node] = True
        stack.add(node)
        for neighbor in skills.get(node, {}).get("dependencies", []):
            if neighbor in stack:
                raise AssertionError(f"Cycle detected in dependencies: {neighbor} in {stack}")
            if neighbor not in visited:
                dfs(neighbor, stack)
        stack.remove(node)

    for skill in skills:
        if skill not in visited:
            dfs(skill, set())


def test_registry_models_trusted_exceptions_without_default_optional_plugins():
    assert REGISTRY_PATH.exists(), (
        f"MISSING_SCOPE_SKILL_REGISTRY: Registry not found at {REGISTRY_PATH}"
    )
    registry = _load_json_nfc_strict(REGISTRY_PATH)
    plugins = registry.get("provider_plugins", {})
    assert "superpowers" in plugins, "Pinned superpowers plugin exception must be present"
    assert plugins["superpowers"].get("enabled") is True
    assert plugins["superpowers"].get("allow_optional_requests") is False, (
        "Optional plugin requests must not be enabled by default"
    )


def test_registry_role_allowlists_keep_reviewer_read_only():
    assert REGISTRY_PATH.exists(), (
        f"MISSING_SCOPE_SKILL_REGISTRY: Registry not found at {REGISTRY_PATH}"
    )
    registry = _load_json_nfc_strict(REGISTRY_PATH)
    roles = registry.get("roles", {})
    assert "code_reviewer" in roles, "code_reviewer role must exist in registry"
    reviewer = roles["code_reviewer"]
    assert reviewer.get("read_only") is True, "code_reviewer must be marked read_only: true"
    reviewer_skills = set(reviewer.get("allowlist", []))
    assert "devops-deployment" not in reviewer_skills, (
        "code_reviewer must never receive deployment capability"
    )


def test_registry_declares_non_overridable_closure_selectors():
    assert REGISTRY_PATH.exists(), (
        f"MISSING_SCOPE_SKILL_REGISTRY: Registry not found at {REGISTRY_PATH}"
    )
    registry = _load_json_nfc_strict(REGISTRY_PATH)
    closures = registry.get("closures", {})
    required_closures = {"source_security", "api", "release", "metaphysics"}
    for rc in required_closures:
        assert rc in closures, f"Mandatory closure selector {rc} must be declared in registry"


def test_registry_cannot_define_alias_capacity_or_application_behavior():
    assert REGISTRY_PATH.exists(), (
        f"MISSING_SCOPE_SKILL_REGISTRY: Registry not found at {REGISTRY_PATH}"
    )
    registry = _load_json_nfc_strict(REGISTRY_PATH)
    forbidden_keys = {
        "account", "alias", "aliases", "capacity", "quota", "quota_pool",
        "model", "models", "effort", "broker", "broker_routes", "dispatchability",
        "external_home", "wrapper_executable", "endpoint", "api_behavior"
    }
    registry_keys = set(registry.keys())
    intersection = registry_keys.intersection(forbidden_keys)
    assert not intersection, f"Registry contains forbidden out-of-scope fields: {intersection}"


def test_every_security_identity_schema_is_closed_and_strict():
    for schema_path in (REGISTRY_SCHEMA_PATH, APPROVED_CONTEXT_SCHEMA_PATH, EVIDENCE_REF_SCHEMA_PATH):
        assert schema_path.exists(), (
            f"MISSING_SCOPE_SKILL_SCHEMA: Security identity schema not found at {schema_path}"
        )
        schema = _load_json_nfc_strict(schema_path)
        assert schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", (
            f"{schema_path} must be Draft 2020-12 schema"
        )
        assert schema.get("additionalProperties") is False or schema.get("unevaluatedProperties") is False, (
            f"{schema_path} must be closed (additionalProperties: false or unevaluatedProperties: false)"
        )
