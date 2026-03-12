# Nala Health Coach

A 4-week AI-powered health coaching chatbot built with React Native, FastAPI, and RAG (Retrieval-Augmented Generation). Nala is based on real interactions from the Examen Tu Salud program, using coaching transcripts to provide personalized, evidence-based wellness support powered by Claude Sonnet 4.5.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React Native 0.81.4, Expo ~54.0, TypeScript ~5.9.2 |
| Navigation | React Navigation 7.x (Native Stack) |
| Auth | Firebase Authentication 12.4.0 (email/password) |
| Backend API | FastAPI (Python, async) |
| Conversation DB | PostgreSQL (Render) |
| Vector DB | PostgreSQL + pgvector (Render, Basic tier) |
| AI/LLM | Anthropic Claude Sonnet 4.5 (primary), OpenAI GPT-4o-mini (fallback) |
| Embeddings | OpenAI text-embedding-3-small (1536-dim) |
| Hosting | Render (backend), Expo Publish (frontend) |

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  FRONTEND (React Native + Expo)               │
│                                                               │
│  Screens: Chat, ChatOverview, Settings, Onboarding           │
│  Contexts: AuthContext, TextSizeContext                       │
│  Services: ApiService (HTTP client)                          │
│  Navigation: AuthStack, MainStack, AppNavigator              │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTPS
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    BACKEND API (FastAPI)                      │
│                                                               │
│  Routes: /chat, /session, /user, /health                     │
│  Services: AIService, ConversationService, DatabaseService   │
│  Models: Conversation, Message, SessionProgress, User        │
└───────────────────────────┬──────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
    ┌─────────────┐  ┌──────────┐  ┌──────────────┐
    │ Conversation │  │    AI    │  │   Firebase   │
    │  History DB  │  │  Backend │  │    (Auth)    │
    │ (PostgreSQL) │  │  (RAG)   │  └──────────────┘
    └─────────────┘  └────┬─────┘
                          │
                          ▼
                ┌──────────────────┐
                │ Transcript DB    │
                │ PostgreSQL +     │
                │ pgvector (RAG)   │
                └──────────────────┘
```

## Getting Started

### Prerequisites

- Node.js v18+, npm v9+
- Python 3.11+
- PostgreSQL 14+ with pgvector extension (for local AI-backend work)
- Expo Go app (iOS/Android) for device testing

### Environment Variables

Create a `.env` file in the project root:

```bash
# API Keys
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...

# Transcript Database (Render PostgreSQL + pgvector)
DATABASE_URL=postgresql://...@dpg-xxx.oregon-postgres.render.com/chatbot_xxx

# Conversation History Database (Render PostgreSQL)
CONVERSATION_DATABASE_URL=postgresql://...@dpg-xxx.oregon-postgres.render.com/nala_conversations

# For local development with transcript DB:
# DB_HOST=localhost
# DB_NAME=chatbot_db
# DB_USER=postgres
# DB_PASSWORD=nala
```

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python dev.py
```

Backend runs at http://127.0.0.1:8000. API docs at http://127.0.0.1:8000/docs.

### Frontend Setup

```bash
cd frontend
npm install
npx expo start
```

Scan the QR code with Expo Go, or press `i` for iOS simulator / `w` for web.

### AI-Backend Setup (for transcript pipeline work)

```bash
cd AI-backend
pip install pandas openai psycopg2-binary python-dotenv
pip install openai==0.28

# Run full pipeline (parse transcripts → create DB → load embeddings → verify)
python chatbot_pipeline.py
```

## Running the App

### Local Development

1. Start backend: `cd backend && python dev.py`
2. Start frontend: `cd frontend && npx expo start`

### Using Deployed Backend

In `frontend/src/services/ApiService.ts`, set `USE_DEPLOYED = true` to point at the Render deployment instead of localhost.

**Production URLs:**
- Backend: https://nala-backend-serv.onrender.com
- Frontend: https://nala-chatbot.expo.app/

> Note: The Render free tier spins down after 15 minutes of inactivity, causing 15-30 second cold starts.

## Project Structure

