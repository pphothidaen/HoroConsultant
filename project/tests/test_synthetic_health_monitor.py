from __future__ import annotations

from pathlib import Path

from scripts import synthetic_health_monitor as monitor


def test_build_health_targets_requires_public_backend_for_production() -> None:
    targets = monitor.build_health_targets(
        {"VERCEL_GATEWAY_URL": "https://vercel.example", "HF_STATIC_CDN_URL": "https://hf.example", "HF_BACKEND_URL": ""},
        require_backend=False,
    )
    assert len(targets) == 1

    try:
        monitor.build_health_targets(
            {"VERCEL_GATEWAY_URL": "https://vercel.example", "HF_STATIC_CDN_URL": "https://hf.example", "HF_BACKEND_URL": ""},
            require_backend=True,
        )
    except ValueError as error:
        assert "HF_BACKEND_URL" in str(error)
    else:
        raise AssertionError("production monitoring must require the public backend")


def test_target_response_validation_rejects_placeholder_200() -> None:
    assert monitor._target_response_is_valid("Vercel Gateway /health", '{"status":"ok"}')
    assert not monitor._target_response_is_valid("Vercel Gateway /health", '{"status":"error"}')
    assert monitor._target_response_is_valid("Hugging Face Static UI /index.html", "<!doctype html><html></html>")
    assert not monitor._target_response_is_valid("Hugging Face Static UI /index.html", '{"status":"ok"}')


def test_run_ping_cycle_fails_on_invalid_200_payload(monkeypatch, tmp_path: Path) -> None:
    targets = [{"name": "Vercel Gateway /health", "url": "https://example/health", "critical": True}]
    monkeypatch.setattr(
        monitor,
        "_ping",
        lambda url, timeout=10: (200, 1.0, '{"status":"error"}', None),
    )
    assert not monitor.run_ping_cycle(targets, report_path=tmp_path / "health.json", environment={})


def test_run_ping_cycle_uses_static_url_fallback(monkeypatch, tmp_path: Path) -> None:
    targets = monitor.build_health_targets(
        {
            "HF_STATIC_CDN_URL": "https://static.example",
            "HF_BACKEND_URL": "https://api.example",
        }
    )

    def fake_ping(url: str, timeout: int = 10):
        if url.endswith("/index.html"):
            return 200, 1.0, "<!doctype html><html></html>", None
        if "static.example" in url:
            return 404, 1.0, "not found", "HTTP 404: Not Found"
        return 200, 1.0, '{"status":"ok"}', None

    monkeypatch.setattr(monitor, "_ping", fake_ping)

    assert monitor.run_ping_cycle(targets, report_path=tmp_path / "health.json", environment={})
    assert targets[0]["url"] == "https://static.example/index.html"
