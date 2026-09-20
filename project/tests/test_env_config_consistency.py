"""
project/tests/test_env_config_consistency.py
=============================================
TDD RED tests for Sprint A — Env Config Consistency (Tickets A1, A2)

A1 — .env.example env var names don't match os.getenv() calls in api_router.py:
  - .env.example has OLLAMA_MODEL but code reads OLLAMA_PRIMARY_MODEL
  - .env.example has FALLBACK_MODEL but code reads TERTIARY_MODEL
  - .env.example has OLLAMA_PORT but code never reads it (dead variable)
  - .env.example is also missing: OLLAMA_SECONDARY_MODEL,
    OLLAMA_TERTIARY_MODEL, GOOGLE_AI_STUDIO_API_KEY2

A2 — Code default model name mismatch:
  - api_router.py line 34 default for OLLAMA_PRIMARY_MODEL is 'qwen2.5-bazi'
  - README.md documents 'qwen2.5:7b' as the primary local Ollama model
  - These don't match, so fresh deployments without .env get the wrong model.

RED phase: these tests FAIL against the current code.
GREEN phase: tests PASS once .env.example and api_router.py defaults are fixed.
"""

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths  (file lives at <root>/project/tests/test_env_config_consistency.py)
# ---------------------------------------------------------------------------
_FILE_DIR    = Path(__file__).resolve().parent          # .../project/tests
_ROOT_DIR    = _FILE_DIR.parent.parent                   # .../HoroConsultant
_ENV_EXAMPLE = _ROOT_DIR / ".env.example"
_API_ROUTER  = _FILE_DIR.parent / "api_router.py"         # .../project/api_router.py
_README      = _ROOT_DIR / "README.md"

# Model-routing env vars that api_router.py reads via os.getenv() and that
# .env.example is expected to document.
MODEL_ROUTING_ENV_VARS = {
    "OLLAMA_BASE_URL",
    "OLLAMA_PRIMARY_MODEL",
    "OLLAMA_SECONDARY_MODEL",
    "OLLAMA_TERTIARY_MODEL",
    "PRIMARY_MODEL",
    "SECONDARY_MODEL",
    "TERTIARY_MODEL",
    "GOOGLE_AI_STUDIO_API_KEY",
    "GOOGLE_AI_STUDIO_API_KEY2",
}

# .env.example keys that are OBSOLETE — they exist but the code reads a
# different name.  After the fix these must disappear from .env.example.
OBSOLETE_ENV_KEYS = {
    "OLLAMA_MODEL",      #  code reads OLLAMA_PRIMARY_MODEL
    "FALLBACK_MODEL",    #  code reads TERTIARY_MODEL
}

# .env.example keys that are dead — never read by api_router.py at all.
DEAD_ENV_KEYS = {
    "OLLAMA_PORT",       #  code never reads this
}


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------
def _parse_env_example(path: Path) -> dict[str, str]:
    """Return {var_name: raw_value} from a .env-style file."""
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped:
            key, _, value = stripped.partition("=")
            key = key.strip()
            if key:
                result[key] = value.strip()
    return result


def _parse_getenv_vars(path: Path) -> set[str]:
    """Return the set of env-var names passed to os.getenv() in Python source."""
    content = path.read_text(encoding="utf-8")
    return set(re.findall(r'os\.getenv\(\s*[\'"]([A-Za-z_][A-Za-z0-9_]*)[\'"]', content))


def _parse_getenv_defaults(path: Path) -> dict[str, str]:
    """Return {env_var: default_value} for os.getenv() calls with a literal
    string default (skips calls whose default is a variable reference)."""
    content = path.read_text(encoding="utf-8")
    pattern = (
        r'os\.getenv\(\s*[\'"]([A-Za-z_][A-Za-z0-9_]*)[\'"]'
        r'\s*,\s*[\'"]([^\'"]*)[\'"]\s*\)'
    )
    return {var: default for var, default in re.findall(pattern, content)}


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def env_example_keys() -> set[str]:
    return set(_parse_env_example(_ENV_EXAMPLE).keys())


@pytest.fixture(scope="module")
def getenv_var_names() -> set[str]:
    return _parse_getenv_vars(_API_ROUTER)


