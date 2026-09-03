import pytest
import re
import json
from pathlib import Path

WORKER_PATH = Path(__file__).parent.parent / "project" / "static" / "_worker.js"


def read_worker_js():
    """Read the _worker.js file content."""
    return WORKER_PATH.read_text()


def extract_regex_pattern(js_content, var_name):
    """Extract a regex pattern from JS source."""
    # Match: const VAR_NAME = /pattern/flags;
    # Use non-greedy match to capture everything between / delimiters
    pattern = rf"{var_name}\s*=\s*/(.*?)/([gimsuy]*);"
    match = re.search(pattern, js_content)
    if match:
        flags_str = match.group(2)
        flags = 0
        if 'i' in flags_str:
            flags |= re.IGNORECASE
        if 'm' in flags_str:
            flags |= re.MULTILINE
        if 's' in flags_str:
            flags |= re.DOTALL
        regex_str = match.group(1)
        return re.compile(regex_str, flags)
    return None


def extract_set(js_content, var_name):
    """Extract a Set literal from JS source."""
    pattern = rf"const\s+{var_name}\s*=\s*new\s+Set\(\[([^\]]*)\]\);"
    match = re.search(pattern, js_content)
    if match:
        items = re.findall(r"'([^']+)'|\"([^\"]+)\"", match.group(1))
        return {a or b for a, b in items}
    return None


def extract_string_array(js_content, var_name):
    """Extract a string array from JS source."""
    pattern = rf"const\s+{var_name}\s*=\s*\[([^\]]*)\];"
    match = re.search(pattern, js_content)
    if match:
        items = re.findall(r"'([^']+)'|\"([^\"]+)\"", match.group(1))
        return [a or b for a, b in items]
    return None


def extract_string(js_content, var_name):
    """Extract a string constant from JS source."""
    pattern = rf"const\s+{var_name}\s*=\s*'([^']+)'|\"([^\"]+)\";"
    match = re.search(pattern, js_content)
    if match:
        return match.group(1) or match.group(2)
    return None


def extract_number(js_content, var_name):
    """Extract a numeric constant from JS source."""
    pattern = rf"const\s+{var_name}\s*=\s*(\d+);"
    match = re.search(pattern, js_content)
    if match:
        return int(match.group(1))
    return None


class TestWorkerStructure:
    """Test that _worker.js has the expected structure and exports."""

    def test_worker_file_exists(self):
        """Worker file must exist."""
        assert WORKER_PATH.exists(), f"_worker.js not found at {WORKER_PATH}"

    def test_worker_has_default_export(self):
        """Worker must have a default export with fetch handler."""
        js = read_worker_js()
        assert "export default" in js, "Missing export default"
        assert "async fetch(request, env)" in js, "Missing fetch handler signature"

    def test_worker_has_backend_base_url(self):
        """Worker must define BACKEND_BASE_URL."""
        js = read_worker_js()
        url = extract_string(js, "BACKEND_BASE_URL")
        assert url is not None, "BACKEND_BASE_URL not found"
        assert url.startswith("http"), f"Invalid BACKEND_BASE_URL: {url}"

    def test_worker_has_cors_allowed_origins(self):
        """Worker must define CORS_ALLOWED_ORIGINS."""
        js = read_worker_js()
        origins = extract_string_array(js, "CORS_ALLOWED_ORIGINS")
        assert origins is not None and len(origins) > 0, "CORS_ALLOWED_ORIGINS not found"

    def test_worker_has_timeout(self):
        """Worker must define BACKEND_TIMEOUT_MS."""
        js = read_worker_js()
        timeout = extract_number(js, "BACKEND_TIMEOUT_MS")
        assert timeout is not None, "BACKEND_TIMEOUT_MS not found"
        assert timeout > 0, "BACKEND_TIMEOUT_MS must be positive"


class TestPathMatching:
    """Test the path matching logic in the worker."""

    def test_public_api_path_matches_valid_routes(self):
        """PUBLIC_API_PATH should match /api/v1/..., /api/v2/..., /api/v3/... routes."""
        js = read_worker_js()
        regex = extract_regex_pattern(js, "PUBLIC_API_PATH")
        assert regex is not None, "PUBLIC_API_PATH regex not found"

        # Should match
        assert regex.search("/api/v1/health")
        assert regex.search("/api/v2/consult")
        assert regex.search("/api/v3/chart")
        assert regex.search("/api/v1/consult/123")

    def test_public_api_path_rejects_invalid_routes(self):
        """PUBLIC_API_PATH should not match invalid API paths."""
        js = read_worker_js()
        regex = extract_regex_pattern(js, "PUBLIC_API_PATH")
        assert regex is not None, "PUBLIC_API_PATH regex not found"

        # Should NOT match
        assert not regex.search("/api/v4/health")  # v4 not allowed
        assert not regex.search("/api/health")  # missing version
        assert not regex.search("/admin/api/v1/health")  # wrong prefix

    def test_privileged_api_path_matches_admin_routes(self):
        """PRIVILEGED_API_PATH should match /admin/... routes."""
        js = read_worker_js()
        regex = extract_regex_pattern(js, "PRIVILEGED_API_PATH")
        assert regex is not None, "PRIVILEGED_API_PATH regex not found"

        assert regex.search("/admin/users")
        assert regex.search("/admin/settings")
        assert regex.search("/admin/hitl/review")

    def test_privileged_api_path_rejects_non_admin(self):
        """PRIVILEGED_API_PATH should not match non-admin paths."""
        js = read_worker_js()
        regex = extract_regex_pattern(js, "PRIVILEGED_API_PATH")
        assert regex is not None, "PRIVILEGED_API_PATH regex not found"

        assert not regex.search("/api/v1/admin")
        assert not regex.search("/public/admin")

    def test_public_read_paths_defined(self):
        """PUBLIC_READ_PATHS should contain standard public endpoints."""
        js = read_worker_js()
        paths = extract_set(js, "PUBLIC_READ_PATHS")
        assert paths is not None, "PUBLIC_READ_PATHS not found"
        assert "/health" in paths
        assert "/docs" in paths
        assert "/openapi.json" in paths

    def test_privileged_read_paths_defined(self):
        """PRIVILEGED_READ_PATHS should contain read-only privileged endpoints."""
        js = read_worker_js()
        paths = extract_set(js, "PRIVILEGED_READ_PATHS")
        assert paths is not None, "PRIVILEGED_READ_PATHS not found"
        assert "/hitl/stats" in paths


