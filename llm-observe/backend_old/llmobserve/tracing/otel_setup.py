"""OpenTelemetry setup and configuration."""

import json
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from llmobserve.config import settings
from llmobserve.tracing.genai_span_processor import GenAISpanProcessor
from llmobserve.tracing.sampler import ParentBasedSampler
from llmobserve.tracing.workflow_span_processor import WorkflowSpanProcessor


def setup_tracing(span_repo=None) -> None:
    """Initialize OpenTelemetry tracing with Console and optional OTLP exporters."""
    # Create resource with service metadata
    resource = Resource.create(
        {
            "service.name": settings.service_name,
            "service.version": "0.1.0",
            "deployment.environment": settings.env,
        }
    )

    # Create tracer provider with parent-based sampling
    tracer_provider = TracerProvider(
        resource=resource,
        sampler=ParentBasedSampler(),
    )

    # Add Console exporter (always enabled for demo)
    console_exporter = ConsoleSpanExporter()
    tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))

    # Add OTLP exporter if endpoint configured
    if settings.otlp_endpoint:
        otlp_exporter = _create_otlp_exporter()
        if otlp_exporter:
            tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Add GenAI span processor if using official GenAI instrumentor and span_repo provided
    if settings.use_genai_instrumentor and span_repo:
        genai_processor = GenAISpanProcessor(span_repo=span_repo)
        tracer_provider.add_span_processor(genai_processor)
    
    # Add Workflow span processor to write workflow spans to database
    if span_repo:
        workflow_processor = WorkflowSpanProcessor(span_repo=span_repo)
        tracer_provider.add_span_processor(workflow_processor)

    # Set as global tracer provider
    trace.set_tracer_provider(tracer_provider)


def _create_otlp_exporter() -> Optional[OTLPSpanExporter]:
    """Create OTLP exporter with optional headers."""
    try:
        headers = {}
        if settings.otlp_headers:
            # Parse headers as JSON or key=value pairs
            try:
                headers = json.loads(settings.otlp_headers)
            except json.JSONDecodeError:
                # Try key=value format
                for pair in settings.otlp_headers.split(","):
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        headers[key.strip()] = value.strip()

        return OTLPSpanExporter(
            endpoint=settings.otlp_endpoint,
            headers=headers if headers else None,
        )
    except Exception as e:
        import structlog
        logger = structlog.get_logger()
        logger.warning("Failed to create OTLP exporter", error=str(e))
        return None


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer instance."""
    return trace.get_tracer(name)

