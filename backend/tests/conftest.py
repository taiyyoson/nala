from unittest.mock import AsyncMock, patch

import pytest
from app import app
from config.database import init_database
from config.settings import settings
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Initialize database before running tests"""
    # Use SQLite for testing if no database URL is configured
    database_url = settings.conversation_database_url or "sqlite:///./test_nala.db"
    init_database(database_url)
    yield


@pytest.fixture(autouse=True)
def mock_ai_service():
    """Mock AI service to avoid requiring AI backend for tests"""
    from unittest.mock import MagicMock

    with patch("routes.chat.get_or_create_ai_service") as mock:
        # Create a mock AI service instance with all necessary attributes
        mock_instance = AsyncMock()

        # Mock the chatbot and session manager - use MagicMock for non-async parts
        mock_session_state = MagicMock()
        mock_session_state.value = "active"
        mock_instance.chatbot = MagicMock()
        mock_instance.chatbot.session_manager = MagicMock()
        mock_instance.chatbot.session_manager.get_state = MagicMock(
            return_value=mock_session_state
        )

        # Mock response generation
        mock_instance.generate_response = AsyncMock(
            return_value=(
                "Hi there! I'm here to support you on your health journey.",
                [],
                "gpt-4",
            )
        )
        mock_instance.stream_response = AsyncMock()
        mock_instance.session_number = 1

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
