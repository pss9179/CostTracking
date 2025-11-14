"""
Agent decorator for automatic agent span creation.

Provides @agent() decorator that wraps agent entrypoint functions
and automatically creates agent spans in the context stack.
"""
import functools
import inspect
import time
import uuid
from typing import Callable, Any, Optional
from llmobserve import context, buffer, config


def agent(name: str) -> Callable:
    """
    Decorator to mark a function as an agent entrypoint.
    
    Automatically creates an agent:{name} span in the context stack,
    enabling hierarchical cost tracking without manual labeling.
    
    Usage:
        @agent("researcher")
        def my_research_agent(query: str):
            # Agent logic here
            result = call_tools_and_llms(query)
            return result
    
    Args:
        name: Agent name (e.g., "researcher", "planner", "executor")
    
    Returns:
        Decorated function that automatically tracks agent spans
    """
    def decorator(func: Callable) -> Callable:
        # Detect if function is async
        is_async = inspect.iscoroutinefunction(func)
        
        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                return await _execute_with_agent_span_async(name, func, args, kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                return _execute_with_agent_span_sync(name, func, args, kwargs)
            return sync_wrapper
    
    return decorator


def _execute_with_agent_span_sync(
    agent_name: str,
    func: Callable,
    args: tuple,
    kwargs: dict
) -> Any:
    """
    Sync version: Execute function within an agent span context.
    
    Handles span creation, stack management, error tracking, and cleanup.
    """
    # Get section stack
    stack = context._get_section_stack()
    
    # Ensure trace_id is initialized
    trace_id = context.get_trace_id()
    
    # Generate span_id for this agent
    span_id = str(uuid.uuid4())
    
    # Get parent_span_id from stack (if exists)
    parent_span_id = stack[-1]["span_id"] if stack else None
    
    # Create section label
    section_label = f"agent:{agent_name}"
    
    # Push agent entry onto stack
    section_entry = {
        "label": section_label,
        "span_id": span_id,
        "parent_span_id": parent_span_id
    }
    stack.append(section_entry)
    
    # Record start time
    start_time = time.time()
    
    # Track exception state
    error_message = None
    status = "ok"
    result = None
    
    try:
        # Execute the actual function
        result = func(*args, **kwargs)
        return result
    except Exception as e:
        # Capture exception but re-raise to not break user code
        error_message = str(e)
        status = "error"
        raise  # Re-raise exception to preserve user's error handling
    finally:
        # Calculate duration
        end_time = time.time()
        latency_ms = max(0.0, (end_time - start_time) * 1000)
        
        # Emit span event to collector
        try:
            if config.is_enabled():
                event = {
                    "id": str(uuid.uuid4()),
                    "trace_id": trace_id,
                    "run_id": context.get_run_id(),
                    "span_id": span_id,
                    "parent_span_id": parent_span_id,
                    "section": section_label,
                    "section_path": context.get_section_path(),
                    "span_type": "agent",
                    "provider": "internal",
                    "endpoint": "agent",
                    "model": None,
                    "cost_usd": 0.0,  # Agents themselves don't cost, only tools/LLMs inside
                    "latency_ms": latency_ms,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "status": status,
                    "customer_id": context.get_customer_id(),
                    "event_metadata": {"error": error_message, "agent_name": agent_name} if error_message else {"agent_name": agent_name},
                    "is_streaming": False,
                    "stream_cancelled": False,
                    "tenant_id": context.get_tenant_id(),
                }
                buffer.add_event(event)
        except Exception:
            pass  # Fail silently to not break user code
        
        # Pop section from stack
        try:
            if stack and len(stack) > 0 and stack[-1].get("span_id") == span_id:
                stack.pop()
        except (IndexError, KeyError):
            # Stack corruption - log but don't crash
            pass


async def _execute_with_agent_span_async(
    agent_name: str,
    func: Callable,
    args: tuple,
    kwargs: dict
) -> Any:
    """
    Async version of _execute_with_agent_span.
    
    Properly handles async functions without blocking the event loop.
    """
    # Get section stack
    stack = context._get_section_stack()
    
    # Ensure trace_id is initialized
    trace_id = context.get_trace_id()
    
    # Generate span_id for this agent
    span_id = str(uuid.uuid4())
    
    # Get parent_span_id from stack (if exists)
    parent_span_id = stack[-1]["span_id"] if stack else None
    
    # Create section label
    section_label = f"agent:{agent_name}"
    
    # Push agent entry onto stack
    section_entry = {
        "label": section_label,
        "span_id": span_id,
        "parent_span_id": parent_span_id
    }
    stack.append(section_entry)
    
    # Record start time
    start_time = time.time()
    
    # Track exception state
    error_message = None
    status = "ok"
    result = None
    
    try:
        # Execute the actual async function
        result = await func(*args, **kwargs)
        return result
    except Exception as e:
        # Capture exception but re-raise to not break user code
        error_message = str(e)
        status = "error"
        raise  # Re-raise exception to preserve user's error handling
    finally:
        # Calculate duration
        end_time = time.time()
        latency_ms = max(0.0, (end_time - start_time) * 1000)
        
        # Emit span event to collector
        try:
            if config.is_enabled():
                event = {
                    "id": str(uuid.uuid4()),
                    "trace_id": trace_id,
                    "run_id": context.get_run_id(),
                    "span_id": span_id,
                    "parent_span_id": parent_span_id,
                    "section": section_label,
                    "section_path": context.get_section_path(),
                    "span_type": "agent",
                    "provider": "internal",
                    "endpoint": "agent",
                    "model": None,
                    "cost_usd": 0.0,
                    "latency_ms": latency_ms,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "status": status,
                    "customer_id": context.get_customer_id(),
                    "event_metadata": {"error": error_message, "agent_name": agent_name} if error_message else {"agent_name": agent_name},
                    "is_streaming": False,
                    "stream_cancelled": False,
                    "tenant_id": context.get_tenant_id(),
                }
                buffer.add_event(event)
        except Exception:
            pass  # Fail silently to not break user code
        
        # Pop section from stack
        try:
            if stack and len(stack) > 0 and stack[-1].get("span_id") == span_id:
                stack.pop()
        except (IndexError, KeyError):
            # Stack corruption - log but don't crash
            pass

