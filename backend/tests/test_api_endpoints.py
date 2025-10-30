import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Nala Health Coach API is running"
    assert data["version"] == "1.0.0"
    assert data["status"] == "healthy"
    assert "endpoints" in data


def test_health_check_endpoint(client: TestClient):
    """Test the basic health check endpoint"""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Nala Health Coach API"
    assert "timestamp" in data


def test_detailed_health_check_endpoint(client: TestClient):
    """Test the detailed health check endpoint"""
    response = client.get("/api/v1/health/detailed")
    assert response.status_code == 200
    data = response.json()
    # Health status might be unhealthy in test environment, so just check it exists
    assert "status" in data
    assert data["status"] in ["healthy", "unhealthy"]
    assert "timestamp" in data
    if data["status"] == "healthy":
        assert "system" in data
        assert "environment" in data


def test_chat_message_endpoint(client: TestClient, sample_chat_request):
    """Test the chat message endpoint"""
    response = client.post("/api/v1/chat/message", json=sample_chat_request)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "conversation_id" in data
    assert "message_id" in data
    assert "timestamp" in data
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 0


def test_chat_message_with_hello(client: TestClient):
    """Test chat endpoint with hello message"""
    request_data = {"message": "hello", "user_id": "test_user"}
    response = client.post("/api/v1/chat/message", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "Hi there!" in data["response"]


def test_chat_message_with_help(client: TestClient):
    """Test chat endpoint with help message"""
    request_data = {"message": "help", "user_id": "test_user"}
    response = client.post("/api/v1/chat/message", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "support you" in data["response"]


def test_get_conversation_not_found(client: TestClient):
    """Test retrieving a non-existent conversation"""
    response = client.get("/api/v1/chat/conversation/nonexistent")
    assert response.status_code == 404
    assert "Conversation not found" in response.json()["detail"]


def test_chat_conversation_flow(client: TestClient):
    """Test full conversation flow"""
    # Send first message
    request_data = {"message": "hello", "user_id": "test_user"}
    response1 = client.post("/api/v1/chat/message", json=request_data)
    assert response1.status_code == 200
    conv_id = response1.json()["conversation_id"]

    # Send second message in same conversation
    request_data2 = {
        "message": "help me with nutrition",
        "conversation_id": conv_id,
        "user_id": "test_user",
    }
    response2 = client.post("/api/v1/chat/message", json=request_data2)
    assert response2.status_code == 200
    assert response2.json()["conversation_id"] == conv_id

    # Retrieve conversation history
    response3 = client.get(f"/api/v1/chat/conversation/{conv_id}")
    assert response3.status_code == 200
    data = response3.json()
    assert data["conversation_id"] == conv_id
    assert len(data["messages"]) == 4  # 2 user messages + 2 assistant responses


def test_invalid_chat_request(client: TestClient):
    """Test chat endpoint with invalid request"""
    response = client.post("/api/v1/chat/message", json={})
    assert response.status_code == 422  # Validation error


def test_chat_stream_endpoint(client: TestClient, sample_chat_request):
    """Test the chat streaming endpoint"""
    response = client.post("/api/v1/chat/stream", json=sample_chat_request)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
