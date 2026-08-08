#!/usr/bin/env python3
"""
scripts/run_universal_bridge.py
================================
Universal Production Metaphysics Engine CLI Runner.

Supports switching between:
  - --mode hybrid (Default: Local thClaws qwen2.5:7b + AGY Subagent Gemini Audit)
  - --mode thclaws (Pure offline thClaws harness)
  - --mode agy (Cloud AGY Subagent MCP protocol)

Usage:
  python3 scripts/run_universal_bridge.py --mode hybrid --date "1990-05-15 14:30:00"
"""

from __future__ import annotations

import sys
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from project.core.universal_runtime_bridge import universal_bridge


def main():
    parser = argparse.ArgumentParser(description="Universal Production Metaphysics Engine Runner")
    parser.add_argument("--mode", choices=["hybrid", "thclaws", "agy"], default="hybrid", help="Execution mode")
    parser.add_argument("--date", default="1990-05-15 14:30:00", help="Birth datetime (YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--query", default="วิเคราะห์ความแข็งแกร่งของ Day Master และอาชีพที่เหมาะสม", help="Astrological query")
    args = parser.parse_args()

    print("=" * 65)
    print(f"🌌 Universal Production Metaphysics Engine — Mode: {args.mode.upper()}")
    print("=" * 65)

    result = universal_bridge.run(birth_datetime=args.date, query=args.query, mode=args.mode)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
