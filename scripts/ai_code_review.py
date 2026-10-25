#!/usr/bin/env python3
"""AI Code Review Agent - Reviews PR diffs using Gemini/AIPASS bridges."""

import argparse
import json
import sys
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Any


class BridgeClient:
    """Client for communicating with AI bridges."""
    
    def __init__(self, bridge_url: str, bridge_name: str):
        self.bridge_url = bridge_url.rstrip('/')
        self.bridge_name = bridge_name
    
    def health_check(self) -> bool:
        """Check if bridge is healthy."""
        try:
            result = subprocess.run(
                ["curl", "-sf", "--max-time", "5", f"{self.bridge_url}/healthz"],
                capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get("service") == self.bridge_name
        except Exception:
            pass
        return False
    
    def review_code(self, diff: str, context: Dict = None) -> Dict:
        """Send code for review."""
        payload = {
            "diff": diff,
            "context": context or {},
            "review_type": "comprehensive",
            "categories": ["security", "style", "correctness", "complexity", "best-practices"]
        }
        
        try:
            # Use the bridge's review endpoint
            result = subprocess.run(
                ["curl", "-sf", "--max-time", "60", "-X", "POST",
                 "-H", "Content-Type: application/json",
                 "-d", json.dumps(payload),
                 f"{self.bridge_url}/review"],
                capture_output=True, text=True, check=False
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {"error": f"Bridge returned {result.returncode}: {result.stderr}"}
                
        except subprocess.TimeoutExpired:
            return {"error": "Bridge timeout"}
        except Exception as e:
            return {"error": str(e)}


def load_diff(diff_file: str) -> str:
    """Load diff from file or stdin."""
    if diff_file == "-":
        return sys.stdin.read()
    else:
        with open(diff_file, 'r') as f:
            return f.read()


def create_review_prompt(diff: str) -> str:
    """Create a comprehensive review prompt for the AI."""
    return f"""You are a senior code reviewer. Review the following diff for:
1. Security vulnerabilities (SQL injection, XSS, path traversal, etc.)
2. Code style and formatting issues
3. Correctness bugs (logic errors, edge cases, null handling)
4. Complexity concerns (cognitive complexity, nested loops, etc.)
5. Best practices violations (naming, patterns, maintainability)

Return a JSON object with this structure:
{{
  "reviews": [
    {{
      "severity": "critical|high|medium|low|info",
      "category": "security|style|correctness|complexity|best-practices",
      "message": "Clear description of the issue",
      "file": "path/to/file.py",
      "line": 123,
      "suggestion": "How to fix it",
      "code_snippet": "relevant code context"
    }}
  ],
  "summary": {{
    "total_issues": 0,
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 0,
    "info": 0
  }},
  "fix_suggestions": [
    {{
      "type": "auto-fix|manual-fix",
      "description": "What to fix",
      "file": "path/to/file.py",
      "line": 123,
      "original_code": "current code",
      "fixed_code": "suggested fix"
    }}
  ]
}}

Diff to review:
```diff
{diff}
```"""


def review_with_ai(diff: str) -> Dict:
    """Review code using available AI bridges."""
    # Try bridges in order of preference
    bridges = [
        BridgeClient("http://localhost:8765", "gemini-web-bridge"),
        BridgeClient("http://localhost:8766", "aipass-web-bridge"),
    ]
    
    for bridge in bridges:
        if bridge.health_check():
            print(f"Using {bridge.bridge_name} for review...", file=sys.stderr)
            result = bridge.review_code(diff)
            if "error" not in result:
                return result
            print(f"{bridge.bridge_name} error: {result.get('error')}", file=sys.stderr)
    
    # Fallback: return structured empty review if no bridge available
    print("Warning: No AI bridge available, returning empty review", file=sys.stderr)
    return {
        "reviews": [],
        "summary": {"total_issues": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
        "fix_suggestions": [],
        "fallback": True,
        "message": "No AI bridge available for review"
    }


def main():
    parser = argparse.ArgumentParser(description="AI Code Review Agent")
    parser.add_argument("--diff-file", help="Path to diff file (use - for stdin)")
    parser.add_argument("--output", choices=["json", "text"], default="json", help="Output format")
    parser.add_argument("--bridge", help="Specific bridge to use (gemini|aipass)")
    parser.add_argument("--context", help="JSON context file for review")
    args = parser.parse_args()
    
    # Load diff
    diff_file = args.diff_file or "-"
    diff = load_diff(diff_file)
    
    if not diff.strip():
        print("Error: No diff provided", file=sys.stderr)
        sys.exit(1)
    
    # Load context if provided
    context = None
    if args.context:
        with open(args.context, 'r') as f:
            context = json.load(f)
    
    # Perform review
    review_result = review_with_ai(diff)
    
    # Add metadata
    review_result["metadata"] = {
        "timestamp": time.time(),
        "diff_size": len(diff),
        "bridge_used": "auto"
    }
    
    # Output
    if args.output == "json":
        print(json.dumps(review_result, indent=2))
    else:
        # Text format for PR comments
        print(format_review_text(review_result))
    
    # Exit with 0 on success (review completed), 1 on error
    if review_result.get("error"):
        sys.exit(1)
    sys.exit(0)


def format_review_text(review: Dict) -> str:
    """Format review as human-readable text for PR comments."""
    lines = ["## 🤖 AI Code Review Results\n"]
    
    summary = review.get("summary", {})
    lines.append(f"**Summary**: {summary.get('total_issues', 0)} issues found")
    lines.append(f"- 🔴 Critical: {summary.get('critical', 0)}")
    lines.append(f"- 🟠 High: {summary.get('high', 0)}")
    lines.append(f"- 🟡 Medium: {summary.get('medium', 0)}")
    lines.append(f"- 🟢 Low: {summary.get('low', 0)}")
    lines.append(f"- ℹ️ Info: {summary.get('info', 0)}")
    lines.append("")
    
    reviews = review.get("reviews", [])
    if reviews:
        lines.append("### Issues Found\n")
        for r in reviews:
            severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "ℹ️"}
            icon = severity_icon.get(r.get("severity", "info"), "ℹ️")
            lines.append(f"{icon} **[{r.get('severity', 'info').upper()}]** {r.get('category', 'general').title()}: {r.get('message', '')}")
            if r.get("file"):
                lines.append(f"   📁 `{r['file']}`:{r.get('line', '?')}")
            if r.get("suggestion"):
                lines.append(f"   💡 *Suggestion*: {r['suggestion']}")
            lines.append("")
    
    fix_suggestions = review.get("fix_suggestions", [])
    if fix_suggestions:
        lines.append("### Suggested Fixes\n")
        for fix in fix_suggestions:
            fix_type = fix.get("type", "manual-fix")
            type_icon = "🤖" if fix_type == "auto-fix" else "👤"
            lines.append(f"{type_icon} **{fix_type.replace('-', ' ').title()}**: {fix.get('description', '')}")
            if fix.get("file"):
                lines.append(f"   📁 `{fix['file']}`:{fix.get('line', '?')}")
            if fix.get("original_code") and fix.get("fixed_code"):
                lines.append(f"   ```diff\n   - {fix['original_code']}\n   + {fix['fixed_code']}\n   ```")
            lines.append("")
    
    if review.get("fallback"):
        lines.append("⚠️ *Note: AI review was not available (no bridge connected). Review skipped.*")
    
    return "\n".join(lines)


if __name__ == "__main__":
    main()