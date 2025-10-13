import psycopg2
import os

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'chatbot_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD')
}
from dotenv import load_dotenv

load_dotenv()

# Support both DATABASE_URL and individual params
def get_db_connection():
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Use DATABASE_URL (Render style)
        return psycopg2.connect(database_url)
    else:
        # Use individual parameters (local style)
        return psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'chatbot_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '')
        )

def reset_database():
    """Drop and recreate the coaching_conversations table"""
    conn = get_db_connection()
    conn.autocommit = True
    cur = conn.cursor()
    
    print("Dropping existing table...")
    cur.execute("DROP TABLE IF EXISTS coaching_conversations CASCADE;")
    
    print("✓ Database reset complete\n")
    
    cur.close()
    conn.close()

def setup_database():
    """Create the table and indexes for coaching conversations"""
    
    # Connect to database
    conn = get_db_connection()
    conn.autocommit = True
    cur = conn.cursor()
    
    print("Creating vector extension...")
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    print("Creating coaching_conversations table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS coaching_conversations (
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
    """)
    
    print("Creating indexes...")
    cur.execute("""
        CREATE INDEX IF NOT EXISTS participant_embedding_idx 
        ON coaching_conversations 
        USING ivfflat (participant_embedding vector_cosine_ops)
        WITH (lists = 100);
    """)
    
    cur.execute("""
        CREATE INDEX IF NOT EXISTS context_category_idx 
        ON coaching_conversations (context_category);
    """)
    
    cur.execute("""
        CREATE INDEX IF NOT EXISTS goal_type_idx 
        ON coaching_conversations (goal_type);
    """)
    
    print("Database setup complete!")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    reset_database()
    setup_database()