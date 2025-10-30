# SQLite to PostgreSQL Migration Guide

Complete guide for switching from SQLite (development) to PostgreSQL (production).

---

## 🎯 **Why Switch to PostgreSQL?**

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| **Concurrent writes** | ❌ One writer at a time | ✅ Thousands of concurrent users |
| **Production ready** | ⚠️ Good for dev/small apps | ✅ Enterprise-grade |
| **Multi-server support** | ❌ File-based, single server | ✅ Can connect multiple API servers |
| **Backup/restore** | ⚠️ Copy file | ✅ Built-in tools (pg_dump, etc.) |
| **Replication** | ❌ Not supported | ✅ Master-slave replication |
| **Maximum size** | ~281 TB (theoretical) | Unlimited (practical) |
| **JSON queries** | ⚠️ Limited | ✅ Full JSONB support |
| **Setup complexity** | ✅ Zero config (just a file) | ⚠️ Requires server setup |

**Recommendation:**
- ✅ **Development:** SQLite (simple, no setup needed)
- ✅ **Production:** PostgreSQL (scalable, reliable)

---

## 📋 **Migration Steps Overview**

1. Install PostgreSQL
2. Create database
3. Update `.env` file
4. Run migration (optional - if you have existing data)
5. Restart backend
6. Verify

---

## 🛠️ **Step 1: Install PostgreSQL**

### **Option A: Install Locally (Development/Testing)**

#### **macOS (Homebrew)**
```bash
# Install PostgreSQL
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Verify installation
psql --version
# Output: psql (PostgreSQL) 15.x

# Check if running
brew services list | grep postgresql
# Output: postgresql@15  started
```

#### **Linux (Ubuntu/Debian)**
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql  # Auto-start on boot

# Verify
psql --version
```

#### **Windows**
```powershell
# Download installer from:
https://www.postgresql.org/download/windows/

# Or use Chocolatey:
choco install postgresql

# Start service from Services panel
```

### **Option B: Use Cloud PostgreSQL (Production)**

#### **Render.com (Free tier available)**
1. Go to https://render.com
2. Create account
3. Click "New +" → "PostgreSQL"
4. Choose "Free" plan
5. Note the connection URL (looks like below)

#### **Railway.app (Free tier)**
1. Go to https://railway.app
2. Create project → Add PostgreSQL
3. Copy connection string

#### **Heroku Postgres**
```bash
heroku addons:create heroku-postgresql:mini
heroku config:get DATABASE_URL
```

#### **Supabase (PostgreSQL + extras)**
1. Go to https://supabase.com
2. Create project
3. Go to Settings → Database
4. Copy connection string

---

## 🗄️ **Step 2: Create Database**

### **Local PostgreSQL**

```bash
# Connect to PostgreSQL (creates default postgres database)
psql postgres

# Create database for conversation storage
CREATE DATABASE nala_conversations;

# Create user (optional - use postgres user for dev)
CREATE USER nala_user WITH PASSWORD 'your_secure_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE nala_conversations TO nala_user;

# Exit
\q

# Verify database created
psql -l | grep nala
# Output: nala_conversations | postgres | UTF8 | ...
```

### **Test Connection**

```bash
# Connect to new database
psql nala_conversations

# You should see:
# nala_conversations=#

# Try a query
SELECT version();

# Exit
\q
```

---

## ⚙️ **Step 3: Update Configuration**

### **Update `.env` File**

```bash
# Open .env file
cd /Users/happiness/src/cs490/nala
nano .env  # or use your editor
```

**Change this:**
```bash
# OLD (SQLite)
DATABASE_URL=sqlite:///./nala_conversations.db
```

**To this (choose one):**

#### **Local PostgreSQL**
```bash
# NEW (PostgreSQL - local)
DATABASE_URL=postgresql://postgres:@localhost:5432/nala_conversations

# Or with custom user:
DATABASE_URL=postgresql://nala_user:your_secure_password@localhost:5432/nala_conversations
```

#### **Cloud PostgreSQL (Render example)**
```bash
# NEW (PostgreSQL - Render.com)
DATABASE_URL=postgresql://nala_user:AbCd1234EfGh5678@dpg-xyz123-a.oregon-postgres.render.com/nala_conversations
```

**Complete `.env` example:**
```bash
# =============================================================================
# Nala Health Coach - Environment Configuration
# =============================================================================

# -----------------------------------------------------------------------------
# Backend Database (Conversation Storage) - UPDATED FOR POSTGRESQL
# -----------------------------------------------------------------------------
# SQLite (Development):
# DATABASE_URL=sqlite:///./nala_conversations.db

# PostgreSQL (Production):
DATABASE_URL=postgresql://postgres:@localhost:5432/nala_conversations

# Or cloud provider:
# DATABASE_URL=postgresql://user:password@host:5432/database_name

