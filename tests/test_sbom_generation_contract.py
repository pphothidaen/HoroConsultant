"""Contract test: SBOM generation job in CI (KAN-300).

M12 of Phase 0 Foundation Hardening (KAN-290, Epic KAN-289).

Red Team CRITICAL-12: missing SBOM — software bill of materials must be
generated for supply chain transparency. CI MUST include a job that generates
an SBOM (CycloneDX/SPDX) on MEDIUM/STRICT tier changes and fails on
critical vulnerabilities (CVSS >= 7).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CI_YML = ROOT / ".github" / "workflows" / "ci.yml"


def _load(path: Path) -> dict:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(doc, dict)
    return doc


# ── ci.yml has sbom-generation job ───────────────────────────────────────


def test_ci_has_sbom_generation_job() -> None:
    ci = _load(CI_YML)
    jobs = ci.get("jobs", {})
    assert "sbom-generation" in jobs, (
        "ci.yml must have a 'sbom-generation' job (M12)"
    )
    job = jobs["sbom-generation"]
    assert job.get("runs-on") == "ubuntu-latest"
    assert "timeout-minutes" in job


def test_sbom_generation_runs_on_medium_strict_tier() -> None:
    ci = _load(CI_YML)
    job = ci.get("jobs", {}).get("sbom-generation", {})
    # Should run on MEDIUM or STRICT tier (dependency or source changes)
    if_condition = job.get("if", "")
    assert "MEDIUM" in if_condition or "STRICT" in if_condition or "medium" in if_condition.lower() or "strict" in if_condition.lower(), (
        "SBOM job must run on MEDIUM/STRICT tier changes (M12)"
    )


def test_sbom_generation_uses_cyclonedx_or_syft() -> None:
    ci = _load(CI_YML)
    job = ci.get("jobs", {}).get("sbom-generation", {})
    steps = job.get("steps", [])

    found_sbom_tool = False
    for step in steps:
        if isinstance(step, dict):
            run = step.get("run", "").lower()
            uses = str(step.get("uses", "")).lower()
            name = step.get("name", "").lower()
            if "cyclonedx" in run or "cyclonedx" in uses or "cyclonedx" in name:
                found_sbom_tool = True
                break
            if "syft" in run or "syft" in uses or "syft" in name:
                found_sbom_tool = True
                break
            if "pip-licenses" in run or "pip-licenses" in uses or "pip-licenses" in name:
                found_sbom_tool = True
                break

    assert found_sbom_tool, (
        "SBOM job must use cyclonedx-bom, syft, or pip-licenses (M12)"
    )


def test_sbom_generation_outputs_spdx_json_artifact() -> None:
    ci = _load(CI_YML)
    job = ci.get("jobs", {}).get("sbom-generation", {})
    steps = job.get("steps", [])

    found_upload = False
    for step in steps:
        if isinstance(step, dict):
            uses = str(step.get("uses", ""))
            if "upload-artifact" in uses:
                with_block = step.get("with", {})
                name = str(with_block.get("name", "")).lower()
                path = str(with_block.get("path", "")).lower()
                retention = with_block.get("retention-days")
                if ("sbom" in name or "bom" in name or "cyclonedx" in name or "spdx" in name) and (
                    ".json" in path or ".xml" in path or ".spdx" in path
                ):
                    assert retention == 90, "SBOM artifact must have retention-days: 90 (M12)"
                    found_upload = True
                    break

    assert found_upload, (
        "SBOM job must upload SPDX/JSON artifact with retention-days: 90 (M12)"
    )


def test_sbom_generation_fails_on_critical_vulns() -> None:
    ci = _load(CI_YML)
    job = ci.get("jobs", {}).get("sbom-generation", {})
    steps = job.get("steps", [])

    found_vuln_check = False
    for step in steps:
        if isinstance(step, dict):
            run = step.get("run", "")
            name = step.get("name", "").lower()
            if "vuln" in name or "vulnerab" in name or "cvss" in run or "critical" in run.lower():
                if "exit 1" in run or "fail" in run.lower():
                    found_vuln_check = True
                    break

    assert found_vuln_check, (
        "SBOM job must fail build when critical vulnerabilities (CVSS >= 7) found (M12)"
    )