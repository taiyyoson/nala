"""
Event Bus Tests - Test pub/sub system for async database operations

Tests the event bus, event models, and subscribers to ensure
reliable async message persistence for conversation memory.
"""

import asyncio

import pytest
from config.database import get_db
from events import (
    EventType,
    MessageReceivedEvent,
    MessageSavedEvent,
    ResponseGeneratedEvent,
    SaveFailedEvent,
    event_bus,
)
from services.database_service import DatabaseService


@pytest.mark.asyncio
class TestEventBus:
    """Test core event bus functionality"""

    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Setup and teardown for each test"""
        # Clear subscribers before each test
        event_bus.clear_all_subscribers()
        yield
        # Clear subscribers after each test
        event_bus.clear_all_subscribers()

    async def test_subscribe_and_publish(self):
        """Test basic subscribe and publish functionality"""
        received_events = []

        async def handler(event):
            received_events.append(event)

        # Subscribe to event
        event_bus.subscribe(EventType.MESSAGE_RECEIVED, handler)

        # Publish event
        event = MessageReceivedEvent(
            conversation_id="conv_test",
            message="Hello world",
            user_id="user_123",
        )

        await event_bus.publish_async(event)

        # Verify event was received
        assert len(received_events) == 1
        assert received_events[0].conversation_id == "conv_test"
        assert received_events[0].message == "Hello world"

    async def test_multiple_subscribers(self):
        """Test that multiple subscribers receive the same event"""
        handler1_calls = []
        handler2_calls = []

        async def handler1(event):
            handler1_calls.append(event)

        async def handler2(event):
            handler2_calls.append(event)

        # Subscribe both handlers
        event_bus.subscribe(EventType.MESSAGE_RECEIVED, handler1)
        event_bus.subscribe(EventType.MESSAGE_RECEIVED, handler2)

        # Publish event
        event = MessageReceivedEvent(
            conversation_id="conv_test",
            message="Test",
            user_id="user_123",
        )

        await event_bus.publish_async(event)

        # Verify both handlers received event
        assert len(handler1_calls) == 1
        assert len(handler2_calls) == 1

    async def test_unsubscribe(self):
        """Test unsubscribing from events"""
        received_events = []

        async def handler(event):
            received_events.append(event)

        # Subscribe and then unsubscribe
        event_bus.subscribe(EventType.MESSAGE_RECEIVED, handler)
        event_bus.unsubscribe(EventType.MESSAGE_RECEIVED, handler)

        # Publish event
        event = MessageReceivedEvent(
            conversation_id="conv_test",
            message="Test",
            user_id="user_123",
        )

        await event_bus.publish_async(event)

        # Verify handler did not receive event
        assert len(received_events) == 0

    async def test_event_isolation(self):
        """Test that subscriber errors don't affect other subscribers"""
        successful_calls = []

        async def failing_handler(event):
            raise Exception("Handler failed!")

        async def successful_handler(event):
            successful_calls.append(event)

        # Subscribe both handlers
        event_bus.subscribe(EventType.MESSAGE_RECEIVED, failing_handler)
        event_bus.subscribe(EventType.MESSAGE_RECEIVED, successful_handler)

        # Publish event
        event = MessageReceivedEvent(
            conversation_id="conv_test",
            message="Test",
            user_id="user_123",
        )

        await event_bus.publish_async(event)

        # Verify successful handler still ran
        assert len(successful_calls) == 1

    async def test_get_subscriber_count(self):
        """Test getting subscriber count for event type"""

        async def handler1(event):
            pass

        async def handler2(event):
            pass

        # Get initial count (might have some from previous tests or global setup)
        initial_count = event_bus.get_subscriber_count(EventType.MESSAGE_RECEIVED)

        # Add subscribers
        event_bus.subscribe(EventType.MESSAGE_RECEIVED, handler1)
        assert (
            event_bus.get_subscriber_count(EventType.MESSAGE_RECEIVED)
            == initial_count + 1
        )

        event_bus.subscribe(EventType.MESSAGE_RECEIVED, handler2)
        assert (
            event_bus.get_subscriber_count(EventType.MESSAGE_RECEIVED)
            == initial_count + 2
        )


@pytest.mark.asyncio
class TestEventModels:
    """Test event model validation"""

    def test_message_received_event(self):
        """Test MessageReceivedEvent model"""
        event = MessageReceivedEvent(
            conversation_id="conv_123",
            message="Hello",
            user_id="user_456",
        )

        assert event.event_type == EventType.MESSAGE_RECEIVED
        assert event.conversation_id == "conv_123"
        assert event.message == "Hello"
        assert event.user_id == "user_456"
        assert event.role == "user"

    def test_response_generated_event(self):
        """Test ResponseGeneratedEvent model"""
        event = ResponseGeneratedEvent(
            conversation_id="conv_123",
            response="AI response here",
            model="gpt-4",
            sources=[{"title": "Source 1"}],
            user_id="user_456",
        )

        assert event.event_type == EventType.RESPONSE_GENERATED
        assert event.conversation_id == "conv_123"
        assert event.response == "AI response here"
        assert event.model == "gpt-4"
        assert len(event.sources) == 1
        assert event.role == "assistant"

    def test_message_saved_event(self):
        """Test MessageSavedEvent model"""
        event = MessageSavedEvent(
            conversation_id="conv_123",
            message_id="msg_789",
            role="user",
            user_id="user_456",
            success=True,
        )

        assert event.event_type == EventType.MESSAGE_SAVED
        assert event.conversation_id == "conv_123"
        assert event.message_id == "msg_789"
        assert event.success is True

    def test_save_failed_event(self):
        """Test SaveFailedEvent model"""
        event = SaveFailedEvent(
            conversation_id="conv_123",
            error="Database connection failed",
            retry_count=2,
            user_id="user_456",
        )

        assert event.event_type == EventType.SAVE_FAILED
        assert event.conversation_id == "conv_123"
        assert event.error == "Database connection failed"
        assert event.retry_count == 2


# NOTE: Database subscriber integration tests are commented out for now
# They require proper database setup in test environment
# The subscriber will be tested via end-to-end API tests instead

# @pytest.mark.asyncio
# class TestDatabaseSubscriber:
#     """Test database subscriber integration"""
#
#     Integration tests would go here, but are better suited for
#     end-to-end API tests where the full app context is available
