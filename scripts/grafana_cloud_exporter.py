"""Read-only backend observability diagnostic with a legacy filename.

The tool validates offline dashboard JSON and probes only the canonical Hugging
Face Docker backend health and metrics endpoints. Network access requires the
explicit ``--live`` flag. The implementation contains no remote write path,
request-identity handling, local-service fallback, response dump, or implicit
environment loading.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Sequence
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any, Literal, TypedDict

CANONICAL_HF_DOCKER_BACKEND = "https://pphothidaen-horoconsultant-core-backend.hf.space"
DEFAULT_TIMEOUT_SECONDS = 5.0
MAX_TIMEOUT_SECONDS = 10.0
MAX_RESPONSE_BYTES = 262_144


class EndpointContract(TypedDict):
    """Fixed read-only endpoint definition."""

    name: str
    url: str
    response_kind: Literal["json", "prometheus"]


class DiagnosticResult(TypedDict):
    """Sanitized probe evidence without response or exception text."""

    name: str
    outcome: Literal["PASSED", "FAILED"]
    classification: Literal[
        "OK",
        "HTTP_ERROR",
        "TIMEOUT",
        "NETWORK_ERROR",
        "INVALID_RESPONSE",
    ]
    http_status: int
    latency_ms: float
    response_bytes: int


READ_ONLY_ENDPOINTS: tuple[EndpointContract, ...] = (
    {
        "name": "backend_health",
        "url": f"{CANONICAL_HF_DOCKER_BACKEND}/health",
        "response_kind": "json",
    },
    {
        "name": "backend_metrics",
        "url": f"{CANONICAL_HF_DOCKER_BACKEND}/metrics",
        "response_kind": "prometheus",
    },
)

OpenRequest = Callable[
    [urllib.request.Request, float],
    AbstractContextManager[Any],
]


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    """Prevent observability probes from leaving the canonical origin."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


def _ascii_text(value: object) -> str:
    """Return printable ASCII for all diagnostic output."""
    return str(value).encode("ascii", errors="backslashreplace").decode("ascii")


def log_info(message: str) -> None:
    """Write one sanitized informational line."""
    print(f"[INFO] {_ascii_text(message)}")


def log_ok(message: str) -> None:
    """Write one sanitized success line."""
    print(f"[OK] {_ascii_text(message)}")


def log_error(message: str) -> None:
    """Write one sanitized error line."""
    print(f"[ERROR] {_ascii_text(message)}")


def _timeout_value(value: str) -> float:
    """Parse a bounded positive network timeout."""
    try:
        timeout = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timeout must be numeric") from exc
    if not 0.1 <= timeout <= MAX_TIMEOUT_SECONDS:
        raise argparse.ArgumentTypeError(
            f"timeout must be between 0.1 and {MAX_TIMEOUT_SECONDS:.1f} seconds"
        )
    return timeout


def load_dashboard_schema(dashboard_path: str | Path) -> dict[str, Any]:
    """Read one caller-selected dashboard JSON file without logging its path."""
    path = Path(dashboard_path)
    if not path.is_file():
        raise FileNotFoundError("dashboard JSON file was not found")
    with path.open("r", encoding="utf-8") as stream:
        data = json.load(stream)
    if not isinstance(data, dict):
        raise TypeError("dashboard JSON root must be an object")
    return data


def format_grafana_payload(
    dashboard: dict[str, Any],
    overwrite: bool = True,
    folder_uid: str = "",
) -> dict[str, Any]:
    """Format dashboard JSON in memory; this function performs no I/O."""
    dashboard_copy = dict(dashboard)
    dashboard_copy["id"] = None
    return {
        "dashboard": dashboard_copy,
        "overwrite": overwrite,
        "folderUid": folder_uid,
        "message": "Validated by HoroConsultant read-only exporter",
    }


