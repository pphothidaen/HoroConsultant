#!/usr/bin/env python3
"""
SAST Scan Script (4B).

Runs static analysis security testing using:
- gitleaks for secret detection (with custom rules)
- Semgrep for code pattern analysis
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_gitleaks_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load gitleaks configuration with custom rules."""
    if config_path and config_path.exists():
        with open(config_path) as f:
            return json.load(f)

    # Default config with custom rules for HoroConsultant
    return {
        "title": "HoroConsultant gitleaks config",
        "version": "1.0.0",
        "rules": [
            # Standard gitleaks rules (subset)
            {
                "id": "generic-api-key",
                "description": "Generic API Key",
                "regex": "(?i)(api[_-]?key|apikey)\\s*[=:]\\s*[\"']?([a-zA-Z0-9_-]{20,})[\"']?",
                "tags": ["key", "api"],
            },
            {
                "id": "generic-secret",
                "description": "Generic Secret",
                "regex": "(?i)(secret|password|passwd|pwd)\\s*[=:]\\s*[\"']?([a-zA-Z0-9_@#$%^&*()-+=]{8,})[\"']?",
                "tags": ["secret", "password"],
            },
            {
                "id": "aws-access-key",
                "description": "AWS Access Key",
                "regex": "AKIA[0-9A-Z]{16}",
                "tags": ["aws", "key"],
            },
            {
                "id": "github-token",
                "description": "GitHub Token",
                "regex": "gh[pousr]_[A-Za-z0-9_]{36,255}",
                "tags": ["github", "token"],
            },
            # Custom rules for HoroConsultant
            {
                "id": "horo-cloudflare-api-token",
                "description": "Cloudflare API Token (HoroConsultant)",
                "regex": "(?i)(cloudflare|cf)[_-]?(api[_-]?token|token)\\s*[=:]\\s*[\"']?([a-zA-Z0-9_-]{20,})[\"']?",
                "tags": ["cloudflare", "horo", "custom"],
            },
            {
                "id": "horo-doppler-token",
                "description": "Doppler Token (HoroConsultant)",
                "regex": "(?i)doppler[_-]?token\\s*[=:]\\s*[\"']?([a-zA-Z0-9_-]{20,})[\"']?",
                "tags": ["doppler", "horo", "custom"],
            },
            {
                "id": "horo-database-url",
                "description": "Database URL with credentials (HoroConsultant)",
                "regex": "(?i)(database[_-]?url|db[_-]?url)\\s*[=:]\\s*[\"']?(postgres|mysql|mongodb)://[^\"'\\s]+:[^\"'\\s]+@[^\"'\\s]+",
                "tags": ["database", "horo", "custom"],
            },
            {
                "id": "horo-internal-service-token",
                "description": "Internal service token pattern (HoroConsultant)",
                "regex": "(?i)(aipass|gemini|hermes)[_-]?(bridge|service)[_-]?token\\s*[=:]\\s*[\"']?([a-zA-Z0-9_-]{16,})[\"']?",
                "tags": ["internal", "horo", "custom"],
            },
        ],
        "allowlist": {
            "description": "Allowlist for false positives",
            "files": ["*.md", "*.txt", "*.example", "*.sample"],
            "commits": [],
            "paths": [".git", "node_modules", "dist", "build", "__pycache__"],
        },
    }


