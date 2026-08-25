#!/usr/bin/env python3
"""Deterministic Rule 11 ticket eligibility and selection enforcement."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import posixpath
import re
from typing import Any, Mapping, Sequence


SEVERITY_RANKS = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
WORK_EFFORT_RANKS = {"XS": 0, "S": 1, "M": 2, "L": 3, "XL": 4}
ACTIVE_STATUSES = frozenset({"TODO", "READY", "DOING"})
SELECTABLE_STATUSES = frozenset({"TODO", "READY"})
KNOWN_STATUSES = ACTIVE_STATUSES | frozenset({"DONE", "BLOCKED"})
SAFE_TICKET_ID = re.compile(r"^[\x21-\x7e]{1,128}$")


class SchedulingError(ValueError):
    """A command-safe Rule 11 rejection raised before process creation."""

    def __init__(self, code: str, message: str) -> None:
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", code):
            raise ValueError("scheduling error code must be uppercase ASCII")
        super().__init__(message)
        self.code = code

    @property
    def command_message(self) -> str:
        return f"BLOCKED: {self.code}: {self}"


@dataclass(frozen=True)
class Ticket:
    """Strict normalized scheduling data for one ticket."""

    ticket_id: str
    severity: str
    work_effort: str
    status: str
    dependencies: tuple[str, ...]
    blockers: tuple[str, ...]
    owner: str
    ownership: tuple[str, ...]
    quota_passed: bool
    hitl_passed: bool
    rule18_decision_valid: bool

    @property
    def order_key(self) -> tuple[int, int, bytes]:
        return (
            -SEVERITY_RANKS[self.severity],
            WORK_EFFORT_RANKS[self.work_effort],
            self.ticket_id.encode("ascii"),
        )


@dataclass(frozen=True)
class Reservation:
    """An explicit ownership reservation for running or selected work."""

    ticket_id: str
    owner: str
    ownership: tuple[str, ...]


@dataclass(frozen=True)
class SchedulingSnapshot:
    """Validated, immutable scheduling checkpoint."""

    tickets: tuple[Ticket, ...]
    reservations: tuple[Reservation, ...]
    digest: str


@dataclass(frozen=True)
class Selection:
    """The selected ticket plus the reservations after that selection."""

    ticket: Ticket
    reservations: tuple[Reservation, ...]
    continued_reservation: bool = False


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SchedulingError("INVALID_SCHEDULING_METADATA", f"{label} must be an object")
    return value


def _closed_mapping(
    value: Any,
    label: str,
    required: set[str],
    optional: set[str] | None = None,
) -> Mapping[str, Any]:
    value = _mapping(value, label)
    optional = optional or set()
    missing = required - set(value)
    unknown = set(value) - required - optional
    if missing:
        raise SchedulingError(
            "INVALID_SCHEDULING_METADATA",
            f"{label} missing fields: {', '.join(sorted(missing))}",
        )
    if unknown:
        raise SchedulingError(
            "INVALID_SCHEDULING_METADATA",
            f"{label} contains unsupported fields: {', '.join(sorted(unknown))}",
        )
    return value


def _required_ascii(value: Any, label: str, *, ticket_id: bool = False) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SchedulingError("INVALID_SCHEDULING_METADATA", f"{label} must be non-empty text")
    if not value.isascii() or any(ord(character) < 0x20 for character in value):
        raise SchedulingError("INVALID_SCHEDULING_METADATA", f"{label} must use printable ASCII")
    if ticket_id and SAFE_TICKET_ID.fullmatch(value) is None:
        raise SchedulingError("INVALID_SCHEDULING_METADATA", f"{label} is invalid")
    return value


def _string_tuple(value: Any, label: str, *, allow_empty: bool) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise SchedulingError("INVALID_SCHEDULING_METADATA", f"{label} must be a list")
    if not allow_empty and not value:
        raise SchedulingError("INVALID_SCHEDULING_METADATA", f"{label} must not be empty")
    normalized = tuple(
        _required_ascii(item, f"{label}[{index}]", ticket_id="dependencies" in label)
        for index, item in enumerate(value)
    )
    if len(normalized) != len(set(normalized)):
        raise SchedulingError("INVALID_SCHEDULING_METADATA", f"{label} contains duplicates")
    return normalized


def canonicalize_ownership_resource(value: Any, label: str) -> str:
    """Return one stable lexical resource identity for overlap checks."""

    resource = _required_ascii(value, label).replace("\\", "/")
    normalized = posixpath.normpath(resource)
    if normalized in {"", ".", "/", ".."} or normalized.startswith("../"):
        raise SchedulingError(
            "INVALID_SCHEDULING_METADATA", f"{label} is an unsafe broad resource"
        )
    # Windows drive and UNC resources are case-insensitive. POSIX and opaque
    # responsibility labels retain their case to avoid false conflicts.
    if re.match(r"^[A-Za-z]:/", normalized) or normalized.startswith("//"):
        normalized = normalized.casefold()
    return normalized


def _ownership_tuple(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise SchedulingError(
            "INVALID_SCHEDULING_METADATA", f"{label} must be a non-empty list"
        )
    normalized = tuple(
        canonicalize_ownership_resource(item, f"{label}[{index}]")
        for index, item in enumerate(value)
    )
    if len(normalized) != len(set(normalized)):
        raise SchedulingError(
            "INVALID_SCHEDULING_METADATA", f"{label} contains duplicate resources"
        )
    return normalized


def _required_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise SchedulingError("INVALID_SCHEDULING_METADATA", f"{label} must be boolean")
    return value


def _canonical_digest(snapshot: Mapping[str, Any]) -> str:
    material = json.dumps(
        snapshot,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return hashlib.sha256(material).hexdigest()


def validate_snapshot(value: Mapping[str, Any]) -> SchedulingSnapshot:
    """Validate a closed Rule 11 snapshot and return normalized immutable data."""

    snapshot = _closed_mapping(
        value,
        "scheduling snapshot",
        {"schema_version", "tickets", "reservations"},
    )
    if snapshot["schema_version"] != 1:
        raise SchedulingError(
            "INVALID_SCHEDULING_METADATA", "scheduling snapshot schema_version must be 1"
        )
    raw_tickets = snapshot["tickets"]
    raw_reservations = snapshot["reservations"]
    if not isinstance(raw_tickets, list) or not raw_tickets:
        raise SchedulingError(
            "INVALID_SCHEDULING_METADATA", "scheduling snapshot tickets must be non-empty"
        )
    if not isinstance(raw_reservations, list):
        raise SchedulingError(
            "INVALID_SCHEDULING_METADATA", "scheduling snapshot reservations must be a list"
        )

    tickets: list[Ticket] = []
    for index, raw_ticket in enumerate(raw_tickets):
        label = f"tickets[{index}]"
        ticket = _closed_mapping(
            raw_ticket,
            label,
            {
                "ticket_id",
                "severity",
                "work_effort",
                "status",
                "dependencies",
                "blockers",
                "owner",
                "ownership",
                "quota_passed",
                "hitl_passed",
                "rule18_decision_valid",
            },
        )
        ticket_id = _required_ascii(ticket["ticket_id"], f"{label}.ticket_id", ticket_id=True)
        severity = _required_ascii(ticket["severity"], f"{label}.severity")
        effort = _required_ascii(ticket["work_effort"], f"{label}.work_effort")
        status = _required_ascii(ticket["status"], f"{label}.status")
        if severity not in SEVERITY_RANKS:
            raise SchedulingError(
                "INVALID_SCHEDULING_METADATA", f"{label}.severity is invalid"
            )
        if effort not in WORK_EFFORT_RANKS:
            raise SchedulingError(
                "INVALID_SCHEDULING_METADATA", f"{label}.work_effort is invalid"
            )
        if status not in KNOWN_STATUSES:
            raise SchedulingError("INVALID_SCHEDULING_METADATA", f"{label}.status is invalid")
        tickets.append(
            Ticket(
                ticket_id=ticket_id,
                severity=severity,
                work_effort=effort,
                status=status,
                dependencies=_string_tuple(
                    ticket["dependencies"], f"{label}.dependencies", allow_empty=True
                ),
                blockers=_string_tuple(ticket["blockers"], f"{label}.blockers", allow_empty=True),
                owner=_required_ascii(ticket["owner"], f"{label}.owner"),
                ownership=_ownership_tuple(ticket["ownership"], f"{label}.ownership"),
                quota_passed=_required_bool(
                    ticket["quota_passed"], f"{label}.quota_passed"
                ),
                hitl_passed=_required_bool(ticket["hitl_passed"], f"{label}.hitl_passed"),
                rule18_decision_valid=_required_bool(
                    ticket["rule18_decision_valid"], f"{label}.rule18_decision_valid"
                ),
            )
        )

    ticket_ids = [ticket.ticket_id for ticket in tickets]
    if len(ticket_ids) != len(set(ticket_ids)):
        raise SchedulingError("INVALID_SCHEDULING_METADATA", "duplicate Ticket ID")
    by_id = {ticket.ticket_id: ticket for ticket in tickets}
    for ticket in tickets:
        unknown_dependencies = set(ticket.dependencies) - set(by_id)
        if unknown_dependencies:
            raise SchedulingError(
                "INVALID_SCHEDULING_METADATA",
                f"ticket {ticket.ticket_id} has unknown dependencies",
            )
        if ticket.ticket_id in ticket.dependencies:
            raise SchedulingError(
                "INVALID_SCHEDULING_METADATA",
                f"ticket {ticket.ticket_id} depends on itself",
            )

    reservations: list[Reservation] = []
    for index, raw_reservation in enumerate(raw_reservations):
        label = f"reservations[{index}]"
        reservation = _closed_mapping(
            raw_reservation, label, {"ticket_id", "owner", "ownership"}
        )
        ticket_id = _required_ascii(
            reservation["ticket_id"], f"{label}.ticket_id", ticket_id=True
        )
        if ticket_id not in by_id:
            raise SchedulingError(
                "INVALID_SCHEDULING_METADATA", f"{label} references an unknown ticket"
            )
        normalized = Reservation(
            ticket_id=ticket_id,
            owner=_required_ascii(reservation["owner"], f"{label}.owner"),
            ownership=_ownership_tuple(reservation["ownership"], f"{label}.ownership"),
        )
        ticket = by_id[ticket_id]
        if normalized.owner != ticket.owner or normalized.ownership != ticket.ownership:
            raise SchedulingError(
                "INVALID_SCHEDULING_METADATA",
                f"{label} does not match its ticket ownership binding",
            )
        reservations.append(normalized)
    reservation_ids = [reservation.ticket_id for reservation in reservations]
    if len(reservation_ids) != len(set(reservation_ids)):
        raise SchedulingError(
            "INVALID_SCHEDULING_METADATA", "duplicate ticket reservation"
        )
    reservation_id_set = set(reservation_ids)
    for ticket in tickets:
        if ticket.status == "DOING" and ticket.ticket_id not in reservation_id_set:
            raise SchedulingError(
                "INVALID_SCHEDULING_METADATA",
                f"DOING ticket {ticket.ticket_id} lacks an ownership reservation",
            )
    for reservation in reservations:
        if by_id[reservation.ticket_id].status not in ACTIVE_STATUSES:
            raise SchedulingError(
                "INVALID_SCHEDULING_METADATA",
                f"reservation {reservation.ticket_id} is not bound to active work",
            )

    return SchedulingSnapshot(
        tickets=tuple(tickets),
        reservations=tuple(reservations),
        digest=_canonical_digest(snapshot),
    )


def _ownership_conflicts(
    ticket: Ticket, reservations: Sequence[Reservation]
) -> bool:
    claimed = ticket.ownership
    return any(
        reservation.ticket_id != ticket.ticket_id
        and any(
            _resources_overlap(candidate, reserved)
            for candidate in claimed
            for reserved in reservation.ownership
        )
        for reservation in reservations
    )


def _resources_overlap(left: str, right: str) -> bool:
    """Detect equality or a segment-bound parent/child ownership overlap."""

    return (
        left == right
        or left.startswith(right.rstrip("/") + "/")
        or right.startswith(left.rstrip("/") + "/")
    )


def _eligible(
    ticket: Ticket,
    statuses: Mapping[str, str],
    reservations: Sequence[Reservation],
) -> bool:
    return (
        ticket.status in SELECTABLE_STATUSES
        and all(reservation.ticket_id != ticket.ticket_id for reservation in reservations)
        and all(statuses[dependency] == "DONE" for dependency in ticket.dependencies)
        and not ticket.blockers
        and ticket.quota_passed
        and ticket.hitl_passed
        and ticket.rule18_decision_valid
        and not _ownership_conflicts(ticket, reservations)
    )


def select_tickets(snapshot: SchedulingSnapshot, capacity: int = 1) -> tuple[Selection, ...]:
    """Select up to capacity tickets, reserving ownership and recomputing each time."""

    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 1:
        raise SchedulingError("INVALID_SCHEDULING_METADATA", "capacity must be positive")
    statuses = {ticket.ticket_id: ticket.status for ticket in snapshot.tickets}
    reservations = list(snapshot.reservations)
    selections: list[Selection] = []
    selected_ids: set[str] = set()
    for _ in range(capacity):
        eligible = sorted(
            (
                ticket
                for ticket in snapshot.tickets
                if ticket.ticket_id not in selected_ids
                and _eligible(ticket, statuses, reservations)
            ),
            key=lambda ticket: ticket.order_key,
        )
        if not eligible:
            break
        selected = eligible[0]
        selected_ids.add(selected.ticket_id)
        reservation = Reservation(selected.ticket_id, selected.owner, selected.ownership)
        reservations.append(reservation)
        selections.append(Selection(selected, tuple(reservations)))
    return tuple(selections)


def enforce_dispatch(
    snapshot: SchedulingSnapshot,
    *,
    ticket_id: str,
    owner: str,
    ownership: Sequence[str],
    decision_valid: bool,
) -> Selection:
    """Bind one executable dispatch to the current Rule 11 selection or reservation."""

    ticket_id = _required_ascii(ticket_id, "dispatch ticket_id", ticket_id=True)
    owner = _required_ascii(owner, "dispatch owner")
    normalized_ownership = tuple(
        canonicalize_ownership_resource(item, f"dispatch ownership[{index}]")
        for index, item in enumerate(ownership)
    )
    if not normalized_ownership:
        raise SchedulingError(
            "INVALID_SCHEDULING_METADATA", "dispatch ownership must not be empty"
        )
    tickets = {ticket.ticket_id: ticket for ticket in snapshot.tickets}
    current = tickets.get(ticket_id)
    if current is None:
        raise SchedulingError(
            "INVALID_SCHEDULING_METADATA", "dispatch ticket is not active in the snapshot"
        )
    if current.owner != owner or current.ownership != normalized_ownership:
        raise SchedulingError(
            "OWNERSHIP_CONFLICT", "dispatch does not match current ticket ownership"
        )
    if not decision_valid or not current.rule18_decision_valid:
        raise SchedulingError(
            "INVALID_RULE18_DECISION", "current ticket lacks a valid Rule 18 decision"
        )

    matching = [
        reservation
        for reservation in snapshot.reservations
        if reservation.ticket_id == current.ticket_id
    ]
    if matching:
        if len(matching) != 1 or matching[0].owner != owner or matching[0].ownership != current.ownership:
            raise SchedulingError(
                "OWNERSHIP_CONFLICT",
                "current ticket reservation does not match dispatch ownership",
            )
        statuses = {ticket.ticket_id: ticket.status for ticket in snapshot.tickets}
        if not (
            all(statuses[dependency] == "DONE" for dependency in current.dependencies)
            and not current.blockers
            and current.quota_passed
            and current.hitl_passed
            and not _ownership_conflicts(current, snapshot.reservations)
        ):
            raise SchedulingError(
                "RESERVED_TICKET_INELIGIBLE",
                "current ticket reservation no longer passes execution gates",
            )
        return Selection(current, snapshot.reservations, continued_reservation=True)
    if current.status == "DOING":
        raise SchedulingError(
            "INVALID_SCHEDULING_METADATA",
            "DOING work requires an explicit current ticket ownership reservation",
        )

    selections = select_tickets(snapshot, capacity=1)
    if not selections:
        raise SchedulingError("NO_ELIGIBLE_TICKET", "no ticket is execution-eligible")
    selected = selections[0]
    if selected.ticket.ticket_id != current.ticket_id:
        raise SchedulingError(
            "NOT_NEXT_ELIGIBLE_TICKET",
            f"current ticket is not next; selected {selected.ticket.ticket_id}",
        )
    return selected
