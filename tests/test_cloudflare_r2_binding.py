import pytest
from pathlib import Path

WRANGLER_PATH = Path(__file__).parent.parent / "wrangler.toml"


def read_wrangler():
    """Read wrangler.toml content."""
    return WRANGLER_PATH.read_text()


class TestR2BucketBinding:
    """R2 must stay out of wrangler.toml until R2 is enabled on the account.

    The Cloudflare account has R2 disabled, so any [[r2_buckets]] entry fails
    `wrangler deploy` with API error 10042. api/index.js (the deployed entry)
    never references env.ARTIFACTS; project/static/_worker.js guards with
    `if (env.ARTIFACTS)` and degrades gracefully. Re-adding the binding
    without enabling R2 first re-breaks every Workers deploy (PR #135/#136
    regression class).
    """

    def test_wrangler_file_exists(self):
        """wrangler.toml must exist."""
        assert WRANGLER_PATH.exists(), f"wrangler.toml not found at {WRANGLER_PATH}"

    def test_r2_buckets_binding_absent(self):
        """wrangler.toml must NOT have [[r2_buckets]] while R2 is disabled."""
        content = read_wrangler()
        assert "[[r2_buckets]]" not in content, \
            "[[r2_buckets]] present but R2 is not enabled on the account (error 10042)"

    def test_artifacts_binding_absent(self):
        """No ARTIFACTS binding may linger in wrangler.toml."""
        content = read_wrangler()
        assert 'binding = "ARTIFACTS"' not in content, \
            "ARTIFACTS binding present but no R2 bucket backs it"


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