def export_dashboard_to_grafana(
    dashboard_path: str | Path,
    *,
    dry_run: bool = True,
    overwrite: bool = True,
    folder_uid: str = "",
    **_legacy_options: object,
) -> dict[str, Any]:
    """Compatibility wrapper that validates only and never exports remotely."""
    dashboard = load_dashboard_schema(dashboard_path)
    payload = format_grafana_payload(
        dashboard,
        overwrite=overwrite,
        folder_uid=folder_uid,
    )
    if dry_run:
        return {
            "status": "dry_run",
            "message": "Dashboard JSON validated successfully in read-only mode",
            "payload": payload,
        }
    return {
        "status": "mutation_disabled",
        "message": "Remote dashboard mutation is disabled",
        "payload": payload,
    }


def _validate_contract(contract: EndpointContract) -> None:
    """Require one exact canonical HTTPS endpoint."""
    if set(contract) != {"name", "url", "response_kind"}:
        raise ValueError("observability endpoint contract is not closed")
    parsed_base = urllib.parse.urlsplit(CANONICAL_HF_DOCKER_BACKEND)
    parsed_url = urllib.parse.urlsplit(contract["url"])
    allowed_contracts = {
        (endpoint["name"], endpoint["url"], endpoint["response_kind"])
        for endpoint in READ_ONLY_ENDPOINTS
    }
    if (
        (
            contract["name"],
            contract["url"],
            contract["response_kind"],
        )
        not in allowed_contracts
        or parsed_url.scheme != "https"
        or parsed_url.netloc != parsed_base.netloc
        or parsed_url.username is not None
        or parsed_url.password is not None
        or parsed_url.port not in (None, 443)
        or parsed_url.query
        or parsed_url.fragment
    ):
        raise ValueError("observability endpoint is outside the fixed allowlist")


def _open_read_only(
    request: urllib.request.Request,
    timeout: float,
) -> AbstractContextManager[Any]:
    """Open one direct GET without ambient proxies or redirects."""
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        _RejectRedirects(),
    ).open(
        request,
        timeout=timeout,
    )


def _failed_result(
    name: str,
    classification: Literal[
        "HTTP_ERROR", "TIMEOUT", "NETWORK_ERROR", "INVALID_RESPONSE"
    ],
    started: float,
    clock: Callable[[], float],
    *,
    http_status: int = 0,
) -> DiagnosticResult:
    """Build sanitized failure evidence."""
    return {
        "name": name,
        "outcome": "FAILED",
        "classification": classification,
        "http_status": http_status,
        "latency_ms": round(max(0.0, (clock() - started) * 1000), 2),
        "response_bytes": 0,
    }


def _valid_response_body(contract: EndpointContract, body: bytes) -> bool:
    """Validate bounded response structure without retaining or returning it."""
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        return False
    if contract["response_kind"] == "json":
        try:
            return isinstance(json.loads(text), dict)
        except json.JSONDecodeError:
            return False
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return bool(lines) and "\x00" not in text


def probe_observability_endpoint(
    contract: EndpointContract,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    open_request: OpenRequest | None = None,
    clock: Callable[[], float] = time.perf_counter,
) -> DiagnosticResult:
    """Probe one fixed endpoint with a bounded body and sanitized result."""
    _validate_contract(contract)
    if not 0.1 <= timeout <= MAX_TIMEOUT_SECONDS:
        raise ValueError("timeout is outside the safe diagnostic range")
    accept = "application/json" if contract["response_kind"] == "json" else "text/plain"
    request = urllib.request.Request(
        contract["url"],
        headers={
            "Accept": accept,
            "User-Agent": "HoroConsultant-ReadOnly-Observability/1.0",
        },
        method="GET",
    )
    started = clock()
    opener = open_request or _open_read_only
    try:
        with opener(request, timeout) as response:
            status = int(getattr(response, "status", 0))
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        return _failed_result(
            contract["name"],
            "HTTP_ERROR",
            started,
            clock,
            http_status=int(exc.code),
        )
    except TimeoutError:
        return _failed_result(contract["name"], "TIMEOUT", started, clock)
    except (OSError, urllib.error.URLError):
        return _failed_result(contract["name"], "NETWORK_ERROR", started, clock)
    except Exception:  # noqa: BLE001 - elide provider/adapter exception text.
        return _failed_result(contract["name"], "NETWORK_ERROR", started, clock)

    if (
        status != 200
        or not isinstance(body, bytes)
        or not body
        or len(body) > MAX_RESPONSE_BYTES
        or not _valid_response_body(contract, body)
    ):
        return _failed_result(
            contract["name"],
            "INVALID_RESPONSE",
            started,
            clock,
            http_status=status,
        )
    return {
        "name": contract["name"],
        "outcome": "PASSED",
        "classification": "OK",
        "http_status": status,
        "latency_ms": round(max(0.0, (clock() - started) * 1000), 2),
        "response_bytes": len(body),
    }


