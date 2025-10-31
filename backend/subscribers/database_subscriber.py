"""
Database Subscriber - Handles database persistence via events

This subscriber listens for message and conversation events and
persists them to the database asynchronously, enabling non-blocking
database operations for conversation memory.
"""

import logging
from typing import Optional

from config.database import db_config
from events import (
    ConversationCreatedEvent,
    ConversationDeletedEvent,
    EventType,
    MessageReceivedEvent,
    MessageSavedEvent,
    ResponseGeneratedEvent,
    SaveFailedEvent,
    event_bus,
)
from services.database_service import DatabaseService

logger = logging.getLogger(__name__)


class DatabaseSubscriber:
    """
    Subscriber that handles database operations via events.

    This subscriber:
    - Listens for message and conversation events
    - Persists data to database asynchronously
    - Publishes confirmation events after successful saves
    - Handles errors and publishes failure events

    Features:
    - Non-blocking database writes
    - Automatic retry on failure (optional)
    - Event-driven architecture
    """

    def __init__(self, max_retries: int = 3):
        """
        Initialize Database Subscriber.

        Args:
            max_retries: Maximum number of retry attempts for failed saves
        """
        self.max_retries = max_retries
        self._is_registered = False
        logger.info("✓ DatabaseSubscriber initialized")

    def register(self) -> None:
        """
        Register event handlers with the event bus.

        This subscribes to all relevant events.
        """
        if self._is_registered:
            logger.warning("⚠ DatabaseSubscriber already registered")
            return

        # Subscribe to conversation events
        event_bus.subscribe(
            EventType.CONVERSATION_CREATED, self.handle_conversation_created
        )

        # Subscribe to message events
        event_bus.subscribe(EventType.MESSAGE_RECEIVED, self.handle_message_received)
        event_bus.subscribe(
            EventType.RESPONSE_GENERATED, self.handle_response_generated
        )

        # Subscribe to error events for retry logic
        event_bus.subscribe(EventType.SAVE_FAILED, self.handle_save_failed)

        self._is_registered = True
        logger.info("✓ DatabaseSubscriber registered with event bus")

    async def handle_conversation_created(
        self, event: ConversationCreatedEvent
    ) -> None:
        """
        Handle conversation creation event.

        Note: Conversation is typically already created by the route,
        so this is mainly for confirmation/logging.

        Args:
            event: ConversationCreatedEvent
        """
        logger.info(
            f"✓ Conversation created: {event.conversation_id} (user: {event.user_id})"
        )

    async def handle_message_received(self, event: MessageReceivedEvent) -> None:
        """
        Handle user message received event.

        This saves the user's message to the database.

        Args:
            event: MessageReceivedEvent
        """
        try:
            # Get database session
            with db_config.session_scope() as session:
                db_service = DatabaseService(session)

                # Save user message
                message_data = {
                    "conversation_id": event.conversation_id,
                    "role": event.role,
                    "content": event.message,
                    "metadata": event.metadata,
                }

                message = db_service.create_message(message_data)

                logger.info(
                    f"✓ Saved user message: {message.id} (conv: {event.conversation_id})"
                )

                # Publish success confirmation
                event_bus.publish(
                    MessageSavedEvent(
                        conversation_id=event.conversation_id,
                        message_id=message.id,
                        role=event.role,
                        user_id=event.user_id,
                        success=True,
                    )
                )

        except Exception as e:
            logger.error(f"✗ Failed to save user message: {e}")

            # Publish failure event for retry logic
            event_bus.publish(
                SaveFailedEvent(
                    conversation_id=event.conversation_id,
                    error=str(e),
                    retry_count=event.metadata.get("retry_count", 0),
                    original_event=event.dict(),
                    user_id=event.user_id,
                )
            )

    async def handle_response_generated(self, event: ResponseGeneratedEvent) -> None:
        """
        Handle AI response generated event.

        This saves the assistant's response to the database.

        Args:
            event: ResponseGeneratedEvent
        """
        try:
            # Get database session
            with db_config.session_scope() as session:
                db_service = DatabaseService(session)

                # Save assistant message
                message_data = {
                    "conversation_id": event.conversation_id,
                    "role": event.role,
                    "content": event.response,
                    "metadata": {
                        "model": event.model,
                        "sources": event.sources,
                        **event.metadata,
                    },
                }

                message = db_service.create_message(message_data)

                logger.info(
                    f"✓ Saved assistant response: {message.id} (conv: {event.conversation_id})"
                )

                # Publish success confirmation
                event_bus.publish(
                    MessageSavedEvent(
                        conversation_id=event.conversation_id,
                        message_id=message.id,
                        role=event.role,
                        user_id=event.user_id,
                        success=True,
                    )
                )

        except Exception as e:
            logger.error(f"✗ Failed to save assistant response: {e}")

            # Publish failure event for retry logic
            event_bus.publish(
                SaveFailedEvent(
                    conversation_id=event.conversation_id,
                    error=str(e),
                    retry_count=event.metadata.get("retry_count", 0),
                    original_event=event.dict(),
                    user_id=event.user_id,
                )
            )

    async def handle_save_failed(self, event: SaveFailedEvent) -> None:
        """
        Handle save failure event with retry logic.

        Args:
            event: SaveFailedEvent
        """
        retry_count = event.retry_count

        if retry_count < self.max_retries:
            logger.warning(
                f"⟳ Retrying save operation (attempt {retry_count + 1}/{self.max_retries})"
            )

            # Recreate original event with updated retry count
            if event.original_event:
                original_event_type = event.original_event.get("event_type")

                # Update retry count in metadata
                if "metadata" not in event.original_event:
                    event.original_event["metadata"] = {}
                event.original_event["metadata"]["retry_count"] = retry_count + 1

                # Re-publish based on original event type
                if original_event_type == EventType.MESSAGE_RECEIVED.value:
                    event_bus.publish(MessageReceivedEvent(**event.original_event))
                elif original_event_type == EventType.RESPONSE_GENERATED.value:
                    event_bus.publish(ResponseGeneratedEvent(**event.original_event))

        else:
            logger.error(
                f"✗ Max retries ({self.max_retries}) reached for conversation {event.conversation_id}. Save failed permanently."
            )
            # TODO: Could send alert, write to error log file, etc.


# Global database subscriber instance
database_subscriber = DatabaseSubscriber()
