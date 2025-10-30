# Quick Start Guide - Nala Health Coach

**Get the full E2E system running in 5 minutes!**

---

## 🎯 **What You Have**

✅ Complete RAG-based health coaching chatbot
✅ Vector database with 1000+ coaching examples
✅ Full service layer connecting AI to frontend
✅ Conversation persistence with SQLite
✅ Ready to deploy

---

## 🚀 **Start in 3 Steps**

### **1. Start Backend**
```bash
cd backend
python dev.py
```

**You'll see:**
```
================================================================================
NALA HEALTH COACH API - STARTING UP
================================================================================

🗄️  Initializing database: sqlite:///./nala_conversations.db
✓ Database tables created
✓ Database initialized successfully

================================================================================
API READY
================================================================================
📍 API URL: http://0.0.0.0:8000
📚 Docs: http://0.0.0.0:8000/docs
🤖 AI Model: claude-sonnet-4
🔍 RAG Top-K: 3
================================================================================
```

### **2. Test API**

**Option A: Use Browser**
```
Open: http://localhost:8000/docs
Click: POST /api/v1/chat/message
Try it out with:
{
  "message": "I'm feeling stressed",
  "user_id": "test_user"
}
```

**Option B: Use curl**
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "I am feeling stressed", "user_id": "test_user"}'
```

### **3. Start Frontend** (Optional)
```bash
cd frontend
npm start
```

---

## 📖 **Key Documentation**

| Document | What It Covers |
|----------|----------------|
| **[IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)** | ⭐ **START HERE** - Complete testing guide |
| [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) | System architecture overview |
| [backend/docs/PERSISTENCE_EXPLAINED.md](backend/docs/PERSISTENCE_EXPLAINED.md) | **How database updates work** |
| [backend/docs/SQLITE_TO_POSTGRESQL.md](backend/docs/SQLITE_TO_POSTGRESQL.md) | **Switching to PostgreSQL** |
| [backend/docs/E2E_FLOW_GUIDE.md](backend/docs/E2E_FLOW_GUIDE.md) | Detailed data flow walkthrough |

---

## ❓ **Common Questions**

### **When does the database get updated?**
**Answer:** Immediately after each message exchange (user + assistant).

- User sends message → API receives it
- Database writes: INSERT user message
- AI generates response (uses vector DB, no writes)
- Database writes: INSERT assistant message
- Response returned to user

**See:** [backend/docs/PERSISTENCE_EXPLAINED.md](backend/docs/PERSISTENCE_EXPLAINED.md)

---

### **How do I switch from SQLite to PostgreSQL?**
**Answer:** Update one line in `.env`:

```bash
# Change from:
DATABASE_URL=sqlite:///./nala_conversations.db

# To:
DATABASE_URL=postgresql://postgres:@localhost:5432/nala_conversations
```

**See:** [backend/docs/SQLITE_TO_POSTGRESQL.md](backend/docs/SQLITE_TO_POSTGRESQL.md)

---

### **Where is my data stored?**

**Conversation Database (User Chats):**
```
Location: backend/nala_conversations.db (SQLite)
Tables: conversations, messages
View: sqlite3 nala_conversations.db "SELECT * FROM messages"
```

**Vector Database (Coaching Knowledge):**
```
Location: PostgreSQL at localhost:5432/chatbot_db
Table: coaching_conversations (1000+ examples)
Used by: AI-backend RAG system for semantic search
```

---

### **Can I view the database?**
**Yes!**

```bash
# SQLite Browser (GUI)
brew install --cask db-browser-for-sqlite
open nala_conversations.db

# Or CLI
sqlite3 nala_conversations.db
.tables
SELECT * FROM conversations;
SELECT * FROM messages;
.quit
```

---

## 🧪 **Quick Tests**

### **Test 1: Send Message**
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "user_id": "test"}'
```

### **Test 2: Continue Conversation**
```bash
# Use conversation_id from Test 1
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to exercise more",
    "conversation_id": "conv_abc123",
    "user_id": "test"
  }'
```

### **Test 3: List Conversations**
```bash
curl "http://localhost:8000/api/v1/chat/conversations?user_id=test"
```

---

## 📊 **System Architecture**

```
┌──────────────┐
│   Frontend   │ React Native + Expo
│  ChatScreen  │
└──────┬───────┘
       │ HTTP POST /api/v1/chat/message
       ▼
┌──────────────────────────────────────────┐
│         FastAPI Backend                  │
│  ┌────────────────────────────────────┐  │
│  │ ConversationService                │  │
│  │  ├─ get history from SQLite        │  │
│  │  ├─ call AIService                 │  │
│  │  └─ save messages to SQLite        │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │ AIService                          │  │
│  │  ├─ calls RAG chatbot              │  │
│  │  └─ vector search + LLM            │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
       │
       ├─────────────────┬────────────────┐
       ▼                 ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  SQLite DB   │  │ AI-Backend   │  │  Vector DB   │
│ conversations│  │ RAG System   │  │ PostgreSQL   │
│  messages    │  │              │  │ 1000+ examples│
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## 🎯 **Next Steps**

1. ✅ **Test the system** - Follow guides above
2. ✅ **Connect frontend** - Start React Native app
3. ✅ **Review documentation** - Understand how it works
4. ✅ **Switch to PostgreSQL** - When ready for production
5. ✅ **Deploy** - Deploy to cloud when tested

---

## 🆘 **Need Help?**

**Documentation:**
- [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) - Comprehensive testing guide
- [backend/docs/PERSISTENCE_EXPLAINED.md](backend/docs/PERSISTENCE_EXPLAINED.md) - Database internals
- [backend/docs/SQLITE_TO_POSTGRESQL.md](backend/docs/SQLITE_TO_POSTGRESQL.md) - Migration guide

**API Docs (when running):**
- http://localhost:8000/docs - Interactive API documentation
- http://localhost:8000/redoc - Alternative documentation

**Troubleshooting:**
- Check logs in terminal where `python dev.py` is running
- Check database: `sqlite3 nala_conversations.db`
- Test AI-backend: `cd AI-backend && python3 -c "from rag_dynamic import UnifiedRAGChatbot; print('✓')"`

---

**🎉 You're ready to go! Start with `python backend/dev.py` and explore the API at http://localhost:8000/docs**
