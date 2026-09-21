"""Contract test: Rust gateway routing table must match Python FastAPI routes.

Prevents the class of bug where routes added to Python (e.g. /admin/provider-pools)
are silently dropped with 404 because the Rust gateway's route_kind() allowlist
was not updated.

Strategy:
  1. Parse rust_core/src/server.rs route_kind() for:
     - Explicit routes: (&Method::GET, "/path")
     - Dynamic prefixes: one_segment_after(dynamic, "/prefix/") or starts_with("/prefix/")
  2. Load the OpenAPI manifest and enumerate (method, path) pairs.
  3. For each OpenAPI route, check if it's covered by explicit routes
     OR dynamic prefix patterns (normalizing {param} → prefix match).
  4. Assert no route is missing.
"""

import re
from pathlib import Path

import pytest

# ── Paths ──────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_RS = REPO_ROOT / "rust_core/src/server.rs"
OPENAPI_JSON = Path("/tmp/oa.json")  # populated by test-first provenance flow


# ── Helpers ─────────────────────────────────────────────────────────────────

def _get_route_kind_body(server_rs_path: Path) -> str:
    """Extract the body of route_kind() from server.rs."""
    text = server_rs_path.read_text()
    start = text.index("fn route_kind")
    end = text.index("fn path_is_known")
    return text[start:end]


def _parse_rust_explicit_routes(server_rs_path: Path) -> set[tuple[str, str]]:
    """Extract explicit (method, path) tuples from route_kind()."""
    body = _get_route_kind_body(server_rs_path)
    pattern = re.compile(r'&Method::(\w+),\s*"([^"]*)"')
    routes: set[tuple[str, str]] = set()
    for method, path in pattern.findall(body):
        if path.startswith("/static/"):
            continue
        routes.add((method.lower(), path))
    return routes


def _parse_rust_dynamic_prefixes(server_rs_path: Path) -> set[str]:
    """Extract all dynamic path prefixes from route_kind().

    Handles:
      - one_segment_after(dynamic, "/prefix/")
      - dynamic.starts_with("/prefix/")
    """
    body = _get_route_kind_body(server_rs_path)

    # Find all one_segment_after prefixes
    one_seg = re.findall(r'one_segment_after\(dynamic,\s*"([^"]*)"\)', body)
    # Find all starts_with prefixes
    starts_with = re.findall(r'starts_with\("([^"]*)"\)', body)

    return set(one_seg + starts_with)


def _load_openapi_routes(openapi_path: Path) -> set[tuple[str, str]]:
    """Load (method, path) pairs from a local OpenAPI JSON file."""
    import json
    data = json.loads(openapi_path.read_text())
    routes: set[tuple[str, str]] = set()
    for path, methods in data.get("paths", {}).items():
        for method in methods:
            if method in ("parameters",):
                continue
            routes.add((method.lower(), path))
    return routes


def _normalize_param_path(path: str) -> str:
    """Normalize OpenAPI path params to prefix form for dynamic matching.

    /api/visualize/{discipline} -> /api/visualize/
    /hitl/item/{item_id}         -> /hitl/item/
    """
    idx = path.find("/{")
    if idx >= 0:
        return path[:idx] + "/"
    return path


def _route_is_covered(
    method: str,
    path: str,
    explicit_routes: set[tuple[str, str]],
    dynamic_prefixes: set[str],
) -> bool:
    """Check if a route is covered by explicit routes OR dynamic patterns."""
    # Check explicit routes
    if (method, path) in explicit_routes:
        return True

    # Check dynamic patterns (for paths with parameters)
    if "{" in path:
        prefix = _normalize_param_path(path)
        if prefix in dynamic_prefixes:
            return True

    return False


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def rust_explicit_routes():
    if not SERVER_RS.exists():
        pytest.skip(f"{SERVER_RS} not found")
    return _parse_rust_explicit_routes(SERVER_RS)


@pytest.fixture(scope="module")
def rust_dynamic_prefixes():
    if not SERVER_RS.exists():
        pytest.skip(f"{SERVER_RS} not found")
    return _parse_rust_dynamic_prefixes(SERVER_RS)


@pytest.fixture(scope="module")
def openapi_routes():
    if not OPENAPI_JSON.exists():
        pytest.skip(f"{OPENAPI_JSON} not found")
    return _load_openapi_routes(OPENAPI_JSON)


@pytest.fixture(scope="module")
def openapi_path_methods(openapi_routes):
    by_path: dict[str, set[str]] = {}
    for method, path in openapi_routes:
        by_path.setdefault(path, set()).add(method)
    return by_path


# ── Tests ───────────────────────────────────────────────────────────────────

pytestmark = [pytest.mark.contract]


class TestRustRouteCoverage:
    """Every route in the Python OpenAPI must exist in the Rust allowlist."""

    def test_all_openapi_paths_have_rust_entry(
        self, rust_explicit_routes, rust_dynamic_prefixes, openapi_routes
    ):
        """No Python route should return a Rust-level 404."""
        missing = []
        for method, path in sorted(openapi_routes):
            if not _route_is_covered(method, path, rust_explicit_routes, rust_dynamic_prefixes):
                missing.append((method, path))

        if missing:
            formatted = sorted(f"  {m:6s} {p}" for m, p in missing)
            pytest.fail(
                f"{len(missing)} route(s) in Python OpenAPI are NOT covered by "
                f"the Rust gateway routing table:\n" + "\n".join(formatted)
            )

    def test_admin_provider_pools_is_routed(self, rust_explicit_routes):
        """Regression guard for the originally reported production 404."""
        assert ("get", "/admin/provider-pools") in rust_explicit_routes, (
            "/admin/provider-pools is missing from the Rust routing table"
        )

    def test_all_admin_paths_proxied(
        self, rust_explicit_routes, rust_dynamic_prefixes, openapi_path_methods
    ):
        """Every /admin/* path in OpenAPI must be covered by the Rust table."""
        admin_paths = {p for p in openapi_path_methods if p.startswith("/admin/")}
        missing = []
        for path in admin_paths:
            methods = openapi_path_methods[path]
            for method in methods:
                if not _route_is_covered(method, path, rust_explicit_routes, rust_dynamic_prefixes):
                    missing.append((method, path))

        if missing:
            formatted = sorted(f"  {m:6s} {p}" for m, p in missing)
            pytest.fail(
                f"Admin paths missing from Rust routing table:\n" + "\n".join(formatted)
            )

    def test_health_is_native(self, rust_explicit_routes):
        """/health must be a Native route (Liveness), not proxied to Python."""
        assert ("get", "/health") in rust_explicit_routes

    def test_visualize_param_route_is_covered(
        self, rust_explicit_routes, rust_dynamic_prefixes
    ):
        """Regression: /api/visualize/{discipline} was missing from Rust table."""
        for method in ("get", "post"):
            assert _route_is_covered(
                method, "/api/visualize/{discipline}",
                rust_explicit_routes, rust_dynamic_prefixes
            ), f"/api/visualize/{{discipline}} ({method.upper()}) not covered"
