"""
scripts/publish_space_hf.py
============================
Automated Hugging Face Spaces Publisher & Inspector for HoroConsultant.

Supports both Static Web App SDK (Free for all HF accounts) and Docker SDK.

Usage
-----
    python3 scripts/publish_space_hf.py [--space-id SPACE_ID] [--sdk static|docker] [--private] [--dry-run] [--check-health]
"""

from __future__ import annotations

import argparse
import datetime
import fnmatch
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("publish_space_hf")

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    from huggingface_hub import HfApi, create_repo
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def get_packaging_commit() -> str:
    """Return the immutable packaging commit directly from the Git repository.

    Packaging provenance must never be supplied by environment variables,
    metadata files, or CLI defaults: those sources can describe a different
    checkout. A full revision makes the source-ancestor proof unambiguous.
    """
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--verify", "HEAD^{commit}"],
            cwd=str(ROOT),
            stderr=subprocess.DEVNULL,
            timeout=2,
            text=True,
        ).strip()
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError("packaging commit cannot be resolved directly from Git HEAD") from exc


def source_is_ancestor_of_packaging(source_commit: str, packaging_commit: str) -> bool:
    """Return whether immutable source provenance is reachable from packaging HEAD."""
    try:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", source_commit, packaging_commit],
            cwd=str(ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def _parse_version_metadata(raw_text: str) -> dict[str, Any]:
    """Parse a version JSON object without accepting duplicate keys."""
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        parsed: dict[str, Any] = {}
        for key, value in pairs:
            if key in parsed:
                raise ValueError(f"duplicate version.json key: {key}")
            parsed[key] = value
        return parsed

    parsed = json.loads(raw_text, object_pairs_hook=reject_duplicate_keys)
    if not isinstance(parsed, dict):
        raise ValueError("version.json must contain a JSON object")
    return parsed

# Patterns to ignore during Docker payload calculation and HF upload
IGNORE_PATTERNS = [
    "models/*",
    "kaggle_kernel/*",
    "__pycache__/*",
    "*.pyc",
    ".git/*",
    "*.bin",
    "*.safetensors",
    "*.pt",
    "*.gguf",
    "*.pdf",
    "rag/obsidian_vault/*",
    "obsidian_vault/*",
    ".pytest_cache/*",
    ".ruff_cache/*",
]


def should_ignore(rel_path: str) -> bool:
    """Check if a relative path matches any pattern in IGNORE_PATTERNS."""
    p_str = rel_path.replace("\\", "/")
    parts = p_str.split("/")
    for pattern in IGNORE_PATTERNS:
        pat_clean = pattern.rstrip("/*")
        if pat_clean in parts or fnmatch.fnmatch(p_str, pattern) or fnmatch.fnmatch(Path(p_str).name, pattern):
            return True
        if fnmatch.fnmatch(p_str, f"*{pattern}*"):
            return True
    return False


def stamp_static_html_version(html_text: str, local_version: str, git_commit: str) -> str:
    """Stamp one static HTML document with an exact release version.

    The publisher previously replaced every ``v1.0.0`` substring. Re-publishing an
    already stamped document therefore produced composite labels such as
    ``v1.0.0.<new>.<old>`` while leaving ``CURRENT_PAGE_VERSION`` stale because
    that JavaScript value does not include a leading ``v``. Keep the rewrite
    scoped to the two version surfaces and the supported cache-busting assets.
    """
    html_text = re.sub(
        r'(window\.CURRENT_PAGE_VERSION\s*=\s*["\'])[^"\']+(["\'])',
        rf'\g<1>{local_version}\g<2>',
        html_text,
    )
    html_text = re.sub(
        r'(<p\b[^>]*\bid=["\']footer-version-text["\'][^>]*>[^<]*?\bv)[^\s<—]+',
        rf'\g<1>{local_version}',
        html_text,
    )

    html_text = re.sub(
        r'href="style\.css(\?v=[^"]*)?"',
        f'href="style.css?v={git_commit}"',
        html_text,
    )
    for asset in ("i18n.js", "voice_engine.js", "app.js"):
        html_text = re.sub(
            rf'src="{re.escape(asset)}(\?v=[^"]*)?"',
            f'src="{asset}?v={git_commit}"',
            html_text,
        )
    return html_text


def stage_static_release_assets() -> tuple[Path, dict[str, str], str]:
    """Validate and stage a complete static release before any HF interaction."""
    from project.core.config import get_release_source_identity

    release_identity = get_release_source_identity()
    packaging_commit = get_packaging_commit()
    release_source_commit = release_identity["release_source_commit"]
    if not source_is_ancestor_of_packaging(release_source_commit, packaging_commit):
        raise ValueError(
            "release_source_commit must be an ancestor of the Git HEAD packaging commit"
        )

    static_dir = ROOT / "project" / "static"
    if not static_dir.is_dir():
        raise ValueError(f"static release directory not found: {static_dir}")
    temp_static_dir = Path(tempfile.mkdtemp(prefix="hf_static_staged_"))
    try:
        shutil.copytree(static_dir, temp_static_dir, dirs_exist_ok=True)
        local_version = release_identity["version"]
        version_meta = {
            "version": local_version,
            "release_source_commit": release_source_commit,
            "release_source_revision": release_identity["release_source_revision"],
            "release_source_metadata_path": release_identity["release_source_metadata_path"],
            "release_source_metadata_sha256": release_identity["release_source_metadata_sha256"],
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "status": "production",
        }
        (temp_static_dir / "version.json").write_text(
            json.dumps(version_meta, indent=2), encoding="utf-8"
        )

        sw_file = temp_static_dir / "sw.js"
        if sw_file.exists():
            sw_text = sw_file.read_text(encoding="utf-8")
            sw_file.write_text(
                re.sub(
                    r"const CACHE_VERSION = ['\"][^'\"]+['\"];",
                    f"const CACHE_VERSION = 'v{local_version}';",
                    sw_text,
                ),
                encoding="utf-8",
            )
        app_file = temp_static_dir / "app.js"
        if app_file.exists():
            app_text = app_file.read_text(encoding="utf-8")
            app_file.write_text(
                re.sub(
                    r"const CLIENT_APP_VERSION = ['\"][^'\"]+['\"];",
                    f'const CLIENT_APP_VERSION = "{local_version}";',
                    app_text,
                ),
                encoding="utf-8",
            )
        for html_name in ("index.html", "admin.html"):
            html_path = temp_static_dir / html_name
            if html_path.exists():
                html_path.write_text(
                    stamp_static_html_version(
                        html_path.read_text(encoding="utf-8"),
                        local_version,
                        release_source_commit,
                    ),
                    encoding="utf-8",
                )
    except Exception:
        shutil.rmtree(temp_static_dir, ignore_errors=True)
        raise
    return temp_static_dir, release_identity, packaging_commit


def get_hf_token() -> str | None:
    """Resolve HF token from supported environment variable names."""
    for key in ("HF_TOKEN", "HUGGINGFACE_TOKEN", "HF_API_TOKEN", "HUGGINGFACE_API_KEY", "HUGGING_FACE_TOKEN"):
        token = os.getenv(key)
        if token:
            return token
    return None


def audit_payload(sdk: str = "static") -> tuple[bool, dict[str, Any]]:
    """
    Perform a static audit of files to be uploaded to Hugging Face Spaces.
    Returns (is_valid, payload_summary).
    """
    payload_summary = {
        "sdk": sdk,
        "files": [],
        "total_files": 0,
        "total_bytes": 0,
        "dockerfile_valid": True,
        "requirements_valid": True,
        "project_valid": True,
    }

    if sdk == "static":
        static_dir = ROOT / "project" / "static"
        if not static_dir.exists():
            logger.error(f"❌ project/static/ directory not found at {static_dir}")
            return False, payload_summary

        file_count = 0
        total_bytes = 0
        for p in static_dir.rglob("*"):
            if p.is_file() and not p.name.startswith("."):
                file_count += 1
                total_bytes += p.stat().st_size

        payload_summary["files"].append({"name": "project/static/ Web Demo UI", "size_bytes": total_bytes, "count": file_count})
        payload_summary["total_files"] = file_count
        payload_summary["total_bytes"] = total_bytes
        return True, payload_summary

    # Docker SDK Audit
    dockerfile_path = ROOT / "Dockerfile.hf"
    req_path = ROOT / "requirements.txt"
    project_dir = ROOT / "project"
    tdd_dir = ROOT / "TDD-HORO-v3.0"

    if not dockerfile_path.exists():
        logger.error(f"❌ Dockerfile.hf not found at {dockerfile_path}")
        return False, payload_summary

    dockerfile_content = dockerfile_path.read_text(encoding="utf-8")
    dockerfile_size = dockerfile_path.stat().st_size
    payload_summary["files"].append({"name": "Dockerfile (via Dockerfile.hf)", "size_bytes": dockerfile_size})
    payload_summary["total_files"] += 1
    payload_summary["total_bytes"] += dockerfile_size

    has_port_7860 = "7860" in dockerfile_content
    has_user_1000 = "1000" in dockerfile_content
    has_uvicorn = "uvicorn" in dockerfile_content
    payload_summary["dockerfile_valid"] = has_port_7860 and has_uvicorn

    if not req_path.exists():
        logger.error(f"❌ requirements.txt not found at {req_path}")
        return False, payload_summary

    req_size = req_path.stat().st_size
    payload_summary["files"].append({"name": "requirements.txt", "size_bytes": req_size})
    payload_summary["total_files"] += 1
    payload_summary["total_bytes"] += req_size

    if not project_dir.exists() or not project_dir.is_dir():
        logger.error(f"❌ project/ directory not found at {project_dir}")
        return False, payload_summary

    project_file_count = 0
    project_bytes = 0
    for p in project_dir.rglob("*"):
        if p.is_file() and not p.name.startswith("."):
            rel_p = str(p.relative_to(project_dir))
            if not should_ignore(f"project/{rel_p}") and not should_ignore(rel_p):
                project_file_count += 1
                project_bytes += p.stat().st_size

    payload_summary["files"].append({"name": "project/ directory", "size_bytes": project_bytes, "count": project_file_count})
    payload_summary["total_files"] += project_file_count
    payload_summary["total_bytes"] += project_bytes

    if not tdd_dir.exists() or not tdd_dir.is_dir():
        logger.error(f"[ERROR] TDD-HORO-v3.0/ directory not found at {tdd_dir}")
        return False, payload_summary

    tdd_file_count = 0
    tdd_bytes = 0
    for p in tdd_dir.rglob("*"):
        if p.is_file() and not p.name.startswith("."):
            rel_p = str(p.relative_to(tdd_dir))
            if not should_ignore(f"TDD-HORO-v3.0/{rel_p}") and not should_ignore(rel_p):
                tdd_file_count += 1
                tdd_bytes += p.stat().st_size

    payload_summary["files"].append({"name": "TDD-HORO-v3.0/ directory", "size_bytes": tdd_bytes, "count": tdd_file_count})
    payload_summary["total_files"] += tdd_file_count
    payload_summary["total_bytes"] += tdd_bytes

    is_valid = payload_summary["dockerfile_valid"] and payload_summary["project_valid"]
    return is_valid, payload_summary


def _space_base_url(space_id: str, sdk: str) -> str:
    """Return the public runtime URL for a Hugging Face Space."""
    parts = space_id.split("/", maxsplit=1)
    if len(parts) == 2:
        user, repo = parts[0].lower(), parts[1].lower().replace("_", "-").replace(".", "-")
        host_name = f"{user}-{repo}"
    else:
        host_name = space_id.lower().replace("/", "-").replace("_", "-").replace(".", "-")
    host_suffix = "static.hf.space" if sdk == "static" else "hf.space"
    return f"https://{host_name}.{host_suffix}"


def verify_space_health(
    space_id: str,
    timeout_seconds: float = 10.0,
    sdk: str = "static",
) -> tuple[bool, str, float]:
    """
    Verify live health check status of a deployed HuggingFace Space.
    Returns (is_healthy, status_message, latency_ms).
    """
    if not HTTPX_AVAILABLE:
        return False, "httpx package not installed", 0.0

    space_host = _space_base_url(space_id, sdk)
    t0 = time.monotonic()

    try:
        with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
            if sdk == "static":
                root_res = client.get(f"{space_host}/")
                version_res = client.get(f"{space_host}/version.json")
                latency_ms = round((time.monotonic() - t0) * 1000, 2)
                if root_res.status_code != 200:
                    return False, f"Static root HTTP {root_res.status_code}", latency_ms
                if version_res.status_code != 200:
                    return False, f"version.json HTTP {version_res.status_code}", latency_ms
                try:
                    version_meta = _parse_version_metadata(version_res.text)
                except ValueError as exc:
                    return False, f"version.json is not valid JSON: {exc}", latency_ms
                required_meta = (
                    "version",
                    "release_source_commit",
                    "release_source_revision",
                    "release_source_metadata_path",
                    "release_source_metadata_sha256",
                    "status",
                )
                missing_meta = [key for key in required_meta if not version_meta.get(key)]
                forbidden_meta = [key for key in ("commit", "packaging_commit") if key in version_meta]
                if missing_meta or forbidden_meta or version_meta.get("status") != "production":
                    return False, f"Invalid production version metadata (missing={missing_meta})", latency_ms
                return (
                    True,
                    "Static root and version.json OK "
                    f"(version={version_meta['version']}, source={version_meta['release_source_commit']})",
                    latency_ms,
                )

            res = client.get(f"{space_host}/health")
            latency_ms = round((time.monotonic() - t0) * 1000, 2)

            if res.status_code == 200:
                body = res.json() if "application/json" in res.headers.get("content-type", "") else res.text
                return True, f"HTTP 200 OK — {body}", latency_ms
            else:
                return False, f"HTTP {res.status_code} — {res.text[:100]}", latency_ms

    except httpx.ConnectTimeout:
        return False, "Connection Timeout (Space may be sleeping or initializing)", 0.0
    except Exception as e:
        return False, f"Connection error: {e}", 0.0


def publish_space(space_id: str, sdk: str = "static", private: bool = False, dry_run: bool = False) -> bool:
    """Upload project to Hugging Face Spaces with Static or Docker SDK."""
    logger.info(f"🔍 Performing Payload Audit for Hugging Face Spaces deployment (SDK: {sdk})...")
    is_valid, summary = audit_payload(sdk=sdk)

    total_mb = round(summary["total_bytes"] / (1024 * 1024), 2)

    print("\n" + "=" * 70)
    print("  HUGGING FACE SPACES DEPLOYMENT PAYLOAD AUDIT")
    print("=" * 70)
    print(f"  Target Space ID      : {space_id}")
    print(f"  Deployment SDK       : {sdk.upper()}")
    print(f"  Filtered File Count  : {summary['total_files']} files")
    print(f"  Filtered Payload Size: {total_mb} MB ({summary['total_bytes']:,} bytes)")
    print("=" * 70)

    for f in summary["files"]:
        count_str = f" ({f['count']} files)" if "count" in f else ""
        print(f"  • {f['name']:<40} : {round(f['size_bytes']/1024, 1):>7} KB{count_str}")
    print("=" * 70 + "\n")

    if not is_valid:
        logger.error("❌ Payload validation failed. Aborting deployment.")
        return False

    temp_static_dir: Path | None = None
    release_identity: dict[str, str] | None = None
    packaging_commit: str | None = None
    if sdk == "static":
        try:
            temp_static_dir, release_identity, packaging_commit = stage_static_release_assets()
        except ValueError as exc:
            logger.error(f"[ERROR] Static release provenance validation failed. Aborting deployment: {exc}")
            return False

    if dry_run:
        logger.info("🧪 [DRY-RUN MODE] Payload audit completed successfully. No remote changes made.")
        if temp_static_dir is not None:
            shutil.rmtree(temp_static_dir, ignore_errors=True)
        return True

    # Live Deployment Execution
    if not HF_AVAILABLE:
        logger.error("❌ huggingface_hub package not found. Run 'pip install huggingface_hub'")
        if temp_static_dir is not None:
            shutil.rmtree(temp_static_dir, ignore_errors=True)
        return False

    token = get_hf_token()
    if not token:
        logger.error(
            "❌ HF token environment variable not found. "
            "Set one of: HF_TOKEN, HUGGINGFACE_TOKEN, HF_API_TOKEN, HUGGINGFACE_API_KEY, HUGGING_FACE_TOKEN."
        )
        if temp_static_dir is not None:
            shutil.rmtree(temp_static_dir, ignore_errors=True)
        return False

    api = HfApi(token=token)

    try:
        user_info = api.whoami()
        logger.info(f"🔐 Authenticated as Hugging Face user: {user_info['name']}")
    except Exception as e:
        logger.error(f"❌ HF Token authentication failed: {e}")
        if temp_static_dir is not None:
            shutil.rmtree(temp_static_dir, ignore_errors=True)
        return False

    logger.info(f"📦 Creating/verifying Hugging Face Space '{space_id}' (SDK: {sdk})...")
    try:
        create_repo(
            repo_id=space_id,
            token=token,
            private=private,
            exist_ok=True,
            repo_type="space",
            space_sdk=sdk,
        )
        logger.info(f"✅ Space ready: https://huggingface.co/spaces/{space_id}")
    except Exception as e:
        logger.warning(f"⚠️ Space creation note: {e}")

    logger.info(f"🚀 Uploading demo files to Space '{space_id}'...")

    try:
        if sdk == "static":
            # Generate and upload README.md with Hugging Face Space YAML frontmatter for Static SDK
            hf_static_readme = """---
title: Horoconsultant Core Backend
emoji: 🔮
colorFrom: indigo
colorTo: purple
sdk: static
pinned: false
---

# 🔮 HoroConsultant — Computational Metaphysics Engine Frontend
"""
            readme_path = ROOT / "README.hf.md"
            readme_path.write_text(hf_static_readme, encoding="utf-8")

            api.upload_file(
                path_or_fileobj=str(readme_path),
                path_in_repo="README.md",
                repo_id=space_id,
                repo_type="space",
            )
            # Remove Dockerfile if it exists in HF repo to force static mode
            try:
                api.delete_file("Dockerfile", repo_id=space_id, repo_type="space")
            except Exception:
                pass

            assert temp_static_dir is not None
            assert release_identity is not None
            assert packaging_commit is not None
            local_version = release_identity["version"]
            release_source_commit = release_identity["release_source_commit"]

            logger.info(
                "[INFO] Staged static assets with source version "
                f"'v{local_version}' (source={release_source_commit}, packaging={packaging_commit})..."
            )

            # Upload static assets to root
            api.upload_folder(
                folder_path=str(temp_static_dir),
                repo_id=space_id,
                repo_type="space",
            )
            # ALSO upload static assets under 'static/' path in repo
            # so that both /app.js, /style.css AND /static/app.js, /static/style.css work without 404!
            api.upload_folder(
                folder_path=str(temp_static_dir),
                path_in_repo="static",
                repo_id=space_id,
                repo_type="space",
            )
            # Ensure index.html exists at root
            if (temp_static_dir / "index.html").exists():
                api.upload_file(
                    path_or_fileobj=str(temp_static_dir / "index.html"),
                    path_in_repo="index.html",
                    repo_id=space_id,
                    repo_type="space",
                )
            shutil.rmtree(temp_static_dir, ignore_errors=True)
        else:
            # Generate and upload README.md with Hugging Face Space YAML frontmatter for Docker SDK
            hf_readme_content = """---
title: Horoconsultant Core Backend
emoji: 🔮
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# 🔮 HoroConsultant — Computational Metaphysics Engine Core Backend

High-Precision 10-Domain Computational Metaphysics Engine, True Solar Time Engine, Multi-Agent Gemini & Local Ollama Hybrid Routing, FAISS Classical Vault RAG, Rust Fast Math Acceleration, and HITL Review Studio.
"""
            readme_path = ROOT / "README.hf.md"
            readme_path.write_text(hf_readme_content, encoding="utf-8")

            api.upload_file(
                path_or_fileobj=str(readme_path),
                path_in_repo="README.md",
                repo_id=space_id,
                repo_type="space",
            )
            api.upload_file(
                path_or_fileobj=str(ROOT / "Dockerfile.hf"),
                path_in_repo="Dockerfile",
                repo_id=space_id,
                repo_type="space",
            )
            api.upload_file(
                path_or_fileobj=str(ROOT / "requirements.txt"),
                path_in_repo="requirements.txt",
                repo_id=space_id,
                repo_type="space",
            )
            # Dockerfile.hf imports runtime helpers from these build-context paths.
            # Keep the local .env out of the payload; only the non-secret example is needed.
            api.upload_file(
                path_or_fileobj=str(ROOT / ".env.example"),
                path_in_repo=".env.example",
                repo_id=space_id,
                repo_type="space",
            )
            api.upload_folder(
                folder_path=str(ROOT / "scripts"),
                path_in_repo="scripts",
                repo_id=space_id,
                repo_type="space",
                ignore_patterns=IGNORE_PATTERNS,
            )
            api.upload_folder(
                folder_path=str(ROOT / "tests"),
                path_in_repo="tests",
                repo_id=space_id,
                repo_type="space",
                ignore_patterns=IGNORE_PATTERNS,
            )
            api.upload_folder(
                folder_path=str(ROOT / "rust_core"),
                path_in_repo="rust_core",
                repo_id=space_id,
                repo_type="space",
                ignore_patterns=[
                    *IGNORE_PATTERNS,
                    "rust_core/target/*",
                    "rust_core/*.so",
                    "rust_core/*.dylib",
                ],
            )
            api.upload_folder(
                folder_path=str(ROOT / "project"),
                path_in_repo="project",
                repo_id=space_id,
                repo_type="space",
                ignore_patterns=IGNORE_PATTERNS,
            )
            api.upload_folder(
                folder_path=str(ROOT / "TDD-HORO-v3.0"),
                path_in_repo="TDD-HORO-v3.0",
                repo_id=space_id,
                repo_type="space",
                ignore_patterns=IGNORE_PATTERNS,
            )

        logger.info("\n🎉 Demo successfully published to Hugging Face Space!")
        logger.info(f"🔗 View Live Demo Space: https://huggingface.co/spaces/{space_id}")

        # Auto-stamp local source files to match the deployed version
        try:
            import subprocess as _sp
            stamp_script = ROOT / "scripts" / "stamp_version.py"
            if stamp_script.exists():
                _sp.run([sys.executable, str(stamp_script)], cwd=str(ROOT), check=False)
                logger.info("📌 Local source files stamped with deployed version.")
        except Exception as stamp_err:
            logger.warning(f"⚠️ Auto-stamp note: {stamp_err}")

        return True

    except Exception as e:
        logger.error(f"❌ Upload failed: {e}")
        return False
    finally:
        if temp_static_dir is not None:
            shutil.rmtree(temp_static_dir, ignore_errors=True)


def verify_live_deployment_version(
    space_id: str,
    timeout_seconds: float = 10.0,
    sdk: str = "static",
) -> tuple[bool, str, dict[str, Any]]:
    """
    Verify that the live Space is running the exact local release version.

    Static verification is intentionally fail-closed: every release metadata and
    client cache surface must be reachable and match. A retired external backend
    is not consulted because it is not evidence for the deployed Static Space.
    Returns (is_matched, message, details).
    """
    from project.core.config import get_release_source_identity

    details = {
        # expected_commit is retained as a compatibility alias for the source
        # identity. Packaging HEAD is reported separately and is never a gate.
        "expected_commit": None,
        "expected_version": None,
        "expected_release_source_commit": None,
        "expected_release_version": None,
        "packaging_commit": None,
        "sdk": sdk,
        "base_url": _space_base_url(space_id, sdk),
        "checks": {},
        "errors": [],
        "failed_checks": [],
        "matched": False,
    }

    if not HTTPX_AVAILABLE:
        details["errors"].append("httpx package not installed")
        return False, "[ERROR] Live verification requires httpx.", details

    try:
        release_identity = get_release_source_identity()
        packaging_commit = get_packaging_commit()
        if not source_is_ancestor_of_packaging(
            release_identity["release_source_commit"], packaging_commit
        ):
            raise ValueError(
                "release_source_commit is not an ancestor of the Git HEAD packaging commit"
            )
    except ValueError as exc:
        details["errors"].append(f"local release identity invalid: {exc}")
        return False, "[ERROR] Live verification requires valid local release metadata.", details

    local_commit = release_identity["release_source_commit"]
    local_version = release_identity["version"]
    details.update(
        {
            "expected_commit": local_commit,
            "expected_version": local_version,
            "expected_release_source_commit": local_commit,
            "expected_release_version": local_version,
            "expected_release_source_revision": release_identity["release_source_revision"],
            "expected_release_source_metadata_path": release_identity["release_source_metadata_path"],
            "expected_release_source_metadata_sha256": release_identity["release_source_metadata_sha256"],
            "release_metadata_path": release_identity["metadata_path"],
            "packaging_commit": packaging_commit,
        }
    )

    base_url = details["base_url"]
    try:
        with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
            if sdk == "docker":
                res = client.get(f"{base_url}/health")
                health_data = res.json() if res.status_code == 200 else {}
                if not isinstance(health_data, dict):
                    health_data = {}
                details["checks"] = {
                    "health_http_200": res.status_code == 200,
                    "health_commit_exact": health_data.get("git_commit") == local_commit,
                    "health_version_exact": health_data.get("version") == local_version,
                }
            else:
                paths = ("version.json", "index.html", "app.js", "sw.js", "v3_tokens.css")
                responses = {path: client.get(f"{base_url}/{path}") for path in paths}
                for path, response in responses.items():
                    details["checks"][f"{path}_http_200"] = response.status_code == 200

                version_meta: dict[str, Any] = {}
                if responses["version.json"].status_code == 200:
                    try:
                        version_text = responses["version.json"].text
                        version_meta = _parse_version_metadata(version_text)
                    except ValueError as exc:
                        details["errors"].append(f"version.json invalid JSON: {exc}")

                index_text = responses["index.html"].text
                app_text = responses["app.js"].text
                sw_text = responses["sw.js"].text
                css_text = responses["v3_tokens.css"].text

                page_versions = re.findall(
                    r'window\.CURRENT_PAGE_VERSION\s*=\s*["\']([^"\']+)["\']',
                    index_text,
                )
                footer_versions = re.findall(
                    r'<p\b[^>]*\bid=["\']footer-version-text["\'][^>]*>[^<]*?\bv([^\s<—]+)',
                    index_text,
                )
                client_versions = re.findall(
                    r'const CLIENT_APP_VERSION\s*=\s*["\']([^"\']+)["\'];',
                    app_text,
                )
                cache_versions = re.findall(
                    r'const CACHE_VERSION\s*=\s*["\']([^"\']+)["\'];',
                    sw_text,
                )

                def cache_ref_versions(attribute: str, asset: str) -> list[str]:
                    return re.findall(
                        rf'{attribute}=["\']{re.escape(asset)}(?:\?v=([^"\']*))?["\']',
                        index_text,
                    )

                live_source_commit = version_meta.get("release_source_commit")

                details["checks"].update(
                    {
                        "version_json_version_exact": version_meta.get("version") == local_version,
                        "version_json_source_commit_exact": live_source_commit == local_commit,
                        "version_json_source_commit_exactly_once": (
                            isinstance(live_source_commit, str)
                            and re.fullmatch(r"[0-9a-f]{7,40}", live_source_commit) is not None
                            and "commit" not in version_meta
                            and "packaging_commit" not in version_meta
                        ),
                        "version_json_version_binds_source_commit": (
                            isinstance(version_meta.get("version"), str)
                            and version_meta.get("version", "").endswith(f".{live_source_commit}")
                        ),
                        "version_json_source_revision_exact": (
                            version_meta.get("release_source_revision")
                            == release_identity["release_source_revision"]
                        ),
                        "version_json_source_metadata_path_exact": (
                            version_meta.get("release_source_metadata_path")
                            == release_identity["release_source_metadata_path"]
                        ),
                        "version_json_source_metadata_digest_exact": (
                            version_meta.get("release_source_metadata_sha256")
                            == release_identity["release_source_metadata_sha256"]
                        ),
                        "version_json_production": version_meta.get("status") == "production",
                        "current_page_version_exact": page_versions == [local_version],
                        "footer_version_exact": footer_versions == [local_version],
                        "style_cache_ref_exact": cache_ref_versions("href", "style.css") == [local_commit],
                        "i18n_cache_ref_exact": cache_ref_versions("src", "i18n.js") == [local_commit],
                        "voice_cache_ref_exact": cache_ref_versions("src", "voice_engine.js") == [local_commit],
                        "app_cache_ref_exact": cache_ref_versions("src", "app.js") == [local_commit],
                        "client_app_version_exact": client_versions == [local_version],
                        "service_worker_cache_version_exact": cache_versions == [f"v{local_version}"],
                        "v3_tokens_css_nonempty": (
                            responses["v3_tokens.css"].status_code == 200 and bool(css_text.strip())
                        ),
                    }
                )
    except (httpx.HTTPError, TypeError, ValueError) as exc:
        details["errors"].append(f"request failure: {exc}")

    failed_checks = [name for name, passed in details["checks"].items() if not passed]
    is_matched = bool(details["checks"]) and not failed_checks and not details["errors"]
    details["matched"] = is_matched
    details["failed_checks"] = failed_checks

    if is_matched:
        msg = (
            f"[OK] Live deployment matches release source '{local_commit}' and version "
            f"'{local_version}' (packaging commit '{packaging_commit}')."
        )
    else:
        failure_summary = ", ".join(failed_checks + details["errors"]) or "no verification evidence"
        msg = f"[ERROR] Live deployment does not match the expected release: {failure_summary}."

    return is_matched, msg, details


def main():
    parser = argparse.ArgumentParser(description="Publish HoroConsultant Demo to Hugging Face Space")
    username = os.getenv("HF_USERNAME", "pphothidaen")
    default_space = f"{username}/horoconsultant-core-backend"

    parser.add_argument("--space-id", default=default_space, help=f"HF Space ID (default: {default_space})")
    parser.add_argument("--sdk", choices=["static", "docker"], default="static", help="Space SDK type (default: static)")
    parser.add_argument("--private", action="store_true", help="Create private Space")
    parser.add_argument("--dry-run", action="store_true", help="Perform static payload audit without uploading")
    parser.add_argument("--check-health", action="store_true", help="Check live health status of target Space")
    parser.add_argument("--verify-version", action="store_true", help="Verify live deployment is running latest git commit version")

    args = parser.parse_args()

    if args.verify_version:
        logger.info(f"🔎 Verifying live deployment version against git commit for '{args.space_id}'...")
        is_matched, msg, details = verify_live_deployment_version(args.space_id, sdk=args.sdk)
        print("\n" + "=" * 70)
        print("  LIVE DEPLOYMENT VERSION VERIFICATION SUMMARY")
        print("=" * 70)
        print(f"  Target Space ID  : {args.space_id}")
        print(f"  Expected Commit  : {details['expected_commit']}")
        print(f"  Expected Version : {details['expected_version']}")
        print(f"  Verification     : {'✅ PASSED (LATEST VERSION CONFIRMED)' if is_matched else '⚠️ PENDING / MISMATCH'}")
        print(f"  Message          : {msg}")
        print("=" * 70 + "\n")
        sys.exit(0 if is_matched else 1)

    if args.check_health:
        logger.info(f"📡 Checking live health status for Space '{args.space_id}'...")
        is_healthy, status_msg, latency_ms = verify_space_health(args.space_id, sdk=args.sdk)
        print("\n" + "=" * 65)
        print("  HUGGING FACE SPACE HEALTH CHECK SUMMARY")
        print("=" * 65)
        print(f"  Target Space ID : {args.space_id}")
        print(f"  Health Status   : {'✅ HEALTHY' if is_healthy else '⚠️ UNHEALTHY / UNREACHABLE'}")
        print(f"  Latency         : {latency_ms} ms")
        print(f"  Details         : {status_msg}")
        print("=" * 65 + "\n")
        sys.exit(0 if is_healthy else 1)

    success = publish_space(args.space_id, sdk=args.sdk, private=args.private, dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
