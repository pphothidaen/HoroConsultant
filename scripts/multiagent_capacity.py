#!/usr/bin/env python3
"""Fail-closed, filesystem-backed S3 capacity leases."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import time
from typing import Any, Iterator, Mapping
import uuid

SCHEMA_VERSION = 1
AGY_DEFAULT_MAX_WORKERS = 3
KNOWN_ACCOUNTS = ("agy1", "agy2", "codex1", "codex2")
ACCOUNT_PROVIDERS = {"agy1": "agy", "agy2": "agy", "codex1": "codex", "codex2": "codex"}
_POLICY_KEYS = {"schema_version", "policy_version", "lease_ttl_seconds", "max_requests_per_lease", "accounts", "backpressure"}
_ACCOUNT_POLICY_KEYS = {"provider", "max_workers", "burn_rate", "circuit_breaker"}
_BURN_KEYS = {"max_requests", "window_seconds"}
_CIRCUIT_KEYS = {"failure_threshold", "failure_window_seconds", "cooldown_seconds", "failure_types", "allow_manual_reset"}
_BACKPRESSURE_KEYS = {"max_duration_seconds", "allow_manual_reset"}
_BACKPRESSURE_MODES = {"block", "queue"}
_FAILURE_TYPES = {"quota_exhausted", "rate_limit", "timeout", "invalid_provider_event", "missing_runtime_proof"}
_LEASE_KEYS = {"schema_version", "lease_id", "account", "pool", "provider", "request_id", "owner", "lane", "acquired_at", "expires_at", "request_budget", "requests_used", "model_quality_floor", "policy_version", "policy_sha256", "lease_sha256"}
_TOKEN = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-/")
_VERSION = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")


class CapacityLeaseError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"CAPACITY_ERROR:{code}")


class UnknownAccountError(CapacityLeaseError):
    def __init__(self) -> None: super().__init__("UNKNOWN_ACCOUNT")


class InvalidPolicyError(CapacityLeaseError):
    def __init__(self, code: str = "POLICY_INVALID") -> None: super().__init__(code)


class LeaseRejectedError(CapacityLeaseError): pass


@dataclass(frozen=True)
class CapacityLease:
    """A signed admission handle; it is not a provider execution receipt."""
    schema_version: int; lease_id: str; account: str; pool: str; provider: str
    request_id: str; owner: str; lane: int; acquired_at: float; expires_at: float
    request_budget: int; requests_used: int; model_quality_floor: str
    policy_version: str; policy_sha256: str; lease_sha256: str
    @property
    def remaining_budget(self) -> int: return self.request_budget - self.requests_used
    @property
    def ttl_seconds(self) -> float: return self.expires_at - self.acquired_at
    def to_dict(self) -> dict[str, Any]: return asdict(self)


def _digest(value: object) -> str:
    try: return hashlib.sha256(json.dumps(value, allow_nan=False, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")).hexdigest()
    except (TypeError, ValueError) as exc: raise InvalidPolicyError("CANONICALIZATION_ERROR") from exc


def _token(value: object, code: str, allowed: set[str] = _TOKEN) -> str:
    if not isinstance(value, str) or not value or not value.isascii() or any(c not in allowed for c in value): raise LeaseRejectedError(code)
    return value


def _integer(value: object, code: str, minimum: int = 1, *, policy: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum: raise (InvalidPolicyError if policy else LeaseRejectedError)(code)
    return value


def _number(value: object, code: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value < 0: raise LeaseRejectedError(code)
    return float(value)


def validate_capacity_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a closed four-account policy with explicit capacities."""
    if not isinstance(policy, Mapping) or set(policy) != _POLICY_KEYS: raise InvalidPolicyError()
    if policy.get("schema_version") != SCHEMA_VERSION: raise InvalidPolicyError("SCHEMA_VERSION_UNSUPPORTED")
    version = policy.get("policy_version")
    if not isinstance(version, str) or not version or not version.isascii() or any(c not in _VERSION for c in version): raise InvalidPolicyError("POLICY_VERSION_INVALID")
    accounts = policy.get("accounts")
    if not isinstance(accounts, Mapping) or set(accounts) != set(KNOWN_ACCOUNTS): raise InvalidPolicyError("ACCOUNT_REGISTRY_INVALID")
    normalized: dict[str, dict[str, Any]] = {}
    backpressure = policy.get("backpressure")
    if not isinstance(backpressure, Mapping) or set(backpressure) != _BACKPRESSURE_KEYS:
        raise InvalidPolicyError("BACKPRESSURE_POLICY_INVALID")
    normalized_backpressure = {
        "max_duration_seconds": _integer(backpressure.get("max_duration_seconds"), "BACKPRESSURE_DURATION_INVALID", policy=True),
        "allow_manual_reset": backpressure.get("allow_manual_reset"),
    }
    if not isinstance(normalized_backpressure["allow_manual_reset"], bool):
        raise InvalidPolicyError("BACKPRESSURE_RESET_POLICY_INVALID")
    for account in KNOWN_ACCOUNTS:
        item = accounts[account]
        if not isinstance(item, Mapping) or set(item) != _ACCOUNT_POLICY_KEYS: raise InvalidPolicyError("ACCOUNT_POLICY_INVALID")
        if item.get("provider") != ACCOUNT_PROVIDERS[account]: raise InvalidPolicyError("PROVIDER_MISMATCH")
        workers = _integer(item.get("max_workers"), "MAX_WORKERS_INVALID", policy=True)
        if account.startswith("agy") and workers != AGY_DEFAULT_MAX_WORKERS: raise InvalidPolicyError("AGY_MAX_WORKERS_MUST_BE_3")
        burn = item.get("burn_rate")
        if not isinstance(burn, Mapping) or set(burn) != _BURN_KEYS: raise InvalidPolicyError("BURN_RATE_POLICY_INVALID")
        circuit = item.get("circuit_breaker")
        if not isinstance(circuit, Mapping) or set(circuit) != _CIRCUIT_KEYS: raise InvalidPolicyError("CIRCUIT_POLICY_INVALID")
        failure_types = circuit.get("failure_types")
        if not isinstance(failure_types, list) or not failure_types or len(set(failure_types)) != len(failure_types) or set(failure_types) - _FAILURE_TYPES:
            raise InvalidPolicyError("CIRCUIT_FAILURE_TYPES_INVALID")
        if not isinstance(circuit.get("allow_manual_reset"), bool): raise InvalidPolicyError("CIRCUIT_RESET_POLICY_INVALID")
        normalized[account] = {
            "provider": ACCOUNT_PROVIDERS[account], "max_workers": workers,
            "burn_rate": {"max_requests": _integer(burn.get("max_requests"), "BURN_RATE_THRESHOLD_INVALID", policy=True), "window_seconds": _integer(burn.get("window_seconds"), "BURN_RATE_WINDOW_INVALID", policy=True)},
            "circuit_breaker": {"failure_threshold": _integer(circuit.get("failure_threshold"), "CIRCUIT_THRESHOLD_INVALID", policy=True), "failure_window_seconds": _integer(circuit.get("failure_window_seconds"), "CIRCUIT_WINDOW_INVALID", policy=True), "cooldown_seconds": _integer(circuit.get("cooldown_seconds"), "CIRCUIT_COOLDOWN_INVALID", policy=True), "failure_types": list(failure_types), "allow_manual_reset": circuit["allow_manual_reset"]},
        }
    return {"schema_version": SCHEMA_VERSION, "policy_version": version, "lease_ttl_seconds": _integer(policy.get("lease_ttl_seconds"), "TTL_INVALID", policy=True), "max_requests_per_lease": _integer(policy.get("max_requests_per_lease"), "REQUEST_BUDGET_INVALID", policy=True), "accounts": normalized, "backpressure": normalized_backpressure}


