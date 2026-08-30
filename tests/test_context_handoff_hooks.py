from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "scripts" / "context_handoff.py"
FIXTURES = ROOT / "tests" / "fixtures" / "context_handoff"

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


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _fixture(runtime: str, name: str) -> dict[str, Any]:
    return _load_json(FIXTURES / runtime / name)


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
) -> subprocess.CompletedProcess[str]:
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


def _assert_native_mapping(output: dict[str, Any], case: dict[str, Any]) -> None:
    assert set(output) == set(case["expected_output_keys"]), case["id"]
    for key, expected in case.get("expected", {}).items():
        assert output[key] == expected, case["id"]
    for field, max_bytes in case.get("max_field_bytes", {}).items():
        assert len(output[field].encode("utf-8")) <= max_bytes, case["id"]
    joined = "\n".join(str(value) for value in output.values()).casefold()
    for marker in case.get("contains", []):
        assert marker.casefold() in joined, case["id"]


def _run_wrapper(
    wrapper: Path,
    payload: dict[str, Any],
) -> subprocess.CompletedProcess[str]:
    safe_env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONUTF8": "1",
    }
    return subprocess.run(
        ["bash", str(wrapper)],
        cwd=ROOT,
        input=json.dumps(payload, separators=(",", ":")),
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
        env=safe_env,
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


def test_codex_hooks_config_matches_exact_events_and_denies_untrusted_projects() -> None:
    expected = _fixture("codex", "hooks_config.json")
    assert CODEX_CONFIG.is_file(), "CODEX_CONTEXT_HANDOFF_HOOKS_MISSING"
    actual = _load_json(CODEX_CONFIG)

    assert actual == expected
    assert set(actual["hooks"]) == {
        "SessionStart",
        "PreCompact",
        "PostCompact",
        "Stop",
        "SessionEnd",
    }
    assert actual["trusted_project_only"] is True
    assert actual["untrusted_project_behavior"] == "deny"

    serialized = json.dumps(actual, sort_keys=True).casefold()
    for prohibited in ("bypass", "skip-trust", "allow-untrusted", "--force", "|| true"):
        assert prohibited not in serialized
    for event, registrations in actual["hooks"].items():
        assert len(registrations) == 1
        registration = registrations[0]
        assert registration["type"] == "command"
        assert registration["timeout"] == 10
        assert registration["command"].endswith(f"--event {event} --native")
        assert "scripts/context_handoff.py hook --runtime codex" in registration["command"]


def test_codex_native_mappings_cover_session_compaction_stop_and_end(tmp_path: Path) -> None:
    fixture = _fixture("codex", "native_mappings.json")
    assert fixture["schema_version"] == "context-handoff-native-fixtures-v1"
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
        "session-end-warning",
    }

    handoff = tmp_path / "HANDOFF.md"
    _create_handoff(handoff)
    for case in cases:
        result = _native_codex(case["event"], case["input"], handoff)
        assert result.returncode == 0, f"{case['id']}: {result.stderr}"
        output = json.loads(result.stdout)
        assert isinstance(output, dict), case["id"]
        _assert_native_mapping(output, case)


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
    payload = {
        field: bad_value,
        "usage": {},
        "last_notified_level": "NORMAL",
        "lanes": [],
    }

    result = _native_codex(event, payload, handoff)

    assert result.returncode == 2
    assert result.stdout == ""
    assert "HOOK_EVENT_INPUT_INVALID" in result.stderr


def test_claude_and_agy_hook_registrations_remain_byte_semantically_unchanged() -> None:
    assert _load_json(CLAUDE_SETTINGS) == _fixture("claude", "registrations.json")
    assert _load_json(AGY_SETTINGS) == _fixture("agy", "registrations.json")


@pytest.mark.parametrize(
    ("runtime", "wrapper", "fixture_name"),
    [
        ("claude", CLAUDE_WRAPPER, "stop_mappings.json"),
        ("agy", AGY_WRAPPER, "stop_mappings.json"),
    ],
)
def test_stop_adapters_match_native_fixtures_and_prevent_recursion(
    runtime: str,
    wrapper: Path,
    fixture_name: str,
) -> None:
    fixture = _fixture(runtime, fixture_name)
    assert fixture["schema_version"] == "context-handoff-native-fixtures-v1"
    for case in fixture["cases"]:
        result = _run_wrapper(wrapper, case["input"])
        output = _parse_json_output(result, case["id"])
        _assert_native_mapping(output, case)


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
    expected = f"scripts/context_handoff.py hook --runtime {runtime} --event Stop --native"
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
        "/reset",
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


def test_sync_checks_cover_context_handoff_and_are_read_only() -> None:
    parity_source = SYNC_PARITY.read_text(encoding="utf-8")
    ecosystem_source = SYNC_ECOSYSTEM.read_text(encoding="utf-8")
    combined = parity_source + ecosystem_source
    for marker in (
        "context_handoff_v1.json",
        "context_handoff.py",
        "anti-cognitive-decay",
        "20-context-handoff.md",
        ".codex/hooks.json",
    ):
        assert marker in combined, f"sync acceptance missing {marker}"

    before = _status_bytes()
    commands = (
        [sys.executable, str(SYNC_PARITY), "--check"],
        [sys.executable, str(SYNC_ECOSYSTEM), "--check"],
    )
    for command in commands:
        result = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        assert result.returncode == 0, result.stdout + result.stderr
    assert _status_bytes() == before


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
