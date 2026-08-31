"""Security baseline for the macOS AI account broker and wrapper bridge.

The production broker contract is intentionally small::

    ai-account-keychain-broker <alias> -- <provider argv...>

Only agy1..agy3 and codex1..codex3 are admitted.  The Swift source may expose
``AI_ACCOUNT_BROKER_TEST_SECURITY`` and ``AI_ACCOUNT_BROKER_TEST_ROOT`` only in
an ``ACCOUNT_BROKER_TESTING`` compilation block so these tests can substitute
synthetic keychain/account fixtures.  Production callers cannot select a
keychain or provider path.

The installer contract is::

    install_ai_account_wrappers.py --output-dir DIR --broker-path PATH
                                   [--dry-run]

All tests install under pytest temporary directories and execute only fake
security, broker, and provider programs.  They never inspect or invoke live
account wrappers or macOS keychains.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
BROKER_SOURCE = ROOT / "scripts" / "ai_account_keychain_broker.swift"
INSTALLER_SOURCE = ROOT / "scripts" / "install_ai_account_wrappers.py"
ALIASES = ("agy1", "agy2", "agy3", "codex1", "codex2", "codex3")
SYNTHETIC_SECRET = "BROKER_TEST_ONLY_SECRET_7f41c9"
TEST_SECURITY_ENV = "AI_ACCOUNT_BROKER_TEST_SECURITY"
TEST_ROOT_ENV = "AI_ACCOUNT_BROKER_TEST_ROOT"


def _clean_env(**updates: str) -> dict[str, str]:
    """Build a credential-free environment for every synthetic subprocess."""

    env = {
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    }
    env.update(updates)
    return env


def _run(
    argv: list[str | Path],
    *,
    env: dict[str, str],
    timeout: int = 20,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(part) for part in argv],
        cwd=ROOT,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )


def _write_executable(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(0o700)


def _json_lines(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _assert_sanitized(completed: subprocess.CompletedProcess[str], *forbidden: str) -> None:
    public_output = completed.stdout + completed.stderr
    for value in forbidden:
        assert value not in public_output


def test_broker_and_bridge_sources_are_present() -> None:
    missing = [
        str(path.relative_to(ROOT))
        for path in (BROKER_SOURCE, INSTALLER_SOURCE)
        if not path.is_file()
    ]
    assert not missing, f"BROKER_TDD_001_SOURCE_MISSING: {', '.join(missing)}"


@pytest.fixture
def installer() -> Path:
    if not INSTALLER_SOURCE.is_file():
        pytest.skip("BROKER-TDD-001 source lane has not created the installer")
    return INSTALLER_SOURCE


@pytest.fixture(scope="session")
def broker_binary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    if not BROKER_SOURCE.is_file():
        pytest.skip("BROKER-TDD-001 source lane has not created the Swift broker")
    if sys.platform != "darwin":
        pytest.skip("the account broker is a macOS-only security boundary")

    swiftc = shutil.which("swiftc")
    assert swiftc is not None, "swiftc is required to verify the macOS broker"
    source = BROKER_SOURCE.read_text(encoding="utf-8")
    for marker in (
        "#if ACCOUNT_BROKER_TESTING",
        TEST_SECURITY_ENV,
        TEST_ROOT_ENV,
    ):
        assert marker in source, f"missing compile-gated synthetic test seam: {marker}"

    output = tmp_path_factory.mktemp("broker-build") / "ai-account-keychain-broker-test"
    completed = _run(
        [swiftc, "-D", "ACCOUNT_BROKER_TESTING", BROKER_SOURCE, "-o", output],
        env=_clean_env(PATH=os.environ.get("PATH", "/usr/bin:/bin")),
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    assert output.is_file()
    return output


@pytest.fixture
def synthetic_runtime(tmp_path: Path) -> dict[str, Any]:
    fake_bin = tmp_path / "fake-bin"
    account_root = tmp_path / "isolated-accounts"
    security_log = tmp_path / "security.jsonl"
    provider_capture = tmp_path / "provider.json"

    fake_security = fake_bin / "security"
    _write_executable(
        fake_security,
        f"""#!{sys.executable}
import json
import os
from pathlib import Path
import sys

secret = {SYNTHETIC_SECRET!r}
args = sys.argv[1:]
mode = os.environ.get("FAKE_SECURITY_MODE", "ok")
log = Path(os.environ["FAKE_SECURITY_LOG"])
record = {{"argv": args, "stdin_matches": None}}

