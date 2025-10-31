"""
Events Package - Pub/Sub event system for async database operations

This package provides a lightweight event bus for decoupling database
operations from the main request flow, enabling non-blocking persistence
of conversation memory.
"""

from .event_bus import EventBus, event_bus
from .event_models import (
    BaseEvent,
    ConversationCreatedEvent,
    ConversationDeletedEvent,
    ConversationUpdatedEvent,
    MessageReceivedEvent,
    MessageSavedEvent,
    ResponseGeneratedEvent,
    SaveFailedEvent,
)
from .event_types import EventType

__all__ = [
    # Event Bus
    "EventBus",
    "event_bus",
    # Event Types
    "EventType",
    # Event Models
    "BaseEvent",
    "ConversationCreatedEvent",
    "ConversationUpdatedEvent",
    "ConversationDeletedEvent",
    "MessageReceivedEvent",
    "ResponseGeneratedEvent",
    "MessageSavedEvent",
    "SaveFailedEvent",
]
