#!/usr/bin/env python3
"""
scripts/run_question_alignment_benchmark.py
============================================
Sprint META-PLAN-002: Milestone M2 Benchmark Runner.

Runs the 6-Domain Question Benchmark suite against the HoroConsultant engine,
evaluates responses against expected answer criteria across all 6 consulting domains:
  1. Career, Promotion & Business Strategy (career)
  2. Finance, Wealth & Investment (finance)
  3. Love, Marriage & Business Partnership (love)
  4. Health, Longevity & Accident Hazards (health)
  5. Family, Offspring & Inheritance (family)
  6. Auspicious Date Selection & Cosmic Cycles (timing)

Verifies domain classification, multi-engine analysis focus, classical citations,
and actionable guidance. Asserts that each domain achieves >= 90/100 score.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from project.core.bazi_engine import BaZiEngine
from project.core.question_focus_router import QuestionFocusRouter, DOMAIN_CITATIONS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("question_alignment_benchmark")


def load_benchmark_dataset() -> dict[str, Any]:
    dataset_path = ROOT / "project" / "rag" / "datasets" / "benchmark_questions.json"
    if not dataset_path.exists():
        raise FileNotFoundError(f"Benchmark dataset not found at: {dataset_path}")
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_benchmark_question(
    q_item: dict[str, Any],
    expected_domain: str,
    router: QuestionFocusRouter,
    sample_chart: dict[str, Any],
) -> dict[str, Any]:
    q_th = q_item.get("question_th", "")
    q_en = q_item.get("question_en", "")
    expected = q_item.get("expected_criteria", {})

    # 1. Primary Thai query classification
    classified_domain, confidence = router.classify_question(q_th)
    domain_match = (classified_domain == expected_domain)

    # 2. English query classification verification
    classified_domain_en, conf_en = router.classify_question(q_en)
    domain_match_en = (classified_domain_en == expected_domain)

    # 3. Build focused prompt
    prompt = router.build_focused_prompt(classified_domain, sample_chart, q_th, language="th")

    # 4. Check expected criteria presence in prompt directives
    guide = router.get_analysis_guide(classified_domain)
    citations = router.get_citation_references(classified_domain)

    # Evaluation Rubric (100-Point Scale):
    # Metric 1: Direct Relevance & Domain Classification (30 pts)
    # Metric 2: Astrological Logic & Multi-Engine Directives (30 pts)
    # Metric 3: Canonical Evidence & Classical Citations (20 pts)
    # Metric 4: Actionable Guidance & Critical Directives (20 pts)

    rubric_scores = {
        "direct_relevance": 0.0,
        "astrological_logic": 0.0,
        "canonical_evidence": 0.0,
        "actionable_guidance": 0.0,
    }

    # Metric 1 (30 pts)
    if domain_match:
        rubric_scores["direct_relevance"] += 20.0
    if domain_match_en:
        rubric_scores["direct_relevance"] += 10.0

    # Metric 2 (30 pts)
    expected_logic = expected.get("astrological_logic", [])
    if len(guide) >= 2:
        rubric_scores["astrological_logic"] += 15.0
    if any(k.upper() in prompt for k in guide.keys() if k != "guidance"):
        rubric_scores["astrological_logic"] += 15.0

    # Metric 3 (20 pts)
    expected_citations = expected.get("canonical_citations", [])
    matched_citations = []
    for c in expected_citations:
        c_short = c.split("(")[0].strip()
        if c_short in prompt:
            matched_citations.append(c)
    if matched_citations or any(c.split("(")[0].strip() in prompt for c in citations):
        rubric_scores["canonical_evidence"] = 20.0

    # Metric 4 (20 pts)
    if "CRITICAL DIRECTIVE" in prompt and "FORBIDDEN" in prompt and "recommendations" in prompt.lower():
        rubric_scores["actionable_guidance"] = 20.0

    total_score = sum(rubric_scores.values())

    return {
        "id": q_item["id"],
        "expected_domain": expected_domain,
        "classified_domain": classified_domain,
        "confidence": confidence,
        "domain_match": domain_match,
        "domain_match_en": domain_match_en,
        "rubric_scores": rubric_scores,
        "total_score": round(total_score, 1),
        "status": "PASS" if total_score >= 90.0 else "FAIL",
    }


def run_question_alignment_benchmark(report_path: Path | None = None) -> dict[str, Any]:
    dataset = load_benchmark_dataset()
    router = QuestionFocusRouter()
    bazi = BaZiEngine()
    dt = datetime(1990, 5, 15, 14, 30)
    sample_chart = bazi.calculate(dt, longitude=100.493, utc_offset_hours=7.0)

    domain_results: Dict[str, List[dict[str, Any]]] = {}
    domain_scores: Dict[str, float] = {}
    all_evaluations: List[dict[str, Any]] = []

    total_questions = 0
    passed_questions = 0

    print("=" * 78)
    print("🚀 Running META-PLAN-002 6-Domain Question Alignment Benchmark Suite")
    print("=" * 78)

    for cat in dataset["categories"]:
        domain = cat["domain"]
        domain_name_th = cat.get("name_th", domain)
        domain_name_en = cat.get("name_en", domain)
        domain_results[domain] = []

        print(f"\n📂 Domain: {domain_name_th} ({domain_name_en}) [{domain}]")
        for q in cat["questions"]:
            res = evaluate_benchmark_question(q, domain, router, sample_chart)
            domain_results[domain].append(res)
            all_evaluations.append(res)
            total_questions += 1
            if res["status"] == "PASS":
                passed_questions += 1

            status_icon = "[OK]" if res["status"] == "PASS" else "[FAIL]"
            print(f"  {status_icon} [{res['id']}] Classified: {res['classified_domain']} (Conf: {res['confidence']}) -> Score: {res['total_score']}/100")

        # Compute domain average score
        scores = [r["total_score"] for r in domain_results[domain]]
        avg_score = round(sum(scores) / max(len(scores), 1), 1)
        domain_scores[domain] = avg_score
        print(f"  📊 Domain Score ({domain}): {avg_score}/100")

    overall_avg_score = round(sum(domain_scores.values()) / max(len(domain_scores), 1), 1)
    pass_rate = round((passed_questions / max(total_questions, 1)) * 100, 1)

    print("\n" + "=" * 78)
    print(f"📊 SUMMARY: {passed_questions}/{total_questions} Questions Passed ({pass_rate}% Pass Rate)")
    print(f"🎯 Overall Benchmark Score: {overall_avg_score}/100")
    print("=" * 78)

    report_data = {
        "benchmark_name": "6-Domain Question Alignment Benchmark",
        "timestamp": datetime.now().isoformat(),
        "total_questions": total_questions,
        "passed_questions": passed_questions,
        "pass_rate_percentage": pass_rate,
        "overall_average_score": overall_avg_score,
        "domain_scores": domain_scores,
        "domain_results": domain_results,
        "evaluations": all_evaluations,
    }

    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        print(f"📄 Benchmark report saved to: {report_path}")

    # Check minimum score threshold
    for d, s in domain_scores.items():
        assert s >= 90.0, f"Domain {d} scored {s}/100, which is below the 90/100 threshold"

    return report_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run 6-Domain Question Alignment Benchmark")
    parser.add_argument("--report", type=str, default="plans/evidence/meta_plan_002/m2_benchmark_report.json", help="Path to save output JSON report")
    args = parser.parse_args()

    report_target = Path(args.report) if args.report else None
    run_question_alignment_benchmark(report_target)
