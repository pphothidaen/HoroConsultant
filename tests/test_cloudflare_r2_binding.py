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


class TestR2ZeroCostGuardrail:
    """Test Cloudflare Worker zero-cost guardrail and Vercel fallback policy."""

    WORKER_PATH = Path(__file__).parent.parent / "project" / "static" / "_worker.js"

    def test_worker_file_exists(self):
        """_worker.js must exist."""
        assert self.WORKER_PATH.exists(), f"_worker.js not found at {self.WORKER_PATH}"

    def test_worker_has_zero_cost_policy_constants(self):
        """_worker.js must define R2 free tier policy limits."""
        content = self.WORKER_PATH.read_text()
        assert "R2_FREE_TIER_POLICY" in content
        assert "maxStorageBytes: 10 * 1024 * 1024 * 1024" in content
        assert "maxClassAOpsMonthly: 1000000" in content
        assert "maxClassBOpsMonthly: 10000000" in content

    def test_worker_has_cost_guardrail_headers(self):
        """_worker.js must emit cost guardrail headers."""
        content = self.WORKER_PATH.read_text()
        assert "'X-Cost-Guardrail': 'free-tier-enforced'" in content
        assert "'X-R2-Policy': 'zero-cost-capped'" in content

    def test_worker_has_vercel_fallback_origin(self):
        """_worker.js must have Vercel fallback redirect URL."""
        content = self.WORKER_PATH.read_text()
        assert "VERCEL_FALLBACK_ORIGIN = 'https://horo-consultant-psi.vercel.app'" in content
        assert "Response.redirect" in content

