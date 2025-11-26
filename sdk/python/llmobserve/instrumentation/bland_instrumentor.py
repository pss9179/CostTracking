"""
Bland AI Voice Agent instrumentor.

Supports:
- bland.calls.create() - Create outbound call
- bland.calls.get() - Get call details with cost
- bland.calls.list() - List calls
- bland.calls.analyze() - Get call analysis
"""
import functools
import time
import uuid
import logging
from typing import Any, Callable, Optional, Dict

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config


# Bland AI pricing (as of 2024)
BLAND_PRICING = {
    "standard": 0.09,  # $0.09/min standard
    "enterprise": 0.05,  # $0.05/min enterprise (volume discount)
    "turbo": 0.12,  # $0.12/min turbo (faster)
    
    # Telephony add-ons
    "phone_number": 2.00,  # $2/month per number
    "call_transfer": 0.01,  # $0.01 per transfer
}


def track_bland_call(
    method_name: str,
    call_id: Optional[str],
    total_cost: float,
    latency_ms: float,
    status: str = "ok",
    error: Optional[str] = None,
    call_duration_seconds: Optional[float] = None,
    call_status: Optional[str] = None,
    transcript: Optional[str] = None,
    from_number: Optional[str] = None,
    to_number: Optional[str] = None,
    cost_breakdown: Optional[Dict] = None,
) -> None:
    """Track a Bland AI API call."""
    
    # Main call event
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": "voice_agent_call",
        "provider": "bland",
        "endpoint": method_name,
        "model": None,  # Bland handles model selection internally
        "cost_usd": total_cost,
        "latency_ms": latency_ms,
        "input_tokens": 0,
        "output_tokens": 0,
        "status": status,
        "tenant_id": config.get_tenant_id(),
        "customer_id": context.get_customer_id(),
        # Voice-specific fields
        "voice_call_id": call_id or context.get_voice_call_id(),
        "audio_duration_seconds": call_duration_seconds,
        "voice_segment_type": "voice_agent",
        "event_metadata": {
            "error": error,
            "call_status": call_status,
            "from_number": from_number,
            "to_number": to_number,
            "transcript": transcript[:500] if transcript else None,  # Truncate
            "cost_breakdown": cost_breakdown,
        },
    }
    
    buffer.add_event(event)
    
    # If we have a cost breakdown, create sub-events
    if cost_breakdown:
        parent_span_id = event["span_id"]
        
        for segment_type, segment_cost in cost_breakdown.items():
            if segment_type == "total" or segment_cost is None or segment_cost == 0:
                continue
            
            segment_event = {
                "id": str(uuid.uuid4()),
                "run_id": context.get_run_id(),
                "span_id": str(uuid.uuid4()),
                "parent_span_id": parent_span_id,
                "section": context.get_current_section(),
                "section_path": f"{context.get_section_path()}/segment:{segment_type}",
                "span_type": f"{segment_type}_call",
                "provider": "bland",
                "endpoint": f"{method_name}.{segment_type}",
                "model": None,
                "cost_usd": segment_cost,
                "latency_ms": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "status": status,
                "tenant_id": config.get_tenant_id(),
                "customer_id": context.get_customer_id(),
                "voice_call_id": call_id,
                "audio_duration_seconds": call_duration_seconds if segment_type in ["stt", "tts"] else None,
                "voice_segment_type": segment_type,
                "event_metadata": None,
            }
            buffer.add_event(segment_event)


def extract_call_info(result: Any) -> Dict:
    """Extract call information from Bland API response."""
    info = {
        "call_id": None,
        "total_cost": 0.0,
        "duration_seconds": None,
        "status": None,
        "transcript": None,
        "from_number": None,
        "to_number": None,
        "cost_breakdown": None,
    }
    
    try:
        # Handle object response
        if hasattr(result, 'id'):
            info["call_id"] = result.id
        if hasattr(result, 'call_id'):
            info["call_id"] = result.call_id
        
        # Duration
        if hasattr(result, 'call_length'):
            info["duration_seconds"] = result.call_length
        elif hasattr(result, 'duration'):
            info["duration_seconds"] = result.duration
        
        # Cost
        if hasattr(result, 'price'):
            info["total_cost"] = result.price
        elif hasattr(result, 'cost'):
            info["total_cost"] = result.cost
        
        # Status
        if hasattr(result, 'status'):
            info["status"] = result.status
        
        # Transcript
        if hasattr(result, 'transcript'):
            info["transcript"] = result.transcript
        elif hasattr(result, 'concatenated_transcript'):
            info["transcript"] = result.concatenated_transcript
        
        # Phone numbers
        if hasattr(result, 'from'):
            info["from_number"] = getattr(result, 'from')
        if hasattr(result, 'to'):
            info["to_number"] = result.to
        
        # Cost breakdown (if available)
        if hasattr(result, 'cost_breakdown'):
            info["cost_breakdown"] = result.cost_breakdown
        
        # Handle dict response
        if isinstance(result, dict):
            info["call_id"] = result.get('id') or result.get('call_id')
            info["duration_seconds"] = result.get('call_length') or result.get('duration')
            info["total_cost"] = result.get('price') or result.get('cost', 0.0)
            info["status"] = result.get('status')
            info["transcript"] = result.get('transcript') or result.get('concatenated_transcript')
            info["from_number"] = result.get('from')
            info["to_number"] = result.get('to')
            info["cost_breakdown"] = result.get('cost_breakdown')
    
    except Exception as e:
        logger.debug(f"[llmobserve] Error extracting Bland call info: {e}")
    
    return info


