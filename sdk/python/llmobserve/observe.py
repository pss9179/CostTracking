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
    use_instrumentors: bool = False,
    auto_detect_agents: bool = True
) -> None:
    """
    Initialize LLM observability with reverse proxy architecture.
    
    Architecture:
    1. HTTP clients (httpx/requests/aiohttp) inject context headers
    2. ALL API calls route through reverse proxy (no monkey-patching)
    3. Proxy parses responses, calculates costs, emits events
    4. SDK-agnostic: works with any API without SDK-specific code
    
    Benefits:
    - No monkey-patching: SDK updates don't break tracking
    - Universal coverage: Works with OpenAI, Pinecone, GraphQL, any HTTP API
    - Transparent: Requests forwarded unchanged (like Kong)
    - Stable: No dependency on SDK internals
    
    This design ensures context propagates across:
    - async/await coroutines
    - Celery/RQ background jobs
    - Multi-threaded workloads
    - Any HTTP-based API (including GraphQL, gRPC over HTTP)
    
    Args:
        collector_url: URL of the collector API (e.g., "http://localhost:8000").
                      If None, reads from LLMOBSERVE_COLLECTOR_URL env var.
        proxy_url: URL of the proxy server (e.g., "http://localhost:9000").
                  If None, proxy will be auto-started on port 9000.
                  Set to None explicitly to disable proxy (not recommended).
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
        auto_start_proxy: DEPRECATED - Proxy auto-starts by default now.
                         Set proxy_url=None explicitly to disable.
        use_instrumentors: If True, use per-SDK instrumentors for other providers.
                          OpenAI and Pinecone ALWAYS use proxy (no monkey-patching).
                          Default: False (pure proxy mode).
    
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
    # DEFAULT: Auto-start proxy for universal coverage (no monkey-patching)
    if not proxy_url:
        if auto_start_proxy:
            try:
                from llmobserve.proxy_manager import start_local_proxy
                proxy_url = start_local_proxy(collector_url=collector_url)
                logger.info(f"[llmobserve] Auto-started proxy at {proxy_url}")
            except Exception as e:
                logger.warning(f"[llmobserve] Failed to auto-start proxy: {e}")
                proxy_url = None
        else:
            # Try to auto-start proxy by default (can be disabled with proxy_url=None explicitly)
            try:
                from llmobserve.proxy_manager import start_local_proxy
                proxy_url = start_local_proxy(collector_url=collector_url)
                logger.info(f"[llmobserve] Auto-started proxy at {proxy_url} (default: all APIs route through proxy)")
            except Exception as e:
                logger.warning(f"[llmobserve] Failed to auto-start proxy: {e}. Set proxy_url manually or install proxy dependencies.")
                proxy_url = None
    
    # Configure SDK
    config.configure(
        collector_url=collector_url,
        proxy_url=proxy_url,
        api_key=api_key,
        flush_interval_ms=flush_interval_ms,
        tenant_id=tenant_id,
        customer_id=customer_id,
        auto_detect_agents=auto_detect_agents
    )
    
    # Set customer and tenant in context if provided
    if customer_id:
        context.set_customer_id(customer_id)
    if tenant_id:
        context.set_tenant_id(tenant_id)
    
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
            logger.info(f"[llmobserve]   → Routing ALL API calls through proxy: {proxy_url}")
            logger.info(f"[llmobserve]   → Universal coverage (no monkey-patching, SDK-agnostic)")
            logger.info(f"[llmobserve]   → OpenAI, Pinecone, and all APIs tracked via proxy")
        else:
            logger.warning("[llmobserve]   ⚠️  No proxy configured - API calls won't be tracked!")
            logger.warning("[llmobserve]   💡 Proxy is required for cost tracking (no monkey-patching)")
            logger.warning("[llmobserve]   💡 Set proxy_url or enable auto_start_proxy=True")
    
    if failed_protocols:
        logger.debug(f"[llmobserve]   Not available: {', '.join(failed_protocols).upper()} (libraries not installed)")
    
    if not patched_protocols:
        logger.warning("[llmobserve] ✗ No protocols could be patched (install httpx/requests/aiohttp/grpcio/websockets)")
    
    # OPTIONAL: Also use per-SDK instrumentors for optimization (avoids proxy latency)
    # NOTE: OpenAI and Pinecone instrumentors are DISABLED - they break when SDKs update
    # All API calls route through proxy instead (universal, SDK-agnostic)
    if use_instrumentors:
        logger.info("[llmobserve] ⚙️  Instrumentors enabled (lower latency, but uses monkey-patching)")
        logger.warning("[llmobserve]   ⚠️  OpenAI and Pinecone instrumentors are DISABLED (use proxy instead)")
        
        from llmobserve.instrumentation import auto_instrument
        libs_to_instrument = os.getenv("LLMOBSERVE_LIBS")
        if libs_to_instrument:
            libs = [lib.strip() for lib in libs_to_instrument.split(",")]
            # Remove OpenAI and Pinecone from list if present
            libs = [lib for lib in libs if lib not in ["openai", "pinecone"]]
        else:
            libs = None  # Instrument all available (except OpenAI/Pinecone)
        
        instrumentation_results = auto_instrument(libs=libs)
        
        successful = [lib for lib, success in instrumentation_results.items() if success]
        failed = [lib for lib, success in instrumentation_results.items() if not success]
        
        if successful:
            logger.info(f"[llmobserve]   ✓ Instrumented: {', '.join(successful)}")
        
        if failed:
            logger.debug(f"[llmobserve]   Not available: {', '.join(failed)} (will use proxy if configured)")
    else:
        logger.info("[llmobserve] ✓ Proxy-based mode (no monkey-patching, SDK-agnostic, universal coverage)")
        logger.info("[llmobserve]   → OpenAI, Pinecone, and all APIs tracked via reverse proxy")
    
    # Start flush timer
    try:
        buffer.start_flush_timer()
    except Exception as e:
        logger.error(f"[llmobserve] Failed to start flush timer: {e}", exc_info=True)
    
    # Mark as initialized
    observe._initialized = True

