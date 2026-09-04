"""Automated validation test suite for macOS AI Account Keychain Isolation.

Verifies:
1. Live host account keychain structure (if present on macOS host).
2. Symlink integrity and target resolution across agy1..4 directories.
3. Silent non-interactive unlock execution without GUI dialog popups.
4. Host default keychain pointing to canonical login keychain.
5. verify_keychain_isolation.sh execution across normal, JSON, silent, and failure modes.
6. Pure ASCII stdout/stderr output across all invocations.
7. Graceful platform handling (Darwin vs non-Darwin).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import stat
import subprocess
import sys
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "verify_keychain_isolation.sh"
LIVE_ACCOUNTS_DIR = Path("/Users/kimlenglim/.ai-accounts/agy")
LIVE_DEFAULT_KEYCHAIN = "/Users/kimlenglim/Library/Keychains/login.keychain-db"
ACCOUNT_NAMES = ["account1", "account2", "account3", "account4"]


def is_pure_ascii(text: str) -> bool:
    """Return True if text contains only pure ASCII characters."""
    try:
        text.encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


def run_script(
    args: list[str] | None = None,
    env_updates: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Execute verify_keychain_isolation.sh and return CompletedProcess."""
    cmd = ["bash", str(SCRIPT_PATH)] + (args or [])
    env = os.environ.copy()
    if env_updates:
        env.update(env_updates)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


class TestKeychainScriptPermissions:
    """Verify script file exists and is readable."""

    def test_script_exists_and_is_readable(self) -> None:
        assert SCRIPT_PATH.is_file(), f"Script missing at {SCRIPT_PATH}"
        assert os.access(SCRIPT_PATH, os.R_OK), f"Script not readable at {SCRIPT_PATH}"

    def test_script_help_flag(self) -> None:
        result = run_script(["--help"])
        assert result.returncode == 0
        assert "Usage: verify_keychain_isolation.sh" in result.stdout
        assert is_pure_ascii(result.stdout)
        assert is_pure_ascii(result.stderr)


