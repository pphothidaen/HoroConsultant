#!/usr/bin/env python3
"""
scripts/run_thclaws_bridge.py
==============================
AGY + thClaws Hybrid Integration Bridge & Runner.

Simulates the full multi-agent workflow coordinated by thClaws Harness
using AGY MCP Tools:

Workflow:
  1. [thClaws Harness] calls bazi_calculate -> Gets TST & 4 Pillars chart
  2. [thClaws Harness] calls rag_search    -> Retrieves 3,132 FAISS vectors
  3. [thClaws Harness] calls bazi_interpret -> Generates Local qwen2.5-bazi reading
  4. [thClaws Harness] calls bazi_validate -> Audits reading via Gemini Cloud Agent

Usage:
  python scripts/run_thclaws_bridge.py [--date "1990-05-15 14:30:00"] [--query "การงานการเงิน"]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from project.mcp_server import HoroMCPTools

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("thclaws_bridge")


def run_thclaws_multiagent_pipeline(birth_datetime: str, query: str = "วิเคราะห์ดวงชะตาโดยรวม") -> dict:
    log.info("=" * 65)
    log.info("🇹🇭 AGY + thClaws (ThaiGPT) Hybrid Multi-Agent Pipeline")
    log.info("=" * 65)

    # Step 1: Agent 1 - bazi-calculator
    log.info("\n🤖 [Agent 1: bazi-calculator] Computing True Solar Time & Four Pillars...")
    chart = HoroMCPTools.bazi_calculate(birth_datetime=birth_datetime)
    dm = chart.get("day_master", {})
    log.info(f"   ✅ Calculated Day Master: {dm.get('stem')} ({dm.get('element')}) | True Solar Time: {chart.get('tst',{}).get('tst_datetime')}")

    # Step 2: Agent 2 - rag-scholar
    log.info("\n🤖 [Agent 2: rag-scholar] Searching 3,132 FAISS vectors for classical references...")
    search_res = HoroMCPTools.rag_search(query=query, top_k=2)
    log.info(f"   ✅ RAG Matches Found: {len(search_res.get('matches', []))} passages")

    # Step 3: Agent 3 - predictor-agent
    log.info("\n🤖 [Agent 3: predictor-agent] Generating Local AI Reading via qwen2.5:7b...")
    interp_res = HoroMCPTools.bazi_interpret(birth_datetime=birth_datetime, query=query)
    interpretation = interp_res.get("interpretation", "")
    log.info(f"   ✅ Prediction Generated ({len(interpretation)} chars) via route: {interp_res.get('route')}")

    # Step 4: Agent 4 - prediction-validator
    log.info("\n🤖 [Agent 4: prediction-validator] Auditing element logic via Gemini Cloud Agent...")
    val_report = HoroMCPTools.bazi_validate(
        bazi_chart=chart,
        initial_interpretation=interpretation,
        query=query
    )
    log.info(f"   ✅ Audit Status: {val_report.get('validation_status')} (Confidence: {val_report.get('confidence_score')})")

    final_output = {
        "harness": "thClaws (thclaws.ai) + AGY Master Engine",
        "birth_datetime": birth_datetime,
        "query": query,
        "chart_summary": {
            "day_master": dm,
            "five_elements": chart.get("five_elements", {}).get("percentages"),
            "tst_datetime": chart.get("tst", {}).get("tst_datetime"),
        },
        "rag_passages": search_res.get("matches"),
        "interpretation": interpretation,
        "validation_report": val_report,
    }

    log.info("\n" + "=" * 65)
    log.info("🎉 AGY + thClaws Multi-Agent Pipeline Completed Successfully!")
    log.info("=" * 65)

    return final_output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGY + thClaws Hybrid Runner")
    parser.add_argument("--date",  default="1990-05-15 14:30:00", help="Birth datetime YYYY-MM-DD HH:MM:SS")
    parser.add_argument("--query", default="วิเคราะห์ความแข็งแกร่งของ Day Master และอาชีพที่เหมาะสม", help="Query string")
    args = parser.parse_args()

    output = run_thclaws_multiagent_pipeline(birth_datetime=args.date, query=args.query)
    print("\n=== FINAL AGENT TEAM OUTPUT ===")
    print(json.dumps(output, indent=2, ensure_ascii=False))
