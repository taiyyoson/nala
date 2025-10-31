"""
Event Bus - Central message broker for pub/sub system

This is a lightweight, in-memory event bus for async message passing.
Focused on enabling non-blocking database operations for conversation memory.
"""

import asyncio
import logging
from collections import defaultdict
from typing import Callable, Dict, List, Optional

from .event_models import BaseEvent
from .event_types import EventType

logger = logging.getLogger(__name__)


class EventBus:
    """
    Lightweight in-memory event bus for pub/sub messaging.

    This event bus enables decoupled, async communication between
    components, primarily for database streaming operations.

    Features:
    - Subscribe to specific event types
    - Publish events to all subscribers
    - Async event handling (non-blocking)
    - Error isolation (one subscriber failure doesn't affect others)

    Example:
        # Subscribe to events
        @event_bus.subscribe(EventType.MESSAGE_RECEIVED)
        async def handle_message(event):
            await save_to_database(event)

        # Publish events
        event_bus.publish(MessageReceivedEvent(
            conversation_id="conv_123",
            message="Hello"
        ))
    """

    def __init__(self):
        """Initialize the event bus."""
        # Dictionary mapping event types to list of subscriber callbacks
        # EventType -> List[Callable]
        self._subscribers: Dict[EventType, List[Callable]] = defaultdict(list)

        # Event queue for async processing
        self._event_queue: asyncio.Queue = asyncio.Queue()

        # Flag to control event processing
        self._running = False

        # Task for processing events
        self._processor_task: Optional[asyncio.Task] = None

        logger.info("✓ EventBus initialized")

    def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            callback: Async function to call when event is published
                     Should accept event as parameter: async def callback(event)

        Example:
            @event_bus.subscribe(EventType.MESSAGE_RECEIVED)
            async def save_message(event):
                await db.save(event.message)
        """
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
            logger.debug(f"✓ Subscribed {callback.__name__} to {event_type.value}")

    def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            callback: Callback function to remove
        """
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)
            logger.debug(f"✓ Unsubscribed {callback.__name__} from {event_type.value}")

    def publish(self, event: BaseEvent) -> None:
        """
        Publish an event to all subscribers (non-blocking).

        This method returns immediately. The event is added to a queue
        and processed asynchronously.

        Args:
            event: Event to publish

        Example:
            event_bus.publish(MessageReceivedEvent(
                conversation_id="conv_123",
                message="Hello"
            ))
        """
        try:
            # Add to queue for async processing
            self._event_queue.put_nowait(event)
            logger.debug(
                f"→ Published {event.event_type.value} (event_id={event.event_id})"
            )
        except Exception as e:
            logger.error(f"✗ Failed to publish event: {e}")

    async def publish_async(self, event: BaseEvent) -> None:
        """
        Publish an event and wait for all subscribers to process it.

        Unlike publish(), this method waits for all subscribers to finish.
        Use this when you need to ensure event processing is complete.

        Args:
            event: Event to publish
        """
        await self._process_event(event)

    async def _process_event(self, event: BaseEvent) -> None:
        """
        Process a single event by calling all subscribers.

        Args:
            event: Event to process
        """
        event_type = event.event_type
        subscribers = self._subscribers.get(event_type, [])

        if not subscribers:
            logger.debug(f"⚠ No subscribers for {event_type.value}")
            return

        logger.debug(
            f"⟳ Processing {event_type.value} with {len(subscribers)} subscriber(s)"
        )

        # Call all subscribers in parallel
        tasks = []
        for callback in subscribers:
            try:
                # Handle both sync and async callbacks
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(callback(event))
                else:
                    # Wrap sync callback in async
                    tasks.append(asyncio.to_thread(callback, event))
            except Exception as e:
                logger.error(f"✗ Error creating task for {callback.__name__}: {e}")

        # Execute all tasks in parallel, catching individual errors
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log any errors
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    callback = subscribers[i]
                    logger.error(
                        f"✗ Error in {callback.__name__} for {event_type.value}: {result}"
                    )

    async def _event_processor(self) -> None:
        """
        Background task that processes events from the queue.

        This runs continuously and processes events as they arrive.
        """
        logger.info("✓ Event processor started")

        while self._running:
            try:
                # Wait for events with timeout to allow graceful shutdown
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._process_event(event)
                self._event_queue.task_done()

            except asyncio.TimeoutError:
                # No events in queue, continue waiting
                continue
            except Exception as e:
                logger.error(f"✗ Error in event processor: {e}")

        logger.info("✓ Event processor stopped")

    async def start(self) -> None:
        """
        Start the event bus processing loop.

        This should be called during application startup.
        """
        if self._running:
            logger.warning("⚠ Event bus already running")
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._event_processor())
        logger.info("✓ Event bus started")

    async def stop(self) -> None:
        """
        Stop the event bus and wait for pending events to complete.

        This should be called during application shutdown.
        """
        if not self._running:
            logger.warning("⚠ Event bus not running")
            return

        logger.info("⟳ Stopping event bus...")
        self._running = False

        # Wait for pending events to complete
        if not self._event_queue.empty():
            logger.info(f"⟳ Processing {self._event_queue.qsize()} pending events...")
            await self._event_queue.join()

        # Cancel processor task
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

        logger.info("✓ Event bus stopped")

    def get_subscriber_count(self, event_type: EventType) -> int:
        """
        Get number of subscribers for an event type.

        Args:
            event_type: Event type to check

        Returns:
            Number of subscribers
        """
        return len(self._subscribers.get(event_type, []))

    def clear_all_subscribers(self) -> None:
        """
        Remove all subscribers (useful for testing).
        """
        self._subscribers.clear()
        logger.info("✓ All subscribers cleared")


# Global event bus instance
event_bus = EventBus()
