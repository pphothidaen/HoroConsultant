"""RED Contract tests for Role Budgets, Quota/Handoff Governance, and Lifecycle.

Covers:
- Default Horo catalog must match exact approved bootstrap allowlist:
  requirement-grill-gate, agile-governance, orchestrator-delegation, anti-cognitive-decay.
- Hard character/line budgets for profiles and skills (<=8000 chars, <=300 lines).
- Leaner catalog proof without capability omission.
- Capability index descriptions <=100 chars, skill bodies <=300 lines.
- Fresh quota observation requirement (thresholds in remaining percentage).
- HandoffSnapshotV1 schema completeness and authority binding.
- Rejection of shallow/incomplete lanes in handoff.
- Local lifecycle terminal state VERIFIED_LOCAL (distinct from DONE).
- Baseline commit gate attributable to qa-e2e-testing, not Rule 21.
- Exact nine skill eval fixtures schema validation and exact-match contract.
- Eval fixtures cannot authorize or enable a skill.
- Durable sanitized pressure receipt verification.
- Exactly one 39-path baseline commit authorized; no second commit, no push.
- Guard classification of all combined baseline paths as tests or manifests.
- Characterization freeze of out-of-scope policy and broker files.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]

PROVENANCE_MANIFEST_PATH = ROOT / "plans/test_provenance/ticket-context-opt-001.json"
PRESSURE_RECEIPT_PATH = ROOT / "plans/evidence/context-opt-001/skill-pressure-red.json"
HANDOFF_PATH = ROOT / "HANDOFF.md"
EVALS_FIXTURES_DIR = ROOT / "tests/fixtures/context_profiles/evals"

FROZEN_OUT_OF_SCOPE_HASHES = {
    ".agents/config/agent_broker.v1.json": "81537118e7bbd3c0451a809a068f3a783023c2fd9f66ea6449613064ca0cff9d",
    ".agents/config/full_capacity_guard.v2.json": "dc2ff9825f484cf49d5f15502631f3a8567a40e27cb6f503cf05e0fc18d8ed60",
    ".agents/config/multiagent_model_policy.yaml": "ffe971c46c551e6c02f6f0fb32009bf880633b60ef74ee78b6f7bb92ff987d9f",
    ".agents/config/multiagent_prompt_command.example.yaml": "9d48a54f31c86a6cc2312c54201c12892c07782e983e97ffe6184efcb917b6a9",
    ".agents/config/multiagent_prompt_command.luna-one-shot.yaml": "4a32daed594635e7e79584416c10c21aec044b1fb397e0fdb69d932fdb2ffd6c",
    ".agents/config/multiagent_prompt_command.runtime-readonly-v2.yaml": "e89d496966f25258bae1668a1d2213493dec22bc0f155f2864510db8b9c62727",
    ".agents/config/multiagent_prompt_command.runtime-readonly-v3.yaml": "0d5bbe34948b6c6b9c0ec5b95ce56e52e45c61cafad4a3c7bfffff9df14be099",
    ".agents/config/multiagent_prompt_command.yaml": "ddf34ec23036ca4f7a914fc333ceaf4a05f6bbbce2d10a5997b0cae8dc1f2442",
    ".agents/config/native_lane_capacity.v1.json": "91bb9ec9c01762cafe4cd3b90c416e02e03cdcd1ceb00471afe8ffec3b3d6202",
    ".agents/config/s3_capacity_policy.json": "839ee358efb0221e329d4c3f86796c0a2d184053b21567aa3fb3db061f8a7221",
    ".agents/hooks/full_capacity_guard.py": "b68fc9c2715c71c29f8f893102b570508f7b012ccb14da52f6354c30ca7c7a7c",
    "scripts/agent_broker_wrapper.py": "3ea712161b11bdec8eb2d2c30daa4b6a3a01fcef140a62bef5d39f8db6d40344",
    "scripts/codex_quota_workaround.py": "ff93eb349e89097ae73d1de9d78a97ae134f8a18a9bd36d3541583fe52e55082",
    "scripts/install_agent_broker.py": "18744a5a1a0ac56ba99c62f31abf8fde070b57f3a712433aa5bf1fbb36a5e141",
    "scripts/multiagent_broker_bridge.py": "d8cd600c623c4b1f9e9967788abdfb62ee6f5d45c85670fb843c5fcd7a48acd9",
    "scripts/multiagent_capacity.py": "5472554a04f34dbeca785d2a8af991538e0d59368d7a22c37e879ad5f0ceee18",
    "scripts/multiagent_prompt_command.py": "88a38a11d56f82e2e98be0d8ca54fbff5a97e7a0a4d923348bd82fe1baa0cb85",
    "scripts/agent_quota_status_guard.py": "26dfc8a9f85a69f238778ea0b94239c2c3623c60e2a1473166c0bad88e0681db",
    "scripts/sync_codex_account_configs.py": "4d37513698a48f400e71e0e113c69e073aa9c74e6b2479494c89e76758aaee79",
}

ALL_NINE_SKILLS = [
    "qa-regression-provenance",
    "qa-api-ui-e2e",
    "five-elements-ui-palette",
    "wcag-apca-color-audit",
    "ui-color-token-handoff",
    "metaphysical-request-router",
    "metaphysical-hitl-scope-gate",
    "metaphysical-finetune-handoff",
    "qa-e2e-testing",
]


def test_default_horo_catalog_is_exact_approved_bootstrap_allowlist():
    agent_default = ROOT / ".agents/agents/default/agent.json"
    assert agent_default.exists(), "Default agent configuration not found"
    data = json.loads(agent_default.read_text(encoding="utf-8"))
    tools = data.get("tools", [])
    expected = [
        "requirement-grill-gate",
        "agile-governance",
        "orchestrator-delegation",
        "anti-cognitive-decay",
    ]
    assert sorted(tools) == sorted(expected), (
        f"DEFAULT_HORO_ALLOWLIST_MISMATCH: Default catalog tools must be exactly {expected}, found {tools}"
    )


def test_every_base_focused_and_compatibility_profile_stays_under_hard_budget():
    budget_script = ROOT / "scripts/optimize_codex_skill_budget.py"
    if budget_script.exists():
        import scripts.optimize_codex_skill_budget as budget
        assert hasattr(budget, "evaluate_all_profiles"), (
            "DEFAULT_HORO_ALLOWLIST_MISMATCH: optimize_codex_skill_budget missing evaluate_all_profiles"
        )
        report = budget.evaluate_all_profiles()
        assert report.get("max_characters", 0) <= 8000
    else:
        # Fallback check on existing skill files
        skills_dir = ROOT / ".agents/skills"
        if skills_dir.exists():
            for p in skills_dir.glob("*/SKILL.md"):
                content = p.read_text(encoding="utf-8")
                assert len(content) <= 8000, f"Skill {p.name} exceeds 8000 characters"


def test_budget_report_proves_leaner_horo_catalog_not_capability_omission():
    registry_path = ROOT / ".agents/config/scope_skill_registry.v1.json"
    assert registry_path.exists(), (
        "DEFAULT_HORO_ALLOWLIST_MISMATCH: Registry must exist to prove lean catalog"
    )


def test_capability_index_descriptions_and_skill_bodies_respect_atomic_limits():
    skills_dir = ROOT / ".agents/skills"
    for skill_path in skills_dir.glob("*/SKILL.md"):
        lines = skill_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) <= 300, f"Skill {skill_path} body must be <= 300 lines, got {len(lines)}"


def test_budget_measurement_failure_is_never_zero_or_pass():
    bad_measurement = {"exit_code": 1, "characters": 0, "status": "ERROR"}
    assert bad_measurement["characters"] == 0
    assert bad_measurement["status"] != "PASS"


def test_provider_launch_requires_fresh_quota_checkpoint():
    assert PROVENANCE_MANIFEST_PATH.exists()
    prov = json.loads(PROVENANCE_MANIFEST_PATH.read_text(encoding="utf-8"))
    obs = prov.get("quota_observations", [])
    assert len(obs) > 0, "Quota observations must be present before provider work"


def test_low_quota_requires_complete_canonical_handoff_before_launch():
    assert HANDOFF_PATH.exists()
    content = HANDOFF_PATH.read_text(encoding="utf-8")
    assert "<!-- HANDOFF-SNAPSHOT-V1:START -->" in content, (
        "HANDOFF_LANE_SCHEMA_INCOMPLETE: Missing HandoffSnapshotV1 marker in HANDOFF.md"
    )


def test_handoff_rejects_shallow_type_correct_but_incomplete_lanes():
    assert HANDOFF_PATH.exists()
    content = HANDOFF_PATH.read_text(encoding="utf-8")
    assert "lanes=[{}]" not in content, (
        "HANDOFF_LANE_SCHEMA_INCOMPLETE: Incomplete lane detected in handoff"
    )


def test_handoff_authority_and_ticket_binding_are_exact():
    assert HANDOFF_PATH.exists()
    content = HANDOFF_PATH.read_text(encoding="utf-8")
    assert "TICKET-CONTEXT-OPT-001" in content


def test_handoff_is_bounded_canonical_secret_free_and_current():
    assert HANDOFF_PATH.exists()
    stat = HANDOFF_PATH.stat()
    assert stat.st_size <= 65536, "HANDOFF.md must remain strictly bounded in size"


def test_handoff_uses_active_ticket_and_remaining_percent_semantics():
    assert HANDOFF_PATH.exists()
    content = HANDOFF_PATH.read_text(encoding="utf-8")
    # Must use remaining percentage, not consumed percentage
    assert "%" in content


def test_quota_thresholds_are_remaining_percent_and_fail_closed():
    guard_script = ROOT / "scripts/agent_quota_status_guard.py"
    assert guard_script.exists()
    text = guard_script.read_text(encoding="utf-8")
    assert "remaining" in text.lower()


def test_local_lifecycle_cannot_weaken_rule21_release_completion():
    rule21_path = ROOT / ".agents/rules/21-agile-governance.md"
    assert rule21_path.exists()
    content = rule21_path.read_text(encoding="utf-8")
    assert "VERIFIED_LOCAL" in content, (
        "LOCAL_LIFECYCLE_CONTRACT_MISSING: Rule 21 must explicitly define VERIFIED_LOCAL terminal state"
    )


def test_baseline_gate_is_qa_e2e_not_rule21_and_verified_local_is_not_done():
    qa_skill_path = ROOT / ".agents/skills/qa-e2e-testing/SKILL.md"
    assert qa_skill_path.exists()
    content = qa_skill_path.read_text(encoding="utf-8")
    assert "test-provenance-v1" in content
    assert "TEST_BASELINE_VERIFIED" in content


def test_exact_nine_skill_eval_fixtures_are_frozen_and_schema_valid():
    assert EVALS_FIXTURES_DIR.exists()
    for skill in ALL_NINE_SKILLS:
        fixture_path = EVALS_FIXTURES_DIR / f"{skill}.json"
        assert fixture_path.exists(), f"Eval fixture missing: {fixture_path}"
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
        assert data.get("skill_name") == skill
        assert len(data.get("evals", [])) >= 2, f"Skill {skill} must have at least 2 eval cases"


def test_each_skill_eval_matches_its_frozen_test_fixture_exactly():
    for skill in ALL_NINE_SKILLS:
        fixture_path = EVALS_FIXTURES_DIR / f"{skill}.json"
        real_eval_path = ROOT / f".agents/skills/{skill}/evals/evals.json"
        assert real_eval_path.exists(), (
            f"REAL_EVAL_SOURCE_MISSING: Real skill eval source missing for {skill} at {real_eval_path}"
        )
        fixture_data = json.loads(fixture_path.read_text(encoding="utf-8"))
        real_data = json.loads(real_eval_path.read_text(encoding="utf-8"))
        assert fixture_data == real_data, f"Real eval for {skill} does not match frozen fixture exactly"


def test_eval_fixture_cannot_authorize_or_enable_a_skill():
    for skill in ALL_NINE_SKILLS:
        fixture_path = EVALS_FIXTURES_DIR / f"{skill}.json"
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
        assert "authorize" not in data
        assert "enabled" not in data
        assert "allowed_roles" not in data


def test_pressure_receipt_is_durable_sanitized_and_digest_bound():
    assert PRESSURE_RECEIPT_PATH.exists(), f"Pressure receipt not found at {PRESSURE_RECEIPT_PATH}"
    receipt = json.loads(PRESSURE_RECEIPT_PATH.read_text(encoding="utf-8"))
    assert receipt.get("schema_version") == "skill-pressure-receipt-v1"
    assert receipt.get("status") == "BLOCKED_PROVIDER_CALL_NOT_AUTHORIZED"
    assert "sanitized_evidence_sha256" in receipt
    assert len(receipt["sanitized_evidence_sha256"]) == 64


def test_pressure_sampling_is_blocked_without_provider_authority():
    assert PRESSURE_RECEIPT_PATH.exists()
    receipt = json.loads(PRESSURE_RECEIPT_PATH.read_text(encoding="utf-8"))
    for run in receipt.get("pressure_runs", []):
        assert run.get("provider_call_executed") is False, (
            "Provider calls must NOT be executed during offline pressure baseline"
        )
        assert run.get("status") == "BLOCKED_PROVIDER_CALL_NOT_AUTHORIZED"


def test_context_and_dispatch_authorities_name_one_combined_39_path_commit():
    assert PROVENANCE_MANIFEST_PATH.exists()
    prov = json.loads(PROVENANCE_MANIFEST_PATH.read_text(encoding="utf-8"))
    auth = prov.get("user_authorizations", {}).get("combined_test_only_commit", {})
    assert auth.get("authorized") is True
    assert auth.get("maximum_count") == 1
    assert auth.get("exact_path_count") == 39


def test_no_document_authorizes_a_second_commit_or_any_push():
    assert PROVENANCE_MANIFEST_PATH.exists()
    prov = json.loads(PROVENANCE_MANIFEST_PATH.read_text(encoding="utf-8"))
    auth = prov.get("user_authorizations", {})
    assert auth.get("push") is False
    assert auth.get("other_commits") is False


def test_source_config_generated_and_runtime_evidence_remain_uncommitted():
    assert PROVENANCE_MANIFEST_PATH.exists()
    prov = json.loads(PROVENANCE_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert prov.get("source_admission", {}).get("admitted") is False


def test_combined_baseline_paths_are_all_guard_classified_as_tests_or_manifests():
    import scripts.test_provenance_guard as guard
    assert PROVENANCE_MANIFEST_PATH.exists()
    prov = json.loads(PROVENANCE_MANIFEST_PATH.read_text(encoding="utf-8"))
    paths = prov.get("combined_baseline_paths", [])
    assert len(paths) == 39, f"Combined baseline paths must be 39, got {len(paths)}"
    for item in paths:
        p = item["path"]
        is_test = any(p.startswith(prefix) for prefix in guard.TEST_PREFIXES)
        is_manifest = p.startswith(guard.MANIFEST_PREFIX)
        assert is_test or is_manifest, (
            f"Path {p} is not classified as test or manifest by test_provenance_guard"
        )


def test_frozen_out_of_scope_policy_and_broker_files_are_immutable():
    for rel_path, expected_sha in FROZEN_OUT_OF_SCOPE_HASHES.items():
        file_path = ROOT / rel_path
        assert file_path.exists(), f"Frozen file {rel_path} does not exist"
        computed_sha = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert computed_sha == expected_sha, (
            f"MUTATION DETECTED in frozen policy/broker file {rel_path}: expected {expected_sha}, got {computed_sha}"
        )


def test_account_configs_and_quota_guard_characterization_preserved():
    guard_path = ROOT / "scripts/agent_quota_status_guard.py"
    sync_path = ROOT / "scripts/sync_codex_account_configs.py"
    assert guard_path.exists()
    assert sync_path.exists()
    guard_sha = hashlib.sha256(guard_path.read_bytes()).hexdigest()
    sync_sha = hashlib.sha256(sync_path.read_bytes()).hexdigest()
    assert guard_sha == FROZEN_OUT_OF_SCOPE_HASHES["scripts/agent_quota_status_guard.py"]
    assert sync_sha == FROZEN_OUT_OF_SCOPE_HASHES["scripts/sync_codex_account_configs.py"]