if args and args[0] == "find-generic-password":
    with log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\\n")
    if mode == "lookup-fail":
        print("synthetic lookup diagnostic " + secret, file=sys.stderr)
        raise SystemExit(41)
    print(secret)
    raise SystemExit(0)

if args and args[0] == "unlock-keychain":
    supplied = sys.stdin.read().rstrip("\\n")
    record["stdin_matches"] = supplied == secret
    with log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\\n")
    if mode == "unlock-fail":
        print("synthetic unlock diagnostic " + secret, file=sys.stderr)
        raise SystemExit(42)
    raise SystemExit(0 if supplied == secret else 43)

with log.open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(record, sort_keys=True) + "\\n")
raise SystemExit(44)
""",
    )

    provider_body = f"""#!{sys.executable}
import json
import os
from pathlib import Path
import sys

capture = Path(os.environ["PROVIDER_CAPTURE"])
capture.write_text(
    json.dumps(
        {{"provider": Path(sys.argv[0]).name, "argv": sys.argv[1:], "env": dict(os.environ)}},
        sort_keys=True,
    ),
    encoding="utf-8",
)
mode = os.environ.get("PROVIDER_MODE", "ok")
if mode == "emit-secret":
    print({SYNTHETIC_SECRET!r})
    print("provider stderr " + {SYNTHETIC_SECRET!r}, file=sys.stderr)
    raise SystemExit(0)
if mode == "fail":
    print("provider failed before execution proof", file=sys.stderr)
    raise SystemExit(73)
print("PROVIDER_EXECUTION_PROOF")
"""
    for provider in ("agy", "codex"):
        _write_executable(fake_bin / provider, provider_body)

    env = _clean_env(
        PATH=f"{fake_bin}:/usr/bin:/bin:/usr/sbin:/sbin",
        HOME=str(tmp_path / "ambient-home"),
        AGY_HOME=str(tmp_path / "ambient-agy"),
        CODEX_HOME=str(tmp_path / "ambient-codex"),
        XDG_CONFIG_HOME=str(tmp_path / "ambient-xdg-config"),
        XDG_CACHE_HOME=str(tmp_path / "ambient-xdg-cache"),
        XDG_DATA_HOME=str(tmp_path / "ambient-xdg-data"),
        TMPDIR=str(tmp_path / "ambient-tmp"),
        TMP=str(tmp_path / "ambient-tmp"),
        TEMP=str(tmp_path / "ambient-tmp"),
        FAKE_SECURITY_LOG=str(security_log),
        PROVIDER_CAPTURE=str(provider_capture),
        **{
            TEST_SECURITY_ENV: str(fake_security),
            TEST_ROOT_ENV: str(account_root),
        },
    )
    return {
        "root": account_root,
        "fake_bin": fake_bin,
        "security": fake_security,
        "security_log": security_log,
        "capture": provider_capture,
        "env": env,
    }


def _run_broker(
    broker: Path,
    runtime: dict[str, Any],
    alias: str,
    args: list[str] | None = None,
    **env_updates: str,
) -> subprocess.CompletedProcess[str]:
    env = dict(runtime["env"])
    env.update(env_updates)
    return _run([broker, alias, "--", *(args or [])], env=env)


def _install(
    installer: Path,
    output_dir: Path,
    broker_path: Path,
    *,
    dry_run: bool = False,
) -> subprocess.CompletedProcess[str]:
    argv: list[str | Path] = [
        sys.executable,
        installer,
        "--output-dir",
        output_dir,
        "--broker-path",
        broker_path,
    ]
    if dry_run:
        argv.append("--dry-run")
    return _run(argv, env=_clean_env())


def test_installer_dry_run_lists_exact_allowlist_without_writing(
    installer: Path, tmp_path: Path
) -> None:
    output_dir = tmp_path / "wrappers"
    broker = tmp_path / "synthetic broker"

    completed = _install(installer, output_dir, broker, dry_run=True)

    assert completed.returncode == 0, completed.stderr
    assert not output_dir.exists()
    for alias in ALIASES:
        assert alias in completed.stdout
    assert "agy4" not in completed.stdout
    assert "codex4" not in completed.stdout
    _assert_sanitized(completed, SYNTHETIC_SECRET)


@pytest.fixture
def installed_wrappers(installer: Path, tmp_path: Path) -> tuple[Path, Path]:
    capture = tmp_path / "fake-broker-capture.json"
    fake_broker = tmp_path / "broker fixture" / "fake broker"
    _write_executable(
        fake_broker,
        f"""#!{sys.executable}
