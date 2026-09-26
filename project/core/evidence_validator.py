"""Deterministic Evidence Gate Validator (AT-06).

Validates WorkerEvidence manifests against JSON Schema, ExecutionIdentity,
SHA-256 integrity hash, and Acceptance Criteria.
Enforces INVARIANT-03 and INVARIANT-04: LLM prose alone can never authorize DONE.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema

from project.core.evidence_models import WorkerEvidenceV1
from project.core.execution_identity import (
    ExecutionIdentity,
    InvalidIdentityError,
    StaleFencingTokenError,
    TicketMismatchError,
)

def _resolve_default_schema_path() -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "schemas" / "worker_evidence_v1.json",
        Path(__file__).resolve().parent.parent / "schemas" / "worker_evidence_v1.json",
        Path.cwd() / "schemas" / "worker_evidence_v1.json",
        Path("/app/schemas/worker_evidence_v1.json"),
        Path("/code/schemas/worker_evidence_v1.json"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


DEFAULT_SCHEMA_PATH = _resolve_default_schema_path()



@dataclass(frozen=True)
class EvidenceValidationResult:
    """Deterministic validation verdict."""

    is_valid: bool
    error_code: Optional[str] = None
    reasons: List[str] = None  # type: ignore

    def __post_init__(self):
        if self.reasons is None:
            object.__setattr__(self, "reasons", [])


class EvidenceValidator:
    """Deterministic validator for worker execution evidence."""

    def __init__(self, schema_path: Optional[Path] = None) -> None:
        path = schema_path or DEFAULT_SCHEMA_PATH
        with open(path, "r", encoding="utf-8") as f:
            self._schema = json.load(f)
        self._validator = jsonschema.Draft202012Validator(self._schema)

    def validate(
        self,
        evidence_payload: Dict[str, Any],
        expected_identity: Optional[ExecutionIdentity] = None,
    ) -> EvidenceValidationResult:
        """Run full deterministic validation suite on evidence payload."""
        reasons: List[str] = []

        # 1. JSON Schema Structural Validation
        errors = list(self._validator.iter_errors(evidence_payload))
        if errors:
            for err in errors:
                reasons.append(f"Schema error: {err.message} at path {list(err.path)}")
            return EvidenceValidationResult(
                is_valid=False,
                error_code="SCHEMA_VALIDATION_FAILED",
                reasons=reasons,
            )

        # 2. Cryptographic Integrity Hash Verification
        given_hash = evidence_payload.get("evidence_hash", "")
        expected_hash = WorkerEvidenceV1.compute_hash(evidence_payload)
        if given_hash != expected_hash:
            reasons.append(
                f"Integrity hash mismatch: payload={given_hash}, computed={expected_hash}"
            )
            return EvidenceValidationResult(
                is_valid=False,
                error_code="EVIDENCE_HASH_MISMATCH",
                reasons=reasons,
            )

        # 3. Execution Identity & Fencing Token Matching
        if expected_identity is not None:
            try:
                expected_identity.validate_mutation(
                    ticket_id=evidence_payload["ticket_id"],
                    attempt=evidence_payload["attempt"],
                    fencing_token=evidence_payload["fencing_token"],
                    lease_id=evidence_payload.get("lease_id"),
                )
                if expected_identity.session_id != evidence_payload["session_id"]:
                    reasons.append(
                        f"Session mismatch: active={expected_identity.session_id}, "
                        f"evidence={evidence_payload['session_id']}"
                    )
                    return EvidenceValidationResult(
                        is_valid=False,
                        error_code="STALE_SESSION",
                        reasons=reasons,
                    )
            except TicketMismatchError as exc:
                return EvidenceValidationResult(
                    is_valid=False,
                    error_code="TICKET_MISMATCH",
                    reasons=[str(exc)],
                )
            except StaleFencingTokenError as exc:
                return EvidenceValidationResult(
                    is_valid=False,
                    error_code="STALE_FENCING_TOKEN",
                    reasons=[str(exc)],
                )
            except InvalidIdentityError as exc:
                return EvidenceValidationResult(
                    is_valid=False,
                    error_code="INVALID_IDENTITY",
                    reasons=[str(exc)],
                )
            except Exception as exc:
                return EvidenceValidationResult(
                    is_valid=False,
                    error_code="IDENTITY_VALIDATION_ERROR",
                    reasons=[str(exc)],
                )

        # 4. Test Suite Execution Outcome
        tests = evidence_payload.get("tests", {})
        if tests.get("failed", 0) > 0:
            reasons.append(f"Test suite recorded {tests['failed']} failed tests")
            return EvidenceValidationResult(
                is_valid=False,
                error_code="TESTS_FAILED",
                reasons=reasons,
            )

        # 5. Acceptance Checks Outcome
        acceptance_checks = evidence_payload.get("acceptance_checks", [])
        for check in acceptance_checks:
            if check.get("status") == "failed":
                reasons.append(f"Acceptance check {check.get('check_id')} marked failed: {check.get('detail')}")
                return EvidenceValidationResult(
                    is_valid=False,
                    error_code="ACCEPTANCE_CHECK_FAILED",
                    reasons=reasons,
                )

        return EvidenceValidationResult(
            is_valid=True,
            error_code=None,
            reasons=["Evidence strictly valid and verified"],
        )
