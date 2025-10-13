"""
Database Initialization Script

Creates tables for conversation storage (separate from AI-backend vector DB).

Usage:
    python -m backend.scripts.init_db
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


def init_conversation_database():
    """Initialize the conversation database."""
    print("=" * 80)
    print("INITIALIZING CONVERSATION DATABASE")
    print("=" * 80)

    # TODO: Implement database initialization
    # 1. Import models and database config
    # from backend.config.settings import settings
    # from backend.config.database import init_database
    # from backend.models.base import Base

    # 2. Initialize database connection
    # print(f"\nDatabase URL: {settings.database_url}")
    # init_database(settings.database_url)

    # 3. Create tables
    # print("\nCreating tables...")
    # - conversations table
    # - messages table

    # 4. Verify creation
    # print("\n✓ Database initialized successfully")
    # print(f"  - Conversations table: created")
    # print(f"  - Messages table: created")

    print("\nTODO: Implement database initialization")
    print("See backend/scripts/init_db.py for details")


def reset_conversation_database():
    """Reset the conversation database (drop and recreate tables)."""
    print("=" * 80)
    print("RESETTING CONVERSATION DATABASE")
    print("=" * 80)
    print("\nWARNING: This will delete all conversations and messages!")

    response = input("Are you sure? (yes/no): ")
    if response.lower() != "yes":
        print("Aborted.")
        return

    # TODO: Implement database reset
    # 1. Drop all tables
    # 2. Recreate tables
    # 3. Verify

    print("\nTODO: Implement database reset")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Initialize conversation database")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database (drop and recreate tables)"
    )

    args = parser.parse_args()

    if args.reset:
        reset_conversation_database()
    else:
        init_conversation_database()
