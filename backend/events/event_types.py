"""
Event Types - Defines all event types in the system

This module defines the event type constants used throughout the pub/sub system.
Focused on database streaming operations for conversation memory.
"""

from enum import Enum


class EventType(str, Enum):
    """
    Event types for the pub/sub system.

    These events are focused on database operations to enable
    async persistence of conversations and messages.
    """

    # Conversation Events
    CONVERSATION_CREATED = "conversation.created"
    CONVERSATION_UPDATED = "conversation.updated"
    CONVERSATION_DELETED = "conversation.deleted"

    # Message Events
    MESSAGE_RECEIVED = "message.received"  # User sends message
    RESPONSE_GENERATED = "response.generated"  # AI generates response
    MESSAGE_SAVED = "message.saved"  # Message persisted to DB (confirmation)

    # Error Events
    SAVE_FAILED = "save.failed"  # Database save operation failed

    def __str__(self) -> str:
        """Return string representation of event type."""
        return self.value
