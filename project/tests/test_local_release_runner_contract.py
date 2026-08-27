"""Executable fail-closed contracts for the frozen local release runners."""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
RUNNERS = {
    "auto": ROOT / "scripts" / "auto_deploy_all.sh",
    "hermes": ROOT / "scripts" / "hermes_sdlc_runner.sh",
    "agentic": ROOT / "scripts" / "agentic_pipeline.sh",
}
BASH = shutil.which("bash")
assert BASH is not None

CANONICAL_PUBLISH = [
    "scripts/publish_space_hf.py",
    "--space-id",
    "pphothidaen/horoconsultant-core-backend",
    "--sdk",
    "docker",
    "--dry-run",
]

FORBIDDEN_TOOLS = (
    "az",
    "curl",
    "docker",
    "doppler",
    "flyctl",
    "gh",
    "git",
    "nc",
    "npx",
    "ssh",
    "vercel",
    "wget",
)


def _write_executable(path: Path, text: str) -> None:
    path.write_text(text, encoding="ascii")
    path.chmod(0o755)


def _mock_command_path(tmp_path: Path) -> tuple[Path, Path]:
    """Create local command doubles so runner execution cannot reach providers."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True)
    command_log = tmp_path / "commands.log"

    _write_executable(
        bin_dir / "python3",
        """#!/bin/sh
record() {
    label="$1"
    shift
    printf '%s' "$label" >> "$COMMAND_LOG"
    for arg in "$@"; do
        printf '\t%s' "$arg" >> "$COMMAND_LOG"
    done
    printf '\n' >> "$COMMAND_LOG"
}

case "${1:-}" in
    *hermes_agy_router.py)
        record "CALL router" "$@"
        printf '%s\n' 'mock-model|medium|agy1|agy1,agy2|review|low|mock-fallback'
        ;;
    -m)
        record "CALL pytest" "$@"
        ;;
    -c)
        record "CALL python-inline"
        ;;
    scripts/run_button_regression.py)
        record "CALL button" "$@"
        ;;
    project/core/code_reviewer.py)
        record "CALL secret-scan" "$@"
        ;;
    scripts/publish_space_hf.py)
        record "CALL publisher" "$@"
        ;;
    *)
        record "CALL python-other" "$@"
        ;;
esac
""",
    )

    _write_executable(
        bin_dir / "tee",
        """#!/bin/sh
printf '%s\n' 'CALL tee' >> "$COMMAND_LOG"
while IFS= read -r line; do
    printf '%s\n' "$line"
done
""",
    )

    forbidden = """#!/bin/sh
tool="${0##*/}"
printf 'FORBIDDEN %s' "$tool" >> "$COMMAND_LOG"
for arg in "$@"; do
    printf '\t%s' "$arg" >> "$COMMAND_LOG"
