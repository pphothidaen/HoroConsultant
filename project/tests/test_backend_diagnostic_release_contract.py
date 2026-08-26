"""Minimal offline contract for the frozen HF Docker backend diagnostics."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any, Self
from urllib.parse import urlsplit
from urllib.request import Request

import pytest

from scripts import grafana_cloud_exporter as grafana
from scripts import run_remote_api_live_test as remote
from scripts import test_live_e2e_network as network

ROOT = Path(__file__).resolve().parents[2]
CANONICAL_BACKEND = "https://pphothidaen-horoconsultant-core-backend.hf.space"
CANONICAL_NETLOC = "pphothidaen-horoconsultant-core-backend.hf.space"
MODULES: tuple[ModuleType, ...] = (grafana, remote, network)
SOURCES = {
    grafana: ROOT / "scripts" / "grafana_cloud_exporter.py",
    remote: ROOT / "scripts" / "run_remote_api_live_test.py",
    network: ROOT / "scripts" / "test_live_e2e_network.py",
}
FROZEN_SHA256 = {
    grafana: "b0b2f4b9bb5989504ca46e197b5b8d79eeb92680bbf691213c6b9beee858f2fb",
    remote: "2fb600f454d46033511117bcb65b5be932296bc7088991396d36cb8b20fec8db",
    network: "f4a00dcf8ec106021dc44eca81f6f8ebd8c07c30d597ed1815728a233a94d15b",
}
EXPECTED_URLS = {
    grafana: (
        f"{CANONICAL_BACKEND}/health",
        f"{CANONICAL_BACKEND}/metrics",
    ),
    remote: (
        f"{CANONICAL_BACKEND}/health",
        f"{CANONICAL_BACKEND}/api/v1/health",
        f"{CANONICAL_BACKEND}/version.json",
    ),
    network: (
        f"{CANONICAL_BACKEND}/health",
        f"{CANONICAL_BACKEND}/api/v1/health",
        f"{CANONICAL_BACKEND}/version.json",
    ),
}
RETIRED_OR_LOCAL_TARGETS = (
    "https://pphothidaen-horoconsultant-core-backend.static.hf.space/health",
    "https://horoconsultant.azurewebsites.net/health",
    "https://horoconsultant.fly.dev/health",
    "http://127.0.0.1:8000/health",
    "http://localhost:8000/health",
    "file:///Users/release-operator/backend/health",
    "/Users/release-operator/backend/health",
)
FORBIDDEN_SOURCE_MARKERS = (
    ".static.hf.space",
    "azurewebsites",
    "azurecontainerapps",
    "fly.dev",
    "fly.io",
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "/users/",
    "c:\\users\\",
    'method="post"',
    "method='post'",
    "requests.post",
    "urllib.request.urlopen",
    "authorization",
    "bearer ",
    "grafana_api_key",
    "os.environ",
    "os.getenv",
    "load_dotenv",
    "subprocess",
)


class FakeResponse:
    def __init__(self, body: bytes, *, status: int = 200) -> None:
        self.body = body
        self.status = status

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, limit: int) -> bytes:
        assert 0 < limit <= grafana.MAX_RESPONSE_BYTES + 1
        return self.body


def _urls(module: ModuleType) -> tuple[str, ...]:
    if module is network:
        return tuple(url for _, url in network.READ_ONLY_URLS)
    return tuple(contract["url"] for contract in module.READ_ONLY_ENDPOINTS)


def _probe(
    module: ModuleType,
    open_request: Callable[[Request, float], FakeResponse],
    *,
    timeout: float = 5.0,
) -> dict[str, Any]:
    if module is grafana:
        return grafana.probe_observability_endpoint(
            grafana.READ_ONLY_ENDPOINTS[0],
            timeout=timeout,
            open_request=open_request,
        )
    if module is remote:
        return remote.probe_endpoint(
            remote.READ_ONLY_ENDPOINTS[0],
            timeout=timeout,
            open_request=open_request,
        )
    return network.execute_network_request(
        network.READ_ONLY_URLS[0][1],
        timeout=timeout,
        open_request=open_request,
    )


def _probe_invalid_target(
    module: ModuleType,
    target: str,
    open_request: Callable[[Request, float], FakeResponse],
) -> None:
    if module is network:
        network.execute_network_request(target, open_request=open_request)
        return
    contract = dict(module.READ_ONLY_ENDPOINTS[0])
    contract["url"] = target
    if module is grafana:
        grafana.probe_observability_endpoint(contract, open_request=open_request)
    else:
        remote.probe_endpoint(contract, open_request=open_request)


def test_frozen_hashes_and_static_policy() -> None:
    for module, source_path in SOURCES.items():
        source = source_path.read_text(encoding="utf-8")
        digest = hashlib.sha256(source_path.read_bytes()).hexdigest()

        assert digest == FROZEN_SHA256[module]
        assert source.isascii()
        assert all(marker not in source.lower() for marker in FORBIDDEN_SOURCE_MARKERS)
        assert 'method="GET"' in source
        assert "ProxyHandler({})" in source
        assert "MAX_TIMEOUT_SECONDS = 10.0" in source
        assert "MAX_RESPONSE_BYTES" in source


def test_exact_canonical_https_endpoint_matrices() -> None:
    for module in MODULES:
        assert module.CANONICAL_HF_DOCKER_BACKEND == CANONICAL_BACKEND
        assert _urls(module) == EXPECTED_URLS[module]
        for target in _urls(module):
            parsed = urlsplit(target)
            assert parsed.scheme == "https"
            assert parsed.netloc == CANONICAL_NETLOC
            assert parsed.username is None
            assert parsed.password is None
            assert parsed.port is None
            assert not parsed.query
            assert not parsed.fragment


@pytest.mark.parametrize("module", MODULES, ids=("grafana", "remote", "network"))
def test_default_cli_is_offline_and_json_evidence_is_target_bound(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def unexpected_open(*_args: object, **_kwargs: object) -> FakeResponse:
        raise AssertionError("default CLI attempted network I/O")

    monkeypatch.setattr(module, "_open_read_only", unexpected_open)
    parser = module.build_cli_parser()
    assert parser.parse_args([]).live is False
    assert parser.parse_args(["--live"]).live is True
    assert module.main(["--json"]) == 0

    output = capsys.readouterr().out
    evidence = json.loads(output)
    assert evidence["method"] == "GET"
    assert evidence["mode"] == "DRY_RUN"
    assert evidence["network_requests"] == 0
    assert evidence["target"] == CANONICAL_BACKEND
    assert str(ROOT) not in output
    assert output.isascii()


def test_explicit_live_mocks_are_get_only_and_do_not_return_bodies() -> None:
    calls: list[Request] = []

    def safe_open(request: Request, timeout: float) -> FakeResponse:
        calls.append(request)
        assert request.get_method() == "GET"
        assert request.data is None
        assert request.full_url in set().union(*EXPECTED_URLS.values())
        assert 0.1 <= timeout <= 10.0
        headers = {name.lower() for name, _ in request.header_items()}
        assert "authorization" not in headers
        assert "cookie" not in headers
        if request.full_url.endswith("/metrics"):
            return FakeResponse(b"process_uptime_seconds 1\n")
        return FakeResponse(b'{"status":"ok","private":"BODY_CANARY"}')

    results = [
        *grafana.run_read_only_diagnostics(live=True, open_request=safe_open),
        *remote.run_diagnostics(live=True, open_request=safe_open),
    ]
    assert network.run_strict_live_e2e_audit(live=True, open_request=safe_open)

    assert len(calls) == 8
    for result in results:
        rendered = json.dumps(result, sort_keys=True)
        assert result["outcome"] == "PASSED"
        assert result["classification"] == "OK"
        assert "BODY_CANARY" not in rendered


def test_invalid_targets_methods_and_contracts_fail_before_io() -> None:
    calls = 0

    def unexpected_open(*_args: object, **_kwargs: object) -> FakeResponse:
        nonlocal calls
        calls += 1
        raise AssertionError("invalid contract reached network I/O")

    for module in MODULES:
        for target in RETIRED_OR_LOCAL_TARGETS:
            with pytest.raises(ValueError, match="allowlist|canonical"):
                _probe_invalid_target(module, target, unexpected_open)

    with pytest.raises(ValueError, match="only GET"):
        network.execute_network_request(
            network.READ_ONLY_URLS[0][1],
            method="POST",
            open_request=unexpected_open,
        )
    with pytest.raises(ValueError, match="HTTP 200"):
        network.execute_network_request(
            network.READ_ONLY_URLS[0][1],
            expected_status=201,
            open_request=unexpected_open,
        )
    for module in (grafana, remote):
        contract = dict(module.READ_ONLY_ENDPOINTS[0])
        contract["name"] = "renamed_health"
        with pytest.raises(ValueError, match="allowlist"):
            if module is grafana:
                grafana.probe_observability_endpoint(
                    contract,
                    open_request=unexpected_open,
                )
            else:
                remote.probe_endpoint(contract, open_request=unexpected_open)
    assert calls == 0


@pytest.mark.parametrize("module", MODULES, ids=("grafana", "remote", "network"))
def test_openers_disable_ambient_proxies_and_redirects(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, Any] = {}
    marker = FakeResponse(b'{"status":"ok"}')

    class FakeOpener:
        def open(self, request: Request, *, timeout: float) -> FakeResponse:
            observed.update(request=request, timeout=timeout)
            return marker

    def fake_build_opener(*handlers: object) -> FakeOpener:
        observed["handlers"] = handlers
        return FakeOpener()

    monkeypatch.setattr(module.urllib.request, "build_opener", fake_build_opener)
    request = Request(EXPECTED_URLS[module][0], method="GET")
    assert module._open_read_only(request, 2.5) is marker

    handlers = observed["handlers"]
    proxies = [
        handler
        for handler in handlers
        if isinstance(handler, module.urllib.request.ProxyHandler)
    ]
    assert len(proxies) == 1
    assert proxies[0].proxies == {}
    assert any(isinstance(handler, module._RejectRedirects) for handler in handlers)
    assert observed["request"] is request
    assert observed["timeout"] == 2.5


@pytest.mark.parametrize("module", MODULES, ids=("grafana", "remote", "network"))
def test_timeout_bounds_fail_before_io(module: ModuleType) -> None:
    calls = 0

    def unexpected_open(*_args: object, **_kwargs: object) -> FakeResponse:
        nonlocal calls
        calls += 1
        raise AssertionError("invalid timeout reached network I/O")

    for timeout in (0.0, -1.0, 10.1, math.inf, math.nan):
        with pytest.raises(ValueError, match="safe diagnostic range"):
            _probe(module, unexpected_open, timeout=timeout)
        with pytest.raises(argparse.ArgumentTypeError, match="between"):
            module._timeout_value(str(timeout))
    assert calls == 0


@pytest.mark.parametrize("module", MODULES, ids=("grafana", "remote", "network"))
def test_invalid_bodies_and_provider_failures_are_sanitized(
    module: ModuleType,
) -> None:
    path_canary = "/Users/private/workstation"
    credential_canary = "TOKEN_CANARY_MUST_NOT_APPEAR"

    def invalid_body(_request: Request, _timeout: float) -> FakeResponse:
        body = json.dumps([path_canary, credential_canary]).encode("ascii")
        return FakeResponse(body)

    invalid = _probe(module, invalid_body)
    assert invalid["classification"] == "INVALID_RESPONSE"
    assert path_canary not in json.dumps(invalid)
    assert credential_canary not in json.dumps(invalid)

    def provider_failure(_request: Request, _timeout: float) -> FakeResponse:
        raise RuntimeError(f"{credential_canary} {path_canary}")

    failed = _probe(module, provider_failure)
    rendered = json.dumps(failed, sort_keys=True)
    assert failed["classification"] == "NETWORK_ERROR"
    assert path_canary not in rendered
    assert credential_canary not in rendered
    assert rendered.isascii()


def test_grafana_compatibility_is_local_only_and_console_redacted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    body_canary = "LOCAL_DASHBOARD_BODY_CANARY"
    credential_canary = "LEGACY_CREDENTIAL_CANARY"
    dashboard = tmp_path / "operator-dashboard.json"
    dashboard.write_text(
        json.dumps({"title": body_canary, "panels": []}),
        encoding="ascii",
    )

    def unexpected_open(*_args: object, **_kwargs: object) -> FakeResponse:
        raise AssertionError("offline dashboard validation attempted network I/O")

    monkeypatch.setattr(grafana, "_open_read_only", unexpected_open)
    assert grafana.main(["--export-dashboard", "--dashboard-path", str(dashboard)]) == 0
    output = capsys.readouterr().out
    assert "dashboard JSON validated in read-only mode" in output
    assert body_canary not in output
    assert str(dashboard) not in output
    assert output.isascii()

    disabled = grafana.export_dashboard_to_grafana(
        dashboard,
        dry_run=False,
        url="https://example.invalid",
        token=credential_canary,
    )
    assert disabled["status"] == "mutation_disabled"
    assert credential_canary not in json.dumps(disabled, sort_keys=True)


@pytest.mark.parametrize("module", MODULES, ids=("grafana", "remote", "network"))
def test_cli_errors_use_fixed_ascii_names_without_workstation_paths(
    module: ModuleType,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path_canary = "/Users/private/secret"
    parser = module.build_cli_parser()
    with pytest.raises(SystemExit) as raised:
        parser.parse_args(["--timeout", path_canary])

    output = capsys.readouterr().err
    assert raised.value.code == 2
    assert path_canary not in output
    assert str(ROOT) not in output
    assert parser.prog in output
    assert output.isascii()
