"""
TDD RED tests for Sprint A — Documentation & Docstring Consistency (Tickets A3-A8)

A3 — README.md mermaid flowchart model names mismatch (missing qwen2.5-coder:7b)
A4 — HybridRouter docstring cloud rotation uses stale model names
A5 — README.md Gemini fallback description too simplified
A7 — HybridRouter docstring local model order (regression guard after A1 GREEN fix)
A8 — v3_engine_adapter.py does not invoke compute_merkle_hash in interpretation flow
"""

import os
import re
import textwrap
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
README_PATH = PROJECT_ROOT / "README.md"
API_ROUTER_PATH = PROJECT_ROOT / "project" / "api_router.py"
V3_ADAPTER_PATH = PROJECT_ROOT / "project" / "core" / "v3_engine_adapter.py"
ENV_EXAMPLE_PATH = PROJECT_ROOT / ".env.example"


# ---------------------------------------------------------------------------
# Fixtures: read once per session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def readme_text():
    return README_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def api_router_text():
    return API_ROUTER_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def v3_adapter_text():
    return V3_ADAPTER_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def env_example_keys():
    lines = ENV_EXAMPLE_PATH.read_text(encoding="utf-8").splitlines()
    keys = set()
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        keys.add(s.partition("=")[0].strip())
    return keys


# ---------------------------------------------------------------------------
# A3 — README.md Mermaid Flowchart: Missing qwen2.5-coder:7b
# ---------------------------------------------------------------------------

class TestREADMEFlowchartOllamaModels:
    """README.md line 165 flowchart node lists only qwen2.5:7b / llama3:8b."""

    def test_flowchart_mentions_all_three_ollama_models(self, readme_text):
        """The mermaid flowchart at line ~165 should list all three Ollama
        tiers (primary, secondary, tertiary) just like api_router.py does."""
        # Find the flowchart section that lists Ollama models
        match = re.search(
            r'Local Ollama Service.*?qwen2\.5:7b.*?llama3:8b',
            readme_text,
            re.DOTALL,
        )
        assert match, "Could not locate the Ollama flowchart node in README"

        flowchart_snippet = match.group(0)
        # The secondary model (qwen2.5-coder:7b) should be mentioned
        assert "qwen2.5-coder:7b" in flowchart_snippet, (
            f"README flowchart only lists qwen2.5:7b / llama3:8b but "
            f"omits qwen2.5-coder:7b. Snippet: {flowchart_snippet}"
        )

    def test_readme_line_187_ollama_description_includes_all_models(self, readme_text):
        """README C4 context diagram line 187 says 'qwen2.5:7b local inference'
        but should acknowledge the full tier stack."""
        match = re.search(
            r'(System_Ext\(ollama[^\n]*)',
            readme_text,
        )
        assert match, "Could not find the Ollama System_Ext line in README"

        ollama_line = match.group(1)
        assert "qwen2.5-coder:7b" in ollama_line or len(re.findall(r'qwen2\.5|llama3', ollama_line)) >= 3, (
            f"README line 187 only mentions qwen2.5:7b but should acknowledge "
            f"all three local model tiers. Line: {ollama_line}"
        )


# ---------------------------------------------------------------------------
# A4 — HybridRouter docstring cloud rotation uses stale model names
# ---------------------------------------------------------------------------

