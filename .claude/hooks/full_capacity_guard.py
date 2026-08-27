#!/usr/bin/env python3
"""Claude adapter for Stage A capacity validation, not interception proof."""

from __future__ import annotations

import importlib.util
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
AUTHORITATIVE_GUARD = ROOT_DIR / ".agents" / "hooks" / "full_capacity_guard.py"


class HookFailure(RuntimeError):
    """A hook adapter failure that must fail closed without a traceback."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise HookFailure("CAPACITY_PAYLOAD_REJECTED")
        result[key] = value
    return result


def _load_guard() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "horo_full_capacity_guard", AUTHORITATIVE_GUARD
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("full-capacity guard is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _read_event(limit: int) -> Mapping[str, Any]:
    raw = sys.stdin.buffer.read(limit + 1)
    if len(raw) > limit:
        raise HookFailure("CAPACITY_PAYLOAD_REJECTED")
    if not raw.strip():
        raise HookFailure("CAPACITY_PAYLOAD_REJECTED")
    try:
        value = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HookFailure("CAPACITY_PAYLOAD_REJECTED") from None
    if not isinstance(value, Mapping):
        raise HookFailure("CAPACITY_PAYLOAD_REJECTED")
    return value


def _emit_block(event: Mapping[str, Any] | None, violation: str) -> None:
    reason = f"[BLOCKED] FULL_CAPACITY_GUARD: {violation}"
    if event is not None and event.get("hook_event_name") == "PreToolUse":
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": reason,
                    }
                },
                ensure_ascii=True,
            )
        )
        return
    # PostToolUse uses the hook's top-level decision contract. In particular,
    # it does not accept the PreToolUse permissionDecision payload.
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=True))


def main() -> int:
    event: Mapping[str, Any] | None = None
    try:
        guard = _load_guard()
        event = _read_event(guard.MAX_INPUT_BYTES)
        violation = guard.evaluate_event(event)
    except HookFailure as exc:
        _emit_block(event, str(exc))
        return 2
    except (OSError, ValueError, ImportError, RuntimeError):
        _emit_block(event, "CAPACITY_GUARD_FAILURE")
        return 2
    except Exception:  # noqa: BLE001 - adapter failures must fail closed
        _emit_block(event, "CAPACITY_GUARD_FAILURE")
        return 2
    if violation is None:
        return 0
    _emit_block(event, violation)
    # Both pre- and post-tool failures must be process-visible. Output shape
    # alone is not a reliable hard-stop contract across hook hosts.
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
