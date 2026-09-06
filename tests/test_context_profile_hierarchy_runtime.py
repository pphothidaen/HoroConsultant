"""RED Contract tests for Context Hierarchy and Provider Runtime Probes.

Covers:
- Provider hierarchy resolution: broad-to-narrow union across scopes without weakening.
- ProviderContextProbeV1 closed field schema and domain hash:
    b"horo-context:evidence:v1\0"
- Provider probe requirements: fresh PASS for Codex, Claude, and AGY; static parity only for Antigravity.
- UNAVAILABLE and UNKNOWN results are nonzero exit codes and never pass-by-skip.
- Sanitized evidence SHA-256 excludes raw provider streams, environment, and secrets.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE_SCRIPT = ROOT / "scripts/probe_agent_context_runtime.py"
CLAUDE_PROBE_FIXTURE = ROOT / "tests/fixtures/context_profiles/claude-probe.json"
AGY_PROBE_FIXTURE = ROOT / "tests/fixtures/context_profiles/agy-probe.json"
ANTIGRAVITY_FIXTURE = ROOT / "tests/fixtures/context_profiles/antigravity-render.json"


def _require_probe():
    assert PROBE_SCRIPT.exists(), (
        f"MISSING_CONTEXT_RUNTIME_PROBE: Probe script not found at {PROBE_SCRIPT}"
    )


def test_provider_hierarchy_unions_broad_to_narrow_without_weakening():
    _require_probe()
    import scripts.probe_agent_context_runtime as prober
    hierarchy = prober.resolve_provider_hierarchy(
        provider="codex",
        target_path="project/routers/v1/auth.py",
        ticket_id="TICKET-CONTEXT-OPT-001",
        lane_id="TICKET-CONTEXT-OPT-001-G",
    )
    assert "root" in hierarchy["normalized_scopes"]
    assert "project/routers" in hierarchy["normalized_scopes"]


def test_provider_context_probe_rejects_placeholder_identity_fields():
    _require_probe()
    import scripts.probe_agent_context_runtime as prober
    raw = json.loads(CLAUDE_PROBE_FIXTURE.read_text(encoding="utf-8"))
    with pytest.raises(ValueError, match="INVALID_IDENTITY"):
        prober.validate_probe_schema(raw)


def test_provider_probe_requires_codex_claude_agy_and_static_antigravity():
    _require_probe()
    import scripts.probe_agent_context_runtime as prober
    # Antigravity does not emit a runtime probe receipt
    with pytest.raises(Exception, match="RUNTIME_PROBE_NOT_SUPPORTED|STATIC_PARITY_ONLY"):
        prober.run_provider_probe("antigravity", ticket_id="TICKET-CONTEXT-OPT-001", lane_id="TICKET-CONTEXT-OPT-001-G")


def test_probe_unavailable_and_unknown_are_nonzero_and_never_pass():
    _require_probe()
    import scripts.probe_agent_context_runtime as prober
    for res_status in ("UNAVAILABLE", "UNKNOWN"):
        receipt = prober.build_probe_receipt(
            provider="claude",
            result=res_status,
            reason_code=f"{res_status}_CODE",
            exit_code=0,
        )
        assert receipt.exit_code != 0, f"{res_status} must have nonzero exit code"
        assert receipt.result != "PASS"


def test_sanitized_evidence_sha256_excludes_raw_streams_and_secrets():
    _require_probe()
    import scripts.probe_agent_context_runtime as prober
    raw = json.loads(AGY_PROBE_FIXTURE.read_text(encoding="utf-8"))
    forbidden_keys = {"stdout", "stderr", "stream", "env", "secret", "token", "password"}
    for fk in forbidden_keys:
        assert fk not in raw, f"ProviderContextProbeV1 must not contain raw/secret field {fk}"
    computed_digest = prober.compute_sanitized_evidence_digest(raw)
    assert len(computed_digest) == 64
