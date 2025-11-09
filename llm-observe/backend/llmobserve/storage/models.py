"""SQLModel database models for spans and traces."""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class SpanSummary(SQLModel, table=True):
    """Summary of an LLM span for storage and querying."""

    __tablename__ = "span_summaries"

    id: Optional[int] = Field(default=None, primary_key=True)
    trace_id: str = Field(index=True, max_length=32)
    span_id: str = Field(index=True, max_length=16)
    parent_span_id: Optional[str] = Field(default=None, max_length=16)
    name: str = Field(max_length=255)
    model: Optional[str] = Field(default=None, max_length=100)
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    cost_usd: float = Field(default=0.0)
    start_time: float  # Unix timestamp
    duration_ms: Optional[float] = Field(default=None)
    tenant_id: str = Field(index=True, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Trace(SQLModel, table=True):
    """Trace metadata for aggregation."""

    __tablename__ = "traces"

    id: Optional[int] = Field(default=None, primary_key=True)
    trace_id: str = Field(unique=True, index=True, max_length=32)
    tenant_id: str = Field(index=True, max_length=100)
    root_span_name: Optional[str] = Field(default=None, max_length=255)
    workflow_name: Optional[str] = Field(default=None, index=True, max_length=255)
    total_cost_usd: float = Field(default=0.0)
    total_tokens: int = Field(default=0)
    span_count: int = Field(default=0)
    start_time: float  # Unix timestamp
    duration_ms: Optional[float] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

