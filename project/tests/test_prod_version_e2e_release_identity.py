"""Fail-closed contracts for the production version E2E runner."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_prod_version_e2e


BASE_URL = "https://example.invalid"
SOURCE_COMMIT = "abc1234"


def _canonical_metadata(commit: str = SOURCE_COMMIT) -> dict[str, str]:
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


def _run_audit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    metadata: dict[str, str],
    *,
    candidate: dict[str, str] | None = None,
) -> dict:
    candidate_path = tmp_path / "candidate-version.json"
    candidate_path.write_text(
        json.dumps(candidate or _canonical_metadata()),
        encoding="utf-8",
    )
    version = metadata["version"]
    resources = {
        f"{BASE_URL}/version.json": json.dumps(metadata),
        f"{BASE_URL}/": (
            f'<script>window.CURRENT_PAGE_VERSION = "{version}";</script>'
            f'<span id="footer-version-text">Version {version}</span>'
        ),
        f"{BASE_URL}/app.js": (
            f'const CLIENT_APP_VERSION = "{version}"; '
            "showVersionModal forcePurgeAndReload checkAppVersion"
        ),
        f"{BASE_URL}/sw.js": f'const CACHE_VERSION = "{version}";',
        f"{BASE_URL}/favicon.ico": "icon",
        f"{BASE_URL}/favicon.svg": "svg",
    }

    def fake_fetch(url: str, timeout: int = 25) -> tuple[int, str, float]:
        assert timeout == 25
        return 200, resources[url], 1.0

    monkeypatch.setattr(run_prod_version_e2e, "fetch_resource", fake_fetch)
    monkeypatch.setattr(
        run_prod_version_e2e,
        "APPROVED_CANDIDATE_METADATA_PATH",
        candidate_path,
    )
    monkeypatch.setattr(
        run_prod_version_e2e,
        "REPORT_PATH",
        tmp_path / "prod-version-report.json",
    )
    return run_prod_version_e2e.run_version_e2e_audit(BASE_URL)


def test_canonical_release_identity_is_reported_exactly(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    metadata = _canonical_metadata()
    report = _run_audit(monkeypatch, tmp_path, metadata)

    assert report["status"] == "ALL_PASSED_READY_FOR_PROD"
    for field, value in metadata.items():
        assert report[field] == value


def test_self_consistent_stale_release_identity_fails_candidate_gate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    report = _run_audit(monkeypatch, tmp_path, _canonical_metadata("def5678"))

    assert report["status"] == "FAILED"
    assert report["checks"] == [
        {
            "name": "version_json_contract",
            "status": "FAILED",
            "error": "candidate_release_identity_mismatch",
        }
    ]


@pytest.mark.parametrize("invalid_kind", ["legacy", "tampered_digest"])
def test_invalid_release_identity_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    invalid_kind: str,
) -> None:
    metadata = _canonical_metadata()
    if invalid_kind == "legacy":
        metadata = {
            "version": metadata["version"],
            "commit": SOURCE_COMMIT,
            "timestamp": "2026-08-27T00:00:00Z",
            "status": "production",
        }
    else:
        metadata["release_source_metadata_sha256"] = "0" * 64

    report = _run_audit(monkeypatch, tmp_path, metadata)

    assert report["status"] == "FAILED"
    assert report["checks"] == [
        {
            "name": "version_json_contract",
            "status": "FAILED",
            "error": "invalid_release_identity",
        }
    ]


def test_invalid_candidate_metadata_fails_before_network_access(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    candidate_path = tmp_path / "candidate-version.json"
    candidate_path.write_text(
        json.dumps(
            {
                "version": "1.0.0.abc1234",
                "commit": "abc1234",
                "status": "production",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        run_prod_version_e2e,
        "APPROVED_CANDIDATE_METADATA_PATH",
        candidate_path,
    )
    monkeypatch.setattr(
        run_prod_version_e2e,
        "REPORT_PATH",
        tmp_path / "prod-version-report.json",
    )
    monkeypatch.setattr(
        run_prod_version_e2e,
        "fetch_resource",
        lambda *_args, **_kwargs: pytest.fail("network must not be reached"),
    )

    report = run_prod_version_e2e.run_version_e2e_audit(BASE_URL)

    assert report["status"] == "FAILED"
    assert report["checks"] == [
        {
            "name": "approved_candidate_contract",
            "status": "FAILED",
            "error": "invalid_approved_candidate_identity",
        }
    ]


@pytest.mark.parametrize(
    "retired_url",
    [
        "https://legacy.static.hf.space",
        "https://legacy.azurecontainerapps.io",
        "https://legacy.fly.dev",
    ],
)
def test_retired_ui_target_is_rejected_before_network_access(
    monkeypatch: pytest.MonkeyPatch,
    retired_url: str,
) -> None:
    monkeypatch.setattr(
        run_prod_version_e2e,
        "fetch_resource",
        lambda *_args, **_kwargs: pytest.fail("network must not be reached"),
    )

    with pytest.raises(ValueError, match="retired"):
        run_prod_version_e2e.run_version_e2e_audit(retired_url)


def test_auto_update_flag_is_rejected_before_audit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        run_prod_version_e2e,
        "run_version_e2e_audit",
        lambda *_args, **_kwargs: pytest.fail("audit must not run"),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_prod_version_e2e.py", "--auto-update"],
    )

    with pytest.raises(SystemExit) as error:
        run_prod_version_e2e.main()

    assert error.value.code == 2
