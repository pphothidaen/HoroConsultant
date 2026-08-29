"""Independent local queue workers.  Dispatch is injected; no provider is wired here."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable, Mapping
from scripts.multiagent_durable_queue import DurableQueue, StaleFenceError

@dataclass(frozen=True)
class RootPolicy:
    aliases: frozenset[str]; max_workers: int; account_caps: Mapping[str,int]
    @classmethod
    def for_root(cls, root: str):
        if root == "A": return cls(frozenset(("codex1","codex2")),3,{"codex1":2,"codex2":2})
        if root == "B": return cls(frozenset(("agy1","agy2")),3,{"agy1":3,"agy2":3})
        raise ValueError("unknown root")

@dataclass(frozen=True)
class AdmissionDecision:
    allowed: bool; code: str = "ALLOWED"
class DispatchBlocked(RuntimeError):
    def __init__(self, code:str): self.code=code;super().__init__(code)

class _Lifecycle:
    def __init__(self, worker, job): self.worker=worker;self.job=job;self.state="CLAIMED";self.provider_was_started=False
    def prepared(self): self.worker.store.transition(self.job.request_id,self.job.fence,"PREPARED");self.state="PREPARED"
    def starting(self):
        if self.state != "PREPARED": raise RuntimeError("lifecycle ordering")
        self.worker.store.transition(self.job.request_id,self.job.fence,"STARTING");self.state="STARTING"
    def provider_started(self):
        if self.state != "STARTING": raise RuntimeError("lifecycle ordering")
        self.worker.store.transition(self.job.request_id,self.job.fence,"RUNNING");self.state="RUNNING";self.provider_was_started=True

class RootWorker:
    def __init__(self, *, store: DurableQueue, root:str, instance_id:str, dispatcher:Callable, admission:Callable|None=None):
        self.store,self.root,self.instance_id,self.dispatcher=store,root,instance_id,dispatcher
        self.policy=RootPolicy.for_root(root);self.admission=admission or (lambda job: AdmissionDecision(True))
        self.pool=ThreadPoolExecutor(max_workers=self.policy.max_workers);self.running:dict[object,str]={};self.registration=None
    def register(self, replace_stale:bool=False):
        self.registration=self.store.register_root_instance(root=self.root,instance_id=self.instance_id,replace_stale=replace_stale);return self.registration
    def heartbeat_once(self):
        if self.registration is None:self.register()
        self.registration=self.store.heartbeat_root_instance(root=self.root,instance_id=self.instance_id,fence=self.registration.fence);return self.registration
    def poll_once(self):
        if self.registration is None:self.register()
        started=0
        active_aliases=list(self.running.values())
        while len(self.running)<self.policy.max_workers:
            job=self.store.claim(root=self.root,instance_id=self.instance_id,aliases=set(self.policy.aliases))
            if not job: break
            if active_aliases.count(job.alias)>=self.policy.account_caps[job.alias]:
                # Put an unstarted job back without changing retry semantics.
                self.store.transition(job.request_id,job.fence,"QUEUED"); break
            decision=self.admission(job)
            if not decision.allowed:
                self.store.transition(job.request_id,job.fence,"QUEUED"); break
            future=self.pool.submit(self._run,job);self.running[future]=job.alias;future.add_done_callback(self._finished);active_aliases.append(job.alias);started+=1
        return started
    def _finished(self,future): self.running.pop(future,None)
    def _run(self,job):
        lifecycle=_Lifecycle(self,job)
        try:
            result,receipt=self.dispatcher(job,lifecycle)
            self.store.complete(request_id=job.request_id,fence=job.fence,instance_id=self.instance_id,result=result,receipt=receipt)
        except DispatchBlocked as exc:
            self.store.complete(request_id=job.request_id,fence=job.fence,instance_id=self.instance_id,result={"status":exc.code,"findings":[]},receipt={"protocol_version":2},state="BLOCKED")
        except Exception:
            # An unstarted attempt can recover; provider-started is terminal UNKNOWN.
            if lifecycle.provider_was_started:
                self.store.transition(job.request_id,job.fence,"UNKNOWN")
            # otherwise retain its lease for expiry recovery.
    def wait_idle(self, timeout:float=5):
        import time
        end=time.monotonic()+timeout
        while self.running and time.monotonic()<end: time.sleep(.01)
    def close(self): self.pool.shutdown(wait=True)

def run_crash_fixture(*, store:DurableQueue, root:str, instance_id:str, request_id:str, crash_after:str)->None:
    policy=RootPolicy.for_root(root); job=store.claim(root=root,instance_id=instance_id,aliases=set(policy.aliases))
    if not job or job.request_id != request_id: raise RuntimeError("fixture claim failed")
    if crash_after == "prepared": store.transition(request_id,job.fence,"PREPARED")
    elif crash_after == "starting":
        store.transition(request_id,job.fence,"PREPARED");store.transition(request_id,job.fence,"STARTING")
    elif crash_after == "provider_started":
        store.transition(request_id,job.fence,"PREPARED");store.transition(request_id,job.fence,"STARTING");store.transition(request_id,job.fence,"RUNNING")
    else: raise ValueError("unknown crash phase")
    store.expire_for_fixture(request_id)
