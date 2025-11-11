"""
SQLModel schema for trace events.
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Index, Column, JSON


class TraceEvent(SQLModel, table=True):
    """
    Represents a single traced operation (LLM call, vector DB query, etc.).
    """
    __tablename__ = "trace_events"
    
    # Primary key
    id: str = Field(primary_key=True, description="UUID4")
    
    # Grouping and hierarchy
    run_id: str = Field(index=True, description="Groups all calls in one user request")
    span_id: str = Field(description="Unique span identifier (future-proof for subtree)")
    parent_span_id: Optional[str] = Field(default=None, description="Parent span (NULL for MVP flat structure)")
    
    # Labels and categorization
    section: str = Field(index=True, description="User-defined label (e.g., 'retrieval', 'reasoning')")
    section_path: Optional[str] = Field(default=None, index=True, description="Full hierarchical section path (e.g., 'agent:researcher/tool:web_search')")
    span_type: str = Field(description="One of: llm, vector_db, api, other")
    provider: str = Field(description="e.g., openai, anthropic, pinecone")
    endpoint: str = Field(description="e.g., chat, embeddings, query, upsert")
    model: Optional[str] = Field(default=None, description="e.g., gpt-4o, text-embedding-3-small")
    tenant_id: Optional[str] = Field(default=None, index=True, description="Tenant identifier for multi-tenant tracking")
    customer_id: Optional[str] = Field(default=None, index=True, description="Customer/end-user identifier within a tenant")
    
    # Metrics
    input_tokens: int = Field(default=0, description="Input/prompt tokens")
    output_tokens: int = Field(default=0, description="Output/completion tokens")
    cached_tokens: int = Field(default=0, description="Cached input tokens (OpenAI prompt caching)")
    cost_usd: float = Field(default=0.0, description="Cost in USD")
    latency_ms: float = Field(default=0.0, description="Latency in milliseconds")
    
    # Status
    status: str = Field(default="ok", description="'ok', 'error', 'cancelled', 'timeout'")
    is_streaming: bool = Field(default=False, description="Whether this was a streaming response")
    stream_cancelled: bool = Field(default=False, description="Whether stream was cancelled early")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Event creation time")
    
    # Arbitrary metadata (renamed from 'metadata' to avoid SQLAlchemy reserved word)
    event_metadata: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="Arbitrary details (tenant_id, user_id, etc.)")
    
    class Config:
        # Create composite indexes
        indexes = [
            Index("idx_run_id", "run_id"),
            Index("idx_section", "section"),
            Index("idx_section_path", "section_path"),
            Index("idx_provider_model", "provider", "model"),
            Index("idx_created_at", "created_at"),
            Index("idx_tenant_id", "tenant_id"),
            Index("idx_customer_id", "customer_id"),
        ]


class TraceEventCreate(SQLModel):
    """Schema for creating trace events (used in API requests)."""
    id: str
    run_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    section: str
    section_path: Optional[str] = None
    span_type: str
    provider: str
    endpoint: str
    model: Optional[str] = None
    tenant_id: Optional[str] = None
    customer_id: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    status: str = "ok"
    is_streaming: bool = False
    stream_cancelled: bool = False
    event_metadata: Optional[dict] = None


class Tenant(SQLModel, table=True):
    """Tenant authentication and metadata."""
    __tablename__ = "tenants"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: str = Field(unique=True, index=True, description="Unique tenant identifier")
    name: str = Field(description="Tenant display name")
    api_key: str = Field(unique=True, index=True, description="API key for authentication")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Tenant creation time")
    
    class Config:
        indexes = [
            Index("idx_tenant_id", "tenant_id"),
            Index("idx_api_key", "api_key"),
        ]


class TenantCreate(SQLModel):
    """Schema for creating tenants."""
    tenant_id: str
    name: str

