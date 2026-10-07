"""
KAN-268: Regression tests for Render-primary backend failover.

These tests verify that:
1. The Cloudflare Worker uses Render as the primary backend origin
2. The HF Space is kept only as a fallback
3. Failover logic exists and is correctly structured
4. The deny-list / isAllowedPath behavior is preserved
"""
import re
from pathlib import Path

WORKER_PATH = Path(__file__).parent.parent / "project" / "static" / "_worker.js"
WRANGLER_PATH = Path(__file__).parent.parent / "wrangler.toml"
WRANGLER_HERMES_PATH = Path(__file__).parent.parent / "wrangler.hermes.toml"

RENDER_ORIGIN = "https://horoconsultant-core-backend.onrender.com"
HF_ORIGIN = "https://pphothidaen-horoconsultant-core-backend.hf.space"


def read_worker():
    return WORKER_PATH.read_text()


def read_wrangler():
    return WRANGLER_PATH.read_text()


def read_wrangler_hermes():
    return WRANGLER_HERMES_PATH.read_text()


class TestBackendOriginConfiguration:
    """Test that the backend origin is correctly configured with Render as primary."""

    def test_render_origin_is_primary_default(self):
        """Render origin must be the default when env.BACKEND_BASE_URL is not set."""
        content = read_worker()
        assert RENDER_ORIGIN in content, "Render origin must be present in _worker.js"

        # Check that Render is the default fallback when env is not set.
        # Accept either an inlined Render origin or the named RENDER_BACKEND_URL const.
        default_pattern = re.search(
            r'env\??\.BACKEND_BASE_URL\s*\|\|\s*(?:[\'"]' + re.escape(RENDER_ORIGIN) + r'[\'"]|RENDER_BACKEND_URL)',
            content
        )
        assert default_pattern, \
            "Render must be the default when env.BACKEND_BASE_URL is not set"

    def test_hf_origin_is_fallback_only(self):
        """HF origin must only appear as a fallback, not as the primary."""
        content = read_worker()
        assert HF_ORIGIN in content, "HF origin must still be present as fallback"

        # The old pattern: const BACKEND_BASE_URL = 'https://pphothidaen-...'
        # must NOT exist
        old_pattern = f"const BACKEND_BASE_URL = '{HF_ORIGIN}'"
        assert old_pattern not in content, \
            "HF origin must not be the hardcoded primary BACKEND_BASE_URL"

        # HF should be in a fallback variable
        assert "HF_FALLBACK" in content or "fallback" in content.lower(), \
            "HF origin must be in a fallback variable"

    def test_wrangler_toml_uses_render_as_primary(self):
        """wrangler.toml must use Render origin as primary BACKEND_BASE_URL."""
        content = read_wrangler()
        assert RENDER_ORIGIN in content, "Render origin must be in wrangler.toml"

        match = re.search(r'BACKEND_BASE_URL\s*=\s*"([^"]+)"', content)
        assert match, "BACKEND_BASE_URL must be set in wrangler.toml"
        assert match.group(1) == RENDER_ORIGIN, \
            f"wrangler.toml BACKEND_BASE_URL must be Render origin, got {match.group(1)}"

    def test_wrangler_hermes_toml_uses_render_as_primary(self):
        """wrangler.hermes.toml must use Render origin as primary BACKEND_BASE_URL."""
        content = read_wrangler_hermes()
        assert RENDER_ORIGIN in content, "Render origin must be in wrangler.hermes.toml"

        match = re.search(r'BACKEND_BASE_URL\s*=\s*"([^"]+)"', content)
        assert match, "BACKEND_BASE_URL must be set in wrangler.hermes.toml"
        assert match.group(1) == RENDER_ORIGIN, \
            f"wrangler.hermes.toml BACKEND_BASE_URL must be Render origin, got {match.group(1)}"

    def test_hf_not_primary_in_either_toml(self):
        """HF origin must not be the primary BACKEND_BASE_URL in either toml."""
        for path, name in [(WRANGLER_PATH, "wrangler.toml"), (WRANGLER_HERMES_PATH, "wrangler.hermes.toml")]:
            content = path.read_text()
            match = re.search(r'BACKEND_BASE_URL\s*=\s*"([^"]+)"', content)
            assert match, f"BACKEND_BASE_URL must be set in {name}"
            assert match.group(1) != HF_ORIGIN, \
                f"HF origin must not be the primary BACKEND_BASE_URL in {name}"


