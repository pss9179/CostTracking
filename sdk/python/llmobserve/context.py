"""
ContextVar-based context management for sections, spans, and run IDs.
Async-safe with support for hierarchical tracing.
"""
import contextvars
import time
import uuid
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

# ContextVar storage for async safety
_run_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("run_id", default=None)
_customer_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("customer_id", default=None)
_tenant_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("tenant_id", default=None)
_section_stack_var: contextvars.ContextVar[List[Dict[str, Any]]] = contextvars.ContextVar("section_stack", default=None)
_trace_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("trace_id", default=None)
# Voice AI tracking
_voice_call_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("voice_call_id", default=None)
_voice_call_start_var: contextvars.ContextVar[Optional[float]] = contextvars.ContextVar("voice_call_start", default=None)
_voice_platform_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("voice_platform", default=None)


def _ensure_run_id() -> str:
    """Ensure run_id is initialized."""
    run_id = _run_id_var.get()
    if run_id is None:
        run_id = str(uuid.uuid4())
        _run_id_var.set(run_id)
    return run_id


def _ensure_trace_id() -> str:
    """Ensure trace_id is initialized (generated at first span)."""
    trace_id = _trace_id_var.get()
    if trace_id is None:
        trace_id = str(uuid.uuid4())
        _trace_id_var.set(trace_id)
    return trace_id


def _get_section_stack() -> List[Dict[str, Any]]:
    """Get section stack, initializing if needed."""
    stack = _section_stack_var.get()
    if stack is None:
        stack = []
        _section_stack_var.set(stack)
    return stack


def get_run_id() -> str:
    """Get the current run ID."""
    return _ensure_run_id()


def set_run_id(run_id: Optional[str] = None) -> None:
    """
    Set a custom run ID.
    
    Args:
        run_id: Custom run ID, or None to auto-generate a new one
    """
    _run_id_var.set(run_id if run_id else str(uuid.uuid4()))


def get_customer_id() -> Optional[str]:
    """Get the current customer ID."""
    return _customer_id_var.get()


def set_customer_id(customer_id: Optional[str] = None) -> None:
    """
    Set the customer ID for all subsequent events.
    
    Args:
        customer_id: Customer/end-user identifier (e.g., "user_123", "enduser_42")
    """
    _customer_id_var.set(customer_id)


def get_tenant_id() -> Optional[str]:
    """Get the current tenant ID."""
    tenant_id = _tenant_id_var.get()
    if tenant_id is None:
        # Fallback to config if not set in context
        from llmobserve import config
        tenant_id = config.get_tenant_id()
    return tenant_id


def set_tenant_id(tenant_id: Optional[str] = None) -> None:
    """
    Set the tenant ID for all subsequent events.
    
    Args:
        tenant_id: Tenant identifier (e.g., "acme", "real_user_test")
    """
    _tenant_id_var.set(tenant_id)


def get_trace_id() -> str:
    """Get the current trace ID (generated at first span if not set)."""
    return _ensure_trace_id()


def set_trace_id(trace_id: Optional[str] = None) -> None:
    """
    Set a custom trace ID for distributed tracing.
    
    Args:
        trace_id: Trace identifier, or None to auto-generate a new one
    """
    _trace_id_var.set(trace_id if trace_id else str(uuid.uuid4()))


def get_current_section() -> str:
    """
    Get the current section label (last segment only).
    
    Returns the most recent section from the stack, or auto-detects from call stack.
    For backward compatibility with flat event model.
    """
    stack = _get_section_stack()
    if stack:
        return stack[-1]["label"]
    
    # Auto-detect agent if no section is set and auto-detection is enabled
    from llmobserve import config
    if config.get_auto_detect_agents():
        from llmobserve.agent_detector import detect_agent_from_stack
        detected = detect_agent_from_stack()
        if detected:
            return detected
    
    return "default"


def get_section_path() -> str:
    """
    Get the full hierarchical section path.
    
    Returns:
        Full path like "agent:researcher/tool:web_search/step:analyze" or auto-detected path.
    """
    stack = _get_section_stack()
    if stack:
        return "/".join(item["label"] for item in stack)
    
    # Auto-detect hierarchical context if no sections are set and auto-detection is enabled
    from llmobserve import config
    if config.get_auto_detect_agents():
        from llmobserve.agent_detector import detect_hierarchical_context
        detected = detect_hierarchical_context()
        if detected:
            return "/".join(detected)
    
    return "default"


def get_current_span_id() -> Optional[str]:
    """
    Get the span_id of the current active section.
    
    Returns:
        span_id of the current section, or None if no active sections.
    """
    stack = _get_section_stack()
    return stack[-1]["span_id"] if stack else None


