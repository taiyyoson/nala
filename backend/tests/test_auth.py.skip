from unittest.mock import MagicMock, patch

import pytest
from app import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def mock_firebase_token():
    """Mock decoded Firebase token"""
    return {
        "uid": "test_user_123",
        "email": "test@example.com",
        "email_verified": True,
        "name": "Test User",
    }


@pytest.fixture
def valid_auth_header():
    """Valid authorization header with Bearer token"""
    return {"Authorization": "Bearer valid_token_123"}


# ========== PUBLIC ENDPOINT TESTS ==========


def test_auth_public_endpoint(client):
    """Test that public endpoints work without authentication"""
    response = client.get("/api/v1/auth/test-public")
    assert response.status_code == 200
    assert "message" in response.json()


# ========== PROTECTED ENDPOINT TESTS ==========


def test_auth_missing_token(client):
    """Test that protected endpoints fail without token"""
    response = client.get("/api/v1/auth/verify")
    assert response.status_code == 401
    assert "Missing auth token" in response.json()["detail"]


def test_auth_invalid_bearer_format(client):
    """Test that malformed Authorization header fails"""
    response = client.get(
        "/api/v1/auth/verify", headers={"Authorization": "InvalidFormat token123"}
    )
    assert response.status_code == 401


def test_auth_empty_token(client):
    """Test that empty Bearer token fails"""
    response = client.get("/api/v1/auth/verify", headers={"Authorization": "Bearer "})
    assert response.status_code == 401


# ========== VALID TOKEN TESTS (MOCKED) ==========


@patch("authentication.auth_service.auth.verify_id_token")
def test_auth_valid_token(mock_verify, client, mock_firebase_token, valid_auth_header):
    """Test that valid Firebase token is accepted"""
    # Mock Firebase's verify_id_token to return our mock token
    mock_verify.return_value = mock_firebase_token

    response = client.get("/api/v1/auth/verify", headers=valid_auth_header)

    assert response.status_code == 200
    assert response.json()["message"] == "Token valid"
    assert response.json()["user"]["uid"] == "test_user_123"
    assert response.json()["user"]["email"] == "test@example.com"


@patch("authentication.auth_service.auth.verify_id_token")
def test_auth_expired_token(mock_verify, client, valid_auth_header):
    """Test that expired token is rejected"""
    # Mock Firebase raising an exception for expired token
    mock_verify.side_effect = Exception("Token expired")

    response = client.get("/api/v1/auth/verify", headers=valid_auth_header)

    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]


@patch("authentication.auth_service.auth.verify_id_token")
def test_auth_invalid_signature(mock_verify, client, valid_auth_header):
    """Test that token with invalid signature is rejected"""
    mock_verify.side_effect = Exception("Invalid signature")

    response = client.get("/api/v1/auth/verify", headers=valid_auth_header)

    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]


# ========== PROTECTED ROUTE INTEGRATION ==========


@patch("authentication.auth_service.auth.verify_id_token")
def test_protected_route_with_valid_token(
    mock_verify, client, mock_firebase_token, valid_auth_header
):
    """Test accessing a protected route with valid authentication"""
    mock_verify.return_value = mock_firebase_token

    # Add this test route to your auth_routes.py first (see below)
    response = client.get("/api/v1/auth/test-protected", headers=valid_auth_header)

    assert response.status_code == 200
    assert "user_id" in response.json()


def test_protected_route_without_token(client):
    """Test that protected routes reject requests without tokens"""
    response = client.get("/api/v1/auth/test-protected")
    assert response.status_code == 401
