"""
Main observe() function to initialize auto-instrumentation.
"""
from typing import Optional
from llmobserve import config, buffer, context
from llmobserve.openai_patch import patch_openai
from llmobserve.pinecone_patch import patch_pinecone


def observe(
    collector_url: str,
    api_key: Optional[str] = None,
    flush_interval_ms: int = 500,
    tenant_id: Optional[str] = None,
    customer_id: Optional[str] = None
) -> None:
    """
    Initialize LLM observability with auto-instrumentation.
    
    This function:
    1. Configures the SDK with collector URL and settings
    2. Applies monkey-patches to supported providers (OpenAI, Pinecone)
    3. Starts the event buffer flush timer
    
    Args:
        collector_url: URL of the collector API (e.g., "http://localhost:8000")
        api_key: Optional API key for collector authentication
        flush_interval_ms: How often to flush events to collector (default: 500ms)
        tenant_id: Optional tenant identifier for multi-tenant tracking
        customer_id: Optional customer identifier for per-customer tracking
    
    Example:
        >>> from llmobserve import observe
        >>> observe("http://localhost:8000")
        >>> observe("http://localhost:8000", tenant_id="acme-corp", customer_id="user_123")
    """
    # Configure SDK
    config.configure(
        collector_url=collector_url,
        api_key=api_key,
        flush_interval_ms=flush_interval_ms,
        tenant_id=tenant_id,
        customer_id=customer_id
    )
    
    # Set tenant in context if provided
    if tenant_id:
        context.set_tenant_id(tenant_id)
    
    # Set customer in context if provided
    if customer_id:
        context.set_customer_id(customer_id)
    
    if not config.is_enabled():
        return
    
    # Apply patches
    patch_openai()
    patch_pinecone()
    
    # Start flush timer
    buffer.start_flush_timer()

