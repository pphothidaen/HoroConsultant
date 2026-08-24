#!/usr/bin/env python3
"""Interactive diagnostic CLI for the Horo Architecture v3.0 pipeline.

The CLI deliberately reuses the same calculation and runtime nodes as the
``/api/v3/calculate`` endpoint.  It is intended for local diagnostics and
operator-friendly inspection of the ten-domain pipeline.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from project.routers.v3 import V3CalculateRequest, _calculate_emissions  # noqa: E402

RUNTIMES_DIR = ROOT / "TDD-HORO-v3.0" / "05_AGENT_PROMPTS_AND_RUNTIMES"
if str(RUNTIMES_DIR) not in sys.path:
    sys.path.insert(0, str(RUNTIMES_DIR))

from runtimes.audit_node import AuditNode  # noqa: E402
from runtimes.consensus_engine import ConsensusEngine  # noqa: E402
from runtimes.plan_composer import PlanComposer  # noqa: E402

DOMAIN_LABELS = {
    "ming_xue_bazi": "BaZi",
    "ming_xue_ziwei": "ZiWei",
    "san_shi_qi_men": "QiMen",
    "ze_ji_xue": "ZeJi",
    "xiang_xue_feng_shui": "XuanKong",
    "san_shi_da_liu_ren": "DaLiuRen",
    "bu_shi_liu_yao": "LiuYao",
    "san_shi_tai_yi": "TaiYi",
    "ming_xue_qi_zheng": "QiZheng",
    "xiang_xue_mian_xiang": "MianXiang",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Horo v3.0 Interactive Diagnostic CLI")
    parser.add_argument("--birth-date", required=True, help="Birth date (YYYY-MM-DD)")
    parser.add_argument("--birth-time", required=True, help="Birth time (HH:MM)")
    parser.add_argument("--lat", type=float, default=13.7563, help="Latitude")
    parser.add_argument("--lon", type=float, default=100.493, help="Longitude")
    parser.add_argument("--intent", default="STRATEGIC_TIMING_ACTION", help="User intent")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output pure JSON")
    return parser


def _validate_datetime(birth_date: str, birth_time: str) -> datetime:
    try:
        parsed_date = date.fromisoformat(birth_date)
        parsed_time = datetime.strptime(birth_time, "%H:%M").time()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("birth date/time must use YYYY-MM-DD and HH:MM") from exc
    return datetime.combine(parsed_date, parsed_time)


def _tri_graph_summary(emissions: list[dict[str, Any]], consensus: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    claim_count = sum(len(emission.get("claims", [])) for emission in emissions)
    arbitration_edges = consensus.get("arbitrated_edges", [])
    events = list(consensus.get("events_emitted", []))
    verdict_event = audit.get("verdict", "AUDIT_UNKNOWN")
    return {
        "G_deriv": {"nodes": len(emissions) + 3, "edges": len(emissions) + 2, "stages": ["L2", "L3/L4", "L5", "L6", "L7"]},
        "G_sem": {"nodes": claim_count, "edges": len(arbitration_edges), "arbitration_edge_types": sorted({edge.get("edge_type", "unknown") for edge in arbitration_edges})},
        "L_event": {"entries": 2 + len(emissions) + len(events) + 2, "events": sorted(events + [verdict_event, "COMPOSER_OUTPUT_EMITTED"])},
    }


def run_pipeline(args: argparse.Namespace) -> dict[str, Any]:
    birth_datetime = _validate_datetime(args.birth_date, args.birth_time)
    request = V3CalculateRequest(
        birth_datetime=birth_datetime.isoformat(),
        latitude=args.lat,
        longitude=args.lon,
        user_intent=args.intent,
    )
    emissions, charts, session_id = _calculate_emissions(request)
    consensus = ConsensusEngine(args.intent).arbitrate_claims(emissions)
    audit = AuditNode().evaluate_consensus_state(consensus)
    composed = PlanComposer().compose_final_report(consensus, audit, language="en")
    return {
        "session_id": session_id,
        "input": {"birth_date": args.birth_date, "birth_time": args.birth_time, "lat": args.lat, "lon": args.lon, "intent": args.intent},
        "domains": [{"domain": DOMAIN_LABELS.get(e["tradition_domain"], e["tradition_domain"]), "claims": len(e.get("claims", [])), "status": "CALCULATED"} for e in emissions],
        "audit": {"metrics": audit["metrics"], "verdict": audit["verdict"]},
        "tri_graph": _tri_graph_summary(emissions, consensus, audit),
        "composer": {"status": composed["status"], "effective_claims_count": composed["effective_claims_count"], "has_epistemic_disclaimer": composed["has_epistemic_disclaimer"]},
        "charts": charts,
    }


def _render(result: dict[str, Any]) -> str:
    audit = result["audit"]
    lines = [
        "+======================================================================+",
        "| HORO v3.0 INTERACTIVE DIAGNOSTIC CLI                               |",
        "+======================================================================+",
        "| Epistemic Disclaimer: rule-based tradition validity and model        |",
        "| consistency only; predictive validity is explicitly disclaimed.    |",
        "+----------------------------------------------------------------------+",
        f"| Intent: {result['input']['intent']:<61}|",
        f"| Birth:  {result['input']['birth_date']} {result['input']['birth_time']:<51}|",
        "+----------------------------------------------------------------------+",
        "| 10-DOMAIN CALCULATION SUMMARY                                       |",
        "+----------------------+--------+-------------------------------+",
        "| Domain               | Claims | Status                        |",
        "+----------------------+--------+-------------------------------+",
    ]
    lines.extend(f"| {row['domain']:<20} | {row['claims']:>6} | {row['status']:<29} |" for row in result["domains"])
    lines.extend([
        "+----------------------+--------+-------------------------------+",
        "| AUDIT METRICS                                                       |",
        f"| LCIw: {audit['metrics']['lciw']:<8} RNIw: {audit['metrics']['rniw']:<8} Verdict: {audit['verdict']:<20} |",
        "+----------------------------------------------------------------------+",
        "| TRI-GRAPH DERIVATION SUMMARY                                       |",
        f"| G_deriv nodes/edges: {result['tri_graph']['G_deriv']['nodes']}/{result['tri_graph']['G_deriv']['edges']:<43}|",
        f"| G_sem   nodes/edges: {result['tri_graph']['G_sem']['nodes']}/{result['tri_graph']['G_sem']['edges']:<43}|",
        f"| L_event entries:     {result['tri_graph']['L_event']['entries']:<45}|",
        "+======================================================================+",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_pipeline(args)
    except (argparse.ArgumentTypeError, ValueError) as exc:
        build_parser().error(str(exc))
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    else:
        print(_render(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