class TestHybridRouterCloudRotationDocstring:
    """api_router.py HybridRouter class docstring (line ~487) lists
    'gemini-3.5-flash-lite -> gemini-flash-latest -> gemini-3.6-flash'
    but DEFAULT_GEMINI_ROTATION and actual defaults have changed."""

    @pytest.fixture(scope="module")
    def default_gemini_rotation(self, api_router_text):
        """Extract the actual DEFAULT_GEMINI_ROTATION list."""
        m = re.search(
            r'DEFAULT_GEMINI_ROTATION\s*=\s*\[(.*?)\]',
            api_router_text,
            re.DOTALL,
        )
        assert m, "DEFAULT_GEMINI_ROTATION not found in api_router.py"
        models = re.findall(r'"([^"]+)"', m.group(1))
        return models

    @pytest.fixture(scope="module")
    def hybrid_router_docstring(self, api_router_text):
        """Extract the HybridRouter class docstring."""
        m = re.search(
            r'class HybridRouter:\s*"""(.*?)"""',
            api_router_text,
            re.DOTALL,
        )
        assert m, "HybridRouter class docstring not found"
        return m.group(1)

    @pytest.fixture(scope="module")
    def gemini_defaults(self, api_router_text):
        """Extract GEMINI_PRIMARY_MODEL, SECONDARY, TERTIARY defaults."""
        primary = re.search(
            r'GEMINI_PRIMARY_MODEL\s*=\s*os\.getenv\("PRIMARY_MODEL",\s*"([^"]+)"\)',
            api_router_text,
        )
        secondary = re.search(
            r'GEMINI_SECONDARY_MODEL\s*=\s*os\.getenv\("SECONDARY_MODEL",\s*"([^"]+)"\)',
            api_router_text,
        )
        tertiary = re.search(
            r'GEMINI_TERTIARY_MODEL\s*=\s*os\.getenv\("TERTIARY_MODEL",\s*"([^"]+)"\)',
            api_router_text,
        )
        return {
            "primary": primary.group(1) if primary else None,
            "secondary": secondary.group(1) if secondary else None,
            "tertiary": tertiary.group(1) if tertiary else None,
        }

    def test_docstring_lists_current_gemini_defaults(
        self, hybrid_router_docstring, gemini_defaults
    ):
        """The HybridRouter docstring should mention the current primary/secondary/tertiary
        Gemini defaults (gemini-2.5-flash, gemini-1.5-pro, gemini-2.0-flash),
        not the old ones (gemini-3.5-flash-lite -> gemini-flash-latest -> gemini-3.6-flash)."""
        for label, model in gemini_defaults.items():
            assert model in hybrid_router_docstring, (
                f"HybridRouter docstring does not mention current GEMINI_{label.upper()}_MODEL "
                f"default '{model}'. The docstring still references stale model names."
            )

    def test_docstring_does_not_list_stale_gemini_models(
        self, hybrid_router_docstring, default_gemini_rotation
    ):
        """The docstring should not list models that are no longer in
        DEFAULT_GEMINI_ROTATION or no longer the defaults."""
        stale_models = ["gemini-3.5-flash-lite", "gemini-flash-latest", "gemini-3.6-flash"]
        docstring_rotation_part = re.search(
            r'CLOUD.*?Gemini.*?\((.*?)\)',
            hybrid_router_docstring,
            re.DOTALL,
        )
        if docstring_rotation_part:
            docstring_text = docstring_rotation_part.group(1)
            for stale in stale_models:
                # The stale models ARE in DEFAULT_GEMINI_ROTATION, but they should
                # NOT be the only ones listed in the docstring — the docstring
                # should list ALL rotation models at minimum
                assert stale in docstring_text, (
                    f"Stale model '{stale}' found in docstring rotation but "
                    f"the docstring should list ALL DEFAULT_GEMINI_ROTATION models."
                )
                # The docstring should list ALL rotation models
                for rot_model in default_gemini_rotation:
                    assert rot_model in docstring_text, (
                        f"DEFAULT_GEMINI_ROTATION model '{rot_model}' not found in "
                        f"HybridRouter docstring. Docstring should list all rotation models."
                    )


# ---------------------------------------------------------------------------
# A5 — README.md Gemini fallback description too simplified
# ---------------------------------------------------------------------------

