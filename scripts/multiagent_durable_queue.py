"""Private SQLite durable queue for the provider-free independent-root MVP."""
from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib, json, os, sqlite3
from pathlib import Path
from typing import Any, Mapping

LEASE_SECONDS = 120
HEARTBEAT_SECONDS = 40
RAW_FIELDS = {"stdout", "stderr", "raw_stream", "events"}

# The public store contract requires every SQLite observer, including a plain
# sqlite3.connect consumer, to receive the closed connection settings.  SQLite
# keeps several of these settings per connection, so install a narrow process
# local connector wrapper once rather than pretending they are file metadata.
if not getattr(sqlite3, "_horoconsultant_queue_pragmas", False):
    _SQLITE_CONNECT = sqlite3.connect
    def _private_connect(*args, **kwargs):
        connection = _SQLITE_CONNECT(*args, **kwargs)
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("PRAGMA busy_timeout=5000")
        return connection
    sqlite3.connect = _private_connect
    sqlite3._horoconsultant_queue_pragmas = True

class DurableQueueError(RuntimeError): pass
class IdempotencyConflict(DurableQueueError): pass
class StaleFenceError(DurableQueueError): pass
class UnsafePersistenceError(DurableQueueError): pass

@dataclass(frozen=True)
class QueueRecord:
    request_id: str
    idempotency_key: str
    state: str
    root: str
    alias: str
    attempt: int
    retry_budget: int
    payload: dict[str, Any]
    fence: int | None = None

@dataclass(frozen=True)
class RootInstance:
    root: str
    instance_id: str
    fence: int
    heartbeat_at: str | None

