"""Permanent R4 durable-dispatch regressions.

These tests deliberately construct ledger state through the public dispatcher
primitives; they do not borrow mutable helpers from the legacy test module.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.multiagent_prompt_command as command


def _policy() -> dict[str, object]:
    return command.load_model_policy(ROOT / ".agents/config/multiagent_model_policy.yaml")


def _route(tmp_path: Path) -> command.Route:
    config = {
        "runtime": {"approved_for_execution": True, "protocol_version": 2},
        "accounts": {"codex1": {"cli": "codex", "command": "codex"}},
        "roles": {"developer": {"alias": "codex1", "cli": "codex", "model": "gpt-5.6-luna", "effort": "medium", "sandbox": "read-only"}},
    }
    path = tmp_path / "routes.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return command.resolve_route(config, "developer")


def _snapshot(ticket: str, ownership: str) -> dict[str, object]:
    return {"schema_version": 1, "tickets": [{"ticket_id": ticket, "severity": "HIGH", "work_effort": "M", "status": "READY", "dependencies": [], "blockers": [], "owner": "developer", "ownership": [ownership], "quota_passed": True, "hitl_passed": True, "rule18_decision_valid": True}], "reservations": []}


def _invocation(tmp_path: Path, *, ticket: str = "TICKET-R4-A", ownership: str = "tests/r4/a.py", attempt: int = 1, objective: str = "R4 durable dispatch") -> command.Invocation:
    policy = _policy()
    decision = {"schema_version": 1, "ticket": ticket, "phase": "implementation", "scope_rank": 1, "complexity_rank": 1, "risk_rank": 1, "ambiguity_rank": 1, "evidence_burden_rank": 1, "quota_band": "healthy", "work_mode": "read_only", "selected_alias": "codex1", "selected_model": "gpt-5.6-luna", "selected_effort": "medium", "rationale": "r4 test", "policy_version": policy["policy_version"], "planning_to_medium_confirmed": True, "hitl_approved": False}
    config = tmp_path / "routes.yaml"
    if not config.exists():
        _route(tmp_path)
    return command.build_invocation(
        _route(tmp_path), command.render_prompt(objective=objective, ownership=ownership), tmp_path,
        decision=decision, model_policy=policy, attempt_id=attempt, objective=objective,
        ownership=ownership, runtime_config_path=config, runtime_config_approved=True,
        scheduling_snapshot=_snapshot(ticket, ownership), claim_store_override=str(tmp_path / "ledger"),
    )


def _release(claim: command.DispatchClaim) -> None:
    if not claim.closed:
        command._release_dispatch_claim(claim)


def _legacy_record(invocation: command.Invocation, state: str, *, key: str | None = None) -> dict[str, object]:
    """Minimal valid R3 ledger record used solely to test its R5 migration."""

    claim_key = key or command._dispatch_claim_key(invocation)
    terminal = state in {"completed", "rejected", "unknown"}
    return {
        "version": 1,
        "claim_key": claim_key,
        "decision_sha256": invocation.decision_digest,
        "scheduling_snapshot_sha256": invocation.scheduling_snapshot_digest,
        "dispatch_identity": command._claim_dispatch_identity(invocation),
        "ticket": invocation.decision["ticket"],
        "route_sha256": command._canonical_sha256({
            "role": invocation.route.role, "alias": invocation.route.alias,
            "provider": invocation.route.cli, "model": invocation.route.model,
            "effort": invocation.route.effort,
        }),
        "ownership_resources": [invocation.ownership],
        "state": state,
        "pid": os.getpid(),
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
        "started_at": "2025-01-01T00:00:00Z",
        "ended_at": "2025-01-01T00:00:01Z" if terminal else None,
        "transport_status": {
            "active": "starting", "completed": "completed",
            "rejected": "provider_result_rejected", "unknown": "transport_unknown",
        }[state],
        "exit_code": 0 if state in {"completed", "rejected"} else None,
        "output_bytes": 1 if state in {"completed", "rejected"} else None,
        "output_sha256": "a" * 64 if state in {"completed", "rejected"} else None,
        "work_result_sha256": "b" * 64 if state == "completed" else None,
    }


def _write_legacy(ledger: Path, record: dict[str, object]) -> Path:
    ledger.mkdir(mode=0o700, exist_ok=True)
    path = ledger / f"{record['claim_key']}.json"
    path.write_text(json.dumps(record, sort_keys=True), encoding="ascii")
    path.chmod(0o600)
    return path


def test_r4_live_overlap_exact_replay_and_unlocked_orphan_recovery(tmp_path):
    first = _invocation(tmp_path, ownership="tests/r4/owned.py")
    claim = command._acquire_dispatch_claim(first)
    try:
        with pytest.raises(command.SchedulingError) as overlap:
            command._acquire_dispatch_claim(_invocation(tmp_path, ticket="TICKET-R4-B", ownership="tests/r4"))
        assert overlap.value.code == "OWNERSHIP_CONFLICT"
        with pytest.raises(command.SchedulingError) as replay:
            command._acquire_dispatch_claim(first)
        assert replay.value.code == "CONCURRENT_DISPATCH_CLAIM"
    finally:
        _release(claim)

    fresh = _invocation(tmp_path, ticket="TICKET-R4-C", ownership="tests/r4")
    recovered = command._acquire_dispatch_claim(fresh)
    try:
        original = json.loads((tmp_path / "ledger" / f"{claim.key}.json").read_text(encoding="ascii"))
        assert original["state"] == "abandoned"
        assert original["abandon_reason"] in {"process_dead", "stale_unlocked"}
    finally:
        _release(recovered)


def test_r4_pid_reuse_abandons_unlocked_claim_but_live_lock_wins(tmp_path, monkeypatch):
    invocation = _invocation(tmp_path, ownership="tests/r4/reused.py")
    claim = command._acquire_dispatch_claim(invocation)
    _release(claim)
    record = json.loads(claim.path.read_text(encoding="ascii"))
    record["process_start_binding"] = "0" * 64
    claim.path.write_text(json.dumps(record, sort_keys=True), encoding="ascii")
    monkeypatch.setattr(command, "_pid_is_alive", lambda _pid: True)
    monkeypatch.setattr(command, "_process_start_binding", lambda _pid: "1" * 64)
    replacement = command._acquire_dispatch_claim(
        _invocation(tmp_path, ticket="TICKET-R4-PID", ownership="tests/r4")
    )
    try:
        persisted = json.loads(claim.path.read_text(encoding="ascii"))
        assert persisted["state"] == "abandoned"
        assert persisted["abandon_reason"] == "pid_reused"
    finally:
        _release(replacement)


def test_r4_hmac_ownership_tokens_conflict_on_ancestor_not_sibling_and_never_persist_paths(tmp_path):
    first = command._acquire_dispatch_claim(_invocation(tmp_path, ownership="tests/r4/parent/a.py"))
    try:
        assert all(len(token) == 64 for token in first.record["ownership_exact_tokens"])
        assert all(len(token) == 64 for token in first.record["ownership_ancestor_tokens"])
        rendered = first.path.read_text(encoding="ascii")
        assert "tests/r4/parent/a.py" not in rendered
        with pytest.raises(command.SchedulingError) as conflict:
            command._acquire_dispatch_claim(_invocation(tmp_path, ticket="TICKET-R4-PARENT", ownership="tests/r4/parent"))
        assert conflict.value.code == "OWNERSHIP_CONFLICT"
        sibling = command._acquire_dispatch_claim(_invocation(tmp_path, ticket="TICKET-R4-SIBLING", ownership="tests/r4/sibling/b.py"))
        _release(sibling)
    finally:
        _release(first)


def test_r4_legacy_or_mixed_raw_ledger_record_fails_closed(tmp_path):
    invocation = _invocation(tmp_path)
    ledger = tmp_path / "ledger"
    ledger.mkdir(mode=0o700)
    legacy = ledger / ("a" * 64 + ".json")
    legacy.write_text(json.dumps({"version": 1, "state": "active", "ownership_resources": ["tests/r4/a.py"]}), encoding="ascii")
    legacy.chmod(0o600)
    with pytest.raises(command.SchedulingError) as exc:
        command._acquire_dispatch_claim(invocation)
    assert exc.value.code == "INVALID_DISPATCH_CLAIM"


def test_r4_portable_claim_proof_validates_without_ledger_and_rejects_tamper_or_local_mismatch(tmp_path, monkeypatch):
    invocation = _invocation(tmp_path)
    monkeypatch.setattr(command, "validate_execution_preflight", lambda _invocation: None)
    output = "\n".join((json.dumps({"type": "thread.started", "thread_id": "r4"}), json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps({"status": "DONE", "scope_owned": ["tests/r4"], "evidence": {"commands": ["pytest"], "outcomes": ["ok"], "artifacts": []}, "findings": ["ok"], "changed_files": [], "residual_risk": "none", "recommended_next_action": "none"})}}), json.dumps({"type": "turn.completed"}))) + "\n"
    monkeypatch.setattr(command.subprocess, "run", lambda argv, **kwargs: subprocess.CompletedProcess(argv, 0, output, ""))
    outcome = command.execute_invocation(invocation)
    receipt = dict(outcome.completed["execution_receipt"])
    work_result = outcome.completed["work_result"]
    persisted_path = tmp_path / "ledger" / f"{receipt['dispatch_claim_key']}.json"
    persisted = json.loads(persisted_path.read_text(encoding="ascii"))
    persisted_path.unlink()
    portable = replace(invocation, claim_store_override=str(tmp_path / "portable-empty"))
    assert command.validate_execution_receipt(
        receipt, work_result, portable, output, portable=True
    )["dispatch_claim_key"] == receipt["dispatch_claim_key"]
    with pytest.raises(command.ConfigurationError, match="native receipt evidence"):
        command.validate_execution_receipt(
            receipt, work_result, portable, outcome.process.stdout, portable=True
        )
    tampered = dict(receipt)
    tampered_proof = dict(receipt["claim_proof"])
    tampered_proof["ticket_sha256"] = "0" * 64
    tampered["claim_proof"] = tampered_proof
    with pytest.raises(command.ConfigurationError):
        command.validate_execution_receipt(
            tampered, work_result, portable, output, portable=True
        )
    persisted["route_sha256"] = "0" * 64
    persisted_path.write_text(json.dumps(persisted, sort_keys=True), encoding="ascii")
    persisted_path.chmod(0o600)
    with pytest.raises(command.ConfigurationError, match="local dispatch proof mismatches"):
        command.validate_execution_receipt(receipt, work_result, invocation, output)


def test_r4_recursive_durable_pii_scan_contains_only_redacted_receipt_and_tokens(tmp_path, monkeypatch):
    pii = "email=person@example.com; user_id=123456; /Users/person/private; 192.0.2.42"
    invocation = _invocation(tmp_path, ownership="tests/r4/pii-safe.py", objective=pii)
    monkeypatch.setattr(command, "validate_execution_preflight", lambda _invocation: None)
    monkeypatch.setattr(command.subprocess, "run", lambda argv, **kwargs: subprocess.CompletedProcess(argv, 0, "", ""))
    claim = command._acquire_dispatch_claim(invocation)
    try:
        durable = "\n".join(path.read_text(encoding="ascii", errors="ignore") for path in (tmp_path / "ledger").rglob("*") if path.is_file())
        for forbidden in ("person@example.com", "123456", "/Users/person", "192.0.2.42", "tests/r4/pii-safe.py"):
            assert forbidden not in durable
    finally:
        _release(claim)


@pytest.mark.parametrize("state", ["active", "completed", "rejected", "unknown"])
def test_r5_migrates_each_supported_legacy_state_and_bootstraps_one_ownership_key(tmp_path, state):
    legacy_invocation = _invocation(tmp_path, ticket="TICKET-R5-LEGACY", ownership="tests/r5/legacy.py")
    original = _legacy_record(legacy_invocation, state)
    legacy_path = _write_legacy(tmp_path / "ledger", original)
    fresh = _invocation(tmp_path, ticket="TICKET-R5-FRESH", ownership="tests/r5/fresh.py")
    claim = command._acquire_dispatch_claim(fresh)
    try:
        migrated = json.loads(legacy_path.read_text(encoding="ascii"))
        assert migrated["version"] == command.DISPATCH_CLAIM_VERSION
        assert migrated["legacy_claim_sha256"] == command._canonical_sha256(original)
        assert migrated["ownership_key_id"] == hashlib.sha256(
            (tmp_path / "ledger" / ".ownership.key").read_bytes()
        ).hexdigest()
        assert "ownership_resources" not in migrated
        if state == "active":
            assert migrated["state"] == "abandoned"
            assert migrated["abandon_reason"] == "stale_unlocked"
        else:
            assert migrated["state"] == state
    finally:
        _release(claim)


def test_r5_migration_interruption_before_and_after_rename_recovers_without_partial_acceptance(tmp_path, monkeypatch):
    legacy_invocation = _invocation(tmp_path, ticket="TICKET-R5-INT", ownership="tests/r5/int.py")
    original = _legacy_record(legacy_invocation, "completed")
    legacy_path = _write_legacy(tmp_path / "ledger", original)
    fresh = _invocation(tmp_path, ticket="TICKET-R5-INT-FRESH", ownership="tests/r5/fresh.py")
    original_rename = command.os.rename
    monkeypatch.setattr(command.os, "rename", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("injected")))
    with pytest.raises(command.SchedulingError) as before:
        command._acquire_dispatch_claim(fresh)
    assert before.value.code == "INVALID_DISPATCH_CLAIM"
    assert json.loads(legacy_path.read_text(encoding="ascii")) == original
    assert (tmp_path / "ledger" / f".{original['claim_key']}.migration-v2.tmp").exists()
    monkeypatch.setattr(command.os, "rename", original_rename)
    recovered = command._acquire_dispatch_claim(fresh)
    try:
        migrated = json.loads(legacy_path.read_text(encoding="ascii"))
        assert migrated["version"] == command.DISPATCH_CLAIM_VERSION
        assert not (tmp_path / "ledger" / f".{original['claim_key']}.migration-v2.tmp").exists()
    finally:
        _release(recovered)

    second_original = _legacy_record(
        _invocation(tmp_path, ticket="TICKET-R5-AFTER", ownership="tests/r5/after.py"),
        "completed",
    )
    second_path = _write_legacy(tmp_path / "ledger", second_original)
    after = _invocation(tmp_path, ticket="TICKET-R5-AFTER-FRESH", ownership="tests/r5/after-fresh.py")

    def rename_then_interrupt(*args, **kwargs):
        original_rename(*args, **kwargs)
        raise OSError("after rename")

    monkeypatch.setattr(command.os, "rename", rename_then_interrupt)
    with pytest.raises(command.SchedulingError) as after_error:
        command._acquire_dispatch_claim(after)
    assert after_error.value.code == "INVALID_DISPATCH_CLAIM"
    monkeypatch.setattr(command.os, "rename", original_rename)
    committed = command._acquire_dispatch_claim(after)
    try:
        assert json.loads(second_path.read_text(encoding="ascii"))["version"] == command.DISPATCH_CLAIM_VERSION
        assert not (tmp_path / "ledger" / f".{second_original['claim_key']}.migration-v2.tmp").exists()
    finally:
        _release(committed)


@pytest.mark.parametrize("key_bytes", [b"", b"x" * 31, b"x" * 33])
def test_r5_ownership_key_failures_fail_closed(tmp_path, key_bytes):
    ledger = tmp_path / "ledger"
    ledger.mkdir(mode=0o700)
    key = ledger / ".ownership.key"
    key.write_bytes(key_bytes)
    key.chmod(0o600)
    with pytest.raises(command.SchedulingError) as exc:
        command._acquire_dispatch_claim(_invocation(tmp_path))
    assert exc.value.code == "INVALID_DISPATCH_CLAIM"


def test_r5_missing_ownership_key_in_a_v2_ledger_fails_closed(tmp_path):
    first = command._acquire_dispatch_claim(_invocation(tmp_path, ticket="TICKET-R5-V2", ownership="tests/r5/v2.py"))
    _release(first)
    (tmp_path / "ledger" / ".ownership.key").unlink()
    with pytest.raises(command.SchedulingError) as exc:
        command._acquire_dispatch_claim(
            _invocation(tmp_path, ticket="TICKET-R5-V2-NEXT", ownership="tests/r5/v2-next.py")
        )
    assert exc.value.code == "INVALID_DISPATCH_CLAIM"


def test_r5_safe_stale_migration_temp_recovers_but_symlink_temp_fails_closed(tmp_path):
    invocation = _invocation(tmp_path, ticket="TICKET-R5-TEMP", ownership="tests/r5/temp.py")
    original = _legacy_record(invocation, "completed")
    legacy_path = _write_legacy(tmp_path / "ledger", original)
    temporary = tmp_path / "ledger" / f".{original['claim_key']}.migration-v2.tmp"
    temporary.write_text("not-json", encoding="ascii")
    temporary.chmod(0o600)
    recovered = command._acquire_dispatch_claim(
        _invocation(tmp_path, ticket="TICKET-R5-TEMP-NEXT", ownership="tests/r5/temp-next.py")
    )
    try:
        assert not temporary.exists()
        assert json.loads(legacy_path.read_text(encoding="ascii"))["version"] == command.DISPATCH_CLAIM_VERSION
    finally:
        _release(recovered)

    second = _legacy_record(_invocation(tmp_path, ticket="TICKET-R5-SYMLINK", ownership="tests/r5/symlink.py"), "completed")
    _write_legacy(tmp_path / "ledger", second)
    unsafe = tmp_path / "ledger" / f".{second['claim_key']}.migration-v2.tmp"
    unsafe.symlink_to(legacy_path)
    with pytest.raises(command.SchedulingError) as exc:
        command._acquire_dispatch_claim(
            _invocation(tmp_path, ticket="TICKET-R5-SYMLINK-NEXT", ownership="tests/r5/symlink-next.py")
        )
    assert exc.value.code == "INVALID_DISPATCH_CLAIM"


def test_r5_mixed_and_all_v1_ledgers_migrate_under_one_ownership_key(tmp_path):
    first = _invocation(tmp_path, ticket="TICKET-R5-MIX-A", ownership="tests/r5/mix-a.py")
    second = _invocation(tmp_path, ticket="TICKET-R5-MIX-B", ownership="tests/r5/mix-b.py")
    first_record = _legacy_record(first, "completed", key="c" * 64)
    second_record = _legacy_record(second, "rejected", key="d" * 64)
    first_path = _write_legacy(tmp_path / "ledger", first_record)
    second_path = _write_legacy(tmp_path / "ledger", second_record)
    trigger = command._acquire_dispatch_claim(
        _invocation(tmp_path, ticket="TICKET-R5-MIX-TRIGGER", ownership="tests/r5/mix-trigger.py")
    )
    try:
        migrated = [json.loads(path.read_text(encoding="ascii")) for path in (first_path, second_path)]
        assert {record["state"] for record in migrated} == {"completed", "rejected"}
        assert len({record["ownership_key_id"] for record in migrated}) == 1
        assert all(record["legacy_claim_sha256"] for record in migrated)
    finally:
        _release(trigger)


def test_r5_migrated_v1_receipt_is_typed_before_generic_schema_rejection(tmp_path):
    invocation = _invocation(tmp_path, ticket="TICKET-R5-RECEIPT", ownership="tests/r5/receipt.py")
    original = _legacy_record(invocation, "completed")
    path = _write_legacy(tmp_path / "ledger", original)
    trigger = command._acquire_dispatch_claim(
        _invocation(tmp_path, ticket="TICKET-R5-TRIGGER", ownership="tests/r5/trigger.py")
    )
    _release(trigger)
    migrated = json.loads(path.read_text(encoding="ascii"))
    with pytest.raises(command.LegacyReceiptRevalidationUnsupported) as exc:
        command.validate_execution_receipt(
            {
                "dispatch_claim_key": original["claim_key"],
                "dispatch_claim_sha256": migrated["legacy_claim_sha256"],
            },
            _work_result_for_r5(), invocation, "{}",
        )
    assert exc.value.code == "LEGACY_RECEIPT_REVALIDATION_UNSUPPORTED"


def _work_result_for_r5() -> dict[str, object]:
    return {
        "status": "DONE", "scope_owned": ["tests/r5"],
        "evidence": {"commands": ["pytest"], "outcomes": ["ok"], "artifacts": []},
        "findings": ["ok"], "changed_files": [], "residual_risk": "none",
        "recommended_next_action": "none",
    }
