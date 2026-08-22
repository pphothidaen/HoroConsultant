#!/usr/bin/env python3
"""Secret-safe quota/status handoff guard for AI agent continuity.

The guard is intentionally conservative: it only acts on an explicit quota
signal supplied by the runtime or by a caller. It never reads secret files and
never prints credential values.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROJECT_TASKS = ROOT / "PROJECT_TASKS.md"
PLAN = ROOT / "plans" / "plan.md"
DEFAULT_THRESHOLD = 10.0

QUOTA_ENV_KEYS = (
    "AGENT_QUOTA_REMAINING_PERCENT",
    "AI_AGENT_QUOTA_REMAINING_PERCENT",
    "CODEX_QUOTA_REMAINING_PERCENT",
    "CODEX_REMAINING_QUOTA_PERCENT",
)


def _parse_percent(raw: str | None) -> float | None:
    if raw is None:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*%?", str(raw))
    if not match:
        return None
    value = float(match.group(1))
    if value < 0:
        return None
    return min(value, 100.0)


def _quota_from_env() -> tuple[float | None, str]:
    for key in QUOTA_ENV_KEYS:
        value = _parse_percent(os.getenv(key))
        if value is not None:
            return value, key
    return None, "none"


def _quota_from_status_text(text: str | None) -> float | None:
    if not text:
        return None
    patterns = (
        r"(?:quota|โควต้า)[^\d]{0,40}(\d+(?:\.\d+)?)\s*%",
        r"(\d+(?:\.\d+)?)\s*%[^\n]{0,40}(?:remaining|left|เหลือ)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return _parse_percent(match.group(1))
    return None


def _docs_have_handoff_markers() -> tuple[bool, list[str]]:
    missing: list[str] = []
    project_text = PROJECT_TASKS.read_text(encoding="utf-8") if PROJECT_TASKS.exists() else ""
    plan_text = PLAN.read_text(encoding="utf-8") if PLAN.exists() else ""

    checks = {
        "PROJECT_TASKS:TICKET-META-008": "TICKET-META-008" in project_text,
        "PROJECT_TASKS:safe resume commands": "Safe Resume Commands" in project_text,
        "PROJECT_TASKS:credential status": "GitHub CLI" in project_text and "Doppler CLI" in project_text,
        "plans:quota migration guard": "Quota Exhaustion / Account Migration Guard" in plan_text,
        "plans:account migration continuity": "Account Migration Continuity" in plan_text,
    }
    for name, passed in checks.items():
        if not passed:
            missing.append(name)
    return not missing, missing


def evaluate(
    remaining_percent: float | None,
    source: str,
    threshold: float = DEFAULT_THRESHOLD,
) -> dict[str, Any]:
    docs_ok, missing = _docs_have_handoff_markers()
    signal_present = remaining_percent is not None
    handoff_required = bool(signal_present and remaining_percent < threshold)
    return {
        "signal_present": signal_present,
        "source": source,
        "remaining_percent": remaining_percent,
        "threshold_percent": threshold,
        "handoff_required": handoff_required,
        "docs_ok": docs_ok,
        "missing_markers": missing,
        "recommended_actions": [
            "Run /status or runtime status check.",
            "Summarize current objective, commits, dirty files, verified checks, blockers, and next safe command.",
            "Update PROJECT_TASKS.md TICKET-META-008 and plans/plan.md without secret values.",
            "Run python3 project/core/code_reviewer.py --scan-secrets.",
        ]
        if handoff_required
        else [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check quota handoff governance status.")
    parser.add_argument("--remaining-percent", type=float, default=None)
    parser.add_argument("--status-text", default="")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--enforce", action="store_true", help="Return non-zero if low quota lacks doc handoff markers")
    args = parser.parse_args()

    remaining = args.remaining_percent
    source = "argument"
    if remaining is None:
        remaining = _quota_from_status_text(args.status_text)
        source = "status-text" if remaining is not None else source
    if remaining is None:
        remaining, source = _quota_from_env()

    result = evaluate(remaining, source, args.threshold)

    if args.json:
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    elif not result["signal_present"]:
        print("[OK] Quota guard: no quota signal present; no handoff threshold evaluated.")
    elif result["handoff_required"]:
        print(
            "[WARNING] Quota guard: remaining quota "
            f"{result['remaining_percent']:.1f}% is below {result['threshold_percent']:.1f}%."
        )
        if result["docs_ok"]:
            print("[OK] Quota handoff markers are present in PROJECT_TASKS.md and plans/plan.md.")
        else:
            print("[ERROR] Missing quota handoff markers: " + ", ".join(result["missing_markers"]))
    else:
        print(
            "[OK] Quota guard: remaining quota "
            f"{result['remaining_percent']:.1f}% is above threshold {result['threshold_percent']:.1f}%."
        )

    if args.enforce and result["handoff_required"] and not result["docs_ok"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
