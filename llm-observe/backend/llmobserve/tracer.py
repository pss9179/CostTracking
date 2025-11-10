"""OpenTelemetry tracer setup and helpers."""

import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger(__name__)

_tracer_provider: Optional[TracerProvider] = None
_tracer: Optional[trace.Tracer] = None


def init_tracer(service_name: str = "llmobserve", api_key: Optional[str] = None) -> None:
    """
    Initialize OpenTelemetry tracer.

    Args:
        service_name: Service name for traces
        api_key: Optional API key (for future cloud export)
    """
    global _tracer_provider, _tracer

    if _tracer_provider is not None:
        logger.warning("Tracer already initialized")
        return

    # Create resource
    resource = Resource.create({
        "service.name": service_name,
    })

    # Create tracer provider
    _tracer_provider = TracerProvider(resource=resource)

    # Add console exporter for development
    console_exporter = ConsoleSpanExporter()
    span_processor = BatchSpanProcessor(console_exporter)
    _tracer_provider.add_span_processor(span_processor)

    # Set as global
    trace.set_tracer_provider(_tracer_provider)

    # Create tracer
    _tracer = trace.get_tracer(__name__)

    logger.info(f"Tracer initialized for service: {service_name}")


def get_tracer() -> trace.Tracer:
    """Get the global tracer instance."""
    global _tracer
    if _tracer is None:
        init_tracer()
    return _tracer


def get_current_trace() -> Optional[trace.Span]:
    """Get current active span."""
    return trace.get_current_span()


def get_current_trace_id() -> Optional[str]:
    """Get current trace ID as hex string."""
    span = get_current_trace()
    if span and span.get_span_context().is_valid:
        return f"{span.get_span_context().trace_id:032x}"
    return None


def get_current_span_id() -> Optional[str]:
    """Get current span ID as hex string."""
    span = get_current_trace()
    if span and span.get_span_context().is_valid:
        return f"{span.get_span_context().span_id:016x}"
    return None

