"""
Retry detection and tracking utilities.

Automatically detects retry attempts and groups them logically.
"""
import functools
import uuid
from contextlib import contextmanager
from typing import Callable, Optional, TypeVar
from llmobserve import context

# Thread-local storage for retry tracking
import contextvars
_retry_context = contextvars.ContextVar("retry_context", default=None)

T = TypeVar("T")


class RetryContext:
    """Tracks retry attempts for a logical operation."""
    
    def __init__(self, operation_id: Optional[str] = None):
        self.operation_id = operation_id or str(uuid.uuid4())
        self.attempt_number = 0
        self.max_attempts = None
    
    def next_attempt(self) -> int:
        """Increment and return next attempt number."""
        self.attempt_number += 1
        return self.attempt_number
    
    def get_metadata(self) -> dict:
        """Get retry metadata for event tracking."""
        return {
            "operation_id": self.operation_id,
            "attempt_number": self.attempt_number,
            "is_retry": self.attempt_number > 1,
            "max_attempts": self.max_attempts
        }


def with_retry_tracking(
    func: Optional[Callable] = None,
    *,
    max_attempts: Optional[int] = None,
    operation_name: Optional[str] = None
) -> Callable:
    """
    Decorator to track retries for a function.
    
    Works with any retry library (tenacity, backoff, etc.) or manual retries.
    
    Usage:
        from tenacity import retry, stop_after_attempt
        from llmobserve.retry_tracking import with_retry_tracking
        
        @retry(stop=stop_after_attempt(3))
        @with_retry_tracking(max_attempts=3)
        def call_openai():
            return client.chat.completions.create(...)
        
        # Events will include:
        # - attempt_number: 1, 2, 3
        # - is_retry: False, True, True
        # - operation_id: same for all 3 attempts
    
    Args:
        max_attempts: Maximum retry attempts (for dashboard display)
        operation_name: Logical operation name (defaults to function name)
    """
    def decorator(target_func: Callable[..., T]) -> Callable[..., T]:
        op_name = operation_name or target_func.__name__
        
        @functools.wraps(target_func)
        def wrapper(*args, **kwargs) -> T:
            # Get or create retry context
            retry_ctx = _retry_context.get()
            
            # If no context exists, this is the first attempt
            if retry_ctx is None:
                retry_ctx = RetryContext()
                retry_ctx.max_attempts = max_attempts
                _retry_context.set(retry_ctx)
                created_context = True
            else:
                created_context = False
            
            # Increment attempt counter
            attempt = retry_ctx.next_attempt()
            
            # Create a section for this attempt
            section_name = f"retry:{op_name}:attempt_{attempt}"
            
            try:
                with context.section(section_name):
                    # Store retry metadata in context for SDK patches to pick up
                    result = target_func(*args, **kwargs)
                    return result
            finally:
                # Clean up context after all attempts complete
                if created_context:
                    _retry_context.set(None)
        
        @functools.wraps(target_func)
        async def async_wrapper(*args, **kwargs) -> T:
            # Get or create retry context
            retry_ctx = _retry_context.get()
            
            if retry_ctx is None:
                retry_ctx = RetryContext()
                retry_ctx.max_attempts = max_attempts
                _retry_context.set(retry_ctx)
                created_context = True
            else:
                created_context = False
            
            attempt = retry_ctx.next_attempt()
            section_name = f"retry:{op_name}:attempt_{attempt}"
            
            try:
                with context.section(section_name):
                    result = await target_func(*args, **kwargs)
                    return result
            finally:
                if created_context:
                    _retry_context.set(None)
        
        # Return appropriate wrapper
        import inspect
        if inspect.iscoroutinefunction(target_func):
            return async_wrapper
        else:
            return wrapper
    
    # Handle both @with_retry_tracking and @with_retry_tracking(...)
    if func is None:
        return decorator
    else:
        return decorator(func)


def get_retry_metadata() -> Optional[dict]:
    """
    Get current retry metadata for inclusion in events.
    
    Returns:
        Dict with operation_id, attempt_number, is_retry, or None if not in retry context
    """
    retry_ctx = _retry_context.get()
    if retry_ctx:
        return retry_ctx.get_metadata()
    return None


def detect_retry_from_section() -> Optional[dict]:
    """
    Detect if current call is a retry by examining section stack.
    
    Looks for sections named "retry:*:attempt_N" to infer retry metadata.
    
    Returns:
        Dict with is_retry, attempt_number, operation_name or None
    """
    section_path = context.get_section_path()
    if not section_path:
        return None
    
    # Look for retry section pattern
    for segment in section_path.split("/"):
        if segment.startswith("retry:"):
            parts = segment.split(":")
            if len(parts) >= 3:
                operation_name = ":".join(parts[1:-1])
                attempt_str = parts[-1]
                
                if attempt_str.startswith("attempt_"):
                    try:
                        attempt_number = int(attempt_str.split("_")[1])
                        return {
                            "is_retry": attempt_number > 1,
                            "attempt_number": attempt_number,
                            "operation_name": operation_name
                        }
                    except (ValueError, IndexError):
                        pass
    
    return None


@contextmanager
def retry_block(max_attempts: Optional[int] = None, operation_name: Optional[str] = None):
    """
    Context manager for manual retry tracking.
    
    Use this when you have custom retry logic (not using decorators).
    
    Usage:
        from llmobserve.retry_tracking import retry_block
        
        for attempt in range(3):
            with retry_block(max_attempts=3, operation_name="api_call"):
                try:
                    result = call_api()
                    break  # Success
                except Exception as e:
                    if attempt == 2:
                        raise  # Last attempt
                    continue  # Retry
    
    Args:
        max_attempts: Maximum retry attempts (for dashboard display)
        operation_name: Logical operation name
    """
    # Get or create retry context
    retry_ctx = _retry_context.get()
    
    # If no context exists, create one
    if retry_ctx is None:
        retry_ctx = RetryContext()
        retry_ctx.max_attempts = max_attempts
        _retry_context.set(retry_ctx)
        created_context = True
    else:
        created_context = False
    
    # Increment attempt counter
    attempt = retry_ctx.next_attempt()
    
    # Create a section for this attempt
    op_name = operation_name or "operation"
    section_name = f"retry:{op_name}:attempt_{attempt}"
    
    try:
        with context.section(section_name):
            yield retry_ctx
    finally:
        # Clean up context after all attempts complete
        if created_context:
            _retry_context.set(None)


# Integration with OpenAI patch - this will be called from openai_patch.py
def enrich_event_with_retry_metadata(event: dict) -> dict:
    """
    Enrich an event with retry metadata if available.
    
    This is called automatically by SDK patches.
    """
    # First try to get from retry context
    retry_meta = get_retry_metadata()
    
    # If not found, try to detect from section path
    if not retry_meta:
        retry_meta = detect_retry_from_section()
    
    # Add to event metadata
    if retry_meta:
        if event.get("event_metadata") is None:
            event["event_metadata"] = {}
        event["event_metadata"].update(retry_meta)
    
    return event