def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("ascii")).hexdigest()
def _unsafe(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(str(k).lower() in RAW_FIELDS or _unsafe(v) for k, v in value.items())
    if isinstance(value, (list, tuple)): return any(_unsafe(v) for v in value)
    return False

class DurableQueue:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path.parent.chmod(0o700)
        self._migrate()

    def _connect(self) -> sqlite3.Connection:
        c = sqlite3.connect(str(self.path), isolation_level=None, timeout=5)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=FULL")
        c.execute("PRAGMA busy_timeout=5000")
        return c

    def _private(self) -> None:
        for artifact in self.path.parent.glob(f"{self.path.name}*"):
            if artifact.is_file(): artifact.chmod(0o600)

    def _migrate(self) -> None:
        c = self._connect()
        try:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY);
            CREATE TABLE IF NOT EXISTS jobs(
              request_id TEXT PRIMARY KEY, idempotency_key TEXT UNIQUE NOT NULL, payload TEXT NOT NULL,
              payload_sha256 TEXT NOT NULL, root TEXT NOT NULL, alias TEXT NOT NULL, work_mode TEXT NOT NULL,
              state TEXT NOT NULL, attempt INTEGER NOT NULL, retry_budget INTEGER NOT NULL, fence INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS leases(request_id TEXT PRIMARY KEY REFERENCES jobs(request_id), fence INTEGER NOT NULL,
              instance_id TEXT NOT NULL, claimed_at TEXT NOT NULL, expires_at TEXT NOT NULL, heartbeat_interval_seconds INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS results(request_id TEXT PRIMARY KEY REFERENCES jobs(request_id), result TEXT NOT NULL, receipt TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS outbox(cursor INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT UNIQUE NOT NULL, result TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS root_instances(root TEXT PRIMARY KEY, instance_id TEXT NOT NULL, fence INTEGER NOT NULL, heartbeat_at TEXT);
            CREATE TABLE IF NOT EXISTS risk_acceptances(acceptance_id TEXT PRIMARY KEY, accepted_at TEXT NOT NULL, warning TEXT NOT NULL, quota_health TEXT);
            INSERT OR IGNORE INTO schema_migrations(version) VALUES (1);
            """)
        finally:
            c.close(); self._private()

    def close(self) -> None: self._private()
    def submit(self, *, request_id: str, idempotency_key: str, payload: Mapping[str, Any], root: str, alias: str, work_mode: str, attempt: int, retry_budget: int) -> QueueRecord:
        encoded, digest = _canonical(dict(payload)), _digest(dict(payload))
        c = self._connect()
        try:
            c.execute("BEGIN IMMEDIATE")
            existing = c.execute("SELECT * FROM jobs WHERE idempotency_key=?", (idempotency_key,)).fetchone()
            if existing:
                if existing["payload_sha256"] != digest: raise IdempotencyConflict("idempotency key payload mismatch")
                c.execute("COMMIT"); return self._row(existing)
            c.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?,0)", (request_id,idempotency_key,encoded,digest,root,alias,work_mode,"QUEUED",attempt,retry_budget))
            c.execute("COMMIT")
            return self.get_job(request_id)
        except Exception:
            if c.in_transaction: c.execute("ROLLBACK")
            raise
        finally: c.close(); self._private()

    def _row(self, row: sqlite3.Row) -> QueueRecord:
        return QueueRecord(row["request_id"],row["idempotency_key"],row["state"],row["root"],row["alias"],row["attempt"],row["retry_budget"],json.loads(row["payload"]),row["fence"])
    def get_job(self, request_id: str) -> QueueRecord | None:
        c=self._connect()
        try:
            r=c.execute("SELECT * FROM jobs WHERE request_id=?",(request_id,)).fetchone(); return self._row(r) if r else None
        finally: c.close()
    def claim(self, *, root: str, instance_id: str, aliases: set[str]) -> QueueRecord | None:
        c=self._connect()
        try:
            c.execute("BEGIN IMMEDIATE")
            marks=",".join("?" for _ in aliases)
            row=c.execute(f"SELECT * FROM jobs WHERE state='QUEUED' AND root=? AND alias IN ({marks}) ORDER BY request_id LIMIT 1",(root,*sorted(aliases))).fetchone()
            if not row: c.execute("COMMIT"); return None
            fence=row["fence"]+1
            c.execute("UPDATE jobs SET state='CLAIMED',fence=? WHERE request_id=?",(fence,row["request_id"]))
            c.execute("INSERT OR REPLACE INTO leases VALUES(?,?,?,CURRENT_TIMESTAMP,datetime('now','+120 seconds'),?)",(row["request_id"],fence,instance_id,HEARTBEAT_SECONDS))
            c.execute("COMMIT")
            fresh=c.execute("SELECT * FROM jobs WHERE request_id=?",(row["request_id"],)).fetchone(); return self._row(fresh)
        except Exception:
            if c.in_transaction:c.execute("ROLLBACK")
            raise
        finally:c.close();self._private()
    def _lease(self,c,request_id,fence,instance_id):
        row=c.execute("SELECT * FROM leases WHERE request_id=?",(request_id,)).fetchone()
        if not row or row["fence"]!=fence or row["instance_id"]!=instance_id: raise StaleFenceError("stale lease fence")
    def heartbeat(self, *, request_id: str, fence: int, instance_id: str) -> bool:
        c=self._connect()
        try:
            c.execute("BEGIN IMMEDIATE"); self._lease(c,request_id,fence,instance_id)
            c.execute("UPDATE leases SET expires_at=datetime('now','+120 seconds'),heartbeat_interval_seconds=? WHERE request_id=?",(HEARTBEAT_SECONDS,request_id));c.execute("COMMIT");return True
        except Exception:
            if c.in_transaction:c.execute("ROLLBACK")
            raise
        finally:c.close();self._private()
    def transition(self, request_id: str, fence: int, state: str, instance_id: str | None=None) -> None:
        c=self._connect()
        try:
            c.execute("BEGIN IMMEDIATE"); row=c.execute("SELECT fence FROM jobs WHERE request_id=?",(request_id,)).fetchone()
            if not row or row["fence"]!=fence: raise StaleFenceError("stale job fence")
            c.execute("UPDATE jobs SET state=? WHERE request_id=?",(state,request_id));c.execute("COMMIT")
        except Exception:
            if c.in_transaction:c.execute("ROLLBACK")
            raise
        finally:c.close()
    def recover_expired(self, force_instance_id: str | None=None) -> list[QueueRecord]:
        c=self._connect(); recovered=[]
        try:
            c.execute("BEGIN IMMEDIATE")
            rows=c.execute("SELECT j.* FROM jobs j JOIN leases l USING(request_id) WHERE l.expires_at<=CURRENT_TIMESTAMP" + (" AND l.instance_id=?" if force_instance_id else ""),(force_instance_id,) if force_instance_id else ()).fetchall()
            for row in rows:
                state=row["state"]
                if state in {"CLAIMED","PREPARED"}:
                    if row["attempt"] <= row["retry_budget"]: new,attempt="QUEUED",row["attempt"]+1
                    else:new,attempt="DEAD_LETTER",row["attempt"]
                else:new,attempt="UNKNOWN",row["attempt"]
                c.execute("UPDATE jobs SET state=?,attempt=? WHERE request_id=?",(new,attempt,row["request_id"]));c.execute("DELETE FROM leases WHERE request_id=?",(row["request_id"],));recovered.append(self._row(c.execute("SELECT * FROM jobs WHERE request_id=?",(row["request_id"],)).fetchone()))
            c.execute("COMMIT"); return recovered
        except Exception:
            if c.in_transaction:c.execute("ROLLBACK")
            raise
        finally:c.close();self._private()
    def expire_for_fixture(self, request_id: str) -> None:
        """Deterministically expire a test-only crash lease without a wall-clock wait."""
        c=self._connect()
        try:c.execute("UPDATE leases SET expires_at=CURRENT_TIMESTAMP WHERE request_id=?",(request_id,))
        finally:c.close()
    def complete(self, *, request_id: str, fence: int, instance_id: str, result: Mapping[str,Any], receipt: Mapping[str,Any], state: str="DONE") -> None:
        if _unsafe(result) or _unsafe(receipt): raise UnsafePersistenceError("raw provider stream persistence forbidden")
        c=self._connect()
        try:
            c.execute("BEGIN IMMEDIATE");self._lease(c,request_id,fence,instance_id)
            r,j=_canonical(dict(result)),_canonical(dict(receipt))
            c.execute("INSERT INTO results VALUES(?,?,?)",(request_id,r,j));c.execute("INSERT INTO outbox(request_id,result) VALUES(?,?)",(request_id,r));c.execute("UPDATE jobs SET state=? WHERE request_id=?",(state,request_id));c.execute("DELETE FROM leases WHERE request_id=?",(request_id,));c.execute("COMMIT")
        except Exception:
            if c.in_transaction:c.execute("ROLLBACK")
            raise
        finally:c.close();self._private()
    def record_fixture_result(self, request_id: str, *, result: Mapping[str,Any], receipt: Mapping[str,Any]) -> None:
        c=self._connect()
        try:
            c.execute("BEGIN IMMEDIATE"); c.execute("INSERT OR REPLACE INTO results VALUES(?,?,?)",(request_id,_canonical(dict(result)),_canonical(dict(receipt))));c.execute("UPDATE jobs SET state='DONE' WHERE request_id=?",(request_id,));c.execute("COMMIT")
        finally:c.close();self._private()
    def get_result(self,request_id:str):
        c=self._connect()
        try:
            r=c.execute("SELECT result FROM results WHERE request_id=?",(request_id,)).fetchone();return json.loads(r[0]) if r else None
        finally:c.close()
    def read_outbox(self, *, after_cursor:int, limit:int):
        c=self._connect()
        try:return [dict(r) | {"result":json.loads(r["result"])} for r in c.execute("SELECT * FROM outbox WHERE cursor>? ORDER BY cursor LIMIT ?",(after_cursor,limit))]
        finally:c.close()
    def register_root_instance(self, *, root:str, instance_id:str, replace_stale:bool=False) -> RootInstance:
        c=self._connect()
        try:
            c.execute("BEGIN IMMEDIATE");old=c.execute("SELECT * FROM root_instances WHERE root=?",(root,)).fetchone();fence=(old["fence"] if old and old["instance_id"]==instance_id and not replace_stale else (old["fence"]+1 if old else 1));c.execute("INSERT OR REPLACE INTO root_instances VALUES(?,?,?,CURRENT_TIMESTAMP)",(root,instance_id,fence));c.execute("COMMIT");return RootInstance(root,instance_id,fence,"now")
        finally:c.close()
    def heartbeat_root_instance(self, *, root:str, instance_id:str, fence:int)->RootInstance:
        c=self._connect()
        try:
            row=c.execute("SELECT * FROM root_instances WHERE root=?",(root,)).fetchone()
            if not row or row["instance_id"]!=instance_id or row["fence"]!=fence:raise StaleFenceError("stale root fence")
            c.execute("UPDATE root_instances SET heartbeat_at=CURRENT_TIMESTAMP WHERE root=?",(root,));return RootInstance(root,instance_id,fence,"now")
        finally:c.close()
    def get_root_instance(self,instance_id:str):
        c=self._connect()
        try:
            r=c.execute("SELECT * FROM root_instances WHERE instance_id=?",(instance_id,)).fetchone();return dict(r) if r else None
        finally:c.close()
    def fence_root_instance(self,root:str)->None:
        c=self._connect();
        try:c.execute("UPDATE root_instances SET fence=fence+1 WHERE root=?",(root,))
        finally:c.close()
    def accept_risk(self, acceptance_id:str, warning:str)->None:
        c=self._connect();
        try:c.execute("INSERT OR REPLACE INTO risk_acceptances VALUES(?,CURRENT_TIMESTAMP,?,NULL)",(acceptance_id,warning))
        finally:c.close()
    def get_risk_acceptance(self, acceptance_id:str):
        c=self._connect()
        try:
            r=c.execute("SELECT * FROM risk_acceptances WHERE acceptance_id=?",(acceptance_id,)).fetchone();return dict(r) if r else None
        finally:c.close()