def _unsigned(lease: CapacityLease | Mapping[str, Any]) -> dict[str, Any]:
    source = lease.to_dict() if isinstance(lease, CapacityLease) else dict(lease)
    return {k: source[k] for k in _LEASE_KEYS - {"lease_sha256"}}


def _parse_lease(value: CapacityLease | Mapping[str, Any], *, verify: bool = True) -> CapacityLease:
    record = value.to_dict() if isinstance(value, CapacityLease) else dict(value) if isinstance(value, Mapping) else None
    if record is None or set(record) != _LEASE_KEYS: raise LeaseRejectedError("LEASE_MISMATCH")
    try: lease = CapacityLease(**record)
    except TypeError as exc: raise LeaseRejectedError("LEASE_MISMATCH") from exc
    try:
        valid = (lease.schema_version == SCHEMA_VERSION and len(lease.lease_id) == 32 and all(c in "0123456789abcdef" for c in lease.lease_id) and lease.account in ACCOUNT_PROVIDERS and lease.pool == lease.account and lease.provider == ACCOUNT_PROVIDERS[lease.account] and _token(lease.request_id, "LEASE_MISMATCH") and _token(lease.owner, "LEASE_MISMATCH") and _token(lease.model_quality_floor, "LEASE_MISMATCH") and _token(lease.policy_version, "LEASE_MISMATCH", _VERSION) and _integer(lease.lane, "LEASE_MISMATCH") and _integer(lease.request_budget, "LEASE_MISMATCH") and isinstance(lease.requests_used, int) and not isinstance(lease.requests_used, bool) and 0 <= lease.requests_used <= lease.request_budget and len(lease.policy_sha256) == 64 and len(lease.lease_sha256) == 64 and all(c in "0123456789abcdef" for c in lease.policy_sha256 + lease.lease_sha256) and _number(lease.acquired_at, "LEASE_MISMATCH") < _number(lease.expires_at, "LEASE_MISMATCH"))
    except (TypeError, CapacityLeaseError): valid = False
    if not valid: raise LeaseRejectedError("LEASE_MISMATCH")
    if verify and _digest(_unsigned(record)) != lease.lease_sha256: raise LeaseRejectedError("STATE_INVALID")
    return lease


