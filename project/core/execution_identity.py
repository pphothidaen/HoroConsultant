"""Composite Execution Identity Contract and Error Semantics.

FROZEN CONTRACT for Sprint K:
Identity components:
  - execution_id: Globally unique monotonic execution attempt ID
  - ticket_id: Jira issue key / task ID (e.g. KAN-123)
  - attempt: 1-indexed attempt number
  - lease_id: Current active lease identifier (e.g. L-8f21)
  - fencing_token: Monotonic fencing token (integer/string)
  - session_id: Hermes/ControlPlane session identifier
  - worker_id: Ephemeral worker process identifier (e.g. node-herdr-01)
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Dict


class ExecutionIdentityError(Exception):
    """Base error for execution identity validation."""

    pass


class InvalidIdentityError(ExecutionIdentityError):
    """Raised when one or more identity components are missing or malformed."""

    pass


class StaleFencingTokenError(ExecutionIdentityError):
    """Raised when an operation is attempted with an outdated fencing token."""

    pass


class LeaseMismatchError(ExecutionIdentityError):
    """Raised when lease ID does not match current active lease."""

    pass


class TicketMismatchError(ExecutionIdentityError):
    """Raised when ticket ID does not match the target execution identity."""

    pass


@dataclass(frozen=True)
class ExecutionIdentity:
    """Immutable composite execution identity."""

    execution_id: str
    ticket_id: str
    attempt: int
    lease_id: str
    fencing_token: str
    session_id: str
    worker_id: str

    def __post_init__(self) -> None:
        """Validate required fields upon initialization."""
        if not self.execution_id or not isinstance(self.execution_id, str):
            raise InvalidIdentityError("execution_id must be a non-empty string")
        if not self.ticket_id or not isinstance(self.ticket_id, str):
            raise InvalidIdentityError("ticket_id must be a non-empty string")
        if not isinstance(self.attempt, int) or self.attempt < 1:
            raise InvalidIdentityError("attempt must be an integer >= 1")
        if not self.lease_id or not isinstance(self.lease_id, str):
            raise InvalidIdentityError("lease_id must be a non-empty string")
        if not self.fencing_token or not isinstance(self.fencing_token, str):
            raise InvalidIdentityError("fencing_token must be a non-empty string")
        if not self.session_id or not isinstance(self.session_id, str):
            raise InvalidIdentityError("session_id must be a non-empty string")
        if not self.worker_id or not isinstance(self.worker_id, str):
            raise InvalidIdentityError("worker_id must be a non-empty string")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize identity to standard dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize identity to deterministic JSON string."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExecutionIdentity:
        """Deserialize identity from dictionary with strict validation."""
        if not isinstance(data, dict):
            raise InvalidIdentityError("Identity payload must be a dictionary")
        required_keys = {
            "execution_id",
            "ticket_id",
            "attempt",
            "lease_id",
            "fencing_token",
            "session_id",
            "worker_id",
        }
        missing = required_keys - set(data.keys())
        if missing:
            raise InvalidIdentityError(f"Missing required identity fields: {sorted(missing)}")
        return cls(
            execution_id=str(data["execution_id"]),
            ticket_id=str(data["ticket_id"]),
            attempt=int(data["attempt"]),
            lease_id=str(data["lease_id"]),
            fencing_token=str(data["fencing_token"]),
            session_id=str(data["session_id"]),
            worker_id=str(data["worker_id"]),
        )

    @classmethod
    def from_json(cls, json_str: str) -> ExecutionIdentity:
        """Deserialize identity from JSON string."""
        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError as exc:
            raise InvalidIdentityError(f"Invalid JSON in identity payload: {exc}") from exc
        return cls.from_dict(parsed)

    def validate_mutation(
        self,
        ticket_id: str,
        attempt: int,
        fencing_token: str,
        lease_id: str | None = None,
    ) -> None:
        """Validate mutation preconditions against this active identity."""
        if self.ticket_id != ticket_id:
            raise TicketMismatchError(
                f"Ticket mismatch: active={self.ticket_id}, attempted={ticket_id}"
            )
        if lease_id is not None and self.lease_id != lease_id:
            raise LeaseMismatchError(
                f"Lease mismatch: active={self.lease_id}, attempted={lease_id}"
            )
        if self.attempt != attempt:
            raise InvalidIdentityError(
                f"Attempt mismatch: active={self.attempt}, attempted={attempt}"
            )
        if self.fencing_token != fencing_token:
            raise StaleFencingTokenError(
                f"Stale fencing token: active={self.fencing_token}, attempted={fencing_token}"
            )
