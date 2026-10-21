#!/usr/bin/env python3
"""Contract test for DPIA Retention & PII Scrubbing (KAN-304).

Asserts:
1. All upload-artifact steps have retention-days
2. DPA.md exists with required sections
3. PII patterns detected and redacted in test fixtures
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def find_workflow_files() -> list[Path]:
    """Find all GitHub workflow YAML files."""
    workflows_dir = Path(".github/workflows")
    return list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))


def test_all_upload_artifacts_have_retention_days() -> tuple[bool, list[str]]:
    """Test that all actions/upload-artifact steps declare retention-days."""
    workflow_files = find_workflow_files()
    violations = []

    for wf_file in workflow_files:
        content = wf_file.read_text(encoding="utf-8")
        lines = content.splitlines()

        in_upload_step = False
        step_indent = 0
        has_retention = False
        step_name = ""

        for i, line in enumerate(lines):
            stripped = line.lstrip()
            indent = len(line) - len(stripped)

            # Detect upload-artifact step start
            if "uses: actions/upload-artifact" in stripped:
                in_upload_step = True
                step_indent = indent
                has_retention = False
                # Look back for step name
                for j in range(i - 1, -1, -1):
                    if lines[j].lstrip().startswith("name:"):
                        step_name = lines[j].lstrip()[5:].strip()
                        break
                continue

            # If we're in an upload step, check for retention-days
            if in_upload_step:
                if stripped.startswith("retention-days:"):
                    has_retention = True
                # Check if we've left the upload step (same or less indent, not continuation)
                if indent <= step_indent and not stripped.startswith(("#", "-")) and i > 0:
                    if "uses:" in stripped:
                        # New step started
                        in_upload_step = False
                    elif not stripped:
                        # Empty line, continue
                        continue
                    elif indent <= step_indent:
                        # Left the step
                        in_upload_step = False

            # Check at end of step
            if in_upload_step and indent <= step_indent and "uses:" in stripped and "upload-artifact" not in stripped:
                in_upload_step = False

        # Also check if the step ended at file end
        if in_upload_step and not has_retention:
            violations.append(f"{wf_file}: upload-artifact step '{step_name}' missing retention-days")

    return len(violations) == 0, violations


def test_dpa_exists_with_required_sections() -> tuple[bool, list[str]]:
    """Test that DPA.md exists and has required sections."""
    dpa_path = Path("docs/governance/DPA.md")
    violations = []

    if not dpa_path.exists():
        violations.append(f"DPA.md not found at {dpa_path}")
        return False, violations

    content = dpa_path.read_text(encoding="utf-8")
    required_sections = [
        "Purpose",
        "Scope",
        "Controller & Processor Details",
        "Vendor DPA Register",
        "Standard Contractual Clauses",
        "Data Subject Rights Fulfillment",
        "Technical & Organizational Measures",
        "Incident Response & Breach Notification",
        "Audit & Compliance",
        "Appendices",
    ]

    for section in required_sections:
        if section not in content:
            violations.append(f"DPA.md missing required section: {section}")

    # Check for vendor register entries
    required_vendors = [
        "Cloudflare",
        "AIPASS",
        "Google",
        "GitHub",
        "Render",
        "Vercel",
        "Kaggle",
    ]

    for vendor in required_vendors:
        if vendor not in content:
            violations.append(f"DPA.md missing vendor entry: {vendor}")

    return len(violations) == 0, violations


def test_pii_patterns_detected_and_redacted() -> tuple[bool, list[str]]:
    """Test that PII scrubbing detects and redacts patterns correctly."""
    violations = []

    # Test fixture
    fixture_path = Path("tests/fixtures/pii_test_data.json")
    allowlist_path = Path("tests/fixtures/pii_test_data.json.pii-allowlist")

    if not fixture_path.exists():
        violations.append(f"Test fixture not found: {fixture_path}")
        return False, violations

    if not allowlist_path.exists():
        violations.append(f"Allowlist not found: {allowlist_path}")
        return False, violations

    # Run pii_scrub on fixture with allowlist
    result = subprocess.run(
        [
            sys.executable,
            "scripts/pii_scrub.py",
            str(fixture_path),
            "--allowlist",
            str(allowlist_path),
            "--verbose",
            "--summary",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        violations.append(f"PII scrubbing failed: {result.stderr}")
        return False, violations

    # Verify no redactions occurred due to allowlist
    # Check for actual redaction markers in output, not summary text
    if "[EMAIL_REDACTED]" in result.stdout or "[OPENAI_KEY_REDACTED]" in result.stdout or "[GITHUB_KEY_REDACTED]" in result.stdout or "[GITLAB_KEY_REDACTED]" in result.stdout or "[JWT_REDACTED]" in result.stdout or "[CREDIT_CARD_REDACTED]" in result.stdout or "[SSN_REDACTED]" in result.stdout or "[CF_RAY_REDACTED]" in result.stdout or "[CF_IP_REDACTED]" in result.stdout:
        violations.append("PII was redacted despite allowlist")

    # Now test WITHOUT allowlist - should redact
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(fixture_path.read_text())
        temp_fixture = f.name

    try:
        result_no_allowlist = subprocess.run(
            [
                sys.executable,
                "scripts/pii_scrub.py",
                temp_fixture,
                "--verbose",
                "--summary",
            ],
            capture_output=True,
            text=True,
        )

        if result_no_allowlist.returncode != 0:
            violations.append(f"PII scrubbing without allowlist failed: {result_no_allowlist.stderr}")
            return False, violations

        # Verify redactions occurred
        expected_redactions = ["[EMAIL_REDACTED]", "[OPENAI_KEY_REDACTED]", "[GITHUB_KEY_REDACTED]",
                               "[GITLAB_KEY_REDACTED]", "[JWT_REDACTED]", "[CREDIT_CARD_REDACTED]",
                               "[SSN_REDACTED]", "[CF_RAY_REDACTED]", "[CF_IP_REDACTED]"]

        combined_output = result_no_allowlist.stdout + result_no_allowlist.stderr

        for redaction in expected_redactions:
            if redaction not in combined_output:
                violations.append(f"Expected redaction not found: {redaction}")

    finally:
        os.unlink(temp_fixture)

    return len(violations) == 0, violations


def test_pii_scrub_integration_in_ci() -> tuple[bool, list[str]]:
    """Test that pii_scrub is called before upload-artifact in CI workflows."""
    violations = []
    workflow_files = find_workflow_files()

    for wf_file in workflow_files:
        content = wf_file.read_text(encoding="utf-8")

        # Find all upload-artifact steps
        upload_steps = list(re.finditer(r"- name: Upload.*?uses: actions/upload-artifact", content, re.DOTALL))

        for match in upload_steps:
            step_content = match.group(0)
            # Check if there's a pii_scrub step before this upload
            before_upload = content[:match.start()]
            # Look for pii_scrub in the last few steps before upload
            if "pii_scrub" not in before_upload[-2000:]:
                # Extract step name for error message
                name_match = re.search(r"- name: (.*?)\n", step_content)
                step_name = name_match.group(1) if name_match else "unknown"
                violations.append(f"{wf_file}: upload step '{step_name}' may not have preceding PII scrub step")

    return len(violations) == 0, violations


def test_cloudflare_worker_monitor_has_scrub_logs() -> tuple[bool, list[str]]:
    """Test that cloudflare_worker_monitor.py has --scrub-logs mode."""
    violations = []
    monitor_path = Path("scripts/cloudflare_worker_monitor.py")

    if not monitor_path.exists():
        violations.append(f"cloudflare_worker_monitor.py not found")
        return False, violations

    content = monitor_path.read_text(encoding="utf-8")

    if "--scrub-logs" not in content:
        violations.append("cloudflare_worker_monitor.py missing --scrub-logs argument")

    if "scrub_stdin" not in content:
        violations.append("cloudflare_worker_monitor.py missing scrub_stdin import/call")

    if "from scripts.pii_scrub import scrub_stdin" not in content:
        violations.append("cloudflare_worker_monitor.py not importing scrub_stdin from pii_scrub")

    return len(violations) == 0, violations


def main() -> int:
    """Run all contract tests."""
    all_passed = True
    all_violations = []

    tests = [
        ("All upload-artifact steps have retention-days", test_all_upload_artifacts_have_retention_days),
        ("DPA.md exists with required sections", test_dpa_exists_with_required_sections),
        ("PII patterns detected and redacted", test_pii_patterns_detected_and_redacted),
        ("PII scrubbing integrated in CI workflows", test_pii_scrub_integration_in_ci),
        ("Cloudflare worker monitor has --scrub-logs", test_cloudflare_worker_monitor_has_scrub_logs),
    ]

    for test_name, test_func in tests:
        print(f"\n[TEST] {test_name}...")
        passed, violations = test_func()
        if passed:
            print(f"[PASS] {test_name}")
        else:
            print(f"[FAIL] {test_name}")
            for v in violations:
                print(f"  - {v}")
            all_passed = False
            all_violations.extend(violations)

    print("\n" + "=" * 60)
    if all_passed:
        print("ALL CONTRACT TESTS PASSED")
        return 0
    else:
        print(f"CONTRACT TESTS FAILED: {len(all_violations)} violations")
        return 1


if __name__ == "__main__":
    sys.exit(main())