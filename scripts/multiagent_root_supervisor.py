"""Local-only supervisor for two independently-owned durable queue roots."""
from __future__ import annotations
import argparse, hashlib, json, os, stat, tempfile, time, uuid
from pathlib import Path
from typing import Any, Mapping
try:
    from scripts.multiagent_durable_queue import DurableQueue
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution from repo root.
    from multiagent_durable_queue import DurableQueue  # type: ignore[no-redef]

class SupervisorError(RuntimeError): pass


class _FixtureProcess:
    """Minimal detached-process stand-in for the local smoke path."""
    _next_pid = 60000

    def __init__(self) -> None:
        type(self)._next_pid += 1
        self.pid = type(self)._next_pid
        self.alive = True

    def terminate(self) -> None: self.alive = False
    def kill(self) -> None: self.alive = False
    def poll(self): return None if self.alive else 0

def resolve_state_dir(*, repo_root:Path, environ:Mapping[str,str]|None=None)->Path:
    env=environ or os.environ; override=env.get("HORO_MULTIAGENT_STATE_DIR")
    if override:
        path=Path(override)
        if not path.is_absolute(): raise SupervisorError("state override must be absolute")
        return path
    base=Path(env.get("XDG_STATE_HOME", str(Path.home()/".local/state")))
    digest=hashlib.sha256(str(repo_root.resolve()).encode()).hexdigest()[:16]
    return base/"horoconsultant"/digest

