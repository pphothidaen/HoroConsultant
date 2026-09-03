"""Frozen black-box contract for mandatory atomic TDD lifecycle enforcement.

The later implementation must provide a read-only repository-evidence hook;
this baseline deliberately does not implement that hook or alter its policies.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = ".agents/hooks/atomic_tdd_guard.py"
RULE_PATH = ".agents/rules/21-agile-governance.md"
SKILL_PATHS = (
    ".agents/skills/agile-governance/SKILL.md",
    ".agents/skills/orchestrator-delegation/SKILL.md",
    ".agents/skills/bsa-doc-skill-management/SKILL.md",
    ".agents/skills/sdlc-aisdlc-workflow/SKILL.md",
)
REGISTRY_PATHS = (
    ".agents/hooks.json",
    ".claude/settings.json",
    ".agy/hooks.json",
    ".codex/hooks.json",
)
SOURCE_TICKET = "TDD-GOV-DEV-020"


def _require_hook() -> Path:
    hook = ROOT / HOOK_PATH
    assert hook.is_file(), f"ATOMIC_TDD_HOOK missing: {HOOK_PATH}"
    return hook


def _invoke(event: dict[str, object]) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    result = subprocess.run(
        [sys.executable, str(_require_hook()), "--repo", str(ROOT)],
        cwd=ROOT,
        input=json.dumps(event),
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise AssertionError(f"ATOMIC_TDD_HOOK must emit one JSON decision: {result.stdout!r}") from error
    assert isinstance(payload, dict), "ATOMIC_TDD_HOOK decision must be an object"
    return result, payload


def _source_event(tool_name: str, tool_input: dict[str, str]) -> dict[str, object]:
    # These booleans are deliberately hostile caller claims.  The hook must
    # bind its decision to repository ticket/manifest/history evidence instead.
    return {
        "tool_name": tool_name,
        "tool_input": tool_input,
        "ticket_id": SOURCE_TICKET,
        "baseline_verified": True,
        "review_pass": True,
        "qa_pass": True,
    }


def _decision(payload: dict[str, object]) -> tuple[str, str]:
    decision = payload.get("decision")
    reason = payload.get("reason")
    assert decision in {"allow", "deny"}, f"invalid hook decision: {payload}"
    assert isinstance(reason, str) and reason, f"missing hook reason: {payload}"
    return str(decision), reason


def test_future_governance_surface_exists_and_is_explicit() -> None:
    _require_hook()
    policy_paths = (RULE_PATH, *SKILL_PATHS)
    missing = [path for path in policy_paths if not (ROOT / path).is_file()]
    assert not missing, f"ATOMIC_TDD_POLICY missing: {missing}"
    policy = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in policy_paths).lower()
    for term in (
        "test_baseline_verified",
        "ready",
        "doing",
        "independent review",
        "independent qa",
        "source",
        "frozen",
        "superseding baseline",
        "requirement change",
    ):
        assert term in policy, f"ATOMIC_TDD_POLICY missing required term: {term}"


def test_source_mutations_fail_closed_despite_untrusted_caller_claims() -> None:
    attempts = (
        _source_event("Edit", {"file_path": ".agents/rules/21-agile-governance.md"}),
        _source_event("Write", {"file_path": ".agents/hooks/atomic_tdd_guard.py"}),
        _source_event("MultiEdit", {"file_path": ".agents/skills/agile-governance/SKILL.md"}),
        _source_event("Bash", {"command": "git commit -m 'feat: bypass baseline'"}),
        _source_event("Bash", {"command": "python3 scripts/sync_ai_agent_ecosystem.py --sync"}),
    )
    for event in attempts:
        result, payload = _invoke(event)
        decision, reason = _decision(payload)
        assert result.returncode == 0, result.stderr
        assert decision == "deny", f"ATOMIC_TDD_SOURCE_BYPASS: {event} -> {payload}"
        assert "TDD" in reason.upper() or "BASELINE" in reason.upper(), payload


def test_baseline_test_work_and_harmless_reads_are_allowed_without_source_admission() -> None:
    events = (
        _source_event("Write", {"file_path": "tests/test_future_atomic_tdd_contract.py"}),
        _source_event("Read", {"file_path": "atomic_tasks.md"}),
        _source_event("Grep", {"pattern": "TDD-GOV-DEV-020", "path": "atomic_tasks.md"}),
        _source_event("Bash", {"command": "git status --short"}),
    )
    for event in events:
        result, payload = _invoke(event)
        decision, _reason = _decision(payload)
        assert result.returncode == 0, result.stderr
        assert decision == "allow", f"ATOMIC_TDD_SAFE_OPERATION_BLOCKED: {event} -> {payload}"


def test_hook_is_read_only_and_registers_across_supported_local_ecosystems() -> None:
    hook = _require_hook()
    before = subprocess.run(
        ["git", "status", "--porcelain=v1"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    result, payload = _invoke(_source_event("Read", {"file_path": "atomic_tasks.md"}))
    decision, _reason = _decision(payload)
    after = subprocess.run(
        ["git", "status", "--porcelain=v1"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    assert result.returncode == 0 and decision == "allow"
    assert after == before, "ATOMIC_TDD_HOOK_MUTATED_REPOSITORY"
    assert "subprocess" in hook.read_text(encoding="utf-8"), "ATOMIC_TDD_HOOK must inspect Git evidence"

    missing = [path for path in REGISTRY_PATHS if HOOK_PATH not in (ROOT / path).read_text(encoding="utf-8")]
    assert not missing, f"ATOMIC_TDD_HOOK_REGISTRATION missing: {missing}"


def test_provenance_guard_and_policy_reject_baseline_integrity_bypasses() -> None:
    guard = (ROOT / "scripts/test_provenance_guard.py").read_text(encoding="utf-8")
    for code in (
        "BASELINE_MIXES_SOURCE_AND_TEST",
        "SOURCE_COMMIT_MISSING_BASELINE_TRAILER",
        "SOURCE_COMMIT_BASELINE_TRAILER_MISMATCH",
        "FROZEN_TEST_CHANGED",
        "TEST_HASH_MISMATCH",
    ):
        assert code in guard, f"ATOMIC_TDD_PROVENANCE_GAP missing: {code}"

    policy = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in (RULE_PATH, *SKILL_PATHS)).lower()
    for term in ("unreviewed", "superseding", "preserve", "independent review", "qa"):
        assert term in policy, f"ATOMIC_TDD_SUPERSESSION_GAP missing: {term}"
