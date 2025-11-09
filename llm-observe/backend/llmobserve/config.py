"""Configuration management using Pydantic Settings."""

import json
import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def find_env_file() -> str:
    """Find .env file in current directory or parent directory."""
    current_dir = Path(__file__).parent.parent.parent  # backend/llmobserve -> backend
    env_paths = [
        current_dir / ".env",  # backend/.env
        current_dir.parent / ".env",  # llm-observe/.env
    ]
    for env_path in env_paths:
        if env_path.exists():
            return str(env_path)
    return ".env"  # Fallback to default


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # OpenAI
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    
    # Pinecone (optional)
    pinecone_api_key: Optional[str] = Field(default=None, alias="PINECONE_API_KEY")
    pinecone_index_name: Optional[str] = Field(default="test", alias="PINECONE_INDEX_NAME")

    # Supabase (optional - can use SQLite instead)
    supabase_url: Optional[str] = Field(default=None, alias="SUPABASE_URL")
    supabase_db_password: Optional[str] = Field(default=None, alias="SUPABASE_DB_PASSWORD")
    
    # Optional: Direct database connection string (if provided, uses PostgreSQL/Supabase)
    # If not provided, will use SQLite for local development
    direct_database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")

    # Environment
    env: str = Field(default="development", alias="ENV")
    service_name: str = Field(default="llm-observe", alias="SERVICE_NAME")

    # Multi-tenancy
    tenant_header: str = Field(default="x-tenant-id", alias="TENANT_HEADER")

    # Privacy
    allow_content_capture: bool = Field(default=False, alias="ALLOW_CONTENT_CAPTURE")

    # Pricing (optional JSON string or path to JSON file)
    model_prices_json: Optional[str] = Field(default=None, alias="MODEL_PRICES_JSON")

    # OpenTelemetry
    otlp_endpoint: Optional[str] = Field(default=None, alias="OTLP_ENDPOINT")
    otlp_headers: Optional[str] = Field(default=None, alias="OTLP_HEADERS")

    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        """
        Get DATABASE_URL - either from env, construct from Supabase, or use SQLite.
        
        Priority:
        1. DATABASE_URL env var (if set)
        2. Construct from SUPABASE_URL + SUPABASE_DB_PASSWORD (if both set)
        3. SQLite (default for local development)
        """
        if self.direct_database_url:
            return self.direct_database_url
        
        # Construct from Supabase URL if both are provided
        if self.supabase_url and self.supabase_db_password:
            url = self.supabase_url.rstrip("/")
            if url.startswith("https://"):
                host = url.replace("https://", "").split(".")[0]
                from urllib.parse import quote_plus
                encoded_password = quote_plus(self.supabase_db_password)
                return (
                    f"postgresql://postgres:{encoded_password}"
                    f"@db.{host}.supabase.co:5432/postgres"
                )
        
        # Default to SQLite (will be handled in db.py)
        return "sqlite:///llmobserve.db"

    def load_model_prices(self) -> dict:
        """Load model prices from JSON string or file."""
        if not self.model_prices_json:
            return self._default_model_prices()

        # Try as JSON string first
        try:
            return json.loads(self.model_prices_json)
        except (json.JSONDecodeError, TypeError):
            pass

        # Try as file path
        price_path = Path(self.model_prices_json)
        if price_path.exists():
            with open(price_path) as f:
                return json.load(f)

        return self._default_model_prices()

    @staticmethod
    def _default_model_prices() -> dict:
        """Default OpenAI model pricing (as of 2024)."""
        return {
            "gpt-4o": {"prompt": 2.50, "completion": 10.00},  # per 1M tokens
            "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
            "gpt-4-turbo": {"prompt": 10.00, "completion": 30.00},
            "gpt-4": {"prompt": 30.00, "completion": 60.00},
            "gpt-3.5-turbo": {"prompt": 0.50, "completion": 1.50},
            "gpt-3.5-turbo-16k": {"prompt": 3.00, "completion": 4.00},
            # Pinecone pricing
            "pinecone-query": {"request": 0.000096},  # $0.096 per 1K queries
            "pinecone-upsert": {"vector": 0.0000012},  # $0.12 per 100K vectors
        }


# Global settings instance
settings = Settings()

