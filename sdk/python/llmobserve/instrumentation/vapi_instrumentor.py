"""
Vapi voice agent platform instrumentor.

Supports:
- client.calls.create() - Create outbound call
- client.calls.get() - Get call details
- client.calls.list() - List calls
- client.assistants.create() - Create assistant
- client.assistants.get() - Get assistant
- client.phone_numbers.list() - List phone numbers

Vapi pricing (as of 2024):
- Voice calls: $0.05/min (base)
- Transcription: $0.01/min
- Various voice providers add-on
"""
import functools
import time
import uuid
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("llmobserve")

from llmobserve import buffer, context, config


def track_vapi_call(
    method_name: str,
    call_duration_seconds: Optional[float] = None,
    latency_ms: float = 0.0,
    status: str = "ok",
    error: Optional[str] = None,
    call_id: Optional[str] = None,
    assistant_id: Optional[str] = None,
    is_voice_call: bool = False,
    cost_breakdown: Optional[dict] = None,
    transcript: Optional[str] = None,
) -> None:
    """Track a Vapi API call with voice-specific fields.
    
    When cost_breakdown is available (from Vapi's costBreakdown field),
    we create separate events for each segment (STT, LLM, TTS, transport)
    so they appear correctly in the Voice Agents dashboard.
    """
    voice_call_id = call_id or context.get_voice_call_id()
    
    # If we have detailed cost breakdown from Vapi, create separate events for each segment
    if is_voice_call and cost_breakdown and any(cost_breakdown.get(k) for k in ['stt', 'llm', 'tts', 'transport']):
        # Create individual events for each segment with cost
        segments = [
            ("stt", cost_breakdown.get("stt"), "stt_call", cost_breakdown.get("llm_prompt_tokens")),
            ("llm", cost_breakdown.get("llm"), "llm_call", cost_breakdown.get("llm_completion_tokens")),
            ("tts", cost_breakdown.get("tts"), "tts_call", cost_breakdown.get("tts_characters")),
            ("telephony", cost_breakdown.get("transport"), "telephony_call", None),
        ]
        
        for segment_type, segment_cost, span_type, tokens in segments:
            if segment_cost and segment_cost > 0:
                event = {
                    "id": str(uuid.uuid4()),
                    "run_id": context.get_run_id(),
                    "span_id": str(uuid.uuid4()),
                    "parent_span_id": context.get_current_span_id(),
                    "section": context.get_current_section(),
                    "section_path": context.get_section_path(),
                    "span_type": span_type,
                    "provider": "vapi",
                    "endpoint": f"{method_name}.{segment_type}",
                    "model": None,
                    "cost_usd": segment_cost,
                    "latency_ms": latency_ms / 4 if latency_ms else 0,  # Estimate per segment
                    "input_tokens": tokens or 0,
                    "output_tokens": 0,
                    "status": status,
                    "tenant_id": config.get_tenant_id(),
                    "customer_id": context.get_customer_id(),
                    "voice_call_id": voice_call_id,
                    "audio_duration_seconds": call_duration_seconds,
                    "voice_segment_type": segment_type,
                    "event_metadata": {
                        "call_id": call_id,
                        "assistant_id": assistant_id,
                        "segment_cost": segment_cost,
                        "transcript": transcript[:500] if transcript else None,
                    },
                }
                buffer.add_event(event)
        
        # Also add Vapi platform fee if present
        if cost_breakdown.get("vapi"):
            event = {
                "id": str(uuid.uuid4()),
                "run_id": context.get_run_id(),
                "span_id": str(uuid.uuid4()),
                "parent_span_id": context.get_current_span_id(),
                "section": context.get_current_section(),
                "section_path": context.get_section_path(),
                "span_type": "platform_fee",
                "provider": "vapi",
                "endpoint": f"{method_name}.platform",
                "model": None,
                "cost_usd": cost_breakdown.get("vapi"),
                "latency_ms": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "status": status,
                "tenant_id": config.get_tenant_id(),
                "customer_id": context.get_customer_id(),
                "voice_call_id": voice_call_id,
                "audio_duration_seconds": call_duration_seconds,
                "voice_segment_type": "platform",
                "event_metadata": {"call_id": call_id},
            }
            buffer.add_event(event)
        return
    
    # Fallback: single event for the whole call
    if is_voice_call and call_duration_seconds:
        duration_minutes = call_duration_seconds / 60.0
        if cost_breakdown and cost_breakdown.get("total"):
            cost_usd = cost_breakdown["total"]
        else:
            cost_usd = duration_minutes * 0.05  # Estimate $0.05/min
        voice_segment_type = "telephony"
        span_type = "voice_call"
    else:
        cost_usd = 0.002 if method_name.startswith("assistants") else 0.001
        voice_segment_type = None
        span_type = "api_call"
    
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": context.get_current_span_id(),
        "section": context.get_current_section(),
        "section_path": context.get_section_path(),
        "span_type": span_type,
        "provider": "vapi",
        "endpoint": method_name,
        "model": None,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
        "input_tokens": 0,
        "output_tokens": 0,
        "status": status,
        "tenant_id": config.get_tenant_id(),
        "customer_id": context.get_customer_id(),
        "voice_call_id": voice_call_id,
        "audio_duration_seconds": call_duration_seconds,
        "voice_segment_type": voice_segment_type,
        "event_metadata": {
            "error": error,
            "call_id": call_id,
            "assistant_id": assistant_id,
            "call_duration_seconds": call_duration_seconds,
            "cost_breakdown": cost_breakdown,
            "transcript": transcript[:500] if transcript else None,
        } if any([error, call_id, assistant_id, call_duration_seconds, cost_breakdown, transcript]) else None,
    }
    
    buffer.add_event(event)


