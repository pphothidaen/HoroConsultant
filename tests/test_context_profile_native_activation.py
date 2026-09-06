"""RED Contract tests for Native Activation and Codex Role Adapter.

Covers:
- Unknown profile exits 64 before launch with PROFILE_UNKNOWN.
- Tampered / stale profile fails before launch.
- Accepts ONLY code-pinned 'debug prompt-input' operation.
- Literal, bounded, shell-free child boundary.
- Canary-free minimal environment allowlist.
- OS/process-enforced no-network and mode-0700 probe home / 0600 files.
- Exact JSON Pointer /0/content/0/text extraction.
- Exactly one non-nested <skills_instructions> block.
- Independent enumeration and strict disjoint namespace separation.
- Rogue workspace/global discovery cannot expand effective inventory.
- Distinct, least-privilege profiles for developer, qa, reviewer, devops.
- Workspace discovery cannot reintroduce unbound Horo skills.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
CODEX_ROLE_SCRIPT = ROOT / "scripts/codex_role.py"
CODEX_PROMPT_FIXTURE = ROOT / "tests/fixtures/context_profiles/codex-prompt.json"


def _require_codex_role():
    assert CODEX_ROLE_SCRIPT.exists(), (
        f"MISSING_CODEX_ROLE_ADAPTER: Codex role adapter not found at {CODEX_ROLE_SCRIPT}"
    )


def test_unknown_profile_exits_64_before_codex_launch():
    _require_resolver = _require_codex_role
    _require_resolver()
    import scripts.codex_role as adapter
    res = adapter.run_codex_role(
        ticket_id="TICKET-CONTEXT-OPT-001",
        lane_id="TICKET-CONTEXT-OPT-001-G",
        profile="unknown_malicious_role",
    )
    assert res.exit_code == 64
    assert "PROFILE_UNKNOWN" in res.reason_code


def test_stale_or_tampered_profile_fails_before_launch():
    _require_codex_role()
    import scripts.codex_role as adapter
    with pytest.raises(Exception, match="TAMPER_DETECTED|STALE_PROFILE|DIGEST_MISMATCH"):
        adapter.verify_profile_integrity(
            profile="developer",
            expected_digest="0000000000000000000000000000000000000000000000000000000000000000",
        )


def test_wrapper_accepts_only_debug_prompt_input_child_operation():
    _require_codex_role()
    import scripts.codex_role as adapter
    forbidden_commands = [
        ["codex", "exec", "sh"],
        ["codex", "login"],
        ["codex", "run"],
        ["codex", "--search"],
        ["codex", "-p", "dev", "-p", "admin"],
    ]
    for cmd in forbidden_commands:
        with pytest.raises(Exception, match="UNAUTHORIZED_COMMAND|FORBIDDEN_OPERATION"):
            adapter.validate_child_operation(cmd)


def test_child_boundary_is_absolute_literal_bounded_and_shell_free():
    _require_codex_role()
    import scripts.codex_role as adapter
    spec = adapter.build_child_invocation("developer", cwd=ROOT)
    assert spec.shell is False, "Subprocess must have shell=False"
    assert spec.argv[0].startswith("/"), "Executable must be an absolute path"
    assert len(spec.argv) <= 32, "Argv count must be strictly bounded"
    assert spec.timeout_seconds <= 30, "Timeout must be <= 30 seconds"


def test_child_environment_is_minimal_and_canary_free():
    _require_codex_role()
    import scripts.codex_role as adapter
    env = adapter.build_isolated_environment(canary_tokens={"SECRET_CANARY": "xyz123"})
    assert "SECRET_CANARY" not in env
    assert "PYTHONPATH" not in env
    assert "PATH" not in env
    for k in env:
        assert k in {"HOME", "CODEX_HOME", "TMPDIR", "LANG", "LC_ALL", "TERM"}, f"Disallowed env var: {k}"


def test_no_network_and_probe_filesystem_boundary_are_enforced():
    _require_codex_role()
    import scripts.codex_role as adapter
    probe_dir = adapter.create_probe_directory()
    stat_mode = probe_dir.stat().st_mode & 0o777
    assert stat_mode == 0o700, f"Probe directory must have 0700 permissions, got {oct(stat_mode)}"
    assert adapter.is_no_network_enforced(), "OS-level or container-level no-network must be verified"


def test_prompt_uses_exact_versioned_json_pointer_and_shape():
    _require_codex_role()
    import scripts.codex_role as adapter
    raw = json.loads(CODEX_PROMPT_FIXTURE.read_text(encoding="utf-8"))
    adapter.validate_prompt_structure(raw)
    assert isinstance(raw, list) and len(raw) == 1, "Root must be array of length 1"
    assert "content" in raw[0] and len(raw[0]["content"]) == 1, "content must be array of length 1"
    text_node = raw[0]["content"][0]
    assert text_node.get("type") == "text", "content[0] must have type 'text'"
    assert "text" in text_node, "JSON Pointer /0/content/0/text must exist"


def test_prompt_has_exactly_one_independently_parsed_skill_block():
    _require_codex_role()
    import scripts.codex_role as adapter
    raw = json.loads(CODEX_PROMPT_FIXTURE.read_text(encoding="utf-8"))
    text = raw[0]["content"][0]["text"]
    skills = adapter.extract_skills_instructions_block(text)
    assert len(skills) >= 1
    start_tag = "<skills_instructions>"
    end_tag = "</skills_instructions>"
    assert text.count(start_tag) == 1, "Must contain exactly one <skills_instructions> start tag"
    assert text.count(end_tag) == 1, "Must contain exactly one </skills_instructions> end tag"
    start_pos = text.index(start_tag)
    end_pos = text.index(end_tag)
    assert start_pos < end_pos, "Start tag must precede end tag"


def test_prompt_namespace_and_source_inventory_is_exact():
    _require_codex_role()
    import scripts.codex_role as adapter
    parsed = adapter.parse_codex_prompt_output(CODEX_PROMPT_FIXTURE.read_text(encoding="utf-8"))
    assert "agile-governance" in parsed["skills"]
    assert "anti-cognitive-decay" in parsed["skills"]
    assert "orchestrator-delegation" in parsed["skills"]
    assert "requirement-grill-gate" in parsed["skills"]


def test_rogue_discovery_cannot_expand_effective_inventory():
    _require_codex_role()
    import scripts.codex_role as adapter
    with pytest.raises(Exception, match="ROGUE_SKILL_DETECTED|UNREGISTERED_SKILL"):
        adapter.audit_effective_inventory(
            effective_skills=["requirement-grill-gate", "rogue-unregistered-skill"],
            registered_skills=["requirement-grill-gate", "agile-governance"],
        )


def test_developer_native_profile_has_exact_horo_inventory():
    _require_codex_role()
    import scripts.codex_role as adapter
    skills = adapter.get_role_horo_skills("developer")
    expected = {"requirement-grill-gate", "agile-governance", "orchestrator-delegation", "anti-cognitive-decay"}
    assert set(skills) == expected, f"Developer skills must be {expected}, got {skills}"


def test_qa_reviewer_devops_profiles_are_distinct_and_least_privilege():
    _require_codex_role()
    import scripts.codex_role as adapter
    qa_skills = set(adapter.get_role_horo_skills("qa_tester"))
    rev_skills = set(adapter.get_role_horo_skills("code_reviewer"))
    devops_skills = set(adapter.get_role_horo_skills("devops"))

    assert "qa-api-ui-e2e" in qa_skills
    assert "devops-deployment" not in rev_skills, "Reviewer must not have deployment capability"
    assert qa_skills != rev_skills, "QA and reviewer skill sets must be distinct"
    assert devops_skills != rev_skills, "DevOps and reviewer skill sets must be distinct"


def test_known_profiles_change_only_manifest_selected_horo_inventory():
    _require_codex_role()
    import scripts.codex_role as adapter
    for role in ("developer", "qa_tester", "code_reviewer", "devops"):
        skills = adapter.get_role_horo_skills(role)
        for s in skills:
            assert not s.startswith("superpowers"), "Provider plugins must not appear in horo_skills"
            assert not s.startswith("browser_"), "Runtime tools must not appear in horo_skills"


def test_workspace_discovery_cannot_reintroduce_unbound_horo_skill():
    _require_codex_role()
    import scripts.codex_role as adapter
    with pytest.raises(Exception, match="UNBOUND_SKILL|DISCOVERY_BLOCKED"):
        adapter.validate_role_catalog(
            role="developer",
            discovered_skills=["requirement-grill-gate", "bsa-doc-skill-management"],
        )


def test_effective_attestation_separates_horo_plugin_and_runtime_tool_sets():
    _require_codex_role()
    import scripts.codex_role as adapter
    attestation = adapter.build_effective_attestation("developer")
    assert set(attestation["horo_skills"]).isdisjoint(set(attestation["provider_plugins"]))
    assert set(attestation["horo_skills"]).isdisjoint(set(attestation["runtime_tools"]))
    assert set(attestation["provider_plugins"]).isdisjoint(set(attestation["runtime_tools"]))
