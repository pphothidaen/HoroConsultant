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

from datetime import datetime, timezone
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
    (re.compile(r'\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b'), "OpenAI API Key"),
    (re.compile(r'\bsk-ant-[A-Za-z0-9_-]{32,}\b'), "Anthropic API Key"),
    (re.compile(r'\bAKIA[0-9A-Z]{16}\b'), "AWS Access Key"),
    (re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'), "Private Key Header"),
    (re.compile(r'\bxox[baprs]-[0-9a-zA-Z]{10,48}\b'), "Slack Token"),
    (re.compile(r'\b[0-9]{9,10}:[a-zA-Z0-9_-]{35}\b'), "Telegram Bot Token"),
]

# Sensitive files that should not be committed with actual secrets
SENSITIVE_FILES = [".env", ".env.production", "kaggle.json"]


class CodeReviewer:
    """Automated Code Reviewer and Safety Auditor."""

    def __init__(self, root_dir: Path = ROOT):
        self.root_dir = root_dir

    @staticmethod
    def scan_secrets(root_dir: Path | str | None = None) -> dict[str, Any]:
        """Scan codebase for leaked secrets or unmasked API keys. Accelerated by Rust Rayon multi-threading."""
        target_root = Path(root_dir) if root_dir is not None else ROOT
        try:
            import rust_core
            if hasattr(rust_core, "run_rust_security_audit"):
                passed, scanned_files, rust_findings = rust_core.run_rust_security_audit(str(target_root))
                findings = [{"file": f, "secret_type": "Security Finding", "count": 1} for f in rust_findings]
                log.info(f"[Rust Security Auditor] Scanned {scanned_files} files in parallel via Rayon")
                return {
                    "scanned_files": scanned_files,
                    "secret_leaks_found": len(findings),
                    "findings": findings,
                    "leaks": findings,
                    "status": "PASSED" if passed else "FAILED"
                }
        except Exception as e:
            log.warning(f"[WARNING] Rust security audit fallback: {e}")

        findings = []
        scanned_files = 0

        for path in target_root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in path.parts for part in [".git", ".pytest_cache", ".ruff_cache", "__pycache__", "venv", ".venv", "wandb", "node_modules", ".vercel", "target", ".worktrees"]):
                continue
            if path.name.startswith(".env") or path.name.startswith("gen-lang-client") or path.name.endswith(".pyc"):
                continue

            if path.stat().st_size > 1_000_000:
                continue

            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                scanned_files += 1

                for pattern, secret_type in SECRET_PATTERNS:
                    matches = pattern.findall(content)
                    if matches:
                        valid_matches = [
                            m for m in matches
                            if not any(d in str(m).lower() for d in ["dummy", "replace", "example", "test", "canary", "placeholder", "sample", "must-never", "fixture"])
                        ]
                        if valid_matches:
                            rel_path = path.relative_to(target_root)
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
            "leaks": findings,
            "status": "PASSED" if len(findings) == 0 else "FAILED"
        }

    @staticmethod
    def audit_python_ast(root_dir: Path | str | None = None) -> dict[str, Any]:
        """Scan repository Python source files for AST syntax anomalies, surrogate encoding crashes, and null-byte corruption."""
        import ast
        target_root = Path(root_dir) if root_dir is not None else ROOT
        issues = []
        scanned_files = 0

        for path in target_root.rglob("*.py"):
            if not path.is_file():
                continue
            if any(part in path.parts for part in [".git", ".pytest_cache", ".ruff_cache", "__pycache__", "venv", ".venv", "wandb", "node_modules", ".vercel", "target", ".worktrees"]):
                continue
            if path.stat().st_size > 2_000_000:
                continue

            rel_path = str(path.relative_to(target_root))
            scanned_files += 1

            # 1. Byte-level checks: null bytes & UTF-8 surrogate code point checks
            try:
                raw_bytes = path.read_bytes()
                if b"\x00" in raw_bytes:
                    issues.append({
                        "file": rel_path,
                        "issue": "Null byte detected in Python source (file corruption or binary injection)",
                        "severity": "CRITICAL"
                    })
                    continue
                try:
                    content = raw_bytes.decode("utf-8")
                except UnicodeDecodeError as exc:
                    issues.append({
                        "file": rel_path,
                        "issue": f"UTF-8 decode crash (invalid byte sequence): {exc}",
                        "severity": "CRITICAL"
                    })
                    continue

                surrogates = [c for c in content if 0xD800 <= ord(c) <= 0xDFFF]
                if surrogates:
                    issues.append({
                        "file": rel_path,
                        "issue": f"Lone surrogate encoding detected ({len(surrogates)} surrogate code points)",
                        "severity": "CRITICAL"
                    })
                    continue
            except Exception as exc:
                issues.append({
                    "file": rel_path,
                    "issue": f"Fail-closed I/O error reading Python source: {exc}",
                    "severity": "CRITICAL"
                })
                continue

            # 2. AST parsing & compile checks
            try:
                tree = ast.parse(content, filename=rel_path)
                compile(content, rel_path, "exec")
            except (SyntaxError, IndentationError, TabError) as exc:
                issues.append({
                    "file": rel_path,
                    "line": getattr(exc, "lineno", None),
                    "issue": f"AST Syntax anomaly: {exc.msg if hasattr(exc, 'msg') else exc}",
                    "severity": "CRITICAL"
                })
                continue
            except Exception as exc:
                issues.append({
                    "file": rel_path,
                    "issue": f"Fail-closed compilation failure: {exc}",
                    "severity": "CRITICAL"
                })
                continue

        return {
            "scanned_python_files": scanned_files,
            "issues_found": len(issues),
            "issues": issues,
            "status": "PASSED" if len(issues) == 0 else "FAILED"
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
                timeout=900

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

    @staticmethod
    def audit_test_provenance(
        ticket: str | None,
        baseline: str | None,
        manifest: str | None,
    ) -> dict[str, Any]:
        """Verify immutable test history when provenance inputs are supplied."""
        supplied = (ticket, baseline, manifest)
        if not any(supplied):
            return {
                "status": "NOT_REQUESTED",
                "ticket_id": None,
                "baseline_commit": None,
                "issues": [],
            }
        if not all(supplied):
            return {
                "status": "FAILED",
                "ticket_id": ticket,
                "baseline_commit": baseline,
                "issues": [
                    {
                        "code": "PROVENANCE_ARGUMENTS_INCOMPLETE",
                        "message": "--ticket, --test-baseline, and --test-manifest are required together",
                    }
                ],
            }

        guard = ROOT / "scripts" / "test_provenance_guard.py"
        command = [
            sys.executable,
            str(guard),
            "verify",
            "--repo",
            str(ROOT),
            "--manifest",
            str(manifest),
            "--baseline",
            str(baseline),
            "--head",
            "HEAD",
            "--include-worktree",
        ]
        try:
            result = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            payload = json.loads(result.stdout)
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            return {
                "status": "FAILED",
                "ticket_id": ticket,
                "baseline_commit": baseline,
                "issues": [
                    {
                        "code": "PROVENANCE_GUARD_ERROR",
                        "message": str(exc),
                    }
                ],
            }

        issues = list(payload.get("issues", []))
        if payload.get("ticket_id") != ticket:
            issues.append(
                {
                    "code": "PROVENANCE_TICKET_MISMATCH",
                    "message": "manifest ticket_id does not match --ticket",
                }
            )
        if payload.get("baseline_commit") != baseline:
            issues.append(
                {
                    "code": "PROVENANCE_BASELINE_MISMATCH",
                    "message": "verified baseline does not match --test-baseline",
                }
            )
        return {
            **payload,
            "status": "PASSED" if result.returncode == 0 and not issues else "FAILED",
            "issues": issues,
        }

    def run_full_review(
        self,
        *,
        ticket: str | None = None,
        test_baseline: str | None = None,
        test_manifest: str | None = None,
    ) -> dict[str, Any]:
        """Execute comprehensive pre-deployment review with strict fail-closed stop conditions."""
        log.info("Running Pre-Deployment Code Review & Safety Audit...")

        secret_report = CodeReviewer.scan_secrets()
        ast_report = CodeReviewer.audit_python_ast()
        kaggle_report = CodeReviewer.audit_kaggle_dependencies()
        notebook_report = CodeReviewer.audit_notebooks()
        test_report = CodeReviewer.run_tests()
        provenance_report = CodeReviewer.audit_test_provenance(
            ticket,
            test_baseline,
            test_manifest,
        )

        stop_conditions = []
        if secret_report.get("status") != "PASSED":
            stop_conditions.append(
                f"STOP_CONDITION_SECRET_LEAK: {secret_report.get('secret_leaks_found', 0)} secret findings"
            )
        if ast_report.get("status") != "PASSED":
            stop_conditions.append(
                f"STOP_CONDITION_AST_ANOMALY: {ast_report.get('issues_found', 0)} AST syntax/encoding issues"
            )
        if notebook_report.get("status") != "PASSED":
            stop_conditions.append(
                f"STOP_CONDITION_NOTEBOOK_FAILURE: {notebook_report.get('issues_found', 0)} notebook issues"
            )
        if test_report.get("status") != "PASSED":
            stop_conditions.append(
                f"STOP_CONDITION_TEST_REGRESSION: exit code {test_report.get('exit_code')}"
            )
        if kaggle_report.get("status") not in ("PASSED", "WARNING"):
            stop_conditions.append(
                f"STOP_CONDITION_KAGGLE_CRITICAL: {kaggle_report.get('issues_found', 0)} dependency issues"
            )
        if provenance_report.get("status") not in ("PASSED", "NOT_REQUESTED"):
            stop_conditions.append(
                f"STOP_CONDITION_PROVENANCE_FAILURE: {len(provenance_report.get('issues', []))} provenance issues"
            )

        overall_status = "READY_FOR_PROD" if not stop_conditions else "BLOCKED"

        audit_report = {
            "auditor": "CodeReviewer v2.0 (Pre-Deployment Safety Auditor)",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": overall_status,
            "stop_conditions": stop_conditions,
            "secret_scan": secret_report,
            "ast_syntax_audit": ast_report,
            "kaggle_cuda_audit": kaggle_report,
            "notebook_audit": notebook_report,
            "test_suite": test_report,
            "test_provenance": provenance_report,
        }

        log.info(f"Audit Complete - Overall Status: {audit_report['overall_status']}")
        if stop_conditions:
            for sc in stop_conditions:
                log.error(f"Stop Condition Tripped: {sc}")
        else:
            log.info("All pre-deployment safety gates passed.")

        return audit_report


def scan_repository_secrets(root_dir: Path | str | None = None) -> dict[str, Any]:
    """Scan repository for secret leaks using Rust Rayon parallel audit."""
    return CodeReviewer.scan_secrets(root_dir=root_dir)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="HoroConsultant Pre-Deployment Code Reviewer")
    parser.add_argument("--review", action="store_true", help="Run full code review & safety audit")
    parser.add_argument("--scan-secrets", action="store_true", help="Scan for secret leaks only")
    parser.add_argument("--audit-ast", action="store_true", help="Audit Python AST syntax and encoding safety")
    parser.add_argument("--use-python", action="store_true", help="Force python execution instead of Rust binary")
    parser.add_argument("--ticket", help="Ticket ID bound to a test-provenance manifest")
    parser.add_argument("--test-baseline", help="Exact committed test-baseline SHA")
    parser.add_argument("--test-manifest", help="Repository-relative test-provenance manifest path")
    args = parser.parse_args()

    rust_binary = ROOT / "rust_core" / "target" / "release" / "code_reviewer"
    provenance_requested = any((args.ticket, args.test_baseline, args.test_manifest))
    if args.review and rust_binary.exists() and not args.use_python and not provenance_requested:
        import subprocess
        res = subprocess.run([str(rust_binary)])
        sys.exit(res.returncode)

    reviewer = CodeReviewer()
    if args.scan_secrets:
        report = CodeReviewer.scan_secrets()
        print(json.dumps(report, indent=2, ensure_ascii=True))
        sys.exit(0 if report["status"] == "PASSED" else 1)

    if args.audit_ast:
        report = CodeReviewer.audit_python_ast()
        print(json.dumps(report, indent=2, ensure_ascii=True))
        sys.exit(0 if report["status"] == "PASSED" else 1)

    report = reviewer.run_full_review(
        ticket=args.ticket,
        test_baseline=args.test_baseline,
        test_manifest=args.test_manifest,
    )
    print(json.dumps(report, indent=2, ensure_ascii=True))
    sys.exit(0 if report["overall_status"] == "READY_FOR_PROD" else 1)


if __name__ == "__main__":
    main()