def run_read_only_diagnostics(
    *,
    live: bool = False,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    open_request: OpenRequest | None = None,
) -> list[DiagnosticResult]:
    """Run no requests by default; live mode executes the fixed GET matrix."""
    if not live:
        for contract in READ_ONLY_ENDPOINTS:
            _validate_contract(contract)
        return []
    return [
        probe_observability_endpoint(
            contract,
            timeout=timeout,
            open_request=open_request,
        )
        for contract in READ_ONLY_ENDPOINTS
    ]


def build_cli_parser() -> argparse.ArgumentParser:
    """Build arguments without reading environment state."""
    parser = argparse.ArgumentParser(
        prog="grafana_cloud_exporter.py",
        description="Read-only canonical HF Docker observability diagnostics.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--live",
        action="store_true",
        help="Opt in to bounded backend HTTPS GET probes.",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the plan without network access (default).",
    )
    parser.add_argument(
        "--check-connection",
        action="store_true",
        help="Retained alias for the read-only diagnostic plan.",
    )
    parser.add_argument(
        "--timeout",
        type=_timeout_value,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Per-request timeout from 0.1 through 10 seconds.",
    )
    parser.add_argument(
        "--export-dashboard",
        action="store_true",
        help="Validate a local dashboard JSON file without remote export.",
    )
    parser.add_argument(
        "--dashboard-path",
        help="Caller-selected dashboard JSON input for offline validation.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print sanitized JSON evidence.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Validate offline by default or run the explicit live GET matrix."""
    args = build_cli_parser().parse_args(argv)
    dashboard_status: str | None = None
    if args.export_dashboard:
        if not args.dashboard_path:
            log_error("dashboard input is required for offline validation")
            return 2
        try:
            dashboard_result = export_dashboard_to_grafana(
                args.dashboard_path,
                dry_run=True,
            )
        except Exception:  # noqa: BLE001 - elide parser/filesystem details.
            log_error("dashboard JSON validation failed")
            return 1
        dashboard_status = str(dashboard_result["status"])

    if not args.live:
        run_read_only_diagnostics(live=False, timeout=args.timeout)
        evidence: dict[str, Any] = {
            "mode": "DRY_RUN",
            "target": CANONICAL_HF_DOCKER_BACKEND,
            "method": "GET",
            "network_requests": 0,
            "probes": [contract["name"] for contract in READ_ONLY_ENDPOINTS],
        }
        if dashboard_status is not None:
            evidence["dashboard"] = dashboard_status
        if args.json:
            print(json.dumps(evidence, sort_keys=True))
        else:
            log_info("mode=DRY_RUN target=" + CANONICAL_HF_DOCKER_BACKEND)
            log_info("method=GET network_requests=0")
            if dashboard_status is not None:
                log_ok("dashboard JSON validated in read-only mode")
            log_ok("observability diagnostic plan validated")
        return 0

    results = run_read_only_diagnostics(live=True, timeout=args.timeout)
    passed = bool(results) and all(item["outcome"] == "PASSED" for item in results)
    if args.json:
        print(
            json.dumps(
                {
                    "method": "GET",
                    "mode": "LIVE_READ_ONLY",
                    "network_requests": len(results),
                    "results": results,
                    "target": CANONICAL_HF_DOCKER_BACKEND,
                },
                sort_keys=True,
            )
        )
    else:
        log_info("mode=LIVE_READ_ONLY target=" + CANONICAL_HF_DOCKER_BACKEND)
        for result in results:
            tag = "[OK]" if result["outcome"] == "PASSED" else "[ERROR]"
            print(
                f"{tag} probe={_ascii_text(result['name'])} "
                f"status={result['http_status']} "
                f"class={result['classification']} "
                f"latency_ms={result['latency_ms']:.2f}"
            )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
