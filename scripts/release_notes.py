#!/usr/bin/env python3
"""
Release Notes Automation Script (4A).

Generates release notes from conventional commits, updates CHANGELOG.md,
and creates GitHub releases.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


@dataclass
class ParsedCommit:
    """Parsed conventional commit."""
    type: str
    scope: Optional[str]
    description: str
    breaking: bool
    hash: str
    raw_message: str

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access for test compatibility."""
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        """Allow dict-like get for test compatibility."""
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        """Allow 'in' operator for test compatibility."""
        return hasattr(self, key)


# Conventional commit type mapping to release note categories
TYPE_CATEGORIES = {
    "feat": "Features",
    "fix": "Fixes",
    "perf": "Performance",
    "refactor": "Refactoring",
    "security": "Security",
    "docs": "Documentation",
    "style": "Styling",
    "test": "Tests",
    "chore": "Chores",
    "build": "Build",
    "ci": "CI",
    "revert": "Reverts",
}

# Types that appear in release notes (in order)
RELEASE_CATEGORIES = [
    "Breaking Changes",
    "Security",
    "Features",
    "Fixes",
    "Performance",
    "Refactoring",
    "Documentation",
    "Tests",
    "Build",
    "CI",
    "Chores",
    "Reverts",
]


def parse_conventional_commit(message: str, commit_hash: str = "") -> ParsedCommit:
    """
    Parse a conventional commit message.

    Format: <type>(<scope>): <description>
    Or with breaking change: <type>(<scope>)!: <description>
    Or with BREAKING CHANGE in body.
    """
    lines = message.strip().split("\n")
    header = lines[0] if lines else ""

    # Parse header: type(scope)!: description
    match = re.match(r"^(\w+)(?:\(([^)]+)\))?(!)?:\s*(.+)$", header)
    if not match:
        # Non-conventional commit
        return ParsedCommit(
            type="chore",
            scope=None,
            description=header,
            breaking=False,
            hash=commit_hash,
            raw_message=message,
        )

    commit_type, scope, breaking_marker, description = match.groups()

    # Check for BREAKING CHANGE in body
    breaking = breaking_marker == "!" or any(
        "BREAKING CHANGE:" in line.upper() for line in lines[1:]
    )

    return ParsedCommit(
        type=commit_type.lower(),
        scope=scope,
        description=description,
        breaking=breaking,
        hash=commit_hash[:7] if commit_hash else "",
        raw_message=message,
    )


def categorize_commits(commits: List[ParsedCommit]) -> Dict[str, List[ParsedCommit]]:
    """Categorize commits into release note sections."""
    categories: Dict[str, List[ParsedCommit]] = {cat: [] for cat in RELEASE_CATEGORIES}

    for commit in commits:
        # Handle both ParsedCommit objects and dicts (for test compatibility)
        breaking = commit.get("breaking", False) if isinstance(commit, dict) else commit.breaking
        commit_type = commit.get("type", "chore") if isinstance(commit, dict) else commit.type

        if breaking:
            categories["Breaking Changes"].append(commit)
        else:
            category = TYPE_CATEGORIES.get(commit_type, "Chores")
            if category in categories:
                categories[category].append(commit)

    # Remove empty categories
    return {k: v for k, v in categories.items() if v}


def generate_release_notes(
    version: str,
    commits: List[ParsedCommit],
    previous_version: Optional[str] = None,
    repo_path: Optional[Path] = None,
) -> str:
    """Generate release notes markdown from commits."""
    lines = []

    # Header
    date_str = datetime.now().strftime("%Y-%m-%d")
    lines.append(f"## [{version}] - {date_str}")
    lines.append("")

    if previous_version:
        lines.append(f"*Compare: [{previous_version}...{version}](https://github.com/{{repo}}/compare/{previous_version}...{version})*")
        lines.append("")

    # Categorize
    categories = categorize_commits(commits)

    for category in RELEASE_CATEGORIES:
        if category not in categories:
            continue
        cat_commits = categories[category]
        if not cat_commits:
            continue

        lines.append(f"### {category}")
        lines.append("")

        for commit in cat_commits:
            # Handle both ParsedCommit objects and dicts (for test compatibility)
            description = commit.get("description", "") if isinstance(commit, dict) else commit.description
            scope = commit.get("scope", None) if isinstance(commit, dict) else commit.scope
            commit_hash = commit.get("hash", "") if isinstance(commit, dict) else commit.hash

            scope_part = f"({scope})" if scope else ""
            hash_part = f" [{commit_hash}]" if commit_hash else ""
            lines.append(f"- {description}{scope_part}{hash_part}")

        lines.append("")

    if not categories:
        lines.append("*No changes in this release.*")
        lines.append("")

    return "\n".join(lines).strip()


def update_changelog(changelog_path: Path, new_notes: str, version: str) -> None:
    """Update CHANGELOG.md with new release notes."""
    if not changelog_path.exists():
        changelog_path.write_text("# Changelog\n\n## [Unreleased]\n")

    content = changelog_path.read_text(encoding="utf-8")

    # Find the [Unreleased] section and insert after it
    unreleased_pattern = r"(##\s*\[Unreleased\])"
    match = re.search(unreleased_pattern, content)
    if match:
        insert_pos = match.end()
        new_content = content[:insert_pos] + "\n\n" + new_notes + "\n" + content[insert_pos:]
    else:
        # No [Unreleased] section, prepend after first heading
        first_heading = re.search(r"^#\s+.+$", content, re.MULTILINE)
        if first_heading:
            insert_pos = first_heading.end()
            new_content = content[:insert_pos] + "\n\n" + new_notes + "\n" + content[insert_pos:]
        else:
            new_content = "# Changelog\n\n" + new_notes + "\n\n" + content

    changelog_path.write_text(new_content, encoding="utf-8")


