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
_section_stack_var: contextvars.ContextVar[List[Dict[str, Any]]] = contextvars.ContextVar("section_stack", default=None)


def _ensure_run_id() -> str:
    """Ensure run_id is initialized."""
    run_id = _run_id_var.get()
    if run_id is None:
        run_id = str(uuid.uuid4())
        _run_id_var.set(run_id)
    return run_id


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


def export() -> Dict[str, Any]:
    """
    Export current context for serialization (e.g., for Celery/background workers).
    
    Returns:
        Dictionary with run_id, customer_id, and section_stack
    """
    return {
        "run_id": _run_id_var.get(),
        "customer_id": _customer_id_var.get(),
        "section_stack": _section_stack_var.get() or [],
    }


def import_context(data: Dict[str, Any]) -> None:
    """
    Import context from dictionary (e.g., from Celery/background workers).
    
    Args:
        data: Dictionary with run_id, customer_id, and section_stack
    
    Example:
        >>> context_data = context.export()
        >>> # In worker:
        >>> context.import_context(context_data)
    """
    if "run_id" in data and data["run_id"]:
        _run_id_var.set(data["run_id"])
    
    if "customer_id" in data:
        _customer_id_var.set(data.get("customer_id"))
    
    if "section_stack" in data:
        _section_stack_var.set(data["section_stack"] or [])

