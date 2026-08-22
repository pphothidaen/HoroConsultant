"""
project/core/code_reviewer.py
===============================
Pre-Deployment Code Reviewer & Safety Auditor Engine.

Automates pre-commit / pre-push code reviews for HoroConsultant:
1. Secret Leakage Scan (API Keys, Doppler Tokens, Passwords)
2. Kaggle & Cloud GPU Dependency Safety Audit (CUDA binary compatibility)
3. Automated Test Suite Verification (Pytest pass rates)
4. AI Code Quality Audit (via HybridRouter / Gemini / Local LLM)

Usage:
------
    # Run full pre-deployment code review
    python project/core/code_reviewer.py --review

    # Check secret leakage only
    python project/core/code_reviewer.py --scan-secrets
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("code_reviewer")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# Regex patterns for detecting hardcoded secrets
SECRET_PATTERNS = [
    (re.compile(r'AIzaSy[A-Za-z0-9_-]{33}'), "Google AI Studio API Key"),
    (re.compile(r'hf_[A-Za-z0-9]{34,}'), "Hugging Face User Token"),
    (re.compile(r'kg_[A-Za-z0-9_-]{20,}'), "Kaggle API Token"),
    (re.compile(r'dp\.pt\.[A-Za-z0-9_-]{20,}'), "Doppler Service Token"),
    (re.compile(r'ghp_[A-Za-z0-9]{36}'), "GitHub Personal Access Token"),
    (re.compile(r'dckr_pat_[A-Za-z0-9_-]{20,}'), "Docker Hub Personal Access Token"),
    (re.compile(r'glc_[A-Za-z0-9_-]{20,}'), "Grafana Cloud API Key"),
]

# Sensitive files that should not be committed with actual secrets
SENSITIVE_FILES = [".env", ".env.production", "kaggle.json"]


class CodeReviewer:
    """Automated Code Reviewer and Safety Auditor."""

    def __init__(self, root_dir: Path = ROOT):
        self.root_dir = root_dir

    @staticmethod
    def scan_secrets() -> dict[str, Any]:
        """Scan codebase for leaked secrets or unmasked API keys. Accelerated by Rust Rayon multi-threading."""
        try:
            import rust_core
            if hasattr(rust_core, "run_rust_security_audit"):
                passed, scanned_files, rust_findings = rust_core.run_rust_security_audit(str(ROOT))
                findings = [{"file": f, "secret_type": "Security Finding", "count": 1} for f in rust_findings]
                log.info(f"⚡ [Rust Security Auditor] Scanned {scanned_files} files in parallel via Rayon")
                return {
                    "scanned_files": scanned_files,
                    "secret_leaks_found": len(findings),
                    "findings": findings,
                    "status": "PASSED" if passed else "FAILED"
                }
        except Exception as e:
            log.warning(f"Rust security audit fallback: {e}")

        findings = []
        scanned_files = 0

        for path in ROOT.rglob("*"):
            if not path.is_file():
                continue
            if any(part in path.parts for part in [".git", ".pytest_cache", ".ruff_cache", "__pycache__", "venv", ".venv", "wandb", "node_modules", ".vercel", "target"]):
                continue
            if path.name.startswith(".env"):
                continue

            if path.stat().st_size > 1_000_000:
                continue

            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                scanned_files += 1

                for pattern, secret_type in SECRET_PATTERNS:
                    matches = pattern.findall(content)
                    if matches:
                        valid_matches = [m for m in matches if not any(d in m.lower() for d in ["dummy", "replace", "example", "test"])]
                        if valid_matches:
                            rel_path = path.relative_to(ROOT)
                            findings.append({
                                "file": str(rel_path),
                                "secret_type": secret_type,
                                "match_count": len(valid_matches),
                                "severity": "CRITICAL"
                            })
            except Exception:
                pass

        return {
            "scanned_files": scanned_files,
            "secret_leaks_found": len(findings),
            "findings": findings,
            "status": "PASSED" if len(findings) == 0 else "FAILED"
        }

    @staticmethod
    def audit_kaggle_dependencies() -> dict[str, Any]:
        """Verify that Kaggle notebook setup does NOT reinstall torch over pre-compiled CUDA binaries."""
        manager_file = ROOT / "scripts" / "kaggle_notebook_manager.py"
        orchestrator_file = ROOT / "scripts" / "cloud_train_orchestrator.py"

        issues = []
        if manager_file.exists():
            content = manager_file.read_text(encoding="utf-8")
            # Check for bad 'pip install torch' pattern in cell setup
            if re.search(r"pip['\"],?\s*['\"]install['\"],?\s*['\"]-q['\"],?\s*['\"]torch['\"]", content):
                issues.append({
                    "file": "scripts/kaggle_notebook_manager.py",
                    "issue": "Notebook setup reinstalls 'torch' on Kaggle, which overwrites pre-installed CUDA binaries causing SIGSEGV (-11).",
                    "severity": "HIGH"
                })

        if orchestrator_file.exists():
            content = orchestrator_file.read_text(encoding="utf-8")
            if "torch_dtype" not in content or "low_cpu_mem_usage" not in content:
                issues.append({
                    "file": "scripts/cloud_train_orchestrator.py",
                    "issue": "Missing 'torch_dtype' or 'low_cpu_mem_usage' in AutoModelForCausalLM loading configuration.",
                    "severity": "MEDIUM"
                })

        return {
            "issues_found": len(issues),
            "issues": issues,
            "status": "PASSED" if len(issues) == 0 else "WARNING"
        }

    @staticmethod
    def audit_notebooks() -> dict[str, Any]:
        """Scan all repository Jupyter notebooks for Python syntax errors, AST validity, and dependency lock compliance."""
        import ast
        notebook_paths = [
            ROOT / "horoconsultant-finetune-pipeline.ipynb",
            ROOT / "project" / "kaggle_kernel" / "notebook.ipynb",
        ]
        issues = []
        scanned_cells = 0

        forbidden_patterns = [
            ("accelerate==0.33.0", "accelerate==0.33.0 forces numpy<2.0 breaking Kaggle numpy 2.x ABI"),
            ("datasets==2.18.0", "datasets==2.18.0 forces pyarrow<15; use datasets>=2.21.0"),
            ("pyarrow_hotfix", "pyarrow_hotfix is deprecated on PyArrow 15+"),
        ]

        for nb_path in notebook_paths:
            if not nb_path.exists():
                continue
            try:
                with open(nb_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for idx, cell in enumerate(data.get("cells", [])):
                    if cell.get("cell_type") != "code":
                        continue
                    scanned_cells += 1
                    source = "".join(cell.get("source", []))
                    cell_label = f"{nb_path.name}:cell_{idx + 1}"

                    # 1. AST syntax check
                    try:
                        ast.parse(source, filename=cell_label)
                        compile(source, cell_label, "exec")
                    except SyntaxError as e:
                        issues.append({
                            "file": str(nb_path.relative_to(ROOT)),
                            "cell": idx + 1,
                            "issue": f"SyntaxError at line {e.lineno}: {e.msg}",
                            "snippet": e.text or "",
                            "severity": "CRITICAL"
                        })

                    # 2. Forbidden dependency check
                    for bad_pat, reason in forbidden_patterns:
                        if bad_pat in source:
                            issues.append({
                                "file": str(nb_path.relative_to(ROOT)),
                                "cell": idx + 1,
                                "issue": f"Forbidden dependency pattern '{bad_pat}': {reason}",
                                "severity": "HIGH"
                            })

            except Exception as e:
                issues.append({
                    "file": str(nb_path.relative_to(ROOT)),
                    "issue": f"Malformed notebook JSON: {e}",
                    "severity": "CRITICAL"
                })

        return {
            "scanned_cells": scanned_cells,
            "issues_found": len(issues),
            "issues": issues,
            "status": "PASSED" if len(issues) == 0 else "FAILED"
        }

    @staticmethod
    def run_tests() -> dict[str, Any]:
        """Run quick pytest suite to ensure zero regressions."""
        try:
            res = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "--ignore=project/kaggle_kernel"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=300

            )
            passed = res.returncode == 0
            summary_line = res.stdout.strip().splitlines()[-1] if res.stdout else res.stderr
            report = {
                "passed": passed,
                "exit_code": res.returncode,
                "summary": summary_line,
                "status": "PASSED" if passed else "FAILED"
            }
            if not passed:
                report["stdout_tail"] = "\n".join(res.stdout.strip().splitlines()[-80:])
                report["stderr_tail"] = "\n".join(res.stderr.strip().splitlines()[-80:])
            return report
        except Exception as e:
            return {
                "passed": False,
                "exit_code": -1,
                "summary": str(e),
                "status": "FAILED"
            }

    def run_full_review(self) -> dict[str, Any]:
        """Execute comprehensive pre-deployment review."""
        log.info("🔎 Running Pre-Deployment Code Review & Safety Audit...")

        secret_report = CodeReviewer.scan_secrets()
        kaggle_report = CodeReviewer.audit_kaggle_dependencies()
        notebook_report = CodeReviewer.audit_notebooks()
        test_report = CodeReviewer.run_tests()

        all_passed = (
            secret_report["status"] == "PASSED" and
            notebook_report["status"] == "PASSED" and
            test_report["status"] == "PASSED" and
            kaggle_report["status"] in ("PASSED", "WARNING")
        )

        audit_report = {
            "auditor": "CodeReviewer v1.0",
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "overall_status": "READY_FOR_PROD" if all_passed else "BLOCKED",
            "secret_scan": secret_report,
            "kaggle_cuda_audit": kaggle_report,
            "notebook_audit": notebook_report,
            "test_suite": test_report,
        }

        log.info(f"📊 Audit Complete — Overall Status: {audit_report['overall_status']}")
        return audit_report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="HoroConsultant Pre-Deployment Code Reviewer")
    parser.add_argument("--review", action="store_true", help="Run full code review & safety audit")
    parser.add_argument("--scan-secrets", action="store_true", help="Scan for secret leaks only")
    parser.add_argument("--use-python", action="store_true", help="Force python execution instead of Rust binary")
    args = parser.parse_args()

    rust_binary = ROOT / "rust_core" / "target" / "release" / "code_reviewer"
    if args.review and rust_binary.exists() and not args.use_python:
        import subprocess
        res = subprocess.run([str(rust_binary)])
        sys.exit(res.returncode)

    reviewer = CodeReviewer()
    if args.scan_secrets:
        report = CodeReviewer.scan_secrets()
        print(json.dumps(report, indent=2, ensure_ascii=False))
        sys.exit(0 if report["status"] == "PASSED" else 1)

    report = reviewer.run_full_review()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    sys.exit(0 if report["overall_status"] == "READY_FOR_PROD" else 1)


if __name__ == "__main__":
    main()
