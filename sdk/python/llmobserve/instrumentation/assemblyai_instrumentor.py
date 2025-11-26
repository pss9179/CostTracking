"""
AssemblyAI STT (Speech-to-Text) instrumentor with audio duration tracking.

Supports:
- assemblyai.Transcriber.transcribe() - Synchronous transcription
- assemblyai.Transcriber.transcribe_async() - Async transcription
- assemblyai.Transcriber.submit() - Submit for batch processing
- assemblyai.RealtimeTranscriber - Real-time streaming
"""
import functools
import time
import uuid
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config


# AssemblyAI pricing (2024 - verified from official pricing page)
ASSEMBLYAI_PRICING = {
    # Core transcription models (per minute)
    "universal": 0.0025,  # $0.15/hr - Pre-recorded and streaming
    "universal-streaming": 0.0025,  # $0.15/hr - Streaming
    "universal-streaming-multilingual": 0.0025,  # $0.15/hr - Multilingual streaming
    "slam-1": 0.0045,  # $0.27/hr - Highest accuracy (English only, Beta)
    "best": 0.0025,  # Legacy alias - maps to universal
    "nano": 0.0025,  # Legacy alias - maps to universal
    "default": 0.0025,  # Default to universal
    
    # Add-ons (per minute, on top of base transcription)
    "keyterms_prompting": 0.00067,  # $0.04/hr - Keyterms prompting add-on
    
    # Speech Understanding add-ons (per minute)
    "speaker_identification": 0.00033,  # $0.02/hr - Speaker identification
    "translation": 0.001,  # $0.06/hr - Translation
    "custom_formatting": 0.0005,  # $0.03/hr - Custom formatting
    "entity_detection": 0.00133,  # $0.08/hr - Entity detection
    "sentiment_analysis": 0.00033,  # $0.02/hr - Sentiment analysis
    "auto_chapters": 0.00133,  # $0.08/hr - Auto chapters
    "key_phrases": 0.00017,  # $0.01/hr - Key phrases
    "topic_detection": 0.0025,  # $0.15/hr - Topic detection
    "summarization": 0.0005,  # $0.03/hr - Summarization
    
    # Guardrails add-ons (per minute)
    "profanity_filtering": 0.00017,  # $0.01/hr - Profanity filtering
    "pii_audio_redaction": 0.00083,  # $0.05/hr - PII audio redaction
    "pii_redaction": 0.00133,  # $0.08/hr - PII redaction
    "content_moderation": 0.0025,  # $0.15/hr - Content moderation
}


def track_assemblyai_call(
    method_name: str,
    model: Optional[str],
    audio_duration_seconds: Optional[float],
    latency_ms: float,
    status: str = "ok",
    error: Optional[str] = None,
    features_used: Optional[list] = None,
    transcript_text: Optional[str] = None,
) -> None:
    """Track an AssemblyAI API call with voice-specific fields."""
    
    # Calculate base cost
    tier = model or "best"
    rate_per_minute = ASSEMBLYAI_PRICING.get(tier, ASSEMBLYAI_PRICING["default"])
    duration_minutes = (audio_duration_seconds or 0) / 60.0
    base_cost = duration_minutes * rate_per_minute
    
    # Add feature costs
    feature_cost = 0.0
    if features_used:
        for feature in features_used:
            if feature in ASSEMBLYAI_PRICING:
                feature_cost += duration_minutes * ASSEMBLYAI_PRICING[feature]
    
    cost_usd = base_cost + feature_cost
    
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": "stt_call",
        "provider": "assemblyai",
        "endpoint": method_name,
        "model": tier,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
        "input_tokens": 0,
        "output_tokens": len(transcript_text.split()) if transcript_text else 0,  # Word count
        "status": status,
        "tenant_id": config.get_tenant_id(),
        "customer_id": context.get_customer_id(),
        # Voice-specific fields
        "voice_call_id": context.get_voice_call_id(),
        "audio_duration_seconds": audio_duration_seconds,
        "voice_segment_type": "stt",
        "event_metadata": {
            "error": error,
            "audio_duration_seconds": audio_duration_seconds,
            "features_used": features_used,
            "transcript": transcript_text[:500] if transcript_text else None,  # Truncate for storage
            "word_count": len(transcript_text.split()) if transcript_text else 0,
        },
    }
    
    buffer.add_event(event)


def extract_transcript_info(result: Any) -> tuple:
    """Extract audio duration and transcript from AssemblyAI response."""
    audio_duration = None
    transcript_text = None
    
    try:
        # Transcript object has audio_duration in seconds
        if hasattr(result, 'audio_duration'):
            audio_duration = result.audio_duration
        
        # Get the transcript text
        if hasattr(result, 'text'):
            transcript_text = result.text
        
        # Check for dict response
        if isinstance(result, dict):
            audio_duration = result.get('audio_duration', audio_duration)
            transcript_text = result.get('text', transcript_text)
    except Exception:
        pass
    
    return audio_duration, transcript_text


