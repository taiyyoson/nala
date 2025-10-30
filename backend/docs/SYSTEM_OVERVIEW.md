# Nala Health Coach - Complete System Overview

**Full-stack AI-powered health coaching chatbot with RAG (Retrieval-Augmented Generation)**

---

## 🏗️ **System Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND: React Native + Expo                                  │
│  - ChatScreen, ChatOverviewScreen, LoadingScreen               │
│  - ApiService (HTTP client)                                     │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP API
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND API: FastAPI                                           │
│  - Routes (chat.py, health.py)                                  │
│  - Services (AIService, ConversationService, DatabaseService)   │
│  - Adapters (Request/Response formatting)                       │
└─────────┬───────────────────────────┬───────────────────────────┘
          │                           │
    Backend DB                   AI Backend
          │                           │
          ▼                           ▼
┌──────────────────────┐    ┌────────────────────────────────────┐
│  SQLite/PostgreSQL   │    │  RAG System (UnifiedRAGChatbot)    │
│  - conversations     │    │  - rag_dynamic.py                  │
│  - messages          │    │  - query.py (VectorSearch)         │
└──────────────────────┘    └────────────┬───────────────────────┘
                                         │
                                         ▼
                            ┌────────────────────────────────────┐
                            │  Vector DB (PostgreSQL + pgvector) │
                            │  - coaching_conversations (1000+)  │
                            │  - Semantic search via embeddings  │
                            └────────────────────────────────────┘
```

---

## 📂 **Project Structure**

```
nala/
├── frontend/                    # React Native app (Expo)
│   ├── src/
│   │   ├── screens/
│   │   │   ├── ChatScreen.tsx              ✅ Implemented
│   │   │   ├── ChatOverviewScreen.tsx      ✅ Implemented
│   │   │   └── LoadingScreen.tsx           ✅ Implemented
│   │   ├── services/
│   │   │   ├── ApiService.ts               ✅ Implemented
│   │   │   └── StorageService.ts           ✅ Implemented
│   │   └── navigation/
│   └── package.json
│
├── backend/                     # FastAPI backend
│   ├── models/                  # Database models (SQLAlchemy)
│   │   ├── base.py                         ✅ Implemented
│   │   ├── conversation.py                 ✅ Implemented
│   │   └── message.py                      ✅ Implemented
│   ├── services/                # Business logic
│   │   ├── ai_service.py                   📝 Skeleton (needs impl)
│   │   ├── conversation_service.py         📝 Skeleton (needs impl)
│   │   └── database_service.py             📝 Skeleton (needs impl)
│   ├── adapters/                # Data transformations
│   │   ├── request_adapter.py              📝 Skeleton (optional)
│   │   └── response_adapter.py             📝 Skeleton (optional)
│   ├── routes/                  # API endpoints
│   │   ├── chat.py                         ⚠️  Uses mocks (needs update)
│   │   └── health.py                       ✅ Implemented
│   ├── config/                  # Configuration
│   │   ├── settings.py                     ✅ Updated
│   │   ├── database.py                     📝 Skeleton
│   │   └── ai_backend.py                   📝 Skeleton
│   ├── schemas/                 # Pydantic models
│   │   └── chat.py                         📝 Skeleton
│   ├── scripts/                 # Utility scripts
│   │   ├── init_db.py                      📝 Skeleton (needs impl)
│   │   └── test_integration.py             📝 Skeleton
│   ├── docs/                    # Documentation
│   │   ├── E2E_FLOW_GUIDE.md               ✅ Complete
│   │   ├── DATABASE_EVOLUTION.md           ✅ Complete
│   │   ├── INTEGRATION_GUIDE.md            ✅ Complete
│   │   ├── IMPLEMENTATION_STATUS.md        ✅ Complete
│   │   └── database_schema_future.puml     ✅ Complete
│   ├── app.py                              ✅ Implemented
│   ├── dev.py                              ✅ Implemented
│   └── requirements.txt                    ✅ Exists
│
├── AI-backend/                  # RAG system (standalone)
│   ├── rag_dynamic.py                      ✅ Fully implemented
│   ├── query.py                            ✅ Fully implemented
│   ├── chatbot_pipeline.py                 ✅ Fully implemented
│   ├── setup_database.py                   ✅ Fully implemented
│   ├── load_embeddings.py                  ✅ Fully implemented
│   ├── parse_transcripts2.py               ✅ Fully implemented
│   ├── coach_responses.csv                 ✅ 1.2MB data
│   └── transcripts/                        ✅ 58+ files
│
├── .env                                    ✅ Updated with all config
└── README.md
```

---

## 💾 **Database Architecture**

### **Two Separate Databases**

#### **1. Backend Database (Conversation Storage)**
- **Purpose:** Store user chat sessions
- **Tech:** SQLite (dev) / PostgreSQL (prod)
- **Location:** `./nala_conversations.db`

```sql
conversations (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36),
    title VARCHAR(255),
    message_count INTEGER,
    metadata JSON,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

