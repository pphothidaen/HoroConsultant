"""
TDD RED tests for Sprint B — MEDIUM severity documentation vs implementation mismatches (B1-B10).

B1 — D3.1: README fallback docs only mention Timeout/429; code falls back on all errors
B2 — D3.2: Cloudflare AI route missing from README diagrams
B3 — D3.3: Codex CLI route undocumented in README
B4 — D4.1: "Is LLM requested?" decision point missing from interpret_bazi
B5 — D4.2: Hardcoded fallback reading undocumented in README
B6 — D4.3: Hardcoded RAG references instead of FAISS search in debate.py
B7 — D4.4: v3 spec L1 Astro Kernel Engine abstraction mismatch
B8 — D4.6: 503 runtime-unavailable failure mode undocumented
B9 — D4.7: Discipline count inconsistency (10 vs 16 vs 11)
B10 — D4.10: HITL sequence diagram mismatch (GET vs upsert)
"""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
API_ROUTER = (PROJECT_ROOT / "project" / "api_router.py").read_text()
DEBATE_PY = (PROJECT_ROOT / "project" / "routers" / "debate.py").read_text()
README_TEXT = (PROJECT_ROOT / "README.md").read_text()
V3_SPEC = (PROJECT_ROOT / "docs" / "v3_api_specification.md").read_text()
V3_PY = (PROJECT_ROOT / "project" / "routers" / "v3.py").read_text()
V3_ADAPTER = (PROJECT_ROOT / "project" / "core" / "v3_engine_adapter.py").read_text()
CONFIG_PY = (PROJECT_ROOT / "project" / "core" / "config.py").read_text()
SVG_GEN = (PROJECT_ROOT / "project" / "core" / "svg_generator.py").read_text()


# ---------------------------------------------------------------------------
# B1 — D3.1: Fallback chain documentation accuracy
# ---------------------------------------------------------------------------

class TestReadmeFallbackChainDocumented:
    """README says fallback only on Timeout/429, but router falls back on ALL errors."""

    def test_readme_documents_all_fallback_error_types(self):
        """README flowchart should mention fallback on errors beyond Timeout/429."""
        # Line 347: `Ollama -- Timeout / 429 --> CloudFallback`
        # But api_router.py:572-637 falls back on connect_error, exception, 503, etc.
        fallback_text = re.search(
            r'.*CloudFallback.*',
            README_TEXT,
        )
        assert fallback_text, "CloudFallback line not found in README"
        fallback_desc = fallback_text.group(0)

        for error_type in ['connect_error', 'exception', '503']:
            assert error_type in fallback_desc, (
                f"README CloudFallback should mention {error_type} as a fallback trigger. "
                f"api_router.py:572-637 falls back on this error type but README "
                f"only mentions Timeout/429."
            )

        # README should mention more than just Timeout/429
        assert 'Timeout' in fallback_desc or '429' in fallback_desc, (
            "README should at least mention Timeout/429 fallback condition"
        )
        # This assertion FAILS because README only says Timeout/429, not all error types
        assert 'connect_error' in fallback_desc or 'exception' in fallback_desc or 'all errors' in fallback_desc.lower(), (
            f"README fallback description '{fallback_desc}' should mention fallback on "
            f"all error types (connect_error, exception, etc.), not just Timeout/429"
        )


# ---------------------------------------------------------------------------
# B2 — D3.2: Cloudflare AI route missing from README diagrams
# ---------------------------------------------------------------------------

