"""
Vonage (Nexmo) telephony instrumentor with fail-open safety.

Tracks costs for:
- Voice calls: ~$0.0127 per minute (US)
- SMS: ~$0.0076 per message (US)

Supports:
- client.voice.create_call() - outbound calls
- client.sms.send_message() - SMS
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

# Vonage pricing (US rates)
VONAGE_VOICE_PER_MINUTE = 0.0127
VONAGE_SMS_COST = 0.0076

# Track active calls for duration tracking
_active_calls: Dict[str, Dict[str, Any]] = {}
_calls_lock = threading.Lock()


def track_vonage_event(
    method_name: str,
    cost_usd: float,
    latency_ms: float,
    duration_seconds: Optional[float] = None,
    call_uuid: Optional[str] = None,
    direction: Optional[str] = None,
    status: str = "ok",
    error: Optional[str] = None,
    voice_call_id: Optional[str] = None,
) -> None:
    """Track a Vonage API call with voice-specific fields."""
    
    # Determine span type
    if "sms" in method_name.lower():
        span_type = "sms_call"
    elif "voice" in method_name.lower() or "call" in method_name.lower():
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
        "provider": "vonage",
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
        "voice_segment_type": "telephony" if "voice" in method_name.lower() or "call" in method_name.lower() else None,
        "event_metadata": {
            "call_uuid": call_uuid,
            "direction": direction,
            "duration_seconds": duration_seconds,
            "error": error,
        } if any([call_uuid, direction, duration_seconds, error]) else None,
    }
    
    buffer.add_event(event)


def calculate_call_cost(duration_seconds: float) -> float:
    """Calculate call cost based on duration."""
    minutes = duration_seconds / 60.0
    return minutes * VONAGE_VOICE_PER_MINUTE


def track_call_end(call_uuid: str, duration_seconds: float, direction: str = "outbound"):
    """
    Manually track a Vonage call's end with known duration.
    
    Args:
        call_uuid: The Vonage Call UUID
        duration_seconds: Actual call duration in seconds
        direction: Call direction
    """
    voice_call_id = None
    with _calls_lock:
        if call_uuid in _active_calls:
            voice_call_id = _active_calls[call_uuid].get("voice_call_id")
            _active_calls.pop(call_uuid, None)
    
    cost = calculate_call_cost(duration_seconds)
    
    track_vonage_event(
        method_name="voice.call_completed",
        cost_usd=cost,
        latency_ms=0,
        duration_seconds=duration_seconds,
        call_uuid=call_uuid,
        direction=direction,
        voice_call_id=voice_call_id,
    )
    
    return cost


def create_voice_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create wrapper for voice call methods."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract call UUID from response
            call_uuid = None
            if hasattr(result, "uuid"):
                call_uuid = result.uuid
            elif isinstance(result, dict):
                call_uuid = result.get("uuid") or result.get("call_uuid")
            
            # Register for duration tracking
            if call_uuid:
                with _calls_lock:
                    _active_calls[call_uuid] = {
                        "start_time": time.time(),
                        "voice_call_id": context.get_voice_call_id(),
                    }
            
            # Log call initiation
            track_vonage_event(
                method_name=method_name,
                cost_usd=0,  # Cost calculated when call ends
                latency_ms=latency_ms,
                call_uuid=call_uuid,
                direction="outbound",
                status="initiated",
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_vonage_event(
                method_name=method_name,
                cost_usd=0,
                latency_ms=latency_ms,
                status="error",
                error=str(e),
            )
            
            raise
    
    return wrapper


def create_sms_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create wrapper for SMS methods."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            # Get price from response if available
            cost = VONAGE_SMS_COST
            if hasattr(result, "message_price") and result.message_price:
                cost = float(result.message_price)
            elif isinstance(result, dict) and result.get("message-price"):
                cost = float(result["message-price"])
            
            track_vonage_event(
                method_name=method_name,
                cost_usd=cost,
                latency_ms=latency_ms,
                status="ok",
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_vonage_event(
                method_name=method_name,
                cost_usd=VONAGE_SMS_COST,
                latency_ms=latency_ms,
                status="error",
                error=str(e),
            )
            
            raise
    
    return wrapper


def instrument_vonage() -> bool:
    """Instrument Vonage SDK for Voice and SMS tracking."""
    try:
        import vonage
    except ImportError:
        logger.debug("[llmobserve] Vonage SDK not installed - skipping")
        return False
    
    try:
        # Vonage has multiple client patterns
        instrumented = False
        
        # Try vonage.Client
        if hasattr(vonage, "Client"):
            Client = vonage.Client
            original_init = Client.__init__
            
            if not hasattr(original_init, "_llmobserve_instrumented"):
                @functools.wraps(original_init)
                def patched_init(self, *args, **kwargs):
                    original_init(self, *args, **kwargs)
                    
                    # Patch voice methods
                    if hasattr(self, "voice"):
                        voice = self.voice
                        for method_name in ["create_call", "send"]:
                            if hasattr(voice, method_name):
                                original = getattr(voice, method_name)
                                if not hasattr(original, "_llmobserve_instrumented"):
                                    wrapped = create_voice_wrapper(original, f"voice.{method_name}")
                                    setattr(voice, method_name, wrapped)
                                    wrapped._llmobserve_instrumented = True
                    
                    # Patch SMS methods
                    if hasattr(self, "sms"):
                        sms = self.sms
                        for method_name in ["send_message", "send"]:
                            if hasattr(sms, method_name):
                                original = getattr(sms, method_name)
                                if not hasattr(original, "_llmobserve_instrumented"):
                                    wrapped = create_sms_wrapper(original, f"sms.{method_name}")
                                    setattr(sms, method_name, wrapped)
                                    wrapped._llmobserve_instrumented = True
                
                Client.__init__ = patched_init
                patched_init._llmobserve_instrumented = True
                instrumented = True
        
        # Try vonage.Vonage (newer SDK)
        if hasattr(vonage, "Vonage"):
            Vonage = vonage.Vonage
            original_vonage_init = Vonage.__init__
            
            if not hasattr(original_vonage_init, "_llmobserve_instrumented"):
                @functools.wraps(original_vonage_init)
                def patched_vonage_init(self, *args, **kwargs):
                    original_vonage_init(self, *args, **kwargs)
                    
                    if hasattr(self, "voice"):
                        voice = self.voice
                        if hasattr(voice, "create_call"):
                            original = voice.create_call
                            if not hasattr(original, "_llmobserve_instrumented"):
                                voice.create_call = create_voice_wrapper(original, "voice.create_call")
                                voice.create_call._llmobserve_instrumented = True
                    
                    if hasattr(self, "sms"):
                        sms = self.sms
                        if hasattr(sms, "send"):
                            original = sms.send
                            if not hasattr(original, "_llmobserve_instrumented"):
                                sms.send = create_sms_wrapper(original, "sms.send")
                                sms.send._llmobserve_instrumented = True
                
                Vonage.__init__ = patched_vonage_init
                patched_vonage_init._llmobserve_instrumented = True
                instrumented = True
        
        if instrumented:
            logger.info("[llmobserve] Successfully instrumented Vonage SDK")
            return True
        else:
            logger.debug("[llmobserve] No instrumentable methods found in Vonage SDK")
            return False
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument Vonage: {e}", exc_info=True)
        return False