messages (
    id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) REFERENCES conversations(id),
    role VARCHAR(20),  -- "user" | "assistant"
    content TEXT,
    metadata JSON,     -- {model, sources, ...}
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

#### **2. Vector Database (Coaching Knowledge Base)**
- **Purpose:** Store coaching examples for RAG retrieval
- **Tech:** PostgreSQL + pgvector
- **Location:** `localhost:5432/chatbot_db`

```sql
coaching_conversations (
    id SERIAL PRIMARY KEY,
    participant_response TEXT,        -- Example user question
    coach_response TEXT,              -- Example coach answer
    participant_embedding VECTOR(1536), -- For semantic search
    context_category VARCHAR(50),     -- "stress_management"
    goal_type VARCHAR(50),            -- "fitness"
    created_at TIMESTAMP
)
```

**Why two databases?**
- Backend DB: Dynamic, read-write, user data
- Vector DB: Static, read-only, knowledge base

---

## 🔄 **Data Flow**

### **User sends: "I'm feeling stressed"**

```
1. FRONTEND (ChatScreen.tsx)
   └─> ApiService.sendMessage("I'm feeling stressed")

2. BACKEND API (routes/chat.py)
   ├─> ConversationService.get_conversation_history()
   │   └─> DatabaseService.get_messages_by_conversation()
   │       └─> [Backend DB] SELECT * FROM messages WHERE conversation_id=...
   │
   ├─> AIService.generate_response("I'm feeling stressed", history)
   │   └─> UnifiedRAGChatbot.generate_response()
   │       ├─> VectorSearch.search("I'm feeling stressed")
   │       │   └─> [Vector DB] SELECT ... ORDER BY embedding <=> query LIMIT 3
   │       │       Returns: 3 similar coaching examples
   │       │
   │       └─> Claude/GPT API call with examples as context
   │           Returns: "Tell me more about what's causing the stress?"
   │
   ├─> ConversationService.add_message("user", "I'm feeling stressed")
   │   └─> [Backend DB] INSERT INTO messages ...
   │
   └─> ConversationService.add_message("assistant", "Tell me more...")
       └─> [Backend DB] INSERT INTO messages ...

3. RESPONSE
   └─> {
         "response": "Tell me more about what's causing the stress?",
         "conversation_id": "conv_abc123",
         "metadata": {"model": "Claude Sonnet 4", "sources": [...]}
       }

4. FRONTEND
   └─> Display response in chat UI
```

---

## 📚 **Key Documentation**

| Document | Purpose | Location |
|----------|---------|----------|
| **SYSTEM_OVERVIEW.md** | This file - high-level overview | Root |
| **E2E_FLOW_GUIDE.md** | Complete data flow walkthrough | backend/docs/ |
| **IMPLEMENTATION_STATUS.md** | What's done, what needs work | backend/docs/ |
| **INTEGRATION_GUIDE.md** | How to implement integration | backend/ |
| **DATABASE_EVOLUTION.md** | Future database enhancements | backend/docs/ |
| **database_schema_future.puml** | PlantUML diagram for future schema | backend/docs/ |

---

## ⚙️ **Configuration (.env)**

```bash
# LLM API Keys
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...

# Backend Database (User Conversations)
DATABASE_URL=sqlite:///./nala_conversations.db

# Vector Database (Coaching Knowledge)
VECTOR_DB_HOST=localhost
VECTOR_DB_PORT=5432
VECTOR_DB_NAME=chatbot_db
VECTOR_DB_USER=postgres
VECTOR_DB_PASSWORD=nala

# AI Configuration
DEFAULT_LLM_MODEL=claude-sonnet-4
TOP_K_SOURCES=3
MIN_SIMILARITY=0.4

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```

---

## 🚀 **Getting Started**

### **1. Setup AI-Backend (Already Done)**
```bash
cd AI-backend
python3 chatbot_pipeline.py
# ✓ Vector database populated with coaching examples
```

### **2. Setup Backend API (Partially Done)**
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Initialize database (once implemented)
python -m backend.scripts.init_db