def _sign(unsigned: dict[str, Any]) -> CapacityLease: return CapacityLease(**unsigned, lease_sha256=_digest(unsigned))
def _now(value: float | int | None) -> float: return _number(time.time() if value is None else value, "CLOCK_INVALID")
def _empty(policy: Mapping[str, Any]) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "policy_sha256": _digest(policy), "leases": {}, "terminal": {}, "burn_events": {account: [] for account in KNOWN_ACCOUNTS}, "failures": {account: [] for account in KNOWN_ACCOUNTS}, "circuits": {account: None for account in KNOWN_ACCOUNTS}, "backpressure": {account: None for account in KNOWN_ACCOUNTS}}


def _validate_state(state: object, policy: Mapping[str, Any]) -> dict[str, Any]:
    keys = {"schema_version", "policy_sha256", "leases", "terminal", "burn_events", "failures", "circuits", "backpressure"}
    if not isinstance(state, dict) or set(state) != keys or state.get("schema_version") != SCHEMA_VERSION or state.get("policy_sha256") != _digest(policy) or not isinstance(state.get("leases"), dict) or not isinstance(state.get("terminal"), dict): raise LeaseRejectedError("POLICY_MISMATCH")
    for key in ("burn_events", "failures", "circuits", "backpressure"):
        if not isinstance(state.get(key), dict) or set(state[key]) != set(KNOWN_ACCOUNTS): raise LeaseRejectedError("STATE_INVALID")
    for ident, record in state["leases"].items():
        lease = _parse_lease(record)
        if ident != lease.lease_id or lease.policy_version != policy["policy_version"] or lease.policy_sha256 != _digest(policy): raise LeaseRejectedError("STATE_INVALID")
    return state


