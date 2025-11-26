"""
Azure Speech Services instrumentor with comprehensive pricing support.

Supports:
- Speech-to-Text (STT): Standard, Custom, Batch, Real-time
- Text-to-Speech (TTS): Neural, Custom Professional, Neural HD
- Speech Translation: Real-time, Live Interpreter, Video Translation
- Speaker Recognition: Verification, Identification
- Avatar: Interactive Avatar

Pricing tiers:
- Pay-as-you-go
- Commitment tiers (Standard & Containers)
"""
import functools
import time
import uuid
import os
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config


# Azure Speech pricing (2024 - verified from official pricing)
# All prices converted to per-minute or per-1K-chars as appropriate

AZURE_SPEECH_STT_PRICING = {
    # Pay-as-you-go (per minute)
    "standard_realtime": 0.0167,  # $1.00/hour
    "standard_batch": 0.003,  # $0.18/hour
    "custom_realtime": 0.02,  # $1.20/hour
    "custom_batch": 0.00375,  # $0.225/hour
    "conversation_multichannel": 0.035,  # $2.10/hour (preview)
    
    # Add-ons (per minute, added on top of base)
    "addon_langid": 0.005,  # $0.30/hour continuous language ID
    "addon_diarization": 0.005,  # $0.30/hour diarization
    "addon_pronunciation": 0.005,  # $0.30/hour pronunciation assessment
    
    # Commitment Tier 1: 2,000 hrs @ $1,600/mo
    "tier1_standard": 0.0133,  # $0.80/hr overage
    "tier1_custom": 0.016,  # $0.96/hr overage
    "tier1_addons": 0.004,  # $0.24/hr overage
    
    # Commitment Tier 2: 10,000 hrs @ $6,500/mo
    "tier2_standard": 0.0108,  # $0.65/hr overage
    "tier2_custom": 0.013,  # $0.78/hr overage
    "tier2_addons": 0.00333,  # $0.20/hr overage
    
    # Commitment Tier 3: 50,000 hrs @ $25,000/mo
    "tier3_standard": 0.00833,  # $0.50/hr overage
    "tier3_custom": 0.01,  # $0.60/hr overage
    "tier3_addons": 0.0025,  # $0.15/hr overage
    
    # Container pricing (per minute)
    "container_tier1_standard": 0.0127,  # $0.76/hr
    "container_tier2_standard": 0.0103,  # $0.62/hr
    "container_tier3_standard": 0.008,  # $0.48/hr
    "container_tier1_custom": 0.01515,  # $0.909/hr
    "container_tier2_custom": 0.0123,  # $0.738/hr
    "container_tier3_custom": 0.00942,  # $0.565/hr
    
    # Default
    "default": 0.0167,  # Standard real-time
}

AZURE_SPEECH_TTS_PRICING = {
    # Pay-as-you-go (per 1K characters)
    "neural": 0.015,  # $15 per 1M characters
    "custom_professional": 0.024,  # $24 per 1M characters
    "custom_neural_hd": 0.048,  # $48 per 1M characters
    
    # Commitment Tier 1: 80M chars @ $960/mo
    "tier1": 0.012,  # $12 per 1M overage
    
    # Commitment Tier 2: 400M chars @ $3,900/mo
    "tier2": 0.00975,  # $9.75 per 1M overage
    
    # Commitment Tier 3: 2,000M chars @ $15,000/mo
    "tier3": 0.0075,  # $7.50 per 1M overage
    
    # Container pricing
    "container_tier1": 0.0114,  # $11.40 per 1M
    "container_tier2": 0.009263,  # $9.263 per 1M
    "container_tier3": 0.007125,  # $7.125 per 1M
    
    # Voice model hosting
    "voice_training_per_hour": 52.0,  # $52 per compute hour
    "voice_hosting_per_hour": 4.04,  # $4.04 per model/hour
    
    # Default
    "default": 0.015,  # Neural
}

AZURE_TRANSLATION_PRICING = {
    # Real-time speech translation (per minute)
    "realtime": 0.0417,  # $2.50/hour
    
    # Live Interpreter
    "live_input_audio": 0.0167,  # $1/hour input audio
    "live_output_text_per_1k": 0.01,  # $10 per 1M characters output text
    "live_output_standard": 0.025,  # $1.50/hour output audio (standard voice)
    "live_output_custom": 0.0333,  # $2.00/hour output audio (custom voice)
    
    # Video Translation
    "video_input": 0.0833,  # $5/hour video input
    "video_output_standard": 0.25,  # $15/hour output standard voice
    "video_output_personal": 0.3333,  # $20/hour output personal voice
    
    "default": 0.0417,  # Real-time
}

