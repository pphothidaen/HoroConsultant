"""
tests/test_publish_space_hf.py
================================
Unit & Integration Tests for Hugging Face Spaces Deployment Publisher.

Tests:
1. Static payload audit validation (Dockerfile.hf, requirements.txt, project/)
2. File filter logic (ignoring models/*, kaggle_kernel/*, *.safetensors)
3. Dry-run function execution without errors
"""

from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.publish_space_hf as publisher
from scripts.publish_space_hf import (
    audit_payload,
    publish_space,
    should_ignore,
    stamp_static_html_version,
    verify_live_deployment_version,
    verify_space_health,
)


class _FakeResponse:
    def __init__(self, status_code=200, text="", json_data=None, content_type="text/plain"):
        self.status_code = status_code
        self.text = text
        self._json_data = json_data
        self.headers = {"content-type": content_type}

    def json(self):
        if self._json_data is not None:
            return self._json_data
        return json.loads(self.text)


class _FakeClient:
    def __init__(self, responses, requested_urls):
        self.responses = responses
        self.requested_urls = requested_urls

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def get(self, url):
        self.requested_urls.append(url)
        response = self.responses.get(url)
        if isinstance(response, Exception):
            raise response
        return response or _FakeResponse(status_code=404, text="not found")


def _install_fake_client(monkeypatch, responses):
    requested_urls = []

    def client_factory(*args, **kwargs):
        return _FakeClient(responses, requested_urls)

    monkeypatch.setattr(publisher.httpx, "Client", client_factory)
    return requested_urls


