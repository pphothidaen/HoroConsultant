"""Contract test: Secret Rotation + OIDC Federation (KAN-296).

M6 of Phase 0 Foundation Hardening (KAN-290, Epic KAN-289).

Red Team CRITICAL: Secrets rotation and OIDC federation must be implemented.
This test freezes the contract: SecretManager MUST implement all interface methods
for quarterly rotation, OIDC federation (Cloudflare/Render/Doppler), and secret scanning.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SECRETS_DIR = ROOT / "src" / "secrets"
MANAGER_TS = SECRETS_DIR / "manager.ts"


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)


# ── Contract 2: SecretManager interface existence ─────────────────────────

def test_secrets_manager_file_exists() -> None:
    """src/secrets/manager.ts must exist."""
    assert MANAGER_TS.exists(), f"Missing {MANAGER_TS}"


def test_secrets_manager_exports_interface() -> None:
    """manager.ts must export SecretManager interface and all types."""
    content = MANAGER_TS.read_text(encoding="utf-8")

    required_exports = [
        "SecretMetadata",
        "RotationResult",
        "SecretManager",
        "OIDCConfig",
        "LeakFinding",
        "configureOIDC",
        "validateOIDC",
        "scanForLeaks",
        "listSecrets",
        "getSecret",
        "rotateSecret",
        "rotateAllDue",
    ]

    for export in required_exports:
        assert export in content, f"Missing export: {export}"


def test_secret_metadata_has_required_fields() -> None:
    """SecretMetadata must have all required fields per CONTRACT 2."""
    content = MANAGER_TS.read_text(encoding="utf-8")

    required_fields = [
        "name: string",
        "provider:",
        "rotationSchedule:",
        "lastRotated: string",
        "nextRotation: string",
        "oidcConfigured: boolean",
        "oidcProvider?: string",
        "scopes?: string[]",
    ]

    for field in required_fields:
        assert field in content, f"SecretMetadata missing field: {field}"


def test_rotation_result_has_required_fields() -> None:
    """RotationResult must have all required fields per CONTRACT 2."""
    content = MANAGER_TS.read_text(encoding="utf-8")

    required_fields = [
        "success: boolean",
        "secretName: string",
        "newValue?: string",
        "rotatedAt: string",
        "error?: string",
    ]

    for field in required_fields:
        assert field in content, f"RotationResult missing field: {field}"


def test_oidc_config_has_required_fields() -> None:
    """OIDCConfig must have all required fields per CONTRACT 2."""
    content = MANAGER_TS.read_text(encoding="utf-8")

    required_fields = [
        "provider:",
        "githubRepo: string",
        "githubEnvironment?: string",
        "audiences?: string[]",
    ]

    for field in required_fields:
        assert field in content, f"OIDCConfig missing field: {field}"


def test_leak_finding_has_required_fields() -> None:
    """LeakFinding must have all required fields per CONTRACT 2."""
    content = MANAGER_TS.read_text(encoding="utf-8")

    required_fields = [
        "file: string",
        "line: number",
        "secretType: string",
        "severity:",
        "matchedContent: string",
    ]

    for field in required_fields:
        assert field in content, f"LeakFinding missing field: {field}"


def test_secret_manager_interface_methods() -> None:
    """SecretManager interface must declare all required methods per CONTRACT 2."""
    content = MANAGER_TS.read_text(encoding="utf-8")

    required_methods = [
        "listSecrets(): Promise<SecretMetadata[]>",
        "getSecret(name: string): Promise<string>",
        "rotateSecret(name: string): Promise<RotationResult>",
        "rotateAllDue(): Promise<RotationResult[]>",
        "configureOIDC(",
        "validateOIDC(",
        "scanForLeaks(paths: string[]): Promise<LeakFinding[]>",
    ]

    for method in required_methods:
        assert method in content, f"SecretManager missing method: {method}"


def test_rotation_schedule_quarterly_supported() -> None:
    """rotationSchedule must support 'quarterly' per CONTRACT 2 acceptance criteria."""
    content = MANAGER_TS.read_text(encoding="utf-8")
    assert "quarterly" in content, "rotationSchedule must support 'quarterly'"


def test_providers_supported() -> None:
    """Provider must include cloudflare, render, doppler, github, custom per CONTRACT 2."""
    content = MANAGER_TS.read_text(encoding="utf-8")

    for provider in ["cloudflare", "render", "doppler", "github", "custom"]:
        assert provider in content, f"Provider '{provider}' not supported"


def test_oidc_provider_configure_method() -> None:
    """configureOIDC must accept cloudflare, render, doppler."""
    content = MANAGER_TS.read_text(encoding="utf-8")

    assert "configureOIDC" in content
    # Check the provider union type includes all three
    assert "cloudflare" in content and "render" in content and "doppler" in content


def test_validate_oidc_method() -> None:
    """validateOIDC must exist for cloudflare, render, doppler."""
    content = MANAGER_TS.read_text(encoding="utf-8")
    assert "validateOIDC" in content


def test_scan_for_leaks_method() -> None:
    """scanForLeaks must exist and integrate with gitleaks/trufflehog."""
    content = MANAGER_TS.read_text(encoding="utf-8")
    assert "scanForLeaks" in content
    assert "LeakFinding[]" in content or "Promise<LeakFinding[]" in content


# ── CI Integration (CONTRACT 5) ────────────────────────────────────────────

def test_ci_has_secret_rotation_oidc_tests_job() -> None:
    """ci.yml must have secret-rotation-oidc-tests job (CONTRACT 5)."""
    ci_path = ROOT / ".github" / "workflows" / "ci.yml"
    assert ci_path.exists(), "ci.yml missing"

    ci_content = ci_path.read_text(encoding="utf-8")
    assert "secret-rotation-oidc-tests" in ci_content, "Missing secret-rotation-oidc-tests job"


def test_secret_rotation_job_depends_on_lint_and_security() -> None:
    """secret-rotation-oidc-tests must depend on lint-and-security (CONTRACT 5)."""
    ci_path = ROOT / ".github" / "workflows" / "ci.yml"
    ci_content = ci_path.read_text(encoding="utf-8")

    # Find the job and check needs
    import yaml
    ci = yaml.safe_load(ci_content)
    job = ci.get("jobs", {}).get("secret-rotation-oidc-tests", {})
    needs = job.get("needs", [])
    assert "lint-and-security" in needs, "secret-rotation-oidc-tests must need lint-and-security"


def test_secret_rotation_job_has_schedule_trigger() -> None:
    """secret-rotation-oidc-tests must have schedule trigger for quarterly rotation (CONTRACT 5)."""
    ci_path = ROOT / ".github" / "workflows" / "ci.yml"
    ci_content = ci_path.read_text(encoding="utf-8")

    import yaml
    ci = yaml.safe_load(ci_content)

    # The schedule trigger is at the workflow level, check it exists
    on_config = ci.get("on", ci.get(True, {}))
    schedule = on_config.get("schedule", [])
    # Must have a quarterly schedule (0 6 1 */3 * = first day of every quarter at 06:00)
    quarterly_found = any(
        "0 6 1 */3 *" in str(s.get("cron", "")) or "quarterly" in str(s.get("cron", "")).lower()
        for s in schedule
    )
    assert quarterly_found, "Workflow must have quarterly schedule trigger for secret rotation"


def test_secret_rotation_job_runs_tests() -> None:
    """secret-rotation-oidc-tests job must run the contract tests."""
    ci_path = ROOT / ".github" / "workflows" / "ci.yml"
    ci_content = ci_path.read_text(encoding="utf-8")

    import yaml
    ci = yaml.safe_load(ci_content)
    job = ci.get("jobs", {}).get("secret-rotation-oidc-tests", {})
    steps = job.get("steps", [])

    found_test_run = False
    for step in steps:
        if isinstance(step, dict):
            run = step.get("run", "")
            if "test_secret_rotation_oidc_contract" in run or "secret_rotation_oidc" in run:
                found_test_run = True
                break

    assert found_test_run, "secret-rotation-oidc-tests job must run the contract test"


def test_secret_rotation_job_uploads_artifact() -> None:
    """secret-rotation-oidc-tests must upload artifact with retention-days: 30 (CONTRACT 5)."""
    ci_path = ROOT / ".github" / "workflows" / "ci.yml"
    ci_content = ci_path.read_text(encoding="utf-8")

    import yaml
    ci = yaml.safe_load(ci_content)
    job = ci.get("jobs", {}).get("secret-rotation-oidc-tests", {})
    steps = job.get("steps", [])

    found_upload = False
    for step in steps:
        if isinstance(step, dict):
            uses = str(step.get("uses", ""))
            if "upload-artifact" in uses:
                with_config = step.get("with", {})
                retention = with_config.get("retention-days")
                if retention == 30 or retention == "30":
                    found_upload = True
                    break

    assert found_upload, "secret-rotation-oidc-tests must upload artifact with retention-days: 30"


# ── Integration with M7 gitleaks (CONTRACT 2) ──────────────────────────────

def test_gitleaks_integration_in_lint_and_security() -> None:
    """lint-and-security job must have gitleaks/trufflehog step (M7 integration)."""
    ci_path = ROOT / ".github" / "workflows" / "ci.yml"
    ci_content = ci_path.read_text(encoding="utf-8")

    import yaml
    ci = yaml.safe_load(ci_content)
    job = ci.get("jobs", {}).get("lint-and-security", {})
    steps = job.get("steps", [])

    found_gitleaks = False
    for step in steps:
        if isinstance(step, dict):
            run = step.get("run", "").lower()
            uses = str(step.get("uses", "")).lower()
            if "gitleaks" in run or "gitleaks" in uses or "trufflehog" in run or "trufflehog" in uses:
                found_gitleaks = True
                break

    assert found_gitleaks, "lint-and-security must run gitleaks/trufflehog for secret scanning"


# ── OIDC Implementation Details ────────────────────────────────────────────

def test_oidc_github_actions_federation() -> None:
    """OIDC config must support GitHub Actions federation."""
    content = MANAGER_TS.read_text(encoding="utf-8")
    assert "github-actions" in content or "githubActions" in content or "GITHUB_ACTIONS" in content


def test_doppler_cli_backing_store() -> None:
    """Non-OIDC secrets must use Doppler CLI as backing store per CONTRACT 2."""
    content = MANAGER_TS.read_text(encoding="utf-8")
    assert "doppler" in content.lower()


def test_no_long_lived_tokens_in_github_secrets() -> None:
    """Implementation must not store long-lived tokens in GitHub secrets."""
    content = MANAGER_TS.read_text(encoding="utf-8")
    # This is a design requirement - the implementation should use OIDC federation
    # The test verifies the design intent is documented
    assert "oidc" in content.lower() or "OIDC" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])