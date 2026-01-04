"""
Anthropic (Claude) SDK instrumentor with version guards and fail-open safety.

Provides modular instrumentation for Anthropic SDK with:
- Version compatibility checks
- Fail-open safety (never breaks user code)
- Support for all billable endpoints (messages, completions, streaming)
"""
import functools
import time
import uuid
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("llmobserve")

# Import shared utilities
from llmobserve import buffer, context, config

# Supported Anthropic SDK versions
SUPPORTED_ANTHROPIC_VERSIONS = {
    "0.18": "0.18.0",
    "0.19": "0.19.0",
    "0.20": "0.20.0",
    "0.21": "0.21.0",
    "0.22": "0.22.0",
    "0.23": "0.23.0",
    "0.24": "0.24.0",
    "0.25": "0.25.0",
}


def check_anthropic_version() -> tuple[bool, Optional[str]]:
    """
    Check if Anthropic SDK version is supported.
    
    Returns:
        (is_supported: bool, version: Optional[str])
    """
    try:
        import anthropic
        version = getattr(anthropic, "__version__", None)
        
        if version is None:
            logger.warning("[llmobserve] Anthropic SDK version unknown - proceeding with caution")
            return True, None  # Fail-open: allow unknown versions
        
        # Check minor version (e.g., "0.18" from "0.18.1")
        minor_version = ".".join(version.split(".")[:2])
        
        if minor_version in SUPPORTED_ANTHROPIC_VERSIONS:
            logger.debug(f"[llmobserve] Anthropic SDK version {version} is supported")
            return True, version
        
        # Check if it's a newer version
        try:
            major, minor = map(int, minor_version.split("."))
            if major == 0 and minor >= 18:
                logger.warning(
                    f"[llmobserve] Anthropic SDK version {version} not explicitly tested. "
                    "Proceeding with caution. If you encounter issues, please report them."
                )
                return True, version
        except ValueError:
            pass
        
        logger.error(
            f"[llmobserve] Anthropic SDK version {version} is not supported. "
            f"Supported versions: {list(SUPPORTED_ANTHROPIC_VERSIONS.keys())}+"
        )
        return False, version
        
    except ImportError:
        logger.debug("[llmobserve] Anthropic SDK not installed")
        return False, None


def track_anthropic_call(
    method_name: str,
    model: Optional[str],
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
    status: str = "ok",
    error: Optional[str] = None,
) -> None:
    """
    Track an Anthropic API call and emit event to collector.
    
    Args:
        method_name: API method name (e.g., "messages.create")
        model: Model name (e.g., "claude-3-haiku")
        input_tokens: Input token count
        output_tokens: Output token count
        latency_ms: Request latency in milliseconds
        status: "ok" or "error"
        error: Error message if status is "error"
    """
    # Calculate cost from pricing registry
    from llmobserve.pricing import compute_cost
    
    cost_usd = compute_cost(
        provider="anthropic",
        model=model or "claude-3-haiku",  # Fallback model
        input_tokens=input_tokens,
        output_tokens=output_tokens
    )
    
    # Build event
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": "llm_call",
        "provider": "anthropic",
        "endpoint": method_name,
        "model": model,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "status": status,
        "tenant_id": config.get_tenant_id(),

        "customer_id": context.get_customer_id(),
        "event_metadata": {"error": error} if error else None,
    }
    
    buffer.add_event(event)


def create_safe_wrapper(original_method: Callable, method_name: str, is_async: bool = False) -> Callable:
    """
    Create a safe wrapper for an Anthropic method.
    
    Args:
        original_method: The original method to wrap
        method_name: Name of the method (for logging)
        is_async: Whether the method is async
    
    Returns:
        Wrapped method with tracking
    """
    if is_async:
        @functools.wraps(original_method)
        async def async_wrapper(*args, **kwargs):
            if not config.is_enabled():
                return await original_method(*args, **kwargs)
            
            start_time = time.time()
            model = kwargs.get("model") or (args[0] if len(args) > 0 else None)
            
            # Check spending caps before making request (model-specific caps)
            from llmobserve.caps import check_spending_caps, should_check_caps, BudgetExceededError
            if should_check_caps() and model:
                try:
                    check_spending_caps(
                        provider="anthropic",
                        model=model,
                        customer_id=context.get_customer_id(),
                        agent=context.get_current_section() if context.get_current_section() != "/" else None,
                    )
                except BudgetExceededError:
                    raise
                except Exception as cap_error:
                    logger.debug(f"[llmobserve] Cap check error (fail-open): {cap_error}")
            
            try:
                result = await original_method(*args, **kwargs)
                latency_ms = (time.time() - start_time) * 1000
                
                # Extract usage from response
                input_tokens = getattr(result.usage, "input_tokens", 0)
                output_tokens = getattr(result.usage, "output_tokens", 0)
                
                # Track the call
                track_anthropic_call(
                    method_name=method_name,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency_ms,
                    status="ok"
                )
                
                return result
            
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                
                # Track error
                track_anthropic_call(
                    method_name=method_name,
                    model=model,
                    input_tokens=0,
                    output_tokens=0,
                    latency_ms=latency_ms,
                    status="error",
                    error=str(e)
                )
                
                raise  # Re-raise to not break user code
        
        return async_wrapper
    else:
        @functools.wraps(original_method)
        def sync_wrapper(*args, **kwargs):
            if not config.is_enabled():
                return original_method(*args, **kwargs)
            
            start_time = time.time()
            model = kwargs.get("model") or (args[0] if len(args) > 0 else None)
            
            # Check spending caps before making request (model-specific caps)
            from llmobserve.caps import check_spending_caps, should_check_caps, BudgetExceededError
            if should_check_caps() and model:
                try:
                    check_spending_caps(
                        provider="anthropic",
                        model=model,
                        customer_id=context.get_customer_id(),
                        agent=context.get_current_section() if context.get_current_section() != "/" else None,
                    )
                except BudgetExceededError:
                    raise
                except Exception as cap_error:
                    logger.debug(f"[llmobserve] Cap check error (fail-open): {cap_error}")
            
            try:
                result = original_method(*args, **kwargs)
                latency_ms = (time.time() - start_time) * 1000
                
                # Extract usage from response
                input_tokens = getattr(result.usage, "input_tokens", 0)
                output_tokens = getattr(result.usage, "output_tokens", 0)
                
                # Track the call
                track_anthropic_call(
                    method_name=method_name,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency_ms,
                    status="ok"
                )
                
                return result
            
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                
                # Track error
                track_anthropic_call(
                    method_name=method_name,
                    model=model,
                    input_tokens=0,
                    output_tokens=0,
                    latency_ms=latency_ms,
                    status="error",
                    error=str(e)
                )
                
                raise  # Re-raise to not break user code
        
        return sync_wrapper


