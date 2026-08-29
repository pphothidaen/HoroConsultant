from __future__ import annotations

import hashlib
import json

import pytest

from scripts import run_live_health_verification as verifier


def _canonical_metadata(commit: str = "abc1234") -> dict[str, str]:
    revision = commit + "a" * (40 - len(commit))
    identity = {
        "release_source_commit": commit,
        "release_source_metadata_path": "project/static/version.json",
        "release_source_revision": revision,
        "version": f"1.0.0.{commit}",
    }
    canonical = json.dumps(
        identity,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "version": identity["version"],
        "release_source_commit": commit,
        "release_source_revision": revision,
        "release_source_metadata_path": identity["release_source_metadata_path"],
        "release_source_metadata_sha256": hashlib.sha256(canonical).hexdigest(),
    }


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


def test_vercel_static_checks_ignore_legacy_hf_static_origin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = _canonical_metadata()
    monkeypatch.setattr(
        verifier,
        "load_approved_candidate_identity",
        lambda: candidate,
    )
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
        "Hugging Face Docker backend version metadata",
        "Public backend deterministic API",
    ]
    assert checks[0]["urls"] == ["https://ui.example/", "https://ui.example/index.html"]
    assert checks[1]["url"] == "https://ui.example/version.json"
    assert checks[2]["url"] == "https://ui.example/app.js"
    assert checks[3]["url"] == "https://ui.example/sw.js"
    assert checks[4]["url"] == "https://backend.example/health"
    assert checks[5]["url"] == "https://backend.example/version.json"
    assert checks[1]["expected_release_identity"] == candidate
    assert checks[5]["expected_release_identity"] == candidate
    stale = _canonical_metadata("def5678")
    for index in (1, 5):
        assert checks[index]["validator"](json.dumps(candidate))
        assert not checks[index]["validator"](json.dumps(stale))


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


@pytest.mark.parametrize(
    "environment",
    [
        {
            "VERCEL_STATIC_URL": "https://legacy.static.hf.space",
            "HF_BACKEND_URL": "https://backend.example",
        },
        {
            "VERCEL_STATIC_URL": "https://legacy.azurewebsites.net",
            "HF_BACKEND_URL": "https://backend.example",
        },
        {
            "VERCEL_STATIC_URL": "https://ui.example",
            "HF_BACKEND_URL": "https://legacy.fly.dev",
        },
    ],
)
def test_retired_release_targets_are_rejected_before_checks(
    environment: dict[str, str],
) -> None:
    with pytest.raises(ValueError, match="retired"):
        verifier.build_checks(environment)


def test_version_validator_requires_exact_approved_candidate_identity() -> None:
    candidate = _canonical_metadata()
    stale = _canonical_metadata("def5678")
    legacy = {
        "version": candidate["version"],
        "commit": candidate["release_source_commit"],
    }
    duplicate = json.dumps(candidate).replace(
        '"release_source_commit": "abc1234"',
        '"release_source_commit": "abc1234", "release_source_commit": "abc1234"',
    )

    assert verifier._is_version_response(json.dumps(candidate), candidate)
    assert not verifier._is_version_response(json.dumps(stale), candidate)
    assert not verifier._is_version_response(json.dumps(legacy), candidate)
    assert not verifier._is_version_response(duplicate, candidate)


def test_javascript_validator_rejects_placeholder_responses() -> None:
    assert verifier._is_javascript_response("const version = '1.2.3';")
    assert not verifier._is_javascript_response("<!doctype html><html>not found</html>")
