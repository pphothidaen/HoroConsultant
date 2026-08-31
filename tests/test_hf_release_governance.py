"""Regression tests for the HF Static production-release governance contract."""

from __future__ import annotations

import json
import hashlib
import re
import shlex
from datetime import datetime
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
RULE = ROOT / ".agents" / "rules" / "16-hf-static-release-verification.md"
CLAUDE_RULE = ROOT / ".claude" / "rules" / "hf-static-release-verification.md"
SKILL = ROOT / ".agents" / "skills" / "hf-static-release-verification" / "SKILL.md"
EVALS = SKILL.parent / "evals" / "evals.json"
CATALOG = ROOT / ".agents" / "AGENTS.md"
SYNC_SCRIPT = ROOT / "scripts" / "sync_ai_agent_ecosystem.py"
POST_DEPLOY_EVIDENCE = (
    ROOT / "project" / "tests" / "artifacts" / "hf_post_deploy_v3_verification_2026-08-25.json"
)
VISUAL_REPORT = ROOT / "project" / "tests" / "artifacts" / "visual_layout_report.json"
CANONICAL_VIEWPORTS = {
    "desktop-4k",
    "laptop-standard",
    "tablet-portrait",
    "mobile-ios",
    "mobile-compact",
}


def _frontmatter(path: Path) -> tuple[dict[str, object], str]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} must start with YAML frontmatter"
    _, raw_frontmatter, body = text.split("---", 2)
    return yaml.safe_load(raw_frontmatter) or {}, body


def _agent(filename: str) -> dict[str, object]:
    path = ROOT / ".antigravity" / "agents" / filename
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_rule_and_claude_mirror_share_release_blockers() -> None:
    rule_text = RULE.read_text(encoding="utf-8")
    claude_data, claude_body = _frontmatter(CLAUDE_RULE)

    assert claude_data.get("description")
    assert claude_data.get("paths")
    for concept in (
        "SDK-aware",
        "fail-closed",
        "exact-cardinality",
        "five canonical viewport",
        "screenshots",
        "never hand-edit",
    ):
        assert concept.casefold() in rule_text.casefold()
        assert concept.casefold() in claude_body.casefold()

    for owner in ("devops", "qa_tester", "code_reviewer", "orchestrator"):
        assert f"`{owner}`" in rule_text
        assert owner in claude_body.casefold()


def test_skill_metadata_evals_owners_and_ascii_report_contract() -> None:
    metadata, body = _frontmatter(SKILL)
    assert metadata["name"] == "hf-static-release-verification"
    assert 1 <= len(str(metadata["description"])) <= 100
    assert metadata["owner"] == "devops"
    assert set(metadata["responsible_agents"]) == {
        "devops",
        "qa_tester",
        "code_reviewer",
        "orchestrator",
    }

    for tag in ("[OK]", "[ERROR]", "[WARNING]", "[INFO]"):
        assert tag in body
    assert "[ERROR] BLOCKED" in body
    assert "[OK] READY_FOR_PROD" in body

    eval_data = json.loads(EVALS.read_text(encoding="utf-8"))
    assert eval_data["skill_name"] == metadata["name"]
    assert len(eval_data["evals"]) >= 3
    assert all(
        item.get("prompt") and item.get("expected_output") and item.get("expectations")
        for item in eval_data["evals"]
    )


def test_skill_commands_reference_existing_repository_files() -> None:
    skill_text = SKILL.read_text(encoding="utf-8")
    commands = re.findall(r"^\s*(python3 .+)$", skill_text, flags=re.MULTILINE)
    assert commands

    referenced_paths: set[str] = set()
    for command in commands:
        parts = shlex.split(command)
        for part in parts:
            if part.endswith(".py"):
                referenced_paths.add(part)

    expected = {
        "scripts/publish_space_hf.py",
        "scripts/run_visual_layout_audit.py",
        "tests/test_publish_space_hf.py",
        "tests/test_hf_release_governance.py",
    }
    assert expected <= referenced_paths
    assert all((ROOT / path).is_file() for path in referenced_paths)
    explicit_target = "--space-id pphothidaen/horoconsultant-core-backend"
    assert skill_text.count(explicit_target) == 2


def test_authoritative_agents_own_distinct_release_responsibilities() -> None:
    contracts = {
        "devops.agent": "HF Static Release Gate Owner",
        "qa-tester.agent": "HF Static QA Evidence Owner",
        "qa_tester.agent": "HF Static QA Evidence Owner",
        "code-reviewer.agent": "HF Static Evidence Guard",
        "code_reviewer.agent": "HF Static Evidence Guard",
        "orchestrator.agent": "HF Static Final Decision Owner",
    }
    for filename, contract in contracts.items():
        agent = _agent(filename)
        assert "hf-static-release-verification" in agent.get("tools", [])
        assert contract in str(agent.get("system_prompt", ""))

    assert _agent("qa-tester.agent") == _agent("qa_tester.agent")
    assert _agent("code-reviewer.agent") == _agent("code_reviewer.agent")


def test_generated_agent_roles_match_authoritative_release_contracts() -> None:
    contracts = {
        "devops": "HF Static Release Gate Owner",
        "qa_tester": "HF Static QA Evidence Owner",
        "code_reviewer": "HF Static Evidence Guard",
        "orchestrator": "HF Static Final Decision Owner",
    }
    for owner, contract in contracts.items():
        agent_json = ROOT / ".agents" / "agents" / owner / "agent.json"
        codex_toml = ROOT / ".codex" / "agents" / f"{owner}.toml"
        downstream = json.loads(agent_json.read_text(encoding="utf-8"))
        codex_text = codex_toml.read_text(encoding="utf-8")
        assert "hf-static-release-verification" in downstream.get("tools", [])
        assert contract in downstream.get("system_prompt", "")
        assert "hf-static-release-verification" in codex_text
        assert contract in codex_text


