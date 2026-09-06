"""Offline characterization only: all provider data below is synthetic.

These tests establish neither native eligibility nor live Spark capability and
are not a RED baseline authorizing production source changes.
"""

from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def command(monkeypatch):
    # Adjacent legacy tests replace functions on the usual imported module.
    # Load the actual source independently so collection order cannot replace
    # the validators under characterization with test-local implementations.
    name = "scripts._external_dispatch_characterization"
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "scripts/multiagent_prompt_command.py"
    )
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module.shutil, "which", lambda _name: None)
    monkeypatch.setattr(
        module.subprocess, "Popen", Mock(side_effect=AssertionError("offline only"))
    )
    monkeypatch.setattr(
        module.subprocess, "run", Mock(side_effect=AssertionError("offline only"))
    )
    monkeypatch.setattr(
        module, "_run_provider_process", Mock(side_effect=AssertionError("offline only"))
    )
    return module


@pytest.fixture
def spark(command, tmp_path):
    policy = command.load_model_policy(ROOT / ".agents/config/multiagent_model_policy.yaml")
    route = command.Route(
        role="code_reviewer", alias="codex1", cli="codex", command="codex",
        home_env="CODEX_HOME", home_path=None, model="gpt-5.3-codex-spark",
        effort="high", mode=None, sandbox="read-only",
    )
    decision = {
        "schema_version": 1, "ticket": "TICKET-SYNTHETIC-EXTERNAL-CONTRACT",
        "phase": "review", "scope_rank": 3, "complexity_rank": 3,
        "risk_rank": 1, "ambiguity_rank": 1, "evidence_burden_rank": 3,
        "quota_band": "healthy", "work_mode": "read_only",
        "selected_alias": route.alias, "selected_model": route.model,
        "selected_effort": route.effort, "rationale": "synthetic offline characterization",
        "policy_version": policy["policy_version"],
        "planning_to_medium_confirmed": True, "hitl_approved": False,
    }
    return command.build_invocation(
        route, "Synthetic offline review", tmp_path,
        decision=decision, model_policy=policy,
    )


@pytest.fixture
def synthetic_result():
    return {
        "status": "DONE", "scope_owned": ["synthetic fixture only"],
        "evidence": {"commands": [], "outcomes": ["synthetic, no execution"], "artifacts": []},
        "findings": ["Synthetic self-report: effective model is gpt-5.3-codex-spark"],
        "changed_files": [], "residual_risk": "Live capability is unproven",
        "recommended_next_action": "Obtain independent platform evidence",
    }


def synthetic_jsonl(*results):
    events = [{"type": "thread.started", "thread_id": "synthetic-thread-1"}]
    events.extend({"type": "item.completed", "item": {
        "type": "agent_message", "text": json.dumps(result),
    }} for result in results)
    events.append({"type": "turn.completed"})
    return "\n".join(json.dumps(event) for event in events) + "\n"


@pytest.mark.parametrize("role", ["devops", "code_reviewer"])
@pytest.mark.parametrize("phase", ["qa", "review", "release", "operations"])
def test_spark_scoped_read_only_exact_argv(command, spark, role, phase):
    invocation = command.build_invocation(
        replace(spark.route, role=role), "Synthetic review", spark.cwd,
        decision={**spark.decision, "phase": phase}, model_policy=spark.model_policy,
    )
    validated = command.validate_dispatch_decision(
        invocation.decision, invocation.model_policy, invocation.route
    )
    assert validated.quality_floor == validated.model_quality_rank == 3
    assert invocation.argv == (
        "codex", "exec", "-C", spark.cwd, "-s", "read-only",
        "-m", "gpt-5.3-codex-spark", "-c", 'model_reasoning_effort="high"',
        "--ephemeral", "--json", "--output-schema", str(command.DEFAULT_WORK_RESULT_SCHEMA), "-",
    )
    assert invocation.work_result_schema_path == str(command.DEFAULT_WORK_RESULT_SCHEMA)
    command.subprocess.Popen.assert_not_called()


@pytest.mark.parametrize("field,value", [
    ("role", "developer"), ("role", "qa_tester"), ("role", "business_analyst"),
    ("phase", "implementation"), ("phase", "planning"),
    ("effort", "low"), ("effort", "medium"), ("effort", "xhigh"),
])
def test_spark_builder_rejects_out_of_scope_selection(command, spark, field, value):
    route = replace(spark.route, **{field: value}) if field != "phase" else spark.route
    decision = dict(spark.decision)
    if field == "phase":
        decision["phase"] = value
    elif field == "effort":
        decision["selected_effort"] = value
    with pytest.raises(command.DispatchDecisionError):
        command.build_invocation(route, "Synthetic review", spark.cwd,
                                 decision=decision, model_policy=spark.model_policy)
    command.subprocess.Popen.assert_not_called()


