"""
Retell AI voice agent platform instrumentor.

Supports:
- client.call.create() - Create outbound call
- client.call.retrieve() - Get call details
- client.call.list() - List calls
- client.agent.create() - Create agent
- client.llm.create() - Create LLM

Retell pricing (as of 2024):
- Voice agent: $0.07/min (includes STT + LLM + TTS + telephony)
- Individual components available for DIY setups
"""
import functools
import time
import uuid
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config


def track_retell_call(
    method_name: str,
    call_duration_seconds: Optional[float] = None,
    latency_ms: float = 0.0,
    status: str = "ok",
    error: Optional[str] = None,
    call_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    is_voice_call: bool = False,
    cost_breakdown: Optional[dict] = None,
    transcript: Optional[str] = None,
) -> None:
    """Track a Retell API call with voice-specific fields and cost breakdown."""
    
    # Calculate cost based on call type
    total_cost = 0.0
    if is_voice_call and call_duration_seconds:
        # Full voice agent: $0.07/min
        duration_minutes = call_duration_seconds / 60.0
        total_cost = duration_minutes * 0.07
        voice_segment_type = "voice_agent"
        span_type = "voice_agent_call"
    else:
        # API management calls (create agent, list calls, etc.)
        total_cost = 0.0  # No cost for API management calls
        voice_segment_type = None
        span_type = "api_call"
    
    # Use actual cost from API if available
    if cost_breakdown and 'total' in cost_breakdown:
        total_cost = cost_breakdown['total']
    
    main_span_id = str(uuid.uuid4())
    
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": main_span_id,
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": span_type,
        "provider": "retell",
        "endpoint": method_name,
        "model": None,
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
        "voice_segment_type": voice_segment_type,
        "voice_platform": "retell",  # Cross-platform tracking
        "event_metadata": {
            "error": error,
            "call_id": call_id,
            "agent_id": agent_id,
            "call_duration_seconds": call_duration_seconds,
            "cost_breakdown": cost_breakdown,
            "transcript": transcript[:500] if transcript else None,
        } if any([error, call_id, agent_id, call_duration_seconds, cost_breakdown, transcript]) else None,
    }
    
    buffer.add_event(event)
    
    # If we have a cost breakdown, create sub-events for each segment
    if cost_breakdown and is_voice_call:
        segment_mapping = {
            'stt': ('stt', 'stt_call'),
            'transcription': ('stt', 'stt_call'),
            'llm': ('llm', 'llm_call'),
            'tts': ('tts', 'tts_call'),
            'voice': ('tts', 'tts_call'),
            'telephony': ('telephony', 'telephony_call'),
            'transport': ('telephony', 'telephony_call'),
        }
        
        for segment_key, segment_cost in cost_breakdown.items():
            if segment_key == 'total' or segment_cost is None or segment_cost == 0:
                continue
            
            segment_info = segment_mapping.get(segment_key, (segment_key, f'{segment_key}_call'))
            segment_type, segment_span_type = segment_info
            
            segment_event = {
                "id": str(uuid.uuid4()),
                "run_id": context.get_run_id(),
                "span_id": str(uuid.uuid4()),
                "parent_span_id": main_span_id,
                "section": context.get_current_section(),
                "section_path": f"{context.get_section_path()}/segment:{segment_type}",
                "span_type": segment_span_type,
                "provider": "retell",
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
                "voice_platform": "retell",  # Cross-platform tracking
                "event_metadata": None,
            }
            buffer.add_event(segment_event)


def extract_call_info(response: Any) -> dict:
    """Extract call ID, duration, agent ID, cost breakdown and transcript from Retell response."""
    info = {
        'call_id': None,
        'duration': None,
        'agent_id': None,
        'cost_breakdown': None,
        'transcript': None,
    }
    
    try:
        # Try object attributes
        if hasattr(response, 'call_id'):
            info['call_id'] = response.call_id
        elif hasattr(response, 'id'):
            info['call_id'] = response.id
            
        if hasattr(response, 'call_duration_seconds'):
            info['duration'] = response.call_duration_seconds
        elif hasattr(response, 'duration'):
            info['duration'] = response.duration
            
        if hasattr(response, 'agent_id'):
            info['agent_id'] = response.agent_id
        
        # Extract cost breakdown (Retell may provide this)
        if hasattr(response, 'cost_breakdown'):
            info['cost_breakdown'] = response.cost_breakdown
        elif hasattr(response, 'costs'):
            info['cost_breakdown'] = response.costs
        
        # Try to build cost breakdown from individual fields
        if not info['cost_breakdown']:
            cost_breakdown = {}
            if hasattr(response, 'stt_cost'):
                cost_breakdown['stt'] = response.stt_cost
            if hasattr(response, 'llm_cost'):
                cost_breakdown['llm'] = response.llm_cost
            if hasattr(response, 'tts_cost'):
                cost_breakdown['tts'] = response.tts_cost
            if hasattr(response, 'telephony_cost'):
                cost_breakdown['telephony'] = response.telephony_cost
            if hasattr(response, 'total_cost'):
                cost_breakdown['total'] = response.total_cost
            if cost_breakdown:
                info['cost_breakdown'] = cost_breakdown
        
        # Extract transcript
        if hasattr(response, 'transcript'):
            info['transcript'] = response.transcript
        elif hasattr(response, 'call_transcript'):
            info['transcript'] = response.call_transcript
            
        # Try dict response
        if isinstance(response, dict):
            info['call_id'] = info['call_id'] or response.get('call_id') or response.get('id')
            info['duration'] = info['duration'] or response.get('call_duration_seconds') or response.get('duration')
            info['agent_id'] = info['agent_id'] or response.get('agent_id')
            info['cost_breakdown'] = info['cost_breakdown'] or response.get('cost_breakdown') or response.get('costs')
            info['transcript'] = info['transcript'] or response.get('transcript') or response.get('call_transcript')
            
            # Try to build cost breakdown from individual dict fields
            if not info['cost_breakdown']:
                cost_breakdown = {}
                for key in ['stt_cost', 'llm_cost', 'tts_cost', 'telephony_cost', 'total_cost']:
                    if key in response and response[key]:
                        cost_breakdown[key.replace('_cost', '')] = response[key]
                if cost_breakdown:
                    info['cost_breakdown'] = cost_breakdown
            
    except Exception:
        pass
    
    return info


