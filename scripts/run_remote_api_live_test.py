"""Read-only diagnostics for the canonical Hugging Face Docker backend.

Network execution is disabled by default and requires ``--live``. The live
mode sends only bounded HTTPS GET requests to the fixed backend health,
API-health, and version contracts. Results never contain response bodies,
redirect targets, request headers, exception text, or user data.
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
from typing import Any, Literal, TypedDict

CANONICAL_HF_DOCKER_BACKEND = "https://pphothidaen-horoconsultant-core-backend.hf.space"
DEFAULT_TIMEOUT_SECONDS = 5.0
MAX_TIMEOUT_SECONDS = 10.0
MAX_RESPONSE_BYTES = 65_536


class EndpointContract(TypedDict):
    """Closed definition for one read-only backend probe."""

    name: str
    url: str
    response_kind: Literal["json"]


class ProbeResult(TypedDict):
    """Sanitized outcome that excludes response and exception content."""

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
        "name": "backend_api_health",
        "url": f"{CANONICAL_HF_DOCKER_BACKEND}/api/v1/health",
        "response_kind": "json",
    },
    {
        "name": "backend_version",
        "url": f"{CANONICAL_HF_DOCKER_BACKEND}/version.json",
        "response_kind": "json",
    },
)

OpenRequest = Callable[
    [urllib.request.Request, float],
    AbstractContextManager[Any],
]


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    """Keep live requests bound to the exact approved backend origin."""

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
    """Return a printable ASCII representation for CLI output."""
    return str(value).encode("ascii", errors="backslashreplace").decode("ascii")


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


def _validate_contract(contract: EndpointContract) -> None:
    """Fail closed unless a probe is an exact canonical HTTPS GET target."""
    if set(contract) != {"name", "url", "response_kind"}:
        raise ValueError("probe contract is not closed")
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
        raise ValueError("probe contract is outside the canonical backend allowlist")


def _open_read_only(
    request: urllib.request.Request,
    timeout: float,
) -> AbstractContextManager[Any]:
    """Open one direct GET without ambient proxies or redirects."""
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        _RejectRedirects(),
    )
    return opener.open(request, timeout=timeout)


def _failed_result(
    name: str,
    classification: Literal[
        "HTTP_ERROR", "TIMEOUT", "NETWORK_ERROR", "INVALID_RESPONSE"
    ],
    started: float,
    clock: Callable[[], float],
    http_status: int = 0,
) -> ProbeResult:
    """Build a sanitized failure result."""
    return {
        "name": name,
        "outcome": "FAILED",
        "classification": classification,
        "http_status": http_status,
        "latency_ms": round(max(0.0, (clock() - started) * 1000), 2),
        "response_bytes": 0,
    }


def probe_endpoint(
    contract: EndpointContract,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    open_request: OpenRequest | None = None,
    clock: Callable[[], float] = time.perf_counter,
) -> ProbeResult:
    """Execute one bounded GET and retain only sanitized outcome metadata."""
    _validate_contract(contract)
    if not 0.1 <= timeout <= MAX_TIMEOUT_SECONDS:
        raise ValueError("timeout is outside the safe diagnostic range")

    request = urllib.request.Request(
        contract["url"],
        headers={
            "Accept": "application/json",
            "User-Agent": "HoroConsultant-ReadOnly-Diagnostic/1.0",
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

    if status != 200 or not isinstance(body, bytes) or len(body) > MAX_RESPONSE_BYTES:
        return _failed_result(
            contract["name"],
            "INVALID_RESPONSE",
            started,
            clock,
            http_status=status,
        )
    try:
        decoded = body.decode("utf-8")
        parsed = json.loads(decoded)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _failed_result(
            contract["name"],
            "INVALID_RESPONSE",
            started,
            clock,
            http_status=status,
        )
    if not isinstance(parsed, dict):
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


def run_diagnostics(
    *,
    live: bool = False,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    open_request: OpenRequest | None = None,
) -> list[ProbeResult]:
    """Run the fixed read-only matrix; default mode performs no I/O."""
    if not live:
        for contract in READ_ONLY_ENDPOINTS:
            _validate_contract(contract)
        return []
    return [
        probe_endpoint(
            contract,
            timeout=timeout,
            open_request=open_request,
        )
        for contract in READ_ONLY_ENDPOINTS
    ]


def build_cli_parser() -> argparse.ArgumentParser:
    """Build the side-effect-free CLI parser."""
    parser = argparse.ArgumentParser(
        prog="run_remote_api_live_test.py",
        description="Read-only canonical HF Docker backend diagnostics.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--live",
        action="store_true",
        help="Opt in to bounded read-only HTTPS GET probes.",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the fixed probe plan without network access (default).",
    )
    parser.add_argument(
        "--timeout",
        type=_timeout_value,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Per-request timeout from 0.1 through 10 seconds.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print sanitized JSON evidence.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run a dry plan or the explicitly opted-in GET matrix."""
    args = build_cli_parser().parse_args(argv)
    if not args.live:
        plan = {
            "mode": "DRY_RUN",
            "target": CANONICAL_HF_DOCKER_BACKEND,
            "method": "GET",
            "network_requests": 0,
            "endpoints": [contract["name"] for contract in READ_ONLY_ENDPOINTS],
            "timeout_seconds": args.timeout,
        }
        if args.json:
            print(json.dumps(plan, sort_keys=True))
        else:
            print("[INFO] mode=DRY_RUN target=" + CANONICAL_HF_DOCKER_BACKEND)
            print("[INFO] method=GET network_requests=0")
            print("[OK] read-only diagnostic plan validated")
        return 0

    results = run_diagnostics(live=True, timeout=args.timeout)
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
        print("[INFO] mode=LIVE_READ_ONLY target=" + CANONICAL_HF_DOCKER_BACKEND)
        for result in results:
            tag = "[OK]" if result["outcome"] == "PASSED" else "[ERROR]"
            print(
                f"{tag} probe={_ascii_text(result['name'])} "
                f"status={result['http_status']} "
                f"class={result['classification']} "
                f"latency_ms={result['latency_ms']:.2f}"
            )
    return 0 if results and all(item["outcome"] == "PASSED" for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
