"""
Database Initialization Script

Creates tables for conversation storage (separate from AI-backend vector DB).

Usage:
    python -m backend.scripts.init_db [--reset]
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir.parent))

from backend.config.settings import settings
from backend.config.database import DatabaseConfig
from backend.models import Base


def init_conversation_database():
    """Initialize the conversation database."""
    print("=" * 80)
    print("INITIALIZING CONVERSATION DATABASE")
    print("=" * 80)

    # Database URL
    database_url = settings.database_url
    print(f"\nDatabase URL: {database_url}")

    # Initialize database connection
    db_config = DatabaseConfig(database_url)

    print("\nCreating tables...")
    db_config.create_tables()

    # Verify tables created
    print("\n✓ Database initialized successfully!")
    print(f"  - conversations table: created")
    print(f"  - messages table: created")

    # Health check
    print("\nPerforming health check...")
    if db_config.health_check():
        print("✓ Database connection is healthy")
    else:
        print("✗ Database connection failed")
        return False

    return True


def reset_conversation_database():
    """Reset the conversation database (drop and recreate tables)."""
    print("=" * 80)
    print("RESETTING CONVERSATION DATABASE")
    print("=" * 80)
    print("\n⚠️  WARNING: This will delete all conversations and messages!")

    response = input("\nAre you sure? Type 'yes' to confirm: ")
    if response.lower() != "yes":
        print("\nAborted.")
        return False

    # Database URL
    database_url = settings.database_url
    print(f"\nDatabase URL: {database_url}")

    # Initialize database connection
    db_config = DatabaseConfig(database_url)

    print("\nDropping tables...")
    db_config.drop_tables()

    print("Recreating tables...")
    db_config.create_tables()

    print("\n✓ Database reset complete!")
    print(f"  - conversations table: recreated")
    print(f"  - messages table: recreated")

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Initialize conversation database")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database (drop and recreate tables)"
    )

    args = parser.parse_args()

    try:
        if args.reset:
            success = reset_conversation_database()
        else:
            success = init_conversation_database()

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
