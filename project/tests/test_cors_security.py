"""Security regressions for the FastAPI-to-Vercel CORS boundary."""

from __future__ import annotations

from fastapi.testclient import TestClient

from project.core.cors import DEFAULT_CORS_ALLOWED_ORIGIN, get_allowed_origins
from project.main import app


DISALLOWED_ORIGIN = "https://untrusted.example"


def _preflight(origin: str):
    return TestClient(app).options(
        "/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type, authorization",
        },
    )


def test_default_cors_origin_is_the_canonical_vercel_frontend(monkeypatch):
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    assert get_allowed_origins() == [DEFAULT_CORS_ALLOWED_ORIGIN]


def test_cors_env_override_is_comma_delimited_and_rejects_wildcards(monkeypatch):
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        " https://preview.example , *, https://preview.example/ , invalid ",
    )
    assert get_allowed_origins() == ["https://preview.example"]


def test_allowed_preflight_returns_exact_origin_and_credential_safe_headers():
    response = _preflight(DEFAULT_CORS_ALLOWED_ORIGIN)

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == DEFAULT_CORS_ALLOWED_ORIGIN
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "content-type" in response.headers["access-control-allow-headers"].lower()
    assert "*" not in response.headers["access-control-allow-origin"]
    assert "Origin" in response.headers["vary"]


def test_disallowed_preflight_and_request_do_not_receive_acao():
    preflight = _preflight(DISALLOWED_ORIGIN)
    request = TestClient(app).get("/health", headers={"Origin": DISALLOWED_ORIGIN})

    assert preflight.status_code == 400
    assert "access-control-allow-origin" not in preflight.headers
    assert "Origin" in preflight.headers["vary"]
    assert request.status_code == 200
    assert "access-control-allow-origin" not in request.headers


def test_exception_response_never_reflects_an_untrusted_origin():
    async def raise_for_cors_regression():
        raise RuntimeError("CORS regression sentinel")

    app.add_api_route("/__cors_regression_raises", raise_for_cors_regression)
    try:
        client = TestClient(app, raise_server_exceptions=False)
        blocked = client.get("/__cors_regression_raises", headers={"Origin": DISALLOWED_ORIGIN})
        allowed = client.get(
            "/__cors_regression_raises",
            headers={"Origin": DEFAULT_CORS_ALLOWED_ORIGIN},
        )
    finally:
        app.router.routes.pop()

    assert blocked.status_code == 500
    assert "access-control-allow-origin" not in blocked.headers
    assert blocked.headers["vary"] == "Origin"
    assert allowed.status_code == 500
    assert allowed.headers["access-control-allow-origin"] == DEFAULT_CORS_ALLOWED_ORIGIN
