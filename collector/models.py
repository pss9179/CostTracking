"""
SQLModel schema for trace events, users, and API keys.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Index, Column, JSON


class User(SQLModel, table=True):
    """User accounts - supports both Clerk and email/password authentication."""
    __tablename__ = "users"
    
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    clerk_user_id: Optional[str] = Field(default=None, unique=True, index=True, description="Clerk user ID (for Clerk auth)")
    email: str = Field(unique=True, index=True, description="User email")
    password_hash: Optional[str] = Field(default=None, description="Bcrypt password hash (for email/password auth)")
    name: Optional[str] = Field(default=None, description="User display name")
    user_type: str = Field(default="solo_dev", description="User type: solo_dev or saas_founder")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation time")
    subscription_tier: str = Field(default="free", description="Subscription tier: free, pro, enterprise")
    stripe_customer_id: Optional[str] = Field(default=None, index=True, description="Stripe customer ID")
    stripe_subscription_id: Optional[str] = Field(default=None, index=True, description="Stripe subscription ID")
    subscription_status: str = Field(default="free", description="Subscription status: free, active, canceled, past_due")
    promo_code: Optional[str] = Field(default=None, description="Promo code used for free access")
    
    class Config:
        indexes = [
            Index("idx_users_email", "email"),
            Index("idx_users_clerk_id", "clerk_user_id"),
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


class SpendingCap(SQLModel, table=True):
    """Spending caps for cost control."""
    __tablename__ = "spending_caps"
    
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True, description="Owner user ID")
    
    # Cap scope
    cap_type: str = Field(description="Type: 'global', 'provider', 'model', 'agent', 'customer'")
    target_name: Optional[str] = Field(default=None, description="Target name (e.g., 'openai', 'gpt-4', 'research_agent', 'customer_123')")
    
    # Cap limits
    limit_amount: float = Field(description="Dollar amount cap (e.g., 100.00 for $100)")
    period: str = Field(description="Period: 'daily', 'weekly', 'monthly'")
    
    # Enforcement mode
    enforcement: str = Field(default="alert", description="Enforcement: 'alert' (email only) or 'hard_block' (prevent requests)")
    exceeded_at: Optional[datetime] = Field(default=None, description="When cap was first exceeded in current period")
    
    # Alert settings
    alert_threshold: float = Field(default=0.8, description="Alert when % of cap is reached (0.8 = 80%)")
    alert_email: str = Field(description="Email to send alerts to")
    
    # Status
    enabled: bool = Field(default=True, description="Whether this cap is active")
    last_alerted_at: Optional[datetime] = Field(default=None, description="Last time alert was sent")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        indexes = [
            Index("idx_caps_user_id", "user_id"),
            Index("idx_caps_enabled", "enabled"),
        ]


class Alert(SQLModel, table=True):
    """Alert history for triggered spending caps."""
    __tablename__ = "alerts"
    
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    cap_id: UUID = Field(foreign_key="spending_caps.id", index=True)
    
    # Alert details
    alert_type: str = Field(description="Type: 'threshold_reached', 'cap_exceeded'")
    current_spend: float = Field(description="Current spend amount")
    cap_limit: float = Field(description="Cap limit amount")
    percentage: float = Field(description="Percentage of cap used")
    
    # Context
    target_type: str = Field(description="What triggered: 'provider', 'model', 'agent', etc.")
    target_name: str = Field(description="Name of target")
    period_start: datetime = Field(description="Start of current period")
    period_end: datetime = Field(description="End of current period")
    
    # Notification
    email_sent: bool = Field(default=False)
    email_sent_at: Optional[datetime] = Field(default=None)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        indexes = [
            Index("idx_alerts_user_id", "user_id"),
            Index("idx_alerts_cap_id", "cap_id"),
            Index("idx_alerts_created_at", "created_at"),
        ]


class CapCreate(SQLModel):
    """Schema for creating a spending cap."""
    cap_type: str
    target_name: Optional[str] = None
    limit_amount: float
    period: str
    enforcement: str = "alert"  # 'alert' or 'hard_block'
    alert_threshold: float = 0.8
    alert_email: str


class CapUpdate(SQLModel):
    """Schema for updating a spending cap."""
    limit_amount: Optional[float] = None
    alert_threshold: Optional[float] = None
    alert_email: Optional[str] = None
    enforcement: Optional[str] = None
    enabled: Optional[bool] = None


class CapResponse(SQLModel):
    """Response for spending cap."""
    id: UUID
    cap_type: str
    target_name: Optional[str]
    limit_amount: float
    period: str
    enforcement: str
    exceeded_at: Optional[datetime] = None
    alert_threshold: float
    alert_email: str
    enabled: bool
    current_spend: Optional[float] = None
    percentage_used: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class AlertResponse(SQLModel):
    """Response for alert."""
    id: UUID
    alert_type: str
    current_spend: float
    cap_limit: float
    percentage: float
    target_type: str
    target_name: str
    period_start: datetime
    period_end: datetime
    email_sent: bool
    created_at: datetime


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


class Pricing(SQLModel, table=True):
    """Pricing configuration for API providers and models."""
    __tablename__ = "pricing"
    
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    provider: str = Field(index=True, description="Provider name (e.g., 'openai', 'stripe')")
    model: Optional[str] = Field(default=None, index=True, description="Model name (e.g., 'gpt-4o', 'charges.create')")
    pricing_type: str = Field(default="token_based", description="Type: 'token_based', 'per_call', 'per_million', etc.")
    pricing_data: dict = Field(default={}, sa_column=Column(JSON), description="Pricing structure (JSON)")
    description: Optional[str] = Field(default=None, description="Human-readable description")
    source: Optional[str] = Field(default=None, description="Source URL or reference")
    region: Optional[str] = Field(default=None, description="Region for region-specific pricing")
    tier: Optional[str] = Field(default=None, index=True, description="Tier/plan name (e.g., 'free', 'serverless', 'standard')")
    effective_date: datetime = Field(default_factory=datetime.utcnow, description="When pricing became effective")
    expires_at: Optional[datetime] = Field(default=None, description="When pricing expires")
    is_active: bool = Field(default=True, description="Whether this pricing is currently active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        indexes = [
            Index("idx_pricing_provider_model", "provider", "model"),
            Index("idx_pricing_active", "is_active"),
            Index("idx_pricing_tier", "tier"),
        ]


class ProviderTier(SQLModel, table=True):
    """User/tenant provider tier configuration."""
    __tablename__ = "provider_tiers"
    
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: Optional[UUID] = Field(default=None, foreign_key="users.id", index=True, description="User ID (for single-user accounts)")
    tenant_id: Optional[str] = Field(default=None, index=True, description="Tenant ID (for multi-tenant accounts)")
    provider: str = Field(index=True, description="Provider name (e.g., 'pinecone', 'openai')")
    tier: str = Field(description="Tier name (e.g., 'free', 'serverless', 'standard', 'dedicated')")
    plan_name: Optional[str] = Field(default=None, description="Human-readable plan name")
    is_active: bool = Field(default=True, description="Whether this tier config is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        indexes = [
            Index("idx_provider_tiers_tenant_provider", "tenant_id", "provider"),
            Index("idx_provider_tiers_user_id", "user_id"),
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

