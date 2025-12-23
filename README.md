# Nala Health Coach

> **A 4-week AI-powered health coaching chatbot built with React Native, FastAPI, and RAG (Retrieval-Augmented Generation)**

Nala is an intelligent health coaching assistant designed to guide users through a structured 4-week wellness program. It combines conversational AI with evidence-based coaching techniques, using real coaching transcripts to provide personalized, empathetic support.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Development Setup](#local-development-setup)
  - [Running the App](#running-the-app)
- [Project Structure](#project-structure)
- [Core Components](#core-components)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Testing](#testing)
- [Contributing](#contributing)

---

## Overview

Nala Health Coach provides users with:
- **Structured 4-week coaching program** with weekly unlockable sessions
- **AI-powered conversations** using Claude/GPT models with RAG
- **Personalized guidance** based on user goals and progress
- **Session persistence** across devices with cloud sync
- **Accessibility features** including adjustable text sizes

The app is designed for research and wellness coaching, with a focus on stress management, habit building, and goal achievement.

---

## Features

### 🎯 Core Features

#### **4-Week Coaching Program**
- **Week 1:** Getting to know you - Initial assessment and goal setting
- **Week 2:** Building habits - Establishing sustainable routines
- **Week 3:** Overcoming challenges - Problem-solving and resilience
- **Week 4:** Reviewing progress - Reflection and planning ahead

#### **Session Management**
- ✅ **Progressive unlock system** - Sessions unlock 7 days after completing the previous one
- ✅ **Session completion tracking** - Backend stores progress with timestamps
- ✅ **Locked chat prevention** - Cannot re-open completed sessions
- ✅ **Visual progress indicators** - Color-coded cards (locked/unlocked/completed)

#### **AI-Powered Conversations**
- 🤖 **RAG (Retrieval-Augmented Generation)** - Uses vector search on real coaching transcripts
- 🧠 **Contextual responses** - Maintains conversation history throughout session
- 📚 **Evidence-based coaching** - Responses grounded in actual coaching examples
- 🔄 **Multi-model support** - Works with Claude Sonnet 4, GPT-4, and other LLMs

#### **User Experience**
- 🎨 **Modern, accessible UI** - Clean design with green wellness theme
- 📱 **Cross-platform** - Works on iOS, Android, and web
- 🔤 **Adjustable text sizes** - Small/Medium/Large options for accessibility
- 🔐 **Secure authentication** - Firebase Auth with email/password
- 💾 **Persistent state** - Progress saved to backend database

#### **Support Resources**
- 📧 **Contact support** - Direct email link to chatbot.nala@gmail.com
- 🆘 **Crisis resources** - Quick access to crisis hotlines (988, USF Counseling)
- ⚙️ **Settings management** - Password reset, text size, logout

---

## Architecture

### System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    FRONTEND (React Native)                   │
│                                                              │
│  ├─ Screens: Chat, ChatOverview, Settings, Onboarding       │
│  ├─ Contexts: AuthContext, TextSizeContext                  │
│  ├─ Services: ApiService (HTTP client)                      │
│  └─ Navigation: MainStack, AuthStack                        │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTPS
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                  BACKEND API (FastAPI)                       │
│                                                              │
│  ├─ Routes: /chat, /session, /user, /health                 │
│  ├─ Services: RAGService, ConversationService, DBService    │
│  └─ Models: User, SessionProgress, Conversation, Message    │
└───────────────────────────┬──────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
    ┌─────────────┐  ┌──────────┐  ┌──────────────┐
    │   SQLite    │  │ AI-Backend│  │   Firebase   │
    │  (Convos)   │  │   (RAG)   │  │    (Auth)    │
    └─────────────┘  └──────────┘  └──────────────┘
                          │
                          ▼
                ┌──────────────────┐
                │ PostgreSQL +     │
                │ pgvector (RAG)   │
                └──────────────────┘
```

### Data Flow

1. **User sends message** → Frontend (ChatScreen)
2. **API call** → Backend `/api/v1/chat/message`
3. **RAG retrieval** → AI-backend searches vector DB for relevant coaching examples
4. **LLM generation** → Claude/GPT generates response with context
5. **Save to DB** → Backend stores conversation in SQLite
6. **Return response** → Frontend displays message

📖 **For detailed architecture documentation, see:** [backend/docs/E2E_FLOW_GUIDE.md](backend/docs/E2E_FLOW_GUIDE.md)

---

## Tech Stack

### Frontend
- **React Native** 0.81.4 - Cross-platform mobile framework
- **Expo** ~54.0 - Development platform
- **TypeScript** ~5.9.2 - Type safety
- **React Navigation** 7.x - Navigation library
- **Firebase** 12.4.0 - Authentication
- **Lucide React Native** - Icon library

### Backend
- **FastAPI** - High-performance Python web framework
- **SQLAlchemy** - ORM for database operations
- **SQLite** - Local conversation storage
- **PostgreSQL + pgvector** - Vector database for RAG
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server

### AI/ML
- **OpenAI API** - GPT models and text embeddings
- **Anthropic API** - Claude models
- **pgvector** - PostgreSQL extension for vector similarity search
- **Custom RAG pipeline** - Retrieval-augmented generation system

### DevOps
- **Render** - Backend hosting
- **Expo Go** - Mobile app preview
- **Git** - Version control
- **pytest** - Backend testing

---

## Getting Started

### Prerequisites

Before running this project, ensure you have:

```bash
# Node.js and npm
node -v  # v18+ recommended
npm -v   # v9+ recommended

# Python
python --version  # 3.9+ required

# Expo CLI
npm install -g expo-cli

# PostgreSQL (for vector database)
psql --version  # 14+ recommended
```

### Local Development Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/nala.git
cd nala
```

#### 2. Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
# Backend API
API_HOST=127.0.0.1
API_PORT=8000
DEBUG=true

# Conversation Database (SQLite)
CONVERSATION_DATABASE_URL=sqlite:///./nala_conversations.db

# Vector Database (PostgreSQL + pgvector)
VECTOR_DB_HOST=localhost
VECTOR_DB_PORT=5432
VECTOR_DB_NAME=chatbot_db
VECTOR_DB_USER=postgres
VECTOR_DB_PASSWORD=your_password

# AI APIs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# LLM Configuration
DEFAULT_LLM_MODEL=claude-sonnet-4
TOP_K_SOURCES=3
MIN_SIMILARITY=0.4

# Firebase (get from Firebase Console)
FIREBASE_API_KEY=...
FIREBASE_AUTH_DOMAIN=...
FIREBASE_PROJECT_ID=...
```

#### 3. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/init_db.py

# Run backend server
python dev.py
```

Backend will be available at `http://127.0.0.1:8000`

#### 4. Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start Expo development server
npm start
```

#### 5. AI-Backend Setup (Vector Database)

```bash
# Navigate to AI-backend
cd AI-backend

# Install dependencies
pip install -r requirements.txt

# Initialize PostgreSQL database with pgvector
psql -U postgres -d chatbot_db < schema.sql

# Populate vector database with coaching transcripts
python populate_vector_db.py
```

---

## Running the App

### Development Mode

### Local Backend

1. **Start backend:** `cd backend && python dev.py`
2. **Start frontend:** `cd frontend && npm start`
3. **Open in Expo Go:**
   - Webapp: press i to set up IOS simulator via X-Code
   - iOS: Scan QR code with Camera app
   - Android: Scan QR code with Expo Go app

#### Option 2: Deployed Backend

In `frontend/src/services/ApiService.ts`:
```typescript
const USE_DEPLOYED = true; // Set to true
```

Then run: `cd frontend && npm start`

---

## Project Structure

```
nala/
├── frontend/                    # React Native mobile app
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   │   └── onboarding/      # Onboarding flow components
│   │   ├── contexts/            # React contexts (Auth, TextSize)
│   │   ├── navigation/          # Navigation stacks
│   │   ├── screens/             # Main app screens
│   │   │   ├── ChatScreen.tsx           # Weekly coaching chat
│   │   │   ├── ChatOverviewScreen.tsx   # 4-week overview
│   │   │   ├── Settings.tsx             # User settings
│   │   │   ├── LoginScreen.tsx          # Authentication
│   │   │   └── OnboardingScreen.tsx     # First-time setup
│   │   ├── services/            # API clients
│   │   │   └── ApiService.ts            # Backend HTTP client
│   │   └── config/              # Firebase config
│   ├── app.json                 # Expo configuration
│   └── package.json             # Dependencies
│
├── backend/                     # FastAPI server
│   ├── routes/                  # API endpoints
│   │   ├── chat.py              # Chat message handling
│   │   ├── session.py           # Session progress tracking
│   │   ├── user.py              # User management
│   │   └── health.py            # Health check endpoint
│   ├── services/                # Business logic
│   │   ├── rag_service.py       # RAG chatbot wrapper
│   │   ├── conversation_service.py  # Conversation management
│   │   └── database_service.py  # Database operations
│   ├── models/                  # SQLAlchemy models
│   │   ├── user.py              # User model
│   │   ├── session_progress.py  # Session progress tracking
│   │   ├── conversation.py      # Conversation metadata
│   │   └── message.py           # Chat messages
│   ├── config/                  # Configuration
│   │   ├── settings.py          # Environment settings
│   │   ├── database.py          # Database connection
│   │   └── firebase_config.py   # Firebase Admin SDK
│   ├── app.py                   # FastAPI app entry point
│   └── requirements.txt         # Python dependencies
│
├── AI-backend/                  # RAG system
│   ├── rag_dynamic.py           # Main RAG chatbot class
│   ├── query.py                 # Vector search utilities
│   ├── chatbot_pipeline.py      # Setup pipeline
│   └── utils/
│       └── database.py          # Session data utilities
│
└── docs/                        # Documentation
    ├── E2E_FLOW_GUIDE.md        # End-to-end architecture
    └── INTEGRATION_GUIDE.md     # Integration steps
```

---

## Core Components

### Frontend Components

#### **ChatScreen.tsx**
The main conversation interface for weekly coaching sessions.

**Key Features:**
- Real-time chat with typing indicators
- Message history with user/assistant bubbles
- Session completion detection and locking
- Dynamic text sizing based on user settings
- Automatic navigation after session completion

**State Management:**
```typescript
const [messages, setMessages] = useState<Message[]>([]);
const [sessionComplete, setSessionComplete] = useState(false);
const [conversationId, setConversationId] = useState<string>("");
```

**API Integration:**
```typescript
// Send message to backend
await fetch(`${API_BASE}/chat/message`, {
  method: "POST",
  body: JSON.stringify({
    message: text,
    user_id: userId,
    conversation_id: conversationId,
    session_number: week
  })
});
```

📖 **See:** [docs/CHAT_SCREEN.md](docs/CHAT_SCREEN.md) for detailed documentation

---

#### **ChatOverviewScreen.tsx**
Visual dashboard showing all 4 weeks of the coaching program.

**Key Features:**
- Color-coded session cards:
  - **Gray:** Locked (not yet accessible)
  - **Pink (#BF5F83):** Unlocked (ready to start)
  - **Green (#4A8B6F):** Completed
- Unlock countdown timers
- Session completion status
- Progress tracking across weeks

**Unlock Logic:**
```typescript
const isSessionUnlocked = (sessionNumber: number): boolean => {
  if (sessionNumber === 1) return true; // Week 1 always unlocked

  const current = progress.find(p => p.session_number === sessionNumber);
  if (current?.unlocked_at) {
    return new Date() >= new Date(current.unlocked_at);
  }

  // Otherwise check if previous session is complete
  const prev = progress.find(p => p.session_number === sessionNumber - 1);
  return !!prev?.completed_at;
};
```

📖 **See:** [docs/SESSION_MANAGEMENT.md](docs/SESSION_MANAGEMENT.md)

---

#### **Settings.tsx**
User settings and support resources.

**Features:**
- Text size adjustment (Small/Medium/Large)
- Password reset via Firebase
- Contact support (email link)
- Crisis resources with hotline numbers
- Logout functionality

**Text Size Context:**
```typescript
const { size, setSize } = useTextSize();
// size can be "small" | "medium" | "large"
```

---

### Backend Services

#### **RAGService** (`services/rag_service.py`)
Wrapper around the AI-backend RAG system.

**Purpose:**
- Initialize RAG chatbot with proper configuration
- Manage conversation history
- Generate AI responses with retrieval augmentation

**Key Methods:**
```python
async def generate_response(
    self,
    user_message: str,
    conversation_history: list[dict],
    session_number: int
) -> tuple[str, list, str]:
    """
    Generate AI response using RAG.

    Returns:
        (response_text, source_documents, model_name)
    """
```

---

#### **ConversationService** (`services/conversation_service.py`)
Manages conversation lifecycle and message storage.

**Responsibilities:**
- Create new conversations
- Add messages to conversations
- Retrieve conversation history
- Format data for AI service

---

#### **DatabaseService** (`services/database_service.py`)
Low-level database operations using SQLAlchemy.

**Operations:**
- CRUD for users, conversations, messages, session progress
- Query optimization
- Transaction management

---

### AI-Backend (RAG System)

#### **UnifiedRAGChatbot** (`AI-backend/rag_dynamic.py`)
Core RAG implementation with vector search.

**Pipeline:**
1. **Embed user query** using OpenAI embeddings
2. **Vector search** in PostgreSQL to find similar coaching examples
3. **Build context** from retrieved examples
4. **Generate response** using Claude/GPT with context
5. **Update conversation history**

**Vector Search:**
```python
# Find top 3 similar coaching examples
results = cursor.execute("""
    SELECT
        participant_response,
        coach_response,
        1 - (participant_embedding <=> %s::vector) as similarity
    FROM coaching_conversations
    WHERE 1 - (participant_embedding <=> %s::vector) >= 0.4
    ORDER BY participant_embedding <=> %s::vector
    LIMIT 3
""", [query_embedding, query_embedding, query_embedding])
```

---

## API Documentation

### Base URL

- **Local:** `http://127.0.0.1:8000/api/v1`
- **Production:** `https://nala-backend-serv.onrender.com/api/v1`

### Interactive Docs

FastAPI provides auto-generated API documentation:
- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

### Key Endpoints

#### **POST /chat/message**
Send a message and get AI response.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I am feeling stressed",
    "user_id": "user_123",
    "session_number": 1,
    "conversation_id": "conv_abc"
  }'
```

**Response:**
```json
{
  "response": "I hear you. Tell me more about what's causing the stress?",
  "conversation_id": "conv_abc123",
  "session_complete": false,
  "metadata": {
    "model": "claude-sonnet-4",
    "source_count": 3
  }
}
```

---

#### **POST /session/complete**
Mark a session as complete and unlock the next one.

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/session/complete?user_id=user_123&session_number=1"
```

**Response:**
```json
{
  "message": "Session marked complete",
  "completed_session": {
    "session_number": 1,
    "completed_at": "2024-12-03T10:30:00Z"
  },
  "next_session": {
    "session_number": 2,
    "unlocked_at": "2024-12-10T10:30:00Z"
  }
}
```

---

#### **GET /session/progress/{user_id}**
Get all session progress for a user.

```bash
curl http://127.0.0.1:8000/api/v1/session/progress/user_123
```

**Response:**
```json
[
  {
    "session_number": 1,
    "completed_at": "2024-12-03T10:30:00Z",
    "unlocked_at": "2024-12-01T00:00:00Z"
  },
  {
    "session_number": 2,
    "completed_at": null,
    "unlocked_at": "2024-12-10T10:30:00Z"
  }
]
```

---

#### **POST /user/onboarding**
Mark user onboarding as complete.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/user/onboarding \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "onboarding_completed": true
  }'
```

---

#### **GET /health**
Check API health status.

```bash
curl http://127.0.0.1:8000/api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "ai_backend": "ready"
}
```

---

## Deployment

### Backend Deployment (Render)

The backend is deployed on Render using `render.yaml`:

```yaml
services:
  - type: web
    name: nala-backend
    env: python
    buildCommand: "pip install -r backend/requirements.txt"
    startCommand: "python backend/app.py"
    envVars:
      - key: OPENAI_API_KEY
        sync: false
      - key: ANTHROPIC_API_KEY
        sync: false
```

**Deployment URL:** https://nala-backend-serv.onrender.com

**Deploy Steps:**
1. Push to GitHub main branch
2. Render auto-deploys from GitHub
3. Verify at: https://nala-backend-serv.onrender.com/health

---

### Frontend Deployment (Expo)

#### Publish to Expo

```bash
# Install EAS CLI
npm install -g eas-cli

eas login
eas whoami

eas deploy
eas deploy --prod
```

This creates a shareable link: `exp://exp.host/@username/frontend`

#### Build Standalone Apps

```bash
# Install EAS CLI
npm install -g eas-cli

# Configure EAS
eas build:configure

# Build for iOS
eas build --platform ios

# Build for Android
eas build --platform android
```

---

## Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v
```

**Test Coverage:**
- API endpoint tests
- Database operations
- RAG service integration
- Authentication flows
- Covered in Github Actions, CI/CD Pipeline

### Frontend Testing

```bash
cd frontend
npm test
```


## Support & Contact

- **Email:** chatbot.nala@gmail.com