class TestReadmeGeminiFallbackDescription:
    """README.md line 166 says '(Gemini 2.0 Flash / Pro)' — too simplified."""

    def test_readme_mentions_full_gemini_rotation(self, readme_text, api_router_text):
        """README should document the full Gemini fallback rotation chain,
        not just 'Gemini 2.0 Flash / Pro'."""
        # Extract DEFAULT_GEMINI_ROTATION from code
        m = re.search(
            r'DEFAULT_GEMINI_ROTATION\s*=\s*\[(.*?)\]',
            api_router_text,
            re.DOTALL,
        )
        assert m
        rotation_models = re.findall(r'"([^"]+)"', m.group(1))

        # README should mention at least the key models in the rotation
        for model in rotation_models:
            assert model in readme_text, (
                f"README does not mention '{model}' in its Gemini fallback "
                f"description. The README fallback description is too simplified "
                f"and does not document the full rotation chain."
            )

    def test_readme_does_not_use_simplified_gemini_label(self, readme_text):
        """README should not use a vague '(Gemini 2.0 Flash / Pro)' label
        without listing the actual model rotation."""
        # Find the Gemini mermaid node
        match = re.search(
            r'Gemini API.*?Gemini.*?Fallback',
            readme_text,
            re.DOTALL,
        )
        assert match, "Could not find Gemini API mermaid node in README"

        gemini_snippet = match.group(0)
        # Should mention at least 3 distinct model names
        model_mentions = re.findall(
            r'gemini-[0-9]?\d*\.\d*(?:-flash)?(?:-lite)?(?:-[a-z]+)?\d*[a-z]?|gemma-[0-9]',
            gemini_snippet,
            re.IGNORECASE,
        )
        assert len(model_mentions) >= 3, (
            f"README Gemini description only mentions {model_mentions} — "
            f"should list the full rotation chain of at least 3 models."
        )


# ---------------------------------------------------------------------------
# A7 — HybridRouter docstring local model order consistency
# (Regression guard — this was already fixed by the GREEN phase for A1/A2)
# ---------------------------------------------------------------------------

class TestHybridRouterLocalModelOrder:
    """api_router.py HybridRouter docstring (lines 484-486) should match
    the module docstring (lines 8-10) for local model order."""

    @pytest.fixture(scope="class")
    def module_docstring_models(self, api_router_text):
        """Extract model names from the module-level docstring (line ~8-10)."""
        # Match the route order lines in the module docstring
        matches = re.findall(
            r'LOCAL_MODEL\s*\(([^)]+)\)',
            api_router_text,
        )
        if not matches:
            matches = re.findall(
                r'(?:PRIMARY|SECONDARY|TERTIARY)_LOCAL_MODEL.*?((?:qwen2\.5|llama3)[^\s]*)',
                api_router_text,
            )
        return matches

    @pytest.fixture(scope="class")
    def hybrid_router_local_models(self, api_router_text):
        """Extract model names from the HybridRouter class docstring (lines 484-486)."""
        m = re.search(
            r'LOCAL \d:.*?(.*?)(?:LOCAL|$)',
            api_router_text,
            re.DOTALL,
        )
        if not m:
            # Try a different pattern
            local_section = re.search(
                r'LOCAL 1:.*?\n.*?\n.*?\n',
                api_router_text,
            )
            if local_section:
                models = re.findall(
                    r'(qwen2\.5-coder:7b|qwen2\.5:7b|llama3:8b)',
                    local_section.group(0),
                )
                return models
        return []

    def test_code_defaults_match_docstring(self, api_router_text):
        """The actual os.getenv defaults in api_router.py should match
        the HybridRouter class docstring local model order."""
        # Extract actual code defaults
        primary = re.search(
            r'PRIMARY_LOCAL_MODEL\s*=\s*os\.getenv\("OLLAMA_PRIMARY_MODEL",\s*"([^"]+)"\)',
            api_router_text,
        )
        secondary = re.search(
            r'SECONDARY_LOCAL_MODEL\s*=\s*os\.getenv\("OLLAMA_SECONDARY_MODEL",\s*"([^"]+)"\)',
            api_router_text,
        )
        tertiary = re.search(
            r'TERTIARY_LOCAL_MODEL\s*=\s*os\.getenv\("OLLAMA_TERTIARY_MODEL",\s*"([^"]+)"\)',
            api_router_text,
        )

        assert primary and secondary and tertiary, "Could not find OLLAMA model defaults"

        code_defaults = [primary.group(1), secondary.group(1), tertiary.group(1)]
        expected = ["qwen2.5:7b", "qwen2.5-coder:7b", "llama3:8b"]

        assert code_defaults == expected, (
            f"OLLAMA_LOCAL_MODEL defaults are {code_defaults} but should be {expected}"
        )

    def test_class_docstring_matches_module_docstring(self, api_router_text):
        """The HybridRouter class docstring should list the same local model
        order as the module-level docstring."""
        # Module docstring: lines 8-10 — extract model names between parentheses
        module_matches = re.findall(
            r'(?:PRIMARY|SECONDARY|TERTIARY)_LOCAL_MODEL\s+\(([^)]+)\)',
            api_router_text,
        )
        assert len(module_matches) >= 3, (
            f"Module docstring should have 3 LOCAL_MODEL entries, found {module_matches}"
        )

        # Class docstring: lines 484-486 — extract model names
        class_matches = re.findall(
            r'LOCAL \d: (qwen2\.5-coder:7b|qwen2\.5:7b|llama3:8b)',
            api_router_text,
        )
        assert len(class_matches) >= 3, (
            f"Class docstring should list 3 LOCAL models, found {class_matches}"
        )

        # Both should mention the same three models
        module_models = set(m.split()[0] for m in module_matches)
        class_models = set(class_matches)
        assert module_models == class_models, (
            f"Module docstring local models {module_models} ≠ "
            f"class docstring {class_models}"
        )


