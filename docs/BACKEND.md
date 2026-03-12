# Backend & AI-Backend Guide

## Backend (FastAPI)

The backend is a FastAPI application hosted on Render that bridges the React Native frontend and the AI-backend session management system. It handles REST API routing, database operations, session state management, and conversation persistence.

### Quick Start

```bash
cd backend
pip install -r requirements.txt
python dev.py
```

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/v1/health

### Folder Structure

```
backend/
├── app.py                    # FastAPI application and startup
├── dev.py                    # Development server
├── config/
│   ├── settings.py           # Environment configuration
│   ├── database.py           # SQLAlchemy database setup
│   └── firebase_config.py    # Firebase admin initialization
├── routes/
│   ├── chat.py               # Chat and conversation endpoints
│   ├── session.py            # Session progress and data endpoints
│   ├── user.py               # User status and onboarding
│   └── health.py             # Health check endpoint
├── services/
│   ├── ai_service.py         # AI/RAG integration layer
│   ├── conversation_service.py  # Conversation management
│   └── database_service.py   # Database operations
├── models/
│   ├── conversation.py       # Conversation and message models
│   ├── session_progress.py   # Session unlock/completion tracking
│   └── user.py               # User model
├── adapters/
│   ├── request_adapter.py    # Request transformation
│   └── response_adapter.py   # Response formatting
└── tests/
    ├── conftest.py            # Fixtures (mock AI, test DB, test client)
    ├── test_api_endpoints.py  # API endpoint tests
    └── test_database.py       # Database operation tests
```

### Core Components

**AIService** (`services/ai_service.py`) — Manages integration with the AI-backend RAG system. Initializes the appropriate session manager (Session 1-4) based on session number, loads previous session data for Sessions 2-4 continuity, and routes messages to the RAG chatbot.

**ConversationService** (`services/conversation_service.py`) — Handles conversation and message persistence in PostgreSQL. Creates or retrieves conversations, saves user and assistant messages with metadata, and maintains conversation history.

**Chat Routes** (`routes/chat.py`) — Primary message handling at `POST /api/v1/chat/message`. Maintains an AI service cache to preserve session state across messages. Detects session completion via `END_SESSION` state and triggers session save.

**Session Routes** (`routes/session.py`) — Session progress tracking:
- `mark_session_complete()` — Marks session complete, unlocks next with 7-day delay
- `get_session_data()` — Loads saved session data (goals, user profile)
- `get_user_progress()` — Returns all session progress records

### Database Models

- **Conversation & Message** — Conversation metadata and individual messages with role (user/assistant), content, timestamp, and optional metadata (model used, RAG sources). CASCADE DELETE on messages when conversation is deleted.
- **SessionProgress** — Tracks completion and unlock timing per session per user. Fields: `user_id`, `session_number`, `completed_at`, `unlocked_at`. UNIQUE constraint on (user_id, session_number).
- **User** — User records with onboarding status.

### Deployment

Hosted on Render (Free tier). Free tier has auto-spindown after 15 minutes of inactivity, causing 15-30 second cold starts. **Upgrade to Basic tier recommended for production.**

Production URL: https://nala-backend-serv.onrender.com

Push to `main` branch triggers auto-deploy via Render.

---

## AI-Backend (RAG System)

The AI-backend is a Python package that manages the RAG pipeline, session state machines, and the transcript processing pipeline. The primary LLM is Claude Sonnet 4.5 with support for other Claude versions and OpenAI models.

### Folder Structure

```
AI-backend/
├── transcripts/               # 58 edited coaching transcripts (.txt)
├── utils/
│   ├── constants.py           # Shared constants across session managers
│   ├── database.py            # Load/save session data and users
│   ├── discovery_helpers.py   # Discovery question helpers (Session 1)
│   ├── goal_detection.py      # Goal detection
│   ├── goal_parser.py         # Goal parsing and SMART validation
│   ├── name_extraction.py     # Extract name from text
│   ├── program_loader.py      # Load program information
│   ├── smart_evaluation.py    # SMART goal evaluation (LLM + heuristic)
│   ├── state_helpers.py       # State result creation utilities
│   ├── state_prompts.py       # Prompts for each state in each session
│   └── unified_storage.py     # Uniform session save/load
├── session1.py - session4.py          # Session state machines
├── session1_manager.py - session4_manager.py  # Interactive chat managers
├── base_session_chatbot.py    # Base class for session managers
├── rag_dynamic.py             # Core RAG pipeline
├── query.py                   # Vector search (multiple modes)
├── chatbot_pipeline.py        # Full transcript → DB pipeline
├── parse_transcripts2.py      # Transcript parser → CSV
├── setup_database.py          # DB schema creation/reset
├── load_embeddings.py         # Embedding generation + DB insertion
├── coach_responses.csv        # Parsed conversation pairs
├── constraintChecker.py       # Impossible promise detection
├── programinfo.txt            # Program info for Session 1
├── test_connection.py         # Transcript DB connection test
├── test_conversationdb.py     # Conversation DB connection test
└── test_session_persistence.py  # Session save/load test
```

