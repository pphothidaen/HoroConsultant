"""Read-only randomized question diagnostics for the production web pair.

The public UI is hosted on Vercel. Requests to its same-origin ``/api`` route
are forwarded to the separately identified Hugging Face Docker backend. The
legacy filename is retained for compatibility; it does not select a release
target.

The command is offline by default. ``--live`` is required before any network
request or report write can occur.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "project" / "tests" / "randomized_static_questions_report.json"

CANONICAL_VERCEL_UI_URL = "https://horo-consultant-psi.vercel.app"
CANONICAL_HF_DOCKER_BACKEND_URL = (
    "https://pphothidaen-horoconsultant-core-backend.hf.space"
)
DEFAULT_TIMEOUT_SECONDS = 15

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("ui_question_diagnostics")

QUESTION_TEMPLATES = [
    {
        "domain": "CAREER",
        "questions": [
            "Analyze career direction, suitable work, and the timing of a job change.",
            "Compare entrepreneurship with public-sector work for this BaZi chart.",
        ],
    },
    {
        "domain": "WEALTH",
        "questions": [
            "Analyze the wealth element, investment timing, and saving strategy.",
            "Explain the wealth vaults in this four-pillars chart.",
        ],
    },
    {
        "domain": "LOVE",
        "questions": [
            "Analyze the spouse palace, relationship pattern, and partner timing.",
            "Explain peach-blossom indicators in this chart.",
        ],
    },
    {
        "domain": "HEALTH",
        "questions": [
            "Analyze five-element balance and general wellness tendencies.",
            "Suggest practical ways to balance the chart through daily habits.",
        ],
    },
    {
        "domain": "DOS",
        "questions": [
            "Identify helpful elements, directions, and practical daily actions.",
        ],
    },
    {
        "domain": "DONTS",
        "questions": [
            "Identify unfavorable patterns and practical actions to avoid.",
        ],
    },
    {
        "domain": "FENGSHUI",
        "questions": [
            "Analyze favorable directions and Period 9 home-office placement.",
        ],
    },
]

SYNTHETIC_LOCATIONS = [
    {"city": "Bangkok", "longitude": 100.4930, "utc_offset_hours": 7.0},
    {"city": "Chiang Mai", "longitude": 98.9853, "utc_offset_hours": 7.0},
    {"city": "Phuket", "longitude": 98.3923, "utc_offset_hours": 7.0},
    {"city": "Singapore", "longitude": 103.8198, "utc_offset_hours": 8.0},
    {"city": "Tokyo", "longitude": 139.6917, "utc_offset_hours": 9.0},
    {"city": "New York", "longitude": -74.0060, "utc_offset_hours": -5.0},
    {"city": "London", "longitude": -0.1276, "utc_offset_hours": 0.0},
]


def _require_canonical_https_url(value: str, expected: str, label: str) -> str:
    """Return the canonical base URL or fail closed before network access."""
    candidate = value.strip().rstrip("/")
    parsed = urlsplit(candidate)
    if (
        candidate != expected
        or parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(f"{label} must be the canonical HTTPS target")
    return candidate


def generate_random_test_cases(count: int = 10) -> list[dict]:
    """Generate synthetic birth inputs and questions across seven domains."""
    cases: list[dict] = []
    start_date = datetime(1965, 1, 1, tzinfo=timezone.utc)
    days_range = (datetime(2005, 12, 31, tzinfo=timezone.utc) - start_date).days

    for index in range(1, count + 1):
        birth = start_date + timedelta(
            days=random.randint(0, days_range),
            hours=random.choice([0, 2, 5, 8, 11, 14, 17, 20, 23]),
            minutes=random.choice([0, 15, 30, 45]),
        )
        location = random.choice(SYNTHETIC_LOCATIONS)
        domain = random.choice(QUESTION_TEMPLATES)
        cases.append(
            {
                "case_id": f"TEST-Q-{index:02d}",
                "synthetic": True,
                "birth_datetime": birth.strftime("%Y-%m-%d %H:%M:%S"),
                "location_name": location["city"],
                "longitude": location["longitude"],
                "utc_offset_hours": location["utc_offset_hours"],
                "unknown_hour": False,
                "enable_validation": True,
                "domain": domain["domain"],
                "category": domain["domain"],
                "query": random.choice(domain["questions"]),
            }
        )
    return cases


def send_bazi_interpret_request(
    payload: dict,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    *,
    ui_url: str = CANONICAL_VERCEL_UI_URL,
) -> tuple[bool, int, dict]:
    """Send one read-only diagnostic request through the Vercel UI gateway."""
    ui_url = _require_canonical_https_url(ui_url, CANONICAL_VERCEL_UI_URL, "UI URL")
    if not 1 <= timeout <= 60:
        raise ValueError("timeout must be between 1 and 60 seconds")
    endpoint = f"{ui_url}/api/v1/bazi/interpret"
    headers = {
        "User-Agent": "HoroConsultant-UI-Diagnostics/1.0",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": ui_url,
        "Referer": f"{ui_url}/",
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=True).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            try:
                decoded = json.loads(body)
            except json.JSONDecodeError:
                return False, response.status, {"error_class": "INVALID_JSON"}
            return response.status == 200, response.status, decoded
    except urllib.error.HTTPError as exc:
        return False, exc.code, {"error_class": "HTTP_ERROR"}
    except (OSError, TimeoutError, urllib.error.URLError):
        return False, 0, {"error_class": "NETWORK_ERROR"}


def run_randomized_ui_questions_test(
    count: int,
    *,
    ui_url: str,
    backend_url: str,
    timeout: int,
) -> dict:
    """Run live synthetic queries and preserve the existing report location."""
    ui_url = _require_canonical_https_url(ui_url, CANONICAL_VERCEL_UI_URL, "UI URL")
    backend_url = _require_canonical_https_url(
        backend_url,
        CANONICAL_HF_DOCKER_BACKEND_URL,
        "Backend URL",
    )
    if not 1 <= count <= 100:
        raise ValueError("count must be between 1 and 100")
    if not 1 <= timeout <= 60:
        raise ValueError("timeout must be between 1 and 60 seconds")
    log.info("[INFO] Vercel UI randomized question diagnostics")
    log.info("[INFO] UI target: %s", ui_url)
    log.info("[INFO] Backend target: %s", backend_url)

    results: list[dict] = []
    passed_count = 0
    for case in generate_random_test_cases(count):
        started = time.monotonic()
        ok, status_code, response = send_bazi_interpret_request(
            case, timeout=timeout, ui_url=ui_url
        )
        latency_ms = round((time.monotonic() - started) * 1000, 2)

        chart = response.get("chart")
        chart_present = isinstance(chart, dict)
        interpretation_present = bool(
            response.get("interpretation") or response.get("text")
        )
        validation_present = (
            "validation_report" in response or "validation_status" in response
        )
        rag_present = "rag_references" in response or "canonical_citations" in response
        passed = ok and chart_present and interpretation_present
        passed_count += int(passed)

        day_master = chart.get("day_master", {}) if chart_present else {}
        results.append(
            {
                "case_id": case["case_id"],
                "domain": case["domain"],
                "category": case["category"],
                "input": {"synthetic": True, "domain": case["domain"]},
                "latency_ms": latency_ms,
                "status": "PASSED" if passed else "FAILED",
                "http_status": status_code,
                "day_master": {
                    "stem": day_master.get("stem", "-"),
                    "element": day_master.get("element", "-"),
                    "strength": day_master.get("strength_status", "-"),
                },
                "chart_present": chart_present,
                "validation_present": validation_present,
                "rag_present": rag_present,
                "interpretation_snippet": (
                    "[REDACTED]" if interpretation_present else ""
                ),
                "validator_status": ("PRESENT" if validation_present else "MISSING"),
                "rag_citations_count": (
                    len(response.get("rag_references", []))
                    if isinstance(response.get("rag_references"), list)
                    else 0
                ),
            }
        )
        tag = "[OK]" if passed else "[ERROR]"
        log.info(
            "%s Case %s domain=%s http=%d latency_ms=%.2f",
            tag,
            case["case_id"],
            case["domain"],
            status_code,
            latency_ms,
        )

    summary = {
        "target_url": f"{ui_url}/",
        "ui_url": ui_url,
        "backend_url": backend_url,
        "test_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_cases": count,
        "passed_count": passed_count,
        "failed_count": count - passed_count,
        "pass_rate_percent": round((passed_count / count) * 100, 2),
        "results": results,
    }
    REPORT_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=True), encoding="utf-8"
    )
    log.info("[INFO] Report saved: project/tests/%s", REPORT_PATH.name)
    return summary


def run_randomized_static_questions_test(
    count: int = 10, *, live: bool = False
) -> dict:
    """Compatibility wrapper that remains offline unless ``live`` is explicit."""
    if not live:
        return {
            "mode": "dry-run",
            "target_url": f"{CANONICAL_VERCEL_UI_URL}/",
            "ui_url": CANONICAL_VERCEL_UI_URL,
            "backend_url": CANONICAL_HF_DOCKER_BACKEND_URL,
            "total_cases": count,
            "passed_count": 0,
            "failed_count": 0,
            "results": [],
        }
    return run_randomized_ui_questions_test(
        count,
        ui_url=CANONICAL_VERCEL_UI_URL,
        backend_url=CANONICAL_HF_DOCKER_BACKEND_URL,
        timeout=DEFAULT_TIMEOUT_SECONDS,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only Vercel UI randomized question diagnostics"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--live", action="store_true", help="Enable live read-only requests"
    )
    mode.add_argument(
        "--dry-run", action="store_true", help="Validate the offline plan"
    )
    parser.add_argument("--ui-url", default=CANONICAL_VERCEL_UI_URL)
    parser.add_argument("--backend-url", default=CANONICAL_HF_DOCKER_BACKEND_URL)
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--seed", type=int, default=41)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        ui_url = _require_canonical_https_url(
            args.ui_url, CANONICAL_VERCEL_UI_URL, "UI URL"
        )
        backend_url = _require_canonical_https_url(
            args.backend_url,
            CANONICAL_HF_DOCKER_BACKEND_URL,
            "Backend URL",
        )
        if not 1 <= args.count <= 100:
            raise ValueError("count must be between 1 and 100")
        if not 1 <= args.timeout <= 60:
            raise ValueError("timeout must be between 1 and 60 seconds")
    except ValueError as exc:
        log.error("[ERROR] Invalid diagnostic configuration: %s", exc)
        return 2

    random.seed(args.seed)
    if not args.live:
        log.info("[INFO] Offline dry run; no network or artifact write")
        log.info("[INFO] UI target: %s", ui_url)
        log.info("[INFO] Backend target: %s", backend_url)
        log.info("[OK] Planned synthetic cases: %d", args.count)
        return 0

    summary = run_randomized_ui_questions_test(
        args.count,
        ui_url=ui_url,
        backend_url=backend_url,
        timeout=args.timeout,
    )
    return 0 if summary["failed_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
