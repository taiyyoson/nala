# Database Persistence - How It Works

This document explains exactly when and how the database is updated during chat interactions.

---

## 🔄 **Message Flow & Database Updates**

### **Step-by-Step: What Happens When User Sends a Message**

Let's trace exactly when database operations occur:

```python
# User sends: "I'm feeling stressed"

@chat_router.post("/message")
async def send_message(request: ChatRequest, db: Session = Depends(get_db)):
    # ========================================================================
    # STEP 1: Get or Create Conversation
    # ========================================================================
    conv_id = await conv_service.get_or_create_conversation(
        conversation_id=request.conversation_id,  # May be None for first message
        user_id=request.user_id
    )
    # 🗄️ DATABASE UPDATE #1:
    # If new conversation:
    #   INSERT INTO conversations (id, user_id, title, message_count, created_at, updated_at)
    #   VALUES ('conv_abc123', 'user_xyz', 'New Conversation', 0, NOW(), NOW())

    # ========================================================================
    # STEP 2: Get Conversation History
    # ========================================================================
    history = await conv_service.get_conversation_history(conv_id, limit=10)
    # 🗄️ DATABASE READ:
    #   SELECT * FROM messages WHERE conversation_id='conv_abc123' ORDER BY created_at LIMIT 10
    # Returns: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

    # ========================================================================
    # STEP 3: Generate AI Response (NO DATABASE OPERATIONS)
    # ========================================================================
    response, sources, model_name = await ai_service.generate_response(
        message=request.message,
        conversation_history=history,  # From step 2
        user_id=request.user_id
    )
    # This calls:
    # - Vector database (read-only search)
    # - LLM API (OpenAI/Anthropic)
    # - NO writes to backend database

    # ========================================================================
    # STEP 4: Save User Message
    # ========================================================================
    await conv_service.add_message(
        conversation_id=conv_id,
        role="user",
        content=request.message
    )
    # 🗄️ DATABASE UPDATE #2:
    #   INSERT INTO messages (id, conversation_id, role, content, created_at)
    #   VALUES ('msg_def456', 'conv_abc123', 'user', 'I'm feeling stressed', NOW())
    #
    # 🗄️ DATABASE UPDATE #3:
    #   UPDATE conversations
    #   SET message_count = message_count + 1, updated_at = NOW()
    #   WHERE id = 'conv_abc123'

    # ========================================================================
    # STEP 5: Save Assistant Response
    # ========================================================================
    msg_data = await conv_service.add_message(
        conversation_id=conv_id,
        role="assistant",
        content=response,
        metadata={"model": model_name, "sources": sources}
    )
    # 🗄️ DATABASE UPDATE #4:
    #   INSERT INTO messages (id, conversation_id, role, content, metadata, created_at)
    #   VALUES ('msg_ghi789', 'conv_abc123', 'assistant', 'Tell me more...', {...}, NOW())
    #
    # 🗄️ DATABASE UPDATE #5:
    #   UPDATE conversations
    #   SET message_count = message_count + 1, updated_at = NOW()
    #   WHERE id = 'conv_abc123'

    # ========================================================================
    # STEP 6: Auto-Generate Title (First Message Only)
    # ========================================================================
    # If this is the first user message (message_count == 1):
    # 🗄️ DATABASE UPDATE #6:
    #   UPDATE conversations
    #   SET title = 'I'm feeling stressed...'
    #   WHERE id = 'conv_abc123'

    # ========================================================================
    # STEP 7: Return Response (NO DATABASE OPERATIONS)
    # ========================================================================
    return ChatResponse(...)
```

---

## 📊 **Database Update Summary**

For **each user message**, there are **5-6 database operations**:

