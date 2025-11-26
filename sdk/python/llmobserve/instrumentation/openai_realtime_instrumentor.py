"""
OpenAI Realtime API instrumentor for voice conversations.

Supports:
- openai.beta.realtime.connect() - WebSocket connection for real-time voice
- Session-level audio input/output tracking
- Token usage for text portions

OpenAI Realtime API pricing (as of 2024):
- Audio input: $0.06/min ($0.001/second)
- Audio output: $0.24/min ($0.004/second)
- Text input: $5/1M tokens (gpt-4o-realtime)
- Text output: $20/1M tokens (gpt-4o-realtime)
"""
import functools
import time
import uuid
import logging
from typing import Any, Callable, Optional, Dict
from contextlib import contextmanager

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config


# OpenAI Realtime pricing
OPENAI_REALTIME_PRICING = {
    "audio_input_per_second": 0.001,    # $0.06/min = $0.001/sec
    "audio_output_per_second": 0.004,   # $0.24/min = $0.004/sec
    "text_input_per_token": 0.000005,   # $5/1M tokens
    "text_output_per_token": 0.000020,  # $20/1M tokens
}


class RealtimeSessionTracker:
    """Track audio and token usage for a realtime session."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.start_time = time.time()
        self.audio_input_seconds = 0.0
        self.audio_output_seconds = 0.0
        self.text_input_tokens = 0
        self.text_output_tokens = 0
        self.events = []
    
    def add_audio_input(self, duration_seconds: float):
        self.audio_input_seconds += duration_seconds
    
    def add_audio_output(self, duration_seconds: float):
        self.audio_output_seconds += duration_seconds
    
    def add_text_input(self, tokens: int):
        self.text_input_tokens += tokens
    
    def add_text_output(self, tokens: int):
        self.text_output_tokens += tokens
    
    def calculate_cost(self) -> Dict[str, float]:
        """Calculate costs for this session."""
        audio_input_cost = self.audio_input_seconds * OPENAI_REALTIME_PRICING["audio_input_per_second"]
        audio_output_cost = self.audio_output_seconds * OPENAI_REALTIME_PRICING["audio_output_per_second"]
        text_input_cost = self.text_input_tokens * OPENAI_REALTIME_PRICING["text_input_per_token"]
        text_output_cost = self.text_output_tokens * OPENAI_REALTIME_PRICING["text_output_per_token"]
        
        return {
            "stt": audio_input_cost,
            "tts": audio_output_cost,
            "llm_input": text_input_cost,
            "llm_output": text_output_cost,
            "total": audio_input_cost + audio_output_cost + text_input_cost + text_output_cost,
        }
    
    def get_duration(self) -> float:
        return time.time() - self.start_time


# Global session tracker
_active_sessions: Dict[str, RealtimeSessionTracker] = {}


def track_realtime_session(
    session_id: str,
    method_name: str,
    latency_ms: float,
    status: str = "ok",
    error: Optional[str] = None,
    audio_input_seconds: float = 0.0,
    audio_output_seconds: float = 0.0,
    text_input_tokens: int = 0,
    text_output_tokens: int = 0,
    cost_breakdown: Optional[Dict] = None,
) -> None:
    """Track an OpenAI Realtime API session."""
    
    # Calculate costs
    if cost_breakdown is None:
        audio_input_cost = audio_input_seconds * OPENAI_REALTIME_PRICING["audio_input_per_second"]
        audio_output_cost = audio_output_seconds * OPENAI_REALTIME_PRICING["audio_output_per_second"]
        text_input_cost = text_input_tokens * OPENAI_REALTIME_PRICING["text_input_per_token"]
        text_output_cost = text_output_tokens * OPENAI_REALTIME_PRICING["text_output_per_token"]
        total_cost = audio_input_cost + audio_output_cost + text_input_cost + text_output_cost
        cost_breakdown = {
            "stt": audio_input_cost,
            "tts": audio_output_cost,
            "llm": text_input_cost + text_output_cost,
            "total": total_cost,
        }
    else:
        total_cost = cost_breakdown.get("total", 0.0)
    
    total_audio_duration = audio_input_seconds + audio_output_seconds
    
    main_span_id = str(uuid.uuid4())
    
    # Main session event
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": main_span_id,
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": "voice_agent_call",
        "provider": "openai",
        "endpoint": method_name,
        "model": "gpt-4o-realtime",
        "cost_usd": total_cost,
        "latency_ms": latency_ms,
        "input_tokens": text_input_tokens,
        "output_tokens": text_output_tokens,
        "status": status,
        "tenant_id": config.get_tenant_id(),
        "customer_id": context.get_customer_id(),
        "voice_call_id": session_id or context.get_voice_call_id(),
        "audio_duration_seconds": total_audio_duration,
        "voice_segment_type": "voice_agent",
        "event_metadata": {
            "error": error,
            "audio_input_seconds": audio_input_seconds,
            "audio_output_seconds": audio_output_seconds,
            "cost_breakdown": cost_breakdown,
        },
    }
    
    buffer.add_event(event)
    
    # Create sub-events for each segment
    if cost_breakdown:
        for segment_type, segment_cost in cost_breakdown.items():
            if segment_type == "total" or segment_cost is None or segment_cost == 0:
                continue
            
            segment_audio_duration = None
            if segment_type == "stt":
                segment_audio_duration = audio_input_seconds
            elif segment_type == "tts":
                segment_audio_duration = audio_output_seconds
            
            segment_event = {
                "id": str(uuid.uuid4()),
                "run_id": context.get_run_id(),
                "span_id": str(uuid.uuid4()),
                "parent_span_id": main_span_id,
                "section": context.get_current_section(),
                "section_path": f"{context.get_section_path()}/segment:{segment_type}",
                "span_type": f"{segment_type}_call",
                "provider": "openai",
                "endpoint": f"{method_name}.{segment_type}",
                "model": "gpt-4o-realtime",
                "cost_usd": segment_cost,
                "latency_ms": 0,
                "input_tokens": text_input_tokens if segment_type == "llm" else 0,
                "output_tokens": text_output_tokens if segment_type == "llm" else 0,
                "status": status,
                "tenant_id": config.get_tenant_id(),
                "customer_id": context.get_customer_id(),
                "voice_call_id": session_id,
                "audio_duration_seconds": segment_audio_duration,
                "voice_segment_type": segment_type,
                "event_metadata": None,
            }
            buffer.add_event(segment_event)


@contextmanager
def realtime_session():
    """
    Context manager to track an OpenAI Realtime session.
    
    Usage:
        from llmobserve.instrumentation.openai_realtime_instrumentor import realtime_session
        
        with realtime_session() as session:
            # Your realtime API calls
            async with client.beta.realtime.connect(model="gpt-4o-realtime") as conn:
                # Send audio, receive responses...
                pass
            
            # Manually track audio durations if needed
            session.add_audio_input(5.2)  # 5.2 seconds of audio input
            session.add_audio_output(3.8)  # 3.8 seconds of audio output
    """
    session_id = str(uuid.uuid4())
    tracker = RealtimeSessionTracker(session_id)
    _active_sessions[session_id] = tracker
    
    # Set voice call context
    original_voice_call_id = context.get_voice_call_id()
    context.set_voice_call_id(session_id)
    
    start_time = time.time()
    
    try:
        yield tracker
    finally:
        latency_ms = (time.time() - start_time) * 1000
        
        # Track the session
        costs = tracker.calculate_cost()
        
        track_realtime_session(
            session_id=session_id,
            method_name="realtime.session",
            latency_ms=latency_ms,
            audio_input_seconds=tracker.audio_input_seconds,
            audio_output_seconds=tracker.audio_output_seconds,
            text_input_tokens=tracker.text_input_tokens,
            text_output_tokens=tracker.text_output_tokens,
            cost_breakdown=costs,
        )
        
        # Cleanup
        del _active_sessions[session_id]
        context.set_voice_call_id(original_voice_call_id)


def create_realtime_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create wrapper for OpenAI Realtime connect method."""
    @functools.wraps(original_method)
    async def async_wrapper(*args, **kwargs):
        if not config.is_enabled():
            return await original_method(*args, **kwargs)
        
        session_id = str(uuid.uuid4())
        tracker = RealtimeSessionTracker(session_id)
        _active_sessions[session_id] = tracker
        
        # Set voice call context
        original_voice_call_id = context.get_voice_call_id()
        context.set_voice_call_id(session_id)
        
        start_time = time.time()
        
        try:
            result = await original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            # The connection itself doesn't have duration yet
            # Actual tracking happens when connection closes or via manual tracking
            
            return result
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_realtime_session(
                session_id=session_id,
                method_name=method_name,
                latency_ms=latency_ms,
                status="error",
                error=str(e),
            )
            
            # Cleanup
            if session_id in _active_sessions:
                del _active_sessions[session_id]
            context.set_voice_call_id(original_voice_call_id)
            
            raise
    
    @functools.wraps(original_method)
    def sync_wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        session_id = str(uuid.uuid4())
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            track_realtime_session(
                session_id=session_id,
                method_name=method_name,
                latency_ms=latency_ms,
                status="ok",
            )
            
            return result
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_realtime_session(
                session_id=session_id,
                method_name=method_name,
                latency_ms=latency_ms,
                status="error",
                error=str(e),
            )
            
            raise
    
    # Return async wrapper if original is async
    import asyncio
    if asyncio.iscoroutinefunction(original_method):
        return async_wrapper
    return sync_wrapper