def create_call_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create wrapper for Retell call methods."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            info = extract_call_info(result)
            
            # Determine if this is a voice call with duration
            is_voice_call = method_name in ["call.create", "call.retrieve"] and info['duration'] is not None
            
            track_retell_call(
                method_name=method_name,
                call_duration_seconds=info['duration'],
                latency_ms=latency_ms,
                status="ok",
                call_id=info['call_id'],
                agent_id=info['agent_id'],
                is_voice_call=is_voice_call,
                cost_breakdown=info['cost_breakdown'],
                transcript=info['transcript'],
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_retell_call(
                method_name=method_name,
                latency_ms=latency_ms,
                status="error",
                error=str(e),
            )
            
            raise
    
    return wrapper


def create_agent_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create wrapper for Retell agent/LLM management methods."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            agent_id = None
            if hasattr(result, 'agent_id'):
                agent_id = result.agent_id
            elif isinstance(result, dict):
                agent_id = result.get('agent_id')
            
            track_retell_call(
                method_name=method_name,
                latency_ms=latency_ms,
                status="ok",
                agent_id=agent_id,
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_retell_call(
                method_name=method_name,
                latency_ms=latency_ms,
                status="error",
                error=str(e),
            )
            
            raise
    
    return wrapper


def instrument_retell() -> bool:
    """Instrument Retell SDK."""
    try:
        from retell import Retell
    except ImportError:
        logger.debug("[llmobserve] Retell SDK not installed - skipping")
        return False
    
    try:
        # Check if already instrumented
        if hasattr(Retell, "_llmobserve_instrumented"):
            logger.debug("[llmobserve] Retell already instrumented")
            return True
        
        original_init = Retell.__init__
        
        @functools.wraps(original_init)
        def patched_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            
            # Patch call methods
            if hasattr(self, 'call'):
                call_obj = self.call
                
                for method_name in ['create', 'retrieve', 'list']:
                    if hasattr(call_obj, method_name):
                        original = getattr(call_obj, method_name)
                        if not hasattr(original, '_llmobserve_instrumented'):
                            wrapped = create_call_wrapper(original, f"call.{method_name}")
                            setattr(call_obj, method_name, wrapped)
                            wrapped._llmobserve_instrumented = True
            
            # Patch agent methods
            if hasattr(self, 'agent'):
                agent_obj = self.agent
                
                for method_name in ['create', 'retrieve', 'list', 'update', 'delete']:
                    if hasattr(agent_obj, method_name):
                        original = getattr(agent_obj, method_name)
                        if not hasattr(original, '_llmobserve_instrumented'):
                            wrapped = create_agent_wrapper(original, f"agent.{method_name}")
                            setattr(agent_obj, method_name, wrapped)
                            wrapped._llmobserve_instrumented = True
            
            # Patch LLM methods
            if hasattr(self, 'llm'):
                llm_obj = self.llm
                
                for method_name in ['create', 'retrieve', 'list', 'update', 'delete']:
                    if hasattr(llm_obj, method_name):
                        original = getattr(llm_obj, method_name)
                        if not hasattr(original, '_llmobserve_instrumented'):
                            wrapped = create_agent_wrapper(original, f"llm.{method_name}")
                            setattr(llm_obj, method_name, wrapped)
                            wrapped._llmobserve_instrumented = True
        
        Retell.__init__ = patched_init
        Retell._llmobserve_instrumented = True
        
        logger.info("[llmobserve] Successfully instrumented Retell SDK")
        return True
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument Retell: {e}", exc_info=True)
        return False

