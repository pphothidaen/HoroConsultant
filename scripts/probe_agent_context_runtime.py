#!/usr/bin/env python3
"""Provider context runtime probe and hierarchy resolver.

Implements:
- Provider hierarchy resolution: broad-to-narrow union across scopes without weakening.
- ProviderContextProbeV1 closed field schema and domain hash:
    b"horo-context:evidence:v1\\0"
- Provider probe requirements: fresh PASS for Codex, Claude, and AGY; static parity only for Antigravity.
- UNAVAILABLE and UNKNOWN results are nonzero exit codes and never pass-by-skip.
- Sanitized evidence SHA-256 excludes raw provider streams, environment, and secrets.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Literal
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / ".agents/config/scope_skill_registry.v1.json"
APPROVED_TICKETS_DIR = ROOT / ".agents/context/tickets"

PREFIX_REGISTRY = b"horo-context:scope-skill-registry:v1\0"
PREFIX_APPROVED_CONTEXT = b"horo-context:approved-ticket-context:v1\0"
PREFIX_EVIDENCE = b"horo-context:evidence:v1\0"

EXPECTED_PROBE_FIELDS = [
    "schema_version",
    "provider",
    "adapter_version",
    "registry_sha256",
    "approved_context_sha256",
    "normalized_scopes",
    "horo_skills",
    "provider_plugins",
    "runtime_tools",
    "result",
    "reason_code",
    "exit_code",
    "issued_at",
    "expires_at",
    "sanitized_evidence_sha256",
]

FORBIDDEN_PROBE_KEYS = {
    "stdout",
    "stderr",
    "stream",
    "env",
    "secret",
    "token",
    "password",
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


class ProviderContextProbeV1(DictWithAttrs):
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


def canonical_json_bytes(value: object) -> bytes:
    _validate_nfc_recursive(value)
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def domain_sha256(prefix: bytes, value: object) -> str:
    return hashlib.sha256(prefix + canonical_json_bytes(value)).hexdigest()


def compute_sanitized_evidence_digest(raw: dict[str, Any]) -> str:
    """Compute domain-separated SHA-256 for sanitized evidence excluding raw fields and self."""
    for fk in FORBIDDEN_PROBE_KEYS:
        if fk in raw:
            raise ValueError(f"FORBIDDEN_FIELD_PRESENT: raw/secret field '{fk}' must not be present")
    clean = {k: v for k, v in raw.items() if k != "sanitized_evidence_sha256"}
    return domain_sha256(PREFIX_EVIDENCE, clean)


def validate_probe_schema(raw: dict[str, Any]) -> None:
    """Validate ProviderContextProbeV1 closed field schema and forbidden fields."""
    for fk in FORBIDDEN_PROBE_KEYS:
        if fk in raw:
            raise ValueError(f"FORBIDDEN_KEY: ProviderContextProbeV1 must not contain raw/secret field '{fk}'")

    for ef in EXPECTED_PROBE_FIELDS:
        if ef not in raw:
            raise ValueError(f"MISSING_FIELD: Field '{ef}' must be present in ProviderContextProbeV1")

    extra_fields = set(raw.keys()) - set(EXPECTED_PROBE_FIELDS)
    if extra_fields:
        raise ValueError(f"UNKNOWN_FIELD: Unknown fields present: {extra_fields}")
    if raw['schema_version'] != 'provider-context-probe-v1' or raw['provider'] not in ('codex', 'claude', 'agy'):
        raise ValueError('INVALID_PROVIDER_OR_SCHEMA')
    for key in ('registry_sha256', 'approved_context_sha256', 'sanitized_evidence_sha256'):
        value = raw[key]
        if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value) or value == '0' * 64:
            raise ValueError(f'INVALID_IDENTITY: {key}')
    if raw['sanitized_evidence_sha256'] != compute_sanitized_evidence_digest(raw):
        raise ValueError('EVIDENCE_DIGEST_MISMATCH')
    if raw['result'] not in ('PASS', 'UNKNOWN', 'UNAVAILABLE', 'FAIL'):
        raise ValueError('INVALID_RESULT')
    code = raw['exit_code']
    if type(code) is not int or code < 0 or (raw['result'] == 'PASS') != (code == 0):
        raise ValueError('INVALID_EXIT_CODE')
    for key in ('normalized_scopes', 'horo_skills', 'provider_plugins', 'runtime_tools'):
        values = raw[key]
        if not isinstance(values, list) or any(not isinstance(v, str) or not v for v in values) or len(values) != len(set(values)):
            raise ValueError(f'INVALID_CAPABILITY_LIST: {key}')
    for key in ('adapter_version', 'reason_code'):
        if not isinstance(raw[key], str) or not raw[key].strip():
            raise ValueError(f'INVALID_FIELD: {key}')
    issued, expires = (_probe_time(raw[key]) for key in ('issued_at', 'expires_at'))
    if expires <= issued or (expires - issued).total_seconds() > 120:
        raise ValueError('INVALID_RECEIPT_LIFETIME')


def _probe_time(value: str) -> datetime.datetime:
    try:
        parsed = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            raise ValueError('timezone required')
        return parsed.astimezone(datetime.timezone.utc)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError('INVALID_TIMESTAMP') from exc


def validate_probe_receipt(raw: dict[str, Any], *, expected_registry_sha256: str,
                           expected_approved_context_sha256: str,
                           now: datetime.datetime | None = None,
                           require_native: bool = True) -> None:
    """Validate static integrity; a self-hash never authenticates native execution."""
    validate_probe_schema(raw)
    clock = now or datetime.datetime.now(datetime.timezone.utc)
    if clock.tzinfo is None:
        raise ValueError('TIMEZONE_REQUIRED')
    if not _probe_time(raw['issued_at']) <= clock < _probe_time(raw['expires_at']):
        raise ValueError('STALE_OR_FUTURE_RECEIPT')
    if raw['registry_sha256'] != expected_registry_sha256 or raw['approved_context_sha256'] != expected_approved_context_sha256:
        raise ValueError('CURRENT_IDENTITY_MISMATCH')
    if require_native:
        # V1 carries no independently authenticated provider observation.
        raise ValueError('TRUSTED_NATIVE_PROOF_UNAVAILABLE')


def resolve_provider_hierarchy(
    provider: str,
    target_path: str,
    ticket_id: str,
    lane_id: str,
) -> dict[str, Any]:
    """Resolve provider hierarchy broad-to-narrow union across scopes."""
    posix_path = Path(target_path).as_posix()
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

    normalized_scopes = sorted(list(set(scopes)))

    return {
        "provider": provider,
        "target_path": target_path,
        "ticket_id": ticket_id,
        "lane_id": lane_id,
        "normalized_scopes": normalized_scopes,
        "horo_skills": [
            "agile-governance",
            "anti-cognitive-decay",
            "orchestrator-delegation",
            "requirement-grill-gate",
        ],
        "provider_plugins": ["superpowers"],
        "runtime_tools": [],
    }


def build_probe_receipt(
    provider: str,
    result: str,
    reason_code: str,
    exit_code: int = 0,
    normalized_scopes: list[str] | None = None,
    horo_skills: list[str] | None = None,
    provider_plugins: list[str] | None = None,
    runtime_tools: list[str] | None = None,
    registry_sha256: str = "0" * 64,
    approved_context_sha256: str = "0" * 64,
) -> ProviderContextProbeV1:
    """Build ProviderContextProbeV1 receipt enforcing fail-closed nonzero exit on UNAVAILABLE/UNKNOWN."""
    if result in ("UNAVAILABLE", "UNKNOWN"):
        if exit_code == 0:
            exit_code = 1
        if registry_sha256 == '0' * 64 or approved_context_sha256 == '0' * 64:
            return ProviderContextProbeV1(schema_version='provider-context-probe-unavailable-v1',
                                          provider=provider, result=result, exit_code=exit_code,
                                          reason_code='UNBOUND_CONTEXT: ' + reason_code)

    now = datetime.datetime.now(datetime.timezone.utc)
    issued_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    expires_at = (now + datetime.timedelta(seconds=120)).strftime("%Y-%m-%dT%H:%M:%SZ")

    data: dict[str, Any] = {
        "schema_version": "provider-context-probe-v1",
        "provider": provider,
        "adapter_version": f"{provider}-probe-v1",
        "registry_sha256": registry_sha256,
        "approved_context_sha256": approved_context_sha256,
        "normalized_scopes": ["root"] if normalized_scopes is None else normalized_scopes,
        "horo_skills": [
            "agile-governance",
            "anti-cognitive-decay",
            "orchestrator-delegation",
            "requirement-grill-gate",
        ] if horo_skills is None else horo_skills,
        "provider_plugins": ["superpowers"] if provider_plugins is None else provider_plugins,
        "runtime_tools": [] if runtime_tools is None else runtime_tools,
        "result": result,
        "reason_code": reason_code,
        "exit_code": exit_code,
        "issued_at": issued_at,
        "expires_at": expires_at,
    }
    data["sanitized_evidence_sha256"] = compute_sanitized_evidence_digest(data)
    validate_probe_schema(data)
    return ProviderContextProbeV1(**data)


def run_provider_probe(
    provider: str,
    ticket_id: str,
    lane_id: str,
    no_network: bool = True,
) -> ProviderContextProbeV1:
    """Run provider probe; Antigravity is static parity only and cannot run runtime probe."""
    if provider == "antigravity":
        raise ValueError("RUNTIME_PROBE_NOT_SUPPORTED: STATIC_PARITY_ONLY Antigravity emits no runtime probe receipt")

    if provider not in ("codex", "claude", "agy"):
        raise ValueError(f"UNSUPPORTED_PROVIDER: {provider}")

    from scripts.resolve_agent_context import resolve_context_for_lane
    from scripts.render_agent_context_profiles import safe_open_bounded
    if not re.fullmatch(r'TICKET-[A-Z0-9-]+', ticket_id):
        raise ValueError('INVALID_TICKET_ID')
    context_path = APPROVED_TICKETS_DIR / f'{ticket_id}.v1.json'
    try:
        context = json.loads(safe_open_bounded(context_path, ROOT))
        registry = json.loads(safe_open_bounded(REGISTRY_PATH, ROOT))
    except (OSError, ValueError):
        # A diagnostic is deliberately not a valid, hash-bound evidence receipt.
        return ProviderContextProbeV1(schema_version='provider-context-probe-unavailable-v1',
                                      provider=provider, result='UNKNOWN', exit_code=1,
                                      reason_code='CONTEXT_OR_REGISTRY_UNAVAILABLE')
    try:
        resolution = resolve_context_for_lane(
            registry_path=REGISTRY_PATH, approved_context_path=context_path,
            lane_id=lane_id, command_argv=['context.resolve'],
        )
    except ValueError:
        return build_probe_receipt(provider, 'UNKNOWN', 'CONTEXT_RESOLUTION_FAILED', 1,
                                   registry_sha256=domain_sha256(PREFIX_REGISTRY, registry),
                                   approved_context_sha256=domain_sha256(PREFIX_APPROVED_CONTEXT, context))
    return build_probe_receipt(
        provider=provider,
        result="UNAVAILABLE",
        reason_code="TRUSTED_NATIVE_PROOF_UNAVAILABLE",
        exit_code=1,
        registry_sha256=domain_sha256(PREFIX_REGISTRY, registry),
        approved_context_sha256=resolution['approved_context_sha256'],
        normalized_scopes=resolution['normalized_scopes'],
        horo_skills=resolution['horo_skills'],
        provider_plugins=resolution['provider_plugins'],
        runtime_tools=resolution['runtime_tools'],
    )


def probe_provider_context(
    provider: Literal["codex", "claude", "agy"],
    ticket_id: str,
    lane_id: str,
) -> ProviderContextProbeV1:
    """Interface method to probe provider context."""
    return run_provider_probe(provider=provider, ticket_id=ticket_id, lane_id=lane_id)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe Agent Context Runtime")
    parser.add_argument("--provider", required=True, choices=["codex", "claude", "agy", "antigravity"])
    parser.add_argument("--ticket-id", required=True)
    parser.add_argument("--lane-id", required=True)
    parser.add_argument("--no-network", action="store_true", default=True)

    args = parser.parse_args(argv)

    try:
        receipt = run_provider_probe(
            provider=args.provider,
            ticket_id=args.ticket_id,
            lane_id=args.lane_id,
            no_network=args.no_network,
        )
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return receipt.exit_code
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    # Support direct script invocation as well as python -m scripts.<module>.
    import sys
    if not __package__:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    raise SystemExit(main())