```
nala/
├── frontend/                    # React Native app (Expo)
│   └── src/
│       ├── components/onboarding/  # Onboarding slide components
│       ├── config/firebaseConfig.ts
│       ├── contexts/            # AuthContext, TextSizeContext
│       ├── navigation/          # AppNavigator, AuthStack, MainStack
│       ├── screens/             # Chat, ChatOverview, Settings, Login, etc.
│       └── services/ApiService.ts
│
├── backend/                     # FastAPI server
│   ├── routes/                  # chat.py, session.py, user.py, health.py
│   ├── services/                # ai_service.py, conversation_service.py, database_service.py
│   ├── models/                  # conversation.py, session_progress.py, user.py
│   ├── config/                  # settings.py, database.py, firebase_config.py
│   ├── adapters/                # request_adapter.py, response_adapter.py
│   └── tests/                   # test_api_endpoints.py, test_database.py
│
├── AI-backend/                  # RAG system + session managers
│   ├── transcripts/             # 58 edited coaching transcripts
│   ├── utils/                   # Shared utilities (database, goal detection, etc.)
│   ├── session1.py - session4.py          # Session state machines
│   ├── session1_manager.py - session4_manager.py  # Session chat managers
│   ├── rag_dynamic.py           # Core RAG pipeline
│   ├── query.py                 # Vector search
│   ├── chatbot_pipeline.py      # Full transcript → DB pipeline
│   ├── parse_transcripts2.py    # Transcript parser
│   ├── setup_database.py        # DB schema creation
│   └── load_embeddings.py       # Embedding generation + insertion
│
└── docs/                        # Documentation
    ├── ARCHITECTURE.md          # System architecture & data flow
    ├── FRONTEND.md              # Frontend guide
    └── BACKEND.md               # Backend, AI-backend, testing, deployment
```

## API Endpoints

### Chat
- `POST /api/v1/chat/message` — Send message, get AI response
- `GET /api/v1/chat/conversation/{id}` — Get conversation history
- `GET /api/v1/chat/conversations?user_id={uid}` — List user conversations

### Session Management
- `POST /api/v1/session/complete?user_id={uid}&session_number={n}` — Mark session complete, unlock next
- `GET /api/v1/session/progress/{user_id}` — Get all session progress
- `GET /api/v1/session/data/{user_id}/{session_number}` — Load session data (goals, profile)
- `GET /api/v1/session/latest/{user_id}` — Get most recent session

### User
- `GET /api/v1/user/status/{user_id}` — Get user status and onboarding state
- `POST /api/v1/user/onboarding` — Mark onboarding complete

### Health
- `GET /api/v1/health` — Health check

## Testing

```bash
cd backend

# Run all tests
pytest -v

# Run with coverage
pytest -v --tb=short --cov=. --cov-report=term-missing

# Specific test files
pytest tests/test_api_endpoints.py -v
pytest tests/test_database.py -v

# By marker
pytest -m database -v
pytest -m api -v
```

Tests use an in-memory SQLite database and mock AI services — no API keys needed.

CI/CD runs automatically on push/PR via GitHub Actions (`.github/workflows/ci.yml`).

## Deployment

### Backend (Render)

Push to `main` branch — Render auto-deploys. Verify at: https://nala-backend-serv.onrender.com/health

### Frontend (Expo Publish)

```bash
cd frontend
npx expo login
npx expo publish
```

Publishes to: https://nala-chatbot.expo.app/

Users open this link in Expo Go or a web browser.

## Documentation

| Document | Description |
|----------|-------------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture, data flow, databases, sessions |
| [docs/FRONTEND.md](docs/FRONTEND.md) | Frontend setup, components, navigation, chat system |
| [docs/BACKEND.md](docs/BACKEND.md) | Backend, AI-backend, testing, CI/CD, deployment |
| [SWEEP_PLAN.md](SWEEP_PLAN.md) | Security audit & cleanup plan |
| [UI_RECOMMENDATIONS.md](UI_RECOMMENDATIONS.md) | UI/UX improvement spec |

## Support

- Email: chatbot.nala@gmail.com
- GitHub: https://github.com/taiyyoson/nala
