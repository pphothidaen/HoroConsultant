"""Unit tests for scripts/governance_sync.py (KAN-97 governance-as-code).

Covers the offline core of the governance sync tool: volatile-key stripping,
recursive drift comparison, apply payload construction, declaration loading,
step-summary rendering, and structural invariants of governance/*.json.
No network access is required.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import governance_sync as gs


REPO_ROOT = Path(__file__).resolve().parents[1]


# --- volatile-key stripping -------------------------------------------------


def test_strip_volatile_removes_keys_recursively() -> None:
    payload = {
        "url": "https://api.github.com/x",
        "enabled": True,
        "nested": {"id": 1, "node_id": "ABC", "keep": "yes"},
        "items": [{"id": 2, "value": "a"}, {"id": 3, "value": "b"}],
    }
    stripped = gs._strip_volatile(payload, ("url", "id", "node_id"))
    assert stripped == {
        "enabled": True,
        "nested": {"keep": "yes"},
        "items": [{"value": "a"}, {"value": "b"}],
    }


def test_strip_volatile_keeps_payload_without_volatile_keys() -> None:
    payload = {"required_approving_review_count": 1, "dismiss_stale_reviews": False}
    assert gs._strip_volatile(payload, gs.BRANCH_PROTECTION_VOLATILE_KEYS) == payload


# --- recursive drift comparison ---------------------------------------------


def test_compare_clean_when_declared_matches_live() -> None:
    drifts: list[tuple[str, str]] = []
    gs._compare("bp", {"a": 1, "b": {"c": [1, 2]}}, {"a": 1, "b": {"c": [1, 2]}}, drifts)
    assert drifts == []


def test_compare_reports_drift_on_value_mismatch() -> None:
    drifts: list[tuple[str, str]] = []
    declared = {"required_pull_request_reviews": {"required_approving_review_count": 2}}
    live = {"required_pull_request_reviews": {"required_approving_review_count": 1}}
    gs._compare("branch_protection", declared, live, drifts)
    assert len(drifts) == 1
    label, detail = drifts[0]
    assert label == "branch_protection.required_pull_request_reviews.required_approving_review_count"
    assert "declared=2" in detail and "live=1" in detail


def test_compare_reports_drift_on_missing_and_extra_keys() -> None:
    drifts: list[tuple[str, str]] = []
    gs._compare("root", {"kept": 1, "gone": 2}, {"kept": 1, "extra": 3}, drifts)
    labels = [label for label, _ in drifts]
    assert "root.gone" in labels  # declared-only
    assert "root.extra" in labels  # live-only


def test_compare_reports_drift_on_list_length() -> None:
    drifts: list[tuple[str, str]] = []
    gs._compare("rulesets", [{"name": "a"}], [], drifts)
    assert len(drifts) == 1
    assert "list length differs" in drifts[0][1]


def test_compare_reports_drift_inside_list_items() -> None:
    drifts: list[tuple[str, str]] = []
    gs._compare("rulesets", [{"enforcement": "active"}], [{"enforcement": "disabled"}], drifts)
    assert drifts[0][0] == "rulesets[0].enforcement"


# --- apply payload construction ---------------------------------------------


def test_bp_apply_payloads_field_sections_use_only_declared_settings() -> None:
    declared = {
        "required_pull_request_reviews": {
            "required_approving_review_count": 1,
            "dismiss_stale_reviews": False,
            "require_code_owner_reviews": False,
            "require_last_push_approval": False,
            "url": "https://api.github.com/ignored",
        },
        "required_status_checks": {"strict": True, "contexts": ["Test Provenance"]},
    }
    payloads = dict(gs._bp_apply_payloads(declared, "owner/repo", "main"))
    reviews_endpoint = "/repos/owner/repo/branches/main/protection/required_pull_request_reviews"
    assert payloads[reviews_endpoint] == {
        "dismiss_stale_reviews": False,
        "require_code_owner_reviews": False,
        "require_last_push_approval": False,
        "required_approving_review_count": 1,
    }
    checks_endpoint = "/repos/owner/repo/branches/main/protection/required_status_checks"
    assert payloads[checks_endpoint] == {"strict": True, "contexts": ["Test Provenance"]}
    assert all("url" not in payload for payload in payloads.values())


def test_bp_apply_payloads_boolean_sections() -> None:
    declared = {
        "enforce_admins": {"enabled": True, "url": "ignored"},
        "allow_force_pushes": {"enabled": False},
    }
    payloads = dict(gs._bp_apply_payloads(declared, "o/r", "main"))
    assert payloads["/repos/o/r/branches/main/protection/enforce_admins"] == {"enabled": True}
    assert payloads["/repos/o/r/branches/main/protection/allow_force_pushes"] == {"enabled": False}


def test_bp_apply_payloads_rejects_malformed_boolean_section() -> None:
    with pytest.raises(gs.GovernanceError):
        gs._bp_apply_payloads({"lock_branch": {"enabled": "yes-please"}}, "o/r", "main")


def test_ruleset_apply_payload_keeps_only_writable_keys() -> None:
    declared = {
        "id": 21626253,
        "name": "Require Test Provenance",
        "target": "branch",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": ["refs/heads/main"], "exclude": []}},
        "rules": [{"type": "required_status_checks"}],
        "created_at": "2026-08-27T12:30:47.958+07:00",
        "_links": {"self": {"href": "ignored"}},
    }
    payload = gs._ruleset_apply_payload(declared)
    assert payload == {
        "name": "Require Test Provenance",
        "target": "branch",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": ["refs/heads/main"], "exclude": []}},
        "rules": [{"type": "required_status_checks"}],
    }


# --- declaration loading ------------------------------------------------------


def test_load_declared_rejects_non_object(tmp_path: Path) -> None:
    target = tmp_path / "not-an-object.json"
    target.write_text(json.dumps([1, 2]), encoding="utf-8")
    with pytest.raises(gs.GovernanceError):
        gs._load_declared(target)


def test_load_declared_rejects_invalid_json(tmp_path: Path) -> None:
    target = tmp_path / "broken.json"
    target.write_text("{not json", encoding="utf-8")
    with pytest.raises(gs.GovernanceError):
        gs._load_declared(target)


def test_load_declared_rulesets_requires_rulesets_array(tmp_path: Path) -> None:
    bad = tmp_path / "rulesets.json"
    bad.write_text(json.dumps({"rulesets": "nope"}), encoding="utf-8")
    with pytest.raises(gs.GovernanceError):
        gs._load_declared_rulesets(bad)


# --- slug validation ----------------------------------------------------------


def test_repo_slug_accepts_valid_and_rejects_garbage() -> None:
    assert gs._repo_slug("owner/repo") == "owner/repo"
    assert gs._repo_slug(None) == gs.DEFAULT_REPO
    with pytest.raises(gs.GovernanceError):
        gs._repo_slug("https://evil.example/owner/repo")


# --- exit codes ---------------------------------------------------------------


def test_exit_codes_are_distinct_and_fail_closed() -> None:
    assert gs.EXIT_OK == 0
    assert gs.EXIT_DRIFT == 1
    assert gs.EXIT_ERROR == 2
    assert len({gs.EXIT_OK, gs.EXIT_DRIFT, gs.EXIT_ERROR}) == 3


# --- step summary -------------------------------------------------------------


def test_write_step_summary_renders_drift_table(tmp_path: Path) -> None:
    summary = tmp_path / "summary.md"
    summary.write_text("", encoding="utf-8")
    monkeypatch_target = {"GITHUB_STEP_SUMMARY": str(summary)}
    import os

    old = os.environ.get("GITHUB_STEP_SUMMARY")
    os.environ["GITHUB_STEP_SUMMARY"] = monkeypatch_target["GITHUB_STEP_SUMMARY"]
    try:
        gs._write_step_summary([("bp.reviews.count", "declared=2 live=1")])
    finally:
        if old is None:
            os.environ.pop("GITHUB_STEP_SUMMARY", None)
        else:
            os.environ["GITHUB_STEP_SUMMARY"] = old
    content = summary.read_text(encoding="utf-8")
    assert "Governance Drift Detection" in content
    assert "DRIFT DETECTED" in content
    assert "`bp.reviews.count`" in content
    assert "declared=2 live=1" in content


def test_write_step_summary_renders_ok_when_no_drift(tmp_path: Path) -> None:
    summary = tmp_path / "summary.md"
    summary.write_text("", encoding="utf-8")
    import os

    old = os.environ.get("GITHUB_STEP_SUMMARY")
    os.environ["GITHUB_STEP_SUMMARY"] = str(summary)
    try:
        gs._write_step_summary([])
    finally:
        if old is None:
            os.environ.pop("GITHUB_STEP_SUMMARY", None)
        else:
            os.environ["GITHUB_STEP_SUMMARY"] = old
    content = summary.read_text(encoding="utf-8")
    assert "No drift" in content
    assert "DRIFT DETECTED" not in content


# --- structural invariants of the committed declaration ----------------------


def test_governance_branch_protection_file_is_structurally_valid() -> None:
    path = REPO_ROOT / "governance" / "branch-protection.main.json"
    assert path.is_file(), "governance/branch-protection.main.json must be committed"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "url" not in data, "volatile server metadata must not be committed"
    reviews = data.get("required_pull_request_reviews")
    assert isinstance(reviews, dict)
    assert isinstance(reviews.get("required_approving_review_count"), int)
    for section in ("enforce_admins", "allow_force_pushes", "allow_deletions"):
        assert isinstance(data.get(section), dict), f"missing section: {section}"
        assert isinstance(data[section].get("enabled"), bool)


def test_governance_rulesets_file_is_structurally_valid() -> None:
    path = REPO_ROOT / "governance" / "rulesets.json"
    assert path.is_file(), "governance/rulesets.json must be committed"
    data = json.loads(path.read_text(encoding="utf-8"))
    rulesets = data.get("rulesets")
    assert isinstance(rulesets, list) and rulesets, "rulesets array must be non-empty"
    for ruleset in rulesets:
        assert isinstance(ruleset, dict)
        assert isinstance(ruleset.get("name"), str) and ruleset["name"]
        assert isinstance(ruleset.get("rules"), list)
        assert isinstance(ruleset.get("conditions"), dict)
        assert "created_at" not in ruleset, "volatile server metadata must not be committed"
        assert "updated_at" not in ruleset, "volatile server metadata must not be committed"


def test_ruleset_volatile_keys_exclude_id_but_keep_it_exported() -> None:
    # "id" is server-assigned but must survive export so apply can target it.
    assert "id" in gs.RULESET_VOLATILE_KEYS
    assert "id" not in gs.RULESET_EXPORT_VOLATILE_KEYS
