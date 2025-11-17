import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
import traceback

from adapters import RequestAdapter, ResponseAdapter
from config.database import get_db
from config.settings import settings
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services import AIService, ConversationService, DatabaseService
from sqlalchemy.orm import Session
from session1_manager import SessionBasedRAGChatbot

chat_router = APIRouter(prefix="/chat", tags=["chat"])

# AI service cache: maintains session state per conversation
_ai_service_cache: Dict[str, AIService] = {}


def get_or_create_ai_service(
    conversation_id: str, session_number: Optional[int] = None
) -> AIService:
    print(f"🧠 Using conversation {conversation_id}, existing={conversation_id in _ai_service_cache}, session={session_number}")

    """
    Get or create an AI service instance for a conversation.
    Maintains session state across messages within the same conversation.
    """

    if conversation_id in _ai_service_cache:
        existing_service = _ai_service_cache[conversation_id]

        # If the session number changed, reset the AI service instance
        if (
            session_number is not None
            and existing_service.session_number != session_number
        ):
            print(
                f"⚠️ Session number changed for conversation {conversation_id}: "
                f"{existing_service.session_number} -> {session_number}"
            )
            ai_service = AIService(
                model=settings.default_llm_model,
                top_k=settings.top_k_sources,
                session_number=session_number,
            )
            _ai_service_cache[conversation_id] = ai_service
            return ai_service

        return existing_service

    # Otherwise create a new AI service instance
    ai_service = AIService(
        model=settings.default_llm_model,
        top_k=settings.top_k_sources,
        session_number=session_number,
    )
    _ai_service_cache[conversation_id] = ai_service
    return ai_service


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_number: Optional[int] = None  # 1–4 for structured coaching sessions


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    message_id: str
    timestamp: datetime
    metadata: Optional[dict] = None


@chat_router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest, db: Session = Depends(get_db)):
    """Send a message to the health coaching chatbot"""
    try:
        # Initialize services
        db_service = DatabaseService(db)
        conv_service = ConversationService(db_service)

        # Retrieve or create conversation
        conv_id = await conv_service.get_or_create_conversation(
            conversation_id=request.conversation_id, user_id=request.user_id
        )

        # Get conversation history (for AI context)
        history = await conv_service.get_conversation_history(
            conversation_id=conv_id, limit=10
        )

        # Get or create AI service instance
        ai_service = get_or_create_ai_service(
            conversation_id=conv_id, session_number=request.session_number
        )

        print(f"🧩 chatbot object id: {id(ai_service.chatbot)}")
        if hasattr(ai_service.chatbot, "session_manager"):
            print(f"🧩 session_manager state: {ai_service.chatbot.session_manager.get_state().value}")

        # DEBUG logs from main
        print(f"🔍 DEBUG: session_number={request.session_number}, history_length={len(history)}")
        print(f"🔍 DEBUG: ai_service.session_number={ai_service.session_number}")
        print(f"🔍 DEBUG: chatbot type={type(ai_service.chatbot).__name__}")

        # **Session 1 Initialization logic preserved**
        if request.session_number == 1 and len(history) == 0:
            print("🎯 INITIALIZING Session 1 with [START_SESSION]")
            response, sources, model_name = await ai_service.generate_response(
                message="[START_SESSION]",
                conversation_history=[],
                user_id=request.user_id,
            )
            print(f"📝 Init response (Nala's greeting): {response[:100]}...")
        else:
            # Normal response generation
            response, sources, model_name = await ai_service.generate_response(
                message=request.message,
                conversation_history=history,
                user_id=request.user_id,
            )

        # Save user message
        await conv_service.add_message(
            conversation_id=conv_id,
            role="user",
            content=request.message,
        )

        # Save assistant response
        msg_data = await conv_service.add_message(
            conversation_id=conv_id,
            role="assistant",
            content=response,
            metadata={
                "model": model_name,
                "sources": ResponseAdapter.format_sources(sources),
            },
        )

        # Session state extraction (optional)
        session_state = None
        if hasattr(ai_service.chatbot, "session_manager"):
            session_state = ai_service.chatbot.session_manager.get_state().value

        # Format final response payload
        formatted_response = ResponseAdapter.ai_response_to_chat_response(
            rag_output=(response, sources, model_name),
            conversation_id=conv_id,
            message_id=msg_data["message_id"],
        )

        return ChatResponse(**formatted_response)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in send_message: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.post("/stream")
async def stream_message(request: ChatRequest, db: Session = Depends(get_db)):
    """Stream chatbot response for real-time chat experience"""

    async def generate_stream():
        try:
            db_service = DatabaseService(db)
            conv_service = ConversationService(db_service)

            # Conversation
            conv_id = await conv_service.get_or_create_conversation(
                conversation_id=request.conversation_id, user_id=request.user_id
            )

            history = await conv_service.get_conversation_history(conv_id, limit=10)

            ai_service = get_or_create_ai_service(
                conversation_id=conv_id, session_number=request.session_number
            )

            # Stream chunks
            full_response = ""
            async for chunk in ai_service.stream_response(
                request.message, history, request.user_id
            ):
                full_response += chunk
                yield ResponseAdapter.streaming_chunk_to_sse(chunk, done=False)

            yield ResponseAdapter.streaming_chunk_to_sse("", done=True)

            # Save messages
            await conv_service.add_message(
                conversation_id=conv_id, role="user", content=request.message
            )

            await conv_service.add_message(
                conversation_id=conv_id,
                role="assistant",
                content=full_response.strip(),
            )

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
    try:
        db_service = DatabaseService(db)
        conv_service = ConversationService(db_service)

        conversation = await conv_service.get_conversation(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return ResponseAdapter.conversation_to_api_format(
            conversation_data=conversation,
            messages=conversation.get("messages"),
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
