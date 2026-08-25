from __future__ import annotations

import pytest

from scripts import run_live_health_verification as verifier


def test_backend_url_derives_from_space_id_when_url_is_unset() -> None:
    environment = {"HF_BACKEND_SPACE_ID": "pphothidaen/horoconsultant-core-backend"}

    assert verifier._backend_url_from_env(environment) == (
        "https://pphothidaen-horoconsultant-core-backend.hf.space"
    )


def test_explicit_backend_url_overrides_space_id() -> None:
    environment = {
        "HF_BACKEND_SPACE_ID": "pphothidaen/horoconsultant-core-backend",
        "HF_BACKEND_URL": "https://backend.example/",
    }

    assert verifier._backend_url_from_env(environment) == "https://backend.example"


def test_vercel_is_the_default_static_release_target() -> None:
    assert verifier.DEFAULT_VERCEL_STATIC_URL == "https://horo-consultant-psi.vercel.app"


def test_vercel_static_checks_ignore_legacy_hf_static_origin() -> None:
    checks = verifier.build_checks(
        {
            "VERCEL_STATIC_URL": "https://ui.example",
            "HF_STATIC_CDN_URL": "https://stale.static.example",
            "HF_BACKEND_URL": "https://backend.example",
        }
    )

    assert [check["name"] for check in checks] == [
        "Vercel static UI",
        "Vercel static version metadata",
        "Vercel static app.js asset",
        "Vercel static service worker asset",
        "Hugging Face Docker backend health",
        "Public backend deterministic API",
    ]
    assert checks[0]["urls"] == ["https://ui.example/", "https://ui.example/index.html"]
    assert checks[1]["url"] == "https://ui.example/version.json"
    assert checks[2]["url"] == "https://ui.example/app.js"
    assert checks[3]["url"] == "https://ui.example/sw.js"
    assert checks[4]["url"] == "https://backend.example/health"


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
def test_static_backend_collision_is_rejected_fail_closed(
    environment: dict[str, str], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        verifier.build_checks(environment)


def test_version_and_javascript_validators_reject_placeholder_responses() -> None:
    assert verifier._is_version_response('{"version":"1.2.3", "release_source_commit":"abc1234"}')
    assert not verifier._is_version_response('{"version":"1.2.3"}')
    assert verifier._is_javascript_response("const version = '1.2.3';")
    assert not verifier._is_javascript_response("<!doctype html><html>not found</html>")