| Operation | Type | Table | What Happens |
|-----------|------|-------|--------------|
| 1 | INSERT | `conversations` | Create conversation (if new) |
| 2 | SELECT | `messages` | Get conversation history |
| 3 | INSERT | `messages` | Save user message |
| 4 | UPDATE | `conversations` | Increment message count |
| 5 | INSERT | `messages` | Save assistant response |
| 6 | UPDATE | `conversations` | Increment message count again |
| 7 | UPDATE | `conversations` | Auto-generate title (first message only) |

---

## ⏰ **When Exactly Are These Updates Committed?**

### **Answer: Immediately, in the same request!**

Here's how SQLAlchemy transactions work:

```python
class DatabaseService:
    def create_message(self, message_data):
        message = Message(...)
        self.session.add(message)  # Staged in transaction

        self.increment_message_count(...)  # Also staged

        self.session.commit()  # 🔥 ALL STAGED CHANGES COMMITTED TO DATABASE
        # At this point, data is persisted to disk

        self.session.refresh(message)  # Get fresh data from DB
        return message
```

**Important:** Each `session.commit()` **immediately writes to the database file/server**.

### **What If There's an Error?**

```python
try:
    # Database operations...
    self.session.add(message)
    self.session.commit()  # ✅ Success - data is saved
except Exception as e:
    self.session.rollback()  # ❌ Error - all changes are reverted
    raise
```

**Behavior:**
- If AI generation fails → User message IS NOT saved (error happens before save)
- If saving fails → Exception raised, transaction rolled back
- If API crashes mid-request → SQLite/PostgreSQL ensure consistency (ACID properties)

---

## 🔍 **Viewing Database in Real-Time**

You can watch the database being updated as you chat:

### **Option 1: SQLite CLI (Real-time)**

```bash
# Terminal 1: Start backend
cd backend
python dev.py

# Terminal 2: Watch database
watch -n 1 'sqlite3 nala_conversations.db "SELECT c.id, c.message_count, m.role, m.content FROM conversations c LEFT JOIN messages m ON m.conversation_id=c.id ORDER BY m.created_at DESC LIMIT 5"'

# Now send messages via API/frontend and watch updates appear!
```

### **Option 2: SQLite Browser GUI**

```bash
# Install DB Browser for SQLite
brew install --cask db-browser-for-sqlite  # macOS

# Open database
open nala_conversations.db

# Click "Browse Data" tab
# Select "messages" table
# Send a message via API
# Click refresh button - you'll see the new rows!
```

---

## 💾 **Database Persistence Guarantees**

### **SQLite (Default)**

```python
DATABASE_URL=sqlite:///./nala_conversations.db
```

**Characteristics:**
- ✅ **Immediate persistence** - Data written to `nala_conversations.db` file
- ✅ **ACID compliant** - Atomic, Consistent, Isolated, Durable
- ✅ **Survives crashes** - Data persists even if server crashes
- ✅ **Survives restarts** - Data available when server restarts
- ⚠️ **Single file** - `nala_conversations.db` in backend directory
- ⚠️ **Not for production at scale** - One writer at a time

**File location:**
```bash
ls -lh backend/nala_conversations.db
# -rw-r--r--  1 user  staff   123K Oct 13 10:30 nala_conversations.db

# The database grows as you add messages
```

### **PostgreSQL (Production)**

```python
DATABASE_URL=postgresql://user:password@localhost/nala_conversations
```

**Characteristics:**
- ✅ **Enterprise-grade** - Handles thousands of concurrent users
- ✅ **Full ACID** - Same guarantees as SQLite, better performance
- ✅ **Replication** - Can replicate to multiple servers
- ✅ **Backup/restore** - Tools like `pg_dump`, `pg_restore`
- ✅ **Concurrent writes** - Multiple API servers can write simultaneously

---

## 🧪 **Testing Persistence**

### **Test 1: Verify Data Survives Restart**