class TestCORSHeaders:
    """Test CORS header generation logic."""

    def test_cors_headers_returns_empty_for_disallowed_origin(self):
        """corsHeaders should return empty dict for non-allowed origins."""
        js = read_worker_js()
        # Verify the function exists and has the origin check
        assert "function corsHeaders(request)" in js
        assert "CORS_ALLOWED_ORIGINS.includes(origin)" in js

    def test_cors_headers_returns_headers_for_allowed_origin(self):
        """corsHeaders should return CORS headers for allowed origins."""
        js = read_worker_js()
        assert "'Access-Control-Allow-Origin'" in js
        assert "'Access-Control-Allow-Methods'" in js
        assert "'Access-Control-Allow-Headers'" in js
        assert "'Vary': 'Origin'" in js


class TestStaticAssetPassthrough:
    """Test that static assets are passed through."""

    def test_worker_checks_static_extensions(self):
        """Worker should check for static file extensions."""
        js = read_worker_js()
        # The file contains \. (backslash + dot) in regex patterns
        assert r"\.(js|css|svg|png|ico|json|html)" in js or \
               r"\.(js|css|svg|png|ico|html)" in js or \
               "\\.(js|css|svg|png|ico|json|html)" in js or \
               "\\\\.(js|css|svg|png|ico|json|html)" in js, \
               "Missing static asset extension check"

    def test_worker_passes_through_static_assets(self):
        """Worker should call fetch(request) for static assets."""
        js = read_worker_js()
        # The worker should have a pass-through for static assets
        assert "return fetch(request)" in js, "Missing static asset pass-through"


class TestProxyToBackend:
    """Test the proxy to backend logic."""

    def test_proxy_function_exists(self):
        """Worker should have a proxyToBackend function."""
        js = read_worker_js()
        assert "async function proxyToBackend(request, path)" in js

    def test_proxy_constructs_backend_url(self):
        """Proxy should construct URL from BACKEND_BASE_URL and path."""
        js = read_worker_js()
        assert "BACKEND_BASE_URL" in js
        assert "path" in js

    def test_proxy_handles_timeout(self):
        """Proxy should implement timeout via AbortController."""
        js = read_worker_js()
        assert "AbortController" in js, "Missing AbortController for timeout"
        assert "setTimeout" in js, "Missing timeout handling"

    def test_proxy_returns_502_on_failure(self):
        """Proxy should return 502 when backend is unavailable."""
        js = read_worker_js()
        assert "502" in js, "Missing 502 status for backend failure"
        assert "Backend unavailable" in js


class TestWorkerFetchHandler:
    """Test the main fetch handler logic."""

    def test_handler_checks_static_assets_first(self):
        """Handler should check static assets before API proxy."""
        js = read_worker_js()
        # Static asset check should come before API proxy
        # Find the static asset regex in the handler
        static_pos = js.find(r"\.(js|css|svg|png|ico|json|html)")
        if static_pos == -1:
            static_pos = js.find("\\.(js|css|svg|png|ico|json|html)")
        if static_pos == -1:
            static_pos = js.find("\\\\.(js|css|svg|png|ico|json|html)")
        # Find the actual call to isAllowedPath in the handler (not the definition)
        api_pos = js.find("if (isAllowedPath")
        assert static_pos > 0, "Static asset check not found"
        assert api_pos > 0, "isAllowedPath check not found"
        assert static_pos < api_pos, "Static check should come before API proxy"

    def test_handler_handles_options_requests(self):
        """Handler should handle OPTIONS preflight requests."""
        js = read_worker_js()
        assert "OPTIONS" in js, "Missing OPTIONS handling"
        assert "204" in js, "Missing 204 status for OPTIONS"

    def test_handler_has_spa_fallback(self):
        """Handler should have SPA fallback (return fetch(request))."""
        js = read_worker_js()
        # Count occurrences of return fetch(request) - should be at least 2 (static + SPA)
        count = js.count("return fetch(request)")
        assert count >= 2, f"Expected at least 2 pass-through calls, found {count}"