def _trim_pressure(state: dict[str, Any], policy: Mapping[str, Any], now: float) -> bool:
    """Expire local pressure evidence only by policy windows and local clock."""
    changed = False
    for account in KNOWN_ACCOUNTS:
        burn_window = policy["accounts"][account]["burn_rate"]["window_seconds"]
        failures_window = policy["accounts"][account]["circuit_breaker"]["failure_window_seconds"]
        for key, window in (("burn_events", burn_window), ("failures", failures_window)):
            values = state[key][account]
            if not isinstance(values, list) or any(not isinstance(event, dict) or not isinstance(event.get("at"), (int, float)) or isinstance(event.get("at"), bool) for event in values): raise LeaseRejectedError("STATE_INVALID")
            if key == "burn_events" and any(set(event) != {"at", "requests", "lease_id"} or not isinstance(event.get("requests"), int) or isinstance(event.get("requests"), bool) or event["requests"] < 1 or not isinstance(event.get("lease_id"), str) for event in values): raise LeaseRejectedError("STATE_INVALID")
            if key == "failures" and any(set(event) != {"at", "type"} or event.get("type") not in policy["accounts"][account]["circuit_breaker"]["failure_types"] for event in values): raise LeaseRejectedError("STATE_INVALID")
            kept = [event for event in values if float(event["at"]) > now - window]
            if len(kept) != len(values): state[key][account] = kept; changed = True
        circuit = state["circuits"][account]
        if circuit is not None:
            if not isinstance(circuit, dict) or set(circuit) != {"opened_at", "open_until", "failure_type"} or not isinstance(circuit["opened_at"], (int, float)) or isinstance(circuit["opened_at"], bool) or not isinstance(circuit["open_until"], (int, float)) or isinstance(circuit["open_until"], bool) or circuit["open_until"] <= circuit["opened_at"] or circuit["failure_type"] not in policy["accounts"][account]["circuit_breaker"]["failure_types"]: raise LeaseRejectedError("STATE_INVALID")
            if float(circuit["open_until"]) <= now: state["circuits"][account] = None; changed = True
        pressure = state["backpressure"][account]
        if pressure is not None:
            if not isinstance(pressure, dict) or set(pressure) != {"mode", "set_at", "until"} or pressure["mode"] not in _BACKPRESSURE_MODES or not isinstance(pressure["set_at"], (int, float)) or isinstance(pressure["set_at"], bool) or not isinstance(pressure["until"], (int, float)) or isinstance(pressure["until"], bool) or pressure["until"] <= pressure["set_at"]: raise LeaseRejectedError("STATE_INVALID")
            if float(pressure["until"]) <= now: state["backpressure"][account] = None; changed = True
    return changed


def _burn_used(state: Mapping[str, Any], account: str) -> int:
    events = state["burn_events"][account]
    if any(not isinstance(event.get("requests"), int) or isinstance(event.get("requests"), bool) or event["requests"] < 1 for event in events): raise LeaseRejectedError("STATE_INVALID")
    return sum(event["requests"] for event in events)


def _admission_gate(state: Mapping[str, Any], policy: Mapping[str, Any], account: str) -> None:
    pressure = state["backpressure"][account]
    if pressure is not None: raise LeaseRejectedError("BACKPRESSURE_QUEUED" if pressure["mode"] == "queue" else "BACKPRESSURE_BLOCKED")
    if state["circuits"][account] is not None: raise LeaseRejectedError("CIRCUIT_OPEN")
    if _burn_used(state, account) >= policy["accounts"][account]["burn_rate"]["max_requests"]: raise LeaseRejectedError("BURN_RATE_EXCEEDED")


@contextmanager
def _locked(root: str | os.PathLike[str], policy: Mapping[str, Any]) -> Iterator[dict[str, Any]]:
    directory = Path(root).resolve()
    try:
        directory.mkdir(parents=True, exist_ok=True, mode=0o700); directory.chmod(0o700)
        lock = (directory / ".capacity.lock").open("a+b"); os.chmod(lock.name, 0o600); fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        source = directory / ".capacity.json"
        if source.exists():
            def duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
                result = dict(pairs)
                if len(result) != len(pairs): raise LeaseRejectedError("STATE_INVALID")
                return result
            state = _validate_state(json.loads(source.read_text("utf-8"), object_pairs_hook=duplicates, parse_constant=lambda _: (_ for _ in ()).throw(LeaseRejectedError("STATE_INVALID"))), policy)
        else: state = _empty(policy)
        yield state
    except CapacityLeaseError: raise
    except (OSError, json.JSONDecodeError, TypeError) as exc: raise LeaseRejectedError("STORAGE_UNAVAILABLE") from exc
    finally:
        if 'lock' in locals(): fcntl.flock(lock.fileno(), fcntl.LOCK_UN); lock.close()


