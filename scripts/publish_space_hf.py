"""Fail-closed publisher and inspector for the canonical HF Docker backend."""

from __future__ import annotations

import argparse
import datetime
import fnmatch
import hashlib
import json
import logging
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("publish_space_hf")

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    from huggingface_hub import CommitOperationAdd, CommitOperationDelete, HfApi

    try:
        from huggingface_hub.errors import HfHubHTTPError
    except ImportError:  # huggingface_hub 0.25.x compatibility
        from huggingface_hub.utils import HfHubHTTPError

    HF_AVAILABLE = True
except ImportError:
    CommitOperationAdd = None  # type: ignore[assignment,misc]
    CommitOperationDelete = None  # type: ignore[assignment,misc]
    HfApi = None  # type: ignore[assignment,misc]
    HfHubHTTPError = Exception  # type: ignore[assignment,misc]
    HF_AVAILABLE = False

# Legacy tests and callers may probe this name. Repository creation is disabled
# and this sentinel is never called by the governed publisher.
create_repo = None

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CANONICAL_SPACE_ID = "pphothidaen/horoconsultant-core-backend"
CANONICAL_SDK = "docker"
CANONICAL_BRANCH = "main"
REPO_TYPE = "space"
MANIFEST_SCHEMA_PATH = ROOT / "project" / "schemas" / "release-manifest-v1.schema.json"
RECEIPT_SCHEMA_PATH = ROOT / "project" / "schemas" / "release-receipt-v1.schema.json"
MANIFEST_SCHEMA_SHA256 = (
    "7055f6b371900c0c7ab6912fc54f052db8dd247dc07af6b60d3c31f091668079"
)
RECEIPT_SCHEMA_SHA256 = (
    "d816e7fea5230a24ccf9fd98c58e7fa8f91d2eb10ad345ccb9a8620faf932343"
)
DEFAULT_MANIFEST_PATH = "hf-release-manifest.json"
DEFAULT_RECEIPT_PATH = "hf-release-receipt.json"
GIT_REVISION_RE = re.compile(r"[0-9a-f]{40}")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
SOURCE_COMMIT_RE = re.compile(r"[0-9a-f]{7,40}")
VERSION_RE = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+\.([0-9a-f]{7,40})")
PRIOR_TREE_DOWNLOAD_WORKERS = 4


class PublisherError(RuntimeError):
    """Typed error whose public rendering never includes provider or local data."""

    def __init__(self, code: str, failure_class: str = "internal_error") -> None:
        super().__init__(code)
        self.code = code
        self.failure_class = failure_class


@dataclass(frozen=True)
class BundleFile:
    """One immutable Git-blob-backed upload mapping."""

    path: str
    source_path: str
    data: bytes
    source_blob_oid: str


@dataclass(frozen=True)
class ReleaseBundle:
    """The exact bytes and validated manifest shared by dry-run and live publish."""

    files: tuple[BundleFile, ...]
    manifest: dict[str, Any]


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise PublisherError("INVALID_CANONICAL_JSON", "invalid_manifest") from exc


def _object_digest(value: dict[str, Any], digest_field: str) -> str:
    unsigned = dict(value)
    unsigned.pop(digest_field, None)
    return hashlib.sha256(_canonical_json(unsigned)).hexdigest()


def _strict_json_bytes(raw: bytes, error_code: str) -> Any:
    def reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, member in pairs:
            if key in value:
                raise PublisherError(error_code)
            value[key] = member
        return value

    def reject_constant(_value: str) -> None:
        raise PublisherError(error_code)

    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=reject_pairs,
            parse_constant=reject_constant,
        )
    except PublisherError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PublisherError(error_code) from exc


def _load_frozen_schema(
    path: Path, expected_sha256: str, error_code: str
) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise PublisherError(error_code) from exc
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise PublisherError(error_code)
    schema = _strict_json_bytes(raw, error_code)
    if not isinstance(schema, dict):
        raise PublisherError(error_code)
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        raise PublisherError(error_code) from exc
    return schema


def _schema_validate(instance: dict[str, Any], *, receipt: bool = False) -> None:
    path = RECEIPT_SCHEMA_PATH if receipt else MANIFEST_SCHEMA_PATH
    digest = RECEIPT_SCHEMA_SHA256 if receipt else MANIFEST_SCHEMA_SHA256
    code = "INVALID_RELEASE_RECEIPT" if receipt else "INVALID_RELEASE_MANIFEST"
    schema = _load_frozen_schema(path, digest, code)
    errors = list(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(
            instance
        )
    )
    if errors:
        failure = "internal_error" if receipt else "invalid_manifest"
        raise PublisherError(code, failure)


def _safe_bundle_path(path: str) -> bool:
    if (
        not path
        or len(path) > 1024
        or path.startswith("/")
        or "\\" in path
        or "//" in path
    ):
        return False
    if any(part in ("", ".", "..") for part in path.split("/")):
        return False
    return not any(ord(char) < 32 or ord(char) == 127 for char in path)


def _git_bytes(args: list[str], error_code: str) -> bytes:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=str(ROOT), stderr=subprocess.DEVNULL, timeout=30
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise PublisherError(error_code, "invalid_provenance") from exc


def _git_text(args: list[str], error_code: str) -> str:
    try:
        return _git_bytes(args, error_code).decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError as exc:
        raise PublisherError(error_code, "invalid_provenance") from exc


def _assert_clean_packaging_commit() -> str:
    packaging_commit = _git_text(
        ["rev-parse", "--verify", "HEAD^{commit}"], "INVALID_PACKAGING_COMMIT"
    )
    if GIT_REVISION_RE.fullmatch(packaging_commit) is None:
        raise PublisherError("INVALID_PACKAGING_COMMIT", "invalid_provenance")
    if not os.getenv("HF_ALLOW_DIRTY_WORKTREE"):
        status_output = _git_bytes(
            ["status", "--porcelain=v1", "-z", "--untracked-files=all"],
            "DIRTY_WORKTREE",
        )
        if status_output:
            raise PublisherError("DIRTY_WORKTREE", "dirty_worktree")
        submodules = _git_text(
            ["submodule", "status", "--recursive"], "INVALID_SUBMODULE_STATE"
        )
        for line in submodules.splitlines():
            if not re.fullmatch(r" [0-9a-f]{40}(?: .*)?", line):
                raise PublisherError("INVALID_SUBMODULE_STATE", "dirty_worktree")
    return packaging_commit


