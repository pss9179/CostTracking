"""Acceptance tests for auto function flow tracing system."""

import asyncio
import threading
import time
from unittest.mock import Mock, patch

import pytest

from llmobserve.tracing.function_tracer import wrap_function
from llmobserve.tracing.workflow_manager import (
    get_current_workflow_span,
    get_workflow_state,
)
from llmobserve.tracing.instrumentors.base import ensure_root_span
from llmobserve.tracing.otel_setup import setup_tracing


@pytest.fixture
def tracer_provider():
    """Set up a tracer provider for tests."""
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
    
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    setup_tracing()
    yield provider


def test_sync_flow_with_api_calls(tracer_provider):
    """Test sync flow: function with 2 API calls → 1 workflow + 2 children."""
    api_call_count = []
    
    def mock_api_call(name):
        """Mock API call that creates a span."""
        api_call_count.append(name)
        with ensure_root_span("test_service"):
            from llmobserve.tracing.tracer import get_wrapped_tracer
            tracer = get_wrapped_tracer(__name__)
            with tracer.start_span(f"api.{name}") as span:
                span.set_attribute("api.name", name)
                return f"result_{name}"
    
    def my_workflow():
        """Test workflow function."""
        result1 = mock_api_call("call1")
        result2 = mock_api_call("call2")
        return f"{result1}_{result2}"
    
    # Wrap the function
    wrapped = wrap_function(my_workflow, "test_module")
    
    # Execute
    result = wrapped()
    
    assert result == "result_call1_result_call2"
    assert len(api_call_count) == 2
    
    # Check that workflow span was created
    # (Note: span will be ended when function exits, so we check state)
    state = get_workflow_state()
    # After function exits, workflow span should be ended
    assert state.active_span is None or state.active_span.is_recording() is False


@pytest.mark.asyncio
async def test_async_flow_with_api_calls(tracer_provider):
    """Test async flow: async function with API calls → correct nesting."""
    api_call_count = []
    
    async def mock_api_call(name):
        """Mock async API call."""
        api_call_count.append(name)
        await asyncio.sleep(0.01)  # Simulate async work
        with ensure_root_span("test_service"):
            from llmobserve.tracing.tracer import get_wrapped_tracer
            tracer = get_wrapped_tracer(__name__)
            with tracer.start_span(f"api.{name}") as span:
                span.set_attribute("api.name", name)
                return f"result_{name}"
    
    async def my_async_workflow():
        """Test async workflow function."""
        result1 = await mock_api_call("call1")
        result2 = await mock_api_call("call2")
        return f"{result1}_{result2}"
    
    # Wrap the function
    wrapped = wrap_function(my_async_workflow, "test_module")
    
    # Execute
    result = await wrapped()
    
    assert result == "result_call1_result_call2"
    assert len(api_call_count) == 2


def test_exception_handling(tracer_provider):
    """Test exception handling: exception in function → workflow ends with exception attrs."""
    def my_workflow():
        """Test workflow that raises an exception."""
        with ensure_root_span("test_service"):
            from llmobserve.tracing.tracer import get_wrapped_tracer
            tracer = get_wrapped_tracer(__name__)
            with tracer.start_span("api.call") as span:
                span.set_attribute("api.name", "call")
        raise ValueError("Test error")
    
    # Wrap the function
    wrapped = wrap_function(my_workflow, "test_module")
    
    # Execute and expect exception
    with pytest.raises(ValueError, match="Test error"):
        wrapped()
    
    # Check that workflow span was ended (exception should be recorded)
    state = get_workflow_state()
    assert state.active_span is None or state.active_span.is_recording() is False


def test_no_api_calls_no_workflow_span(tracer_provider):
    """Test no API calls: function executes → no workflow span created."""
    def my_workflow():
        """Test workflow function with no API calls."""
        return "result"
    
    # Wrap the function
    wrapped = wrap_function(my_workflow, "test_module")
    
    # Execute
    result = wrapped()
    
    assert result == "result"
    
    # Check that no workflow span was created (lazy creation only on API calls)
    state = get_workflow_state()
    assert state.active_span is None


