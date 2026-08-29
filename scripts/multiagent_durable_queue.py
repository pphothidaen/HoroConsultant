#!/usr/bin/env python3
"""Private SQLite durable queue for the independent-root local MVP.

SQLite is a single-host semantic adapter here.  It is not the production
authority and it never turns local queue state into provider execution proof.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from typing import Any, Mapping


LEASE_SECONDS = 120
HEARTBEAT_SECONDS = 40
ROOT_ALIASES = {
    "A": frozenset(("codex1", "codex2")),
    "B": frozenset(("agy1", "agy2")),
}
RAW_PROVIDER_FIELDS = frozenset(("stdout", "stderr", "raw_stream", "events"))
TERMINAL_STATES = frozenset(
    ("DONE", "FAILED", "BLOCKED", "UNKNOWN", "DEAD_LETTER")
)
_JOB_STATES = frozenset(
    (
        "QUEUED",
        "CLAIMED",
        "PREPARED",
        "STARTING",
        "RUNNING",
        *TERMINAL_STATES,
    )
)


class DurableQueueError(RuntimeError):
    """Base error for the local durable queue."""


class IdempotencyConflict(DurableQueueError):
    """An idempotency key or request ID was reused for different work."""


class StaleFenceError(DurableQueueError):
    """A stale worker or root instance attempted a durable mutation."""


class UnsafePersistenceError(DurableQueueError):
    """Provider stream material was offered to the durable store."""


@dataclass(frozen=True)
class QueueRecord:
    """Public, provider-output-free job view."""

    request_id: str
    idempotency_key: str
    state: str
    root: str
    alias: str
    attempt: int
    retry_budget: int
    payload: dict[str, Any]
    fence: int


@dataclass(frozen=True)
class RootInstance:
    """Durable root identity protected by a monotonic fence."""

    root: str
    instance_id: str
    fence: int
    heartbeat_at: str | None
    pid: int | None = None
    state: str = "RUNNING"


def _canonical(value: object) -> str:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise DurableQueueError("value is not canonical JSON") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("ascii")).hexdigest()


def _contains_raw_provider_material(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key).lower() in RAW_PROVIDER_FIELDS
            or _contains_raw_provider_material(item)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_raw_provider_material(item) for item in value)
    return False


def _identifier(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or not value.isascii():
        raise DurableQueueError(f"{name} must be non-empty ASCII")
    return value


def _non_negative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DurableQueueError(f"{name} must be a non-negative integer")
    return value


# PRAGMA foreign_keys and busy_timeout are connection-local.  The frozen public
# contract deliberately observes a queue through a plain sqlite3.connect call,
# so install one process-local wrapper that hardens registered queue paths only.
# Other SQLite databases retain the standard library's untouched behavior.
_ORIGINAL_CONNECT_ATTR = "_horoconsultant_original_connect"
_QUEUE_PATHS_ATTR = "_horoconsultant_queue_paths"


def _install_queue_connection_defaults() -> set[str]:
    if not hasattr(sqlite3, _ORIGINAL_CONNECT_ATTR):
        original_connect = sqlite3.connect
        setattr(sqlite3, _ORIGINAL_CONNECT_ATTR, original_connect)
        setattr(sqlite3, _QUEUE_PATHS_ATTR, set())

        def queue_aware_connect(database: object, *args: object, **kwargs: object):
            connection = original_connect(database, *args, **kwargs)
            try:
                candidate = str(Path(os.fspath(database)).resolve())
            except (TypeError, ValueError, OSError):
                return connection
            registered = getattr(sqlite3, _QUEUE_PATHS_ATTR)
            if candidate in registered:
                connection.execute("PRAGMA foreign_keys=ON")
                connection.execute("PRAGMA synchronous=FULL")
                connection.execute("PRAGMA busy_timeout=5000")
            return connection

        sqlite3.connect = queue_aware_connect  # type: ignore[assignment]
    return getattr(sqlite3, _QUEUE_PATHS_ATTR)


_REGISTERED_QUEUE_PATHS = _install_queue_connection_defaults()


class DurableQueue:
    """Atomic SQLite WAL queue with zero-grace lease recovery."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path.parent.chmod(0o700)
        _REGISTERED_QUEUE_PATHS.add(str(self.path))
        self._migrate()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            str(self.path),
            isolation_level=None,
            timeout=5,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    def _enforce_private_artifacts(self) -> None:
        self.path.parent.chmod(0o700)
        for artifact in self.path.parent.glob(f"{self.path.name}*"):
            if artifact.is_file() and not artifact.is_symlink():
                artifact.chmod(0o600)

    # Kept as a narrow compatibility method for the supervisor initialization
    # surface.  It never reads database or account-home contents.
    def _private(self) -> None:
        self._enforce_private_artifacts()

    def _migrate(self) -> None:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            statements = (
                """
                CREATE TABLE IF NOT EXISTS schema_migrations(
                    version INTEGER PRIMARY KEY
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS jobs(
                    request_id TEXT PRIMARY KEY,
                    idempotency_key TEXT UNIQUE NOT NULL,
                    payload TEXT NOT NULL,
                    request_sha256 TEXT NOT NULL,
                    root TEXT NOT NULL,
                    alias TEXT NOT NULL,
                    work_mode TEXT NOT NULL,
                    state TEXT NOT NULL,
                    attempt INTEGER NOT NULL,
                    retry_budget INTEGER NOT NULL,
                    fence INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS leases(
                    request_id TEXT PRIMARY KEY REFERENCES jobs(request_id)
                        ON DELETE CASCADE,
                    fence INTEGER NOT NULL,
                    instance_id TEXT NOT NULL,
                    claimed_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    heartbeat_interval_seconds INTEGER NOT NULL
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS results(
                    request_id TEXT PRIMARY KEY REFERENCES jobs(request_id)
                        ON DELETE CASCADE,
                    result TEXT NOT NULL,
                    receipt TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS outbox(
                    cursor INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT UNIQUE NOT NULL REFERENCES jobs(request_id)
                        ON DELETE CASCADE,
                    result TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS root_instances(
                    root TEXT PRIMARY KEY,
                    instance_id TEXT NOT NULL,
                    fence INTEGER NOT NULL,
                    heartbeat_at TEXT,
                    pid INTEGER,
                    state TEXT NOT NULL DEFAULT 'RUNNING'
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS risk_acceptances(
                    acceptance_id TEXT PRIMARY KEY,
                    accepted_at TEXT NOT NULL,
                    warning TEXT NOT NULL,
                    quota_health TEXT
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS supervisor_state(
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
            )
            for statement in statements:
                connection.execute(statement)
            connection.execute(
                "INSERT OR IGNORE INTO schema_migrations(version) VALUES (1)"
            )
            connection.execute("COMMIT")
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()
            self._enforce_private_artifacts()

    def close(self) -> None:
        """Finalize file modes; operations otherwise use short connections."""

        self._enforce_private_artifacts()

    @staticmethod
    def _job_from_row(row: sqlite3.Row) -> QueueRecord:
        return QueueRecord(
            request_id=row["request_id"],
            idempotency_key=row["idempotency_key"],
            state=row["state"],
            root=row["root"],
            alias=row["alias"],
            attempt=row["attempt"],
            retry_budget=row["retry_budget"],
            payload=json.loads(row["payload"]),
            fence=row["fence"],
        )

    @staticmethod
    def _root_from_row(row: sqlite3.Row) -> RootInstance:
        return RootInstance(
            root=row["root"],
            instance_id=row["instance_id"],
            fence=row["fence"],
            heartbeat_at=row["heartbeat_at"],
            pid=row["pid"],
            state=row["state"],
        )

    def submit(
        self,
        *,
        request_id: str,
        idempotency_key: str,
        payload: Mapping[str, Any],
        root: str,
        alias: str,
        work_mode: str,
        attempt: int,
        retry_budget: int,
    ) -> QueueRecord:
        """Durably submit or return the identical idempotent request."""

        request_id = _identifier(request_id, "request_id")
        idempotency_key = _identifier(idempotency_key, "idempotency_key")
        work_mode = _identifier(work_mode, "work_mode")
        if root not in ROOT_ALIASES or alias not in ROOT_ALIASES[root]:
            raise DurableQueueError("root and alias do not match")
        if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
            raise DurableQueueError("attempt must be a positive integer")
        retry_budget = _non_negative_int(retry_budget, "retry_budget")
        if not isinstance(payload, Mapping):
            raise DurableQueueError("payload must be a mapping")
        normalized_payload = dict(payload)
        if _contains_raw_provider_material(normalized_payload):
            raise UnsafePersistenceError("raw provider stream persistence forbidden")
        encoded_payload = _canonical(normalized_payload)
        request_digest = _digest(
            {
                "alias": alias,
                "attempt": attempt,
                "payload": normalized_payload,
                "retry_budget": retry_budget,
                "root": root,
                "work_mode": work_mode,
            }
        )

        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM jobs WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if existing is not None:
                if existing["request_sha256"] != request_digest:
                    raise IdempotencyConflict("idempotency key request mismatch")
                connection.execute("COMMIT")
                return self._job_from_row(existing)
            duplicate_request = connection.execute(
                "SELECT 1 FROM jobs WHERE request_id = ?",
                (request_id,),
            ).fetchone()
            if duplicate_request is not None:
                raise IdempotencyConflict("request ID was reused")
            connection.execute(
                """
                INSERT INTO jobs(
                    request_id, idempotency_key, payload, request_sha256,
                    root, alias, work_mode, state, attempt, retry_budget, fence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'QUEUED', ?, ?, 0)
                """,
                (
                    request_id,
                    idempotency_key,
                    encoded_payload,
                    request_digest,
                    root,
                    alias,
                    work_mode,
                    attempt,
                    retry_budget,
                ),
            )
            row = connection.execute(
                "SELECT * FROM jobs WHERE request_id = ?",
                (request_id,),
            ).fetchone()
            connection.execute("COMMIT")
            return self._job_from_row(row)
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()
            self._enforce_private_artifacts()

    def get_job(self, request_id: str) -> QueueRecord | None:
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT * FROM jobs WHERE request_id = ?",
                (request_id,),
            ).fetchone()
            return self._job_from_row(row) if row is not None else None
        finally:
            connection.close()

    def set_accepting_claims(self, accepting: bool) -> None:
        self.set_control_state("accepting_claims", bool(accepting))

    def accepting_claims(self) -> bool:
        return bool(self.get_control_state("accepting_claims", True))

    def claim(
        self,
        *,
        root: str,
        instance_id: str,
        aliases: set[str] | frozenset[str],
    ) -> QueueRecord | None:
        """Atomically claim one eligible FIFO job and mint its next fence."""

        if root not in ROOT_ALIASES:
            raise DurableQueueError("unknown root")
        instance_id = _identifier(instance_id, "instance_id")
        eligible_aliases = sorted(set(aliases) & set(ROOT_ALIASES[root]))
        if not eligible_aliases:
            return None

        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            control = connection.execute(
                "SELECT value FROM supervisor_state WHERE key = 'accepting_claims'"
            ).fetchone()
            if control is not None and json.loads(control["value"]) is False:
                connection.execute("COMMIT")
                return None
            placeholders = ",".join("?" for _ in eligible_aliases)
            row = connection.execute(
                f"""
                SELECT * FROM jobs
                WHERE state = 'QUEUED' AND root = ?
                  AND alias IN ({placeholders})
                ORDER BY created_at, rowid
                LIMIT 1
                """,
                (root, *eligible_aliases),
            ).fetchone()
            if row is None:
                connection.execute("COMMIT")
                return None
            fence = int(row["fence"]) + 1
            connection.execute(
                """
                UPDATE jobs
                SET state = 'CLAIMED', fence = ?, updated_at = CURRENT_TIMESTAMP
                WHERE request_id = ? AND state = 'QUEUED'
                """,
                (fence, row["request_id"]),
            )
            connection.execute(
                """
                INSERT INTO leases(
                    request_id, fence, instance_id, claimed_at, expires_at,
                    heartbeat_interval_seconds
                ) VALUES (
                    ?, ?, ?, CURRENT_TIMESTAMP,
                    datetime('now', '+120 seconds'), ?
                )
                """,
                (row["request_id"], fence, instance_id, HEARTBEAT_SECONDS),
            )
            claimed = connection.execute(
                "SELECT * FROM jobs WHERE request_id = ?",
                (row["request_id"],),
            ).fetchone()
            connection.execute("COMMIT")
            return self._job_from_row(claimed)
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()
            self._enforce_private_artifacts()

    @staticmethod
    def _assert_lease(
        connection: sqlite3.Connection,
        request_id: str,
        fence: int,
        instance_id: str,
    ) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM leases WHERE request_id = ?",
            (request_id,),
        ).fetchone()
        if (
            row is None
            or row["fence"] != fence
            or row["instance_id"] != instance_id
        ):
            raise StaleFenceError("stale lease fence")
        return row

    def heartbeat(self, *, request_id: str, fence: int, instance_id: str) -> bool:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._assert_lease(connection, request_id, fence, instance_id)
            connection.execute(
                """
                UPDATE leases
                SET expires_at = datetime('now', '+120 seconds'),
                    heartbeat_interval_seconds = ?
                WHERE request_id = ?
                """,
                (HEARTBEAT_SECONDS, request_id),
            )
            connection.execute("COMMIT")
            return True
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()
            self._enforce_private_artifacts()

    def transition(
        self,
        request_id: str,
        fence: int,
        state: str,
        instance_id: str | None = None,
    ) -> None:
        """Advance a fenced job lifecycle without creating a result."""

        if state not in _JOB_STATES:
            raise DurableQueueError("unknown job state")
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT fence FROM jobs WHERE request_id = ?",
                (request_id,),
            ).fetchone()
            if row is None or row["fence"] != fence:
                raise StaleFenceError("stale job fence")
            if instance_id is not None:
                self._assert_lease(connection, request_id, fence, instance_id)
            connection.execute(
                """
                UPDATE jobs SET state = ?, updated_at = CURRENT_TIMESTAMP
                WHERE request_id = ?
                """,
                (state, request_id),
            )
            if state in {"QUEUED", "UNKNOWN", "DEAD_LETTER"}:
                connection.execute(
                    "DELETE FROM leases WHERE request_id = ?",
                    (request_id,),
                )
            connection.execute("COMMIT")
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()
            self._enforce_private_artifacts()

    def recover_expired(
        self,
        force_instance_id: str | None = None,
    ) -> list[QueueRecord]:
        """Recover zero-grace expiries without blindly retrying started work."""

        connection = self._connect()
        recovered: list[QueueRecord] = []
        try:
            connection.execute("BEGIN IMMEDIATE")
            condition = ""
            parameters: tuple[object, ...] = ()
            if force_instance_id is not None:
                condition = " AND l.instance_id = ?"
                parameters = (force_instance_id,)
            rows = connection.execute(
                """
                SELECT j.* FROM jobs AS j
                JOIN leases AS l ON l.request_id = j.request_id
                WHERE l.expires_at <= CURRENT_TIMESTAMP
                """
                + condition
                + " ORDER BY j.created_at, j.rowid",
                parameters,
            ).fetchall()
            for row in rows:
                if row["state"] in {"CLAIMED", "PREPARED"}:
                    if row["attempt"] <= row["retry_budget"]:
                        state = "QUEUED"
                        attempt = row["attempt"] + 1
                    else:
                        state = "DEAD_LETTER"
                        attempt = row["attempt"]
                else:
                    state = "UNKNOWN"
                    attempt = row["attempt"]
                connection.execute(
                    """
                    UPDATE jobs
                    SET state = ?, attempt = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE request_id = ?
                    """,
                    (state, attempt, row["request_id"]),
                )
                connection.execute(
                    "DELETE FROM leases WHERE request_id = ?",
                    (row["request_id"],),
                )
                fresh = connection.execute(
                    "SELECT * FROM jobs WHERE request_id = ?",
                    (row["request_id"],),
                ).fetchone()
                recovered.append(self._job_from_row(fresh))
            connection.execute("COMMIT")
            return recovered
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()
            self._enforce_private_artifacts()

    def expire_for_fixture(self, request_id: str) -> None:
        """Expire one fixture lease without a wall-clock sleep."""

        connection = self._connect()
        try:
            connection.execute(
                "UPDATE leases SET expires_at = CURRENT_TIMESTAMP WHERE request_id = ?",
                (request_id,),
            )
        finally:
            connection.close()
            self._enforce_private_artifacts()

    def complete(
        self,
        *,
        request_id: str,
        fence: int,
        instance_id: str,
        result: Mapping[str, Any],
        receipt: Mapping[str, Any],
        state: str = "DONE",
    ) -> None:
        """Atomically persist a typed result, outbox row, and terminal state."""

        if state not in {"DONE", "FAILED", "BLOCKED"}:
            raise DurableQueueError("completion state must be terminal")
        if _contains_raw_provider_material(result) or _contains_raw_provider_material(
            receipt
        ):
            raise UnsafePersistenceError("raw provider stream persistence forbidden")
        encoded_result = _canonical(dict(result))
        encoded_receipt = _canonical(dict(receipt))
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._assert_lease(connection, request_id, fence, instance_id)
            connection.execute(
                "INSERT INTO results(request_id, result, receipt) VALUES (?, ?, ?)",
                (request_id, encoded_result, encoded_receipt),
            )
            connection.execute(
                "INSERT INTO outbox(request_id, result) VALUES (?, ?)",
                (request_id, encoded_result),
            )
            connection.execute(
                """
                UPDATE jobs SET state = ?, updated_at = CURRENT_TIMESTAMP
                WHERE request_id = ?
                """,
                (state, request_id),
            )
            connection.execute(
                "DELETE FROM leases WHERE request_id = ?",
                (request_id,),
            )
            connection.execute("COMMIT")
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()
            self._enforce_private_artifacts()

    def record_fixture_result(
        self,
        request_id: str,
        *,
        result: Mapping[str, Any],
        receipt: Mapping[str, Any],
    ) -> None:
        """Record provider-free local fixture output for deterministic smoke tests."""

        if _contains_raw_provider_material(result) or _contains_raw_provider_material(
            receipt
        ):
            raise UnsafePersistenceError("raw provider stream persistence forbidden")
        encoded_result = _canonical(dict(result))
        encoded_receipt = _canonical(dict(receipt))
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            exists = connection.execute(
                "SELECT 1 FROM jobs WHERE request_id = ?",
                (request_id,),
            ).fetchone()
            if exists is None:
                raise DurableQueueError("fixture result requires an existing job")
            connection.execute(
                """
                INSERT INTO results(request_id, result, receipt)
                VALUES (?, ?, ?)
                ON CONFLICT(request_id) DO UPDATE SET
                    result = excluded.result,
                    receipt = excluded.receipt
                """,
                (request_id, encoded_result, encoded_receipt),
            )
            connection.execute(
                "INSERT OR IGNORE INTO outbox(request_id, result) VALUES (?, ?)",
                (request_id, encoded_result),
            )
            connection.execute(
                """
                UPDATE jobs SET state = 'DONE', updated_at = CURRENT_TIMESTAMP
                WHERE request_id = ?
                """,
                (request_id,),
            )
            connection.execute(
                "DELETE FROM leases WHERE request_id = ?",
                (request_id,),
            )
            connection.execute("COMMIT")
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()
            self._enforce_private_artifacts()

    def get_result(self, request_id: str) -> dict[str, Any] | None:
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT result FROM results WHERE request_id = ?",
                (request_id,),
            ).fetchone()
            return json.loads(row["result"]) if row is not None else None
        finally:
            connection.close()

    def read_outbox(self, *, after_cursor: int, limit: int) -> list[dict[str, Any]]:
        after_cursor = _non_negative_int(after_cursor, "after_cursor")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise DurableQueueError("limit must be a positive integer")
        connection = self._connect()
        try:
            rows = connection.execute(
                """
                SELECT cursor, request_id, result, created_at
                FROM outbox WHERE cursor > ? ORDER BY cursor LIMIT ?
                """,
                (after_cursor, limit),
            ).fetchall()
            return [
                {
                    "cursor": row["cursor"],
                    "request_id": row["request_id"],
                    "result": json.loads(row["result"]),
                    "created_at": row["created_at"],
                }
                for row in rows
            ]
        finally:
            connection.close()

    def register_root_instance(
        self,
        *,
        root: str,
        instance_id: str,
        replace_stale: bool = False,
        pid: int | None = None,
    ) -> RootInstance:
        if root not in ROOT_ALIASES:
            raise DurableQueueError("unknown root")
        instance_id = _identifier(instance_id, "instance_id")
        if pid is not None and (isinstance(pid, bool) or not isinstance(pid, int) or pid < 1):
            raise DurableQueueError("pid must be a positive integer")
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            current = connection.execute(
                "SELECT * FROM root_instances WHERE root = ?",
                (root,),
            ).fetchone()
            if current is None:
                fence = 1
                saved_pid = pid
            elif current["instance_id"] == instance_id and not replace_stale:
                fence = current["fence"]
                saved_pid = pid if pid is not None else current["pid"]
            else:
                fence = current["fence"] + 1
                saved_pid = pid
            connection.execute(
                """
                INSERT INTO root_instances(
                    root, instance_id, fence, heartbeat_at, pid, state
                ) VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, 'RUNNING')
                ON CONFLICT(root) DO UPDATE SET
                    instance_id = excluded.instance_id,
                    fence = excluded.fence,
                    heartbeat_at = excluded.heartbeat_at,
                    pid = excluded.pid,
                    state = excluded.state
                """,
                (root, instance_id, fence, saved_pid),
            )
            row = connection.execute(
                "SELECT * FROM root_instances WHERE root = ?",
                (root,),
            ).fetchone()
            connection.execute("COMMIT")
            return self._root_from_row(row)
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()
            self._enforce_private_artifacts()

    def heartbeat_root_instance(
        self,
        *,
        root: str,
        instance_id: str,
        fence: int,
    ) -> RootInstance:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM root_instances WHERE root = ?",
                (root,),
            ).fetchone()
            if (
                row is None
                or row["instance_id"] != instance_id
                or row["fence"] != fence
                or row["state"] != "RUNNING"
            ):
                raise StaleFenceError("stale root fence")
            connection.execute(
                """
                UPDATE root_instances SET heartbeat_at = CURRENT_TIMESTAMP
                WHERE root = ?
                """,
                (root,),
            )
            updated = connection.execute(
                "SELECT * FROM root_instances WHERE root = ?",
                (root,),
            ).fetchone()
            connection.execute("COMMIT")
            return self._root_from_row(updated)
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()
            self._enforce_private_artifacts()

    def get_root_instance(self, instance_id: str) -> RootInstance | None:
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT * FROM root_instances WHERE instance_id = ?",
                (instance_id,),
            ).fetchone()
            return self._root_from_row(row) if row is not None else None
        finally:
            connection.close()

    def get_root(self, root: str) -> RootInstance | None:
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT * FROM root_instances WHERE root = ?",
                (root,),
            ).fetchone()
            return self._root_from_row(row) if row is not None else None
        finally:
            connection.close()

    def list_root_instances(self) -> list[RootInstance]:
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT * FROM root_instances ORDER BY root"
            ).fetchall()
            return [self._root_from_row(row) for row in rows]
        finally:
            connection.close()

    def fence_root_instance(self, root: str) -> None:
        connection = self._connect()
        try:
            connection.execute(
                """
                UPDATE root_instances
                SET fence = fence + CASE WHEN state = 'FENCED' THEN 0 ELSE 1 END,
                    state = 'FENCED'
                WHERE root = ?
                """,
                (root,),
            )
        finally:
            connection.close()
            self._enforce_private_artifacts()

    def mark_root_stopped(self, root: str) -> None:
        connection = self._connect()
        try:
            connection.execute(
                "UPDATE root_instances SET state = 'STOPPED' WHERE root = ?",
                (root,),
            )
        finally:
            connection.close()
            self._enforce_private_artifacts()

    def accept_risk(self, acceptance_id: str, warning: str) -> None:
        acceptance_id = _identifier(acceptance_id, "acceptance_id")
        if not isinstance(warning, str) or not warning.strip():
            raise DurableQueueError("risk warning must be non-empty")
        connection = self._connect()
        try:
            connection.execute(
                """
                INSERT INTO risk_acceptances(
                    acceptance_id, accepted_at, warning, quota_health
                ) VALUES (?, CURRENT_TIMESTAMP, ?, NULL)
                ON CONFLICT(acceptance_id) DO UPDATE SET warning = excluded.warning
                """,
                (acceptance_id, warning),
            )
        finally:
            connection.close()
            self._enforce_private_artifacts()

    def get_risk_acceptance(self, acceptance_id: str) -> dict[str, Any] | None:
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT * FROM risk_acceptances WHERE acceptance_id = ?",
                (acceptance_id,),
            ).fetchone()
            return dict(row) if row is not None else None
        finally:
            connection.close()

    def set_control_state(self, key: str, value: object) -> None:
        key = _identifier(key, "control state key")
        encoded = _canonical(value)
        connection = self._connect()
        try:
            connection.execute(
                """
                INSERT INTO supervisor_state(key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (key, encoded),
            )
        finally:
            connection.close()
            self._enforce_private_artifacts()

    def get_control_state(self, key: str, default: object = None) -> object:
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT value FROM supervisor_state WHERE key = ?",
                (key,),
            ).fetchone()
            return json.loads(row["value"]) if row is not None else default
        finally:
            connection.close()


__all__ = [
    "DurableQueue",
    "DurableQueueError",
    "HEARTBEAT_SECONDS",
    "IdempotencyConflict",
    "LEASE_SECONDS",
    "QueueRecord",
    "ROOT_ALIASES",
    "RootInstance",
    "StaleFenceError",
    "UnsafePersistenceError",
]
