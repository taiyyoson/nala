import asyncio
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from adapters import RequestAdapter, ResponseAdapter
from config.database import get_db
from config.settings import settings
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services import AIService, ConversationService, DatabaseService
from session1_manager import SessionBasedRAGChatbot
from sqlalchemy.orm import Session

# Add AI-backend to path for session database utilities
_ai_backend_path = Path(__file__).parent.parent.parent / "AI-backend"
if str(_ai_backend_path) not in sys.path:
    sys.path.insert(0, str(_ai_backend_path))

from utils.database import load_session_from_db, save_session_to_db

chat_router = APIRouter(prefix="/chat", tags=["chat"])

# AI service cache: maintains session state per conversation
_ai_service_cache: Dict[str, AIService] = {}


def get_or_create_ai_service(
    conversation_id: str,
    session_number: Optional[int] = None,
    user_id: Optional[str] = None,
) -> AIService:
    """
    Get or create an AI service instance for a conversation.
    Maintains session state across messages within the same conversation.

    For Session 2+, automatically loads previous session data from database.
    """
    print(
        f"🧠 Using conversation {conversation_id}, existing={conversation_id in _ai_service_cache}, session={session_number}"
    )

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
            # Load previous session data for Session 2+
            previous_session_data = _load_previous_session_data(user_id, session_number)

            ai_service = AIService(
                model=settings.default_llm_model,
                top_k=settings.top_k_sources,
                session_number=session_number,
                previous_session_data=previous_session_data,
            )
            _ai_service_cache[conversation_id] = ai_service
            return ai_service

        return existing_service

    # Load previous session data for Session 2+
    previous_session_data = _load_previous_session_data(user_id, session_number)

    # Create new AI service instance
    ai_service = AIService(
        model=settings.default_llm_model,
        top_k=settings.top_k_sources,
        session_number=session_number,
        previous_session_data=previous_session_data,
    )
    _ai_service_cache[conversation_id] = ai_service
    return ai_service


def _load_previous_session_data(
    user_id: Optional[str], session_number: Optional[int]
) -> Optional[Dict]:
    """
    Load previous session data from database for Session 2+.

    Returns user_profile from the previous session, which contains:
    - name, goals, discovery_questions for Session 1 → 2
    - Updated goals, stress levels, etc. for Session 2 → 3
    """
    if not user_id or not session_number or session_number <= 1:
        return None

    prev_session_num = session_number - 1
    print(f"📂 Loading Session {prev_session_num} data for user {user_id}...")

    try:
        prev_session = load_session_from_db(user_id, prev_session_num)
        if prev_session:
            print(f"✅ Loaded previous session data: {list(prev_session.get('user_profile', {}).keys())}")
            return prev_session.get('user_profile')
        else:
            print(f"⚠️ No Session {prev_session_num} data found for user {user_id}")
            return None
    except Exception as e:
        print(f"❌ Error loading previous session: {e}")
        return None


