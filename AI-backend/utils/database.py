import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor

# PostgreSQL connection URL in this format:
# postgresql://user:password@host:port/database
DATABASE_URL = os.getenv("CONVERSATION_DATABASE_URL")


def get_connection():
    """Get a database connection"""
    if not DATABASE_URL:
        raise ValueError("CONVERSATION_DATABASE_URL environment variable not set")
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_database():
    """Initialize the database with required tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                uid TEXT NOT NULL,
                session_number INTEGER NOT NULL,
                user_profile JSONB NOT NULL,
                session_info JSONB,
                chat_history JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(uid, session_number)
            )
        ''')
        
        # Create index for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sessions_uid ON sessions(uid)
        ''')
        
        conn.commit()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"Database init error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def save_session_to_db(uid: str, session_number: int, data: Dict[str, Any]) -> bool:
    """Save session data to database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        user_profile = json.dumps(data.get("user_profile", {}))
        session_info = json.dumps(data.get("session_info", {}))
        chat_history = json.dumps(data.get("chat_history", []))
        
        cursor.execute('''
            INSERT INTO sessions (uid, session_number, user_profile, session_info, chat_history, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (uid, session_number) DO UPDATE SET
                user_profile = EXCLUDED.user_profile,
                session_info = EXCLUDED.session_info,
                chat_history = EXCLUDED.chat_history,
                updated_at = EXCLUDED.updated_at
        ''', (uid, session_number, user_profile, session_info, chat_history, datetime.now()))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Database save error: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def load_session_from_db(uid: str, session_number: int) -> Optional[Dict[str, Any]]:
    """Load session data from database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT user_profile, session_info, chat_history
            FROM sessions
            WHERE uid = %s AND session_number = %s
        ''', (uid, session_number))
        
        row = cursor.fetchone()
        if row:
            return {
                "user_profile": row['user_profile'],
                "session_info": row['session_info'] or {},
                "chat_history": row['chat_history'] or []
            }
        return None
    except Exception as e:
        print(f"Database load error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def get_latest_session_for_user(uid: str) -> Optional[Dict[str, Any]]:
    """Get the most recent session for a user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT session_number, user_profile, session_info, chat_history
            FROM sessions
            WHERE uid = %s
            ORDER BY session_number DESC
            LIMIT 1
        ''', (uid,))
        
        row = cursor.fetchone()
        if row:
            return {
                "session_number": row['session_number'],
                "user_profile": row['user_profile'],
                "session_info": row['session_info'] or {},
                "chat_history": row['chat_history'] or []
            }
        return None
    except Exception as e:
        print(f"Database load error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def get_user_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Find a user by their name (case-insensitive)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT uid, session_number, user_profile, session_info
            FROM sessions
            WHERE LOWER(user_profile->>'name') = LOWER(%s)
            ORDER BY session_number DESC
            LIMIT 1
        ''', (name,))
        
        row = cursor.fetchone()
        if row:
            return {
                "uid": row['uid'],
                "session_number": row['session_number'],
                "user_profile": row['user_profile'],
                "session_info": row['session_info'] or {}
            }
        return None
    except Exception as e:
        print(f"Database search error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def list_users() -> List[Dict[str, Any]]:
    """List all unique users in the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT 
                uid,
                MAX(session_number) as last_session,
                MAX(user_profile->>'name') as name,
                MAX(updated_at) as last_updated
            FROM sessions
            GROUP BY uid
            ORDER BY MAX(updated_at) DESC
        ''')
        
        return [
            {
                "uid": row['uid'],
                "last_session": row['last_session'],
                "name": row['name'],
                "last_updated": row['last_updated']
            }
            for row in cursor.fetchall()
        ]
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def delete_user_sessions(uid: str) -> bool:
    """Delete all sessions for a user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM sessions WHERE uid = %s', (uid,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Database delete error: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()
