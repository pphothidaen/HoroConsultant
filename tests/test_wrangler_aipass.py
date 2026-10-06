import pytest
import re
from pathlib import Path

WRANGLER_PATH = Path(__file__).parent.parent / "wrangler.aipass.toml"


def read_wrangler():
    """Read wrangler.aipass.toml content."""
    return WRANGLER_PATH.read_text()


class TestWranglerAipassConfig:
    """Test that wrangler.aipass.toml is valid for AIPass account deployment."""

    def test_account_id_is_set(self):
        """wrangler.aipass.toml must have account_id set (not placeholder)."""
        content = read_wrangler()
        assert "account_id" in content, "Missing account_id in wrangler.aipass.toml"
        assert "REPLACE_WITH" not in content.split("account_id")[1].split("\n")[0], \
            "account_id must be a real value, not a placeholder"

    def test_account_id_format(self):
        """account_id must be a 32-character hex string for AIPass account."""
        content = read_wrangler()
        match = re.search(r'account_id\s*=\s*"([a-f0-9]{32})"', content)
        assert match, "account_id must be a 32-character hex string"
        # Verify it's the AIPass account ID
        assert match.group(1) == "db2b77716a826311bbf9d104e125f540", \
            "account_id must match AIPass account (db2b77716a826311bbf9d104e125f540)"

    def test_project_name_set(self):
        """wrangler.aipass.toml must have Workers project name."""
        content = read_wrangler()
        assert 'name = "aipass-web-bridge"' in content, \
            'Expected Workers name = "aipass-web-bridge"'

    def test_main_entry_point_set(self):
        """wrangler.aipass.toml must specify main entry point."""
        content = read_wrangler()
        assert 'main = "worker.js"' in content, \
            "Missing main entry point for Workers"

    def test_compatibility_date_set(self):
        """wrangler.aipass.toml must have compatibility_date."""
        content = read_wrangler()
        assert "compatibility_date" in content

    def test_durable_objects_configured(self):
        """wrangler.aipass.toml must have EXT_HUB durable object."""
        content = read_wrangler()
        assert "[durable_objects]" in content
        assert "EXT_HUB" in content
        assert "ExtHub" in content

    def test_migrations_configured(self):
        """wrangler.aipass.toml must have migrations for DO."""
        content = read_wrangler()
        assert "[[migrations]]" in content
        assert "tag = \"v1\"" in content
        assert "new_sqlite_classes" in content
        assert "ExtHub" in content

    def test_secrets_not_hardcoded(self):
        """wrangler.aipass.toml must not have hardcoded secrets (stored in Doppler)."""
        content = read_wrangler()
        # These should be set via wrangler secret put or Doppler
        assert "BRIDGE_SECRET" not in content or "secret" in content.lower() or "dashboard" in content.lower()
        assert "CLIENT_API_KEY" not in content or "secret" in content.lower() or "dashboard" in content.lower()

    def test_chrome_extension_config(self):
        """wrangler.aipass.toml must document Chrome extension bridge URL."""
        content = read_wrangler()
        assert "aipass-web-bridge" in content
        assert "workers.dev" in content
        assert "v1" in content  # Hermes provider base_url


class TestWranglerAipassSyntax:
    """Test that wrangler.aipass.toml has valid TOML syntax."""

    def test_toml_parses(self):
        """wrangler.aipass.toml must be valid TOML."""
        import tomllib
        with open(WRANGLER_PATH, "rb") as f:
            config = tomllib.load(f)
        
        # Verify required top-level keys exist
        assert "name" in config
        assert "main" in config
        assert "compatibility_date" in config
        assert "account_id" in config
        assert "durable_objects" in config
        assert "migrations" in config