# -----------------------------------------------------------------------------
# Vector Database (AI-Backend - Coaching Knowledge Base)
# -----------------------------------------------------------------------------
VECTOR_DB_HOST=localhost
VECTOR_DB_PORT=5432
VECTOR_DB_NAME=chatbot_db
VECTOR_DB_USER=postgres
VECTOR_DB_PASSWORD=nala

# (rest of .env stays the same...)
```

**Save and close.**

---

## 🔄 **Step 4: Initialize PostgreSQL Database**

### **Option A: Fresh Start (No Existing Data)**

Simply restart the backend - tables will be created automatically:

```bash
cd backend
python dev.py

# You should see:
# 🗄️  Initializing database: postgresql://postgres:@localhost/nala_conversations
# ✓ Database tables created
# ✓ Database initialized successfully
```

**Verify tables created:**
```bash
psql nala_conversations

# List tables
\dt

# Output:
#  Schema |       Name       | Type  |  Owner
# --------+------------------+-------+----------
#  public | conversations    | table | postgres
#  public | messages         | table | postgres

# View schema
\d conversations
\d messages

# Exit
\q
```

### **Option B: Migrate Existing SQLite Data**

If you have conversations in SQLite that you want to keep:

#### **Method 1: Manual Export/Import (Small datasets)**

```bash
# 1. Export from SQLite
sqlite3 nala_conversations.db <<EOF
.mode insert conversations
.output conversations.sql
SELECT * FROM conversations;
.output messages.sql
SELECT * FROM messages;
EOF

# 2. Edit SQL files to be PostgreSQL-compatible
# (SQLite uses different syntax for some things)

# 3. Import to PostgreSQL
psql nala_conversations < conversations.sql
psql nala_conversations < messages.sql
```

#### **Method 2: Use Migration Script**

Create `backend/scripts/migrate_sqlite_to_postgres.py`:

```python
"""
Migrate data from SQLite to PostgreSQL

Usage: python -m backend.scripts.migrate_sqlite_to_postgres
"""

import sqlite3
import psycopg2
from backend.config.settings import settings

def migrate():
    # Connect to SQLite
    sqlite_conn = sqlite3.connect('nala_conversations.db')
    sqlite_cursor = sqlite_conn.cursor()

    # Connect to PostgreSQL
    pg_url = settings.database_url
    # Parse URL (postgresql://user:pass@host:port/db)
    # For simplicity, use psycopg2.connect with URL
    pg_conn = psycopg2.connect(pg_url)
    pg_cursor = pg_conn.cursor()

    # Migrate conversations
    print("Migrating conversations...")
    sqlite_cursor.execute("SELECT * FROM conversations")
    conversations = sqlite_cursor.fetchall()

    for conv in conversations:
        pg_cursor.execute("""
            INSERT INTO conversations
            (id, user_id, title, message_count, metadata, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, conv)

    print(f"✓ Migrated {len(conversations)} conversations")

    # Migrate messages
    print("Migrating messages...")
    sqlite_cursor.execute("SELECT * FROM messages")
    messages = sqlite_cursor.fetchall()

    for msg in messages:
        pg_cursor.execute("""
            INSERT INTO messages
            (id, conversation_id, role, content, metadata, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, msg)

    print(f"✓ Migrated {len(messages)} messages")

    # Commit and close
    pg_conn.commit()
    sqlite_conn.close()
    pg_conn.close()

    print("\n✓ Migration complete!")

if __name__ == "__main__":
    migrate()
```

Run migration:
```bash
python -m backend.scripts.migrate_sqlite_to_postgres
```

#### **Method 3: Use pgloader (Automatic)**

```bash
# Install pgloader
brew install pgloader  # macOS
sudo apt install pgloader  # Linux

# Create migration config
cat > sqlite_to_pg.load <<EOF
LOAD DATABASE
    FROM sqlite://nala_conversations.db
    INTO postgresql://postgres:@localhost/nala_conversations

WITH include drop, create tables, create indexes, reset sequences

SET work_mem to '16MB', maintenance_work_mem to '512 MB';
EOF

# Run migration
pgloader sqlite_to_pg.load
```

---

## ✅ **Step 5: Verify Migration**

### **Test 1: Check Tables**

```bash
psql nala_conversations

# List tables
\dt

# Count records
SELECT COUNT(*) FROM conversations;
SELECT COUNT(*) FROM messages;

# View sample data
SELECT * FROM conversations LIMIT 5;
SELECT * FROM messages LIMIT 5;

\q
```

### **Test 2: Send a Message**

```bash
# Start backend
cd backend
python dev.py

# Send test message
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Testing PostgreSQL", "user_id": "test_user"}'

# Should work and save to PostgreSQL!
```

### **Test 3: Verify Data Persisted**

```bash
psql nala_conversations

SELECT c.id, c.title, COUNT(m.id) as msg_count
FROM conversations c
LEFT JOIN messages m ON m.conversation_id = c.id
GROUP BY c.id, c.title
ORDER BY c.created_at DESC;

\q
```

---

## 🔧 **Troubleshooting**

### **Issue 1: "could not connect to server"**

```bash
# Check if PostgreSQL is running
brew services list | grep postgresql  # macOS
sudo systemctl status postgresql      # Linux

# Start if not running
brew services start postgresql@15     # macOS
sudo systemctl start postgresql       # Linux
```

### **Issue 2: "authentication failed"**

```bash
# Edit pg_hba.conf to trust local connections
sudo nano /opt/homebrew/var/postgresql@15/pg_hba.conf  # macOS
sudo nano /etc/postgresql/15/main/pg_hba.conf          # Linux

# Change this line:
# local   all   all   peer
# To:
local   all   all   trust

# Restart PostgreSQL
brew services restart postgresql@15   # macOS
sudo systemctl restart postgresql     # Linux
```

### **Issue 3: "database does not exist"**

```bash
# Create database
createdb nala_conversations

# Or via psql
psql postgres -c "CREATE DATABASE nala_conversations;"
```

### **Issue 4: "column does not exist"**

This means tables weren't created. Run:

```bash
python -m backend.scripts.init_db --reset
```

---

## 🚀 **Production Deployment**

### **Environment Variables**

```bash
# Production .env (DO NOT commit to git!)
DATABASE_URL=postgresql://user:password@prod-db.example.com:5432/nala_prod

# Use environment variables on hosting platform:
# - Heroku: heroku config:set DATABASE_URL=...
# - Render: Set in dashboard
# - AWS: Use AWS Systems Manager Parameter Store
```

### **Security Best Practices**

1. **Use connection pooling:**
```python
# backend/config/database.py
self.engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_size=20,          # Max connections
    max_overflow=10,       # Extra connections when busy
    pool_recycle=3600      # Recycle connections after 1 hour
)
```

2. **Use SSL for cloud connections:**
```python
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