### Sessions

Session context for Claude is built from similar conversation pairs from the transcripts plus history from previous sessions.

**Session 1** — Getting to know you. States include intro, discovery, goal setting, etc. `session1.py` manages states; `session1_manager.py` manages the interactive chat.

**Sessions 2 & 3** — Building habits / Overcoming challenges. Load previous session data for continuity. Same pattern: `sessionN.py` (states) + `sessionN_manager.py` (chat).

**Session 4** — Reviewing progress. Loads all prior session data for comprehensive review.

The `_manager.py` files also serve as standalone terminal debuggers for each session.

### Transcript Pipeline

Process raw transcripts into the vector database:

```bash
python chatbot_pipeline.py
```

This runs:
1. `parse_transcripts2.py` — Parse `transcripts/*.txt` → `coach_responses.csv`
2. `setup_database.py` — Reset and create DB tables + indexes
3. `load_embeddings.py` — Generate embeddings, insert into DB
4. `query.py` — Verify database correctness

### Utility Files

- `base_session_chatbot.py` — Base class for session manager files
- `constraintChecker.py` — Identifies impossible promises and fixes them
- `programinfo.txt` — Detailed program information used in Session 1
- `test_connection.py` / `test_conversationdb.py` — Database connection tests (important because USF network occasionally blocks port 5432 to Render)

---

## Testing

### Backend Tests

All tests are in `backend/tests/` using pytest. Tests use in-memory SQLite and mock AI services — no API keys needed.

**Test files:**
- `test_api_endpoints.py` — All FastAPI REST endpoints (health, chat, conversation flow, validation)
- `test_database.py` — Database CRUD, conversation history, cascade deletes, health checks
- `conftest.py` — Shared fixtures (test DB, mock AI service, test client, sample data)

### Running Tests

```bash
cd backend

# All tests
pytest -v

# With coverage
pytest -v --tb=short --cov=. --cov-report=term-missing

# Specific file
pytest tests/test_api_endpoints.py -v --tb=short
pytest tests/test_database.py -v --tb=short

# By marker
pytest -m database -v
pytest -m api -v

# Single test
pytest tests/test_api_endpoints.py::test_health_check_endpoint -v
```

### E2E Tests

Full flow tests (onboarding → session 1 → 2 → 3 → 4):

```bash
cd backend
venv/bin/python -m pytest tests/test_e2e_full_flow.py -v
```

The E2E tests use a `StatefulMockAIService` that counts `generate_response()` calls and triggers `END_SESSION` after 3 messages. No real LLM calls needed — tests run in ~0.2s.

### AI-Backend Tests

```bash
cd AI-backend
python test_connection.py          # Transcript DB connection
python test_conversationdb.py      # Conversation DB connection
python test_session_persistence.py # Session save/load
```

---

## CI/CD Pipeline

Defined in `.github/workflows/ci.yml`. Runs on:
- Push to `main`, `develop`, or `taiyo-backend-skeleton` branches
- Pull requests targeting `main` or `develop`

### Pipeline Steps

1. **Environment Setup** — Python 3.11, cached pip dependencies, install requirements
2. **Linting** — Flake8 (critical errors fail build, style issues warn only)
3. **Formatting** — Black and isort (fail build if not formatted)
4. **Tests** — Database tests, API tests, then full suite with coverage

### Running CI/CD Locally

```bash
cd backend

# Lint
python3 -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Check formatting
python3 -m black --check .
python3 -m isort --check-only .

# Auto-fix formatting
python3 -m black .
python3 -m isort .

# Run tests
python3 -m pytest -v --tb=short
```

All PRs must pass CI/CD before merging.
