from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

<<<<<<< HEAD
    # Conversation Database (SQLite for local dev, PostgreSQL for prod)
    database_url: str = "sqlite:///./nala_conversations.db"
=======
    # Claude API settings
    claude_api_key: str =os.getenv("CLAUDE_API_KEY")
    claude_model: str = "claude-3-sonnet-20240229"
>>>>>>> 2eeaf78 (working e2e pipeline, rag connected to frontend via api handler)

    # Vector Database (PostgreSQL with pgvector - used by AI-backend)
    vector_db_host: str = "localhost"
    vector_db_port: str = "5432"
    vector_db_name: str = "chatbot_db"
    vector_db_user: str = "postgres"
    vector_db_password: str = "nala"

    # LLM API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # AI Configuration
    default_llm_model: str = "claude-sonnet-4"
    top_k_sources: int = 3
    min_similarity: float = 0.4

    # CORS
    cors_origins: List[str] = ["*"]

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
