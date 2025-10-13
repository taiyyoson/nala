"""
Database Configuration - Database connection and session management

Handles SQLAlchemy engine and session creation for conversation database.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os


class DatabaseConfig:
    """
    Database configuration and connection management.

    This handles the conversation database (SQLite/PostgreSQL for conversations),
    separate from the AI-backend's PostgreSQL vector database.
    """

    def __init__(self, database_url: str):
        """
        Initialize database configuration.

        Args:
            database_url: SQLAlchemy database URL
                         Examples:
                         - SQLite: "sqlite:///./nala_conversations.db"
                         - PostgreSQL: "postgresql://user:pass@localhost/dbname"
        """
        # TODO: Create engine
        # self.engine = create_engine(
        #     database_url,
        #     connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
        #     pool_pre_ping=True  # Verify connections before using
        # )

        # TODO: Create session factory
        # self.SessionLocal = sessionmaker(
        #     autocommit=False,
        #     autoflush=False,
        #     bind=self.engine
        # )
        pass

    def get_session(self) -> Generator[Session, None, None]:
        """
        Get database session (for dependency injection).

        Yields:
            SQLAlchemy Session

        Usage in FastAPI:
            @app.get("/endpoint")
            def endpoint(db: Session = Depends(get_db)):
                ...
        """
        # TODO: Implement session management
        # db = self.SessionLocal()
        # try:
        #     yield db
        # finally:
        #     db.close()
        raise NotImplementedError("Session management not yet implemented")

    def create_tables(self):
        """Create all tables defined in models."""
        # TODO: Create tables
        # from backend.models.base import Base
        # Base.metadata.create_all(bind=self.engine)
        pass

    def drop_tables(self):
        """Drop all tables (use with caution!)."""
        # TODO: Drop tables
        # from backend.models.base import Base
        # Base.metadata.drop_all(bind=self.engine)
        pass


# Global database instance (initialized in app startup)
db_config: DatabaseConfig = None


def init_database(database_url: str):
    """
    Initialize the global database configuration.

    Args:
        database_url: Database connection URL
    """
    global db_config
    # TODO: Initialize database
    # db_config = DatabaseConfig(database_url)
    # db_config.create_tables()
    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.

    Usage:
        @router.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    # TODO: Return session from global db_config
    # return db_config.get_session()
    raise NotImplementedError("Database dependency not yet implemented")