def create_call_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create wrapper for Bland call methods."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract call info
            info = extract_call_info(result)
            
            # Calculate cost from duration if not provided
            total_cost = info["total_cost"]
            if total_cost == 0 and info["duration_seconds"]:
                total_cost = (info["duration_seconds"] / 60.0) * BLAND_PRICING["standard"]
            
            track_bland_call(
                method_name=method_name,
                call_id=info["call_id"],
                total_cost=total_cost,
                latency_ms=latency_ms,
                status="ok",
                call_duration_seconds=info["duration_seconds"],
                call_status=info["status"],
                transcript=info["transcript"],
                from_number=info["from_number"],
                to_number=info["to_number"],
                cost_breakdown=info["cost_breakdown"],
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_bland_call(
                method_name=method_name,
                call_id=None,
                total_cost=0.0,
                latency_ms=latency_ms,
                status="error",
                error=str(e),
            )
            
            raise
    
    return wrapper


def instrument_bland() -> bool:
    """Instrument Bland AI SDK."""
    
    # Try different possible import paths
    bland_module = None
    
    try:
        import bland
        bland_module = bland
    except ImportError:
        pass
    
    if not bland_module:
        try:
            from bland_ai import Bland
            bland_module = Bland
        except ImportError:
            pass
    
    if not bland_module:
        try:
            import bland_ai
            bland_module = bland_ai
        except ImportError:
            logger.debug("[llmobserve] Bland AI SDK not installed - skipping")
            return False
    
    try:
        # Check if already instrumented
        if hasattr(bland_module, "_llmobserve_instrumented"):
            logger.debug("[llmobserve] Bland AI already instrumented")
            return True
        
        # Try to find and patch the calls resource
        # Different SDK versions might have different structures
        
        # Pattern 1: bland.calls.create(), bland.calls.get()
        if hasattr(bland_module, 'calls'):
            calls = bland_module.calls
            
            if hasattr(calls, 'create') and not hasattr(calls.create, '_llmobserve_instrumented'):
                original = calls.create
                wrapped = create_call_wrapper(original, "calls.create")
                calls.create = wrapped
                wrapped._llmobserve_instrumented = True
                logger.debug("[llmobserve] Instrumented bland.calls.create")
            
            if hasattr(calls, 'get') and not hasattr(calls.get, '_llmobserve_instrumented'):
                original = calls.get
                wrapped = create_call_wrapper(original, "calls.get")
                calls.get = wrapped
                wrapped._llmobserve_instrumented = True
                logger.debug("[llmobserve] Instrumented bland.calls.get")
            
            if hasattr(calls, 'list') and not hasattr(calls.list, '_llmobserve_instrumented'):
                original = calls.list
                wrapped = create_call_wrapper(original, "calls.list")
                calls.list = wrapped
                wrapped._llmobserve_instrumented = True
                logger.debug("[llmobserve] Instrumented bland.calls.list")
        
        # Pattern 2: Bland class with instance methods
        if hasattr(bland_module, 'Bland'):
            BlandClass = bland_module.Bland
            
            original_init = BlandClass.__init__
            
            @functools.wraps(original_init)
            def patched_init(self, *args, **kwargs):
                original_init(self, *args, **kwargs)
                
                # Patch instance methods
                if hasattr(self, 'calls'):
                    calls = self.calls
                    
                    if hasattr(calls, 'create') and not hasattr(calls.create, '_llmobserve_instrumented'):
                        original = calls.create
                        wrapped = create_call_wrapper(original, "calls.create")
                        calls.create = wrapped
                        wrapped._llmobserve_instrumented = True
                    
                    if hasattr(calls, 'get') and not hasattr(calls.get, '_llmobserve_instrumented'):
                        original = calls.get
                        wrapped = create_call_wrapper(original, "calls.get")
                        calls.get = wrapped
                        wrapped._llmobserve_instrumented = True
            
            BlandClass.__init__ = patched_init
            BlandClass._llmobserve_instrumented = True
        
        bland_module._llmobserve_instrumented = True
        logger.info("[llmobserve] Successfully instrumented Bland AI SDK")
        return True
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument Bland AI: {e}", exc_info=True)
        return False

