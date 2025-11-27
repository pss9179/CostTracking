"""
Deepgram STT (Speech-to-Text) instrumentor with audio duration tracking.

Supports:
- client.listen.prerecorded.transcribe_file() - File transcription
- client.listen.prerecorded.transcribe_url() - URL transcription
- client.listen.live() - Live/streaming transcription
- client.speak.tts() - Text-to-Speech (Aura)
- Voice Agent API - Full voice agent platform
"""
import functools
import time
import uuid
import os
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config


# Deepgram pricing (2024 - verified from official pricing page)
# All prices in per-minute (STT) or per-1K-chars (TTS)

DEEPGRAM_STT_STREAMING_PAYG = {
    "flux": 0.0077,
    "nova-3": 0.0077,  # Monolingual
    "nova-3-mono": 0.0077,
    "nova-3-multi": 0.0092,  # Multilingual
    "nova-1": 0.0058,
    "nova-2": 0.0058,
    "nova": 0.0058,  # Default to nova-1/2
    "enhanced": 0.0165,
    "base": 0.0145,
}

DEEPGRAM_STT_STREAMING_GROWTH = {
    "flux": 0.0065,
    "nova-3": 0.0065,
    "nova-3-mono": 0.0065,
    "nova-3-multi": 0.0078,
    "nova-1": 0.0047,
    "nova-2": 0.0047,
    "nova": 0.0047,
    "enhanced": 0.0136,
    "base": 0.0105,
}

DEEPGRAM_STT_PRERECORDED_PAYG = {
    "nova-3": 0.0043,  # Monolingual
    "nova-3-mono": 0.0043,
    "nova-3-multi": 0.0052,  # Multilingual
    "nova-1": 0.0043,
    "nova-2": 0.0043,
    "nova": 0.0043,
    "nova-2-general": 0.0043,
    "nova-2-meeting": 0.0043,
    "nova-2-phonecall": 0.0043,
    "nova-2-medical": 0.0073,
    "enhanced": 0.0145,
    "base": 0.0125,
    "whisper-large": 0.0048,
}

DEEPGRAM_STT_PRERECORDED_GROWTH = {
    "nova-3": 0.0036,
    "nova-3-mono": 0.0036,
    "nova-3-multi": 0.0043,
    "nova-1": 0.0035,
    "nova-2": 0.0035,
    "nova": 0.0035,
    "nova-2-general": 0.0035,
    "nova-2-meeting": 0.0035,
    "nova-2-phonecall": 0.0035,
    "nova-2-medical": 0.0058,  # Estimated ~85% of PAYG
    "enhanced": 0.0115,
    "base": 0.0095,
    "whisper-large": 0.0048,  # Same for PAYG and Growth
}

DEEPGRAM_STT_ADDONS_PAYG = {
    "redaction": 0.0020,
    "keyterm": 0.0013,
    "diarization": 0.0020,
    "entity_detection": 0.0017,
}

DEEPGRAM_STT_ADDONS_GROWTH = {
    "redaction": 0.0017,
    "keyterm": 0.0012,
    "diarization": 0.0017,
    "entity_detection": 0.0017,  # Same for both
}

DEEPGRAM_TTS_PAYG = {
    "aura-2": 0.030,
    "aura-1": 0.015,
    "aura": 0.015,  # Default to aura-1
    "default": 0.030,  # Default to aura-2
}

DEEPGRAM_TTS_GROWTH = {
    "aura-2": 0.027,
    "aura-1": 0.0135,
    "aura": 0.0135,
    "default": 0.027,
}

DEEPGRAM_VOICE_AGENT_PAYG = {
    "standard": 0.08,
    "standard-byo-tts": 0.06,
    "custom-byo-llm": 0.07,
    "custom-byo-all": 0.05,
    "advanced": 0.16,
    "advanced-byo-tts": 0.12,
}

DEEPGRAM_VOICE_AGENT_GROWTH = {
    "standard": 0.07,
    "standard-byo-tts": 0.05,
    "custom-byo-llm": 0.06,
    "custom-byo-all": 0.04,
    "advanced": 0.15,
    "advanced-byo-tts": 0.11,
}


def get_pricing_tier() -> str:
    """Get the pricing tier from environment. Default is 'payg'."""
    return os.environ.get("DEEPGRAM_TIER", "payg").lower()


