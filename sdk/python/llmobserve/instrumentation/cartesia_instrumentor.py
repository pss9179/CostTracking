"""
Cartesia TTS instrumentor with fail-open safety.

Tracks costs for:
- Sonic model: $0.040 per 1K characters
- Sonic Turbo: $0.015 per 1K characters

Supports:
- client.tts.bytes() - synchronous TTS
- client.tts.sse() - streaming TTS
- AsyncCartesia equivalents
"""
import functools
import time
import uuid
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config

# Cartesia uses credits: 1 credit = 1 character for TTS
# Pricing varies by plan. Set CARTESIA_PLAN env var to override.
# Options: pro-monthly, pro-yearly, startup-monthly, startup-yearly, scale-monthly, scale-yearly
import os

CARTESIA_PLAN_PRICING = {
    # Plan: cost per 1K credits (= per 1K chars for TTS)
    "pro-monthly": 0.050,      # $5/100K
    "pro-yearly": 0.040,       # $4/100K
    "startup-monthly": 0.039,  # $49/1.25M
    "startup-yearly": 0.031,   # $39/1.25M (DEFAULT - most common for production)
    "scale-monthly": 0.037,    # $299/8M
    "scale-yearly": 0.030,     # $239/8M
}

def get_cartesia_price_per_1k() -> float:
    """Get Cartesia price based on user's plan (from env var or default)."""
    plan = os.environ.get("CARTESIA_PLAN", "startup-yearly").lower()
    return CARTESIA_PLAN_PRICING.get(plan, CARTESIA_PLAN_PRICING["startup-yearly"])

CARTESIA_PRICING = {
    "sonic-english": get_cartesia_price_per_1k(),
    "sonic-multilingual": get_cartesia_price_per_1k(),
    "sonic": get_cartesia_price_per_1k(),
    "sonic-2": get_cartesia_price_per_1k(),
    "default": get_cartesia_price_per_1k(),
}


def track_cartesia_call(
    method_name: str,
    model: Optional[str],
    character_count: int,
    latency_ms: float,
    voice_id: Optional[str] = None,
    status: str = "ok",
    error: Optional[str] = None,
) -> None:
    """Track a Cartesia TTS API call."""
    
    # Calculate cost based on model
    model_key = model.lower() if model else "default"
    price_per_1k = CARTESIA_PRICING.get(model_key, CARTESIA_PRICING["default"])
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
        "provider": "cartesia",
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
        "voice_platform": context.get_voice_platform(),  # Cross-platform tracking
        "event_metadata": {
            "character_count": character_count,
            "voice_id": voice_id,
            "error": error,
        } if any([character_count, voice_id, error]) else None,
    }
    
    buffer.add_event(event)


def extract_text_length(args, kwargs) -> int:
    """Extract text length from Cartesia API call arguments."""
    # Check kwargs first
    transcript = kwargs.get("transcript")
    if transcript:
        if isinstance(transcript, str):
            return len(transcript)
        elif isinstance(transcript, dict):
            return len(transcript.get("text", ""))
    
    # Check positional args
    for arg in args:
        if isinstance(arg, str):
            return len(arg)
        elif isinstance(arg, dict) and "text" in arg:
            return len(arg["text"])
    
    return 0


