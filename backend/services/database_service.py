"""
Database Service - Data Persistence Layer

This service handles all database operations for conversations and messages.
Abstracts database implementation details from other services.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from backend.models import Conversation, Message
import uuid


class DatabaseService:
    """
    Service for database operations.

    Responsibilities:
    - CRUD operations for conversations
    - CRUD operations for messages
    - Query optimization
    - Transaction management
    """

    def __init__(self, session: Session):
        """
        Initialize Database Service

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    # =========================================================================
    # Conversation Operations
    # =========================================================================

    def create_conversation(self, conversation_data: Dict[str, Any]) -> Conversation:
        """
        Create a new conversation record.

        Args:
            conversation_data: Dict with conversation fields
                {
                    "user_id": "user_123",
                    "title": "Health coaching session",
                    "metadata": {"week": 1}
                }

        Returns:
            Created Conversation object
        """
        conversation = Conversation(
            id=conversation_data.get("id") or f"conv_{uuid.uuid4().hex[:12]}",
            user_id=conversation_data.get("user_id"),
            title=conversation_data.get("title"),
            message_count=0,
            metadata=conversation_data.get("metadata", {})
        )

        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)

        return conversation

    def get_conversation_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """
        Retrieve conversation by ID.

        Args:
            conversation_id: ID to look up

        Returns:
            Conversation object or None
        """
        return self.session.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

    def list_user_conversations(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Conversation]:
        """
        List all conversations for a user.

        Args:
            user_id: User ID to filter by
            limit: Max results
            offset: Pagination offset

        Returns:
            List of Conversation objects ordered by updated_at DESC
        """
        return (
            self.session.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def update_conversation(
        self,
        conversation_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Conversation]:
        """
        Update conversation fields.

        Args:
            conversation_id: ID of conversation to update
            updates: Dict of fields to update
                {"title": "New title", "metadata": {...}}

        Returns:
            Updated Conversation object or None
        """
        conversation = self.get_conversation_by_id(conversation_id)

        if not conversation:
            return None

        # Update allowed fields
        for key, value in updates.items():
            if key in ["title", "metadata", "message_count"]:
                setattr(conversation, key, value)

        # Update timestamp
        conversation.updated_at = datetime.utcnow()

        self.session.commit()
        self.session.refresh(conversation)

        return conversation

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation and all its messages (cascade).

        Args:
            conversation_id: ID to delete

        Returns:
            True if successful, False if not found
        """
        conversation = self.get_conversation_by_id(conversation_id)

        if not conversation:
            return False

        self.session.delete(conversation)
        self.session.commit()

        return True

    def increment_message_count(self, conversation_id: str) -> bool:
        """
        Increment message count for a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            True if successful
        """
        conversation = self.get_conversation_by_id(conversation_id)

        if not conversation:
            return False

        conversation.message_count += 1
        conversation.updated_at = datetime.utcnow()

        self.session.commit()

        return True

    # =========================================================================
    # Message Operations
    # =========================================================================

    def create_message(self, message_data: Dict[str, Any]) -> Message:
        """
        Create a new message record.

        Args:
            message_data: Dict with message fields
                {
                    "conversation_id": "conv_123",
                    "role": "user",
                    "content": "I'm feeling stressed",
                    "metadata": {"mood": 7}
                }

        Returns:
            Created Message object
        """
        message = Message(
            id=message_data.get("id") or f"msg_{uuid.uuid4().hex[:12]}",
            conversation_id=message_data["conversation_id"],
            role=message_data["role"],
            content=message_data["content"],
            metadata=message_data.get("metadata", {})
        )

        self.session.add(message)

        # Increment conversation message count and update timestamp
        self.increment_message_count(message_data["conversation_id"])

        self.session.commit()
        self.session.refresh(message)

        return message

    def get_messages_by_conversation(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Message]:
        """
        Get all messages for a conversation.

        Args:
            conversation_id: Conversation ID
            limit: Optional limit on results
            offset: Pagination offset

        Returns:
            List of Message objects ordered by created_at ASC
        """
        query = (
            self.session.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )

        if limit:
            query = query.limit(limit).offset(offset)

        return query.all()

    def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """
        Retrieve a single message.

        Args:
            message_id: Message ID

        Returns:
            Message object or None
        """
        return self.session.query(Message).filter(
            Message.id == message_id
        ).first()

    def update_message(
        self,
        message_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Message]:
        """
        Update message fields.

        Args:
            message_id: ID of message to update
            updates: Dict of fields to update
                {"content": "Updated text", "metadata": {...}}

        Returns:
            Updated Message object or None
        """
        message = self.get_message_by_id(message_id)

        if not message:
            return None

        # Update allowed fields
        for key, value in updates.items():
            if key in ["content", "metadata"]:
                setattr(message, key, value)

        # Update timestamp
        message.updated_at = datetime.utcnow()

        self.session.commit()
        self.session.refresh(message)

        return message

    def delete_message(self, message_id: str) -> bool:
        """
        Delete a message.

        Args:
            message_id: ID to delete

        Returns:
            True if successful, False if not found
        """
        message = self.get_message_by_id(message_id)

        if not message:
            return False

        # Decrement conversation message count
        conversation = self.get_conversation_by_id(message.conversation_id)
        if conversation:
            conversation.message_count = max(0, conversation.message_count - 1)

        self.session.delete(message)
        self.session.commit()

        return True

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_conversation_message_count(self, conversation_id: str) -> int:
        """
        Get total message count for a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Number of messages
        """
        return self.session.query(Message).filter(
            Message.conversation_id == conversation_id
        ).count()

    def get_recent_messages(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> List[Message]:
        """
        Get most recent messages for a conversation.

        Args:
            conversation_id: Conversation ID
            limit: Number of recent messages to retrieve

        Returns:
            List of recent Message objects
        """
        return (
            self.session.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )[::-1]  # Reverse to chronological order

    def health_check(self) -> bool:
        """
        Check if database connection is healthy.

        Returns:
            True if connection is working
        """
        try:
            self.session.execute("SELECT 1")
            return True
        except Exception:
            return False