@pytest.mark.parametrize("identity", ["agy", "agy1", "agy2", "agy3", "AgY2.exe", "symlink", "declared"])
def test_synthetic_native_claim_cannot_bypass_agy_prespawn_denial(
    command, spark, tmp_path, monkeypatch, identity,
):
    executable = identity
    if identity == "symlink":
        target = tmp_path / "agy2"
        target.touch()
        link = tmp_path / "codex"
        link.symlink_to(target)
        executable = str(link)
    route = replace(spark.route, command=executable)
    if identity == "declared":
        executable = "codex"
        route = replace(spark.route, cli="agy", alias="agy1")
    # Deliberately convincing caller metadata is untrusted, not a real receipt.
    local_claim = {
        "synthetic": True, "schema": "LocalSupervisorReceipt",
        "decision": "ALLOW", "platform_native": True,
        "effective_model": "claude-opus-4-6", "effective_effort": "high",
        "session_id": "synthetic-thread-1", "receipt_sha256": "a" * 64,
    }
    invocation = replace(
        spark, route=route, argv=(executable, *spark.argv[1:]),
        decision={**spark.decision, "native_receipt": local_claim},
        env_overrides={"SYNTHETIC_NATIVE_RECEIPT": json.dumps(local_claim)},
    )
    blocked_steps = {}
    for name in (
        "_validated_invocation_decision", "validate_execution_preflight",
        "_prepare_probe_authorization", "_consume_prepared_approval",
        "_acquire_dispatch_claim", "_run_provider_process",
    ):
        blocked_steps[name] = Mock(side_effect=AssertionError(f"unreachable: {name}"))
        monkeypatch.setattr(command, name, blocked_steps[name])
    with pytest.raises(command.PlatformNativePrespawnReceiptRequired) as exc:
        command.execute_invocation(invocation)
    assert exc.value.code == "PLATFORM_NATIVE_PRESPAWN_RECEIPT_REQUIRED"
    for step in blocked_steps.values():
        step.assert_not_called()
    command.subprocess.Popen.assert_not_called()


@pytest.mark.parametrize("case", ["duplicate", "conflict", "malformed"])
def test_spark_parser_rejects_ambiguous_or_conflicting_final(command, spark, synthetic_result, case):
    telemetry = synthetic_jsonl(synthetic_result)
    final = synthetic_result
    expected = "work_result_validation"
    if case == "duplicate":
        telemetry = synthetic_jsonl(synthetic_result, synthetic_result)
        expected = "final_message_cardinality"
    elif case == "conflict":
        final = {**synthetic_result, "findings": ["Conflicting synthetic final"]}
    else:
        telemetry = "{invalid-json}\n"
        expected = "terminal_shape"
    with pytest.raises(command.ProviderParseError) as exc:
        command.parse_provider_result(spark, telemetry, private_final=final)
    assert exc.value.provider_parse_reason == expected


def test_successful_synthetic_spark_output_does_not_prove_effective_model(command, spark, synthetic_result):
    telemetry = synthetic_jsonl(synthetic_result)
    parsed = command.parse_provider_result(spark, telemetry, private_final=synthetic_result)
    assert parsed.work_result["status"] == "DONE"
    # In-memory transport evidence only: no process, receipt or live proof.
    process = subprocess.CompletedProcess(spark.argv, 0, telemetry, "")
    for channel in ("stdout", "stderr"):
        raw = getattr(process, channel).encode()
        setattr(process, f"_{channel}_bytes", len(raw))
        setattr(process, f"_{channel}_sha256", hashlib.sha256(raw).hexdigest())
    final_raw = json.dumps(synthetic_result).encode()
    process._private_final_result = command.PrivateFinalResult(
        synthetic_result, len(final_raw), hashlib.sha256(final_raw).hexdigest()
    )
    process._private_final_bytes = len(final_raw)
    process._private_final_sha256 = hashlib.sha256(final_raw).hexdigest()
    process._private_final_work_result_sha256 = command._canonical_sha256(synthetic_result)
    process._sanitized_argv = ["codex", "exec", "-m", "gpt-5.3-codex-spark"]
    process._sanitized_argv_sha256 = command._canonical_sha256(process._sanitized_argv)
    provenance = command._execution_provenance(spark, process, parsed)
    assert provenance["requested"]["model"] == "gpt-5.3-codex-spark"
    assert provenance["requested"]["effort"] == "high"
    assert provenance["effective"] == dict.fromkeys(("model", "effort", "account", "quota"), "NOT PROVEN")
    assert provenance["cli_version"] == "NOT PROVEN"
    command.subprocess.Popen.assert_not_called()
