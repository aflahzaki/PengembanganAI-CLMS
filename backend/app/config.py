"""Application configuration using pydantic-settings."""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # LLM Configuration
    LLM_BASE_URL: str = "https://api.groq.com/openai/v1"
    LLM_MODEL_NAME: str = "llama-3.3-70b-versatile"
    LLM_API_KEY: str = ""

    # ChromaDB Configuration
    CHROMA_DB_PATH: str = "data/chroma_db"

    # Templates Configuration
    TEMPLATES_DIR: str = "data/templates"

    # Embedding Configuration
    EMBEDDING_MODEL: str = "nomic-embed-text-v1.5"

    # Rate Limiting
    # Delay in seconds between API calls in clause-by-clause mode.
    # Set to 0 for local LLMs or paid tiers with no rate limit.
    RATE_LIMIT_DELAY_SECONDS: float = 2.5

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Application
    APP_NAME: str = "CLMS RAG Pipeline"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def data_absolute_path(self) -> Path:
        """Get absolute path for the data directory."""
        return Path(__file__).parent.parent / "data"

    @property
    def chroma_db_absolute_path(self) -> Path:
        """Get absolute path for ChromaDB storage."""
        path = Path(self.CHROMA_DB_PATH)
        if not path.is_absolute():
            path = Path(__file__).parent.parent / path
        return path

    @property
    def templates_absolute_path(self) -> Path:
        """Get absolute path for templates directory."""
        path = Path(self.TEMPLATES_DIR)
        if not path.is_absolute():
            path = Path(__file__).parent.parent / path
        return path


settings = Settings()
