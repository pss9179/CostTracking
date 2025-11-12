"""
SQLModel schema for trace events, users, and API keys.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Index, Column, JSON


class User(SQLModel, table=True):
    """User accounts with email/password authentication."""
    __tablename__ = "users"
    
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, description="User email")
    password_hash: str = Field(description="Bcrypt password hash")
    name: Optional[str] = Field(default=None, description="User display name")
    user_type: str = Field(default="solo_dev", description="User type: solo_dev or saas_founder")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation time")
    subscription_tier: str = Field(default="free", description="Subscription tier: free, pro, enterprise")
    
    class Config:
        indexes = [
            Index("idx_users_email", "email"),
        ]


class UserSignup(SQLModel):
    """Schema for user signup."""
    email: str
    password: str
    name: Optional[str] = None
    user_type: str = "solo_dev"  # solo_dev or saas_founder


class UserLogin(SQLModel):
    """Schema for user login."""
    email: str
    password: str


class UserResponse(SQLModel):
    """Public user data (no password)."""
    id: UUID
    email: str
    name: Optional[str]
    user_type: str
    created_at: datetime
    subscription_tier: str


class APIKey(SQLModel, table=True):
    """API keys for SDK authentication."""
    __tablename__ = "api_keys"
    
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True, description="Owner user ID")
    key_hash: str = Field(unique=True, index=True, description="bcrypt hash of the full API key")
    key_prefix: str = Field(description="Displayable prefix (e.g., llmo_sk_abc...)")
    name: str = Field(description="User-friendly name")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation time")
    last_used_at: Optional[datetime] = Field(default=None, description="Last usage timestamp")
    revoked_at: Optional[datetime] = Field(default=None, description="Revocation timestamp")
    
    class Config:
        indexes = [
            Index("idx_api_keys_user_id", "user_id"),
            Index("idx_api_keys_hash", "key_hash"),
        ]


class APIKeyCreate(SQLModel):
    """Schema for creating API keys."""
    name: str


class APIKeyResponse(SQLModel):
    """Response after creating an API key (includes plaintext key once)."""
    id: UUID
    name: str
    key: str  # Full plaintext key (only returned once!)
    key_prefix: str
    created_at: datetime


class APIKeyListItem(SQLModel):
    """API key list item (without full key)."""
    id: UUID
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: Optional[datetime]


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
    
    # Multi-tenancy and customer tracking
    tenant_id: str = Field(default="default_tenant", index=True, description="Tenant identifier (defaults to 'default_tenant' for solo devs)")
    user_id: Optional[UUID] = Field(default=None, foreign_key="users.id", index=True, description="Optional user reference (for auth)")
    customer_id: Optional[str] = Field(default=None, index=True, description="End-customer identifier (tenant's customers)")
    
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
            Index("idx_user_id", "user_id"),
            Index("idx_customer_id", "customer_id"),
            Index("idx_tenant_created", "tenant_id", "created_at"),
            Index("idx_tenant_customer", "tenant_id", "customer_id"),
            Index("idx_user_created", "user_id", "created_at"),
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
    tenant_id: Optional[str] = None  # Optional: defaults to "default_tenant" if not provided
    customer_id: Optional[str] = None  # Optional: for tracking tenant's end-customers
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    status: str = "ok"
    is_streaming: bool = False
    stream_cancelled: bool = False
    event_metadata: Optional[dict] = None
    # Note: tenant_id and user_id can be extracted from API key/auth, or sent explicitly

