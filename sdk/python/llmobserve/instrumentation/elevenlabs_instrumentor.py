"""
ElevenLabs TTS/Voice Cloning instrumentor with version guards and fail-open safety.

Supports:
- client.generate() - TTS
- client.clone() - voice cloning
- client.text_to_speech.convert() - v2 API
"""
import functools
import time
import uuid
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config


def track_elevenlabs_call(
    method_name: str,
    model: Optional[str],
    character_count: int,
    latency_ms: float,
    status: str = "ok",
    error: Optional[str] = None,
) -> None:
    """Track an ElevenLabs API call."""
    from llmobserve.pricing import compute_cost
    
    # ElevenLabs charges per 1K characters
    cost_usd = (character_count / 1000) * 0.18  # $0.18 per 1K chars (default rate)
    
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": "tts_call",
        "provider": "elevenlabs",
        "endpoint": method_name,
        "model": model,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
        "input_tokens": character_count,  # Store character count in input_tokens
        "output_tokens": 0,
        "status": status,
        "tenant_id": config.get_tenant_id(),

        "customer_id": context.get_customer_id(),
        "event_metadata": {"error": error, "character_count": character_count} if error or character_count else None,
    }
    
    buffer.add_event(event)


def create_safe_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create safe wrapper for ElevenLabs method."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        # Extract text input to count characters
        text = kwargs.get("text") or (args[0] if len(args) > 0 else "")
        character_count = len(text) if isinstance(text, str) else 0
        
        model_name = kwargs.get("model_id") or kwargs.get("model") or "eleven_multilingual_v2"
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            track_elevenlabs_call(
                method_name=method_name,
                model=model_name,
                character_count=character_count,
                latency_ms=latency_ms,
                status="ok"
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_elevenlabs_call(
                method_name=method_name,
                model=model_name,
                character_count=character_count,
                latency_ms=latency_ms,
                status="error",
                error=str(e)
            )
            
            raise
    
    return wrapper


def instrument_elevenlabs() -> bool:
    """Instrument ElevenLabs SDK."""
    try:
        from elevenlabs import client
    except ImportError:
        logger.debug("[llmobserve] ElevenLabs SDK not installed - skipping")
        return False
    
    try:
        # Patch generate() method
        if hasattr(client, "ElevenLabs"):
            if hasattr(client.ElevenLabs, "generate"):
                if hasattr(client.ElevenLabs.generate, "_llmobserve_instrumented"):
                    logger.debug("[llmobserve] ElevenLabs already instrumented")
                    return True
                
                original_generate = client.ElevenLabs.generate
                wrapped_generate = create_safe_wrapper(original_generate, "generate")
                client.ElevenLabs.generate = wrapped_generate
                wrapped_generate._llmobserve_instrumented = True
                wrapped_generate._llmobserve_original = original_generate
                
                logger.debug("[llmobserve] Instrumented elevenlabs.client.ElevenLabs.generate")
        
        # Patch text_to_speech.convert() if available
        if hasattr(client, "ElevenLabs") and hasattr(client.ElevenLabs, "text_to_speech"):
            if hasattr(client.ElevenLabs.text_to_speech, "convert"):
                original_convert = client.ElevenLabs.text_to_speech.convert
                wrapped_convert = create_safe_wrapper(original_convert, "text_to_speech.convert")
                client.ElevenLabs.text_to_speech.convert = wrapped_convert
                wrapped_convert._llmobserve_instrumented = True
                wrapped_convert._llmobserve_original = original_convert
                
                logger.debug("[llmobserve] Instrumented elevenlabs.client.ElevenLabs.text_to_speech.convert")
        
        logger.info("[llmobserve] Successfully instrumented ElevenLabs SDK")
        return True
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument ElevenLabs: {e}", exc_info=True)
        return False

