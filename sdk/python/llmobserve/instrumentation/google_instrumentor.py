"""
Google Gemini / Vertex AI instrumentor with version guards and fail-open safety.

Supports:
- google.generativeai (Gemini API)
- google.cloud.aiplatform (Vertex AI)
"""
import functools
import time
import uuid
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config


def check_gemini_installed() -> tuple[bool, Optional[str]]:
    """Check if Gemini SDK is installed."""
    try:
        import google.generativeai as genai
        version = getattr(genai, "__version__", "unknown")
        return True, version
    except ImportError:
        logger.debug("[llmobserve] Google Gemini SDK not installed")
        return False, None


def track_gemini_call(
    method_name: str,
    model: Optional[str],
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
    status: str = "ok",
    error: Optional[str] = None,
) -> None:
    """Track a Gemini API call."""
    from llmobserve.pricing import compute_cost
    
    cost_usd = compute_cost(
        provider="google",
        model=model or "gemini-1.5-flash",
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
        "span_type": "llm_call",
        "provider": "google",
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
    """Create safe wrapper for Gemini method."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        model_name = kwargs.get("model") or "gemini-1.5-flash"
        
        # Check spending caps before making request (model-specific caps)
        from llmobserve.caps import check_spending_caps, should_check_caps, BudgetExceededError
        if should_check_caps() and model_name:
            try:
                check_spending_caps(
                    provider="google",
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
            
            if hasattr(result, "usage_metadata"):
                input_tokens = getattr(result.usage_metadata, "prompt_token_count", 0)
                output_tokens = getattr(result.usage_metadata, "candidates_token_count", 0)
            
            track_gemini_call(
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
            
            track_gemini_call(
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


def instrument_google() -> bool:
    """Instrument Google Gemini SDK."""
    try:
        import google.generativeai as genai
    except ImportError:
        logger.debug("[llmobserve] Google Gemini SDK not installed - skipping")
        return False
    
    is_installed, version = check_gemini_installed()
    if not is_installed:
        return False
    
    try:
        # Patch GenerativeModel.generate_content()
        if hasattr(genai, "GenerativeModel"):
            if hasattr(genai.GenerativeModel.generate_content, "_llmobserve_instrumented"):
                logger.debug("[llmobserve] Google Gemini already instrumented")
                return True
            
            original_generate = genai.GenerativeModel.generate_content
            wrapped_generate = create_safe_wrapper(original_generate, "generate_content")
            
            genai.GenerativeModel.generate_content = wrapped_generate
            wrapped_generate._llmobserve_instrumented = True
            wrapped_generate._llmobserve_original = original_generate
            
            logger.debug("[llmobserve] Instrumented google.generativeai.GenerativeModel.generate_content")
        
        logger.info(f"[llmobserve] Successfully instrumented Google Gemini SDK (version {version})")
        return True
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument Google Gemini: {e}", exc_info=True)
        return False

