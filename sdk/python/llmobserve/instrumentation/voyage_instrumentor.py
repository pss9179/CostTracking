"""
Voyage AI embeddings instrumentor with fail-open safety.
"""
import functools
import time
import uuid
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config


def track_voyage_call(
    model: Optional[str],
    input_tokens: int,
    latency_ms: float,
    status: str = "ok",
    error: Optional[str] = None,
) -> None:
    """Track a Voyage AI embeddings call."""
    # Voyage pricing: $0.12 per 1M tokens (voyage-2), $0.06 per 1M (voyage-lite-02)
    pricing = {"voyage-2": 0.12 / 1_000_000, "voyage-lite-02": 0.06 / 1_000_000}
    rate = pricing.get(model or "voyage-2", 0.12 / 1_000_000)
    cost_usd = input_tokens * rate
    
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": "embedding_call",
        "provider": "voyage",
        "endpoint": "embed",
        "model": model,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
        "input_tokens": input_tokens,
        "output_tokens": 0,
        "status": status,
        "tenant_id": config.get_tenant_id(),

        "customer_id": context.get_customer_id(),
        "event_metadata": {"error": error} if error else None,
    }
    
    buffer.add_event(event)


def create_safe_wrapper(original_method: Callable) -> Callable:
    """Create safe wrapper for Voyage method."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        model_name = kwargs.get("model") or "voyage-2"
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract token count from response
            input_tokens = getattr(result, "total_tokens", 0)
            
            track_voyage_call(
                model=model_name,
                input_tokens=input_tokens,
                latency_ms=latency_ms,
                status="ok"
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_voyage_call(
                model=model_name,
                input_tokens=0,
                latency_ms=latency_ms,
                status="error",
                error=str(e)
            )
            
            raise
    
    return wrapper


def instrument_voyage() -> bool:
    """Instrument Voyage AI SDK."""
    try:
        import voyageai
    except ImportError:
        logger.debug("[llmobserve] Voyage AI SDK not installed - skipping")
        return False
    
    try:
        # Patch Client.embed()
        if hasattr(voyageai, "Client"):
            if hasattr(voyageai.Client.embed, "_llmobserve_instrumented"):
                logger.debug("[llmobserve] Voyage AI already instrumented")
                return True
            
            original_embed = voyageai.Client.embed
            wrapped_embed = create_safe_wrapper(original_embed)
            voyageai.Client.embed = wrapped_embed
            wrapped_embed._llmobserve_instrumented = True
            wrapped_embed._llmobserve_original = original_embed
            
            logger.debug("[llmobserve] Instrumented voyageai.Client.embed")
        
        logger.info("[llmobserve] Successfully instrumented Voyage AI SDK")
        return True
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument Voyage AI: {e}", exc_info=True)
        return False

