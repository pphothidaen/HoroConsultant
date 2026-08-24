"""End-to-end synthetic consultation coverage for Horo v3.0."""

import pytest
from fastapi.testclient import TestClient

from project.main import app
from scripts.run_v3_e2e_consultation import (
    PROFILES,
    assert_consultation_contract,
    consultation_payload,
)


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.parametrize("profile", PROFILES, ids=[f"profile-{p['id']}" for p in PROFILES])
def test_synthetic_consultation_completes_all_v3_acceptance_criteria(client, profile):
    response = client.post("/api/v3/calculate", json=consultation_payload(profile))
    body = response.json()

    assert response.status_code == 200, body
    assert_consultation_contract(profile, body)