class TestCloudflareAIRouteInDocs:
    """Cloudflare Workers AI route (api_router.py:518-524) is undocumented."""

    def test_readme_mentions_cloudflare_ai_route(self):
        """README should document Cloudflare Workers AI as a fallback route."""
        # api_router.py:518-524 adds Cloudflare AI route before Gemini in cloud mode
        assert 'cloudflare' in API_ROUTER.lower(), (
            "api_router.py should reference Cloudflare AI in route building"
        )

        # README should also mention Cloudflare AI in architecture diagrams
        readme_mentions = 'cloudflare' in README_TEXT.lower()
        assert readme_mentions, (
            "README should mention Cloudflare Workers AI route, but it doesn't. "
            "The route is in api_router.py:518-524 but absent from all diagrams."
        )

    def test_c4_diagram_includes_cloudflare(self):
        """C4 context diagram should include Cloudflare AI system."""
        c4_section = re.search(
            r'System_Ext\(.*?cloudflare',
            README_TEXT,
            re.IGNORECASE,
        )
        assert c4_section, (
            "C4 diagram should include a System_Ext for Cloudflare AI"
        )


# ---------------------------------------------------------------------------
# B3 — D3.3: Codex CLI route undocumented in README
# ---------------------------------------------------------------------------

class TestCodexCLIRouteInDocs:
    """Codex CLI route (api_router.py:510-511) is undocumented."""

    def test_readme_mentions_codex_cli_route(self):
        """README should document codex_cli as a cloud-mode route."""
        assert 'codex' in API_ROUTER.lower(), (
            "api_router.py should reference Codex CLI route"
        )
        # README has "Codex CLI" in C4 diagram but NOT "codex_cli" as route type
        assert 'codex_cli' in README_TEXT, (
            "README should mention 'codex_cli' as a cloud-mode route type. "
            "The C4 diagram mentions 'Codex CLI' system but the route type "
            "is not documented in the routing flowcharts."
        )


# ---------------------------------------------------------------------------
# B4 — D4.1: "Is LLM interpretation requested?" decision point missing
# ---------------------------------------------------------------------------

class TestLLMDecisionPointInDebate:
    """README line 342 shows CheckLLM{Is LLM Interpretation Requested?} but
    interpret_bazi always calls router.generate()."""

    def test_readme_shows_llm_conditional_branch(self):
        """README flowchart should show conditional LLM check."""
        assert 'Is LLM' in README_TEXT or 'LLM Interpretation Requested' in README_TEXT, (
            "README should show 'Is LLM Interpretation Requested?' decision point"
        )

    def test_interpret_bazi_has_conditional_llm_check(self):
        """interpret_bazi in debate.py should have a conditional branch on LLM usage."""
        # README says: CheckLLM{Is LLM Requested?} -> No: return chart JSON
        # But debate.py:252-263 always calls router.generate()
        generate_calls = len(re.findall(r'router\.generate\(', DEBATE_PY))
        assert generate_calls > 0, "interpret_bazi should call router.generate()"

        # Check if there's a conditional around router.generate()
        # Look for if/else patterns before router.generate()
        conditional_pattern = re.search(
            r'if.*llm|if.*interpretation|if.*generate|if.*fast_return|if.*chart_only',
            DEBATE_PY,
            re.IGNORECASE,
        )
        assert conditional_pattern, (
            "interpret_bazi should have a conditional branch (if statement) controlling "
            "whether to call the LLM. The README shows 'Is LLM Requested?' decision point "
            "but the code always calls router.generate() unconditionally."
        )


# ---------------------------------------------------------------------------
# B5 — D4.2: Hardcoded fallback reading undocumented
# ---------------------------------------------------------------------------

class TestFallbackReadingDocumented:
    """debate.py:262-263 has _generate_fallback_reading() but README doesn't mention it."""

    def test_readme_documents_fallback_reading(self):
        """README should document the fallback reading generation path."""
        # The README should mention fallback reading or hardcoded reading
        has_fallback_doc = (
            'fallback reading' in README_TEXT.lower()
            or 'fallback generation' in README_TEXT.lower()
            or '_generate_fallback' in README_TEXT
        )
        assert has_fallback_doc, (
            "README does not document the fallback reading generation. "
            "debate.py:262-263 calls _generate_fallback_reading() when LLM returns empty, "
            "but this path is absent from all documented flows."
        )

    def test_debate_has_fallback_reading_function(self):
        """debate.py should have a fallback reading function."""
        assert '_generate_fallback_reading' in DEBATE_PY, (
            "debate.py should have _generate_fallback_reading function"
        )