# Start API
python dev.py
# Running on http://localhost:8000
```

### **3. Setup Frontend (Already Done)**
```bash
cd frontend
npm install
npm start
# Running on http://localhost:8081
```

---

## ✅ **What's Working**

- ✅ Frontend UI (chat interface, navigation)
- ✅ Backend API structure (FastAPI app, routes)
- ✅ AI-backend RAG system (vector search + LLM)
- ✅ Vector database (1000+ coaching examples)
- ✅ Database models (Conversation, Message)
- ✅ Configuration (settings, environment vars)
- ✅ Comprehensive documentation

---

## ⏳ **What Needs Implementation**

**Critical Path (to make it work end-to-end):**

1. **DatabaseService** (2-3 hours)
   - SQLAlchemy session management
   - CRUD operations for conversations/messages

2. **Database Initialization** (30 min)
   - Create tables using models
   - Run migration script

3. **AIService** (1-2 hours)
   - Import RAG chatbot from AI-backend
   - Implement generate_response method

4. **ConversationService** (2-3 hours)
   - Orchestrate database + AI services
   - Handle conversation logic

5. **Update API Routes** (1 hour)
   - Replace mocks with service calls
   - Add error handling

6. **Testing** (2-3 hours)
   - Test each service independently
   - Test full end-to-end flow
   - Fix bugs

**Total estimated time:** 10-15 hours

---

## 🎯 **Features**

### **Current (MVP)**
- ✅ Real-time chat interface
- ✅ RAG-based responses (retrieves 3 similar coaching examples)
- ✅ Multi-model support (GPT-4o, Claude Sonnet/Opus)
- ✅ Conversation history (once database is connected)
- ✅ Context-aware responses
- ✅ Message metadata (model used, sources)

### **Future (Phase 2-4)**
See [DATABASE_EVOLUTION.md](backend/docs/DATABASE_EVOLUTION.md) for:
- User profiles and personalization
- SMART goal tracking
- Week-based structured program (4 weeks)
- Progress check-ins
- Session summaries
- Engagement analytics

---

## 🛠️ **Technology Stack**

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React Native, Expo, TypeScript | Mobile app |
| **Backend API** | FastAPI, Python 3.x | REST API |
| **Services** | SQLAlchemy, async/await | Business logic |
| **AI Backend** | OpenAI, Anthropic, LangChain | RAG system |
| **Conversation DB** | SQLite (dev), PostgreSQL (prod) | User data |
| **Vector DB** | PostgreSQL + pgvector | Semantic search |
| **Embeddings** | OpenAI text-embedding-3-small (1536-dim) | Vector search |

---

## 📖 **API Endpoints**

### **Current**
```
POST   /api/v1/chat/message          # Send message (using mocks)
POST   /api/v1/chat/stream           # Stream response (using mocks)
GET    /api/v1/chat/conversation/:id # Get conversation (using mocks)
GET    /api/v1/health                # Health check ✅
GET    /api/v1/health/detailed       # Detailed health ✅
GET    /docs                         # API documentation ✅
```

### **Future (once implemented)**
```
GET    /api/v1/chat/conversations    # List user's conversations
POST   /api/v1/chat/conversations    # Create new conversation
DELETE /api/v1/chat/conversation/:id # Delete conversation
PATCH  /api/v1/chat/conversation/:id # Update conversation title
```

---

## 🔍 **Key Concepts**

### **RAG (Retrieval-Augmented Generation)**
1. User asks: "I'm feeling stressed"
2. System generates embedding for query
3. Vector search finds 3 most similar past coaching examples
4. Examples are used as context for LLM
5. LLM generates response in coaching style
6. Response returned to user

### **Two-Database Pattern**
- **Backend DB:** Stores what users are saying (conversations)
- **Vector DB:** Stores what coaches have said before (examples)
- Keeps user data separate from knowledge base
- Enables personalization + RAG simultaneously

### **Service Layer Pattern**
- **Routes:** HTTP handling only
- **Services:** Business logic
- **Adapters:** Data transformation
- **Models:** Database structure
- Clean separation of concerns

---

## 📞 **Support & Resources**

- **API Documentation:** http://localhost:8000/docs (when running)
- **Integration Guide:** `backend/INTEGRATION_GUIDE.md`
- **Implementation Status:** `backend/docs/IMPLEMENTATION_STATUS.md`
- **E2E Flow:** `backend/docs/E2E_FLOW_GUIDE.md`

---

## 🎓 **For New Developers**

**Start here:**
1. Read this file (you are here!)
2. Read `backend/docs/E2E_FLOW_GUIDE.md` - Understand the data flow
3. Read `backend/docs/IMPLEMENTATION_STATUS.md` - See what needs work
4. Follow `backend/INTEGRATION_GUIDE.md` - Step-by-step implementation

**Quick commands:**
```bash
# Start backend
cd backend && python dev.py

# Start frontend
cd frontend && npm start

# Test AI-backend
cd AI-backend && python3 -c "from rag_dynamic import UnifiedRAGChatbot; print('✓ Works')"

# Initialize database (once implemented)
python -m backend.scripts.init_db
```

---

**Last Updated:** 2024-10-13
**Version:** 1.0
**Status:** MVP in progress - Core architecture complete, services need implementation