```bash
# 1. Start backend and send a message
cd backend
python dev.py

# In another terminal:
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Test persistence", "user_id": "test"}'

# Save the conversation_id from response
CONV_ID="conv_abc123..."

# 2. Stop backend (Ctrl+C)

# 3. Restart backend
python dev.py

# 4. Retrieve conversation - IT'S STILL THERE!
curl http://localhost:8000/api/v1/chat/conversation/$CONV_ID

# Response shows all messages preserved ✅
```

### **Test 2: Verify Crash Recovery**

```bash
# 1. Send a message
curl -X POST http://localhost:8000/api/v1/chat/message \
  -d '{"message": "Before crash", "user_id": "test"}'

# 2. Kill backend forcefully
kill -9 $(pgrep -f "python dev.py")

# 3. Restart backend
python dev.py

# 4. Check database
sqlite3 nala_conversations.db "SELECT * FROM messages ORDER BY created_at DESC LIMIT 1"

# Message is still there! SQLite guarantees durability ✅
```

---

## 📈 **Database Growth Over Time**

```bash
# Check database size
ls -lh nala_conversations.db

# After 100 messages: ~50 KB
# After 1,000 messages: ~500 KB
# After 10,000 messages: ~5 MB
# After 100,000 messages: ~50 MB

# SQLite can handle databases up to 281 TB (theoretical limit)
# Practical limit for web apps: ~100 GB
```

---

## 🔐 **Data Integrity**

### **Foreign Key Constraints**

```sql
-- Messages table has foreign key to conversations
CREATE TABLE messages (
    conversation_id VARCHAR(36) REFERENCES conversations(id) ON DELETE CASCADE
);

-- This means:
-- 1. Cannot create message without valid conversation ✅
-- 2. Deleting conversation auto-deletes all messages ✅
-- 3. Cannot orphan messages ✅
```

**Test it:**
```bash
# 1. Create conversation with messages
curl -X POST http://localhost:8000/api/v1/chat/message \
  -d '{"message": "Hello", "user_id": "test"}'
# Note the conversation_id

# 2. Check messages exist
sqlite3 nala_conversations.db "SELECT COUNT(*) FROM messages WHERE conversation_id='conv_...';"
# Output: 2 (user + assistant)

# 3. Delete conversation
curl -X DELETE http://localhost:8000/api/v1/chat/conversation/conv_...

# 4. Check messages - AUTOMATICALLY DELETED
sqlite3 nala_conversations.db "SELECT COUNT(*) FROM messages WHERE conversation_id='conv_...';"
# Output: 0 ✅
```

---

## 🚨 **What Happens If Database Is Lost?**

### **Scenario: Delete `nala_conversations.db` file**

```bash
# 1. Delete database
rm nala_conversations.db

# 2. Restart backend
python dev.py
# Output: ✓ Database tables created (new empty database)

# 3. Send message
curl -X POST http://localhost:8000/api/v1/chat/message \
  -d '{"message": "After database loss", "user_id": "test"}'

# Result: Works fine! New database created automatically
# But: All previous conversations are GONE

# Lesson: BACKUP YOUR DATABASE IN PRODUCTION!
```

---

## 📝 **Summary**

| Question | Answer |
|----------|--------|
| **When is data saved?** | Immediately after each message (user + assistant) |
| **How many database writes per message?** | 5-6 operations (2 INSERTs, 3-4 UPDATEs) |
| **Is it atomic?** | Yes - all changes in a transaction |
| **What if there's an error?** | Transaction rolled back, no partial data saved |
| **Does it survive crashes?** | Yes - SQLite/PostgreSQL are ACID compliant |
| **Does it survive restarts?** | Yes - data persists in database file |
| **Where is the database?** | SQLite: `backend/nala_conversations.db` file |
| **Can I see it in real-time?** | Yes - use SQLite CLI or DB Browser |
| **What if I delete the database?** | Backend auto-creates new empty database on startup |

---

**Next:** See [SQLITE_TO_POSTGRESQL.md](./SQLITE_TO_POSTGRESQL.md) for migration guide.
