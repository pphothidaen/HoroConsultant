"""Jira Untrusted Content Sanitizer and Security Boundary (AT-13).

Enforces INVARIANT-07: All Jira content is untrusted input.
Sanitizes titles, descriptions, and comments to neutralize prompt injection,
command injection, and delimiter escapement before reaching autonomous workers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


DANGEROUS_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+previous\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+all\s+prior", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+in\s+dan\s+mode", re.IGNORECASE),
    re.compile(r"system\s*:\s*override", re.IGNORECASE),
    re.compile(r"<\s*system\s*>", re.IGNORECASE),
    re.compile(r"\[\s*system_override\s*\]", re.IGNORECASE),
]


@dataclass(frozen=True)
class SanitizedJiraPayload:
    """Sanitized and encapsulated Jira issue payload."""

    ticket_id: str
    summary: str
    sanitized_description: str
    target_artifacts: List[str]
    verification_command: Optional[str]
    is_suspicious: bool
    stripped_patterns: List[str]


class JiraContentSanitizer:
    """Sanitizes incoming untrusted Jira content."""

    def sanitize(self, raw_issue: Dict[str, Any]) -> SanitizedJiraPayload:
        """Sanitize raw Jira issue dictionary."""
        ticket_id = str(raw_issue.get("key") or raw_issue.get("ticket_id") or "UNKNOWN")
        raw_summary = str(raw_issue.get("summary") or "")
        raw_desc = str(raw_issue.get("description") or "")
        target_artifacts = raw_issue.get("target_artifacts") or []
        verify_cmd = raw_issue.get("verification_command")

        # 1. Strip raw control characters
        clean_summary = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", raw_summary).strip()
        clean_desc = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", raw_desc).strip()

        # 2. Check and neutralize prompt injection attempts
        stripped: List[str] = []
        is_suspicious = False

        for pattern in DANGEROUS_INJECTION_PATTERNS:
            if pattern.search(clean_desc):
                is_suspicious = True
                stripped.append(pattern.pattern)
                clean_desc = pattern.sub("[REDACTED_SUSPICIOUS_PROMPT]", clean_desc)

            if pattern.search(clean_summary):
                is_suspicious = True
                stripped.append(pattern.pattern)
                clean_summary = pattern.sub("[REDACTED_PROMPT]", clean_summary)

        # 3. Sanitize artifacts path traversal attempts
        sanitized_artifacts = []
        for art in target_artifacts:
            art_str = str(art).strip()
            # Prevent absolute paths escaping workspace or ../ traversal
            if ".." in art_str or art_str.startswith("/"):
                is_suspicious = True
                stripped.append(f"path_traversal: {art_str}")
                continue
            sanitized_artifacts.append(art_str)

        return SanitizedJiraPayload(
            ticket_id=ticket_id,
            summary=clean_summary,
            sanitized_description=clean_desc,
            target_artifacts=sanitized_artifacts,
            verification_command=str(verify_cmd).strip() if verify_cmd else None,
            is_suspicious=is_suspicious,
            stripped_patterns=stripped,
        )
