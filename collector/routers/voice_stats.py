"""
Voice Stats router - provides aggregated statistics for voice AI agents.

Tracks STT + LLM + TTS + telephony costs with per-call breakdown,
cost/minute calculations, and provider comparisons.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func, and_, or_
from sqlalchemy import case, distinct
from models import TraceEvent
from db import get_session
from auth import get_current_user_id
from clerk_auth import get_current_clerk_user

router = APIRouter(prefix="/stats/voice", tags=["voice-stats"])

# Voice AI providers
VOICE_PROVIDERS = [
    "vapi", "retell", "bland", "livekit",  # Full platforms
    "deepgram", "assemblyai", "openai",  # STT
    "elevenlabs", "playht", "cartesia", "rime", "resemble",  # TTS
    "twilio",  # Telephony
]

# Voice segment types
VOICE_SEGMENT_TYPES = ["stt", "llm", "tts", "telephony", "call_summary"]

# Voice platforms for cross-platform tracking
VOICE_PLATFORMS = ["vapi", "retell", "bland", "livekit", "diy", "direct"]


@router.get("/calls")
async def get_voice_calls(
    hours: int = Query(24, description="Time window in hours"),
    limit: int = Query(50, description="Max number of calls to return"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)
) -> List[Dict[str, Any]]:
    """
    Get voice calls with per-call breakdown of STT + LLM + TTS costs.
    
    Groups events by voice_call_id to show the complete cost breakdown
    for each voice agent interaction.
    """
    user_id = current_user.id
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Get all voice calls with segment breakdown
    statement = select(
        TraceEvent.voice_call_id,
        TraceEvent.voice_segment_type,
        TraceEvent.customer_id,
        func.sum(TraceEvent.cost_usd).label("segment_cost"),
        func.sum(TraceEvent.audio_duration_seconds).label("audio_duration"),
        func.sum(TraceEvent.latency_ms).label("total_latency"),
        func.count(TraceEvent.id).label("event_count"),
        func.min(TraceEvent.created_at).label("started_at"),
        func.max(TraceEvent.created_at).label("ended_at"),
    ).where(
        and_(
            TraceEvent.created_at >= cutoff,
            TraceEvent.user_id == user_id,
            TraceEvent.user_id.isnot(None),
            TraceEvent.voice_call_id.isnot(None),
        )
    ).group_by(
        TraceEvent.voice_call_id,
        TraceEvent.voice_segment_type,
        TraceEvent.customer_id,
    ).order_by(func.min(TraceEvent.created_at).desc())
    
    results = session.exec(statement).all()
    
    # Group by voice_call_id
    calls = {}
    for r in results:
        call_id = r.voice_call_id
        if call_id not in calls:
            calls[call_id] = {
                "voice_call_id": call_id,
                "customer_id": r.customer_id,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "ended_at": r.ended_at.isoformat() if r.ended_at else None,
                "total_cost": 0.0,
                "total_duration_seconds": 0.0,
                "total_latency_ms": 0.0,
                "segments": {},
            }
        
        segment_type = r.voice_segment_type or "unknown"
        calls[call_id]["segments"][segment_type] = {
            "cost": round(r.segment_cost or 0.0, 6),
            "duration_seconds": round(r.audio_duration or 0.0, 2),
            "latency_ms": round(r.total_latency or 0.0, 2),
            "event_count": r.event_count,
        }
        calls[call_id]["total_cost"] += r.segment_cost or 0.0
        calls[call_id]["total_duration_seconds"] += r.audio_duration or 0.0
        calls[call_id]["total_latency_ms"] += r.total_latency or 0.0
    
    # Convert to list and calculate cost/minute
    call_list = []
    for call in calls.values():
        call["total_cost"] = round(call["total_cost"], 6)
        call["total_duration_seconds"] = round(call["total_duration_seconds"], 2)
        call["total_latency_ms"] = round(call["total_latency_ms"], 2)
        
        # Calculate cost per minute
        if call["total_duration_seconds"] > 0:
            call["cost_per_minute"] = round(
                (call["total_cost"] / call["total_duration_seconds"]) * 60, 4
            )
        else:
            call["cost_per_minute"] = 0.0
        
        call_list.append(call)
    
    # Sort by started_at desc and limit
    call_list.sort(key=lambda x: x.get("started_at") or "", reverse=True)
    return call_list[:limit]


@router.get("/by-platform")
async def get_voice_costs_by_platform(
    hours: int = Query(24, description="Time window in hours"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)
) -> Dict[str, Any]:
    """
    Get voice AI costs aggregated by platform (Vapi vs Retell vs DIY).
    
    Cross-platform tracking: See all your voice spend across different platforms
    in one unified view. Compare cost-per-minute between managed platforms and DIY.
    """
    user_id = current_user.id
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Get stats by platform
    statement = select(
        TraceEvent.voice_platform,
        func.sum(TraceEvent.cost_usd).label("total_cost"),
        func.sum(TraceEvent.audio_duration_seconds).label("total_duration"),
        func.count(distinct(TraceEvent.voice_call_id)).label("call_count"),
        func.count(TraceEvent.id).label("event_count"),
        func.avg(TraceEvent.latency_ms).label("avg_latency"),
    ).where(
        and_(
            TraceEvent.created_at >= cutoff,
            TraceEvent.user_id == user_id,
            TraceEvent.voice_platform.isnot(None),
        )
    ).group_by(TraceEvent.voice_platform).order_by(func.sum(TraceEvent.cost_usd).desc())
    
    results = session.exec(statement).all()
    
    total_cost = sum(r.total_cost or 0 for r in results)
    total_calls = sum(r.call_count or 0 for r in results)
    
    platforms = []
    for r in results:
        duration_minutes = (r.total_duration or 0) / 60.0
        cost_per_minute = (r.total_cost / duration_minutes) if duration_minutes > 0 else 0
        cost_per_call = (r.total_cost / r.call_count) if r.call_count > 0 else 0
        
        platforms.append({
            "platform": r.voice_platform or "unknown",
            "total_cost": round(r.total_cost or 0.0, 4),
            "total_duration_minutes": round(duration_minutes, 2),
            "call_count": r.call_count or 0,
            "event_count": r.event_count,
            "avg_latency_ms": round(r.avg_latency or 0.0, 2),
            "cost_per_minute": round(cost_per_minute, 4),
            "cost_per_call": round(cost_per_call, 4),
            "percentage": round((r.total_cost / total_cost * 100) if total_cost > 0 else 0, 1),
        })
    
    # Find cheapest platform
    cheapest = min(platforms, key=lambda x: x["cost_per_minute"]) if platforms else None
    most_expensive = max(platforms, key=lambda x: x["cost_per_minute"]) if platforms else None
    
    # Calculate potential savings
    potential_savings = 0.0
    if cheapest and most_expensive and cheapest != most_expensive:
        # If all calls were on cheapest platform
        total_minutes = sum(p["total_duration_minutes"] for p in platforms)
        current_total = sum(p["total_cost"] for p in platforms)
        if_all_cheapest = total_minutes * cheapest["cost_per_minute"]
        potential_savings = current_total - if_all_cheapest
    
    return {
        "time_window_hours": hours,
        "summary": {
            "total_cost": round(total_cost, 4),
            "total_calls": total_calls,
            "platform_count": len(platforms),
        },
        "platforms": platforms,
        "insights": {
            "cheapest_platform": cheapest["platform"] if cheapest else None,
            "cheapest_cost_per_minute": cheapest["cost_per_minute"] if cheapest else 0,
            "most_expensive_platform": most_expensive["platform"] if most_expensive else None,
            "most_expensive_cost_per_minute": most_expensive["cost_per_minute"] if most_expensive else 0,
            "potential_monthly_savings": round(potential_savings * 4.33, 2),  # Extrapolate to monthly
            "recommendation": f"Move calls from {most_expensive['platform']} to {cheapest['platform']} to save ${potential_savings:.2f}/week" if potential_savings > 0.1 else None,
        },
    }


@router.get("/by-provider")
async def get_voice_costs_by_provider(
    hours: int = Query(24, description="Time window in hours"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)
) -> List[Dict[str, Any]]:
    """
    Get voice AI costs aggregated by provider.
    
    Compare costs between Vapi, Retell, Bland, DIY (Deepgram + ElevenLabs), etc.
    """
    user_id = current_user.id
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    statement = select(
        TraceEvent.provider,
        func.sum(TraceEvent.cost_usd).label("total_cost"),
        func.sum(TraceEvent.audio_duration_seconds).label("total_duration"),
        func.count(distinct(TraceEvent.voice_call_id)).label("call_count"),
        func.count(TraceEvent.id).label("event_count"),
        func.avg(TraceEvent.latency_ms).label("avg_latency"),
    ).where(
        and_(
            TraceEvent.created_at >= cutoff,
            TraceEvent.user_id == user_id,
            TraceEvent.user_id.isnot(None),
            or_(
                TraceEvent.provider.in_(VOICE_PROVIDERS),
                TraceEvent.voice_segment_type.isnot(None),
            )
        )
    ).group_by(TraceEvent.provider).order_by(func.sum(TraceEvent.cost_usd).desc())
    
    results = session.exec(statement).all()
    
    total_cost = sum(r.total_cost or 0 for r in results)
    
    providers = []
    for r in results:
        duration_minutes = (r.total_duration or 0) / 60.0
        cost_per_minute = (r.total_cost / duration_minutes) if duration_minutes > 0 else 0
        
        providers.append({
            "provider": r.provider,
            "total_cost": round(r.total_cost or 0.0, 6),
            "total_duration_seconds": round(r.total_duration or 0.0, 2),
            "total_duration_minutes": round(duration_minutes, 2),
            "call_count": r.call_count or 0,
            "event_count": r.event_count,
            "avg_latency_ms": round(r.avg_latency or 0.0, 2),
            "cost_per_minute": round(cost_per_minute, 4),
            "percentage": round((r.total_cost / total_cost * 100) if total_cost > 0 else 0, 2),
        })
    
    return providers


@router.get("/by-segment")
async def get_voice_costs_by_segment(
    hours: int = Query(24, description="Time window in hours"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)
) -> List[Dict[str, Any]]:
    """
    Get voice AI costs aggregated by segment type (STT, LLM, TTS, telephony).
    
    Shows where the money goes in your voice pipeline.
    """
    user_id = current_user.id
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    statement = select(
        TraceEvent.voice_segment_type,
        func.sum(TraceEvent.cost_usd).label("total_cost"),
        func.sum(TraceEvent.audio_duration_seconds).label("total_duration"),
        func.count(TraceEvent.id).label("event_count"),
        func.avg(TraceEvent.latency_ms).label("avg_latency"),
    ).where(
        and_(
            TraceEvent.created_at >= cutoff,
            TraceEvent.user_id == user_id,
            TraceEvent.user_id.isnot(None),
            TraceEvent.voice_segment_type.isnot(None),
            TraceEvent.voice_segment_type != "call_summary",  # Exclude summaries
        )
    ).group_by(TraceEvent.voice_segment_type).order_by(func.sum(TraceEvent.cost_usd).desc())
    
    results = session.exec(statement).all()
    
    total_cost = sum(r.total_cost or 0 for r in results)
    
    segments = []
    for r in results:
        duration_minutes = (r.total_duration or 0) / 60.0
        cost_per_minute = (r.total_cost / duration_minutes) if duration_minutes > 0 else 0
        
        segments.append({
            "segment_type": r.voice_segment_type,
            "total_cost": round(r.total_cost or 0.0, 6),
            "total_duration_seconds": round(r.total_duration or 0.0, 2),
            "event_count": r.event_count,
            "avg_latency_ms": round(r.avg_latency or 0.0, 2),
            "cost_per_minute": round(cost_per_minute, 4),
            "percentage": round((r.total_cost / total_cost * 100) if total_cost > 0 else 0, 2),
        })
    
    return segments


@router.get("/cost-per-minute")
async def get_voice_cost_per_minute(
    hours: int = Query(24, description="Time window in hours"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)
) -> Dict[str, Any]:
    """
    Get true cost per minute for voice AI usage.
    
    Calculates the effective cost per minute across all voice operations.
    """
    user_id = current_user.id
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Get total costs and duration
    statement = select(
        func.sum(TraceEvent.cost_usd).label("total_cost"),
        func.sum(TraceEvent.audio_duration_seconds).label("total_duration"),
        func.count(distinct(TraceEvent.voice_call_id)).label("total_calls"),
        func.count(TraceEvent.id).label("total_events"),
    ).where(
        and_(
            TraceEvent.created_at >= cutoff,
            TraceEvent.user_id == user_id,
            TraceEvent.user_id.isnot(None),
            or_(
                TraceEvent.provider.in_(VOICE_PROVIDERS),
                TraceEvent.voice_segment_type.isnot(None),
            )
        )
    )
    
    result = session.exec(statement).first()
    
    total_cost = result.total_cost or 0.0
    total_duration_seconds = result.total_duration or 0.0
    total_duration_minutes = total_duration_seconds / 60.0
    total_calls = result.total_calls or 0
    total_events = result.total_events or 0
    
    cost_per_minute = (total_cost / total_duration_minutes) if total_duration_minutes > 0 else 0.0
    cost_per_call = (total_cost / total_calls) if total_calls > 0 else 0.0
    avg_call_duration = (total_duration_seconds / total_calls) if total_calls > 0 else 0.0
    
    return {
        "total_cost": round(total_cost, 6),
        "total_duration_seconds": round(total_duration_seconds, 2),
        "total_duration_minutes": round(total_duration_minutes, 2),
        "total_calls": total_calls,
        "total_events": total_events,
        "cost_per_minute": round(cost_per_minute, 4),
        "cost_per_call": round(cost_per_call, 4),
        "avg_call_duration_seconds": round(avg_call_duration, 2),
        "time_window_hours": hours,
    }


@router.get("/forecast")
async def get_voice_forecast(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)
) -> Dict[str, Any]:
    """
    Predict monthly bill based on current voice AI usage patterns.
    
    Uses last 7 days of data to project monthly costs.
    """
    user_id = current_user.id
    
    # Get last 7 days of data for projection
    week_cutoff = datetime.utcnow() - timedelta(days=7)
    
    statement = select(
        func.sum(TraceEvent.cost_usd).label("weekly_cost"),
        func.sum(TraceEvent.audio_duration_seconds).label("weekly_duration"),
        func.count(distinct(TraceEvent.voice_call_id)).label("weekly_calls"),
    ).where(
        and_(
            TraceEvent.created_at >= week_cutoff,
            TraceEvent.user_id == user_id,
            TraceEvent.user_id.isnot(None),
            or_(
                TraceEvent.provider.in_(VOICE_PROVIDERS),
                TraceEvent.voice_segment_type.isnot(None),
            )
        )
    )
    
    result = session.exec(statement).first()
    
    weekly_cost = result.weekly_cost or 0.0
    weekly_duration = result.weekly_duration or 0.0
    weekly_calls = result.weekly_calls or 0
    
    # Project to monthly (4.33 weeks per month)
    monthly_cost_projection = weekly_cost * 4.33
    monthly_duration_projection = weekly_duration * 4.33
    monthly_calls_projection = int(weekly_calls * 4.33)
    
    # Calculate daily averages
    daily_cost = weekly_cost / 7
    daily_calls = weekly_calls / 7
    daily_duration = weekly_duration / 7
    
    return {
        # Last 7 days actual
        "last_7_days": {
            "total_cost": round(weekly_cost, 4),
            "total_duration_minutes": round(weekly_duration / 60, 2),
            "total_calls": weekly_calls,
        },
        # Daily averages
        "daily_average": {
            "cost": round(daily_cost, 4),
            "duration_minutes": round(daily_duration / 60, 2),
            "calls": round(daily_calls, 1),
        },
        # Monthly projection
        "monthly_projection": {
            "cost": round(monthly_cost_projection, 2),
            "duration_minutes": round(monthly_duration_projection / 60, 1),
            "calls": monthly_calls_projection,
        },
        # Confidence note
        "note": "Projection based on last 7 days of usage. Actual costs may vary.",
    }


@router.get("/by-customer")
async def get_voice_costs_by_customer(
    hours: int = Query(720, description="Time window in hours (default 30 days)"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)
) -> List[Dict[str, Any]]:
    """
    Get voice AI costs aggregated by customer.
    
    Track which customers are driving voice agent costs.
    """
    user_id = current_user.id
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    statement = select(
        TraceEvent.customer_id,
        func.sum(TraceEvent.cost_usd).label("total_cost"),
        func.sum(TraceEvent.audio_duration_seconds).label("total_duration"),
        func.count(distinct(TraceEvent.voice_call_id)).label("call_count"),
        func.avg(TraceEvent.latency_ms).label("avg_latency"),
    ).where(
        and_(
            TraceEvent.created_at >= cutoff,
            TraceEvent.user_id == user_id,
            TraceEvent.user_id.isnot(None),
            TraceEvent.customer_id.isnot(None),
            or_(
                TraceEvent.provider.in_(VOICE_PROVIDERS),
                TraceEvent.voice_segment_type.isnot(None),
            )
        )
    ).group_by(TraceEvent.customer_id).order_by(func.sum(TraceEvent.cost_usd).desc())
    
    results = session.exec(statement).all()
    
    customers = []
    for r in results:
        duration_minutes = (r.total_duration or 0) / 60.0
        cost_per_minute = (r.total_cost / duration_minutes) if duration_minutes > 0 else 0
        
        customers.append({
            "customer_id": r.customer_id,
            "total_cost": round(r.total_cost or 0.0, 6),
            "total_duration_minutes": round(duration_minutes, 2),
            "call_count": r.call_count or 0,
            "avg_latency_ms": round(r.avg_latency or 0.0, 2),
            "cost_per_minute": round(cost_per_minute, 4),
        })
    
    return customers


# Alternative provider pricing (per unit costs)
# These are used for "What If" calculations
ALTERNATIVE_PRICING = {
    # STT providers (per minute)
    "stt": {
        "deepgram_nova3": {"name": "Deepgram Nova-3", "per_minute": 0.0059},
        "deepgram_nova2": {"name": "Deepgram Nova-2", "per_minute": 0.0043},
        "assemblyai": {"name": "AssemblyAI", "per_minute": 0.0037},
        "openai_whisper": {"name": "OpenAI Whisper", "per_minute": 0.006},
        "google_gemini": {"name": "Google Gemini", "per_minute": 0.002},  # ~$0.70/1M tokens, ~3000 tokens/min
        "azure_stt": {"name": "Azure Speech", "per_minute": 0.0167},  # $1/hour
    },
    # LLM providers (per 1M tokens - we'll convert)
    "llm": {
        "gpt4o": {"name": "GPT-4o", "per_1m_input": 2.50, "per_1m_output": 10.00},
        "gpt4o_mini": {"name": "GPT-4o-mini", "per_1m_input": 0.15, "per_1m_output": 0.60},
        "claude_sonnet": {"name": "Claude 3.5 Sonnet", "per_1m_input": 3.00, "per_1m_output": 15.00},
        "claude_haiku": {"name": "Claude 3.5 Haiku", "per_1m_input": 0.80, "per_1m_output": 4.00},
        "gemini_flash": {"name": "Gemini 2.0 Flash", "per_1m_input": 0.10, "per_1m_output": 0.40},
        "groq_llama": {"name": "Groq Llama 3.3 70B", "per_1m_input": 0.59, "per_1m_output": 0.79},
    },
    # TTS providers (per 1K characters)
    "tts": {
        "elevenlabs": {"name": "ElevenLabs", "per_1k_chars": 0.30},
        "cartesia": {"name": "Cartesia Sonic", "per_1k_chars": 0.04},
        "playht": {"name": "PlayHT", "per_1k_chars": 0.05},
        "deepgram_aura": {"name": "Deepgram Aura", "per_1k_chars": 0.015},
        "openai_tts": {"name": "OpenAI TTS", "per_1k_chars": 0.015},
        "azure_tts": {"name": "Azure Neural TTS", "per_1k_chars": 0.015},
    },
}


@router.get("/alternative-costs")
async def get_alternative_costs(
    hours: int = Query(24, description="Time window in hours"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)
) -> Dict[str, Any]:
    """
    Calculate what your voice AI usage would cost with alternative providers.
    
    Uses actual usage metrics (tokens, characters, duration) to compute accurate
    alternative costs - not just per-minute estimates.
    """
    user_id = current_user.id
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Get aggregated usage by segment type
    statement = select(
        TraceEvent.voice_segment_type,
        func.sum(TraceEvent.input_tokens).label("total_input_tokens"),
        func.sum(TraceEvent.output_tokens).label("total_output_tokens"),
        func.sum(TraceEvent.audio_duration_seconds).label("total_duration"),
        func.sum(TraceEvent.cost_usd).label("actual_cost"),
        func.count(TraceEvent.id).label("event_count"),
    ).where(
        and_(
            TraceEvent.created_at >= cutoff,
            TraceEvent.user_id == user_id,
            TraceEvent.voice_segment_type.isnot(None),
        )
    ).group_by(TraceEvent.voice_segment_type)
    
    results = session.exec(statement).all()
    
    # Build usage summary
    usage = {
        "stt": {"duration_minutes": 0, "actual_cost": 0},
        "llm": {"input_tokens": 0, "output_tokens": 0, "actual_cost": 0},
        "tts": {"characters": 0, "actual_cost": 0},
    }
    
    for r in results:
        seg_type = r.voice_segment_type
        if seg_type == "stt":
            usage["stt"]["duration_minutes"] = (r.total_duration or 0) / 60.0
            usage["stt"]["actual_cost"] = r.actual_cost or 0
        elif seg_type == "llm":
            usage["llm"]["input_tokens"] = r.total_input_tokens or 0
            usage["llm"]["output_tokens"] = r.total_output_tokens or 0
            usage["llm"]["actual_cost"] = r.actual_cost or 0
        elif seg_type == "tts":
            # TTS characters are stored in input_tokens field
            usage["tts"]["characters"] = r.total_input_tokens or 0
            usage["tts"]["actual_cost"] = r.actual_cost or 0
    
    # Calculate alternative costs for each segment
    alternatives = {
        "stt": [],
        "llm": [],
        "tts": [],
    }
    
    # STT alternatives (per minute pricing)
    stt_minutes = usage["stt"]["duration_minutes"]
    stt_actual = usage["stt"]["actual_cost"]
    for key, provider in ALTERNATIVE_PRICING["stt"].items():
        alt_cost = stt_minutes * provider["per_minute"]
        savings = stt_actual - alt_cost
        alternatives["stt"].append({
            "provider": key,
            "name": provider["name"],
            "projected_cost": round(alt_cost, 4),
            "savings": round(savings, 4),
            "savings_percent": round((savings / stt_actual * 100) if stt_actual > 0 else 0, 1),
        })
    alternatives["stt"].sort(key=lambda x: x["projected_cost"])
    
    # LLM alternatives (per token pricing)
    llm_input = usage["llm"]["input_tokens"]
    llm_output = usage["llm"]["output_tokens"]
    llm_actual = usage["llm"]["actual_cost"]
    for key, provider in ALTERNATIVE_PRICING["llm"].items():
        input_cost = (llm_input / 1_000_000) * provider["per_1m_input"]
        output_cost = (llm_output / 1_000_000) * provider["per_1m_output"]
        alt_cost = input_cost + output_cost
        savings = llm_actual - alt_cost
        alternatives["llm"].append({
            "provider": key,
            "name": provider["name"],
            "projected_cost": round(alt_cost, 4),
            "savings": round(savings, 4),
            "savings_percent": round((savings / llm_actual * 100) if llm_actual > 0 else 0, 1),
        })
    alternatives["llm"].sort(key=lambda x: x["projected_cost"])
    
    # TTS alternatives (per character pricing)
    tts_chars = usage["tts"]["characters"]
    tts_actual = usage["tts"]["actual_cost"]
    for key, provider in ALTERNATIVE_PRICING["tts"].items():
        alt_cost = (tts_chars / 1000) * provider["per_1k_chars"]
        savings = tts_actual - alt_cost
        alternatives["tts"].append({
            "provider": key,
            "name": provider["name"],
            "projected_cost": round(alt_cost, 4),
            "savings": round(savings, 4),
            "savings_percent": round((savings / tts_actual * 100) if tts_actual > 0 else 0, 1),
        })
    alternatives["tts"].sort(key=lambda x: x["projected_cost"])
    
    # Calculate best DIY stack
    best_stt = alternatives["stt"][0] if alternatives["stt"] else None
    best_llm = alternatives["llm"][0] if alternatives["llm"] else None
    best_tts = alternatives["tts"][0] if alternatives["tts"] else None
    
    total_actual = stt_actual + llm_actual + tts_actual
    total_best_diy = (
        (best_stt["projected_cost"] if best_stt else 0) +
        (best_llm["projected_cost"] if best_llm else 0) +
        (best_tts["projected_cost"] if best_tts else 0)
    )
    
    return {
        "time_window_hours": hours,
        "usage": {
            "stt_minutes": round(stt_minutes, 2),
            "llm_input_tokens": llm_input,
            "llm_output_tokens": llm_output,
            "tts_characters": tts_chars,
        },
        "actual_costs": {
            "stt": round(stt_actual, 4),
            "llm": round(llm_actual, 4),
            "tts": round(tts_actual, 4),
            "total": round(total_actual, 4),
        },
        "alternatives": alternatives,
        "best_diy_stack": {
            "stt": best_stt["name"] if best_stt else None,
            "llm": best_llm["name"] if best_llm else None,
            "tts": best_tts["name"] if best_tts else None,
            "total_cost": round(total_best_diy, 4),
            "total_savings": round(total_actual - total_best_diy, 4),
            "savings_percent": round(((total_actual - total_best_diy) / total_actual * 100) if total_actual > 0 else 0, 1),
        },
    }

