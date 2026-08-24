"""Run the Horo v3.0 synthetic consultation acceptance suite.

The runner uses the public FastAPI contract in-process, which keeps the test
deterministic while still exercising the complete v3 calculation pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

from fastapi.testclient import TestClient

# Make ``python3 scripts/run_v3_e2e_consultation.py`` behave like a module
# invocation from the repository root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from project.main import app


MANDATORY_DISCLAIMER_MARKER = "Predictive Validity is Explicitly Disclaimed"
REPORT_PATH = PROJECT_ROOT / "project" / "tests" / "v3_e2e_consultation_report.json"

PROFILES: tuple[dict[str, Any], ...] = (
    {
        "id": "A",
        "name": "Tech Startup Timing",
        "intent": "STRATEGIC_TIMING_ACTION",
        "birth_datetime": "1992-03-15T12:00:00",
        "city": "Bangkok",
        "latitude": 13.7563,
        "longitude": 100.5018,
        "tz_offset": 7.0,
    },
    {
        "id": "B",
        "name": "Real Estate Investment",
        "intent": "RISK_MITIGATION",
        "birth_datetime": "1985-08-20T12:00:00",
        "city": "Singapore",
        "latitude": 1.3521,
        "longitude": 103.8198,
        "tz_offset": 8.0,
    },
    {
        "id": "C",
        "name": "Career & Relocation",
        "intent": "SPIRITUAL_ALIGNMENT",
        "birth_datetime": "1998-11-05T12:00:00",
        "city": "Tokyo",
        "latitude": 35.6762,
        "longitude": 139.6503,
        "tz_offset": 9.0,
    },
    {
        "id": "D",
        "name": "Partnership & Marriage",
        "intent": "RELATIONSHIP_SYNASTRY",
        "birth_datetime": "1990-06-12T12:00:00",
        "city": "London",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "tz_offset": 0.0,
    },
    {
        "id": "E",
        "name": "Health & Longevity",
        "intent": "HOLISTIC_WELLNESS",
        "birth_datetime": "1978-01-30T12:00:00",
        "city": "New York",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "tz_offset": -5.0,
    },
)


def consultation_payload(profile: dict[str, Any]) -> dict[str, Any]:
    """Translate a synthetic profile into the v3 HTTP request contract."""
    return {
        "birth_datetime": profile["birth_datetime"],
        "latitude": profile["latitude"],
        "longitude": profile["longitude"],
        "tz_offset": profile["tz_offset"],
        "user_intent": profile["intent"],
        "language": "en",
    }


def assert_consultation_contract(profile: dict[str, Any], response: dict[str, Any]) -> None:
    """Assert the ticket's acceptance criteria for one consultation."""
    assert response.get("status") == "COMPLETED", (profile["id"], response)

    emissions = response.get("emissions")
    assert isinstance(emissions, list) and len(emissions) == 10, profile["id"]
    assert all(isinstance(item, dict) and item.get("claims") for item in emissions)
    assert len({item.get("tradition_domain") for item in emissions}) == 10

    report_markdown = response.get("report_markdown", "")
    assert MANDATORY_DISCLAIMER_MARKER in report_markdown

    metrics = response.get("audit_metrics", {})
    for metric_name in ("lciw", "rniw"):
        metric = metrics.get(metric_name)
        assert isinstance(metric, (int, float)) and 0.0 <= metric <= 1.0, (
            profile["id"],
            metric_name,
            metric,
        )


def run_profile(client: TestClient, profile: dict[str, Any]) -> dict[str, Any]:
    """Execute and validate one profile, returning a compact report record."""
    result = client.post("/api/v3/calculate", json=consultation_payload(profile))
    body = result.json()
    assert result.status_code == 200, (profile["id"], result.status_code, body)
    assert_consultation_contract(profile, body)
    metrics = body["audit_metrics"]
    return {
        "profile_id": profile["id"],
        "profile": profile,
        "status_code": result.status_code,
        "status": body["status"],
        "emission_count": len(body["emissions"]),
        "populated_emission_count": sum(bool(item.get("claims")) for item in body["emissions"]),
        "has_epistemic_disclaimer": MANDATORY_DISCLAIMER_MARKER in body["report_markdown"],
        "audit_metrics": {"LCIw": metrics["lciw"], "RNIw": metrics["rniw"]},
    }


def run_suite() -> list[dict[str, Any]]:
    with TestClient(app) as client:
        return [run_profile(client, profile) for profile in PROFILES]


def main() -> int:
    results = run_suite()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(
            {"ticket": "TICKET-HORO30-027", "profiles": results, "profile_count": len(results)},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print("+----+--------------------------------+--------+----------+----------+")
    print("| ID | Consultation                    | Status | Emissions| LCIw/RNIw|")
    print("+----+--------------------------------+--------+----------+----------+")
    for item in results:
        profile = item["profile"]
        metrics = item["audit_metrics"]
        print(
            f"| {item['profile_id']:<2} | {profile['name']:<30} | {item['status']:<6} "
            f"| {item['populated_emission_count']:>2}/10     | {metrics['LCIw']:.4f}/{metrics['RNIw']:.4f} |"
        )
    print("+----+--------------------------------+--------+----------+----------+")
    print(f"PASS: {len(results)}/5 profiles")
    print(f"Report: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
