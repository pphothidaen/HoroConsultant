"""Bounded read-only network audit for the canonical HF Docker backend.

The default invocation is a dry run. ``--live`` is the only network opt-in,
and even live mode permits only fixed HTTPS GET contracts. Requests contain no
user data, and results expose no response or exception text.
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
READ_ONLY_URLS: tuple[tuple[str, str], ...] = (
    ("backend_health", f"{CANONICAL_HF_DOCKER_BACKEND}/health"),
    ("backend_api_health", f"{CANONICAL_HF_DOCKER_BACKEND}/api/v1/health"),
    ("backend_version", f"{CANONICAL_HF_DOCKER_BACKEND}/version.json"),
)


class NetworkResult(TypedDict):
    """Sanitized result for one fixed read-only request."""

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


OpenRequest = Callable[
    [urllib.request.Request, float],
    AbstractContextManager[Any],
]


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    """Prevent a fixed backend probe from leaving its approved origin."""

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
    """Return printable ASCII without leaking arbitrary Unicode text."""
    return str(value).encode("ascii", errors="backslashreplace").decode("ascii")


def _timeout_value(value: str) -> float:
    """Parse a bounded timeout for the live opt-in."""
    try:
        timeout = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timeout must be numeric") from exc
    if not 0.1 <= timeout <= MAX_TIMEOUT_SECONDS:
        raise argparse.ArgumentTypeError(
            f"timeout must be between 0.1 and {MAX_TIMEOUT_SECONDS:.1f} seconds"
        )
    return timeout


def _allowed_url_names() -> dict[str, str]:
    """Return the immutable logical-name mapping for the read-only matrix."""
    return {url: name for name, url in READ_ONLY_URLS}


def _validate_url(url: str) -> str:
    """Return the logical probe name or fail closed on a noncanonical URL."""
    parsed_base = urllib.parse.urlsplit(CANONICAL_HF_DOCKER_BACKEND)
    parsed_url = urllib.parse.urlsplit(url)
    name = _allowed_url_names().get(url)
    if (
        name is None
        or parsed_url.scheme != "https"
        or parsed_url.netloc != parsed_base.netloc
        or parsed_url.username is not None
        or parsed_url.password is not None
        or parsed_url.port not in (None, 443)
        or parsed_url.query
        or parsed_url.fragment
    ):
        raise ValueError("network diagnostic URL is outside the fixed allowlist")
    return name


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


def _failure(
    name: str,
    classification: Literal[
        "HTTP_ERROR", "TIMEOUT", "NETWORK_ERROR", "INVALID_RESPONSE"
    ],
    started: float,
    clock: Callable[[], float],
    *,
    status: int = 0,
) -> NetworkResult:
    """Create one sanitized failure without raw provider data."""
    return {
        "name": name,
        "outcome": "FAILED",
        "classification": classification,
        "http_status": status,
        "latency_ms": round(max(0.0, (clock() - started) * 1000), 2),
        "response_bytes": 0,
    }


def execute_network_request(
    url: str,
    method: str = "GET",
    *,
    expected_status: int = 200,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    open_request: OpenRequest | None = None,
    clock: Callable[[], float] = time.perf_counter,
) -> NetworkResult:
    """Execute one canonical GET; every other method or URL is rejected."""
    name = _validate_url(url)
    if method != "GET":
        raise ValueError("only GET is allowed by the read-only diagnostic contract")
    if expected_status != 200:
        raise ValueError("only the HTTP 200 endpoint contract is supported")
    if not 0.1 <= timeout <= MAX_TIMEOUT_SECONDS:
        raise ValueError("timeout is outside the safe diagnostic range")

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "HoroConsultant-ReadOnly-Network-Audit/1.0",
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
        return _failure(
            name,
            "HTTP_ERROR",
            started,
            clock,
            status=int(exc.code),
        )
    except TimeoutError:
        return _failure(name, "TIMEOUT", started, clock)
    except (OSError, urllib.error.URLError):
        return _failure(name, "NETWORK_ERROR", started, clock)
    except Exception:  # noqa: BLE001 - elide provider/adapter exception text.
        return _failure(name, "NETWORK_ERROR", started, clock)

    if status != expected_status or not isinstance(body, bytes):
        return _failure(
            name,
            "INVALID_RESPONSE",
            started,
            clock,
            status=status,
        )
    if not body or len(body) > MAX_RESPONSE_BYTES:
        return _failure(
            name,
            "INVALID_RESPONSE",
            started,
            clock,
            status=status,
        )
    try:
        parsed_body = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _failure(
            name,
            "INVALID_RESPONSE",
            started,
            clock,
            status=status,
        )
    if not isinstance(parsed_body, dict):
        return _failure(
            name,
            "INVALID_RESPONSE",
            started,
            clock,
            status=status,
        )
    return {
        "name": name,
        "outcome": "PASSED",
        "classification": "OK",
        "http_status": status,
        "latency_ms": round(max(0.0, (clock() - started) * 1000), 2),
        "response_bytes": len(body),
    }


def run_strict_live_e2e_audit(
    *,
    live: bool = False,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    open_request: OpenRequest | None = None,
) -> bool:
    """Validate the plan, or run it only when explicit live opt-in is true."""
    if not live:
        for _, url in READ_ONLY_URLS:
            _validate_url(url)
        return True
    results = [
        execute_network_request(
            url,
            timeout=timeout,
            open_request=open_request,
        )
        for _, url in READ_ONLY_URLS
    ]
    return bool(results) and all(result["outcome"] == "PASSED" for result in results)


def build_cli_parser() -> argparse.ArgumentParser:
    """Build CLI arguments without network or environment access."""
    parser = argparse.ArgumentParser(
        prog="test_live_e2e_network.py",
        description="Read-only canonical HF Docker backend network audit.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--live",
        action="store_true",
        help="Opt in to the fixed HTTPS GET matrix.",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the matrix without requests (default).",
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
        help="Print a sanitized plan or result summary.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run dry by default; live mode remains bounded to the fixed matrix."""
    args = build_cli_parser().parse_args(argv)
    if not args.live:
        run_strict_live_e2e_audit(live=False, timeout=args.timeout)
        evidence = {
            "mode": "DRY_RUN",
            "target": CANONICAL_HF_DOCKER_BACKEND,
            "method": "GET",
            "network_requests": 0,
            "probes": [name for name, _ in READ_ONLY_URLS],
        }
        if args.json:
            print(json.dumps(evidence, sort_keys=True))
        else:
            print("[INFO] mode=DRY_RUN target=" + CANONICAL_HF_DOCKER_BACKEND)
            print("[INFO] method=GET network_requests=0")
            print("[OK] strict read-only network plan validated")
        return 0

    results = [
        execute_network_request(url, timeout=args.timeout) for _, url in READ_ONLY_URLS
    ]
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
        print("[INFO] mode=LIVE_READ_ONLY target=" + CANONICAL_HF_DOCKER_BACKEND)
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
