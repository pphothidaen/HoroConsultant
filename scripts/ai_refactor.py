#!/usr/bin/env python3
"""AI Refactoring Agent - Analyzes AI reviews and codebase to suggest refactorings."""

import argparse
import json
import sys
import os
import subprocess
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
    
    def suggest_refactors(self, review: Dict, codebase_context: Dict = None) -> Dict:
        """Get refactoring suggestions from AI."""
        payload = {
            "review": review,
            "codebase_context": codebase_context or {},
            "task": "refactoring_suggestions",
            "categories": ["dead-code", "complexity", "duplication", "modernization", "performance", "security"]
        }
        
        try:
            result = subprocess.run(
                ["curl", "-sf", "--max-time", "60", "-X", "POST",
                 "-H", "Content-Type: application/json",
                 "-d", json.dumps(payload),
                 f"{self.bridge_url}/refactor"],
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


def load_review(review_file: str) -> Dict:
    """Load review results from file."""
    with open(review_file, 'r') as f:
        return json.load(f)


def load_codebase_context(path: str) -> Dict:
    """Load basic codebase context."""
    context: Dict = {
        "files": [],
        "languages": {},
        "size_estimate": 0
    }
    
    p = Path(path)
    if p.is_file():
        context["files"] = [str(p)]
    elif p.is_dir():
        for ext in ['.py', '.js', '.ts', '.java', '.go', '.rs']:
            context["files"].extend([str(f) for f in p.rglob(f"*{ext}")])
            if context["files"]:
                context["languages"][ext] = len([f for f in context["files"] if f.endswith(ext)])
    
    context["size_estimate"] = len(context["files"])
    return context


def create_refactor_prompt(review: Dict, context: Dict) -> str:
    """Create a comprehensive refactoring prompt for the AI."""
    return f"""You are a senior software architect. Analyze the code review results and codebase context to suggest refactorings.

Review Results:
```json
{json.dumps(review, indent=2)}
```

Codebase Context:
```json
{json.dumps(context, indent=2)}
```

Return a JSON object with this structure:
{{
  "refactorings": [
    {{
      "id": "unique-id",
      "type": "extract-function|remove-dead-code|simplify-complexity|modernize-pattern|optimize-performance|fix-duplication",
      "severity": "critical|high|medium|low",
      "category": "maintainability|performance|security|readability",
      "title": "Short descriptive title",
      "description": "Detailed explanation of the refactoring",
      "files_affected": ["path/to/file1.py", "path/to/file2.py"],
      "estimated_effort": "trivial|small|medium|large",
      "safety": "auto-fix|needs-review|high-risk",
      "before_example": "code before refactoring",
      "after_example": "code after refactoring",
      "tests_needed": ["test description"],
      "related_review_issues": ["review issue messages this addresses"]
    }}
  ],
  "summary": {{
    "total_suggestions": 0,
    "auto_fixable": 0,
    "needs_review": 0,
    "high_risk": 0,
    "by_type": {{}}
  }},
  "priority_order": ["refactoring-id-1", "refactoring-id-2"]
}}"""


def suggest_with_ai(review: Dict, context: Dict) -> Dict:
    """Get refactoring suggestions using available AI bridges."""
    bridges = [
        BridgeClient("http://localhost:8765", "gemini-web-bridge"),
        BridgeClient("http://localhost:8766", "aipass-web-bridge"),
    ]
    
    for bridge in bridges:
        if bridge.health_check():
            print(f"Using {bridge.bridge_name} for refactoring...", file=sys.stderr)
            result = bridge.suggest_refactors(review, context)
            if "error" not in result:
                return result
            print(f"{bridge.bridge_name} error: {result.get('error')}", file=sys.stderr)
    
    # Fallback: rule-based suggestions from review
    print("Warning: No AI bridge available, using rule-based fallback", file=sys.stderr)
    return generate_fallback_refactors(review, context)


def generate_fallback_refactors(review: Dict, context: Dict) -> Dict:
    """Generate basic refactoring suggestions from review issues."""
    refactorings = []
    
    for issue in review.get("reviews", []):
        category = issue.get("category", "")
        severity = issue.get("severity", "")
        file_path = issue.get("file", "")
        message = issue.get("message", "")
        
        if not file_path:
            continue
        
        refactor = {
            "id": f"refactor-{len(refactorings)+1}",
            "type": "unknown",
            "severity": severity,
            "category": "maintainability",
            "title": f"Address {category}: {message[:60]}",
            "description": f"Review issue: {message}\nSuggestion: {issue.get('suggestion', 'No specific suggestion')}",
            "files_affected": [file_path],
            "estimated_effort": "small" if severity in ("low", "medium") else "medium",
            "safety": "needs-review",
            "before_example": issue.get("code_snippet", ""),
            "after_example": "",
            "tests_needed": ["Verify behavior unchanged"],
            "related_review_issues": [message]
        }
        
        # Classify by category
        if category == "style":
            refactor["type"] = "modernize-pattern"
            refactor["safety"] = "auto-fix"
        elif category == "complexity":
            refactor["type"] = "simplify-complexity"
        elif category == "correctness":
            refactor["type"] = "fix-duplication"
        elif category == "security":
            refactor["type"] = "modernize-pattern"
            refactor["category"] = "security"
        elif category == "best-practices":
            refactor["type"] = "modernize-pattern"
        
        refactorings.append(refactor)
    
    # Summary
    summary = {
        "total_suggestions": len(refactorings),
        "auto_fixable": sum(1 for r in refactorings if r["safety"] == "auto-fix"),
        "needs_review": sum(1 for r in refactorings if r["safety"] == "needs-review"),
        "high_risk": sum(1 for r in refactorings if r["safety"] == "high-risk"),
        "by_type": {}
    }
    
    for r in refactorings:
        t = r["type"]
        summary["by_type"][t] = summary["by_type"].get(t, 0) + 1
    
    return {
        "refactorings": refactorings,
        "summary": summary,
        "priority_order": [r["id"] for r in sorted(refactorings, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x["severity"], 4))],
        "fallback": True,
        "message": "Generated from rule-based fallback (no AI bridge)"
    }


