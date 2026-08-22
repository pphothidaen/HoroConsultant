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