# ---------------------------------------------------------------------------
# B6 — D4.3: Hardcoded RAG references instead of FAISS search
# ---------------------------------------------------------------------------

class TestRAGReferencesAreNotHardcoded:
    """debate.py:274-279 returns hardcoded RAG references instead of FAISS search."""

    def test_readme_claims_faiss_rag_search(self):
        """README should claim FAISS vector search for RAG."""
        assert 'faiss' in README_TEXT.lower(), (
            "README should mention FAISS for RAG search"
        )

    def test_interpret_bazi_uses_faiss_not_hardcoded(self):
        """interpret_bazi should use FAISS search, not hardcoded references."""
        # Check for hardcoded rag_references list
        hardcoded_pattern = re.search(
            r'rag_references\s*=\s*\[.*?\]',
            DEBATE_PY,
            re.DOTALL,
        )
        assert hardcoded_pattern is None, (
            "interpret_bazi should NOT have hardcoded rag_references list. "
            "debate.py:274-279 has a hardcoded list of 4 classical texts, "
            "but README claims FAISS vector search (3,132 chunks)."
        )
        assert 'faiss' in DEBATE_PY.lower(), (
            "debate.py should use FAISS search for RAG references, "
            "but it uses hardcoded references instead."
        )


# ---------------------------------------------------------------------------
# B7 — D4.4: L1 Astro Kernel Engine abstraction mismatch
# ---------------------------------------------------------------------------

class TestAstroKernelAbstraction:
    """v3_api_specification.md:18 describes L1 Astro Kernel Engine, but TST
    is calculated inside BaZiEngine, not a separate layer."""

    def test_v3_spec_describes_l1_astro_kernel(self):
        """The v3 spec should describe an L1 layer that computes TST/ephemeris."""
        # L1 should compute true solar time — name may be 'Astro Kernel' or 'Astronomical'
        assert 'L1' in V3_SPEC, "Spec should describe L1 layer"
        assert (
            'Astro Kernel' in V3_SPEC
            or 'Astronomical' in V3_SPEC
            or 'true solar' in V3_SPEC.lower()
            or 'calculate_true_solar' in V3_SPEC
        ), "L1 should describe astronomical/TST calculation, not just routing"

    def test_v3_spec_matches_actual_tst_location(self):
        """The v3 spec's L1 description should match where TST is actually calculated."""
        # v3_api_specification.md:18 says L1 Astro Kernel Engine handles TST
        # v3.py:143 calls BaZiEngine().calculate() which internally calls solar_time.py
        # bazi_engine.py:763 calls calculate_true_solar_time
        has_bazengine_tst = 'BaZiEngine().calculate' in V3_PY
        has_solar_time_call = 'calculate_true_solar_time' in (PROJECT_ROOT / "project" / "core" / "bazi_engine.py").read_text()

        # The L1 section should not reference a separate gRPC/Proto3 service
        # that doesn't exist in the actual code. TST is computed in-process.
        spec_has_proto3_service = 'astro_kernel_service' in V3_SPEC
        has_separate_astro = 'astro_kernel_service' in V3_ADAPTER or 'astro_kernel' in V3_ADAPTER

        if spec_has_proto3_service and not has_separate_astro:
            pytest.fail(
                "v3 spec still references astro_kernel_service.proto as a separate "
                "gRPC service, but v3_engine_adapter.py has no such import. "
                "TST (True Solar Time) is calculated inside BaZiEngine, not a separate L1 layer."
            )


# ---------------------------------------------------------------------------
# B8 — D4.6: 503 runtime-unavailable failure mode undocumented
# ---------------------------------------------------------------------------

