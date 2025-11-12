"""
Type definitions for trace events.
"""
from typing import Optional, TypedDict
from datetime import datetime


class TraceEvent(TypedDict, total=False):
    """Schema for a trace event with hierarchical span tracking."""
    id: str
    run_id: str
    span_id: str
    parent_span_id: Optional[str]
    section: str
    section_path: Optional[str]  # Full hierarchical path (e.g., "agent:researcher/tool:web_search")
    span_type: str
    provider: str
    endpoint: str
    model: Optional[str]
    tenant_id: Optional[str]  # Tenant identifier (defaults to "default_tenant")
    customer_id: Optional[str]  # Tenant's end-customer identifier (optional)
    input_tokens: int
    output_tokens: int
    cached_tokens: int  # For OpenAI prompt caching
    cost_usd: float
    latency_ms: float
    status: str
    is_streaming: bool  # Whether this was a streaming response
    stream_cancelled: bool  # Whether stream was cancelled early
    event_metadata: Optional[dict]
    # Note: user_id is injected by the backend from API key, not sent by SDK

