"""Sequence-2 black-box contract for repository-backed atomic TDD admission.

The suite deliberately builds disposable Git histories.  It does not trust
caller-supplied gate booleans and it does not mutate the checkout under test.
"""

from __future__ import annotations

import hashlib
import json
import os
import py_compile
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
CORE_HOOK = ROOT / ".agents/hooks/atomic_tdd_guard.py"
CLAUDE_HOOK = ROOT / ".claude/hooks/atomic_tdd_guard.py"
AGY_HOOK = ROOT / ".agy/hooks/atomic-tdd-guard.sh"
V2_MANIFEST = ROOT / "plans/test_provenance/ticket-tdd-gov-qa-017-baseline.json"
V1_BASELINE = "b38d5077057c3852a7e2e21af37376567231f810"
V1_TEST_SHA256 = "ce7b2c1c5e0428188dc456438bfa3df6e4bb237df92c94c3e5648947f1c86642"
REQUIREMENT_PARENT = "aa279de6f801375f3b893407653f2b8a62bf41ea"

FUTURE_PATH_ALLOWLIST = [
    ".agents/config/atomic_tdd_lifecycle_v1.json",
    ".agents/schemas/atomic-tdd-lifecycle-v1.schema.json",
    ".agents/rules/21-agile-governance.md",
    ".claude/rules/agile-governance.md",
    ".agy/rules/agile-governance.md",
    ".agents/hooks/atomic_tdd_guard.py",
    ".claude/hooks/atomic_tdd_guard.py",
    ".agy/hooks/atomic-tdd-guard.sh",
    ".agents/hooks/full_capacity_guard.py",
    ".agents/hooks.json",
    ".claude/settings.json",
    ".agy/hooks.json",
    ".codex/hooks.json",
    ".agents/skills/agile-governance/SKILL.md",
    ".agents/skills/orchestrator-delegation/SKILL.md",
    ".agents/skills/bsa-doc-skill-management/SKILL.md",
    ".agents/skills/sdlc-aisdlc-workflow/SKILL.md",
    ".antigravity/skills/agile-governance/SKILL.md",
    ".antigravity/skills/orchestrator-delegation/SKILL.md",
    ".antigravity/skills/bsa-doc-skill-management/SKILL.md",
    ".antigravity/skills/sdlc-aisdlc-workflow/SKILL.md",
    "scripts/sync_ai_agent_ecosystem.py",
    "scripts/sync_claude_agy_parity.py",
    "scripts/sync_sdlc_agents.py",
    "scripts/test_provenance_guard.py",
    "atomic_tasks.md",
    "plans/plan.md",
    "plans/evidence/tdd-governance/tdd-gov-review-018.json",
    "plans/evidence/tdd-governance/tdd-gov-qa-030.json",
    "plans/evidence/tdd-governance/tdd-gov-review-040.json",
]


def _run(
    argv: list[str],
    *,
    cwd: Path,
    stdin: dict[str, Any] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd,
        input=json.dumps(stdin) if stdin is not None else None,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def _git(repo: Path, *args: str) -> str:
    result = _run(["git", *args], cwd=repo)
    assert result.returncode == 0, result.stderr or result.stdout
    return result.stdout.strip()


def _write(repo: Path, relative: str, content: str | bytes) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _commit(repo: Path, subject: str, *, baseline: str | None = None) -> str:
    _git(repo, "add", "-A")
    message = subject if baseline is None else f"{subject}\n\nTest-Baseline: {baseline}"
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _manifest(
    *,
    ticket: str,
    parent: str,
    test_path: str,
    test_hash: str,
    allowed: list[str],
    sequence: int,
    supersedes: str | None,
    correction_reason: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": "test-provenance-v1",
        "ticket_id": ticket,
        "sequence": sequence,
        "provenance_status": "VERIFIED",
        "baseline_parent": parent,
        "test_files": [{"path": test_path, "sha256": test_hash}],
        "red_tests": [
            {
                "command": ["python3", "-m", "pytest", "-q", test_path],
                "expected_exit": 1,
                "failure_fingerprint": "DYNAMIC_CONTRACT_RED",
            }
        ],
        "allowed_source_paths": allowed,
        "test_owner_role": "qa_tester",
        "reviewer_role": "code_reviewer",
        "supersedes": supersedes,
        "correction_reason": correction_reason,
        "rationale": "Disposable black-box provenance fixture.",
    }


def _board(ticket: str, state: str, history: list[str], baseline_manifest: str, receipt: str) -> str:
    record = {
        "schema_version": "atomic-task-records-v1",
        "tickets": [
            {
                "ticket_id": ticket,
                "owner_role": "developer",
                "state": state,
                "lifecycle_history": history,
                "dependencies": [
                    {"ticket_id": "TICKET-ORBIT-QA-017", "required_state": "TEST_BASELINE_VERIFIED"},
                    {"ticket_id": "TICKET-ORBIT-REVIEW-018", "required_state": "PASS", "receipt": receipt},
                ],
                "writable_paths": ["src/widget.py"],
                "baseline_manifest": baseline_manifest,
                "review_receipt": receipt,
            }
        ],
    }
    return "# Atomic tasks\n\n<!-- atomic-task-records-v1:start -->\n" + json.dumps(record, sort_keys=True) + "\n<!-- atomic-task-records-v1:end -->\n"


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True)
    _git(path, "init", "-q")
    _git(path, "config", "user.name", "QA Fixture")
    _git(path, "config", "user.email", "qa-fixture@example.invalid")
    _write(path, "src/widget.py", "VALUE = 1\n")
    _write(path, "atomic_tasks.md", "# Atomic tasks\n")
    _commit(path, "chore: initialize disposable repository")