class TestV3SpecDocuments503:
    """v3_api_specification.md doesn't document 503, but v3.py:102-105 raises it."""

    def test_v3_spec_documents_503_error(self):
        """v3 API spec should document 503 error code."""
        assert '503' in V3_SPEC, (
            "v3_api_specification.md should document 503 (runtime unavailable) error code. "
            "v3.py:102-105 raises HTTPException(503, ...) but the spec only shows 400, 422, 500."
        )

    def test_v3_code_raises_503(self):
        """v3.py should raise 503 when runtime assets unavailable."""
        assert '503' in V3_PY and 'runtime' in V3_PY.lower() or 'unavailable' in V3_PY.lower(), (
            "v3.py should have 503 runtime unavailable error"
        )


# ---------------------------------------------------------------------------
# B9 — D4.7: Discipline count inconsistency
# ---------------------------------------------------------------------------

class TestDisciplineCountConsistency:
    """README mentions 16, 10, 11 disciplines inconsistently."""

    def test_readme_discipline_count_is_consistent(self):
        """All README references should use the same discipline count."""
        # Count actual disciplines in api_router.py DISCIPLINE_TOOL_MAP
        map_section = re.search(
            r'DISCIPLINE_TOOL_MAP.*?=\s*\{(.*?)\}',
            API_ROUTER,
            re.DOTALL,
        )
        assert map_section, "DISCIPLINE_TOOL_MAP not found in api_router.py"

        # Count entries in the map
        entries = re.findall(r'"([a-z_]+)"\s*:', map_section.group(1))
        actual_count = len(entries)

        # Check README for conflicting numbers
        has_16 = '16-Domain' in README_TEXT or '16 discip' in README_TEXT.lower() or '16 canonical' in README_TEXT.lower()
        has_10 = '10 canonical' in README_TEXT or '10 Metaphysical' in README_TEXT or '10 distinct' in README_TEXT
        has_11 = '11 Discipline' in README_TEXT or '11 discipline' in README_TEXT.lower()

        if has_16 and has_10:
            pytest.fail(
                f"README mentions both 16-Domain (intro) and 10 canonical disciplines "
                f"(architecture), but api_router.py has {actual_count} disciplines. "
                f"Count should be consistent across all documentation."
            )

    def test_svg_generator_has_16_renderers(self):
        """svg_generator.py should have 16 discipline-specific SVG renderers."""
        svg_funcs = re.findall(r'def generate_[a-z_]+_svg\(', SVG_GEN)
        assert len(svg_funcs) >= 16, (
            f"svg_generator.py should have at least 16 discipline SVG renderers, "
            f"found {len(svg_funcs)}: {svg_funcs}"
        )


# ---------------------------------------------------------------------------
# B10 — D4.10: HITL sequence diagram mismatch
# ---------------------------------------------------------------------------

class TestHITLDiagramMatchesImplementation:
    """README HITL diagram shows GET /hitl/item/{id} -> load item & heatmap,
    but debate.py uses upsert_external_hitl_item (upsert, not GET)."""

    def test_hitl_diagram_shows_correct_interface(self):
        """README HITL should show upsert interface, not GET."""
        # README line 397-398: HITL UI calls GET /hitl/item/{item_id} → DB: Load item
        has_get_in_diagram = 'GET /hitl/item' in README_TEXT
        assert not has_get_in_diagram, (
            "README HITL diagram shows 'GET /hitl/item/{item_id}' — this is wrong. "
            "The actual implementation uses upsert_external_hitl_item() (an upsert operation). "
            "The diagram should show the upsert interface, not a GET-based load."
        )

    def test_debate_uses_upsert_not_get(self):
        """debate.py should use upsert, not a GET-based load."""
        assert 'upsert_external_hitl_item' in DEBATE_PY, (
            "debate.py should use upsert_external_hitl_item for HITL integration"
        )
        assert 'confidence_heatmap' not in DEBATE_PY.lower(), (
            "debate.py should not reference 'confidence_heatmap' — the HITL item "
            "data structure includes source_domain, source_id, confidence_score, "
            "conflict_detected, consensus_matrix, not a heatmap."
        )
