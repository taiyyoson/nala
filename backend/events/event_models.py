"""
Event Models - Pydantic models for all events

These models ensure type safety and validation for events
flowing through the pub/sub system.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .event_types import EventType


class BaseEvent(BaseModel):
    """
    Base event model that all events inherit from.

    Attributes:
        event_type: Type of event
        event_id: Unique identifier for this event
        timestamp: When the event was created
        user_id: Optional user who triggered the event
        metadata: Additional event metadata
    """

    event_type: EventType
    event_id: str = Field(
        default_factory=lambda: f"evt_{datetime.utcnow().timestamp()}"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


# ============================================================================
# Conversation Events
# ============================================================================


class ConversationCreatedEvent(BaseEvent):
    """
    Event published when a new conversation is created.

    Attributes:
        conversation_id: ID of the created conversation
        title: Conversation title
    """

    event_type: EventType = EventType.CONVERSATION_CREATED
    conversation_id: str
    title: Optional[str] = None


class ConversationUpdatedEvent(BaseEvent):
    """
    Event published when a conversation is updated.

    Attributes:
        conversation_id: ID of the updated conversation
        updates: Dictionary of updated fields
    """

    event_type: EventType = EventType.CONVERSATION_UPDATED
    conversation_id: str
    updates: Dict[str, Any]


class ConversationDeletedEvent(BaseEvent):
    """
    Event published when a conversation is deleted.

    Attributes:
        conversation_id: ID of the deleted conversation
    """

    event_type: EventType = EventType.CONVERSATION_DELETED
    conversation_id: str


# ============================================================================
# Message Events
# ============================================================================


class MessageReceivedEvent(BaseEvent):
    """
    Event published when a user message is received.

    This triggers:
    - Saving user message to database
    - AI response generation (handled by chat route)

    Attributes:
        conversation_id: ID of the conversation
        message: User's message content
        role: Message role (typically "user")
    """

    event_type: EventType = EventType.MESSAGE_RECEIVED
    conversation_id: str
    message: str
    role: str = "user"


class ResponseGeneratedEvent(BaseEvent):
    """
    Event published when AI generates a response.

    This triggers:
    - Saving assistant message to database
    - Optional analytics tracking

    Attributes:
        conversation_id: ID of the conversation
        response: AI's response content
        role: Message role (typically "assistant")
        model: AI model used
        sources: Retrieved sources used in response
    """

    event_type: EventType = EventType.RESPONSE_GENERATED
    conversation_id: str
    response: str
    role: str = "assistant"
    model: Optional[str] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)


class MessageSavedEvent(BaseEvent):
    """
    Event published after a message is successfully saved to database.

    This is a confirmation event that can be used for:
    - Analytics
    - Logging
    - Triggering downstream actions

    Attributes:
        conversation_id: ID of the conversation
        message_id: ID of the saved message
        role: Message role
        success: Whether save was successful
    """

    event_type: EventType = EventType.MESSAGE_SAVED
    conversation_id: str
    message_id: str
    role: str
    success: bool = True


# ============================================================================
# Error Events
# ============================================================================


class SaveFailedEvent(BaseEvent):
    """
    Event published when a database save operation fails.

    This can trigger:
    - Retry logic
    - Error logging
    - Alerting

    Attributes:
        conversation_id: ID of the conversation
        error: Error message
        retry_count: Number of retry attempts
        original_event: The event that failed to process
    """

    event_type: EventType = EventType.SAVE_FAILED
    conversation_id: str
    error: str
    retry_count: int = 0
    original_event: Optional[Dict[str, Any]] = None