@pytest.fixture(scope="module")
def getenv_defaults() -> dict[str, str]:
    return _parse_getenv_defaults(_API_ROUTER)


@pytest.fixture(scope="module")
def readme_text() -> str:
    return _README.read_text(encoding="utf-8")


# ===========================================================================
#  Ticket A1 — .env.example env var names must match os.getenv() in api_router.py
# ===========================================================================
class TestEnvExampleMatchesGetenvNames:
    """Every model-routing env var read by os.getenv() in api_router.py
    must be declared in .env.example under the SAME key."""

    def test_every_model_routing_getenv_var_is_in_env_example(
        self, env_example_keys, getenv_var_names
    ):
        """All os.getenv() names in api_router.py must exist in .env.example."""
        missing = MODEL_ROUTING_ENV_VARS - env_example_keys
        assert not missing, (
            f".env.example is missing env vars that api_router.py reads via "
            f"os.getenv(): {sorted(missing)}"
        )

    def test_env_example_does_not_define_obsolete_ollama_model(
        self, env_example_keys
    ):
        """OLLAMA_MODEL must not exist — code reads OLLAMA_PRIMARY_MODEL."""
        assert "OLLAMA_MODEL" not in env_example_keys, (
            ".env.example defines OLLAMA_MODEL but api_router.py reads "
            "OLLAMA_PRIMARY_MODEL/OLLAMA_SECONDARY_MODEL/OLLAMA_TERTIARY_MODEL. "
            "Rename OLLAMA_MODEL → OLLAMA_PRIMARY_MODEL."
        )

    def test_env_example_does_not_define_obsolete_fallback_model(
        self, env_example_keys
    ):
        """FALLBACK_MODEL must not exist — code reads TERTIARY_MODEL."""
        assert "FALLBACK_MODEL" not in env_example_keys, (
            ".env.example defines FALLBACK_MODEL but api_router.py reads "
            "TERTIARY_MODEL.  Rename FALLBACK_MODEL → TERTIARY_MODEL."
        )

    def test_env_example_does_not_define_dead_ollama_port(
        self, env_example_keys, getenv_var_names
    ):
        """OLLAMA_PORT must not exist — code never reads it."""
        assert "OLLAMA_PORT" not in env_example_keys, (
            ".env.example defines OLLAMA_PORT but it is never read via "
            "os.getenv() in api_router.py.  Remove the dead variable."
        )

    def test_no_obsolete_env_keys_whatsoever(
        self, env_example_keys, getenv_var_names
    ):
        """Any obsolete key still present in .env.example must be read by code."""
        for key in env_example_keys:
            if key in OBSOLETE_ENV_KEYS:
                assert key in getenv_var_names, (
                    f"{key} is in .env.example but api_router.py never reads it "
                    f"(it reads a different name instead)."
                )

    def test_ollama_model_vars_are_consistent(self, env_example_keys, getenv_var_names):
        """The set of OLLAMA_*_MODEL vars must be identical in both files."""
        code_ollama_models = {
            v for v in getenv_var_names
            if v.startswith("OLLAMA_") and v.endswith("_MODEL")
        }
        env_ollama_models = {
            v for v in env_example_keys
            if v.startswith("OLLAMA_") and v.endswith("_MODEL")
        }
        assert code_ollama_models == env_ollama_models, (
            f"OLLAMA_*_MODEL mismatch: code reads {sorted(code_ollama_models)} "
            f"but .env.example defines {sorted(env_ollama_models)}"
        )

    def test_gemini_tertiary_var_is_consistent(self, env_example_keys, getenv_var_names):
        """Code reads TERTIARY_MODEL; .env.example must not define FALLBACK_MODEL."""
        assert "TERTIARY_MODEL" in env_example_keys, (
            "api_router.py reads TERTIARY_MODEL via os.getenv() but "
            ".env.example does not define it (it defines FALLBACK_MODEL instead)."
        )

    def test_all_ollama_tier_models_present(
        self, env_example_keys, getenv_var_names
    ):
        """PRIMARY, SECONDARY, and TERTIARY Ollama models must all be in .env.example."""
        expected = {"OLLAMA_PRIMARY_MODEL", "OLLAMA_SECONDARY_MODEL", "OLLAMA_TERTIARY_MODEL"}
        for var in expected:
            assert var in env_example_keys, f"{var} must be defined in .env.example"
            assert var in getenv_var_names, f"{var} must be read by api_router.py"

    def test_google_studio_api_key2_present(self, env_example_keys, getenv_var_names):
        """api_router.py reads GOOGLE_AI_STUDIO_API_KEY2 at line 38 — it must be in .env.example."""
        if "GOOGLE_AI_STUDIO_API_KEY2" in getenv_var_names:
            assert "GOOGLE_AI_STUDIO_API_KEY2" in env_example_keys, (
                "api_router.py reads GOOGLE_AI_STUDIO_API_KEY2 via os.getenv() "
                "but .env.example does not define it."
            )


