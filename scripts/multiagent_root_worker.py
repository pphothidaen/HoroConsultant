#!/usr/bin/env python3
"""Independent local workers for Root A and Root B durable queues.

Dispatch is injected.  This module does not select credentials, authenticate an
account, or treat a configured alias as provider execution proof.
"""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
import signal
import threading
import time
from types import MappingProxyType
from typing import Any, Callable, Mapping, Protocol

try:
    from scripts.multiagent_durable_queue import (
        DurableQueue,
        HEARTBEAT_SECONDS,
        QueueRecord,
        RootInstance,
        StaleFenceError,
    )
except ModuleNotFoundError:  # Direct execution from the repository root.
    from multiagent_durable_queue import (  # type: ignore[no-redef]
        DurableQueue,
        HEARTBEAT_SECONDS,
        QueueRecord,
        RootInstance,
        StaleFenceError,
    )


ROOT_POOL_WORKERS = 3
_ROOT_ACCOUNT_CAPS = {
    "A": MappingProxyType({"codex1": 2, "codex2": 2}),
    "B": MappingProxyType({"agy1": 3, "agy2": 3}),
}


@dataclass(frozen=True)
class RootPolicy:
    """Closed account ownership and local concurrency policy for one root."""

    aliases: frozenset[str]
    max_workers: int
    account_caps: Mapping[str, int]

    @classmethod
    def for_root(cls, root: str) -> "RootPolicy":
        try:
            account_caps = _ROOT_ACCOUNT_CAPS[root]
        except (KeyError, TypeError) as exc:
            raise ValueError("unknown root") from exc
        return cls(
            aliases=frozenset(account_caps),
            max_workers=ROOT_POOL_WORKERS,
            account_caps=account_caps,
        )


@dataclass(frozen=True)
class AdmissionDecision:
    """Typed local admission result; it is not a capacity or runtime receipt."""

    allowed: bool
    code: str = "ALLOWED"


class DispatchBlocked(RuntimeError):
    """A provider-independent typed block such as auth or executable failure."""

    def __init__(self, code: str) -> None:
        if not isinstance(code, str) or not code or not code.isascii():
            raise ValueError("dispatch block code must be non-empty ASCII")
        self.code = code
        super().__init__(code)


class Lifecycle(Protocol):
    def prepared(self) -> None: ...
    def starting(self) -> None: ...
    def provider_started(self) -> None: ...


Dispatcher = Callable[[QueueRecord, Lifecycle], tuple[Mapping[str, Any], Mapping[str, Any]]]
Admission = Callable[[QueueRecord], AdmissionDecision]


class _Lifecycle:
    """Persist lifecycle boundaries before external effects may occur."""

    def __init__(self, worker: "RootWorker", job: QueueRecord) -> None:
        self.worker = worker
        self.job = job
        self.state = "CLAIMED"
        self.provider_was_started = False

    @property
    def start_boundary_crossed(self) -> bool:
        return self.state in {"STARTING", "RUNNING"}

    def prepared(self) -> None:
        if self.state != "CLAIMED":
            raise RuntimeError("lifecycle event out of order")
        self.worker.store.transition(
            self.job.request_id,
            self.job.fence,
            "PREPARED",
            instance_id=self.worker.instance_id,
        )
        self.state = "PREPARED"

    def starting(self) -> None:
        if self.state != "PREPARED":
            raise RuntimeError("lifecycle event out of order")
        # STARTING is the no-blind-retry boundary: process creation can have an
        # unknown effect even before a provider-native start event is parsed.
        self.worker.store.transition(
            self.job.request_id,
            self.job.fence,
            "STARTING",
            instance_id=self.worker.instance_id,
        )
        self.state = "STARTING"

    def provider_started(self) -> None:
        if self.state != "STARTING":
            raise RuntimeError("lifecycle event out of order")
        self.worker.store.transition(
            self.job.request_id,
            self.job.fence,
            "RUNNING",
            instance_id=self.worker.instance_id,
        )
        self.state = "RUNNING"
        self.provider_was_started = True


