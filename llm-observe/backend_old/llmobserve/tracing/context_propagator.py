"""Context propagation for threading, async, multiprocessing, and Celery."""

import asyncio
import contextvars
import functools
from typing import Any, Callable, Optional

from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from llmobserve.tracing.workflow_manager import (
    _current_workflow_span,
    _workflow_function_name,
    _workflow_start_time,
    _workflow_state,
    get_workflow_state,
)

propagator = TraceContextTextMapPropagator()


def _copy_workflow_context() -> dict:
    """Copy current workflow context for propagation."""
    ctx = {}
    
    # Copy workflow span context
    workflow_span = _current_workflow_span.get()
    if workflow_span:
        span_context = workflow_span.get_span_context()
        if span_context.is_valid:
            carrier = {}
            propagator.inject(carrier)
            ctx["trace_context"] = carrier
    
    # Copy other context vars
    ctx["workflow_function_name"] = _workflow_function_name.get()
    ctx["workflow_start_time"] = _workflow_start_time.get()
    
    # Copy workflow state
    try:
        state = get_workflow_state()
        ctx["workflow_state"] = {
            "call_depth": state.call_depth.copy(),
            "function_name": state.function_name,
            "start_time": state.start_time,
        }
    except Exception:
        ctx["workflow_state"] = {}
    
    return ctx


def _restore_workflow_context(ctx: dict) -> None:
    """Restore workflow context from copied context."""
    # Restore trace context
    if "trace_context" in ctx:
        carrier = ctx["trace_context"]
        try:
            extracted_context = propagator.extract(carrier)
            if extracted_context:
                # Set the extracted context as current
                trace.set_tracer_provider(trace.get_tracer_provider())
        except Exception:
            pass  # Best-effort: don't crash
    
    # Restore other context vars
    if ctx.get("workflow_function_name"):
        _workflow_function_name.set(ctx["workflow_function_name"])
    if ctx.get("workflow_start_time"):
        _workflow_start_time.set(ctx["workflow_start_time"])
    
    # Restore workflow state
    if "workflow_state" in ctx:
        try:
            state = get_workflow_state()
            state_data = ctx["workflow_state"]
            if isinstance(state_data, dict):
                state.call_depth = state_data.get("call_depth", {}).copy()
                state.function_name = state_data.get("function_name")
                state.start_time = state_data.get("start_time")
        except Exception:
            pass  # Best-effort: don't crash


# Threading support
_original_thread_start = None


def _patched_thread_start(self):
    """Patched Thread.start() that propagates workflow context."""
    # Copy context before starting thread
    ctx = _copy_workflow_context()
    
    # Store context in thread object
    self._llmobserve_context = ctx
    
    # Wrap the run method to restore context
    original_run = self.run
    
    def run_with_context():
        _restore_workflow_context(ctx)
        return original_run()
    
    self.run = run_with_context
    
    # Call original start
    return _original_thread_start(self)


def patch_threading():
    """Patch threading.Thread to propagate workflow context."""
    global _original_thread_start
    
    if _original_thread_start is None:
        import threading
        
        _original_thread_start = threading.Thread.start
        threading.Thread.start = _patched_thread_start


# Async support
_original_create_task = None


def _patched_create_task(coro, *, name=None, context=None):
    """Patched asyncio.create_task() that propagates workflow context."""
    # If context is explicitly provided, use it
    if context is None:
        # Copy current context (includes workflow context vars)
        context = contextvars.copy_context()
    
    # Create task with copied context
    return _original_create_task(coro, name=name, context=context)


def patch_asyncio():
    """Patch asyncio.create_task() to propagate workflow context."""
    global _original_create_task
    
    if _original_create_task is None:
        _original_create_task = asyncio.create_task
        asyncio.create_task = _patched_create_task


# Multiprocessing support
_original_process_start = None


def _patched_process_start(self):
    """Patched Process.start() that propagates workflow context."""
    # Copy context
    ctx = _copy_workflow_context()
    
    # Store context in process object
    self._llmobserve_context = ctx
    
    # Wrap the run method to restore context
    original_run = self.run
    
    def run_with_context():
        _restore_workflow_context(ctx)
        return original_run()
    
    self.run = run_with_context
    
    # Call original start
    return _original_process_start(self)


def patch_multiprocessing():
    """Patch multiprocessing.Process to propagate workflow context."""
    global _original_process_start
    
    if _original_process_start is None:
        try:
            import multiprocessing
            
            _original_process_start = multiprocessing.Process.start
            multiprocessing.Process.start = _patched_process_start
        except ImportError:
            pass  # multiprocessing not available


# Celery support
_celery_patched = False


def inject_headers(headers: Optional[dict] = None) -> dict:
    """
    Inject workflow context into headers for Celery.
    
    Args:
        headers: Optional existing headers dict
    
    Returns:
        Headers dict with workflow context injected
    """
    if headers is None:
        headers = {}
    
    ctx = _copy_workflow_context()
    headers["_llmobserve_context"] = ctx
    
    return headers


def extract_headers(headers: dict) -> None:
    """
    Extract workflow context from headers for Celery.
    
    Args:
        headers: Headers dict containing workflow context
    """
    ctx = headers.get("_llmobserve_context")
    if ctx:
        _restore_workflow_context(ctx)


def patch_celery():
    """Patch Celery to propagate workflow context."""
    global _celery_patched
    
    if _celery_patched:
        return
    
    try:
        import celery
        
        # Patch send_task to inject context
        original_send_task = celery.Celery.send_task
        
        def patched_send_task(self, name, args=None, kwargs=None, **options):
            # Copy context
            ctx = _copy_workflow_context()
            
            # Inject context into task headers
            if "headers" not in options:
                options["headers"] = {}
            options["headers"]["_llmobserve_context"] = ctx
            
            return original_send_task(self, name, args=args, kwargs=kwargs, **options)
        
        celery.Celery.send_task = patched_send_task
        
        # Patch task execution to restore context
        original_apply_async = celery.Task.apply_async
        
        def patched_apply_async(self, args=None, kwargs=None, **options):
            # Extract context from headers
            headers = options.get("headers", {})
            ctx = headers.get("_llmobserve_context")
            
            if ctx:
                # Restore context before executing task
                _restore_workflow_context(ctx)
            
            return original_apply_async(self, args=args, kwargs=kwargs, **options)
        
        celery.Task.apply_async = patched_apply_async
        
        _celery_patched = True
    except ImportError:
        pass  # Celery not installed


# Webhook helpers (opt-in)
def inject_webhook_context(headers: Optional[dict] = None) -> dict:
    """
    Inject workflow context into webhook headers.
    
    Args:
        headers: Optional existing headers dict
    
    Returns:
        Headers dict with workflow context injected
    """
    return inject_headers(headers)


def extract_webhook_context(headers: dict) -> None:
    """
    Extract workflow context from webhook headers.
    
    Args:
        headers: Headers dict containing workflow context
    """
    extract_headers(headers)


def enable_context_propagation():
    """Enable all context propagation patches."""
    patch_threading()
    patch_asyncio()
    patch_multiprocessing()
    patch_celery()
