"""
Message-related events for event-driven architecture.

Events represent facts - things that have already happened.
Use past tense naming: MessageCreated (not CreateMessage).
"""

from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel


class MessageCreatedEvent(BaseModel):
    """
    Event fired when a user sends a message to the chatbot.

    This event represents the initial user input before AI processing.
    """
    event_id: str
    timestamp: datetime
    conversation_id: str
    user_id: str
    message_content: str
    session_number: Optional[int] = None
    metadata: Dict = {}

    class Config:
        frozen = True  # Events are immutable


class MessageProcessedEvent(BaseModel):
    """
    Event fired when the AI has generated a response to a message.

    This event represents the complete message exchange (user + AI response).
    """
    event_id: str
    timestamp: datetime
    conversation_id: str
    user_id: str
    user_message: str
    ai_response: str
    model_used: str
    session_number: Optional[int] = None
    sources: list = []
    metadata: Dict = {}

    class Config:
        frozen = True  # Events are immutable