class RootWorker:
    """Bounded thread-pool consumer for exactly one root's account aliases."""

    def __init__(
        self,
        *,
        store: DurableQueue,
        root: str,
        instance_id: str,
        dispatcher: Dispatcher,
        admission: Admission | None = None,
    ) -> None:
        self.store = store
        self.root = root
        self.instance_id = instance_id
        self.dispatcher = dispatcher
        self.policy = RootPolicy.for_root(root)
        self.admission = admission or (lambda _job: AdmissionDecision(True))
        self._pool = ThreadPoolExecutor(
            max_workers=self.policy.max_workers,
            thread_name_prefix=f"root-{root.lower()}-worker",
        )
        self._lock = threading.RLock()
        self._running: dict[Future[None], str] = {}
        self.registration: RootInstance | None = None

    @property
    def running(self) -> Mapping[Future[None], str]:
        with self._lock:
            return dict(self._running)

    def register(self, replace_stale: bool = False) -> RootInstance:
        self.registration = self.store.register_root_instance(
            root=self.root,
            instance_id=self.instance_id,
            replace_stale=replace_stale,
        )
        return self.registration

    def heartbeat_once(self) -> RootInstance:
        if self.registration is None:
            self.register()
        assert self.registration is not None
        self.registration = self.store.heartbeat_root_instance(
            root=self.root,
            instance_id=self.instance_id,
            fence=self.registration.fence,
        )
        return self.registration

    def _active_counts(self) -> Counter[str]:
        with self._lock:
            return Counter(self._running.values())

    def poll_once(self) -> int:
        """Admit as many jobs as the root and account-local caps allow."""

        if self.registration is None:
            self.register()
        started = 0
        while True:
            counts = self._active_counts()
            with self._lock:
                if len(self._running) >= self.policy.max_workers:
                    break
            available_aliases = {
                alias
                for alias in self.policy.aliases
                if counts[alias] < self.policy.account_caps[alias]
            }
            if not available_aliases:
                break
            job = self.store.claim(
                root=self.root,
                instance_id=self.instance_id,
                aliases=available_aliases,
            )
            if job is None:
                break
            try:
                decision = self.admission(job)
            except Exception:
                self.store.transition(job.request_id, job.fence, "QUEUED")
                raise
            if not isinstance(decision, AdmissionDecision):
                self.store.transition(job.request_id, job.fence, "QUEUED")
                raise TypeError("admission must return AdmissionDecision")
            if not decision.allowed:
                # Keep the exact alias queued.  Do not borrow or silently fall
                # back to another account when pressure or a circuit blocks it.
                self.store.transition(job.request_id, job.fence, "QUEUED")
                break
            future = self._pool.submit(self._run, job)
            with self._lock:
                self._running[future] = job.alias
            future.add_done_callback(self._finished)
            started += 1
        return started

    def _finished(self, future: Future[None]) -> None:
        with self._lock:
            self._running.pop(future, None)

    def _heartbeat_job(
        self,
        job: QueueRecord,
        stop: threading.Event,
    ) -> None:
        while not stop.wait(HEARTBEAT_SECONDS):
            try:
                self.store.heartbeat(
                    request_id=job.request_id,
                    fence=job.fence,
                    instance_id=self.instance_id,
                )
            except StaleFenceError:
                return

    def _run(self, job: QueueRecord) -> None:
        lifecycle = _Lifecycle(self, job)
        stop_heartbeat = threading.Event()
        heartbeat = threading.Thread(
            target=self._heartbeat_job,
            args=(job, stop_heartbeat),
            name=f"lease-heartbeat-{job.request_id}",
            daemon=True,
        )
        heartbeat.start()
        try:
            result, receipt = self.dispatcher(job, lifecycle)
            self.store.complete(
                request_id=job.request_id,
                fence=job.fence,
                instance_id=self.instance_id,
                result=result,
                receipt=receipt,
            )
        except DispatchBlocked as exc:
            if lifecycle.start_boundary_crossed:
                self.store.transition(job.request_id, job.fence, "UNKNOWN")
            else:
                self.store.complete(
                    request_id=job.request_id,
                    fence=job.fence,
                    instance_id=self.instance_id,
                    result={"status": exc.code, "findings": []},
                    receipt={"protocol_version": 2, "execution_started": False},
                    state="BLOCKED",
                )
        except Exception:
            # Before STARTING, the durable lease remains recoverable.  At or
            # after STARTING, the effect is ambiguous and cannot be retried.
            if lifecycle.start_boundary_crossed:
                self.store.transition(job.request_id, job.fence, "UNKNOWN")
        finally:
            stop_heartbeat.set()
            heartbeat.join(timeout=1)

    def wait_idle(self, timeout: float = 5) -> None:
        if timeout < 0:
            raise ValueError("timeout must be non-negative")
        deadline = time.monotonic() + timeout
        while time.monotonic() <= deadline:
            with self._lock:
                if not self._running:
                    return
            time.sleep(0.01)

    def close(self) -> None:
        self._pool.shutdown(wait=True)


