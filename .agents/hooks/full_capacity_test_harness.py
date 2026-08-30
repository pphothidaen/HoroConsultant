#!/usr/bin/env python3
"""Unregistered subprocess harness for temp-ledger capacity guard tests only."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

ROOT_DIR = Path(__file__).resolve().parents[2]
GUARD_PATH = ROOT_DIR / ".agents" / "hooks" / "full_capacity_guard.py"


def _load_guard() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "horo_full_capacity_guard_test_target", GUARD_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("capacity guard unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _emit(violation: str) -> None:
    print(
        json.dumps(
            {
                "decision": "deny",
                "reason": f"[BLOCKED] FULL_CAPACITY_GUARD: {violation}",
            },
            ensure_ascii=True,
        )
    )


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in {"audit", "evaluate"}:
        _emit("CAPACITY_TEST_HARNESS_ARGUMENT_INVALID")
        return 2
    state_directory = Path(sys.argv[2])
    try:
        guard = _load_guard()
        if sys.argv[1] == "audit":
            result = guard._offline_full_audit(
                guard._load_config(), internal_test_directory=state_directory
            )
            print(json.dumps({"status": "[OK]", **result}, ensure_ascii=True))
            return 0
        event = guard._read_event()
        violation = guard._evaluate_event_for_test(event, state_directory)
    except Exception as exc:  # noqa: BLE001 - test harness must fail closed
        code = getattr(exc, "code", "CAPACITY_TEST_HARNESS_FAILURE")
        _emit(str(code))
        return 2
    if violation is None:
        print(json.dumps({}))
        return 0
    _emit(violation)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
