"""
Helper to create events from HTTP/gRPC/WebSocket responses.

Used by interceptors when no proxy is available.
"""
import uuid
import time
import logging
from typing import Optional, Dict, Any
from llmobserve import buffer, context, config
from llmobserve.types import TraceEvent

logger = logging.getLogger("llmobserve")


def extract_provider_from_url(url: str) -> Optional[str]:
    """Extract provider from URL."""
    url_lower = url.lower()
    
    if "openai.com" in url_lower or "api.openai.com" in url_lower:
        return "openai"
    elif "anthropic.com" in url_lower or "api.anthropic.com" in url_lower:
        return "anthropic"
    elif "cohere.ai" in url_lower or "api.cohere.ai" in url_lower:
        return "cohere"
    elif "googleapis.com" in url_lower:
        if "generativelanguage" in url_lower:
            return "google"
        return "google-cloud"
    elif "huggingface" in url_lower:
        return "huggingface"
    elif "pinecone.io" in url_lower:
        return "pinecone"
    elif "replicate.com" in url_lower:
        return "replicate"
    elif "together.xyz" in url_lower or "together.ai" in url_lower:
        return "together"
    elif "perplexity.ai" in url_lower:
        return "perplexity"
    elif "mistral.ai" in url_lower:
        return "mistral"
    elif "groq.com" in url_lower:
        return "groq"
    elif "openrouter.ai" in url_lower or "openrouter" in url_lower:
        return "openrouter"
    
    return "unknown"


def extract_model_from_request(request_body: Optional[Dict], provider: str) -> Optional[str]:
    """Extract model from request body."""
    if not request_body:
        return None
    
    # Common patterns
    if isinstance(request_body, dict):
        return (
            request_body.get("model") or
            request_body.get("model_id") or
            request_body.get("engine") or
            None
        )
    
    return None


def extract_tokens_from_response(response_body: Optional[Dict], provider: str) -> tuple[Optional[int], Optional[int], Optional[int]]:
    """
    Extract token counts from response.
    
    Returns: (prompt_tokens, completion_tokens, total_tokens)
    """
    if not response_body or not isinstance(response_body, dict):
        return None, None, None
    
    # OpenAI format
    if "usage" in response_body:
        usage = response_body["usage"]
        return (
            usage.get("prompt_tokens"),
            usage.get("completion_tokens"),
            usage.get("total_tokens")
        )
    
    # Anthropic format
    if provider == "anthropic":
        return (
            response_body.get("usage", {}).get("input_tokens"),
            response_body.get("usage", {}).get("output_tokens"),
            None  # Anthropic doesn't provide total, we'll calculate it
        )
    
    # Cohere format
    if provider == "cohere" and "meta" in response_body:
        meta = response_body["meta"]
        billed_units = meta.get("billed_units", {})
        return (
            billed_units.get("input_tokens"),
            billed_units.get("output_tokens"),
            None
        )
    
    return None, None, None


def create_event_from_http_response(
    method: str,
    url: str,
    status_code: int,
    request_body: Optional[Dict],
    response_body: Optional[Dict],
    latency_ms: float,
    request_id: Optional[str] = None
) -> Optional[TraceEvent]:
    """
    Create a TraceEvent from HTTP request/response data.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        status_code: HTTP status code
        request_body: Parsed request JSON
        response_body: Parsed response JSON
        latency_ms: Request latency in milliseconds
        request_id: Optional request ID
    
    Returns:
        TraceEvent or None if event should not be created
    """
    # Extract provider
    provider = extract_provider_from_url(url)
    if provider == "unknown":
        logger.debug(f"[llmobserve] Unknown provider for URL: {url}")
        # Still track it, just mark as unknown
    
    # Extract model
    model = extract_model_from_request(request_body, provider)
    
    # Extract tokens
    input_tokens, output_tokens, total_tokens = extract_tokens_from_response(response_body, provider)
    
    # Calculate total if not provided
    if total_tokens is None and input_tokens and output_tokens:
        total_tokens = input_tokens + output_tokens
    
    # Get context
    run_id = context.get_run_id()
    span_id = request_id or str(uuid.uuid4())
    parent_span_id = context.get_current_span_id()
    section = context.get_current_section() or "/"
    section_path = context.get_section_path() or "/"
    customer_id = context.get_customer_id()
    tenant_id = config.get_tenant_id()
    
    # Get semantic label from semantic map
    try:
        from llmobserve.semantic_mapper import get_semantic_label_from_call_stack
        semantic_label = get_semantic_label_from_call_stack()
    except Exception:
        semantic_label = None
    
    # Create event (using backend schema field names!)
    event: TraceEvent = {
        "id": str(uuid.uuid4()),
        "run_id": run_id,
        "span_id": span_id,
        "parent_span_id": parent_span_id or "",
        "section": section,
        "section_path": section_path,
        "span_type": "http_fallback",  # Mark as HTTP fallback
        "provider": provider,
        "model": model,  # Backend expects "model" not "model_id"
        "endpoint": f"{method} {url}",
        "input_tokens": input_tokens or 0,  # Backend expects "input_tokens"
        "output_tokens": output_tokens or 0,  # Backend expects "output_tokens"
        "cached_tokens": 0,
        "latency_ms": latency_ms,
        "status": "ok" if status_code < 400 else "error",
        "is_streaming": False,
        "stream_cancelled": False,
        "cost_usd": 0.0,  # Will be calculated below
        "event_metadata": {
            "status_code": status_code,
            "url": url,
            "method": method
        }
    }
    
    # Add optional fields
    if customer_id:
        event["customer_id"] = customer_id
    if tenant_id:
        event["tenant_id"] = tenant_id
    if semantic_label:
        event["semantic_label"] = semantic_label
    
    # Calculate cost if we have token info
    if provider and model and total_tokens:
        try:
            from llmobserve.pricing import compute_cost
            cost = compute_cost(
                provider=provider,
                model_id=model,
                prompt_tokens=input_tokens or 0,
                completion_tokens=output_tokens or 0,
                total_tokens=total_tokens
            )
            if cost is not None:
                event["cost_usd"] = cost
        except Exception as e:
            logger.debug(f"[llmobserve] Failed to compute cost: {e}")
    
    return event


def should_create_event(url: str, status_code: int) -> bool:
    """
    Determine if we should create an event for this request.
    
    Skip:
    - Requests to our own collector
    - Failed requests (5xx)
    - Rate limited requests (429)
    """
    collector_url = config.get_collector_url()
    
    # Skip collector requests
    if collector_url and url.startswith(collector_url):
        return False
    
    # Skip failed requests
    if status_code >= 500:
        return False
    
    # Skip rate limited
    if status_code == 429:
        return False
    
    return True

