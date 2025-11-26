"""
Twilio SMS/Voice instrumentor with full call duration tracking.

Tracks costs for:
- SMS messages ($0.0079 per message - US)
- Voice calls ($0.014 per minute - US outbound)
- Call duration tracking via calls().fetch() and status callbacks

For DIY voice stacks, use the TwilioCallTracker context manager to
automatically track call duration when the call ends.
"""
import functools
import time
import uuid
import logging
import threading
from typing import Any, Callable, Optional, Dict
from contextlib import contextmanager

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config

# Track active calls for duration tracking
_active_calls: Dict[str, Dict[str, Any]] = {}
_calls_lock = threading.Lock()

# Pricing constants
TWILIO_SMS_COST = 0.0079  # per message (US)
TWILIO_VOICE_PER_MINUTE = 0.014  # per minute outbound (US)
TWILIO_VOICE_INBOUND_PER_MINUTE = 0.0085  # per minute inbound


def track_twilio_event(
    method_name: str,
    cost_usd: float,
    latency_ms: float,
    duration_seconds: Optional[float] = None,
    call_sid: Optional[str] = None,
    direction: Optional[str] = None,
    status: str = "ok",
    error: Optional[str] = None,
    voice_call_id: Optional[str] = None,
) -> None:
    """Track a Twilio API call with voice-specific fields."""
    
    # Determine span type based on method
    if "messages" in method_name:
        span_type = "sms_call"
    elif "calls" in method_name:
        span_type = "telephony_call"
    else:
        span_type = "communication_call"
    
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": span_type,
        "provider": "twilio",
        "endpoint": method_name,
        "model": None,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
        "input_tokens": 0,
        "output_tokens": 0,
        "status": status,
        "tenant_id": config.get_tenant_id(),
        "customer_id": context.get_customer_id(),
        "voice_call_id": voice_call_id or context.get_voice_call_id(),
        "audio_duration_seconds": duration_seconds,
        "voice_segment_type": "telephony" if "calls" in method_name else None,
        "event_metadata": {
            "call_sid": call_sid,
            "direction": direction,
            "duration_seconds": duration_seconds,
            "error": error,
        } if any([call_sid, direction, duration_seconds, error]) else None,
    }
    
    buffer.add_event(event)


def calculate_call_cost(duration_seconds: float, direction: str = "outbound") -> float:
    """Calculate call cost based on duration and direction."""
    minutes = duration_seconds / 60.0
    if direction == "inbound":
        return minutes * TWILIO_VOICE_INBOUND_PER_MINUTE
    return minutes * TWILIO_VOICE_PER_MINUTE


class TwilioCallTracker:
    """
    Context manager for tracking Twilio voice call duration.
    
    Usage:
        with TwilioCallTracker(call_sid="CA...") as tracker:
            # Your voice call logic here
            # When context exits, it will fetch call status and log duration
    
    Or manually:
        tracker = TwilioCallTracker(call_sid="CA...")
        tracker.start()
        # ... call logic ...
        tracker.end()  # Fetches final duration and logs cost
    """
    
    def __init__(
        self, 
        call_sid: str,
        twilio_client: Any = None,
        voice_call_id: Optional[str] = None,
        direction: str = "outbound",
    ):
        self.call_sid = call_sid
        self.twilio_client = twilio_client
        self.voice_call_id = voice_call_id or context.get_voice_call_id()
        self.direction = direction
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration_seconds: Optional[float] = None
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()
        return False
    
    def start(self):
        """Mark call start time."""
        self.start_time = time.time()
        with _calls_lock:
            _active_calls[self.call_sid] = {
                "start_time": self.start_time,
                "voice_call_id": self.voice_call_id,
                "direction": self.direction,
            }
    
    def end(self, fetch_from_api: bool = True):
        """
        Mark call end and log the final cost.
        
        Args:
            fetch_from_api: If True and twilio_client is set, fetch actual duration from API
        """
        self.end_time = time.time()
        
        # Try to get actual duration from Twilio API
        if fetch_from_api and self.twilio_client and self.call_sid:
            try:
                call = self.twilio_client.calls(self.call_sid).fetch()
                if call.duration:
                    self.duration_seconds = float(call.duration)
                elif call.status in ["completed", "busy", "failed", "no-answer", "canceled"]:
                    # Call ended but no duration - use our tracked time
                    self.duration_seconds = self.end_time - self.start_time if self.start_time else 0
            except Exception as e:
                logger.warning(f"[llmobserve] Failed to fetch Twilio call duration: {e}")
                self.duration_seconds = self.end_time - self.start_time if self.start_time else 0
        else:
            self.duration_seconds = self.end_time - self.start_time if self.start_time else 0
        
        # Calculate and log cost
        cost = calculate_call_cost(self.duration_seconds, self.direction)
        
        track_twilio_event(
            method_name="calls.duration",
            cost_usd=cost,
            latency_ms=0,
            duration_seconds=self.duration_seconds,
            call_sid=self.call_sid,
            direction=self.direction,
            voice_call_id=self.voice_call_id,
        )
        
        # Clean up
        with _calls_lock:
            _active_calls.pop(self.call_sid, None)
        
        return self.duration_seconds, cost