def instrument_anthropic() -> bool:
    """
    Instrument Anthropic SDK for cost tracking.
    
    Returns:
        True if instrumentation succeeded, False otherwise
    """
    try:
        import anthropic
    except ImportError:
        logger.debug("[llmobserve] Anthropic SDK not installed - skipping instrumentation")
        return False
    
    # Version check
    is_supported, version = check_anthropic_version()
    if not is_supported:
        logger.warning("[llmobserve] Anthropic SDK version not supported - skipping instrumentation")
        return False
    
    try:
        import inspect
        
        # In newer Anthropic SDK versions (0.75+), messages is a cached_property
        # We need to patch the Messages class directly instead of accessing it through the client class
        
        # Try to get the Messages class from the resources module
        messages_class = None
        try:
            from anthropic.resources import Messages
            messages_class = Messages
        except ImportError:
            try:
                from anthropic.resources.messages import Messages
                messages_class = Messages
            except ImportError:
                pass
        
        if messages_class:
            # Check if already instrumented
            if hasattr(messages_class, "_llmobserve_instrumented"):
                logger.debug("[llmobserve] Anthropic Messages already instrumented")
                return True
            
            # Patch messages.create()
            if hasattr(messages_class, "create"):
                original_create = messages_class.create
                is_async = inspect.iscoroutinefunction(original_create)
                wrapped_create = create_safe_wrapper(original_create, "messages.create", is_async=is_async)
                
                messages_class.create = wrapped_create
                wrapped_create._llmobserve_instrumented = True
                wrapped_create._llmobserve_original = original_create
                
                logger.debug("[llmobserve] Instrumented anthropic.resources.Messages.create")
            
            # Mark the class as instrumented
            messages_class._llmobserve_instrumented = True
        else:
            # Fallback: Try to patch on client class (older SDK versions)
            if hasattr(anthropic, "Anthropic"):
                client_class = anthropic.Anthropic
                
                # Check if messages is directly accessible (older SDK)
                try:
                    if hasattr(client_class, "messages") and not isinstance(
                        getattr(type(client_class), 'messages', None), property
                    ):
                        if hasattr(client_class.messages, "create"):
                            original_create = client_class.messages.create
                            is_async = inspect.iscoroutinefunction(original_create)
                            wrapped_create = create_safe_wrapper(original_create, "messages.create", is_async=is_async)
                            
                            client_class.messages.create = wrapped_create
                            wrapped_create._llmobserve_instrumented = True
                            wrapped_create._llmobserve_original = original_create
                            
                            logger.debug("[llmobserve] Instrumented anthropic.Anthropic.messages.create (fallback)")
                except (AttributeError, TypeError):
                    logger.debug("[llmobserve] Could not patch Anthropic via client class fallback")
        
        # Patch completions.create() - legacy endpoint (try both approaches)
        completions_class = None
        try:
            from anthropic.resources import Completions
            completions_class = Completions
        except ImportError:
            try:
                from anthropic.resources.completions import Completions
                completions_class = Completions
            except ImportError:
                pass
        
        if completions_class and hasattr(completions_class, "create"):
            original_completions = completions_class.create
            is_async = inspect.iscoroutinefunction(original_completions)
            wrapped_completions = create_safe_wrapper(original_completions, "completions.create", is_async=is_async)
            
            completions_class.create = wrapped_completions
            wrapped_completions._llmobserve_instrumented = True
            wrapped_completions._llmobserve_original = original_completions
            
            logger.debug("[llmobserve] Instrumented anthropic.resources.Completions.create")
        
        logger.info(f"[llmobserve] Successfully instrumented Anthropic SDK (version {version})")
        return True
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument Anthropic SDK: {e}", exc_info=True)
        return False