AZURE_SPEAKER_RECOGNITION_PRICING = {
    # Per transaction
    "verification": 0.005,  # $5 per 1,000 transactions
    "identification": 0.01,  # $10 per 1,000 transactions
    
    # Storage
    "profile_storage_per_1k": 0.0002,  # $0.20 per 1,000 profiles/month
}

AZURE_AVATAR_PRICING = {
    # Per minute
    "interactive": 0.50,  # $0.50/min interactive avatar
}


def get_stt_pricing_tier() -> str:
    """Get the STT pricing tier from environment or default to pay-as-you-go."""
    return os.environ.get("AZURE_SPEECH_STT_TIER", "standard_realtime")


def get_tts_pricing_tier() -> str:
    """Get the TTS pricing tier from environment or default to pay-as-you-go."""
    return os.environ.get("AZURE_SPEECH_TTS_TIER", "neural")


def track_azure_stt_call(
    method_name: str,
    audio_duration_seconds: Optional[float],
    latency_ms: float,
    model: Optional[str] = None,
    is_batch: bool = False,
    is_custom: bool = False,
    addons: Optional[list] = None,
    status: str = "ok",
    error: Optional[str] = None,
    transcript: Optional[str] = None,
) -> None:
    """Track an Azure Speech-to-Text API call."""
    
    # Determine pricing tier
    tier = get_stt_pricing_tier()
    
    # Determine base rate
    if tier.startswith("tier") or tier.startswith("container"):
        base_rate = AZURE_SPEECH_STT_PRICING.get(tier, AZURE_SPEECH_STT_PRICING["default"])
    elif is_custom and is_batch:
        base_rate = AZURE_SPEECH_STT_PRICING["custom_batch"]
    elif is_custom:
        base_rate = AZURE_SPEECH_STT_PRICING["custom_realtime"]
    elif is_batch:
        base_rate = AZURE_SPEECH_STT_PRICING["standard_batch"]
    else:
        base_rate = AZURE_SPEECH_STT_PRICING["standard_realtime"]
    
    duration_minutes = (audio_duration_seconds or 0) / 60.0
    base_cost = duration_minutes * base_rate
    
    # Add addon costs
    addon_cost = 0.0
    if addons:
        for addon in addons:
            addon_key = f"addon_{addon}"
            if addon_key in AZURE_SPEECH_STT_PRICING:
                addon_cost += duration_minutes * AZURE_SPEECH_STT_PRICING[addon_key]
    
    cost_usd = base_cost + addon_cost
    
    model_name = model or ("custom" if is_custom else "standard")
    if is_batch:
        model_name += "_batch"
    
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": "stt_call",
        "provider": "azure_speech",
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
            "is_batch": is_batch,
            "is_custom": is_custom,
            "addons": addons,
            "pricing_tier": tier,
            "transcript": transcript[:500] if transcript else None,
        },
    }
    
    buffer.add_event(event)


def track_azure_tts_call(
    method_name: str,
    character_count: int,
    latency_ms: float,
    voice_name: Optional[str] = None,
    is_custom: bool = False,
    is_hd: bool = False,
    status: str = "ok",
    error: Optional[str] = None,
    audio_duration_seconds: Optional[float] = None,
) -> None:
    """Track an Azure Text-to-Speech API call."""
    
    # Determine pricing tier
    tier = get_tts_pricing_tier()
    
    # Determine rate
    if tier.startswith("tier") or tier.startswith("container"):
        rate_per_1k = AZURE_SPEECH_TTS_PRICING.get(tier, AZURE_SPEECH_TTS_PRICING["default"])
    elif is_custom and is_hd:
        rate_per_1k = AZURE_SPEECH_TTS_PRICING["custom_neural_hd"]
    elif is_custom:
        rate_per_1k = AZURE_SPEECH_TTS_PRICING["custom_professional"]
    else:
        rate_per_1k = AZURE_SPEECH_TTS_PRICING["neural"]
    
    cost_usd = (character_count / 1000.0) * rate_per_1k
    
    model_name = voice_name or "neural"
    if is_custom:
        model_name = f"custom_{model_name}"
    if is_hd:
        model_name += "_hd"
    
    # Estimate audio duration if not provided (avg ~15 chars/sec)
    if audio_duration_seconds is None:
        audio_duration_seconds = character_count / 15.0
    
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": "tts_call",
        "provider": "azure_speech",
        "endpoint": method_name,
        "model": model_name,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
        "input_tokens": character_count,
        "output_tokens": 0,
        "status": status,
        "tenant_id": config.get_tenant_id(),
        "customer_id": context.get_customer_id(),
        # Voice-specific fields
        "voice_call_id": context.get_voice_call_id(),
        "audio_duration_seconds": audio_duration_seconds,
        "voice_segment_type": "tts",
        "event_metadata": {
            "error": error,
            "character_count": character_count,
            "is_custom": is_custom,
            "is_hd": is_hd,
            "pricing_tier": tier,
        },
    }
    
    buffer.add_event(event)


