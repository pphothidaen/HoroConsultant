"""
KAN-258: API Authentication Tests
Tests that all API endpoints require Google ID Token authentication.
"""
import pytest
import os
from fastapi.testclient import TestClient


def create_test_client(testing_mode: bool = True):
    """Create a test client with specified testing mode."""
    if testing_mode:
        os.environ["TESTING"] = "1"
        os.environ["PYTEST_CURRENT_TEST"] = "test_session"
    else:
        os.environ["TESTING"] = "0"
        if "PYTEST_CURRENT_TEST" in os.environ:
            del os.environ["PYTEST_CURRENT_TEST"]
    
    # Force fresh import
    import sys
    for mod in list(sys.modules.keys()):
        if 'project' in mod:
            del sys.modules[mod]
    
    from project.main import app
    return TestClient(app)


# Endpoints that should be PUBLIC (no auth required in either mode)
PUBLIC_ENDPOINTS = [
    ("GET", "/"),
    ("GET", "/health"),
    ("GET", "/metrics"),
    ("GET", "/docs"),
    ("GET", "/redoc"),
    ("GET", "/openapi.json"),
    ("GET", "/admin/auth/config"),  # Bootstrap auth config
    ("POST", "/admin/auth/google"),  # Verify Google token
    ("GET", "/hitl/stats"),  # Explicitly allowed in middleware
    ("GET", "/advanced"),
    ("GET", "/hitl-studio"),
    ("GET", "/app.js"),
    ("GET", "/style.css"),
    ("GET", "/lite"),
    ("GET", "/lite/"),
    ("GET", "/lite.css"),
    ("GET", "/lite.js"),
    ("GET", "/voice_engine.js"),
    ("GET", "/i18n.js"),
    ("GET", "/sw.js"),
    ("GET", "/version.json"),
    ("GET", "/export_engine.js"),
    ("GET", "/export_modal.css"),
]

# Endpoints that should REQUIRE authentication when NOT in test mode
PROTECTED_ENDPOINTS = [
    # Astrology calculation endpoints
    ("GET", "/api/v1/bazi/calculate"),
    ("GET", "/api/v1/ziwei/calculate"),
    ("GET", "/api/v1/qimen/calculate"),
    ("GET", "/api/v1/liuren/calculate"),
    ("GET", "/api/v1/iching/calculate"),
    ("GET", "/api/v1/xuankong/calculate"),
    ("GET", "/api/v1/zeji/calculate"),
    ("GET", "/api/v1/thaivedic/calculate"),
    ("GET", "/api/v1/western/calculate"),
    ("GET", "/api/v1/numerology/calculate"),
    ("GET", "/api/v1/eot"),
    ("POST", "/api/v1/location/resolve"),
    
    # MCP endpoints
    ("GET", "/api/mcp/manifest"),
    ("POST", "/api/mcp/call"),
    
    # Route/Focus endpoints
    ("GET", "/api/route/focus"),
    ("POST", "/api/route/focus"),
    
    # Debate endpoints
    ("POST", "/api/debate/synthesize"),
    
    # Universal calculation endpoints
    ("GET", "/api/calculate/bazi"),
    ("POST", "/api/calculate/bazi"),
    
    # Admin data endpoints (not auth bootstrap)
    ("GET", "/admin/catalog"),
    ("GET", "/admin/catalog/summary"),
    ("GET", "/admin/provider-pools"),
    ("GET", "/admin/grayzone"),
    ("GET", "/admin/finetune/status"),
    
    # HITL endpoints (except stats)
    ("GET", "/hitl/queue"),
    ("GET", "/hitl/item/test"),
    ("POST", "/hitl/draft/test"),
    ("POST", "/hitl/review/test"),
    ("GET", "/hitl/export"),
    ("POST", "/hitl/batch-draft"),
    ("DELETE", "/hitl/review/test"),
    ("GET", "/hitl/backoffice"),
    ("GET", "/hitl/scope-audit"),
    ("POST", "/hitl/trigger"),
    
    # V2/V3 endpoints
    ("GET", "/api/v2/health"),
    ("POST", "/api/v2/calculate/unified"),
    ("POST", "/api/v2/interpret/focused"),
    ("POST", "/api/v2/interpret/grounded"),
    ("GET", "/api/v2/interpret/grounded/jobs/test"),
    ("POST", "/api/v2/mian_xiang/analyze"),
    ("GET", "/api/v2/llm/providers/status"),
    ("GET", "/api/v2/llm/aipass/preflight"),
    ("POST", "/api/v2/llm/route-test"),
    ("GET", "/api/v3/health"),
    ("POST", "/api/v3/calculate"),
    ("GET", "/api/v3/schema"),
    ("POST", "/api/v3/audit"),
    
    # Synastry
    ("POST", "/api/v1/synastry/analyze"),
    
    # Calendar
    ("GET", "/api/v1/calendar/month"),
    ("POST", "/api/v1/calendar/query-dates"),
    
    # Simulation
    ("GET", "/api/v1/simulation/preset-scenarios"),
    ("POST", "/api/v1/simulation/simulate-scenarios"),
    
    # LuoPan & Dream
    ("POST", "/api/v1/luopan/calculate"),
    ("POST", "/api/v1/dream/interpret"),
    
    # MLOps
    ("GET", "/api/v1/mlops/status"),
    ("GET", "/api/v1/mlops/hf_status"),
    ("GET", "/api/v1/mlops/checklist"),
    ("GET", "/api/v1/mlops/datasets"),
    ("POST", "/api/v1/mlops/distill"),
    ("POST", "/api/v1/mlops/train"),
    ("POST", "/api/v1/mlops/telegram/webhook"),
]


