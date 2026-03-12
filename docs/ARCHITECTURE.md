# Architecture & Data Flow

## System Overview

Nala uses a three-tier architecture: a React Native frontend, a FastAPI backend, and a Python-based AI backend that implements RAG (Retrieval-Augmented Generation) using real coaching transcripts.

The backend serves as the bridge between the frontend and the AI system. It handles REST API routing, database operations, session state management, and conversation persistence.

## Data Flow: User Sends a Message

```
1. FRONTEND (ChatScreen.tsx)
   └─> POST /api/v1/chat/message
       {message, user_id, session_number, conversation_id}

2. BACKEND (routes/chat.py)
   ├─> ConversationService: get or create conversation
   ├─> ConversationService: load conversation history from DB
   ├─> AIService: initialize session manager (Session 1-4)
   │   └─> Loads previous session data for Sessions 2-4
   ├─> AIService: generate_response(message, history)
   │   └─> AI-Backend RAG pipeline:
   │       ├─> Embed user query (OpenAI text-embedding-3-small)
   │       ├─> Vector search in transcript DB (top 3 similar pairs)
   │       └─> Claude Sonnet 4.5 generates response with context
   ├─> ConversationService: save user message to DB
   ├─> ConversationService: save assistant message to DB
   └─> Check for END_SESSION state → trigger session save if complete

3. RESPONSE
   └─> {response, conversation_id, session_complete, metadata}

4. FRONTEND
   └─> Display response, handle session completion if flagged
```

## Databases

Nala uses two separate PostgreSQL databases, both hosted on Render.

### Transcript Database (Vector DB)

Stores pre-parsed coaching examples for RAG retrieval. Read-only during chat — only written to when new transcripts are processed via the pipeline.

**Render tier:** Basic (required for pgvector)

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE coaching_conversations (
    id SERIAL PRIMARY KEY,
    participant_response TEXT NOT NULL,
    coach_response TEXT NOT NULL,
    context_category VARCHAR(50),
    goal_type VARCHAR(50),
    confidence_level INTEGER,
    keywords TEXT,
    source_file TEXT,
    participant_embedding vector(1536),
    coach_embedding vector(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON coaching_conversations
    USING ivfflat (participant_embedding vector_cosine_ops);
CREATE INDEX ON coaching_conversations (context_category);
CREATE INDEX ON coaching_conversations (goal_type);
```

### Conversation History Database

Stores user chat sessions, messages, and session progress. Read-write during every chat interaction.

**Render tier:** Free (should be upgraded to Basic for production)

**Key tables:**
- `conversations` — Conversation metadata (id, user_id, title, message_count, timestamps)
- `messages` — Individual messages (conversation_id FK, role, content, metadata, timestamps)
- `session_progress` — Session unlock/completion tracking (user_id, session_number, completed_at, unlocked_at)
- `users` — User records and onboarding status

**Relationships:**
- One conversation → many messages (CASCADE DELETE)
- `session_progress` has UNIQUE constraint on (user_id, session_number)

## Session System

Nala runs a structured 4-week coaching program. Each session has a state machine managed by the AI-backend.

### Session Flow

```
Week 1: Getting to know you     (always unlocked)
   ↓ Complete → 7-day wait
Week 2: Building habits          (unlocks 7 days after Week 1)
   ↓ Complete → 7-day wait
Week 3: Overcoming challenges    (unlocks 7 days after Week 2)
   ↓ Complete → 7-day wait
Week 4: Reviewing progress       (unlocks 7 days after Week 3)
   ↓ Complete → Program finished
```

### Session States

Each session (session1.py through session4.py) defines a state machine with states like INTRO, DISCOVERY, GOAL_SETTING, END_SESSION, etc. The AI-backend manages state transitions based on conversation content.

When a session reaches `END_SESSION` state:
1. Backend calls `save_session()` to persist user profile, goals, and chat history
2. Backend marks `SessionProgress` as complete with `completed_at` timestamp
3. Backend creates next session's `SessionProgress` with `unlocked_at = now + 7 days`
4. Frontend receives `session_complete: true` and navigates back to overview

### Session Data Continuity

Sessions 2-4 load data from previous sessions via `utils/database.py`:
- User name, goals, and profile from Session 1
- Progress and habits from Sessions 2-3
- All prior data for Session 4's review

### Frontend Session Display

The frontend determines session state from backend data:
- **Session 1:** Always unlocked
- **Unlocked:** `unlocked_at` exists and is in the past, OR previous session has `completed_at`
- **Completed:** Session has a `completed_at` value
- **Locked:** Everything else — displayed as non-interactive gray card

### AI Service Cache

The backend maintains an in-memory cache of AI service instances (`Dict[str, AIService]`) keyed by conversation ID. This preserves session state across messages within the same conversation. The cache is not bounded — this is a known issue (see SWEEP_PLAN.md, item 3A).

## RAG Pipeline

The RAG system retrieves relevant coaching examples to give Claude context for how a health coach should respond.

### How It Works

1. User message is embedded using OpenAI `text-embedding-3-small` (1536 dimensions)
2. Vector similarity search finds top 3 matching participant responses from transcript DB
3. Matching coach responses are included as context in Claude's prompt
4. Claude generates a response in the style of the real health coaches
5. Conversation history is maintained across the session

### Vector Search (query.py)

```sql
SELECT participant_response, coach_response,
       1 - (participant_embedding <=> query_embedding) as similarity
FROM coaching_conversations
WHERE 1 - (participant_embedding <=> query_embedding) >= 0.4
ORDER BY participant_embedding <=> query_embedding
LIMIT 3
```

Minimum similarity threshold: 0.4. Top-K: 3.

## Transcript Pipeline

Raw coaching transcripts → structured database entries:

```
transcripts/*.txt → parse_transcripts2.py → coach_responses.csv
                                                     ↓
                    setup_database.py ← creates tables + indexes
                                                     ↓
                    load_embeddings.py → generates embeddings → inserts into DB
                                                     ↓
                    query.py → verifies database correctness
```

Run the full pipeline: `python chatbot_pipeline.py`

### Transcript Format Requirements

Transcripts must follow this exact format:
```
HH:MM:SS Speaker: Text content here
```

- Timestamps: `HH:MM:SS` (two digits each, colon-separated)
- Speaker labels: exactly `Coach:` or `Participant:` (case-sensitive)
- The parser pairs consecutive Participant → Coach exchanges as conversation pairs

See the full transcript formatting guide in the technical documentation PDF.

## Database Operations Per Message

For each user message, there are approximately 5-6 database operations:

| # | Type | Table | What |
|---|------|-------|------|
| 1 | INSERT/SELECT | conversations | Get or create conversation |
| 2 | SELECT | messages | Load conversation history |
| 3 | INSERT | messages | Save user message |
| 4 | UPDATE | conversations | Increment message count |
| 5 | INSERT | messages | Save assistant message |
| 6 | UPDATE | conversations | Increment message count |

All operations use SQLAlchemy with immediate commits. Errors trigger transaction rollback.
