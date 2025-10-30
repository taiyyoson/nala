from unittest.mock import AsyncMock, patch

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


@pytest.fixture(autouse=True)
def mock_ai_service():
    """Mock AI service to avoid requiring AI backend for tests"""
    with patch("routes.chat.get_or_create_ai_service") as mock:
        # Create a mock AI service instance
        mock_instance = AsyncMock()
        mock_instance.generate_response = AsyncMock(
            return_value=(
                "Hi there! I'm here to support you on your health journey.",
                [],
                "gpt-4",
            )
        )
        mock_instance.stream_response = AsyncMock()
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_chat_request():
    """Sample chat request for testing"""
    return {"message": "Hello, I need help with my health", "user_id": "test_user_123"}
