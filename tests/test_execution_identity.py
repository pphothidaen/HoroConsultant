"""Unit tests for ExecutionIdentity contract and error semantics (AT-01)."""

import pytest

from project.core.execution_identity import (
    ExecutionIdentity,
    InvalidIdentityError,
    LeaseMismatchError,
    StaleFencingTokenError,
    TicketMismatchError,
)


def test_execution_identity_creation_and_immutability():
    ident = ExecutionIdentity(
        execution_id="exec-001",
        ticket_id="KAN-142",
        attempt=1,
        lease_id="L-8f21",
        fencing_token="fence-10",
        session_id="session-20260925",
        worker_id="node-herdr-01",
    )
    assert ident.execution_id == "exec-001"
    assert ident.ticket_id == "KAN-142"
    assert ident.attempt == 1
    assert ident.lease_id == "L-8f21"
    assert ident.fencing_token == "fence-10"
    assert ident.session_id == "session-20260925"
    assert ident.worker_id == "node-herdr-01"

    # Verify frozen/immutable
    with pytest.raises(Exception):
        ident.attempt = 2  # type: ignore


def test_execution_identity_validation_invalid_fields():
    with pytest.raises(InvalidIdentityError, match="attempt must be an integer >= 1"):
        ExecutionIdentity(
            execution_id="exec-001",
            ticket_id="KAN-142",
            attempt=0,
            lease_id="L-8f21",
            fencing_token="fence-10",
            session_id="session-20260925",
            worker_id="node-herdr-01",
        )

    with pytest.raises(InvalidIdentityError, match="ticket_id must be a non-empty string"):
        ExecutionIdentity(
            execution_id="exec-001",
            ticket_id="",
            attempt=1,
            lease_id="L-8f21",
            fencing_token="fence-10",
            session_id="session-20260925",
            worker_id="node-herdr-01",
        )


def test_execution_identity_serialization_roundtrip():
    ident = ExecutionIdentity(
        execution_id="exec-002",
        ticket_id="KAN-200",
        attempt=3,
        lease_id="L-9999",
        fencing_token="fence-42",
        session_id="session-abc",
        worker_id="worker-02",
    )
    d = ident.to_dict()
    ident2 = ExecutionIdentity.from_dict(d)
    assert ident == ident2

    json_str = ident.to_json()
    ident3 = ExecutionIdentity.from_json(json_str)
    assert ident == ident3


def test_execution_identity_mutation_validation_success():
    ident = ExecutionIdentity(
        execution_id="exec-003",
        ticket_id="KAN-300",
        attempt=2,
        lease_id="L-300",
        fencing_token="fence-300",
        session_id="session-300",
        worker_id="worker-300",
    )
    # Valid mutation check
    ident.validate_mutation(
        ticket_id="KAN-300",
        attempt=2,
        fencing_token="fence-300",
        lease_id="L-300",
    )


def test_execution_identity_mutation_validation_errors():
    ident = ExecutionIdentity(
        execution_id="exec-004",
        ticket_id="KAN-400",
        attempt=1,
        lease_id="L-400",
        fencing_token="fence-400",
        session_id="session-400",
        worker_id="worker-400",
    )

    # Ticket mismatch
    with pytest.raises(TicketMismatchError):
        ident.validate_mutation(
            ticket_id="KAN-999",
            attempt=1,
            fencing_token="fence-400",
        )

    # Lease mismatch
    with pytest.raises(LeaseMismatchError):
        ident.validate_mutation(
            ticket_id="KAN-400",
            attempt=1,
            fencing_token="fence-400",
            lease_id="L-WRONG",
        )

    # Stale fencing token
    with pytest.raises(StaleFencingTokenError):
        ident.validate_mutation(
            ticket_id="KAN-400",
            attempt=1,
            fencing_token="fence-OLD",
        )

    # Attempt mismatch
    with pytest.raises(InvalidIdentityError):
        ident.validate_mutation(
            ticket_id="KAN-400",
            attempt=2,
            fencing_token="fence-400",
        )
