from __future__ import annotations

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


def test_hf_static_default_uses_docker_space_origin() -> None:
    assert verifier.DEFAULT_HF_STATIC_CDN_URL == (
        "https://pphothidaen-horoconsultant-core-backend.hf.space"
    )


def test_same_hf_space_uses_backend_origin_for_static_ui() -> None:
    checks = verifier.build_checks(
        {
            "HF_BACKEND_SPACE_ID": "pphothidaen/horoconsultant-core-backend",
            "HF_STATIC_SPACE_ID": "pphothidaen/horoconsultant-core-backend",
            "HF_BACKEND_URL": "https://backend.example",
            "HF_STATIC_CDN_URL": "https://stale.static.example",
        }
    )

    assert checks[0]["urls"][0] == "https://backend.example/"