def _write(root: str | os.PathLike[str], state: dict[str, Any]) -> None:
    directory = Path(root).resolve(); fd, temp = tempfile.mkstemp(prefix=".capacity.", dir=directory)
    try:
        os.fchmod(fd, 0o600); os.write(fd, json.dumps(state, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")); os.fsync(fd); os.close(fd); fd = -1; os.replace(temp, directory / ".capacity.json"); temp = ""
    finally:
        if fd >= 0: os.close(fd)
        if temp:
            try: os.unlink(temp)
            except OSError: pass


def _reap(state: dict[str, Any], now: float) -> int:
    expired = [key for key, value in state["leases"].items() if value["expires_at"] <= now]
    for key in expired:
        value = state["leases"].pop(key); state["terminal"][key] = {"status": "expired", "lease_sha256": value["lease_sha256"], "terminal_at": now}
    return len(expired)


def acquire_lease(store_path: str | os.PathLike[str], *, account: str, request_id: str, owner: str, lane: int, request_budget: int, model_quality_floor: str, policy: Mapping[str, Any], now: float | int | None = None, ttl_seconds: int | None = None) -> CapacityLease:
    """Atomically reserve one account-local lane, bounded by the canonical policy."""
    policy = validate_capacity_policy(policy)
    if account not in ACCOUNT_PROVIDERS: raise UnknownAccountError()
    _token(request_id, "REQUEST_ID_INVALID"); _token(owner, "OWNER_INVALID"); _token(model_quality_floor, "QUALITY_FLOOR_INVALID"); _integer(lane, "LANE_INVALID"); _integer(request_budget, "NON_POSITIVE_BUDGET")
    if request_budget > policy["max_requests_per_lease"]: raise LeaseRejectedError("BUDGET_OVERRUN")
    ttl = policy["lease_ttl_seconds"] if ttl_seconds is None else _integer(ttl_seconds, "TTL_INVALID")
    if ttl > policy["lease_ttl_seconds"]: raise LeaseRejectedError("TTL_OVERRUN")
    current = _now(now)
    with _locked(store_path, policy) as state:
        changed = bool(_reap(state, current))
        changed = _trim_pressure(state, policy, current) or changed
        try: _admission_gate(state, policy, account)
        except LeaseRejectedError:
            if changed: _write(store_path, state)
            raise
        if any(item["request_id"] == request_id for item in state["leases"].values()):
            if changed: _write(store_path, state)
            raise LeaseRejectedError("REQUEST_ALREADY_LEASED")
        active = [item for item in state["leases"].values() if item["account"] == account]
        if len(active) >= policy["accounts"][account]["max_workers"]:
            if changed: _write(store_path, state)
            raise LeaseRejectedError("OVER_CAPACITY")
        unsigned = {"schema_version": SCHEMA_VERSION, "lease_id": uuid.uuid4().hex, "account": account, "pool": account, "provider": ACCOUNT_PROVIDERS[account], "request_id": request_id, "owner": owner, "lane": lane, "acquired_at": current, "expires_at": current + ttl, "request_budget": request_budget, "requests_used": 0, "model_quality_floor": model_quality_floor, "policy_version": policy["policy_version"], "policy_sha256": _digest(policy)}
        lease = _sign(unsigned); state["leases"][lease.lease_id] = lease.to_dict(); _write(store_path, state); return lease


def consume_lease(store_path: str | os.PathLike[str], lease: CapacityLease | Mapping[str, Any], *, requests: int, policy: Mapping[str, Any], now: float | int | None = None) -> CapacityLease:
    """Atomically charge positive request consumption to a live lease."""
    candidate, policy, current = _parse_lease(lease), validate_capacity_policy(policy), _now(now); _integer(requests, "CONSUMPTION_INVALID")
    with _locked(store_path, policy) as state:
        changed = _trim_pressure(state, policy, current)
        stored = state["leases"].get(candidate.lease_id)
        if stored is None: raise LeaseRejectedError("REPLAY_REJECTED" if candidate.lease_id in state["terminal"] else "LEASE_MISMATCH")
        stored_lease = _parse_lease(stored)
        if stored_lease.to_dict() != candidate.to_dict(): raise LeaseRejectedError("LEASE_MISMATCH")
        if stored_lease.expires_at <= current: _reap(state, current); _write(store_path, state); raise LeaseRejectedError("LEASE_EXPIRED")
        if requests > stored_lease.remaining_budget: raise LeaseRejectedError("BUDGET_OVERRUN")
        if _burn_used(state, stored_lease.account) + requests > policy["accounts"][stored_lease.account]["burn_rate"]["max_requests"]:
            if changed: _write(store_path, state)
            raise LeaseRejectedError("BURN_RATE_EXCEEDED")
        updated = _sign({**_unsigned(stored_lease), "requests_used": stored_lease.requests_used + requests})
        state["leases"][updated.lease_id] = updated.to_dict()
        state["burn_events"][stored_lease.account].append({"at": current, "requests": requests, "lease_id": stored_lease.lease_id})
        _write(store_path, state); return updated


def release_lease(store_path: str | os.PathLike[str], lease: CapacityLease | Mapping[str, Any], *, policy: Mapping[str, Any], requests_used: int | None = None, now: float | int | None = None) -> CapacityLease:
    candidate, policy, current = _parse_lease(lease), validate_capacity_policy(policy), _now(now)
    with _locked(store_path, policy) as state:
        stored = state["leases"].get(candidate.lease_id)
        if stored is None: raise LeaseRejectedError("REPLAY_REJECTED" if candidate.lease_id in state["terminal"] else "LEASE_MISMATCH")
        saved = _parse_lease(stored)
        if saved.to_dict() != candidate.to_dict(): raise LeaseRejectedError("LEASE_MISMATCH")
        if saved.expires_at <= current: _reap(state, current); _write(store_path, state); raise LeaseRejectedError("LEASE_EXPIRED")
        total = saved.requests_used if requests_used is None else _integer(requests_used, "BUDGET_OVERRUN", 0)
        if total < saved.requests_used or total > saved.request_budget: raise LeaseRejectedError("BUDGET_OVERRUN")
        released = _sign({**_unsigned(saved), "requests_used": total}); state["leases"].pop(saved.lease_id); state["terminal"][saved.lease_id] = {"status": "released", "lease_sha256": released.lease_sha256, "terminal_at": current}; _write(store_path, state); return released


def reap_expired(store_path: str | os.PathLike[str], *, policy: Mapping[str, Any], now: float | int | None = None) -> int:
    policy, current = validate_capacity_policy(policy), _now(now)
    with _locked(store_path, policy) as state:
        count = _reap(state, current)
        changed = _trim_pressure(state, policy, current)
        if count or changed: _write(store_path, state)
        return count


def set_backpressure(store_path: str | os.PathLike[str], *, account: str, mode: str, policy: Mapping[str, Any], duration_seconds: int | None = None, now: float | int | None = None) -> None:
    """Set an account-local S4 admission hold. It never reroutes another pool."""
    policy, current = validate_capacity_policy(policy), _now(now)
    if account not in ACCOUNT_PROVIDERS: raise UnknownAccountError()
    if mode not in _BACKPRESSURE_MODES: raise LeaseRejectedError("BACKPRESSURE_MODE_INVALID")
    duration = policy["backpressure"]["max_duration_seconds"] if duration_seconds is None else _integer(duration_seconds, "BACKPRESSURE_DURATION_INVALID")
    if duration > policy["backpressure"]["max_duration_seconds"]: raise LeaseRejectedError("BACKPRESSURE_DURATION_INVALID")
    with _locked(store_path, policy) as state:
        _trim_pressure(state, policy, current)
        state["backpressure"][account] = {"mode": mode, "set_at": current, "until": current + duration}
        _write(store_path, state)


def clear_backpressure(store_path: str | os.PathLike[str], *, account: str, policy: Mapping[str, Any], now: float | int | None = None) -> None:
    """Allow an early clear only when the policy explicitly authorizes it."""
    policy, current = validate_capacity_policy(policy), _now(now)
    if account not in ACCOUNT_PROVIDERS: raise UnknownAccountError()
    if not policy["backpressure"]["allow_manual_reset"]: raise LeaseRejectedError("BACKPRESSURE_RESET_NOT_ALLOWED")
    with _locked(store_path, policy) as state:
        _trim_pressure(state, policy, current); state["backpressure"][account] = None; _write(store_path, state)


def record_failure(store_path: str | os.PathLike[str], *, account: str, failure_type: str, policy: Mapping[str, Any], now: float | int | None = None) -> bool:
    """Record a typed local failure and open only this pool's circuit when configured."""
    policy, current = validate_capacity_policy(policy), _now(now)
    if account not in ACCOUNT_PROVIDERS: raise UnknownAccountError()
    if failure_type not in policy["accounts"][account]["circuit_breaker"]["failure_types"]: raise LeaseRejectedError("FAILURE_TYPE_NOT_ALLOWED")
    with _locked(store_path, policy) as state:
        _trim_pressure(state, policy, current)
        failures = state["failures"][account]
        failures.append({"at": current, "type": failure_type})
        circuit = policy["accounts"][account]["circuit_breaker"]
        opened = len(failures) >= circuit["failure_threshold"]
        if opened:
            state["circuits"][account] = {"opened_at": current, "open_until": current + circuit["cooldown_seconds"], "failure_type": failure_type}
        _write(store_path, state)
        return opened


def reset_circuit(store_path: str | os.PathLike[str], *, account: str, policy: Mapping[str, Any], now: float | int | None = None) -> None:
    """Permit an explicit local reset only when the checked policy permits it."""
    policy, current = validate_capacity_policy(policy), _now(now)
    if account not in ACCOUNT_PROVIDERS: raise UnknownAccountError()
    if not policy["accounts"][account]["circuit_breaker"]["allow_manual_reset"]: raise LeaseRejectedError("CIRCUIT_RESET_NOT_ALLOWED")
    with _locked(store_path, policy) as state:
        _trim_pressure(state, policy, current); state["circuits"][account] = None; state["failures"][account] = []; _write(store_path, state)


def capacity_snapshot(store_path: str | os.PathLike[str], *, policy: Mapping[str, Any], now: float | int | None = None) -> dict[str, Any]:
    """Return signed, provider-output-free account-local admission observations."""
    policy, current = validate_capacity_policy(policy), _now(now)
    with _locked(store_path, policy) as state:
        changed = bool(_reap(state, current))
        if _trim_pressure(state, policy, current) or changed: _write(store_path, state)
        accounts: dict[str, dict[str, Any]] = {}
        for account in KNOWN_ACCOUNTS:
            active = [item for item in state["leases"].values() if item["account"] == account]
            maximum = policy["accounts"][account]["max_workers"]
            burn = policy["accounts"][account]["burn_rate"]
            pressure = state["backpressure"][account]
            circuit = state["circuits"][account]
            accounts[account] = {"provider": ACCOUNT_PROVIDERS[account], "max_workers": maximum, "active_workers": len(active), "available_workers": maximum - len(active), "reserved_request_budget": sum(item["request_budget"] for item in active), "used_requests": sum(item["requests_used"] for item in active), "burn_rate": {"requests_in_window": _burn_used(state, account), **burn}, "backpressure": pressure, "circuit": circuit, "admission_state": "S5" if circuit else "S4" if pressure or _burn_used(state, account) >= burn["max_requests"] else "S3"}
        result = {"schema_version": SCHEMA_VERSION, "policy_sha256": _digest(policy), "observed_at": current, "accounts": accounts}
        return {**result, "snapshot_sha256": _digest(result)}


__all__ = ["AGY_DEFAULT_MAX_WORKERS", "KNOWN_ACCOUNTS", "CapacityLease", "CapacityLeaseError", "InvalidPolicyError", "LeaseRejectedError", "UnknownAccountError", "acquire_lease", "capacity_snapshot", "clear_backpressure", "consume_lease", "record_failure", "reap_expired", "release_lease", "reset_circuit", "set_backpressure", "validate_capacity_policy"]
