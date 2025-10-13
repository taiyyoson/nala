# Database Schema Evolution Guide

This document outlines the evolution of the Nala Health Coach backend database from a simple MVP design to a comprehensive structured coaching program system.

---

## Table of Contents

1. [Current State: Phase 1 (MVP)](#phase-1-mvp-current)
2. [Future State: Phase 2-4](#future-phases)
3. [Migration Guide](#migration-guide)
4. [PlantUML Diagram](#plantuml-diagram)
5. [Implementation Checklist](#implementation-checklist)

---

## Phase 1: MVP (Current)

### **Schema: 2 Tables**

```
conversations
  ├─ id (UUID, PK)
  ├─ user_id (VARCHAR, nullable)
  ├─ title (VARCHAR)
  ├─ message_count (INTEGER)
  ├─ metadata (JSON)
  ├─ created_at (TIMESTAMP)
  └─ updated_at (TIMESTAMP)

messages
  ├─ id (UUID, PK)
  ├─ conversation_id (UUID, FK → conversations.id)
  ├─ role (ENUM: user/assistant/system)
  ├─ content (TEXT)
  ├─ metadata (JSON)
  ├─ created_at (TIMESTAMP)
  └─ updated_at (TIMESTAMP)
```

### **Capabilities**
- ✅ Real-time chat with RAG-based responses
- ✅ Conversation history and persistence
- ✅ Context-aware multi-turn conversations
- ✅ Multiple conversations per user
- ✅ Message metadata (model used, sources, etc.)

### **Limitations**
- ⚠️ No structured program progression (weeks/sessions)
- ⚠️ No explicit goal tracking
- ⚠️ No user profile/persona management
- ⚠️ Analytics require parsing JSON metadata
- ⚠️ Progress tracking is manual/ad-hoc

### **Current Workarounds**

Store structured data in JSON metadata fields:

```json
// conversation.metadata
{
  "week_number": 1,
  "session_type": "goal_setting",
  "goal_id": "fitness_goal_1",
  "program_status": "active"
}

// message.metadata
{
  "model": "Claude Sonnet 4",
  "sources": [...],
  "mood_rating": 7,
  "takeaways": ["Set realistic goals", "Start small"],
  "action_items": ["Exercise 3x this week"]
}
```

---

## Future Phases

## Phase 2: User Management & Personalization

**When:** You need user accounts beyond Firebase, personalization, and engagement tracking

### **New Tables**

#### **`users`**
```sql
CREATE TABLE users (
  user_id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255),  -- Optional if using Firebase only
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  phone_number VARCHAR(20),
  created_at TIMESTAMP DEFAULT NOW(),
  last_login TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
```

**Purpose:**
- Central user registry (can sync with Firebase)
- Store user profile information
- Track login history

#### **`user_persona`**
```sql
CREATE TABLE user_persona (
  persona_id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
  personal_details JSONB,  -- Flexible storage for user context
  has_dog BOOLEAN,
  preferences JSONB,  -- Coaching style preferences, notification settings
  vector_data VECTOR(1536),  -- User profile embedding for personalization
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_persona_user ON user_persona(user_id);
```

**Purpose:**
- Store user-specific context for personalized coaching
- Vector embedding of user profile for similarity-based personalization
- Track user preferences (communication style, topics, etc.)

#### **`engagement_analytics`**
```sql
CREATE TABLE engagement_analytics (
  analytics_id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
  total_messages INTEGER DEFAULT 0,
  avg_response_time INTERVAL,
  session_completion_rate DECIMAL(5,2),  -- Percentage
  last_activity TIMESTAMP,
  engagement_score DECIMAL(5,2),  -- Computed metric
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_analytics_user ON engagement_analytics(user_id);
```

**Purpose:**
- Track user engagement metrics
- Calculate completion rates and activity patterns
- Support analytics dashboards

### **Migration Steps**

1. **Create new tables**
   ```bash
   python -m backend.scripts.migrate add_user_tables
   ```

2. **Migrate existing data**
   ```sql
   -- Create user records from existing conversations
   INSERT INTO users (user_id, created_at)
   SELECT DISTINCT user_id, MIN(created_at)
   FROM conversations
   WHERE user_id IS NOT NULL
   GROUP BY user_id;

   -- Initialize analytics for each user
   INSERT INTO engagement_analytics (analytics_id, user_id, total_messages, last_activity)
   SELECT gen_random_uuid(), user_id, COUNT(*), MAX(updated_at)
   FROM conversations c
   JOIN messages m ON m.conversation_id = c.id
   GROUP BY user_id;
   ```

3. **Update application code**
   - Add User model: `backend/models/user.py`
   - Add UserPersona model: `backend/models/user_persona.py`
   - Add analytics tracking to message handlers

---

## Phase 3: Structured Coaching Program

**When:** You need week-based progression, SMART goals, and session management

### **New Tables**

#### **`smart_goals`**
```sql
CREATE TABLE smart_goals (
  goal_id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
  goal_type VARCHAR(50) NOT NULL,  -- fitness, nutrition, stress, sleep, etc.
  specific TEXT NOT NULL,
  measurable TEXT NOT NULL,
  achievable TEXT NOT NULL,
  relevant TEXT NOT NULL,
  time_bound TEXT NOT NULL,
  status VARCHAR(20) DEFAULT 'active',  -- active, completed, revised, abandoned
  created_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP
);

CREATE INDEX idx_goals_user ON smart_goals(user_id);
CREATE INDEX idx_goals_status ON smart_goals(status);
```

**Purpose:**
- Track user goals using SMART framework
- Support goal revision and progress tracking
- Enable goal-specific coaching sessions

#### **`sessions`**
```sql
CREATE TABLE sessions (
  session_id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
  goal_id UUID REFERENCES smart_goals(goal_id) ON DELETE SET NULL,
  session_number INTEGER NOT NULL,
  week_number INTEGER NOT NULL,
  session_type VARCHAR(50),  -- goal_setting, check_in, reflection, etc.
  scheduled_date TIMESTAMP,
  completed_date TIMESTAMP,
  status VARCHAR(20) DEFAULT 'locked',  -- locked, unlocked, in_progress, completed
  summary TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_week ON sessions(week_number);
CREATE UNIQUE INDEX idx_sessions_user_week ON sessions(user_id, week_number, session_number);
```

**Purpose:**
- Manage 4-week structured program
- Implement unlock logic (week 2 unlocks after week 1 completes)
- Track session completion and scheduling

**Unlock Logic:**
```sql
-- Check if user can unlock next session
SELECT
  CASE
    WHEN status = 'completed' THEN TRUE
    ELSE FALSE
  END as can_unlock_next
FROM sessions
WHERE user_id = 'user_id'
  AND week_number = (SELECT MAX(week_number) FROM sessions WHERE status = 'completed');
```

#### **`session_takeaways`**
```sql
CREATE TABLE session_takeaways (
  takeaway_id UUID PRIMARY KEY,
  session_id UUID REFERENCES sessions(session_id) ON DELETE CASCADE,
  key_learnings TEXT,
  action_items TEXT,
  revised_goal TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_takeaways_session ON session_takeaways(session_id);
```

**Purpose:**
- Summarize coaching sessions
- Track action items for follow-up
- Record goal revisions

#### **`check_ins`**
```sql
CREATE TABLE check_ins (
  checkin_id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
  goal_id UUID REFERENCES smart_goals(goal_id) ON DELETE CASCADE,
  checkin_date DATE NOT NULL,
  progress_notes TEXT,
  mood_rating INTEGER CHECK (mood_rating BETWEEN 1 AND 10),
  goal_progress INTEGER CHECK (goal_progress BETWEEN 0 AND 100),  -- Percentage
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_checkins_user ON check_ins(user_id);
CREATE INDEX idx_checkins_goal ON check_ins(goal_id);
CREATE INDEX idx_checkins_date ON check_ins(checkin_date);
```

**Purpose:**
- Track progress between sessions
- Capture mood and goal progress metrics
- Enable progress visualization

### **Migration Steps**

1. **Create new tables**
   ```bash
   python -m backend.scripts.migrate add_program_tables
   ```

2. **Extract goals from existing conversations**
   ```sql
   -- Parse goals from conversation metadata
   INSERT INTO smart_goals (goal_id, user_id, goal_type, specific, ...)
   SELECT
     gen_random_uuid(),
     user_id,
     metadata->>'goal_type',
     metadata->>'goal_description',
     ...
   FROM conversations
   WHERE metadata->>'goal_type' IS NOT NULL;
   ```

3. **Map conversations to sessions**
   ```sql
   -- Create sessions from conversations with week metadata
   INSERT INTO sessions (session_id, user_id, week_number, status)
   SELECT
     gen_random_uuid(),
     user_id,
     COALESCE((metadata->>'week_number')::INTEGER, 1),
     CASE
       WHEN updated_at < NOW() - INTERVAL '7 days' THEN 'completed'
       ELSE 'in_progress'
     END
   FROM conversations
   WHERE metadata->>'week_number' IS NOT NULL;
   ```

4. **Update application code**
   - Add new models in `backend/models/`
   - Create `SessionService` for session management
   - Implement unlock logic in `routes/sessions.py`
   - Update frontend to check session status before navigation

---

## Phase 4: Advanced Transcript Management

**When:** You need fine-grained message analysis separate from chat history

### **New Tables**

#### **`transcripts`**
```sql
CREATE TABLE transcripts (
  transcript_id UUID PRIMARY KEY,
  session_id UUID REFERENCES sessions(session_id) ON DELETE CASCADE,
  message_order INTEGER NOT NULL,
  sender VARCHAR(20) NOT NULL,  -- user, assistant, system
  message_content TEXT NOT NULL,
  timestamp TIMESTAMP DEFAULT NOW(),
  metadata JSONB
);

CREATE INDEX idx_transcripts_session ON transcripts(session_id);
CREATE INDEX idx_transcripts_order ON transcripts(session_id, message_order);
```

**Purpose:**
- Session-specific transcript analysis
- Link messages directly to coaching sessions
- Enable advanced analytics on coaching patterns

**Difference from `messages`:**
- `messages` = General conversation messages (ongoing chat)
- `transcripts` = Session-specific coaching transcripts (completed sessions)

### **Migration Steps**

1. **Create table**
   ```bash
   python -m backend.scripts.migrate add_transcripts
   ```

2. **Copy completed session messages**
   ```sql
   -- Copy messages from completed sessions to transcripts
   INSERT INTO transcripts (transcript_id, session_id, message_order, sender, message_content, timestamp)
   SELECT
     gen_random_uuid(),
     s.session_id,
     ROW_NUMBER() OVER (PARTITION BY m.conversation_id ORDER BY m.created_at),
     m.role,
     m.content,
     m.created_at
   FROM messages m
   JOIN conversations c ON c.id = m.conversation_id
   JOIN sessions s ON s.user_id = c.user_id
     AND s.week_number = (c.metadata->>'week_number')::INTEGER
   WHERE s.status = 'completed';
   ```

---

## Migration Guide

### **Pre-Migration Checklist**

- [ ] Backup current database
- [ ] Test migration on staging environment
- [ ] Update application dependencies
- [ ] Prepare rollback plan

### **Migration Command Structure**

```bash
# General pattern
python -m backend.scripts.migrate [phase_name] [--dry-run] [--rollback]

# Examples
python -m backend.scripts.migrate add_user_tables --dry-run
python -m backend.scripts.migrate add_program_tables
python -m backend.scripts.migrate add_transcripts --rollback
```

### **Post-Migration Tasks**

1. **Verify data integrity**
   ```sql
   -- Check foreign key relationships
   SELECT
     (SELECT COUNT(*) FROM users) as users_count,
     (SELECT COUNT(*) FROM conversations WHERE user_id NOT IN (SELECT user_id FROM users)) as orphaned_conversations;
   ```

2. **Update API endpoints**
   - Add new routes for sessions, goals, check-ins
   - Update existing routes to use new tables
   - Deprecate JSON metadata queries

3. **Update frontend**
   - Fetch session status for unlock logic
   - Display goal progress from check_ins table
   - Show session takeaways

4. **Test thoroughly**
   - Run integration tests
   - Test unlock logic
   - Verify analytics calculations

---

## PlantUML Diagram

The full future schema with all relationships is defined in [`database_schema_future.puml`](./database_schema_future.puml).

**To view the diagram:**

1. Install PlantUML:
   ```bash
   brew install plantuml  # macOS
   # or visit https://plantuml.com/download
   ```

2. Generate PNG:
   ```bash
   plantuml backend/docs/database_schema_future.puml
   ```

3. Or use online editor: https://www.plantuml.com/plantuml/uml/

### **Diagram Overview**

The diagram shows 8 interconnected tables:

- **Users** (1) → **User_Persona** (1)
- **Users** (1) → **SMART_Goals** (many)
- **Users** (1) → **Sessions** (many)
- **Users** (1) → **Check_Ins** (many)
- **Users** (1) → **Engagement_Analytics** (1)
- **SMART_Goals** (1) → **Sessions** (many)
- **SMART_Goals** (1) → **Check_Ins** (many)
- **Sessions** (1) → **Transcripts** (many)
- **Sessions** (1) → **Session_Takeaways** (1)

---

## Implementation Checklist

### **Phase 2: User Management**
- [ ] Create migration script: `backend/scripts/migrations/002_add_user_tables.py`
- [ ] Add models: `User`, `UserPersona`, `EngagementAnalytics`
- [ ] Add services: `UserService`, `AnalyticsService`
- [ ] Update routes to include user context
- [ ] Sync Firebase users to database
- [ ] Add admin dashboard for user analytics

### **Phase 3: Structured Program**
- [ ] Create migration script: `backend/scripts/migrations/003_add_program_tables.py`
- [ ] Add models: `SmartGoal`, `Session`, `SessionTakeaway`, `CheckIn`
- [ ] Add services: `GoalService`, `SessionService`, `CheckInService`
- [ ] Implement session unlock logic
- [ ] Add routes: `/goals`, `/sessions`, `/check-ins`
- [ ] Update frontend: Session unlock UI, goal tracking
- [ ] Add weekly check-in notifications

### **Phase 4: Transcript Management**
- [ ] Create migration script: `backend/scripts/migrations/004_add_transcripts.py`
- [ ] Add model: `Transcript`
- [ ] Add service: `TranscriptService`
- [ ] Implement transcript analysis endpoint
- [ ] Build coaching pattern analytics

---

## Decision Matrix: When to Migrate?

| Requirement | Stay Phase 1 | Migrate to Phase 2 | Migrate to Phase 3 |
|-------------|--------------|--------------------|--------------------|
| Basic chat | ✅ | ✅ | ✅ |
| User profiles beyond Firebase | ❌ | ✅ | ✅ |
| Personalization vectors | ❌ | ✅ | ✅ |
| Engagement analytics | ⚠️ Manual | ✅ Automated | ✅ Automated |
| SMART goal tracking | ⚠️ Manual | ⚠️ Manual | ✅ Structured |
| Week-based program | ⚠️ App logic | ⚠️ App logic | ✅ DB-enforced |
| Session unlock logic | ⚠️ Frontend only | ⚠️ Frontend only | ✅ Backend logic |
| Progress check-ins | ❌ | ❌ | ✅ |
| Session summaries | ⚠️ In messages | ⚠️ In messages | ✅ Dedicated table |
| < 1000 users | ✅ | ✅ | ✅ |
| 1000-10000 users | ⚠️ Acceptable | ✅ | ✅ |
| > 10000 users | ❌ | ⚠️ Acceptable | ✅ |

---

## Additional Resources

- **Current Schema:** `backend/models/` (conversation.py, message.py)
- **Future Schema:** `backend/docs/database_schema_future.puml`
- **Integration Guide:** `backend/INTEGRATION_GUIDE.md`
- **Migration Scripts:** `backend/scripts/migrations/` (to be created)

---

## Notes

- All UUIDs are generated using `gen_random_uuid()` (PostgreSQL) or Python `uuid.uuid4()`
- Timestamps use UTC timezone
- JSON fields use JSONB in PostgreSQL for better query performance
- Vector fields require pgvector extension
- Consider adding soft deletes (deleted_at column) instead of CASCADE DELETE for audit trails

---

**Last Updated:** 2024-10-13
**Version:** 1.0
**Author:** Nala Health Coach Development Team
