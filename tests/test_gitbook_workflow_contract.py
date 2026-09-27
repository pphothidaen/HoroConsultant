"""TDD contract tests for the GitBook sync restoration (KAN-132).

Verifies that gitbook-docs.yaml was restored from git history and that the
gitbook-webhook-pr.yml workflow provides the webhook-to-PR bridge needed
for branch protection provenance checks.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
GITBOOK_DOCS_YAML = ROOT / "gitbook-docs.yaml"
WEBHOOK_WORKFLOW = ROOT / ".github/workflows/gitbook-webhook-pr.yml"
REPO_GUIDELINES = ROOT / "docs/repository-guidelines.md"


@pytest.fixture(scope="module")
def gitbook_doc() -> dict:
    assert GITBOOK_DOCS_YAML.exists(), "gitbook-docs.yaml must be restored"
    doc = yaml.safe_load(GITBOOK_DOCS_YAML.read_text(encoding="utf-8"))
    assert isinstance(doc, dict)
    return doc


@pytest.fixture(scope="module")
def webhook_doc() -> dict:
    assert WEBHOOK_WORKFLOW.exists(), "gitbook-webhook-pr.yml must exist"
    doc = yaml.safe_load(WEBHOOK_WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(doc, dict)
    return doc


@pytest.fixture(scope="module")
def guidelines_text() -> str:
    return REPO_GUIDELINES.read_text(encoding="utf-8")


# ── gitbook-docs.yaml ────────────────────────────────────────────────────

def test_gitbook_yaml_has_schema(gitbook_doc: dict) -> None:
    assert "$schema" in gitbook_doc
    assert "api.gitbook.com" in gitbook_doc["$schema"]


def test_gitbook_yaml_has_site_config(gitbook_doc: dict) -> None:
    assert "site" in gitbook_doc
    assert "structure" in gitbook_doc["site"]


# ── gitbook-webhook-pr.yml ───────────────────────────────────────────────

def test_workflow_name(webhook_doc: dict) -> None:
    assert webhook_doc["name"] == "GitBook Webhook to PR"


def test_workflow_triggers(webhook_doc: dict) -> None:
    on_block = webhook_doc.get("on", webhook_doc.get(True, {}))
    assert "workflow_dispatch" in on_block
    assert "repository_dispatch" in on_block


def test_repository_dispatch_event_type(webhook_doc: dict) -> None:
    on_block = webhook_doc.get("on", webhook_doc.get(True, {}))
    types = on_block["repository_dispatch"]["types"]
    assert "gitbook_docs_sync" in types


def test_workflow_permissions(webhook_doc: dict) -> None:
    perms = webhook_doc["permissions"]
    assert perms.get("contents") == "write"
    assert perms.get("pull-requests") == "write"


def test_workflow_has_pr_creation_step(webhook_doc: dict) -> None:
    steps = webhook_doc["jobs"]["gitbook-pr"]["steps"]
    names = [s.get("name", "") for s in steps]
    assert "Create PR" in names


def test_workflow_resolves_branch_params(webhook_doc: dict) -> None:
    steps = webhook_doc["jobs"]["gitbook-pr"]["steps"]
    names = [s.get("name", "") for s in steps]
    assert "Resolve sync parameters" in names


# ── docs/repository-guidelines.md ────────────────────────────────────────

def test_guidelines_documents_webhook_workflow(guidelines_text: str) -> None:
    """The GitBook integration section must document the webhook-to-PR solution."""
    assert "webhook" in guidelines_text.lower() or "repository_dispatch" in guidelines_text.lower()


def test_guidelines_no_failing_status(guidelines_text: str) -> None:
    """The guidelines must not declare GitBook sync as failing."""
    assert "CI status แสดง \"failure\"" not in guidelines_text
