import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    # LLM settings
    default_llm_model: str = "claude-sonnet-4.5"
    top_k_sources: int = 3

    # Claude API settings
    claude_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    claude_model: str = "claude-3-sonnet-20240229"

    # OpenAI API settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # Database
    conv_db_url: str = os.getenv("CONV_DATABASE_URL", "sqlite:///./nala_dev.db")

    # CORS
    cors_origins: List[str] = ["*"]

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"


# Global settings instance
settings = Settings()
