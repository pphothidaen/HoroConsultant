"""Contract tests for the Horo Architecture v3.0 HTTP router."""

from fastapi.testclient import TestClient

from project.main import app


client = TestClient(app)

CALCULATE_PAYLOAD = {
    "birth_datetime": "1990-05-15T14:30:00",
    "latitude": 13.7563,
    "longitude": 100.493,
    "tz_offset": 7.0,
    "language": "th",
}


def test_v3_health() -> None:
    response = client.get("/api/v3/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "HEALTHY",
        "version": "3.0.0",
        "active_domains": ["BaZi", "ZiWei", "QiMen", "ZeJi", "XuanKong", "DaLiuRen", "LiuYao", "TaiYi", "QiZheng", "MianXiang"],
    }


def test_v3_schema() -> None:
    response = client.get("/api/v3/schema")
    body = response.json()
    assert response.status_code == 200
    assert body["title"] == "HoroClaimEmission"
    assert "node_id" in body["properties"]
    assert "claims" in body["properties"]


def test_v3_calculate_contains_epistemic_disclaimer() -> None:
    response = client.post("/api/v3/calculate", json=CALCULATE_PAYLOAD)
    body = response.json()
    assert response.status_code == 200, body
    assert body["status"] == "COMPLETED"
    assert body["has_epistemic_disclaimer"] is True
    assert "Predictive Validity is Explicitly Disclaimed" in body["report_markdown"]
    assert body["audit_metrics"]["lciw"] >= 0
    assert len(body["emissions"]) == 10
    assert len(body["charts"]) == 10
    assert {emission["tradition_domain"] for emission in body["emissions"]} == {
        "ming_xue_bazi", "ming_xue_ziwei", "san_shi_qi_men", "ze_ji_xue",
        "xiang_xue_feng_shui", "san_shi_da_liu_ren", "bu_shi_liu_yao",
        "san_shi_tai_yi", "ming_xue_qi_zheng", "xiang_xue_mian_xiang",
    }


def test_v3_audit_returns_verdict_and_metrics() -> None:
    calculate = client.post("/api/v3/calculate", json=CALCULATE_PAYLOAD)
    emissions = calculate.json()["emissions"]
    response = client.post("/api/v3/audit", json={"emissions": emissions})
    body = response.json()
    assert response.status_code == 200
    assert body["verdict"].startswith("AUDIT_")
    assert "lciw" in body["metrics"]
    assert "rniw" in body["metrics"]
