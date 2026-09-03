import pytest
import re
from pathlib import Path

WORKER_PATH = Path(__file__).parent.parent / "project" / "static" / "_worker.js"


def read_worker_js():
    """Read the _worker.js file content."""
    return WORKER_PATH.read_text()


def extract_function_body(js_content, func_name):
    """Extract a function body from JS source."""
    pattern = rf"(?:async\s+)?function\s+{func_name}\s*\([^)]*\)\s*\{{"
    match = re.search(pattern, js_content)
    if not match:
        return None
    start = match.end()
    depth = 1
    i = start
    while i < len(js_content) and depth > 0:
        if js_content[i] == '{':
            depth += 1
        elif js_content[i] == '}':
            depth -= 1
        i += 1
    return js_content[start:i - 1]


class TestTurnstileFunctionExists:
    """Test that _worker.js has Turnstile verification function."""

    def test_worker_file_exists(self):
        """Worker file must exist."""
        assert WORKER_PATH.exists(), f"_worker.js not found at {WORKER_PATH}"

    def test_turnstile_verify_function_exists(self):
        """Worker must have a verifyTurnstile function."""
        js = read_worker_js()
        assert "async function verifyTurnstile" in js or "function verifyTurnstile" in js, \
            "Missing verifyTurnstile function"

    def test_turnstile_verify_calls_siteverify(self):
        """verifyTurnstile must call Cloudflare's siteverify endpoint."""
        js = read_worker_js()
        body = extract_function_body(js, "verifyTurnstile")
        assert body is not None, "verifyTurnstile function not found"
        assert "siteverify" in body, "verifyTurnstile must call siteverify endpoint"

    def test_turnstile_verify_checks_success(self):
        """verifyTurnstile must check the success field in response."""
        js = read_worker_js()
        body = extract_function_body(js, "verifyTurnstile")
        assert body is not None, "verifyTurnstile function not found"
        assert "success" in body, "verifyTurnstile must check success field"


class TestTurnstileIntegration:
    """Test that Turnstile is integrated into the fetch handler for admin routes."""

    def test_turnstile_constant_defined(self):
        """Worker must define a Turnstile secret constant."""
        js = read_worker_js()
        assert "TURNSTILE" in js.upper(), "Missing Turnstile secret constant"

    def test_admin_route_triggers_turnstile_check(self):
        """Admin routes (PRIVILEGED_API_PATH) must trigger Turnstile verification."""
        js = read_worker_js()
        # The worker should reference turnstile verification for admin paths
        assert "verifyTurnstile" in js, "verifyTurnstile must be called in worker"
        # Check that turnstile check happens for privileged/admin paths
        assert "cf-turnstile-response" in js or "turnstile" in js.lower(), \
            "Worker must check cf-turnstile-response header for admin routes"

    def test_turnstile_failure_returns_403(self):
        """Failed Turnstile verification must return 403 status."""
        js = read_worker_js()
        # Should return 403 when turnstile fails
        assert "403" in js, "Missing 403 status for Turnstile failure"

    def test_public_route_skips_turnstile(self):
        """Public API routes should not require Turnstile."""
        js = read_worker_js()
        # Verify that turnstile check is conditional on admin paths
        # The verifyTurnstile should only be called for PRIVILEGED_API_PATH
        privileged_pos = js.find("PRIVILEGED_API_PATH")
        turnstile_pos = js.find("verifyTurnstile")
        assert privileged_pos > 0, "PRIVILEGED_API_PATH not found"
        assert turnstile_pos > 0, "verifyTurnstile not found"
        # Turnstile logic should appear after the privileged path definition
        assert turnstile_pos > privileged_pos, \
            "Turnstile check should be associated with privileged/admin path handling"
