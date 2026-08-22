import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    SARVAM_API_KEY: Optional[str] = None
    EMBEDDING_PROVIDER: str = "local" # local or external
    EMBEDDING_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"
    QDRANT_MODE: str = os.getenv("QDRANT_MODE", "local") # local or cloud
    
    @property
    def clean_qdrant_url(self) -> Optional[str]:
        val = os.getenv("QDRANT_URL")
        return val.strip() if val else None

    QDRANT_URL: Optional[str] = os.getenv("QDRANT_URL", None)
    QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY", None)
    VECTOR_DB_URL: str = "local"
    VECTOR_DB_API_KEY: Optional[str] = None
    GENERATION_PROVIDER: str = "gemini" # gemini, openai, anthropic
    GENERATION_MODEL: str = "gemini-2.5-flash"
    GENERATION_API_KEY: Optional[str] = None
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