def track_azure_translation_call(
    method_name: str,
    audio_duration_seconds: Optional[float],
    latency_ms: float,
    translation_type: str = "realtime",
    output_character_count: int = 0,
    status: str = "ok",
    error: Optional[str] = None,
) -> None:
    """Track an Azure Speech Translation API call."""
    
    duration_minutes = (audio_duration_seconds or 0) / 60.0
    
    # Calculate cost based on translation type
    if translation_type == "realtime":
        cost_usd = duration_minutes * AZURE_TRANSLATION_PRICING["realtime"]
    elif translation_type == "live_interpreter":
        # Input + output audio + output text
        input_cost = duration_minutes * AZURE_TRANSLATION_PRICING["live_input_audio"]
        output_audio_cost = duration_minutes * AZURE_TRANSLATION_PRICING["live_output_standard"]
        output_text_cost = (output_character_count / 1000.0) * AZURE_TRANSLATION_PRICING["live_output_text_per_1k"]
        cost_usd = input_cost + output_audio_cost + output_text_cost
    elif translation_type == "video":
        input_cost = duration_minutes * AZURE_TRANSLATION_PRICING["video_input"]
        output_cost = duration_minutes * AZURE_TRANSLATION_PRICING["video_output_standard"]
        cost_usd = input_cost + output_cost
    else:
        cost_usd = duration_minutes * AZURE_TRANSLATION_PRICING["default"]
    
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": "translation_call",
        "provider": "azure_speech",
        "endpoint": method_name,
        "model": translation_type,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
        "input_tokens": 0,
        "output_tokens": output_character_count,
        "status": status,
        "tenant_id": config.get_tenant_id(),
        "customer_id": context.get_customer_id(),
        # Voice-specific fields
        "voice_call_id": context.get_voice_call_id(),
        "audio_duration_seconds": audio_duration_seconds,
        "voice_segment_type": "translation",
        "event_metadata": {
            "error": error,
            "translation_type": translation_type,
        },
    }
    
    buffer.add_event(event)


def track_azure_speaker_recognition_call(
    method_name: str,
    operation: str,  # "verification" or "identification"
    transaction_count: int = 1,
    latency_ms: float = 0,
    status: str = "ok",
    error: Optional[str] = None,
) -> None:
    """Track an Azure Speaker Recognition API call."""
    
    rate = AZURE_SPEAKER_RECOGNITION_PRICING.get(operation, 0.005)
    cost_usd = transaction_count * rate
    
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": "speaker_recognition_call",
        "provider": "azure_speech",
        "endpoint": method_name,
        "model": operation,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
        "input_tokens": 0,
        "output_tokens": 0,
        "status": status,
        "tenant_id": config.get_tenant_id(),
        "customer_id": context.get_customer_id(),
        "voice_call_id": context.get_voice_call_id(),
        "voice_segment_type": "speaker_recognition",
        "event_metadata": {
            "error": error,
            "operation": operation,
            "transaction_count": transaction_count,
        },
    }
    
    buffer.add_event(event)


def track_azure_avatar_call(
    method_name: str,
    duration_minutes: float,
    latency_ms: float,
    avatar_type: str = "interactive",
    status: str = "ok",
    error: Optional[str] = None,
) -> None:
    """Track an Azure Avatar API call."""
    
    rate = AZURE_AVATAR_PRICING.get(avatar_type, AZURE_AVATAR_PRICING["interactive"])
    cost_usd = duration_minutes * rate
    
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": "avatar_call",
        "provider": "azure_speech",
        "endpoint": method_name,
        "model": avatar_type,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
        "input_tokens": 0,
        "output_tokens": 0,
        "status": status,
        "tenant_id": config.get_tenant_id(),
        "customer_id": context.get_customer_id(),
        "voice_call_id": context.get_voice_call_id(),
        "audio_duration_seconds": duration_minutes * 60,
        "voice_segment_type": "avatar",
        "event_metadata": {
            "error": error,
            "avatar_type": avatar_type,
        },
    }
    
    buffer.add_event(event)


