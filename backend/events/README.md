# Events Package - Pub/Sub System

This package implements a lightweight, in-memory event-driven pub/sub system for async database operations.

## Quick Start

### Publishing Events

```python
from events import MessageReceivedEvent, event_bus

# Publish an event (non-blocking)
await event_bus.publish_async(
    MessageReceivedEvent(
        conversation_id="conv_123",
        message="Hello world",
        user_id="user_456"
    )
)
```

### Subscribing to Events

```python
from events import EventType, event_bus

# Register a subscriber
@event_bus.subscribe(EventType.MESSAGE_RECEIVED)
async def my_handler(event):
    print(f"Received: {event.message}")
```

## Available Event Types

- `CONVERSATION_CREATED` - New conversation started
- `MESSAGE_RECEIVED` - User message received
- `RESPONSE_GENERATED` - AI response generated
- `MESSAGE_SAVED` - Message saved to database
- `SAVE_FAILED` - Database save failed

## Event Models

All events inherit from `BaseEvent` and include:
- `event_type`: Type of event
- `event_id`: Unique identifier
- `timestamp`: When event was created
- `user_id`: Optional user identifier
- `metadata`: Additional event data

### Example: MessageReceivedEvent

```python
MessageReceivedEvent(
    conversation_id="conv_123",     # Required
    message="Hello",                 # Required
    role="user",                     # Default: "user"
    user_id="user_456",             # Optional
    metadata={"source": "mobile"}    # Optional
)
```

## Files

- `event_types.py` - Event type enum
- `event_models.py` - Pydantic event models
- `event_bus.py` - Central message broker
- `__init__.py` - Package exports

## Architecture

```
Publisher → Event Bus → Subscribers
   ↓          ↓            ↓
Routes    (Queue)    Database, Analytics, etc.
```

## See Also

- [Full Architecture Documentation](../docs/PUB_SUB_ARCHITECTURE.md)
- [Database Subscriber](../subscribers/database_subscriber.py)
- [Tests](../tests/test_event_bus.py)