done
printf '\n' >> "$COMMAND_LOG"
exit 97
"""
    for name in FORBIDDEN_TOOLS:
        _write_executable(bin_dir / name, forbidden)

    return bin_dir, command_log


def _run_runner(
    tmp_path: Path,
    runner: str,
    *args: str,
    extra_env: dict[str, str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    bin_dir, command_log = _mock_command_path(tmp_path)
    isolated_home = tmp_path / "home"
    isolated_home.mkdir()

    env = os.environ.copy()
    for name in (
        "BASH_ENV",
        "CDPATH",
        "CODEX_PRO",
        "CODEX_PRO_BASE_URL",
        "ENV",
        "GOOGLE_AI_STUDIO_API_KEY",
        "HERMES_NOTIFY_WEBHOOK_URL",
        "NINE_ROUTER_API_KEY",
        "NINE_ROUTER_BASE_URL",
        "ROUTER_BASE_URL",
        "SLACK_WEBHOOK_URL",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    ):
        env.pop(name, None)
    env.update(
        {
            "COMMAND_LOG": str(command_log),
            "HOME": str(isolated_home),
            "LC_ALL": "C",
            "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
        }
    )
    if extra_env:
        env.update(extra_env)

    result = subprocess.run(
        [BASH, str(RUNNERS[runner]), *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    commands = (
        command_log.read_text(encoding="ascii").splitlines()
        if command_log.exists()
        else []
    )
    return result, commands


def _assert_safe_execution(
    result: subprocess.CompletedProcess[str],
    commands: list[str],
) -> None:
    assert result.stdout.isascii()
    assert result.stderr.isascii()
    assert not [command for command in commands if command.startswith("FORBIDDEN ")]


def test_runner_sources_are_ascii_and_contain_no_release_mutation_commands():
    texts = {
        name: path.read_text(encoding="utf-8") for name, path in RUNNERS.items()
    }
    assert all(text.isascii() for text in texts.values())

    owned_behavior = "\n".join(texts.values())
    forbidden_patterns = (
        r"\bgit[ \t]+push\b",
        r"\bflyctl\b",
        r"\baz[ \t]+(?:containerapp|deployment|group|resource)\b",
        r"\b(?:npx[ \t]+)?vercel[ \t]+.*--prod\b",
        r"\bsetup_production_secrets\.sh\b",
        r"\bsync_doppler_secrets\.py\b",
        r"--sdk[ \t]+static\b",
        r"\btest_live_e2e_network\.py\b",
        r"\bapi\.telegram\.org\b",
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, owned_behavior, flags=re.IGNORECASE)

    assert not re.search(
        r"^[ \t]*(?:source|\.)[ \t]+[^\n]*(?:\.env|credential|secret)",
        owned_behavior,
        flags=re.IGNORECASE | re.MULTILINE,
    )


@pytest.mark.parametrize("runner", tuple(RUNNERS))
def test_each_release_readiness_path_uses_only_canonical_docker_dry_run(runner):
    text = RUNNERS[runner].read_text(encoding="ascii").replace("\\\n", " ")
    commands = re.findall(
        r"python3[ \t]+scripts/publish_space_hf\.py[^\n]*",
        text,
    )

    assert len(commands) == 1
    assert shlex.split(commands[0]) == ["python3", *CANONICAL_PUBLISH]


@pytest.mark.parametrize(
    ("args", "expected_code", "expected_marker"),
    (
        ((), 2, "[ERROR] BLOCKED"),
        (("deploy",), 2, "[ERROR] BLOCKED"),
        (("unknown",), 2, "[ERROR] BLOCKED"),
        (("--help",), 0, "Local production deployment is disabled."),
    ),
)
def test_auto_runner_default_deploy_and_unknown_are_non_executing(
    tmp_path,
    args,
    expected_code,
    expected_marker,
):
    result, commands = _run_runner(tmp_path, "auto", *args)

    assert result.returncode == expected_code
    assert expected_marker in result.stdout
    assert commands == []
    _assert_safe_execution(result, commands)


def test_auto_runner_dry_run_executes_only_local_qa_scan_and_package_plan(tmp_path):
    result, commands = _run_runner(tmp_path, "auto", "--dry-run")

    assert result.returncode == 0
    assert commands == [
        "CALL pytest\t-m\tpytest\t-v\t--ignore=project/kaggle_kernel",
        "CALL button\tscripts/run_button_regression.py",
        "CALL secret-scan\tproject/core/code_reviewer.py\t--scan-secrets",
        "CALL publisher\t" + "\t".join(CANONICAL_PUBLISH),
    ]
    assert "No deploy, publish, push, or secret synchronization was performed." in result.stdout
    _assert_safe_execution(result, commands)


@pytest.mark.parametrize(
    ("args", "expected_code", "expected_marker"),
    (
        ((), 0, "Hermes SDLC Execution Runner"),
        (("deploy",), 1, "[ERROR]   BLOCKED"),
        (("unknown",), 1, "[ERROR]   BLOCKED"),
    ),
)
def test_hermes_default_deploy_and_unknown_never_execute_commands(
    tmp_path,
    args,
    expected_code,
    expected_marker,
):
    result, commands = _run_runner(tmp_path, "hermes", *args)

    assert result.returncode == expected_code
    assert expected_marker in result.stdout
    assert commands == []
    _assert_safe_execution(result, commands)


def test_hermes_release_plan_is_local_and_ignores_provider_environment(tmp_path):
    result, commands = _run_runner(
        tmp_path,
        "hermes",
        "release-plan",
        extra_env={
            "HERMES_NOTIFY_WEBHOOK_URL": "https://network.invalid/hook",
            "NINE_ROUTER_BASE_URL": "https://network.invalid/v1",
            "ROUTER_BASE_URL": "https://network.invalid/v1",
        },
    )

    assert result.returncode == 0
    assert commands == [
        "CALL secret-scan\tproject/core/code_reviewer.py\t--scan-secrets",
        "CALL publisher\t" + "\t".join(CANONICAL_PUBLISH),
    ]
    assert "Local release readiness dry-run completed." in result.stdout
    _assert_safe_execution(result, commands)


def test_non_release_hermes_qa_and_sync_orchestration_remains_callable(tmp_path):
    qa_result, qa_commands = _run_runner(
        tmp_path / "qa",
        "hermes",
        "qa",
        extra_env={"ROUTER_BASE_URL": "https://mock.invalid/v1"},
    )
    sync_result, sync_commands = _run_runner(tmp_path / "sync", "hermes", "sync")

    assert qa_result.returncode == 0
    qa_labels = [command.split("\t", 1)[0] for command in qa_commands]
    assert len(qa_labels) == 4
    assert qa_labels[0] == "CALL router"
    assert sorted(qa_labels[1:3]) == ["CALL pytest", "CALL tee"]
    assert qa_labels[3] == "CALL button"
    assert sync_result.returncode == 0
    assert sync_commands == [
        "CALL python-other\tscripts/sync_sdlc_agents.py\t--sync",
        "CALL python-other\tscripts/sync_codex_agents.py\t--sync",
        "CALL python-other\tscripts/sync_codex_agents.py\t--check",
    ]
    _assert_safe_execution(qa_result, qa_commands)
    _assert_safe_execution(sync_result, sync_commands)


def test_agentic_pipeline_preserves_all_local_sdlc_phases_without_mutation(tmp_path):
    result, commands = _run_runner(tmp_path, "agentic")

    assert result.returncode == 0
    assert [command.split("\t", 1)[0] for command in commands] == [
        "CALL router",
        "CALL python-inline",
        "CALL pytest",
        "CALL button",
        "CALL secret-scan",
        "CALL publisher",
    ]
    assert commands[-1] == "CALL publisher\t" + "\t".join(CANONICAL_PUBLISH)
    for phase in range(1, 6):
        assert f"PHASE {phase}:" in result.stdout
    assert "LOCAL MULTI-AGENT VALIDATION COMPLETE" in result.stdout
    assert "Release Boundary" in result.stdout
    _assert_safe_execution(result, commands)
