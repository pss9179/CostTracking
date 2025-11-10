"""Generic HTTP wrapper for tracking external API calls."""

import time
from typing import Any, Optional

import httpx
from opentelemetry import baggage

from llmobserve.exporter import get_exporter
from llmobserve.tracer import get_current_trace_id, get_current_span_id


def tracked_request(
    method: str,
    url: str,
    **kwargs: Any,
) -> httpx.Response:
    """
    Make an HTTP request and track it.

    Usage:
        from llmobserve.providers import tracked_request
        response = tracked_request("GET", "https://api.example.com/data")
    """
    start_time = time.time()
    exporter = get_exporter()
    
    # Make request
    with httpx.Client() as client:
        response = client.request(method, url, **kwargs)
    
    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000
    
    # Extract provider from URL
    provider = "http"
    if "api.openai.com" in url:
        provider = "openai"
    elif "api.anthropic.com" in url:
        provider = "anthropic"
    elif "api.pinecone.io" in url:
        provider = "pinecone"
    
    # Get context
    tenant_id = baggage.get_baggage("tenant_id") or "default"
    workflow_id = baggage.get_baggage("workflow_id")
    trace_id = get_current_trace_id()
    span_id = get_current_span_id()
    
    # Record cost (0.0 for HTTP, but track duration)
    exporter.record_cost(
        tenant_id=tenant_id,
        provider=provider,
        cost_usd=0.0,
        duration_ms=duration_ms,
        workflow_id=workflow_id,
        trace_id=trace_id,
        span_id=span_id,
        operation=method.lower(),
    )
    
    return response

