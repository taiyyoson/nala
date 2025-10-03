import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_chat_request():
    """Sample chat request for testing"""
    return {"message": "Hello, I need help with my health", "user_id": "test_user_123"}
