"""
Chat Schemas - Pydantic models for chat API endpoints

Enhanced versions of the basic models in routes/chat.py with additional fields.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatMessage(BaseModel):
    """Individual message in a conversation."""

    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(default=None, description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "I'm feeling stressed about my workload",
                "timestamp": "2024-10-13T10:30:00Z"
            }
        }


class ChatRequest(BaseModel):
    """Request model for sending a chat message."""

    message: str = Field(..., min_length=1, description="User's message")
    conversation_id: Optional[str] = Field(default=None, description="Existing conversation ID")
    user_id: Optional[str] = Field(default=None, description="User ID")
    model_preference: Optional[str] = Field(default=None, description="Preferred LLM model")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "I'm struggling with motivation to exercise",
                "conversation_id": "conv_123",
                "user_id": "user_456"
            }
        }


class SourceInfo(BaseModel):
    """Information about a retrieved coaching example."""

    similarity: float = Field(..., description="Similarity score (0-1)")
    category: Optional[str] = Field(default=None, description="Context category")
    goal_type: Optional[str] = Field(default=None, description="Goal type")
    snippet: Optional[str] = Field(default=None, description="Example snippet")


class ChatResponse(BaseModel):
    """Response model for chat messages."""

    response: str = Field(..., description="Assistant's response")
    conversation_id: str = Field(..., description="Conversation ID")
    message_id: str = Field(..., description="Unique message ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Response metadata (model used, sources, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "response": "It sounds like you're feeling overwhelmed. What specifically about your workload is causing the most stress?",
                "conversation_id": "conv_123",
                "message_id": "msg_789",
                "timestamp": "2024-10-13T10:30:05Z",
                "metadata": {
                    "model": "Claude Sonnet 4",
                    "source_count": 3,
                    "sources": [
                        {
                            "similarity": 0.85,
                            "category": "stress_management"
                        }
                    ]
                }
            }
        }


class StreamChunk(BaseModel):
    """Chunk of streamed response."""

    content: str = Field(..., description="Text content")
    done: bool = Field(default=False, description="Whether streaming is complete")
    error: Optional[str] = Field(default=None, description="Error message if any")


class ConversationSummary(BaseModel):
    """Summary of a conversation for list views."""

    conversation_id: str = Field(..., description="Conversation ID")
    title: Optional[str] = Field(default=None, description="Conversation title")
    last_message_preview: Optional[str] = Field(default=None, description="Preview of last message")
    message_count: int = Field(default=0, description="Total message count")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_123",
                "title": "Stress management discussion",
                "last_message_preview": "It sounds like you're feeling...",
                "message_count": 8,
                "created_at": "2024-10-13T10:00:00Z",
                "updated_at": "2024-10-13T10:30:00Z"
            }
        }


class ConversationDetail(BaseModel):
    """Detailed conversation with full message history."""

    conversation_id: str = Field(..., description="Conversation ID")
    user_id: Optional[str] = Field(default=None, description="User ID")
    title: Optional[str] = Field(default=None, description="Conversation title")
    message_count: int = Field(default=0, description="Total message count")
    messages: List[ChatMessage] = Field(default_factory=list, description="All messages")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_123",
                "user_id": "user_456",
                "title": "Stress management discussion",
                "message_count": 2,
                "messages": [
                    {
                        "role": "user",
                        "content": "I'm feeling stressed",
                        "timestamp": "2024-10-13T10:30:00Z"
                    },
                    {
                        "role": "assistant",
                        "content": "I understand...",
                        "timestamp": "2024-10-13T10:30:05Z"
                    }
                ],
                "created_at": "2024-10-13T10:00:00Z",
                "updated_at": "2024-10-13T10:30:05Z"
            }
        }


class ConversationListResponse(BaseModel):
    """Response for listing conversations."""

    conversations: List[ConversationSummary] = Field(..., description="List of conversations")
    total: int = Field(..., description="Total conversation count")
    limit: int = Field(..., description="Results limit")
    offset: int = Field(..., description="Results offset")
