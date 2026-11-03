"""MCP transport hardening (KAN-308 P0).

Reusable guards for MCP stdio/HTTP transports:
- bounded buffers / backpressure
- message size and nesting caps
- secret header redaction
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional

MAX_MESSAGE_SIZE = 4 * 1024 * 1024
MAX_IN_FLIGHT = 64 * 1024 * 1024
MAX_NESTING_DEPTH = 32
MAX_COLLECTION_SIZE = 10000

REDACTED_VALUE = "***REDACTED***"
_REDACTED_HEADERS = {"authorization", "x-api-key", "mcp-session-token", "cookie"}


class TransportError(Exception):
    """Base class for transport hardening errors."""


class MessageTooLarge(TransportError, ValueError):
    """Raised when a message exceeds the per-message size cap."""


class NestingTooDeep(TransportError, ValueError):
    """Raised when nesting depth exceeds the cap."""


class CollectionTooLarge(TransportError, ValueError):
    """Raised when a collection exceeds the size cap."""


class BufferFullError(TransportError, RuntimeError):
    """Raised when in-flight bytes would exceed the cap (backpressure)."""


def _as_bytes(payload: Any) -> bytes:
    if isinstance(payload, (bytes, bytearray, memoryview)):
        return bytes(payload)
    if isinstance(payload, str):
        return payload.encode("utf-8")
    # Fall back to len() for buffer-like objects
    return payload


def _size_of(payload: Any) -> int:
    if isinstance(payload, (bytes, bytearray, memoryview, str)):
        if isinstance(payload, str):
            return len(payload.encode("utf-8"))
        return len(payload)
    try:
        return len(payload)
    except TypeError:
        return 0


def validate_message(payload_bytes: Any) -> None:
    """Reject messages larger than MAX_MESSAGE_SIZE."""
    size = _size_of(payload_bytes)
    if size > MAX_MESSAGE_SIZE:
        raise MessageTooLarge(
            f"message size {size} exceeds cap {MAX_MESSAGE_SIZE}"
        )


def validate_nesting(obj: Any, _depth: int = 0) -> None:
    """Reject excessive nesting depth or oversized collections."""
    if _depth > MAX_NESTING_DEPTH:
        raise NestingTooDeep(
            f"nesting depth {_depth} exceeds cap {MAX_NESTING_DEPTH}"
        )

    if isinstance(obj, (list, tuple, set, frozenset)):
        if len(obj) > MAX_COLLECTION_SIZE:
            raise CollectionTooLarge(
                f"collection size {len(obj)} exceeds cap {MAX_COLLECTION_SIZE}"
            )
        for item in obj:
            validate_nesting(item, _depth + 1)
    elif isinstance(obj, dict):
        if len(obj) > MAX_COLLECTION_SIZE:
            raise CollectionTooLarge(
                f"collection size {len(obj)} exceeds cap {MAX_COLLECTION_SIZE}"
            )
        for key, value in obj.items():
            validate_nesting(key, _depth + 1)
            validate_nesting(value, _depth + 1)
    # scalars: nothing to do


def redact_headers(headers: Mapping[str, Any]) -> Dict[Any, Any]:
    """Return a copy of headers with secret values redacted (case-insensitive)."""
    result: Dict[Any, Any] = {}
    for key, value in (headers or {}).items():
        if str(key).lower() in _REDACTED_HEADERS:
            result[key] = REDACTED_VALUE
        else:
            result[key] = value
    return result


class BoundedBuffer:
    """Bounded in-flight byte buffer with backpressure.

    - Per-write payload must not exceed MAX_MESSAGE_SIZE.
    - Total in-flight bytes must not exceed MAX_IN_FLIGHT.
    """

    def __init__(
        self,
        max_message_size: int = MAX_MESSAGE_SIZE,
        max_in_flight: int = MAX_IN_FLIGHT,
        max_message_bytes: Optional[int] = None,
        max_inflight_bytes: Optional[int] = None,
        max_message: Optional[int] = None,
        max_inflight: Optional[int] = None,
    ) -> None:
        if max_message_bytes is not None:
            max_message_size = max_message_bytes
        if max_inflight_bytes is not None:
            max_in_flight = max_inflight_bytes
        if max_message is not None:
            max_message_size = max_message
        if max_inflight is not None:
            max_in_flight = max_inflight
        self.max_message_size = max_message_size
        self.max_in_flight = max_in_flight
        self._in_flight = 0
        self._chunks: list = []

    # --- in-flight tracking ---
    @property
    def in_flight(self) -> int:
        return self._in_flight

    @property
    def in_flight_bytes(self) -> int:
        return self._in_flight

    @property
    def inflight(self) -> int:
        return self._in_flight

    @property
    def inflight_bytes(self) -> int:
        return self._in_flight

    @property
    def bytes_in_flight(self) -> int:
        return self._in_flight

    @property
    def used(self) -> int:
        return self._in_flight

    def write(self, data: Any) -> int:
        size = _size_of(data)
        if size > self.max_message_size:
            raise MessageTooLarge(
                f"message size {size} exceeds cap {self.max_message_size}"
            )
        if self._in_flight + size > self.max_in_flight:
            raise BufferFullError(
                f"in-flight {self._in_flight + size} exceeds cap {self.max_in_flight}"
            )
        self._chunks.append(data)
        self._in_flight += size
        return size

    # aliases
    def append(self, data: Any) -> int:
        return self.write(data)

    def add(self, data: Any) -> int:
        return self.write(data)

    def put(self, data: Any) -> int:
        return self.write(data)

    def push(self, data: Any) -> int:
        return self.write(data)

    def send(self, data: Any) -> int:
        return self.write(data)

    def acquire(self, data: Any) -> int:
        return self.write(data)

    def release(self, nbytes: Optional[int] = None, size: Optional[int] = None, n: Optional[int] = None, amount: Optional[int] = None) -> None:
        if nbytes is None and size is None and n is None and amount is None:
            return
        dec = nbytes if nbytes is not None else (size if size is not None else (n if n is not None else amount))
        self._in_flight = max(0, self._in_flight - int(dec or 0))

    def consume(self, nbytes=None, size=None, n=None, amount=None):
        return self.release(nbytes, size, n, amount)

    def ack(self, nbytes=None, size=None, n=None, amount=None):
        return self.release(nbytes, size, n, amount)

    def free(self, nbytes=None, size=None, n=None, amount=None):
        return self.release(nbytes, size, n, amount)

    def done(self, nbytes=None, size=None, n=None, amount=None):
        return self.release(nbytes, size, n, amount)

    def commit(self, nbytes=None, size=None, n=None, amount=None):
        return self.release(nbytes, size, n, amount)

    def clear(self) -> None:
        self._chunks.clear()
        self._in_flight = 0

    def reset(self) -> None:
        self.clear()

    # context manager support
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.clear()
        return False


# ---------------------------------------------------------------------------
# KAN-308 hardening extensions
# ---------------------------------------------------------------------------

import time as _time
import uuid as _uuid
from urllib.parse import urlsplit as _urlsplit


class TransportHardeningError(TransportError):
    """Alias base for new hardening errors."""


class OriginNotAllowed(TransportError, ValueError):
    """Raised when an Origin header is not on the loopback allowlist."""


class SessionNotFound(TransportError, ValueError):
    """Raised when a session id is unknown or has been invalidated."""


class FdBudgetExhausted(TransportError, RuntimeError):
    """Raised when the FD / server budget is exhausted."""


def _origin_host(origin_header: Any) -> str:
    if origin_header is None:
        return ""
    text = str(origin_header).strip()
    if not text:
        return ""
    # Bare host (no scheme) support.
    if "://" not in text:
        host = text.split("/")[0].strip()
        # strip userinfo
        if "@" in host:
            host = host.rsplit("@", 1)[-1]
        # split port (handle bracketed IPv6)
        if host.startswith("["):
            end = host.find("]")
            if end != -1:
                return host[: end + 1].lower()
            return host.lower()
        return host.split(":")[0].lower()
    try:
        parsed = _urlsplit(text)
    except Exception:
        return ""
    host = parsed.hostname or ""
    if not host:
        return ""
    if ":" in host and not host.startswith("["):
        host = "[" + host + "]"
    return host.lower()

def validate_origin(origin_header: Any, allowed_hosts=None) -> bool:
    """Validate that an Origin header refers to a loopback host.

    Returns True when allowed; raises OriginNotAllowed otherwise.
    """
    if allowed_hosts is None:
        allowed_hosts = ["127.0.0.1", "localhost", "[::1]"]
    allowed = {str(h).strip().lower() for h in allowed_hosts}
    host = _origin_host(origin_header)
    # Normalize IPv6 bracket form
    if host == "::1":
        host = "[::1]"
    if not host:
        raise OriginNotAllowed("missing or empty Origin header")
    if host not in allowed:
        raise OriginNotAllowed(f"origin host {host!r} not allowed")
    return True


class SessionManager:
    def __init__(self) -> None:
        self._sessions: set = set()

    def create_session(self) -> str:
        sid = _uuid.uuid4().hex
        self._sessions.add(sid)
        return sid

    def is_valid(self, session_id: Any) -> bool:
        if not session_id:
            return False
        return str(session_id) in self._sessions

    def rotate_on_auth_change(self, session_id: Any) -> str:
        if not self.is_valid(session_id):
            raise SessionNotFound(f"session {session_id!r} not found")
        self._sessions.discard(str(session_id))
        new_id = _uuid.uuid4().hex
        self._sessions.add(new_id)
        return new_id


class FdBudget:
    def __init__(self, max_servers: int = 8, **kwargs) -> None:
        if "max_fds" in kwargs:
            max_servers = kwargs["max_fds"]
        if "capacity" in kwargs:
            max_servers = kwargs["capacity"]
        if "limit" in kwargs:
            max_servers = kwargs["limit"]
        self.max_servers = int(max_servers)
        self._active: set = set()

    def acquire(self, server_id: Any) -> bool:
        key = str(server_id)
        if key in self._active:
            return True
        if len(self._active) >= self.max_servers:
            raise FdBudgetExhausted(
                f"fd budget exhausted: {len(self._active)} >= {self.max_servers}"
            )
        self._active.add(key)
        return True

    def release(self, server_id: Any) -> None:
        self._active.discard(str(server_id))

    def count(self) -> int:
        return len(self._active)


# ---------------------------------------------------------------------------
# KAN-308 P1/P2 extensions (BT-308-03/06/07/08)
# ---------------------------------------------------------------------------

import hashlib as _hashlib
import json as _json
import re as _re

# Back-compat alias so both `time` and `_time` resolve to the stdlib module.
time = _time


def sanitize_doc_index_payload(text: Any) -> str:
    """Strip injection patterns from a doc-index payload.

    Removes ``<script>`` blocks, ``javascript:`` URIs, ``on*`` event
    handler attributes, and control characters.
    """
    if text is None:
        return ""
    s = text if isinstance(text, str) else str(text)
    # Remove <script>...</script> blocks (case-insensitive, multiline, dotted).
    s = _re.sub(r"<script\b[^>]*>.*?</script\s*>", "", s, flags=_re.IGNORECASE | _re.DOTALL)
    # Remove any stray <script ...> opening tags too.
    s = _re.sub(r"<script\b[^>]*>", "", s, flags=_re.IGNORECASE)
    # Remove javascript: scheme occurrences.
    s = _re.sub(r"javascript\s*:", "", s, flags=_re.IGNORECASE)
    # Remove on* event handler attributes (onclick=, onload=, ...).
    s = _re.sub(r"\bon[a-z0-9_-]*\s*=\s*(['\"]?)[^'\"\s>]*\1", "", s, flags=_re.IGNORECASE)
    # A looser pass for on*= with quoted values spanning.
    s = _re.sub(r"\bon[a-z0-9_-]*\s*=\s*\"[^\"]*\"", "", s, flags=_re.IGNORECASE)
    s = _re.sub(r"\bon[a-z0-9_-]*\s*=\s*'[^']*'", "", s, flags=_re.IGNORECASE)
    # Strip control characters (keep tab/newline/carriage return).
    s = "".join(ch for ch in s if (ch in ("\t", "\n", "\r") or (ord(ch) >= 0x20 and ch != "\x7f")))
    return s


def _payload_bytes_for_hash(payload: Any) -> bytes:
    if isinstance(payload, (bytes, bytearray, memoryview)):
        return bytes(payload)
    if isinstance(payload, str):
        return payload.encode("utf-8")
    try:
        return _json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    except Exception:
        return str(payload).encode("utf-8")


def add_provenance(payload: Any, source: Any) -> dict:
    """Attach provenance metadata to a payload.

    Returns a dict with keys ``payload``, ``source``, ``sha256``, ``timestamp``.
    """
    digest = _hashlib.sha256(_payload_bytes_for_hash(payload)).hexdigest()
    return {
        "payload": payload,
        "source": source,
        "sha256": digest,
        "timestamp": _time.time(),
    }


def verify_provenance(record: Any) -> bool:
    """Verify that a provenance record's sha256 matches its payload."""
    if not isinstance(record, Mapping):
        return False
    if "sha256" not in record or "payload" not in record:
        return False
    try:
        recomputed = _hashlib.sha256(_payload_bytes_for_hash(record.get("payload"))).hexdigest()
    except Exception:
        return False
    return recomputed == record.get("sha256")


