"""
Message Model - Database model for chat messages

Stores individual messages within conversations.
"""

from sqlalchemy import Column, String, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
import enum


class MessageRole(enum.Enum):
    """Enum for message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


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

    # TODO: Define schema
    # id = Column(String(36), primary_key=True)
    # conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False, index=True)
    # role = Column(Enum(MessageRole), nullable=False)
    # content = Column(Text, nullable=False)
    # metadata = Column(JSON, default=dict)

    # Relationships
    # conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"

    # TODO: Add helper methods
    # - to_dict() - Convert to dictionary
    # - to_api_format() - Format for API response
    # - extract_sources() - Get sources from metadata
