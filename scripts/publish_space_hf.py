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

import os
import sys
import argparse
import logging
import fnmatch
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
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


def audit_payload(sdk: str = "static") -> Tuple[bool, Dict[str, Any]]:
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

    is_valid = payload_summary["dockerfile_valid"] and payload_summary["project_valid"]
    return is_valid, payload_summary


def verify_space_health(space_id: str, timeout_seconds: float = 10.0) -> Tuple[bool, str, float]:
    """
    Verify live health check status of a deployed HuggingFace Space.
    Returns (is_healthy, status_message, latency_ms).
    """
    if not HTTPX_AVAILABLE:
        return False, "httpx package not installed", 0.0

    parts = space_id.split("/")
    if len(parts) == 2:
        user, repo = parts[0].lower(), parts[1].lower().replace("_", "-").replace(".", "-")
        space_host = f"https://{user}-{repo}.hf.space"
    else:
        space_host = f"https://{space_id.lower().replace('/', '-')}.hf.space"

    health_url = f"{space_host}/health"
    t0 = time.monotonic()

    try:
        with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
            res = client.get(health_url)
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

    if dry_run:
        logger.info("🧪 [DRY-RUN MODE] Payload audit completed successfully. No remote changes made.")
        token = os.getenv("HF_TOKEN")
        if token and HF_AVAILABLE:
            try:
                api = HfApi(token=token)
                user_info = api.whoami()
                logger.info(f"🔐 HF API Token Verified (Authenticated as: {user_info.get('name')})")
            except Exception as e:
                logger.warning(f"⚠️ HF API Token Note: {e}")
        return True

    # Live Deployment Execution
    if not HF_AVAILABLE:
        logger.error("❌ huggingface_hub package not found. Run 'pip install huggingface_hub'")
        return False

    token = os.getenv("HF_TOKEN")
    if not token:
        logger.error("❌ HF_TOKEN environment variable not found in .env")
        return False

    api = HfApi(token=token)

    try:
        user_info = api.whoami()
        logger.info(f"🔐 Authenticated as Hugging Face user: {user_info['name']}")
    except Exception as e:
        logger.error(f"❌ HF Token authentication failed: {e}")
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

            static_dir = ROOT / "project" / "static"
            api.upload_folder(
                folder_path=str(static_dir),
                repo_id=space_id,
                repo_type="space",
            )
            # Create index.html at root if not directly copied
            if (static_dir / "index.html").exists():
                api.upload_file(
                    path_or_fileobj=str(static_dir / "index.html"),
                    path_in_repo="index.html",
                    repo_id=space_id,
                    repo_type="space",
                )
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
            api.upload_folder(
                folder_path=str(ROOT / "project"),
                path_in_repo="project",
                repo_id=space_id,
                repo_type="space",
                ignore_patterns=IGNORE_PATTERNS,
            )

        logger.info(f"\n🎉 Demo successfully published to Hugging Face Space!")
        logger.info(f"🔗 View Live Demo Space: https://huggingface.co/spaces/{space_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Upload failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Publish HoroConsultant Demo to Hugging Face Space")
    username = os.getenv("HF_USERNAME", "pphothidaen")
    default_space = f"{username}/horoconsultant-core-backend"

    parser.add_argument("--space-id", default=default_space, help=f"HF Space ID (default: {default_space})")
    parser.add_argument("--sdk", choices=["static", "docker"], default="static", help="Space SDK type (default: static)")
    parser.add_argument("--private", action="store_true", help="Create private Space")
    parser.add_argument("--dry-run", action="store_true", help="Perform static payload audit without uploading")
    parser.add_argument("--check-health", action="store_true", help="Check live health status of target Space")

    args = parser.parse_args()

    if args.check_health:
        logger.info(f"📡 Checking live health status for Space '{args.space_id}'...")
        is_healthy, status_msg, latency_ms = verify_space_health(args.space_id)
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