def extract_features_from_config(config_obj: Any) -> list:
    """Extract enabled features from AssemblyAI TranscriptionConfig."""
    features = []
    
    try:
        if hasattr(config_obj, 'speaker_labels') and config_obj.speaker_labels:
            features.append('speaker_labels')
        if hasattr(config_obj, 'content_safety') and config_obj.content_safety:
            features.append('content_moderation')
        if hasattr(config_obj, 'iab_categories') and config_obj.iab_categories:
            features.append('iab_categories')
        if hasattr(config_obj, 'sentiment_analysis') and config_obj.sentiment_analysis:
            features.append('sentiment_analysis')
        if hasattr(config_obj, 'entity_detection') and config_obj.entity_detection:
            features.append('entity_detection')
        if hasattr(config_obj, 'summarization') and config_obj.summarization:
            features.append('summarization')
        if hasattr(config_obj, 'auto_chapters') and config_obj.auto_chapters:
            features.append('auto_chapters')
    except Exception:
        pass
    
    return features


def create_transcribe_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create wrapper for AssemblyAI transcribe methods."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        # Extract model/tier from config
        model = "best"
        features_used = []
        
        transcription_config = kwargs.get('config')
        if transcription_config:
            if hasattr(transcription_config, 'speech_model'):
                model = str(transcription_config.speech_model) if transcription_config.speech_model else "best"
            features_used = extract_features_from_config(transcription_config)
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract info from result
            audio_duration, transcript_text = extract_transcript_info(result)
            
            track_assemblyai_call(
                method_name=method_name,
                model=model,
                audio_duration_seconds=audio_duration,
                latency_ms=latency_ms,
                status="ok",
                features_used=features_used,
                transcript_text=transcript_text,
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_assemblyai_call(
                method_name=method_name,
                model=model,
                audio_duration_seconds=None,
                latency_ms=latency_ms,
                status="error",
                error=str(e),
                features_used=features_used,
            )
            
            raise
    
    return wrapper


def create_realtime_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create wrapper for AssemblyAI real-time transcription."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            track_assemblyai_call(
                method_name=method_name,
                model="realtime",
                audio_duration_seconds=None,  # Real-time doesn't have fixed duration
                latency_ms=latency_ms,
                status="ok",
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_assemblyai_call(
                method_name=method_name,
                model="realtime",
                audio_duration_seconds=None,
                latency_ms=latency_ms,
                status="error",
                error=str(e),
            )
            
            raise
    
    return wrapper


def instrument_assemblyai() -> bool:
    """Instrument AssemblyAI SDK."""
    try:
        import assemblyai
    except ImportError:
        logger.debug("[llmobserve] AssemblyAI SDK not installed - skipping")
        return False
    
    try:
        # Check if already instrumented
        if hasattr(assemblyai, "_llmobserve_instrumented"):
            logger.debug("[llmobserve] AssemblyAI already instrumented")
            return True
        
        # Patch Transcriber class
        if hasattr(assemblyai, 'Transcriber'):
            Transcriber = assemblyai.Transcriber
            
            # Patch transcribe method
            if hasattr(Transcriber, 'transcribe'):
                if not hasattr(Transcriber.transcribe, '_llmobserve_instrumented'):
                    original = Transcriber.transcribe
                    wrapped = create_transcribe_wrapper(original, "transcribe")
                    Transcriber.transcribe = wrapped
                    wrapped._llmobserve_instrumented = True
                    logger.debug("[llmobserve] Instrumented assemblyai.Transcriber.transcribe")
            
            # Patch submit method (for async batch jobs)
            if hasattr(Transcriber, 'submit'):
                if not hasattr(Transcriber.submit, '_llmobserve_instrumented'):
                    original = Transcriber.submit
                    wrapped = create_transcribe_wrapper(original, "submit")
                    Transcriber.submit = wrapped
                    wrapped._llmobserve_instrumented = True
                    logger.debug("[llmobserve] Instrumented assemblyai.Transcriber.submit")
        
        # Patch RealtimeTranscriber class
        if hasattr(assemblyai, 'RealtimeTranscriber'):
            RealtimeTranscriber = assemblyai.RealtimeTranscriber
            
            if hasattr(RealtimeTranscriber, 'connect'):
                if not hasattr(RealtimeTranscriber.connect, '_llmobserve_instrumented'):
                    original = RealtimeTranscriber.connect
                    wrapped = create_realtime_wrapper(original, "realtime.connect")
                    RealtimeTranscriber.connect = wrapped
                    wrapped._llmobserve_instrumented = True
                    logger.debug("[llmobserve] Instrumented assemblyai.RealtimeTranscriber.connect")
        
        assemblyai._llmobserve_instrumented = True
        logger.info("[llmobserve] Successfully instrumented AssemblyAI SDK")
        return True
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument AssemblyAI: {e}", exc_info=True)
        return False

