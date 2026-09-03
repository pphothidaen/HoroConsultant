import pytest
from pathlib import Path

WRANGLER_PATH = Path(__file__).parent.parent / "wrangler.toml"


def read_wrangler():
    """Read wrangler.toml content."""
    return WRANGLER_PATH.read_text()


class TestR2BucketBinding:
    """Test that wrangler.toml has R2 bucket binding for model artifacts."""

    def test_wrangler_file_exists(self):
        """wrangler.toml must exist."""
        assert WRANGLER_PATH.exists(), f"wrangler.toml not found at {WRANGLER_PATH}"

    def test_r2_buckets_binding_exists(self):
        """wrangler.toml must have [[r2_buckets]] binding."""
        content = read_wrangler()
        assert "[[r2_buckets]]" in content, "Missing [[r2_buckets]] binding in wrangler.toml"

    def test_r2_binding_has_artifacts_binding(self):
        """R2 bucket binding must use binding = 'ARTIFACTS'."""
        content = read_wrangler()
        assert 'binding = "ARTIFACTS"' in content, "Missing binding = 'ARTIFACTS' in r2_buckets"

    def test_r2_binding_has_bucket_name(self):
        """R2 bucket binding must have a bucket_name field."""
        content = read_wrangler()
        assert "bucket_name" in content, "Missing bucket_name field in r2_buckets binding"

    def test_r2_bucket_name_is_horoconsultant_artifacts(self):
        """R2 bucket must be named 'horoconsultant-artifacts'."""
        content = read_wrangler()
        assert "horoconsultant-artifacts" in content, \
            "R2 bucket must be named 'horoconsultant-artifacts'"