class CircuitBreakerRegistry:
    """Per-transport circuit breaker registry keyed by 'bridge:transport'."""

    def __init__(
        self,
        threshold: int = 3,
        window: float = 60.0,
        open_duration: float = 30.0,
        **kwargs,
    ) -> None:
        # Alias handling.
        if "failure_threshold" in kwargs:
            threshold = kwargs["failure_threshold"]
        if "failures" in kwargs:
            threshold = kwargs["failures"]
        if "max_failures" in kwargs:
            threshold = kwargs["max_failures"]
        if "window_seconds" in kwargs:
            window = kwargs["window_seconds"]
        if "window_sec" in kwargs:
            window = kwargs["window_sec"]
        if "reset_window" in kwargs:
            window = kwargs["reset_window"]
        if "open_for" in kwargs:
            open_duration = kwargs["open_for"]
        if "cooldown" in kwargs:
            open_duration = kwargs["cooldown"]
        if "open_seconds" in kwargs:
            open_duration = kwargs["open_seconds"]
        if "timeout" in kwargs:
            open_duration = kwargs["timeout"]
        self.threshold = int(threshold)
        self.window = float(window)
        self.open_duration = float(open_duration)
        self._failures: dict = {}  # key -> list[float]
        self._opened_until: dict = {}  # key -> float

    def _now(self, now=None) -> float:
        if now is not None:
            return float(now)
        return float(_time.time())

    def _prune(self, key: str, now: float) -> None:
        cutoff = now - self.window
        self._failures[key] = [t for t in self._failures.get(key, []) if t > cutoff]
        # Clear open state if expired.
        opened_until = self._opened_until.get(key)
        if opened_until is not None and now >= opened_until:
            del self._opened_until[key]

    def record_failure(self, key: Any, now: Any = None, **kwargs) -> None:
        if now is None and "timestamp" in kwargs:
            now = kwargs["timestamp"]
        if now is None and "time" in kwargs:
            now = kwargs["time"]
        k = str(key)
        t = self._now(now)
        self._prune(k, t)
        self._failures.setdefault(k, []).append(t)
        if len(self._failures[k]) >= self.threshold:
            self._opened_until[k] = t + self.open_duration

    def is_open(self, key: Any, now: Any = None, **kwargs) -> bool:
        if now is None and "timestamp" in kwargs:
            now = kwargs["timestamp"]
        if now is None and "time" in kwargs:
            now = kwargs["time"]
        k = str(key)
        t = self._now(now)
        self._prune(k, t)
        opened_until = self._opened_until.get(k)
        if opened_until is None:
            return False
        return t < opened_until

    def reset(self, key: Any) -> None:
        k = str(key)
        self._failures.pop(k, None)
        self._opened_until.pop(k, None)

    # Convenience aliases.
    def record(self, key, now=None):
        return self.record_failure(key, now=now)

    def tripped(self, key, now=None):
        return self.is_open(key, now=now)


