#!/usr/bin/env python3
"""Action Priority Guard for branch migration in HoroConsultant.

Enforces the three Action Priority phases during branch migration and release:

Phase 1 (Immediate / เร่งด่วนสูงสุด):
  - check_worktrees: Inspect active/dirty/temporary worktrees and ensure no collision.
  - check_immutable_recovery_refs: Verify recovery/pre-test-provenance-20260827
    (or origin/recovery/pre-test-provenance-20260827) ref and required commit message.

Phase 2 (Urgent / เร่งด่วน):
  - check_test_provenance: Verify committed test-first provenance and manifests.
  - check_production_deployment_guards: Verify deployment separation between
    Vercel static URL and HF Docker Space (pphothidaen/horoconsultant-core-backend).

Phase 3 (Routine / ไม่เร่งด่วน):
  - check_ai_ecosystem_sync: Verify AI agent ecosystem sync via sync_ai_agent_ecosystem.py.
  - check_rust_wheel_and_tests: Verify Rust core / Python fallback and test suite readiness.
  - check_viewport_artifacts: Verify 5 canonical viewport artifacts and screenshot receipts.

All log output is strictly pure ASCII ([OK], [ERROR], [WARNING], [INFO]) to comply
with Rule 3 Pure ASCII Logging Guard.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "branch-migration-action-priority-report-v1"

IMMUTABLE_RECOVERY_REF = "recovery/pre-test-provenance-20260827"
IMMUTABLE_RECOVERY_REMOTE_REF = "origin/recovery/pre-test-provenance-20260827"
REQUIRED_RECOVERY_COMMIT_MESSAGE = (
    "chore(recovery): preserve pre-gate mixed worktree [NON_TDD_RECONSTRUCTED]"
)

CANONICAL_HF_SPACE = "pphothidaen/horoconsultant-core-backend"
CANONICAL_HF_ORIGIN = "https://pphothidaen-horoconsultant-core-backend.hf.space"
CANONICAL_SDK = "docker"

CANONICAL_VIEWPORTS = (
    "mobile_375x667",
    "tablet_768x1024",
    "laptop_1280x800",
    "desktop_1440x900",
    "desktop_1920x1080",
)


class ActionPriorityGuardError(RuntimeError):
    """Raised when repository inspection encounters an unrecoverable failure."""


def _git(
    repo: Path,
    *args: str,
    check: bool = True,
    text: bool = True,
) -> subprocess.CompletedProcess[Any]:
    """Run a git command in the target repository safely."""
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=text,
        check=False,
    )
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout or "git command failed").strip()
        raise ActionPriorityGuardError(f"git {' '.join(args)}: {detail}")
    return result


def find_repo_root(hint: Path | str | None = None) -> Path:
    """Resolve the absolute root directory of the git repository."""
    start_path = Path(hint or Path(__file__).resolve().parent.parent).resolve()
    if not start_path.exists():
        start_path = Path.cwd()
    res = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=start_path if start_path.is_dir() else start_path.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode == 0 and res.stdout.strip():
        return Path(res.stdout.strip()).resolve()
    # Fallback to parent of scripts directory
    return Path(__file__).resolve().parent.parent


@dataclass
class WorktreeInfo:
    """Metadata describing a single git worktree."""

    path: str
    head_sha: str
    branch: str | None = None
    is_bare: bool = False
    is_detached: bool = False
    is_temporary: bool = False
    is_dirty: bool = False
    dirty_files_count: int = 0
    exists_on_disk: bool = True
    lock_reason: str | None = None
    prunable_reason: str | None = None


@dataclass
class WorktreeCheckResult:
    """Verification results for all active worktrees."""

    status: str  # PASSED, WARNING, FAILED
    total_worktrees: int = 0
    active_worktrees: list[dict[str, Any]] = field(default_factory=list)
    dirty_worktrees: list[dict[str, Any]] = field(default_factory=list)
    temporary_worktrees: list[dict[str, Any]] = field(default_factory=list)
    collisions: list[dict[str, str]] = field(default_factory=list)
    issues: list[dict[str, str]] = field(default_factory=list)


@dataclass
class RecoveryRefCheckResult:
    """Verification results for immutable recovery refs."""

    status: str  # PASSED, FAILED
    ref: str | None = None
    commit_sha: str | None = None
    commit_message: str | None = None
    matched_expected: bool = False
    issues: list[dict[str, str]] = field(default_factory=list)


@dataclass
class TestProvenanceCheckResult:
    """Verification results for TDD baseline provenance."""

    status: str  # PASSED, FAILED
    manifests_count: int = 0
    manifests_verified: int = 0
    guard_script_present: bool = False
    guard_status: str = "UNKNOWN"
    issues: list[dict[str, str]] = field(default_factory=list)


@dataclass
class DeploymentGuardCheckResult:
    """Verification results for production deployment separation."""

    status: str  # PASSED, FAILED
    canonical_hf_space: str = CANONICAL_HF_SPACE
    canonical_hf_origin: str = CANONICAL_HF_ORIGIN
    gateway_origin_enforced: bool = False
    publisher_space_enforced: bool = False
    dockerfile_present: bool = False
    manifest_schema_present: bool = False
    issues: list[dict[str, str]] = field(default_factory=list)


@dataclass
class EcosystemSyncCheckResult:
    """Verification results for AI agent ecosystem synchronization."""

    status: str  # PASSED, FAILED
    sync_script_present: bool = False
    sync_passed: bool = False
    details: str = ""
    issues: list[dict[str, str]] = field(default_factory=list)


@dataclass
class RustAndTestsCheckResult:
    """Verification results for Rust core / Python fallback and test readiness."""

    status: str  # PASSED, FAILED
    rust_core_present: bool = False
    python_fallback_allowed: bool = False
    fast_math_present: bool = False
    test_suites_ready: bool = False
    test_files_count: int = 0
    issues: list[dict[str, str]] = field(default_factory=list)


@dataclass
class ViewportArtifactsCheckResult:
    """Verification results for 5 canonical viewport artifacts and receipts."""

    status: str  # PASSED, FAILED
    viewports_verified: int = 0
    canonical_viewports: list[str] = field(default_factory=list)
    receipt_present: bool = False
    receipt_overall_status: str | None = None
    screenshots_count: int = 0
    missing_viewports: list[str] = field(default_factory=list)
    issues: list[dict[str, str]] = field(default_factory=list)


@dataclass
class PhaseResult:
    """Aggregated status and results for an Action Priority phase."""

    phase_number: int
    phase_name: str
    status: str  # PASSED, WARNING, FAILED
    checks: dict[str, Any] = field(default_factory=dict)
    issues: list[dict[str, str]] = field(default_factory=list)


@dataclass
class ActionPriorityReport:
    """Comprehensive structured receipt for branch migration action priority audit."""

    schema_version: str = SCHEMA_VERSION
    generated_at: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    repo_root: str = ""
    phase_filter: str = "all"
    strict_mode: bool = False
    audit_only: bool = False
    overall_status: str = "PASSED"  # PASSED, WARNING, FAILED
    phases: dict[str, dict[str, Any]] = field(default_factory=dict)
    summary: dict[str, int] = field(default_factory=dict)
    issues: list[dict[str, str]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        """Convert report dataclass to serializable dictionary."""
        return asdict(self)


# =============================================================================
# PHASE 1: Immediate / เร่งด่วนสูงสุด
# =============================================================================


def _is_temporary_path(path_str: str) -> bool:
    """Determine if a worktree path represents an ephemeral/temporary workspace."""
    normalized = path_str.replace("\\", "/")
    return (
        normalized.startswith("/tmp/")
        or normalized.startswith("/private/tmp/")
        or "/tmp/" in normalized
        or "/temp/" in normalized
        or "tmp" in Path(normalized).name.lower()
    )


def check_worktrees(repo_root: Path, strict: bool = False) -> WorktreeCheckResult:
    """Inspect active worktrees, check cleanliness, and detect branch collisions."""
    result = WorktreeCheckResult(status="PASSED")
    raw_list = _git(repo_root, "worktree", "list", "--porcelain", check=False)
    if raw_list.returncode != 0:
        result.status = "FAILED"
        result.issues.append(
            {
                "code": "WORKTREE_LIST_FAILED",
                "message": f"Unable to list git worktrees: {raw_list.stderr.strip()}",
            }
        )
        return result

    blocks = raw_list.stdout.strip().split("\n\n")
    worktrees: list[WorktreeInfo] = []
    branch_map: dict[str, list[str]] = {}

    for block in blocks:
        if not block.strip():
            continue
        lines = block.strip().splitlines()
        wt_path: str | None = None
        head_sha: str = ""
        branch: str | None = None
        is_bare = False
        is_detached = False
        lock_reason: str | None = None
        prunable_reason: str | None = None

        for line in lines:
            if line.startswith("worktree "):
                wt_path = line[len("worktree ") :].strip()
            elif line.startswith("HEAD "):
                head_sha = line[len("HEAD ") :].strip()
            elif line.startswith("branch "):
                branch = line[len("branch ") :].strip()
            elif line == "bare":
                is_bare = True
            elif line == "detached":
                is_detached = True
            elif line.startswith("locked"):
                lock_reason = line[len("locked") :].strip() or "locked"
            elif line.startswith("prunable"):
                prunable_reason = line[len("prunable") :].strip() or "prunable"

        if not wt_path:
            continue

        wt_path_obj = Path(wt_path)
        exists = wt_path_obj.exists() and wt_path_obj.is_dir()
        is_temp = _is_temporary_path(wt_path)
        is_dirty = False
        dirty_files_count = 0

        if exists and not is_bare:
            status_res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=wt_path_obj,
                capture_output=True,
                text=True,
                check=False,
            )
            if status_res.returncode == 0:
                dirty_lines = [l for l in status_res.stdout.splitlines() if l.strip()]
                dirty_files_count = len(dirty_lines)
                is_dirty = dirty_files_count > 0

        info = WorktreeInfo(
            path=wt_path,
            head_sha=head_sha,
            branch=branch,
            is_bare=is_bare,
            is_detached=is_detached,
            is_temporary=is_temp,
            is_dirty=is_dirty,
            dirty_files_count=dirty_files_count,
            exists_on_disk=exists,
            lock_reason=lock_reason,
            prunable_reason=prunable_reason,
        )
        worktrees.append(info)

        if branch and not is_detached and not is_bare:
            branch_map.setdefault(branch, []).append(wt_path)

    result.total_worktrees = len(worktrees)
    for wt in worktrees:
        wt_dict = asdict(wt)
        result.active_worktrees.append(wt_dict)
        if wt.is_dirty:
            result.dirty_worktrees.append(wt_dict)
        if wt.is_temporary:
            result.temporary_worktrees.append(wt_dict)

    # Check for branch collisions (multiple worktrees checking out the same branch)
    for br, paths in branch_map.items():
        if len(paths) > 1:
            collision = {
                "branch": br,
                "paths": ", ".join(paths),
                "message": f"Branch collision detected for '{br}' across {len(paths)} worktrees",
            }
            result.collisions.append(collision)
            result.issues.append(
                {
                    "code": "WORKTREE_BRANCH_COLLISION",
                    "message": collision["message"],
                }
            )

    if result.collisions:
        result.status = "FAILED"
    elif result.dirty_worktrees:
        if strict:
            result.status = "FAILED"
            result.issues.append(
                {
                    "code": "DIRTY_WORKTREES_STRICT_FAILURE",
                    "message": f"Strict mode failure: {len(result.dirty_worktrees)} dirty worktree(s) found",
                }
            )
        else:
            result.status = "WARNING"
            result.issues.append(
                {
                    "code": "DIRTY_WORKTREES_DETECTED",
                    "message": f"Detected {len(result.dirty_worktrees)} dirty worktree(s)",
                }
            )

    return result


def check_immutable_recovery_refs(
    repo_root: Path,
    target_ref: str | None = None,
) -> RecoveryRefCheckResult:
    """Verify that the immutable recovery ref exists with the exact commit message."""
    result = RecoveryRefCheckResult(status="PASSED")
    candidate_refs = [
        target_ref,
        IMMUTABLE_RECOVERY_REF,
        f"refs/heads/{IMMUTABLE_RECOVERY_REF}",
        IMMUTABLE_RECOVERY_REMOTE_REF,
        f"refs/remotes/{IMMUTABLE_RECOVERY_REMOTE_REF}",
    ]
    resolved_ref: str | None = None
    commit_sha: str | None = None

    for ref in candidate_refs:
        if not ref:
            continue
        rev_res = _git(repo_root, "rev-parse", "--verify", f"{ref}^{{commit}}", check=False)
        if rev_res.returncode == 0 and rev_res.stdout.strip():
            resolved_ref = ref
            commit_sha = rev_res.stdout.strip()
            break

    if not resolved_ref or not commit_sha:
        result.status = "FAILED"
        result.issues.append(
            {
                "code": "MISSING_IMMUTABLE_RECOVERY_REF",
                "message": (
                    f"Immutable recovery ref '{IMMUTABLE_RECOVERY_REF}' "
                    f"or '{IMMUTABLE_RECOVERY_REMOTE_REF}' was not found in git repository"
                ),
            }
        )
        return result

    result.ref = resolved_ref
    result.commit_sha = commit_sha

    # Extract commit message
    msg_res = _git(repo_root, "log", "-n", "1", "--format=%B", commit_sha, check=False)
    if msg_res.returncode != 0:
        result.status = "FAILED"
        result.issues.append(
            {
                "code": "CANNOT_READ_RECOVERY_COMMIT_MESSAGE",
                "message": f"Failed to retrieve commit message for recovery ref {resolved_ref}",
            }
        )
        return result

    commit_msg = msg_res.stdout.strip()
    result.commit_message = commit_msg

    # Verify exact match or prefix subject match
    subject = commit_msg.splitlines()[0].strip() if commit_msg else ""
    if (
        subject == REQUIRED_RECOVERY_COMMIT_MESSAGE
        or REQUIRED_RECOVERY_COMMIT_MESSAGE in commit_msg
    ):
        result.matched_expected = True
    else:
        result.status = "FAILED"
        result.matched_expected = False
        result.issues.append(
            {
                "code": "INVALID_RECOVERY_COMMIT_MESSAGE",
                "message": (
                    f"Recovery commit message mismatch. Expected: '{REQUIRED_RECOVERY_COMMIT_MESSAGE}', "
                    f"Found: '{subject}'"
                ),
            }
        )

    return result


def run_phase_1(repo_root: Path, strict: bool = False) -> PhaseResult:
    """Execute Phase 1 (Immediate / เร่งด่วนสูงสุด) checks."""
    worktree_res = check_worktrees(repo_root, strict=strict)
    recovery_res = check_immutable_recovery_refs(repo_root)

    phase_status = "PASSED"
    if worktree_res.status == "FAILED" or recovery_res.status == "FAILED":
        phase_status = "FAILED"
    elif worktree_res.status == "WARNING" or recovery_res.status == "WARNING":
        phase_status = "WARNING"

    all_issues = list(worktree_res.issues) + list(recovery_res.issues)

    return PhaseResult(
        phase_number=1,
        phase_name="Immediate (Phase 1)",
        status=phase_status,
        checks={
            "worktrees": asdict(worktree_res),
            "immutable_recovery_refs": asdict(recovery_res),
        },
        issues=all_issues,
    )


# =============================================================================
# PHASE 2: Urgent / เร่งด่วน
# =============================================================================


def check_test_provenance(repo_root: Path) -> TestProvenanceCheckResult:
    """Verify test-first provenance, manifests in plans/test_provenance, and guard script."""
    result = TestProvenanceCheckResult(status="PASSED")
    guard_script = repo_root / "scripts" / "test_provenance_guard.py"
    manifests_dir = repo_root / "plans" / "test_provenance"

    result.guard_script_present = guard_script.is_file()
    if not result.guard_script_present:
        result.status = "FAILED"
        result.issues.append(
            {
                "code": "MISSING_TEST_PROVENANCE_GUARD",
                "message": f"Required guard script not found: {guard_script}",
            }
        )
        return result

    if not manifests_dir.is_dir():
        result.status = "FAILED"
        result.issues.append(
            {
                "code": "MISSING_TEST_PROVENANCE_MANIFESTS_DIR",
                "message": f"Manifests directory not found: {manifests_dir}",
            }
        )
        return result

    manifest_files = list(manifests_dir.glob("*.json"))
    result.manifests_count = len(manifest_files)
    if result.manifests_count == 0:
        result.status = "FAILED"
        result.issues.append(
            {
                "code": "NO_TEST_PROVENANCE_MANIFESTS",
                "message": "No test provenance manifest JSON files found in plans/test_provenance/",
            }
        )
        return result

    verified_count = 0
    for mf in manifest_files:
        try:
            with open(mf, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "ticket_id" in data and "baseline_parent" in data:
                verified_count += 1
            else:
                result.issues.append(
                    {
                        "code": "MALFORMED_MANIFEST",
                        "message": f"Manifest missing required keys: {mf.name}",
                    }
                )
        except Exception as err:
            result.issues.append(
                {
                    "code": "INVALID_MANIFEST_JSON",
                    "message": f"Cannot parse manifest {mf.name}: {err}",
                }
            )

    result.manifests_verified = verified_count
    if result.issues:
        result.status = "FAILED"
        result.guard_status = "FAILED"
    else:
        result.guard_status = "PASSED"

    return result


def check_production_deployment_guards(repo_root: Path) -> DeploymentGuardCheckResult:
    """Verify deployment separation between Vercel static gateway and HF Docker space."""
    result = DeploymentGuardCheckResult(status="PASSED")

    # 1. Inspect api/index.js for canonical HF origin enforcement
    api_gateway = repo_root / "api" / "index.js"
    if api_gateway.is_file():
        content = api_gateway.read_text(encoding="utf-8")
        if CANONICAL_HF_ORIGIN in content and "CANONICAL_HF_BACKEND_ORIGIN" in content:
            result.gateway_origin_enforced = True
        else:
            result.issues.append(
                {
                    "code": "GATEWAY_ORIGIN_MISMATCH",
                    "message": f"api/index.js does not enforce canonical HF origin {CANONICAL_HF_ORIGIN}",
                }
            )
    else:
        result.issues.append(
            {
                "code": "MISSING_API_GATEWAY",
                "message": "api/index.js not found in repository",
            }
        )

    # 2. Inspect scripts/publish_space_hf.py for canonical space target
    publisher = repo_root / "scripts" / "publish_space_hf.py"
    if publisher.is_file():
        pub_content = publisher.read_text(encoding="utf-8")
        if (
            f'CANONICAL_SPACE_ID = "{CANONICAL_HF_SPACE}"' in pub_content
            and f'CANONICAL_SDK = "{CANONICAL_SDK}"' in pub_content
        ):
            result.publisher_space_enforced = True
        else:
            result.issues.append(
                {
                    "code": "PUBLISHER_TARGET_MISMATCH",
                    "message": f"scripts/publish_space_hf.py does not match canonical Space {CANONICAL_HF_SPACE}",
                }
            )
    else:
        result.issues.append(
            {
                "code": "MISSING_PUBLISHER_SCRIPT",
                "message": "scripts/publish_space_hf.py not found in repository",
            }
        )

    # 3. Check Dockerfile and release schemas
    dockerfile = repo_root / "Dockerfile"
    dockerfile_hf = repo_root / "Dockerfile.hf"
    result.dockerfile_present = dockerfile.is_file() or dockerfile_hf.is_file()
    if not result.dockerfile_present:
        result.issues.append(
            {
                "code": "MISSING_DOCKERFILE",
                "message": "Neither Dockerfile nor Dockerfile.hf found for backend deployment",
            }
        )

    manifest_schema = repo_root / "project" / "schemas" / "release-manifest-v1.schema.json"
    result.manifest_schema_present = manifest_schema.is_file()
    if not result.manifest_schema_present:
        result.issues.append(
            {
                "code": "MISSING_RELEASE_MANIFEST_SCHEMA",
                "message": "project/schemas/release-manifest-v1.schema.json not found",
            }
        )

    if result.issues:
        result.status = "FAILED"

    return result


def run_phase_2(repo_root: Path, strict: bool = False) -> PhaseResult:
    """Execute Phase 2 (Urgent / เร่งด่วน) checks."""
    provenance_res = check_test_provenance(repo_root)
    deploy_res = check_production_deployment_guards(repo_root)

    phase_status = "PASSED"
    if provenance_res.status == "FAILED" or deploy_res.status == "FAILED":
        phase_status = "FAILED"
    elif provenance_res.status == "WARNING" or deploy_res.status == "WARNING":
        phase_status = "WARNING"

    all_issues = list(provenance_res.issues) + list(deploy_res.issues)

    return PhaseResult(
        phase_number=2,
        phase_name="Urgent (Phase 2)",
        status=phase_status,
        checks={
            "test_provenance": asdict(provenance_res),
            "production_deployment_guards": asdict(deploy_res),
        },
        issues=all_issues,
    )


# =============================================================================
# PHASE 3: Routine / ไม่เร่งด่วน
# =============================================================================


def check_ai_ecosystem_sync(repo_root: Path) -> EcosystemSyncCheckResult:
    """Verify AI agent ecosystem sync via scripts/sync_ai_agent_ecosystem.py --check."""
    result = EcosystemSyncCheckResult(status="PASSED")
    sync_script = repo_root / "scripts" / "sync_ai_agent_ecosystem.py"
    result.sync_script_present = sync_script.is_file()

    if not result.sync_script_present:
        result.status = "FAILED"
        result.issues.append(
            {
                "code": "MISSING_AI_ECOSYSTEM_SYNC_SCRIPT",
                "message": f"Sync script not found: {sync_script}",
            }
        )
        return result

    res = subprocess.run(
        [sys.executable, str(sync_script), "--check"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    result.sync_passed = res.returncode == 0
    result.details = (res.stdout or res.stderr or "").strip()

    if not result.sync_passed:
        result.status = "FAILED"
        result.issues.append(
            {
                "code": "AI_ECOSYSTEM_SYNC_FAILED",
                "message": f"sync_ai_agent_ecosystem.py failed with returncode {res.returncode}",
            }
        )

    return result


def check_rust_wheel_and_tests(repo_root: Path) -> RustAndTestsCheckResult:
    """Verify Rust core / Python fallback settings and test suite readiness."""
    result = RustAndTestsCheckResult(status="PASSED")
    rust_dir = repo_root / "rust_core"
    fast_math = repo_root / "project" / "core" / "fast_math.py"
    tests_dir = repo_root / "tests"
    project_tests_dir = repo_root / "project" / "tests"

    result.rust_core_present = rust_dir.is_dir()
    result.fast_math_present = fast_math.is_file()

    # Check fallback setting in environment or default configuration
    result.python_fallback_allowed = (
        os.environ.get("HORO_ALLOW_PYTHON_FALLBACK") == "1"
        or (rust_dir / "__init__.py").is_file()
    )

    test_files: list[Path] = []
    if tests_dir.is_dir():
        test_files.extend(tests_dir.glob("test_*.py"))
    if project_tests_dir.is_dir():
        test_files.extend(project_tests_dir.glob("test_*.py"))

    result.test_files_count = len(test_files)
    result.test_suites_ready = result.test_files_count > 0

    if not result.fast_math_present:
        result.issues.append(
            {
                "code": "MISSING_FAST_MATH",
                "message": "project/core/fast_math.py is missing",
            }
        )
    if not result.test_suites_ready:
        result.issues.append(
            {
                "code": "NO_TEST_FILES_FOUND",
                "message": "No test files found in tests/ or project/tests/",
            }
        )

    if result.issues:
        result.status = "FAILED"

    return result


def check_viewport_artifacts(repo_root: Path) -> ViewportArtifactsCheckResult:
    """Verify 5 canonical viewport artifacts and screenshot receipts."""
    result = ViewportArtifactsCheckResult(
        status="PASSED",
        canonical_viewports=list(CANONICAL_VIEWPORTS),
    )
    receipt_file = (
        repo_root / "project" / "tests" / "multi_viewport_visual_audit_receipt.json"
    )
    screenshots_dir = (
        repo_root / "project" / "tests" / "screenshots" / "canonical_viewports"
    )

    result.receipt_present = receipt_file.is_file()
    if result.receipt_present:
        try:
            with open(receipt_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            result.receipt_overall_status = data.get("overall_status")
        except Exception as err:
            result.issues.append(
                {
                    "code": "INVALID_VIEWPORT_RECEIPT_JSON",
                    "message": f"Failed to parse receipt file: {err}",
                }
            )

    if screenshots_dir.is_dir():
        screenshot_files = list(screenshots_dir.glob("*.png"))
        result.screenshots_count = len(screenshot_files)
        screenshot_names = [f.name for f in screenshot_files]
        verified_vp = 0
        missing: list[str] = []
        for vp in CANONICAL_VIEWPORTS:
            if any(f.startswith(vp) for f in screenshot_names):
                verified_vp += 1
            else:
                missing.append(vp)
        result.viewports_verified = verified_vp
        result.missing_viewports = missing
        if missing:
            result.issues.append(
                {
                    "code": "MISSING_VIEWPORT_SCREENSHOTS",
                    "message": f"Missing screenshots for viewports: {', '.join(missing)}",
                }
            )
    else:
        result.missing_viewports = list(CANONICAL_VIEWPORTS)
        result.issues.append(
            {
                "code": "MISSING_SCREENSHOTS_DIR",
                "message": f"Directory not found: {screenshots_dir}",
            }
        )

    if not result.receipt_present or result.missing_viewports:
        result.status = "FAILED"

    return result


def run_phase_3(repo_root: Path, strict: bool = False) -> PhaseResult:
    """Execute Phase 3 (Routine / ไม่เร่งด่วน) checks."""
    sync_res = check_ai_ecosystem_sync(repo_root)
    rust_res = check_rust_wheel_and_tests(repo_root)
    vp_res = check_viewport_artifacts(repo_root)

    phase_status = "PASSED"
    if (
        sync_res.status == "FAILED"
        or rust_res.status == "FAILED"
        or vp_res.status == "FAILED"
    ):
        phase_status = "FAILED"
    elif (
        sync_res.status == "WARNING"
        or rust_res.status == "WARNING"
        or vp_res.status == "WARNING"
    ):
        phase_status = "WARNING"

    all_issues = list(sync_res.issues) + list(rust_res.issues) + list(vp_res.issues)

    return PhaseResult(
        phase_number=3,
        phase_name="Routine (Phase 3)",
        status=phase_status,
        checks={
            "ai_ecosystem_sync": asdict(sync_res),
            "rust_wheel_and_tests": asdict(rust_res),
            "viewport_artifacts": asdict(vp_res),
        },
        issues=all_issues,
    )


# =============================================================================
# Action Priority Orchestrator & CLI
# =============================================================================


def run_action_priority_guard(
    repo_root: Path,
    phase: str = "all",
    strict: bool = False,
    audit_only: bool = False,
) -> ActionPriorityReport:
    """Execute the specified Action Priority phase(s) and build a report."""
    report = ActionPriorityReport(
        repo_root=str(repo_root),
        phase_filter=phase,
        strict_mode=strict,
        audit_only=audit_only,
    )

    phases_to_run: list[int] = []
    normalized_phase = phase.lower().strip()
    if normalized_phase in ("all", "0"):
        phases_to_run = [1, 2, 3]
    elif normalized_phase in ("immediate", "1"):
        phases_to_run = [1]
    elif normalized_phase in ("urgent", "2"):
        phases_to_run = [2]
    elif normalized_phase in ("routine", "3"):
        phases_to_run = [3]
    else:
        raise ValueError(
            f"Unknown phase '{phase}'. Choose from: all, immediate, urgent, routine, 1, 2, 3"
        )

    phase_results: list[PhaseResult] = []
    if 1 in phases_to_run:
        res1 = run_phase_1(repo_root, strict=strict)
        phase_results.append(res1)
        report.phases["phase_1_immediate"] = asdict(res1)
    if 2 in phases_to_run:
        res2 = run_phase_2(repo_root, strict=strict)
        phase_results.append(res2)
        report.phases["phase_2_urgent"] = asdict(res2)
    if 3 in phases_to_run:
        res3 = run_phase_3(repo_root, strict=strict)
        phase_results.append(res3)
        report.phases["phase_3_routine"] = asdict(res3)

    total_checks = sum(len(p.checks) for p in phase_results)
    failed_checks = 0
    warning_checks = 0
    passed_checks = 0

    for pr in phase_results:
        for chk_name, chk_data in pr.checks.items():
            st = chk_data.get("status", "UNKNOWN")
            if st == "FAILED":
                failed_checks += 1
            elif st == "WARNING":
                warning_checks += 1
            elif st == "PASSED":
                passed_checks += 1
        report.issues.extend(pr.issues)

    report.summary = {
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "warning_checks": warning_checks,
    }

    if failed_checks > 0:
        report.overall_status = "FAILED"
    elif warning_checks > 0:
        report.overall_status = "WARNING"
    else:
        report.overall_status = "PASSED"

    return report


def print_ascii_report(report: ActionPriorityReport) -> None:
    """Emit pure ASCII formatted logs to stdout."""
    print("=" * 78)
    print(f"[INFO] Action Priority Guard for Branch Migration")
    print(f"[INFO] Schema Version : {report.schema_version}")
    print(f"[INFO] Repository Root: {report.repo_root}")
    print(f"[INFO] Phase Filter   : {report.phase_filter}")
    print(f"[INFO] Strict Mode    : {report.strict_mode}")
    print(f"[INFO] Audit Only     : {report.audit_only}")
    print("=" * 78)

    for phase_key, phase_dict in report.phases.items():
        phase_name = phase_dict.get("phase_name", phase_key)
        phase_st = phase_dict.get("status", "UNKNOWN")
        tag = f"[{phase_st}]"
        print(f"\n{tag} --- {phase_name} ---")

        checks = phase_dict.get("checks", {})
        for chk_key, chk_data in checks.items():
            chk_st = chk_data.get("status", "UNKNOWN")
            chk_tag = f"[{chk_st}]"
            print(f"  {chk_tag} Check: {chk_key}")

            if chk_key == "worktrees":
                print(
                    f"        Total: {chk_data.get('total_worktrees', 0)}, "
                    f"Dirty: {len(chk_data.get('dirty_worktrees', []))}, "
                    f"Collisions: {len(chk_data.get('collisions', []))}"
                )
            elif chk_key == "immutable_recovery_refs":
                print(
                    f"        Ref: {chk_data.get('ref')}, "
                    f"Commit: {chk_data.get('commit_sha', '')[:10]}, "
                    f"Matched: {chk_data.get('matched_expected')}"
                )
            elif chk_key == "test_provenance":
                print(
                    f"        Manifests: {chk_data.get('manifests_verified')}/{chk_data.get('manifests_count')}, "
                    f"Guard Present: {chk_data.get('guard_script_present')}"
                )
            elif chk_key == "production_deployment_guards":
                print(
                    f"        HF Space: {chk_data.get('canonical_hf_space')}, "
                    f"Gateway Origin Enforced: {chk_data.get('gateway_origin_enforced')}"
                )
            elif chk_key == "ai_ecosystem_sync":
                print(f"        Ecosystem Sync Passed: {chk_data.get('sync_passed')}")
            elif chk_key == "rust_wheel_and_tests":
                print(
                    f"        Rust Present: {chk_data.get('rust_core_present')}, "
                    f"Python Fallback: {chk_data.get('python_fallback_allowed')}, "
                    f"Test Files: {chk_data.get('test_files_count')}"
                )
            elif chk_key == "viewport_artifacts":
                print(
                    f"        Viewports Verified: {chk_data.get('viewports_verified')}/5, "
                    f"Screenshots Count: {chk_data.get('screenshots_count')}"
                )

            issues = chk_data.get("issues", [])
            for iss in issues:
                print(f"        [ISSUE] {iss.get('code')}: {iss.get('message')}")

    print("\n" + "=" * 78)
    summary = report.summary
    print(
        f"[INFO] Summary: Total={summary.get('total_checks', 0)}, "
        f"Passed={summary.get('passed_checks', 0)}, "
        f"Failed={summary.get('failed_checks', 0)}, "
        f"Warnings={summary.get('warning_checks', 0)}"
    )
    overall_tag = f"[{report.overall_status}]"
    print(f"{overall_tag} Action Priority Guard Final Verdict: {report.overall_status}")
    print("=" * 78)


def main() -> int:
    """CLI entrypoint for Action Priority Guard."""
    parser = argparse.ArgumentParser(
        description="Action Priority Guard for Branch Migration in HoroConsultant",
    )
    parser.add_argument(
        "--phase",
        choices=["all", "immediate", "urgent", "routine", "1", "2", "3"],
        default="all",
        help="Action priority phase to audit (default: all)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Audit only mode (does not modify state)",
    )
    parser.add_argument(
        "--strict",
        "--enforce",
        action="store_true",
        dest="strict",
        help="Fail closed: exit code 1 if any check fails or warnings in strict mode",
    )
    parser.add_argument(
        "--json-output",
        metavar="PATH",
        help="Path to write structured JSON receipt report",
    )
    parser.add_argument(
        "--repo",
        metavar="PATH",
        help="Target git repository root path (default: auto-detected)",
    )

    args = parser.parse_args()

    repo_root = find_repo_root(args.repo)
    report = run_action_priority_guard(
        repo_root=repo_root,
        phase=args.phase,
        strict=args.strict,
        audit_only=args.check,
    )

    print_ascii_report(report)

    if args.json_output:
        out_path = Path(args.json_output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report.as_dict(), f, indent=2, sort_keys=True)
        print(f"[OK] Report JSON written to: {out_path}")

    if args.strict and report.overall_status in ("FAILED", "WARNING"):
        return 1
    if report.overall_status == "FAILED":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
