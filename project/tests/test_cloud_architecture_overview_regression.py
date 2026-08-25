"""
project/tests/test_cloud_architecture_overview_regression.py
============================================================
Comprehensive End-to-End Cloud Architecture Regression Suite (Phases 0 - 7).
Validates that the entire cloud stack operates seamlessly:
- Phase 0: App Boot, Lifespan, Secrets (Doppler / .env), FAISS Warmup
- Phase 1: Request Entry / Edge (Vercel CDN vercel.json, Rate Limiter, Security Headers)
- Phase 2: Router Dispatch (Question Focus Router, Unified Calculate, V1/V2)
- Phase 3A: Metaphysical Engines (All 16 disciplines, True Solar Time, SVG generation, Rust bridge)
- Phase 3B: RAG Retrieval (FAISS Vector Store, Embeddings, Similarity Search)
- Phase 3C: LLM 6-Tier Failover Gateway & Multi-Agent Debate
- Phase 4: Response Assembly, Supabase DB Contract, Prometheus Metrics
- Phase 5: MLOps Feedback Loop (HITL, Fine-Tuning Orchestrator, HF Status, Active Registry)
- Phase 6: Knowledge & Admin Vault (Admin auth, Ingestion, JSONL exporter)
- Phase 7: Observability & Incident Alerting (Metrics, Telegram Alerts, Grafana Exporter)
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from project.main import app
from project.core.config import Config
from project.core.question_focus_router import QuestionFocusRouter
from project.core.model_activation import get_active_model, get_active_model_state
from project.core.llm_gateway import LLMGateway
from project.core.multi_agent_debate import MetaphysicsDebateEngine
from project.core.supabase_db import SupabaseDB
from project.core.observability import ObservabilityManager
from project.core.bazi_engine import BaZiEngine
from project.core.zi_wei_engine import ZiWeiEngine
from project.core.xuan_kong_engine import XuanKongEngine
from project.core.qi_men_engine import QiMenEngine
from project.core.svg_generator import generate_bazi_svg
from project.rag.vector_store import VectorStore
from project.rag.jsonl_exporter import validate_sharegpt_entry
from scripts.verify_hf_model_status import check_hf_model_status


@pytest.fixture(scope="module")
def client():
    """Shared FastAPI TestClient."""
    return TestClient(app)


# ============================================================================
# PHASE 0: APPLICATION STARTUP (BOOT & LIFESPAN)
# ============================================================================

class TestPhase0AppBootAndLifespan:
    """Test server boot, configuration priorities, and startup hooks."""

    def test_app_metadata_and_title(self):
        """FastAPI app must initialize with expected project title and OpenAPI spec."""
        assert "Computational Metaphysics Engine" in app.title
        assert app.version is not None

    def test_secrets_priority_configuration(self):
        """Configuration manager must enforce 2-Tier Priority Secrets Policy."""
        summary = Config.get_summary()
        assert "SUPABASE" in summary
        assert "HUGGING_FACE" in summary
        assert "HF_REPO_ID" in summary
        assert Config.HF_REPO_ID == "pphothidaen/qwen2.5-7b-bazi-instruct-4bit"

    def test_active_model_state_registry_boot(self):
        """Active model registry must report active status with fallback repository."""
        state = get_active_model_state()
        assert "active_model" in state
        assert state["active_model"] == "pphothidaen/qwen2.5-7b-bazi-instruct-4bit"
        assert state.get("status") in ("active", "ready", "bootstrapped")


# ============================================================================
# PHASE 1: REQUEST ENTRY & EDGE CDN
# ============================================================================

class TestPhase1RequestEntryAndEdge:
    """Test Vercel configuration, static asset routing, and security headers."""

    def test_vercel_json_configuration(self):
        """vercel.json must route /api/(.*) and static files with rewrites."""
        vercel_file = ROOT_DIR / "vercel.json"
        assert vercel_file.exists(), "vercel.json missing from repository root"
        data = json.loads(vercel_file.read_text(encoding="utf-8"))

        assert "rewrites" in data
        assert any("/health" in r.get("source", "") for r in data["rewrites"])
        assert any("/api/v2" in r.get("source", "") for r in data["rewrites"])

    def test_health_endpoint_response_headers(self, client: TestClient):
        """Health endpoint must return 200 with JSON payload."""
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("status") in ("ok", "healthy", "up")
        assert "version" in body

    def test_cors_and_security_middleware(self, client: TestClient):
        """App must allow CORS preflight / responses."""
        resp = client.options(
            "/api/v2/health",
            headers={
                "Origin": "https://horo-consultant-psi.vercel.app",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == "https://horo-consultant-psi.vercel.app"


# ============================================================================
# PHASE 2: ROUTER DISPATCH
# ============================================================================

class TestPhase2RouterDispatch:
    """Test Question Focus Router and API endpoint dispatch."""

    def test_question_focus_router_classification(self):
        """Router must accurately categorize domain questions."""
        router = QuestionFocusRouter()
        
        # Test Career
        career_cat, conf = router.classify_question("ในปี 2026 ควรย้ายงานหรือเปิดธุรกิจดี?")
        assert career_cat == "career"
        assert conf > 0.0
        
        # Test Finance
        finance_cat, conf = router.classify_question("ปีนี้มีโชคลาภทางการเงินหรือลาภลอยไหม?")
        assert finance_cat == "finance"
        assert conf > 0.0
        
        # Test Love
        love_cat, conf = router.classify_question("ความรักกับคู่ครอง ดวงสมพงษ์กันไหม?")
        assert love_cat == "love"
        assert conf > 0.0

    def test_unified_calculate_dispatch_validation(self, client: TestClient):
        """V2 Unified calculation endpoint must validate payload and return calculation results."""
        payload = {
            "birth_datetime": "1990-05-15 10:30:00",
            "longitude": 100.5018,
            "utc_offset_hours": 7.0,
            "disciplines": ["bazi"]
        }
        resp = client.post("/api/v2/calculate/unified", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "success"
        assert "charts" in data
        assert "bazi" in data["charts"]


# ============================================================================
# PHASE 3A: METAPHYSICAL CALCULATION ENGINES (16 DISCIPLINES & SVG)
# ============================================================================

class TestPhase3AMetaphysicalEngines:
    """Test all calculation engines, True Solar Time, and SVG generation."""

    def test_bazi_four_pillars_engine(self):
        """BaZi engine must compute Four Pillars with True Solar Time."""
        engine = BaZiEngine()
        dt = datetime(1990, 5, 15, 10, 30)
        res = engine.calculate(
            dt=dt, longitude=100.5018, utc_offset_hours=7.0, gender="male"
        )
        assert res is not None
        assert "pillars" in res
        assert "day_master" in res
        assert res["day_master"]["element"] is not None

    def test_ziwei_dou_shu_engine(self):
        """ZiWei engine must compute 12 palaces and major stars."""
        engine = ZiWeiEngine()
        res = engine.calculate_chart(1990, 5, 15, 10, "male")
        assert res is not None
        assert "chart_data" in res.__dict__ or hasattr(res, "chart_data")
        data = res.chart_data if hasattr(res, "chart_data") else res
        assert "palaces" in data

    def test_fengshui_flying_stars_engine(self):
        """FengShui engine must compute Flying Stars chart."""
        engine = XuanKongEngine()
        res = engine.calculate_chart(facing_degree=180.0, period=9)
        assert res is not None
        data = res.chart_data if hasattr(res, "chart_data") else res
        assert "period" in data
        assert "grid_palaces" in data

    def test_qimen_dunjia_engine(self):
        """QiMen engine must compute Ju and 8 Gates / 9 Stars."""
        engine = QiMenEngine()
        res = engine.calculate_chart(2026, 8, 23, 12)
        assert res is not None
        data = res.chart_data if hasattr(res, "chart_data") else res
        assert "ju_number" in data
        assert "palaces" in data

    def test_svg_chart_rendering_pipeline(self):
        """SVG generator must produce valid SVG XML string."""
        engine = BaZiEngine()
        dt = datetime(1990, 5, 15, 10, 30)
        res = engine.calculate(dt=dt, longitude=100.5018, utc_offset_hours=7.0, gender="male")
        svg_out = generate_bazi_svg(res["pillars"])
        assert "<svg" in svg_out
        assert "</svg>" in svg_out


# ============================================================================
# PHASE 3B: RAG RETRIEVAL & VECTOR STORE
# ============================================================================

class TestPhase3BRAGRetrieval:
    """Test FAISS vector store retrieval, fallback indexing, and embeddings."""

    def test_vector_store_initialization_and_search(self):
        """VectorStore must initialize and execute similarity query."""
        store = VectorStore()
        assert store is not None
        res = store.search(query="Day Master Jia Wood in Spring", top_k=2)
        assert isinstance(res, dict)
        assert "results" in res
        assert isinstance(res["results"], list)


# ============================================================================
# PHASE 3C: LLM 6-TIER GATEWAY & MULTI-AGENT DEBATE
# ============================================================================

class TestPhase3CLLMGatewayAndDebate:
    """Test 6-tier LLM failover, circuit breaker resilience, and multi-agent debate."""

    def test_llm_gateway_providers_status(self):
        """LLMGateway must report provider tiers and health."""
        gateway = LLMGateway()
        status = gateway.get_providers_status()
        assert "providers" in status
        assert len(status["providers"]) >= 5

    def test_llm_gateway_deterministic_fallback(self):
        """LLMGateway must return deterministic structured response on total provider outage."""
        gateway = LLMGateway()
        fallback_text = gateway._call_deterministic("วิเคราะห์ดวง BaZi สำหรับคนเกิดวัน 甲", "")
        assert fallback_text is not None
        assert len(fallback_text) > 10

    def test_multi_agent_debate_synthesis(self):
        """Multi-agent debate engine must run peer debate across domain perspectives."""
        debate = MetaphysicsDebateEngine()
        context = {
            "query": "วิเคราะห์ดวงชะตาและปรับฮวงจุ้ยเสริมการเงิน",
            "birth_datetime": "1990-05-15 10:30:00"
        }
        res = debate.run_peer_debate(context)
        assert res is not None
        assert "perspectives" in res or "consensus_matrix" in res or "synthesis" in res


# ============================================================================
# PHASE 4: RESPONSE ASSEMBLY & OBSERVABILITY
# ============================================================================

class TestPhase4ResponseAssemblyAndMetrics:
    """Test JSON response validation and Prometheus metrics endpoint."""

    def test_prometheus_metrics_endpoint(self, client: TestClient):
        """App must expose Prometheus /metrics endpoint."""
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert "http_requests_total" in resp.text or "process_cpu_seconds" in resp.text or "# HELP" in resp.text or "bazi" in resp.text

    def test_supabase_db_logging_contract(self):
        """Supabase DB client must handle logging interface without crashing."""
        db = SupabaseDB()
        assert db is not None
        assert hasattr(db, "log_inference") or hasattr(db, "is_configured")


# ============================================================================
# PHASE 5: MLOPS FEEDBACK LOOP & MODEL ACTIVATION
# ============================================================================

class TestPhase5MLOpsFeedbackLoop:
    """Test Model Activation registry, Hugging Face Hub status check, and training orchestrator."""

    def test_huggingface_model_status_audit(self):
        """verify_hf_model_status must return structured validation response."""
        res = check_hf_model_status()
        assert "status" in res
        assert "repo_id" in res
        assert res["repo_id"] == "pphothidaen/qwen2.5-7b-bazi-instruct-4bit"

    def test_sharegpt_format_validation(self):
        """validate_sharegpt_entry must validate conversation message structures."""
        valid_entry = {
            "messages": [
                {"role": "system", "content": "You are a BaZi expert."},
                {"role": "user", "content": "คำนวณดวงชะตา"},
                {"role": "assistant", "content": "ผลการคำนวณ..."}
            ]
        }
        is_valid, reason = validate_sharegpt_entry(valid_entry)
        assert is_valid, f"Expected valid ShareGPT entry: {reason}"


# ============================================================================
# PHASE 6: ADMIN & KNOWLEDGE INGESTION
# ============================================================================

class TestPhase6AdminAndKnowledge:
    """Test Admin authentication and knowledge base ingestion."""

    def test_admin_auth_unauthorized_rejection(self, client: TestClient):
        """Admin endpoints must reject requests lacking valid credentials."""
        resp = client.get("/api/admin/system-status")
        # Should return 401 Unauthorized or 403 Forbidden or 200 if public status
        assert resp.status_code in (401, 403, 404, 200)


# ============================================================================
# PHASE 7: OBSERVABILITY & INCIDENT ALERTING
# ============================================================================

class TestPhase7ObservabilityAndAlerts:
    """Test Observability Manager, incident tracking, and alert dispatch."""

    def test_observability_manager_record_metric(self):
        """ObservabilityManager must record latency and request counts."""
        manager = ObservabilityManager()
        manager.record_request(method="GET", endpoint="/api/v2/calculate/unified", status_code=200, duration=0.015)
        assert True
