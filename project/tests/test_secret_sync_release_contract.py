"""Offline release contracts for opt-in secret synchronization."""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "sync_doppler_secrets.py"
ENV_EXAMPLE = ROOT / ".env.example"
CANONICAL_SPACE_ID = "pphothidaen/horoconsultant-core-backend"
CANONICAL_BACKEND_URL = (
    "https://pphothidaen-horoconsultant-core-backend.hf.space"
)
CANONICAL_VERCEL_URL = "https://horo-consultant-psi.vercel.app"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "sync_doppler_secrets_release_contract",
        SCRIPT,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _captured_text(capsys, caplog) -> str:
    captured = capsys.readouterr()
    return f"{captured.out}\n{captured.err}\n{caplog.text}"


def test_default_cli_is_dry_run_and_never_reads_dotenv_or_reaches_providers(
    tmp_path,
    monkeypatch,
    caplog,
    capsys,
):
    caplog.set_level(logging.INFO, logger="doppler_sync")
    module = _load_module()
    example = tmp_path / ".env.example"
    implicit_env = tmp_path / ".env"
    canary = "IMPLICIT_DOTENV_MUST_NOT_BE_READ"
    example.write_text(
        f"HF_BACKEND_SPACE_ID={CANONICAL_SPACE_ID}\n",
        encoding="ascii",
    )
    implicit_env.write_text(f"HF_TOKEN={canary}\n", encoding="ascii")
    loaded_paths: list[Path] = []

    def fake_dotenv_values(path):
        loaded_paths.append(Path(path))
        return {"HF_BACKEND_SPACE_ID": CANONICAL_SPACE_ID}

    def forbidden_provider_call(*_args, **_kwargs):
        raise AssertionError("default dry-run reached an external subprocess")

    monkeypatch.setattr(module, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(module, "dotenv_values", fake_dotenv_values)
    monkeypatch.setattr(module.subprocess, "run", forbidden_provider_call)
    monkeypatch.setattr(module, "get_doppler_cli_path", forbidden_provider_call)
    monkeypatch.setattr(module.sys, "argv", [str(SCRIPT)])

    with pytest.raises(SystemExit) as raised:
        module.main()

    output = _captured_text(capsys, caplog)
    assert raised.value.code == 0
    assert loaded_paths == [example]
    assert implicit_env not in loaded_paths
    assert canary not in output
    assert "[OK] Dry run" in output
    assert output.isascii()


def test_apply_requires_explicit_env_file_before_sync(monkeypatch, caplog, capsys):
    caplog.set_level(logging.INFO, logger="doppler_sync")
    module = _load_module()

    def forbidden_sync(*_args, **_kwargs):
        raise AssertionError("sync started without an explicit environment file")

    monkeypatch.setattr(module, "sync_secrets_to_doppler", forbidden_sync)
    monkeypatch.setattr(module.sys, "argv", [str(SCRIPT), "--apply"])

    with pytest.raises(SystemExit) as raised:
        module.main()

    output = _captured_text(capsys, caplog)
    assert raised.value.code == 2
    assert "--apply requires an explicit --env-file" in output
    assert output.isascii()


def test_missing_explicit_file_blocks_before_parse_or_subprocess(
    tmp_path,
    monkeypatch,
    caplog,
    capsys,
):
    caplog.set_level(logging.INFO, logger="doppler_sync")
    module = _load_module()
    missing = tmp_path / "missing-production.env"

    def forbidden_call(*_args, **_kwargs):
        raise AssertionError("missing file reached parsing or a provider subprocess")

    monkeypatch.setattr(module, "dotenv_values", forbidden_call)
    monkeypatch.setattr(module.subprocess, "run", forbidden_call)
    monkeypatch.setattr(module, "get_doppler_cli_path", forbidden_call)
    monkeypatch.setattr(
        module.sys,
        "argv",
        [str(SCRIPT), "--apply", "--env-file", str(missing)],
    )

    with pytest.raises(SystemExit) as raised:
        module.main()

    output = _captured_text(capsys, caplog)
    assert raised.value.code == 1
    assert "Requested environment file was not found" in output
    assert missing.name in output
    assert output.isascii()


def test_explicit_apply_excludes_retired_keys_and_forwards_hf_vercel_targets(
    tmp_path,
    monkeypatch,
    caplog,
    capsys,
):
    caplog.set_level(logging.INFO, logger="doppler_sync")
    module = _load_module()
    active_token = "hf_TEST_CANARY_ACTIVE_VALUE_123456789"
    azure_canary = "AZURE_CANARY_MUST_BE_EXCLUDED"
    fly_canary = "FLY_CANARY_MUST_BE_EXCLUDED"
    env_file = tmp_path / "release.env"
    env_file.write_text(
        "\n".join(
            (
                f"HF_BACKEND_SPACE_ID={CANONICAL_SPACE_ID}",
                f"HF_BACKEND_URL={CANONICAL_BACKEND_URL}",
                f"VERCEL_STATIC_URL={CANONICAL_VERCEL_URL}",
                f"HF_TOKEN={active_token}",
                f"AZURE_CREDENTIALS={azure_canary}",
                f"FLY_API_TOKEN={fly_canary}",
            )
        )
        + "\n",
        encoding="ascii",
    )
    subprocess_calls: list[tuple[list[str], dict]] = []
    github_calls: list[tuple[dict[str, str], bool]] = []

    def fake_run(command, **kwargs):
        subprocess_calls.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout="provider-output", stderr="")

    def fake_github_sync(values, dry_run=False):
        github_calls.append((dict(values), dry_run))

    monkeypatch.setattr(module, "get_doppler_cli_path", lambda: "doppler-mock")
    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(module, "sync_github_secrets", fake_github_sync)
    monkeypatch.setattr(
        module.sys,
        "argv",
        [
            str(SCRIPT),
            "--apply",
            "--env-file",
            str(env_file),
            "--project",
            "horo-consultant",
            "--config",
            "prd",
        ],
    )

    with pytest.raises(SystemExit) as raised:
        module.main()

    output = _captured_text(capsys, caplog)
    assert raised.value.code == 0
    assert len(subprocess_calls) == 1
    command, kwargs = subprocess_calls[0]
    assert command[:7] == [
        "doppler-mock",
        "secrets",
        "set",
        "--project",
        "horo-consultant",
        "--config",
        "prd",
    ]
    forwarded = set(command[7:])
    assert f"HF_BACKEND_SPACE_ID={CANONICAL_SPACE_ID}" in forwarded
    assert f"HF_BACKEND_URL={CANONICAL_BACKEND_URL}" in forwarded
    assert f"VERCEL_STATIC_URL={CANONICAL_VERCEL_URL}" in forwarded
    assert f"HF_TOKEN={active_token}" in forwarded
    assert not any(item.startswith(("AZURE_", "FLY_")) for item in forwarded)
    assert kwargs == {"capture_output": True, "text": True, "check": False}
    assert github_calls == [
        (
            {
                "HF_BACKEND_SPACE_ID": CANONICAL_SPACE_ID,
                "HF_BACKEND_URL": CANONICAL_BACKEND_URL,
                "VERCEL_STATIC_URL": CANONICAL_VERCEL_URL,
                "HF_TOKEN": active_token,
            },
            False,
        )
    ]
    for value in (active_token, azure_canary, fly_canary, "provider-output"):
        assert value not in output
    assert "Ignored 2 retired release-platform keys" in output
    assert output.isascii()