def extract_vapi_call_info(response: Any) -> dict:
    """Extract call ID, duration, assistant ID, cost breakdown, and transcript from Vapi response.
    
    Vapi provides detailed costBreakdown with:
    - transport: Twilio/Vonage telephony cost
    - stt: Speech-to-text cost
    - llm: Language model cost  
    - tts: Text-to-speech cost
    - vapi: Vapi platform fee
    - total: Total cost
    - llmPromptTokens, llmCompletionTokens, ttsCharacters
    """
    info = {
        'call_id': None,
        'duration': None,
        'assistant_id': None,
        'cost_breakdown': None,
        'transcript': None,
    }
    
    try:
        # Try object attributes
        if hasattr(response, 'id'):
            info['call_id'] = response.id
        if hasattr(response, 'duration'):
            info['duration'] = response.duration
        elif hasattr(response, 'ended_at') and hasattr(response, 'started_at'):
            # Calculate duration from timestamps
            if response.ended_at and response.started_at:
                try:
                    from datetime import datetime
                    ended = response.ended_at if isinstance(response.ended_at, datetime) else datetime.fromisoformat(response.ended_at.replace('Z', '+00:00'))
                    started = response.started_at if isinstance(response.started_at, datetime) else datetime.fromisoformat(response.started_at.replace('Z', '+00:00'))
                    info['duration'] = (ended - started).total_seconds()
                except:
                    pass
        if hasattr(response, 'assistant_id'):
            info['assistant_id'] = response.assistant_id
        elif hasattr(response, 'assistantId'):
            info['assistant_id'] = response.assistantId
        
        # Extract transcript
        if hasattr(response, 'transcript'):
            info['transcript'] = response.transcript
        elif hasattr(response, 'messages') and response.messages:
            # Build transcript from messages
            try:
                messages = response.messages
                transcript_parts = []
                for msg in messages[:20]:  # Limit to first 20 messages
                    role = getattr(msg, 'role', None) or (msg.get('role') if isinstance(msg, dict) else None)
                    content = getattr(msg, 'content', None) or (msg.get('content') if isinstance(msg, dict) else None)
                    if role and content:
                        transcript_parts.append(f"{role}: {content}")
                info['transcript'] = "\n".join(transcript_parts)[:1000]  # Truncate to 1000 chars
            except:
                pass
            
        # Extract detailed costBreakdown (Vapi provides STT/LLM/TTS/transport breakdown!)
        if hasattr(response, 'cost_breakdown') and response.cost_breakdown:
            cb = response.cost_breakdown
            info['cost_breakdown'] = {
                "stt": getattr(cb, 'stt', None),
                "llm": getattr(cb, 'llm', None),
                "tts": getattr(cb, 'tts', None),
                "transport": getattr(cb, 'transport', None),
                "vapi": getattr(cb, 'vapi', None),
                "total": getattr(cb, 'total', None),
                "llm_prompt_tokens": getattr(cb, 'llmPromptTokens', None) or getattr(cb, 'llm_prompt_tokens', None),
                "llm_completion_tokens": getattr(cb, 'llmCompletionTokens', None) or getattr(cb, 'llm_completion_tokens', None),
                "tts_characters": getattr(cb, 'ttsCharacters', None) or getattr(cb, 'tts_characters', None),
            }
        elif hasattr(response, 'costBreakdown') and response.costBreakdown:
            cb = response.costBreakdown
            info['cost_breakdown'] = {
                "stt": getattr(cb, 'stt', None),
                "llm": getattr(cb, 'llm', None),
                "tts": getattr(cb, 'tts', None),
                "transport": getattr(cb, 'transport', None),
                "vapi": getattr(cb, 'vapi', None),
                "total": getattr(cb, 'total', None),
                "llm_prompt_tokens": getattr(cb, 'llmPromptTokens', None),
                "llm_completion_tokens": getattr(cb, 'llmCompletionTokens', None),
                "tts_characters": getattr(cb, 'ttsCharacters', None),
            }
        elif hasattr(response, 'cost'):
            info['cost_breakdown'] = {"total": response.cost}
            
        # Try dict response
        if isinstance(response, dict):
            info['call_id'] = info['call_id'] or response.get('id')
            info['duration'] = info['duration'] or response.get('duration')
            if not info['duration'] and response.get('endedAt') and response.get('startedAt'):
                try:
                    from datetime import datetime
                    ended = datetime.fromisoformat(response['endedAt'].replace('Z', '+00:00'))
                    started = datetime.fromisoformat(response['startedAt'].replace('Z', '+00:00'))
                    info['duration'] = (ended - started).total_seconds()
                except:
                    pass
            info['assistant_id'] = info['assistant_id'] or response.get('assistant_id') or response.get('assistantId')
            
            # Extract transcript from dict
            if not info['transcript']:
                info['transcript'] = response.get('transcript')
                if not info['transcript'] and response.get('messages'):
                    try:
                        messages = response.get('messages', [])
                        transcript_parts = []
                        for msg in messages[:20]:
                            role = msg.get('role', '')
                            content = msg.get('content', '')
                            if role and content:
                                transcript_parts.append(f"{role}: {content}")
                        info['transcript'] = "\n".join(transcript_parts)[:1000]
                    except:
                        pass
            
            # Extract costBreakdown from dict
            cb = response.get('costBreakdown') or response.get('cost_breakdown')
            if cb and isinstance(cb, dict):
                info['cost_breakdown'] = {
                    "stt": cb.get('stt'),
                    "llm": cb.get('llm'),
                    "tts": cb.get('tts'),
                    "transport": cb.get('transport'),
                    "vapi": cb.get('vapi'),
                    "total": cb.get('total'),
                    "llm_prompt_tokens": cb.get('llmPromptTokens'),
                    "llm_completion_tokens": cb.get('llmCompletionTokens'),
                    "tts_characters": cb.get('ttsCharacters'),
                }
            elif not info['cost_breakdown'] and response.get('cost'):
                info['cost_breakdown'] = {"total": response.get('cost')}
                
    except Exception:
        pass
    
    return info