def track_call_end(call_sid: str, duration_seconds: float, direction: str = "outbound"):
    """
    Manually track a call's end with known duration.
    
    Useful when you receive a webhook with call duration.
    
    Args:
        call_sid: The Twilio Call SID
        duration_seconds: Actual call duration in seconds
        direction: "outbound" or "inbound"
    """
    voice_call_id = None
    with _calls_lock:
        if call_sid in _active_calls:
            voice_call_id = _active_calls[call_sid].get("voice_call_id")
            _active_calls.pop(call_sid, None)
    
    cost = calculate_call_cost(duration_seconds, direction)
    
    track_twilio_event(
        method_name="calls.completed",
        cost_usd=cost,
        latency_ms=0,
        duration_seconds=duration_seconds,
        call_sid=call_sid,
        direction=direction,
        voice_call_id=voice_call_id,
    )
    
    return cost


def create_calls_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create wrapper for calls.create that tracks call initiation."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract call info
            call_sid = getattr(result, "sid", None)
            direction = getattr(result, "direction", "outbound-api")
            
            # Register this call for duration tracking
            if call_sid:
                with _calls_lock:
                    _active_calls[call_sid] = {
                        "start_time": time.time(),
                        "voice_call_id": context.get_voice_call_id(),
                        "direction": direction,
                    }
            
            # Log call initiation (cost will come later with duration)
            track_twilio_event(
                method_name=method_name,
                cost_usd=0,  # Cost calculated when call ends
                latency_ms=latency_ms,
                call_sid=call_sid,
                direction=direction,
                status="initiated",
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_twilio_event(
                method_name=method_name,
                cost_usd=0,
                latency_ms=latency_ms,
                status="error",
                error=str(e),
            )
            
            raise
    
    return wrapper


def create_fetch_wrapper(original_method: Callable) -> Callable:
    """Create wrapper for calls().fetch() to track call duration when fetched."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        result = original_method(*args, **kwargs)
        
        # If call is completed and has duration, log it
        call_sid = getattr(result, "sid", None)
        duration = getattr(result, "duration", None)
        status = getattr(result, "status", None)
        direction = getattr(result, "direction", "outbound-api")
        
        if call_sid and duration and status == "completed":
            # Check if we haven't already logged this
            with _calls_lock:
                if call_sid in _active_calls:
                    voice_call_id = _active_calls[call_sid].get("voice_call_id")
                    _active_calls.pop(call_sid, None)
                    
                    cost = calculate_call_cost(float(duration), direction)
                    
                    track_twilio_event(
                        method_name="calls.fetch",
                        cost_usd=cost,
                        latency_ms=0,
                        duration_seconds=float(duration),
                        call_sid=call_sid,
                        direction=direction,
                        voice_call_id=voice_call_id,
                    )
        
        return result
    
    return wrapper


def create_messages_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create wrapper for messages.create."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            # Get actual price if available
            cost = TWILIO_SMS_COST
            if hasattr(result, "price") and result.price:
                cost = abs(float(result.price))
            
            track_twilio_event(
                method_name=method_name,
                cost_usd=cost,
                latency_ms=latency_ms,
                status="ok",
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_twilio_event(
                method_name=method_name,
                cost_usd=TWILIO_SMS_COST,
                latency_ms=latency_ms,
                status="error",
                error=str(e),
            )
            
            raise
    
    return wrapper


def instrument_twilio() -> bool:
    """Instrument Twilio SDK for SMS and Voice tracking."""
    try:
        from twilio.rest import Client
    except ImportError:
        logger.debug("[llmobserve] Twilio SDK not installed - skipping")
        return False
    
    try:
        original_init = Client.__init__
        
        if hasattr(original_init, "_llmobserve_instrumented"):
                logger.debug("[llmobserve] Twilio already instrumented")
                return True
            
        @functools.wraps(original_init)
        def patched_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            
            # Patch messages.create
            if hasattr(self, "messages") and hasattr(self.messages, "create"):
                original_messages_create = self.messages.create
                if not hasattr(original_messages_create, "_llmobserve_instrumented"):
                    self.messages.create = create_messages_wrapper(original_messages_create, "messages.create")
                    self.messages.create._llmobserve_instrumented = True
                    self.messages.create._llmobserve_original = original_messages_create
        
            # Patch calls.create
            if hasattr(self, "calls") and hasattr(self.calls, "create"):
                original_calls_create = self.calls.create
                if not hasattr(original_calls_create, "_llmobserve_instrumented"):
                    self.calls.create = create_calls_wrapper(original_calls_create, "calls.create")
                    self.calls.create._llmobserve_instrumented = True
                    self.calls.create._llmobserve_original = original_calls_create
        
        Client.__init__ = patched_init
        patched_init._llmobserve_instrumented = True
        patched_init._llmobserve_original = original_init
        
        logger.info("[llmobserve] Successfully instrumented Twilio SDK")
        return True
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument Twilio: {e}", exc_info=True)
        return False
