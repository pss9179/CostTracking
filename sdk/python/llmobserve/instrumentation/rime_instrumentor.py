"""
Rime TTS instrumentor with fail-open safety.

Tracks costs for:
- Rime TTS: ~$0.006 per 1K characters (varies by plan)

Supports:
- client.tts() - synchronous TTS
- client.synthesize() - alternative method
- Streaming variants
"""
import functools
import time
import uuid
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config

# Pricing per 1K characters (Rime is one of the cheapest TTS)
RIME_PRICE_PER_1K = 0.006


def track_rime_call(
    method_name: str,
    model: Optional[str],
    character_count: int,
    latency_ms: float,
    speaker: Optional[str] = None,
    status: str = "ok",
    error: Optional[str] = None,
) -> None:
    """Track a Rime TTS API call."""
    
    cost_usd = (character_count / 1000) * RIME_PRICE_PER_1K
    
    # Estimate audio duration (average 150 words/min, 5 chars/word)
    estimated_duration = (character_count / 750) * 60  # seconds
    
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": "tts_call",
        "provider": "rime",
        "endpoint": method_name,
        "model": model or "rime-tts",
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
        "input_tokens": character_count,
        "output_tokens": 0,
        "status": status,
        "tenant_id": config.get_tenant_id(),
        "customer_id": context.get_customer_id(),
        "voice_call_id": context.get_voice_call_id(),
        "audio_duration_seconds": estimated_duration,
        "voice_segment_type": "tts",
        "event_metadata": {
            "character_count": character_count,
            "speaker": speaker,
            "error": error,
        } if any([character_count, speaker, error]) else None,
    }
    
    buffer.add_event(event)


def extract_text(args, kwargs) -> str:
    """Extract text from Rime API call arguments."""
    text = kwargs.get("text") or kwargs.get("input") or kwargs.get("content")
    if text:
        return text if isinstance(text, str) else ""
    
    for arg in args:
        if isinstance(arg, str) and len(arg) > 0:
            return arg
    
    return ""


def create_tts_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create wrapper for Rime TTS methods."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        text = extract_text(args, kwargs)
        character_count = len(text)
        speaker = kwargs.get("speaker") or kwargs.get("voice")
        model = kwargs.get("model")
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            track_rime_call(
                method_name=method_name,
                model=model,
                character_count=character_count,
                latency_ms=latency_ms,
                speaker=speaker,
                status="ok",
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_rime_call(
                method_name=method_name,
                model=model,
                character_count=character_count,
                latency_ms=latency_ms,
                speaker=speaker,
                status="error",
                error=str(e),
            )
            
            raise
    
    return wrapper


def create_async_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create async wrapper for Rime TTS methods."""
    @functools.wraps(original_method)
    async def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return await original_method(*args, **kwargs)
        
        start_time = time.time()
        
        text = extract_text(args, kwargs)
        character_count = len(text)
        speaker = kwargs.get("speaker") or kwargs.get("voice")
        model = kwargs.get("model")
        
        try:
            result = await original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            track_rime_call(
                method_name=method_name,
                model=model,
                character_count=character_count,
                latency_ms=latency_ms,
                speaker=speaker,
                status="ok",
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_rime_call(
                method_name=method_name,
                model=model,
                character_count=character_count,
                latency_ms=latency_ms,
                speaker=speaker,
                status="error",
                error=str(e),
            )
            
            raise
    
    return wrapper


def instrument_rime() -> bool:
    """Instrument Rime SDK for TTS tracking."""
    try:
        import rime
    except ImportError:
        logger.debug("[llmobserve] Rime SDK not installed - skipping")
        return False
    
    try:
        # Rime has different client patterns - try to patch common ones
        instrumented = False
        
        # Try RimeClient
        if hasattr(rime, "RimeClient"):
            Client = rime.RimeClient
            original_init = Client.__init__
            
            if not hasattr(original_init, "_llmobserve_instrumented"):
                @functools.wraps(original_init)
                def patched_init(self, *args, **kwargs):
                    original_init(self, *args, **kwargs)
                    
                    for method_name in ["tts", "synthesize", "speak", "generate"]:
                        if hasattr(self, method_name):
                            original = getattr(self, method_name)
                            if not hasattr(original, "_llmobserve_instrumented"):
                                wrapped = create_tts_wrapper(original, method_name)
                                setattr(self, method_name, wrapped)
                                wrapped._llmobserve_instrumented = True
                
                Client.__init__ = patched_init
                patched_init._llmobserve_instrumented = True
                instrumented = True
        
        # Try direct module functions
        for func_name in ["tts", "synthesize", "speak"]:
            if hasattr(rime, func_name):
                original = getattr(rime, func_name)
                if not hasattr(original, "_llmobserve_instrumented"):
                    wrapped = create_tts_wrapper(original, func_name)
                    setattr(rime, func_name, wrapped)
                    wrapped._llmobserve_instrumented = True
                    instrumented = True
        
        if instrumented:
            logger.info("[llmobserve] Successfully instrumented Rime SDK")
            return True
        else:
            logger.debug("[llmobserve] No instrumentable methods found in Rime SDK")
            return False
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument Rime: {e}", exc_info=True)
        return False

