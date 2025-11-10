"""Function-level workflow tracing using contextvars."""

import contextvars
import functools
import inspect
import os
import time
from typing import Any, Callable, Optional

from opentelemetry import trace

from llmobserve.config import settings

tracer = trace.get_tracer(__name__)

# Context variables for workflow tracking
current_workflow_span: contextvars.ContextVar[Optional[trace.Span]] = contextvars.ContextVar(
    "current_workflow_span", default=None
)
workflow_function_name: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "workflow_function_name", default=None
)
workflow_start_time: contextvars.ContextVar[Optional[float]] = contextvars.ContextVar(
    "workflow_start_time", default=None
)
workflow_call_stack: contextvars.ContextVar[list] = contextvars.ContextVar(
    "workflow_call_stack", default=[]
)


def should_wrap_function(func: Callable, module_name: str) -> bool:
    """
    Determine if a function should be wrapped for workflow tracing.
    
    Args:
        func: Function to check
        module_name: Name of the module containing the function
    
    Returns:
        True if function should be wrapped, False otherwise
    """
    # Skip if already wrapped
    if getattr(func, "_llmobserve_wrapped", False):
        return False
    
    # Skip magic methods (unless explicitly enabled)
    if func.__name__.startswith("__") and func.__name__ not in ("__call__", "__init__"):
        return False
    
    # Skip if function is in stdlib
    if module_name.startswith(("_", "sys", "os", "json", "builtins")):
        return False
    
    # Check if module is in site-packages (third-party)
    import sys
    for path in sys.path:
        if "site-packages" in path and module_name in sys.modules:
            mod = sys.modules[module_name]
            if hasattr(mod, "__file__") and mod.__file__:
                if "site-packages" in mod.__file__:
                    return False
    
    # Check function patterns from config
    function_patterns = os.getenv(
        "LLMOBSERVE_FUNCTION_PATTERNS", "*_workflow,*_agent,*_handler"
    ).split(",")
    
    # If pattern is "*" or empty, wrap all user functions
    if "*" in function_patterns or not function_patterns or function_patterns == [""]:
        return True
    
    # Check if function name matches any pattern
    for pattern in function_patterns:
        pattern = pattern.strip()
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            if func.__name__.startswith(prefix):
                return True
        elif pattern in func.__name__:
            return True
    
    return False


def wrap_function(func: Callable, module_name: str) -> Callable:
    """
    Wrap a function to create workflow spans on entry.
    
    Args:
        func: Function to wrap
        module_name: Name of the module containing the function
    
    Returns:
        Wrapped function
    """
    if inspect.iscoroutinefunction(func):
        return wrap_async_function(func, module_name)
    else:
        return wrap_sync_function(func, module_name)


def wrap_sync_function(func: Callable, module_name: str) -> Callable:
    """Wrap a synchronous function."""
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get function metadata
        func_name = func.__name__
        workflow_name = f"workflow.{func_name}"
        
        # Get current workflow span (for nested calls)
        parent_workflow = current_workflow_span.get()
        
        # Create workflow span on function entry (before any code runs)
        # This ensures the span exists before any API calls happen
        with tracer.start_as_current_span(workflow_name) as workflow_span:
            # Set workflow attributes
            workflow_span.set_attribute("function.name", func_name)
            workflow_span.set_attribute("function.module", module_name)
            workflow_span.set_attribute("workflow.type", "auto")
            
            # Try to get file path
            try:
                if hasattr(func, "__code__") and func.__code__.co_filename:
                    workflow_span.set_attribute("function.file", func.__code__.co_filename)
            except Exception:
                pass
            
            # Set workflow context
            token_span = current_workflow_span.set(workflow_span)
            token_name = workflow_function_name.set(func_name)
            token_time = workflow_start_time.set(time.time())
            
            # Update call stack
            stack = workflow_call_stack.get().copy()
            stack.append(workflow_span)
            token_stack = workflow_call_stack.set(stack)
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                # Record exception on span
                workflow_span.record_exception(e)
                workflow_span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
            finally:
                # Always restore context (even on exceptions)
                current_workflow_span.reset(token_span)
                workflow_function_name.reset(token_name)
                workflow_start_time.reset(token_time)
                workflow_call_stack.reset(token_stack)
                
                # Restore parent workflow if it existed
                if parent_workflow:
                    current_workflow_span.set(parent_workflow)
    
    wrapper._llmobserve_wrapped = True
    return wrapper


def wrap_async_function(func: Callable, module_name: str) -> Callable:
    """Wrap an asynchronous function."""
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Get function metadata
        func_name = func.__name__
        workflow_name = f"workflow.{func_name}"
        
        # Get current workflow span (for nested calls)
        parent_workflow = current_workflow_span.get()
        
        # Create workflow span on function entry (before any code runs)
        # This ensures the span exists before any API calls happen
        with tracer.start_as_current_span(workflow_name) as workflow_span:
            # Set workflow attributes
            workflow_span.set_attribute("function.name", func_name)
            workflow_span.set_attribute("function.module", module_name)
            workflow_span.set_attribute("workflow.type", "auto")
            
            # Try to get file path
            try:
                if hasattr(func, "__code__") and func.__code__.co_filename:
                    workflow_span.set_attribute("function.file", func.__code__.co_filename)
            except Exception:
                pass
            
            # Set workflow context
            token_span = current_workflow_span.set(workflow_span)
            token_name = workflow_function_name.set(func_name)
            token_time = workflow_start_time.set(time.time())
            
            # Update call stack
            stack = workflow_call_stack.get().copy()
            stack.append(workflow_span)
            token_stack = workflow_call_stack.set(stack)
            
            try:
                # Execute the async function
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                # Record exception on span
                workflow_span.record_exception(e)
                workflow_span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
            finally:
                # Always restore context (even on exceptions)
                current_workflow_span.reset(token_span)
                workflow_function_name.reset(token_name)
                workflow_start_time.reset(token_time)
                workflow_call_stack.reset(token_stack)
                
                # Restore parent workflow if it existed
                if parent_workflow:
                    current_workflow_span.set(parent_workflow)
    
    wrapper._llmobserve_wrapped = True
    return wrapper


def get_current_workflow_span() -> Optional[trace.Span]:
    """Get the current workflow span from contextvars."""
    return current_workflow_span.get()


def workflow_trace(func: Callable) -> Callable:
    """
    Decorator to manually wrap a function for workflow tracing.
    
    Usage:
        @workflow_trace
        def my_function():
            # This function will create a workflow span
            pass
    """
    # Get module name from function's module
    module_name = getattr(func, "__module__", "unknown")
    if module_name == "unknown":
        try:
            import inspect
            frame = inspect.currentframe()
            if frame and frame.f_back:
                module_name = frame.f_back.f_globals.get("__name__", "unknown")
        except Exception:
            pass
    
    return wrap_function(func, module_name)

