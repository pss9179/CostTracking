"""
Main observe() function to initialize auto-instrumentation.

Uses the new modular instrumentation API with fail-open safety.
"""
import logging
import os
from typing import Optional
from llmobserve import config, buffer, context
from llmobserve.instrumentation import auto_instrument

logger = logging.getLogger("llmobserve")


def observe(
    collector_url: Optional[str] = None,
    api_key: Optional[str] = None,
    flush_interval_ms: int = 500,
    customer_id: Optional[str] = None
) -> None:
    """
    Initialize LLM observability with auto-instrumentation.
    
    This function:
    1. Configures the SDK with collector URL and API key
    2. Applies monkey-patches to supported providers (OpenAI, Pinecone)
    3. Starts the event buffer flush timer
    
    Args:
        collector_url: URL of the collector API (e.g., "http://localhost:8000").
                      If None, reads from LLMOBSERVE_COLLECTOR_URL env var.
        api_key: API key for authentication (get from dashboard).
                If None, reads from LLMOBSERVE_API_KEY env var.
        flush_interval_ms: How often to flush events to collector (default: 500ms).
                          Can be overridden with LLMOBSERVE_FLUSH_INTERVAL_MS env var.
        customer_id: Optional customer identifier for tracking your end-users.
                    Can be set via LLMOBSERVE_CUSTOMER_ID env var.
    
    Example:
        >>> import llmobserve
        >>> # Simple: uses env vars
        >>> llmobserve.observe()
        >>> 
        >>> # Or explicit:
        >>> llmobserve.observe(
        ...     collector_url="http://localhost:8000",
        ...     api_key="llmo_sk_abc123..."
        ... )
        >>> # Track costs per your end-customer
        >>> from llmobserve import set_customer_id
        >>> set_customer_id("customer_xyz")
    """
    # Global initialization guard
    if hasattr(observe, "_initialized"):
        logger.debug("[llmobserve] Already initialized, skipping")
        return
    
    # Read from env vars if not provided
    if collector_url is None:
        collector_url = os.getenv("LLMOBSERVE_COLLECTOR_URL")
    
    if api_key is None:
        api_key = os.getenv("LLMOBSERVE_API_KEY")
    
    if flush_interval_ms == 500:  # Only override if using default
        flush_interval_ms_env = os.getenv("LLMOBSERVE_FLUSH_INTERVAL_MS")
        if flush_interval_ms_env:
            try:
                flush_interval_ms = int(flush_interval_ms_env)
            except ValueError:
                logger.warning(f"[llmobserve] Invalid LLMOBSERVE_FLUSH_INTERVAL_MS: {flush_interval_ms_env}")
    
    if customer_id is None:
        customer_id = os.getenv("LLMOBSERVE_CUSTOMER_ID")
    
    # Validate required args
    if not collector_url:
        logger.error(
            "[llmobserve] collector_url required. "
            "Provide as argument or set LLMOBSERVE_COLLECTOR_URL env var."
        )
        return
    
    # API key is optional for MVP/self-hosted deployments
    if not api_key:
        logger.warning("[llmobserve] No API key provided - using unauthenticated mode")
        api_key = "dev-mode"  # Placeholder for MVP
    
    # Configure SDK
    config.configure(
        collector_url=collector_url,
        api_key=api_key,
        flush_interval_ms=flush_interval_ms,
        customer_id=customer_id
    )
    
    # Set customer in context if provided
    if customer_id:
        context.set_customer_id(customer_id)
    
    if not config.is_enabled():
        logger.debug("[llmobserve] Observability disabled, skipping instrumentation")
        return
    
    # Get libraries to instrument from env var or default to all
    libs_env = os.getenv("LLMOBSERVE_LIBS")
    if libs_env:
        libs = [lib.strip() for lib in libs_env.split(",")]
    else:
        libs = None  # Instrument all registered libraries
    
    # Apply instrumentation with fail-open safety
    results = auto_instrument(libs=libs)
    
    # Log results
    successful = [lib for lib, success in results.items() if success]
    failed = [lib for lib, success in results.items() if not success]
    
    if successful:
        logger.info(f"[llmobserve] Successfully instrumented: {', '.join(successful)}")
    
    if failed:
        logger.warning(f"[llmobserve] Failed to instrument: {', '.join(failed)}")
    
    # Start flush timer
    try:
        buffer.start_flush_timer()
    except Exception as e:
        logger.error(f"[llmobserve] Failed to start flush timer: {e}", exc_info=True)
    
    # Mark as initialized
    observe._initialized = True

