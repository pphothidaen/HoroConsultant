#!/usr/bin/env python3
"""
Dependency Vulnerability Scan Script (4B).

Scans dependencies for known vulnerabilities using:
- OSV (Open Source Vulnerabilities) database
- GitHub Dependabot alerts
- Creates auto-PRs for vulnerable dependencies
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Vulnerability:
    """Represents a dependency vulnerability."""
    package: str
    current_version: str
    fixed_version: Optional[str]
    severity: str  # critical, high, medium, low
    cve: Optional[str] = None
    ghsa: Optional[str] = None
    ecosystem: str = "pypi"
    description: str = ""
    references: List[str] = None

    def __post_init__(self):
        if self.references is None:
            self.references = []


def parse_pyproject_toml(pyproject_path: Path) -> Dict[str, str]:
    """Parse pyproject.toml and extract dependencies."""
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            return {}

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    deps = {}

    # Project dependencies
    project = data.get("project", {})
    for dep in project.get("dependencies", []):
        # Parse "package>=1.0.0" format
        import re
        match = re.match(r"^([a-zA-Z0-9_-]+)([<>=!~]+.*)?$", dep)
        if match:
            name, version = match.groups()
            deps[name.lower()] = version or ""

    # Optional dependencies
    for extra_deps in data.get("project", {}).get("optional-dependencies", {}).values():
        for dep in extra_deps:
            import re
            match = re.match(r"^([a-zA-Z0-9_-]+)([<>=!~]+.*)?$", dep)
            if match:
                name, version = match.groups()
                deps[name.lower()] = version or ""

    # Tool dependencies (poetry, pdm, etc.)
    for tool in ("poetry", "pdm", "pipenv"):
        tool_deps = data.get("tool", {}).get(tool, {}).get("dependencies", {})
        if isinstance(tool_deps, dict):
            for name, spec in tool_deps.items():
                if name != "python":
                    deps[name.lower()] = str(spec) if not isinstance(spec, str) else spec

    return deps


def parse_package_json(package_json_path: Path) -> Dict[str, str]:
    """Parse package.json and extract dependencies."""
    with open(package_json_path) as f:
        data = json.load(f)

    deps = {}
    for dep_type in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        for name, version in data.get(dep_type, {}).items():
            deps[name.lower()] = version

    return deps


def parse_requirements_txt(req_path: Path) -> Dict[str, str]:
    """Parse requirements.txt and extract dependencies."""
    deps = {}
    with open(req_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                import re
                match = re.match(r"^([a-zA-Z0-9_-]+)([<>=!~]+.*)?$", line)
                if match:
                    name, version = match.groups()
                    deps[name.lower()] = version or ""
    return deps


def detect_manifest_files(repo_path: Path) -> List[Path]:
    """Detect dependency manifest files in the repository."""
    manifests = []
    for pattern in ["pyproject.toml", "package.json", "requirements.txt", "setup.py", "Pipfile", "poetry.lock", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"]:
        manifests.extend(repo_path.rglob(pattern))
    return manifests


def query_osv(
    package: str,
    version: str,
    ecosystem: str = "PyPI",
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Query OSV (Open Source Vulnerabilities) API for a package."""
    if dry_run:
        # Mock response for testing
        return {
            "success": True,
            "dry_run": True,
            "vulnerabilities": [
                {
                    "id": "GHSA-test-1234",
                    "summary": "Test vulnerability",
                    "severity": "HIGH",
                    "affected": [{"package": {"name": package}, "ranges": [{"type": "ECOSYSTEM", "events": [{"fixed": "2.0.0"}]}]}],
                }
            ] if package == "test-vulnerable-package" else [],
        }

    # Query OSV API
    url = "https://api.osv.dev/v1/query"
    payload = {
        "package": {"name": package, "ecosystem": ecosystem},
        "version": version,
    }

    try:
        import urllib.request
        import urllib.error

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            return {"success": True, "vulnerabilities": data.get("vulns", [])}
    except urllib.error.HTTPError as e:
        return {"success": False, "error": f"HTTP {e.code}: {e.reason}"}
    except urllib.error.URLError as e:
        return {"success": False, "error": f"Network error: {e.reason}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def parse_osv_vulnerabilities(osv_result: Dict[str, Any], package: str, current_version: str, ecosystem: str) -> List[Vulnerability]:
    """Parse OSV API response into Vulnerability objects."""
    vulns = []
    for vuln in osv_result.get("vulnerabilities", []):
        # Extract severity
        severity = "medium"
        for sev in vuln.get("severity", []):
            if sev.get("type") == "CVSS_V3":
                score = sev.get("score", "").upper()
                if score in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
                    severity = score.lower()
                    break

        # Extract fixed version
        fixed_version = None
        for affected in vuln.get("affected", []):
            for range_info in affected.get("ranges", []):
                for event in range_info.get("events", []):
                    if "fixed" in event:
                        fixed_version = event["fixed"]
                        break

        # Extract CVE/GHSA
        cve = None
        ghsa = None
        for alias in vuln.get("aliases", []):
            if alias.startswith("CVE-"):
                cve = alias
            elif alias.startswith("GHSA-"):
                ghsa = alias

        vulns.append(Vulnerability(
            package=package,
            current_version=current_version,
            fixed_version=fixed_version,
            severity=severity,
            cve=cve,
            ghsa=ghsa,
            ecosystem=ecosystem.lower(),
            description=vuln.get("summary", ""),
            references=[ref.get("url", "") for ref in vuln.get("references", []) if ref.get("url")],
        ))

    return vulns


def scan_dependencies(
    manifest_path: str,
    ecosystem: str = "pypi",
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Scan dependencies in a manifest file for vulnerabilities."""
    manifest = Path(manifest_path).resolve()

    if not manifest.exists():
        return {"success": False, "error": f"Manifest not found: {manifest_path}"}

    # Parse dependencies based on manifest type
    deps = {}
    if manifest.name == "pyproject.toml":
        deps = parse_pyproject_toml(manifest)
    elif manifest.name == "package.json":
        deps = parse_package_json(manifest)
    elif manifest.name == "requirements.txt":
        deps = parse_requirements_txt(manifest)
    else:
        return {"success": False, "error": f"Unsupported manifest: {manifest.name}"}

    if not deps:
        return {"success": True, "vulnerabilities": [], "message": "No dependencies found"}

    all_vulns = []
    scanned = 0

    # Map ecosystem
    ecosystem_map = {
        "pypi": "PyPI",
        "npm": "npm",
        "maven": "Maven",
        "go": "Go",
        "nuget": "NuGet",
        "rubygems": "RubyGems",
        "cargo": "crates.io",
    }
    osv_ecosystem = ecosystem_map.get(ecosystem.lower(), "PyPI")

    for package, version in deps.items():
        if not version or version in ("*", "latest"):
            continue

        osv_result = query_osv(package, version, osv_ecosystem, dry_run)
        if osv_result.get("success"):
            vulns = parse_osv_vulnerabilities(osv_result, package, version, ecosystem)
            all_vulns.extend(vulns)
            scanned += 1
        else:
            print(f"Warning: Failed to scan {package}@{version}: {osv_result.get('error')}", file=sys.stderr)

    return {
        "success": True,
        "manifest": str(manifest),
        "ecosystem": ecosystem,
        "dependencies_scanned": scanned,
        "vulnerabilities": [asdict(v) for v in all_vulns],
        "summary": {
            "total": len(all_vulns),
            "critical": len([v for v in all_vulns if v.severity == "critical"]),
            "high": len([v for v in all_vulns if v.severity == "high"]),
            "medium": len([v for v in all_vulns if v.severity == "medium"]),
            "low": len([v for v in all_vulns if v.severity == "low"]),
        },
    }


def process_dependabot_alerts(
    alerts: List[Dict[str, Any]],
    dry_run: bool = True,
) -> Dict[str, Any]:
    """Process Dependabot alerts and create auto-PRs for fixes."""
    prs_created = []

    for alert in alerts:
        package = alert.get("package", "")
        current = alert.get("current_version", "")
        fixed = alert.get("fixed_version", "")
        severity = alert.get("severity", "medium").lower()

        if not fixed:
            continue

        if dry_run:
            prs_created.append({
                "package": package,
                "current_version": current,
                "fixed_version": fixed,
                "severity": severity,
                "pr_number": "dry-run",
                "pr_url": "https://github.com/example/repo/pull/123",
            })
        else:
            # Real implementation would create PR via GitHub API
            # This is a placeholder for the actual implementation
            prs_created.append({
                "package": package,
                "current_version": current,
                "fixed_version": fixed,
                "severity": severity,
                "pr_number": None,
                "pr_url": None,
                "error": "Auto-PR creation not implemented",
            })

    return {
        "success": True,
        "alerts_processed": len(alerts),
        "prs_created": prs_created,
    }


def create_vulnerability_pr(
    vuln: Dict[str, Any],
    dry_run: bool = True,
) -> Dict[str, Any]:
    """Create a PR to fix a vulnerable dependency."""
    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "package": vuln.get("package"),
            "current_version": vuln.get("current_version"),
            "fixed_version": vuln.get("fixed_version"),
            "pr_number": "dry-run",
            "pr_url": "https://github.com/example/repo/pull/123",
        }

    # Real implementation would:
    # 1. Fork/clone repo
    # 2. Update dependency in manifest
    # 3. Run tests
    # 4. Create PR via GitHub API
    return {
        "success": False,
        "error": "Auto-PR creation not implemented in non-dry-run mode",
        "package": vuln.get("package"),
    }


def should_run_weekly_scan(force: bool = False) -> bool:
    """Check if weekly vulnerability scan should run."""
    if force:
        return True

    # Check if 7 days have passed since last scan
    # This would typically check a timestamp file or CI schedule
    # For now, always return True when forced
    return False


def main():
    parser = argparse.ArgumentParser(description="Scan dependencies for vulnerabilities")
    parser.add_argument("--manifest", help="Path to manifest file (pyproject.toml, package.json, etc.)")
    parser.add_argument("--repo", default=".", help="Repository root to scan for manifests")
    parser.add_argument("--ecosystem", default="pypi", help="Package ecosystem (pypi, npm, etc.)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run")
    parser.add_argument("--output", help="Output JSON file")
    parser.add_argument("--weekly", action="store_true", help="Run weekly scan")

    args = parser.parse_args()

    if args.weekly and not should_run_weekly_scan(force=False):
        print("Weekly scan not due")
        return 0

    # Find manifests to scan
    repo_path = Path(args.repo).resolve()
    if args.manifest:
        manifests = [Path(args.manifest).resolve()]
    else:
        manifests = detect_manifest_files(repo_path)

    if not manifests:
        print("No dependency manifests found")
        return 0

    all_results = []
    all_vulns = []

    for manifest in manifests:
        # Detect ecosystem from manifest
        if manifest.name == "package.json":
            ecosystem = "npm"
        elif manifest.name in ("pyproject.toml", "requirements.txt", "setup.py", "Pipfile", "poetry.lock"):
            ecosystem = "pypi"
        else:
            ecosystem = args.ecosystem

        result = scan_dependencies(str(manifest), ecosystem, args.dry_run)
        all_results.append(result)
        if result.get("success"):
            all_vulns.extend(result.get("vulnerabilities", []))

    # Aggregate results
    combined = {
        "success": all(r.get("success", False) for r in all_results),
        "manifests_scanned": len(manifests),
        "results": all_results,
        "vulnerabilities": all_vulns,
        "summary": {
            "total": len(all_vulns),
            "critical": len([v for v in all_vulns if v.get("severity") == "critical"]),
            "high": len([v for v in all_vulns if v.get("severity") == "high"]),
            "medium": len([v for v in all_vulns if v.get("severity") == "medium"]),
            "low": len([v for v in all_vulns if v.get("severity") == "low"]),
        },
    }

    if args.output:
        with open(args.output, "w") as f:
            json.dump(combined, f, indent=2)

    print(json.dumps(combined, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())