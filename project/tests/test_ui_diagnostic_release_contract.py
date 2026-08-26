"""Offline contracts for the frozen production UI diagnostic commands."""

from __future__ import annotations

import asyncio
import json
import sys
import urllib.error
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from scripts import (
    audit_ui_overlap,
    run_live_e2e_hf_space,
    run_vercel_prod_curl_regression,
    test_static_hf_space_questions,
)

VERCEL_UI_URL = "https://horo-consultant-psi.vercel.app"
HF_DOCKER_BACKEND_URL = "https://pphothidaen-horoconsultant-core-backend.hf.space"

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATHS = (
    ROOT / "scripts" / "test_static_hf_space_questions.py",
    ROOT / "scripts" / "run_live_e2e_hf_space.py",
    ROOT / "scripts" / "audit_ui_overlap.py",
    ROOT / "scripts" / "run_vercel_prod_curl_regression.py",
)

DIAGNOSTICS: tuple[tuple[str, ModuleType, str], ...] = (
    (
        "randomized-questions",
        test_static_hf_space_questions,
        "run_randomized_ui_questions_test",
    ),
    ("browser-e2e", run_live_e2e_hf_space, "run_live_e2e"),
    ("overlap-audit", audit_ui_overlap, "run_live_audit"),
    ("http-regression", run_vercel_prod_curl_regression, "run_regression"),
)

RETIRED_OR_LOCAL_TARGETS = (
    "https://pphothidaen-horoconsultant-core-backend.static.hf.space",
    "https://horoconsultant.azurewebsites.net",
    "https://horoconsultant.fly.dev",
    "http://127.0.0.1:8000",
    "http://localhost:8080",
    "file:///Users/release-operator/project/static/index.html",
    "/Users/release-operator/project/static/index.html",
)


@pytest.mark.parametrize(
    ("_name", "diagnostic", "_live_runner"),
    DIAGNOSTICS,
    ids=[item[0] for item in DIAGNOSTICS],
)
def test_each_diagnostic_exposes_the_separate_canonical_target_pair(
    _name: str,
    diagnostic: ModuleType,
    _live_runner: str,
) -> None:
    assert diagnostic.CANONICAL_VERCEL_UI_URL == VERCEL_UI_URL
    assert diagnostic.CANONICAL_HF_DOCKER_BACKEND_URL == HF_DOCKER_BACKEND_URL
    assert diagnostic.CANONICAL_VERCEL_UI_URL != (
        diagnostic.CANONICAL_HF_DOCKER_BACKEND_URL
    )

    args = diagnostic._parser().parse_args([])
    assert args.live is False
    assert args.ui_url == VERCEL_UI_URL
    assert args.backend_url == HF_DOCKER_BACKEND_URL


@pytest.mark.parametrize(
    ("_name", "diagnostic", "live_runner"),
    DIAGNOSTICS,
    ids=[item[0] for item in DIAGNOSTICS],
)
def test_default_execution_is_offline_and_does_not_enter_the_live_runner(
    monkeypatch: pytest.MonkeyPatch,
    _name: str,
    diagnostic: ModuleType,
    live_runner: str,
) -> None:
    def unexpected_live_execution(*_args, **_kwargs):
        raise AssertionError("default execution reached a live diagnostic path")

    monkeypatch.setattr(diagnostic, live_runner, unexpected_live_execution)
    monkeypatch.setattr(sys, "argv", [diagnostic.__file__])

    assert diagnostic.main() == 0


@pytest.mark.parametrize(
    ("_name", "diagnostic", "_live_runner"),
    DIAGNOSTICS,
    ids=[item[0] for item in DIAGNOSTICS],
)
@pytest.mark.parametrize(
    "retired_target",
    RETIRED_OR_LOCAL_TARGETS,
    ids=(
        "hf-static",
        "azure",
        "fly",
        "loopback",
        "localhost",
        "workstation-file-url",
        "workstation-path",
    ),
)
def test_retired_and_workstation_targets_are_rejected_for_both_roles(
    _name: str,
    diagnostic: ModuleType,
    _live_runner: str,
    retired_target: str,
) -> None:
    for expected, label in (
        (VERCEL_UI_URL, "UI URL"),
        (HF_DOCKER_BACKEND_URL, "Backend URL"),
    ):
        with pytest.raises(ValueError, match="canonical HTTPS target"):
            diagnostic._require_canonical_https_url(
                retired_target,
                expected,
                label,
            )


