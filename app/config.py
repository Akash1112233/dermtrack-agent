from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API keys
    groq_api_key: str = Field(min_length=1)
    google_api_key: str = Field(min_length=1)
    deepgram_api_key: str = Field(min_length=1)

    # Database
    mongodb_uri: str = Field(min_length=1)
    mongodb_database: str = Field(min_length=1)

    # Model configuration
    groq_transcription_model: str = "whisper-large-v3"
    deepgram_stt_model: str = "nova-3"
    gemini_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    deepgram_tts_model: str = "aura-2-thalia-en"

    # Application configuration
    app_env: str = "development"
    log_level: str = "INFO"
    store_media_files: bool = False
    tavily_api_key: str | None = None
    tavily_api_url: str = "https://api.tavily.com/search"
    tavily_enabled: bool = False
    tavily_max_results: int = Field(default=5, ge=1, le=10)
    tavily_timeout_seconds: float = Field(default=10.0, gt=0, le=60)
    tavily_allowed_domains: str = "aad.org,nhs.uk,medlineplus.gov,cdc.gov,who.int,bad.org.uk,nice.org.uk"
    vector_store_backend: str = "atlas"
    chroma_persist_directory: str = "data/chroma"
    chroma_collection_name: str = "dermtrack_knowledge"

@lru_cache
def get_settings() -> Settings:
    """Return a cached application settings instance."""
    return Settings()