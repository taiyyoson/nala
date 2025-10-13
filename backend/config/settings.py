import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    # Claude API settings
    claude_api_key: str =os.getenv("CLAUDE_API_KEY")
    claude_model: str = "claude-3-sonnet-20240229"

    # Database
    database_url: str = "sqlite:///./nala_dev.db"

    # CORS
    cors_origins: List[str] = ["*"]

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
