"""
Twilio SMS/Voice instrumentor with fail-open safety.

Tracks costs for:
- SMS messages ($0.0079 per message - US)
- Voice calls ($0.013 per minute - US)
"""
import functools
import time
import uuid
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config


def track_twilio_call(
    method_name: str,
    cost_usd: float,
    latency_ms: float,
    status: str = "ok",
    error: Optional[str] = None,
) -> None:
    """Track a Twilio API call."""
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": "communication_call",
        "provider": "twilio",
        "endpoint": method_name,
        "model": None,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
        "input_tokens": 0,
        "output_tokens": 0,
        "status": status,
        "customer_id": context.get_customer_id(),
        "event_metadata": {"error": error} if error else None,
    }
    
    buffer.add_event(event)


def create_safe_wrapper(original_method: Callable, method_name: str, default_cost: float) -> Callable:
    """Create safe wrapper for Twilio method."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract actual cost from response if available
            cost = float(result.price) if hasattr(result, "price") and result.price else default_cost
            
            track_twilio_call(
                method_name=method_name,
                cost_usd=abs(cost),  # Price is negative, so abs()
                latency_ms=latency_ms,
                status="ok"
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_twilio_call(
                method_name=method_name,
                cost_usd=default_cost,
                latency_ms=latency_ms,
                status="error",
                error=str(e)
            )
            
            raise
    
    return wrapper


def instrument_twilio() -> bool:
    """Instrument Twilio SDK."""
    try:
        from twilio.rest import Client
    except ImportError:
        logger.debug("[llmobserve] Twilio SDK not installed - skipping")
        return False
    
    try:
        # Patch messages.create() - SMS
        if hasattr(Client, "messages"):
            original_create = Client.messages.create
            if hasattr(original_create, "_llmobserve_instrumented"):
                logger.debug("[llmobserve] Twilio already instrumented")
                return True
            
            wrapped_create = create_safe_wrapper(original_create, "messages.create", default_cost=0.0079)
            Client.messages.create = wrapped_create
            wrapped_create._llmobserve_instrumented = True
            wrapped_create._llmobserve_original = original_create
            
            logger.debug("[llmobserve] Instrumented twilio.rest.Client.messages.create")
        
        # Patch calls.create() - Voice
        if hasattr(Client, "calls"):
            original_calls = Client.calls.create
            wrapped_calls = create_safe_wrapper(original_calls, "calls.create", default_cost=0.013)
            Client.calls.create = wrapped_calls
            wrapped_calls._llmobserve_instrumented = True
            wrapped_calls._llmobserve_original = original_calls
            
            logger.debug("[llmobserve] Instrumented twilio.rest.Client.calls.create")
        
        logger.info("[llmobserve] Successfully instrumented Twilio SDK")
        return True
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument Twilio: {e}", exc_info=True)
        return False

