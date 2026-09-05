"""Offline RED baseline: Context G receipts must reflect measured source state.

Only temporary fixtures are mutated. No provider executable, account config, or
historical evidence receipt is used as an authority or written by these tests.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import socket
import subprocess

import pytest

from scripts import render_agent_context_profiles as render
from scripts import probe_agent_context_runtime as probe
from scripts import optimize_codex_skill_budget as budget
from scripts import sync_ai_agent_ecosystem as ecosystem

ROOT = Path(__file__).resolve().parents[1]
HEAD = "1577f8c49507e4e348597164e686a46419b9d6d3"
CONTEXT = ".agents/context/tickets/TICKET-CONTEXT-OPT-001-G-EVIDENCE-BASELINE-002.v1.json"
REGISTRY = ".agents/config/scope_skill_registry.v1.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def put(root, path, text):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


@pytest.fixture
def offline(monkeypatch):
    def prohibited(*args, **kwargs):
        pytest.fail("UNAUTHORIZED_PROVIDER_OR_CHILD_CALL")
    monkeypatch.setattr(socket, "create_connection", prohibited)
    monkeypatch.setattr(socket.socket, "connect", prohibited)
    monkeypatch.setattr(subprocess, "Popen", prohibited)


def fixture_paths():
    explicit = [REGISTRY, CONTEXT, ".agents/AGENTS.md",
                ".agents/rules/16-hf-static-release-verification.md",
                ".claude/rules/hf-static-release-verification.md",
                ".agents/skills/hf-static-release-verification/evals/evals.json"]
    patterns = [".agents/schemas/*.json", ".agents/skills/*/SKILL.md",
                ".agents/agents/*/agent.json", ".antigravity/agents/*.agent",
                ".codex/agents/*.toml"]
    return sorted({Path(p) for p in explicit} |
                  {p.relative_to(ROOT) for pattern in patterns for p in ROOT.glob(pattern)})


@pytest.fixture
def repo(tmp_path, monkeypatch, offline):
    for relative in fixture_paths():
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    put(tmp_path, ".git/HEAD", HEAD + "\n")
    for module in (render, probe, ecosystem):
        monkeypatch.setattr(module, "ROOT", tmp_path)
    for module in (render, probe):
        monkeypatch.setattr(module, "REGISTRY_PATH", tmp_path / REGISTRY)
        monkeypatch.setattr(module, "APPROVED_TICKETS_DIR", tmp_path / ".agents/context/tickets")
    return tmp_path


@pytest.mark.parametrize("target", [".codex/agents/devops.toml", ".antigravity/agents/devops.agent"])
def test_render_manifest_hashes_actual_provider_artifacts(repo, target):
    manifest = render.get_current_manifest(repo)
    inventory = {item["path"]: item["sha256"] for item in manifest["inventory"]}
    assert inventory.get(target) == digest(repo / target), "RENDER_ARTIFACT_HASH_MISSING"
    put(repo, target, (repo / target).read_text() + "\n# tampered\n")
    changed = render.get_current_manifest(repo)
    assert changed["manifest_sha256"] != manifest["manifest_sha256"], "RENDER_TAMPER_NOT_BOUND"


@pytest.mark.parametrize("identity", [REGISTRY, CONTEXT, ".git/HEAD"])
def test_render_manifest_binds_current_identity(repo, identity):
    before = render.get_current_manifest(repo)
    path = repo / identity
    if identity == ".git/HEAD":
        path.write_text("a" * 40 + "\n")
    else:
        data = json.loads(path.read_text())
        data["revision" if identity == CONTEXT else "registry_version"] = 999
        path.write_text(json.dumps(data))
    after = render.get_current_manifest(repo)
    assert after["manifest_sha256"] != before["manifest_sha256"], "RENDER_IDENTITY_NOT_BOUND"


@pytest.mark.parametrize("mutation", ["missing", "tampered", "extra"])
def test_render_check_rejects_bad_inventory(repo, mutation):
    target = repo / ".codex/agents/devops.toml"
    if mutation == "missing":
        target.unlink()
    elif mutation == "tampered":
        target.write_text('name = "unauthorized-role"\n')
    else:
        put(repo, ".codex/agents/unauthorized.toml", 'name = "unauthorized"\n')
    before = {str(p.relative_to(repo)): digest(p) for p in repo.rglob("*") if p.is_file()}
    results = render.check_context_profiles(output_root=repo)
    assert results and not all(item.ok for item in results), "UNCONDITIONAL_RENDER_PASS"
    assert before == {str(p.relative_to(repo)): digest(p) for p in repo.rglob("*") if p.is_file()}


def test_antigravity_parity_rejects_semantic_tamper(repo):
    put(repo, ".antigravity/agents/devops.agent", 'name: devops\ntools: [unauthorized]\n')
    assert render.verify_provider_scope_parity() is False, "UNCONDITIONAL_ANTIGRAVITY_PARITY"


def test_budget_measurement_is_reproducible_and_source_bound(repo):
    evaluate = getattr(budget, "evaluate_all_profiles", None)
    assert callable(evaluate), "BUDGET_MEASUREMENT_API_MISSING"
    first = evaluate(project_root=repo)
    second = evaluate(project_root=repo)
    assert first == second, "BUDGET_NOT_REPRODUCIBLE"
    assert first.get("measurement_command"), "BUDGET_MEASUREMENT_COMMAND_MISSING"
    sources = first.get("source_sha256", {})
    for relative in (REGISTRY, CONTEXT):
        assert sources.get(relative) == digest(repo / relative), "BUDGET_SOURCE_IDENTITY_MISSING"
    assert first.get("head_commit") == HEAD, "BUDGET_HEAD_IDENTITY_MISSING"
    assert first.get("profiles"), "BUDGET_EMPTY_MEASUREMENT"
    assert first.get("native_prompt_proof") is False, "STATIC_BUDGET_IS_NOT_NATIVE_PROMPT_PROOF"
    for profile in first["profiles"]:
        paths = profile.get("measured_paths", [])
        assert paths, "BUDGET_MEASURED_INPUTS_MISSING"
        text = "".join((repo / p).read_text() for p in paths)
        assert profile["total_prompt_characters"] == len(text), "BUDGET_INVENTED_PROMPT_LENGTH"
    skill = repo / ".agents/skills/qa-regression-provenance/SKILL.md"
    skill.write_text(skill.read_text() + "\n" + "X" * 9000)
    changed = evaluate(project_root=repo)
    assert changed != first, "BUDGET_STALE_SOURCE_ACCEPTED"
    assert changed["all_within_budget"] is False, "BUDGET_OVERRUN_NOT_REJECTED"


@pytest.mark.parametrize("provider", ["codex", "claude", "agy"])
def test_offline_probe_never_fabricates_native_pass(repo, provider):
    receipt = probe.run_provider_probe(provider, "TICKET-CONTEXT-OPT-001", "G", no_network=True)
    assert receipt["result"] in {"UNAVAILABLE", "UNKNOWN"}, "SYNTHETIC_NATIVE_PASS"
    assert receipt["exit_code"] != 0, "OFFLINE_NATIVE_PROOF_FAIL_OPEN"


def receipt_fixture():
    # Deliberately only a signed static assertion, never a native observation.
    raw = dict(schema_version="provider-context-probe-v1", provider="codex",
               adapter_version="codex-probe-v1", registry_sha256="a" * 64,
               approved_context_sha256="b" * 64, normalized_scopes=["root"],
               horo_skills=[], provider_plugins=[], runtime_tools=[], result="UNKNOWN",
               reason_code="STATIC_VALIDATION_ONLY", exit_code=1,
               issued_at="2026-09-05T16:00:00Z", expires_at="2026-09-05T16:02:00Z")
    raw["sanitized_evidence_sha256"] = probe.compute_sanitized_evidence_digest(raw)
    return raw


@pytest.mark.parametrize("mutation", ["zero-registry", "zero-context", "tampered-digest", "invalid-exit"])
def test_probe_schema_rejects_invalid_evidence(mutation, offline):
    raw = receipt_fixture()
    if mutation == "zero-registry":
        raw["registry_sha256"] = "0" * 64
    elif mutation == "zero-context":
        raw["approved_context_sha256"] = "0" * 64
    elif mutation == "invalid-exit":
        raw["exit_code"] = 0
    if mutation == "tampered-digest":
        raw["reason_code"] = "TAMPERED"
    else:
        raw["sanitized_evidence_sha256"] = probe.compute_sanitized_evidence_digest(raw)
    rejected = False
    try:
        probe.validate_probe_schema(raw)
    except ValueError:
        rejected = True
    assert rejected, "INVALID_PROBE_EVIDENCE_ACCEPTED"


@pytest.mark.parametrize("mutation", ["expired", "future", "registry", "context", "synthetic-pass"])
def test_runtime_evidence_requires_fresh_matching_native_proof(mutation, offline):
    validate = getattr(probe, "validate_probe_receipt", None)
    assert callable(validate), "RUNTIME_EVIDENCE_VALIDATOR_MISSING"
    raw = receipt_fixture()
    now = dt.datetime(2026, 9, 5, 16, 1, tzinfo=dt.timezone.utc)
    if mutation == "expired":
        now += dt.timedelta(minutes=2)
    elif mutation == "future":
        now -= dt.timedelta(minutes=2)
    elif mutation in {"registry", "context"}:
        raw["registry_sha256" if mutation == "registry" else "approved_context_sha256"] = "c" * 64
    else:
        raw.update(result="PASS", reason_code="CODEX_PROBE_OK", exit_code=0)
    raw["sanitized_evidence_sha256"] = probe.compute_sanitized_evidence_digest(raw)
    with pytest.raises(ValueError):
        validate(raw, expected_registry_sha256="a" * 64,
                 expected_approved_context_sha256="b" * 64, now=now, require_native=(mutation == "synthetic-pass"))


def test_antigravity_runtime_is_explicitly_unsupported(offline):
    with pytest.raises(ValueError, match="STATIC_PARITY_ONLY"):
        probe.run_provider_probe("antigravity", "TICKET-CONTEXT-OPT-001", "G")


def test_unknown_receipt_retains_nonzero_exit(offline):
    raw = probe.build_probe_receipt("codex", "UNKNOWN", "STATIC_VALIDATION_ONLY",
                                    registry_sha256="a" * 64, approved_context_sha256="b" * 64)
    assert raw["result"] == "UNKNOWN" and raw["exit_code"] != 0


def test_native_devops_contract_passes_governance(repo):
    result = ecosystem.check_hf_static_release_governance()
    assert result.ok, "NATIVE_HF_VERCEL_OWNER_CONTRACT_REJECTED: " + result.detail


def test_marker_alone_cannot_authorize_azure(repo):
    # A marker-only 'fix' must not legitimize obsolete platform authority.
    for path in (repo / ".agents/agents/devops/agent.json",):
        raw = json.loads(path.read_text())
        raw["system_prompt"] += "\nHF Static Release Gate Owner\nPrimary Backend: Azure Container Apps (ACA)."
        path.write_text(json.dumps(raw))
    generated = repo / ".codex/agents/devops.toml"
    generated.write_text(generated.read_text() + "\n# HF Static Release Gate Owner\n")
    result = ecosystem.check_hf_static_release_governance()
    assert not result.ok, "UNSUPPORTED_AZURE_AUTHORITY_ACCEPTED"


def test_static_receipt_validation_does_not_require_native_proof(offline):
    validate = getattr(probe, "validate_probe_receipt", None)
    assert callable(validate), "RUNTIME_EVIDENCE_VALIDATOR_MISSING"
    # Acceptance of a fresh UNKNOWN receipt only proves static validity.
    validate(receipt_fixture(), expected_registry_sha256="a" * 64,
             expected_approved_context_sha256="b" * 64,
             now=dt.datetime(2026, 9, 5, 16, 1, tzinfo=dt.timezone.utc),
             require_native=False)


def test_rendered_fixture_is_checkable(repo):
    render.render_all(output_root=repo)
    results = render.check_context_profiles(output_root=repo)
    assert results and all(item.ok for item in results), "RENDERED_FIXTURE_REJECTED"
    assert render.verify_provider_scope_parity() is True, "RENDERED_PARITY_REJECTED"


def test_truthful_native_hf_vercel_fixture_is_accepted(repo):
    import yaml
    path = repo / ".agents/agents/devops/agent.json"
    data = json.loads(path.read_text())
    data["system_prompt"] = (
        "HF Static Release Gate Owner. Primary backend: HF Spaces Docker. "
        "Vercel static UI. SDK-aware fail-closed exact-cardinality verification; "
        "five canonical viewports; rollback uses prior HF revision and Vercel deployment."
    )
    path.write_text(json.dumps(data))
    # This is isolated generated fixture data, not edits to managed repo mirrors.
    put(repo, ".codex/agents/devops.toml", 'name = "devops"\n# ' + data["system_prompt"]
        + "\n# hf-static-release-verification\n")
    alias = repo / ".antigravity/agents/devops.agent"
    mirrored = yaml.safe_load(alias.read_text())
    mirrored["system_prompt"] = data["system_prompt"]
    alias.write_text(yaml.safe_dump(mirrored))
    result = ecosystem.check_hf_static_release_governance()
    assert result.ok, "TRUTHFUL_NATIVE_OWNER_FIXTURE_REJECTED: " + result.detail


def test_small_budget_fixture_is_within_budget(repo):
    evaluate = getattr(budget, "evaluate_all_profiles", None)
    assert callable(evaluate), "BUDGET_MEASUREMENT_API_MISSING"
    # Preserve profile membership and skill metadata while making actual bodies small.
    for skill in (repo / ".agents/skills").glob("*/SKILL.md"):
        original = skill.read_text()
        parts = original.split("---", 2)
        if len(parts) == 3 and not parts[0].strip():
            skill.write_text("---" + parts[1] + "---\nSmall QA fixture.\n")
        else:
            skill.write_text("Small QA fixture.\n")
    for agent in (repo / ".agents/agents").glob("*/agent.json"):
        data = json.loads(agent.read_text())
        data["system_prompt"] = "Small QA fixture."
        agent.write_text(json.dumps(data))
    report = evaluate(project_root=repo)
    assert report.get("profiles"), "SMALL_BUDGET_FIXTURE_EMPTY"
    assert report.get("all_within_budget") is True, "SMALL_BUDGET_FIXTURE_REJECTED"
    for profile in report["profiles"]:
        assert 0 < profile["total_prompt_characters"] <= 8000, "SMALL_BUDGET_MEASUREMENT_INVALID"
        assert profile.get("within_budget") is True, "SMALL_PROFILE_REJECTED"
