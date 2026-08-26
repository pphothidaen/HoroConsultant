"""Release contract tests for the frozen HF gateway and browser mirror."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]
GATEWAY = ROOT / "api" / "gateway.js"
HEALTH = ROOT / "api" / "health.js"
STATIC_APP = ROOT / "project" / "static" / "app.js"
PUBLIC_APP = ROOT / "public" / "app.js"


def _function_source(source: str, name: str) -> str:
    async_marker = f"async function {name}("
    marker = async_marker if async_marker in source else f"function {name}("
    start = source.index(marker)
    end = source.index("\n}\n\n", start) + 2
    return source[start:end]


def _browser_probe(configured: object, endpoint: str, status: int = 200) -> dict[str, object]:
    """Evaluate the browser routing helpers in Node without network access."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is required for the static browser routing contract")

    source = STATIC_APP.read_text(encoding="utf-8")
    get_base_url = _function_source(source, "getApiBaseUrl")
    fetch_api = _function_source(source, "fetchApi")
    script = f"""
      const calls = [];
      globalThis.window = {{
        API_BASE_URL: {json.dumps(configured)},
        location: {{ origin: "https://ui.example" }},
      }};
      globalThis.beginApiRequest = () => {{}};
      globalThis.endApiRequest = () => {{}};
      globalThis.fetch = async (url, options) => {{
        calls.push({{ url, options }});
        return {{ ok: {str(status < 400).lower()}, status: {status} }};
      }};
      {get_base_url}
      {fetch_api}
      try {{
        const base = getApiBaseUrl();
        await fetchApi({json.dumps(endpoint)}, {{ showLoader: false }});
        process.stdout.write(JSON.stringify({{ base, calls }}));
      }} catch (error) {{
        process.stdout.write(JSON.stringify({{ error: String(error.message), calls }}));
      }}
    """
    completed = subprocess.run(
        [node, "--input-type=module", "--eval", script],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_gateway_and_health_have_one_hf_backend_route_without_azure_fallback() -> None:
    gateway = GATEWAY.read_text(encoding="utf-8")
    health = HEALTH.read_text(encoding="utf-8")

    assert "configuredBackendOrigin" in gateway
    assert 'parsed.protocol !== "https:"' in gateway
    assert 'parsed.hostname.endsWith(".hf.space")' in gateway
    assert "AZURE_API_ORIGIN" not in gateway
    assert "proxyToAzure" not in gateway
    assert "proxyToBackend" in health
    assert "proxyToAzure" not in health
    assert "Azure" not in health


def test_static_and_public_browser_assets_are_byte_identical_and_have_no_host_fallback() -> None:
    static = STATIC_APP.read_bytes()
    public = PUBLIC_APP.read_bytes()

    assert static == public
    rendered = static.decode("utf-8")
    assert "BACKEND_API_HOSTS" not in rendered
    assert "candidateBases" not in rendered
    assert "static.hf.space" not in rendered
    assert "azurecontainerapps" not in rendered.lower()
    assert "All API hosts failed" not in rendered
    assert "errJson.detail" not in rendered
    assert "const safeReason" in rendered


def test_browser_routes_only_same_origin_or_hf_and_never_retries_an_upstream_response() -> None:
    same_origin = _browser_probe("https://ui.example", "/api/v1/health")
    hf_backend = _browser_probe("https://canonical-backend.hf.space", "/api/v1/health", status=503)
    relative = _browser_probe(None, "/api/v1/health")

    assert same_origin["base"] == "https://ui.example"
    assert same_origin["calls"] == [
        {"url": "https://ui.example/api/v1/health", "options": {"signal": {}}}
    ]
    assert hf_backend["base"] == "https://canonical-backend.hf.space"
    assert [call["url"] for call in hf_backend["calls"]] == [
        "https://canonical-backend.hf.space/api/v1/health"
    ]
    assert relative["base"] == ""
    assert [call["url"] for call in relative["calls"]] == ["/api/v1/health"]


@pytest.mark.parametrize(
    "configured",
    [
        "http://ui.example",
        "https://outside.example",
        "https://ui.example/unexpected-path",
        "https://legacy.azurecontainerapps.io",
        "https://user:password@canonical-backend.hf.space",
    ],
)
def test_invalid_browser_target_fails_closed_with_path_free_public_error(configured: str) -> None:
    result = _browser_probe(configured, "/api/v1/health")

    assert result == {"error": "Invalid API endpoint configuration.", "calls": []}


@pytest.mark.parametrize("endpoint", ["https://outside.example/api", "//outside.example", "/api#fragment", "/api\\path"])
def test_invalid_browser_path_fails_before_fetch(endpoint: str) -> None:
    result = _browser_probe("https://canonical-backend.hf.space", endpoint)

    assert result == {"error": "Invalid API request path.", "calls": []}