class TestFailoverLogic:
    """Test that failover logic exists and is correctly structured."""

    def test_failover_function_exists(self):
        """Worker must have a function to get the fallback backend URL."""
        content = read_worker()
        assert "getFallbackBackendUrl" in content or "fallback" in content.lower(), \
            "Worker must have failover/fallback logic"

    def test_proxy_to_backend_accepts_env(self):
        """proxyToBackend must accept env parameter for dynamic backend URL."""
        content = read_worker()
        # The function signature must include env
        match = re.search(r'async function proxyToBackend\s*\(\s*request\s*,\s*path\s*,\s*env\s*\)', content)
        assert match, "proxyToBackend must accept (request, path, env) parameters"

    def test_failover_tries_primary_then_fallback(self):
        """Failover logic must try primary first, then fallback on failure."""
        content = read_worker()
        # Must have a pattern of trying primary, then fallback
        # Look for the structure: try primary, catch/check, try fallback
        assert "tryFetchOrigin" in content or "fetchFromOrigin" in content, \
            "Worker must have a helper to fetch from a specific origin"

        # The failover pattern: primary first, then fallback
        primary_pos = content.find("primaryBase")
        fallback_pos = content.find("fallbackBase")
        assert primary_pos > 0, "Worker must reference primaryBase"
        assert fallback_pos > 0, "Worker must reference fallbackBase"
        assert primary_pos < fallback_pos, \
            "Primary must be tried before fallback in the code flow"

    def test_response_marks_serving_origin(self):
        """Response must include x-backend-origin header to mark which origin served it."""
        content = read_worker()
        assert "x-backend-origin" in content, \
            "Worker must set x-backend-origin header"

        # Must set it to 'render' or 'hf'
        assert "'render'" in content or '"render"' in content, \
            "Worker must mark render origin in x-backend-origin"
        assert "'hf'" in content or '"hf"' in content, \
            "Worker must mark hf origin in x-backend-origin"

    def test_failover_on_5xx(self):
        """Failover must trigger on 5xx responses from primary."""
        content = read_worker()
        # Must check for 5xx status to trigger failover
        assert "500" in content or "5xx" in content.lower(), \
            "Worker must check for 5xx status to trigger failover"

    def test_failover_on_network_error(self):
        """Failover must trigger on network errors from primary."""
        content = read_worker()
        # Must catch errors from primary fetch
        # The tryFetchOrigin or similar must catch errors
        assert "catch" in content, "Worker must catch errors for failover"


