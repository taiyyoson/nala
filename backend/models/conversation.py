"""
Conversation Model - Database model for conversations

Stores conversation metadata and relationships to messages.
"""

import uuid

from sqlalchemy import JSON, Column, Integer, String
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Conversation(Base, TimestampMixin):
    """
    Conversation database model.

    Attributes:
        id: Primary key (UUID string)
        user_id: ID of user who owns this conversation
        title: Conversation title (auto-generated or user-provided)
        message_count: Cached count of messages
        metadata: JSON field for additional data (model preferences, tags, etc.)
        messages: Relationship to Message model
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """

    __tablename__ = "conversations"

    id = Column(
        String(36), primary_key=True, default=lambda: f"conv_{uuid.uuid4().hex[:12]}"
    )
    user_id = Column(String(36), index=True, nullable=True)  # Firebase UID
    title = Column(String(255), nullable=True)
    message_count = Column(Integer, default=0)
    metadata = Column(JSON, default=dict)

    # Relationships
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, title={self.title}, messages={self.message_count})>"

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "conversation_id": self.id,
            "user_id": self.user_id,
            "title": self.title or "Untitled Conversation",
            "message_count": self.message_count,
            "metadata": self.metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def update_message_count(self, session):
        """Recalculate and update message count from database."""
        from .message import Message

        count = (
            session.query(Message).filter(Message.conversation_id == self.id).count()
        )
        self.message_count = count
        return count

    def generate_title_from_first_message(self, session):
        """Auto-generate title from first user message (max 50 chars)."""
        from .message import Message

        first_message = (
            session.query(Message)
            .filter(Message.conversation_id == self.id, Message.role == "user")
            .order_by(Message.created_at)
            .first()
        )

        if first_message:
            content = first_message.content[:50]
            self.title = content + "..." if len(first_message.content) > 50 else content
            return self.title
        return None
