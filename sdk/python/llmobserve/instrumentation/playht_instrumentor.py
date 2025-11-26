"""
PlayHT TTS instrumentor with fail-open safety.

Tracks costs for:
- Play3.0-mini: $0.030 per 1K characters
- PlayHT2.0-turbo: $0.050 per 1K characters  
- PlayHT2.0: $0.050 per 1K characters
- PlayHT1.0: $0.050 per 1K characters

Supports:
- client.tts() - synchronous TTS
- client.stream() - streaming TTS
- Async variants
"""
import functools
import time
import uuid
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config

# Pricing per 1K characters
PLAYHT_PRICING = {
    "play3.0-mini": 0.030,
    "play3.0-mini-ws": 0.030,
    "play3.0-mini-http": 0.030,
    "playht2.0-turbo": 0.050,
    "playht2.0": 0.050,
    "playht1.0": 0.050,
    "default": 0.050,
}


def track_playht_call(
    method_name: str,
    model: Optional[str],
    character_count: int,
    latency_ms: float,
    voice: Optional[str] = None,
    status: str = "ok",
    error: Optional[str] = None,
) -> None:
    """Track a PlayHT TTS API call."""
    
    # Calculate cost based on model
    model_key = model.lower() if model else "default"
    price_per_1k = PLAYHT_PRICING.get(model_key, PLAYHT_PRICING["default"])
    cost_usd = (character_count / 1000) * price_per_1k
    
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
        "provider": "playht",
        "endpoint": method_name,
        "model": model,
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
            "voice": voice,
            "error": error,
        } if any([character_count, voice, error]) else None,
    }
    
    buffer.add_event(event)


def extract_text(args, kwargs) -> str:
    """Extract text from PlayHT API call arguments."""
    # Check kwargs
    text = kwargs.get("text") or kwargs.get("input")
    if text:
        return text if isinstance(text, str) else ""
    
    # Check positional args
    for arg in args:
        if isinstance(arg, str) and len(arg) > 0:
            return arg
    
    return ""


def create_tts_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create wrapper for PlayHT TTS methods."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        # Extract parameters
        text = extract_text(args, kwargs)
        character_count = len(text)
        voice = kwargs.get("voice")
        
        # Model detection - PlayHT uses voice engine
        model = kwargs.get("voice_engine") or kwargs.get("model")
        if not model:
            # Default to Play3.0-mini for newer SDK
            model = "Play3.0-mini"
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            track_playht_call(
                method_name=method_name,
                model=model,
                character_count=character_count,
                latency_ms=latency_ms,
                voice=voice,
                status="ok",
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_playht_call(
                method_name=method_name,
                model=model,
                character_count=character_count,
                latency_ms=latency_ms,
                voice=voice,
                status="error",
                error=str(e),
            )
            
            raise
    
    return wrapper


def create_async_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create async wrapper for PlayHT TTS methods."""
    @functools.wraps(original_method)
    async def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return await original_method(*args, **kwargs)
        
        start_time = time.time()
        
        text = extract_text(args, kwargs)
        character_count = len(text)
        voice = kwargs.get("voice")
        model = kwargs.get("voice_engine") or kwargs.get("model") or "Play3.0-mini"
        
        try:
            result = await original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            track_playht_call(
                method_name=method_name,
                model=model,
                character_count=character_count,
                latency_ms=latency_ms,
                voice=voice,
                status="ok",
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_playht_call(
                method_name=method_name,
                model=model,
                character_count=character_count,
                latency_ms=latency_ms,
                voice=voice,
                status="error",
                error=str(e),
            )
            
            raise
    
    return wrapper


def instrument_playht() -> bool:
    """Instrument PlayHT SDK for TTS tracking."""
    try:
        from pyht import Client
    except ImportError:
        try:
            # Try alternative import
            import playht
            Client = getattr(playht, "Client", None)
            if not Client:
                logger.debug("[llmobserve] PlayHT SDK not installed - skipping")
                return False
        except ImportError:
            logger.debug("[llmobserve] PlayHT SDK not installed - skipping")
            return False
    
    try:
        original_init = Client.__init__
        
        if hasattr(original_init, "_llmobserve_instrumented"):
            logger.debug("[llmobserve] PlayHT already instrumented")
            return True
        
        @functools.wraps(original_init)
        def patched_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            
            # Patch tts() method
            if hasattr(self, "tts"):
                original_tts = self.tts
                if not hasattr(original_tts, "_llmobserve_instrumented"):
                    self.tts = create_tts_wrapper(original_tts, "tts")
                    self.tts._llmobserve_instrumented = True
                    self.tts._llmobserve_original = original_tts
            
            # Patch stream() method
            if hasattr(self, "stream"):
                original_stream = self.stream
                if not hasattr(original_stream, "_llmobserve_instrumented"):
                    self.stream = create_tts_wrapper(original_stream, "stream")
                    self.stream._llmobserve_instrumented = True
                    self.stream._llmobserve_original = original_stream
            
            # Patch get_stream() if available
            if hasattr(self, "get_stream"):
                original_get_stream = self.get_stream
                if not hasattr(original_get_stream, "_llmobserve_instrumented"):
                    self.get_stream = create_tts_wrapper(original_get_stream, "get_stream")
                    self.get_stream._llmobserve_instrumented = True
        
        Client.__init__ = patched_init
        patched_init._llmobserve_instrumented = True
        patched_init._llmobserve_original = original_init
        
        # Try to patch AsyncClient if available
        try:
            from pyht import AsyncClient
            
            original_async_init = AsyncClient.__init__
            
            @functools.wraps(original_async_init)
            def patched_async_init(self, *args, **kwargs):
                original_async_init(self, *args, **kwargs)
                
                if hasattr(self, "tts"):
                    original_tts = self.tts
                    if not hasattr(original_tts, "_llmobserve_instrumented"):
                        self.tts = create_async_wrapper(original_tts, "tts")
                        self.tts._llmobserve_instrumented = True
                
                if hasattr(self, "stream"):
                    original_stream = self.stream
                    if not hasattr(original_stream, "_llmobserve_instrumented"):
                        self.stream = create_async_wrapper(original_stream, "stream")
                        self.stream._llmobserve_instrumented = True
            
            AsyncClient.__init__ = patched_async_init
            patched_async_init._llmobserve_instrumented = True
            
        except ImportError:
            pass
        
        logger.info("[llmobserve] Successfully instrumented PlayHT SDK")
        return True
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument PlayHT: {e}", exc_info=True)
        return False