def _release_metadata(version="1.0.0.6c351ba", commit="6c351ba"):
    revision = f"{commit}{'0' * (40 - len(commit))}"
    canonical = {
        "release_source_commit": commit,
        "release_source_metadata_path": "project/static/version.json",
        "release_source_revision": revision,
        "version": version,
    }
    return {
        "version": version,
        "release_source_commit": commit,
        "release_source_revision": revision,
        "release_source_metadata_path": "project/static/version.json",
        "release_source_metadata_sha256": hashlib.sha256(
            json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "status": "production",
    }


def _static_release_responses(version="1.0.0.6c351ba", commit="6c351ba"):
    base_url = "https://pphothidaen-horoconsultant-core-backend.static.hf.space"
    index = f'''
    <link rel="stylesheet" href="style.css?v={commit}">
    <script>window.CURRENT_PAGE_VERSION = "{version}";</script>
    <p id="footer-version-text">Engine v{version} — Powered</p>
    <script src="voice_engine.js?v={commit}"></script>
    <script src="i18n.js?v={commit}"></script>
    <script src="app.js?v={commit}"></script>
    '''
    return {
        f"{base_url}/version.json": _FakeResponse(
            text=json.dumps(_release_metadata(version, commit)),
            content_type="application/json",
        ),
        f"{base_url}/index.html": _FakeResponse(text=index),
        f"{base_url}/app.js": _FakeResponse(text=f'const CLIENT_APP_VERSION = "{version}";'),
        f"{base_url}/sw.js": _FakeResponse(text=f"const CACHE_VERSION = 'v{version}';"),
        f"{base_url}/v3_tokens.css": _FakeResponse(text=":root { --v3-surface: #fff; }"),
    }


def _set_expected_release(monkeypatch, version="1.0.0.6c351ba", commit="6c351ba"):
    from project.core import config

    metadata = _release_metadata(version, commit)
    monkeypatch.setattr(
        config,
        "get_release_source_identity",
        lambda: {
            **metadata,
            "metadata_path": "/release/version.json",
        },
    )


def test_should_ignore_patterns():
    """Verify that heavy model files and cache directories are properly ignored."""
    assert should_ignore("project/models/qwen2.5-bazi-fused/model.safetensors") is True
    assert should_ignore("project/kaggle_kernel/notebook.ipynb") is True
    assert should_ignore("project/__pycache__/main.cpython-311.pyc") is True
    assert should_ignore("project/core/multi_agent_debate.py") is False
    assert should_ignore("project/main.py") is False


def test_audit_payload_integrity():
    """Verify payload audit structure and required files check."""
    is_valid, summary = audit_payload()
    assert is_valid is True
    assert summary["dockerfile_valid"] is True
    assert summary["requirements_valid"] is True
    assert summary["project_valid"] is True
    assert summary["total_files"] > 0
    assert summary["total_bytes"] > 0


def test_docker_build_context_dependencies_exist():
    """Dockerfile COPY sources must be present in the published repository payload."""
    dockerfile = (ROOT / "Dockerfile.hf").read_text(encoding="utf-8")
    assert (ROOT / ".env.example").is_file()
    assert (ROOT / "scripts").is_dir()
    assert (ROOT / "tests").is_dir()
    assert (ROOT / "rust_core" / "Cargo.toml").is_file()
    assert (ROOT / "rust_core" / "tests").is_dir()
    assert "COPY --chown=user:user scripts/" in dockerfile
    assert "COPY --chown=user:user tests/" in dockerfile
    assert "COPY --chown=user:user .env.example" in dockerfile
    assert "maturin build --locked --release" in dockerfile
    assert "COPY rust_core/Cargo.toml" in dockerfile
    assert "COPY rust_core/tests" in dockerfile
    assert "python3-venv patchelf" in dockerfile


def test_publish_space_dry_run():
    """Verify dry-run mode returns True without throwing exception."""
    result = publish_space("pphothidaen/test-horoconsultant-backend", dry_run=True)
    assert result is True


def test_packaging_commit_is_resolved_only_from_git_head(monkeypatch):
    observed = {}

    def fake_check_output(command, **kwargs):
        observed["command"] = command
        observed["cwd"] = kwargs["cwd"]
        return "a" * 40

    monkeypatch.setenv("GIT_COMMIT_HASH", "b" * 40)
    monkeypatch.setenv("VERCEL_GIT_COMMIT_SHA", "c" * 40)
    monkeypatch.setattr(publisher.subprocess, "check_output", fake_check_output)

    assert publisher.get_packaging_commit() == "a" * 40
    assert observed["command"] == ["git", "rev-parse", "--verify", "HEAD^{commit}"]
    assert observed["cwd"] == str(ROOT)


@pytest.mark.parametrize(
    ("mutation", "error_fragment"),
    [
        (lambda metadata: metadata.pop("release_source_commit"), "missing required fields"),
        (lambda metadata: metadata.__setitem__("commit", "6c351ba"), "forbidden fields"),
        (lambda metadata: metadata.__setitem__("packaging_commit", "c9f9161"), "forbidden fields"),
        (lambda metadata: metadata.__setitem__("release_source_metadata_sha256", "0" * 64), "digest does not match"),
        (lambda metadata: metadata.__setitem__("release_source_revision", "0" * 40), "digest does not match"),
    ],
)
def test_release_source_identity_fails_closed_for_malformed_or_legacy_metadata(
    monkeypatch, tmp_path, mutation, error_fragment
):
    from project.core import config

    metadata = _release_metadata(version="1.0.0.c9f9161", commit="c9f9161")
    metadata["release_source_revision"] = "c9f916108f2302de20b28cf31ae1660e63f60394"
    canonical = {
        "release_source_commit": metadata["release_source_commit"],
        "release_source_metadata_path": metadata["release_source_metadata_path"],
        "release_source_revision": metadata["release_source_revision"],
        "version": metadata["version"],
    }
    metadata["release_source_metadata_sha256"] = hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    mutation(metadata)
    metadata_path = tmp_path / "project" / "static" / "version.json"
    metadata_path.parent.mkdir(parents=True)
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    monkeypatch.setattr(config, "BASE_DIR", tmp_path)
    monkeypatch.setattr(
        config.subprocess,
        "check_output",
        lambda *args, **kwargs: "c9f916108f2302de20b28cf31ae1660e63f60394",
    )

    with pytest.raises(ValueError, match=error_fragment):
        config.get_release_source_identity()


def test_release_source_identity_rejects_duplicate_release_source_commit(monkeypatch, tmp_path):
    from project.core import config

    metadata_path = tmp_path / "project" / "static" / "version.json"
    metadata_path.parent.mkdir(parents=True)
    metadata_path.write_text(
        '{"version":"1.0.0.c9f9161","release_source_commit":"c9f9161",'
        '"release_source_commit":"e432e0d"}',
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "BASE_DIR", tmp_path)

    with pytest.raises(ValueError, match="duplicate local release metadata key"):
        config.get_release_source_identity()


def test_release_source_identity_rejects_source_revision_conflict(monkeypatch, tmp_path):
    from project.core import config

    metadata = _release_metadata(version="1.0.0.c9f9161", commit="c9f9161")
    metadata["release_source_revision"] = "0" * 40
    canonical = {
        "release_source_commit": metadata["release_source_commit"],
        "release_source_metadata_path": metadata["release_source_metadata_path"],
        "release_source_revision": metadata["release_source_revision"],
        "version": metadata["version"],
    }
    metadata["release_source_metadata_sha256"] = hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    metadata_path = tmp_path / "project" / "static" / "version.json"
    metadata_path.parent.mkdir(parents=True)
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    monkeypatch.setattr(config, "BASE_DIR", tmp_path)
    monkeypatch.setattr(
        config.subprocess,
        "check_output",
        lambda *args, **kwargs: "c9f916108f2302de20b28cf31ae1660e63f60394",
    )

    with pytest.raises(ValueError, match="revision conflicts"):
        config.get_release_source_identity()


def test_stamp_static_html_version_normalizes_stale_and_composite_labels():
    """Static staging must emit one coherent version on every HTML surface."""
    source = '''
    <script>window.CURRENT_PAGE_VERSION = "1.0.0.e432e0d";</script>
    <p id="footer-version-text">Engine v1.0.0.aaaaaaa.e432e0d — Powered</p>
    <p>Release notes for v1.0.0 must remain untouched.</p>
    <link rel="stylesheet" href="style.css?v=old">
    <script src="i18n.js"></script>
    <script src="voice_engine.js?v=old"></script>
    <script src="app.js?v=old"></script>
    '''

    stamped = stamp_static_html_version(source, "1.0.0.6c351ba", "6c351ba")

    assert 'window.CURRENT_PAGE_VERSION = "1.0.0.6c351ba"' in stamped
    assert 'id="footer-version-text">Engine v1.0.0.6c351ba — Powered' in stamped
    assert "aaaaaaa" not in stamped
    assert "e432e0d" not in stamped
    assert "Release notes for v1.0.0 must remain untouched." in stamped
    assert 'href="style.css?v=6c351ba"' in stamped
    assert 'src="i18n.js?v=6c351ba"' in stamped
    assert 'src="voice_engine.js?v=6c351ba"' in stamped
    assert 'src="app.js?v=6c351ba"' in stamped

    assert stamp_static_html_version(stamped, "1.0.0.6c351ba", "6c351ba") == stamped


def test_verify_static_health_checks_root_and_production_version_metadata(monkeypatch):
    """Static Spaces do not expose the Docker-only /health endpoint."""
    base_url = "https://pphothidaen-horoconsultant-core-backend.static.hf.space"
    responses = {
        f"{base_url}/": _FakeResponse(text="<html>HoroConsultant</html>"),
        f"{base_url}/version.json": _FakeResponse(
            text=json.dumps(_release_metadata()),
            content_type="application/json",
        ),
    }
    requested_urls = _install_fake_client(monkeypatch, responses)

    is_healthy, message, _ = verify_space_health(
        "pphothidaen/horoconsultant-core-backend",
        sdk="static",
    )

    assert is_healthy is True
    assert "Static root and version.json OK" in message
    assert f"{base_url}/health" not in requested_urls
    assert requested_urls == [f"{base_url}/", f"{base_url}/version.json"]


def test_verify_static_health_fails_when_version_asset_is_missing(monkeypatch):
    base_url = "https://pphothidaen-horoconsultant-core-backend.static.hf.space"
    responses = {f"{base_url}/": _FakeResponse(text="<html>HoroConsultant</html>")}
    _install_fake_client(monkeypatch, responses)

    is_healthy, message, _ = verify_space_health(
        "pphothidaen/horoconsultant-core-backend",
        sdk="static",
    )

    assert is_healthy is False
    assert message == "version.json HTTP 404"


def test_verify_docker_health_keeps_health_endpoint_compatibility(monkeypatch):
    health_url = "https://pphothidaen-horoconsultant-core-backend.hf.space/health"
    requested_urls = _install_fake_client(
        monkeypatch,
        {
            health_url: _FakeResponse(
                text='{"status":"ok"}',
                json_data={"status": "ok"},
                content_type="application/json",
            )
        },
    )

    is_healthy, message, _ = verify_space_health(
        "pphothidaen/horoconsultant-core-backend",
        sdk="docker",
    )

    assert is_healthy is True
    assert "HTTP 200 OK" in message
    assert requested_urls == [health_url]


def test_verify_live_static_release_requires_all_exact_version_surfaces(monkeypatch):
    _set_expected_release(monkeypatch)
    responses = _static_release_responses()
    requested_urls = _install_fake_client(monkeypatch, responses)

    matched, message, details = verify_live_deployment_version(
        "pphothidaen/horoconsultant-core-backend",
        sdk="static",
    )

    assert matched is True
    assert message.startswith("[OK]")
    assert details["matched"] is True
    assert details["expected_release_source_commit"] == "6c351ba"
    assert details["packaging_commit"] == publisher.get_packaging_commit()
    assert details["failed_checks"] == []
    assert all(details["checks"].values())
    assert len(requested_urls) == 5
    assert not any("fly.dev" in url for url in requested_urls)


def test_verify_live_static_release_rejects_stale_and_composite_html_versions(monkeypatch):
    _set_expected_release(monkeypatch)
    responses = _static_release_responses()
    index_url = "https://pphothidaen-horoconsultant-core-backend.static.hf.space/index.html"
    responses[index_url] = _FakeResponse(
        text='''
        <link rel="stylesheet" href="style.css?v=6c351ba">
        <script>window.CURRENT_PAGE_VERSION = "1.0.0.e432e0d";</script>
        <p id="footer-version-text">Engine v1.0.0.6c351ba.e432e0d — Powered</p>
        <script src="voice_engine.js?v=6c351ba"></script>
        <script src="i18n.js?v=6c351ba"></script>
        <script src="app.js?v=6c351ba"></script>
        ''',
    )
    _install_fake_client(monkeypatch, responses)

    matched, message, details = verify_live_deployment_version(
        "pphothidaen/horoconsultant-core-backend",
        sdk="static",
    )

    assert matched is False
    assert message.startswith("[ERROR]")
    assert details["checks"]["current_page_version_exact"] is False
    assert details["checks"]["footer_version_exact"] is False
    assert "current_page_version_exact" in details["failed_checks"]
    assert "footer_version_exact" in details["failed_checks"]


def test_verify_live_static_release_fails_closed_when_asset_is_missing(monkeypatch):
    _set_expected_release(monkeypatch)
    responses = _static_release_responses()
    css_url = "https://pphothidaen-horoconsultant-core-backend.static.hf.space/v3_tokens.css"
    responses.pop(css_url)
    _install_fake_client(monkeypatch, responses)

    matched, message, details = verify_live_deployment_version(
        "pphothidaen/horoconsultant-core-backend",
        sdk="static",
    )

    assert matched is False
    assert message.startswith("[ERROR]")
    assert details["checks"]["v3_tokens.css_http_200"] is False
    assert details["checks"]["v3_tokens_css_nonempty"] is False


def test_verify_live_static_release_rejects_duplicate_version_surfaces(monkeypatch):
    """A correct first value must not hide a later stale or composite duplicate."""
    _set_expected_release(monkeypatch)
    responses = _static_release_responses()
    base_url = "https://pphothidaen-horoconsultant-core-backend.static.hf.space"
    responses[f"{base_url}/index.html"] = _FakeResponse(
        text='''
        <link rel="stylesheet" href="style.css?v=6c351ba">
        <link rel="stylesheet" href="style.css?v=e432e0d">
        <script>window.CURRENT_PAGE_VERSION = "1.0.0.6c351ba";</script>
        <script>window.CURRENT_PAGE_VERSION = "1.0.0.e432e0d";</script>
        <p id="footer-version-text">Engine v1.0.0.6c351ba — Powered</p>
        <p id="footer-version-text">Engine v1.0.0.6c351ba.e432e0d — Powered</p>
        <script src="voice_engine.js?v=6c351ba"></script>
        <script src="voice_engine.js?v=e432e0d"></script>
        <script src="i18n.js?v=6c351ba"></script>
        <script src="i18n.js?v=e432e0d"></script>
        <script src="app.js?v=6c351ba"></script>
        <script src="app.js?v=e432e0d"></script>
        ''',
    )
    responses[f"{base_url}/app.js"] = _FakeResponse(
        text='''
        const CLIENT_APP_VERSION = "1.0.0.6c351ba";
        const CLIENT_APP_VERSION = "1.0.0.e432e0d";
        ''',
    )
    responses[f"{base_url}/sw.js"] = _FakeResponse(
        text="""
        const CACHE_VERSION = 'v1.0.0.6c351ba';
        const CACHE_VERSION = 'v1.0.0.e432e0d';
        """,
    )
    _install_fake_client(monkeypatch, responses)

    matched, message, details = verify_live_deployment_version(
        "pphothidaen/horoconsultant-core-backend",
        sdk="static",
    )

    assert matched is False
    assert message.startswith("[ERROR]")
    duplicate_sensitive_checks = {
        "current_page_version_exact",
        "footer_version_exact",
        "style_cache_ref_exact",
        "i18n_cache_ref_exact",
        "voice_cache_ref_exact",
        "app_cache_ref_exact",
        "client_app_version_exact",
        "service_worker_cache_version_exact",
    }
    assert duplicate_sensitive_checks.issubset(details["failed_checks"])


def test_verify_live_static_release_fails_closed_on_http_error(monkeypatch):
    _set_expected_release(monkeypatch)
    responses = _static_release_responses()
    version_url = "https://pphothidaen-horoconsultant-core-backend.static.hf.space/version.json"
    responses[version_url] = publisher.httpx.ConnectError("network unavailable")
    _install_fake_client(monkeypatch, responses)

    matched, message, details = verify_live_deployment_version(
        "pphothidaen/horoconsultant-core-backend",
        sdk="static",
    )

    assert matched is False
    assert message.startswith("[ERROR]")
    assert details["matched"] is False
    assert details["failed_checks"] == []
    assert any("request failure" in error for error in details["errors"])


def test_verify_version_cli_exits_nonzero_when_release_mismatches(monkeypatch):
    details = {
        "expected_commit": "6c351ba",
        "expected_version": "1.0.0.6c351ba",
    }
    monkeypatch.setattr(
        publisher,
        "verify_live_deployment_version",
        lambda space_id, sdk: (False, "[ERROR] mismatch", details),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["publish_space_hf.py", "--sdk", "static", "--verify-version"],
    )

    with pytest.raises(SystemExit) as exit_info:
        publisher.main()

    assert exit_info.value.code == 1


def test_verify_live_release_without_httpx_keeps_stable_failure_schema(monkeypatch):
    _set_expected_release(monkeypatch)
    monkeypatch.setattr(publisher, "HTTPX_AVAILABLE", False)

    matched, message, details = verify_live_deployment_version(
        "pphothidaen/horoconsultant-core-backend",
        sdk="static",
    )

    assert matched is False
    assert message.startswith("[ERROR]")
    assert details["matched"] is False
    assert details["checks"] == {}
    assert details["failed_checks"] == []
    assert details["errors"] == ["httpx package not installed"]


def test_verify_live_docker_release_rejects_version_and_commit_mismatch(monkeypatch):
    _set_expected_release(monkeypatch)
    health_url = "https://pphothidaen-horoconsultant-core-backend.hf.space/health"
    _install_fake_client(
        monkeypatch,
        {
            health_url: _FakeResponse(
                json_data={"version": "1.0.0.e432e0d", "git_commit": "e432e0d"},
                content_type="application/json",
            )
        },
    )

    matched, message, details = verify_live_deployment_version(
        "pphothidaen/horoconsultant-core-backend",
        sdk="docker",
    )

    assert matched is False
    assert message.startswith("[ERROR]")
    assert details["checks"]["health_http_200"] is True
    assert details["checks"]["health_commit_exact"] is False
    assert details["checks"]["health_version_exact"] is False
    assert details["failed_checks"] == ["health_commit_exact", "health_version_exact"]


def test_verify_live_static_release_accepts_source_metadata_when_packaging_head_differs(monkeypatch):
    """A later evidence commit must not invalidate immutable source provenance."""
    _set_expected_release(monkeypatch, version="1.0.0.6c351ba", commit="6c351ba")
    monkeypatch.setattr(publisher, "get_packaging_commit", lambda: "c9f9161" * 5 + "c9f91")
    monkeypatch.setattr(publisher, "source_is_ancestor_of_packaging", lambda source, packaging: True)
    responses = _static_release_responses(version="1.0.0.6c351ba", commit="6c351ba")
    responses[
        "https://pphothidaen-horoconsultant-core-backend.static.hf.space/version.json"
    ] = _FakeResponse(
        text=json.dumps(_release_metadata()),
        content_type="application/json",
    )
    _install_fake_client(monkeypatch, responses)

    matched, message, details = verify_live_deployment_version(
        "pphothidaen/horoconsultant-core-backend",
        sdk="static",
    )

    assert matched is True
    assert message.startswith("[OK]")
    assert details["expected_release_source_commit"] == "6c351ba"
    assert details["packaging_commit"] == "c9f9161" * 5 + "c9f91"


def test_verify_live_static_release_rejects_conflicting_source_provenance(monkeypatch):
    _set_expected_release(monkeypatch)
    responses = _static_release_responses()
    responses[
        "https://pphothidaen-horoconsultant-core-backend.static.hf.space/version.json"
    ] = _FakeResponse(
        text=json.dumps(_release_metadata(commit="e432e0d")),
        content_type="application/json",
    )
    _install_fake_client(monkeypatch, responses)

    matched, message, details = verify_live_deployment_version(
        "pphothidaen/horoconsultant-core-backend",
        sdk="static",
    )

    assert matched is False
    assert message.startswith("[ERROR]")
    assert details["checks"]["version_json_source_commit_exactly_once"] is True
    assert details["checks"]["version_json_source_commit_exact"] is False


def test_verify_live_static_release_rejects_duplicate_version_metadata_keys(monkeypatch):
    """JSON parsing must not silently accept a duplicate source identity field."""
    _set_expected_release(monkeypatch)
    responses = _static_release_responses()
    responses[
        "https://pphothidaen-horoconsultant-core-backend.static.hf.space/version.json"
    ] = _FakeResponse(
        text=(
            '{"version":"1.0.0.6c351ba",'
            '"release_source_commit":"6c351ba",'
            '"release_source_commit":"e432e0d","status":"production"}'
        ),
        content_type="application/json",
    )
    _install_fake_client(monkeypatch, responses)

    matched, message, details = verify_live_deployment_version(
        "pphothidaen/horoconsultant-core-backend",
        sdk="static",
    )

    assert matched is False
    assert message.startswith("[ERROR]")
    assert any("duplicate version.json key" in error for error in details["errors"])


def test_verify_live_static_release_rejects_packaging_commit_on_version_surface(monkeypatch):
    """Packaging provenance belongs to publisher evidence, never deployed metadata."""
    _set_expected_release(monkeypatch)
    responses = _static_release_responses()
    base_url = "https://pphothidaen-horoconsultant-core-backend.static.hf.space"
    version_meta = _release_metadata()
    version_meta["packaging_commit"] = "c9f9161"
    responses[f"{base_url}/version.json"] = _FakeResponse(text=json.dumps(version_meta))
    _install_fake_client(monkeypatch, responses)

    matched, _, details = verify_live_deployment_version(
        "pphothidaen/horoconsultant-core-backend", sdk="static"
    )

    assert matched is False
    assert details["checks"]["version_json_source_commit_exactly_once"] is False


def test_verify_live_static_release_fails_when_source_is_not_packaging_ancestor(monkeypatch):
    _set_expected_release(monkeypatch)
    monkeypatch.setattr(publisher, "get_packaging_commit", lambda: "c9f9161" * 5 + "c9f91")
    monkeypatch.setattr(publisher, "source_is_ancestor_of_packaging", lambda source, packaging: False)

    matched, message, details = verify_live_deployment_version(
        "pphothidaen/horoconsultant-core-backend", sdk="static"
    )

    assert matched is False
    assert message.startswith("[ERROR]")
    assert any("not an ancestor" in error for error in details["errors"])
