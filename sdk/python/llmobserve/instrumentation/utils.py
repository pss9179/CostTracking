"""
Shared utilities for instrumentation.

Provides common functions for token estimation, usage extraction, and event tracking.
"""
import logging
import time
import uuid
from typing import Any, Optional

logger = logging.getLogger("llmobserve")

# Try to import tiktoken
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


def get_tokenizer(model: Optional[str]) -> Any:
    """Get tiktoken tokenizer for a model, with fallback."""
    if not TIKTOKEN_AVAILABLE:
        return None
    
    try:
        return tiktoken.encoding_for_model(model) if model else None
    except KeyError:
        # Fallback to cl100k_base (used by gpt-4, gpt-3.5-turbo)
        return tiktoken.get_encoding("cl100k_base")


def estimate_tokens(text: str, model: Optional[str]) -> int:
    """Estimate token count for text using tiktoken."""
    if not TIKTOKEN_AVAILABLE or not text:
        return 0
    
    try:
        encoding = get_tokenizer(model)
        if encoding:
            return len(encoding.encode(text))
    except Exception as e:
        logger.debug(f"[llmobserve] Failed to estimate tokens: {e}")
    
    return 0


def estimate_input_tokens_from_messages(messages: list, model: Optional[str]) -> int:
    """Estimate input tokens from chat messages."""
    if not TIKTOKEN_AVAILABLE or not messages:
        return 0
    
    try:
        encoding = get_tokenizer(model)
        if not encoding:
            return 0
        
        total_tokens = 3  # Start with reply priming tokens
        
        for message in messages:
            total_tokens += 3  # role, content, separator
            
            if isinstance(message, dict):
                role = message.get("role", "")
                content = message.get("content", "")
            else:
                role = getattr(message, "role", "")
                content = getattr(message, "content", "")
            
            total_tokens += len(encoding.encode(str(role)))
            total_tokens += len(encoding.encode(str(content)))
        
        return total_tokens
    except Exception as e:
        logger.debug(f"[llmobserve] Failed to estimate input tokens: {e}")
        return 0


def extract_openai_usage(response: Any, method_name: str) -> tuple[int, int, int]:
    """Extract input_tokens, output_tokens, and cached_tokens from OpenAI response."""
    input_tokens = 0
    output_tokens = 0
    cached_tokens = 0
    
    if hasattr(response, "usage") and response.usage:
        usage = response.usage
        input_tokens = getattr(usage, "prompt_tokens", 0)
        output_tokens = getattr(usage, "completion_tokens", 0)
        
        if hasattr(usage, "prompt_tokens_details"):
            details = usage.prompt_tokens_details
            if details and hasattr(details, "cached_tokens"):
                cached_tokens = getattr(details, "cached_tokens", 0)
                input_tokens = input_tokens - cached_tokens
    
    return input_tokens, output_tokens, cached_tokens


def track_openai_call(
    method_name: str,
    model: Optional[str],
    start_time: float,
    response: Any,
    error: Optional[Exception] = None,
    is_streaming: bool = False,
    stream_cancelled: bool = False,
    extra_params: Optional[dict] = None
) -> None:
    """Track a single OpenAI API call."""
    from llmobserve import buffer, context, pricing
    from llmobserve.retry_tracking import enrich_event_with_retry_metadata
    
    latency_ms = (time.time() - start_time) * 1000
    
    # Extract usage
    input_tokens, output_tokens, cached_tokens = extract_openai_usage(response, method_name)
    
    # Calculate cost
    cost = pricing.compute_cost(
        provider="openai",
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_tokens=cached_tokens
    )
    
    # Get hierarchical section information
    section_path = context.get_section_path()
    span_id = context.get_current_span_id() or str(uuid.uuid4())
    parent_span_id = context.get_parent_span_id()
    
    # Detect status
    status = "cancelled" if stream_cancelled else ("error" if error else "ok")
    
    if error:
        error_str = str(error).lower()
        if "429" in error_str or "rate" in error_str:
            status = "rate_limited"
    
    # Create event
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "section": context.get_current_section(),
        "section_path": section_path,
        "span_type": "llm",
        "provider": "openai",
        "endpoint": method_name,
        "model": model,
        "tenant_id": config.get_tenant_id(),
        "customer_id": context.get_customer_id(),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_tokens": int(cached_tokens),
        "cost_usd": cost,
        "latency_ms": latency_ms,
        "status": status,
        "is_streaming": is_streaming,
        "stream_cancelled": stream_cancelled,
        "event_metadata": extra_params if extra_params else {},
        "schema_version": "1.0",  # Schema version for collector
    }
    
    # Enrich with retry metadata
    event = enrich_event_with_retry_metadata(event)
    
    buffer.add_event(event)

