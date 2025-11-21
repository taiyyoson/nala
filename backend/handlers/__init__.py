"""
Event handlers for processing domain events.

Handlers are NOT active in the current flow - they're setup for future use.
When you're ready to go event-driven, wire these up in your routes.
"""

from .base_handler import EventHandler
from .message_handler import MessageCreatedHandler, MessageProcessedHandler

__all__ = ["EventHandler", "MessageCreatedHandler", "MessageProcessedHandler"]
