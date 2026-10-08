import pytest
import re
from pathlib import Path

WRANGLER_PATH = Path(__file__).parent.parent / "wrangler.hermes.toml"


def read_wrangler():
    """Read wrangler.hermes.toml content."""
    return WRANGLER_PATH.read_text()


class TestWranglerHermesConfig:
    """Test that wrangler.hermes.toml is valid for Hermes account deployment."""

    def test_account_id_is_set(self):
        """wrangler.hermes.toml must have account_id set (not placeholder)."""
        content = read_wrangler()
        assert "account_id" in content, "Missing account_id in wrangler.hermes.toml"
        assert "REPLACE_WITH" not in content.split("account_id")[1].split("\n")[0], \
            "account_id must be a real value, not a placeholder"

    def test_account_id_format(self):
        """account_id must be a 32-character hex string for Hermes account."""
        content = read_wrangler()
        match = re.search(r'account_id\s*=\s*"([a-f0-9]{32})"', content)
        assert match, "account_id must be a 32-character hex string"
        # Verify it's the Hermes account ID
        assert match.group(1) == "bda49e4e77e00609cb1ef68561b0d9eb", \
            "account_id must match Hermes account (bda49e4e77e00609cb1ef68561b0d9eb)"

    def test_project_name_set(self):
        """wrangler.hermes.toml must have Workers project name."""
        content = read_wrangler()
        assert 'name = "horoconsultant"' in content, \
            'Expected Workers name = "horoconsultant"'

    def test_main_entry_point_set(self):
        """wrangler.hermes.toml must specify main entry point.

        KAN-269: consolidated onto the file the live Worker actually runs.
        """
        content = read_wrangler()
        assert 'main = "project/static/_worker.js"' in content, \
            "main must point at the deployed Worker entry point"

    def test_compatibility_date_set(self):
        """wrangler.hermes.toml must have compatibility_date."""
        content = read_wrangler()
        assert "compatibility_date" in content
        assert "compatibility_flags" in content
        assert "nodejs_compat" in content

    def test_kv_namespaces_configured(self):
        """wrangler.hermes.toml must have KV namespace binding for CACHE."""
        content = read_wrangler()
        assert "[[kv_namespaces]]" in content
        assert 'binding = "CACHE"' in content
        assert "07d1f31739eb418b944bf8d66f17a452" in content

    def test_r2_buckets_absent(self):
        """No [[r2_buckets]] while R2 is disabled on the account."""
        content = read_wrangler()
        assert "[[r2_buckets]]" not in content
        assert 'binding = "ARTIFACTS"' not in content

    def test_no_dead_cron_triggers(self):
        """KAN-273: no cron may be registered without a valid target.

        Parsed, not grepped — this file carries a commented reference block for
        another worker (hermes-harness-hooks) that legitimately mentions crons.
        """
        import tomllib
        with open(WRANGLER_PATH, "rb") as handle:
            config = tomllib.load(handle)
        assert not (config.get("triggers") or {}).get("crons")

    def test_observability_configured(self):
        """wrangler.hermes.toml must have observability enabled."""
        content = read_wrangler()
        assert "[observability]" in content
        assert "enabled = true" in content

    def test_environment_variables(self):
        """wrangler.hermes.toml must have required environment variables."""
        content = read_wrangler()
        assert "BACKEND_BASE_URL" in content
        assert "BACKEND_TIMEOUT_MS" in content
        assert "CORS_ALLOWED_ORIGINS" in content
        assert "ENVIRONMENT" in content

    def test_env_specific_configs(self):
        """wrangler.hermes.toml must have preview and production env configs."""
        content = read_wrangler()
        assert "[env.preview]" in content
        assert "[env.production]" in content
        assert 'ENVIRONMENT = "preview"' in content
        assert 'ENVIRONMENT = "production"' in content


class TestWranglerHermesSyntax:
    """Test that wrangler.hermes.toml has valid TOML syntax."""

    def test_toml_parses(self):
        """wrangler.hermes.toml must be valid TOML."""
        import tomllib
        with open(WRANGLER_PATH, "rb") as f:
            config = tomllib.load(f)
        
        # Verify required top-level keys exist
        assert "name" in config
        assert "main" in config
        assert "compatibility_date" in config
        assert "account_id" in config
        assert "vars" in config
        assert "kv_namespaces" in config
        # KAN-273: `triggers` was removed — the Worker cron had no valid target.
        assert "observability" in config
        assert "env" in config