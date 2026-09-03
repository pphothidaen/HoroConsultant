import pytest
from pathlib import Path

WRANGLER_PATH = Path(__file__).parent.parent / "wrangler.toml"


def read_wrangler():
    """Read wrangler.toml content."""
    return WRANGLER_PATH.read_text()


class TestKVNamespaceBinding:
    """Test that wrangler.toml has KV namespace binding for cache."""

    def test_wrangler_file_exists(self):
        """wrangler.toml must exist."""
        assert WRANGLER_PATH.exists(), f"wrangler.toml not found at {WRANGLER_PATH}"

    def test_kv_namespaces_binding_exists(self):
        """wrangler.toml must have [[kv_namespaces]] binding."""
        content = read_wrangler()
        assert "[[kv_namespaces]]" in content, "Missing [[kv_namespaces]] binding in wrangler.toml"

    def test_kv_binding_has_cache_binding(self):
        """KV namespace binding must use binding = 'CACHE'."""
        content = read_wrangler()
        assert 'binding = "CACHE"' in content, "Missing binding = 'CACHE' in kv_namespaces"

    def test_kv_binding_has_id(self):
        """KV namespace binding must have an id field."""
        content = read_wrangler()
        # Find the kv_namespaces section
        assert "id =" in content, "Missing id field in kv_namespaces binding"