def instrument_openai_realtime() -> bool:
    """Instrument OpenAI Realtime API."""
    try:
        import openai
    except ImportError:
        logger.debug("[llmobserve] OpenAI SDK not installed - skipping realtime")
        return False
    
    try:
        # Check if already instrumented
        if hasattr(openai, "_llmobserve_realtime_instrumented"):
            logger.debug("[llmobserve] OpenAI Realtime already instrumented")
            return True
        
        # Check if beta.realtime exists
        client_class = openai.OpenAI if hasattr(openai, 'OpenAI') else None
        async_client_class = openai.AsyncOpenAI if hasattr(openai, 'AsyncOpenAI') else None
        
        instrumented = False
        
        # Patch OpenAI client
        if client_class:
            original_init = client_class.__init__
            
            @functools.wraps(original_init)
            def patched_init(self, *args, **kwargs):
                original_init(self, *args, **kwargs)
                
                # Patch beta.realtime if it exists
                if hasattr(self, 'beta') and hasattr(self.beta, 'realtime'):
                    realtime = self.beta.realtime
                    
                    if hasattr(realtime, 'connect') and not hasattr(realtime.connect, '_llmobserve_instrumented'):
                        original = realtime.connect
                        wrapped = create_realtime_wrapper(original, "realtime.connect")
                        realtime.connect = wrapped
                        wrapped._llmobserve_instrumented = True
                        logger.debug("[llmobserve] Instrumented openai.beta.realtime.connect")
            
            client_class.__init__ = patched_init
            instrumented = True
        
        # Patch AsyncOpenAI client
        if async_client_class:
            original_async_init = async_client_class.__init__
            
            @functools.wraps(original_async_init)
            def patched_async_init(self, *args, **kwargs):
                original_async_init(self, *args, **kwargs)
                
                if hasattr(self, 'beta') and hasattr(self.beta, 'realtime'):
                    realtime = self.beta.realtime
                    
                    if hasattr(realtime, 'connect') and not hasattr(realtime.connect, '_llmobserve_instrumented'):
                        original = realtime.connect
                        wrapped = create_realtime_wrapper(original, "realtime.connect")
                        realtime.connect = wrapped
                        wrapped._llmobserve_instrumented = True
                        logger.debug("[llmobserve] Instrumented async openai.beta.realtime.connect")
            
            async_client_class.__init__ = patched_async_init
            instrumented = True
        
        if instrumented:
            openai._llmobserve_realtime_instrumented = True
            logger.info("[llmobserve] Successfully instrumented OpenAI Realtime API")
            return True
        else:
            logger.debug("[llmobserve] OpenAI Realtime API not found in SDK")
            return False
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument OpenAI Realtime: {e}", exc_info=True)
        return False


# Export for manual usage
__all__ = [
    "instrument_openai_realtime",
    "realtime_session",
    "RealtimeSessionTracker",
    "track_realtime_session",
]

