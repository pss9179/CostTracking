"""SQLModel database models for cost tracking."""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class CostEvent(SQLModel, table=True):
    """Cost event record for tracking AI usage and costs per tenant/workflow."""

    __tablename__ = "cost_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: str = Field(index=True, max_length=100)
    workflow_id: Optional[str] = Field(default=None, index=True, max_length=255)
    provider: str = Field(max_length=100)  # e.g., "openai", "pinecone", "anthropic"
    model: Optional[str] = Field(default=None, max_length=100)  # e.g., "gpt-4o", "claude-3-opus"
    cost_usd: float = Field(default=0.0)
    duration_ms: float = Field(default=0.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    trace_id: Optional[str] = Field(default=None, max_length=32, index=True)
    span_id: Optional[str] = Field(default=None, max_length=16)
    # Additional metadata
    prompt_tokens: Optional[int] = Field(default=None)
    completion_tokens: Optional[int] = Field(default=None)
    total_tokens: Optional[int] = Field(default=None)
    operation: Optional[str] = Field(default=None, max_length=100)  # e.g., "query", "upsert", "chat"

