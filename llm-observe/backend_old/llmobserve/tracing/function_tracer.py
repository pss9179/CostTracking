"""Function-level workflow tracing using workflow_manager (no spans on entry)."""

import functools
import inspect
import os
from typing import Any, Callable, Optional

from llmobserve.config import settings
from llmobserve.tracing.workflow_manager import (
    begin_function,
    end_function,
    end_workflow_span,
    get_current_workflow_span,
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
    # Default to "*" to wrap ALL user functions automatically (not just specific patterns)
    function_patterns = os.getenv(
        "LLMOBSERVE_FUNCTION_PATTERNS", "*"
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
    Wrap a function to track execution state (no spans on entry).
    
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
    """Wrap a synchronous function to track state only."""
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get function metadata
        func_name = func.__name__
        function_key = f"{module_name}.{func_name}"
        
        # Get function file path
        function_file = None
        try:
            if hasattr(func, "__code__") and func.__code__.co_filename:
                function_file = func.__code__.co_filename
        except Exception:
            pass
        
        # Track function entry (returns recursion depth) - pass metadata
        depth = begin_function(function_key, func_name, module_name, function_file)
        
        # Store metadata for lazy span creation
        # The workflow span will be created lazily on first API call
        # via workflow_manager.ensure_parent_for_first_api_call()
        
        try:
            # Execute the function
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            # Record exception on workflow span if it exists
            workflow_span = get_current_workflow_span()
            if workflow_span:
                try:
                    workflow_span.record_exception(e)
                    workflow_span.set_status(
                        __import__("opentelemetry").trace.Status(
                            __import__("opentelemetry").trace.StatusCode.ERROR, str(e)
                        )
                    )
                except Exception:
                    pass  # Best-effort: don't crash user app
            raise
        finally:
            # Track function exit
            remaining_depth = end_function(function_key)
            
            # End workflow span only when outermost call exits
            if remaining_depth == 0:
                try:
                    # Check if exception occurred
                    import sys
                    exc_info = sys.exc_info()
                    exception = exc_info[1] if exc_info[0] else None
                    end_workflow_span(exception)
                except Exception:
                    pass  # Best-effort: don't crash user app
    
    wrapper._llmobserve_wrapped = True
    wrapper._llmobserve_module = module_name
    wrapper._llmobserve_function_name = func_name
    wrapper._llmobserve_function_file = getattr(func, "__code__", None) and getattr(
        func.__code__, "co_filename", None
    )
    return wrapper


def wrap_async_function(func: Callable, module_name: str) -> Callable:
    """Wrap an asynchronous function to track state only."""
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Get function metadata
        func_name = func.__name__
        function_key = f"{module_name}.{func_name}"
        
        # Get function file path
        function_file = None
        try:
            if hasattr(func, "__code__") and func.__code__.co_filename:
                function_file = func.__code__.co_filename
        except Exception:
            pass
        
        # Track function entry (returns recursion depth) - pass metadata
        depth = begin_function(function_key, func_name, module_name, function_file)
        
        # Store metadata for lazy span creation
        # The workflow span will be created lazily on first API call
        # via workflow_manager.ensure_parent_for_first_api_call()
        
        try:
            # Execute the async function
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            # Record exception on workflow span if it exists
            workflow_span = get_current_workflow_span()
            if workflow_span:
                try:
                    workflow_span.record_exception(e)
                    workflow_span.set_status(
                        __import__("opentelemetry").trace.Status(
                            __import__("opentelemetry").trace.StatusCode.ERROR, str(e)
                        )
                    )
                except Exception:
                    pass  # Best-effort: don't crash user app
            raise
        finally:
            # Track function exit
            remaining_depth = end_function(function_key)
            
            # End workflow span only when outermost call exits
            if remaining_depth == 0:
                try:
                    # Check if exception occurred
                    import sys
                    exc_info = sys.exc_info()
                    exception = exc_info[1] if exc_info[0] else None
                    end_workflow_span(exception)
                except Exception:
                    pass  # Best-effort: don't crash user app
    
    wrapper._llmobserve_wrapped = True
    wrapper._llmobserve_module = module_name
    wrapper._llmobserve_function_name = func_name
    wrapper._llmobserve_function_file = getattr(func, "__code__", None) and getattr(
        func.__code__, "co_filename", None
    )
    return wrapper


# get_current_workflow_span is imported from workflow_manager above


def workflow_trace(func: Callable) -> Callable:
    """
    Decorator to manually wrap a function for workflow tracing.
    
    Usage:
        @workflow_trace
        def my_function():
            # This function will track execution state
            pass
    """
    # Get module name from function's module
    module_name = getattr(func, "__module__", "unknown")
    if module_name == "unknown":
        try:
            frame = inspect.currentframe()
            if frame and frame.f_back:
                module_name = frame.f_back.f_globals.get("__name__", "unknown")
        except Exception:
            pass
    
    return wrap_function(func, module_name)