@pytest.mark.parametrize(
    ("_name", "diagnostic", "live_runner"),
    DIAGNOSTICS,
    ids=[item[0] for item in DIAGNOSTICS],
)
@pytest.mark.parametrize(
    ("option", "invalid_target"),
    (
        ("--ui-url", HF_DOCKER_BACKEND_URL),
        ("--backend-url", VERCEL_UI_URL),
        (
            "--ui-url",
            "https://pphothidaen-horoconsultant-core-backend.static.hf.space",
        ),
        ("--backend-url", "https://horoconsultant.fly.dev"),
    ),
    ids=("backend-as-ui", "ui-as-backend", "hf-static-ui", "fly-backend"),
)
def test_live_mode_fails_closed_before_execution_when_roles_or_targets_are_invalid(
    monkeypatch: pytest.MonkeyPatch,
    _name: str,
    diagnostic: ModuleType,
    live_runner: str,
    option: str,
    invalid_target: str,
) -> None:
    def unexpected_live_execution(*_args, **_kwargs):
        raise AssertionError("invalid configuration reached a live diagnostic path")

    monkeypatch.setattr(diagnostic, live_runner, unexpected_live_execution)
    monkeypatch.setattr(
        sys,
        "argv",
        [diagnostic.__file__, "--live", option, invalid_target],
    )

    assert diagnostic.main() == 2


def test_overlap_audit_preserves_the_five_canonical_viewports() -> None:
    assert audit_ui_overlap.VIEWPORTS == [
        {"name": "desktop-4k", "width": 1920, "height": 1080},
        {"name": "laptop-standard", "width": 1366, "height": 768},
        {"name": "tablet-portrait", "width": 768, "height": 1024},
        {"name": "mobile-ios", "width": 390, "height": 844},
        {"name": "mobile-compact", "width": 360, "height": 740},
    ]


def test_frozen_sources_are_ascii_and_exclude_retired_or_workstation_targets() -> None:
    forbidden_literals = (
        "static.hf.space",
        "azurewebsites.net",
        "azurecontainerapps.io",
        "fly.dev",
        "http://127.0.0.1",
        "http://localhost",
        "file://",
        "/users/",
        "/home/",
    )

    for source_path in SOURCE_PATHS:
        source_bytes = source_path.read_bytes()
        assert source_bytes.isascii(), source_path.name
        rendered = source_bytes.decode("ascii").lower()
        for forbidden in forbidden_literals:
            assert forbidden not in rendered, (source_path.name, forbidden)


@pytest.mark.parametrize(
    ("_name", "diagnostic", "live_runner"),
    DIAGNOSTICS,
    ids=[item[0] for item in DIAGNOSTICS],
)
@pytest.mark.parametrize("timeout", (0, 61), ids=("zero", "above-maximum"))
def test_timeout_bounds_fail_before_live_execution(
    monkeypatch: pytest.MonkeyPatch,
    _name: str,
    diagnostic: ModuleType,
    live_runner: str,
    timeout: int,
) -> None:
    def unexpected_live_execution(*_args, **_kwargs):
        raise AssertionError("invalid timeout reached a live diagnostic path")

    monkeypatch.setattr(diagnostic, live_runner, unexpected_live_execution)
    monkeypatch.setattr(
        sys,
        "argv",
        [diagnostic.__file__, "--live", "--timeout", str(timeout)],
    )

    assert diagnostic.main() == 2


@pytest.mark.parametrize("count", (0, 101), ids=("zero", "above-maximum"))
def test_question_count_bounds_fail_before_live_execution(
    monkeypatch: pytest.MonkeyPatch,
    count: int,
) -> None:
    def unexpected_live_execution(*_args, **_kwargs):
        raise AssertionError("invalid count reached a live diagnostic path")

    diagnostic = test_static_hf_space_questions
    monkeypatch.setattr(
        diagnostic,
        "run_randomized_ui_questions_test",
        unexpected_live_execution,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [diagnostic.__file__, "--live", "--count", str(count)],
    )

    assert diagnostic.main() == 2


