#!/usr/bin/env python3
"""Quality Gate - Evaluates AI review results against thresholds."""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any


# Default thresholds - can be overridden via config file or env vars
DEFAULT_THRESHOLDS = {
    "critical": 0,      # Zero tolerance for critical
    "high": 0,          # Zero tolerance for high
    "medium": 5,        # Allow up to 5 medium issues
    "low": 20,          # Allow up to 20 low issues
    "info": 50,         # Allow up to 50 info issues
}

# Categories that are blocking by default
BLOCKING_CATEGORIES = {"security", "correctness"}


def load_thresholds(config_file: str = None) -> Dict:
    """Load thresholds from config file or use defaults."""
    thresholds = DEFAULT_THRESHOLDS.copy()
    
    if config_file and Path(config_file).exists():
        with open(config_file, 'r') as f:
            custom = json.load(f)
            thresholds.update(custom.get("thresholds", {}))
    
    # Also check environment variables
    for key in thresholds:
        env_key = f"QUALITY_GATE_{key.upper()}"
        if env_key in os.environ:
            thresholds[key] = int(os.environ[env_key])
    
    return thresholds


def load_review(review_file: str) -> Dict:
    """Load review results from file."""
    with open(review_file, 'r') as f:
        return json.load(f)


def evaluate_quality_gate(review: Dict, thresholds: Dict, override: bool = False) -> Dict:
    """Evaluate review against quality thresholds."""
    summary = review.get("summary", {})
    reviews = review.get("reviews", [])
    
    results = {
        "passed": True,
        "violations": [],
        "warnings": [],
        "summary": summary,
        "override_used": override
    }
    
    # Check each severity threshold
    for severity, max_allowed in thresholds.items():
        actual = summary.get(severity, 0)
        if actual > max_allowed:
            if override:
                results["warnings"].append({
                    "type": "threshold_exceeded",
                    "severity": severity,
                    "actual": actual,
                    "allowed": max_allowed,
                    "message": f"{severity.capitalize()} issues ({actual}) exceed threshold ({max_allowed}) - overridden"
                })
            else:
                results["passed"] = False
                results["violations"].append({
                    "type": "threshold_exceeded",
                    "severity": severity,
                    "actual": actual,
                    "allowed": max_allowed,
                    "message": f"{severity.capitalize()} issues ({actual}) exceed threshold ({max_allowed})"
                })
    
    # Check for blocking category issues (always fail unless overridden)
    if not override:
        for review_item in reviews:
            category = review_item.get("category", "").lower()
            severity = review_item.get("severity", "").lower()
            if category in BLOCKING_CATEGORIES and severity in ("critical", "high"):
                results["passed"] = False
                results["violations"].append({
                    "type": "blocking_category",
                    "category": category,
                    "severity": severity,
                    "message": f"{severity.capitalize()} {category} issue found: {review_item.get('message', '')}",
                    "file": review_item.get("file"),
                    "line": review_item.get("line")
                })
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Quality Gate for AI Code Reviews")
    parser.add_argument("--review-file", required=True, help="Path to AI review JSON file")
    parser.add_argument("--config", help="Path to quality gate config JSON")
    parser.add_argument("--override", action="store_true", help="Override quality gate (human approval)")
    parser.add_argument("--output", choices=["json", "text"], default="text", help="Output format")
    args = parser.parse_args()
    
    # Load review and thresholds
    review = load_review(args.review_file)
    thresholds = load_thresholds(args.config)
    
    # Evaluate
    results = evaluate_quality_gate(review, thresholds, args.override)
    
    # Output
    if args.output == "json":
        print(json.dumps(results, indent=2))
    else:
        print(format_results_text(results))
    
    # Exit code
    sys.exit(0 if results["passed"] else 1)


def format_results_text(results: Dict) -> str:
    """Format results as human-readable text."""
    lines = []
    
    if results["passed"]:
        lines.append("✅ QUALITY GATE PASSED")
    else:
        lines.append("❌ QUALITY GATE FAILED")
    
    if results["override_used"]:
        lines.append("⚠️ Human override was used")
    
    lines.append("")
    lines.append("Thresholds:")
    for severity, max_allowed in DEFAULT_THRESHOLDS.items():
        actual = results["summary"].get(severity, 0)
        status = "✅" if actual <= max_allowed else "❌"
        lines.append(f"  {status} {severity.capitalize()}: {actual}/{max_allowed}")
    
    if results["violations"]:
        lines.append("")
        lines.append("Violations:")
        for v in results["violations"]:
            lines.append(f"  ❌ {v['message']}")
    
    if results["warnings"]:
        lines.append("")
        lines.append("Warnings (overridden):")
        for w in results["warnings"]:
            lines.append(f"  ⚠️ {w['message']}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    import os
    main()