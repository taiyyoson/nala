# Backend Integration Guide

This guide explains the architecture and how to implement the integration between the FastAPI backend and the AI-backend RAG system.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React Native)                  │
│                     src/services/ApiService.ts                   │
└─────────────────────────────────────┬───────────────────────────┘
                                      │ HTTP POST /api/v1/chat/message
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI ROUTES (Layer 2)                    │
│                    backend/routes/chat.py                        │
│                    - send_message()                              │
│                    - stream_message()                            │
└─────────────────────────────────────┬───────────────────────────┘
                                      │ Call services
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER (Layer 3)                       │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐│
│  │   AIService     │  │ ConversationSvc  │  │  DatabaseSvc    ││
│  │                 │  │                  │  │                 ││
│  │ - generate_     │  │ - create_conv()  │  │ - save_conv()   ││
│  │   response()    │  │ - add_message()  │  │ - get_messages()││
│  │ - stream_resp() │  │ - get_history()  │  │ - update_conv() ││
│  └─────────────────┘  └──────────────────┘  └─────────────────┘│
└─────────────────────────────────────┬───────────────────────────┘
                                      │ Use adapters
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ADAPTER LAYER (Layer 4)                       │
│  ┌──────────────────────┐         ┌───────────────────────────┐ │
│  │  RequestAdapter      │         │  ResponseAdapter          │ │
│  │  - Format API req    │         │  - Format RAG output      │ │
│  │  - Transform history │         │  - Add metadata           │ │
│  └──────────────────────┘         └───────────────────────────┘ │
└─────────────────────────────────────┬───────────────────────────┘
                                      │ Call RAG system
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI BACKEND (Layer 5)                          │
│                   AI-backend/rag_dynamic.py                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  UnifiedRAGChatbot                                         │ │
│  │  - generate_response(message, history)                     │ │
│  │  - Returns: (response, sources, model_name)                │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────┬───────────────────────────┘
                                      │ Vector search
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              VECTOR DATABASE (Layer 6)                           │
│  PostgreSQL with pgvector - coaching_conversations table         │
│  - 1536-dim embeddings                                           │
│  - Semantic search for coaching examples                         │
└─────────────────────────────────────────────────────────────────┘
```

## Files Created (Skeleton)

### Service Layer
- **`backend/services/ai_service.py`** - Bridge to RAG system
- **`backend/services/conversation_service.py`** - Conversation management
- **`backend/services/database_service.py`** - Data persistence

### Adapter Layer
- **`backend/adapters/request_adapter.py`** - Transform API requests
- **`backend/adapters/response_adapter.py`** - Transform RAG responses

### Database Layer
- **`backend/models/base.py`** - SQLAlchemy base
- **`backend/models/conversation.py`** - Conversation model
- **`backend/models/message.py`** - Message model

### API Schemas
- **`backend/schemas/chat.py`** - Enhanced Pydantic models

### Configuration
- **`backend/config/settings.py`** - Updated with AI config
- **`backend/config/database.py`** - Database connection management
- **`backend/config/ai_backend.py`** - AI-backend integration config

### Scripts
- **`backend/scripts/init_db.py`** - Initialize conversation database
- **`backend/scripts/test_integration.py`** - Integration tests

## Implementation Order

### Phase 1: Database Setup
1. Implement `backend/models/conversation.py` - Define Conversation schema
2. Implement `backend/models/message.py` - Define Message schema
3. Implement `backend/config/database.py` - Database connection
4. Run `python -m backend.scripts.init_db` - Create tables

### Phase 2: Service Layer
5. Implement `backend/services/database_service.py` - CRUD operations
6. Implement `backend/services/ai_service.py` - RAG integration
7. Implement `backend/services/conversation_service.py` - Business logic

### Phase 3: Adapters
8. Implement `backend/adapters/request_adapter.py` - Format requests
9. Implement `backend/adapters/response_adapter.py` - Format responses

### Phase 4: API Integration
10. Modify `backend/routes/chat.py` - Replace mocks with service calls
11. Test with `python -m backend.scripts.test_integration`

### Phase 5: Testing & Deployment
12. Test full flow: Frontend → API → Services → RAG → Response
13. Add error handling and logging
14. Deploy and monitor

## Key Integration Points

### 1. AIService → RAG Chatbot
```python
# In backend/services/ai_service.py
from rag_dynamic import UnifiedRAGChatbot

def __init__(self):
    self.chatbot = UnifiedRAGChatbot(model='claude-sonnet-4', top_k=3)

async def generate_response(self, message, history):
    response, sources, model = self.chatbot.generate_response(
        message,
        use_history=True
    )
    return (response, sources, model)
```

### 2. Routes → Services
```python
# In backend/routes/chat.py
from backend.services import AIService, ConversationService

ai_service = AIService()
conv_service = ConversationService()

@chat_router.post("/message")
async def send_message(request: ChatRequest):
    # Get conversation history
    history = await conv_service.get_conversation_history(request.conversation_id)

    # Generate response using AI
    response, sources, model = await ai_service.generate_response(
        request.message,
        conversation_history=history
    )

    # Save messages
    await conv_service.add_message(request.conversation_id, "user", request.message)
    await conv_service.add_message(request.conversation_id, "assistant", response)

    return ChatResponse(...)
```

### 3. Adapters → Transformations
```python
# Request transformation
ai_input = RequestAdapter.chat_request_to_ai_input(
    message=request.message,
    conversation_history=history
)

# Response transformation
api_response = ResponseAdapter.ai_response_to_chat_response(
    rag_output=(response, sources, model),
    conversation_id=conv_id
)
```

## Environment Variables

Add to `.env`:
```bash
# Conversation Database (separate from vector DB)
DATABASE_URL=sqlite:///./nala_conversations.db

# Vector Database (AI-backend)
VECTOR_DB_HOST=localhost
VECTOR_DB_PORT=5432
VECTOR_DB_NAME=chatbot_db
VECTOR_DB_USER=postgres
VECTOR_DB_PASSWORD=nala

# LLM API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# AI Configuration
DEFAULT_LLM_MODEL=claude-sonnet-4
TOP_K_SOURCES=3
MIN_SIMILARITY=0.4
```

## Testing

### Test Integration
```bash
python -m backend.scripts.test_integration
```

### Test API Endpoint
```bash
# Start backend
python backend/dev.py

# In another terminal
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "I'm feeling stressed"}'
```

## Next Steps

1. **Review** all skeleton files to understand structure
2. **Implement** database models first (models/conversation.py, models/message.py)
3. **Implement** database service (services/database_service.py)
4. **Implement** AI service (services/ai_service.py)
5. **Integrate** into API routes (routes/chat.py)
6. **Test** end-to-end flow

## Notes

- **Two Databases**:
  - Conversation DB (SQLite/PostgreSQL) - stores chat history
  - Vector DB (PostgreSQL + pgvector) - stores coaching examples

- **RAG System**: Already implemented in AI-backend, just need to call it

- **Conversation History**: Store in conversation DB, pass to RAG for context

- **Error Handling**: Add try-catch blocks and proper error responses

- **Streaming**: Can be added later, start with regular responses
