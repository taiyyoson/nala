"""
Message Model - Database model for chat messages

Stores individual messages within conversations.
"""

from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
import uuid


class Message(Base, TimestampMixin):
    """
    Message database model.

    Attributes:
        id: Primary key (UUID string)
        conversation_id: Foreign key to Conversation
        role: Message role (user, assistant, system)
        content: Message text content
        metadata: JSON field for additional data (model used, sources, etc.)
        conversation: Relationship to Conversation model
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """

    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    metadata = Column(JSON, default=dict)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, conv={self.conversation_id})>"

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "message_id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata or {},
            "timestamp": self.created_at.isoformat() if self.created_at else None,
        }

    def to_api_format(self):
        """Format for API response (simpler version)."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
        }

    def extract_sources(self):
        """Get sources from metadata if available."""
        if self.metadata and "sources" in self.metadata:
            return self.metadata["sources"]
        return []
