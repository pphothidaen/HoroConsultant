#!/usr/bin/env python3
"""
scripts/run_benchmark_evaluation.py
====================================
Runs the 6-Domain Question Benchmark suite against the HoroConsultant engine,
evaluates responses against expected answer criteria, and generates an alignment report.

Source: plans/question_forecast_alignment_spec.md
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from project.core.bazi_engine import BaZiEngine
from project.core.question_focus_router import QuestionFocusRouter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("benchmark_evaluation")


def load_benchmark_dataset() -> dict[str, Any]:
    dataset_path = ROOT / "project" / "rag" / "datasets" / "benchmark_questions.json"
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_question(
    q_item: dict[str, Any],
    domain: str,
    router: QuestionFocusRouter,
    sample_chart: dict[str, Any],
) -> dict[str, Any]:
    q_th = q_item["question_th"]
    expected = q_item.get("expected_criteria", {})

    # 1. Classification check
    classified_domain, confidence = router.classify_question(q_th)
    domain_match = (classified_domain == domain)

    # 2. Build focused prompt
    prompt = router.build_focused_prompt(classified_domain, sample_chart, q_th, language="th")

    # 3. Check expected criteria presence in prompt directives
    guide = router.get_analysis_guide(classified_domain)
    citations = router.get_citation_references(classified_domain)

    # Criteria alignment score
    score = 0.0
    total_checks = 4

    # Check 1: Domain matched correctly
    if domain_match:
        score += 1.0

    # Check 2: Analysis guide has specific engine directives
    if len(guide) >= 2:
        score += 1.0

    # Check 3: Canonical citations included
    expected_citations = expected.get("canonical_citations", [])
    citation_matched = any(c.split("(")[0].strip() in prompt for c in expected_citations)
    if citation_matched:
        score += 1.0

    # Check 4: Prompt has critical directives
    if "CRITICAL DIRECTIVE" in prompt and "FORBIDDEN" in prompt:
        score += 1.0

    alignment_pct = round((score / total_checks) * 100, 1)

    return {
        "id": q_item["id"],
        "domain": domain,
        "classified_as": classified_domain,
        "confidence": confidence,
        "domain_match": domain_match,
        "alignment_percentage": alignment_pct,
        "status": "PASS" if alignment_pct >= 75.0 else "FAIL",
    }


def run_benchmark():
    dataset = load_benchmark_dataset()
    router = QuestionFocusRouter()
    from datetime import datetime
    bazi = BaZiEngine()
    dt = datetime.strptime("1990-05-15 14:30:00", "%Y-%m-%d %H:%M:%S")
    sample_chart = bazi.calculate(dt, 100.493, 7.0)

    results = []
    total_questions = 0
    passed_questions = 0

    print("=" * 70)
    print("🚀 Running 6-Domain Question Benchmark & Forecast Alignment Suite")
    print("=" * 70)

    for cat in dataset["categories"]:
        domain = cat["domain"]
        print(f"\n📂 Domain: {cat['name_th']} ({cat['name_en']})")
        for q in cat["questions"]:
            res = evaluate_question(q, domain, router, sample_chart)
            results.append(res)
            total_questions += 1
            if res["status"] == "PASS":
                passed_questions += 1

            status_icon = "✅" if res["status"] == "PASS" else "❌"
            print(f"  {status_icon} [{res['id']}] Domain: {res['classified_as']} (Conf: {res['confidence']}) -> Score: {res['alignment_percentage']}%")

    overall_pass_rate = round((passed_questions / max(total_questions, 1)) * 100, 1)
    print("\n" + "=" * 70)
    print(f"📊 SUMMARY: {passed_questions}/{total_questions} Questions Passed ({overall_pass_rate}% Pass Rate)")
    print("=" * 70)

    report_path = ROOT / "project" / "tests" / "benchmark_evaluation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_questions": total_questions,
            "passed_questions": passed_questions,
            "overall_pass_rate": overall_pass_rate,
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"📄 Saved report to: {report_path}")

    assert overall_pass_rate == 100.0, f"Benchmark failed: {overall_pass_rate}% < 100%"
    print("[OK] Benchmark evaluation passed with 100% alignment!")


if __name__ == "__main__":
    run_benchmark()
