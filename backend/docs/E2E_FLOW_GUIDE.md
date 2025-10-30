# End-to-End Flow Guide: Frontend → Backend → AI-Backend → Response

Complete guide for understanding and implementing the full data flow in the Nala Health Coach application.

---

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Database Design](#database-design)
3. [Data Flow Walkthrough](#data-flow-walkthrough)
4. [Component Responsibilities](#component-responsibilities)
5. [Implementation Status](#implementation-status)
6. [Quick Reference](#quick-reference)

---

## System Architecture Overview

### **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React Native + Expo)                   │
│                                                                      │
│  Screens:                        Services:                          │
│  - ChatScreen.tsx                - ApiService.ts                    │
│  - ChatOverviewScreen.tsx        - StorageService.ts                │
│  - LoadingScreen.tsx                                                │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                    HTTP POST /api/v1/chat/message
                    {message, conversation_id, user_id}
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  BACKEND API (FastAPI - Layer 2)                    │
│                                                                      │
│  Routes:              Config:             Middleware:               │
│  - routes/chat.py     - settings.py       - CORS                    │
│  - routes/health.py   - database.py                                 │
│                       - ai_backend.py                               │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
┌──────────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│  ConversationService │ │   AIService     │ │  DatabaseService    │
│  (Layer 3)           │ │   (Layer 3)     │ │  (Layer 3)          │
│                      │ │                 │ │                     │
│ - create_conv()      │ │ - generate_     │ │ - save_conv()       │
│ - add_message()      │ │   response()    │ │ - get_messages()    │
│ - get_history()      │ │ - stream_resp() │ │ - update_conv()     │
└──────────┬───────────┘ └────────┬────────┘ └──────────┬──────────┘
           │                      │                      │
           │     ┌────────────────┘                      │
           │     │                                       │
           │     │  ┌────────────────────────────────────┘
           │     │  │
           │     ▼  ▼
           │  ┌─────────────────────────────────────────┐
           │  │    ADAPTER LAYER (Layer 4)              │
           │  │                                         │
           │  │  RequestAdapter    ResponseAdapter     │
           │  │  - Format API req  - Format RAG output │
           │  │  - Transform hist  - Add metadata      │
           │  └─────────────────┬───────────────────────┘
           │                    │
           │                    │
           ▼                    ▼
┌──────────────────────┐ ┌────────────────────────────────────────┐
│  BACKEND DATABASE    │ │    AI BACKEND (Layer 5)                │
│  (SQLite/PostgreSQL) │ │                                        │
│                      │ │  UnifiedRAGChatbot                     │
│  Tables:             │ │  - rag_dynamic.py                      │
│  - conversations     │ │  - query.py (VectorSearch)             │
│  - messages          │ │  - chatbot_pipeline.py                 │
└──────────────────────┘ └─────────────────┬──────────────────────┘
                                            │
                                            │ Vector Search
                                            │
                                            ▼
                         ┌────────────────────────────────────────┐
                         │  VECTOR DATABASE (Layer 6)             │
                         │  PostgreSQL + pgvector                 │
                         │                                        │
                         │  Table: coaching_conversations         │
                         │  - participant_response                │
                         │  - coach_response                      │
                         │  - participant_embedding (1536-dim)    │
                         │  - context_category, goal_type         │
                         └────────────────────────────────────────┘
```

---

## Database Design

### **Two Separate Databases**

#### **Database 1: Backend Database (Conversation Storage)**

**Purpose:** Store user chat sessions and message history
**Technology:** SQLite (dev) / PostgreSQL (prod)
**Location:** `./nala_conversations.db`

**Tables:**

```sql
-- Conversation metadata
CREATE TABLE conversations (
    id VARCHAR(36) PRIMARY KEY,           -- "conv_abc123"
    user_id VARCHAR(36),                  -- Firebase UID (nullable)
    title VARCHAR(255),                   -- "Week 1 Coaching"
    message_count INTEGER DEFAULT 0,      -- Cached count
    metadata JSON,                         -- Flexible storage
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_conv_user ON conversations(user_id);
CREATE INDEX idx_conv_updated ON conversations(updated_at DESC);

-- Individual messages
CREATE TABLE messages (
    id VARCHAR(36) PRIMARY KEY,           -- "msg_def456"
    conversation_id VARCHAR(36) NOT NULL, -- FK to conversations
    role VARCHAR(20) NOT NULL,            -- "user" | "assistant" | "system"
    content TEXT NOT NULL,                -- Message text
    metadata JSON,                         -- Model, sources, etc.
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,

    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX idx_msg_conv ON messages(conversation_id);
CREATE INDEX idx_msg_created ON messages(conversation_id, created_at);
```

**Relationship:** One conversation → Many messages (CASCADE DELETE)

---

#### **Database 2: Vector Database (Coaching Knowledge Base)**

**Purpose:** Store pre-parsed coaching examples for RAG retrieval
**Technology:** PostgreSQL + pgvector
**Location:** `localhost:5432/chatbot_db`

**Table:**

```sql
CREATE TABLE coaching_conversations (
    id SERIAL PRIMARY KEY,
    participant_response TEXT NOT NULL,    -- Example user question
    coach_response TEXT NOT NULL,          -- Example coach answer
    context_category VARCHAR(50),          -- "stress_management"
    goal_type VARCHAR(50),                 -- "fitness"
    confidence_level INTEGER,
    keywords TEXT,
    source_file TEXT,
    participant_embedding VECTOR(1536),    -- For semantic search
    coach_embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX participant_embedding_idx
ON coaching_conversations
USING ivfflat (participant_embedding vector_cosine_ops);
```

**Access Pattern:** Read-only (search only, no writes during chat)

---

### **Why Two Databases?**

| Aspect | Backend DB | Vector DB |
|--------|-----------|-----------|
| **Purpose** | User chat storage | Coaching knowledge base |
| **Data** | Live conversations | Pre-parsed examples |
| **Operations** | Read/Write | Read-only (search) |
| **Updates** | Every message | Rarely (new transcripts) |
| **User Association** | Yes (user_id) | No |
| **Vector Search** | No | Yes (semantic search) |

---

## Data Flow Walkthrough

### **Step-by-Step: User Sends "I'm feeling stressed"**

#### **1. Frontend: User Input**

**File:** `frontend/src/screens/ChatScreen.tsx`

```typescript
const handleSendMessage = async (messageText: string) => {
  const response = await ApiService.sendMessage(messageText);
  // Display response in chat UI
};
```

**API Call:**
```typescript
// frontend/src/services/ApiService.ts
POST http://localhost:8000/api/v1/chat/message
{
  "message": "I'm feeling stressed",
  "conversation_id": "conv_abc123",
  "user_id": "user_xyz789"
}
```

---

#### **2. Backend API: Route Handler**

**File:** `backend/routes/chat.py`

```python
@chat_router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    # 1. Get conversation history from Backend DB
    history = await conversation_service.get_conversation_history(
        conversation_id=request.conversation_id
    )

    # 2. Generate AI response using RAG
    response, sources, model = await ai_service.generate_response(
        message=request.message,
        conversation_history=history,
        user_id=request.user_id
    )

    # 3. Save user message to Backend DB
    await conversation_service.add_message(
        conversation_id=request.conversation_id,
        role="user",
        content=request.message
    )

    # 4. Save assistant response to Backend DB
    await conversation_service.add_message(
        conversation_id=request.conversation_id,
        role="assistant",
        content=response,
        metadata={"model": model, "sources": sources}
    )

    # 5. Return formatted response
    return ChatResponse(
        response=response,
        conversation_id=request.conversation_id,
        message_id="msg_" + uuid.uuid4().hex,
        timestamp=datetime.now()
    )
```

---

#### **3. Service Layer: Business Logic**

**File:** `backend/services/conversation_service.py`

```python
class ConversationService:
    async def get_conversation_history(self, conversation_id: str):
        # Query Backend DB for past messages
        messages = await db_service.get_messages_by_conversation(conversation_id)

        # Format for AI service: [{"role": "user", "content": "..."}]
        return RequestAdapter.format_conversation_history(messages)
```

**File:** `backend/services/ai_service.py`

```python
class AIService:
    async def generate_response(self, message, conversation_history, user_id):
        # 1. Set conversation history in RAG chatbot
        self.chatbot.conversation_history = conversation_history

        # 2. Generate response (this calls Vector DB internally)
        response, sources, model = self.chatbot.generate_response(
            user_message=message,
            use_history=True
        )

        # 3. Return structured output
        return (response, sources, model)
```

---

#### **4. AI Backend: RAG Processing**

**File:** `AI-backend/rag_dynamic.py`

```python
class UnifiedRAGChatbot:
    def generate_response(self, user_message, use_history=True):
        # 1. Vector search in Vector DB
        retrieved_examples = self.retrieve(user_message)
        # Calls: AI-backend/query.py → VectorSearch.search()
        # Returns: 3 most similar coaching examples

        # 2. Build context from examples
        context = self.build_context(retrieved_examples)
        # Example: "Here are relevant coaching examples:
        #           Participant: feeling overwhelmed
        #           Coach: Tell me more about..."

        # 3. Build system prompt
        system_prompt = self.get_system_prompt(context)

        # 4. Generate response with LLM (Claude/GPT)
        if self.model_info['provider'] == 'anthropic':
            response = self.generate_with_anthropic(user_message, system_prompt)
        else:
            response = self.generate_with_openai(user_message, system_prompt)

        # 5. Update conversation history
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": response})

        # 6. Return tuple
        return (response, retrieved_examples, self.model_info['name'])
```

---

#### **5. Vector Database: Semantic Search**

**File:** `AI-backend/query.py`

```python
class VectorSearch:
    def search(self, query, limit=3, min_similarity=0.4):
        # 1. Generate embedding for user query
        query_embedding = openai.embeddings.create(
            model="text-embedding-3-small",
            input=query  # "I'm feeling stressed"
        ).data[0].embedding  # 1536-dimensional vector

        # 2. Vector similarity search in PostgreSQL
        results = cursor.execute("""
            SELECT
                participant_response,
                coach_response,
                context_category,
                goal_type,
                1 - (participant_embedding <=> %s::vector) as similarity
            FROM coaching_conversations
            WHERE 1 - (participant_embedding <=> %s::vector) >= %s
            ORDER BY participant_embedding <=> %s::vector
            LIMIT %s
        """, [query_embedding, query_embedding, min_similarity,
              query_embedding, limit])

        # 3. Return top 3 similar examples
        return results.fetchall()
        # Example results:
        # [
        #   ("feeling overwhelmed", "Tell me more...", "stress", "wellbeing", 0.85),
        #   ("so stressed", "What's causing it?", "stress", "work", 0.78),
        #   ("anxious about work", "Let's break it down", "anxiety", "work", 0.72)
        # ]
```

---

#### **6. Backend Database: Save Messages**

**File:** `backend/services/database_service.py`

```python
class DatabaseService:
    async def create_message(self, message_data):
        # Insert user message
        cursor.execute("""
            INSERT INTO messages (id, conversation_id, role, content, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            "msg_001",
            "conv_abc123",
            "user",
            "I'm feeling stressed",
            {},
            datetime.now()
        ])

        # Insert assistant message
        cursor.execute("""
            INSERT INTO messages (id, conversation_id, role, content, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            "msg_002",
            "conv_abc123",
            "assistant",
            "I hear you. Tell me more about what's causing the stress?",
            {"model": "Claude Sonnet 4", "sources": [...]},
            datetime.now()
        ])

        # Update conversation
        cursor.execute("""
            UPDATE conversations
            SET message_count = message_count + 2, updated_at = ?
            WHERE id = ?
        """, [datetime.now(), "conv_abc123"])
```

---

#### **7. Response: Back to Frontend**

**Response JSON:**
```json
{
  "response": "I hear you. Tell me more about what's causing the stress?",
  "conversation_id": "conv_abc123",
  "message_id": "msg_002",
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
```

**Frontend displays:**
```
User: I'm feeling stressed
Coach: I hear you. Tell me more about what's causing the stress?
```

---

## Component Responsibilities

### **Layer 1: Frontend (React Native)**

**Responsibilities:**
- ✅ User interface and input handling
- ✅ Display chat messages
- ✅ Call backend API
- ✅ Local storage (chat cache)
- ❌ NO business logic
- ❌ NO direct database access

**Key Files:**
- `frontend/src/screens/ChatScreen.tsx` - Chat UI
- `frontend/src/services/ApiService.ts` - HTTP client

---

### **Layer 2: Backend API (FastAPI)**

**Responsibilities:**
- ✅ HTTP request handling
- ✅ Request validation (Pydantic)
- ✅ Route logic
- ✅ CORS configuration
- ❌ NO business logic (delegate to services)
- ❌ NO direct AI calls (delegate to AIService)

**Key Files:**
- `backend/routes/chat.py` - API endpoints
- `backend/app.py` - FastAPI app setup

---

### **Layer 3: Service Layer**

#### **AIService**
**Responsibilities:**
- ✅ Initialize RAG chatbot
- ✅ Call RAG system for responses
- ✅ Handle model selection
- ❌ NO database writes

**Key File:** `backend/services/ai_service.py`

#### **ConversationService**
**Responsibilities:**
- ✅ Manage conversation lifecycle
- ✅ Add messages to conversations
- ✅ Format conversation history
- ✅ Orchestrate database + AI calls

**Key File:** `backend/services/conversation_service.py`

#### **DatabaseService**
**Responsibilities:**
- ✅ CRUD operations on Backend DB
- ✅ SQL queries
- ✅ Connection management
- ❌ NO business logic

**Key File:** `backend/services/database_service.py`

---

### **Layer 4: Adapter Layer**

**Responsibilities:**
- ✅ Transform API requests → Service format
- ✅ Transform RAG output → API responses
- ✅ Format conversation history
- ❌ NO business logic

**Key Files:**
- `backend/adapters/request_adapter.py`
- `backend/adapters/response_adapter.py`

---

### **Layer 5: AI Backend (RAG System)**

**Responsibilities:**
- ✅ Vector search in coaching examples
- ✅ Generate embeddings
- ✅ Call LLM APIs (OpenAI/Anthropic)
- ✅ Manage conversation context
- ❌ NO user data persistence

**Key Files:**
- `AI-backend/rag_dynamic.py` - RAG chatbot
- `AI-backend/query.py` - Vector search
- `AI-backend/chatbot_pipeline.py` - Setup pipeline

---

### **Layer 6: Databases**

#### **Backend Database (SQLite/PostgreSQL)**
- ✅ Store conversations
- ✅ Store messages
- ✅ User associations

#### **Vector Database (PostgreSQL + pgvector)**
- ✅ Store coaching examples
- ✅ Vector embeddings
- ✅ Semantic search

---

## Implementation Status

### **✅ Already Implemented**

| Component | Status | Location |
|-----------|--------|----------|
| Frontend UI | ✅ Complete | `frontend/src/` |
| API Routes (mock) | ✅ Complete | `backend/routes/` |
| RAG Chatbot | ✅ Complete | `AI-backend/rag_dynamic.py` |
| Vector Search | ✅ Complete | `AI-backend/query.py` |
| Vector Database | ✅ Populated | PostgreSQL `chatbot_db` |
| FastAPI Setup | ✅ Complete | `backend/app.py` |

### **📝 Skeleton Created (Need Implementation)**

| Component | Status | Location |
|-----------|--------|----------|
| Database Models | 📝 Skeleton | `backend/models/` |
| Service Layer | 📝 Skeleton | `backend/services/` |
| Adapters | 📝 Skeleton | `backend/adapters/` |
| Database Config | 📝 Skeleton | `backend/config/database.py` |
| API Schemas | 📝 Skeleton | `backend/schemas/` |

### **❌ Not Yet Started**

| Component | Status | What's Needed |
|-----------|--------|---------------|
| Backend DB Tables | ❌ Not created | Run `init_db.py` |
| Route Integration | ❌ Using mocks | Replace with service calls |
| Integration Tests | ❌ Empty | Implement test suite |

---

## Quick Reference

### **Environment Variables**

```bash
# .env file
# Conversation Database
DATABASE_URL=sqlite:///./nala_conversations.db

# Vector Database (AI-backend)
VECTOR_DB_HOST=localhost
VECTOR_DB_PORT=5432
VECTOR_DB_NAME=chatbot_db
VECTOR_DB_USER=postgres
VECTOR_DB_PASSWORD=nala

# LLM APIs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# AI Configuration
DEFAULT_LLM_MODEL=claude-sonnet-4
TOP_K_SOURCES=3
MIN_SIMILARITY=0.4
```

### **Key Commands**

```bash
# Initialize Backend Database
python -m backend.scripts.init_db

# Test Integration
python -m backend.scripts.test_integration

# Start Backend API
python backend/dev.py

# Start Frontend
cd frontend && npm start
```

### **Important Paths**

| What | Path |
|------|------|
| Backend DB | `./nala_conversations.db` |
| Vector DB | `localhost:5432/chatbot_db` |
| API Base URL | `http://localhost:8000/api/v1` |
| API Docs | `http://localhost:8000/docs` |
| Frontend | `http://localhost:8081` |

---

## Next Steps

1. ✅ Review this guide
2. ⏭️ Implement database models
3. ⏭️ Implement service layer
4. ⏭️ Update API routes
5. ⏭️ Test end-to-end flow

See [`INTEGRATION_GUIDE.md`](./INTEGRATION_GUIDE.md) for detailed implementation steps.

---

**Last Updated:** 2024-10-13
**Version:** 1.0
