#!/usr/bin/env python3
"""scripts/durable_store.py

KAN-275: a tiny durable store for the nightly sync's bookkeeping.

Why this exists: the sync wrote its output to a container-local path on Render's
free tier, where the filesystem is ephemeral and the instance spins down after 15
minutes idle. The job reported success while its result was discarded — the same
silent-success failure class as KAN-273.

What is stored is *bookkeeping only* (idempotency key, lease, fencing token,
heartbeat, last-success summary). The corpus itself is derived from Google Drive
and can be rebuilt, so it does not need to live here.

Backends:
  * local — a JSON file (tests, offline runs)
  * d1    — Cloudflare D1 over its REST API (production)
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class LeaseHeldError(RuntimeError):
    """Raised when another run holds a live lease on the same run key."""


STATE_KEY = "state"
D1_TIMEOUT_SECONDS = 10


def _d1_request(url: str, payload: dict[str, Any], token: str) -> dict[str, Any]:
    """POST one statement to the Cloudflare D1 REST API.

    Kept as a module-level function so tests can substitute it without network
    access (see tests/test_kan275_durable_store.py).
    """
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=D1_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


@dataclass
class DurableStore:
    backend: str
    location: str

    # ---------------------------------------------------------------- factories

    @classmethod
    def local(cls, path: str | Path) -> "DurableStore":
        return cls(backend="local", location=str(path))

    @classmethod
    def from_env(cls) -> "DurableStore":
        backend = os.getenv("HORO_DURABLE_STORE", "local").strip().lower()
        if backend == "d1":
            return cls(backend="d1", location=os.environ["HORO_D1_DATABASE_ID"])
        return cls.local(os.getenv("HORO_DURABLE_STORE_PATH", "project/data/sync_state.json"))

    # ------------------------------------------------------------------ plumbing

    def _d1_url(self) -> str:
        account = os.environ["CLOUDFLARE_ACCOUNT_ID"]
        return (
            f"https://api.cloudflare.com/client/v4/accounts/{account}"
            f"/d1/database/{self.location}/query"
        )

    def _d1_token(self) -> str:
        token = os.getenv("CLOUDFLARE_D1_API_TOKEN", "").strip()
        if not token:
            raise RuntimeError(
                "CLOUDFLARE_D1_API_TOKEN is not set; the d1 backend cannot persist "
                "bookkeeping. Refusing to continue rather than silently discard the run."
            )
        return token

    def _d1_rows(self, sql: str, params: list[Any]) -> list[dict[str, Any]]:
        """Run one statement and return the flattened result rows."""
        response = _d1_request(self._d1_url(), {"sql": sql, "params": params}, self._d1_token())
        if not response.get("success", False):
            raise RuntimeError(f"D1 query failed: {response.get('errors')}")
        blocks = response.get("result") or []
        return (blocks[0].get("results") if blocks else None) or []

    def _read_raw(self) -> dict[str, Any]:
        if self.backend == "local":
            path = Path(self.location)
            if not path.exists():
                return {}
            return json.loads(path.read_text(encoding="utf-8"))
        rows = self._d1_rows(
            "SELECT v FROM sync_state WHERE k = ?", [STATE_KEY]
        )
        if not rows:
            return {}
        return json.loads(rows[0]["v"])

    def _write_raw(self, payload: dict[str, Any]) -> None:
        if self.backend == "local":
            path = Path(self.location)
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            return
        self._d1_rows(
            "INSERT OR REPLACE INTO sync_state (k, v, updated_at) VALUES (?, ?, ?)",
            [STATE_KEY, json.dumps(payload, ensure_ascii=False), time.time()],
        )

    # --------------------------------------------------------------------- api

    def read(self) -> dict[str, Any]:
        return self._read_raw()

    def begin_run(self, run_key: str, owner: str, lease_seconds: int = 3600) -> dict[str, Any]:
        state = self._read_raw()
        now = time.time()
        lease = state.get("lease")
        if lease and lease.get("run_key") == run_key and lease.get("expires_at", 0) > now:
            raise LeaseHeldError(
                f"run {run_key} is leased by {lease.get('owner')} until {lease.get('expires_at')}"
            )
        token = int(state.get("fencing_counter", 0)) + 1
        state["fencing_counter"] = token
        state["lease"] = {
            "run_key": run_key,
            "owner": owner,
            "fencing_token": token,
            "started_at": now,
            "expires_at": now + lease_seconds,
        }
        state.setdefault("heartbeat", {})
        state["heartbeat"] = {"run_key": run_key, "step": "begin", "at": now}
        self._write_raw(state)
        return state["lease"]

    def heartbeat(self, run_key: str, step: str, detail: str = "") -> None:
        state = self._read_raw()
        state["heartbeat"] = {"run_key": run_key, "step": step, "detail": detail, "at": time.time()}
        self._write_raw(state)

    def complete_run(self, run_key: str, vectors: int = 0) -> None:
        state = self._read_raw()
        state["last_success"] = {
            "run_key": run_key,
            "vectors": vectors,
            "completed_at": time.time(),
            "heartbeat": state.get("heartbeat", {}),
        }
        state.pop("lease", None)
        self._write_raw(state)

    def is_stale(self, max_age_seconds: int = 86400) -> bool:
        state = self._read_raw()
        beat = state.get("heartbeat") or {}
        if not beat:
            return True
        return (time.time() - beat.get("at", 0)) > max_age_seconds
