"""
ContextVar-based context management for sections, spans, and run IDs.
Async-safe with support for hierarchical tracing.
"""
import contextvars
import uuid
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

# ContextVar storage for async safety
_run_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("run_id", default=None)
_tenant_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("tenant_id", default=None)
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


def get_tenant_id() -> Optional[str]:
    """Get the current tenant ID."""
    return _tenant_id_var.get()


def set_tenant_id(tenant_id: Optional[str] = None) -> None:
    """
    Set the tenant ID for all subsequent events.
    
    Args:
        tenant_id: Tenant identifier (e.g., "acme", "beta-corp")
    """
    _tenant_id_var.set(tenant_id)


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
    
    Returns the most recent section from the stack, or "default" if none.
    For backward compatibility with flat event model.
    """
    stack = _get_section_stack()
    return stack[-1]["label"] if stack else "default"


def get_section_path() -> str:
    """
    Get the full hierarchical section path.
    
    Returns:
        Full path like "agent:researcher/tool:web_search/step:analyze" or "default" if no sections.
    """
    stack = _get_section_stack()
    if not stack:
        return "default"
    return "/".join(item["label"] for item in stack)


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
    
    try:
        yield
    finally:
        # Pop section from stack (only if it's still the top)
        if stack and stack[-1]["label"] == name:
            stack.pop()