import json
import os
from pathlib import Path
import sys
Path(os.environ["FAKE_BROKER_CAPTURE"]).write_text(
    json.dumps({{"argv": sys.argv[1:], "env": dict(os.environ)}}, sort_keys=True),
    encoding="utf-8",
)
""",
    )
    output_dir = tmp_path / "installed wrappers"
    completed = _install(installer, output_dir, fake_broker)
    assert completed.returncode == 0, completed.stderr
    return output_dir, capture


def test_installer_creates_only_owner_executable_allowlisted_wrappers(
    installed_wrappers: tuple[Path, Path],
) -> None:
    output_dir, _ = installed_wrappers
    assert sorted(path.name for path in output_dir.iterdir()) == list(ALIASES)
    assert stat.S_IMODE(output_dir.stat().st_mode) == 0o700
    for wrapper in output_dir.iterdir():
        assert wrapper.is_file() and not wrapper.is_symlink()
        assert stat.S_IMODE(wrapper.stat().st_mode) == 0o700


def test_installed_templates_contain_no_secret_or_environment_assignment(
    installed_wrappers: tuple[Path, Path],
) -> None:
    output_dir, _ = installed_wrappers
    for wrapper in output_dir.iterdir():
        text = wrapper.read_text(encoding="utf-8")
        assert SYNTHETIC_SECRET not in text
        for variable in (
            "HOME=",
            "AGY_HOME=",
            "CODEX_HOME=",
            "XDG_CONFIG_HOME=",
            "XDG_CACHE_HOME=",
            "XDG_DATA_HOME=",
            "TMPDIR=",
        ):
            assert variable not in text


@pytest.mark.parametrize("alias", ALIASES)
def test_wrapper_forwards_exact_arguments_without_shell_interpretation(
    installed_wrappers: tuple[Path, Path], alias: str, tmp_path: Path
) -> None:
    output_dir, capture = installed_wrappers
    args = ["", "two words", "$(touch should-not-exist)", "semi;colon", "--", "雪"]
    env = _clean_env(
        FAKE_BROKER_CAPTURE=str(capture),
        HOME=str(tmp_path / "ambient"),
    )

    completed = _run([output_dir / alias, *args], env=env)

    assert completed.returncode == 0, completed.stderr
    record = json.loads(capture.read_text(encoding="utf-8"))
    assert record["argv"] == [alias, "--", *args]
    assert not (ROOT / "should-not-exist").exists()
    assert SYNTHETIC_SECRET not in record["argv"]
    _assert_sanitized(completed, SYNTHETIC_SECRET)


def test_installer_refuses_symlink_output_directory(
    installer: Path, tmp_path: Path
) -> None:
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    linked_dir = tmp_path / "linked"
    linked_dir.symlink_to(real_dir, target_is_directory=True)

    completed = _install(installer, linked_dir, tmp_path / "fake-broker")

    assert completed.returncode != 0
    assert list(real_dir.iterdir()) == []
    _assert_sanitized(completed, SYNTHETIC_SECRET)


@pytest.mark.parametrize("flag", ["--keychain", "--keychain-path", "--provider", "--provider-path"])
def test_installer_has_no_keychain_or_provider_override_flags(
    installer: Path, tmp_path: Path, flag: str
) -> None:
    completed = _run(
        [
            sys.executable,
            installer,
            "--output-dir",
            tmp_path / "out",
            "--broker-path",
            tmp_path / "broker",
            flag,
            tmp_path / "attacker-controlled",
        ],
        env=_clean_env(),
    )
    assert completed.returncode != 0
    assert not (tmp_path / "out").exists()


def test_swift_source_compiles_in_release_mode(tmp_path: Path) -> None:
    if not BROKER_SOURCE.is_file():
        pytest.skip("BROKER-TDD-001 source lane has not created the Swift broker")
    if sys.platform != "darwin":
        pytest.skip("the account broker is a macOS-only security boundary")
    swiftc = shutil.which("swiftc")
    assert swiftc is not None, "swiftc is required to verify the macOS broker"

    completed = _run(
        [swiftc, BROKER_SOURCE, "-o", tmp_path / "release-broker"],
        env=_clean_env(PATH=os.environ.get("PATH", "/usr/bin:/bin")),
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize(
    "alias",
    ["agy0", "agy4", "codex0", "codex4", "AGY1", "../agy1", "agy1/../../x", ""],
)
def test_broker_rejects_every_alias_outside_exact_allowlist_without_side_effects(
    broker_binary: Path,
    synthetic_runtime: dict[str, Any],
    alias: str,
) -> None:
    completed = _run_broker(broker_binary, synthetic_runtime, alias)

    assert completed.returncode != 0
    assert not synthetic_runtime["security_log"].exists()
    assert not synthetic_runtime["capture"].exists()
    _assert_sanitized(completed, SYNTHETIC_SECRET, alias if alias else "\0")


@pytest.mark.parametrize("flag", ["--keychain", "--keychain-path", "--provider", "--provider-path"])
def test_broker_rejects_arbitrary_keychain_and_provider_paths_before_lookup(
    broker_binary: Path,
    synthetic_runtime: dict[str, Any],
    flag: str,
    tmp_path: Path,
) -> None:
    completed = _run(
        [broker_binary, flag, tmp_path / "attacker-controlled", "agy1", "--"],
        env=synthetic_runtime["env"],
    )

    assert completed.returncode != 0
    assert not synthetic_runtime["security_log"].exists()
    assert not synthetic_runtime["capture"].exists()


@pytest.mark.parametrize("alias", ALIASES)
def test_exact_allowlisted_alias_selects_only_its_fixed_provider(
    broker_binary: Path,
    synthetic_runtime: dict[str, Any],
    alias: str,
) -> None:
    completed = _run_broker(broker_binary, synthetic_runtime, alias, ["version"])

    assert completed.returncode == 0, completed.stderr
    capture = json.loads(synthetic_runtime["capture"].read_text(encoding="utf-8"))
    assert capture["argv"] == ["version"]
    assert capture["provider"] == ("agy" if alias.startswith("agy") else "codex")
    assert "PROVIDER_EXECUTION_PROOF" in completed.stdout
    security_records = _json_lines(synthetic_runtime["security_log"])
    assert [record["argv"][0] for record in security_records] == [
        "find-generic-password",
        "unlock-keychain",
    ]
    assert security_records[1]["stdin_matches"] is True


def test_broker_forwards_provider_arguments_byte_for_byte(
    broker_binary: Path,
    synthetic_runtime: dict[str, Any],
) -> None:
    args = ["", "two words", "--provider-path", "/provider-owned/value", "a=b", "雪", "--"]

    completed = _run_broker(broker_binary, synthetic_runtime, "codex2", args)

    assert completed.returncode == 0, completed.stderr
    capture = json.loads(synthetic_runtime["capture"].read_text(encoding="utf-8"))
    assert capture["argv"] == args


@pytest.mark.parametrize("mode", ["lookup-fail", "unlock-fail"])
def test_keychain_failure_is_fail_closed_and_never_uses_environment_fallback(
    broker_binary: Path,
    synthetic_runtime: dict[str, Any],
    mode: str,
) -> None:
    completed = _run_broker(
        broker_binary,
        synthetic_runtime,
        "agy2",
        ["status"],
        FAKE_SECURITY_MODE=mode,
        OPENAI_API_KEY=SYNTHETIC_SECRET,
        GEMINI_API_KEY=SYNTHETIC_SECRET,
    )

    assert completed.returncode != 0
    assert not synthetic_runtime["capture"].exists()
    _assert_sanitized(completed, SYNTHETIC_SECRET, "OPENAI_API_KEY", "GEMINI_API_KEY")
    records = _json_lines(synthetic_runtime["security_log"])
    expected_calls = 1 if mode == "lookup-fail" else 2
    assert len(records) == expected_calls


def test_secret_never_reaches_provider_env_argv_or_public_streams(
    broker_binary: Path,
    synthetic_runtime: dict[str, Any],
) -> None:
    completed = _run_broker(broker_binary, synthetic_runtime, "agy1", ["safe-arg"])

    assert completed.returncode == 0, completed.stderr
    capture_text = synthetic_runtime["capture"].read_text(encoding="utf-8")
    security_text = synthetic_runtime["security_log"].read_text(encoding="utf-8")
    assert SYNTHETIC_SECRET not in capture_text
    assert SYNTHETIC_SECRET not in security_text
    _assert_sanitized(completed, SYNTHETIC_SECRET)


def test_known_keychain_secret_is_redacted_from_provider_output(
    broker_binary: Path,
    synthetic_runtime: dict[str, Any],
) -> None:
    completed = _run_broker(
        broker_binary,
        synthetic_runtime,
        "codex1",
        PROVIDER_MODE="emit-secret",
    )

    assert completed.returncode == 0
    _assert_sanitized(completed, SYNTHETIC_SECRET)


@pytest.mark.parametrize("alias", ALIASES)
def test_broker_applies_per_alias_home_provider_xdg_and_tmp_isolation(
    broker_binary: Path,
    synthetic_runtime: dict[str, Any],
    alias: str,
) -> None:
    completed = _run_broker(broker_binary, synthetic_runtime, alias)
    assert completed.returncode == 0, completed.stderr
    env = json.loads(synthetic_runtime["capture"].read_text(encoding="utf-8"))["env"]
    alias_root = synthetic_runtime["root"] / alias
    expected = {
        "HOME": alias_root / "home",
        "XDG_CONFIG_HOME": alias_root / "xdg" / "config",
        "XDG_CACHE_HOME": alias_root / "xdg" / "cache",
        "XDG_DATA_HOME": alias_root / "xdg" / "data",
        "TMPDIR": alias_root / "tmp",
        "TMP": alias_root / "tmp",
        "TEMP": alias_root / "tmp",
    }
    provider_home = "AGY_HOME" if alias.startswith("agy") else "CODEX_HOME"
    other_home = "CODEX_HOME" if provider_home == "AGY_HOME" else "AGY_HOME"
    expected[provider_home] = alias_root / ("agy" if alias.startswith("agy") else "codex")

    for name, path in expected.items():
        assert env[name] == str(path)
        assert path.is_dir()
        assert stat.S_IMODE(path.stat().st_mode) == 0o700
    assert other_home not in env
    assert stat.S_IMODE(alias_root.stat().st_mode) == 0o700


def test_provider_exit_is_not_reported_as_execution_success(
    broker_binary: Path,
    synthetic_runtime: dict[str, Any],
) -> None:
    completed = _run_broker(
        broker_binary,
        synthetic_runtime,
        "codex3",
        PROVIDER_MODE="fail",
    )

    assert completed.returncode == 73
    assert synthetic_runtime["capture"].is_file()
    assert "PROVIDER_EXECUTION_PROOF" not in completed.stdout
    public = (completed.stdout + completed.stderr).lower()
    assert "execution successful" not in public
    assert "account executed" not in public


def test_admission_without_provider_spawn_is_not_execution_proof(
    broker_binary: Path,
    synthetic_runtime: dict[str, Any],
) -> None:
    (synthetic_runtime["fake_bin"] / "codex").unlink()

    completed = _run_broker(broker_binary, synthetic_runtime, "codex2")

    assert completed.returncode != 0
    assert len(_json_lines(synthetic_runtime["security_log"])) == 2
    assert not synthetic_runtime["capture"].exists()
    assert "PROVIDER_EXECUTION_PROOF" not in completed.stdout
    _assert_sanitized(completed, SYNTHETIC_SECRET, str(synthetic_runtime["root"]))


def test_invalid_alias_and_keychain_errors_are_sanitized(
    broker_binary: Path,
    synthetic_runtime: dict[str, Any],
) -> None:
    hostile_alias = "invalid-" + SYNTHETIC_SECRET
    invalid = _run_broker(broker_binary, synthetic_runtime, hostile_alias)
    assert invalid.returncode != 0
    _assert_sanitized(invalid, hostile_alias, SYNTHETIC_SECRET)

    failed_runtime = dict(synthetic_runtime)
    failed_runtime["security_log"] = synthetic_runtime["security_log"].with_name("failed-security.jsonl")
    failed_runtime["env"] = dict(synthetic_runtime["env"])
    failed_runtime["env"]["FAKE_SECURITY_LOG"] = str(failed_runtime["security_log"])
    lookup = _run_broker(
        broker_binary,
        failed_runtime,
        "agy3",
        FAKE_SECURITY_MODE="lookup-fail",
    )
    assert lookup.returncode != 0
    _assert_sanitized(lookup, SYNTHETIC_SECRET, str(failed_runtime["root"]))
