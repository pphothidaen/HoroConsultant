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
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("code_reviewer")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# ============================================================================
# Phase 2.1: Layered Review Configuration
# ============================================================================

# Layer 1A: Complexity thresholds (radon)
COMPLEXITY_THRESHOLD_RANK = "C"  # Rank C or worse (CC >= 11)
COMPLEXITY_THRESHOLD_CC = 11     # Cyclomatic Complexity >= 11
MAINTAINABILITY_THRESHOLD = 20   # Maintainability Index < 20

# Layer 1B: Security thresholds (bandit)
BANDIT_SEVERITY_LEVELS = ["MEDIUM", "HIGH"]  # Block on MEDIUM/HIGH in enforce mode

# Noise control
MAX_FINDINGS_CAP = 8  # Max findings displayed per review

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
    def run_tests(test_paths: list[str] | None = None, timeout: int = 1800) -> dict[str, Any]:
        """Run quick pytest suite to ensure zero regressions.

        If ``test_paths`` is provided, only those files/globs are tested
        (TIER_MEDIUM targeted execution). Otherwise the full suite is run.
        """
        if test_paths:
            cmd = [sys.executable, "-m", "pytest", "-v", "-m", "not network"] + test_paths
        else:
            cmd = [sys.executable, "-m", "pytest", "-q", "-m", "not network", "--ignore=project/kaggle_kernel"]
        try:
            res = subprocess.run(
                cmd,
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=1800

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
        skip_tests: bool = False,
        test_globs: list[str] | None = None,
    ) -> dict[str, Any]:
        """Execute comprehensive pre-deployment review with strict fail-closed stop conditions."""
        log.info("Running Pre-Deployment Code Review & Safety Audit...")

        secret_report = CodeReviewer.scan_secrets()
        ast_report = CodeReviewer.audit_python_ast()
        kaggle_report = CodeReviewer.audit_kaggle_dependencies()
        notebook_report = CodeReviewer.audit_notebooks()
        if skip_tests:
            # Caller (e.g. CI) already ran the full pytest suite in a prior
            # step; re-running it here is redundant and has intermittently
            # hung until the 1800s subprocess timeout (2026-09-21 incident).
            test_report = {
                "passed": True,
                "exit_code": None,
                "summary": "Test suite execution skipped (--skip-tests); CI ran the suite in a prior step.",
                "status": "SKIPPED",
            }
            log.info("Test suite execution skipped via --skip-tests.")
        else:
            test_report = CodeReviewer.run_tests(test_paths=test_globs)
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
        if test_report.get("status") not in ("PASSED", "SKIPPED"):
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


# ============================================================================
# Phase 2.1: Layered Review Architecture (Layer 1: Static Analysis)
# ============================================================================