def create_github_release(
    tag: str,
    title: str,
    body: str,
    draft: bool = False,
    prerelease: bool = False,
    dry_run: bool = False,
    repo: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a GitHub release (or simulate in dry-run)."""
    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "tag": tag,
            "title": title,
            "prerelease": prerelease,
            "draft": draft,
        }

    # Real implementation would use gh CLI or GitHub API
    # For now, return success structure
    cmd = ["gh", "release", "create", tag, "--title", title, "--notes", body]
    if draft:
        cmd.append("--draft")
    if prerelease:
        cmd.append("--prerelease")
    if repo:
        cmd.extend(["--repo", repo])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return {
            "success": True,
            "output": result.stdout,
            "tag": tag,
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "error": e.stderr,
            "tag": tag,
        }


def should_generate_on_merge(target_branch: str, source_branch: str) -> bool:
    """Check if release notes should be generated on merge to target branch."""
    return target_branch in ("main", "master")


def should_generate_on_tag(tag: str) -> bool:
    """Check if release notes should be generated on tag push."""
    # Match version tags: v1.2.3, v2.0.0-rc.1, release/1.2.0
    version_tag_pattern = r"^(v?\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?|release/\d+\.\d+(\.\d+)?)$"
    return bool(re.match(version_tag_pattern, tag))


def get_commits_since_tag(repo_path: Path, tag: str) -> List[ParsedCommit]:
    """Get commits since the given tag."""
    try:
        # Get commits between tag and HEAD
        result = subprocess.run(
            ["git", "log", f"{tag}..HEAD", "--pretty=format:%H|%s", "--no-merges"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return []

    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|", 1)
        if len(parts) == 2:
            commit_hash, subject = parts
            # Get full message for breaking change detection
            msg_result = subprocess.run(
                ["git", "show", "-s", "--format=%B", commit_hash],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            full_message = msg_result.stdout.strip()
            commits.append(parse_conventional_commit(full_message, commit_hash))

    return commits


def get_last_tag(repo_path: Path) -> Optional[str]:
    """Get the most recent version tag."""
    try:
        result = subprocess.run(
            ["git", "tag", "--list", "--sort=-v:refname"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        tags = result.stdout.strip().split("\n")
        for tag in tags:
            if should_generate_on_tag(tag):
                return tag
    except subprocess.CalledProcessError:
        pass
    return None


def main():
    parser = argparse.ArgumentParser(description="Generate release notes from conventional commits")
    parser.add_argument("--version", help="Version tag (e.g., v1.2.0)")
    parser.add_argument("--previous-version", help="Previous version tag")
    parser.add_argument("--repo-path", default=".", help="Path to git repository")
    parser.add_argument("--changelog", help="Path to CHANGELOG.md")
    parser.add_argument("--output", help="Output file for release notes")
    parser.add_argument("--github-release", action="store_true", help="Create GitHub release")
    parser.add_argument("--title", help="Release title")
    parser.add_argument("--draft", action="store_true", help="Create draft release")
    parser.add_argument("--prerelease", action="store_true", help="Mark as prerelease")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no GitHub API calls)")
    parser.add_argument("--repo", help="GitHub repo (owner/repo)")

    args = parser.parse_args()

    repo_path = Path(args.repo_path).resolve()

    # Determine version
    version = args.version
    if not version:
        # Try to get from tag
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--exact-match"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                version = result.stdout.strip()
        except Exception:
            pass

    if not version:
        print("Error: --version required or must be on a tag", file=sys.stderr)
        return 1

    # Get previous version
    previous_version = args.previous_version
    if not previous_version:
        previous_version = get_last_tag(repo_path)

    # Get commits since last tag
    since_tag = previous_version or get_last_tag(repo_path)
    if since_tag:
        commits = get_commits_since_tag(repo_path, since_tag)
    else:
        # All commits
        try:
            result = subprocess.run(
                ["git", "log", "--pretty=format:%H|%s", "--no-merges"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            commits = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("|", 1)
                if len(parts) == 2:
                    commit_hash, subject = parts
                    msg_result = subprocess.run(
                        ["git", "show", "-s", "--format=%B", commit_hash],
                        cwd=repo_path,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    full_message = msg_result.stdout.strip()
                    commits.append(parse_conventional_commit(full_message, commit_hash))
        except subprocess.CalledProcessError:
            commits = []

    # Generate release notes
    notes = generate_release_notes(version, commits, previous_version, repo_path)

    # Output
    if args.output:
        Path(args.output).write_text(notes, encoding="utf-8")
    else:
        print(notes)

    # Update changelog
    if args.changelog:
        update_changelog(Path(args.changelog), notes, version)
        print(f"Updated {args.changelog}", file=sys.stderr)

    # Create GitHub release
    if args.github_release:
        title = args.title or f"Release {version}"
        result = create_github_release(
            tag=version,
            title=title,
            body=notes,
            draft=args.draft,
            prerelease=args.prerelease,
            dry_run=args.dry_run,
            repo=args.repo,
        )
        if result.get("success"):
            print(f"GitHub release created: {version}", file=sys.stderr)
        else:
            print(f"Failed to create GitHub release: {result.get('error')}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())