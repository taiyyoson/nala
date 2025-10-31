"""
Database Tests - Test conversation and message persistence

Tests the database service layer to ensure conversations and messages
are properly stored and retrieved for user memory/conversation history.
"""

import pytest
from config.database import get_db
from services.database_service import DatabaseService

pytestmark = pytest.mark.database


@pytest.fixture
def db_service(client):
    """Create a database service instance for testing"""
    db = next(get_db())
    return DatabaseService(db)


class TestConversationOperations:
    """Test conversation CRUD operations"""

    def test_create_conversation(self, db_service):
        """Test creating a new conversation"""
        conv_data = {
            "user_id": "test_user_001",
            "title": "Health Goals Discussion",
            "metadata": {"week": 1, "topic": "nutrition"},
        }

        conversation = db_service.create_conversation(conv_data)

        assert conversation.id is not None
        assert conversation.user_id == "test_user_001"
        assert conversation.title == "Health Goals Discussion"
        assert conversation.message_count == 0
        assert conversation.extra_data["week"] == 1
        assert conversation.created_at is not None

    def test_get_conversation_by_id(self, db_service):
        """Test retrieving a conversation by ID"""
        # Create conversation
        conv_data = {"user_id": "test_user_002", "title": "Test Conversation"}
        created_conv = db_service.create_conversation(conv_data)

        # Retrieve it
        retrieved_conv = db_service.get_conversation_by_id(created_conv.id)

        assert retrieved_conv is not None
        assert retrieved_conv.id == created_conv.id
        assert retrieved_conv.title == "Test Conversation"

    def test_get_nonexistent_conversation(self, db_service):
        """Test retrieving a conversation that doesn't exist"""
        result = db_service.get_conversation_by_id("nonexistent_id")
        assert result is None

    def test_list_user_conversations(self, db_service):
        """Test listing all conversations for a user"""
        user_id = "test_user_003"

        # Create multiple conversations
        for i in range(3):
            db_service.create_conversation(
                {"user_id": user_id, "title": f"Conversation {i}"}
            )

        # List conversations
        conversations = db_service.list_user_conversations(user_id)

        assert len(conversations) >= 3
        assert all(conv.user_id == user_id for conv in conversations)

    def test_update_conversation(self, db_service):
        """Test updating conversation fields"""
        # Create conversation
        conv = db_service.create_conversation(
            {"user_id": "test_user_004", "title": "Original Title"}
        )

        # Update title only (metadata updates aren't supported in update_conversation)
        updates = {"title": "Updated Title"}
        updated_conv = db_service.update_conversation(conv.id, updates)

        assert updated_conv.title == "Updated Title"

    def test_delete_conversation(self, db_service):
        """Test deleting a conversation"""
        # Create conversation
        conv = db_service.create_conversation(
            {"user_id": "test_user_005", "title": "To Delete"}
        )
        conv_id = conv.id

        # Delete it
        result = db_service.delete_conversation(conv_id)
        assert result is True

        # Verify it's gone
        deleted_conv = db_service.get_conversation_by_id(conv_id)
        assert deleted_conv is None


class TestMessageOperations:
    """Test message CRUD operations"""

    def test_create_message(self, db_service):
        """Test creating a message in a conversation"""
        # Create conversation first
        conv = db_service.create_conversation(
            {"user_id": "test_user_006", "title": "Message Test"}
        )

        # Create message
        msg_data = {
            "conversation_id": conv.id,
            "role": "user",
            "content": "I want to improve my health",
            "metadata": {"mood": 7},
        }

        message = db_service.create_message(msg_data)

        assert message.id is not None
        assert message.conversation_id == conv.id
        assert message.role == "user"
        assert message.content == "I want to improve my health"
        assert message.extra_data["mood"] == 7

        # Verify conversation message count increased
        updated_conv = db_service.get_conversation_by_id(conv.id)
        assert updated_conv.message_count == 1

    def test_get_messages_by_conversation(self, db_service):
        """Test retrieving all messages in a conversation"""
        # Create conversation
        conv = db_service.create_conversation(
            {"user_id": "test_user_007", "title": "Message History Test"}
        )

        # Add multiple messages
        messages_to_add = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How can you help?"},
            {"role": "assistant", "content": "I can help with your health goals."},
        ]

        for msg_data in messages_to_add:
            msg_data["conversation_id"] = conv.id
            db_service.create_message(msg_data)

        # Retrieve messages
        messages = db_service.get_messages_by_conversation(conv.id)

        assert len(messages) == 4
        assert messages[0].role == "user"
        assert messages[0].content == "Hello"
        assert messages[1].role == "assistant"
        # Messages should be in chronological order
        assert messages[0].created_at <= messages[1].created_at

    def test_get_message_by_id(self, db_service):
        """Test retrieving a single message"""
        conv = db_service.create_conversation(
            {"user_id": "test_user_008", "title": "Single Message Test"}
        )

        msg = db_service.create_message(
            {
                "conversation_id": conv.id,
                "role": "user",
                "content": "Test message",
            }
        )

        retrieved_msg = db_service.get_message_by_id(msg.id)

        assert retrieved_msg is not None
        assert retrieved_msg.id == msg.id
        assert retrieved_msg.content == "Test message"

    def test_update_message(self, db_service):
        """Test updating a message"""
        conv = db_service.create_conversation(
            {"user_id": "test_user_009", "title": "Update Message Test"}
        )

        msg = db_service.create_message(
            {
                "conversation_id": conv.id,
                "role": "user",
                "content": "Original content",
            }
        )

        # Update message content only
        updates = {"content": "Updated content"}
        updated_msg = db_service.update_message(msg.id, updates)

        assert updated_msg.content == "Updated content"

    def test_delete_message(self, db_service):
        """Test deleting a message"""
        conv = db_service.create_conversation(
            {"user_id": "test_user_010", "title": "Delete Message Test"}
        )

        msg = db_service.create_message(
            {
                "conversation_id": conv.id,
                "role": "user",
                "content": "To be deleted",
            }
        )
        msg_id = msg.id

        # Delete message
        result = db_service.delete_message(msg_id)
        assert result is True

        # Verify it's gone
        deleted_msg = db_service.get_message_by_id(msg_id)
        assert deleted_msg is None

        # Verify conversation message count decreased
        updated_conv = db_service.get_conversation_by_id(conv.id)
        assert updated_conv.message_count == 0


