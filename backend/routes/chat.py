from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import json
import asyncio
from datetime import datetime

chat_router = APIRouter(prefix="/chat", tags=["chat"])

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    message_id: str
    timestamp: datetime

# In-memory storage for development (replace with database later)
conversations = {}

@chat_router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Send a message to the health coaching chatbot"""
    try:
        # Generate conversation ID if not provided
        conv_id = request.conversation_id or f"conv_{datetime.now().isoformat()}"

        # Store user message
        if conv_id not in conversations:
            conversations[conv_id] = []

        user_message = ChatMessage(
            role="user",
            content=request.message,
            timestamp=datetime.now()
        )
        conversations[conv_id].append(user_message)

        # Mock response for now - replace with Claude API integration
        bot_response = await generate_mock_response(request.message)

        assistant_message = ChatMessage(
            role="assistant",
            content=bot_response,
            timestamp=datetime.now()
        )
        conversations[conv_id].append(assistant_message)

        return ChatResponse(
            response=bot_response,
            conversation_id=conv_id,
            message_id=f"msg_{datetime.now().isoformat()}",
            timestamp=datetime.now()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.post("/stream")
async def stream_message(request: ChatRequest):
    """Stream chatbot response for real-time chat experience"""
    async def generate_stream():
        try:
            # Mock streaming response - replace with actual Claude streaming
            mock_response = await generate_mock_response(request.message)
            words = mock_response.split()

            for i, word in enumerate(words):
                chunk = {
                    "content": word + " ",
                    "done": i == len(words) - 1
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.1)  # Simulate streaming delay

        except Exception as e:
            error_chunk = {"error": str(e), "done": True}
            yield f"data: {json.dumps(error_chunk)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

@chat_router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Retrieve conversation history"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "conversation_id": conversation_id,
        "messages": conversations[conversation_id]
    }

async def generate_mock_response(user_message: str) -> str:
    """Mock response generator - replace with Claude API integration"""
    responses = {
        "hello": "Hi there! I'm your health coach. How can I help you today?",
        "help": "I'm here to support you on your health journey. You can ask me about nutrition, exercise, stress management, or any health goals you'd like to work on.",
        "default": "I understand you're looking for guidance. Can you tell me more about what specific area of your health you'd like to focus on today?"
    }

    message_lower = user_message.lower()
    for key, response in responses.items():
        if key in message_lower:
            return response

    return responses["default"]