class RootSupervisor:
    def __init__(self, *, state_dir:Path, account_homes:Mapping[str,Path]|None=None, process_factory=None, pid_probe=None):
        self.state_dir=Path(state_dir);self.queue=DurableQueue(self.state_dir/"durable-queue.sqlite3")
        self.account_homes=dict(account_homes or {});self.process_factory=process_factory or self._default_process;self.pid_probe=pid_probe or self._default_probe
        self.processes={};self.accepting_submissions=True;self.bootstrap_open=False;self.bootstrap_sealed=False;self.bootstrap_id=None
    def _default_process(self, **kwargs):
        class P:
            pid=0
            def terminate(self): pass
            def kill(self):pass
            def poll(self):return None
        return P()
    def _default_probe(self,pid): return False
    def init(self):
        self.state_dir.mkdir(parents=True,exist_ok=True,mode=0o700);self.state_dir.chmod(0o700);self.queue._private();return {"state_dir":str(self.state_dir)}
    def doctor(self, *, repair_home_permissions:bool=False):
        for home in self.account_homes.values():
            if home.is_symlink():
                if repair_home_permissions: raise SupervisorError("symlink account home")
                return {"ok":False,"code":"ACCOUNT_HOME_PERMISSIONS"}
            mode=stat.S_IMODE(home.stat().st_mode)
            if mode != 0o700:
                if repair_home_permissions:
                    if home.stat().st_uid != os.getuid(): raise SupervisorError("foreign owner")
                    home.chmod(0o700)
                else:return {"ok":False,"code":"ACCOUNT_HOME_PERMISSIONS"}
        return {"ok":True,"code":"OK"}
    def start(self, *, bootstrap_local_unsafe:bool=False, accept_risk:str|None=None, risk_statement:str|None=None):
        self.init()
        if bootstrap_local_unsafe:
            if self.bootstrap_sealed: raise SupervisorError("bootstrap sealed")
            if not accept_risk: raise SupervisorError("risk acceptance required")
            self.bootstrap_open=True;self.bootstrap_id=accept_risk;self.queue.accept_risk(accept_risk, risk_statement or "Local bootstrap unknown/constrained quota warning")
        else:self.bootstrap_open=False;self.bootstrap_id=None
        self.accepting_submissions=True;roots=[]
        for root in ("A","B"):
            instance=f"root-{root.lower()}-{uuid.uuid4().hex[:12]}";process=self.process_factory(root=root,instance_id=instance,state_dir=self.state_dir);self.processes[root]=(process,instance);roots.append({"root":root,"pid":process.pid,"instance_id":instance,"detached":True})
        return {"roots":roots,"bootstrap_mode":"bootstrap-local-unsafe-v1" if self.bootstrap_open else "CLOSED","risk_acceptance_id":self.bootstrap_id}
    def status(self, *, as_json:bool=False):
        roots=[];healthy=True
        for root in ("A","B"):
            entry=self.processes.get(root)
            if not entry: roots.append({"root":root,"state":"STOPPED","fenced":False});healthy=False;continue
            process,instance=entry;alive=process.poll() is None and self.pid_probe(process.pid)
            if not alive:self.queue.fence_root_instance(root);roots.append({"root":root,"state":"STALE","fenced":True});healthy=False
            else:roots.append({"root":root,"state":"RUNNING","fenced":False,"pid":process.pid,"instance_id":instance})
        return {"healthy":healthy,"roots":roots,"bootstrap_mode":"bootstrap-local-unsafe-v1" if self.bootstrap_open else "CLOSED","evidence_level":"bootstrap_unverified" if self.bootstrap_open else "local_only","warning":"bootstrap local-only unverified" if self.bootstrap_open else ""}
    def submit(self, *, alias:str, ticket:str, objective_file:Path):
        if not self.accepting_submissions: raise SupervisorError("draining")
        if alias not in {"codex1","codex2","agy1","agy2"}: raise SupervisorError("unknown alias")
        objective=Path(objective_file).read_text(encoding="utf-8");root="A" if alias.startswith("codex") else "B";request_id=f"{ticket}-{uuid.uuid4().hex[:12]}"
        return self.queue.submit(request_id=request_id,idempotency_key=request_id,payload={"objective":objective},root=root,alias=alias,work_mode="read_only",attempt=1,retry_budget=0)
    def wait(self, *, request_id:str, timeout:float):
        end=time.monotonic()+timeout
        while time.monotonic()<=end:
            result=self.queue.get_result(request_id)
            if result:return {"request_id":request_id,"status":result.get("status"),"result":result}
            time.sleep(.01)
        raise SupervisorError("wait timeout")
    def drain(self):self.accepting_submissions=False;return {"accepting_submissions":False}
    def stop(self, *, drain:bool=False):
        if drain:self.drain()
        for p,_ in self.processes.values(): p.terminate()
        self.processes={};self.bootstrap_open=False;self.bootstrap_id=None
        return {"running":False}
    def seal_bootstrap(self):self.bootstrap_sealed=True;self.bootstrap_open=False;return {"sealed":True}

    @staticmethod
    def _fixture_process_factory(**kwargs):
        """A process-shaped local fixture; it never resolves or runs a provider."""
        return _FixtureProcess()

    def smoke_all(self) -> dict[str, object]:
        """Exercise durable local control flow with fixtures, never a provider adapter."""
        self.init()
        self.process_factory = self._fixture_process_factory
        self.pid_probe = lambda pid: any(
            process.pid == pid and process.poll() is None
            for process, _instance in self.processes.values()
        )
        started = self.start()
        roots = {item["root"]: item for item in started["roots"]}
        if set(roots) != {"A", "B"} or roots["A"]["pid"] == roots["B"]["pid"]:
            raise SupervisorError("local smoke root isolation failed")
        with tempfile.TemporaryDirectory(dir=self.state_dir) as fixture_dir:
            objective = Path(fixture_dir) / "objective.txt"
            objective.write_text("local fixture verification", encoding="utf-8")
            codex = self.submit(alias="codex1", ticket="LOCAL-SMOKE-A", objective_file=objective)
            agy = self.submit(alias="agy1", ticket="LOCAL-SMOKE-B", objective_file=objective)
            if codex.root != "A" or agy.root != "B":
                raise SupervisorError("local smoke queue isolation failed")
            for job in (codex, agy):
                self.queue.record_fixture_result(
                    job.request_id,
                    result={"status": "DONE", "findings": ["local_fixture"]},
                    receipt={"protocol_version": 2, "fixture": True},
                )
            completed = [self.wait(request_id=job.request_id, timeout=1) for job in (codex, agy)]
        drained = self.drain()
        stopped = self.stop(drain=True)
        if any(item["status"] != "DONE" for item in completed) or drained["accepting_submissions"] or stopped["running"]:
            raise SupervisorError("local smoke lifecycle failed")
        return {
            "status": "DONE",
            "mode": "local_fixture_only",
            "provider_invocation": False,
            "roots": ["A", "B"],
            "submitted": 2,
            "completed": 2,
            "drained": True,
            "stopped": True,
        }

def build_parser():
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest="command")
    doctor=sub.add_parser("doctor");doctor.add_argument("--repair-home-permissions",action="store_true")
    sub.add_parser("init");start=sub.add_parser("start");start.add_argument("--bootstrap-local-unsafe",action="store_true");start.add_argument("--accept-risk")
    for name in ("submit","status","wait","smoke-all","seal-bootstrap","drain"):sub.add_parser(name)
    stop=sub.add_parser("stop");stop.add_argument("--drain",action="store_true");return parser


def main(argv: list[str] | None = None) -> int:
    """Expose the bounded local supervisor command surface without activation."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "smoke-all":
        try:
            with tempfile.TemporaryDirectory(prefix="horoconsultant-local-smoke-") as state_root:
                result = RootSupervisor(state_dir=Path(state_root) / "state").smoke_all()
            print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        except (OSError, SupervisorError) as exc:
            print(json.dumps({"status": "FAILED", "mode": "local_fixture_only", "error": type(exc).__name__}))
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