def get_parent_span_id() -> Optional[str]:
    """
    Get the parent_span_id of the current active section.
    
    Returns:
        parent_span_id of the current section, or None if no parent.
    """
    stack = _get_section_stack()
    return stack[-1]["parent_span_id"] if stack else None


@contextmanager
def section(name: str):
    """
    Context manager to label a section of code with hierarchical span tracking.
    
    Supports semantic labels for agents, tools, and steps:
    - agent:<name> → for orchestrators or autonomous agents
    - tool:<name>  → for external API or function calls
    - step:<name>  → for multi-step logic or workflows
    
    Usage:
        with section("agent:researcher"):
            with section("tool:web_search"):
                # Your code here
                pass
    
    Args:
        name: Section label (e.g., "agent:researcher", "tool:web_search", "step:analyze")
    """
    from llmobserve import buffer
    
    stack = _get_section_stack()
    
    # Generate span_id for this section
    span_id = str(uuid.uuid4())
    
    # Get parent_span_id from previous stack top (if exists)
    parent_span_id = stack[-1]["span_id"] if stack else None
    
    # Push section entry onto stack
    section_entry = {
        "label": name,
        "span_id": span_id,
        "parent_span_id": parent_span_id
    }
    stack.append(section_entry)
    
    # Record start time
    start_time = time.time()
    
    # Track exception state
    error_message = None
    status = "ok"
    
    try:
        yield
    except Exception as e:
        # Capture exception but re-raise to not break user code
        error_message = str(e)
        status = "error"
        raise  # Re-raise exception to preserve user's error handling
    finally:
        # Calculate duration with clock skew guard
        end_time = time.time()
        latency_ms = max(0.0, (end_time - start_time) * 1000)  # Prevent negative latencies
        
        # Emit span event to collector
        try:
            from llmobserve.config import is_enabled
            if is_enabled():
                event = {
                    "id": str(uuid.uuid4()),  # Unique event ID
                    "run_id": get_run_id(),
                    "span_id": span_id,
                    "parent_span_id": parent_span_id,
                    "section": name,
                    "section_path": get_section_path(),
                    "span_type": "section",  # Mark as section span (not API call)
                    "provider": "internal",  # Sections are internal, not external API calls
                    "endpoint": "span",
                    "model": None,
                    "cost_usd": 0.0,  # Sections themselves don't cost, only API calls inside
                    "latency_ms": latency_ms,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "status": status,
                    "customer_id": get_customer_id(),
                    "event_metadata": {"error": error_message} if error_message else None,
                    "is_streaming": False,  # Add required fields
                    "stream_cancelled": False,
                    "tenant_id": config.get_tenant_id(),  # Add tenant_id
                }
                buffer.add_event(event)
        except Exception:
            pass  # Fail silently to not break user code
        
        # Pop section from stack in separate try/finally for safety
        try:
            if stack and len(stack) > 0 and stack[-1].get("span_id") == span_id:
                stack.pop()
        except (IndexError, KeyError):
            # Stack corruption - log but don't crash
            pass


def get_voice_call_id() -> Optional[str]:
    """Get the current voice call ID for grouping STT + LLM + TTS events."""
    return _voice_call_id_var.get()


def set_voice_call_id(voice_call_id: Optional[str] = None) -> None:
    """
    Set the voice call ID for grouping voice pipeline events.
    
    Args:
        voice_call_id: Unique identifier for the voice call, or None to auto-generate
    """
    _voice_call_id_var.set(voice_call_id if voice_call_id else str(uuid.uuid4()))


def get_voice_platform() -> Optional[str]:
    """Get the current voice platform (vapi, retell, diy, etc.)."""
    return _voice_platform_var.get()


def set_voice_platform(platform: Optional[str] = None) -> None:
    """
    Set the voice platform for cross-platform tracking.
    
    Args:
        platform: Platform identifier ('vapi', 'retell', 'bland', 'livekit', 'diy', 'direct')
    """
    _voice_platform_var.set(platform)


