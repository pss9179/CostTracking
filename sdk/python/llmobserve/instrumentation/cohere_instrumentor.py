"""
Cohere SDK instrumentor with version guards and fail-open safety.

Supports:
- co.chat() - chat endpoint
- co.generate() - completion endpoint
- co.embed() - embeddings endpoint
"""
import functools
import time
import uuid
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config


def track_cohere_call(
    method_name: str,
    model: Optional[str],
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
    status: str = "ok",
    error: Optional[str] = None,
) -> None:
    """Track a Cohere API call."""
    from llmobserve.pricing import compute_cost
    
    cost_usd = compute_cost(
        provider="cohere",
        model=model or "command",
        input_tokens=input_tokens,
        output_tokens=output_tokens
    )
    
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": "llm_call" if method_name != "embed" else "embedding_call",
        "provider": "cohere",
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


def create_safe_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create safe wrapper for Cohere method."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        model_name = kwargs.get("model") or "command"
        
        # Check spending caps before making request (model-specific caps)
        from llmobserve.caps import check_spending_caps, should_check_caps, BudgetExceededError
        if should_check_caps() and model_name:
            try:
                check_spending_caps(
                    provider="cohere",
                    model=model_name,
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
            input_tokens = 0
            output_tokens = 0
            
            if hasattr(result, "meta") and hasattr(result.meta, "billed_units"):
                input_tokens = getattr(result.meta.billed_units, "input_tokens", 0)
                output_tokens = getattr(result.meta.billed_units, "output_tokens", 0)
            
            track_cohere_call(
                method_name=method_name,
                model=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                status="ok"
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_cohere_call(
                method_name=method_name,
                model=model_name,
                input_tokens=0,
                output_tokens=0,
                latency_ms=latency_ms,
                status="error",
                error=str(e)
            )
            
            raise
    
    return wrapper


def instrument_cohere() -> bool:
    """Instrument Cohere SDK."""
    try:
        import cohere
    except ImportError:
        logger.debug("[llmobserve] Cohere SDK not installed - skipping")
        return False
    
    try:
        # Patch Client.chat()
        if hasattr(cohere.Client, "chat"):
            if hasattr(cohere.Client.chat, "_llmobserve_instrumented"):
                logger.debug("[llmobserve] Cohere already instrumented")
                return True
            
            original_chat = cohere.Client.chat
            wrapped_chat = create_safe_wrapper(original_chat, "chat")
            cohere.Client.chat = wrapped_chat
            wrapped_chat._llmobserve_instrumented = True
            wrapped_chat._llmobserve_original = original_chat
            
            logger.debug("[llmobserve] Instrumented cohere.Client.chat")
        
        # Patch Client.generate()
        if hasattr(cohere.Client, "generate"):
            original_generate = cohere.Client.generate
            wrapped_generate = create_safe_wrapper(original_generate, "generate")
            cohere.Client.generate = wrapped_generate
            wrapped_generate._llmobserve_instrumented = True
            wrapped_generate._llmobserve_original = original_generate
            
            logger.debug("[llmobserve] Instrumented cohere.Client.generate")
        
        # Patch Client.embed()
        if hasattr(cohere.Client, "embed"):
            original_embed = cohere.Client.embed
            wrapped_embed = create_safe_wrapper(original_embed, "embed")
            cohere.Client.embed = wrapped_embed
            wrapped_embed._llmobserve_instrumented = True
            wrapped_embed._llmobserve_original = original_embed
            
            logger.debug("[llmobserve] Instrumented cohere.Client.embed")
        
        logger.info("[llmobserve] Successfully instrumented Cohere SDK")
        return True
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument Cohere: {e}", exc_info=True)
        return False

