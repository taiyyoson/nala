import os
from utils.database import init_database, save_session_to_db, load_session_from_db, list_users

# Check connection string exists
db_url = os.getenv("CONVERSATION_DATABASE_URL")
if not db_url:
    print("❌ CONVERSATION_DATABASE_URL not set!")
    print("Set it with: export CONVERSATION_DATABASE_URL='postgresql://...'")
    exit(1)

print(f"✓ CONVERSATION_DATABASE_URL is set")

# Try to initialize
print("\nInitializing database...")
init_database()

# Try a test save
print("\nTesting save...")
test_data = {
    "user_profile": {"uid": "test123", "name": "Test User", "goals": []},
    "session_info": {"session_number": 1},
    "chat_history": []
}
if save_session_to_db("test123", 1, test_data):
    print("✓ Save successful")
else:
    print("❌ Save failed")

# Try a test load
print("\nTesting load...")
loaded = load_session_from_db("test123", 1)
if loaded:
    print(f"✓ Load successful: {loaded['user_profile']['name']}")
else:
    print("❌ Load failed")

# List users
print("\nListing users...")
users = list_users()
print(f"✓ Found {len(users)} user(s)")
for u in users:
    print(f"  - {u['name']} ({u['uid']})")