#!/usr/bin/env python3
"""
Test suite for Phase 4 Security Scanning Enhancement (4B).

Tests cover:
- gitleaks custom rules for project-specific patterns
- SAST scanning (CodeQL / Semgrep) in CI
- Dependency vulnerability scanning (OSV / Dependabot alerts → auto-PR)
- Secret rotation verification in CI (M6 completion)
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestSecurityScanning:
    """Test cases for security scanning enhancements."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp(prefix="security_scan_test_")

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_sast_scan_script_exists(self):
        """Test that sast_scan.py script exists."""
        script_path = PROJECT_ROOT / "scripts" / "sast_scan.py"
        assert script_path.exists(), f"Script not found: {script_path}"

    def test_sast_scan_help(self):
        """Test that SAST scan script shows help."""
        script_path = PROJECT_ROOT / "scripts" / "sast_scan.py"
        result = subprocess.run([sys.executable, str(script_path), "--help"], capture_output=True, text=True)
        assert result.returncode == 0
        assert "sast" in result.stdout.lower() or "scan" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_dependency_scan_script_exists(self):
        """Test that dependency_scan.py script exists."""
        script_path = PROJECT_ROOT / "scripts" / "dependency_scan.py"
        assert script_path.exists(), f"Script not found: {script_path}"

    def test_dependency_scan_help(self):
        """Test that dependency scan script shows help."""
        script_path = PROJECT_ROOT / "scripts" / "dependency_scan.py"
        result = subprocess.run([sys.executable, str(script_path), "--help"], capture_output=True, text=True)
        assert result.returncode == 0
        assert "depend" in result.stdout.lower() or "scan" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_gitleaks_custom_rules(self):
        """Test gitleaks custom rules configuration."""
        from scripts.sast_scan import load_gitleaks_config

        config = load_gitleaks_config()

        # Should have base rules
        assert "rules" in config
        assert len(config["rules"]) > 0

        # Should have project-specific custom rules
        rule_ids = [r.get("id", "") for r in config["rules"]]
        custom_rules = [r for r in rule_ids if "horo" in r.lower() or "custom" in r.lower() or "project" in r.lower()]
        assert len(custom_rules) > 0, "Missing project-specific custom rules"

    def test_gitleaks_custom_rule_patterns(self):
        """Test that custom rules cover project-specific patterns."""
        from scripts.sast_scan import load_gitleaks_config

        config = load_gitleaks_config()

        # Check for patterns like: API keys, database URLs, internal tokens
        patterns = []
        for rule in config["rules"]:
            if "regex" in rule:
                patterns.append(rule["regex"])

        # Should detect common secret patterns
        pattern_text = " ".join(patterns)
        assert "api[_-]?key" in pattern_text.lower() or "apikey" in pattern_text.lower()
        assert "secret" in pattern_text.lower()
        assert "token" in pattern_text.lower()
        assert "password" in pattern_text.lower()

    def test_semgrep_rules_exist(self):
        """Test that Semgrep rules are configured."""
        from scripts.sast_scan import load_semgrep_config

        config = load_semgrep_config()

        assert "rules" in config
        assert len(config["rules"]) > 0

        # Should include security-relevant rules
        rule_ids = [r.get("id", "") for r in config["rules"]]
        security_rules = [r for r in rule_ids if any(kw in r.lower() for kw in ["security", "xss", "sqli", "crypto", "auth", "secret"])]
        assert len(security_rules) > 0, "Missing security-focused Semgrep rules"

    def test_sast_scan_execution(self):
        """Test SAST scan execution (dry-run)."""
        from scripts.sast_scan import run_sast_scan

        result = run_sast_scan(
            target_path=str(PROJECT_ROOT),
            tools=["semgrep"],  # Use semgrep as primary, gitleaks as secondary
            dry_run=True
        )

        assert "success" in result
        # In dry-run, should succeed or return expected structure
        assert result.get("dry_run") is True or result.get("success") is True

    def test_dependency_vulnerability_scan(self):
        """Test dependency vulnerability scanning."""
        from scripts.dependency_scan import scan_dependencies

        result = scan_dependencies(
            manifest_path=str(PROJECT_ROOT / "pyproject.toml"),
            ecosystem="pypi",
            dry_run=True
        )

        assert "success" in result
        assert "vulnerabilities" in result
        assert isinstance(result["vulnerabilities"], list)

    def test_osv_integration(self):
        """Test OSV (Open Source Vulnerabilities) API integration."""
        from scripts.dependency_scan import query_osv

        # Test with a known vulnerable package (mocked in dry-run)
        result = query_osv("requests", "2.25.0", ecosystem="PyPI", dry_run=True)

        assert "success" in result
        assert result.get("dry_run") is True or "vulnerabilities" in result

    def test_dependabot_alert_processing(self):
        """Test processing of Dependabot alerts to auto-PR."""
        from scripts.dependency_scan import process_dependabot_alerts

        alerts = [
            {
                "id": "GHSA-1234-5678-90ab",
                "package": "lodash",
                "current_version": "4.17.15",
                "fixed_version": "4.17.21",
                "severity": "high",
                "ecosystem": "npm"
            }
        ]

        result = process_dependabot_alerts(alerts, dry_run=True)

        assert result["success"] is True
        assert "prs_created" in result
        assert isinstance(result["prs_created"], list)

    def test_secret_rotation_verification(self):
        """Test secret rotation verification in CI."""
        from scripts.sast_scan import verify_secret_rotation

        result = verify_secret_rotation(
            secrets_list=["GITHUB_TOKEN", "DOCKER_HUB_TOKEN", "CLOUDFLARE_API_TOKEN"],
            rotation_period_days=90,
            dry_run=True
        )

        assert "success" in result
        assert "rotation_status" in result
        assert isinstance(result["rotation_status"], dict)

    def test_zero_critical_findings_gate(self):
        """Test that SAST scan fails on critical findings."""
        from scripts.sast_scan import evaluate_findings_gate

        # Critical findings should fail
        findings = [
            {"severity": "critical", "rule": "hardcoded-secret", "file": "config.py"},
            {"severity": "high", "rule": "sql-injection", "file": "db.py"},
        ]
        result = evaluate_findings_gate(findings, fail_on_critical=True)
        assert result["pass"] is False
        assert "critical" in str(result).lower()

        # No critical findings should pass
        findings_no_critical = [
            {"severity": "high", "rule": "sql-injection", "file": "db.py"},
            {"severity": "medium", "rule": "weak-crypto", "file": "crypto.py"},
        ]
        result = evaluate_findings_gate(findings_no_critical, fail_on_critical=True)
        assert result["pass"] is True

    def test_weekly_schedule_trigger(self):
        """Test weekly vulnerability scan schedule trigger."""
        from scripts.dependency_scan import should_run_weekly_scan

        # Should run on schedule (mocked cron check)
        assert should_run_weekly_scan(force=True) is True
        # Actual cron logic tested in CI, not here

    def test_auto_pr_creation_for_vulns(self):
        """Test automatic PR creation for dependency vulnerabilities."""
        from scripts.dependency_scan import create_vulnerability_pr

        vuln = {
            "package": "requests",
            "current_version": "2.25.0",
            "fixed_version": "2.28.0",
            "severity": "high",
            "cve": "CVE-2023-12345"
        }

        result = create_vulnerability_pr(vuln, dry_run=True)

        assert result["success"] is True
        assert "pr_number" in result or "dry_run" in result

    def test_gitleaks_baseline_compliance(self):
        """Test that gitleaks baseline is maintained."""
        from scripts.sast_scan import check_gitleaks_baseline

        result = check_gitleaks_baseline(
            baseline_path=str(PROJECT_ROOT / ".gitleaks-baseline"),
            dry_run=True
        )

        assert "success" in result
        assert "baseline_exists" in result