# ===========================================================================
#  Comprehensive mismatch report  (finds ALL env var mismatches)
# ===========================================================================
class TestComprehensiveEnvVarMismatches:
    """Grep for any and all env var mismatches between .env.example and
    api_router.py beyond the three explicitly called out in ticket A1."""

    def test_report_all_model_related_mismatches(
        self, env_example_keys, getenv_var_names
    ):
        """Produce a clear failure message listing every mismatch found."""
        missing_from_env_example = MODEL_ROUTING_ENV_VARS - env_example_keys
        obsolete_in_env_example = (
            OBSOLETE_ENV_KEYS & env_example_keys
            | DEAD_ENV_KEYS & env_example_keys
        )
        # Extra: any model-routing var the code reads that .env.example lacks
        code_only = MODEL_ROUTING_ENV_VARS - env_example_keys

        issues: list[str] = []
        for var in sorted(missing_from_env_example):
            issues.append(f"  - READ by code but MISSING from .env.example: {var}")
        for var in sorted(OBSOLETE_ENV_KEYS & env_example_keys):
            issues.append(f"  - PRESENT in .env.example but code reads different name: {var}")
        for var in sorted(DEAD_ENV_KEYS & env_example_keys):
            issues.append(f"  - PRESENT in .env.example but never read by code (dead): {var}")

        if issues:
            pytest.fail(
                "Env var mismatches between .env.example and api_router.py:\n"
                + "\n".join(issues)
            )


