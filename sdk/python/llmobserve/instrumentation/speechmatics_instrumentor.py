"""
Speechmatics STT/TTS instrumentor with comprehensive pricing support.

Supports:
- Real-time STT (Standard/Enhanced)
- Batch STT (Standard/Enhanced)
- TTS
- Bolt-on features (Translation, Summaries, Chapters, Sentiment, Topics)

Pricing tiers:
- Standard: Cheaper, lower accuracy
- Enhanced: More accurate, more expensive

Free monthly allowance:
- Realtime STT: 240 min/month
- Batch STT: 240 min/month
- TTS: 1,000,000 chars (~20 hours)

Model Training Discount:
- 33% off all STT when enabled in Speechmatics dashboard
- Set SPEECHMATICS_MODEL_TRAINING=true to apply discount
"""
import functools
import time
import uuid
import os
import logging
from typing import Any, Callable, Optional, List

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config


# Speechmatics STT pricing (2024 - verified from official pricing)
SPEECHMATICS_STT_PRICING = {
    # Real-time (used by Vapi, LiveKit, Retell, etc.)
    "realtime": {
        "standard": 0.0053,  # $0.318/hr
        "enhanced": 0.0093,  # $0.558/hr
    },
    # Batch (pre-recorded)
    "batch": {
        "standard": 0.0040,  # $0.24/hr
        "enhanced": 0.0067,  # $0.402/hr
    },
}

# With 33% model training discount
SPEECHMATICS_STT_PRICING_DISCOUNT = {
    "realtime": {
        "standard": 0.00355,
        "enhanced": 0.00623,
    },
    "batch": {
        "standard": 0.00268,
        "enhanced": 0.00449,
    },
}

# Bolt-on features (per minute, added on top of base STT)
SPEECHMATICS_ADDON_PRICING = {
    "translation": 0.0108,
    "summaries": 0.0020,
    "chapters": 0.0067,
    "sentiment": 0.0020,
    "topics": 0.0033,
}

# TTS pricing
SPEECHMATICS_TTS_PRICING = 0.011  # per 1K chars


def has_model_training_discount() -> bool:
    """Check if model training discount is enabled."""
    return os.environ.get("SPEECHMATICS_MODEL_TRAINING", "").lower() in ("true", "1", "yes")


def get_operating_point() -> str:
    """Get the operating point (standard/enhanced) from environment."""
    return os.environ.get("SPEECHMATICS_OPERATING_POINT", "standard").lower()


def track_speechmatics_stt_call(
    method_name: str,
    audio_duration_seconds: Optional[float],
    latency_ms: float,
    is_realtime: bool = True,
    operating_point: Optional[str] = None,
    addons: Optional[List[str]] = None,
    status: str = "ok",
    error: Optional[str] = None,
    transcript: Optional[str] = None,
    language: Optional[str] = None,
) -> None:
    """Track a Speechmatics STT call."""
    
    # Determine pricing
    has_discount = has_model_training_discount()
    pricing = SPEECHMATICS_STT_PRICING_DISCOUNT if has_discount else SPEECHMATICS_STT_PRICING
    
    mode = "realtime" if is_realtime else "batch"
    op_point = (operating_point or get_operating_point()).lower()
    if op_point not in ("standard", "enhanced"):
        op_point = "standard"
    
    rate_per_minute = pricing[mode][op_point]
    duration_minutes = (audio_duration_seconds or 0) / 60.0
    base_cost = duration_minutes * rate_per_minute
    
    # Add addon costs
    addon_cost = 0.0
    if addons:
        for addon in addons:
            addon_key = addon.lower()
            if addon_key in SPEECHMATICS_ADDON_PRICING:
                addon_cost += duration_minutes * SPEECHMATICS_ADDON_PRICING[addon_key]
    
    cost_usd = base_cost + addon_cost
    
    model_name = f"{mode}_{op_point}"
    if has_discount:
        model_name += "_discount"
    
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": "stt_call",
        "provider": "speechmatics",
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
            "mode": mode,
            "operating_point": op_point,
            "has_discount": has_discount,
            "addons": addons,
            "language": language,
            "transcript": transcript[:500] if transcript else None,
        },
    }
    
    buffer.add_event(event)


def track_speechmatics_tts_call(
    method_name: str,
    character_count: int,
    latency_ms: float,
    voice: Optional[str] = None,
    status: str = "ok",
    error: Optional[str] = None,
    audio_duration_seconds: Optional[float] = None,
) -> None:
    """Track a Speechmatics TTS call."""
    
    cost_usd = (character_count / 1000.0) * SPEECHMATICS_TTS_PRICING
    
    # Estimate audio duration if not provided (~15 chars/sec)
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
        "provider": "speechmatics",
        "endpoint": method_name,
        "model": voice or "default",
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
            "voice": voice,
        },
    }
    
    buffer.add_event(event)


def instrument_speechmatics() -> bool:
    """Instrument Speechmatics SDK."""
    try:
        import speechmatics
    except ImportError:
        logger.debug("[llmobserve] Speechmatics SDK not installed - skipping")
        return False
    
    try:
        # Check if already instrumented
        if hasattr(speechmatics, "_llmobserve_instrumented"):
            logger.debug("[llmobserve] Speechmatics already instrumented")
            return True
        
        # Speechmatics uses WebSocket-based API for realtime
        # We provide helper functions for manual tracking
        
        speechmatics._llmobserve_instrumented = True
        
        logger.info("[llmobserve] Successfully instrumented Speechmatics SDK")
        return True
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument Speechmatics: {e}", exc_info=True)
        return False


# Convenience functions for manual tracking
def calculate_stt_cost(
    audio_duration_seconds: float,
    is_realtime: bool = True,
    operating_point: str = "standard",
    addons: Optional[List[str]] = None,
    has_discount: bool = False,
) -> float:
    """
    Calculate Speechmatics STT cost.
    
    Args:
        audio_duration_seconds: Duration of audio
        is_realtime: True for realtime, False for batch
        operating_point: "standard" or "enhanced"
        addons: List of addons (translation, summaries, chapters, sentiment, topics)
        has_discount: Whether 33% model training discount applies
        
    Returns:
        Cost in USD
    """
    pricing = SPEECHMATICS_STT_PRICING_DISCOUNT if has_discount else SPEECHMATICS_STT_PRICING
    mode = "realtime" if is_realtime else "batch"
    op_point = operating_point.lower()
    if op_point not in ("standard", "enhanced"):
        op_point = "standard"
    
    rate_per_minute = pricing[mode][op_point]
    duration_minutes = audio_duration_seconds / 60.0
    base_cost = duration_minutes * rate_per_minute
    
    addon_cost = 0.0
    if addons:
        for addon in addons:
            addon_key = addon.lower()
            if addon_key in SPEECHMATICS_ADDON_PRICING:
                addon_cost += duration_minutes * SPEECHMATICS_ADDON_PRICING[addon_key]
    
    return base_cost + addon_cost


def calculate_tts_cost(character_count: int) -> float:
    """
    Calculate Speechmatics TTS cost.
    
    Args:
        character_count: Number of characters
        
    Returns:
        Cost in USD
    """
    return (character_count / 1000.0) * SPEECHMATICS_TTS_PRICING

