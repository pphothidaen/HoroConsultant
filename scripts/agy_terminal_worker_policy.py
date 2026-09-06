"""Build and validate a local candidate policy, without runtime enforcement proof.

This module performs no CLI, authentication, provider, or admission operations.
"""

POLICY_STATUS = "CANDIDATE_UNVERIFIED"

_DENIES = (
    "read_file(*)",
    "write_file(*)",
    "read_url(*)",
    "execute_url(*)",
    "command(*)",
    "unsandboxed(*)",
    "mcp(*)",
)


def build_candidate_policy() -> dict:
    """Return a fresh candidate configuration in canonical denial order."""
    return {"permissions": {"allow": [], "deny": list(_DENIES)}}


def validate_candidate_policy(value: object) -> dict:
    """Return a fresh canonical candidate or raise ValueError without mutation."""
    if type(value) is not dict or any(type(key) is not str for key in value):
        raise ValueError("Candidate policy must be a plain dict with string keys")
    if set(value) != {"permissions"}:
        raise ValueError("Candidate policy requires only permissions")
    permissions = value["permissions"]
    if type(permissions) is not dict or any(type(key) is not str for key in permissions):
        raise ValueError("Permissions must be a plain dict with string keys")
    if set(permissions) != {"allow", "deny"}:
        raise ValueError("Permissions requires only allow and deny")
    allow, deny = permissions["allow"], permissions["deny"]
    if type(allow) is not list or allow:
        raise ValueError("Allow must be an empty plain list")
    if type(deny) is not list or any(type(rule) is not str for rule in deny):
        raise ValueError("Deny must be a plain list of strings")
    if len(deny) != len(_DENIES) or set(deny) != set(_DENIES):
        raise ValueError("Deny must contain each exact candidate rule once")
    return build_candidate_policy()
