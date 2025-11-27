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
    stt_provider: Optional[str] = None,
    stt_model: Optional[str] = None,
    tts_provider: Optional[str] = None,
    tts_model: Optional[str] = None,
    llm_provider: Optional[str] = None,
    llm_model: Optional[str] = None,
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
        # Map segment type to provider/model info
        segment_providers = {
            "stt": (stt_provider or "vapi", stt_model),
            "llm": (llm_provider or "vapi", llm_model),
            "tts": (tts_provider or "vapi", tts_model),
            "telephony": ("vapi", None),  # Telephony is always Vapi/Twilio/Vonage
        }
        
        # Get usage metrics for recalculation
        llm_prompt_tokens = cost_breakdown.get("llm_prompt_tokens") or 0
        llm_completion_tokens = cost_breakdown.get("llm_completion_tokens") or 0
        tts_characters = cost_breakdown.get("tts_characters") or 0
        
        segments = [
            # (segment_type, cost, span_type, input_tokens, output_tokens)
            # STT: uses audio duration (stored in audio_duration_seconds field)
            ("stt", cost_breakdown.get("stt"), "stt_call", 0, 0),
            # LLM: uses prompt/completion tokens
            ("llm", cost_breakdown.get("llm"), "llm_call", int(llm_prompt_tokens), int(llm_completion_tokens)),
            # TTS: uses characters (stored in input_tokens for now, TODO: add tts_characters field)
            ("tts", cost_breakdown.get("tts"), "tts_call", int(tts_characters), 0),
            # Telephony: uses audio duration
            ("telephony", cost_breakdown.get("transport"), "telephony_call", 0, 0),
        ]
        
        for segment_type, segment_cost, span_type, input_tokens, output_tokens in segments:
            if segment_cost and segment_cost > 0:
                provider, model = segment_providers.get(segment_type, ("vapi", None))
                event = {
                    "id": str(uuid.uuid4()),
                    "run_id": context.get_run_id(),
                    "span_id": str(uuid.uuid4()),
                    "parent_span_id": context.get_current_span_id(),
                    "section": context.get_current_section(),
                    "section_path": context.get_section_path(),
                    "span_type": span_type,
                    "provider": provider.lower() if provider else "vapi",  # Normalize to lowercase
                    "endpoint": f"{method_name}.{segment_type}",
                    "model": model,
                    "cost_usd": segment_cost,
                    "latency_ms": latency_ms / 4 if latency_ms else 0,  # Estimate per segment
                    "input_tokens": input_tokens or 0,
                    "output_tokens": output_tokens or 0,
                    "status": status,
                    "tenant_id": config.get_tenant_id(),
                    "customer_id": context.get_customer_id(),
                    "voice_call_id": voice_call_id,
                    "audio_duration_seconds": call_duration_seconds,
                    "voice_segment_type": segment_type,
                    "voice_platform": "vapi",  # Cross-platform tracking
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
                "voice_platform": "vapi",  # Cross-platform tracking
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


def fetch_vapi_assistant(assistant_id: str, vapi_client: Any = None) -> Optional[dict]:
    """Fetch assistant configuration from Vapi API to get provider/model info.
    
    Returns assistant dict with transcriber, voice, and model fields.
    """
    if not assistant_id:
        return None
    
    try:
        # Try to use Vapi client if available
        if vapi_client and hasattr(vapi_client, 'assistants'):
            try:
                assistants_obj = vapi_client.assistants
                if hasattr(assistants_obj, 'get'):
                    assistant = assistants_obj.get(assistant_id)
                elif callable(assistants_obj):
                    assistant = assistants_obj(assistant_id)
                else:
                    assistant = None
                
                if assistant:
                    # Convert to dict if it's an object
                    if isinstance(assistant, dict):
                        return {
                            'transcriber': assistant.get('transcriber'),
                            'voice': assistant.get('voice'),
                            'model': assistant.get('model'),
                        }
                    elif hasattr(assistant, 'transcriber') or hasattr(assistant, 'voice') or hasattr(assistant, 'model'):
                        return {
                            'transcriber': getattr(assistant, 'transcriber', None),
                            'voice': getattr(assistant, 'voice', None),
                            'model': getattr(assistant, 'model', None),
                        }
            except Exception as e:
                logger.debug(f"[llmobserve] Failed to fetch assistant {assistant_id}: {e}")
                pass
    except Exception as e:
        logger.debug(f"[llmobserve] Error in fetch_vapi_assistant: {e}")
        pass
    
    return None


def extract_vapi_call_info(response: Any, vapi_client: Any = None) -> dict:
    """Extract call ID, duration, assistant ID, cost breakdown, transcript, and provider/model info from Vapi response.
    
    Vapi provides detailed costBreakdown with:
    - transport: Twilio/Vonage telephony cost
    - stt: Speech-to-text cost
    - llm: Language model cost  
    - tts: Text-to-speech cost
    - vapi: Vapi platform fee
    - total: Total cost
    - llmPromptTokens, llmCompletionTokens, ttsCharacters
    
    Also attempts to extract provider/model info from:
    - Call response (if available)
    - Assistant configuration (via assistant_id)
    """
    info = {
        'call_id': None,
        'duration': None,
        'assistant_id': None,
        'cost_breakdown': None,
        'transcript': None,
        'stt_provider': None,
        'stt_model': None,
        'tts_provider': None,
        'tts_model': None,
        'llm_provider': None,
        'llm_model': None,
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
            
            # Try to extract provider/model info from call response
            # Vapi may include assistant config or provider info in the call response
            if response.get('assistant'):
                assistant = response.get('assistant')
                if isinstance(assistant, dict):
                    # Extract STT provider/model
                    if assistant.get('transcriber'):
                        transcriber = assistant.get('transcriber')
                        if isinstance(transcriber, dict):
                            info['stt_provider'] = transcriber.get('provider')
                            info['stt_model'] = transcriber.get('model')
                    
                    # Extract TTS provider/model
                    if assistant.get('voice'):
                        voice = assistant.get('voice')
                        if isinstance(voice, dict):
                            info['tts_provider'] = voice.get('provider')
                            info['tts_model'] = voice.get('model') or voice.get('voiceId')
                    
                    # Extract LLM provider/model
                    if assistant.get('model'):
                        model_config = assistant.get('model')
                        if isinstance(model_config, dict):
                            info['llm_provider'] = model_config.get('provider')
                            info['llm_model'] = model_config.get('model')
                    elif assistant.get('llm'):
                        llm_config = assistant.get('llm')
                        if isinstance(llm_config, dict):
                            info['llm_provider'] = llm_config.get('provider')
                            info['llm_model'] = llm_config.get('model')
            
            # Also check direct fields on response (some APIs expose this directly)
            if response.get('transcriber'):
                transcriber = response.get('transcriber')
                if isinstance(transcriber, dict):
                    info['stt_provider'] = info['stt_provider'] or transcriber.get('provider')
                    info['stt_model'] = info['stt_model'] or transcriber.get('model')
            
            if response.get('voice'):
                voice = response.get('voice')
                if isinstance(voice, dict):
                    info['tts_provider'] = info['tts_provider'] or voice.get('provider')
                    info['tts_model'] = info['tts_model'] or voice.get('model') or voice.get('voiceId')
            
            if response.get('model'):
                model_config = response.get('model')
                if isinstance(model_config, dict):
                    info['llm_provider'] = info['llm_provider'] or model_config.get('provider')
                    info['llm_model'] = info['llm_model'] or model_config.get('model')
        
        # Try object attributes for provider/model
        if hasattr(response, 'assistant') and response.assistant:
            assistant = response.assistant
            try:
                if hasattr(assistant, 'transcriber') and assistant.transcriber:
                    if hasattr(assistant.transcriber, 'provider'):
                        info['stt_provider'] = assistant.transcriber.provider
                    if hasattr(assistant.transcriber, 'model'):
                        info['stt_model'] = assistant.transcriber.model
                
                if hasattr(assistant, 'voice') and assistant.voice:
                    if hasattr(assistant.voice, 'provider'):
                        info['tts_provider'] = assistant.voice.provider
                    if hasattr(assistant.voice, 'model'):
                        info['tts_model'] = assistant.voice.model
                    elif hasattr(assistant.voice, 'voiceId'):
                        info['tts_model'] = assistant.voice.voiceId
                
                if hasattr(assistant, 'model') and assistant.model:
                    if hasattr(assistant.model, 'provider'):
                        info['llm_provider'] = assistant.model.provider
                    if hasattr(assistant.model, 'model'):
                        info['llm_model'] = assistant.model.model
                elif hasattr(assistant, 'llm') and assistant.llm:
                    if hasattr(assistant.llm, 'provider'):
                        info['llm_provider'] = assistant.llm.provider
                    if hasattr(assistant.llm, 'model'):
                        info['llm_model'] = assistant.llm.model
            except:
                pass
        
        # If we have assistant_id but no assistant object, try to fetch it
        if info['assistant_id'] and not any([info['stt_provider'], info['tts_provider'], info['llm_provider']]):
            assistant_config = fetch_vapi_assistant(info['assistant_id'], vapi_client)
            if assistant_config:
                # Extract from fetched assistant
                if assistant_config.get('transcriber'):
                    transcriber = assistant_config['transcriber']
                    if isinstance(transcriber, dict):
                        info['stt_provider'] = transcriber.get('provider')
                        info['stt_model'] = transcriber.get('model')
                    elif hasattr(transcriber, 'provider'):
                        info['stt_provider'] = transcriber.provider
                        info['stt_model'] = getattr(transcriber, 'model', None)
                
                if assistant_config.get('voice'):
                    voice = assistant_config['voice']
                    if isinstance(voice, dict):
                        info['tts_provider'] = voice.get('provider')
                        info['tts_model'] = voice.get('model') or voice.get('voiceId')
                    elif hasattr(voice, 'provider'):
                        info['tts_provider'] = voice.provider
                        info['tts_model'] = getattr(voice, 'model', None) or getattr(voice, 'voiceId', None)
                
                if assistant_config.get('model'):
                    model_config = assistant_config['model']
                    if isinstance(model_config, dict):
                        info['llm_provider'] = model_config.get('provider')
                        info['llm_model'] = model_config.get('model')
                    elif hasattr(model_config, 'provider'):
                        info['llm_provider'] = model_config.provider
                        info['llm_model'] = getattr(model_config, 'model', None)
                
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
            
            # Get Vapi client instance (first arg is usually self)
            vapi_client = args[0] if args else None
            
            info = extract_vapi_call_info(result, vapi_client)
            
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
                stt_provider=info.get('stt_provider'),
                stt_model=info.get('stt_model'),
                tts_provider=info.get('tts_provider'),
                tts_model=info.get('tts_model'),
                llm_provider=info.get('llm_provider'),
                llm_model=info.get('llm_model'),
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

