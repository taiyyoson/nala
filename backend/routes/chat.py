import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional

from adapters import RequestAdapter, ResponseAdapter
from config.database import get_db
from config.settings import settings
from events import MessageReceivedEvent, ResponseGeneratedEvent, event_bus
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services import AIService, ConversationService, DatabaseService
from sqlalchemy.orm import Session

chat_router = APIRouter(prefix="/chat", tags=["chat"])

# AI service cache: maintains session state per conversation
# Key: conversation_id, Value: AIService instance
_ai_service_cache: Dict[str, AIService] = {}


def get_or_create_ai_service(
    conversation_id: str, session_number: Optional[int] = None
) -> AIService:
    """
    Get or create an AI service instance for a conversation.
    Maintains session state across messages within the same conversation.

    Args:
        conversation_id: Unique conversation identifier
        session_number: Session number (1-4) for structured coaching

    Returns:
        AIService instance with session state
    """
    # Check if we already have an AI service for this conversation
    if conversation_id in _ai_service_cache:
        existing_service = _ai_service_cache[conversation_id]
        # Verify session number matches (if provided)
        if (
            session_number is not None
            and existing_service.session_number != session_number
        ):
            # Session number changed - create new service
            print(
                f"⚠️ Session number changed for conversation {conversation_id}: {existing_service.session_number} -> {session_number}"
            )
            ai_service = AIService(
                model=settings.default_llm_model,
                top_k=settings.top_k_sources,
                session_number=session_number,
            )
            _ai_service_cache[conversation_id] = ai_service
            return ai_service
        return existing_service

    # Create new AI service for this conversation
    ai_service = AIService(
        model=settings.default_llm_model,
        top_k=settings.top_k_sources,
        session_number=session_number,
    )
    _ai_service_cache[conversation_id] = ai_service
    return ai_service


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_number: Optional[int] = None  # 1-4 for structured coaching sessions


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    message_id: str
    timestamp: datetime
    metadata: Optional[dict] = None


@chat_router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest, db: Session = Depends(get_db)):
    """Send a message to the health coaching chatbot (with async database via pub/sub)"""
    try:
        # Initialize services
        db_service = DatabaseService(db)
        conv_service = ConversationService(db_service)

        # Get or create conversation
        conv_id = await conv_service.get_or_create_conversation(
            conversation_id=request.conversation_id, user_id=request.user_id
        )

        # Publish event: User message received (DB save happens async via subscriber)
        user_msg_event = MessageReceivedEvent(
            conversation_id=conv_id,
            message=request.message,
            role="user",
            user_id=request.user_id,
        )
        # Use publish_async to ensure immediate processing in tests
        await event_bus.publish_async(user_msg_event)

        # Get conversation history (for AI context)
        history = await conv_service.get_conversation_history(
            conversation_id=conv_id, limit=10  # Last 10 messages for context
        )

        # Get or create AI service with session state for this conversation
        ai_service = get_or_create_ai_service(
            conversation_id=conv_id, session_number=request.session_number
        )

        # Generate AI response using RAG system (with session management if applicable)
        response, sources, model_name = await ai_service.generate_response(
            message=request.message,
            conversation_history=history,
            user_id=request.user_id,
        )

        # Publish event: AI response generated (DB save happens async via subscriber)
        ai_response_event = ResponseGeneratedEvent(
            conversation_id=conv_id,
            response=response,
            role="assistant",
            model=model_name,
            sources=ResponseAdapter.format_sources(sources),
            user_id=request.user_id,
        )
        # Use publish_async to ensure immediate processing in tests
        await event_bus.publish_async(ai_response_event)

        # Generate a temporary message ID for response (actual ID created by subscriber)
        import uuid

        temp_message_id = f"msg_{uuid.uuid4().hex[:12]}"

        # Format response using adapter
        formatted_response = ResponseAdapter.ai_response_to_chat_response(
            rag_output=(response, sources, model_name),
            conversation_id=conv_id,
            message_id=temp_message_id,
        )

        return ChatResponse(**formatted_response)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in send_message: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.post("/stream")
async def stream_message(request: ChatRequest, db: Session = Depends(get_db)):
    """Stream chatbot response for real-time chat experience (with async database via pub/sub)"""

    async def generate_stream():
        try:
            # Initialize services
            db_service = DatabaseService(db)
            conv_service = ConversationService(db_service)

            # Get or create conversation
            conv_id = await conv_service.get_or_create_conversation(
                conversation_id=request.conversation_id, user_id=request.user_id
            )

            # Publish event: User message received (DB save happens async)
            user_msg_event = MessageReceivedEvent(
                conversation_id=conv_id,
                message=request.message,
                role="user",
                user_id=request.user_id,
            )
            await event_bus.publish_async(user_msg_event)

            # Get conversation history
            history = await conv_service.get_conversation_history(conv_id, limit=10)

            # Get or create AI service with session state
            ai_service = get_or_create_ai_service(
                conversation_id=conv_id, session_number=request.session_number
            )

            # Stream response from AI service
            full_response = ""
            async for chunk in ai_service.stream_response(
                request.message, history, request.user_id
            ):
                full_response += chunk
                yield ResponseAdapter.streaming_chunk_to_sse(chunk, done=False)

            # Final chunk
            yield ResponseAdapter.streaming_chunk_to_sse("", done=True)

            # Publish event: AI response generated (DB save happens async)
            ai_response_event = ResponseGeneratedEvent(
                conversation_id=conv_id,
                response=full_response.strip(),
                role="assistant",
                user_id=request.user_id,
            )
            await event_bus.publish_async(ai_response_event)

        except Exception as e:
            error_chunk = ResponseAdapter.error_to_api_response(e, 500)
            yield f"data: {json.dumps(error_chunk)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@chat_router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Retrieve conversation history"""
    try:
        db_service = DatabaseService(db)
        conv_service = ConversationService(db_service)

        conversation = await conv_service.get_conversation(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return ResponseAdapter.conversation_to_api_format(
            conversation_data=conversation, messages=conversation.get("messages")
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.get("/conversations")
async def list_conversations(
    user_id: str, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)
):
    """List all conversations for a user"""
    try:
        db_service = DatabaseService(db)
        conv_service = ConversationService(db_service)

        conversations = await conv_service.list_conversations(user_id, limit, offset)

        return {
            "conversations": [
                ResponseAdapter.format_conversation_summary(conv)
                for conv in conversations
            ],
            "total": len(conversations),
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        print(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Delete a conversation and all its messages"""
    try:
        db_service = DatabaseService(db)
        conv_service = ConversationService(db_service)

        success = await conv_service.delete_conversation(conversation_id)

        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {"success": True, "message": "Conversation deleted"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
