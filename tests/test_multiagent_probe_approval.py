"""Focused fail-closed ProbeClaim/ApprovalGrant/consume/receipt-v3 tests."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from itertools import product
import json
from pathlib import Path
import shutil
import subprocess
import sys

from jsonschema import Draft202012Validator, FormatChecker
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.multiagent_prompt_command as command


def _work_result() -> dict[str, object]:
    return {
        "status": "DONE", "scope_owned": ["tests/preauth"],
        "evidence": {"commands": ["pytest"], "outcomes": ["ok"], "artifacts": []},
        "findings": ["preauthorization contract"], "changed_files": [],
        "residual_risk": "local attestation is nonportable",
        "recommended_next_action": "retain content-free receipts",
    }


def _invocation(tmp_path: Path) -> command.Invocation:
    tmp_path.mkdir(mode=0o700, parents=True, exist_ok=True)
    home = tmp_path / "account-home"
    home.mkdir(mode=0o700)
    synthetic_codex = tmp_path / "codex"
    shutil.copy2(sys.executable, synthetic_codex)
    synthetic_codex.chmod(synthetic_codex.stat().st_mode | 0o100)
    runtime = tmp_path / "runtime.yaml"
    runtime.write_text("runtime:\n  approved_for_execution: true\n  protocol_version: 2\n", encoding="utf-8")
    work_schema = tmp_path / "work-result-v2.schema.json"
    work_schema.write_text(
        (ROOT / ".agents/schemas/multiagent-work-result-v2.schema.json").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )
    policy = command.load_model_policy(ROOT / ".agents/config/multiagent_model_policy.yaml")
    route = command.Route(
        role="developer", alias="codex1", cli="codex", command=str(synthetic_codex),
        home_env="CODEX_HOME", home_path=str(home), model="gpt-5.6-luna",
        effort="medium", mode=None, sandbox="workspace-write",
    )
    decision = {
        "schema_version": 1, "ticket": "TICKET-PREAUTH-TEST", "phase": "implementation",
        "scope_rank": 1, "complexity_rank": 1, "risk_rank": 1, "ambiguity_rank": 1,
        "evidence_burden_rank": 1, "quota_band": "healthy", "work_mode": "mutation",
        "selected_alias": "codex1", "selected_model": "gpt-5.6-luna",
        "selected_effort": "medium", "rationale": "focused preauthorization test",
        "policy_version": policy["policy_version"], "planning_to_medium_confirmed": True,
        "hitl_approved": False,
    }
    ownership = "tests/preauth/owned.py"
    snapshot = {
        "schema_version": 1,
        "tickets": [{
            "ticket_id": decision["ticket"], "severity": "HIGH", "work_effort": "M",
            "status": "READY", "dependencies": [], "blockers": [], "owner": "developer",
            "ownership": [ownership], "quota_passed": True, "hitl_passed": True,
            "rule18_decision_valid": True,
        }],
        "reservations": [],
    }
    return command.build_invocation(
        route, command.render_prompt(objective="safe probe", ownership=ownership), tmp_path,
        decision=decision, model_policy=policy, objective="safe probe", ownership=ownership,
        runtime_config_path=runtime, runtime_config_approved=True,
        work_result_schema_path=work_schema,
        scheduling_snapshot=snapshot, claim_store_override=str(tmp_path / "dispatch-ledger"),
    )


def _authorized(tmp_path: Path) -> command.Invocation:
    base = _invocation(tmp_path)
    claim_path = tmp_path / "probe-claim.json"
    grant_path = tmp_path / "approval-grant.json"
    store = tmp_path / "consume-store"
    store.mkdir(mode=0o700)
    configured = replace(
        base, probe_claim_path=str(claim_path), approval_grant_path=str(grant_path),
        approval_store_path=str(store), approval_session_id="session-test",
    )
    command.emit_probe_claim(configured, claim_path, session_id="session-test")
    command.emit_probe_approval(
        configured, claim_path, grant_path, session_id="session-test"
    )
    return configured


def _codex_stream(result: dict[str, object]) -> str:
    return "\n".join((
        json.dumps({"type": "thread.started", "thread_id": "preauth-thread"}),
        json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(result)}}),
        json.dumps({"type": "turn.completed"}),
    )) + "\n"


def _fake_provider(work_result: dict[str, object]):
    def run(argv, **_kwargs):
        flag = "--output-last-message"
        Path(argv[argv.index(flag) + 1]).write_text(json.dumps(work_result), encoding="utf-8")
        return subprocess.CompletedProcess(argv, 0, _codex_stream(work_result), "")
    return run


def _write_private_json(path: Path, value: dict[str, object], *, canonical=True):
    payload = (
        command._canonical_json_bytes(value)
        if canonical
        else json.dumps(value, indent=2, sort_keys=True).encode("ascii")
    )
    path.write_bytes(payload)
    path.chmod(0o600)


def _rewrite_temporal_artifacts(
    invocation: command.Invocation,
    *,
    epoch: datetime,
    claim_created_seconds: int,
    grant_created_seconds: int,
) -> None:
    claim_path = Path(invocation.probe_claim_path)
    grant_path = Path(invocation.approval_grant_path)
    claim = json.loads(claim_path.read_text(encoding="ascii"))
    claim_created = epoch + timedelta(seconds=claim_created_seconds)
    claim["created_at"] = command._format_utc(claim_created)
    claim["expires_at"] = command._format_utc(
        claim_created + timedelta(seconds=command.PROBE_CLAIM_TTL_SECONDS)
    )
    claim["claim_id"] = command._artifact_address(claim, "claim_id")
    _write_private_json(claim_path, claim)

    grant = json.loads(grant_path.read_text(encoding="ascii"))
    grant_created = epoch + timedelta(seconds=grant_created_seconds)
    grant["claim_id"] = claim["claim_id"]
    grant["claim_sha256"] = command.hashlib.sha256(
        command._canonical_json_bytes(claim)
    ).hexdigest()
    grant["created_at"] = command._format_utc(grant_created)
    grant["expires_at"] = command._format_utc(
        grant_created + timedelta(seconds=command.APPROVAL_GRANT_TTL_SECONDS)
    )
    grant["grant_id"] = command._artifact_address(grant, "grant_id")
    _write_private_json(grant_path, grant)


def test_exact_authorization_consumes_once_and_emits_bound_receipt_v3(tmp_path, monkeypatch):
    invocation = _authorized(tmp_path)
    monkeypatch.setattr(command, "_run_provider_process", _fake_provider(_work_result()))
    outcome = command.execute_invocation(invocation)
    receipt = outcome.completed["execution_receipt"]
    consume = outcome.completed["approval_consume_receipt"]
    assert receipt["receipt_schema_version"] == 3
    assert receipt["approval_consume_receipt_id"] == consume["consume_id"]
    assert receipt["preauthorization_scope"] == command.PREAUTH_SCOPE
    assert consume["authenticity_claimed"] is False
    assert command.validate_execution_receipt(
        receipt, outcome.completed["work_result"], invocation,
        _codex_stream(_work_result()),
    ) == receipt


@pytest.mark.parametrize(
    "alternate_claim,alternate_grant,alternate_consume,alternate_ledger",
    [bits for bits in product((False, True), repeat=4) if any(bits)],
)
def test_frozen_artifacts_reject_every_alternate_store_cartesian_variant(
    tmp_path,
    monkeypatch,
    alternate_claim,
    alternate_grant,
    alternate_consume,
    alternate_ledger,
):
    invocation = _authorized(tmp_path)
    changed = invocation
    if alternate_claim:
        directory = tmp_path / "alternate-claim-store"
        directory.mkdir(mode=0o700)
        path = directory / "probe-claim.json"
        shutil.copyfile(invocation.probe_claim_path, path)
        path.chmod(0o600)
        changed = replace(changed, probe_claim_path=str(path))
    if alternate_grant:
        directory = tmp_path / "alternate-grant-store"
        directory.mkdir(mode=0o700)
        path = directory / "approval-grant.json"
        shutil.copyfile(invocation.approval_grant_path, path)
        path.chmod(0o600)
        changed = replace(changed, approval_grant_path=str(path))
    if alternate_consume:
        directory = tmp_path / "alternate-consume-store"
        directory.mkdir(mode=0o700)
        changed = replace(changed, approval_store_path=str(directory))
    if alternate_ledger:
        changed = replace(
            changed, claim_store_override=str(tmp_path / "alternate-ledger")
        )

    starts: list[tuple[object, ...]] = []
    provider = _fake_provider(_work_result())

    def counted_provider(*args, **kwargs):
        starts.append(args)
        return provider(*args, **kwargs)

    monkeypatch.setattr(command, "_run_provider_process", counted_provider)
    with pytest.raises(command.ProbeAuthorizationError):
        command.execute_invocation(changed)
    assert starts == []
    assert not list(tmp_path.rglob("*.consume.json"))

    command.execute_invocation(invocation)
    assert len(starts) == 1
    assert len(list(tmp_path.rglob("*.consume.json"))) == 1
    with pytest.raises((command.ConfigurationError, command.SchedulingError)):
        command.execute_invocation(changed)
    assert len(starts) == 1
    assert len(list(tmp_path.rglob("*.consume.json"))) == 1


def test_rename_symlink_and_hardlink_store_aliases_fail_before_consume_or_start(
    tmp_path, monkeypatch
):
    cases: list[command.Invocation] = []

    renamed = _authorized(tmp_path / "rename")
    moved_store = Path(renamed.probe_claim_path).parent / "renamed-claim-store"
    moved_store.mkdir(mode=0o700)
    moved_claim = moved_store / "probe-claim.json"
    Path(renamed.probe_claim_path).rename(moved_claim)
    cases.append(
        replace(
            renamed,
            probe_claim_path=str(moved_claim),
        )
    )

    symlinked = _authorized(tmp_path / "symlink")
    symlink_parent = tmp_path / "symlink-alias"
    symlink_parent.symlink_to(Path(symlinked.probe_claim_path).parent)
    cases.append(
        replace(
            symlinked,
            probe_claim_path=str(symlink_parent / "probe-claim.json"),
        )
    )

    linked = _authorized(tmp_path / "hardlink")
    hardlink_path = Path(linked.probe_claim_path).with_name("claim-hardlink.json")
    hardlink_path.hardlink_to(Path(linked.probe_claim_path))
    cases.append(replace(linked, probe_claim_path=str(hardlink_path)))

    starts: list[object] = []
    monkeypatch.setattr(
        command,
        "_run_provider_process",
        lambda *args, **kwargs: starts.append(args),
    )
    for candidate in cases:
        with pytest.raises((command.ProbeAuthorizationError, command.SchedulingError)):
            command.execute_invocation(candidate)
    assert starts == []
    assert not list(tmp_path.rglob("*.consume.json"))


def test_missing_or_wrong_session_and_symlink_fail_before_provider(tmp_path, monkeypatch):
    base = _invocation(tmp_path)
    called = False
    def forbidden(*_a, **_k):
        nonlocal called
        called = True
        raise AssertionError("provider must not start")
    monkeypatch.setattr(command, "_run_provider_process", forbidden)
    with pytest.raises(command.ProbeAuthorizationError):
        command.execute_invocation(base)
    authorized = _authorized(tmp_path / "wrong")
    with pytest.raises(command.ProbeAuthorizationError):
        command.execute_invocation(replace(authorized, approval_session_id="other-session"))
    symlink = tmp_path / "claim-link.json"
    symlink.symlink_to(authorized.probe_claim_path)
    with pytest.raises(command.ProbeAuthorizationError):
        command.execute_invocation(replace(authorized, probe_claim_path=str(symlink)))
    assert called is False


def test_malformed_expired_and_revoked_artifacts_fail_closed(tmp_path):
    base = _invocation(tmp_path)
    malformed = tmp_path / "malformed.json"
    malformed.write_text('{"schema_version":1,"schema_version":1}', encoding="ascii")
    malformed.chmod(0o600)
    with pytest.raises(command.ProbeAuthorizationError):
        command._secure_json_artifact(malformed)

    old = (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat(
        timespec="microseconds"
    ).replace("+00:00", "Z")
    configured = _authorized(tmp_path / "expired")
    bound = command._bind_invocation_to_current_stores(configured)
    expired = command.build_probe_claim(
        bound, session_id="session-test", created_at=old
    )
    with pytest.raises(command.ProbeAuthorizationError, match="expired"):
        command._validate_claim_record_v1(expired)

    authorized = _authorized(tmp_path / "revoked")
    grant_path = Path(authorized.approval_grant_path)
    grant = json.loads(grant_path.read_text(encoding="ascii"))
    grant["revoked"] = True
    grant["grant_id"] = command._artifact_address(grant, "grant_id")
    grant_path.write_text(json.dumps(grant, sort_keys=True, separators=(",", ":")), encoding="ascii")
    with pytest.raises(command.ProbeAuthorizationError):
        command._prepare_probe_authorization(authorized)


@pytest.mark.parametrize(
    "claim_offset,grant_offset,now_offset,reason",
    [
        (1, 1, 0, "not yet valid"),
        (0, 1, 0, "not yet valid"),
        (0, -1, 0, "temporal binding"),
        (0, 481, 500, "temporal binding"),
        (0, 0, 600, "expired"),
        (0, 0, 120, "expired"),
    ],
)
def test_temporal_future_order_and_expiry_boundaries_have_zero_provider_starts(
    tmp_path,
    monkeypatch,
    claim_offset,
    grant_offset,
    now_offset,
    reason,
):
    epoch = datetime(2026, 8, 26, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(command, "_utc_datetime", lambda: epoch)
    invocation = _authorized(tmp_path)
    _rewrite_temporal_artifacts(
        invocation,
        epoch=epoch,
        claim_created_seconds=claim_offset,
        grant_created_seconds=grant_offset,
    )
    captured = epoch + timedelta(seconds=now_offset)
    monkeypatch.setattr(command, "_utc_datetime", lambda: captured)
    starts: list[object] = []
    monkeypatch.setattr(
        command,
        "_run_provider_process",
        lambda *args, **kwargs: starts.append(args),
    )
    with pytest.raises(command.ProbeAuthorizationError, match=reason):
        command.execute_invocation(invocation)
    assert starts == []
    assert not list(Path(invocation.approval_store_path).glob("*.consume.json"))


def test_temporal_equal_created_and_equal_expiry_are_valid_with_one_captured_now(
    tmp_path, monkeypatch
):
    epoch = datetime(2026, 8, 26, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(command, "_utc_datetime", lambda: epoch)
    invocation = _authorized(tmp_path)
    _rewrite_temporal_artifacts(
        invocation,
        epoch=epoch,
        claim_created_seconds=0,
        grant_created_seconds=480,
    )
    captured = epoch + timedelta(seconds=480)
    calls = 0

    def one_now():
        nonlocal calls
        calls += 1
        return captured

    monkeypatch.setattr(command, "_utc_datetime", one_now)
    prepared = command._prepare_probe_authorization(invocation)
    prepared.close()
    assert calls == 1


@pytest.mark.parametrize(
    "mutation",
    ["attempt", "route", "prompt", "objective", "ownership", "policy"],
)
def test_every_exact_invocation_binding_rejects_substitution(tmp_path, mutation):
    invocation = _authorized(tmp_path)
    if mutation == "attempt":
        changed = replace(invocation, attempt_id=2)
    elif mutation == "route":
        changed = replace(
            invocation,
            route=replace(invocation.route, alias="codex2"),
        )
    elif mutation == "prompt":
        changed = replace(invocation, prompt_stdin=invocation.prompt_stdin + " altered")
    elif mutation == "objective":
        changed = replace(invocation, objective="altered objective")
    elif mutation == "ownership":
        changed = replace(invocation, ownership="tests/preauth/other.py")
    else:
        policy = dict(invocation.model_policy)
        policy["policy_version"] = "altered"
        changed = replace(invocation, model_policy=policy)
    with pytest.raises((command.ConfigurationError, command.SchedulingError)):
        command._prepare_probe_authorization(changed)


def test_policy_source_runtime_and_schema_digests_are_content_bound(tmp_path):
    invocation = _authorized(tmp_path)
    prepared = command._prepare_probe_authorization(invocation)
    try:
        binding = prepared.binding
        assert binding["model_policy_sha256"] == command._canonical_sha256(
            invocation.model_policy
        )
        assert binding["dispatcher_source_sha256"] == command._sha256_regular_file(
            Path(command.__file__), "dispatcher"
        )
    finally:
        prepared.close()
    Path(invocation.runtime_config_path).write_text("runtime: altered\n", encoding="utf-8")
    with pytest.raises(command.ProbeAuthorizationError, match="binding"):
        command._prepare_probe_authorization(invocation)

    second = _authorized(tmp_path / "schema")
    Path(second.work_result_schema_path).write_text("{}", encoding="utf-8")
    with pytest.raises(command.ProbeAuthorizationError, match="binding"):
        command._prepare_probe_authorization(second)


def test_two_consumers_have_exactly_one_winner(tmp_path):
    invocation = _authorized(tmp_path)

    def consume() -> str:
        prepared = command._prepare_probe_authorization(invocation)
        try:
            command._consume_prepared_approval(invocation, prepared)
            return "winner"
        except command.ProbeAuthorizationError:
            return "rejected"
        finally:
            prepared.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _index: consume(), range(2)))
    assert sorted(results) == ["rejected", "winner"]


def test_concurrent_alias_attempts_have_exactly_one_start_and_one_consume(
    tmp_path, monkeypatch
):
    invocation = _authorized(tmp_path)
    alternate = replace(
        invocation, route=replace(invocation.route, alias="codex2")
    )
    starts: list[str] = []
    provider = _fake_provider(_work_result())

    def counted_provider(*args, **kwargs):
        starts.append("started")
        return provider(*args, **kwargs)

    monkeypatch.setattr(command, "_run_provider_process", counted_provider)

    def run(candidate):
        try:
            command.execute_invocation(candidate)
            return "winner"
        except (command.ConfigurationError, command.SchedulingError):
            return "rejected"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(run, (invocation, alternate)))
    assert sorted(outcomes) == ["rejected", "winner"]
    assert starts == ["started"]
    assert len(list(Path(invocation.approval_store_path).glob("*.consume.json"))) == 1


def test_post_consume_failure_burns_grant_and_privacy_is_content_free(tmp_path, monkeypatch):
    invocation = _authorized(tmp_path)
    monkeypatch.setattr(
        command, "_run_provider_process",
        lambda *_a, **_k: (_ for _ in ()).throw(OSError("injected after consume")),
    )
    with pytest.raises(OSError):
        command.execute_invocation(invocation)
    with pytest.raises(command.ProbeAuthorizationError, match="already consumed"):
        command.execute_invocation(invocation)
    alternate = replace(
        invocation, route=replace(invocation.route, alias="codex2")
    )
    with pytest.raises((command.ConfigurationError, command.SchedulingError)):
        command.execute_invocation(alternate)
    durable = "\n".join(
        path.read_text(encoding="ascii", errors="ignore")
        for path in tmp_path.rglob("*.json")
    )
    assert "safe probe" not in durable
    assert "tests/preauth/owned.py" not in durable
    assert "raw_stream" not in durable or '"raw_streams_retained":false' in durable


def test_consume_schema_and_runtime_are_two_fully_closed_variants(tmp_path):
    invocation = _authorized(tmp_path)
    prepared = command._prepare_probe_authorization(invocation)
    try:
        receipt = command._consume_prepared_approval(invocation, prepared)
        anchor = dict(prepared.anchor_artifact.record)
        anchor_sha256 = command.hashlib.sha256(
            prepared.anchor_artifact.raw
        ).hexdigest()
    finally:
        prepared.close()
    consumed = command._parse_utc_timestamp(receipt["consumed_at"], "consumed")
    tombstone = {
        "schema_version": 1,
        "artifact_type": "ApprovalConsumeTombstone",
        "consume_id": receipt["consume_id"],
        "grant_id": receipt["grant_id"],
        "original_receipt_sha256": command.hashlib.sha256(
            command._canonical_json_bytes(receipt)
        ).hexdigest(),
        "consume_anchor_id": anchor["anchor_id"],
        "consume_anchor_sha256": anchor_sha256,
        "consumed_at": receipt["consumed_at"],
        "compacted_at": command._format_utc(consumed + timedelta(days=91)),
        "anti_replay": True,
        "retention": "indefinite",
        "attestation_scope": command.PREAUTH_SCOPE,
        "authenticity_claimed": False,
        "raw_streams_retained": False,
    }
    schema = json.loads(
        command.DEFAULT_APPROVAL_CONSUME_SCHEMA.read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    assert all(variant["additionalProperties"] is False for variant in schema["oneOf"])
    assert not list(validator.iter_errors(receipt))
    assert not list(validator.iter_errors(tombstone))
    assert command._validate_consume_record_v1(receipt) == receipt
    assert command._validate_consume_record_v1(tombstone) == tombstone

    invalid = (
        dict(receipt, anti_replay=True),
        dict(tombstone, claim_id=receipt["claim_id"]),
        dict(receipt, unknown="blocked"),
        dict(tombstone, unknown="blocked"),
    )
    for candidate in invalid:
        assert list(validator.iter_errors(candidate))
        with pytest.raises(command.ProbeAuthorizationError, match="variant fields"):
            command._validate_consume_record_v1(candidate)
    nested = dict(receipt)
    nested["binding"] = dict(receipt["binding"], unexpected="blocked")
    nested["consume_id"] = command._artifact_address(nested, "consume_id")
    assert list(validator.iter_errors(nested))
    with pytest.raises(command.ProbeAuthorizationError, match="binding fields"):
        command._validate_consume_record_v1(nested)


@pytest.mark.parametrize(
    "mutation",
    [
        "backdate_readdress",
        "canonical_reencoding",
        "missing_anchor",
        "wrong_anchor_hash",
        "wrong_anchor_timestamp",
    ],
)
def test_receipt_validation_rejects_raw_consume_and_anchor_mutations(
    tmp_path, monkeypatch, mutation
):
    invocation = _authorized(tmp_path)
    monkeypatch.setattr(
        command, "_run_provider_process", _fake_provider(_work_result())
    )
    outcome = command.execute_invocation(invocation)
    consume = outcome.completed["approval_consume_receipt"]
    consume_path = (
        Path(invocation.approval_store_path)
        / f"{consume['grant_id']}.consume.json"
    )
    anchor_path = (
        Path(invocation.claim_store_override)
        / command._consume_anchor_name(consume["grant_id"])
    )
    if mutation == "backdate_readdress":
        changed = json.loads(consume_path.read_text(encoding="ascii"))
        timestamp = command._parse_utc_timestamp(changed["consumed_at"], "consume")
        changed["consumed_at"] = command._format_utc(timestamp - timedelta(days=1))
        changed["consume_id"] = command._artifact_address(changed, "consume_id")
        _write_private_json(consume_path, changed)
    elif mutation == "canonical_reencoding":
        changed = json.loads(consume_path.read_text(encoding="ascii"))
        _write_private_json(consume_path, changed, canonical=False)
    elif mutation == "missing_anchor":
        anchor_path.unlink()
    else:
        changed = json.loads(anchor_path.read_text(encoding="ascii"))
        if mutation == "wrong_anchor_hash":
            changed["consume_receipt_sha256"] = "0" * 64
        else:
            timestamp = command._parse_utc_timestamp(
                changed["consumed_at"], "anchor"
            )
            changed["consumed_at"] = command._format_utc(
                timestamp + timedelta(microseconds=1)
            )
        changed["anchor_id"] = command._artifact_address(changed, "anchor_id")
        _write_private_json(anchor_path, changed)

    with pytest.raises(command.ConfigurationError):
        command.validate_execution_receipt(
            outcome.completed["execution_receipt"],
            outcome.completed["work_result"],
            invocation,
            _codex_stream(_work_result()),
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "backdate_readdress",
        "canonical_reencoding",
        "missing_anchor",
        "wrong_anchor_hash",
        "wrong_anchor_timestamp",
    ],
)
def test_compaction_rejects_raw_consume_and_anchor_mutations(tmp_path, mutation):
    invocation = _authorized(tmp_path)
    prepared = command._prepare_probe_authorization(invocation)
    try:
        consume = command._consume_prepared_approval(invocation, prepared)
    finally:
        prepared.close()
    consume_path = (
        Path(invocation.approval_store_path)
        / f"{consume['grant_id']}.consume.json"
    )
    anchor_path = (
        Path(invocation.claim_store_override)
        / command._consume_anchor_name(consume["grant_id"])
    )
    if mutation == "backdate_readdress":
        changed = json.loads(consume_path.read_text(encoding="ascii"))
        timestamp = command._parse_utc_timestamp(changed["consumed_at"], "consume")
        changed["consumed_at"] = command._format_utc(
            timestamp - timedelta(days=91)
        )
        changed["consume_id"] = command._artifact_address(changed, "consume_id")
        _write_private_json(consume_path, changed)
    elif mutation == "canonical_reencoding":
        changed = json.loads(consume_path.read_text(encoding="ascii"))
        _write_private_json(consume_path, changed, canonical=False)
    elif mutation == "missing_anchor":
        anchor_path.unlink()
    else:
        changed = json.loads(anchor_path.read_text(encoding="ascii"))
        if mutation == "wrong_anchor_hash":
            changed["consume_receipt_sha256"] = "0" * 64
        else:
            timestamp = command._parse_utc_timestamp(
                changed["consumed_at"], "anchor"
            )
            changed["consumed_at"] = command._format_utc(
                timestamp + timedelta(microseconds=1)
            )
        changed["anchor_id"] = command._artifact_address(changed, "anchor_id")
        _write_private_json(anchor_path, changed)
    with pytest.raises(command.ProbeAuthorizationError):
        command.compact_approval_consume_tombstone(
            invocation.approval_store_path,
            consume["grant_id"],
            invocation=invocation,
        )


def test_manual_compaction_only_after_90_days_retains_indefinite_tombstone(
    tmp_path, monkeypatch
):
    invocation = _authorized(tmp_path)
    prepared = command._prepare_probe_authorization(invocation)
    try:
        consume = command._consume_prepared_approval(invocation, prepared)
    finally:
        prepared.close()
    with pytest.raises(command.ProbeAuthorizationError, match="not eligible"):
            command.compact_approval_consume_tombstone(
            invocation.approval_store_path,
            consume["grant_id"],
            invocation=invocation,
        )
    current_now = datetime.now(timezone.utc)
    historical_now = current_now - timedelta(days=91)
    monkeypatch.setattr(command, "_utc_datetime", lambda: historical_now)
    old_invocation = _authorized(tmp_path / "historical")
    old_prepared = command._prepare_probe_authorization(old_invocation)
    try:
        consume = command._consume_prepared_approval(old_invocation, old_prepared)
    finally:
        old_prepared.close()
    monkeypatch.setattr(command, "_utc_datetime", lambda: current_now)
    tombstone = command.compact_approval_consume_tombstone(
        old_invocation.approval_store_path,
        consume["grant_id"],
        invocation=old_invocation,
    )
    assert tombstone["anti_replay"] is True
    assert tombstone["retention"] == "indefinite"
    schema = json.loads(
        command.DEFAULT_APPROVAL_CONSUME_SCHEMA.read_text(encoding="utf-8")
    )
    assert not list(
        Draft202012Validator(
            schema, format_checker=FormatChecker()
        ).iter_errors(tombstone)
    )
    assert command._validate_consume_record_v1(tombstone) == tombstone
    with pytest.raises(command.ProbeAuthorizationError, match="already consumed"):
        command._prepare_probe_authorization(old_invocation)
