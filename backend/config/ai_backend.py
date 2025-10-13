"""
AI Backend Configuration - Settings for integrating with AI-backend

Contains configuration for connecting to the RAG system and vector database.
"""

import os
from pathlib import Path
from typing import Optional


class AIBackendConfig:
    """
    Configuration for AI backend integration.

    This configures access to:
    - AI-backend Python modules (RAG system)
    - PostgreSQL vector database (coaching_conversations table)
    - OpenAI/Anthropic API credentials
    """

    def __init__(self):
        """Initialize AI backend configuration from environment."""

        # AI-backend module path
        self.ai_backend_path = self._get_ai_backend_path()

        # Vector database (PostgreSQL with pgvector)
        self.vector_db_host = os.getenv("VECTOR_DB_HOST", "localhost")
        self.vector_db_port = os.getenv("VECTOR_DB_PORT", "5432")
        self.vector_db_name = os.getenv("VECTOR_DB_NAME", "chatbot_db")
        self.vector_db_user = os.getenv("VECTOR_DB_USER", "postgres")
        self.vector_db_password = os.getenv("VECTOR_DB_PASSWORD", "nala")

        # LLM API Keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

        # RAG configuration
        self.default_model = os.getenv("DEFAULT_LLM_MODEL", "claude-sonnet-4")
        self.top_k_sources = int(os.getenv("TOP_K_SOURCES", "3"))
        self.min_similarity = float(os.getenv("MIN_SIMILARITY", "0.4"))

    def _get_ai_backend_path(self) -> str:
        """Get absolute path to AI-backend directory."""
        # Assuming backend/ and AI-backend/ are siblings
        backend_dir = Path(__file__).parent.parent
        ai_backend_dir = backend_dir.parent / "AI-backend"
        return str(ai_backend_dir.absolute())

    @property
    def vector_db_url(self) -> str:
        """Get PostgreSQL connection URL for vector database."""
        return f"postgresql://{self.vector_db_user}:{self.vector_db_password}@{self.vector_db_host}:{self.vector_db_port}/{self.vector_db_name}"

    def validate(self) -> bool:
        """
        Validate configuration.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If required configuration is missing
        """
        # 1. Check AI-backend path exists
        ai_backend_path = Path(self.ai_backend_path)
        if not ai_backend_path.exists():
            raise ValueError(f"AI-backend path does not exist: {self.ai_backend_path}")

        # 2. Check at least one LLM API key is present
        if not self.openai_api_key and not self.anthropic_api_key:
            raise ValueError("At least one LLM API key (OpenAI or Anthropic) must be configured")

        # 3. Check vector DB credentials
        if not self.vector_db_user or not self.vector_db_password:
            raise ValueError("Vector database credentials (user and password) are required")

        if not self.vector_db_host or not self.vector_db_name:
            raise ValueError("Vector database host and name are required")

        return True

    def to_dict(self) -> dict:
        """
        Export configuration as dictionary (for logging/debugging).

        Returns:
            Dict with non-sensitive config values
        """
        return {
            "ai_backend_path": self.ai_backend_path,
            "vector_db_host": self.vector_db_host,
            "vector_db_name": self.vector_db_name,
            "default_model": self.default_model,
            "top_k_sources": self.top_k_sources,
            "min_similarity": self.min_similarity,
            "openai_configured": bool(self.openai_api_key),
            "anthropic_configured": bool(self.anthropic_api_key),
        }


# Global config instance
ai_config = AIBackendConfig()