def track_deepgram_call(
    method_name: str,
    model: Optional[str],
    audio_duration_seconds: Optional[float],
    latency_ms: float,
    status: str = "ok",
    error: Optional[str] = None,
    is_tts: bool = False,
    is_streaming: bool = False,
    character_count: int = 0,
    transcript: Optional[str] = None,
    addons: Optional[list] = None,
) -> None:
    """Track a Deepgram API call with voice-specific fields."""
    
    tier = get_pricing_tier()
    is_growth = tier == "growth"
    
    # Determine pricing based on model and type
    if is_tts:
        # TTS pricing per 1K chars
        tts_pricing = DEEPGRAM_TTS_GROWTH if is_growth else DEEPGRAM_TTS_PAYG
        model_key = (model or "").lower().split("-")[0] if model else "default"
        if "aura-2" in (model or "").lower():
            model_key = "aura-2"
        elif "aura" in (model or "").lower():
            model_key = "aura-1"
        rate_per_1k = tts_pricing.get(model_key, tts_pricing["default"])
        cost_usd = (character_count / 1000) * rate_per_1k
        voice_segment_type = "tts"
        span_type = "tts_call"
    else:
        # STT pricing: varies by model, streaming vs prerecorded, and tier
        if is_streaming:
            stt_pricing = DEEPGRAM_STT_STREAMING_GROWTH if is_growth else DEEPGRAM_STT_STREAMING_PAYG
        else:
            stt_pricing = DEEPGRAM_STT_PRERECORDED_GROWTH if is_growth else DEEPGRAM_STT_PRERECORDED_PAYG
        
        model_key = (model or "nova-2").lower()
        rate_per_minute = stt_pricing.get(model_key, stt_pricing.get("nova", 0.0043))
        duration_minutes = (audio_duration_seconds or 0) / 60.0
        base_cost = duration_minutes * rate_per_minute
        
        # Add addon costs
        addon_cost = 0.0
        if addons:
            addon_pricing = DEEPGRAM_STT_ADDONS_GROWTH if is_growth else DEEPGRAM_STT_ADDONS_PAYG
            for addon in addons:
                addon_key = addon.lower().replace("_", "")
                if addon_key in addon_pricing:
                    addon_cost += duration_minutes * addon_pricing[addon_key]
        
        cost_usd = base_cost + addon_cost
        voice_segment_type = "stt"
        span_type = "stt_call"
    
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": span_type,
        "provider": "deepgram",
        "endpoint": method_name,
        "model": model,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
        "input_tokens": character_count if is_tts else 0,
        "output_tokens": 0,
        "status": status,
        "tenant_id": config.get_tenant_id(),
        "customer_id": context.get_customer_id(),
        # Voice-specific fields
        "voice_call_id": context.get_voice_call_id(),
        "audio_duration_seconds": audio_duration_seconds,
        "voice_segment_type": voice_segment_type,
        "voice_platform": context.get_voice_platform(),  # Cross-platform tracking (diy, vapi, etc.)
        "event_metadata": {
            "error": error,
            "audio_duration_seconds": audio_duration_seconds,
            "character_count": character_count if is_tts else None,
            "transcript": transcript[:500] if transcript else None,
        } if error or audio_duration_seconds or transcript else None,
    }
    
    buffer.add_event(event)


def extract_audio_duration(response: Any) -> Optional[float]:
    """Extract audio duration from Deepgram response."""
    try:
        # Try to get duration from response metadata
        if hasattr(response, 'metadata') and hasattr(response.metadata, 'duration'):
            return response.metadata.duration
        if hasattr(response, 'results') and hasattr(response.results, 'duration'):
            return response.results.duration
        # Check for dict response
        if isinstance(response, dict):
            if 'metadata' in response and 'duration' in response['metadata']:
                return response['metadata']['duration']
            if 'results' in response and 'duration' in response['results']:
                return response['results']['duration']
    except Exception:
        pass
    return None