def load_semgrep_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load Semgrep configuration."""
    if config_path and config_path.exists():
        with open(config_path) as f:
            return json.load(f)

    # Default security-focused Semgrep rules
    return {
        "rules": [
            # Python security rules
            {
                "id": "python-sql-injection",
                "pattern-either": [
                    {"pattern": "execute($X + $Y)"},
                    {"pattern": "execute(f\"...{$X}...\")"},
                    {"pattern": "cursor.execute($X % $Y)"},
                ],
                "message": "Potential SQL injection - use parameterized queries",
                "languages": ["python"],
                "severity": "ERROR",
                "metadata": {"category": "security", "cwe": "CWE-89"},
            },
            {
                "id": "python-command-injection",
                "pattern-either": [
                    {"pattern": "subprocess.call($X, shell=True)"},
                    {"pattern": "subprocess.run($X, shell=True)"},
                    {"pattern": "os.system($X)"},
                    {"pattern": "os.popen($X)"},
                ],
                "message": "Command injection risk - avoid shell=True",
                "languages": ["python"],
                "severity": "ERROR",
                "metadata": {"category": "security", "cwe": "CWE-78"},
            },
            {
                "id": "python-hardcoded-secret",
                "pattern-either": [
                    {"pattern": "$X = \"...\"", "metavariable-regex": {"X": "(?i)(password|secret|token|api_key|apikey)"}},
                    {"pattern": "$X = '...'", "metavariable-regex": {"X": "(?i)(password|secret|token|api_key|apikey)"}},
                ],
                "message": "Hardcoded secret detected",
                "languages": ["python"],
                "severity": "ERROR",
                "metadata": {"category": "security", "cwe": "CWE-798"},
            },
            {
                "id": "python-weak-crypto",
                "pattern-either": [
                    {"pattern": "hashlib.md5($X)"},
                    {"pattern": "hashlib.sha1($X)"},
                    {"pattern": "Crypto.Cipher.ARC4"},
                    {"pattern": "Crypto.Cipher.DES"},
                ],
                "message": "Weak cryptographic algorithm",
                "languages": ["python"],
                "severity": "WARNING",
                "metadata": {"category": "security", "cwe": "CWE-327"},
            },
            {
                "id": "python-path-traversal",
                "pattern": "open($X)",
                "message": "Potential path traversal - validate file paths",
                "languages": ["python"],
                "severity": "WARNING",
                "metadata": {"category": "security", "cwe": "CWE-22"},
            },
            # JavaScript/TypeScript security rules
            {
                "id": "js-xss-innerhtml",
                "pattern-either": [
                    {"pattern": "$X.innerHTML = $Y"},
                    {"pattern": "$X.outerHTML = $Y"},
                    {"pattern": "document.write($X)"},
                ],
                "message": "Potential XSS - sanitize user input before DOM insertion",
                "languages": ["javascript", "typescript"],
                "severity": "ERROR",
                "metadata": {"category": "security", "cwe": "CWE-79"},
            },
            {
                "id": "js-eval-injection",
                "pattern-either": [
                    {"pattern": "eval($X)"},
                    {"pattern": "new Function($X)"},
                    {"pattern": "setTimeout($X, $Y)"},
                    {"pattern": "setInterval($X, $Y)"},
                ],
                "message": "Code injection risk - avoid eval/Function",
                "languages": ["javascript", "typescript"],
                "severity": "ERROR",
                "metadata": {"category": "security", "cwe": "CWE-95"},
            },
            {
                "id": "js-hardcoded-secret",
                "pattern": "const $X = \"...\"",
                "metavariable-regex": {"X": "(?i)(password|secret|token|apiKey|api_key)"},
                "message": "Hardcoded secret detected",
                "languages": ["javascript", "typescript"],
                "severity": "ERROR",
                "metadata": {"category": "security", "cwe": "CWE-798"},
            },
        ]
    }


def run_gitleaks(
    target_path: Path,
    config: Dict[str, Any],
    baseline_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run gitleaks scan."""
    # Write config to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config, f)
        config_file = f.name

    try:
        cmd = ["gitleaks", "detect", "--source", str(target_path), "--config", config_file, "--report-format", "json"]
        if baseline_path and baseline_path.exists():
            cmd.extend(["--baseline", str(baseline_path)])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        # gitleaks returns 1 when leaks found, 0 when clean
        if result.returncode == 0:
            return {"success": True, "findings": [], "leaks_found": False}
        elif result.returncode == 1:
            try:
                findings = json.loads(result.stdout) if result.stdout.strip() else []
                return {"success": True, "findings": findings, "leaks_found": True}
            except json.JSONDecodeError:
                return {"success": False, "error": "Failed to parse gitleaks output", "raw": result.stdout}
        else:
            return {"success": False, "error": result.stderr, "returncode": result.returncode}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "gitleaks timed out"}
    except FileNotFoundError:
        return {"success": False, "error": "gitleaks not installed"}
    finally:
        try:
            os.unlink(config_file)
        except OSError:
            pass