class LayeredCodeReviewer:
    """Layer 1 Deterministic Surface Analysis: Complexity (radon) + Security (bandit).

    Integrates with ai_sdlc_metrics.py for telemetry recording.
    """

    def __init__(
        self,
        target_files: list[str],
        ticket_id: str = "UNKNOWN",
        mode: str | None = None,
        root_dir: Path | None = None,
    ):
        self.root_dir = root_dir or ROOT
        # Filter to existing .py files
        self.target_files = [
            str(self.root_dir / f) for f in target_files
            if f.endswith(".py") and (self.root_dir / f).exists()
        ]
        self.ticket_id = ticket_id
        resolved_mode = mode if mode is not None else os.getenv("HORO_GATE_MODE", "observation")
        self.mode = str(resolved_mode).lower()
        self.findings: list[dict[str, Any]] = []

    def run_radon_complexity(self) -> None:
        """Inspects Cyclomatic Complexity & Maintainability using radon (Layer 1A)."""
        if not self.target_files:
            return

        # Use venv python if available
        python_bin = sys.executable
        venv_python = self.root_dir / ".venv" / "bin" / "python"
        if venv_python.exists():
            python_bin = str(venv_python)

        # CC check: radon cc -j -n C (show functions with rank C or worse)
        cmd_cc = [python_bin, "-m", "radon", "cc", "-j", "-n", COMPLEXITY_THRESHOLD_RANK] + self.target_files
        res_cc = subprocess.run(cmd_cc, capture_output=True, text=True)
        if res_cc.returncode == 0 and res_cc.stdout.strip():
            try:
                data = json.loads(res_cc.stdout)
                for file_path, blocks in data.items():
                    for block in blocks:
                        cc = block.get("complexity", 0)
                        rank = block.get("rank", "")
                        if cc >= COMPLEXITY_THRESHOLD_CC:
                            severity = "ERROR" if rank in ("D", "E", "F") else "WARNING"
                            self.findings.append({
                                "tool": "radon_cc",
                                "file": str(Path(file_path).relative_to(self.root_dir)),
                                "line": block.get("lineno", 1),
                                "name": block.get("name"),
                                "severity": severity,
                                "score": cc,
                                "rank": rank,
                                "message": f"High Cyclomatic Complexity ({cc}, Rank {rank}) in {block.get('type', 'function')} '{block.get('name', 'unknown')}'"
                            })
            except json.JSONDecodeError:
                pass

        # MI check: radon mi -j (Maintainability Index)
        cmd_mi = [python_bin, "-m", "radon", "mi", "-j"] + self.target_files
        res_mi = subprocess.run(cmd_mi, capture_output=True, text=True)
        if res_mi.returncode == 0 and res_mi.stdout.strip():
            try:
                data = json.loads(res_mi.stdout)
                for file_path, mi_score in data.items():
                    if isinstance(mi_score, (int, float)) and mi_score < MAINTAINABILITY_THRESHOLD:
                        self.findings.append({
                            "tool": "radon_mi",
                            "file": str(Path(file_path).relative_to(self.root_dir)),
                            "line": 1,
                            "name": "module",
                            "severity": "WARNING",
                            "score": mi_score,
                            "rank": "N/A",
                            "message": f"Low Maintainability Index ({mi_score:.1f} < {MAINTAINABILITY_THRESHOLD})"
                        })
            except json.JSONDecodeError:
                pass

    def run_bandit_security(self) -> None:
        """Inspects security vulnerabilities using bandit (Layer 1B)."""
        if not self.target_files:
            return

        python_bin = sys.executable
        venv_python = self.root_dir / ".venv" / "bin" / "python"
        if venv_python.exists():
            python_bin = str(venv_python)

        cmd = [python_bin, "-m", "bandit", "-f", "json", "-q"] + self.target_files
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.stdout.strip():
            try:
                data = json.loads(res.stdout)
                for result in data.get("results", []):
                    severity = result.get("issue_severity", "LOW").upper()
                    if severity in BANDIT_SEVERITY_LEVELS:
                        self.findings.append({
                            "tool": "bandit",
                            "file": str(Path(result.get("filename", "")).relative_to(self.root_dir)),
                            "line": result.get("line_number", 1),
                            "name": result.get("test_id"),
                            "severity": severity,
                            "confidence": result.get("issue_confidence"),
                            "message": result.get("issue_text")
                        })
            except json.JSONDecodeError:
                pass

    def record_telemetry(self) -> None:
        """Sends each finding to SQLite metrics via ai_sdlc_metrics.py."""
        for finding in self.findings[:MAX_FINDINGS_CAP]:
            tool = finding["tool"]
            severity = finding["severity"]

            # Map tool to finding_type
            if tool in ("radon_cc", "radon_mi"):
                finding_type = "complexity"
                severity_map = {"ERROR": "high", "WARNING": "medium", "HIGH": "high"}
            elif tool == "bandit":
                finding_type = "security"
                severity_map = {"HIGH": "high", "MEDIUM": "medium", "LOW": "low"}
            else:
                finding_type = "syntax"
                severity_map = {"ERROR": "high", "WARNING": "medium"}

            mapped_severity = severity_map.get(severity.upper(), "medium")

            cmd = [
                sys.executable, "scripts/ai_sdlc_metrics.py", "record-review-signal",
                "--ticket-id", self.ticket_id,
                "--finding-type", finding_type,
                "--severity", mapped_severity,
                "--file", finding["file"],
                "--line", str(finding["line"]),
                "--message", finding["message"]
            ]
            subprocess.run(cmd, capture_output=True, cwd=self.root_dir)

    def record_gate(self) -> None:
        """Record a gate event to ai_sdlc_metrics.py (Observation Mode)."""
        try:
            # Compute a risk tier consistent with tdd_gate
            try:
                import sys as _sys
                _sys.path.insert(0, str(self.root_dir / "scripts"))
                import tdd_gate as _tg
                rel_files = [str(Path(f).relative_to(self.root_dir)) for f in self.target_files]
                tier = _tg.detect_risk_tier(rel_files) if rel_files else "Tier 1"
            except Exception:
                tier = "Tier 2"

            if not self.findings:
                result = "PASS"
            elif self.mode == "observation":
                result = "FAIL_OBSERVED"
            else:
                result = "FAIL"

            script = self.root_dir / "scripts" / "ai_sdlc_metrics.py"
            cmd = [
                sys.executable, str(script), "record-gate",
                "--gate-name", "code_reviewer",
                "--gate-mode", self.mode,
                "--tier", tier,
                "--result", result,
                "--ticket-id", self.ticket_id,
            ]
            subprocess.run(cmd, capture_output=True, text=True, cwd=self.root_dir)
        except Exception:
            pass

    def evaluate(self) -> tuple[int, list[dict[str, Any]]]:
        """Run all Layer 1 checks. Returns (exit_code, findings)."""
        self.run_radon_complexity()
        self.run_bandit_security()
        self.record_telemetry()
        self.record_gate()

        if not self.findings:
            print("[LAYERED-REVIEW] All static checks passed cleanly (radon + bandit).")
            return 0, []

        print(f"\n[LAYERED-REVIEW] Found {len(self.findings)} static issues (Capped display at {MAX_FINDINGS_CAP}):")
        for idx, item in enumerate(self.findings[:MAX_FINDINGS_CAP], 1):
            print(f"  {idx}. [{item['tool'].upper()}] {item['file']}:{item['line']} - {item['severity']}: {item['message']}")

        if len(self.findings) > MAX_FINDINGS_CAP:
            print(f"  ... and {len(self.findings) - MAX_FINDINGS_CAP} additional findings suppressed.")

        if self.mode == "enforce":
            has_blocking = any(f["severity"] in ["HIGH", "ERROR", "MEDIUM"] for f in self.findings)
            if has_blocking:
                print("\n[LAYERED-REVIEW BLOCKED] Hard errors found in enforce mode.")
                return 1, self.findings[:MAX_FINDINGS_CAP]

        if self.mode == "observation":
            print(f"\nWARNING: Layered review found {len(self.findings)} issue(s); observation mode allows (exit 0).")

        print(f"\n[LAYERED-REVIEW NOTICE] Mode is '{self.mode}'. Non-blocking exit 0.")
        return 0, self.findings[:MAX_FINDINGS_CAP]


