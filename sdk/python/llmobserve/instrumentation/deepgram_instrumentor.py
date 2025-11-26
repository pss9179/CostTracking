"""
Deepgram STT (Speech-to-Text) instrumentor with audio duration tracking.

Supports:
- client.listen.prerecorded.transcribe_file() - File transcription
- client.listen.prerecorded.transcribe_url() - URL transcription
- client.listen.live() - Live/streaming transcription
- client.speak.tts() - Text-to-Speech (Aura)
"""
import functools
import time
import uuid
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config


def track_deepgram_call(
    method_name: str,
    model: Optional[str],
    audio_duration_seconds: Optional[float],
    latency_ms: float,
    status: str = "ok",
    error: Optional[str] = None,
    is_tts: bool = False,
    character_count: int = 0,
    transcript: Optional[str] = None,
) -> None:
    """Track a Deepgram API call with voice-specific fields."""
    
    # Determine pricing based on model and type
    if is_tts:
        # Deepgram Aura TTS: $0.015 per 1K chars
        cost_usd = (character_count / 1000) * 0.015
        voice_segment_type = "tts"
        span_type = "tts_call"
    else:
        # STT pricing: varies by model
        pricing = {
            "nova-2": 0.0043,
            "nova-2-general": 0.0043,
            "nova-2-meeting": 0.0043,
            "nova-2-phonecall": 0.0043,
            "nova-2-medical": 0.0073,
            "nova": 0.0043,
            "whisper-large": 0.0048,
            "base": 0.0125,
        }
        rate_per_minute = pricing.get(model or "nova-2", 0.0043)
        duration_minutes = (audio_duration_seconds or 0) / 60.0
        cost_usd = duration_minutes * rate_per_minute
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