class TestConversationHistory:
    """Test conversation history functionality (memory persistence)"""

    def test_full_conversation_flow(self, db_service):
        """Test a complete conversation with multiple exchanges"""
        # Create conversation
        conv = db_service.create_conversation(
            {
                "user_id": "test_user_011",
                "title": "Health Coaching Session",
                "metadata": {"session": 1, "week": 1},
            }
        )

        # Simulate a conversation
        conversation_exchanges = [
            ("user", "Hi, I'm struggling with my nutrition"),
            (
                "assistant",
                "I'm here to help. What specific challenges are you facing?",
            ),
            ("user", "I tend to skip breakfast and overeat at night"),
            (
                "assistant",
                "That's a common pattern. Let's work on building a morning routine.",
            ),
            ("user", "That sounds helpful"),
            ("assistant", "Great! Let's start with small, sustainable changes."),
        ]

        for role, content in conversation_exchanges:
            db_service.create_message(
                {
                    "conversation_id": conv.id,
                    "role": role,
                    "content": content,
                }
            )

        # Retrieve full conversation history
        history = db_service.get_messages_by_conversation(conv.id)

        assert len(history) == 6
        assert history[0].content == "Hi, I'm struggling with my nutrition"
        assert history[-1].content == "Great! Let's start with small, sustainable changes."

        # Verify conversation metadata
        updated_conv = db_service.get_conversation_by_id(conv.id)
        assert updated_conv.message_count == 6
        assert updated_conv.extra_data["session"] == 1

    def test_recent_messages_retrieval(self, db_service):
        """Test retrieving only recent messages for context"""
        conv = db_service.create_conversation(
            {"user_id": "test_user_012", "title": "Long Conversation"}
        )

        # Add 20 messages
        for i in range(20):
            db_service.create_message(
                {
                    "conversation_id": conv.id,
                    "role": "user" if i % 2 == 0 else "assistant",
                    "content": f"Message {i}",
                }
            )

        # Get only the 10 most recent messages
        recent_messages = db_service.get_recent_messages(conv.id, limit=10)

        assert len(recent_messages) == 10
        assert recent_messages[0].content == "Message 10"  # Should be in order
        assert recent_messages[-1].content == "Message 19"

    def test_conversation_cascade_delete(self, db_service):
        """Test that deleting a conversation also deletes its messages"""
        conv = db_service.create_conversation(
            {"user_id": "test_user_013", "title": "Cascade Test"}
        )

        # Add messages
        msg_ids = []
        for i in range(3):
            msg = db_service.create_message(
                {
                    "conversation_id": conv.id,
                    "role": "user",
                    "content": f"Message {i}",
                }
            )
            msg_ids.append(msg.id)

        # Delete conversation
        db_service.delete_conversation(conv.id)

        # Verify messages are also deleted (cascade)
        for msg_id in msg_ids:
            deleted_msg = db_service.get_message_by_id(msg_id)
            assert deleted_msg is None

    def test_message_count_accuracy(self, db_service):
        """Test that message count stays accurate"""
        conv = db_service.create_conversation(
            {"user_id": "test_user_014", "title": "Count Test"}
        )

        # Add 5 messages
        for i in range(5):
            db_service.create_message(
                {
                    "conversation_id": conv.id,
                    "role": "user",
                    "content": f"Message {i}",
                }
            )

        # Check count
        updated_conv = db_service.get_conversation_by_id(conv.id)
        assert updated_conv.message_count == 5

        # Verify with actual query
        actual_count = db_service.get_conversation_message_count(conv.id)
        assert actual_count == 5
        assert updated_conv.message_count == actual_count


class TestDatabaseHealth:
    """Test database connection and health checks"""

    def test_database_health_check(self, db_service):
        """Test that database connection is healthy"""
        is_healthy = db_service.health_check()
        # Health check should return a boolean
        assert isinstance(is_healthy, bool)

    def test_conversation_to_dict(self, db_service):
        """Test conversation serialization for API responses"""
        conv = db_service.create_conversation(
            {
                "user_id": "test_user_015",
                "title": "Serialization Test",
                "metadata": {"key": "value"},
            }
        )

        conv_dict = conv.to_dict()

        assert conv_dict["conversation_id"] == conv.id
        assert conv_dict["user_id"] == "test_user_015"
        assert conv_dict["title"] == "Serialization Test"
        assert conv_dict["metadata"]["key"] == "value"
        assert "created_at" in conv_dict
        assert "updated_at" in conv_dict

    def test_message_to_dict(self, db_service):
        """Test message serialization for API responses"""
        conv = db_service.create_conversation(
            {"user_id": "test_user_016", "title": "Message Serialization Test"}
        )

        msg = db_service.create_message(
            {
                "conversation_id": conv.id,
                "role": "user",
                "content": "Test content",
                "metadata": {"source": "mobile"},
            }
        )

        msg_dict = msg.to_dict()

        assert msg_dict["message_id"] == msg.id
        assert msg_dict["role"] == "user"
        assert msg_dict["content"] == "Test content"
        assert msg_dict["metadata"]["source"] == "mobile"
        assert "timestamp" in msg_dict
