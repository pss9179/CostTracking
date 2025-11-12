"""
Main observe() function to initialize hybrid SDK+Proxy architecture.

Patches HTTP clients and routes traffic through proxy for universal coverage.
"""
import logging
import os
from typing import Optional
from llmobserve import config, buffer, context

logger = logging.getLogger("llmobserve")


def observe(
    collector_url: Optional[str] = None,
    proxy_url: Optional[str] = None,
    api_key: Optional[str] = None,
    flush_interval_ms: int = 500,
    customer_id: Optional[str] = None,
    auto_start_proxy: bool = False
) -> None:
    """
    Initialize LLM observability with hybrid SDK+Proxy architecture.
    
    This function:
    1. Configures the SDK with collector and optional proxy URL
    2. Patches HTTP clients (httpx, requests, aiohttp) to inject context headers
    3. Routes requests through proxy (if configured) for universal API coverage
    4. Starts the event buffer flush timer
    
    Args:
        collector_url: URL of the collector API (e.g., "http://localhost:8000").
                      If None, reads from LLMOBSERVE_COLLECTOR_URL env var.
        proxy_url: URL of the proxy server (e.g., "http://localhost:9000").
                  If None and auto_start_proxy=True, starts local proxy.
                  If None and auto_start_proxy=False, runs in direct mode (no proxy).
        api_key: API key for authentication (get from dashboard).
                If None, reads from LLMOBSERVE_API_KEY env var.
        flush_interval_ms: How often to flush events to collector (default: 500ms).
                          Can be overridden with LLMOBSERVE_FLUSH_INTERVAL_MS env var.
        customer_id: Optional customer identifier for tracking your end-users.
                    Can be set via LLMOBSERVE_CUSTOMER_ID env var.
        auto_start_proxy: If True, automatically start local proxy server.
                         WARNING: Requires proxy dependencies installed.
    
    Example:
        >>> import llmobserve
        >>> # Simple: uses env vars, no proxy (direct mode)
        >>> llmobserve.observe()
        >>> 
        >>> # With external proxy (production):
        >>> llmobserve.observe(
        ...     collector_url="http://localhost:8000",
        ...     proxy_url="http://localhost:9000",
        ...     api_key="llmo_sk_abc123..."
        ... )
        >>> 
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
    
    if proxy_url is None:
        proxy_url = os.getenv("LLMOBSERVE_PROXY_URL")
    
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
    
    # Auto-start proxy if requested (and not already provided)
    if auto_start_proxy and not proxy_url:
        try:
            from llmobserve.proxy_manager import start_local_proxy
            proxy_url = start_local_proxy(collector_url=collector_url)
            logger.info(f"[llmobserve] Auto-started proxy at {proxy_url}")
        except Exception as e:
            logger.warning(f"[llmobserve] Failed to auto-start proxy: {e}. Running in direct mode.")
            proxy_url = None
    
    # Configure SDK
    config.configure(
        collector_url=collector_url,
        proxy_url=proxy_url,
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
    
    # Patch HTTP clients (replaces per-SDK instrumentors)
    from llmobserve.http_interceptor import patch_all_http_clients
    patched = patch_all_http_clients()
    
    if patched:
        if proxy_url:
            logger.info(f"[llmobserve] HTTP clients patched, routing through proxy: {proxy_url}")
        else:
            logger.info("[llmobserve] HTTP clients patched (direct mode - no proxy)")
    else:
        logger.warning("[llmobserve] No HTTP clients patched. Install httpx, requests, or aiohttp.")
    
    # Start flush timer
    try:
        buffer.start_flush_timer()
    except Exception as e:
        logger.error(f"[llmobserve] Failed to start flush timer: {e}", exc_info=True)
    
    # Mark as initialized
    observe._initialized = True

