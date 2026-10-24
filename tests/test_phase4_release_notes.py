#!/usr/bin/env python3
"""
Test suite for Phase 4 Release Notes Automation (4A).

Tests cover:
- Conventional commit parsing
- Release note generation from merged PRs
- Categorization: Features, Fixes, Breaking Changes, Security, Dependencies
- GitHub Releases integration
- CHANGELOG.md integration
- Trigger on tag push / main merge
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestReleaseNotesAutomation:
    """Test cases for release notes generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp(prefix="release_notes_test_")
        self.repo_dir = Path(self.test_dir) / "test_repo"
        self.repo_dir.mkdir()
        self._init_git_repo()

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _init_git_repo(self):
        """Initialize a git repo with conventional commits."""
        subprocess.run(["git", "init"], cwd=self.repo_dir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.repo_dir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.repo_dir, capture_output=True)

        # Create initial commit
        (self.repo_dir / "README.md").write_text("# Test Repo\n")
        subprocess.run(["git", "add", "."], cwd=self.repo_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "chore: initial commit"], cwd=self.repo_dir, capture_output=True)

    def _run_git(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run git command in test repo."""
        return subprocess.run(["git"] + args, cwd=self.repo_dir, capture_output=True, text=True)

    def _make_commit(self, message: str, files: Optional[Dict[str, str]] = None):
        """Create a commit with given message and optional files."""
        if files:
            for path, content in files.items():
                file_path = self.repo_dir / path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
        self._run_git(["add", "."])
        self._run_git(["commit", "-m", message])

    def _create_tag(self, tag_name: str):
        """Create a git tag."""
        self._run_git(["tag", tag_name])

    def test_script_exists(self):
        """Test that release_notes.py script exists."""
        script_path = PROJECT_ROOT / "scripts" / "release_notes.py"
        assert script_path.exists(), f"Script not found: {script_path}"

    def test_script_help(self):
        """Test that script shows help with --help flag."""
        script_path = PROJECT_ROOT / "scripts" / "release_notes.py"
        result = subprocess.run([sys.executable, str(script_path), "--help"], capture_output=True, text=True)
        assert result.returncode == 0
        assert "release" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_conventional_commit_parsing(self):
        """Test parsing of conventional commit messages."""
        from scripts.release_notes import parse_conventional_commit

        # Test feat
        result = parse_conventional_commit("feat: add new API endpoint")
        assert result["type"] == "feat"
        assert result["scope"] is None
        assert result["description"] == "add new API endpoint"
        assert result["breaking"] is False

        # Test feat with scope
        result = parse_conventional_commit("feat(api): add new endpoint")
        assert result["type"] == "feat"
        assert result["scope"] == "api"

        # Test fix
        result = parse_conventional_commit("fix: resolve memory leak")
        assert result["type"] == "fix"

        # Test breaking change
        result = parse_conventional_commit("feat: new API!\n\nBREAKING CHANGE: API v2 incompatible")
        assert result["breaking"] is True

        # Test chore (should be categorized but not in release notes)
        result = parse_conventional_commit("chore: update dependencies")
        assert result["type"] == "chore"

    def test_commit_categorization(self):
        """Test categorization of commits into release note sections."""
        from scripts.release_notes import categorize_commits

        commits = [
            {"type": "feat", "scope": "api", "description": "add user endpoint", "breaking": False, "hash": "abc123"},
            {"type": "feat", "scope": "ui", "description": "new dashboard", "breaking": False, "hash": "def456"},
            {"type": "fix", "scope": "auth", "description": "token refresh bug", "breaking": False, "hash": "ghi789"},
            {"type": "fix", "scope": None, "description": "typo in docs", "breaking": False, "hash": "jkl012"},
            {"type": "feat", "scope": "api", "description": "v2 migration", "breaking": True, "hash": "mno345"},
            {"type": "security", "scope": "auth", "description": "fix XSS vulnerability", "breaking": False, "hash": "pqr678"},
            {"type": "chore", "scope": "deps", "description": "update lodash", "breaking": False, "hash": "stu901"},
        ]

        categories = categorize_commits(commits)

        assert "Features" in categories
        assert len(categories["Features"]) == 2
        assert "Fixes" in categories
        assert len(categories["Fixes"]) == 2
        assert "Breaking Changes" in categories
        assert len(categories["Breaking Changes"]) == 1
        assert "Security" in categories
        assert len(categories["Security"]) == 1
        assert "Dependencies" not in categories or len(categories.get("Dependencies", [])) == 0

    def test_release_notes_generation(self):
        """Test generation of release notes from commits."""
        from scripts.release_notes import generate_release_notes

        commits = [
            {"type": "feat", "scope": "api", "description": "add user endpoint", "breaking": False, "hash": "abc123"},
            {"type": "fix", "scope": "auth", "description": "token refresh bug", "breaking": False, "hash": "def456"},
            {"type": "feat", "scope": "api", "description": "v2 migration", "breaking": True, "hash": "ghi789"},
        ]

        notes = generate_release_notes("v1.2.0", commits, "v1.1.0")

        assert "v1.2.0" in notes
        assert "Features" in notes
        assert "add user endpoint" in notes
        assert "Fixes" in notes
        assert "token refresh bug" in notes
        assert "Breaking Changes" in notes
        assert "v2 migration" in notes

    def test_changelog_update(self):
        """Test CHANGELOG.md update with new release notes."""
        from scripts.release_notes import update_changelog

        changelog_path = self.repo_dir / "CHANGELOG.md"
        changelog_path.write_text("# Changelog\n\n## [Unreleased]\n")

        new_notes = "## [v1.2.0] - 2024-01-15\n\n### Features\n- Add user endpoint\n"

        update_changelog(changelog_path, new_notes, "v1.2.0")

        content = changelog_path.read_text()
        assert "v1.2.0" in content
        assert "Add user endpoint" in content
        assert "[Unreleased]" in content  # Should preserve Unreleased section

    def test_github_release_creation(self):
        """Test GitHub release creation (mocked)."""
        from scripts.release_notes import create_github_release

        # This should work without actual GitHub API (mocked or dry-run)
        result = create_github_release(
            tag="v1.2.0",
            title="Release v1.2.0",
            body="Release notes here",
            draft=False,
            prerelease=False,
            dry_run=True
        )

        assert result["success"] is True
        assert "dry_run" in result or "mock" in str(result).lower()

    def test_main_merge_trigger(self):
        """Test that release notes are generated on main merge (simulated)."""
        from scripts.release_notes import should_generate_on_merge

        # Merge to main should trigger
        assert should_generate_on_merge("main", "feature/abc") is True
        assert should_generate_on_merge("main", "hotfix/xyz") is True

        # Non-main merges should not trigger
        assert should_generate_on_merge("develop", "feature/abc") is False
        assert should_generate_on_merge("staging", "feature/abc") is False

    def test_tag_push_trigger(self):
        """Test that release notes are generated on tag push."""
        from scripts.release_notes import should_generate_on_tag

        # Version tags should trigger
        assert should_generate_on_tag("v1.2.0") is True
        assert should_generate_on_tag("v2.0.0-rc.1") is True
        assert should_generate_on_tag("release/1.2.0") is True

        # Non-version tags should not trigger
        assert should_generate_on_tag("latest") is False
        assert should_generate_on_tag("test-tag") is False

    def test_get_commits_since_tag(self):
        """Test retrieving commits since last tag."""
        from scripts.release_notes import get_commits_since_tag

        # Create some commits
        self._make_commit("feat: add feature A")
        self._make_commit("fix: fix bug B")
        self._create_tag("v1.0.0")
        self._make_commit("feat: add feature C")
        self._make_commit("fix: fix bug D")

        commits = get_commits_since_tag(self.repo_dir, "v1.0.0")

        assert len(commits) == 2
        assert any("feature C" in c["description"] for c in commits)
        assert any("bug D" in c["description"] for c in commits)

    def test_empty_release_notes(self):
        """Test handling of no new commits since last tag."""
        from scripts.release_notes import generate_release_notes

        notes = generate_release_notes("v1.1.0", [], "v1.0.0")
        assert "No changes" in notes or "no changes" in notes.lower() or len(notes.strip()) == 0


if __name__ == "__main__":
    # Run tests manually for quick verification
    test = TestReleaseNotesAutomation()
    test.setup_method()
    try:
        test.test_script_exists()
        print("✅ test_script_exists passed")
    except Exception as e:
        print(f"❌ test_script_exists failed: {e}")

    try:
        test.test_script_help()
        print("✅ test_script_help passed")
    except Exception as e:
        print(f"❌ test_script_help failed: {e}")

    try:
        test.test_conventional_commit_parsing()
        print("✅ test_conventional_commit_parsing passed")
    except Exception as e:
        print(f"❌ test_conventional_commit_parsing failed: {e}")

    try:
        test.test_commit_categorization()
        print("✅ test_commit_categorization passed")
    except Exception as e:
        print(f"❌ test_commit_categorization failed: {e}")

    try:
        test.test_release_notes_generation()
        print("✅ test_release_notes_generation passed")
    except Exception as e:
        print(f"❌ test_release_notes_generation failed: {e}")

    try:
        test.test_changelog_update()
        print("✅ test_changelog_update passed")
    except Exception as e:
        print(f"❌ test_changelog_update failed: {e}")

    try:
        test.test_github_release_creation()
        print("✅ test_github_release_creation passed")
    except Exception as e:
        print(f"❌ test_github_release_creation failed: {e}")

    try:
        test.test_main_merge_trigger()
        print("✅ test_main_merge_trigger passed")
    except Exception as e:
        print(f"❌ test_main_merge_trigger failed: {e}")

    try:
        test.test_tag_push_trigger()
        print("✅ test_tag_push_trigger passed")
    except Exception as e:
        print(f"❌ test_tag_push_trigger failed: {e}")

    try:
        test.test_get_commits_since_tag()
        print("✅ test_get_commits_since_tag passed")
    except Exception as e:
        print(f"❌ test_get_commits_since_tag failed: {e}")

    try:
        test.test_empty_release_notes()
        print("✅ test_empty_release_notes passed")
    except Exception as e:
        print(f"❌ test_empty_release_notes failed: {e}")

    test.teardown_method()
    print("\n🔴 RED PHASE: All tests should FAIL (scripts not implemented yet)")