@pytest.mark.parametrize("retries", (-1, 3), ids=("negative", "above-maximum"))
def test_http_retry_bounds_fail_before_live_execution(
    monkeypatch: pytest.MonkeyPatch,
    retries: int,
) -> None:
    def unexpected_live_execution(*_args, **_kwargs):
        raise AssertionError("invalid retries reached a live diagnostic path")

    diagnostic = run_vercel_prod_curl_regression
    monkeypatch.setattr(diagnostic, "run_regression", unexpected_live_execution)
    monkeypatch.setattr(
        sys,
        "argv",
        [diagnostic.__file__, "--live", "--retries", str(retries)],
    )

    assert diagnostic.main() == 2


@pytest.mark.parametrize(
    ("_name", "diagnostic", "live_runner"),
    DIAGNOSTICS,
    ids=[item[0] for item in DIAGNOSTICS],
)
def test_invalid_target_diagnostics_do_not_echo_attacker_content(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
    _name: str,
    diagnostic: ModuleType,
    live_runner: str,
) -> None:
    marker = "attacker-marker-non-ascii-\u0e04\u0e27\u0e32\u0e21\u0e25\u0e31\u0e1a"

    def unexpected_live_execution(*_args, **_kwargs):
        raise AssertionError("invalid target reached a live diagnostic path")

    monkeypatch.setattr(diagnostic, live_runner, unexpected_live_execution)
    monkeypatch.setattr(
        sys,
        "argv",
        [diagnostic.__file__, "--live", "--ui-url", f"https://bad.invalid/{marker}"],
    )

    assert diagnostic.main() == 2
    captured = capsys.readouterr()
    rendered = captured.out + captured.err + caplog.text
    assert marker not in rendered