class TestKAN258APIAuth:
    """Test that all API endpoints require authentication."""
    
    def test_public_endpoints_accessible_in_test_mode(self):
        """Public endpoints should work in test mode (TESTING=1)."""
        client = create_test_client(testing_mode=True)
        for method, path in PUBLIC_ENDPOINTS:
            if method == "GET":
                resp = client.get(path)
            elif method == "POST":
                resp = client.post(path, json={})
            else:
                continue
            
            # Public endpoints should NOT return 401/403 in test mode
            assert resp.status_code not in (401, 403), \
                f"Public endpoint {method} {path} returned {resp.status_code} in test mode - should be accessible"
    
    def test_protected_endpoints_accessible_in_test_mode(self):
        """Protected endpoints should work in test mode (TESTING=1) due to test bypass."""
        client = create_test_client(testing_mode=True)
        for method, path in PROTECTED_ENDPOINTS:
            if method == "GET":
                resp = client.get(path)
            elif method == "POST":
                resp = client.post(path, json={})
            else:
                continue
            
            # In test mode, protected endpoints should NOT return 401/403 (test bypass)
            # They may return 404/405 if not registered, or 200/422 if registered
            assert resp.status_code not in (401, 403), \
                f"Protected endpoint {method} {path} returned {resp.status_code} in test mode - should be accessible due to test bypass"
    
    def test_public_endpoints_accessible_in_production_mode(self):
        """Public endpoints should work in production mode (TESTING=0)."""
        client = create_test_client(testing_mode=False)
        for method, path in PUBLIC_ENDPOINTS:
            if method == "GET":
                resp = client.get(path)
            elif method == "POST":
                resp = client.post(path, json={})
            else:
                continue
            
            # Public endpoints should NOT return 401/403 in production mode
            assert resp.status_code not in (401, 403), \
                f"Public endpoint {method} {path} returned {resp.status_code} in production mode - should be accessible"
    
    def test_protected_endpoints_require_auth_in_production_mode(self):
        """Protected endpoints should return 401/403 in production mode (TESTING=0)."""
        client = create_test_client(testing_mode=False)
        for method, path in PROTECTED_ENDPOINTS:
            if method == "GET":
                resp = client.get(path)
            elif method == "POST":
                resp = client.post(path, json={})
            else:
                continue
            
            # In production mode, protected endpoints should return 401 or 403
            # (or 404/405 if path doesn't exist or wrong method)
            assert resp.status_code in (401, 403, 404, 405), \
                f"Protected endpoint {method} {path} returned {resp.status_code} in production mode - should require auth (401/403)"
    
    def test_admin_data_endpoints_require_bearer_token(self):
        """Admin data endpoints should require Bearer token in production mode."""
        client = create_test_client(testing_mode=False)
        admin_data_endpoints = [
            "/admin/catalog",
            "/admin/catalog/summary",
            "/admin/provider-pools",
            "/admin/grayzone",
            "/admin/finetune/status",
        ]
        
        for path in admin_data_endpoints:
            # Without Authorization header
            resp = client.get(path)
            assert resp.status_code == 401, \
                f"{path} should return 401 without auth, got {resp.status_code}"
            
            # With invalid Authorization header
            resp = client.get(path, headers={"Authorization": "Bearer invalid_token"})
            assert resp.status_code in (401, 403), \
                f"{path} should return 401/403 with invalid token, got {resp.status_code}"
    
    def test_hitl_stats_endpoint_public_in_both_modes(self):
        """HITL stats endpoint should be publicly accessible in both modes."""
        # Test mode
        client_test = create_test_client(testing_mode=True)
        resp = client_test.get("/hitl/stats")
        assert resp.status_code != 401, "/hitl/stats should be public in test mode"
        
        # Production mode
        client_prod = create_test_client(testing_mode=False)
        resp = client_prod.get("/hitl/stats")
        assert resp.status_code != 401, "/hitl/stats should be public in production mode"
    
    def test_calculate_endpoints_require_auth_in_production_mode(self):
        """All /calculate/* and /api/calculate/* endpoints should require auth in production mode."""
        client = create_test_client(testing_mode=False)
        calc_endpoints = [
            "/calculate/bazi",
            "/api/calculate/bazi",
            "/calculate/ziwei",
            "/api/calculate/ziwei",
            "/calculate/qimen",
            "/api/calculate/qimen",
        ]
        
        for path in calc_endpoints:
            resp = client.get(path)
            assert resp.status_code in (401, 403, 404), \
                f"{path} should require auth (401/403) in production mode, got {resp.status_code}"
            
            resp = client.post(path, json={})
            assert resp.status_code in (401, 403, 404, 422), \
                f"POST {path} should require auth (401/403) in production mode, got {resp.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])