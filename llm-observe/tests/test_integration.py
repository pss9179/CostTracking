"""Integration tests for demo agent workflow."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

from llmobserve.demo.agent import run_agent_workflow
from llmobserve.storage.repo import SpanRepository


@pytest.fixture
def tracer_provider():
    """Set up tracer provider for tests."""
    provider = TracerProvider()
    processor = SimpleSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    return provider


@pytest.mark.asyncio
async def test_agent_workflow_mock(tracer_provider):
    """Test agent workflow with mocked GPT calls."""
    # Mock OpenAI
    with patch("llmobserve.demo.tools.openai") as mock_openai:
        mock_client = Mock()
        mock_openai.OpenAI.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Mocked response"))]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=20)
        mock_response.model = "gpt-3.5-turbo"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        # Run workflow
        trace_id = await run_agent_workflow()
        
        # Should return a trace ID
        assert trace_id is not None
        assert len(trace_id) == 32  # Hex string length


@pytest.mark.asyncio
async def test_fake_app_mock():
    """Test fake app with mocked GPT calls."""
    from llmobserve.demo.fake_app import run_fake_app
    
    # Mock OpenAI
    with patch("llmobserve.demo.fake_app.openai") as mock_openai:
        mock_client = Mock()
        mock_openai.OpenAI.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Mocked response"))]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=20)
        mock_response.model = "gpt-3.5-turbo"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        # Run fake app (should not raise)
        await run_fake_app()

