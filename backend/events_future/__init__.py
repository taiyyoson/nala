"""
Event definitions for future event-driven architecture.

This module contains event data classes that represent things that have happened
in the system. These are NOT part of the active flow yet - they're setup for future use.
"""

from .message_events import MessageCreatedEvent, MessageProcessedEvent

__all__ = ["MessageCreatedEvent", "MessageProcessedEvent"]
