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
    
    # Instrumentation toggle - use official GenAI instrumentation if True
    use_genai_instrumentor: bool = Field(default=False, alias="USE_GENAI_INSTRUMENTOR")
    
    # Function tracing configuration
    auto_function_tracing: bool = Field(default=True, alias="LLMOBSERVE_AUTO_FUNCTION_TRACING")
    function_patterns: str = Field(default="*", alias="LLMOBSERVE_FUNCTION_PATTERNS")  # Default to "*" to wrap all functions
    exclude_modules: str = Field(default="test,__pycache__", alias="LLMOBSERVE_EXCLUDE_MODULES")

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
        """Default model pricing for LLMs, vector DBs, embeddings, and inference APIs (as of 2024)."""
        return {
            # OpenAI models (per 1M tokens)
            "gpt-4o": {"prompt": 2.50, "completion": 10.00},
            "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
            "gpt-4-turbo": {"prompt": 10.00, "completion": 30.00},
            "gpt-4": {"prompt": 30.00, "completion": 60.00},
            "gpt-3.5-turbo": {"prompt": 0.50, "completion": 1.50},
            "gpt-3.5-turbo-16k": {"prompt": 3.00, "completion": 4.00},
            "text-embedding-3-small": {"prompt": 0.02, "completion": 0.0},
            "text-embedding-3-large": {"prompt": 0.13, "completion": 0.0},
            # Anthropic models (per 1M tokens)
            "claude-3-5-sonnet-20241022": {"prompt": 3.00, "completion": 15.00},
            "claude-3-5-sonnet": {"prompt": 3.00, "completion": 15.00},
            "claude-3-opus": {"prompt": 15.00, "completion": 75.00},
            "claude-3-sonnet": {"prompt": 3.00, "completion": 15.00},
            "claude-3-haiku": {"prompt": 0.25, "completion": 1.25},
            # Cohere models (per 1M tokens)
            "command-r-plus": {"prompt": 3.00, "completion": 15.00},
            "command-r": {"prompt": 0.50, "completion": 1.50},
            "command": {"prompt": 1.00, "completion": 2.00},
            "cohere-embed-v3": {"prompt": 0.10, "completion": 0.0},
            # Mistral models (per 1M tokens)
            "mistral-large": {"prompt": 8.00, "completion": 24.00},
            "mistral-medium": {"prompt": 2.70, "completion": 8.10},
            "mistral-small": {"prompt": 0.20, "completion": 0.60},
            # Google Gemini models (per 1M tokens)
            "gemini-1.5-pro": {"prompt": 1.25, "completion": 5.00},
            "gemini-1.5-flash": {"prompt": 0.075, "completion": 0.30},
            "gemini-pro": {"prompt": 0.50, "completion": 1.50},
            "embedding-001": {"prompt": 0.10, "completion": 0.0},
            # xAI models (per 1M tokens)
            "grok-beta": {"prompt": 5.00, "completion": 15.00},
            # AWS Bedrock models (per 1M tokens) - approximate pricing
            "anthropic.claude-3-5-sonnet": {"prompt": 3.00, "completion": 15.00},
            "anthropic.claude-3-opus": {"prompt": 15.00, "completion": 75.00},
            "amazon.titan-embed": {"prompt": 0.10, "completion": 0.0},
            # Together.ai models (per 1M tokens)
            "togethercomputer/llama-2-70b": {"prompt": 0.70, "completion": 0.90},
            "meta-llama/Llama-2-70b-chat-hf": {"prompt": 0.70, "completion": 0.90},
            # Vector Database pricing
            "pinecone-query": {"request": 0.000096},  # $0.096 per 1K queries
            "pinecone-upsert": {"vector": 0.0000012},  # $0.12 per 100K vectors
            "weaviate-query": {"request": 0.0},  # Free tier, paid plans vary
            "weaviate-search": {"request": 0.0},
            "qdrant-search": {"request": 0.0},  # Self-hosted free, cloud pricing varies
            "qdrant-scroll": {"request": 0.0},
            "qdrant-retrieve": {"request": 0.0},
            "milvus-search": {"request": 0.0},  # Self-hosted free, cloud pricing varies
            "milvus-query": {"request": 0.0},
            "chroma-query": {"request": 0.0},  # Open source, free
            "chroma-get": {"request": 0.0},
            "redisvector-search": {"request": 0.0},  # Redis pricing varies
            "redisvector-ft": {"request": 0.0},
            # Embeddings APIs (per 1M tokens)
            "jinaai-embed": {"prompt": 0.05, "completion": 0.0},
            "voyageai-embed": {"prompt": 0.10, "completion": 0.0},
            # Inference APIs (approximate pricing)
            "replicate-run": {"request": 0.0001},  # Varies by model, approximate
            "huggingface-text": {"request": 0.0},  # Free tier available
            "huggingface-embed": {"request": 0.0},
            "deepgram-transcribe": {"request": 0.0043},  # $0.0043 per minute
            "elevenlabs-generate": {"request": 0.30},  # $0.30 per 1000 characters
        }


# Global settings instance
settings = Settings()

