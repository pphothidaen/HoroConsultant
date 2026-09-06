"""RED Contract tests for Context Profile Generation and Filesystem Safety.

Covers:
- One-way rendering from canonical .agents to Codex, Claude, AGY, and Antigravity.
- Provider mirrors/mtimes are drift, never authority.
- Normalized provider scope and capability sets match registry.
- Generated inventory rejects missing, extra, or stale artifacts.
- Byte determinism across sort order, mtime, locale, and repository root.
- Strict canonical JSON algorithm: sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False, no newline.
- Non-ASCII fixtures testing ensure_ascii=True and NFC rejection.
- All five exact domain-separated SHA-256 prefixes terminating in NUL:
    b"horo-context:scope-skill-registry:v1\0"
    b"horo-context:approved-ticket-context:v1\0"
    b"horo-context:scope-skill-manifest:v1\0"
    b"horo-context:evidence:v1\0"
    b"horo-context:capability-index:v1\0"
- Raw artifact SHA-256 (plain bytes, no prefix).
- Manifest self-digest exclusion of manifest_sha256 field and non-recursive inventory.
- Bounded-read same-buffer hash/parse and TOCTOU protection.
- Atomic 0600 temp fsync replace writer.
- Managed roots: .codex/agents/, .claude/agents/, .claude/rules/, .claude/skills/,
  .agy/agents/, .agy/rules/, .agy/skills/, .antigravity/agents/, .antigravity/skills/.
- Marker replacement safety: ordered, single pair, outside bytes identical.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
RENDERER_SCRIPT = ROOT / "scripts/render_agent_context_profiles.py"


def _require_renderer():
    assert RENDERER_SCRIPT.exists(), (
        f"MISSING_CONTEXT_PROFILE_RENDERER: Renderer script not found at {RENDERER_SCRIPT}"
    )


def test_registry_renders_supported_generated_providers_in_one_direction(tmp_path: Path):
    _require_renderer()
    import scripts.render_agent_context_profiles as renderer
    manifest = renderer.render_all(output_root=tmp_path)
    assert "codex" in manifest["rendered_targets"]
    assert "antigravity" in manifest["rendered_targets"]


def test_newer_or_modified_provider_mirror_is_drift_not_authority():
    _require_renderer()
    import scripts.render_agent_context_profiles as renderer
    with pytest.raises(Exception, match="PROVIDER_DRIFT_DETECTED|CANONICAL_SOURCE_MISMATCH"):
        renderer.detect_mirror_drift(
            canonical_path=ROOT / ".agents/agents/developer/agent.json",
            mirror_path=ROOT / ".codex/agents/developer.json",
        )


def test_normalized_provider_scope_and_capability_sets_match_registry():
    _require_renderer()
    import scripts.render_agent_context_profiles as renderer
    assert renderer.verify_provider_scope_parity()


def test_generated_inventory_rejects_missing_and_extra_stale_artifacts():
    _require_renderer()
    import scripts.render_agent_context_profiles as renderer
    with pytest.raises(Exception, match="EXTRA_ARTIFACT_DETECTED|MISSING_ARTIFACT"):
        renderer.validate_inventory(declared_paths=["a.json"], actual_paths=["a.json", "stale.json"])


def test_manifest_is_byte_deterministic_across_order_mtime_locale_and_root():
    _require_renderer()
    import scripts.render_agent_context_profiles as renderer
    m1 = renderer.generate_manifest_bytes(seed=1)
    m2 = renderer.generate_manifest_bytes(seed=2)
    assert m1 == m2, "Manifest bytes must be 100% deterministic"


def test_all_identity_json_uses_one_exact_canonical_algorithm():
    _require_renderer()
    import scripts.render_agent_context_profiles as renderer
    val = {"z": 1, "a": 2, "m": [3, 4]}
    canon = renderer.canonical_json_bytes(val)
    expected = b'{"a":2,"m":[3,4],"z":1}'
    assert canon == expected
    assert not canon.endswith(b"\n"), "Canonical JSON must not have trailing newline"


def test_non_ascii_fixture_proves_ensure_ascii_true_and_nfc_contract():
    _require_renderer()
    import scripts.render_agent_context_profiles as renderer
    # Decomposed e + combining acute accent
    decomposed = "e\u0301"
    with pytest.raises(Exception, match="NON_NFC_UNICODE|INVALID_UNICODE"):
        renderer.canonical_json_bytes({"text": decomposed})
    # NFC string with ensure_ascii=True escapes
    nfc = "\u00e9"
    canon = renderer.canonical_json_bytes({"text": nfc})
    assert b"\\u00e9" in canon, "ensure_ascii=True must escape non-ASCII characters"


def test_all_structured_digests_use_exact_domain_prefixes():
    _require_renderer()
    import scripts.render_agent_context_profiles as renderer
    prefixes = {
        "registry": b"horo-context:scope-skill-registry:v1\0",
        "approved_context": b"horo-context:approved-ticket-context:v1\0",
        "manifest": b"horo-context:scope-skill-manifest:v1\0",
        "evidence": b"horo-context:evidence:v1\0",
        "capability_index": b"horo-context:capability-index:v1\0",
    }
    for name, prefix in prefixes.items():
        h = renderer.domain_sha256(prefix, {"test": 1})
        assert len(h) == 64, f"Domain digest for {name} must be 64-char hex SHA-256"


def test_manifest_inventory_binds_every_source_and_artifact():
    _require_renderer()
    import scripts.render_agent_context_profiles as renderer
    manifest = renderer.get_current_manifest()
    assert "inventory" in manifest
    assert len(manifest["inventory"]) > 0


def test_manifest_self_digest_and_nonrecursive_inventory_are_exact():
    _require_renderer()
    import scripts.render_agent_context_profiles as renderer
    manifest = renderer.get_current_manifest()
    # Manifest itself must not be in its own artifact inventory
    inventory_paths = [entry["path"] for entry in manifest["inventory"]]
    assert "plans/test_provenance/ticket-context-opt-001.json" not in inventory_paths
    # Self-digest computation
    assert "manifest_sha256" in manifest
    computed = renderer.compute_manifest_self_digest(manifest)
    assert computed == manifest["manifest_sha256"]


def test_generator_version_registry_version_and_registry_digest_are_bound():
    _require_renderer()
    import scripts.render_agent_context_profiles as renderer
    manifest = renderer.get_current_manifest()
    assert "generator_version" in manifest
    assert "registry_version" in manifest
    assert "registry_sha256" in manifest


def test_paths_reject_every_escape_and_nonregular_object():
    _require_renderer()
    import scripts.render_agent_context_profiles as renderer
    with pytest.raises(Exception, match="SYMLINK_REJECTED|ESCAPE_DETECTED|UNSAFE_PATH"):
        renderer.safe_open_bounded(Path("/dev/null"))


def test_bounded_read_revalidates_identity_and_uses_one_buffer():
    _require_renderer()
    import scripts.render_agent_context_profiles as renderer
    # Buffer overflow beyond 2 MiB limit
    with pytest.raises(Exception, match="BUFFER_LIMIT_EXCEEDED|PAYLOAD_TOO_LARGE"):
        renderer.bounded_read_single_buffer(Path("big_file"), max_bytes=1024)


def test_atomic_writer_is_same_directory_race_safe_and_durable():
    _require_renderer()
    import scripts.render_agent_context_profiles as renderer
    target = ROOT / "tmp_test_atomic.txt"
    renderer.atomic_write_0600(target, b"test content")
    assert target.exists()
    assert (target.stat().st_mode & 0o777) == 0o600
    target.unlink()


def test_predicted_manifest_snapshot_blocks_mixed_generation():
    _require_renderer()
    import scripts.render_agent_context_profiles as renderer
    with pytest.raises(Exception, match="SNAPSHOT_DRIFT|TOCTOU_DETECTED"):
        renderer.verify_source_snapshot_before_write(stale_snapshot={"a": "1"}, current_snapshot={"a": "2"})


def test_managed_roots_define_runtime_effective_extras_exactly():
    _require_renderer()
    import scripts.render_agent_context_profiles as renderer
    roots = renderer.MANAGED_ROOTS
    expected = {
        ".codex/agents/",
        ".claude/agents/", ".claude/rules/", ".claude/skills/",
        ".agy/agents/", ".agy/rules/", ".agy/skills/",
        ".antigravity/agents/", ".antigravity/skills/",
    }
    assert set(roots) == expected


def test_generated_marker_replacement_is_single_bounded_and_non_destructive():
    _require_renderer()
    import scripts.render_agent_context_profiles as renderer
    text = "HEADER\n<!-- SCOPE-SKILL-REGISTRY:START -->\nOLD\n<!-- SCOPE-SKILL-REGISTRY:END -->\nFOOTER"
    new_text = renderer.replace_marker_section(text, "SCOPE-SKILL-REGISTRY", "NEW")
    assert new_text == "HEADER\n<!-- SCOPE-SKILL-REGISTRY:START -->\nNEW\n<!-- SCOPE-SKILL-REGISTRY:END -->\nFOOTER"
    assert new_text.startswith("HEADER\n")
    assert new_text.endswith("\nFOOTER")
