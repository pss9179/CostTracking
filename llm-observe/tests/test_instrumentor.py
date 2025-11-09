"""Tests for OpenAI instrumentor."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

from llmobserve.tracing.instrumentors.openai_instr import OpenAIInstrumentor
from llmobserve.tracing.enrichers import SpanEnricher


@pytest.fixture
def tracer_provider():
    """Set up tracer provider for tests."""
    provider = TracerProvider()
    processor = SimpleSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    return provider


def test_openai_instrumentor_init():
    """Test instrumentor initialization."""
    enricher = SpanEnricher()
    instrumentor = OpenAIInstrumentor(span_enricher=enricher)
    
    assert instrumentor.span_enricher == enricher
    assert not instrumentor._instrumented


def test_openai_instrumentor_instrument():
    """Test instrumenting OpenAI (mock)."""
    enricher = SpanEnricher()
    instrumentor = OpenAIInstrumentor(span_enricher=enricher)
    
    # Mock OpenAI module
    with patch("llmobserve.tracing.instrumentors.openai_instr.openai") as mock_openai:
        mock_openai.OpenAI = Mock()
        
        # Try to instrument (will fail if OpenAI not installed, but that's ok)
        try:
            instrumentor.instrument()
        except ImportError:
            pass  # Expected if OpenAI not installed in test env


def test_openai_instrumentor_uninstrument():
    """Test uninstrumenting OpenAI."""
    enricher = SpanEnricher()
    instrumentor = OpenAIInstrumentor(span_enricher=enricher)
    
    # Should not crash even if not instrumented
    instrumentor.uninstrument()

