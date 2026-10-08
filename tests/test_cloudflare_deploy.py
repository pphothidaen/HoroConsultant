import pytest
import re
from pathlib import Path

WRANGLER_PATH = Path(__file__).parent.parent / "wrangler.toml"


def read_wrangler():
    """Read wrangler.toml content."""
    return WRANGLER_PATH.read_text()


class TestDeploymentReadiness:
    """Test that wrangler.toml is ready for Workers deployment."""

    def test_account_id_is_set(self):
        """wrangler.toml must have account_id set (not placeholder)."""
        content = read_wrangler()
        assert "account_id" in content, "Missing account_id in wrangler.toml"
        assert "REPLACE_WITH" not in content.split("account_id")[1].split("\n")[0], \
            "account_id must be a real value, not a placeholder"

    def test_account_id_format(self):
        """account_id must be a 32-character hex string."""
        content = read_wrangler()
        match = re.search(r'account_id\s*=\s*"([a-f0-9]{32})"', content)
        assert match, "account_id must be a 32-character hex string"

    def test_project_name_set(self):
        """wrangler.toml must have Workers project name (not Pages)."""
        content = read_wrangler()
        assert 'name = "horoconsultant"' in content, \
            "Expected Workers name = \"horoconsultant\""

    def test_main_entry_point_set(self):
        """wrangler.toml must specify main entry point (not Pages output dir).

        KAN-269: consolidated onto the file the live Worker actually runs.
        api/index.js remains the Vercel gateway, served from its own channel.
        """
        content = read_wrangler()
        assert 'main = "project/static/_worker.js"' in content, \
            "main must point at the deployed Worker entry point"


class TestWranglerConfigIntegrity:
    """Test that wrangler.toml has all required sections for Workers."""

    def test_kv_namespaces_configured(self):
        """wrangler.toml must have KV namespace binding."""
        content = read_wrangler()
        assert "[[kv_namespaces]]" in content
        assert 'binding = "CACHE"' in content

    def test_r2_buckets_absent_until_r2_enabled(self):
        """No [[r2_buckets]] while R2 is disabled on the account (error 10042)."""
        content = read_wrangler()
        assert "[[r2_buckets]]" not in content
        assert 'binding = "ARTIFACTS"' not in content

    def test_no_dead_cron_triggers(self):
        """KAN-273: no cron may be registered without a valid target.

        The Worker's cron POSTed /api/v1/sync, which the backend does not serve.
        The backend schedules its own sync (project/main.py), so the Worker cron
        was a redundant duplicate that silently 404'd twice a day.
        Parsed, not grepped — these files carry commented reference blocks.
        """
        import tomllib
        with open(WRANGLER_PATH, "rb") as handle:
            config = tomllib.load(handle)
        assert not (config.get("triggers") or {}).get("crons")

    def test_observability_configured(self):
        """wrangler.toml must have observability enabled."""
        content = read_wrangler()
        assert "[observability]" in content