3. **Never commit `.env` to git:**
```bash
# .gitignore
.env
*.db
```

4. **Use secrets management:**
```bash
# AWS Secrets Manager, HashiCorp Vault, etc.
```

---

## 📊 **Performance Comparison**

### **Simple Benchmark**

```bash
# SQLite (baseline)
time (for i in {1..100}; do
  curl -s -X POST http://localhost:8000/api/v1/chat/message \
    -H "Content-Type: application/json" \
    -d '{"message": "Test", "user_id": "bench"}' > /dev/null
done)

# PostgreSQL (after migration)
# Run same test

# Typical results:
# SQLite: ~100 req/sec
# PostgreSQL (local): ~200 req/sec
# PostgreSQL (cloud): ~150 req/sec (network latency)
```

---

## 🔄 **Switching Back to SQLite**

If you need to revert:

```bash
# 1. Update .env
DATABASE_URL=sqlite:///./nala_conversations.db

# 2. Restart backend
cd backend
python dev.py

# SQLite database will be created/used automatically
```

---

## 📝 **Summary**

### **Quick Reference**

| Task | Command |
|------|---------|
| **Install PostgreSQL (macOS)** | `brew install postgresql@15` |
| **Start PostgreSQL** | `brew services start postgresql@15` |
| **Create database** | `createdb nala_conversations` |
| **Update .env** | `DATABASE_URL=postgresql://...` |
| **Initialize tables** | `python dev.py` (auto-creates tables) |
| **Connect to DB** | `psql nala_conversations` |
| **View tables** | `\dt` in psql |
| **Migrate data** | Use pgloader or custom script |
| **Verify** | `SELECT COUNT(*) FROM conversations;` |

### **Connection String Format**

```
postgresql://[user]:[password]@[host]:[port]/[database]

Examples:
postgresql://postgres:@localhost:5432/nala_conversations     # Local, no password
postgresql://user:pass@localhost:5432/nala_conversations     # Local, with password
postgresql://user:pass@db.example.com:5432/nala_prod       # Remote
```

---

## ✅ **Checklist**

- [ ] PostgreSQL installed and running
- [ ] Database created (`nala_conversations`)
- [ ] `.env` updated with PostgreSQL URL
- [ ] Backend restarted
- [ ] Tables created (check with `\dt`)
- [ ] Test message sent successfully
- [ ] Data persists in PostgreSQL
- [ ] Old SQLite file backed up (if needed)

---

**You're now running on PostgreSQL! 🎉**

For questions, see:
- [PERSISTENCE_EXPLAINED.md](./PERSISTENCE_EXPLAINED.md) - How database updates work
- [IMPLEMENTATION_COMPLETE.md](../IMPLEMENTATION_COMPLETE.md) - Testing guide