def create_tts_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create wrapper for Cartesia TTS methods."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        # Extract parameters
        character_count = extract_text_length(args, kwargs)
        model_id = kwargs.get("model_id") or kwargs.get("model")
        voice_id = kwargs.get("voice_id")
        if isinstance(kwargs.get("voice"), dict):
            voice_id = kwargs["voice"].get("id")
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            track_cartesia_call(
                method_name=method_name,
                model=model_id,
                character_count=character_count,
                latency_ms=latency_ms,
                voice_id=voice_id,
                status="ok",
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_cartesia_call(
                method_name=method_name,
                model=model_id,
                character_count=character_count,
                latency_ms=latency_ms,
                voice_id=voice_id,
                status="error",
                error=str(e),
            )
            
            raise
    
    return wrapper


def create_async_tts_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create async wrapper for Cartesia TTS methods."""
    @functools.wraps(original_method)
    async def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return await original_method(*args, **kwargs)
        
        start_time = time.time()
        
        character_count = extract_text_length(args, kwargs)
        model_id = kwargs.get("model_id") or kwargs.get("model")
        voice_id = kwargs.get("voice_id")
        if isinstance(kwargs.get("voice"), dict):
            voice_id = kwargs["voice"].get("id")
        
        try:
            result = await original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            track_cartesia_call(
                method_name=method_name,
                model=model_id,
                character_count=character_count,
                latency_ms=latency_ms,
                voice_id=voice_id,
                status="ok",
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_cartesia_call(
                method_name=method_name,
                model=model_id,
                character_count=character_count,
                latency_ms=latency_ms,
                voice_id=voice_id,
                status="error",
                error=str(e),
            )
            
            raise
    
    return wrapper


def instrument_cartesia() -> bool:
    """Instrument Cartesia SDK for TTS tracking."""
    try:
        from cartesia import Cartesia
    except ImportError:
        logger.debug("[llmobserve] Cartesia SDK not installed - skipping")
        return False
    
    try:
        original_init = Cartesia.__init__
        
        if hasattr(original_init, "_llmobserve_instrumented"):
            logger.debug("[llmobserve] Cartesia already instrumented")
            return True
        
        @functools.wraps(original_init)
        def patched_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            
            # Patch tts.bytes()
            if hasattr(self, "tts") and hasattr(self.tts, "bytes"):
                original_bytes = self.tts.bytes
                if not hasattr(original_bytes, "_llmobserve_instrumented"):
                    self.tts.bytes = create_tts_wrapper(original_bytes, "tts.bytes")
                    self.tts.bytes._llmobserve_instrumented = True
                    self.tts.bytes._llmobserve_original = original_bytes
            
            # Patch tts.sse() for streaming
            if hasattr(self, "tts") and hasattr(self.tts, "sse"):
                original_sse = self.tts.sse
                if not hasattr(original_sse, "_llmobserve_instrumented"):
                    self.tts.sse = create_tts_wrapper(original_sse, "tts.sse")
                    self.tts.sse._llmobserve_instrumented = True
                    self.tts.sse._llmobserve_original = original_sse
        
        Cartesia.__init__ = patched_init
        patched_init._llmobserve_instrumented = True
        patched_init._llmobserve_original = original_init
        
        # Try to patch AsyncCartesia if available
        try:
            from cartesia import AsyncCartesia
            
            original_async_init = AsyncCartesia.__init__
            
            @functools.wraps(original_async_init)
            def patched_async_init(self, *args, **kwargs):
                original_async_init(self, *args, **kwargs)
                
                if hasattr(self, "tts") and hasattr(self.tts, "bytes"):
                    original_bytes = self.tts.bytes
                    if not hasattr(original_bytes, "_llmobserve_instrumented"):
                        self.tts.bytes = create_async_tts_wrapper(original_bytes, "tts.bytes")
                        self.tts.bytes._llmobserve_instrumented = True
                
                if hasattr(self, "tts") and hasattr(self.tts, "sse"):
                    original_sse = self.tts.sse
                    if not hasattr(original_sse, "_llmobserve_instrumented"):
                        self.tts.sse = create_async_tts_wrapper(original_sse, "tts.sse")
                        self.tts.sse._llmobserve_instrumented = True
            
            AsyncCartesia.__init__ = patched_async_init
            patched_async_init._llmobserve_instrumented = True
            
        except ImportError:
            pass
        
        logger.info("[llmobserve] Successfully instrumented Cartesia SDK")
        return True
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument Cartesia: {e}", exc_info=True)
        return False