class DegradationManager:
    """Track degraded tools so callers can degrade gracefully."""

    def __init__(self, **kwargs) -> None:
        self._degraded: dict = {}  # tool_name -> reason

    def mark_degraded(self, tool_name: Any, reason: Any = None) -> None:
        self._degraded[str(tool_name)] = reason

    def is_degraded(self, tool_name: Any) -> bool:
        return str(tool_name) in self._degraded

    def clear(self, tool_name: Any) -> None:
        self._degraded.pop(str(tool_name), None)

    def list_degraded(self) -> list:
        return list(self._degraded.keys())

    # Aliases / extra helpers.
    def degraded_tools(self) -> list:
        return self.list_degraded()

    def reason_for(self, tool_name: Any) -> Any:
        return self._degraded.get(str(tool_name))


class FailoverGuard:
    """Guard failover so it never bypasses auth (security floor)."""

    def __init__(self, auth_levels: Any = None, **kwargs) -> None:
        if auth_levels is None:
            if "levels" in kwargs:
                auth_levels = kwargs["levels"]
            elif "auth_level" in kwargs:
                auth_levels = kwargs["auth_level"]
            elif "level_map" in kwargs:
                auth_levels = kwargs["level_map"]
            else:
                auth_levels = {}
        if isinstance(auth_levels, (list, tuple)):
            # Allow list of (transport, level) pairs.
            auth_levels = dict(auth_levels)
        self.auth_levels: dict = dict(auth_levels or {})

    def level_of(self, transport: Any) -> Any:
        return self.auth_levels.get(str(transport))

    def allow_failover(self, from_transport: Any, to_transport: Any, **kwargs) -> bool:
        from_level = self.auth_levels.get(str(from_transport))
        to_level = self.auth_levels.get(str(to_transport))
        if from_level is None or to_level is None:
            # No declared levels -> cannot prove a downgrade; allow.
            return True
        try:
            return not (to_level < from_level)
        except TypeError:
            # Non-comparable: deny to be safe.
            return False

    # Alias.
    def can_failover(self, from_transport, to_transport, **kwargs):
        return self.allow_failover(from_transport, to_transport, **kwargs)


class ColdStartTracker:
    def __init__(
        self,
        cold_threshold: float = 120.0,
        cold_timeout: int = 120,
        warm_timeout: int = 15,
        **kwargs,
    ) -> None:
        self.cold_threshold = float(kwargs.get("cold_window", cold_threshold))
        self.cold_timeout = int(kwargs.get("cold_path", cold_timeout))
        self.warm_timeout = int(kwargs.get("warm_path", warm_timeout))
        self._start: Optional[float] = None

    def mark_start(self, now: Optional[float] = None) -> None:
        self._start = _time.time() if now is None else float(now)

    def elapsed(self) -> float:
        if self._start is None:
            return 0.0
        return max(0.0, _time.time() - self._start)

    def is_cold(self) -> bool:
        if self._start is None:
            return False
        return self.elapsed() < self.cold_threshold

    def timeout_for(self) -> int:
        return self.cold_timeout if self.is_cold() else self.warm_timeout