def extract_transcript(response: Any) -> Optional[str]:
    """Extract transcript text from Deepgram response."""
    try:
        # Try to get transcript from results
        if hasattr(response, 'results') and hasattr(response.results, 'channels'):
            channels = response.results.channels
            if channels and len(channels) > 0:
                alternatives = getattr(channels[0], 'alternatives', [])
                if alternatives and len(alternatives) > 0:
                    transcript = getattr(alternatives[0], 'transcript', None)
                    if transcript:
                        return transcript[:1000]  # Truncate to 1000 chars
        
        # Check for dict response
        if isinstance(response, dict):
            results = response.get('results', {})
            channels = results.get('channels', [])
            if channels and len(channels) > 0:
                alternatives = channels[0].get('alternatives', [])
                if alternatives and len(alternatives) > 0:
                    transcript = alternatives[0].get('transcript', '')
                    if transcript:
                        return transcript[:1000]
    except Exception:
        pass
    return None


def create_stt_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create safe wrapper for Deepgram STT methods."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        model_name = kwargs.get("model") or kwargs.get("options", {}).get("model") or "nova-2"
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract audio duration and transcript from response
            audio_duration = extract_audio_duration(result)
            transcript = extract_transcript(result)
            
            track_deepgram_call(
                method_name=method_name,
                model=model_name,
                audio_duration_seconds=audio_duration,
                latency_ms=latency_ms,
                status="ok",
                transcript=transcript,
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_deepgram_call(
                method_name=method_name,
                model=model_name,
                audio_duration_seconds=None,
                latency_ms=latency_ms,
                status="error",
                error=str(e)
            )
            
            raise
    
    return wrapper


def create_tts_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create safe wrapper for Deepgram TTS methods."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        # Extract text input to count characters
        text = kwargs.get("text") or (args[0] if len(args) > 0 else "")
        character_count = len(text) if isinstance(text, str) else 0
        model_name = kwargs.get("model") or "aura-asteria-en"
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            # Estimate audio duration from character count (avg 15 chars/second)
            estimated_duration = character_count / 15.0
            
            track_deepgram_call(
                method_name=method_name,
                model=model_name,
                audio_duration_seconds=estimated_duration,
                latency_ms=latency_ms,
                status="ok",
                is_tts=True,
                character_count=character_count
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_deepgram_call(
                method_name=method_name,
                model=model_name,
                audio_duration_seconds=None,
                latency_ms=latency_ms,
                status="error",
                error=str(e),
                is_tts=True,
                character_count=character_count
            )
            
            raise
    
    return wrapper


def instrument_deepgram() -> bool:
    """Instrument Deepgram SDK."""
    try:
        from deepgram import DeepgramClient
    except ImportError:
        logger.debug("[llmobserve] Deepgram SDK not installed - skipping")
        return False
    
    try:
        # Check if already instrumented
        if hasattr(DeepgramClient, "_llmobserve_instrumented"):
            logger.debug("[llmobserve] Deepgram already instrumented")
            return True
        
        # Patch prerecorded transcription methods
        original_init = DeepgramClient.__init__
        
        @functools.wraps(original_init)
        def patched_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            
            # Patch listen.prerecorded methods if they exist
            if hasattr(self, 'listen') and hasattr(self.listen, 'prerecorded'):
                prerecorded = self.listen.prerecorded
                
                if hasattr(prerecorded, 'transcribe_file'):
                    if not hasattr(prerecorded.transcribe_file, '_llmobserve_instrumented'):
                        original = prerecorded.transcribe_file
                        wrapped = create_stt_wrapper(original, "transcribe_file")
                        prerecorded.transcribe_file = wrapped
                        wrapped._llmobserve_instrumented = True
                
                if hasattr(prerecorded, 'transcribe_url'):
                    if not hasattr(prerecorded.transcribe_url, '_llmobserve_instrumented'):
                        original = prerecorded.transcribe_url
                        wrapped = create_stt_wrapper(original, "transcribe_url")
                        prerecorded.transcribe_url = wrapped
                        wrapped._llmobserve_instrumented = True
            
            # Patch speak.tts methods if they exist
            if hasattr(self, 'speak') and hasattr(self.speak, 'v'):
                speak_v = self.speak.v
                if hasattr(speak_v, 'save'):
                    if not hasattr(speak_v.save, '_llmobserve_instrumented'):
                        original = speak_v.save
                        wrapped = create_tts_wrapper(original, "speak.save")
                        speak_v.save = wrapped
                        wrapped._llmobserve_instrumented = True
        
        DeepgramClient.__init__ = patched_init
        DeepgramClient._llmobserve_instrumented = True
        
        logger.info("[llmobserve] Successfully instrumented Deepgram SDK")
        return True
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument Deepgram: {e}", exc_info=True)
        return False