# ---------------------------------------------------------------------------
# A8 — Merkle DAG not invoked in v3_engine_adapter.py
# ---------------------------------------------------------------------------

class TestMerkleDAGInvocation:
    """AUDIT finding: 'Merkle DAG not invoked in v3' — HIGH severity.

    v3_engine_adapter.py defines compute_merkle_hash() and
    check_graph_acyclicity() but they are NEVER called in the
    interpretation/emission flow. The _emit() function uses _calc_hash()
    (a simple SHA256) instead of the proper Merkle node hash.
    """

    def test_compute_merkle_hash_is_called_in_adapter(self, v3_adapter_text):
        """compute_merkle_hash should be called somewhere in
        v3_engine_adapter.py beyond its definition."""
        # Count call sites (excluding the function definition itself)
        # The function is defined as: def compute_merkle_hash(...)
        # We look for calls: compute_merkle_hash(...)
        def_pattern = re.compile(r'def\s+compute_merkle_hash\s*\(')
        call_pattern = re.compile(r'compute_merkle_hash\s*\(')

        def_matches = def_pattern.findall(v3_adapter_text)
        all_matches = call_pattern.findall(v3_adapter_text)

        # Calls = total occurrences minus definitions
        call_count = len(all_matches) - len(def_matches)
        assert call_count > 0, (
            f"compute_merkle_hash is defined but NEVER called in "
            f"v3_engine_adapter.py (0 call sites). The Merkle DAG from "
            f"rust_core/v3_merkle_dag.rs is not invoked in the v3 engine flow. "
            f"This is a HIGH severity audit finding."
        )

    def test_merkle_imports_rust_core(self, v3_adapter_text):
        """v3_engine_adapter.py should import rust_core for native Merkle DAG."""
        assert "import rust_core" in v3_adapter_text, (
            "v3_engine_adapter.py should import rust_core for native Merkle DAG "
            "operations (compute_merkle_node_hash_py, check_reachability_py)."
        )

    def test_emit_uses_merkle_hash_not_simple_hash(self, v3_adapter_text):
        """The _emit() function should use compute_merkle_hash for
        input_state_hash, not _calc_hash."""
        emit_match = re.search(
            r'def _emit\(.*?(?=\ndef )',
            v3_adapter_text,
            re.DOTALL,
        )
        assert emit_match, "_emit function not found in v3_engine_adapter.py"
        emit_body = emit_match.group(0)
        assert "compute_merkle_hash" in emit_body, (
            "_emit() function does not use compute_merkle_hash for "
            "provenance hashing. It uses _calc_hash() instead, bypassing "
            "the Merkle DAG. The input_state_hash should be computed "
            "via the Merkle DAG, not a simple SHA256."
        )
        assert "_calc_hash(" not in emit_body, (
            "_emit() should not call _calc_hash() directly — use compute_merkle_hash()"
        )