def create_calls_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create wrapper for Vapi calls methods."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            info = extract_vapi_call_info(result)
            
            # Determine if this is a voice call with duration
            is_voice_call = method_name in ["calls.create", "calls.get"] and info['duration'] is not None
            
            track_vapi_call(
                method_name=method_name,
                call_duration_seconds=info['duration'],
                latency_ms=latency_ms,
                status="ok",
                call_id=info['call_id'],
                assistant_id=info['assistant_id'],
                is_voice_call=is_voice_call,
                cost_breakdown=info['cost_breakdown'],
                transcript=info['transcript'],
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_vapi_call(
                method_name=method_name,
                latency_ms=latency_ms,
                status="error",
                error=str(e),
            )
            
            raise
    
    return wrapper


def create_management_wrapper(original_method: Callable, method_name: str) -> Callable:
    """Create wrapper for Vapi management methods (assistants, phone numbers)."""
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        if not config.is_enabled():
            return original_method(*args, **kwargs)
        
        start_time = time.time()
        
        try:
            result = original_method(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            assistant_id = None
            if hasattr(result, 'id'):
                assistant_id = result.id
            elif isinstance(result, dict):
                assistant_id = result.get('id')
            
            track_vapi_call(
                method_name=method_name,
                latency_ms=latency_ms,
                status="ok",
                assistant_id=assistant_id,
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            track_vapi_call(
                method_name=method_name,
                latency_ms=latency_ms,
                status="error",
                error=str(e),
            )
            
            raise
    
    return wrapper


def instrument_vapi() -> bool:
    """Instrument Vapi SDK."""
    try:
        from vapi import Vapi
    except ImportError:
        logger.debug("[llmobserve] Vapi SDK not installed - skipping")
        return False
    
    try:
        # Check if already instrumented
        if hasattr(Vapi, "_llmobserve_instrumented"):
            logger.debug("[llmobserve] Vapi already instrumented")
            return True
        
        original_init = Vapi.__init__
        
        @functools.wraps(original_init)
        def patched_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            
            # Patch calls methods
            if hasattr(self, 'calls'):
                calls_obj = self.calls
                
                for method_name in ['create', 'get', 'list']:
                    if hasattr(calls_obj, method_name):
                        original = getattr(calls_obj, method_name)
                        if not hasattr(original, '_llmobserve_instrumented'):
                            wrapped = create_calls_wrapper(original, f"calls.{method_name}")
                            setattr(calls_obj, method_name, wrapped)
                            wrapped._llmobserve_instrumented = True
            
            # Patch assistants methods
            if hasattr(self, 'assistants'):
                assistants_obj = self.assistants
                
                for method_name in ['create', 'get', 'list', 'update', 'delete']:
                    if hasattr(assistants_obj, method_name):
                        original = getattr(assistants_obj, method_name)
                        if not hasattr(original, '_llmobserve_instrumented'):
                            wrapped = create_management_wrapper(original, f"assistants.{method_name}")
                            setattr(assistants_obj, method_name, wrapped)
                            wrapped._llmobserve_instrumented = True
            
            # Patch phone_numbers methods
            if hasattr(self, 'phone_numbers'):
                phone_obj = self.phone_numbers
                
                for method_name in ['create', 'get', 'list', 'update', 'delete']:
                    if hasattr(phone_obj, method_name):
                        original = getattr(phone_obj, method_name)
                        if not hasattr(original, '_llmobserve_instrumented'):
                            wrapped = create_management_wrapper(original, f"phone_numbers.{method_name}")
                            setattr(phone_obj, method_name, wrapped)
                            wrapped._llmobserve_instrumented = True
        
        Vapi.__init__ = patched_init
        Vapi._llmobserve_instrumented = True
        
        logger.info("[llmobserve] Successfully instrumented Vapi SDK")
        return True
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to instrument Vapi: {e}", exc_info=True)
        return False

