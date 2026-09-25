"""Typed Python models for Evidence Contract v1.0."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class TestResultSummary:
    """Aggregated test execution counters."""

    total: int
    passed: int
    failed: int
    skipped: int


@dataclass(frozen=True)
class AcceptanceCheck:
    """Individual Jira / task acceptance check outcome."""

    check_id: str
    status: str  # 'passed' | 'failed' | 'waived'
    detail: str


@dataclass(frozen=True)
class CommandReceipt:
    """Execution receipt for commands run during task."""

    command: str
    exit_code: int
    stdout_hash: str


@dataclass(frozen=True)
class ArtifactEvidence:
    """Produced artifact path and SHA-256 hash."""

    path: str
    sha256: str


@dataclass(frozen=True)
class WorkerEvidenceV1:
    """Full deterministic worker evidence manifest."""

    schema_version: str
    execution_id: str
    ticket_id: str
    attempt: int
    lease_id: str
    fencing_token: str
    session_id: str
    worker_id: str
    git_sha: str
    environment: str
    tests: TestResultSummary
    acceptance_checks: List[AcceptanceCheck]
    command_receipts: List[CommandReceipt]
    timestamp: str
    evidence_hash: str
    artifacts: Optional[List[ArtifactEvidence]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert evidence to standard dictionary."""
        d = asdict(self)
        if self.artifacts is None:
            d.pop("artifacts", None)
        return d

    def to_json(self) -> str:
        """Convert evidence to deterministic JSON string."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def compute_hash(cls, payload_without_hash: Dict[str, Any]) -> str:
        """Compute SHA-256 digest over normalized payload excluding evidence_hash."""
        data = {k: v for k, v in payload_without_hash.items() if k != "evidence_hash"}
        normalized = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
