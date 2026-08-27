"""Fail-closed contracts for the production version E2E runner."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts import run_prod_version_e2e


BASE_URL = "https://example.invalid"
SOURCE_COMMIT = "abc1234"
SOURCE_REVISION = SOURCE_COMMIT + "a" * 33


def _canonical_metadata() -> dict[str, str]:
    identity = {
        "release_source_commit": SOURCE_COMMIT,
        "release_source_metadata_path": "project/static/version.json",
        "release_source_revision": SOURCE_REVISION,
        "version": f"1.0.0.{SOURCE_COMMIT}",
    }
    canonical = json.dumps(
        identity,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "version": identity["version"],
        "release_source_commit": SOURCE_COMMIT,
        "release_source_revision": SOURCE_REVISION,
        "release_source_metadata_path": identity["release_source_metadata_path"],
        "release_source_metadata_sha256": hashlib.sha256(canonical).hexdigest(),
    }


def _run_audit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    metadata: dict[str, str],
) -> dict:
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