@contextmanager
def voice_call(call_id: Optional[str] = None, customer_id: Optional[str] = None, platform: Optional[str] = None):
    """
    Context manager to group all voice pipeline events (STT + LLM + TTS) as one call.
    
    This allows you to track the complete cost and latency breakdown of a voice
    agent interaction, seeing exactly how much each component (STT, LLM, TTS,
    telephony) contributed to the total.
    
    Usage:
        with voice_call() as call_id:
            # STT event will be tagged with this call_id
            transcript = transcribe_audio(audio)
            
            # LLM event will be tagged with this call_id  
            response = llm.generate(transcript)
            
            # TTS event will be tagged with this call_id
            audio_out = synthesize_speech(response)
    
    Args:
        call_id: Custom call ID (auto-generated if None)
        customer_id: Optional customer ID to associate with this call
        platform: Voice platform ('vapi', 'retell', 'bland', 'livekit', 'diy', 'direct')
    
    Yields:
        The voice call ID being used
    """
    from llmobserve import buffer
    
    # Generate or use provided call_id
    actual_call_id = call_id if call_id else str(uuid.uuid4())
    
    # Store previous values
    previous_call_id = _voice_call_id_var.get()
    previous_customer_id = _customer_id_var.get()
    previous_call_start = _voice_call_start_var.get()
    previous_platform = _voice_platform_var.get()
    
    # Set new values
    _voice_call_id_var.set(actual_call_id)
    _voice_call_start_var.set(time.time())
    
    if customer_id:
        _customer_id_var.set(customer_id)
    
    if platform:
        _voice_platform_var.set(platform)
    
    # Track status
    status = "ok"
    error_message = None
    
    try:
        yield actual_call_id
    except Exception as e:
        status = "error"
        error_message = str(e)
        raise
    finally:
        # Calculate total call duration
        call_start = _voice_call_start_var.get()
        call_duration_ms = max(0.0, (time.time() - call_start) * 1000) if call_start else 0.0
        
        # Emit voice call summary event
        try:
            from llmobserve.config import is_enabled, get_tenant_id
            if is_enabled():
                event = {
                    "id": str(uuid.uuid4()),
                    "run_id": get_run_id(),
                    "span_id": str(uuid.uuid4()),
                    "parent_span_id": get_current_span_id(),
                    "section": get_current_section(),
                    "section_path": get_section_path(),
                    "span_type": "voice_call",
                    "provider": "voice_pipeline",
                    "endpoint": "call_summary",
                    "model": None,
                    "cost_usd": 0.0,  # Actual costs are in child events
                    "latency_ms": call_duration_ms,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "status": status,
                    "customer_id": get_customer_id(),
                    "voice_call_id": actual_call_id,
                    "audio_duration_seconds": call_duration_ms / 1000.0,
                    "voice_segment_type": "call_summary",
                    "voice_platform": platform or previous_platform,  # Cross-platform tracking
                    "event_metadata": {
                        "error": error_message,
                        "total_duration_ms": call_duration_ms,
                    } if error_message else {"total_duration_ms": call_duration_ms},
                    "is_streaming": False,
                    "stream_cancelled": False,
                    "tenant_id": get_tenant_id(),
                }
                buffer.add_event(event)
        except Exception:
            pass  # Fail silently
        
        # Restore previous values
        _voice_call_id_var.set(previous_call_id)
        _voice_call_start_var.set(previous_call_start)
        _voice_platform_var.set(previous_platform)
        if customer_id:
            _customer_id_var.set(previous_customer_id)


@contextmanager
def diy_voice_call(call_id: Optional[str] = None, customer_id: Optional[str] = None):
    """
    Convenience context manager for DIY voice calls (sets platform='diy').
    
    Use this when you're orchestrating your own voice pipeline with separate
    STT, LLM, and TTS providers (e.g., Deepgram + OpenAI + ElevenLabs).
    
    Usage:
        with diy_voice_call() as call_id:
            # STT with Deepgram
            transcript = deepgram.transcribe(audio)
            
            # LLM with OpenAI
            response = openai.chat.completions.create(...)
            
            # TTS with ElevenLabs
            audio_out = elevenlabs.generate(transcript)
    
    Args:
        call_id: Custom call ID (auto-generated if None)
        customer_id: Optional customer ID to associate with this call
    
    Yields:
        The voice call ID being used
    """
    with voice_call(call_id=call_id, customer_id=customer_id, platform="diy") as call_id:
        yield call_id


def export() -> Dict[str, Any]:
    """
    Export current context for serialization (e.g., for Celery/background workers).
    
    Returns:
        Dictionary with trace_id, run_id, customer_id, voice_call_id, and section_stack
    """
    return {
        "trace_id": _trace_id_var.get(),
        "run_id": _run_id_var.get(),
        "customer_id": _customer_id_var.get(),
        "voice_call_id": _voice_call_id_var.get(),
        "section_stack": _section_stack_var.get() or [],
    }


def import_context(data: Dict[str, Any]) -> None:
    """
    Import context from dictionary (e.g., from Celery/background workers).
    
    Args:
        data: Dictionary with trace_id, run_id, customer_id, voice_call_id, and section_stack
    
    Example:
        >>> context_data = context.export()
        >>> # In worker:
        >>> context.import_context(context_data)
    """
    if "trace_id" in data and data["trace_id"]:
        _trace_id_var.set(data["trace_id"])
    
    if "run_id" in data and data["run_id"]:
        _run_id_var.set(data["run_id"])
    
    if "customer_id" in data:
        _customer_id_var.set(data.get("customer_id"))
    
    if "voice_call_id" in data:
        _voice_call_id_var.set(data.get("voice_call_id"))
    
    if "section_stack" in data:
        _section_stack_var.set(data["section_stack"] or [])

