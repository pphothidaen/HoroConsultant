import pytest
import re
from pathlib import Path

WRANGLER_PATH = Path(__file__).parent.parent / "wrangler.gemini.toml"


def read_wrangler():
    """Read wrangler.gemini.toml content."""
    return WRANGLER_PATH.read_text()


class TestWranglerGeminiConfig:
    """Test that wrangler.gemini.toml is valid for Gemini account deployment."""

    def test_account_id_is_set(self):
        """wrangler.gemini.toml must have account_id set (not placeholder)."""
        content = read_wrangler()
        assert "account_id" in content, "Missing account_id in wrangler.gemini.toml"
        assert "REPLACE_WITH" not in content.split("account_id")[1].split("\n")[0], \
            "account_id must be a real value, not a placeholder"

    def test_account_id_format(self):
        """account_id must be a 32-character hex string for Gemini account."""
        content = read_wrangler()
        match = re.search(r'account_id\s*=\s*"([a-f0-9]{32})"', content)
        assert match, "account_id must be a 32-character hex string"
        # Verify it's the Gemini account ID
        assert match.group(1) == "d91b1a43a188b73be61833adee445111", \
            "account_id must match Gemini account (d91b1a43a188b73be61833adee445111)"

    def test_project_name_set(self):
        """wrangler.gemini.toml must have Workers project name 'prod'."""
        content = read_wrangler()
        assert 'name = "prod"' in content, \
            'Expected Workers name = "prod"'

    def test_main_entry_point_set(self):
        """wrangler.gemini.toml must specify main entry point."""
        content = read_wrangler()
        assert 'main = "src/index.js"' in content, \
            "Missing main entry point for Workers"

    def test_compatibility_date_set(self):
        """wrangler.gemini.toml must have compatibility_date and nodejs_compat."""
        content = read_wrangler()
        assert "compatibility_date" in content
        assert "compatibility_flags" in content
        assert "nodejs_compat" in content

    def test_workers_dev_enabled(self):
        """wrangler.gemini.toml must have workers_dev = true for *.workers.dev subdomain."""
        content = read_wrangler()
        assert "workers_dev = true" in content

    def test_durable_objects_configured(self):
        """wrangler.gemini.toml must have BRIDGE_DO durable object."""
        content = read_wrangler()
        assert "[durable_objects]" in content
        assert "BRIDGE_DO" in content
        assert "GeminiBridgeDO" in content

    def test_kv_namespaces_configured(self):
        """wrangler.gemini.toml must have KV namespace binding for ARTIFACT_KV."""
        content = read_wrangler()
        assert "[[kv_namespaces]]" in content
        assert 'binding = "ARTIFACT_KV"' in content
        assert "400bc54565de455689ece92f8351bcb9" in content

    def test_migrations_configured(self):
        """wrangler.gemini.toml must have migrations for DO."""
        content = read_wrangler()
        assert "[[migrations]]" in content
        assert "tag = \"v1\"" in content
        assert "new_sqlite_classes" in content
        assert "GeminiBridgeDO" in content

    def test_observability_disabled(self):
        """wrangler.gemini.toml has observability disabled (KAN-236)."""
        content = read_wrangler()
        assert "[observability]" in content
        assert "enabled = false" in content

    def test_environment_variables(self):
        """wrangler.gemini.toml must have required environment variables."""
        content = read_wrangler()
        assert "BRIDGE_VERBOSE" in content
        assert "CONTEXT_ROTATION_THRESHOLD" in content
        assert "MULTI_SESSION" in content

    def test_secrets_not_hardcoded(self):
        """wrangler.gemini.toml must not have hardcoded secrets."""
        content = read_wrangler()
        # These should be set via wrangler secret put
        assert "BRIDGE_AUTH_TOKEN" not in content or "secret" in content.lower()
        assert "CLIENT_API_KEY" not in content or "secret" in content.lower()


class TestWranglerGeminiSyntax:
    """Test that wrangler.gemini.toml has valid TOML syntax."""

    def test_toml_parses(self):
        """wrangler.gemini.toml must be valid TOML."""
        import tomllib
        with open(WRANGLER_PATH, "rb") as f:
            config = tomllib.load(f)
        
        # Verify required top-level keys exist
        assert "name" in config
        assert "main" in config
        assert "compatibility_date" in config
        assert "account_id" in config
        assert "workers_dev" in config
        assert "durable_objects" in config
        assert "kv_namespaces" in config
        assert "migrations" in config
        assert "observability" in config
        assert "vars" in config