def create_stt_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create wrapper for Azure Speech STT methods."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract audio duration and transcript from result
            audio_duration = None
            transcript = None
            
            if hasattr(result, 'duration'):
                # Duration is usually in ticks (100-nanosecond units)
                audio_duration = result.duration / 10_000_000.0
            
            if hasattr(result, 'text'):
                transcript = result.text
            
            track_azure_stt_call(
                method_name=method_name,
                audio_duration_seconds=audio_duration,
                latency_ms=latency_ms,
                status="ok",
                transcript=transcript,
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_azure_stt_call(
                method_name=method_name,
                audio_duration_seconds=None,
                latency_ms=latency_ms,
                status="error",
                error=str(e),
            )
            
            raise
    
    return wrapper


def create_tts_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create wrapper for Azure Speech TTS methods."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        # Extract text input
        text = kwargs.get("text") or ""
        if not text and args:
            # First arg might be text or SSML
            text = str(args[0]) if args[0] else ""
        
        character_count = len(text)
        voice_name = kwargs.get("voice") or kwargs.get("voice_name")
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract audio duration from result if available
            audio_duration = None
            if hasattr(result, 'audio_duration'):
                audio_duration = result.audio_duration / 10_000_000.0
            
            track_azure_tts_call(
                method_name=method_name,
                character_count=character_count,
                latency_ms=latency_ms,
                voice_name=voice_name,
                status="ok",
                audio_duration_seconds=audio_duration,
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_azure_tts_call(
                method_name=method_name,
                character_count=character_count,
                latency_ms=latency_ms,
                voice_name=voice_name,
                status="error",
                error=str(e),
            )
            
            raise
    
    return wrapper


def instrument_azure_speech() -> bool:
    """Instrument Azure Speech SDK."""
    try:
        import azure.cognitiveservices.speech as speechsdk
    except ImportError:
        logger.debug("[llmobserve] Azure Speech SDK not installed - skipping")
        return False
    
    try:
        # Check if already instrumented
        if hasattr(speechsdk, "_llmobserve_instrumented"):
            logger.debug("[llmobserve] Azure Speech SDK already instrumented")
            return True
        
        # Patch SpeechRecognizer
        if hasattr(speechsdk, 'SpeechRecognizer'):
            original_recognize_once = speechsdk.SpeechRecognizer.recognize_once
            if not hasattr(original_recognize_once, '_llmobserve_instrumented'):
                speechsdk.SpeechRecognizer.recognize_once = create_stt_wrapper(
                    original_recognize_once, "recognize_once"
                )
                speechsdk.SpeechRecognizer.recognize_once._llmobserve_instrumented = True
            
            original_recognize_once_async = speechsdk.SpeechRecognizer.recognize_once_async
            if not hasattr(original_recognize_once_async, '_llmobserve_instrumented'):
                speechsdk.SpeechRecognizer.recognize_once_async = create_stt_wrapper(
                    original_recognize_once_async, "recognize_once_async"
                )
                speechsdk.SpeechRecognizer.recognize_once_async._llmobserve_instrumented = True
        
        # Patch SpeechSynthesizer
        if hasattr(speechsdk, 'SpeechSynthesizer'):
            original_speak_text = speechsdk.SpeechSynthesizer.speak_text
            if not hasattr(original_speak_text, '_llmobserve_instrumented'):
                speechsdk.SpeechSynthesizer.speak_text = create_tts_wrapper(
                    original_speak_text, "speak_text"
                )
                speechsdk.SpeechSynthesizer.speak_text._llmobserve_instrumented = True
            
            original_speak_text_async = speechsdk.SpeechSynthesizer.speak_text_async
            if not hasattr(original_speak_text_async, '_llmobserve_instrumented'):
                speechsdk.SpeechSynthesizer.speak_text_async = create_tts_wrapper(
                    original_speak_text_async, "speak_text_async"
                )
                speechsdk.SpeechSynthesizer.speak_text_async._llmobserve_instrumented = True
            
            original_speak_ssml = speechsdk.SpeechSynthesizer.speak_ssml
            if not hasattr(original_speak_ssml, '_llmobserve_instrumented'):
                speechsdk.SpeechSynthesizer.speak_ssml = create_tts_wrapper(
                    original_speak_ssml, "speak_ssml"
                )
                speechsdk.SpeechSynthesizer.speak_ssml._llmobserve_instrumented = True
            
            original_speak_ssml_async = speechsdk.SpeechSynthesizer.speak_ssml_async
            if not hasattr(original_speak_ssml_async, '_llmobserve_instrumented'):
                speechsdk.SpeechSynthesizer.speak_ssml_async = create_tts_wrapper(
                    original_speak_ssml_async, "speak_ssml_async"
                )
                speechsdk.SpeechSynthesizer.speak_ssml_async._llmobserve_instrumented = True
        
        speechsdk._llmobserve_instrumented = True
        
        logger.info("[llmobserve] Successfully instrumented Azure Speech SDK")
        return True
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument Azure Speech: {e}", exc_info=True)
        return False

