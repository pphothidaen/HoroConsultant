#!/usr/bin/env python3
"""Jira agent-label governance gate.

Enforces the agent-* label taxonomy on the KAN board
(pansakorn.atlassian.net). Two modes:

  audit   - list all non-Epic issues missing an agent-* label
            (exit 1 if any found; used by cron/CI sweeps)
  check   - verify a single issue carries an agent-* label
            (used by quality gate before transitions/merges)

Read-only: never mutates Jira issues. Standard library only.
Credentials come from .env (JIRA_API_TOKEN, JIRA_EMAIL, JIRA_BASE_URL)
following the two-tier secret architecture - never hardcoded.

Exit codes:
  0 = all issues carry an agent-* label
  1 = governance violation found (or API failure in strict mode)
  2 = configuration error (missing credentials)
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, List, Optional
import re

DEFAULT_PROJECT = "KAN"
DEFAULT_SITE = "https://pansakorn.atlassian.net"

# Canonical agent label taxonomy (governance hook 2b).
AGENT_LABELS = [
    "agent-hermes",
    "agent-user",
    "agent-lead_ba",
    "agent-ba_auditor",
    "agent-ba_intake",
    "agent-code_reviewer",
    "agent-developer_core",
    "agent-developer_api",
    "agent-qa_tester",
    "agent-devops",
    "agent-orchestrator",
    "agent-agy1",
    "agent-agy2",
    "agent-agy3",
    "agent-agy4",
    "agent-agy5",
    "agent-codex1",
    "agent-codex2",
    "agent-codex3",
]

JQL_UNLABELED = (
    'project = {project} AND issuetype != Epic '
    'AND NOT (labels in ({label_list}))'
)


def load_env(path: str = ".env") -> dict:
    """Parse .env directly (source-safe: handles comments/export lines)."""
    env = {}
    if not os.path.isfile(path):
        return env
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):]
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def build_client(env: dict):
    token = env.get("JIRA_API_TOKEN") or os.environ.get("JIRA_API_TOKEN")
    email = env.get("JIRA_EMAIL") or os.environ.get("JIRA_EMAIL")
    site = env.get("JIRA_BASE_URL") or os.environ.get("JIRA_BASE_URL") or DEFAULT_SITE
    if not token or not email:
        return None, None, None
    secret = base64.b64encode(f"{email}:{token}".encode()).decode()
    return site, {"Authorization": f"Basic {secret}", "Content-Type": "application/json"}, token


def jira_request(site: str, headers: dict, method: str, path: str,
                 body: Optional[dict] = None, retries: int = 4) -> tuple[int, Any]:
    """Jira Cloud retry pattern: 429 -> 25s, 503 -> 15s, max 4 attempts."""
    last_error: Optional[Exception] = None
    for attempt in range(retries):
        request = urllib.request.Request(
            f"{site}{path}",
            method=method,
            headers=headers,
            data=json.dumps(body).encode() if body else None,
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read().decode() or "{}"
                return response.status, json.loads(raw)
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code == 429 and attempt < retries - 1:
                time.sleep(25)
                continue
            if error.code == 503 and attempt < retries - 1:
                time.sleep(15)
                continue
            body_text = error.read().decode() or ""
            return error.code, {"error": body_text[:200]}
        except (urllib.error.URLError, TimeoutError) as error:
            last_error = error
            if attempt < retries - 1:
                time.sleep(5)
                continue
    code = getattr(last_error, "code", 0) or 1
    return code, {"error": str(last_error)[:200]}


def fetch_unlabeled(site: str, headers: dict, project: str) -> tuple[int, list]:
    """Return (http_status, [issue keys missing agent-* labels])."""
    label_list = ", ".join(f'"{label}"' for label in AGENT_LABELS)
    jql = JQL_UNLABELED.format(project=project, label_list=label_list)
    status, data = jira_request(
        site, headers, "POST", "/rest/api/3/search/jql",
        {"jql": jql, "maxResults": 100, "fields": ["key", "labels", "summary", "issuetype"]},
    )
    if status not in (200, 201):
        return status, []
    issues = data.get("issues", []) if isinstance(data, dict) else []
    missing = [
        issue["key"] for issue in issues
        if not any(label.startswith("agent-") for label in issue.get("fields", {}).get("labels") or [])
    ]
    return status, missing


def fetch_issue(site: str, headers: dict, key: str) -> tuple[int, Any]:
    return jira_request(site, headers, "GET", f"/rest/api/3/issue/{key}?fields=labels,summary,status")


def cmd_audit(env: dict, project: str) -> int:
    site, headers, _ = build_client(env)
    if not site:
        print("[ERROR] Jira label audit blocked: missing JIRA_API_TOKEN/JIRA_EMAIL.")
        return 2
    status, missing = fetch_unlabeled(site, headers, project)
    if status not in (200, 201):
        print(f"[ERROR] Jira label audit failed: HTTP {status}.")
        return 1
    if not missing:
        print(f"[OK] All non-Epic issues in {project} carry an agent-* label.")
        return 0
    print(f"[ERROR] {len(missing)} issue(s) in {project} missing agent-* label:")
    for key in missing:
        print(f"  - {key}")
    print("[INFO] Add an agent-* label (default: agent-hermes) via "
          "mcp__atlassian__editJiraIssue or twg jira workitem update.")
    return 1


# ---------------------------------------------------------------------------
# Scope-relevance heuristic (KAN-181).
#
# `cmd_check` historically validated LABEL PRESENCE ONLY, so any ticket key
# that merely carried an agent-* label satisfied the gate. Real defect: a
# commit citing KAN-181 passed the gate against a stale KAN-133 key left in
# .git/COMMIT_EDITMSG, even though KAN-133's scope (renewable leases) had
# nothing to do with the commit (webhook dispatch).
#
# A label match is necessary but not sufficient evidence that the cited ticket
# is the right one. The comparison below is a WORD-OVERLAP heuristic, so it
# only ever adds a [WARN] line; it never changes a return value. Heuristics
# that could block a legitimate commit would be worse than no signal at all.
# ---------------------------------------------------------------------------

# Conventional-commit scaffolding and English glue carry no scope signal.
SCOPE_STOPWORDS = frozenset({
    "about", "above", "after", "again", "against", "also", "and", "are",
    "because", "been", "before", "being", "below", "between", "both", "but",
    "can", "cannot", "could", "did", "does", "doing", "done", "down", "during",
    "each", "few", "for", "from", "further", "had", "has", "have", "having",
    "her", "here", "hers", "him", "his", "how", "into", "its", "itself",
    "just", "let", "like", "make", "makes", "making", "more", "most", "much",
    "must", "myself", "not", "now", "off", "once", "only", "onto", "other",
    "our", "ours", "out", "over", "own", "same", "shall", "she", "should",
    "since", "some", "such", "than", "that", "the", "their", "theirs", "them",
    "then", "there", "these", "they", "this", "those", "through", "thus",
    "too", "under", "until", "upon", "use", "used", "uses", "using", "very",
    "was", "were", "what", "when", "where", "which", "while", "who", "whom",
    "why", "will", "with", "within", "would", "you", "your", "yours",
    # Conventional-commit type/scope verbs: ubiquitous in every subject line.
    "build", "chore", "ci", "docs", "feat", "feature", "fix", "fixes",
    "hotfix", "perf", "refactor", "revert", "style", "test", "tests",
    "wip", "add", "added", "adds", "bump", "improve", "improves", "move",
    "remove", "removes", "rename", "support", "tweak", "update", "updated",
    "updates",
})

# Below this length a token is noise ("ci", "fix") rather than scope signal.
SCOPE_MIN_TOKEN_LEN = 4

# Ticket keys ("KAN-181") and agent roster labels ("agent-hermes") are identity,
# not subject matter. Stripping them keeps a ticket from "matching" a commit
# purely because both mention the same key or the same agent lane.
_TICKET_KEY_RE = re.compile(r"\b[a-z]{2,}-\d+\b", re.IGNORECASE)
_AGENT_LABEL_RE = re.compile(r"\bagent-[a-z0-9_]+\b", re.IGNORECASE)
_WORD_RE = re.compile(r"[a-z0-9]+")


def _singular(word: str) -> str:
    """Cheap plural fold so 'labels' and 'label' match each other."""
    if len(word) > 4 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def scope_tokens(text: str | None) -> set:
    """Return the significant lowercase word tokens of `text`.

    Drops ticket keys, agent-* labels, stopwords, and very short words, and
    adds a singular variant alongside each plural so noun forms line up.
    """
    if not text:
        return set()
    cleaned = _TICKET_KEY_RE.sub(" ", _AGENT_LABEL_RE.sub(" ", str(text)))
    tokens: set = set()
    for word in _WORD_RE.findall(cleaned.lower()):
        if len(word) < SCOPE_MIN_TOKEN_LEN or word in SCOPE_STOPWORDS:
            continue
        tokens.add(word)
        singular = _singular(word)
        if singular != word:
            tokens.add(singular)
    return tokens


def scope_overlap(summary: str | None, commit_message: str | None):
    """Return the shared scope tokens, or None when the pair is not evaluable.

    None means "no evidence either way" - a missing summary, a missing commit
    message, or boilerplate-only input. Callers must treat None as silence,
    never as a mismatch.
    """
    summary_tokens = scope_tokens(summary)
    message_tokens = scope_tokens(commit_message)
    if not summary_tokens or not message_tokens:
        return None
    return summary_tokens & message_tokens


def _ascii_safe(value: str, limit: int = 120) -> str:
    """Fold to ASCII and clip, so the warning obeys scripts/AGENTS.md."""
    text = " ".join(str(value or "").split())
    text = text.encode("ascii", "replace").decode("ascii")
    if len(text) > limit:
        text = text[:limit].rstrip() + "..."
    return text


def cmd_check(env: dict, key: str, commit_message: str = "") -> int:
    site, headers, _ = build_client(env)
    if not site:
        print("[ERROR] Jira label check blocked: missing JIRA_API_TOKEN/JIRA_EMAIL.")
        return 2
    status, data = fetch_issue(site, headers, key)
    if status == 200:
        labels = data.get("fields", {}).get("labels") or []
        agent = [label for label in labels if label.startswith("agent-")]
        if agent:
            print(f"[OK] {key} carries agent label: {', '.join(agent)}")
            # Scope warning only. Never changes the return value: a heuristic
            # false positive must not block legitimate work.
            summary = data.get("fields", {}).get("summary") or ""
            overlap = scope_overlap(summary, commit_message)
            if overlap is not None and not overlap:
                subject = next((line.strip() for line in str(commit_message).splitlines()
                                if line.strip()), "")
                print(f"[WARN] {key} scope does not appear related to this commit.")
                print(f"[WARN]   ticket summary: {_ascii_safe(summary)}")
                print(f"[WARN]   commit subject: {_ascii_safe(subject)}")
                print("[INFO] Governance hook 2b: confirm the cited ticket is the correct")
                print("[INFO] ticket for this change. This is advisory and does not block.")
            return 0
        print(f"[ERROR] {key} has no agent-* label (labels: {', '.join(labels) or 'none'}).")
        print("[INFO] Governance hook 2b: every issue must carry an agent-* label.")
        return 1
    if status in (401, 403):
        print(f"[WARN] Jira credentials rejected (HTTP {status}) — governance check skipped.")
        return 2
    if status == 404:
        print(f"[WARN] {key} not found in Jira (HTTP 404) — cannot verify label, check skipped.")
        return 2
    print(f"[WARN] Jira API returned HTTP {status} for {key} — governance check skipped.")
    return 2




# ---------------------------------------------------------------------------
# Backward-compatibility layer (preserved from earlier governance version).
# These functions allow legacy callers (pre-kan-105 hooks, CI scripts) to
# validate agent-* labels via text matching rather than Jira API queries.
# ---------------------------------------------------------------------------

# Agent label pattern: agent- followed by alphanumeric, underscore, hyphen
LABEL_PATTERN = re.compile(r"\bagent-[a-zA-Z0-9][a-zA-Z0-9_-]*\b")

# Allowed agent prefixes (matches the known agent roster)
ALLOWED_AGENT_PREFIXES = [
    "agy1", "agy2", "agy3", "agy4", "agy5",
    "codex1", "codex2", "codex3",
    "hermes", "default",
]

# Commit types that bypass label requirement
BYPASS_PATTERNS = [
    r"^Merge\s",           # Merge commits
    r"^Revert\s",          # Revert commits
    r"^fixup!\s",          # Fixup commits
    r"^squash!\s",         # Squash commits
    r"^\s*(#\d+)\s*$",     # Empty commit messages
]


def get_staged_commit_message() -> Optional[str]:
    """Read commit message from COMMIT_EDITMSG or stdin.

    Kept for backward compatibility with legacy commit-msg hooks that
    import this function directly.
    """
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], "r") as f:
                return f.read()
        except FileNotFoundError:
            pass
    return None


def validate_commit_message(message: str) -> tuple[bool, List[str]]:
    """Validate that a commit message contains an agent-* label.

    Returns:
        (is_valid, issues): Whether the message is valid and list of issues.
    """
    issues: List[str] = []

    # Strip comments
    lines = message.split("\n")
    clean_lines = [l for l in lines if not l.startswith("#")]
    clean_message = "\n".join(clean_lines).strip()

    if not clean_message:
        return False, ["Empty commit message"]

    # Check bypass patterns
    for pattern in BYPASS_PATTERNS:
        if re.match(pattern, clean_message, re.IGNORECASE):
            return True, []

    # Find agent-* labels
    labels = LABEL_PATTERN.findall(clean_message)

    if not labels:
        issues.append(
            f"No agent-* label found. Expected one of: {', '.join(f'agent-{p}' for p in ALLOWED_AGENT_PREFIXES)}"
        )
        return False, issues

    # Validate labels are from known agents
    for label in labels:
        agent_name = label.replace("agent-", "", 1)
        if agent_name not in ALLOWED_AGENT_PREFIXES:
            issues.append(f"Unknown agent label: {label}")

    if issues:
        return False, issues

    return True, []


def _legacy_main() -> int:
    """Legacy entry point: read commit message from file arg, validate text."""
    message = get_staged_commit_message()
    if message is None:
        print("ERROR: No commit message provided", file=sys.stderr)
        return 1

    is_valid, issues = validate_commit_message(message)

    if not is_valid:
        print("AGENT LABEL CHECK FAILED:", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        print(
            "\nFix: Add an agent-* label to your commit message, e.g.:",
            file=sys.stderr,
        )
        print('  feat: add new feature [KAN-101] agent-hermes', file=sys.stderr)
        return 1

    return 0


def main(argv: list[str] | None = None) -> int:
    """Unified entry point.

    Dispatch logic:
      - If first positional arg is 'audit' or 'check' -> Jira API subcommand
      - Otherwise -> treat as commit message file (legacy mode)
    """
    if argv is None:
        argv = sys.argv[1:]

    # Detect subcommand mode (audit / check / with --flags)
    parser = argparse.ArgumentParser(
        description="Jira agent-label governance gate (KAN-105)",
        add_help=False,
    )
    parser.add_argument("--project", default=DEFAULT_PROJECT)
    parser.add_argument("--env", default=".env")
    subparsers = parser.add_subparsers(dest="mode")
    subparsers.add_parser("audit", help="audit all issues for missing agent-* labels")
    check_parser = subparsers.add_parser("check", help="check single issue for agent-* label")
    check_parser.add_argument("key")

    # If the first arg is 'audit' or 'check', use subcommand mode
    if argv and argv[0] in ("audit", "check", "--help", "-h"):
        args = parser.parse_args(argv)
        if args.mode == "audit":
            env = load_env(args.env)
            return cmd_audit(env, args.project)
        elif args.mode == "check":
            env = load_env(args.env)
            return cmd_check(env, args.key)
        else:
            parser.print_help()
            return 0
        return 0

    # Legacy mode: first arg is a commit message file path
    return _legacy_main()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
