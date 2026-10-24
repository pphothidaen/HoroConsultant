#!/usr/bin/env python3
"""Detect AI-generated code in PR and enforce human review checkbox."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional


def run_cmd(cmd: list[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    """Run command and return result."""
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def get_pr_commits(base: str, head: str, repo: Optional[Path] = None) -> list[str]:
    """Get commit SHAs in PR range."""
    result = run_cmd(["git", "rev-list", f"{base}..{head}"], cwd=repo)
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def get_commit_subject(repo: Path, commit: str) -> str:
    """Get commit subject line."""
    result = run_cmd(["git", "show", "-s", "--format=%s", commit], cwd=repo)
    return result.stdout.strip() if result.returncode == 0 else ""


def get_commit_files(repo: Path, commit: str) -> list[str]:
    """Get files changed in commit."""
    result = run_cmd(["git", "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", commit], cwd=repo)
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def is_ai_generated_commit(repo: Path, commit: str) -> bool:
    """Check if commit is AI-generated based on explicit subject prefix only.

    Only commits with explicit 'AI-Generated:' prefix in subject are considered AI-generated.
    This avoids false positives from implementation commits that mention AI in their messages.
    """
    subject = get_commit_subject(repo, commit)

    # Only explicit AI-Generated: prefix triggers AI detection
    if subject.startswith("AI-Generated:"):
        return True

    return False


def get_pr_labels(repo: Path, base: str, head: str) -> list[str]:
    """Get PR labels (simulated - in CI we'd use GitHub API)."""
    # In CI, this would use GitHub API
    # For local testing, check commit messages for label patterns
    labels = []
    commits = get_pr_commits(base, head, repo)
    for commit in commits:
        subject = get_commit_subject(repo, commit)
        if "ai-generated" in subject.lower():
            labels.append("ai-generated")
        if "ai-review-required" in subject.lower():
            labels.append("ai-review-required")
    return labels


def check_human_review_checkbox(pr_body: str) -> bool:
    """Check if human review checkbox is checked in PR body."""
    # Look for checked checkbox pattern: "- [x] I have reviewed ALL AI-generated code"
    pattern = r"-\s*\[x\]\s*I have reviewed ALL AI-generated code"
    return bool(re.search(pattern, pr_body, re.IGNORECASE))


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Detect AI-generated code and enforce human review")
    parser.add_argument("--base", required=True, help="Base commit SHA")
    parser.add_argument("--head", default="HEAD", help="Head commit SHA")
    parser.add_argument("--pr-body", default="", help="PR body text")
    parser.add_argument("--repo", default=".", help="Repository path")
    parser.add_argument("--json-out", help="Output JSON report path")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()

    # Get PR commits
    commits = get_pr_commits(args.base, args.head, repo)

    # Detect AI-generated commits
    ai_commits = []
    ai_files = set()

    for commit in commits:
        if is_ai_generated_commit(repo, commit):
            ai_commits.append(commit)
            files = get_commit_files(repo, commit)
            ai_files.update(files)

    # Also check for ai-generated label
    labels = get_pr_labels(repo, args.base, args.head)
    has_ai_label = "ai-generated" in labels

    # Determine if AI review is required
    ai_review_required = bool(ai_commits) or has_ai_label

    # Check human review checkbox
    human_review_checked = check_human_review_checkbox(args.pr_body)

    # Build report
    report = {
        "ai_review_required": ai_review_required,
        "ai_commits": ai_commits,
        "ai_files": sorted(ai_files),
        "has_ai_label": has_ai_label,
        "human_review_checked": human_review_checked,
        "review_passed": not ai_review_required or human_review_checked,
    }

    # Output
    if args.json_out:
        output = Path(args.json_out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2))

    # Print summary
    print(f"AI Review Required: {ai_review_required}")
    print(f"AI Commits Found: {len(ai_commits)}")
    print(f"AI Files: {len(ai_files)}")
    print(f"Has AI Label: {has_ai_label}")
    print(f"Human Review Checked: {human_review_checked}")
    print(f"Review Passed: {report['review_passed']}")

    if ai_commits:
        print("\nAI Commits:")
        for c in ai_commits:
            subject = get_commit_subject(repo, c)
            print(f"  {c[:8]} - {subject}")

    if ai_files:
        print("\nAI Files:")
        for f in sorted(ai_files):
            print(f"  {f}")

    # Exit code: 0 = pass, 1 = fail (AI review required but not checked)
    sys.exit(0 if report["review_passed"] else 1)


if __name__ == "__main__":
    main()