def test_question_runner_validates_targets_before_generation_or_artifact_write(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "questions-report.json"

    def unexpected_generation(_count: int):
        raise AssertionError("invalid target reached case generation")

    monkeypatch.setattr(
        test_static_hf_space_questions,
        "generate_random_test_cases",
        unexpected_generation,
    )
    monkeypatch.setattr(
        test_static_hf_space_questions,
        "REPORT_PATH",
        report_path,
    )

    with pytest.raises(ValueError, match="canonical HTTPS target"):
        test_static_hf_space_questions.run_randomized_ui_questions_test(
            1,
            ui_url=VERCEL_UI_URL,
            backend_url="https://retired.invalid",
            timeout=15,
        )

    assert not report_path.exists()


@pytest.mark.parametrize(
    ("diagnostic", "runner"),
    (
        (run_live_e2e_hf_space, run_live_e2e_hf_space.run_live_e2e),
        (audit_ui_overlap, audit_ui_overlap.run_live_audit),
    ),
    ids=("browser-e2e", "overlap-audit"),
)
def test_browser_runners_validate_targets_before_import_or_artifact_write(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    diagnostic: ModuleType,
    runner,
) -> None:
    poisoned_async_api = ModuleType("playwright.async_api")

    def unexpected_playwright_access():
        raise AssertionError("invalid target reached Playwright")

    poisoned_async_api.async_playwright = unexpected_playwright_access
    monkeypatch.setitem(sys.modules, "playwright.async_api", poisoned_async_api)
    if diagnostic is run_live_e2e_hf_space:
        monkeypatch.setattr(diagnostic, "SCREENSHOT_DIR", tmp_path / "screenshots")
        monkeypatch.setattr(diagnostic, "REPORT_PATH", tmp_path / "report.json")

    with pytest.raises(ValueError, match="canonical HTTPS target"):
        asyncio.run(
            runner(
                ui_url="https://retired.invalid",
                backend_url=HF_DOCKER_BACKEND_URL,
                timeout_seconds=15,
            )
        )

    assert list(tmp_path.iterdir()) == []


def test_http_runner_validates_targets_before_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_request(*_args, **_kwargs):
        raise AssertionError("invalid target reached HTTP I/O")

    monkeypatch.setattr(
        run_vercel_prod_curl_regression,
        "_do_request",
        unexpected_request,
    )

    with pytest.raises(ValueError, match="canonical HTTPS target"):
        run_vercel_prod_curl_regression.run_regression(
            "https://retired.invalid",
            15,
            0,
            backend_url=HF_DOCKER_BACKEND_URL,
        )


def test_question_live_opt_in_forwards_only_validated_bounded_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[dict] = []

    def fake_live_runner(count: int, **kwargs) -> dict:
        observed.append({"count": count, **kwargs})
        return {"failed_count": 0}

    diagnostic = test_static_hf_space_questions
    monkeypatch.setattr(
        diagnostic,
        "run_randomized_ui_questions_test",
        fake_live_runner,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [diagnostic.__file__, "--live", "--count", "2", "--timeout", "7"],
    )

    assert diagnostic.main() == 0
    assert observed == [
        {
            "count": 2,
            "ui_url": VERCEL_UI_URL,
            "backend_url": HF_DOCKER_BACKEND_URL,
            "timeout": 7,
        }
    ]


@pytest.mark.parametrize(
    ("diagnostic", "runner_name"),
    (
        (run_live_e2e_hf_space, "run_live_e2e"),
        (audit_ui_overlap, "run_live_audit"),
    ),
    ids=("browser-e2e", "overlap-audit"),
)
def test_browser_live_opt_in_forwards_only_validated_bounded_configuration(
    monkeypatch: pytest.MonkeyPatch,
    diagnostic: ModuleType,
    runner_name: str,
) -> None:
    observed: list[dict] = []

    async def fake_live_runner(**kwargs) -> bool:
        observed.append(kwargs)
        return True

    monkeypatch.setattr(diagnostic, runner_name, fake_live_runner)
    monkeypatch.setattr(
        sys,
        "argv",
        [diagnostic.__file__, "--live", "--timeout", "9"],
    )

    assert diagnostic.main() == 0
    assert observed == [
        {
            "ui_url": VERCEL_UI_URL,
            "backend_url": HF_DOCKER_BACKEND_URL,
            "timeout_seconds": 9,
        }
    ]


def test_http_live_opt_in_forwards_bounded_timeout_and_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[dict] = []

    def fake_live_runner(base_url: str, timeout: int, retries: int, **kwargs) -> int:
        observed.append(
            {
                "base_url": base_url,
                "timeout": timeout,
                "retries": retries,
                **kwargs,
            }
        )
        return 0

    diagnostic = run_vercel_prod_curl_regression
    monkeypatch.setattr(diagnostic, "run_regression", fake_live_runner)
    monkeypatch.setattr(
        sys,
        "argv",
        [diagnostic.__file__, "--live", "--timeout", "11", "--retries", "2"],
    )

    assert diagnostic.main() == 0
    assert observed == [
        {
            "base_url": VERCEL_UI_URL,
            "timeout": 11,
            "retries": 2,
            "backend_url": HF_DOCKER_BACKEND_URL,
        }
    ]


def test_question_network_failure_has_one_bounded_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed_timeouts: list[int] = []

    def fail_request(_request, *, timeout: int):
        observed_timeouts.append(timeout)
        raise urllib.error.URLError("PRIVATE_UPSTREAM_DETAIL")

    monkeypatch.setattr(
        test_static_hf_space_questions.urllib.request,
        "urlopen",
        fail_request,
    )

    ok, status, response = test_static_hf_space_questions.send_bazi_interpret_request(
        {"synthetic": True},
        timeout=13,
        ui_url=VERCEL_UI_URL,
    )

    assert observed_timeouts == [13]
    assert (ok, status, response) == (
        False,
        0,
        {"error_class": "NETWORK_ERROR"},
    )


def test_http_network_retries_are_bounded_and_sanitized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed_timeouts: list[int] = []

    def fail_request(_request, *, timeout: int):
        observed_timeouts.append(timeout)
        raise urllib.error.URLError("PRIVATE_UPSTREAM_DETAIL")

    monkeypatch.setattr(
        run_vercel_prod_curl_regression.urllib.request,
        "urlopen",
        fail_request,
    )

    result = run_vercel_prod_curl_regression._do_request(
        f"{VERCEL_UI_URL}/health",
        timeout_seconds=13,
        retries=2,
    )

    assert observed_timeouts == [13, 13, 13]
    assert result["error"] == "NETWORK_ERROR"
    assert result["body_text"] == ""
    assert "PRIVATE_UPSTREAM_DETAIL" not in json.dumps(result)


def test_question_report_is_ascii_and_redacts_interpretation_and_input_content(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    report_path = tmp_path / "questions-report.json"
    private_markers = (
        "PRIVATE_QUERY_MARKER",
        "PRIVATE_BIRTH_MARKER",
        "PRIVATE_LOCATION_MARKER",
        "PRIVATE_INTERPRETATION_MARKER",
    )
    case = {
        "case_id": "TEST-Q-01",
        "synthetic": True,
        "birth_datetime": private_markers[1],
        "location_name": private_markers[2],
        "longitude": 100.493,
        "utc_offset_hours": 7.0,
        "unknown_hour": False,
        "enable_validation": True,
        "domain": "CAREER",
        "category": "CAREER",
        "query": private_markers[0],
    }

    monkeypatch.setattr(
        test_static_hf_space_questions,
        "REPORT_PATH",
        report_path,
    )
    monkeypatch.setattr(
        test_static_hf_space_questions,
        "generate_random_test_cases",
        lambda count: [case] if count == 1 else [],
    )
    monkeypatch.setattr(
        test_static_hf_space_questions,
        "send_bazi_interpret_request",
        lambda *_args, **_kwargs: (
            True,
            200,
            {
                "chart": {
                    "day_master": {
                        "stem": "\u7532",
                        "element": "Wood",
                        "strength_status": "balanced",
                    }
                },
                "interpretation": private_markers[3],
                "validation_report": {"status": "present"},
                "rag_references": [{"id": "synthetic-reference"}],
            },
        ),
    )

    summary = test_static_hf_space_questions.run_randomized_ui_questions_test(
        1,
        ui_url=VERCEL_UI_URL,
        backend_url=HF_DOCKER_BACKEND_URL,
        timeout=15,
    )

    report_bytes = report_path.read_bytes()
    rendered = report_bytes.decode("ascii")
    assert report_bytes.isascii()
    assert summary["results"][0]["interpretation_snippet"] == "[REDACTED]"
    for marker in private_markers:
        assert marker not in rendered
        assert marker not in caplog.text


class _FakeLocator:
    async def count(self) -> int:
        return 0


class _FakePage:
    def __init__(self) -> None:
        self.current_url = ""
        self.visited_urls: list[str] = []
        self.content_requested = False

    def on(self, _event: str, _callback) -> None:
        return None

    def locator(self, _selector: str) -> _FakeLocator:
        return _FakeLocator()

    async def goto(self, url: str, **_kwargs):
        self.current_url = url
        self.visited_urls.append(url)
        return SimpleNamespace(status=200)

    async def screenshot(self, **_kwargs) -> None:
        return None

    async def fill(self, _selector: str, _value: str) -> None:
        return None

    async def click(self, _selector: str, **_kwargs) -> None:
        return None

    async def wait_for_function(self, _expression: str, **_kwargs) -> None:
        return None

    async def inner_text(self, _selector: str) -> str:
        return "PRIVATE_INTERPRETATION_CONTENT " + ("x" * 60)

    async def input_value(self, _selector: str) -> str:
        return "100.493"

    async def content(self) -> str:
        self.content_requested = True
        raise AssertionError("admin or HITL page content was requested")


class _FakeBrowser:
    def __init__(self, page: _FakePage) -> None:
        self.page = page

    async def new_context(self, **_kwargs):
        return _FakeContext(self.page)

    async def close(self) -> None:
        return None


class _FakeContext:
    def __init__(self, page: _FakePage) -> None:
        self.page = page

    async def new_page(self) -> _FakePage:
        return self.page


class _FakeChromium:
    def __init__(self, page: _FakePage) -> None:
        self.page = page

    async def launch(self, **_kwargs) -> _FakeBrowser:
        return _FakeBrowser(self.page)


class _FakePlaywrightContext:
    def __init__(self, page: _FakePage) -> None:
        self.page = page

    async def __aenter__(self):
        return SimpleNamespace(chromium=_FakeChromium(self.page))

    async def __aexit__(self, _exc_type, _exc, _traceback) -> None:
        return None


def test_e2e_report_is_ascii_and_never_records_admin_or_hitl_content(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    page = _FakePage()
    async_api = ModuleType("playwright.async_api")
    async_api.async_playwright = lambda: _FakePlaywrightContext(page)
    playwright = ModuleType("playwright")
    playwright.async_api = async_api
    monkeypatch.setitem(sys.modules, "playwright", playwright)
    monkeypatch.setitem(sys.modules, "playwright.async_api", async_api)
    monkeypatch.setattr(
        run_live_e2e_hf_space,
        "SCREENSHOT_DIR",
        tmp_path / "screenshots",
    )
    report_path = tmp_path / "e2e-report.json"
    monkeypatch.setattr(run_live_e2e_hf_space, "REPORT_PATH", report_path)

    passed = asyncio.run(
        run_live_e2e_hf_space.run_live_e2e(
            ui_url=VERCEL_UI_URL,
            backend_url=HF_DOCKER_BACKEND_URL,
            timeout_seconds=12,
        )
    )

    report_bytes = report_path.read_bytes()
    rendered = report_bytes.decode("ascii")
    report = json.loads(rendered)
    output = capsys.readouterr().out
    assert passed is True
    assert report_bytes.isascii()
    assert page.content_requested is False
    assert all(url.startswith(f"{VERCEL_UI_URL}/") for url in page.visited_urls)
    assert not any(HF_DOCKER_BACKEND_URL in url for url in page.visited_urls)
    assert "PRIVATE_INTERPRETATION_CONTENT" not in rendered
    assert "PRIVATE_INTERPRETATION_CONTENT" not in output
    assert report["results"][-2]["details"] == ("HTTP 200; content_not_recorded=true")
    assert report["results"][-1]["details"] == ("HTTP 200; content_not_recorded=true")


def test_http_diagnostic_does_not_print_response_content(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    private_marker = "PRIVATE_HTTP_RESPONSE_CONTENT"
    responses = iter(
        (
            {
                "status": 200,
                "headers": {
                    "access-control-allow-origin": VERCEL_UI_URL,
                    "x-deploy-sha": "synthetic-sha",
                },
                "body_text": "[REDACTED]",
                "body_json": {"status": "ok", "private": private_marker},
                "latency_ms": 1.0,
                "error": None,
            },
            {
                "status": 204,
                "headers": {
                    "access-control-allow-origin": VERCEL_UI_URL,
                    "access-control-allow-methods": "POST",
                },
                "body_text": "",
                "body_json": None,
                "latency_ms": 1.0,
                "error": None,
            },
            {
                "status": 200,
                "headers": {
                    "access-control-allow-origin": VERCEL_UI_URL,
                    "x-ai-source": "synthetic",
                    "x-ai-model": "synthetic",
                },
                "body_text": "[REDACTED]",
                "body_json": {
                    "chart": {},
                    "interpretation": private_marker,
                },
                "latency_ms": 1.0,
                "error": None,
            },
        )
    )
    observed_bounds: list[tuple[int, int]] = []

    def fake_request(*_args, timeout_seconds: int, retries: int, **_kwargs):
        observed_bounds.append((timeout_seconds, retries))
        return next(responses)

    monkeypatch.setattr(
        run_vercel_prod_curl_regression,
        "_do_request",
        fake_request,
    )

    assert (
        run_vercel_prod_curl_regression.run_regression(
            VERCEL_UI_URL,
            17,
            2,
            backend_url=HF_DOCKER_BACKEND_URL,
        )
        == 0
    )
    output = capsys.readouterr().out
    assert observed_bounds == [(17, 2), (17, 2), (17, 2)]
    assert output.isascii()
    assert private_marker not in output
