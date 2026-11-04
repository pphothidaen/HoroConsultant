"""
tests/test_verify_branch_protection.py — Unit tests for Branch Protection Verifier.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from verify_branch_protection import BranchProtectionVerifier


@pytest.fixture
def mock_verifier():
    """Create a verifier with mocked requests."""
    with patch("verify_branch_protection.requests") as mock_requests:
        verifier = BranchProtectionVerifier("owner/repo", "fake-token")
        yield verifier, mock_requests


def test_no_protection_rules(mock_verifier):
    """Should fail when no protection rules exist."""
    verifier, mock_requests = mock_verifier
    mock_response = Mock()
    mock_response.status_code = 404
    mock_requests.get.return_value = mock_response

    all_passed, passed, failed = verifier.check_protection("main")
    assert not all_passed
    assert any("No branch protection rules found" in f for f in failed)


def test_all_checks_pass(mock_verifier):
    """Should pass when all required rules are configured correctly."""
    verifier, mock_requests = mock_verifier

    # Mock protection response
    protection_response = Mock()
    protection_response.status_code = 200
    protection_response.json.return_value = {
        "required_pull_request_reviews": {},
        "required_status_checks": {"contexts": ["ci/test", "ci/lint"], "strict": True},
        "required_linear_history": {"enabled": True},
        "required_conversation_resolution": {"enabled": True},
    }

    # Mock required reviews response
    reviews_response = Mock()
    reviews_response.status_code = 200
    reviews_response.json.return_value = {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews": True,
        "bypass_pull_request_allowances": {
            "apps": [],
            "teams": [],
            "users": []
        }
    }

    mock_requests.get.side_effect = [protection_response, reviews_response]

    all_passed, passed, failed = verifier.check_protection("main")
    assert all_passed
    assert len(failed) == 0
    assert any("Require pull request before merging: ENABLED" in p for p in passed)
    assert any("Required approving reviews: 1" in p for p in passed)
    assert any("Dismiss stale pull request approvals: ENABLED" in p for p in passed)
    assert any("Separation of Duties enforced" in p for p in passed)


def test_github_actions_bot_allowed_to_bypass(mock_verifier):
    """Should fail when GitHub Actions bot can bypass reviews."""
    verifier, mock_requests = mock_verifier

    protection_response = Mock()
    protection_response.status_code = 200
    protection_response.json.return_value = {
        "required_pull_request_reviews": {},
        "required_status_checks": None,
        "required_linear_history": {"enabled": False},
        "required_conversation_resolution": {"enabled": False},
    }

    reviews_response = Mock()
    reviews_response.status_code = 200
    reviews_response.json.return_value = {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews": True,
        "bypass_pull_request_allowances": {
            "apps": [{"login": "github-actions"}],
            "teams": [],
            "users": []
        }
    }

    mock_requests.get.side_effect = [protection_response, reviews_response]

    all_passed, passed, failed = verifier.check_protection("main")
    assert not all_passed
    assert any("GitHub Actions bot is ALLOWED to bypass reviews" in f for f in failed)


def test_insufficient_approvals(mock_verifier):
    """Should fail when required approvals < 1."""
    verifier, mock_requests = mock_verifier

    protection_response = Mock()
    protection_response.status_code = 200
    protection_response.json.return_value = {"required_pull_request_reviews": {}}

    reviews_response = Mock()
    reviews_response.status_code = 200
    reviews_response.json.return_value = {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews": True,
        "bypass_pull_request_allowances": {"apps": [], "teams": [], "users": []}
    }

    mock_requests.get.side_effect = [protection_response, reviews_response]

    all_passed, passed, failed = verifier.check_protection("main")
    assert not all_passed
    assert any("Required approving reviews: 0 (must be >= 1)" in f for f in failed)


def test_dismiss_stale_disabled(mock_verifier):
    """Should fail when dismiss stale reviews is disabled."""
    verifier, mock_requests = mock_verifier

    protection_response = Mock()
    protection_response.status_code = 200
    protection_response.json.return_value = {"required_pull_request_reviews": {}}

    reviews_response = Mock()
    reviews_response.status_code = 200
    reviews_response.json.return_value = {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews": False,
        "bypass_pull_request_allowances": {"apps": [], "teams": [], "users": []}
    }

    mock_requests.get.side_effect = [protection_response, reviews_response]

    all_passed, passed, failed = verifier.check_protection("main")
    assert not all_passed
    assert any("Dismiss stale pull request approvals: DISABLED" in f for f in failed)


def test_optional_checks_warn_only(mock_verifier):
    """Optional checks (status checks, linear history, conversation resolution) should warn but not fail."""
    verifier, mock_requests = mock_verifier

    protection_response = Mock()
    protection_response.status_code = 200
    protection_response.json.return_value = {
        "required_pull_request_reviews": {},
        "required_status_checks": None,
        "required_linear_history": {"enabled": False},
        "required_conversation_resolution": {"enabled": False},
    }

    reviews_response = Mock()
    reviews_response.status_code = 200
    reviews_response.json.return_value = {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews": True,
        "bypass_pull_request_allowances": {"apps": [], "teams": [], "users": []}
    }

    mock_requests.get.side_effect = [protection_response, reviews_response]

    all_passed, passed, failed = verifier.check_protection("main")
    # Required checks pass, optional checks show as warnings but don't block
    assert all_passed  # Still passes because only required checks block
    # Optional warnings should not be in failed list (they don't block)
    assert not any("NOT CONFIGURED" in f for f in failed)
    assert not any("DISABLED (recommended)" in f for f in failed)
    # But they should be visible in passed list as warnings
    assert any("Required status checks: NOT CONFIGURED" in p for p in passed)
    assert any("Require linear history: DISABLED" in p for p in passed)
    assert any("Require conversation resolution: DISABLED" in p for p in passed)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])