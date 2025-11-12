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
    tenant_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    auto_start_proxy: bool = False,
    use_instrumentors: bool = False
) -> None:
    """
    Initialize LLM observability with header-based context propagation.
    
    Architecture:
    1. HTTP clients (httpx/requests/aiohttp) ALWAYS inject context headers
    2. Headers carry run_id, tenant_id, customer_id, section_path for distributed tracing
    3. Proxy reads headers and emits events (universal coverage)
    4. Instrumentors provide direct tracking as optimization (optional)
    
    This design ensures context propagates across:
    - async/await coroutines
    - Celery/RQ background jobs
    - Multi-threaded workloads
    - Any HTTP-based API
    
    Args:
        collector_url: URL of the collector API (e.g., "http://localhost:8000").
                      If None, reads from LLMOBSERVE_COLLECTOR_URL env var.
        proxy_url: URL of the proxy server (e.g., "http://localhost:9000").
                  If provided, ALL external HTTP calls route through proxy.
                  If None, headers are still injected (for future proxy).
        api_key: API key for authentication (get from dashboard).
                If None, reads from LLMOBSERVE_API_KEY env var.
        flush_interval_ms: How often to flush events to collector (default: 500ms).
                          Can be overridden with LLMOBSERVE_FLUSH_INTERVAL_MS env var.
        tenant_id: Tenant identifier for multi-tenancy (defaults to "default_tenant").
                  Can be set via LLMOBSERVE_TENANT_ID env var.
                  Use "default_tenant" for solo dev or shared-key SaaS.
                  Use unique tenant_id per logged-in customer for multi-tenant SaaS.
        customer_id: Optional end-customer identifier (tracks tenant's customers).
                    Can be set via LLMOBSERVE_CUSTOMER_ID env var.
        auto_start_proxy: If True, automatically start local proxy server.
                         WARNING: Requires proxy dependencies installed.
        use_instrumentors: If True, also use per-SDK instrumentors for optimization.
                          If False, rely purely on header injection + proxy.
                          Default: False (pure header mode, no monkey-patching).
    
    Example:
        >>> import llmobserve
        >>> 
        >>> # Solo developer (default tenant)
        >>> llmobserve.observe(
        ...     collector_url="http://localhost:8000"
        ... )
        >>> 
        >>> # SaaS with shared keys (track your customers)
        >>> llmobserve.observe(
        ...     collector_url="http://localhost:8000",
        ...     tenant_id="your_company"  # Or use default
        ... )
        >>> from llmobserve import set_customer_id
        >>> set_customer_id("customer_xyz")  # Track your end-users
        >>> 
        >>> # Multi-tenant SaaS (each customer sees only their data)
        >>> llmobserve.observe(
        ...     collector_url="http://localhost:8000",
        ...     tenant_id=logged_in_user.tenant_id  # From auth
        ... )
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
        tenant_id=tenant_id,
        customer_id=customer_id
    )
    
    # Set customer in context if provided
    if customer_id:
        context.set_customer_id(customer_id)
    
    if not config.is_enabled():
        logger.debug("[llmobserve] Observability disabled, skipping instrumentation")
        return
    
    # PRIMARY: Patch HTTP, gRPC, and WebSocket protocols for universal coverage
    # This ensures context propagates across all network calls
    from llmobserve.http_interceptor import patch_all_protocols
    protocol_results = patch_all_protocols()
    
    # Report patching results
    patched_protocols = [proto for proto, success in protocol_results.items() if success]
    failed_protocols = [proto for proto, success in protocol_results.items() if not success]
    
    if patched_protocols:
        logger.info(f"[llmobserve] ✓ Protocols patched: {', '.join(patched_protocols).upper()}")
        if proxy_url:
            logger.info(f"[llmobserve]   → Routing through proxy: {proxy_url}")
            logger.info(f"[llmobserve]   → Universal coverage for all patched protocols")
        else:
            logger.info("[llmobserve]   → Context headers enabled (proxy can be added later)")
            if not use_instrumentors:
                logger.warning("[llmobserve]   ⚠️  No proxy configured AND instrumentors disabled - API calls won't be tracked!")
                logger.warning("[llmobserve]   💡 Either set proxy_url or use_instrumentors=True")
    
    if failed_protocols:
        logger.debug(f"[llmobserve]   Not available: {', '.join(failed_protocols).upper()} (libraries not installed)")
    
    if not patched_protocols:
        logger.warning("[llmobserve] ✗ No protocols could be patched (install httpx/requests/aiohttp/grpcio/websockets)")
    
    # OPTIONAL: Also use per-SDK instrumentors for optimization (avoids proxy latency)
    if use_instrumentors:
        logger.info("[llmobserve] ⚙️  Instrumentors enabled (lower latency, but uses monkey-patching)")
        
        from llmobserve.instrumentation import auto_instrument
        libs_to_instrument = os.getenv("LLMOBSERVE_LIBS")
        if libs_to_instrument:
            libs = [lib.strip() for lib in libs_to_instrument.split(",")]
        else:
            libs = None  # Instrument all available
        
        instrumentation_results = auto_instrument(libs=libs)
        
        successful = [lib for lib, success in instrumentation_results.items() if success]
        failed = [lib for lib, success in instrumentation_results.items() if not success]
        
        if successful:
            logger.info(f"[llmobserve]   ✓ Instrumented: {', '.join(successful)}")
        
        if failed:
            logger.debug(f"[llmobserve]   Not available: {', '.join(failed)} (will use proxy if configured)")
    else:
        logger.info("[llmobserve] ✓ Pure header-based mode (no monkey-patching, universal coverage)")
    
    # Start flush timer
    try:
        buffer.start_flush_timer()
    except Exception as e:
        logger.error(f"[llmobserve] Failed to start flush timer: {e}", exc_info=True)
    
    # Mark as initialized
    observe._initialized = True

