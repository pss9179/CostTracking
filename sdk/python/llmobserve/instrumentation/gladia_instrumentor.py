"""
Gladia STT (Speech-to-Text) instrumentor with audio duration tracking.

Supports:
- Real-time transcription
- Async (pre-recorded) transcription
- Models: Fast, Accurate, Solaria

Pricing tiers:
- Self-Serve: Real-time $0.75/hr, Async $0.61/hr
- Scaling: Real-time $0.55/hr, Async $0.50/hr
- Enterprise: Custom pricing
"""
import functools
import time
import uuid
import os
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config


# Gladia pricing (2024 - verified from official pricing page)
# All prices converted to per-minute

GLADIA_PRICING = {
    # Self-Serve tier
    "selfserve": {
        "realtime": 0.0125,  # $0.75/hr
        "async": 0.01017,  # $0.61/hr
    },
    # Scaling tier
    "scaling": {
        "realtime": 0.00917,  # $0.55/hr
        "async": 0.00833,  # $0.50/hr
    },
}

# Available models (same pricing for all models within a tier)
GLADIA_MODELS = ["fast", "accurate", "solaria"]


def get_pricing_tier() -> str:
    """Get the pricing tier from environment. Default is 'selfserve'."""
    return os.environ.get("GLADIA_TIER", "selfserve").lower()


def track_gladia_call(
    method_name: str,
    model: Optional[str],
    audio_duration_seconds: Optional[float],
    latency_ms: float,
    is_realtime: bool = True,
    status: str = "ok",
    error: Optional[str] = None,
    transcript: Optional[str] = None,
    language: Optional[str] = None,
) -> None:
    """Track a Gladia API call with voice-specific fields."""
    
    tier = get_pricing_tier()
    tier_pricing = GLADIA_PRICING.get(tier, GLADIA_PRICING["selfserve"])
    
    # Determine rate based on realtime vs async
    mode = "realtime" if is_realtime else "async"
    rate_per_minute = tier_pricing.get(mode, tier_pricing["realtime"])
    
    duration_minutes = (audio_duration_seconds or 0) / 60.0
    cost_usd = duration_minutes * rate_per_minute
    
    model_name = model or "fast"
    
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": "stt_call",
        "provider": "gladia",
        "endpoint": method_name,
        "model": model_name,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
        "input_tokens": 0,
        "output_tokens": len(transcript.split()) if transcript else 0,
        "status": status,
        "tenant_id": config.get_tenant_id(),
        "customer_id": context.get_customer_id(),
        # Voice-specific fields
        "voice_call_id": context.get_voice_call_id(),
        "audio_duration_seconds": audio_duration_seconds,
        "voice_segment_type": "stt",
        "event_metadata": {
            "error": error,
            "model": model_name,
            "mode": mode,
            "pricing_tier": tier,
            "language": language,
            "transcript": transcript[:500] if transcript else None,
        },
    }
    
    buffer.add_event(event)


def extract_transcript_info(response: Any) -> tuple:
    """Extract transcript text and duration from Gladia response."""
    transcript = None
    duration = None
    
    try:
        # Try to get from response object
        if hasattr(response, 'result'):
            result = response.result
            if hasattr(result, 'transcription'):
                transcription = result.transcription
                if hasattr(transcription, 'full_transcript'):
                    transcript = transcription.full_transcript
                if hasattr(transcription, 'duration'):
                    duration = transcription.duration
        
        # Try dict response
        if isinstance(response, dict):
            result = response.get('result', {})
            transcription = result.get('transcription', {})
            transcript = transcription.get('full_transcript') or transcript
            duration = transcription.get('duration') or duration
            
            # Also check top-level
            if not transcript:
                transcript = response.get('transcription', {}).get('full_transcript')
            if not duration:
                duration = response.get('metadata', {}).get('audio_duration')
    except Exception:
        pass
    
    return transcript, duration


def create_transcribe_wrapper(original_method: Callable, method_name: str, is_realtime: bool = False) -> Callable:
    """Create wrapper for Gladia transcription methods."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        model = kwargs.get("model") or kwargs.get("transcription_config", {}).get("model") or "fast"
        language = kwargs.get("language") or kwargs.get("transcription_config", {}).get("language")
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            transcript, audio_duration = extract_transcript_info(result)
            
            track_gladia_call(
                method_name=method_name,
                model=model,
                audio_duration_seconds=audio_duration,
                latency_ms=latency_ms,
                is_realtime=is_realtime,
                status="ok",
                transcript=transcript,
                language=language,
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_gladia_call(
                method_name=method_name,
                model=model,
                audio_duration_seconds=None,
                latency_ms=latency_ms,
                is_realtime=is_realtime,
                status="error",
                error=str(e),
                language=language,
            )
            
            raise
    
    return wrapper


def instrument_gladia() -> bool:
    """Instrument Gladia SDK."""
    try:
        import gladia
    except ImportError:
        logger.debug("[llmobserve] Gladia SDK not installed - skipping")
        return False
    
    try:
        # Check if already instrumented
        if hasattr(gladia, "_llmobserve_instrumented"):
            logger.debug("[llmobserve] Gladia already instrumented")
            return True
        
        # Try to patch the client
        if hasattr(gladia, 'Gladia') or hasattr(gladia, 'GladiaClient'):
            client_class = getattr(gladia, 'Gladia', None) or getattr(gladia, 'GladiaClient', None)
            
            if client_class:
                original_init = client_class.__init__
                
                @functools.wraps(original_init)
                def patched_init(self, *args, **kwargs):
                    original_init(self, *args, **kwargs)
                    
                    # Patch async transcription methods
                    if hasattr(self, 'audio'):
                        audio = self.audio
                        if hasattr(audio, 'transcription'):
                            transcription = audio.transcription
                            
                            # Patch create method (async/pre-recorded)
                            if hasattr(transcription, 'create'):
                                if not hasattr(transcription.create, '_llmobserve_instrumented'):
                                    original = transcription.create
                                    wrapped = create_transcribe_wrapper(original, "transcription.create", is_realtime=False)
                                    transcription.create = wrapped
                                    wrapped._llmobserve_instrumented = True
                        
                        # Patch live transcription if available
                        if hasattr(audio, 'live'):
                            live = audio.live
                            if hasattr(live, 'create'):
                                if not hasattr(live.create, '_llmobserve_instrumented'):
                                    original = live.create
                                    wrapped = create_transcribe_wrapper(original, "live.create", is_realtime=True)
                                    live.create = wrapped
                                    wrapped._llmobserve_instrumented = True
                
                client_class.__init__ = patched_init
                client_class._llmobserve_instrumented = True
        
        gladia._llmobserve_instrumented = True
        
        logger.info("[llmobserve] Successfully instrumented Gladia SDK")
        return True
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument Gladia: {e}", exc_info=True)
        return False

