"""Base instrumentor interface and registry."""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import List

from opentelemetry import trace

tracer = trace.get_tracer(__name__)


@contextmanager
def ensure_root_span(service_name: str):
    """
    Auto-create a root span if no active span exists.
    
    This enables plug-and-play behavior: if a user calls an API without any
    manual tracing setup, we automatically create a root trace for that call.
    
    Args:
        service_name: Service name for the auto-root span (e.g., "openai", "pinecone")
    
    Yields:
        A context manager that wraps the API call. If no active span exists,
        creates an "auto.workflow.{service_name}" root span. If a parent span
        exists, child spans will automatically link to it.
    
    Example:
        with ensure_root_span("openai"):
            # API call here - will be wrapped in auto.workflow.openai if no parent
            response = openai.chat.completions.create(...)
    """
    # Check if there's an active span with valid trace context
    # This enables plug-and-play: if no parent span exists, we create a root span
    current_span = trace.get_current_span()
    has_valid_context = False
    try:
        if current_span is not None and hasattr(current_span, "get_span_context"):
            span_context = current_span.get_span_context()
            has_valid_context = span_context.is_valid if span_context else False
    except (AttributeError, TypeError):
        # If span context check fails, assume no valid context
        has_valid_context = False
    
    # If no valid parent span exists, create an auto-root span
    if not has_valid_context:
        # Create auto-root span that wraps the entire API call
        auto_root_name = f"auto.workflow.{service_name}"
        with tracer.start_as_current_span(auto_root_name) as auto_root_span:
            # Set attribute to mark this as an auto-created root span
            auto_root_span.set_attribute("auto.root", True)
            auto_root_span.set_attribute("service.name", service_name)
            yield auto_root_span
    else:
        # Parent span exists - child spans will automatically link to it
        # No need to create a wrapper span, just yield None
        yield None


class Instrumentor(ABC):
    """Base class for auto-instrumentation."""

    @abstractmethod
    def instrument(self) -> None:
        """Apply instrumentation to target library."""
        pass

    @abstractmethod
    def uninstrument(self) -> None:
        """Remove instrumentation from target library."""
        pass


class InstrumentorRegistry:
    """Registry for managing instrumentors."""

    def __init__(self):
        """Initialize empty registry."""
        self._instrumentors: List[Instrumentor] = []

    def register(self, instrumentor: Instrumentor) -> None:
        """Register an instrumentor."""
        self._instrumentors.append(instrumentor)

    def instrument_all(self) -> None:
        """Apply all registered instrumentors."""
        for instr in self._instrumentors:
            try:
                instr.instrument()
            except Exception as e:
                import structlog
                logger = structlog.get_logger()
                logger.error("Failed to apply instrumentor", instrumentor=type(instr).__name__, error=str(e))

    def uninstrument_all(self) -> None:
        """Remove all instrumentations."""
        for instr in self._instrumentors:
            try:
                instr.uninstrument()
            except Exception as e:
                import structlog
                logger = structlog.get_logger()
                logger.error("Failed to remove instrumentor", instrumentor=type(instr).__name__, error=str(e))


# Global registry
instrumentor_registry = InstrumentorRegistry()

