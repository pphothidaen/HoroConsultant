from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "scripts" / "context_handoff.py"
FIXTURES = ROOT / "tests" / "fixtures" / "context_handoff"
CODEX_HOOKS_FIXTURE = FIXTURES / "codex" / "hooks_config.json"
CODEX_NATIVE_FIXTURE = FIXTURES / "codex" / "native_mappings.json"
CLAUDE_STOP_FIXTURE = FIXTURES / "claude" / "stop_mappings.json"
AGY_STOP_FIXTURE = FIXTURES / "agy" / "stop_mappings.json"

CODEX_CONFIG = ROOT / ".codex" / "hooks.json"
CLAUDE_SETTINGS = ROOT / ".claude" / "settings.json"
AGY_SETTINGS = ROOT / ".agy" / "hooks.json"
CLAUDE_WRAPPER = ROOT / ".claude" / "hooks" / "stop-monitor.sh"
AGY_WRAPPER = ROOT / ".agy" / "hooks" / "stop-monitor.sh"

CANONICAL_SKILL = ROOT / ".agents" / "skills" / "anti-cognitive-decay" / "SKILL.md"
CANONICAL_RULE = ROOT / ".agents" / "rules" / "20-context-handoff.md"
CATALOG = ROOT / ".agents" / "AGENTS.md"
SYNC_PARITY = ROOT / "scripts" / "sync_claude_agy_parity.py"
SYNC_ECOSYSTEM = ROOT / "scripts" / "sync_ai_agent_ecosystem.py"

GENERATED_SKILLS = (
    ROOT / ".antigravity" / "skills" / "anti-cognitive-decay" / "SKILL.md",
    ROOT / ".claude" / "skills" / "anti-cognitive-decay" / "SKILL.md",
    ROOT / ".agy" / "skills" / "anti-cognitive-decay" / "SKILL.md",
)

CANONICAL_FIXTURES = (
    CODEX_HOOKS_FIXTURE,
    CODEX_NATIVE_FIXTURE,
    CLAUDE_STOP_FIXTURE,
    AGY_STOP_FIXTURE,
)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _fixture(runtime: str, name: str) -> dict[str, Any]:
    return _load_json(FIXTURES / runtime / name)


def _codex_handler(event: str) -> dict[str, Any]:
    config = _load_json(CODEX_HOOKS_FIXTURE)
    groups = config["hooks"][event]
    assert len(groups) == 1
    handlers = groups[0]["hooks"]
    assert len(handlers) == 1
    handler = handlers[0]
    assert isinstance(handler, dict)
    return handler


def _minimal_snapshot() -> dict[str, Any]:
    return {
        "schema_version": "HandoffSnapshotV1",
        "created_at": "2026-08-30T00:00:00Z",
        "runtime": "codex",
        "ticket_id": "CTX-010-RED",
        "reason": "manual",
        "objective": "Preserve bounded cross-runtime context without authority drift",
        "summary": "A canonical derived capsule used by native hook mapping fixtures.",
        "next_action": "Read PROJECT_TASKS.md and plans/plan.md before resuming.",
        "authority": {
            "current_state": "PROJECT_TASKS.md",
            "implementation_plan": "plans/plan.md",
            "derived_handoff": "HANDOFF.md",
        },
        "lanes": [],
        "dirty_paths": ["tests/test_context_handoff_hooks.py"],
        "risks": ["Never infer provider proof from a local hook."],
        "decisions": ["Only an operator may compact, clear, or reset."],
        "clear_ready": True,
    }


