"""
LiveKit Voice Agent instrumentor with full pipeline tracking.

Supports:
- livekit.agents.VoicePipelineAgent - Full voice agent with STT/LLM/TTS
- livekit.plugins.deepgram - Deepgram STT plugin
- livekit.plugins.openai - OpenAI STT/TTS plugins
- livekit.plugins.elevenlabs - ElevenLabs TTS plugin
- livekit.plugins.silero - VAD plugin
"""
import functools
import time
import uuid
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config


# LiveKit pricing (as of 2024)
LIVEKIT_PRICING = {
    # Voice Agent Platform
    "voice_agent": 0.04,  # $0.04/min for full agent
    "room": 0.002,  # $0.002/min per participant
    
    # STT plugins
    "deepgram": 0.0043,  # Deepgram nova-2
    "whisper": 0.006,  # OpenAI Whisper
    "azure_speech": 0.001,  # Azure STT
    
    # TTS plugins  
    "elevenlabs": 0.18,  # $0.18/1K chars
    "openai_tts": 0.015,  # $0.015/1K chars
    "cartesia": 0.015,  # $0.015/1K chars
    "playht": 0.40,  # $0.40/1K chars
    
    # LLM (passthrough to provider)
    "openai": 0.0,  # Tracked separately
    "anthropic": 0.0,  # Tracked separately
}


def track_livekit_call(
    method_name: str,
    segment_type: str,  # "stt", "llm", "tts", "agent", "room"
    model: Optional[str] = None,
    audio_duration_seconds: Optional[float] = None,
    character_count: int = 0,
    latency_ms: float = 0,
    status: str = "ok",
    error: Optional[str] = None,
    room_name: Optional[str] = None,
    participant_count: int = 1,
) -> None:
    """Track a LiveKit API call with voice-specific fields."""
    
    # Calculate cost based on segment type
    if segment_type == "stt":
        rate = LIVEKIT_PRICING.get(model or "deepgram", 0.0043)
        duration_minutes = (audio_duration_seconds or 0) / 60.0
        cost_usd = duration_minutes * rate
        span_type = "stt_call"
    elif segment_type == "tts":
        rate = LIVEKIT_PRICING.get(model or "elevenlabs", 0.18)
        cost_usd = (character_count / 1000) * rate
        span_type = "tts_call"
    elif segment_type == "agent":
        duration_minutes = (audio_duration_seconds or 0) / 60.0
        cost_usd = duration_minutes * LIVEKIT_PRICING["voice_agent"]
        span_type = "voice_agent_call"
    elif segment_type == "room":
        duration_minutes = (audio_duration_seconds or 0) / 60.0
        cost_usd = duration_minutes * LIVEKIT_PRICING["room"] * participant_count
        span_type = "room_call"
    else:
        cost_usd = 0.0
        span_type = f"{segment_type}_call"
    
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": span_type,
        "provider": "livekit",
        "endpoint": method_name,
        "model": model,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
        "input_tokens": character_count if segment_type == "tts" else 0,
        "output_tokens": 0,
        "status": status,
        "tenant_id": config.get_tenant_id(),
        "customer_id": context.get_customer_id(),
        # Voice-specific fields
        "voice_call_id": context.get_voice_call_id(),
        "audio_duration_seconds": audio_duration_seconds,
        "voice_segment_type": segment_type if segment_type in ["stt", "llm", "tts", "telephony"] else "agent",
        "event_metadata": {
            "error": error,
            "room_name": room_name,
            "participant_count": participant_count,
            "character_count": character_count if segment_type == "tts" else None,
        },
    }
    
    buffer.add_event(event)


def create_stt_wrapper(original_method: Callable, method_name: str, plugin_name: str) -> Callable:
    """Create wrapper for LiveKit STT plugin methods."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            # Try to extract audio duration from result
            audio_duration = None
            if hasattr(result, 'duration'):
                audio_duration = result.duration
            elif hasattr(result, 'metadata') and hasattr(result.metadata, 'duration'):
                audio_duration = result.metadata.duration
            
            track_livekit_call(
                method_name=method_name,
                segment_type="stt",
                model=plugin_name,
                audio_duration_seconds=audio_duration,
                latency_ms=latency_ms,
                status="ok"
            )
            
            return result
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            track_livekit_call(
                method_name=method_name,
                segment_type="stt",
                model=plugin_name,
                latency_ms=latency_ms,
                status="error",
                error=str(e)
            )
            raise
    
    return wrapper


def create_tts_wrapper(original_method: Callable, method_name: str, plugin_name: str) -> Callable:
    """Create wrapper for LiveKit TTS plugin methods."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        # Extract text for character count
        text = kwargs.get("text") or (args[0] if len(args) > 0 else "")
        character_count = len(text) if isinstance(text, str) else 0
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            # Estimate audio duration (avg 15 chars/second)
            estimated_duration = character_count / 15.0
            
            track_livekit_call(
                method_name=method_name,
                segment_type="tts",
                model=plugin_name,
                audio_duration_seconds=estimated_duration,
                character_count=character_count,
                latency_ms=latency_ms,
                status="ok"
            )
            
            return result
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            track_livekit_call(
                method_name=method_name,
                segment_type="tts",
                model=plugin_name,
                character_count=character_count,
                latency_ms=latency_ms,
                status="error",
                error=str(e)
            )
            raise
    
    return wrapper