def _add_baseline(
    repo: Path,
    *,
    ticket: str,
    sequence: int,
    supersedes: str | None = None,
    correction_reason: str | None = None,
    mixed_source: bool = False,
) -> tuple[str, str]:
    parent = _git(repo, "rev-parse", "HEAD")
    suffix = str(sequence)
    test_path = f"tests/test_contract_{suffix}.py"
    manifest_path = f"plans/test_provenance/{ticket.lower()}-baseline.json"
    _write(repo, test_path, f"def test_contract_{suffix}():\n    assert True\n")
    if mixed_source:
        _write(repo, "src/widget.py", "VALUE = 'mixed-with-baseline'\n")
    manifest = _manifest(
        ticket=ticket,
        parent=parent,
        test_path=test_path,
        test_hash=_sha256(repo / test_path),
        allowed=["src/widget.py", "atomic_tasks.md", "plans/evidence/atomic-tdd/"],
        sequence=sequence,
        supersedes=supersedes,
        correction_reason=correction_reason,
    )
    _write(repo, manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    baseline = _commit(repo, f"test: freeze disposable sequence {sequence}")
    return baseline, manifest_path


def _history(
    tmp_path: Path,
    *,
    state: str = "DOING",
    lifecycle: list[str] | None = None,
    owner_approved: bool = True,
    reviewed: bool = True,
    mixed_source: bool = False,
    tamper_test: bool = False,
    trailer: str = "correct",
    source_before_baseline: bool = False,
) -> tuple[Path, str, str]:
    repo = tmp_path / "repo"
    _init_repo(repo)
    old_baseline, _ = _add_baseline(repo, ticket="TICKET-ORBIT-QA-010", sequence=1)

    requirement = {
        "schema_version": "atomic-tdd-requirement-change-v1",
        "ticket_id": "TICKET-ORBIT-BSA-016",
        "approved_by": "owner",
        "approved_at": "2026-09-03",
        "approved": owner_approved,
        "superseded_baseline": old_baseline,
        "review_failure": "TICKET-ORBIT-REVIEW-015",
    }
    _write(repo, "plans/requirements/ticket-orbit-bsa-016.json", json.dumps(requirement, sort_keys=True) + "\n")
    requirement_commit = _commit(repo, "docs: record owner requirement decision")
    if source_before_baseline:
        _write(repo, "src/widget.py", "VALUE = 'source-before-baseline'\n")
        _commit(repo, "feat: premature source mutation")

    baseline, manifest_path = _add_baseline(
        repo,
        ticket="TICKET-ORBIT-QA-017",
        sequence=2,
        supersedes=old_baseline,
        correction_reason="Owner approval 2026-09-03 corrects REVIEW-015 gaps.",
        mixed_source=mixed_source,
    )
    if tamper_test:
        _write(repo, "tests/test_contract_2.py", "def test_contract_2():\n    assert False\n")
        _commit(repo, "test: tamper frozen contract", baseline=baseline)

    receipt_path = "plans/evidence/atomic-tdd/ticket-orbit-review-018.json"
    if reviewed:
        manifest_hash = _sha256(repo / manifest_path)
        receipt = {
            "schema_version": "atomic-tdd-review-v1",
            "source_ticket_id": "TICKET-ORBIT-DEV-020",
            "baseline_ticket_id": "TICKET-ORBIT-QA-017",
            "baseline_commit": baseline,
            "manifest_path": manifest_path,
            "manifest_sha256": manifest_hash,
            "supersedes": old_baseline,
            "requirement_change_commit": requirement_commit,
            "verdict": "PASS",
            "reviewer_role": "code_reviewer",
        }
        _write(repo, receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        _commit(repo, "review: approve disposable baseline", baseline=baseline)

    board = _board(
        "TICKET-ORBIT-DEV-020",
        state,
        lifecycle or ["TODO", "READY", "DOING"],
        manifest_path,
        receipt_path,
    )
    _write(repo, "atomic_tasks.md", board)
    _commit(repo, "docs: admit disposable source ticket", baseline=baseline)

    _write(repo, "src/widget.py", "VALUE = 2\n")
    if trailer == "correct":
        source_commit = _commit(repo, "feat: implement disposable widget", baseline=baseline)
    elif trailer == "mismatch":
        source_commit = _commit(repo, "feat: implement disposable widget", baseline="0" * 40)
    elif trailer == "missing":
        source_commit = _commit(repo, "feat: implement disposable widget")
    else:
        raise AssertionError(f"unsupported trailer fixture: {trailer}")
    return repo, baseline, source_commit


def _core_event(repo: Path, *, path: str = "src/widget.py") -> dict[str, Any]:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": path},
        "ticket_id": "TICKET-ORBIT-DEV-020",
        "baseline_verified": True,
        "review_pass": True,
        "qa_pass": True,
        "repo": str(repo),
    }


def _invoke_core(repo: Path, *, path: str = "src/widget.py") -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    assert CORE_HOOK.is_file(), "ATOMIC_TDD_IMPLEMENTATION_MISSING:.agents/hooks/atomic_tdd_guard.py"
    result = _run([sys.executable, str(CORE_HOOK), "--repo", str(repo), "--adapter", "core"], cwd=ROOT, stdin=_core_event(repo, path=path))
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"ATOMIC_TDD_CORE_PROTOCOL_INVALID:{result.stdout!r}:{result.stderr!r}") from exc
    assert isinstance(payload, dict)
    assert payload.get("decision") in {"allow", "deny"}
    assert isinstance(payload.get("reason_code"), str) and payload["reason_code"]
    return result, payload