def _git_blob_oid(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


def _git_lfs_pointer_blob_oid(data: bytes) -> str:
    pointer = (
        "version https://git-lfs.github.com/spec/v1\n"
        f"oid sha256:{hashlib.sha256(data).hexdigest()}\n"
        f"size {len(data)}\n"
    ).encode("ascii")
    return _git_blob_oid(pointer)


def _git_blob_batch(oids: list[str], error_code: str) -> dict[str, bytes]:
    unique_oids = list(dict.fromkeys(oids))
    if any(re.fullmatch(r"[0-9a-f]{40}", oid) is None for oid in unique_oids):
        raise PublisherError(error_code, "invalid_provenance")
    try:
        completed = subprocess.run(
            ["git", "cat-file", "--batch"],
            cwd=str(ROOT),
            input=("\n".join(unique_oids) + "\n").encode("ascii"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=60,
            check=True,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise PublisherError(error_code, "invalid_provenance") from exc
    output = completed.stdout
    cursor = 0
    blobs: dict[str, bytes] = {}
    for expected_oid in unique_oids:
        line_end = output.find(b"\n", cursor)
        if line_end < 0:
            raise PublisherError(error_code, "invalid_provenance")
        try:
            header_oid, object_type, raw_size = output[cursor:line_end].split(b" ", 2)
            size = int(raw_size)
        except (ValueError, UnicodeError) as exc:
            raise PublisherError(error_code, "invalid_provenance") from exc
        cursor = line_end + 1
        data_end = cursor + size
        if (
            header_oid.decode("ascii", errors="strict") != expected_oid
            or object_type != b"blob"
            or size < 0
            or data_end >= len(output)
            or output[data_end : data_end + 1] != b"\n"
        ):
            raise PublisherError(error_code, "invalid_provenance")
        blobs[expected_oid] = output[cursor:data_end]
        cursor = data_end + 1
    if cursor != len(output):
        raise PublisherError(error_code, "invalid_provenance")
    return blobs


def _payload_destination(source_path: str) -> str | None:
    exact = {
        ".env.example": ".env.example",
        "Dockerfile.hf": "Dockerfile",
        "README.hf.md": "README.md",
        "requirements.txt": "requirements.txt",
    }
    if source_path in exact:
        return exact[source_path]
    prefixes = ("scripts/", "tests/", "rust_core/", "project/", "TDD-HORO-v3.0/")
    if source_path.startswith(prefixes) and not should_ignore(source_path):
        return source_path
    return None


def _tracked_release_files(packaging_commit: str) -> tuple[BundleFile, ...]:
    raw_tree = _git_bytes(
        ["ls-tree", "-r", "-z", "--full-tree", packaging_commit],
        "INVALID_GIT_TREE",
    )
    selected: list[tuple[str, str, str]] = []
    destinations: set[str] = set()
    for raw_record in raw_tree.split(b"\0"):
        if not raw_record:
            continue
        try:
            metadata, raw_path = raw_record.split(b"\t", 1)
            mode, object_type, raw_oid = metadata.split(b" ", 2)
            source_path = raw_path.decode("utf-8", errors="strict")
            oid = raw_oid.decode("ascii", errors="strict")
        except (ValueError, UnicodeDecodeError) as exc:
            raise PublisherError("INVALID_GIT_TREE", "invalid_provenance") from exc
        destination = _payload_destination(source_path)
        if destination is None:
            continue
        if (
            mode != b"100644"
            or object_type != b"blob"
            or re.fullmatch(r"[0-9a-f]{40}", oid) is None
            or not _safe_bundle_path(source_path)
            or not _safe_bundle_path(destination)
        ):
            raise PublisherError("INVALID_PAYLOAD_FILE", "invalid_manifest")
        if destination in destinations:
            raise PublisherError("DUPLICATE_PAYLOAD_PATH", "invalid_manifest")
        destinations.add(destination)
        local_path = ROOT / source_path
        try:
            local_stat = local_path.lstat()
        except OSError as exc:
            raise PublisherError("INVALID_PAYLOAD_FILE", "invalid_manifest") from exc
        if (
            not stat.S_ISREG(local_stat.st_mode)
            or stat.S_IMODE(local_stat.st_mode) != 0o644
            or local_stat.st_nlink < 1
        ):
            raise PublisherError("INVALID_PAYLOAD_FILE", "invalid_manifest")
        selected.append((destination, source_path, oid))
    blob_data = _git_blob_batch([item[2] for item in selected], "INVALID_GIT_BLOB")
    files: list[BundleFile] = []
    for destination, source_path, oid in selected:
        data = blob_data[oid]
        if _git_blob_oid(data) != oid:
            raise PublisherError("INVALID_GIT_BLOB", "invalid_provenance")
        files.append(BundleFile(destination, source_path, data, oid))
    files.sort(key=lambda item: item.path.encode("utf-8"))
    if not files:
        raise PublisherError("EMPTY_RELEASE_BUNDLE", "invalid_manifest")
    return tuple(files)


def _release_identity_from_bundle(
    files: tuple[BundleFile, ...], packaging_commit: str
) -> dict[str, str]:
    matches = [item for item in files if item.path == "project/static/version.json"]
    if len(matches) != 1:
        raise PublisherError("INVALID_RELEASE_PROVENANCE", "invalid_provenance")
    metadata = _strict_json_bytes(matches[0].data, "INVALID_RELEASE_PROVENANCE")
    required = {
        "version",
        "release_source_commit",
        "release_source_revision",
        "release_source_metadata_path",
        "release_source_metadata_sha256",
    }
    if not isinstance(metadata, dict) or set(metadata) != required:
        raise PublisherError("INVALID_RELEASE_PROVENANCE", "invalid_provenance")
    if not all(isinstance(metadata[key], str) for key in required):
        raise PublisherError("INVALID_RELEASE_PROVENANCE", "invalid_provenance")
    version = metadata["version"]
    source_commit = metadata["release_source_commit"]
    source_revision = metadata["release_source_revision"]
    source_path = metadata["release_source_metadata_path"]
    source_digest = metadata["release_source_metadata_sha256"]
    version_match = VERSION_RE.fullmatch(version)
    if (
        version_match is None
        or SOURCE_COMMIT_RE.fullmatch(source_commit) is None
        or version_match.group(1) != source_commit
        or GIT_REVISION_RE.fullmatch(source_revision) is None
        or source_path != "project/static/version.json"
        or SHA256_RE.fullmatch(source_digest) is None
    ):
        raise PublisherError("INVALID_RELEASE_PROVENANCE", "invalid_provenance")
    canonical_source = {
        "release_source_commit": source_commit,
        "release_source_metadata_path": source_path,
        "release_source_revision": source_revision,
        "version": version,
    }
    if hashlib.sha256(_canonical_json(canonical_source)).hexdigest() != source_digest:
        raise PublisherError("INVALID_RELEASE_PROVENANCE", "invalid_provenance")
    resolved = _git_text(
        ["rev-parse", "--verify", f"{source_commit}^{{commit}}"],
        "INVALID_RELEASE_PROVENANCE",
    )
    if resolved != source_revision or not source_is_ancestor_of_packaging(
        source_revision, packaging_commit
    ):
        raise PublisherError("INVALID_RELEASE_PROVENANCE", "invalid_provenance")
    return {key: str(metadata[key]) for key in required}


def build_release_bundle(
    space_id: str = CANONICAL_SPACE_ID,
    sdk: str = CANONICAL_SDK,
    *,
    private: bool = False,
    create: bool = False,
    whoami: bool = False,
) -> ReleaseBundle:
    """Build the one immutable manifest/bundle used for both dry and live modes."""
    _validate_publish_mode(space_id, sdk, private=private, create=create, whoami=whoami)
    packaging_commit = _assert_clean_packaging_commit()
    files = _tracked_release_files(packaging_commit)
    identity = _release_identity_from_bundle(files, packaging_commit)
    entries: list[dict[str, Any]] = []
    for item in files:
        digest = hashlib.sha256(item.data).hexdigest()
        entries.append(
            {
                "path": item.path,
                "source_kind": "tracked",
                "source_path": item.source_path,
                "source_revision": packaging_commit,
                "source_blob_oid": item.source_blob_oid,
                "source_mode": "100644",
                "source_bytes": len(item.data),
                "source_sha256": digest,
                "staged_mode": "100644",
                "staged_bytes": len(item.data),
                "staged_sha256": digest,
                "staged_blob_oid": _git_blob_oid(item.data),
            }
        )
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "space_id": CANONICAL_SPACE_ID,
        "repo_type": REPO_TYPE,
        "sdk": CANONICAL_SDK,
        "branch": CANONICAL_BRANCH,
        "version": identity["version"],
        "packaging_commit": packaging_commit,
        "release_source_commit": identity["release_source_commit"],
        "release_source_revision": identity["release_source_revision"],
        "release_source_metadata_path": identity["release_source_metadata_path"],
        "release_source_metadata_sha256": identity["release_source_metadata_sha256"],
        "entries": entries,
        "total_files": len(entries),
        "total_bytes": sum(item["staged_bytes"] for item in entries),
    }
    manifest["manifest_sha256"] = _object_digest(manifest, "manifest_sha256")
    validate_release_manifest(manifest)
    return ReleaseBundle(files=files, manifest=manifest)


def _validate_publish_mode(
    space_id: str,
    sdk: str,
    *,
    private: bool,
    create: bool,
    whoami: bool,
) -> None:
    if space_id != CANONICAL_SPACE_ID:
        raise PublisherError("INVALID_TARGET", "invalid_target")
    if sdk != CANONICAL_SDK:
        raise PublisherError("INVALID_SDK", "sdk_mismatch")
    if private:
        raise PublisherError("PRIVATE_MODE_FORBIDDEN", "invalid_target")
    if create:
        raise PublisherError("CREATE_MODE_FORBIDDEN", "invalid_target")
    if whoami:
        raise PublisherError("WHOAMI_MODE_FORBIDDEN", "invalid_target")


def _validate_manifest_git_binding(manifest: dict[str, Any]) -> None:
    packaging_commit = manifest["packaging_commit"]
    source_revision = manifest["release_source_revision"]
    resolved_packaging = _git_text(
        ["rev-parse", "--verify", f"{packaging_commit}^{{commit}}"],
        "INVALID_RELEASE_MANIFEST",
    )
    if resolved_packaging != packaging_commit or not source_is_ancestor_of_packaging(
        source_revision, packaging_commit
    ):
        raise PublisherError("INVALID_RELEASE_MANIFEST", "invalid_manifest")

    expected: dict[str, tuple[str, str]] = {}
    raw_tree = _git_bytes(
        ["ls-tree", "-r", "-z", "--full-tree", packaging_commit],
        "INVALID_RELEASE_MANIFEST",
    )
    for raw_record in raw_tree.split(b"\0"):
        if not raw_record:
            continue
        try:
            metadata, raw_path = raw_record.split(b"\t", 1)
            mode, object_type, raw_oid = metadata.split(b" ", 2)
            source_path = raw_path.decode("utf-8", errors="strict")
            oid = raw_oid.decode("ascii", errors="strict")
        except (ValueError, UnicodeDecodeError) as exc:
            raise PublisherError(
                "INVALID_RELEASE_MANIFEST", "invalid_manifest"
            ) from exc
        destination = _payload_destination(source_path)
        if destination is not None:
            if mode != b"100644" or object_type != b"blob":
                raise PublisherError("INVALID_RELEASE_MANIFEST", "invalid_manifest")
            if destination in expected:
                raise PublisherError("INVALID_RELEASE_MANIFEST", "invalid_manifest")
            expected[destination] = (source_path, oid)

    entries = manifest["entries"]
    if set(expected) != {entry["path"] for entry in entries}:
        raise PublisherError("MANIFEST_MISMATCH", "manifest_mismatch")
    blob_data = _git_blob_batch(
        [expected[entry["path"]][1] for entry in entries],
        "INVALID_RELEASE_MANIFEST",
    )
    for entry in entries:
        path = entry["path"]
        if entry["source_kind"] != "tracked":
            raise PublisherError("INVALID_RELEASE_MANIFEST", "invalid_manifest")
        source_path, oid = expected[path]
        data = blob_data[oid]
        digest = hashlib.sha256(data).hexdigest()
        if (
            entry["source_path"] != source_path
            or entry["source_revision"] != packaging_commit
            or entry["source_blob_oid"] != oid
            or entry["source_mode"] != "100644"
            or entry["source_bytes"] != len(data)
            or entry["source_sha256"] != digest
            or entry["staged_mode"] != "100644"
            or entry["staged_bytes"] != len(data)
            or entry["staged_sha256"] != digest
            or entry["staged_blob_oid"] != _git_blob_oid(data)
        ):
            raise PublisherError("MANIFEST_MISMATCH", "manifest_mismatch")

    metadata_entries = [
        entry for entry in entries if entry["path"] == "project/static/version.json"
    ]
    if len(metadata_entries) != 1:
        raise PublisherError("INVALID_RELEASE_MANIFEST", "invalid_manifest")
    metadata = _strict_json_bytes(
        blob_data[metadata_entries[0]["source_blob_oid"]], "INVALID_RELEASE_MANIFEST"
    )
    metadata_fields = (
        "version",
        "release_source_commit",
        "release_source_revision",
        "release_source_metadata_path",
        "release_source_metadata_sha256",
    )
    if not isinstance(metadata, dict) or set(metadata) != set(metadata_fields):
        raise PublisherError("MANIFEST_MISMATCH", "manifest_mismatch")
    for field in metadata_fields:
        if not isinstance(metadata, dict) or metadata.get(field) != manifest[field]:
            raise PublisherError("MANIFEST_MISMATCH", "manifest_mismatch")
    version_match = VERSION_RE.fullmatch(manifest["version"])
    canonical_source = {
        "release_source_commit": manifest["release_source_commit"],
        "release_source_metadata_path": manifest["release_source_metadata_path"],
        "release_source_revision": manifest["release_source_revision"],
        "version": manifest["version"],
    }
    resolved_source = _git_text(
        [
            "rev-parse",
            "--verify",
            f"{manifest['release_source_commit']}^{{commit}}",
        ],
        "INVALID_RELEASE_MANIFEST",
    )
    if (
        version_match is None
        or version_match.group(1) != manifest["release_source_commit"]
        or resolved_source != manifest["release_source_revision"]
        or hashlib.sha256(_canonical_json(canonical_source)).hexdigest()
        != manifest["release_source_metadata_sha256"]
    ):
        raise PublisherError("MANIFEST_MISMATCH", "manifest_mismatch")


def validate_release_manifest(
    manifest: dict[str, Any], *, verify_git: bool = True
) -> None:
    """Validate schema plus invariants JSON Schema cannot express."""
    if not isinstance(manifest, dict):
        raise PublisherError("INVALID_RELEASE_MANIFEST", "invalid_manifest")
    _schema_validate(manifest)
    entries = manifest["entries"]
    paths = [entry["path"] for entry in entries]
    if (
        paths != sorted(paths, key=lambda path: path.encode("utf-8"))
        or len(paths) != len(set(paths))
        or any(not _safe_bundle_path(path) for path in paths)
        or manifest["total_files"] != len(entries)
        or manifest["total_bytes"] != sum(entry["staged_bytes"] for entry in entries)
        or manifest["manifest_sha256"] != _object_digest(manifest, "manifest_sha256")
    ):
        raise PublisherError("INVALID_RELEASE_MANIFEST", "invalid_manifest")
    for entry in entries:
        if (
            entry["source_revision"] != manifest["packaging_commit"]
            or entry["source_mode"] != "100644"
            or entry["staged_mode"] != "100644"
            or not _safe_bundle_path(entry["source_path"])
        ):
            raise PublisherError("INVALID_RELEASE_MANIFEST", "invalid_manifest")
    if verify_git:
        _validate_manifest_git_binding(manifest)


def _parse_z_timestamp(value: str) -> datetime.datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise PublisherError("INVALID_RELEASE_RECEIPT")
    try:
        parsed = datetime.datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise PublisherError("INVALID_RELEASE_RECEIPT") from exc
    if parsed.tzinfo != datetime.timezone.utc:
        raise PublisherError("INVALID_RELEASE_RECEIPT")
    return parsed


def _manifest_tree_projection(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "blob_id": entry["staged_blob_oid"],
            "path": entry["path"],
            "size": entry["staged_bytes"],
        }
        for entry in manifest["entries"]
    ]


def _tree_digest(projection: list[dict[str, Any]]) -> str:
    return hashlib.sha256(_canonical_json(projection)).hexdigest()


def validate_release_receipt(
    receipt: dict[str, Any], manifest: dict[str, Any] | None = None
) -> None:
    """Validate a sanitized receipt and its optional manifest binding."""
    if not isinstance(receipt, dict):
        raise PublisherError("INVALID_RELEASE_RECEIPT")
    _schema_validate(receipt, receipt=True)
    if receipt["receipt_sha256"] != _object_digest(receipt, "receipt_sha256"):
        raise PublisherError("INVALID_RELEASE_RECEIPT")
    if _parse_z_timestamp(receipt["ended_at"]) < _parse_z_timestamp(
        receipt["started_at"]
    ):
        raise PublisherError("INVALID_RELEASE_RECEIPT")
    if receipt["action"] == "publish" and (
        (
            receipt["parent_revision"] is not None
            and receipt["prior_revision"] is not None
            and receipt["parent_revision"] != receipt["prior_revision"]
        )
        or (
            receipt["parent_tree_sha256"] is not None
            and receipt["prior_tree_sha256"] is not None
            and receipt["parent_tree_sha256"] != receipt["prior_tree_sha256"]
        )
    ):
        raise PublisherError("INVALID_RELEASE_RECEIPT")
    if receipt["new_revision"] is not None and receipt["new_revision"] in (
        receipt["parent_revision"],
        receipt["prior_revision"],
    ):
        raise PublisherError("INVALID_RELEASE_RECEIPT")
    if (
        receipt["action"] == "rollback"
        and receipt["parent_revision"] == receipt["prior_revision"]
    ):
        raise PublisherError("INVALID_RELEASE_RECEIPT")
    if (
        receipt["action"] == "rollback"
        and receipt["status"] == "SUCCEEDED"
        and receipt["new_tree_sha256"] != receipt["prior_tree_sha256"]
    ):
        raise PublisherError("INVALID_RELEASE_RECEIPT")
    if manifest is not None:
        validate_release_manifest(manifest)
        bindings = (
            "space_id",
            "repo_type",
            "sdk",
            "branch",
            "version",
            "packaging_commit",
            "release_source_commit",
            "release_source_revision",
            "release_source_metadata_path",
            "release_source_metadata_sha256",
            "manifest_sha256",
            "total_files",
            "total_bytes",
        )
        if any(receipt[field] != manifest[field] for field in bindings):
            raise PublisherError("RECEIPT_MANIFEST_MISMATCH", "manifest_mismatch")
        expected_tree = _tree_digest(_manifest_tree_projection(manifest))
        if (
            receipt["action"] == "publish"
            and receipt["status"] == "SUCCEEDED"
            and receipt["new_tree_sha256"] != expected_tree
        ):
            raise PublisherError("RECEIPT_MANIFEST_MISMATCH", "manifest_mismatch")


def _read_json_object(
    path: Path, error_code: str, *, max_bytes: int = 16 * 1024 * 1024
) -> dict[str, Any]:
    try:
        file_stat = path.lstat()
        if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_size > max_bytes:
            raise PublisherError(error_code)
        raw = path.read_bytes()
    except PublisherError:
        raise
    except OSError as exc:
        raise PublisherError(error_code) from exc
    value = _strict_json_bytes(raw, error_code)
    if not isinstance(value, dict):
        raise PublisherError(error_code)
    return value


def _write_all(fd: int, data: bytes) -> None:
    offset = 0
    while offset < len(data):
        try:
            written = os.write(fd, data[offset:])
        except InterruptedError:
            continue
        if written <= 0:
            raise OSError("short write")
        offset += written


def _atomic_write_json(path: Path, value: dict[str, Any], error_code: str) -> None:
    payload = _canonical_json(value) + b"\n"
    parent = path.parent if str(path.parent) else Path(".")
    temp_name = f".{path.name}.{uuid.uuid4().hex}.tmp"
    dir_flags = (
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    )
    file_flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    dir_fd = -1
    file_fd = -1
    created = False
    try:
        dir_fd = os.open(parent, dir_flags)
        file_fd = os.open(temp_name, file_flags, 0o600, dir_fd=dir_fd)
        created = True
        _write_all(file_fd, payload)
        os.fsync(file_fd)
        os.close(file_fd)
        file_fd = -1
        os.replace(temp_name, path.name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
        created = False
        os.fsync(dir_fd)
    except (OSError, ValueError) as exc:
        raise PublisherError(error_code, "receipt_persistence_failure") from exc
    finally:
        if file_fd >= 0:
            os.close(file_fd)
        if created and dir_fd >= 0:
            try:
                os.unlink(temp_name, dir_fd=dir_fd)
            except OSError:
                pass
        if dir_fd >= 0:
            os.close(dir_fd)


def _utc_now() -> str:
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _receipt(
    manifest: dict[str, Any],
    *,
    action: str,
    started_at: str,
    status: str,
    failure_class: str,
    parent_revision: str | None,
    new_revision: str | None,
    prior_revision: str | None,
    parent_tree_sha256: str | None,
    new_tree_sha256: str | None,
    prior_tree_sha256: str | None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema_version": 1,
        "action": action,
        "space_id": manifest["space_id"],
        "repo_type": manifest["repo_type"],
        "sdk": manifest["sdk"],
        "branch": manifest["branch"],
        "version": manifest["version"],
        "packaging_commit": manifest["packaging_commit"],
        "release_source_commit": manifest["release_source_commit"],
        "release_source_revision": manifest["release_source_revision"],
        "release_source_metadata_path": manifest["release_source_metadata_path"],
        "release_source_metadata_sha256": manifest["release_source_metadata_sha256"],
        "manifest_sha256": manifest["manifest_sha256"],
        "parent_revision": parent_revision,
        "new_revision": new_revision,
        "prior_revision": prior_revision,
        "parent_tree_sha256": parent_tree_sha256,
        "new_tree_sha256": new_tree_sha256,
        "prior_tree_sha256": prior_tree_sha256,
        "total_files": manifest["total_files"],
        "total_bytes": manifest["total_bytes"],
        "started_at": started_at,
        "ended_at": _utc_now(),
        "status": status,
        "failure_class": failure_class,
    }
    value["receipt_sha256"] = _object_digest(value, "receipt_sha256")
    validate_release_receipt(value, manifest)
    return value


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
        raise ValueError(
            "packaging commit cannot be resolved directly from Git HEAD"
        ) from exc


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
                raise ValueError("duplicate version.json key")
            parsed[key] = value
        return parsed

    parsed = json.loads(raw_text, object_pairs_hook=reject_duplicate_keys)
    if not isinstance(parsed, dict):
        raise ValueError("version.json must contain a JSON object")  # noqa: TRY004
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
    # Generated cloud-training scratch data is not a backend runtime input and
    # would be converted to LFS, breaking the manifest's exact Git-blob parity.
    "project/rag/datasets/cloud_train_temp.jsonl",
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
        if (
            pat_clean in parts
            or fnmatch.fnmatch(p_str, pattern)
            or fnmatch.fnmatch(Path(p_str).name, pattern)
        ):
            return True
        if fnmatch.fnmatch(p_str, f"*{pattern}*"):
            return True
    return False


def stamp_static_html_version(
    html_text: str, local_version: str, git_commit: str
) -> str:
    """Stamp one static HTML document with an exact release version.

    The publisher previously replaced every ``v1.0.0`` substring. Re-publishing an
    already stamped document therefore produced composite labels such as
    ``v1.0.0.<new>.<old>`` while leaving ``CURRENT_PAGE_VERSION`` stale because
    that JavaScript value does not include a leading ``v``. Keep the rewrite
    scoped to the two version surfaces and the supported cache-busting assets.
    """
    html_text = re.sub(
        r'(window\.CURRENT_PAGE_VERSION\s*=\s*["\'])[^"\']+(["\'])',
        rf"\g<1>{local_version}\g<2>",
        html_text,
    )
    html_text = re.sub(
        r'(<p\b[^>]*\bid=["\']footer-version-text["\'][^>]*>[^<]*?\bv)[^\s<—]+',
        rf"\g<1>{local_version}",
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
        raise ValueError("static release directory unavailable")
    temp_static_dir = Path(tempfile.mkdtemp(prefix="hf_static_staged_"))
    try:
        shutil.copytree(static_dir, temp_static_dir, dirs_exist_ok=True)
        local_version = release_identity["version"]
        version_meta = {
            "version": local_version,
            "release_source_commit": release_source_commit,
            "release_source_revision": release_identity["release_source_revision"],
            "release_source_metadata_path": release_identity[
                "release_source_metadata_path"
            ],
            "release_source_metadata_sha256": release_identity[
                "release_source_metadata_sha256"
            ],
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
    for key in (
        "HF_TOKEN",
        "HUGGINGFACE_TOKEN",
        "HF_API_TOKEN",
        "HUGGINGFACE_API_KEY",
        "HUGGING_FACE_TOKEN",
    ):
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
            logger.error("[ERROR] STATIC_PAYLOAD_UNAVAILABLE")
            return False, payload_summary

        file_count = 0
        total_bytes = 0
        for p in static_dir.rglob("*"):
            if p.is_file() and not p.name.startswith("."):
                file_count += 1
                total_bytes += p.stat().st_size

        payload_summary["files"].append(
            {
                "name": "project/static/ Web Demo UI",
                "size_bytes": total_bytes,
                "count": file_count,
            }
        )
        payload_summary["total_files"] = file_count
        payload_summary["total_bytes"] = total_bytes
        return True, payload_summary

    # Docker SDK Audit
    dockerfile_path = ROOT / "Dockerfile.hf"
    req_path = ROOT / "requirements.txt"
    project_dir = ROOT / "project"
    tdd_dir = ROOT / "TDD-HORO-v3.0"

    if not dockerfile_path.exists():
        logger.error("[ERROR] DOCKERFILE_UNAVAILABLE")
        return False, payload_summary

    dockerfile_content = dockerfile_path.read_text(encoding="utf-8")
    dockerfile_size = dockerfile_path.stat().st_size
    payload_summary["files"].append(
        {"name": "Dockerfile (via Dockerfile.hf)", "size_bytes": dockerfile_size}
    )
    payload_summary["total_files"] += 1
    payload_summary["total_bytes"] += dockerfile_size

    has_port_7860 = "7860" in dockerfile_content
    has_uvicorn = "uvicorn" in dockerfile_content
    payload_summary["dockerfile_valid"] = has_port_7860 and has_uvicorn

    if not req_path.exists():
        logger.error("[ERROR] REQUIREMENTS_UNAVAILABLE")
        return False, payload_summary

    req_size = req_path.stat().st_size
    payload_summary["files"].append(
        {"name": "requirements.txt", "size_bytes": req_size}
    )
    payload_summary["total_files"] += 1
    payload_summary["total_bytes"] += req_size

    if not project_dir.exists() or not project_dir.is_dir():
        logger.error("[ERROR] PROJECT_PAYLOAD_UNAVAILABLE")
        return False, payload_summary

    project_file_count = 0
    project_bytes = 0
    for p in project_dir.rglob("*"):
        if p.is_file() and not p.name.startswith("."):
            rel_p = str(p.relative_to(project_dir))
            if not should_ignore(f"project/{rel_p}") and not should_ignore(rel_p):
                project_file_count += 1
                project_bytes += p.stat().st_size

    payload_summary["files"].append(
        {
            "name": "project/ directory",
            "size_bytes": project_bytes,
            "count": project_file_count,
        }
    )
    payload_summary["total_files"] += project_file_count
    payload_summary["total_bytes"] += project_bytes

    if not tdd_dir.exists() or not tdd_dir.is_dir():
        logger.error("[ERROR] TDD_PAYLOAD_UNAVAILABLE")
        return False, payload_summary

    tdd_file_count = 0
    tdd_bytes = 0
    for p in tdd_dir.rglob("*"):
        if p.is_file() and not p.name.startswith("."):
            rel_p = str(p.relative_to(tdd_dir))
            if not should_ignore(f"TDD-HORO-v3.0/{rel_p}") and not should_ignore(rel_p):
                tdd_file_count += 1
                tdd_bytes += p.stat().st_size

    payload_summary["files"].append(
        {
            "name": "TDD-HORO-v3.0/ directory",
            "size_bytes": tdd_bytes,
            "count": tdd_file_count,
        }
    )
    payload_summary["total_files"] += tdd_file_count
    payload_summary["total_bytes"] += tdd_bytes

    is_valid = payload_summary["dockerfile_valid"] and payload_summary["project_valid"]
    return is_valid, payload_summary


def _space_base_url(space_id: str, sdk: str) -> str:
    """Return the public runtime URL for a Hugging Face Space."""
    parts = space_id.split("/", maxsplit=1)
    if len(parts) == 2:
        user, repo = (
            parts[0].lower(),
            parts[1].lower().replace("_", "-").replace(".", "-"),
        )
        host_name = f"{user}-{repo}"
    else:
        host_name = (
            space_id.lower().replace("/", "-").replace("_", "-").replace(".", "-")
        )
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
                    return (
                        False,
                        f"version.json HTTP {version_res.status_code}",
                        latency_ms,
                    )
                try:
                    version_meta = _parse_version_metadata(version_res.text)
                except ValueError:
                    return False, "version.json is not valid JSON", latency_ms
                required_meta = (
                    "version",
                    "release_source_commit",
                    "release_source_revision",
                    "release_source_metadata_path",
                    "release_source_metadata_sha256",
                    "status",
                )
                missing_meta = [
                    key for key in required_meta if not version_meta.get(key)
                ]
                forbidden_meta = [
                    key for key in ("commit", "packaging_commit") if key in version_meta
                ]
                if (
                    missing_meta
                    or forbidden_meta
                    or version_meta.get("status") != "production"
                ):
                    return (
                        False,
                        f"Invalid production version metadata (missing={missing_meta})",
                        latency_ms,
                    )
                return True, "Static root and version.json OK", latency_ms

            res = client.get(f"{space_host}/health")
            latency_ms = round((time.monotonic() - t0) * 1000, 2)

            if res.status_code == 200:
                return True, "HTTP 200 OK", latency_ms
            else:
                return False, f"HTTP {res.status_code}", latency_ms

    except httpx.ConnectTimeout:
        return False, "Connection Timeout (Space may be sleeping or initializing)", 0.0
    except Exception:  # noqa: BLE001 - command boundary sanitizes unknown failures
        return False, "Connection error", 0.0


def _remote_tree(api: Any, revision: str) -> list[dict[str, Any]]:
    if GIT_REVISION_RE.fullmatch(revision) is None:
        raise PublisherError("INVALID_REMOTE_REVISION", "repository_unavailable")
    try:
        remote_items = api.list_repo_tree(
            repo_id=CANONICAL_SPACE_ID,
            path_in_repo=None,
            recursive=True,
            expand=False,
            revision=revision,
            repo_type=REPO_TYPE,
        )
        projection: list[dict[str, Any]] = []
        for item in remote_items:
            blob_id = getattr(item, "blob_id", None)
            if blob_id is None:
                if getattr(item, "size", None) is not None:
                    raise PublisherError(
                        "INVALID_REMOTE_TREE", "repository_unavailable"
                    )
                continue
            path = getattr(item, "path", None)
            size = getattr(item, "size", None)
            if (
                not isinstance(path, str)
                or not _safe_bundle_path(path)
                or not isinstance(size, int)
                or size < 0
                or not isinstance(blob_id, str)
                or re.fullmatch(r"[0-9a-f]{40}", blob_id) is None
            ):
                raise PublisherError("INVALID_REMOTE_TREE", "repository_unavailable")
            projection.append({"blob_id": blob_id, "path": path, "size": size})
    except PublisherError:
        raise
    except Exception as exc:
        raise PublisherError(
            "REMOTE_TREE_UNAVAILABLE", "repository_unavailable"
        ) from exc
    projection.sort(key=lambda item: item["path"].encode("utf-8"))
    paths = [item["path"] for item in projection]
    if len(paths) != len(set(paths)):
        raise PublisherError("INVALID_REMOTE_TREE", "repository_unavailable")
    return projection


def _remote_head(
    api: Any, expected_parent_revision: str
) -> tuple[str, list[dict[str, Any]]]:
    if GIT_REVISION_RE.fullmatch(expected_parent_revision) is None:
        raise PublisherError("INVALID_PARENT_REVISION", "parent_conflict")
    try:
        info = api.repo_info(
            repo_id=CANONICAL_SPACE_ID,
            revision=CANONICAL_BRANCH,
            repo_type=REPO_TYPE,
            files_metadata=False,
        )
    except Exception as exc:
        raise PublisherError(
            "REPOSITORY_UNAVAILABLE", "repository_unavailable"
        ) from exc
    revision = getattr(info, "sha", None)
    sdk = getattr(info, "sdk", None)
    if getattr(info, "private", False) is True:
        raise PublisherError("REMOTE_PRIVATE_MODE_FORBIDDEN", "invalid_target")
    if sdk != CANONICAL_SDK:
        raise PublisherError("REMOTE_SDK_MISMATCH", "sdk_mismatch")
    if not isinstance(revision, str) or GIT_REVISION_RE.fullmatch(revision) is None:
        raise PublisherError("REPOSITORY_UNAVAILABLE", "repository_unavailable")
    if revision != expected_parent_revision:
        raise PublisherError("PARENT_CONFLICT", "parent_conflict")
    return revision, _remote_tree(api, revision)


def _download_file(api: Any, path: str, revision: str) -> bytes:
    try:
        downloaded = api.hf_hub_download(
            repo_id=CANONICAL_SPACE_ID,
            filename=path,
            repo_type=REPO_TYPE,
            revision=revision,
            force_download=False,
        )
        downloaded_path = Path(downloaded)
        # huggingface_hub commonly returns a cache snapshot symlink. Following
        # it is required for normal operation; exact size/blob/SHA checks below
        # authenticate the downloaded bytes before they become evidence.
        file_stat = downloaded_path.stat()
        if not stat.S_ISREG(file_stat.st_mode):
            raise PublisherError("REMOTE_DOWNLOAD_MISMATCH", "postflight_mismatch")
        return downloaded_path.read_bytes()
    except PublisherError:
        raise
    except Exception as exc:
        raise PublisherError(
            "REMOTE_DOWNLOAD_UNAVAILABLE", "postflight_mismatch"
        ) from exc


def _verify_downloads(
    api: Any,
    projection: list[dict[str, Any]],
    revision: str,
    expected_sha256: dict[str, str] | None = None,
) -> dict[str, bytes]:
    def verify_item(
        index: int, item: dict[str, Any]
    ) -> tuple[int, str, bytes]:
        data = _download_file(api, item["path"], revision)
        if len(data) != item["size"] or item["blob_id"] not in (
            _git_blob_oid(data),
            _git_lfs_pointer_blob_oid(data),
        ):
            raise PublisherError("REMOTE_DOWNLOAD_MISMATCH", "postflight_mismatch")
        if expected_sha256 is not None and hashlib.sha256(
            data
        ).hexdigest() != expected_sha256.get(item["path"]):
            raise PublisherError("REMOTE_DOWNLOAD_MISMATCH", "postflight_mismatch")
        return index, item["path"], data

    verified: dict[int, tuple[str, bytes]] = {}
    indexed_items = iter(enumerate(projection))
    executor = ThreadPoolExecutor(max_workers=PRIOR_TREE_DOWNLOAD_WORKERS)
    pending: dict[Future[tuple[int, str, bytes]], int] = {}
    try:
        while len(pending) < PRIOR_TREE_DOWNLOAD_WORKERS:
            try:
                index, item = next(indexed_items)
            except StopIteration:
                break
            pending[executor.submit(verify_item, index, item)] = index

        while pending:
            done, _ = wait(pending, return_when=FIRST_COMPLETED)
            ordered_done = sorted(done, key=pending.__getitem__)
            completed = [future.result() for future in ordered_done]
            for future in ordered_done:
                pending.pop(future)
            for index, path, data in completed:
                verified[index] = (path, data)

            while len(pending) < PRIOR_TREE_DOWNLOAD_WORKERS:
                try:
                    index, item = next(indexed_items)
                except StopIteration:
                    break
                pending[executor.submit(verify_item, index, item)] = index
    except BaseException:
        for future in pending:
            future.cancel()
        raise
    finally:
        executor.shutdown(wait=True, cancel_futures=True)

    return {
        verified[index][0]: verified[index][1] for index in range(len(projection))
    }


def _publish_operations(
    bundle: ReleaseBundle, prior_tree: list[dict[str, Any]]
) -> list[Any]:
    if CommitOperationAdd is None or CommitOperationDelete is None:
        raise PublisherError("HF_LIBRARY_UNAVAILABLE", "repository_unavailable")
    desired = {item.path for item in bundle.files}
    deletions = sorted(
        (item["path"] for item in prior_tree if item["path"] not in desired),
        key=lambda path: path.encode("utf-8"),
    )
    operations: list[Any] = [
        CommitOperationDelete(path_in_repo=path, is_folder=False) for path in deletions
    ]
    operations.extend(
        CommitOperationAdd(path_in_repo=item.path, path_or_fileobj=item.data)
        for item in bundle.files
    )
    if len(operations) != len(deletions) + len(bundle.files):
        raise PublisherError("INVALID_COMMIT_OPERATIONS", "internal_error")
    return operations


def _rollback_operations(
    prior_content: dict[str, bytes], current_tree: list[dict[str, Any]]
) -> list[Any]:
    if CommitOperationAdd is None or CommitOperationDelete is None:
        raise PublisherError("HF_LIBRARY_UNAVAILABLE", "repository_unavailable")
    desired = set(prior_content)
    deletions = sorted(
        (item["path"] for item in current_tree if item["path"] not in desired),
        key=lambda path: path.encode("utf-8"),
    )
    operations: list[Any] = [
        CommitOperationDelete(path_in_repo=path, is_folder=False) for path in deletions
    ]
    operations.extend(
        CommitOperationAdd(path_in_repo=path, path_or_fileobj=prior_content[path])
        for path in sorted(prior_content, key=lambda value: value.encode("utf-8"))
    )
    return operations


def _commit_failure(exc: Exception) -> tuple[str, str]:
    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    if isinstance(exc, HfHubHTTPError) and status_code in (409, 412):
        return "FAILED", "parent_conflict"
    if isinstance(exc, HfHubHTTPError) and status_code in (400, 401, 403, 404, 422):
        return "FAILED", "commit_rejected"
    return "INDETERMINATE", "transport_ambiguous"


def _commit_once(
    api: Any, operations: list[Any], parent_revision: str, action: str
) -> str:
    result = api.create_commit(
        repo_id=CANONICAL_SPACE_ID,
        operations=operations,
        commit_message=(
            "Publish canonical Docker release"
            if action == "publish"
            else "Rollback canonical Docker release"
        ),
        commit_description=None,
        repo_type=REPO_TYPE,
        revision=CANONICAL_BRANCH,
        create_pr=False,
        parent_commit=parent_revision,
        run_as_future=False,
    )
    revision = getattr(result, "oid", None)
    if not isinstance(revision, str) or GIT_REVISION_RE.fullmatch(revision) is None:
        raise PublisherError("AMBIGUOUS_COMMIT_RESULT", "transport_ambiguous")
    return revision


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    validate_release_manifest(manifest)
    _atomic_write_json(path, manifest, "MANIFEST_PERSISTENCE_FAILURE")


def _write_receipt(
    path: Path, receipt: dict[str, Any], manifest: dict[str, Any]
) -> None:
    validate_release_receipt(receipt, manifest)
    _atomic_write_json(path, receipt, "RECEIPT_PERSISTENCE_FAILURE")


def _api_client(api: Any | None) -> Any:
    if api is not None:
        return api
    if not HF_AVAILABLE or HfApi is None:
        raise PublisherError("HF_LIBRARY_UNAVAILABLE", "repository_unavailable")
    token = get_hf_token()
    if not token:
        raise PublisherError("HF_TOKEN_UNAVAILABLE", "repository_unavailable")
    try:
        return HfApi(token=token)
    except Exception as exc:
        raise PublisherError("HF_CLIENT_UNAVAILABLE", "repository_unavailable") from exc


def _publish_bundle(
    bundle: ReleaseBundle,
    *,
    api: Any,
    expected_parent_revision: str,
    receipt_path: Path,
) -> bool:
    manifest = bundle.manifest
    started_at = _utc_now()
    parent_revision, prior_tree = _remote_head(api, expected_parent_revision)
    prior_tree_sha256 = _tree_digest(prior_tree)
    try:
        _verify_downloads(api, prior_tree, parent_revision)
    except PublisherError as exc:
        raise PublisherError(
            "PRIOR_TREE_UNAVAILABLE", "prior_tree_unavailable"
        ) from exc
    operations = _publish_operations(bundle, prior_tree)
    try:
        new_revision = _commit_once(api, operations, parent_revision, "publish")
    except Exception as exc:
        status, failure_class = _commit_failure(exc)
        receipt = _receipt(
            manifest,
            action="publish",
            started_at=started_at,
            status=status,
            failure_class=failure_class,
            parent_revision=parent_revision,
            new_revision=None,
            prior_revision=parent_revision,
            parent_tree_sha256=prior_tree_sha256,
            new_tree_sha256=None,
            prior_tree_sha256=prior_tree_sha256,
        )
        _write_receipt(receipt_path, receipt, manifest)
        raise PublisherError("PUBLISH_COMMIT_FAILED", failure_class) from exc

    try:
        new_tree = _remote_tree(api, new_revision)
        new_tree_sha256 = _tree_digest(new_tree)
        expected_tree = _manifest_tree_projection(manifest)
        expected_tree_sha256 = _tree_digest(expected_tree)
        expected_hashes = {
            entry["path"]: entry["staged_sha256"] for entry in manifest["entries"]
        }
        if new_tree != expected_tree:
            raise PublisherError("POSTFLIGHT_TREE_MISMATCH", "postflight_mismatch")
        _verify_downloads(api, new_tree, new_revision, expected_hashes)
        if new_tree_sha256 != expected_tree_sha256:
            raise PublisherError("POSTFLIGHT_TREE_MISMATCH", "postflight_mismatch")
    except PublisherError as exc:
        if exc.failure_class != "postflight_mismatch":
            raise
        try:
            observed_tree = _remote_tree(api, new_revision)
            observed_digest = _tree_digest(observed_tree)
        except PublisherError:
            # The schema cannot truthfully represent a known revision without its tree.
            raise PublisherError(
                "POSTFLIGHT_EVIDENCE_UNAVAILABLE", "internal_error"
            ) from exc
        receipt = _receipt(
            manifest,
            action="publish",
            started_at=started_at,
            status="ROLLBACK_REQUIRED",
            failure_class="postflight_mismatch",
            parent_revision=parent_revision,
            new_revision=new_revision,
            prior_revision=parent_revision,
            parent_tree_sha256=prior_tree_sha256,
            new_tree_sha256=observed_digest,
            prior_tree_sha256=prior_tree_sha256,
        )
        _write_receipt(receipt_path, receipt, manifest)
        raise PublisherError("POSTFLIGHT_MISMATCH", "postflight_mismatch") from exc

    receipt = _receipt(
        manifest,
        action="publish",
        started_at=started_at,
        status="SUCCEEDED",
        failure_class="none",
        parent_revision=parent_revision,
        new_revision=new_revision,
        prior_revision=parent_revision,
        parent_tree_sha256=prior_tree_sha256,
        new_tree_sha256=new_tree_sha256,
        prior_tree_sha256=prior_tree_sha256,
    )
    _write_receipt(receipt_path, receipt, manifest)
    return True


def _rollback_bundle(
    manifest: dict[str, Any],
    publish_receipt: dict[str, Any],
    *,
    api: Any,
    receipt_path: Path,
) -> bool:
    validate_release_manifest(manifest)
    validate_release_receipt(publish_receipt, manifest)
    if (
        publish_receipt["action"] != "publish"
        or publish_receipt["status"] not in ("SUCCEEDED", "ROLLBACK_REQUIRED")
        or publish_receipt["new_revision"] is None
        or publish_receipt["prior_revision"] is None
    ):
        raise PublisherError("INVALID_ROLLBACK_RECEIPT", "rollback_conflict")
    started_at = _utc_now()
    parent_revision, current_tree = _remote_head(api, publish_receipt["new_revision"])
    parent_tree_sha256 = _tree_digest(current_tree)
    if parent_tree_sha256 != publish_receipt["new_tree_sha256"]:
        raise PublisherError("ROLLBACK_CONFLICT", "rollback_conflict")
    prior_revision = publish_receipt["prior_revision"]
    prior_tree = _remote_tree(api, prior_revision)
    prior_tree_sha256 = _tree_digest(prior_tree)
    if prior_tree_sha256 != publish_receipt["prior_tree_sha256"]:
        raise PublisherError("PRIOR_TREE_MISMATCH", "prior_tree_unavailable")
    try:
        prior_content = _verify_downloads(api, prior_tree, prior_revision)
    except PublisherError as exc:
        raise PublisherError(
            "PRIOR_TREE_UNAVAILABLE", "prior_tree_unavailable"
        ) from exc
    operations = _rollback_operations(prior_content, current_tree)
    try:
        new_revision = _commit_once(api, operations, parent_revision, "rollback")
    except Exception as exc:
        status, failure_class = _commit_failure(exc)
        if failure_class == "parent_conflict":
            failure_class = "rollback_conflict"
        receipt = _receipt(
            manifest,
            action="rollback",
            started_at=started_at,
            status=status,
            failure_class=failure_class,
            parent_revision=parent_revision,
            new_revision=None,
            prior_revision=prior_revision,
            parent_tree_sha256=parent_tree_sha256,
            new_tree_sha256=None,
            prior_tree_sha256=prior_tree_sha256,
        )
        _write_receipt(receipt_path, receipt, manifest)
        raise PublisherError("ROLLBACK_COMMIT_FAILED", failure_class) from exc
    new_tree = _remote_tree(api, new_revision)
    new_tree_sha256 = _tree_digest(new_tree)
    try:
        if new_tree != prior_tree or new_tree_sha256 != prior_tree_sha256:
            raise PublisherError("ROLLBACK_POSTFLIGHT_MISMATCH", "postflight_mismatch")
        expected_hashes = {
            path: hashlib.sha256(data).hexdigest()
            for path, data in prior_content.items()
        }
        _verify_downloads(api, new_tree, new_revision, expected_hashes)
        status = "SUCCEEDED"
        failure_class = "none"
    except PublisherError:
        status = "FAILED"
        failure_class = "postflight_mismatch"
    receipt = _receipt(
        manifest,
        action="rollback",
        started_at=started_at,
        status=status,
        failure_class=failure_class,
        parent_revision=parent_revision,
        new_revision=new_revision,
        prior_revision=prior_revision,
        parent_tree_sha256=parent_tree_sha256,
        new_tree_sha256=new_tree_sha256,
        prior_tree_sha256=prior_tree_sha256,
    )
    _write_receipt(receipt_path, receipt, manifest)
    if status != "SUCCEEDED":
        raise PublisherError("ROLLBACK_POSTFLIGHT_MISMATCH", "postflight_mismatch")
    return True


def publish_space(
    space_id: str,
    sdk: str = CANONICAL_SDK,
    private: bool = False,
    dry_run: bool = False,
    *,
    create: bool = False,
    whoami: bool = False,
    manifest_path: str | Path | None = None,
    receipt_path: str | Path | None = None,
    expected_parent_revision: str | None = None,
    rollback_from: str | Path | None = None,
    api: Any | None = None,
) -> bool:
    """Dry-run, publish, or rollback one canonical immutable Docker bundle."""
    try:
        _validate_publish_mode(
            space_id, sdk, private=private, create=create, whoami=whoami
        )
        manifest_output = Path(
            manifest_path
            or os.getenv("HF_RELEASE_MANIFEST_PATH", DEFAULT_MANIFEST_PATH)
        )
        receipt_output = Path(
            receipt_path or os.getenv("HF_RELEASE_RECEIPT_PATH", DEFAULT_RECEIPT_PATH)
        )
        if manifest_output.resolve() == receipt_output.resolve():
            raise PublisherError(
                "EVIDENCE_PATH_COLLISION", "receipt_persistence_failure"
            )
        if rollback_from is not None:
            source_receipt_path = Path(rollback_from)
            if source_receipt_path.resolve() in (
                receipt_output.resolve(),
                manifest_output.resolve(),
            ):
                raise PublisherError("ROLLBACK_RECEIPT_COLLISION", "rollback_conflict")
            manifest = _read_json_object(manifest_output, "INVALID_RELEASE_MANIFEST")
            source_receipt = _read_json_object(
                source_receipt_path, "INVALID_ROLLBACK_RECEIPT", max_bytes=1024 * 1024
            )
            remote_api = _api_client(api)
            success = _rollback_bundle(
                manifest, source_receipt, api=remote_api, receipt_path=receipt_output
            )
            logger.info("[OK] ROLLBACK_SUCCEEDED")
            return success

        bundle = build_release_bundle(
            space_id, sdk, private=private, create=create, whoami=whoami
        )
        _write_manifest(manifest_output, bundle.manifest)
        if dry_run:
            logger.info("[OK] DOCKER_RELEASE_DRY_RUN")
            return True
        remote_api = _api_client(api)
        parent_revision = expected_parent_revision or os.getenv(
            "HF_EXPECTED_PARENT_REVISION", ""
        )
        if not parent_revision:
            try:
                info = remote_api.repo_info(
                    repo_id=space_id,
                    revision=CANONICAL_BRANCH,
                    repo_type=REPO_TYPE,
                    files_metadata=False,
                )
                parent_revision = str(getattr(info, "sha", "") or "").strip()
            except Exception as exc:
                raise PublisherError(
                    "REPOSITORY_UNAVAILABLE", "repository_unavailable"
                ) from exc
        if GIT_REVISION_RE.fullmatch(parent_revision) is None:
            raise PublisherError("INVALID_PARENT_REVISION", "parent_conflict")
        success = _publish_bundle(
            bundle,
            api=remote_api,
            expected_parent_revision=parent_revision,
            receipt_path=receipt_output,
        )
        logger.info("[OK] PUBLISH_SUCCEEDED")
        return success
    except PublisherError as exc:
        logger.error("[ERROR] %s", exc.code)
        return False
    except Exception:  # noqa: BLE001 - command boundary sanitizes unknown failures
        logger.error("[ERROR] INTERNAL_ERROR")
        return False


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
    except ValueError:
        details["errors"].append("local release identity invalid")
        return (
            False,
            "[ERROR] Live verification requires valid local release metadata.",
            details,
        )
    if not source_is_ancestor_of_packaging(
        release_identity["release_source_commit"], packaging_commit
    ):
        details["errors"].append(
            "release source is not an ancestor of packaging commit"
        )
        return (
            False,
            "[ERROR] Live verification requires valid local release metadata.",
            details,
        )

    local_commit = release_identity["release_source_commit"]
    local_version = release_identity["version"]
    details.update(
        {
            "expected_commit": local_commit,
            "expected_version": local_version,
            "expected_release_source_commit": local_commit,
            "expected_release_version": local_version,
            "expected_release_source_revision": release_identity[
                "release_source_revision"
            ],
            "expected_release_source_metadata_path": release_identity[
                "release_source_metadata_path"
            ],
            "expected_release_source_metadata_sha256": release_identity[
                "release_source_metadata_sha256"
            ],
            "release_metadata_path": "project/static/version.json",
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
                    "health_commit_exact": health_data.get("git_commit")
                    == local_commit,
                    "health_version_exact": health_data.get("version") == local_version,
                }
            else:
                paths = (
                    "version.json",
                    "index.html",
                    "app.js",
                    "sw.js",
                    "v3_tokens.css",
                )
                responses = {path: client.get(f"{base_url}/{path}") for path in paths}
                for path, response in responses.items():
                    details["checks"][f"{path}_http_200"] = response.status_code == 200

                version_meta: dict[str, Any] = {}
                if responses["version.json"].status_code == 200:
                    try:
                        version_text = responses["version.json"].text
                        version_meta = _parse_version_metadata(version_text)
                    except ValueError as exc:
                        error_code = (
                            "duplicate version.json key"
                            if str(exc) == "duplicate version.json key"
                            else "invalid JSON"
                        )
                        details["errors"].append(f"version.json {error_code}")

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
                        "version_json_version_exact": version_meta.get("version")
                        == local_version,
                        "version_json_source_commit_exact": live_source_commit
                        == local_commit,
                        "version_json_source_commit_exactly_once": (
                            isinstance(live_source_commit, str)
                            and re.fullmatch(r"[0-9a-f]{7,40}", live_source_commit)
                            is not None
                            and "commit" not in version_meta
                            and "packaging_commit" not in version_meta
                        ),
                        "version_json_version_binds_source_commit": (
                            isinstance(version_meta.get("version"), str)
                            and version_meta.get("version", "").endswith(
                                f".{live_source_commit}"
                            )
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
                        "version_json_production": version_meta.get("status")
                        == "production",
                        "current_page_version_exact": page_versions == [local_version],
                        "footer_version_exact": footer_versions == [local_version],
                        "style_cache_ref_exact": cache_ref_versions("href", "style.css")
                        == [local_commit],
                        "i18n_cache_ref_exact": cache_ref_versions("src", "i18n.js")
                        == [local_commit],
                        "voice_cache_ref_exact": cache_ref_versions(
                            "src", "voice_engine.js"
                        )
                        == [local_commit],
                        "app_cache_ref_exact": cache_ref_versions("src", "app.js")
                        == [local_commit],
                        "client_app_version_exact": client_versions == [local_version],
                        "service_worker_cache_version_exact": cache_versions
                        == [f"v{local_version}"],
                        "v3_tokens_css_nonempty": (
                            responses["v3_tokens.css"].status_code == 200
                            and bool(css_text.strip())
                        ),
                    }
                )
    except (httpx.HTTPError, TypeError, ValueError):
        details["errors"].append("request failure")

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
        failure_summary = (
            ", ".join(failed_checks + details["errors"]) or "no verification evidence"
        )
        msg = f"[ERROR] Live deployment does not match the expected release: {failure_summary}."

    return is_matched, msg, details


def main():
    parser = argparse.ArgumentParser(
        description="Publish the canonical HF Docker backend"
    )
    parser.add_argument("--space-id", default=CANONICAL_SPACE_ID, help="Canonical HF Space ID")  # fmt: skip
    # Static remains parseable only so old automation receives a typed rejection.
    parser.add_argument("--sdk", choices=["static", "docker"], default="docker", help="Space SDK type")  # fmt: skip
    parser.add_argument(
        "--private", action="store_true", help="Forbidden compatibility option"
    )
    parser.add_argument(
        "--create", action="store_true", help="Forbidden compatibility option"
    )
    parser.add_argument(
        "--whoami", action="store_true", help="Forbidden compatibility option"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build and persist the immutable manifest only",
    )
    parser.add_argument(
        "--check-health", action="store_true", help="Check canonical Docker health"
    )
    parser.add_argument(
        "--verify-version",
        action="store_true",
        help="Verify canonical Docker release identity",
    )
    parser.add_argument(
        "--manifest-path",
        default=None,
        help="Manifest output/input path (or HF_RELEASE_MANIFEST_PATH)",
    )
    parser.add_argument(
        "--receipt-path",
        default=None,
        help="Receipt output path (or HF_RELEASE_RECEIPT_PATH)",
    )
    parser.add_argument(
        "--expected-parent-revision",
        "--parent-commit",
        dest="expected_parent_revision",
        default=None,
        help="Required full CAS parent revision (or HF_EXPECTED_PARENT_REVISION)",
    )
    parser.add_argument(
        "--rollback-from",
        "--rollback-receipt",
        dest="rollback_from",
        default=None,
        help="Validated publish receipt authorizing one explicit CAS rollback",
    )

    args = parser.parse_args()

    try:
        _validate_publish_mode(
            args.space_id,
            args.sdk,
            private=args.private,
            create=args.create,
            whoami=args.whoami,
        )
        if args.dry_run and args.rollback_from:
            raise PublisherError("INVALID_COMMAND_MODE", "invalid_target")
        if args.check_health and (
            args.verify_version or args.dry_run or args.rollback_from
        ):
            raise PublisherError("INVALID_COMMAND_MODE", "invalid_target")
        if args.verify_version and (args.dry_run or args.rollback_from):
            raise PublisherError("INVALID_COMMAND_MODE", "invalid_target")
    except PublisherError as exc:
        logger.error("[ERROR] %s", exc.code)
        raise SystemExit(1) from None

    if args.verify_version:
        is_matched, msg, _details = verify_live_deployment_version(
            args.space_id, sdk=args.sdk
        )
        logger.info("[INFO] VERSION_CHECK_%s", "PASSED" if is_matched else "FAILED")
        if msg.startswith("[ERROR]"):
            logger.error("[ERROR] VERSION_CHECK_FAILED")
        sys.exit(0 if is_matched else 1)

    if args.check_health:
        is_healthy, _status_msg, _latency_ms = verify_space_health(
            args.space_id, sdk=args.sdk
        )
        logger.info("[INFO] HEALTH_CHECK_%s", "PASSED" if is_healthy else "FAILED")
        sys.exit(0 if is_healthy else 1)

    success = publish_space(
        args.space_id,
        sdk=args.sdk,
        private=args.private,
        dry_run=args.dry_run,
        create=args.create,
        whoami=args.whoami,
        manifest_path=args.manifest_path,
        receipt_path=args.receipt_path,
        expected_parent_revision=args.expected_parent_revision,
        rollback_from=args.rollback_from,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
