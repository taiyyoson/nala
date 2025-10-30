import pytest
from app import app
from config.database import init_database
from config.settings import settings
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Initialize database before running tests"""
    init_database(settings.database_url)
    yield


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_chat_request():
    """Sample chat request for testing"""
    return {"message": "Hello, I need help with my health", "user_id": "test_user_123"}
