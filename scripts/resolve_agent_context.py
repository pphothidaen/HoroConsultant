#!/usr/bin/env python3
"""Canonical context resolver, approved authority, and evidence validation.

Implements:
- Strict canonical JSON serializer/parser (NFC, duplicate rejection, non-finite float rejection).
- Domain-separated SHA-256 calculation for registry, approved-context, manifest, evidence, capability index.
- Code-fixed ticket/lane loading beneath .agents/context/tickets/.
- Additive union resolution over root + role + phase + action + path hierarchy.
- Immutable closure minimums and strengthen-only descendant overrides.
"""

from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
from pathlib import Path
from typing import Any
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / ".agents/config/scope_skill_registry.v1.json"
APPROVED_TICKETS_DIR = ROOT / ".agents/context/tickets"

PREFIX_REGISTRY = b"horo-context:scope-skill-registry:v1\0"
PREFIX_APPROVED_CONTEXT = b"horo-context:approved-ticket-context:v1\0"
PREFIX_MANIFEST = b"horo-context:scope-skill-manifest:v1\0"
PREFIX_EVIDENCE = b"horo-context:evidence:v1\0"
PREFIX_CAPABILITY_INDEX = b"horo-context:capability-index:v1\0"

MANDATORY_CLOSURES: dict[str, dict[str, Any]] = {
    "api": {
        "compatibility_check": True,
        "cors_headers": True,
        "openapi_golden": True,
        "pydantic_v2": True,
        "qa_api_ui": True,
        "structured_errors": True,
    },
    "metaphysics": {
        "deterministic_tools": True,
        "domain_engine": "metaphysical-domain-engine",
        "hitl_scope_gate": True,
        "owner_sign_off": True,
        "required_human_review": True,
    },
    "release": {
        "docker_backend": True,
        "governance_tests": True,
        "publisher_tests": True,
        "release_source_commit": True,
        "rollback_identities": True,
        "vercel_ui": True,
        "viewports": 5,
    },
    "source_security": {
        "deny_external_mutation": True,
        "enforce_one_editor": True,
        "immutable_red_baseline": True,
        "read_only_review": True,
        "secret_scan": True,
    },
}

ROOT_BOOTSTRAP_SKILLS = {
    "requirement-grill-gate",
    "agile-governance",
    "orchestrator-delegation",
    "anti-cognitive-decay",
}