def create_agent_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create wrapper for VoicePipelineAgent methods."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        # Generate voice_call_id for this agent session
        voice_call_id = context.get_voice_call_id() or str(uuid.uuid4())
        if not context.get_voice_call_id():
            context.set_voice_call_id(voice_call_id)
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            track_livekit_call(
                method_name=method_name,
                segment_type="agent",
                latency_ms=latency_ms,
                status="ok"
            )
            
            return result
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            track_livekit_call(
                method_name=method_name,
                segment_type="agent",
                latency_ms=latency_ms,
                status="error",
                error=str(e)
            )
            raise
    
    return wrapper


def instrument_livekit() -> bool:
    """Instrument LiveKit SDK and plugins."""
    instrumented_any = False
    
    # Try to instrument livekit-agents VoicePipelineAgent
    try:
        from livekit.agents.voice_assistant import VoicePipelineAgent
        
        if not hasattr(VoicePipelineAgent, "_llmobserve_instrumented"):
            # Patch start method
            if hasattr(VoicePipelineAgent, "start"):
                original_start = VoicePipelineAgent.start
                wrapped_start = create_agent_wrapper(original_start, "VoicePipelineAgent.start")
                VoicePipelineAgent.start = wrapped_start
                wrapped_start._llmobserve_instrumented = True
            
            VoicePipelineAgent._llmobserve_instrumented = True
            logger.info("[llmobserve] Instrumented livekit.agents.VoicePipelineAgent")
            instrumented_any = True
    except ImportError:
        logger.debug("[llmobserve] livekit-agents not installed - skipping VoicePipelineAgent")
    
    # Try to instrument Deepgram plugin
    try:
        from livekit.plugins import deepgram as lk_deepgram
        
        if hasattr(lk_deepgram, "STT") and not hasattr(lk_deepgram.STT, "_llmobserve_instrumented"):
            if hasattr(lk_deepgram.STT, "recognize"):
                original = lk_deepgram.STT.recognize
                wrapped = create_stt_wrapper(original, "deepgram.STT.recognize", "deepgram")
                lk_deepgram.STT.recognize = wrapped
                wrapped._llmobserve_instrumented = True
            
            lk_deepgram.STT._llmobserve_instrumented = True
            logger.info("[llmobserve] Instrumented livekit.plugins.deepgram.STT")
            instrumented_any = True
    except ImportError:
        logger.debug("[llmobserve] livekit-plugins-deepgram not installed - skipping")
    
    # Try to instrument ElevenLabs plugin
    try:
        from livekit.plugins import elevenlabs as lk_elevenlabs
        
        if hasattr(lk_elevenlabs, "TTS") and not hasattr(lk_elevenlabs.TTS, "_llmobserve_instrumented"):
            if hasattr(lk_elevenlabs.TTS, "synthesize"):
                original = lk_elevenlabs.TTS.synthesize
                wrapped = create_tts_wrapper(original, "elevenlabs.TTS.synthesize", "elevenlabs")
                lk_elevenlabs.TTS.synthesize = wrapped
                wrapped._llmobserve_instrumented = True
            
            lk_elevenlabs.TTS._llmobserve_instrumented = True
            logger.info("[llmobserve] Instrumented livekit.plugins.elevenlabs.TTS")
            instrumented_any = True
    except ImportError:
        logger.debug("[llmobserve] livekit-plugins-elevenlabs not installed - skipping")
    
    # Try to instrument OpenAI plugin (TTS)
    try:
        from livekit.plugins import openai as lk_openai
        
        if hasattr(lk_openai, "TTS") and not hasattr(lk_openai.TTS, "_llmobserve_instrumented"):
            if hasattr(lk_openai.TTS, "synthesize"):
                original = lk_openai.TTS.synthesize
                wrapped = create_tts_wrapper(original, "openai.TTS.synthesize", "openai_tts")
                lk_openai.TTS.synthesize = wrapped
                wrapped._llmobserve_instrumented = True
            
            lk_openai.TTS._llmobserve_instrumented = True
            logger.info("[llmobserve] Instrumented livekit.plugins.openai.TTS")
            instrumented_any = True
    except ImportError:
        logger.debug("[llmobserve] livekit-plugins-openai not installed - skipping")
    
    # Try to instrument Cartesia plugin
    try:
        from livekit.plugins import cartesia as lk_cartesia
        
        if hasattr(lk_cartesia, "TTS") and not hasattr(lk_cartesia.TTS, "_llmobserve_instrumented"):
            if hasattr(lk_cartesia.TTS, "synthesize"):
                original = lk_cartesia.TTS.synthesize
                wrapped = create_tts_wrapper(original, "cartesia.TTS.synthesize", "cartesia")
                lk_cartesia.TTS.synthesize = wrapped
                wrapped._llmobserve_instrumented = True
            
            lk_cartesia.TTS._llmobserve_instrumented = True
            logger.info("[llmobserve] Instrumented livekit.plugins.cartesia.TTS")
            instrumented_any = True
    except ImportError:
        logger.debug("[llmobserve] livekit-plugins-cartesia not installed - skipping")
    
    if instrumented_any:
        logger.info("[llmobserve] Successfully instrumented LiveKit SDK")
    else:
        logger.debug("[llmobserve] No LiveKit components found to instrument")
    
    return instrumented_any

