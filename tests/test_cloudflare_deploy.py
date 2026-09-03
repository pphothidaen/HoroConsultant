import pytest
import re
from pathlib import Path

WRANGLER_PATH = Path(__file__).parent.parent / "wrangler.toml"


def read_wrangler():
    """Read wrangler.toml content."""
    return WRANGLER_PATH.read_text()


class TestDeploymentReadiness:
    """Test that wrangler.toml is ready for deployment."""

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
        """wrangler.toml must have project name."""
        content = read_wrangler()
        assert 'name = "horoconsultant-pages"' in content

    def test_build_output_dir_set(self):
        """wrangler.toml must specify pages_build_output_dir."""
        content = read_wrangler()
        assert 'pages_build_output_dir = "project/static"' in content


class TestWranglerConfigIntegrity:
    """Test that wrangler.toml has all required sections."""

    def test_kv_namespaces_configured(self):
        """wrangler.toml must have KV namespace binding."""
        content = read_wrangler()
        assert "[[kv_namespaces]]" in content
        assert 'binding = "CACHE"' in content

    def test_r2_buckets_configured(self):
        """wrangler.toml must have R2 bucket binding."""
        content = read_wrangler()
        assert "[[r2_buckets]]" in content
        assert 'binding = "ARTIFACTS"' in content

    def test_triggers_configured(self):
        """wrangler.toml must have triggers section."""
        content = read_wrangler()
        assert "[triggers]" in content
        assert 'crons' in content

    def test_observability_configured(self):
        """wrangler.toml must have observability enabled."""
        content = read_wrangler()
        assert "[observability]" in content