def _assert_denied(repo: Path, reason_code: str, *, path: str = "src/widget.py") -> None:
    result, payload = _invoke_core(repo, path=path)
    assert result.returncode != 0
    assert payload == {"decision": "deny", "reason_code": reason_code}


def test_sequence_1_artifacts_are_still_byte_identical() -> None:
    test_bytes = _run(["git", "show", f"{V1_BASELINE}:tests/test_atomic_tdd_lifecycle_governance.py"], cwd=ROOT).stdout.encode()
    current_test = (ROOT / "tests/test_atomic_tdd_lifecycle_governance.py").read_bytes()
    assert hashlib.sha256(test_bytes).hexdigest() == V1_TEST_SHA256
    assert current_test == test_bytes
    old_manifest = _run(["git", "show", f"{V1_BASELINE}:plans/test_provenance/ticket-tdd-gov-qa-010-baseline.json"], cwd=ROOT).stdout.encode()
    assert (ROOT / "plans/test_provenance/ticket-tdd-gov-qa-010-baseline.json").read_bytes() == old_manifest


def test_v2_manifest_is_closed_and_uses_exact_authorized_allowlist() -> None:
    manifest = json.loads(V2_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "test-provenance-v1"
    assert manifest["sequence"] == 2
    assert manifest["baseline_parent"] == REQUIREMENT_PARENT
    assert manifest["supersedes"] == V1_BASELINE
    assert "2026-09-03" in manifest["correction_reason"]
    assert "REVIEW-015" in manifest["correction_reason"]
    assert manifest["test_owner_role"] == "qa_tester"
    assert manifest["reviewer_role"] == "code_reviewer"
    assert manifest["allowed_source_paths"] == FUTURE_PATH_ALLOWLIST


def test_generic_reviewed_repository_history_allows_owned_source(tmp_path: Path) -> None:
    repo, _, _ = _history(tmp_path)
    relative_result, relative = _invoke_core(repo)
    absolute_result, absolute = _invoke_core(repo, path=str(repo / "src/widget.py"))
    assert relative_result.returncode == absolute_result.returncode == 0
    assert relative == absolute == {"decision": "allow", "reason_code": "ATOMIC_TDD_ADMITTED"}


@pytest.mark.parametrize("state", ["TODO", "READY", "BLOCKED", "NEEDS_HITL", "DONE"])
def test_non_doing_lifecycle_states_deny_source(tmp_path: Path, state: str) -> None:
    repo, _, _ = _history(tmp_path, state=state, lifecycle=["TODO", state] if state != "TODO" else ["TODO"])
    _assert_denied(repo, "TICKET_STATE_NOT_DOING")


def test_direct_lifecycle_skip_is_rejected(tmp_path: Path) -> None:
    repo, _, _ = _history(tmp_path, lifecycle=["TODO", "DOING"])
    _assert_denied(repo, "INVALID_LIFECYCLE_TRANSITION")


@pytest.mark.parametrize(
    ("variant", "reason"),
    [
        ({"mixed_source": True}, "BASELINE_MIXES_SOURCE_AND_TEST"),
        ({"tamper_test": True}, "FROZEN_TEST_CHANGED"),
        ({"trailer": "missing"}, "SOURCE_COMMIT_MISSING_BASELINE_TRAILER"),
        ({"trailer": "mismatch"}, "SOURCE_COMMIT_BASELINE_TRAILER_MISMATCH"),
        ({"source_before_baseline": True}, "SOURCE_PRECEDES_BASELINE"),
    ],
)
def test_dynamic_git_provenance_failures_are_distinct(tmp_path: Path, variant: dict[str, Any], reason: str) -> None:
    repo, _, _ = _history(tmp_path, **variant)
    _assert_denied(repo, reason)


def test_unapproved_and_unreviewed_supersessions_fail_closed(tmp_path: Path) -> None:
    unapproved, _, _ = _history(tmp_path / "unapproved", owner_approved=False)
    unreviewed, _, _ = _history(tmp_path / "unreviewed", reviewed=False)
    _assert_denied(unapproved, "REQUIREMENT_CHANGE_NOT_APPROVED")
    _assert_denied(unreviewed, "INDEPENDENT_REVIEW_REQUIRED")


def test_hostile_caller_claims_cannot_replace_repository_evidence(tmp_path: Path) -> None:
    repo, _, _ = _history(tmp_path)
    (repo / "plans/evidence/atomic-tdd/ticket-orbit-review-018.json").unlink()
    result, payload = _invoke_core(repo)
    assert result.returncode != 0
    assert payload == {"decision": "deny", "reason_code": "REPOSITORY_EVIDENCE_DIRTY"}


def test_path_ownership_is_contained_and_symlinks_fail_closed(tmp_path: Path) -> None:
    repo, _, _ = _history(tmp_path)
    outside = tmp_path / "outside.py"
    outside.write_text("SECRET = False\n", encoding="utf-8")
    (repo / "src/link.py").symlink_to(outside)
    for target in ("src/widget.py.bak", "../outside.py", str(repo / "src/link.py")):
        _assert_denied(repo, "PATH_OUTSIDE_OWNERSHIP", path=target)


def _commands_from_registry(path: Path, platform: str) -> list[tuple[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    hooks = data["hooks"]
    entries = hooks.get("PreToolUse", []) if platform != "codex" else hooks.get("project", {}).get("PreToolUse", [])
    commands: list[tuple[str, str]] = []
    for entry in entries:
        matcher = entry.get("matcher", "")
        handlers = entry.get("hooks") or ([entry["handler"]] if "handler" in entry else [])
        for handler in handlers:
            if isinstance(handler, dict) and isinstance(handler.get("command"), str):
                commands.append((matcher, handler["command"]))
    return commands


def test_real_registries_have_one_functional_guard_and_codex_claims_no_native_pretooluse() -> None:
    expected = {
        "agents": (ROOT / ".agents/hooks.json", ".agents/hooks/atomic_tdd_guard.py"),
        "claude": (ROOT / ".claude/settings.json", ".claude/hooks/atomic_tdd_guard.py"),
        "agy": (ROOT / ".agy/hooks.json", ".agy/hooks/atomic-tdd-guard.sh"),
    }
    for platform, (registry, executable) in expected.items():
        matches = [(matcher, command) for matcher, command in _commands_from_registry(registry, platform) if executable in command]
        assert len(matches) == 1, f"{platform} requires exactly one functional PreToolUse atomic TDD guard: {matches}"
        matcher, command = matches[0]
        assert matcher in {".*", "Edit|Write|MultiEdit|Bash", "run_command|write_to_file|replace_file_content"}
        assert (ROOT / executable).is_file()
        assert command.split()[0] in {"python3", "bash", executable}

    codex = json.loads((ROOT / ".codex/hooks.json").read_text(encoding="utf-8"))
    assert "PreToolUse" not in codex.get("hooks", {}).get("project", {})
    assert "atomic_tdd_guard" not in json.dumps(codex)
    assert "no native pretooluse" in codex["description"].lower()


def test_claude_and_agy_adapters_emit_native_deny_protocols(tmp_path: Path) -> None:
    repo, _, _ = _history(tmp_path, state="BLOCKED", lifecycle=["TODO", "READY", "BLOCKED"])
    event = _core_event(repo)
    assert CLAUDE_HOOK.is_file(), "ATOMIC_TDD_IMPLEMENTATION_MISSING:.claude/hooks/atomic_tdd_guard.py"
    claude = _run([sys.executable, str(CLAUDE_HOOK), "--repo", str(repo)], cwd=ROOT, stdin=event)
    claude_payload = json.loads(claude.stdout)
    assert claude.returncode == 0
    assert claude_payload == {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "TICKET_STATE_NOT_DOING",
        }
    }

    agy_event = {
        "toolCall": {
            "name": "write_to_file",
            "args": {
                "file_path": "src/widget.py",
                "ticket_id": "TICKET-ORBIT-DEV-020",
                "baseline_verified": True,
                "review_pass": True,
            },
        },
        "repo": str(repo),
    }
    assert AGY_HOOK.is_file(), "ATOMIC_TDD_IMPLEMENTATION_MISSING:.agy/hooks/atomic-tdd-guard.sh"
    agy = _run(["bash", str(AGY_HOOK), "--repo", str(repo)], cwd=ROOT, stdin=agy_event)
    assert agy.returncode == 2
    assert json.loads(agy.stdout) == {"decision": "deny", "reason": "TICKET_STATE_NOT_DOING"}


def test_canonical_mirrors_syntax_and_read_only_sync_checks() -> None:
    rule = (ROOT / ".agents/rules/21-agile-governance.md").read_bytes()
    assert (ROOT / ".claude/rules/agile-governance.md").read_bytes() == rule
    assert (ROOT / ".agy/rules/agile-governance.md").read_bytes() == rule
    for skill in ("agile-governance", "orchestrator-delegation", "bsa-doc-skill-management", "sdlc-aisdlc-workflow"):
        canonical = (ROOT / f".agents/skills/{skill}/SKILL.md").read_bytes()
        assert (ROOT / f".antigravity/skills/{skill}/SKILL.md").read_bytes() == canonical
    assert CORE_HOOK.read_bytes() == CLAUDE_HOOK.read_bytes()

    for path in (CORE_HOOK, CLAUDE_HOOK, ROOT / ".agents/hooks/full_capacity_guard.py"):
        py_compile.compile(str(path), doraise=True)
    shell_syntax = _run(["bash", "-n", str(AGY_HOOK)], cwd=ROOT)
    assert shell_syntax.returncode == 0, shell_syntax.stderr

    for command in (
        [sys.executable, "scripts/sync_ai_agent_ecosystem.py", "--check"],
        [sys.executable, "scripts/sync_claude_agy_parity.py", "--check"],
        [sys.executable, "scripts/sync_sdlc_agents.py", "--check"],
    ):
        result = _run(command, cwd=ROOT)
        assert result.returncode == 0, result.stdout + result.stderr