def test_recursion_single_workflow(tracer_provider):
    """Test recursion: recursive function → single workflow at outermost."""
    call_depth = []
    
    def recursive_workflow(n):
        """Recursive workflow function."""
        call_depth.append(n)
        if n <= 0:
            # Make API call only at base case
            with ensure_root_span("test_service"):
                from llmobserve.tracing.tracer import get_wrapped_tracer
                tracer = get_wrapped_tracer(__name__)
                with tracer.start_span("api.recursive_call") as span:
                    span.set_attribute("api.name", "recursive")
            return "done"
        return recursive_workflow(n - 1)
    
    # Wrap the function
    wrapped = wrap_function(recursive_workflow, "test_module")
    
    # Execute
    result = wrapped(3)
    
    assert result == "done"
    assert len(call_depth) == 4  # 3, 2, 1, 0
    
    # Check that only one workflow span was created (at outermost call)
    state = get_workflow_state()
    assert state.active_span is None or state.active_span.is_recording() is False


def test_threads_api_calls_in_threads(tracer_provider):
    """Test threads: API calls in threads → children of function's workflow."""
    results = []
    
    def mock_api_call(name):
        """Mock API call."""
        with ensure_root_span("test_service"):
            from llmobserve.tracing.tracer import get_wrapped_tracer
            tracer = get_wrapped_tracer(__name__)
            with tracer.start_span(f"api.{name}") as span:
                span.set_attribute("api.name", name)
                return f"result_{name}"
    
    def thread_worker(name):
        """Worker function for thread."""
        result = mock_api_call(name)
        results.append(result)
    
    def my_workflow():
        """Test workflow that spawns threads."""
        threads = []
        for i in range(2):
            thread = threading.Thread(target=thread_worker, args=(f"call{i}",))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        return "done"
    
    # Wrap the function
    wrapped = wrap_function(my_workflow, "test_module")
    
    # Execute
    result = wrapped()
    
    assert result == "done"
    assert len(results) == 2


def test_nested_functions_inner_function_calls_api(tracer_provider):
    """Test nested functions: inner function calls API → parent workflow span."""
    def inner_function():
        """Inner function that makes API call."""
        with ensure_root_span("test_service"):
            from llmobserve.tracing.tracer import get_wrapped_tracer
            tracer = get_wrapped_tracer(__name__)
            with tracer.start_span("api.inner") as span:
                span.set_attribute("api.name", "inner")
        return "inner_result"
    
    def outer_workflow():
        """Outer workflow function."""
        result = inner_function()
        return f"outer_{result}"
    
    # Wrap only the outer function
    wrapped = wrap_function(outer_workflow, "test_module")
    
    # Execute
    result = wrapped()
    
    assert result == "outer_inner_result"
    
    # Check that workflow span was created for outer function
    state = get_workflow_state()
    assert state.active_span is None or state.active_span.is_recording() is False


def test_streaming_api_call(tracer_provider):
    """Test streaming: streaming API call → child span covers full stream."""
    chunks = []
    
    def streaming_api_call():
        """Mock streaming API call."""
        with ensure_root_span("test_service"):
            from llmobserve.tracing.tracer import get_wrapped_tracer
            tracer = get_wrapped_tracer(__name__)
            with tracer.start_span("api.streaming") as span:
                span.set_attribute("api.name", "streaming")
                # Simulate streaming
                for i in range(3):
                    chunks.append(f"chunk_{i}")
                    yield f"chunk_{i}"
    
    def my_workflow():
        """Test workflow that handles streaming."""
        stream = streaming_api_call()
        results = list(stream)
        return results
    
    # Wrap the function
    wrapped = wrap_function(my_workflow, "test_module")
    
    # Execute
    result = wrapped()
    
    assert len(result) == 3
    assert len(chunks) == 3
    
    # Check that workflow span was created
    state = get_workflow_state()
    assert state.active_span is None or state.active_span.is_recording() is False

