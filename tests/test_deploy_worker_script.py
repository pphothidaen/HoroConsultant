"""Offline fail-closed tests for scripts/deploy-worker.sh (TICKET-264).

The deploy helper must dispatch `wrangler deploy` against exactly one of the
three per-account wrangler configs (hermes, gemini, aipass), use dry-run for
preview, and refuse production unless CLOUDFLARE_API_TOKEN is present. All
tests are hermetic: `npx`/`wrangler` are stubbed on PATH and never reach the
network.
"""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "deploy-worker.sh"

ACCOUNTS = ("hermes", "gemini", "aipass")


@pytest.fixture(scope="module")
def stub_env(tmp_path_factory):
    """PATH prefix with npx/wrangler stubs that record argv and exit 0."""
    bin_dir = tmp_path_factory.mktemp("stub-bin")
    call_log = bin_dir / "wrangler-calls.log"
    stub_body = (
        "#!/bin/sh\n"
        'printf "%s\\n" "$*" >> "$STUB_CALL_LOG"\n'
        "exit 0\n"
    )
    for name in ("npx", "wrangler"):
        stub = bin_dir / name
        stub.write_text(stub_body, encoding="utf-8")
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
    return bin_dir, call_log


def run_deploy(args, stub_env, env_extra=None):
    """Run deploy-worker.sh with stubbed npx/wrangler and no API token."""
    bin_dir, call_log = stub_env
    if call_log.exists():
        call_log.unlink()
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"
    env["STUB_CALL_LOG"] = str(call_log)
    env.pop("CLOUDFLARE_API_TOKEN", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
        check=False,
    )


def stubbed_calls(call_log):
    if not call_log.exists():
        return []
    return [line.strip() for line in call_log.read_text().splitlines() if line.strip()]


class TestDeployWorkerScriptContract:
    """scripts/deploy-worker.sh must fail closed before any deploy occurs."""

    def test_script_exists_with_bash_shebang(self):
        assert SCRIPT.is_file(), f"Missing deploy helper: {SCRIPT}"
        first_line = SCRIPT.read_text(encoding="utf-8").splitlines()[0]
        assert first_line.startswith("#!"), "deploy-worker.sh must have a shebang"
        assert "bash" in first_line, "deploy-worker.sh must run under bash"

    def test_script_is_committed_100644_for_hf_payload_contract(self):
        mode = subprocess.check_output(
            ["git", "ls-files", "-s", "scripts/deploy-worker.sh"],
            cwd=ROOT,
            text=True,
        ).split()[0]
        assert mode == "100644", (
            "HF payload contract requires regular 100644 sources; "
            "invoke via 'bash scripts/deploy-worker.sh'"
        )

    def test_no_args_fails_with_usage_listing_all_three_accounts(self, stub_env):
        result = run_deploy([], stub_env)
        output = result.stdout + result.stderr
        assert result.returncode != 0, "no-args invocation must fail closed"
        for account in ACCOUNTS:
            assert account in output, (
                f"usage text must mention the '{account}' account"
            )

    def test_invalid_account_is_rejected_without_deploying(self, stub_env):
        bin_dir, call_log = stub_env
        result = run_deploy(["bogus", "preview"], stub_env)
        output = result.stdout + result.stderr
        assert result.returncode != 0, "unknown account must be rejected"
        assert stubbed_calls(call_log) == [], (
            "unknown account must never invoke npx/wrangler"
        )

    @pytest.mark.parametrize("account", ACCOUNTS)
    def test_valid_account_maps_to_its_wrangler_config_in_preview_dry_run(
        self, stub_env, account
    ):
        bin_dir, call_log = stub_env
        result = run_deploy([account, "preview"], stub_env)
        calls = stubbed_calls(call_log)
        assert result.returncode == 0, (
            f"preview dry-run for '{account}' must succeed; "
            f"stderr={result.stderr!r}"
        )
        assert calls, "preview mode must invoke the stubbed wrangler entrypoint"
        joined = " ".join(calls)
        assert "deploy" in joined, f"expected a wrangler deploy call, got: {joined}"
        assert "--dry-run" in joined, (
            f"preview mode must pass --dry-run, got: {joined}"
        )
        assert f"wrangler.{account}.toml" in joined, (
            f"account '{account}' must map to wrangler.{account}.toml, got: {joined}"
        )
        for other in ACCOUNTS:
            if other != account:
                assert f"wrangler.{other}.toml" not in joined, (
                    f"account '{account}' must not deploy the '{other}' config"
                )

    @pytest.mark.parametrize("account", ACCOUNTS)
    def test_production_without_api_token_fails_before_deploying(
        self, stub_env, account
    ):
        bin_dir, call_log = stub_env
        result = run_deploy([account, "production"], stub_env)
        output = result.stdout + result.stderr
        assert result.returncode != 0, (
            "production without CLOUDFLARE_API_TOKEN must fail closed"
        )
        assert "CLOUDFLARE_API_TOKEN" in output, (
            "error must name the missing CLOUDFLARE_API_TOKEN secret"
        )
        assert stubbed_calls(call_log) == [], (
            "production gate must trigger before any npx/wrangler invocation"
        )