class TestDenyListPreserved:
    """Test that the deny-list / isAllowedPath behavior is preserved."""

    def test_is_allowed_path_exists(self):
        """isAllowedPath function must exist and be unchanged."""
        content = read_worker()
        assert "function isAllowedPath" in content, "isAllowedPath function must exist"

    def test_privileged_api_path_preserved(self):
        """PRIVILEGED_API_PATH pattern must be preserved."""
        content = read_worker()
        assert "PRIVILEGED_API_PATH" in content, "PRIVILEGED_API_PATH must exist"
        # The regex escapes the slashes, so assert on the escaped form.
        assert r"\/admin\/" in content, "Admin path pattern must be preserved"

    def test_public_api_path_preserved(self):
        """PUBLIC_API_PATH pattern must be preserved."""
        content = read_worker()
        assert "PUBLIC_API_PATH" in content, "PUBLIC_API_PATH must exist"

    def test_artifact_path_preserved(self):
        """ARTIFACT_PATH pattern must be preserved."""
        content = read_worker()
        assert "ARTIFACT_PATH" in content, "ARTIFACT_PATH must exist"

    def test_admin_nope_still_denied(self):
        """/admin/nope must still be gated (Turnstile), never publicly readable."""
        content = read_worker()
        # It must not be in the public read allow-list.
        assert "/admin/nope" not in content, \
            "/admin/nope must not be explicitly allow-listed"
        # It must match PRIVILEGED_API_PATH so it goes through the Turnstile gate.
        m = re.search(r"const PRIVILEGED_API_PATH = /(.+?)/;", content)
        assert m, "PRIVILEGED_API_PATH regex must be present"
        privileged = re.compile(m.group(1))
        assert privileged.search("/admin/nope"), \
            "/admin/nope must match PRIVILEGED_API_PATH (Turnstile-gated)"
        # And the public API pattern must NOT match it.
        pm = re.search(r"const PUBLIC_API_PATH = /(.+?)/;", content)
        assert pm, "PUBLIC_API_PATH regex must be present"
        assert not re.compile(pm.group(1)).search("/admin/nope"), \
            "/admin/nope must not match the public API pattern"


class TestWorkerModuleStructure:
    """Test the overall structure of the worker module."""

    def test_no_hardcoded_hf_as_sole_backend(self):
        """_worker.js must not hardcode HF origin as the sole backend const."""
        content = read_worker()
        # The old pattern must be gone
        assert f"const BACKEND_BASE_URL = '{HF_ORIGIN}'" not in content, \
            "HF origin must not be the sole hardcoded backend"

        # There should be separate consts for Render and HF
        assert "RENDER_BACKEND_URL" in content, "Must have RENDER_BACKEND_URL const"
        assert "HF_FALLBACK_URL" in content, "Must have HF_FALLBACK_URL const"

    def test_get_primary_backend_url_function(self):
        """Worker must have getPrimaryBackendUrl function."""
        content = read_worker()
        assert "getPrimaryBackendUrl" in content, \
            "Worker must have getPrimaryBackendUrl function"

        # It should return env.BACKEND_BASE_URL or the Render default const.
        match = re.search(
            r'function getPrimaryBackendUrl\s*\([^)]*\)\s*\{[^}]*env\??\.BACKEND_BASE_URL\s*\|\|\s*(?:[\'"]' + re.escape(RENDER_ORIGIN) + r'[\'"]|RENDER_BACKEND_URL)',
            content,
            re.DOTALL
        )
        assert match, "getPrimaryBackendUrl must return env.BACKEND_BASE_URL or Render default"

    def test_handle_wake_uses_dynamic_backend(self):
        """handleWake must use the dynamic backend URL, not hardcoded."""
        content = read_worker()
        # handleWake should use getPrimaryBackendUrl(env) instead of BACKEND_BASE_URL
        assert "getPrimaryBackendUrl" in content, \
            "handleWake must use getPrimaryBackendUrl for dynamic backend URL"
        # The old pattern: `${BACKEND_BASE_URL}/health` should be gone
        assert "${BACKEND_BASE_URL}" not in content, \
            "Worker must not use hardcoded BACKEND_BASE_URL template literal"

    def test_scheduled_uses_dynamic_backend(self):
        """scheduled handler must use the dynamic backend URL."""
        content = read_worker()
        # The scheduled handler should use getPrimaryBackendUrl(env)
        # Check that BACKEND_BASE_URL is not used in scheduled
        scheduled_match = re.search(r'async scheduled\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        if scheduled_match:
            scheduled_body = scheduled_match.group(1)
            assert "BACKEND_BASE_URL" not in scheduled_body, \
                "scheduled handler must not use hardcoded BACKEND_BASE_URL"
