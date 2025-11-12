"""
Stripe payment processing instrumentor with fail-open safety.

Tracks transaction fees on:
- stripe.PaymentIntent.create()
- stripe.Charge.create()
"""
import functools
import time
import uuid
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config


def track_stripe_transaction(
    method_name: str,
    amount: float,
    latency_ms: float,
    status: str = "ok",
    error: Optional[str] = None,
) -> None:
    """Track a Stripe transaction."""
    # Stripe fee: 2.9% + $0.30
    cost_usd = (amount * 0.029) + 0.30
    
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": "payment_transaction",
        "provider": "stripe",
        "endpoint": method_name,
        "model": None,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
        "input_tokens": 0,
        "output_tokens": 0,
        "status": status,
        "tenant_id": config.get_tenant_id(),

        "customer_id": context.get_customer_id(),
        "event_metadata": {"error": error, "transaction_amount": amount} if error or amount else None,
    }
    
    buffer.add_event(event)


def create_safe_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create safe wrapper for Stripe method."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        # Extract amount (in cents, convert to dollars)
        amount_cents = kwargs.get("amount") or 0
        amount_usd = amount_cents / 100.0
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            track_stripe_transaction(
                method_name=method_name,
                amount=amount_usd,
                latency_ms=latency_ms,
                status="ok"
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_stripe_transaction(
                method_name=method_name,
                amount=amount_usd,
                latency_ms=latency_ms,
                status="error",
                error=str(e)
            )
            
            raise
    
    return wrapper


def instrument_stripe() -> bool:
    """Instrument Stripe SDK."""
    try:
        import stripe
    except ImportError:
        logger.debug("[llmobserve] Stripe SDK not installed - skipping")
        return False
    
    try:
        # Patch PaymentIntent.create()
        if hasattr(stripe, "PaymentIntent"):
            if hasattr(stripe.PaymentIntent.create, "_llmobserve_instrumented"):
                logger.debug("[llmobserve] Stripe already instrumented")
                return True
            
            original_create = stripe.PaymentIntent.create
            wrapped_create = create_safe_wrapper(original_create, "PaymentIntent.create")
            stripe.PaymentIntent.create = wrapped_create
            wrapped_create._llmobserve_instrumented = True
            wrapped_create._llmobserve_original = original_create
            
            logger.debug("[llmobserve] Instrumented stripe.PaymentIntent.create")
        
        # Patch Charge.create()
        if hasattr(stripe, "Charge"):
            original_charge = stripe.Charge.create
            wrapped_charge = create_safe_wrapper(original_charge, "Charge.create")
            stripe.Charge.create = wrapped_charge
            wrapped_charge._llmobserve_instrumented = True
            wrapped_charge._llmobserve_original = original_charge
            
            logger.debug("[llmobserve] Instrumented stripe.Charge.create")
        
        logger.info("[llmobserve] Successfully instrumented Stripe SDK")
        return True
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument Stripe: {e}", exc_info=True)
        return False