if __name__ == "__main__":
    # Run tests manually for quick verification
    test = TestSecurityScanning()
    test.setup_method()
    try:
        test.test_sast_scan_script_exists()
        print("✅ test_sast_scan_script_exists passed")
    except Exception as e:
        print(f"❌ test_sast_scan_script_exists failed: {e}")

    try:
        test.test_sast_scan_help()
        print("✅ test_sast_scan_help passed")
    except Exception as e:
        print(f"❌ test_sast_scan_help failed: {e}")

    try:
        test.test_dependency_scan_script_exists()
        print("✅ test_dependency_scan_script_exists passed")
    except Exception as e:
        print(f"❌ test_dependency_scan_script_exists failed: {e}")

    try:
        test.test_dependency_scan_help()
        print("✅ test_dependency_scan_help passed")
    except Exception as e:
        print(f"❌ test_dependency_scan_help failed: {e}")

    try:
        test.test_gitleaks_custom_rules()
        print("✅ test_gitleaks_custom_rules passed")
    except Exception as e:
        print(f"❌ test_gitleaks_custom_rules failed: {e}")

    try:
        test.test_gitleaks_custom_rule_patterns()
        print("✅ test_gitleaks_custom_rule_patterns passed")
    except Exception as e:
        print(f"❌ test_gitleaks_custom_rule_patterns failed: {e}")

    try:
        test.test_semgrep_rules_exist()
        print("✅ test_semgrep_rules_exist passed")
    except Exception as e:
        print(f"❌ test_semgrep_rules_exist failed: {e}")

    try:
        test.test_sast_scan_execution()
        print("✅ test_sast_scan_execution passed")
    except Exception as e:
        print(f"❌ test_sast_scan_execution failed: {e}")

    try:
        test.test_dependency_vulnerability_scan()
        print("✅ test_dependency_vulnerability_scan passed")
    except Exception as e:
        print(f"❌ test_dependency_vulnerability_scan failed: {e}")

    try:
        test.test_osv_integration()
        print("✅ test_osv_integration passed")
    except Exception as e:
        print(f"❌ test_osv_integration failed: {e}")

    try:
        test.test_dependabot_alert_processing()
        print("✅ test_dependabot_alert_processing passed")
    except Exception as e:
        print(f"❌ test_dependabot_alert_processing failed: {e}")

    try:
        test.test_secret_rotation_verification()
        print("✅ test_secret_rotation_verification passed")
    except Exception as e:
        print(f"❌ test_secret_rotation_verification failed: {e}")

    try:
        test.test_zero_critical_findings_gate()
        print("✅ test_zero_critical_findings_gate passed")
    except Exception as e:
        print(f"❌ test_zero_critical_findings_gate failed: {e}")

    try:
        test.test_weekly_schedule_trigger()
        print("✅ test_weekly_schedule_trigger passed")
    except Exception as e:
        print(f"❌ test_weekly_schedule_trigger failed: {e}")

    try:
        test.test_auto_pr_creation_for_vulns()
        print("✅ test_auto_pr_creation_for_vulns passed")
    except Exception as e:
        print(f"❌ test_auto_pr_creation_for_vulns failed: {e}")

    try:
        test.test_gitleaks_baseline_compliance()
        print("✅ test_gitleaks_baseline_compliance passed")
    except Exception as e:
        print(f"❌ test_gitleaks_baseline_compliance failed: {e}")

    test.teardown_method()
    print("\n🔴 RED PHASE: All tests should FAIL (scripts not implemented yet)")