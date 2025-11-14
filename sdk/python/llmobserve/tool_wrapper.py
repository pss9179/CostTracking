"""
Tool wrapping system for automatic tool span creation.

Provides wrap_tool() function and @tool() decorator for automatic
tool cost tracking without manual labeling.
"""
import functools
import inspect
import time
import uuid
from typing import Callable, Any, Optional
from llmobserve import context, buffer, config


def wrap_tool(func: Callable, name: Optional[str] = None) -> Callable:
    """
    Wrap any callable to automatically create tool spans.
    
    Idempotent: Never double-wraps (safe to call multiple times).
    
    Args:
        func: Callable to wrap (function/method/lambda/class with __call__ or .run)
        name: Optional tool name. If None, extracted from func.name, func.__name__, or func.__class__.__name__
    
    Returns:
        Wrapped callable that automatically tracks tool spans
    
    Usage:
        # Wrap a function
        search_tool = wrap_tool(search_function, name="web_search")
        
        # Wrap automatically (name from function)
        @wrap_tool
        def calculator(expr):
            return eval(expr)
    """
    # Idempotent check: Never double-wrap
    if getattr(func, "__llmobserve_wrapped__", False):
        return func
    
    # Extract tool name with priority order
    tool_name = (
        name
        or getattr(func, "name", None)  # Tool object's .name attribute
        or getattr(func, "__name__", None)  # Function name
        or func.__class__.__name__  # Class name
    )
    
    # Detect if function is async
    is_async = inspect.iscoroutinefunction(func)
    
    if is_async:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            return await _execute_with_tool_span_async(tool_name, func, args, kwargs)
        
        # Mark as wrapped
        async_wrapper.__llmobserve_wrapped__ = True
        async_wrapper.__llmobserve_original__ = func
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            return _execute_with_tool_span_sync(tool_name, func, args, kwargs)
        
        # Mark as wrapped
        sync_wrapper.__llmobserve_wrapped__ = True
        sync_wrapper.__llmobserve_original__ = func
        return sync_wrapper


def tool(name: str) -> Callable:
    """
    Decorator to mark a function as a tool.
    
    Automatically creates a tool:{name} span in the context stack.
    
    Usage:
        @tool("web_search")
        def search_web(query: str):
            # Tool logic here
            result = call_search_api(query)
            return result
    
    Args:
        name: Tool name (e.g., "web_search", "calculator", "code_executor")
    
    Returns:
        Decorated function that automatically tracks tool spans
    """
    def decorator(func: Callable) -> Callable:
        return wrap_tool(func, name=name)
    return decorator


def _execute_with_tool_span_sync(
    tool_name: str,
    func: Callable,
    args: tuple,
    kwargs: dict
) -> Any:
    """
    Sync version: Execute function within a tool span context.
    
    Handles span creation, stack management, error tracking, and cleanup.
    """
    # Get section stack
    stack = context._get_section_stack()
    
    # Ensure trace_id is initialized
    trace_id = context.get_trace_id()
    
    # Generate span_id for this tool
    span_id = str(uuid.uuid4())
    
    # Get parent_span_id from stack (if exists)
    parent_span_id = stack[-1]["span_id"] if stack else None
    
    # Create section label
    section_label = f"tool:{tool_name}"
    
    # Push tool entry onto stack
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
    
    # Capture args representation (truncate to avoid PII leaks)
    try:
        args_repr = str(args)[:100] if args else ""
        kwargs_repr = str(kwargs)[:100] if kwargs else ""
    except Exception:
        args_repr = "<unprintable>"
        kwargs_repr = "<unprintable>"
    
    try:
        # Execute the actual function
        result = func(*args, **kwargs)
        
        # Capture return type
        return_type = type(result).__name__ if result is not None else "None"
        
        return result
    except Exception as e:
        # Capture exception but re-raise to not break user code
        error_message = str(e)
        status = "error"
        return_type = "error"
        raise  # Re-raise exception to preserve user's error handling
    finally:
        # Calculate duration
        end_time = time.time()
        latency_ms = max(0.0, (end_time - start_time) * 1000)
        
        # Emit span event to collector
        try:
            if config.is_enabled():
                metadata = {
                    "tool_name": tool_name,
                    "func_name": getattr(func, "__name__", "unknown"),
                    "args_repr": args_repr,
                    "kwargs_repr": kwargs_repr,
                    "return_type": return_type if 'return_type' in locals() else "unknown"
                }
                
                if error_message:
                    metadata["error"] = error_message
                
                event = {
                    "id": str(uuid.uuid4()),
                    "trace_id": trace_id,
                    "run_id": context.get_run_id(),
                    "span_id": span_id,
                    "parent_span_id": parent_span_id,
                    "section": section_label,
                    "section_path": context.get_section_path(),
                    "span_type": "tool",
                    "provider": "internal",
                    "endpoint": "tool",
                    "model": None,
                    "cost_usd": 0.0,  # Tools themselves don't cost, only API calls inside
                    "latency_ms": latency_ms,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "status": status,
                    "customer_id": context.get_customer_id(),
                    "event_metadata": metadata,
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


async def _execute_with_tool_span_async(
    tool_name: str,
    func: Callable,
    args: tuple,
    kwargs: dict
) -> Any:
    """
    Async version: Execute function within a tool span context.
    
    Properly handles async functions without blocking the event loop.
    """
    # Get section stack
    stack = context._get_section_stack()
    
    # Ensure trace_id is initialized
    trace_id = context.get_trace_id()
    
    # Generate span_id for this tool
    span_id = str(uuid.uuid4())
    
    # Get parent_span_id from stack (if exists)
    parent_span_id = stack[-1]["span_id"] if stack else None
    
    # Create section label
    section_label = f"tool:{tool_name}"
    
    # Push tool entry onto stack
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
    
    # Capture args representation (truncate to avoid PII leaks)
    try:
        args_repr = str(args)[:100] if args else ""
        kwargs_repr = str(kwargs)[:100] if kwargs else ""
    except Exception:
        args_repr = "<unprintable>"
        kwargs_repr = "<unprintable>"
    
    try:
        # Execute the actual async function
        result = await func(*args, **kwargs)
        
        # Capture return type
        return_type = type(result).__name__ if result is not None else "None"
        
        return result
    except Exception as e:
        # Capture exception but re-raise to not break user code
        error_message = str(e)
        status = "error"
        return_type = "error"
        raise  # Re-raise exception to preserve user's error handling
    finally:
        # Calculate duration
        end_time = time.time()
        latency_ms = max(0.0, (end_time - start_time) * 1000)
        
        # Emit span event to collector
        try:
            if config.is_enabled():
                metadata = {
                    "tool_name": tool_name,
                    "func_name": getattr(func, "__name__", "unknown"),
                    "args_repr": args_repr,
                    "kwargs_repr": kwargs_repr,
                    "return_type": return_type if 'return_type' in locals() else "unknown"
                }
                
                if error_message:
                    metadata["error"] = error_message
                
                event = {
                    "id": str(uuid.uuid4()),
                    "trace_id": trace_id,
                    "run_id": context.get_run_id(),
                    "span_id": span_id,
                    "parent_span_id": parent_span_id,
                    "section": section_label,
                    "section_path": context.get_section_path(),
                    "span_type": "tool",
                    "provider": "internal",
                    "endpoint": "tool",
                    "model": None,
                    "cost_usd": 0.0,
                    "latency_ms": latency_ms,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "status": status,
                    "customer_id": context.get_customer_id(),
                    "event_metadata": metadata,
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

