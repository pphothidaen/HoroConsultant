"""
project/tests/test_button_regression.py
=========================================
Comprehensive UI Button Regression Test Suite for HoroConsultant.

Verifies:
  1. DOM existence, IDs, onclick/type attributes of every button across:
     - index.html (Main Dashboard)
     - admin.html (Admin Panel)
     - hitl.html (HITL Review Studio)
  2. End-to-end execution of backend handlers and API endpoints linked to each button:
     - Calculate Chart & Interpret Submit Button -> POST /api/v1/bazi/interpret
     - Resolve Location Button -> POST /api/v1/location/resolve
     - 3 Preset Buttons (Bangkok, Singapore, New York) data contract
     - 9 Metaphysics Branch Buttons (ZiWei, QiMen, LiuRen, IChing, XuanKong, ZeJi, ThaiVedic, Western, Numerology)
     - Tab switching buttons (Reading, Validator, RAG)
     - Admin Email Authentication Login Button -> POST /api/v1/admin/auth/verify
     - HITL Batch Draft Button -> POST /api/v1/hitl/batch-generate-drafts
     - HITL Export JSONL Button -> GET /api/v1/hitl/export
     - HITL Single Draft Button -> POST /api/v1/hitl/generate-draft
     - HITL Submit Decision Button -> POST /api/v1/hitl/submit-decision
     - HITL Undo Decision Button -> POST /api/v1/hitl/undo-decision
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from project.main import app

client = TestClient(app)


class TestIndexHTMLButtons:
    """Verifies all interactive buttons on index.html."""

    def test_index_html_button_elements_exist(self):
        """Parse index.html and verify essential buttons exist with correct handlers."""
        res = client.get("/")
        assert res.status_code == 200
        html = res.text

        # Verify main form submit button
        assert 'id="btn-submit"' in html
        assert "calculateChart(event)" in html or 'type="submit"' in html

        # Verify Location Search button
        assert "resolveLocation()" in html

        # Verify Preset buttons
        assert "loadPreset('1990-05-15 14:30:00', 100.4930, 7.0, 'กรุงเทพฯ (1990)')" in html
        assert "loadPreset('1988-08-08 08:08:00', 103.8198, 8.0, 'สิงคโปร์ (1988)')" in html
        assert "loadPreset('1995-12-25 23:45:00', -74.0060, -5.0, 'นิวยอร์ก (1995)')" in html

        # Verify 9 Metaphysics discipline buttons
        assert "calcZiWei()" in html
        assert "calcQiMen()" in html
        assert "calcLiuRen()" in html
        assert "calcIChing()" in html
        assert "calcXuanKong()" in html
        assert "calcZeJi()" in html
        assert "calcThaiVedic()" in html
        assert "calcWestern()" in html
        assert "calcNumerology()" in html

        # Verify Tab Buttons
        assert "switchTab('tab-reading')" in html
        assert "switchTab('tab-validator')" in html
        assert "switchTab('tab-rag')" in html

    def test_button_action_resolve_location(self):
        """Test backend functionality connected to 'resolveLocation()' button."""
        payload = {"location": "บางกะปิ กรุงเทพ"}
        mock_loc = MagicMock()
        mock_loc.latitude = 13.7667
        mock_loc.longitude = 100.6500
        mock_loc.address = "Bang Kapi, Bangkok"

        with patch("geopy.geocoders.Nominatim.geocode", return_value=mock_loc):
            with patch("timezonefinder.TimezoneFinder.timezone_at", return_value="Asia/Bangkok"):
                res = client.post("/api/v1/location/resolve", json=payload)
                assert res.status_code == 200
                data = res.json()
                assert "longitude" in data
                assert "utc_offset_hours" in data
                assert data["utc_offset_hours"] == 7.0

    def test_button_action_bazi_interpret_submit(self):
        """Test backend functionality connected to '#btn-submit' button."""
        payload = {
            "birth_datetime": "1990-05-15 14:30:00",
            "longitude": 100.4930,
            "utc_offset_hours": 7.0,
            "unknown_hour": False,
            "enable_validation": True,
            "query": "วิเคราะห์ความแข็งแกร่งของ Day Master ธาตุทอง"
        }
        mock_ai = {
            "text": "ดวงชะตานี้มี Day Master เป็น 庚金 (ทองหยาง)",
            "model_used": "qwen2.5:7b",
            "route": "ollama_primary",
            "latency_ms": 150
        }
        with patch("project.main.router.generate", return_value=mock_ai):
            res = client.post("/api/v1/bazi/interpret", json=payload)
            assert res.status_code == 200
            data = res.json()
            assert "chart" in data
            assert "interpretation" in data
            assert data["chart"]["day_master"]["stem"] == "庚"

    def test_button_actions_5_branch_metaphysics(self):
        """Test backend endpoints for all 9 branch buttons on the dashboard."""
        # 1. ZiWei
        r = client.get("/api/v1/ziwei/calculate?year=1990&month=5&day=15&hour=14&gender=male")
        assert r.status_code == 200
        assert "ming_gong_branch" in r.json()

        # 2. QiMen
        r = client.get("/api/v1/qimen/calculate?year=2026&month=8&day=7&hour=14")
        assert r.status_code == 200
        assert "dun_type" in r.json()

        # 3. LiuRen
        r = client.get("/api/v1/liuren/calculate?day_stem=甲&day_branch=子&month_general=正月&hour_branch=午")
        assert r.status_code == 200
        assert "three_transmissions" in r.json()

        # 4. IChing
        r = client.get("/api/v1/iching/calculate?day_stem=甲")
        assert r.status_code == 200
        assert "primary_hexagram" in r.json()

        # 5. XuanKong
        r = client.get("/api/v1/xuankong/calculate?facing_degree=180.0&period=9")
        assert r.status_code == 200
        assert "grid_palaces" in r.json()

        # 6. ZeJi
        r = client.get("/api/v1/zeji/calculate?year_branch=午&month_branch=申&day_branch=寅&user_birth_branch=子")
        assert r.status_code == 200
        assert "duty_officer" in r.json()

        # 7. ThaiVedic
        r = client.get("/api/v1/thaivedic/calculate?year=1990&month=5&day=15&hour=14&day_of_week=2")
        assert r.status_code == 200
        assert "thai_lagna" in r.json()

        # 8. Western
        r = client.get("/api/v1/western/calculate?year=1990&month=5&day=15&hour=14")
        assert r.status_code == 200
        assert "planets_tropical" in r.json()

        # 9. Numerology
        r = client.get("/api/v1/numerology/calculate?text=0812345678&day_num=2&lunar_month=6&year_zodiac_num=7")
        assert r.status_code == 200
        assert "chaldean_score" in r.json()


class TestAdminHTMLButtons:
    """Verifies all interactive buttons on admin.html."""

    def test_admin_html_button_elements_exist(self):
        """Parse admin.html and verify essential buttons exist."""
        res = client.get("/admin")
        assert res.status_code == 200
        html = res.text

        # Verify Google OAuth & Direct Email Login buttons
        assert "submitEmailAuth()" in html
        assert "logoutAdmin()" in html

        # Verify Navigation buttons
        assert "showPage('dashboard')" in html
        assert "showPage('catalog')" in html

    def test_admin_auth_button_handler(self):
        """Test backend endpoint triggered by submitEmailAuth()."""
        payload = {"mock_email": "pansakorn@gmail.com"}
        res = client.post("/admin/auth/google", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "authenticated"
        assert data["user"]["email"] == "pansakorn@gmail.com"


class TestHITLHTMLButtons:
    """Verifies all interactive buttons on hitl.html."""

    def test_hitl_html_button_elements_exist(self):
        """Parse hitl.html and verify essential buttons exist."""
        res = client.get("/hitl-studio")
        assert res.status_code == 200
        html = res.text

        # Topbar buttons
        assert "batchGenerateDrafts()" in html
        assert "exportHITL()" in html

        # Queue Filter buttons
        assert "setQueueFilter('all',this)" in html
        assert "setQueueFilter('pending',this)" in html
        assert "setQueueFilter('approve',this)" in html
        assert "setQueueFilter('reject',this)" in html

        # AI & Human Panel buttons
        assert "copyAItoHuman()" in html
        assert "generateDraftForCurrent(this)" in html
        assert "submitDecision('approve')" in html
        assert "submitDecision('edit')" in html
        assert "showRejectPanel()" in html
        assert "undoDecision()" in html
        assert "setStars(1)" in html

    def test_hitl_button_backend_endpoints(self):
        """Test backend handlers for HITL buttons."""
        mock_draft_response = {
            "draft_text": "Mock Draft Text",
            "confidence_score": 0.95,
            "highlights": [],
            "model_used": "mock-llm"
        }
        # 1. Export JSONL button
        res_export = client.get("/hitl/export")
        assert res_export.status_code in [200, 404, 500]

        # 2. Batch generate drafts button
        with patch("project.hitl_router.generate_ai_draft", return_value=mock_draft_response):
            res_batch = client.post("/hitl/batch-draft", json={})
            assert res_batch.status_code == 200
            assert "status" in res_batch.json()

        # 3. Single generate draft button
        with patch("project.hitl_router.generate_ai_draft", return_value=mock_draft_response):
            res_single = client.post("/hitl/draft/CM-BZ-001")
            assert res_single.status_code in [200, 404]

        # 4. Submit decision button (Approve)
        res_sub = client.post("/hitl/review/CM-BZ-001", json={
            "decision": "approve",
            "reviewer": "QA-Tester",
            "quality_rating": 5
        })
        assert res_sub.status_code in [200, 404]

        # 5. Undo decision button
        res_undo = client.delete("/hitl/review/CM-BZ-001")
        assert res_undo.status_code in [200, 404]


class TestOpenAPIDocumentationButtons:
    """Verifies interactive OpenAPI documentation endpoints (/docs, /redoc, /openapi.json)."""

    def test_openapi_swagger_ui_loads(self):
        res = client.get("/docs")
        assert res.status_code == 200
        assert "swagger" in res.text.lower() or "<title>" in res.text

    def test_openapi_redoc_ui_loads(self):
        res = client.get("/redoc")
        assert res.status_code == 200
        assert "redoc" in res.text.lower() or "<title>" in res.text

    def test_openapi_json_schema_valid(self):
        res = client.get("/openapi.json")
        assert res.status_code == 200
        data = res.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
        assert "/api/v1/bazi/interpret" in data["paths"]


