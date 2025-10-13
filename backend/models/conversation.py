"""
Conversation Model - Database model for conversations

Stores conversation metadata and relationships to messages.
"""

from sqlalchemy import Column, String, Integer, Text
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

    # TODO: Define schema
    # id = Column(String(36), primary_key=True)
    # user_id = Column(String(36), index=True, nullable=True)
    # title = Column(String(255))
    # message_count = Column(Integer, default=0)
    # metadata = Column(JSON, default=dict)

    # Relationships
    # messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Conversation(id={self.id}, title={self.title})>"

    # TODO: Add helper methods
    # - to_dict() - Convert to dictionary
    # - update_message_count() - Recalculate message count
    # - generate_title_from_first_message() - Auto-generate title
