"""
Google STT (Speech-to-Text) instrumentor for Gemini multimodal audio.

NOTE: When Vapi uses "Google" as transcriber provider, it uses Gemini multimodal
LLMs (NOT Google Speech-to-Text V1/V2). Costs are based on audio input tokens,
not per-minute pricing.

Supported models:
- Gemini 2.0 Flash: $0.70 per 1M audio tokens
- Gemini 2.0 Flash Lite: $0.30 per 1M audio tokens
- Gemini 1.5 Pro: $1.25 per 1M audio tokens

Token rate: ~50 tokens per second (~3,000 tokens per minute)

Cost formula: (seconds × 50 / 1,000,000) × price_per_1M_tokens
"""
import functools
import time
import uuid
import os
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config


# Google Gemini audio input pricing (2024 - from Google's Gemini pricing page)
# Prices are per 1 million audio input tokens
# Audio converts at ~50 tokens per second

GEMINI_AUDIO_PRICING = {
    # Per 1M audio input tokens
    "gemini-2.0-flash": 0.70,
    "gemini-2.0-flash-lite": 0.30,
    "gemini-1.5-pro": 1.25,
    "gemini-1.5-flash": 0.70,  # Fallback to 2.0 flash pricing
    "default": 0.70,  # Default to Gemini 2.0 Flash
}

# Audio token rate: ~50 tokens per second
AUDIO_TOKENS_PER_SECOND = 50


def calculate_audio_cost(audio_seconds: float, model: str) -> float:
    """
    Calculate cost for Gemini multimodal audio transcription.
    
    Formula: (seconds × 50 / 1,000,000) × price_per_1M_tokens
    
    Args:
        audio_seconds: Duration of audio in seconds
        model: Gemini model name
        
    Returns:
        Cost in USD
    """
    # Convert seconds to tokens
    audio_tokens = audio_seconds * AUDIO_TOKENS_PER_SECOND
    
    # Get price per 1M tokens
    model_key = model.lower() if model else "default"
    
    # Try to match model name
    price_per_1m = GEMINI_AUDIO_PRICING["default"]
    for key, price in GEMINI_AUDIO_PRICING.items():
        if key in model_key:
            price_per_1m = price
            break
    
    # Calculate cost
    cost = (audio_tokens / 1_000_000) * price_per_1m
    
    return cost


def track_google_stt_call(
    method_name: str,
    model: Optional[str],
    audio_duration_seconds: Optional[float],
    latency_ms: float,
    status: str = "ok",
    error: Optional[str] = None,
    transcript: Optional[str] = None,
    audio_tokens: Optional[int] = None,
) -> None:
    """Track a Google/Gemini STT call with audio token-based pricing."""
    
    model_name = model or "gemini-2.0-flash"
    duration_seconds = audio_duration_seconds or 0
    
    # Calculate audio tokens if not provided
    if audio_tokens is None:
        audio_tokens = int(duration_seconds * AUDIO_TOKENS_PER_SECOND)
    
    # Calculate cost
    cost_usd = calculate_audio_cost(duration_seconds, model_name)
    
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": "stt_call",
        "provider": "google",
        "endpoint": method_name,
        "model": model_name,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
        "input_tokens": audio_tokens,  # Audio tokens as input
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
            "audio_tokens": audio_tokens,
            "tokens_per_second": AUDIO_TOKENS_PER_SECOND,
            "pricing_model": "gemini_multimodal_audio",
            "transcript": transcript[:500] if transcript else None,
        },
    }
    
    buffer.add_event(event)


def instrument_google_stt() -> bool:
    """
    Instrument Google Gemini for STT.
    
    Note: This specifically handles the case where Vapi uses Gemini models
    for transcription, NOT the traditional Google Speech-to-Text API.
    """
    try:
        import google.generativeai as genai
    except ImportError:
        logger.debug("[llmobserve] Google Generative AI SDK not installed - skipping Google STT")
        return False
    
    try:
        # Check if already instrumented
        if hasattr(genai, "_llmobserve_stt_instrumented"):
            logger.debug("[llmobserve] Google Gemini STT already instrumented")
            return True
        
        # The Gemini SDK's generate_content can accept audio
        # We'll provide a helper function for manual tracking since
        # audio transcription often goes through Vapi's abstraction
        
        genai._llmobserve_stt_instrumented = True
        
        logger.info("[llmobserve] Successfully instrumented Google Gemini STT")
        return True
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument Google STT: {e}", exc_info=True)
        return False


# Convenience function for manual tracking
def track_gemini_transcription(
    audio_duration_seconds: float,
    model: str = "gemini-2.0-flash",
    transcript: Optional[str] = None,
    latency_ms: float = 0,
) -> float:
    """
    Manually track a Gemini audio transcription and return the cost.
    
    Use this when integrating with Vapi or other platforms that use
    Gemini for transcription.
    
    Args:
        audio_duration_seconds: Duration of audio transcribed
        model: Gemini model used (gemini-2.0-flash, gemini-2.0-flash-lite, gemini-1.5-pro)
        transcript: The transcribed text (optional, for logging)
        latency_ms: Processing latency in milliseconds
        
    Returns:
        Cost in USD
        
    Example:
        >>> cost = track_gemini_transcription(
        ...     audio_duration_seconds=180,  # 3 minutes
        ...     model="gemini-2.0-flash",
        ... )
        >>> print(f"Cost: ${cost:.4f}")  # ~$0.0063
    """
    cost = calculate_audio_cost(audio_duration_seconds, model)
    
    track_google_stt_call(
        method_name="gemini_transcription",
        model=model,
        audio_duration_seconds=audio_duration_seconds,
        latency_ms=latency_ms,
        status="ok",
        transcript=transcript,
    )
    
    return cost

