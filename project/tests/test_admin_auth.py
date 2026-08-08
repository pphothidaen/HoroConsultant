"""
project/tests/test_admin_auth.py
=================================
Unit tests for Admin Panel Google Account Authentication & Authorization.
"""

from fastapi.testclient import TestClient
from project.main import app

client = TestClient(app)


def test_auth_config_endpoint():
    response = client.get("/admin/auth/config")
    assert response.status_code == 200
    data = response.json()
    assert "allowed_emails" in data
    assert "pansakorn@gmail.com" in data["allowed_emails"]


def test_authorized_email_login_pansakorn():
    response = client.post("/admin/auth/google", json={"mock_email": "pansakorn@gmail.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "authenticated"
    assert data["user"]["email"] == "pansakorn@gmail.com"
    assert data["user"]["role"] == "admin"


def test_authorized_email_login_kimlenglim_work():
    response = client.post("/admin/auth/google", json={"mock_email": "kimlenglim.work@gmail.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "authenticated"
    assert data["user"]["email"] == "kimlenglim.work@gmail.com"
    assert data["user"]["role"] == "admin"


def test_unauthorized_email_rejected():
    response = client.post("/admin/auth/google", json={"mock_email": "hacker@evil.com"})
    assert response.status_code == 403
    data = response.json()
    assert "Access Denied" in data["detail"]
    assert "hacker@evil.com" in data["detail"]
