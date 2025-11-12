"""
Celery and background worker support for context propagation.

Problem: contextvars don't cross process boundaries (Celery tasks run in separate processes).
Solution: Serialize context and pass as task arguments, then restore in worker.
"""
import functools
from typing import Any, Callable, Optional
from llmobserve import context


def get_current_context() -> dict:
    """
    Serialize current observability context for passing to background tasks.
    
    Returns:
        Dict with run_id, tenant_id, customer_id, section_stack
    """
    section_stack = context._get_section_stack()
    
    return {
        "run_id": context.get_run_id(),
        "customer_id": context.get_customer_id(),
        "section_stack": [
            {"label": s["label"], "span_id": s["span_id"], "parent_span_id": s["parent_span_id"]}
            for s in section_stack
        ] if section_stack else []
    }


def restore_context(ctx: dict) -> None:
    """
    Restore observability context in a background worker.
    
    Args:
        ctx: Context dict from get_current_context()
    """
    if not ctx:
        return
    
    # Restore IDs
    if ctx.get("run_id"):
        context.set_run_id(ctx["run_id"])
    if ctx.get("customer_id"):
        context.set_customer_id(ctx["customer_id"])
    
    # Restore section stack
    if ctx.get("section_stack"):
        # Manually reconstruct the stack
        stack = context._get_section_stack()
        stack.clear()
        stack.extend(ctx["section_stack"])


def observe_task(func: Optional[Callable] = None, *, section: Optional[str] = None):
    """
    Decorator for Celery/background tasks to automatically propagate observability context.
    
    Usage with Celery:
        @celery.task
        @observe_task
        def my_task(arg1, arg2):
            # Context is automatically restored here
            client.chat.completions.create(...)  # Tracked!
    
    Usage with explicit section:
        @celery.task
        @observe_task(section="background:process_documents")
        def process_documents(doc_ids):
            # Runs inside section context
            pass
    
    Manual usage (if you can't use decorator):
        # In main process
        ctx = get_current_context()
        my_task.delay(arg1, arg2, _llmobserve_ctx=ctx)
        
        # In worker
        @celery.task
        def my_task(arg1, arg2, _llmobserve_ctx=None):
            restore_context(_llmobserve_ctx)
            # Now context is restored
    """
    def decorator(task_func: Callable) -> Callable:
        @functools.wraps(task_func)
        def sync_wrapper(*args, **kwargs):
            # Extract context from kwargs (if passed)
            ctx = kwargs.pop("_llmobserve_ctx", None)
            
            # Restore context
            if ctx:
                restore_context(ctx)
            
            # Execute in section if specified
            if section:
                with context.section(section):
                    return task_func(*args, **kwargs)
            else:
                return task_func(*args, **kwargs)
        
        @functools.wraps(task_func)
        async def async_wrapper(*args, **kwargs):
            # Extract context from kwargs
            ctx = kwargs.pop("_llmobserve_ctx", None)
            
            # Restore context
            if ctx:
                restore_context(ctx)
            
            # Execute in section if specified
            if section:
                with context.section(section):
                    return await task_func(*args, **kwargs)
            else:
                return await task_func(*args, **kwargs)
        
        # Determine if async
        import inspect
        if inspect.iscoroutinefunction(task_func):
            return async_wrapper
        else:
            return sync_wrapper
    
    # Handle both @observe_task and @observe_task(section="...")
    if func is None:
        return decorator
    else:
        return decorator(func)


def with_context(func: Callable, *args, **kwargs) -> Any:
    """
    Execute a function with current context in a ThreadPoolExecutor or similar.
    
    Usage:
        from concurrent.futures import ThreadPoolExecutor
        
        with ThreadPoolExecutor() as executor:
            # Wrong: context lost
            future = executor.submit(expensive_task, arg1)
            
            # Correct: context preserved
            future = executor.submit(with_context, expensive_task, arg1)
    
    Args:
        func: Function to execute
        *args: Arguments to pass to function
        **kwargs: Keyword arguments to pass to function
    
    Returns:
        Result of func(*args, **kwargs)
    """
    # Capture context in main thread
    ctx = get_current_context()
    
    def wrapper():
        # Restore context in worker thread
        restore_context(ctx)
        return func(*args, **kwargs)
    
    return wrapper()


# Celery integration helper
def patch_celery_task(celery_app):
    """
    Monkey-patch Celery to automatically inject context into all tasks.
    
    Usage:
        from celery import Celery
        from llmobserve.celery_support import patch_celery_task
        
        app = Celery('myapp')
        patch_celery_task(app)  # Auto-injects context into ALL tasks
        
        @app.task
        def my_task(arg):
            # Context automatically available!
            pass
    
    NOTE: This is advanced usage. For most cases, use @observe_task decorator.
    """
    original_apply_async = celery_app.Task.apply_async
    
    @functools.wraps(original_apply_async)
    def apply_async_with_context(self, args=None, kwargs=None, **options):
        # Inject context into kwargs
        if kwargs is None:
            kwargs = {}
        
        # Only inject if not already present
        if "_llmobserve_ctx" not in kwargs:
            kwargs["_llmobserve_ctx"] = get_current_context()
        
        return original_apply_async(self, args=args, kwargs=kwargs, **options)
    
    celery_app.Task.apply_async = apply_async_with_context
    print("[llmobserve] Celery patched - context will auto-propagate to all tasks")
    print("[llmobserve] Make sure tasks accept **kwargs or _llmobserve_ctx parameter!")


# RQ (Redis Queue) support
def observe_rq_job(func: Callable) -> Callable:
    """
    Decorator for RQ (Redis Queue) jobs to propagate context.
    
    Usage:
        from rq import Queue
        from llmobserve.celery_support import observe_rq_job
        
        @observe_rq_job
        def my_job(arg1):
            # Context restored here
            pass
        
        # Enqueue job
        queue.enqueue(my_job, arg1)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ctx = kwargs.pop("_llmobserve_ctx", None)
        if ctx:
            restore_context(ctx)
        return func(*args, **kwargs)
    
    # Wrap the enqueue to inject context
    original_func = wrapper
    
    def enqueue_with_context(queue, *args, **kwargs):
        ctx = get_current_context()
        kwargs["_llmobserve_ctx"] = ctx
        return queue.enqueue(original_func, *args, **kwargs)
    
    wrapper.enqueue_with_context = enqueue_with_context
    return wrapper

