"""
project/tests/test_admin_auth.py
=================================
Unit tests for Admin Panel Google Account Authentication & Authorization.
"""

import base64
import json
import os
import time
from unittest.mock import AsyncMock, patch

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from fastapi.testclient import TestClient

from project.main import app

client = TestClient(app)


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _signed_google_credential(email: str, client_id: str) -> tuple[str, dict[str, dict[str, str]]]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_numbers = private_key.public_key().public_numbers()
    key_id = "local-test-key"
    header = {"alg": "RS256", "kid": key_id, "typ": "JWT"}
    now = int(time.time())
    payload = {
        "iss": "https://accounts.google.com",
        "aud": client_id,
        "exp": now + 300,
        "iat": now,
        "email_verified": True,
        "email": email,
        "name": "Local QA Identity",
    }
    header_part = _base64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_part = _base64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_part}.{payload_part}".encode("ascii")
    signature = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    credential = f"{header_part}.{payload_part}.{_base64url(signature)}"

    def _unsigned_bytes(value: int) -> bytes:
        return value.to_bytes((value.bit_length() + 7) // 8, "big")

    jwks = {
        key_id: {
            "kty": "RSA",
            "alg": "RS256",
            "kid": key_id,
            "n": _base64url(_unsigned_bytes(public_numbers.n)),
            "e": _base64url(_unsigned_bytes(public_numbers.e)),
        }
    }
    return credential, jwks


def test_auth_config_endpoint():
    with patch.dict(
        os.environ,
        {"GOOGLE_CLIENT_ID": "local-client-id", "ADMIN_AUTH_REQUIRED": "true"},
        clear=True,
    ):
        response = client.get("/admin/auth/config")

    assert response.status_code == 200
    data = response.json()
    assert data == {"google_client_id": "local-client-id", "auth_required": True}
    assert "allowed_emails" not in data


def test_authorized_email_login_pansakorn():
    mock_response = client.post(
        "/admin/auth/google",
        json={"mock_email": "pansakorn@gmail.com"},
    )
    assert mock_response.status_code == 422

    client_id = "local-client-id"
    credential, jwks = _signed_google_credential("pansakorn@gmail.com", client_id)
    with (
        patch.dict(
            os.environ,
            {
                "GOOGLE_CLIENT_ID": client_id,
                "ADMIN_ALLOWED_EMAILS": "pansakorn@gmail.com",
            },
            clear=True,
        ),
        patch("project.admin_router._google_jwks", new=AsyncMock(return_value=jwks)),
    ):
        response = client.post("/admin/auth/google", json={"credential": credential})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "authenticated"
    assert data["user"]["email"] == "pansakorn@gmail.com"
    assert data["user"]["role"] == "admin"
    assert data["user"]["auth_provider"] == "google"


def test_authorized_email_login_kimlenglim_work():
    client_id = "local-client-id"
    credential, jwks = _signed_google_credential("kimlenglim.work@gmail.com", client_id)
    with (
        patch.dict(
            os.environ,
            {
                "GOOGLE_CLIENT_ID": client_id,
                "ADMIN_ALLOWED_EMAILS": "kimlenglim.work@gmail.com",
            },
            clear=True,
        ),
        patch("project.admin_router._google_jwks", new=AsyncMock(return_value=jwks)),
    ):
        response = client.post("/admin/auth/google", json={"credential": credential})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "authenticated"
    assert data["user"]["email"] == "kimlenglim.work@gmail.com"
    assert data["user"]["role"] == "admin"
    assert data["user"]["auth_provider"] == "google"


def test_unauthorized_email_rejected():
    client_id = "local-client-id"
    allowed_email = "pansakorn@gmail.com"
    rejected_email = "hacker@evil.com"
    credential, jwks = _signed_google_credential(rejected_email, client_id)
    with (
        patch.dict(
            os.environ,
            {"GOOGLE_CLIENT_ID": client_id, "ADMIN_ALLOWED_EMAILS": allowed_email},
            clear=True,
        ),
        patch("project.admin_router._google_jwks", new=AsyncMock(return_value=jwks)),
    ):
        malformed = client.post(
            "/admin/auth/google",
            json={"credential": "not-a-valid-google-jwt-token"},
        )
        response = client.post("/admin/auth/google", json={"credential": credential})

    assert malformed.status_code == 401
    assert malformed.json() == {"detail": "Authentication required."}
    assert response.status_code == 403
    data = response.json()
    assert data == {"detail": "Access denied."}
    response_text = response.text.lower()
    assert rejected_email not in response_text
    assert allowed_email not in response_text