def run_crash_fixture(
    *,
    store: DurableQueue,
    root: str,
    instance_id: str,
    request_id: str,
    crash_after: str,
) -> None:
    """Persist a deterministic crash boundary without invoking a provider."""

    policy = RootPolicy.for_root(root)
    job = store.claim(
        root=root,
        instance_id=instance_id,
        aliases=set(policy.aliases),
    )
    if job is None or job.request_id != request_id:
        raise RuntimeError("fixture claim failed")
    if crash_after == "prepared":
        store.transition(request_id, job.fence, "PREPARED")
    elif crash_after == "starting":
        store.transition(request_id, job.fence, "PREPARED")
        store.transition(request_id, job.fence, "STARTING")
    elif crash_after == "provider_started":
        store.transition(request_id, job.fence, "PREPARED")
        store.transition(request_id, job.fence, "STARTING")
        store.transition(request_id, job.fence, "RUNNING")
    else:
        raise ValueError("unknown crash phase")
    store.expire_for_fixture(request_id)


def _closed_admission(_job: QueueRecord) -> AdmissionDecision:
    # A standalone daemon has no bound provider adapter.  It must leave work
    # queued instead of fabricating a dispatch or typed execution receipt.
    return AdmissionDecision(False, "DISPATCH_NOT_CONFIGURED")


def _unreachable_dispatcher(
    _job: QueueRecord,
    _lifecycle: Lifecycle,
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    raise DispatchBlocked("BLOCKED_DISPATCH_NOT_CONFIGURED")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one local durable root worker")
    parser.add_argument("--root", choices=("A", "B"), required=True)
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--instance-id", required=True)
    parser.add_argument("--poll-interval", type=float, default=0.25)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.poll_interval <= 0:
        raise SystemExit("poll interval must be positive")
    store = DurableQueue(f"{args.state_dir}/durable-queue.sqlite3")
    worker = RootWorker(
        store=store,
        root=args.root,
        instance_id=args.instance_id,
        dispatcher=_unreachable_dispatcher,
        admission=_closed_admission,
    )
    stopping = threading.Event()

    def request_stop(_signum: int, _frame: object) -> None:
        stopping.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    worker.register()
    next_root_heartbeat = time.monotonic()
    try:
        while not stopping.is_set():
            if time.monotonic() >= next_root_heartbeat:
                worker.heartbeat_once()
                next_root_heartbeat = time.monotonic() + HEARTBEAT_SECONDS
            worker.poll_once()
            stopping.wait(args.poll_interval)
    except StaleFenceError:
        return 2
    finally:
        worker.close()
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "AdmissionDecision",
    "DispatchBlocked",
    "RootPolicy",
    "RootWorker",
    "run_crash_fixture",
]