def _create_handoff(path: Path) -> None:
    assert ENTRYPOINT.is_file(), "CONTEXT_HANDOFF_ENTRYPOINT_MISSING"
    result = subprocess.run(
        [sys.executable, str(ENTRYPOINT), "snapshot", "--output", str(path)],
        cwd=ROOT,
        input=json.dumps(_minimal_snapshot()),
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr


def _native_codex(
    event: str,
    payload: dict[str, Any],
    handoff: Path,
    *,
    normalized_state: dict[str, Any] | None = None,
    timeout: float = 5.0,
) -> subprocess.CompletedProcess[str]:
    state = normalized_state or {
        "usage": {},
        "last_notified_level": "NORMAL",
        "lanes": [],
    }
    return subprocess.run(
        [
            sys.executable,
            str(ENTRYPOINT),
            "hook",
            "--runtime",
            "codex",
            "--event",
            event,
            "--native",
            "--state-json",
            json.dumps(state, separators=(",", ":")),
            "--handoff",
            str(handoff),
        ],
        cwd=ROOT,
        input=json.dumps(payload, separators=(",", ":")),
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def _assert_native_mapping(output: dict[str, Any], case: dict[str, Any]) -> None:
    assert set(output) == set(case["expected_output_keys"]), case["id"]
    for key, expected in case.get("expected", {}).items():
        assert output[key] == expected, case["id"]
    if "expected_hook_event_name" in case:
        hook_output = output["hookSpecificOutput"]
        assert set(hook_output) == {"hookEventName", "additionalContext"}, case["id"]
        assert hook_output["hookEventName"] == case["expected_hook_event_name"]
        additional_context = hook_output["additionalContext"]
        assert isinstance(additional_context, str), case["id"]
        assert len(additional_context.encode("utf-8")) <= case[
            "max_additional_context_bytes"
        ]
    for field, max_bytes in case.get("max_field_bytes", {}).items():
        assert len(output[field].encode("utf-8")) <= max_bytes, case["id"]
    joined = json.dumps(output, ensure_ascii=False, sort_keys=True).casefold()
    for marker in case.get("contains", []):
        assert marker.casefold() in joined, case["id"]


def _run_wrapper(
    wrapper: Path,
    payload: dict[str, Any],
    *,
    cwd: Path = ROOT,
) -> subprocess.CompletedProcess[str]:
    safe_env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONUTF8": "1",
    }
    return subprocess.run(
        ["bash", str(wrapper)],
        cwd=cwd,
        input=json.dumps(payload, separators=(",", ":")),
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
        env=safe_env,
    )


def _native_runtime(
    runtime: str,
    wire_event: str,
    normalized_event: str,
    payload: dict[str, Any],
    normalized_state: dict[str, Any],
    handoff: Path,
) -> subprocess.CompletedProcess[str]:
    assert ENTRYPOINT.is_file(), "CONTEXT_HANDOFF_ENTRYPOINT_MISSING"
    return subprocess.run(
        [
            sys.executable,
            str(ENTRYPOINT),
            "hook",
            "--runtime",
            runtime,
            "--event",
            normalized_event,
            "--wire-event",
            wire_event,
            "--native",
            "--state-json",
            json.dumps(normalized_state, separators=(",", ":")),
            "--handoff",
            str(handoff),
        ],
        cwd=ROOT,
        input=json.dumps(payload, separators=(",", ":")),
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )


def _parse_json_output(result: subprocess.CompletedProcess[str], case_id: str) -> dict[str, Any]:
    assert result.returncode == 0, f"{case_id}: {result.stderr}"
    value = json.loads(result.stdout)
    assert isinstance(value, dict), case_id
    return value


def _status_bytes() -> bytes:
    return subprocess.run(
        ["git", "status", "--porcelain=v1", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout


def test_codex_hooks_config_uses_native_three_level_shape_without_trust_fields() -> None:
    expected = _load_json(CODEX_HOOKS_FIXTURE)
    assert CODEX_CONFIG.is_file(), "CODEX_CONTEXT_HANDOFF_HOOKS_MISSING"
    actual = _load_json(CODEX_CONFIG)

    assert actual == expected
    assert set(actual) == {"description", "hooks"}
    assert set(actual["hooks"]) == {
        "SessionStart",
        "PreCompact",
        "PostCompact",
        "Stop",
        "SessionEnd",
    }
    expected_matchers = {
        "SessionStart": "startup|resume|clear|compact",
        "PreCompact": "manual|auto",
        "PostCompact": "manual|auto",
        "Stop": None,
        "SessionEnd": "other",
    }
    observed_keys: set[str] = set()
    for event, groups in actual["hooks"].items():
        assert len(groups) == 1
        group = groups[0]
        assert set(group) == ({"hooks"} if expected_matchers[event] is None else {"matcher", "hooks"})
        if expected_matchers[event] is not None:
            assert group["matcher"] == expected_matchers[event]
        assert len(group["hooks"]) == 1
        handler = group["hooks"][0]
        assert set(handler) == {"type", "command", "timeout"}
        observed_keys.update(handler)
        assert handler["type"] == "command"
        expected_command = (
            'python3 "$(git rev-parse --show-toplevel)/scripts/context_handoff.py" '
            f"hook --runtime codex --event {event} --native"
        )
        assert handler["command"] == expected_command
        assert isinstance(handler["timeout"], int)
        assert 0 < handler["timeout"] <= (3 if event == "SessionEnd" else 10)

    serialized_keys = " ".join(sorted(set(actual) | set(actual["hooks"]) | observed_keys))
    for invented_trust_key in (
        "trusted_project_only",
        "untrusted_project_behavior",
        "trusted",
        "trust_hash",
        "managed",
        "bypass",
    ):
        assert invented_trust_key not in serialized_keys.casefold()


def test_codex_registered_command_resolves_git_root_from_nested_cwd() -> None:
    assert ENTRYPOINT.is_file(), "CONTEXT_HANDOFF_ENTRYPOINT_MISSING"
    fixture = _load_json(CODEX_NATIVE_FIXTURE)
    case = next(case for case in fixture["cases"] if case["id"] == "stop-recursion-safe")
    nested_cwd = ROOT / "tests" / "fixtures" / "context_handoff" / "codex"
    before = _status_bytes()
    result = subprocess.run(
        ["bash", "-c", _codex_handler("Stop")["command"]],
        cwd=nested_cwd,
        input=json.dumps(case["input"], separators=(",", ":")),
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
        env={
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "PYTHONUTF8": "1",
        },
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {}
    assert _status_bytes() == before


def test_repository_only_acknowledges_native_dangerous_bypass_and_never_uses_it() -> None:
    dangerous_flag = "--dangerously-" + "bypass-hook-trust"
    tracked = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout.decode("utf-8").split("\0")
    acknowledgements: list[tuple[str, str]] = []
    for relative_path in tracked:
        if not relative_path:
            continue
        path = ROOT / relative_path
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if dangerous_flag in text:
            for line in text.splitlines():
                if dangerous_flag in line:
                    acknowledgements.append((relative_path, line))
                    assert "may expose" in line.casefold(), relative_path
            normalized = text.casefold()
            assert "never invoke or recommend" in normalized, relative_path
            assert "managed hooks" in normalized and "outside" in normalized, relative_path

        if not relative_path.startswith("tests/"):
            compacted = re.sub(r"[\s'\"`+\\]", "", text)
            if dangerous_flag in compacted:
                assert dangerous_flag in text, f"assembled bypass flag in {relative_path}"

    assert acknowledgements, "native CLI bypass boundary must be acknowledged honestly"


def test_codex_native_mappings_cover_session_compaction_stop_and_end(tmp_path: Path) -> None:
    fixture = _load_json(CODEX_NATIVE_FIXTURE)
    assert fixture["schema_version"] == "context-handoff-native-fixtures-v3"
    cases = fixture["cases"]
    assert {case["id"] for case in cases} == {
        "session-start-startup",
        "session-start-resume",
        "session-start-clear",
        "session-start-compact",
        "pre-compact-manual",
        "pre-compact-auto",
        "post-compact-manual",
        "post-compact-auto",
        "stop-warning",
        "stop-recursion-safe",
        "session-end-snapshot",
    }

    exact_wire_keys = {
        "SessionStart": {
            "session_id",
            "transcript_path",
            "cwd",
            "hook_event_name",
            "model",
            "permission_mode",
            "source",
        },
        "PreCompact": {
            "session_id",
            "transcript_path",
            "cwd",
            "hook_event_name",
            "model",
            "turn_id",
            "trigger",
        },
        "PostCompact": {
            "session_id",
            "transcript_path",
            "cwd",
            "hook_event_name",
            "model",
            "turn_id",
            "trigger",
        },
        "Stop": {
            "session_id",
            "transcript_path",
            "cwd",
            "hook_event_name",
            "model",
            "permission_mode",
            "turn_id",
            "stop_hook_active",
            "last_assistant_message",
        },
        "SessionEnd": {
            "session_id",
            "transcript_path",
            "cwd",
            "hook_event_name",
            "reason",
        },
    }

    handoff = tmp_path / "HANDOFF.md"
    _create_handoff(handoff)
    for case in cases:
        assert case["input"]["hook_event_name"] == case["event"]
        assert set(case["input"]) == exact_wire_keys[case["event"]], case["id"]
        assert set(case["normalized_state"]) == {
            "usage",
            "last_notified_level",
            "lanes",
        }
        assert {"usage", "last_notified_level", "lanes"}.isdisjoint(case["input"])
        if case["event"] == "Stop":
            assert "stop_hook_active" in case["input"]
            assert "hook_active" not in case["input"]
        if case["event"] == "SessionEnd":
            continue
        result = _native_codex(
            case["event"],
            case["input"],
            handoff,
            normalized_state=case["normalized_state"],
        )
        assert result.returncode == 0, f"{case['id']}: {result.stderr}"
        output = json.loads(result.stdout)
        assert isinstance(output, dict), case["id"]
        _assert_native_mapping(output, case)
        persisted = handoff.read_text(encoding="utf-8")
        emitted = result.stdout + result.stderr + persisted
        for private_field in (
            "session_id",
            "transcript_path",
            "turn_id",
            "last_assistant_message",
        ):
            value = case["input"].get(private_field)
            if isinstance(value, str):
                assert value not in emitted, f"{case['id']} leaked {private_field}"


def test_codex_session_end_is_empty_nonsteering_and_bounded_by_three_second_timeout(
    tmp_path: Path,
) -> None:
    fixture = _load_json(CODEX_NATIVE_FIXTURE)
    case = next(case for case in fixture["cases"] if case["event"] == "SessionEnd")
    handoff = tmp_path / "HANDOFF.md"
    state = dict(case["normalized_state"])
    state["snapshot"] = _minimal_snapshot()

    started = time.monotonic()
    result = _native_codex(
        "SessionEnd",
        case["input"],
        handoff,
        normalized_state=state,
        timeout=3.0,
    )
    elapsed = time.monotonic() - started

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert elapsed < 3.25
    raw = handoff.read_bytes()
    assert 0 < len(raw) <= 16 * 1024
    assert raw.count(b"<!-- HANDOFF-SNAPSHOT-V1:START -->") == 1
    assert raw.count(b"<!-- HANDOFF-SNAPSHOT-V1:END -->") == 1
    combined = result.stdout.encode() + result.stderr.encode() + raw
    for field in ("session_id", "transcript_path"):
        assert case["input"][field].encode() not in combined
    for steering in (b"systemMessage", b"continue", b"decision", b"stopReason"):
        assert steering not in result.stdout.encode()


def test_codex_hook_outputs_only_request_operator_actions() -> None:
    fixture = _load_json(CODEX_NATIVE_FIXTURE)
    for case in fixture["cases"]:
        expected_keys = set(case["expected_output_keys"])
        assert "decision" not in expected_keys, case["id"]
        assert "continue" not in expected_keys, case["id"]
        output_contract = {
            key: case[key]
            for key in (
                "expected_output_kind",
                "expected_output_keys",
                "expected",
                "expected_hook_event_name",
                "contains",
            )
            if key in case
        }
        serialized = json.dumps(output_contract, sort_keys=True).casefold()
        for automatic_action in (
            '"continue": false',
            '"decision": "block"',
            "/compact",
            "/clear",
            "/reset",
            "send-keys",
            "write_stdin",
        ):
            assert automatic_action not in serialized, case["id"]


@pytest.mark.parametrize(
    ("event", "field", "bad_value"),
    [
        ("SessionStart", "source", "unknown"),
        ("PreCompact", "trigger", "scheduled"),
        ("PostCompact", "trigger", "scheduled"),
    ],
)
def test_codex_native_mapping_rejects_unknown_start_or_compact_signals(
    tmp_path: Path,
    event: str,
    field: str,
    bad_value: str,
) -> None:
    handoff = tmp_path / "HANDOFF.md"
    _create_handoff(handoff)
    fixture = _load_json(CODEX_NATIVE_FIXTURE)
    payload = dict(next(case for case in fixture["cases"] if case["event"] == event)["input"])
    payload[field] = bad_value

    result = _native_codex(event, payload, handoff)

    assert result.returncode == 2
    assert result.stdout == ""
    assert "HOOK_EVENT_INPUT_INVALID" in result.stderr


def test_claude_and_agy_registrations_use_root_stable_wrapper_commands() -> None:
    claude = _load_json(CLAUDE_SETTINGS)
    claude_stop = claude["hooks"]["Stop"]
    assert len(claude_stop) == 1 and len(claude_stop[0]["hooks"]) == 1
    claude_handler = claude_stop[0]["hooks"][0]
    assert claude_handler == {
        "type": "command",
        "command": 'bash "${CLAUDE_PROJECT_DIR}/.claude/hooks/stop-monitor.sh"',
        "timeout": 10,
    }

    agy = _load_json(AGY_SETTINGS)
    agy_groups = agy["hooks"]["AfterAgent"]
    assert agy_groups == [
        {
            "matcher": "*",
            "sequential": True,
            "hooks": [
                {
                    "name": "context-handoff-stop-normalizer",
                    "type": "command",
                    "command": 'bash "$(git rev-parse --show-toplevel)/.agy/hooks/stop-monitor.sh"',
                    "timeout": 3000,
                }
            ],
        }
    ]


@pytest.mark.parametrize(
    ("runtime", "wrapper", "fixture_path"),
    [
        ("claude", CLAUDE_WRAPPER, CLAUDE_STOP_FIXTURE),
        ("agy", AGY_WRAPPER, AGY_STOP_FIXTURE),
    ],
)
def test_stop_adapters_match_native_fixtures_and_prevent_recursion(
    runtime: str,
    wrapper: Path,
    fixture_path: Path,
) -> None:
    fixture = _load_json(fixture_path)
    assert fixture["schema_version"] == "context-handoff-native-fixtures-v3"
    assert fixture["wire_event"] in {"Stop", "AfterAgent"}
    normalized_event = fixture.get("normalized_event", "Stop")
    if runtime == "claude":
        assert fixture["wire_event"] == "Stop"
        exact_wire_keys = {
            "session_id",
            "transcript_path",
            "cwd",
            "permission_mode",
            "hook_event_name",
            "stop_hook_active",
            "last_assistant_message",
        }
    else:
        assert fixture["wire_event"] == "AfterAgent"
        assert fixture["normalized_event"] == "Stop"
        exact_wire_keys = {
            "session_id",
            "transcript_path",
            "cwd",
            "hook_event_name",
            "timestamp",
            "prompt",
            "prompt_response",
            "stop_hook_active",
        }
    handoff = FIXTURES / runtime / "nonpersistent-HANDOFF.md"
    for case in fixture["cases"]:
        assert set(case["input"]) == exact_wire_keys
        assert case["input"]["hook_event_name"] == fixture["wire_event"]
        assert "stop_hook_active" in case["input"]
        assert "hook_active" not in case["input"]
        assert {"usage", "last_notified_level", "lanes"}.isdisjoint(case["input"])
        assert set(case["normalized_state"]) == {
            "usage",
            "last_notified_level",
            "lanes",
        }
        result = _native_runtime(
            runtime,
            fixture["wire_event"],
            normalized_event,
            case["input"],
            case["normalized_state"],
            handoff,
        )
        output = _parse_json_output(result, case["id"])
        _assert_native_mapping(output, case)
        emitted = result.stdout + result.stderr
        for private_field in (
            "session_id",
            "transcript_path",
            "last_assistant_message",
            "prompt",
            "prompt_response",
        ):
            value = case["input"].get(private_field)
            if isinstance(value, str):
                assert value not in emitted, f"{case['id']} leaked {private_field}"
    assert not handoff.exists(), "Stop adapters must not persist native identifiers"


@pytest.mark.parametrize(
    ("runtime", "wrapper"),
    [("claude", CLAUDE_WRAPPER), ("agy", AGY_WRAPPER)],
)
def test_stop_wrappers_are_thin_fail_closed_shared_engine_adapters(
    runtime: str,
    wrapper: Path,
) -> None:
    assert wrapper.is_file()
    assert os.access(wrapper, os.X_OK)
    text = wrapper.read_text(encoding="utf-8")
    command_lines = "\n".join(
        line.split("#", 1)[0].strip()
        for line in text.splitlines()
        if line.split("#", 1)[0].strip()
    )
    expected = (
        'python3 "$(git rev-parse --show-toplevel)/scripts/context_handoff.py" '
        f"hook --runtime {runtime} --event Stop"
        + (" --wire-event AfterAgent" if runtime == "agy" else "")
        + " --native"
    )
    assert expected in command_lines
    assert "set -euo pipefail" in command_lines

    for duplicated_or_unsafe in (
        "grep ",
        "du ",
        "cat ",
        "transcriptPath",
        "CONTEXT_USAGE_PERCENT",
        "|| true",
        "eval ",
        "/clear",
        "/compact",
        "/reset",
        "send-keys",
        "write_stdin",
    ):
        assert duplicated_or_unsafe not in command_lines


def test_skill_rule_catalog_and_generated_mirrors_freeze_one_operator_only_policy() -> None:
    for path in (CANONICAL_SKILL, CANONICAL_RULE, CATALOG):
        assert path.is_file(), f"missing context handoff governance: {path.relative_to(ROOT)}"

    skill = CANONICAL_SKILL.read_text(encoding="utf-8")
    rule = CANONICAL_RULE.read_text(encoding="utf-8")
    catalog = CATALOG.read_text(encoding="utf-8")
    assert re.search(r"^name:\s*anti-cognitive-decay\s*$", skill, re.MULTILINE)

    required_markers = (
        "HandoffSnapshotV1",
        "PROJECT_TASKS.md",
        "plans/plan.md",
        "HANDOFF.md",
        "UNKNOWN",
        "clear_ready",
        "64 KiB",
        "16 KiB",
        "400 KiB",
        "450 KiB",
        "900 KiB",
        "raw transcript",
        "operator",
        "non-managed",
        "user review",
        "exact current hash",
        "managed hooks",
        "outside",
    )
    for marker in required_markers:
        assert marker.casefold() in skill.casefold(), f"skill missing {marker}"
        assert marker.casefold() in rule.casefold(), f"rule missing {marker}"
    for threshold in ("40%", "45%", "80%"):
        assert threshold in skill
        assert threshold in rule
    assert "anti-cognitive-decay" in catalog
    assert "20-context-handoff.md" in catalog

    canonical_bytes = CANONICAL_SKILL.read_bytes()
    for mirror in GENERATED_SKILLS:
        assert mirror.is_file(), f"missing generated skill mirror: {mirror.relative_to(ROOT)}"
        assert mirror.read_bytes() == canonical_bytes


def _copy_sync_test_repo(destination: Path) -> Path:
    def ignore_heavy(directory: str, names: list[str]) -> set[str]:
        ignored = {
            name
            for name in names
            if name in {".git", ".pytest_cache", "__pycache__", "node_modules", ".venv"}
        }
        if Path(directory).resolve() == ROOT:
            ignored.update(
                name
                for name in names
                if name in {"project", "public", "rust_core", "TDD-HORO-v3.0"}
            )
        return ignored

    replica = destination / "repo"
    shutil.copytree(ROOT, replica, ignore=ignore_heavy, copy_function=shutil.copy2)
    return replica


def test_sync_is_exact_deterministic_and_drift_negative_in_temp_repo(
    tmp_path: Path,
) -> None:
    assert CANONICAL_SKILL.is_file(), "CANONICAL_CONTEXT_HANDOFF_SKILL_MISSING"
    replica = _copy_sync_test_repo(tmp_path)
    canonical = replica / ".agents" / "skills" / "anti-cognitive-decay" / "SKILL.md"
    canonical_bytes = (
        b"---\n"
        b"name: anti-cognitive-decay\n"
        b"description: Canonical deterministic context handoff sync canary.\n"
        b"---\n\n"
        b"# Canonical context handoff sync canary\n\n"
        b"Generated mirrors must equal these bytes exactly.\n"
        b"\n## Gotchas\n\n"
        b"- Never select a generated mirror as the canonical source.\n"
    )
    canonical.write_bytes(canonical_bytes)
    replica_mirrors = tuple(replica / path.relative_to(ROOT) for path in GENERATED_SKILLS)
    for index, mirror in enumerate(replica_mirrors):
        mirror.parent.mkdir(parents=True, exist_ok=True)
        mirror.write_bytes(f"stale-generated-{index}\n".encode("ascii"))

    sync_command = [
        sys.executable,
        str(replica / "scripts" / "sync_ai_agent_ecosystem.py"),
        "--sync",
    ]
    first = subprocess.run(
        sync_command,
        cwd=replica,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert first.returncode == 0, first.stdout + first.stderr
    assert canonical.read_bytes() == canonical_bytes
    assert [path.read_bytes() for path in replica_mirrors] == [canonical_bytes] * 3
    first_generated = {path.relative_to(replica): path.read_bytes() for path in replica_mirrors}

    second = subprocess.run(
        sync_command,
        cwd=replica,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert second.returncode == 0, second.stdout + second.stderr
    assert canonical.read_bytes() == canonical_bytes
    assert {
        path.relative_to(replica): path.read_bytes() for path in replica_mirrors
    } == first_generated

    for script in ("sync_claude_agy_parity.py", "sync_ai_agent_ecosystem.py"):
        check_result = subprocess.run(
            [sys.executable, str(replica / "scripts" / script), "--check"],
            cwd=replica,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        assert check_result.returncode == 0, check_result.stdout + check_result.stderr

    replica_mirrors[0].write_bytes(canonical_bytes + b"drift\n")
    drift_check = subprocess.run(
        [
            sys.executable,
            str(replica / "scripts" / "sync_ai_agent_ecosystem.py"),
            "--check",
        ],
        cwd=replica,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert drift_check.returncode != 0
    assert "anti-cognitive-decay" in (drift_check.stdout + drift_check.stderr).casefold()
    assert canonical.read_bytes() == canonical_bytes


def test_fixture_files_are_closed_json_and_contain_no_absolute_home_or_secret_material() -> None:
    fixture_paths = sorted(FIXTURES.glob("*/*.json"))
    assert {path.parent.name for path in fixture_paths} == {"codex", "claude", "agy"}
    assert len(fixture_paths) == 6
    for path in fixture_paths:
        raw = path.read_text(encoding="utf-8")
        value = json.loads(raw)
        assert isinstance(value, dict)
        assert not re.search(r"/(?:Users|home)/[^/\s]+", raw)
        assert "BEGIN PRIVATE KEY" not in raw
        assert "sk-" not in raw.casefold()