def format_refactor_text(refactor: Dict) -> str:
    """Format refactoring as human-readable text."""
    lines = ["## 🔧 AI Refactoring Suggestions\n"]
    
    summary = refactor.get("summary", {})
    lines.append(f"**Summary**: {summary.get('total_suggestions', 0)} refactoring suggestions")
    lines.append(f"- 🤖 Auto-fixable: {summary.get('auto_fixable', 0)}")
    lines.append(f"- 👤 Needs review: {summary.get('needs_review', 0)}")
    lines.append(f"- ⚠️ High risk: {summary.get('high_risk', 0)}")
    lines.append("")
    
    for r in refactor.get("refactorings", []):
        safety_icon = {"auto-fix": "🤖", "needs-review": "👤", "high-risk": "⚠️"}
        icon = safety_icon.get(r.get("safety", "needs-review"), "👤")
        severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
        sev_icon = severity_icon.get(r.get("severity", "low"), "🟢")
        
        lines.append(f"{icon} {sev_icon} **[{r.get('type', 'unknown').replace('-', ' ').title()}]** {r.get('title', '')}")
        lines.append(f"   📁 Files: {', '.join(r.get('files_affected', []))}")
        lines.append(f"   💪 Effort: {r.get('estimated_effort', 'unknown')}")
        lines.append(f"   🛡️ Safety: {r.get('safety', 'needs-review')}")
        if r.get("description"):
            lines.append(f"   📝 {r['description'][:200]}...")
        if r.get("before_example") and r.get("after_example"):
            lines.append(f"   ```diff")
            lines.append(f"   - {r['before_example'][:100]}")
            lines.append(f"   + {r['after_example'][:100]}")
            lines.append(f"   ```")
        lines.append("")
    
    if refactor.get("fallback"):
        lines.append("⚠️ *Note: Suggestions generated from rule-based fallback (AI bridge unavailable).*")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="AI Refactoring Agent")
    parser.add_argument("--review-file", required=True, help="Path to AI review JSON file")
    parser.add_argument("--codebase-path", default=".", help="Path to codebase for context")
    parser.add_argument("--output", choices=["json", "text"], default="json", help="Output format")
    parser.add_argument("--bridge", help="Specific bridge to use (gemini|aipass)")
    args = parser.parse_args()
    
    # Load inputs
    review = load_review(args.review_file)
    context = load_codebase_context(args.codebase_path)
    
    # Get suggestions
    refactor_result = suggest_with_ai(review, context)
    
    # Add metadata
    refactor_result["metadata"] = {
        "codebase_files": context.get("size_estimate", 0),
        "review_issues": review.get("summary", {}).get("total_issues", 0)
    }
    
    # Output
    if args.output == "json":
        print(json.dumps(refactor_result, indent=2))
    else:
        print(format_refactor_text(refactor_result))
    
    if refactor_result.get("error"):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()