def run_layered_review(
    target_files: list[str],
    ticket_id: str = "UNKNOWN",
    mode: str | None = None,
) -> tuple[int, list[dict[str, Any]]]:
    """Convenience function for CI/CD integration."""
    reviewer = LayeredCodeReviewer(target_files, ticket_id, mode)
    return reviewer.evaluate()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Code Reviewer & Safety Auditor")
    parser.add_argument("--use-python", action="store_true", help="Force python execution instead of Rust binary")
    parser.add_argument("--ticket", help="Ticket ID bound to a test-provenance manifest")
    parser.add_argument("--test-baseline", help="Exact committed test-baseline SHA")
    parser.add_argument("--test-manifest", help="Repository-relative test-provenance manifest path")
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip the nested pytest run (use when CI already ran the suite in a prior step)",
    )
    parser.add_argument(
        "--test-globs",
        nargs="*",
        default=None,
        help="Run only the specified test paths/globs instead of full suite (TIER_MEDIUM).",
    )
    parser.add_argument("--scan-secrets", action="store_true", help="Run secret scan only")
    parser.add_argument("--audit-ast", action="store_true", help="Run AST audit only")
    parser.add_argument("--review", action="store_true", help="Run full review (default)")
    parser.add_argument("--layered-review", action="store_true", help="Run Layer 1 static analysis (radon + bandit)")
    parser.add_argument("--layered-files", nargs="*", default=None, help="Files to analyze in layered review (default: all .py files)")
    parser.add_argument("--ticket-id", help="Ticket ID for telemetry correlation")
    parser.add_argument("--gate-mode", choices=["observation", "enforce"], default=os.getenv("HORO_GATE_MODE", "observation"), help="Gate mode for layered review")
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

    if args.layered_review:
        target_files = args.layered_files if args.layered_files else [
            str(p.relative_to(ROOT)) for p in ROOT.rglob("*.py") if "tests/" not in str(p)
        ]
        ticket_id = args.ticket_id or os.getenv("TICKET_ID", "UNKNOWN")
        exit_code, findings = run_layered_review(target_files, ticket_id, args.gate_mode)
        print(json.dumps({"findings": findings}, indent=2, ensure_ascii=True))
        sys.exit(exit_code)

    report = reviewer.run_full_review(
        ticket=args.ticket,
        test_baseline=args.test_baseline,
        test_manifest=args.test_manifest,
        skip_tests=args.skip_tests,
        test_globs=args.test_globs,
    )
    print(json.dumps(report, indent=2, ensure_ascii=True))
    sys.exit(0 if report["overall_status"] == "READY_FOR_PROD" else 1)


if __name__ == "__main__":
    main()