def _save_session_on_completion(
    ai_service: AIService,
    user_id: str,
    session_number: int,
    conversation_history: List[Dict],
) -> bool:
    """
    Save session data to database when session reaches END_SESSION state.

    Extracts user profile, goals, and metadata from the chatbot's session manager
    and persists it for use in subsequent sessions.
    """
    print(f"💾 Saving Session {session_number} data for user {user_id}...")

    try:
        session_manager = ai_service.chatbot.session_manager
        session_data = session_manager.session_data

        # Build user profile based on session number
        if session_number == 1:
            # Session 1: Extract discovery info and initial goals
            discovery = {
                "general_about": session_data.get("discovery", {}).get("general_about"),
                "current_exercise": session_data.get("discovery", {}).get("current_exercise"),
                "current_sleep": session_data.get("discovery", {}).get("current_sleep"),
                "current_eating": session_data.get("discovery", {}).get("current_eating"),
                "free_time_activities": session_data.get("discovery", {}).get("free_time_activities"),
            }

            goals = []
            for goal_detail in session_data.get("goal_details", []):
                goals.append({
                    "goal": goal_detail.get("goal"),
                    "confidence": goal_detail.get("confidence"),
                    "stress": None,
                    "session_created": 1,
                    "status": "active",
                    "created_at": session_data.get("session_start"),
                })

            user_profile = {
                "uid": user_id,
                "name": session_data.get("user_name"),
                "goals": goals,
                "discovery_questions": discovery,
            }
        else:
            # Session 2+: Extract updated goals and any new data
            user_profile = {
                "uid": user_id,
                "name": session_data.get("user_name"),
                "goals": session_data.get("new_goals", []) or session_data.get("goals_to_keep", []),
                "previous_goals": session_data.get("previous_goals", []),
                "stress_level": session_data.get("stress_level"),
                "successes": session_data.get("successes", []),
                "challenges": session_data.get("challenges", []),
                "path_chosen": session_data.get("path_chosen"),
            }

        # Build session info
        session_info = {
            "session_number": session_number,
            "current_state": session_manager.get_state().value,
            "metadata": {
                "turn_count": session_data.get("turn_count"),
                "current_goal": session_data.get("current_goal"),
            },
        }

        # Build full data payload
        full_data = {
            "user_profile": user_profile,
            "session_info": session_info,
            "chat_history": conversation_history or [],
        }

        # Save to database
        success = save_session_to_db(user_id, session_number, full_data)
        if success:
            print(f"✅ Session {session_number} saved successfully for user {user_id}")
        else:
            print(f"❌ Failed to save Session {session_number} for user {user_id}")
        return success

    except Exception as e:
        print(f"❌ Error saving session: {e}")
        traceback.print_exc()
        return False


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
    try:
        db_service = DatabaseService(db)
        conv_service = ConversationService(db_service)

        conv_id = await conv_service.get_or_create_conversation(
            conversation_id=request.conversation_id, user_id=request.user_id
        )

        history = await conv_service.get_conversation_history(
            conversation_id=conv_id, limit=10
        )

        ai_service = get_or_create_ai_service(
            conversation_id=conv_id,
            session_number=request.session_number,
            user_id=request.user_id,
        )

        response, sources, model_name = await ai_service.generate_response(
            message=request.message,
            conversation_history=history,
            user_id=request.user_id,
        )

        # 🟢 Detect end of coaching session 1 via session manager
        session_complete = False
        if hasattr(ai_service.chatbot, "session_manager"):
            print(
                f"🧩 session_manager state: {ai_service.chatbot.session_manager.get_state().value}"
            )

        # DEBUG logs from main
        print(
            f"🔍 DEBUG: session_number={request.session_number}, history_length={len(history)}"
        )
        print(f"🔍 DEBUG: ai_service.session_number={ai_service.session_number}")
        print(f"🔍 DEBUG: chatbot type={type(ai_service.chatbot).__name__}")

                session_obj = db.query(SessionProgress).filter_by(
                    user_id=request.user_id,
                    session_number=request.session_number,
                ).first()

                if session_obj:
                    unlock_time = session_obj.mark_complete(unlock_delay_days=7)
                else:
                    # If session record doesn't exist, create new
                    session_obj = SessionProgress(
                        user_id=request.user_id,
                        session_number=request.session_number,
                        completed_at=datetime.utcnow(),
                        unlocked_at=None,
                    )
                    db.add(session_obj)

                db.commit()
                db.refresh(session_obj)

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
                "session_complete": session_complete,
            },
        )

        # Session state extraction and auto-save on completion
        session_state = None
        if hasattr(ai_service.chatbot, "session_manager"):
            session_state = ai_service.chatbot.session_manager.get_state().value

            # Auto-save session data when session ends
            if session_state == "end_session" and request.user_id and request.session_number:
                _save_session_on_completion(
                    ai_service=ai_service,
                    user_id=request.user_id,
                    session_number=request.session_number,
                    conversation_history=ai_service.chatbot.conversation_history,
                )

        # Format final response payload
        formatted_response = ResponseAdapter.ai_response_to_chat_response(
            rag_output=(response, sources, model_name),
            conversation_id=conv_id,
            message_id=msg_data["message_id"],
        )
        formatted_response["session_complete"] = session_complete

        return ChatResponse(**formatted_response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# NOTE: Streaming endpoint commented out - not currently used by frontend
# Uncomment if you want to implement real-time streaming chat UI
#
# @chat_router.post("/stream")
# async def stream_message(request: ChatRequest, db: Session = Depends(get_db)):
#     """Stream chatbot response for real-time chat experience"""
#
#     async def generate_stream():
#         try:
#             db_service = DatabaseService(db)
#             conv_service = ConversationService(db_service)
#
#             # Conversation
#             conv_id = await conv_service.get_or_create_conversation(
#                 conversation_id=request.conversation_id, user_id=request.user_id
#             )
#
#             history = await conv_service.get_conversation_history(conv_id, limit=10)
#
#             ai_service = get_or_create_ai_service(
#                 conversation_id=conv_id, session_number=request.session_number
#             )
#
#             # Stream chunks
#             full_response = ""
#             async for chunk in ai_service.stream_response(
#                 request.message, history, request.user_id
#             ):
#                 full_response += chunk
#                 yield ResponseAdapter.streaming_chunk_to_sse(chunk, done=False)
#
#             yield ResponseAdapter.streaming_chunk_to_sse("", done=True)
#
#             # Save messages
#             await conv_service.add_message(
#                 conversation_id=conv_id, role="user", content=request.message
#             )
#
#             await conv_service.add_message(
#                 conversation_id=conv_id,
#                 role="assistant",
#                 content=full_response.strip(),
#             )
#
#         except Exception as e:
#             error_chunk = ResponseAdapter.error_to_api_response(e, 500)
#             yield f"data: {json.dumps(error_chunk)}\n\n"
#
#     return StreamingResponse(
#         generate_stream(),
#         media_type="text/event-stream",
#         headers={
#             "Cache-Control": "no-cache",
#             "Connection": "keep-alive",
#             "X-Accel-Buffering": "no",
#         },
#     )


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
