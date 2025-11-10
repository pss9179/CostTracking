"""Unified wrapped tracer with automatic enrichment and persistence."""

from contextlib import contextmanager
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import Span, Tracer

from llmobserve.tracing.enrichers import SpanEnricher
from llmobserve.storage.repo import SpanRepository


class WrappedTracer:
    """
    Unified tracer abstraction that wraps OpenTelemetry tracer.
    
    Provides simplified interface with automatic enrichment and persistence.
    All spans (workflow, LLM, API) flow through this unified layer.
    """
    
    def __init__(
        self,
        tracer: Tracer,
        span_enricher: Optional[SpanEnricher] = None,
        span_repo: Optional[SpanRepository] = None,
    ):
        """
        Initialize wrapped tracer.
        
        Args:
            tracer: OpenTelemetry tracer instance
            span_enricher: Optional span enricher for automatic enrichment
            span_repo: Optional span repository for persistence
        """
        self._tracer = tracer
        self._span_enricher = span_enricher
        self._span_repo = span_repo
    
    @contextmanager
    def start_span(self, name: str, **kwargs):
        """
        Start a new span with automatic enrichment and persistence.
        
        Args:
            name: Span name
            **kwargs: Additional arguments passed to tracer.start_as_current_span()
        
        Yields:
            Span instance
        """
        with self._tracer.start_as_current_span(name, **kwargs) as span:
            try:
                yield span
            finally:
                # Automatic enrichment happens via SpanEnricher in instrumentors
                # Automatic persistence happens via SpanProcessor in otel_setup
                pass
    
    def end_span(self, span: Span) -> None:
        """
        End a span (usually handled automatically by context manager).
        
        Args:
            span: Span to end
        """
        if hasattr(span, "end"):
            span.end()
    
    def current_span(self) -> Optional[Span]:
        """
        Get the current active span.
        
        Returns:
            Current span or None if no active span
        """
        return trace.get_current_span()


# Global tracer provider instance
_tracer_provider: Optional[TracerProvider] = None
_span_enricher: Optional[SpanEnricher] = None
_span_repo: Optional[SpanRepository] = None


def get_tracer_provider() -> Optional[TracerProvider]:
    """Get the global tracer provider instance."""
    global _tracer_provider
    if _tracer_provider is None:
        _tracer_provider = trace.get_tracer_provider()
    return _tracer_provider


def set_tracer_provider(provider: TracerProvider) -> None:
    """Set the global tracer provider instance."""
    global _tracer_provider
    _tracer_provider = provider
    trace.set_tracer_provider(provider)


def set_span_enricher(enricher: SpanEnricher) -> None:
    """Set the global span enricher instance."""
    global _span_enricher
    _span_enricher = enricher


def set_span_repo(repo: SpanRepository) -> None:
    """Set the global span repository instance."""
    global _span_repo
    _span_repo = repo


def get_wrapped_tracer(name: str) -> WrappedTracer:
    """
    Get a wrapped tracer instance for a given name.
    
    Args:
        name: Tracer name (usually __name__)
    
    Returns:
        WrappedTracer instance
    """
    provider = get_tracer_provider()
    if provider is None:
        # Fallback to default provider
        otel_tracer = trace.get_tracer(name)
    else:
        otel_tracer = provider.get_tracer(name)
    
    return WrappedTracer(
        tracer=otel_tracer,
        span_enricher=_span_enricher,
        span_repo=_span_repo,
    )


# Convenience function for getting wrapped tracer (matches OpenTelemetry API)
def get_tracer(name: str) -> WrappedTracer:
    """
    Get a wrapped tracer instance (convenience function matching OpenTelemetry API).
    
    Args:
        name: Tracer name (usually __name__)
    
    Returns:
        WrappedTracer instance
    """
    return get_wrapped_tracer(name)