class TestLiveHostKeychainIsolation:
    """Test live host configuration if running on host with configured accounts."""

    @pytest.mark.skipif(
        not LIVE_ACCOUNTS_DIR.exists() or platform.system() != "Darwin",
        reason="Live macOS AI accounts directory not found or not running on Darwin",
    )
    def test_live_account_symlinks_and_databases(self) -> None:
        for idx, acc in enumerate(ACCOUNT_NAMES, start=1):
            acc_dir = LIVE_ACCOUNTS_DIR / acc
            assert acc_dir.is_dir(), f"Live account dir missing: {acc_dir}"

            kc_dir = acc_dir / "Library" / "Keychains"
            assert kc_dir.is_dir(), f"Live keychains dir missing: {kc_dir}"

            primary_db = kc_dir / f"agy{idx}.keychain-db"
            assert primary_db.is_file(), f"Primary keychain db missing: {primary_db}"

            login_db_link = kc_dir / "login.keychain-db"
            assert login_db_link.is_symlink(), f"login.keychain-db is not symlink: {login_db_link}"
            target_db = os.readlink(str(login_db_link))
            assert Path(target_db).name == f"agy{idx}.keychain-db", (
                f"login.keychain-db target mismatch: {target_db} != agy{idx}.keychain-db"
            )

            login_legacy_link = kc_dir / "login.keychain"
            assert login_legacy_link.is_symlink(), f"login.keychain is not symlink: {login_legacy_link}"
            target_legacy = os.readlink(str(login_legacy_link))
            assert Path(target_legacy).name == f"agy{idx}.keychain-db", (
                f"login.keychain target mismatch: {target_legacy} != agy{idx}.keychain-db"
            )

    @pytest.mark.skipif(
        not LIVE_ACCOUNTS_DIR.exists() or platform.system() != "Darwin",
        reason="Live macOS AI accounts directory not found or not running on Darwin",
    )
    def test_live_default_keychain(self) -> None:
        result = subprocess.run(
            ["security", "default-keychain"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        cleaned = result.stdout.strip().strip('"').strip()
        assert cleaned == LIVE_DEFAULT_KEYCHAIN, (
            f"Default keychain {cleaned} does not match expected canonical path {LIVE_DEFAULT_KEYCHAIN}"
        )

    @pytest.mark.skipif(
        not LIVE_ACCOUNTS_DIR.exists() or platform.system() != "Darwin",
        reason="Live macOS AI accounts directory not found or not running on Darwin",
    )
    def test_live_script_execution_success(self) -> None:
        result = run_script()
        assert result.returncode == 0, f"Script failed with output: {result.stdout}\n{result.stderr}"
        assert "[SUMMARY] Status: PASS" in result.stdout
        assert is_pure_ascii(result.stdout)
        assert is_pure_ascii(result.stderr)

    @pytest.mark.skipif(
        not LIVE_ACCOUNTS_DIR.exists() or platform.system() != "Darwin",
        reason="Live macOS AI accounts directory not found or not running on Darwin",
    )
    def test_live_script_json_mode(self) -> None:
        result = run_script(["--json"])
        assert result.returncode == 0
        assert is_pure_ascii(result.stdout)
        data = json.loads(result.stdout)
        assert data["status"] == "PASS"
        assert data["failures"] == 0
        assert len(data["accounts"]) == 4
        for acc_info in data["accounts"]:
            assert acc_info["status"] == "PASSED"
            assert acc_info["unlock_status"] in ("NON_INTERACTIVE_VERIFIED", "SKIPPED_NON_DARWIN")

    @pytest.mark.skipif(
        not LIVE_ACCOUNTS_DIR.exists() or platform.system() != "Darwin",
        reason="Live macOS AI accounts directory not found or not running on Darwin",
    )
    def test_live_script_silent_mode(self) -> None:
        result = run_script(["--silent"])
        assert result.returncode == 0
        assert "[OK]" not in result.stdout
        assert "[INFO]" not in result.stdout
        assert "[SUMMARY] Status: PASS" in result.stdout
        assert is_pure_ascii(result.stdout)


class TestSyntheticKeychainIsolation:
    """Test validation script behavior against controlled synthetic directories."""

    @pytest.fixture
    def synthetic_env(self, tmp_path: Path) -> dict[str, Any]:
        """Create a synthetic 4-account directory layout."""
        accounts_root = tmp_path / "ai-accounts" / "agy"
        for i in range(1, 5):
            acc_dir = accounts_root / f"account{i}"
            kc_dir = acc_dir / "Library" / "Keychains"
            kc_dir.mkdir(parents=True, exist_ok=True)
            db_file = kc_dir / f"agy{i}.keychain-db"
            db_file.write_bytes(b"SYNTHETIC_KEYCHAIN_DATA")

            login_db = kc_dir / "login.keychain-db"
            login_db.symlink_to(f"agy{i}.keychain-db")

            login_legacy = kc_dir / "login.keychain"
            login_legacy.symlink_to(f"agy{i}.keychain-db")

        default_kc = LIVE_DEFAULT_KEYCHAIN if platform.system() == "Darwin" else str(tmp_path / "mock.keychain-db")
        return {
            "root": accounts_root,
            "default_keychain": default_kc,
        }

    def test_synthetic_valid_structure_passes(self, synthetic_env: dict[str, Any]) -> None:
        args = [
            "--accounts-dir",
            str(synthetic_env["root"]),
            "--default-keychain",
            synthetic_env["default_keychain"],
        ]
        result = run_script(args)
        assert result.returncode == 0
        assert "[SUMMARY] Status: PASS" in result.stdout
        assert is_pure_ascii(result.stdout)

    def test_synthetic_json_mode(self, synthetic_env: dict[str, Any]) -> None:
        args = [
            "--accounts-dir",
            str(synthetic_env["root"]),
            "--default-keychain",
            synthetic_env["default_keychain"],
            "--json",
        ]
        result = run_script(args)
        assert result.returncode == 0
        assert is_pure_ascii(result.stdout)
        data = json.loads(result.stdout)
        assert data["status"] == "PASS"
        assert data["checks_passed"] == data["checks_total"]
        assert len(data["accounts"]) == 4

    def test_synthetic_missing_keychain_db_fails(self, synthetic_env: dict[str, Any]) -> None:
        # Remove primary db in account2
        target_db = synthetic_env["root"] / "account2" / "Library" / "Keychains" / "agy2.keychain-db"
        target_db.unlink()

        args = [
            "--accounts-dir",
            str(synthetic_env["root"]),
            "--default-keychain",
            synthetic_env["default_keychain"],
        ]
        result = run_script(args)
        assert result.returncode == 1
        assert "[ERROR] [account2] Target keychain-db missing: agy2.keychain-db" in result.stdout
        assert "[SUMMARY] Status: FAIL" in result.stdout
        assert is_pure_ascii(result.stdout)

    def test_synthetic_broken_symlink_fails(self, synthetic_env: dict[str, Any]) -> None:
        # Point login.keychain-db to non-matching target
        login_db = synthetic_env["root"] / "account3" / "Library" / "Keychains" / "login.keychain-db"
        login_db.unlink()
        login_db.symlink_to("wrong_target.keychain-db")

        args = [
            "--accounts-dir",
            str(synthetic_env["root"]),
            "--default-keychain",
            synthetic_env["default_keychain"],
        ]
        result = run_script(args)
        assert result.returncode == 1
        assert "[ERROR] [account3] login.keychain-db points to invalid target: wrong_target.keychain-db" in result.stdout
        assert "[SUMMARY] Status: FAIL" in result.stdout

    def test_synthetic_missing_symlink_fails(self, synthetic_env: dict[str, Any]) -> None:
        # Replace symlink with regular file
        login_legacy = synthetic_env["root"] / "account4" / "Library" / "Keychains" / "login.keychain"
        login_legacy.unlink()
        login_legacy.write_text("not_a_symlink")

        args = [
            "--accounts-dir",
            str(synthetic_env["root"]),
            "--default-keychain",
            synthetic_env["default_keychain"],
        ]
        result = run_script(args)
        assert result.returncode == 1
        assert "[ERROR] [account4] login.keychain is not a symlink" in result.stdout
        assert "[SUMMARY] Status: FAIL" in result.stdout

    def test_synthetic_default_keychain_mismatch_fails_on_darwin(
        self, synthetic_env: dict[str, Any]
    ) -> None:
        if platform.system() != "Darwin":
            pytest.skip("Default keychain check runs strictly on macOS Darwin")

        args = [
            "--accounts-dir",
            str(synthetic_env["root"]),
            "--default-keychain",
            "/Invalid/Path/NonExistent.keychain-db",
        ]
        result = run_script(args)
        assert result.returncode == 1
        assert "[ERROR] Default keychain mismatch." in result.stdout
        assert "[SUMMARY] Status: FAIL" in result.stdout

    def test_synthetic_partial_accounts_list(self, synthetic_env: dict[str, Any]) -> None:
        args = [
            "--accounts-dir",
            str(synthetic_env["root"]),
            "--default-keychain",
            synthetic_env["default_keychain"],
            "--accounts",
            "account1,account3",
            "--json",
        ]
        result = run_script(args)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert len(data["accounts"]) == 2
        assert [acc["account"] for acc in data["accounts"]] == ["account1", "account3"]