def test_doppler_and_github_failures_never_emit_values_or_provider_output(
    tmp_path,
    monkeypatch,
    caplog,
    capsys,
):
    caplog.set_level(logging.INFO, logger="doppler_sync")
    module = _load_module()
    canary = "hf_TEST_CANARY_MUST_STAY_REDACTED_123456789"
    provider_output = f"provider rejected value={canary}"
    env_file = tmp_path / "release.env"
    env_file.write_text(f"HF_TOKEN={canary}\n", encoding="ascii")
    calls: list[list[str]] = []

    def fake_run(command, **_kwargs):
        calls.append(command)
        if command[:3] == ["doppler-mock", "secrets", "set"]:
            return SimpleNamespace(returncode=0, stdout=provider_output, stderr="")
        assert command == ["gh", "secret", "set", "HF_TOKEN"]
        return SimpleNamespace(
            returncode=1,
            stdout=provider_output,
            stderr=provider_output,
        )

    monkeypatch.setattr(module, "get_doppler_cli_path", lambda: "doppler-mock")
    monkeypatch.setattr(module.shutil, "which", lambda name: f"/mock/{name}")
    monkeypatch.setattr(module.subprocess, "run", fake_run)

    assert module.sync_secrets_to_doppler(env_file, dry_run=False) is True

    output = _captured_text(capsys, caplog)
    assert len(calls) == 2
    assert calls[1] == ["gh", "secret", "set", "HF_TOKEN"]
    assert canary not in output
    assert provider_output not in output
    assert "details redacted" in output
    assert output.isascii()


def test_source_and_environment_example_are_ascii_and_release_scoped():
    source = SCRIPT.read_text(encoding="utf-8")
    example = ENV_EXAMPLE.read_text(encoding="utf-8")
    assignments = {
        key.strip(): value.strip()
        for line in example.splitlines()
        if line and not line.startswith("#") and "=" in line
        for key, value in [line.split("=", maxsplit=1)]
    }

    assert source.isascii()
    assert example.isascii()
    assert not any(key.startswith(("AZURE_", "FLY_")) for key in assignments)
    assert "azurecontainerapps" not in example.lower()
    assert "azure.com" not in example.lower()
    assert "fly.dev" not in example.lower()
    assert "fly.io" not in example.lower()
    assert assignments["HF_BACKEND_SPACE_ID"] == CANONICAL_SPACE_ID
    assert assignments["HF_BACKEND_URL"] == CANONICAL_BACKEND_URL
    assert assignments["VERCEL_STATIC_URL"] == CANONICAL_VERCEL_URL
    assert "Production CI injects GitHub Secrets" in example
    assert "Doppler-managed environment variables" in example
    assert "this file is not a release prerequisite" in example
    assert 'args.env_file or (ROOT_DIR / ".env.example")' in source
    assert "args.apply and args.env_file is None" in source
    assert 'dotenv_values(".env")' not in source
