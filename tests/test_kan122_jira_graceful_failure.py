"""KAN-122: Jira API helper graceful failure on 401/403/404."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import pytest
from unittest.mock import patch, MagicMock
from jira_api_helper import get_available_transitions, transition_issue


class TestJiraGraceful404:
    """Test that 404 responses return empty transitions without raising."""

    @patch('jira_api_helper.requests.get')
    @patch.dict(os.environ, {
        'JIRA_EMAIL': 'test@pansakorn.com',
        'JIRA_API_TOKEN': 'fake-token-123',
        'JIRA_DOMAIN': 'pansakorn.atlassian.net'
    })
    def test_404_returns_empty_transitions(self, mock_get):
        """404 response should return empty list (non-blocking)."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        transitions = get_available_transitions('KAN-NONEXISTENT')
        assert transitions == []

    @patch('jira_api_helper.requests.get')
    @patch.dict(os.environ, {
        'JIRA_EMAIL': 'test@pansakorn.com',
        'JIRA_API_TOKEN': 'fake-token-123',
        'JIRA_DOMAIN': 'pansakorn.atlassian.net'
    })
    def test_401_returns_empty_transitions(self, mock_get):
        """401 unauthorized should return empty list (non-blocking)."""
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_get.return_value = mock_resp

        transitions = get_available_transitions('KAN-121')
        assert transitions == []

    @patch('jira_api_helper.requests.get')
    @patch.dict(os.environ, {
        'JIRA_EMAIL': 'test@pansakorn.com',
        'JIRA_API_TOKEN': 'fake-token-123',
        'JIRA_DOMAIN': 'pansakorn.atlassian.net'
    })
    def test_403_returns_empty_transitions(self, mock_get):
        """403 forbidden should return empty list (non-blocking)."""
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_get.return_value = mock_resp

        transitions = get_available_transitions('KAN-121')
        assert transitions == []

    @patch('jira_api_helper.requests.get')
    @patch('jira_api_helper.requests.post')
    @patch.dict(os.environ, {
        'JIRA_EMAIL': 'test@pansakorn.com',
        'JIRA_API_TOKEN': 'fake-token-123',
        'JIRA_DOMAIN': 'pansakorn.atlassian.net'
    })
    def test_transition_issue_returns_true_on_missing_issue(self, mock_post, mock_get):
        """transition_issue should return True (skip) when issue is not found."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        # transition_issue calls get_available_transitions → empty → returns True (skip)
        result = transition_issue('KAN-NONEXISTENT', 'Review')
        assert result is True