def test_catalog_and_umbrella_gate_make_governance_enforceable() -> None:
    catalog_text = CATALOG.read_text(encoding="utf-8")
    sync_text = SYNC_SCRIPT.read_text(encoding="utf-8")
    assert "hf-static-release-verification" in catalog_text
    assert "def check_hf_static_release_governance()" in sync_text
    assert "check_hf_static_release_governance()," in sync_text


def test_generated_codex_roles_are_not_the_authoritative_edit_target() -> None:
    rule_text = RULE.read_text(encoding="utf-8")
    sync_text = SYNC_SCRIPT.read_text(encoding="utf-8")
    gate_start = sync_text.index("def check_hf_static_release_governance()")
    gate_end = sync_text.index("\ndef run_checks", gate_start)
    gate_source = sync_text[gate_start:gate_end]
    assert 'ROOT / ".antigravity" / "agents"' in gate_source
    assert 'ROOT / ".codex"' in gate_source
    assert ".write_text(" not in gate_source
    assert "never hand-edit them" in rule_text


def test_gradient_indeterminate_requires_documented_manual_resolution() -> None:
    rule_text = RULE.read_text(encoding="utf-8")
    _, claude_body = _frontmatter(CLAUDE_RULE)
    skill_text = SKILL.read_text(encoding="utf-8")
    for text in (rule_text, claude_body, skill_text):
        normalized = " ".join(text.casefold().split())
        assert "unresolved indeterminate" in normalized
        assert "manual reviewer" in normalized
        for field in ("viewport", "finding", "reviewer", "decision", "timestamp"):
            assert field in normalized


def test_rule_uses_explicit_space_id_for_both_live_gates() -> None:
    rule_text = RULE.read_text(encoding="utf-8")
    target = "--space-id pphothidaen/horoconsultant-core-backend"
    assert rule_text.count(target) == 2


def test_post_deploy_manual_gradient_evidence_is_current_and_complete() -> None:
    evidence = json.loads(POST_DEPLOY_EVIDENCE.read_text(encoding="utf-8"))
    report = json.loads(VISUAL_REPORT.read_text(encoding="utf-8"))
    visual_evidence = evidence["visual_evidence"]
    report_evidence = visual_evidence["report"]

    report_path = ROOT / report_evidence["path"]
    assert report_path == VISUAL_REPORT
    assert report_path.is_file()
    assert re.fullmatch(r"[0-9a-f]{64}", report_evidence["sha256"])
    assert _sha256(report_path) == report_evidence["sha256"]
    assert report_evidence["timestamp"] == report["timestamp"]

    screenshots = visual_evidence["screenshots"]
    assert len(screenshots) == 5
    assert {item["viewport"] for item in screenshots} == CANONICAL_VIEWPORTS
    assert len({item["path"] for item in screenshots}) == 5
    assert {item["path"] for item in screenshots} == set(
        evidence["visual_post_deploy"]["screenshot_paths"]
    )
    for item in screenshots:
        screenshot_path = ROOT / item["path"]
        assert screenshot_path.is_file()
        assert re.fullmatch(r"[0-9a-f]{64}", item["sha256"])
        assert _sha256(screenshot_path) == item["sha256"]

    scenario_findings = {
        scenario["viewport"]: scenario["contrast_indeterminate_count"]
        for scenario in report["scenarios"]
    }
    reviews = evidence["manual_gradient_reviews"]
    assert len(reviews) == 5
    assert {review["viewport"] for review in reviews} == CANONICAL_VIEWPORTS
    assert len({review["viewport"] for review in reviews}) == 5
    assert sum(len(review["findings"]) for review in reviews) == report["total_contrast_indeterminate"] == 0
    review_timestamps = []
    for review in reviews:
        findings = review["findings"]
        assert len(findings) == scenario_findings[review["viewport"]] == 0
        if "reviewed_at" in review:
            reviewed_at = _timestamp(review["reviewed_at"])
            assert reviewed_at.tzinfo is not None
            review_timestamps.append(reviewed_at)
        for finding in findings:
            assert finding["reviewer_role"] == "ui_visual_tester"
            reviewed_at = _timestamp(finding["reviewed_at"])
            assert reviewed_at.tzinfo is not None
            review_timestamps.append(reviewed_at)
            assert finding["decision"] == "PASS"
            normalized_basis = finding["basis"].casefold()
            for phrase in (
                "readable over dark/amber disclaimer gradient",
                "no clipping, collision, or artefact",
                "zero layout defects",
            ):
                assert phrase in normalized_basis

    freshness = evidence["evidence_freshness"]
    report_timestamp = _timestamp(report["timestamp"])
    assert _timestamp(freshness["audit_completed_at"]) <= report_timestamp
    assert max(_timestamp(item["captured_at"]) for item in screenshots) <= report_timestamp
    assert len(set(review_timestamps)) == 1
    assert report_timestamp <= min(review_timestamps)
    assert _timestamp(freshness["audit_completed_at"]) <= _timestamp(
        freshness["manual_review_completed_at"]
    ) <= _timestamp(freshness["evidence_updated_at"])
    assert freshness["hf_revision"] == evidence["hf_revision"]
    assert freshness["source_version"] == evidence["source_version"]

    invalidation = " ".join(evidence["invalidation_condition"]).casefold()
    for condition in (
        "report or any reviewed screenshot is regenerated",
        "sha256 does not match",
        "newer production deploy or hugging face revision",
        "css or design-token changes",
        "rerun is not green",
    ):
        assert condition in invalidation
