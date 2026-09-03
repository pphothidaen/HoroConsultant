import pytest
import re
from pathlib import Path

WORKER_PATH = Path(__file__).parent.parent / "project" / "static" / "_worker.js"


def read_worker_js():
    """Read the _worker.js file content."""
    return WORKER_PATH.read_text()


def extract_function_body(js_content, func_name):
    """Extract a function body from JS source."""
    # Match: async function funcName(...) { ... }
    pattern = rf"(?:async\s+)?function\s+{func_name}\s*\([^)]*\)\s*\{{"
    match = re.search(pattern, js_content)
    if not match:
        return None
    # Find matching closing brace
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


class TestKVCacheFunctions:
    """Test that _worker.js has KV cache helper functions."""

    def test_worker_file_exists(self):
        """Worker file must exist."""
        assert WORKER_PATH.exists(), f"_worker.js not found at {WORKER_PATH}"

    def test_kvcache_get_function_exists(self):
        """Worker must have a kvCacheGet function."""
        js = read_worker_js()
        assert "async function kvCacheGet" in js or "function kvCacheGet" in js, \
            "Missing kvCacheGet function"

    def test_kvcache_set_function_exists(self):
        """Worker must have a kvCacheSet function."""
        js = read_worker_js()
        assert "async function kvCacheSet" in js or "function kvCacheSet" in js, \
            "Missing kvCacheSet function"

    def test_cache_key_function_exists(self):
        """Worker must have a cacheKey function."""
        js = read_worker_js()
        assert "function cacheKey" in js, "Missing cacheKey function"


class TestKVCacheImplementation:
    """Test the KV cache implementation details."""

    def test_kvcache_get_reads_from_env_cache(self):
        """kvCacheGet should read from env.CACHE."""
        js = read_worker_js()
        body = extract_function_body(js, "kvCacheGet")
        assert body is not None, "kvCacheGet function not found"
        assert "env.CACHE.get" in body, "kvCacheGet must use env.CACHE.get"

    def test_kvcache_set_writes_to_env_cache(self):
        """kvCacheSet should write to env.CACHE."""
        js = read_worker_js()
        body = extract_function_body(js, "kvCacheSet")
        assert body is not None, "kvCacheSet function not found"
        assert "env.CACHE.put" in body, "kvCacheSet must use env.CACHE.put"

    def test_kvcache_set_supports_ttl(self):
        """kvCacheSet should support TTL via expirationTtl."""
        js = read_worker_js()
        body = extract_function_body(js, "kvCacheSet")
        assert body is not None, "kvCacheSet function not found"
        assert "expirationTtl" in body, "kvCacheSet must support expirationTtl"

    def test_cache_key_includes_method_and_path(self):
        """cacheKey should include request method and path."""
        js = read_worker_js()
        body = extract_function_body(js, "cacheKey")
        assert body is not None, "cacheKey function not found"
        assert "method" in body.lower(), "cacheKey must include request method"
        assert "pathname" in body.lower() or "path" in body.lower(), "cacheKey must include path"


class TestKVCacheIntegration:
    """Test that KV cache is integrated into the fetch handler."""

    def test_fetch_handler_checks_cache_before_proxy(self):
        """Fetch handler should check KV cache before proxying."""
        js = read_worker_js()
        # Should have cache check before proxyToBackend call
        cache_pos = js.find("kvCacheGet")
        proxy_pos = js.find("proxyToBackend")
        assert cache_pos > 0, "kvCacheGet not found in worker"
        assert proxy_pos > 0, "proxyToBackend not found in worker"
        assert cache_pos < proxy_pos, "Cache check should come before proxy"

    def test_fetch_handler_returns_cached_response(self):
        """Fetch handler should return cached response on cache hit."""
        js = read_worker_js()
        assert "X-Cache" in js, "Missing X-Cache header for cache hit"
        assert "HIT" in js, "Missing HIT value for X-Cache header"

    def test_fetch_handler_writes_cache_after_proxy(self):
        """Fetch handler should write to cache after successful proxy."""
        js = read_worker_js()
        # Should have kvCacheSet after proxyToBackend
        cache_set_pos = js.find("kvCacheSet")
        proxy_pos = js.find("proxyToBackend")
        assert cache_set_pos > 0, "kvCacheSet not found in worker"
        assert cache_set_pos > proxy_pos, "Cache write should come after proxy"

    def test_cache_only_for_get_requests(self):
        """Cache should only be used for GET requests."""
        js = read_worker_js()
        assert "GET" in js, "Cache should check for GET method"
