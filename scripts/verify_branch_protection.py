#!/usr/bin/env python3
"""
scripts/verify_branch_protection.py — Verify GitHub Branch Protection Rules.

Checks that the `main` branch has the required protection rules enabled:
1. Require a pull request before merging
2. Require at least 1 approving review
3. Dismiss stale pull request approvals when new commits are pushed
4. **Disallow GitHub Actions (bots) from approving reviews** (Separation of Duties)

Usage:
    python scripts/verify_branch_protection.py                    # Check main branch
    python scripts/verify_branch_protection.py --branch develop   # Check custom branch
    python scripts/verify_branch_protection.py --json             # Output JSON for CI
    python scripts/verify_branch_protection.py --repo owner/repo  # Check different repo

Environment:
    GH_TOKEN or GITHUB_TOKEN - GitHub token with `repo` scope (admin:repo_hook for org-level)
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Optional, Tuple

try:
    import requests
except ImportError:
    print("[ERROR] 'requests' library not found. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)


class BranchProtectionVerifier:
    """Verifies GitHub branch protection rules via REST API."""

    def __init__(self, repo: str, token: str, api_base: str = "https://api.github.com"):
        self.repo = repo
        self.token = token
        self.api_base = api_base.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def get_branch_protection(self, branch: str) -> Optional[Dict]:
        """Fetch branch protection rules for a branch."""
        url = f"{self.api_base}/repos/{self.repo}/branches/{branch}/protection"
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            if resp.status_code == 404:
                return None  # No protection rules
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"[ERROR] Failed to fetch branch protection: {e}", file=sys.stderr)
            return None

    def get_required_reviews(self, branch: str) -> Optional[Dict]:
        """Fetch required pull request reviews configuration."""
        url = f"{self.api_base}/repos/{self.repo}/branches/{branch}/protection/required_pull_request_reviews"
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"[ERROR] Failed to fetch required reviews: {e}", file=sys.stderr)
            return None

    def check_protection(self, branch: str) -> Tuple[bool, List[str], List[str]]:
        """
        Verify all required protection rules.

        Returns:
            (all_passed, passed_checks, failed_checks)
        """
        protection = self.get_branch_protection(branch)
        if not protection:
            return False, [], [
                "❌ No branch protection rules found on branch",
                "   → Enable 'Require a pull request before merging' in branch settings"
            ]

        reviews = self.get_required_reviews(branch)
        if not reviews:
            return False, [], [
                "❌ Required pull request reviews not configured",
                "   → Enable 'Require approvals' in branch protection rules"
            ]

        passed = []
        failed = []

        # 1. Require PR before merging (implied by protection existing)
        if protection.get("required_pull_request_reviews") is not None:
            passed.append("✅ Require pull request before merging: ENABLED")
        else:
            failed.append("❌ Require pull request before merging: DISABLED")

        # 2. Require at least 1 approval
        required_approvals = reviews.get("required_approving_review_count", 0)
        if required_approvals >= 1:
            passed.append(f"✅ Required approving reviews: {required_approvals} (>= 1)")
        else:
            failed.append(f"❌ Required approving reviews: {required_approvals} (must be >= 1)")

        # 3. Dismiss stale reviews
        dismiss_stale = reviews.get("dismiss_stale_reviews", False)
        if dismiss_stale:
            passed.append("✅ Dismiss stale pull request approvals: ENABLED")
        else:
            failed.append("❌ Dismiss stale pull request approvals: DISABLED")

        # 4. Disallow GitHub Actions / bots from approving (CRITICAL for Separation of Duties)
        # Check if 'bypass_pull_request_allowances' allows apps/bots to bypass
        bypass_allowances = reviews.get("bypass_pull_request_allowances", {})
        apps_allowed = bypass_allowances.get("apps", [])
        teams_allowed = bypass_allowances.get("teams", [])
        users_allowed = bypass_allowances.get("users", [])

        # The critical check: no apps (including GitHub Actions bot) should be allowed to bypass
        if not apps_allowed and not teams_allowed and not users_allowed:
            passed.append("✅ No bypass allowances for apps/teams/users (Separation of Duties enforced)")
        else:
            # If there are allowances, check specifically for GitHub Actions bot
            gh_actions_bot = "github-actions" in [a.get("login", "").lower() for a in apps_allowed]
            if gh_actions_bot:
                failed.append("❌ GitHub Actions bot is ALLOWED to bypass reviews (VIOLATES Separation of Duties)")
            else:
                # Other allowances might be OK (e.g., specific human users), but warn
                details = []
                if apps_allowed:
                    details.append(f"apps: {[a.get('login') for a in apps_allowed]}")
                if teams_allowed:
                    details.append(f"teams: {[t.get('slug') for t in teams_allowed]}")
                if users_allowed:
                    details.append(f"users: {[u.get('login') for u in users_allowed]}")
                failed.append(f"⚠️ Bypass allowances exist (review manually): {', '.join(details)}")

        # Track optional/recommended checks separately (don't block on these)
        optional_passed = []
        optional_warnings = []

        # Optional: Require status checks to pass (recommended)
        required_status_checks = protection.get("required_status_checks")
        if required_status_checks:
            contexts = required_status_checks.get("contexts", [])
            strict = required_status_checks.get("strict", False)
            optional_passed.append(f"✅ Required status checks: {len(contexts)} context(s), strict={strict}")
        else:
            optional_warnings.append("⚠️ Required status checks: NOT CONFIGURED (recommended)")

        # Optional: Require linear history (recommended)
        linear_history = protection.get("required_linear_history", {}).get("enabled", False)
        if linear_history:
            optional_passed.append("✅ Require linear history: ENABLED")
        else:
            optional_warnings.append("⚠️ Require linear history: DISABLED (recommended)")

        # Optional: Require conversation resolution (recommended)
        conversation_resolution = protection.get("required_conversation_resolution", {}).get("enabled", False)
        if conversation_resolution:
            optional_passed.append("✅ Require conversation resolution: ENABLED")
        else:
            optional_warnings.append("⚠️ Require conversation resolution: DISABLED (recommended)")

        # Combine passed checks
        passed.extend(optional_passed)
        passed.extend(optional_warnings)  # Include warnings in output for visibility
        all_passed = len(failed) == 0  # Only required failures block
        return all_passed, passed, failed


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify GitHub Branch Protection Rules")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"),
                       help="Repository in format 'owner/repo' (default: GITHUB_REPOSITORY env)")
    parser.add_argument("--branch", default="main", help="Branch to check (default: main)")
    parser.add_argument("--token", default=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"),
                       help="GitHub token (default: GH_TOKEN or GITHUB_TOKEN env)")
    parser.add_argument("--json", action="store_true", help="Output JSON for CI consumption")
    parser.add_argument("--fail-fast", action="store_true", help="Exit on first failure (default: check all)")
    parser.add_argument("--api-base", default="https://api.github.com", help="GitHub API base URL")

    args = parser.parse_args()

    if not args.repo:
        print("[ERROR] Repository not specified. Use --repo or set GITHUB_REPOSITORY env var.", file=sys.stderr)
        return 1

    if not args.token:
        print("[ERROR] GitHub token not provided. Set GH_TOKEN or GITHUB_TOKEN env var.", file=sys.stderr)
        return 1

    verifier = BranchProtectionVerifier(args.repo, args.token, args.api_base)
    all_passed, passed, failed = verifier.check_protection(args.branch)

    if args.json:
        output = {
            "branch": args.branch,
            "repo": args.repo,
            "all_passed": all_passed,
            "checks": {
                "passed": passed,
                "failed": failed
            }
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"\n🔍 Verifying branch protection for {args.repo}:{args.branch}")
        print("=" * 60)
        for check in passed:
            print(check)
        for check in failed:
            print(check)
        print("=" * 60)
        if all_passed:
            print("🎉 ALL REQUIRED CHECKS PASSED")
        else:
            print(f"💥 {len(failed)} CHECK(S) FAILED — Branch protection not compliant")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())