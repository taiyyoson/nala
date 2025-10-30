"""
Database Configuration - Database connection and session management

Handles SQLAlchemy engine and session creation for conversation database.
"""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


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
        # Create engine with appropriate settings
        connect_args = {}
        if "sqlite" in database_url:
            # SQLite-specific: disable same thread check for async compatibility
            connect_args = {"check_same_thread": False}

        self.engine = create_engine(
            database_url,
            connect_args=connect_args,
            pool_pre_ping=True,  # Verify connections before using
            echo=False,  # Set to True for SQL query debugging
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

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
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    @contextmanager
    def session_scope(self):
        """
        Provide a transactional scope for database operations.

        Usage:
            with db_config.session_scope() as session:
                session.add(obj)
                # Auto-commits on success, rolls back on exception
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_tables(self):
        """Create all tables defined in models."""
        from backend.models.base import Base

        Base.metadata.create_all(bind=self.engine)
        print("✓ Database tables created")

    def drop_tables(self):
        """Drop all tables (use with caution!)."""
        from backend.models.base import Base

        Base.metadata.drop_all(bind=self.engine)
        print("✓ Database tables dropped")

    def health_check(self) -> bool:
        """
        Check if database connection is healthy.

        Returns:
            True if connection is working
        """
        try:
            with self.session_scope() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            print(f"Database health check failed: {e}")
            return False


# Global database instance (initialized in app startup)
db_config: DatabaseConfig = None


def init_database(database_url: str) -> DatabaseConfig:
    """
    Initialize the global database configuration.

    Args:
        database_url: Database connection URL

    Returns:
        DatabaseConfig instance
    """
    global db_config
    db_config = DatabaseConfig(database_url)
    db_config.create_tables()
    return db_config


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.

    Usage:
        @router.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    if db_config is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return db_config.get_session()
