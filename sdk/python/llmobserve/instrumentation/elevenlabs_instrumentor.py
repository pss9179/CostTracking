"""
ElevenLabs TTS and STT instrumentor with version guards and fail-open safety.

Supports:
- TTS: client.generate(), client.text_to_speech.convert()
- STT: client.speech_to_text.convert() (Scribe)
"""
import functools
import time
import uuid
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config

# TTS pricing per 1K characters (Pro tier rates)
ELEVENLABS_TTS_PRICING = {
    # Multilingual models (higher quality)
    "eleven_multilingual_v2": 0.24,
    "eleven_multilingual_v3": 0.24,
    # Turbo models (balanced)
    "eleven_turbo_v2": 0.18,
    "eleven_turbo_v2_5": 0.18,
    # Flash models (fastest, cheapest)
    "eleven_flash_v2": 0.12,
    "eleven_flash_v2_5": 0.12,
    # Default (Pro tier multilingual)
    "default": 0.24,
}

# STT pricing per minute (Pro tier rates)
ELEVENLABS_STT_PRICING = {
    "scribe_v1": 0.0067,  # $0.40/hour
    "scribe_v2": 0.0088,  # $0.53/hour (realtime)
    "scribe_v2_realtime": 0.0088,
    "default": 0.0067,
}


def track_elevenlabs_tts(
    method_name: str,
    model: Optional[str],
    character_count: int,
    latency_ms: float,
    voice_id: Optional[str] = None,
    status: str = "ok",
    error: Optional[str] = None,
) -> None:
    """Track an ElevenLabs TTS call."""
    
    model_key = model.lower() if model else "default"
    price_per_1k = ELEVENLABS_TTS_PRICING.get(model_key, ELEVENLABS_TTS_PRICING["default"])
    cost_usd = (character_count / 1000) * price_per_1k
    
    # Estimate audio duration (150 words/min, ~5 chars/word = 750 chars/min)
    estimated_duration = (character_count / 750) * 60  # seconds
    
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


def track_elevenlabs_stt(
    method_name: str,
    model: Optional[str],
    audio_duration_seconds: float,
    latency_ms: float,
    transcript: Optional[str] = None,
    status: str = "ok",
    error: Optional[str] = None,
) -> None:
    """Track an ElevenLabs STT (Scribe) call."""
    
    model_key = model.lower() if model else "default"
    price_per_min = ELEVENLABS_STT_PRICING.get(model_key, ELEVENLABS_STT_PRICING["default"])
    cost_usd = (audio_duration_seconds / 60) * price_per_min
    
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": "stt_call",
        "provider": "elevenlabs",
        "endpoint": method_name,
        "model": model or "scribe_v1",
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
        "input_tokens": 0,
        "output_tokens": len(transcript) if transcript else 0,
        "status": status,
        "tenant_id": config.get_tenant_id(),
        "customer_id": context.get_customer_id(),
        "voice_call_id": context.get_voice_call_id(),
        "audio_duration_seconds": audio_duration_seconds,
        "voice_segment_type": "stt",
        "voice_platform": context.get_voice_platform(),  # Cross-platform tracking
        "event_metadata": {
            "transcript": transcript[:500] if transcript else None,  # Truncate for storage
            "error": error,
        } if any([transcript, error]) else None,
    }
    
    buffer.add_event(event)


def create_tts_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create wrapper for ElevenLabs TTS methods."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        # Extract text input
        text = kwargs.get("text") or (args[0] if len(args) > 0 else "")
        character_count = len(text) if isinstance(text, str) else 0
        
        model_name = kwargs.get("model_id") or kwargs.get("model") or "eleven_multilingual_v2"
        voice_id = kwargs.get("voice_id") or kwargs.get("voice")
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            track_elevenlabs_tts(
                method_name=method_name,
                model=model_name,
                character_count=character_count,
                latency_ms=latency_ms,
                voice_id=voice_id,
                status="ok",
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_elevenlabs_tts(
                method_name=method_name,
                model=model_name,
                character_count=character_count,
                latency_ms=latency_ms,
                voice_id=voice_id,
                status="error",
                error=str(e),
            )
            
            raise
    
    return wrapper


def create_stt_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create wrapper for ElevenLabs STT (Scribe) methods."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        model_name = kwargs.get("model_id") or kwargs.get("model") or "scribe_v1"
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            # Try to extract duration and transcript from result
            audio_duration = 0
            transcript = None
            
            if hasattr(result, "audio_duration"):
                audio_duration = float(result.audio_duration)
            elif hasattr(result, "duration"):
                audio_duration = float(result.duration)
            
            if hasattr(result, "text"):
                transcript = result.text
            elif hasattr(result, "transcript"):
                transcript = result.transcript
            
            # Estimate duration from latency if not available (rough estimate)
            if audio_duration == 0:
                audio_duration = latency_ms / 1000 * 0.5  # Assume 2x realtime processing
            
            track_elevenlabs_stt(
                method_name=method_name,
                model=model_name,
                audio_duration_seconds=audio_duration,
                latency_ms=latency_ms,
                transcript=transcript,
                status="ok",
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_elevenlabs_stt(
                method_name=method_name,
                model=model_name,
                audio_duration_seconds=0,
                latency_ms=latency_ms,
                status="error",
                error=str(e),
            )
            
            raise
    
    return wrapper


def instrument_elevenlabs() -> bool:
    """Instrument ElevenLabs SDK for TTS and STT tracking."""
    try:
        from elevenlabs import ElevenLabs
    except ImportError:
        try:
            from elevenlabs import client
            ElevenLabs = client.ElevenLabs
        except ImportError:
            logger.debug("[llmobserve] ElevenLabs SDK not installed - skipping")
            return False
    
    try:
        original_init = ElevenLabs.__init__
        
        if hasattr(original_init, "_llmobserve_instrumented"):
            logger.debug("[llmobserve] ElevenLabs already instrumented")
            return True
        
        @functools.wraps(original_init)
        def patched_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            
            # Patch TTS methods
            if hasattr(self, "generate"):
                original = self.generate
                if not hasattr(original, "_llmobserve_instrumented"):
                    self.generate = create_tts_wrapper(original, "generate")
                    self.generate._llmobserve_instrumented = True
            
            if hasattr(self, "text_to_speech"):
                tts = self.text_to_speech
                if hasattr(tts, "convert"):
                    original = tts.convert
                    if not hasattr(original, "_llmobserve_instrumented"):
                        tts.convert = create_tts_wrapper(original, "text_to_speech.convert")
                        tts.convert._llmobserve_instrumented = True
                
                if hasattr(tts, "convert_as_stream"):
                    original = tts.convert_as_stream
                    if not hasattr(original, "_llmobserve_instrumented"):
                        tts.convert_as_stream = create_tts_wrapper(original, "text_to_speech.convert_as_stream")
                        tts.convert_as_stream._llmobserve_instrumented = True
            
            # Patch STT (Scribe) methods
            if hasattr(self, "speech_to_text"):
                stt = self.speech_to_text
                if hasattr(stt, "convert"):
                    original = stt.convert
                    if not hasattr(original, "_llmobserve_instrumented"):
                        stt.convert = create_stt_wrapper(original, "speech_to_text.convert")
                        stt.convert._llmobserve_instrumented = True
        
        ElevenLabs.__init__ = patched_init
        patched_init._llmobserve_instrumented = True
        patched_init._llmobserve_original = original_init
        
        logger.info("[llmobserve] Successfully instrumented ElevenLabs SDK")
        return True
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument ElevenLabs: {e}", exc_info=True)
        return False
