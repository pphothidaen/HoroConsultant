from __future__ import annotations

from pathlib import Path

import pytest

from scripts import synthetic_health_monitor as monitor


def test_build_health_targets_requires_public_backend_for_production() -> None:
    targets = monitor.build_health_targets(
        {"VERCEL_STATIC_URL": "https://vercel.example", "HF_BACKEND_URL": ""},
        require_backend=False,
    )
    assert len(targets) == 4
    assert all(target["name"].startswith("Vercel static") for target in targets)

    with pytest.raises(ValueError, match="HF_BACKEND_URL"):
        monitor.build_health_targets(
            {"VERCEL_STATIC_URL": "https://vercel.example", "HF_BACKEND_URL": ""},
            require_backend=True,
        )


def test_targets_use_vercel_assets_and_exact_hf_docker_health_only() -> None:
    targets = monitor.build_health_targets(
        {
            "VERCEL_STATIC_URL": "https://ui.example",
            "HF_STATIC_CDN_URL": "https://stale.static.example",
            "HF_BACKEND_URL": "https://api.example",
        }
    )

    assert targets[0]["urls"] == ["https://ui.example/", "https://ui.example/index.html"]
    assert [target["url"] for target in targets[1:4]] == [
        "https://ui.example/version.json",
        "https://ui.example/app.js",
        "https://ui.example/sw.js",
    ]
    assert targets[4]["url"] == "https://api.example/health"
    assert "urls" not in targets[4]


@pytest.mark.parametrize(
    "environment, message",
    [
        (
            {
                "HF_BACKEND_SPACE_ID": "pphothidaen/horoconsultant-core-backend",
                "HF_STATIC_SPACE_ID": "pphothidaen/horoconsultant-core-backend",
                "VERCEL_STATIC_URL": "https://ui.example",
                "HF_BACKEND_URL": "https://backend.example",
            },
            "must not equal",
        ),
        (
            {
                "VERCEL_STATIC_URL": "https://same.example",
                "HF_BACKEND_URL": "https://same.example",
            },
            "must not equal",
        ),
    ],
)
def test_monitor_rejects_static_backend_collision_fail_closed(
    environment: dict[str, str], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        monitor.build_health_targets(environment)


def test_target_response_validation_rejects_placeholder_200() -> None:
    assert monitor._target_response_is_valid("Hugging Face Docker Backend /health", '{"status":"ok"}')
    assert not monitor._target_response_is_valid("Hugging Face Docker Backend /health", '{"status":"error"}')
    assert monitor._target_response_is_valid("Vercel static UI", "<!doctype html><html></html>")
    assert monitor._target_response_is_valid(
        "Vercel static version metadata", '{"version":"1.0.0", "release_source_commit":"abc1234"}'
    )
    assert not monitor._target_response_is_valid("Vercel static version metadata", '{"version":"1.0.0"}')
    assert monitor._target_response_is_valid("Vercel static app.js asset", "const app = true;")
    assert not monitor._target_response_is_valid("Vercel static app.js asset", "<!doctype html><html></html>")


def test_run_ping_cycle_fails_on_invalid_200_payload(monkeypatch, tmp_path: Path) -> None:
    targets = [{"name": "Hugging Face Docker Backend /health", "url": "https://example/health", "critical": True}]
    monkeypatch.setattr(
        monitor,
        "_ping",
        lambda url, timeout=10: (200, 1.0, '{"status":"error"}', None),
    )
    assert not monitor.run_ping_cycle(targets, report_path=tmp_path / "health.json", environment={})


def test_run_ping_cycle_uses_only_vercel_index_fallback(monkeypatch, tmp_path: Path) -> None:
    targets = monitor.build_health_targets(
        {
            "VERCEL_STATIC_URL": "https://ui.example",
            "HF_BACKEND_URL": "https://api.example",
        }
    )

    def fake_ping(url: str, timeout: int = 10):
        if url == "https://ui.example/index.html":
            return 200, 1.0, "<!doctype html><html></html>", None
        if url == "https://ui.example/":
            return 404, 1.0, "not found", "HTTP 404: Not Found"
        if url.endswith("/version.json"):
            return 200, 1.0, '{"version":"1.0.0", "release_source_commit":"abc1234"}', None
        if url.endswith(("/app.js", "/sw.js")):
            return 200, 1.0, "const app = true;", None
        if url == "https://api.example/health":
            return 200, 1.0, '{"status":"ok"}', None
        raise AssertionError(f"unexpected fallback target: {url}")

    monkeypatch.setattr(monitor, "_ping", fake_ping)

    assert monitor.run_ping_cycle(targets, report_path=tmp_path / "health.json", environment={})
    assert targets[0]["url"] == "https://ui.example/index.html"