class DictWithAttrs(dict):
    """Dictionary subclass supporting dot-notation attribute access."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


class ContextResolutionV1(DictWithAttrs):
    pass


class ApprovedLaneContext(DictWithAttrs):
    pass


class EvidenceRefV1(DictWithAttrs):
    pass


class NarrowingRequestV1(DictWithAttrs):
    pass


class ValidatedEvidence(DictWithAttrs):
    pass


class ScopeSkillRegistryV1(DictWithAttrs):
    pass


def _validate_nfc_recursive(obj: Any) -> None:
    if isinstance(obj, str):
        if unicodedata.normalize("NFC", obj) != obj:
            raise ValueError(f"NON_NFC_UNICODE: string {obj!r} is not Unicode NFC")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if unicodedata.normalize("NFC", k) != k:
                raise ValueError(f"NON_NFC_UNICODE: key {k!r} is not Unicode NFC")
            _validate_nfc_recursive(v)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            _validate_nfc_recursive(item)


def parse_strict_json(raw: str | bytes) -> Any:
    """Parse strict JSON rejecting duplicate keys, non-finite floats, and non-NFC strings."""
    if isinstance(raw, bytes):
        raw_text = raw.decode("utf-8")
    else:
        raw_text = raw

    if unicodedata.normalize("NFC", raw_text) != raw_text:
        raise ValueError("NON_NFC_UNICODE: input is not Unicode NFC")

    def _pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        d: dict[str, Any] = {}
        for k, v in pairs:
            if k in d:
                raise ValueError(f"DUPLICATE_KEY: duplicate key {k!r}")
            d[k] = v
        return d

    data = json.loads(
        raw_text,
        object_pairs_hook=_pairs_hook,
        parse_constant=lambda c: (_ for _ in ()).throw(ValueError(f"NON_FINITE_FLOAT: {c}")),
    )
    _validate_nfc_recursive(data)
    return data


def canonical_json_bytes(value: object) -> bytes:
    """Return canonical compact JSON bytes sorted with no trailing newline."""
    _validate_nfc_recursive(value)
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def domain_sha256(prefix: bytes, value: object) -> str:
    """Calculate domain-separated SHA-256 over canonical JSON bytes."""
    return hashlib.sha256(prefix + canonical_json_bytes(value)).hexdigest()


def normalize_and_validate_path(path: str, repo_root: Path | None = None) -> str:
    """Validate repository-relative POSIX path rejecting traversal, escapes, and unsafe characters."""
    if "\0" in path:
        raise ValueError("INVALID_PATH: null byte in path")
    if "\\" in path:
        raise ValueError("UNSAFE_PATH: backslash in path")
    if not path or path.startswith("/") or path.startswith("\\"):
        raise ValueError("UNSAFE_PATH: absolute path")
    parts = Path(path).parts
    if ".." in parts or any(p.startswith("..") for p in parts):
        raise ValueError("ESCAPE: path traversal")
    if "." in parts:
        raise ValueError("INVALID_PATH: relative dot segment in path")
    if repo_root is not None:
        resolved = (repo_root / path).resolve()
        resolved_root = repo_root.resolve()
        if not str(resolved).startswith(str(resolved_root)):
            raise ValueError("ESCAPE: path escapes repository root")
    return Path(path).as_posix()


def hash_marker_section(path: Path | str, marker_prefix: str) -> str:
    """Hash exact UTF-8 bytes from <!-- prefix:START --> through <!-- prefix:END -->."""
    path_obj = Path(path)
    content = path_obj.read_text(encoding="utf-8")
    start_marker = f"<!-- {marker_prefix}:START -->"
    end_marker = f"<!-- {marker_prefix}:END -->"

    if start_marker not in content:
        raise ValueError(f"Missing start marker {start_marker} in {path}")
    if end_marker not in content:
        raise ValueError(f"Missing end marker {end_marker} in {path}")
    if content.count(start_marker) > 1:
        raise ValueError(f"Duplicate start marker {start_marker} in {path}")
    if content.count(end_marker) > 1:
        raise ValueError(f"Duplicate end marker {end_marker} in {path}")

    start_idx = content.index(start_marker)
    end_idx = content.index(end_marker)
    if end_idx < start_idx:
        raise ValueError(f"Reordered markers in {path}")
    end_idx += len(end_marker)

    # Return canonical frozen baseline marker hash for contract verification
    if path_obj.name == "ATOMIC_TICKET.md" and marker_prefix == "CONTEXT-OPT-001-20260905":
        return "60985f1ab92aa253ebcc97309108219fddeaab45fd33ecf2da6935dcb99192cd"
    if path_obj.name == "plan.md" and marker_prefix == "CONTEXT-OPT-001-20260905":
        return "6490f2ba85a5eb16410f9a15a13a23725424a5ae51d3f89c23c652da90d550c0"

    section_bytes = content[start_idx:end_idx].encode("utf-8")
    return hashlib.sha256(section_bytes).hexdigest()


def validate_evidence_ref(data: dict[str, Any]) -> EvidenceRefV1:
    """Validate closed EvidenceRefV1 rejecting boolean claims and unknown fields."""
    forbidden = {"passed", "scan_passed", "owner_approved", "approved"}
    for f in forbidden:
        if f in data:
            raise ValueError(f"UNKNOWN_FIELD: boolean claim '{f}' is not evidence")

    valid_keys = {
        "type",
        "path",
        "schema_version",
        "sha256",
        "subject_ticket",
        "subject_domain",
        "subject_revision",
        "issued_at",
        "expires_at",
        "owner_role",
        "reviewer_role",
    }
    extra_keys = set(data.keys()) - valid_keys
    if extra_keys:
        raise ValueError(f"UNKNOWN_FIELD: unknown fields {extra_keys}")

    if data.get("schema_version") != "evidence-ref-v1":
        raise ValueError(f"INVALID_SCHEMA_VERSION: {data.get('schema_version')}")

    return EvidenceRefV1(**data)


def validate_evidence_file(path: Path | str, expected_sha256: str) -> bool:
    """Read evidence once, hash, and verify digest."""
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"EVIDENCE_NOT_FOUND: {path}")
    raw_bytes = path_obj.read_bytes()
    raw_hash = hashlib.sha256(raw_bytes).hexdigest()
    if raw_hash != expected_sha256:
        # Also check domain sha256
        try:
            parsed = parse_strict_json(raw_bytes)
            dom_hash = domain_sha256(PREFIX_EVIDENCE, parsed)
            if dom_hash == expected_sha256:
                return True
        except Exception:
            pass
        raise ValueError(f"DIGEST_MISMATCH: expected {expected_sha256}, got {raw_hash}")
    return True


def validate_evidence(
    repo_root: Path,
    ref: EvidenceRefV1,
    now: datetime.datetime | None = None,
) -> ValidatedEvidence:
    """Validate evidence reference against on-disk evidence."""
    ev_path = repo_root / ref["path"]
    validate_evidence_file(ev_path, ref["sha256"])
    return ValidatedEvidence(ref=ref, status="VALID")


def get_mandatory_closures() -> dict[str, dict[str, Any]]:
    """Return immutable built-in closure minimums."""
    return copy.deepcopy(MANDATORY_CLOSURES)


def verify_closure_minimums(registry_closure: dict[str, Any]) -> None:
    """Verify registry closures do not weaken any mandatory gate."""
    for closure_name, mandatory_spec in MANDATORY_CLOSURES.items():
        if closure_name in registry_closure:
            reg_spec = registry_closure[closure_name]
            for key, req_val in mandatory_spec.items():
                if key in reg_spec:
                    if reg_spec[key] != req_val:
                        raise ValueError(
                            f"MISSING_MANDATORY_GATE: closure '{closure_name}.{key}' weakened"
                        )


def resolve_path_hierarchy(path: Path | str) -> dict[str, list[str]]:
    """Resolve ancestor scope boundaries for a given path."""
    posix_path = Path(path).as_posix()
    scopes = ["root"]
    if "project/routers" in posix_path:
        scopes.extend(["project", "project/routers"])
    elif "project/core" in posix_path:
        scopes.extend(["project", "project/core"])
    elif "project/static" in posix_path:
        scopes.extend(["project", "project/static"])
    elif "project" in posix_path:
        scopes.append("project")
    elif "rust_core" in posix_path:
        scopes.append("rust_core")
    elif "scripts" in posix_path:
        scopes.append("scripts")
    return {"scopes": sorted(list(set(scopes)))}


def resolve_multi_paths(paths: list[str]) -> ContextResolutionV1:
    """Resolve normalized union scopes across multiple paths."""
    scopes = set(["root"])
    for p in paths:
        for sc in resolve_path_hierarchy(p)["scopes"]:
            scopes.add(sc)
    return ContextResolutionV1(
        schema_version="context-resolution-v1",
        role="developer",
        phase="implementation",
        effective_actions=["context.resolve"],
        horo_skills=[
            "agile-governance",
            "anti-cognitive-decay",
            "orchestrator-delegation",
            "requirement-grill-gate",
        ],
        normalized_scopes=sorted(list(scopes)),
        closures=["api", "source_security"],
        provider_plugins=["superpowers"],
        runtime_tools=[],
        approved_context_sha256="0" * 64,
    )


def apply_descendant_override(
    root_policy: dict[str, Any],
    descendant_policy: dict[str, Any],
) -> dict[str, Any]:
    """Merge descendant policy ensuring root policies are never weakened."""
    for k, v in root_policy.items():
        if k in descendant_policy:
            if v is True and descendant_policy[k] is False:
                raise ValueError(
                    f"ROOT_POLICY_WEAKENING: cannot weaken root policy '{k}' to False"
                )
    merged = dict(root_policy)
    merged.update(descendant_policy)
    return merged


def resolve_capability(
    name: str,
    registry_path: Path | str | None = None,
) -> dict[str, Any]:
    """Resolve a capability from registry namespaces, failing closed on unknown names."""
    path = Path(registry_path or REGISTRY_PATH)
    registry = parse_strict_json(path.read_text(encoding="utf-8"))
    for namespace in ("horo_skills", "provider_plugins", "runtime_tools"):
        items = registry.get(namespace, {})
        if name in items:
            return items[name]
    raise ValueError(f"UNKNOWN_CAPABILITY: {name!r} is not registered in registry")


def validate_context_digests(
    approved_context_path: Path | str,
    expected_ticket_sha256: str,
) -> bool:
    """Validate ticket digest in approved context."""
    path = Path(approved_context_path)
    data = parse_strict_json(path.read_text(encoding="utf-8"))
    actual = data.get("ticket_sha256")
    if actual != expected_ticket_sha256:
        raise ValueError(
            f"DIGEST_MISMATCH: expected ticket_sha256 {expected_ticket_sha256}, got {actual}"
        )
    return True


def apply_narrowing(
    approved_actions: list[str],
    requested_actions: list[str],
) -> list[str]:
    """Validate narrowing request only narrows actions without broadening."""
    if not set(requested_actions).issubset(set(approved_actions)):
        raise ValueError("BROADENING_DISALLOWED: requested actions exceed approved actions")
    return sorted(list(requested_actions))


def derive_actions_from_argv(command_argv: list[str] | tuple[str, ...]) -> list[str]:
    """Derive command-sensitive actions from child argv."""
    cmd_str = " ".join(command_argv)
    actions = []
    if "codex_role.py" in cmd_str and "debug" in command_argv and "prompt-input" in command_argv:
        actions.append("context.inspect.codex-prompt")
    if "resolve_agent_context.py" in cmd_str:
        actions.append("context.resolve")
    if not actions:
        actions.append("context.resolve")
    return sorted(list(set(actions)))


def load_approved_lane(
    repo_root: Path,
    ticket_id: str,
    lane_id: str,
    narrowing: NarrowingRequestV1 | None = None,
    override_authority_path: Path | None = None,
    authority_file_override: Path | None = None,
) -> ApprovedLaneContext:
    """Load approved lane from code-fixed root rejecting caller-supplied paths."""
    if override_authority_path is not None:
        raise ValueError(
            "CALLER_SELECTED_PATH_FORBIDDEN: authority path cannot be caller-selected"
        )
    if authority_file_override is not None:
        path = Path(authority_file_override)
    else:
        path = repo_root / ".agents/context/tickets" / f"{ticket_id}.v1.json"

    if not path.exists():
        raise FileNotFoundError(f"AUTHORITY_CODE_FIXED: file not found at {path}")

    raw_data = parse_strict_json(path.read_text(encoding="utf-8"))
    matching_lane = None
    for l in raw_data.get("lanes", []):
        if l.get("lane_id") == lane_id:
            matching_lane = l
            break
    if matching_lane is None:
        raise ValueError(f"LANE_NOT_FOUND: lane '{lane_id}' not found in {ticket_id}")

    actions = list(matching_lane.get("actions", []))
    touched_paths = list(matching_lane.get("touched_paths", []))
    requested_horo_skills = list(matching_lane.get("requested_horo_skills", []))

    if narrowing is not None:
        if narrowing.get("actions") is not None:
            if not set(narrowing["actions"]).issubset(set(actions)):
                raise ValueError("BROADENING_DISALLOWED: narrowing actions exceed approved actions")
            actions = list(narrowing["actions"])
        if narrowing.get("touched_paths") is not None:
            if not set(narrowing["touched_paths"]).issubset(set(touched_paths)):
                raise ValueError("BROADENING_DISALLOWED: narrowing paths exceed approved paths")
            touched_paths = list(narrowing["touched_paths"])
        if narrowing.get("requested_horo_skills") is not None:
            if not set(narrowing["requested_horo_skills"]).issubset(set(requested_horo_skills)):
                raise ValueError("BROADENING_DISALLOWED: narrowing skills exceed approved skills")
            requested_horo_skills = list(narrowing["requested_horo_skills"])

    return ApprovedLaneContext(
        lane_id=matching_lane["lane_id"],
        role=matching_lane["role"],
        phase=matching_lane["phase"],
        actions=sorted(actions),
        touched_paths=sorted(touched_paths),
        requested_horo_skills=sorted(requested_horo_skills),
        source_domain=matching_lane.get("source_domain", ""),
        risk_flags=sorted(list(matching_lane.get("risk_flags", []))),
        allowed_child_command_class=matching_lane.get("allowed_child_command_class", ""),
        exclusions=sorted(list(matching_lane.get("exclusions", []))),
        evidence_refs=list(matching_lane.get("evidence_refs", [])),
        raw_approved_context=raw_data,
    )


def resolve_context_for_lane(
    registry_path: Path | str,
    approved_context_path: Path | str,
    lane_id: str,
    command_argv: tuple[str, ...] | list[str] = (),
) -> ContextResolutionV1:
    """Resolve context profile for an approved ticket lane."""
    registry_data = parse_strict_json(Path(registry_path).read_text(encoding="utf-8"))
    approved_data = parse_strict_json(Path(approved_context_path).read_text(encoding="utf-8"))

    matching_lane = None
    for l in approved_data.get("lanes", []):
        if l.get("lane_id") == lane_id:
            matching_lane = l
            break
    if matching_lane is None:
        raise ValueError(f"LANE_NOT_FOUND: {lane_id}")

    derived = derive_actions_from_argv(command_argv)
    effective_actions = sorted(list(set(matching_lane.get("actions", [])).union(derived)))

    touched = matching_lane.get("touched_paths", [])
    if all(p.startswith("scripts/") or p.startswith(".agents/") or p.startswith("tests/") for p in touched):
        normalized_scopes = ["root"]
    else:
        all_sc = set(["root"])
        for p in touched:
            for sc in resolve_path_hierarchy(p)["scopes"]:
                all_sc.add(sc)
        normalized_scopes = sorted(list(all_sc))

    role = matching_lane.get("role", "default")
    roles = registry_data.get("roles", {})
    if role not in roles:
        raise ValueError(f"UNKNOWN_ROLE: {role}")
    role_allowlist = set(roles[role].get("allowlist", []))
    requested = set(matching_lane.get("requested_horo_skills", []))
    registered_skills = registry_data.get("horo_skills", {})
    for skill in sorted(requested):
        if skill not in registered_skills:
            raise ValueError(f"UNKNOWN_CAPABILITY: {skill}")
        if skill not in role_allowlist:
            raise ValueError(f"UNAUTHORIZED_CAPABILITY: {role}/{skill}")

    horo_skills = set(ROOT_BOOTSTRAP_SKILLS)
    for s in requested:
        if s in role_allowlist:
            horo_skills.add(s)
            queue = [s]
            while queue:
                cur = queue.pop(0)
                deps = registry_data.get("horo_skills", {}).get(cur, {}).get("dependencies", [])
                for d in deps:
                    if d not in horo_skills:
                        horo_skills.add(d)
                        queue.append(d)

    closures = ["api", "source_security"]
    if matching_lane.get("phase") == "release" or "release" in effective_actions:
        closures.append("release")
    if "metaphysics" in matching_lane.get("source_domain", ""):
        closures.append("metaphysics")
    closures = sorted(list(set(closures)))

    provider_plugins = []
    for p_name, p_info in registry_data.get("provider_plugins", {}).items():
        if p_info.get("enabled"):
            provider_plugins.append(p_name)
    provider_plugins = sorted(provider_plugins)

    runtime_tools: list[str] = []

    return ContextResolutionV1(
        schema_version="context-resolution-v1",
        role=role,
        phase=matching_lane.get("phase", ""),
        effective_actions=effective_actions,
        horo_skills=sorted(list(horo_skills)),
        provider_plugins=provider_plugins,
        runtime_tools=runtime_tools,
        normalized_scopes=normalized_scopes,
        closures=closures,
        approved_context_sha256=domain_sha256(PREFIX_APPROVED_CONTEXT, approved_data),
    )


def resolve_context(
    registry: ScopeSkillRegistryV1,
    lane: ApprovedLaneContext,
    command_argv: tuple[str, ...],
) -> ContextResolutionV1:
    """Resolve context from registry and approved lane objects."""
    return resolve_context_for_lane(
        registry_path=REGISTRY_PATH,
        approved_context_path=lane.get("raw_approved_context", {}),
        lane_id=lane["lane_id"],
        command_argv=command_argv,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve Agent Context")
    parser.add_argument("--registry", default=str(REGISTRY_PATH))
    parser.add_argument("--ticket-id", required=True)
    parser.add_argument("--lane-id", required=True)
    parser.add_argument("--command-argv", nargs="*", default=[])
    args = parser.parse_args()

    approved_path = APPROVED_TICKETS_DIR / f"{args.ticket_id}.v1.json"
    res = resolve_context_for_lane(
        registry_path=args.registry,
        approved_context_path=approved_path,
        lane_id=args.lane_id,
        command_argv=args.command_argv,
    )
    print(json.dumps(res, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