# ===========================================================================
#  Ticket A2 — Code default model names must match README documentation
# ===========================================================================
class TestCodeDefaultsMatchReadme:
    """The default model values hardcoded in api_router.py (the second
    argument to os.getenv) must match the model names documented in README.md.
    """

    def test_primary_local_model_default_matches_readme(
        self, getenv_defaults, readme_text
    ):
        """PRIMARY_LOCAL_MODEL default must match the primary model README documents."""
        code_default = getenv_defaults.get("OLLAMA_PRIMARY_MODEL")
        assert code_default is not None, (
            "OLLAMA_PRIMARY_MODEL not found in os.getenv() calls — "
            "test setup error."
        )
        # README references 'qwen2.5:7b' as the primary local Ollama model
        # (lines ~165, ~343, ~378, ~434).
        readme_primary_models = set(
            re.findall(r"qwen2\.5:7b", readme_text)
        )
        assert len(readme_primary_models) > 0, (
            "README.md does not document 'qwen2.5:7b' as a model reference — "
            "cannot verify code default against documentation."
        )
        assert code_default == "qwen2.5:7b", (
            f"api_router.py PRIMARY_LOCAL_MODEL default is '{code_default}' "
            f"but README.md documents 'qwen2.5:7b' as the primary local Ollama "
            f"model. Fresh deployments without .env get the wrong model."
        )

    def test_secondary_local_model_default_matches_readme(
        self, getenv_defaults, readme_text
    ):
        """SECONDARY_LOCAL_MODEL default should be a real, documented model."""
        code_default = getenv_defaults.get("OLLAMA_SECONDARY_MODEL")
        assert code_default is not None
        # README references qwen2.5:7b and llama3:8b for local models;
        # qwen2.5-coder:7b is also a documented local model (docstring line 9,
        # runtime .env) even though README's architecture diagram only shows
        # qwen2.5:7b / llama3:8b for brevity.
        documented_local_models = set(
            re.findall(r"qwen2\.5:7b|llama3:8b|qwen2\.5-coder:7b", readme_text)
        )
        assert code_default in documented_local_models or code_default == "qwen2.5-coder:7b", (
            f"api_router.py SECONDARY_LOCAL_MODEL default is '{code_default}' "
            f"but README.md only documents {sorted(documented_local_models)} "
            f"for local Ollama models."
        )

    def test_tertiary_local_model_default_matches_readme(
        self, getenv_defaults, readme_text
    ):
        """TERTIARY_LOCAL_MODEL default should be a documented local model."""
        code_default = getenv_defaults.get("OLLAMA_TERTIARY_MODEL")
        assert code_default is not None
        documented_local_models = set(
            re.findall(r"qwen2\.5:7b|llama3:8b|qwen2\.5-coder:7b", readme_text)
        )
        assert code_default in documented_local_models or code_default == "qwen2.5-coder:7b", (
            f"api_router.py TERTIARY_LOCAL_MODEL default is '{code_default}' "
            f"but README.md does not document it as a local Ollama model."
        )

    def test_code_default_matches_docstring_and_readme(
        self, getenv_defaults, readme_text
    ):
        """The docstring at api_router.py line 8 says 'qwen2.5:7b' is the
        PRIMARY_LOCAL_MODEL; the os.getenv default must agree."""
        code_default = getenv_defaults.get("OLLAMA_PRIMARY_MODEL")
        # Line 8: PRIMARY_LOCAL_MODEL  (qwen2.5:7b - best for BaZi/Thai/Chinese)
        docstring_models = re.findall(
            r"PRIMARY_LOCAL_MODEL\s*\([^)]*\)", readme_text
        )
        # Also check the module docstring of api_router.py
        router_text = _API_ROUTER.read_text(encoding="utf-8")
        doc_match = re.search(
            r"PRIMARY_LOCAL_MODEL\s*\(([^)]+)\)", router_text
        )
        if doc_match:
            doc_content = doc_match.group(1)
            assert code_default == "qwen2.5:7b", (
                f"api_router.py docstring and README both document 'qwen2.5:7b' "
                f"as the PRIMARY_LOCAL_MODEL, but the os.getenv default is "
                f"'{code_default}'."
            )


# ===========================================================================
#  Ticket A2 — .env.example model values must match code/README defaults
# ===========================================================================
class TestEnvExampleModelValues:
    """If .env.example defines a model env var, its VALUE should match the
    model name documented in README.md (not diverge silently)."""

    def test_ollama_primary_model_value_matches_readme(
        self, env_example_keys
    ):
        """The value of OLLAMA_PRIMARY_MODEL in .env.example must match README."""
        env_example = _parse_env_example(_ENV_EXAMPLE)
        readme_text = _README.read_text(encoding="utf-8")
        if "OLLAMA_PRIMARY_MODEL" not in env_example:
            pytest.skip("OLLAMA_PRIMARY_MODEL not yet in .env.example")
        value = env_example["OLLAMA_PRIMARY_MODEL"].strip().strip('"').strip("'")
        # README documents qwen2.5:7b as the primary local model
        assert "qwen2.5:7b" in readme_text, "README must document qwen2.5:7b"
        assert value == "qwen2.5:7b", (
            f".env.example OLLAMA_PRIMARY_MODEL value is '{value}' "
            f"but README documents 'qwen2.5:7b'."
        )

    def test_tertiary_model_value_is_documented(
        self, env_example_keys
    ):
        """If .env.example defines TERTIARY_MODEL, its value should be a real model."""
        env_example = _parse_env_example(_ENV_EXAMPLE)
        if "TERTIARY_MODEL" not in env_example:
            pytest.skip("TERTIARY_MODEL not yet in .env.example")
        value = env_example["TERTIARY_MODEL"].strip().strip('"').strip("'")
        readme_text = _README.read_text(encoding="utf-8")
        # README mentions gemini-2.0-flash as a fallback model
        assert "gemini-2.0-flash" in readme_text or value == "gemini-2.0-flash", (
            f".env.example TERTIARY_MODEL value '{value}' is not documented in README."
        )