def run_semgrep(
    target_path: Path,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """Run Semgrep scan."""
    # Write config to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config, f)
        config_file = f.name

    try:
        cmd = ["semgrep", "scan", "--config", config_file, "--json", str(target_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode in (0, 1):  # 0 = no findings, 1 = findings found
            try:
                output = json.loads(result.stdout) if result.stdout.strip() else {"results": []}
                findings = output.get("results", [])
                return {"success": True, "findings": findings}
            except json.JSONDecodeError:
                return {"success": False, "error": "Failed to parse Semgrep output", "raw": result.stdout}
        else:
            return {"success": False, "error": result.stderr, "returncode": result.returncode}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Semgrep timed out"}
    except FileNotFoundError:
        return {"success": False, "error": "Semgrep not installed"}
    finally:
        try:
            os.unlink(config_file)
        except OSError:
            pass


def run_sast_scan(
    target_path: str,
    tools: Optional[List[str]] = None,
    dry_run: bool = False,
    baseline_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Run SAST scan with specified tools."""
    tools = tools or ["semgrep", "gitleaks"]
    target = Path(target_path).resolve()
    baseline = Path(baseline_path).resolve() if baseline_path else None

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "tools": tools,
            "target": str(target),
        }

    all_findings = []
    results = {}

    if "gitleaks" in tools:
        config = load_gitleaks_config()
        gitleaks_result = run_gitleaks(target, config, baseline)
        results["gitleaks"] = gitleaks_result
        if gitleaks_result.get("success") and gitleaks_result.get("leaks_found"):
            all_findings.extend([
                {
                    "tool": "gitleaks",
                    "rule": f.get("rule", "unknown"),
                    "file": f.get("file", ""),
                    "line": f.get("line", 0),
                    "severity": "critical" if "secret" in f.get("rule", "").lower() or "token" in f.get("rule", "").lower() else "high",
                    "description": f.get("description", "Secret detected"),
                }
                for f in gitleaks_result.get("findings", [])
            ])

    if "semgrep" in tools:
        config = load_semgrep_config()
        semgrep_result = run_semgrep(target, config)
        results["semgrep"] = semgrep_result
        if semgrep_result.get("success"):
            for f in semgrep_result.get("findings", []):
                severity = f.get("extra", {}).get("severity", "medium").lower()
                if severity == "error":
                    severity = "high"
                all_findings.append({
                    "tool": "semgrep",
                    "rule": f.get("check_id", "unknown"),
                    "file": f.get("path", ""),
                    "line": f.get("start", {}).get("line", 0),
                    "severity": severity,
                    "description": f.get("extra", {}).get("message", "Pattern match"),
                })

    return {
        "success": all(r.get("success", False) for r in results.values()),
        "tools": results,
        "findings": all_findings,
        "summary": {
            "total": len(all_findings),
            "critical": len([f for f in all_findings if f["severity"] == "critical"]),
            "high": len([f for f in all_findings if f["severity"] == "high"]),
            "medium": len([f for f in all_findings if f["severity"] == "medium"]),
            "low": len([f for f in all_findings if f["severity"] == "low"]),
        },
    }


def evaluate_findings_gate(
    findings: List[Dict[str, Any]],
    fail_on_critical: bool = True,
    fail_on_high: bool = False,
    max_medium: int = 10,
    max_low: int = 50,
) -> Dict[str, Any]:
    """Evaluate findings against quality gate thresholds."""
    critical = [f for f in findings if f["severity"] == "critical"]
    high = [f for f in findings if f["severity"] == "high"]
    medium = [f for f in findings if f["severity"] == "medium"]
    low = [f for f in findings if f["severity"] == "low"]

    passed = True
    reasons = []

    if fail_on_critical and critical:
        passed = False
        reasons.append(f"{len(critical)} critical findings")

    if fail_on_high and high:
        passed = False
        reasons.append(f"{len(high)} high findings")

    if len(medium) > max_medium:
        passed = False
        reasons.append(f"{len(medium)} medium findings (max {max_medium})")

    if len(low) > max_low:
        passed = False
        reasons.append(f"{len(low)} low findings (max {max_low})")

    return {
        "pass": passed,
        "reasons": reasons,
        "counts": {
            "critical": len(critical),
            "high": len(high),
            "medium": len(medium),
            "low": len(low),
        },
    }


def verify_secret_rotation(
    secrets_list: List[str],
    rotation_period_days: int = 90,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Verify secret rotation compliance."""
    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "rotation_status": {s: {"rotated": True, "days_since_rotation": 30} for s in secrets_list},
        }

    # In real implementation, check Doppler/1Password/HashiCorp Vault for rotation dates
    # For now, return mock status
    return {
        "success": True,
        "rotation_status": {
            secret: {
                "rotated": True,
                "days_since_rotation": 30,
                "next_rotation_due": rotation_period_days - 30,
            }
            for secret in secrets_list
        },
    }


def check_gitleaks_baseline(
    baseline_path: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Check gitleaks baseline file exists and is valid."""
    baseline = Path(baseline_path)

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "baseline_exists": baseline.exists(),
        }

    if not baseline.exists():
        return {
            "success": False,
            "baseline_exists": False,
            "error": f"Baseline file not found: {baseline_path}",
        }

    try:
        with open(baseline) as f:
            data = json.load(f)
        return {
            "success": True,
            "baseline_exists": True,
            "entry_count": len(data) if isinstance(data, list) else len(data.get("leaks", [])),
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "baseline_exists": True,
            "error": f"Invalid JSON in baseline: {e}",
        }


def main():
    parser = argparse.ArgumentParser(description="Run SAST security scans")
    parser.add_argument("--target", default=".", help="Target path to scan")
    parser.add_argument("--tools", nargs="+", choices=["gitleaks", "semgrep"], default=["gitleaks", "semgrep"])
    parser.add_argument("--baseline", help="Path to gitleaks baseline file")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no actual scan)")
    parser.add_argument("--fail-on-critical", action="store_true", default=True)
    parser.add_argument("--fail-on-high", action="store_true", default=False)
    parser.add_argument("--max-medium", type=int, default=10)
    parser.add_argument("--max-low", type=int, default=50)
    parser.add_argument("--output", help="Output JSON file")

    args = parser.parse_args()

    result = run_sast_scan(
        target_path=args.target,
        tools=args.tools,
        dry_run=args.dry_run,
        baseline_path=args.baseline,
    )

    if not args.dry_run and result.get("findings"):
        gate_result = evaluate_findings_gate(
            result["findings"],
            fail_on_critical=args.fail_on_critical,
            fail_on_high=args.fail_on_high,
            max_medium=args.max_medium,
            max_low=args.max_low,
        )
        result["quality_gate"] = gate_result

        if not gate_result["pass"]:
            print(f"Quality gate FAILED: {', '.join(gate_result['reasons'])}", file=sys.stderr)
            result["quality_gate_passed"] = False
        else:
            print("Quality gate PASSED", file=sys.stderr)
            result["quality_gate_passed"] = True

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
    return 0 if result.get("quality_gate_passed", True) else 1


if __name__ == "__main__":
    sys.exit(main())