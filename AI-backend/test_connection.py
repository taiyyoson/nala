# test_connection.py
import psycopg2
import os
from dotenv import load_dotenv
import time

load_dotenv()

print("Testing database connection...")
print(f"Connecting to: {os.getenv('DATABASE_URL', 'NOT SET')[:50]}...")

try:
    start = time.time()
    conn = psycopg2.connect(
        os.getenv('DATABASE_URL'),
        connect_timeout=30,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5
    )
    elapsed = time.time() - start
    print(f"✓ Connected successfully in {elapsed:.2f}s")
    
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    print(f"✓ Database version: {version[:50]}")
    
    cur.execute("SELECT COUNT(*) FROM coaching_conversations;")
    count = cur.fetchone()[0]
    print(f"✓ Coaching conversations count: {count}")
    
    cur.close()
    conn.close()
    print("✓ Connection closed cleanly")
    
except psycopg2.OperationalError as e:
    print(f"✗ Connection failed: {e}")
except Exception as e:
    print(f"✗ Error: {e}")