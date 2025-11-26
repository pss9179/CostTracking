"""
Telnyx telephony instrumentor with fail-open safety.

Tracks costs for:
- Voice calls: ~$0.007 per minute (varies by destination)
- SMS: ~$0.004 per message (US)

Supports:
- telnyx.Call.create() - outbound calls
- telnyx.Message.create() - SMS/MMS
- Async variants
"""
import functools
import time
import uuid
import logging
import threading
from typing import Any, Callable, Optional, Dict

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config

# Telnyx pricing (US rates - very competitive)
TELNYX_VOICE_PER_MINUTE = 0.007
TELNYX_SMS_COST = 0.004

# Track active calls
_active_calls: Dict[str, Dict[str, Any]] = {}
_calls_lock = threading.Lock()


def track_telnyx_event(
    method_name: str,
    cost_usd: float,
    latency_ms: float,
    duration_seconds: Optional[float] = None,
    call_control_id: Optional[str] = None,
    direction: Optional[str] = None,
    status: str = "ok",
    error: Optional[str] = None,
    voice_call_id: Optional[str] = None,
) -> None:
    """Track a Telnyx API call with voice-specific fields."""
    
    if "message" in method_name.lower():
        span_type = "sms_call"
    elif "call" in method_name.lower():
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
        "provider": "telnyx",
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
        "voice_segment_type": "telephony" if "call" in method_name.lower() else None,
        "event_metadata": {
            "call_control_id": call_control_id,
            "direction": direction,
            "duration_seconds": duration_seconds,
            "error": error,
        } if any([call_control_id, direction, duration_seconds, error]) else None,
    }
    
    buffer.add_event(event)


def calculate_call_cost(duration_seconds: float) -> float:
    """Calculate call cost based on duration."""
    minutes = duration_seconds / 60.0
    return minutes * TELNYX_VOICE_PER_MINUTE


def track_call_end(call_control_id: str, duration_seconds: float, direction: str = "outbound"):
    """
    Manually track a Telnyx call's end with known duration.
    
    Args:
        call_control_id: The Telnyx Call Control ID
        duration_seconds: Actual call duration in seconds
        direction: Call direction
    """
    voice_call_id = None
    with _calls_lock:
        if call_control_id in _active_calls:
            voice_call_id = _active_calls[call_control_id].get("voice_call_id")
            _active_calls.pop(call_control_id, None)
    
    cost = calculate_call_cost(duration_seconds)
    
    track_telnyx_event(
        method_name="call.completed",
        cost_usd=cost,
        latency_ms=0,
        duration_seconds=duration_seconds,
        call_control_id=call_control_id,
        direction=direction,
        voice_call_id=voice_call_id,
    )
    
    return cost


def create_call_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create wrapper for call methods."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract call control ID
            call_control_id = None
            if hasattr(result, "call_control_id"):
                call_control_id = result.call_control_id
            elif hasattr(result, "data") and hasattr(result.data, "call_control_id"):
                call_control_id = result.data.call_control_id
            elif isinstance(result, dict):
                call_control_id = result.get("call_control_id") or result.get("data", {}).get("call_control_id")
            
            # Register for duration tracking
            if call_control_id:
                with _calls_lock:
                    _active_calls[call_control_id] = {
                        "start_time": time.time(),
                        "voice_call_id": context.get_voice_call_id(),
                    }
            
            track_telnyx_event(
                method_name=method_name,
                cost_usd=0,  # Cost calculated when call ends
                latency_ms=latency_ms,
                call_control_id=call_control_id,
                direction="outbound",
                status="initiated",
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_telnyx_event(
                method_name=method_name,
                cost_usd=0,
                latency_ms=latency_ms,
                status="error",
                error=str(e),
            )
            
            raise
    
    return wrapper


def create_message_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create wrapper for message methods."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            # Get cost from response if available
            cost = TELNYX_SMS_COST
            if hasattr(result, "cost") and result.cost:
                cost = float(result.cost.amount) if hasattr(result.cost, "amount") else float(result.cost)
            elif hasattr(result, "data") and hasattr(result.data, "cost"):
                data_cost = result.data.cost
                cost = float(data_cost.amount) if hasattr(data_cost, "amount") else float(data_cost)
            
            track_telnyx_event(
                method_name=method_name,
                cost_usd=cost,
                latency_ms=latency_ms,
                status="ok",
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_telnyx_event(
                method_name=method_name,
                cost_usd=TELNYX_SMS_COST,
                latency_ms=latency_ms,
                status="error",
                error=str(e),
            )
            
            raise
    
    return wrapper


def instrument_telnyx() -> bool:
    """Instrument Telnyx SDK for Voice and SMS tracking."""
    try:
        import telnyx
    except ImportError:
        logger.debug("[llmobserve] Telnyx SDK not installed - skipping")
        return False
    
    try:
        instrumented = False
        
        # Patch telnyx.Call.create
        if hasattr(telnyx, "Call"):
            Call = telnyx.Call
            if hasattr(Call, "create"):
                original_create = Call.create
                if not hasattr(original_create, "_llmobserve_instrumented"):
                    Call.create = create_call_wrapper(original_create, "Call.create")
                    Call.create._llmobserve_instrumented = True
                    Call.create._llmobserve_original = original_create
                    instrumented = True
        
        # Patch telnyx.Message.create
        if hasattr(telnyx, "Message"):
            Message = telnyx.Message
            if hasattr(Message, "create"):
                original_create = Message.create
                if not hasattr(original_create, "_llmobserve_instrumented"):
                    Message.create = create_message_wrapper(original_create, "Message.create")
                    Message.create._llmobserve_instrumented = True
                    Message.create._llmobserve_original = original_create
                    instrumented = True
        
        # Try telnyx.api_resources patterns if available
        if hasattr(telnyx, "api_resources"):
            api = telnyx.api_resources
            
            if hasattr(api, "Call") and hasattr(api.Call, "create"):
                original = api.Call.create
                if not hasattr(original, "_llmobserve_instrumented"):
                    api.Call.create = create_call_wrapper(original, "Call.create")
                    api.Call.create._llmobserve_instrumented = True
                    instrumented = True
            
            if hasattr(api, "Message") and hasattr(api.Message, "create"):
                original = api.Message.create
                if not hasattr(original, "_llmobserve_instrumented"):
                    api.Message.create = create_message_wrapper(original, "Message.create")
                    api.Message.create._llmobserve_instrumented = True
                    instrumented = True
        
        if instrumented:
            logger.info("[llmobserve] Successfully instrumented Telnyx SDK")
            return True
        else:
            logger.debug("[llmobserve] No instrumentable methods found in Telnyx SDK")
            return False
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument Telnyx: {e}", exc_info=True)
        return False

