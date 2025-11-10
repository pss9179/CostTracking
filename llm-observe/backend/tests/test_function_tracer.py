"""Tests for function-level workflow tracing."""

import asyncio
import pytest

from llmobserve.tracing.function_tracer import (
    get_current_workflow_span,
    should_wrap_function,
    workflow_trace,
)


def test_should_wrap_function():
    """Test function detection logic."""
    # Should wrap workflow functions
    def test_workflow():
        pass
    
    assert should_wrap_function(test_workflow, "test_module") is True
    
    # Should not wrap private functions
    def __private():
        pass
    
    assert should_wrap_function(__private, "test_module") is False
    
    # Should not wrap stdlib functions
    import json
    
    assert should_wrap_function(json.dumps, "json") is False


def test_sync_function_wrapping():
    """Test wrapping synchronous functions."""
    @workflow_trace
    def test_function():
        return "result"
    
    # Function should be wrapped
    assert hasattr(test_function, "_llmobserve_wrapped")
    assert test_function() == "result"


def test_async_function_wrapping():
    """Test wrapping asynchronous functions."""
    @workflow_trace
    async def test_async_function():
        return "result"
    
    # Function should be wrapped
    assert hasattr(test_async_function, "_llmobserve_wrapped")
    
    # Should work with async
    result = asyncio.run(test_async_function())
    assert result == "result"


def test_nested_function_calls():
    """Test nested function calls inherit workflow span."""
    @workflow_trace
    def outer_function():
        @workflow_trace
        def inner_function():
            return get_current_workflow_span() is not None
        
        return inner_function()
    
    # Inner function should have workflow span
    assert outer_function() is True


def test_exception_handling():
    """Test that workflow spans end even on exceptions."""
    @workflow_trace
    def failing_function():
        raise ValueError("test error")
    
    # Should raise exception
    with pytest.raises(ValueError):
        failing_function()
    
    # Workflow span should have ended (no active span)
    assert get_current_workflow_span() is None


def test_workflow_span_attributes():
    """Test that workflow spans have correct attributes."""
    @workflow_trace
    def test_function():
        span = get_current_workflow_span()
        if span:
            return {
                "name": span.name,
                "has_function_name": span.attributes.get("function.name") is not None,
                "has_module": span.attributes.get("function.module") is not None,
            }
        return None
    
    result = test_function()
    assert result is not None
    assert result["name"] == "workflow.test_function"
    assert result["has_function_name"] is True
    assert result["has_module"] is True


@pytest.mark.asyncio
async def test_async_context_propagation():
    """Test that workflow context propagates to async tasks."""
    @workflow_trace
    async def async_workflow():
        # Create a task
        async def inner_task():
            return get_current_workflow_span() is not None
        
        task = asyncio.create_task(inner_task())
        return await task
    
    # Context should propagate to task
    result = await async_workflow()
    assert result is True


def test_recursive_function():
    """Test recursive functions get separate workflow spans."""
    call_count = {"count": 0}
    
    @workflow_trace
    def recursive_function(n):
        call_count["count"] += 1
        span = get_current_workflow_span()
        if span:
            # Each call should have its own span
            return span.name
        if n > 0:
            return recursive_function(n - 1)
        return None
    
    # Should create separate spans for each call
    result = recursive_function(2)
    assert result == "workflow.recursive_function"
    assert call_count["count"] == 3  # Initial call + 2 recursive calls

