"""Fail-closed secret guard for the tracked .mcp.json MCP config.

.mcp.json is committed to a PUBLIC repository, so it must never contain
literal credentials. MCP authentication belongs in user-scope config
(~/.claude.json) or ${VAR} environment references.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MCP_JSON = ROOT / ".mcp.json"

ENV_REFERENCE = re.compile(r"^\$\{[A-Za-z_][A-Za-z0-9_]*\}$")
CREDENTIAL_PATTERNS = (
    ("bearer-token", re.compile(r"^Bearer\s+\S{20,}$", re.IGNORECASE)),
    (
        "known-key-prefix",
        re.compile(
            r"\b(?:ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}"
            r"|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}"
            r"|xox[bp]-[A-Za-z0-9-]{20,}|AKIA[0-9A-Z]{16}"
            r"|hf_[A-Za-z0-9]{20,})"
        ),
    ),
    ("long-base64-blob", re.compile(r"^[A-Za-z0-9+/_=-]{40,}$")),
    ("long-hex-blob", re.compile(r"^[a-f0-9]{32,}$")),
)


def _mcp_servers() -> dict:
    data = json.loads(MCP_JSON.read_text(encoding="utf-8"))
    servers = data.get("mcpServers")
    assert isinstance(servers, dict), "mcpServers must be a JSON object"
    return servers


def test_mcp_json_parses_with_mcp_servers_object() -> None:
    servers = _mcp_servers()
    assert isinstance(servers, dict)


def test_tracked_mcp_json_has_no_literal_credentials() -> None:
    violations: list[str] = []
    for server_name, config in _mcp_servers().items():
        credential_fields: dict[str, str] = {}
        credential_fields.update(config.get("headers") or {})
        env = config.get("env") or {}
        if isinstance(env, dict):
            credential_fields.update(env)
        for field_name, value in credential_fields.items():
            if not isinstance(value, str):
                continue
            if ENV_REFERENCE.match(value):
                continue
            for label, pattern in CREDENTIAL_PATTERNS:
                if pattern.search(value):
                    violations.append(
                        f"server {server_name!r} field {field_name!r} matches {label}"
                    )
                    break
    assert not violations, (
        "literal credential suspected in tracked .mcp.json "
        f"({'; '.join(violations)}); use ${{VAR}} env references or "
        "user-scope MCP config instead of committing secrets"
    )
