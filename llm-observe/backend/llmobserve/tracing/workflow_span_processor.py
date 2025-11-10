"""Span processor to write workflow spans to database."""

from opentelemetry import baggage, trace
from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor

from llmobserve.semantics import WORKFLOW_TENANT_ID
from llmobserve.storage.repo import SpanRepository


class WorkflowSpanProcessor(SpanProcessor):
    """
    Span processor that writes workflow spans to the database.
    
    Workflow spans are spans that start with "workflow." and represent
    function-level workflow execution.
    """

    def __init__(self, span_repo: SpanRepository):
        """Initialize with span repository."""
        self.span_repo = span_repo

    def on_start(self, span: trace.Span, parent_context=None) -> None:
        """Called when a span starts."""
        pass

    def on_end(self, span: ReadableSpan) -> None:
        """Called when a span ends - write workflow spans and API spans to database."""
        span_name = span.name
        
        # Process workflow spans (spans that start with "workflow.")
        # Also process mock API spans (gmail.*, gcal.*, vapi.*, pinecone.*) for visualization
        is_workflow_span = span_name.startswith("workflow.")
        is_mock_api_span = (
            span_name.startswith("gmail.") or
            span_name.startswith("gcal.") or
            span_name.startswith("vapi.") or
            span_name.startswith("pinecone.")
        )
        
        if not (is_workflow_span or is_mock_api_span):
            return
        
        span_context = span.get_span_context()
        if not span_context.is_valid:
            return
        
        # Get tenant ID
        attrs = dict(span.attributes) if span.attributes else {}
        tenant_id = baggage.get_baggage(WORKFLOW_TENANT_ID) or attrs.get(WORKFLOW_TENANT_ID) or "default"
        
        # Get parent span ID
        parent_span_id = None
        if span.parent:
            parent_span_id = f"{span.parent.span_id:016x}"
        
        # Calculate duration
        duration_ms = None
        if span.end_time and span.start_time:
            duration_ms = (span.end_time - span.start_time) / 1e6  # Convert nanoseconds to milliseconds
        
        # Extract function name from attributes
        function_name = attrs.get("function.name", "")
        
        # Write workflow span summary
        summary = {
            "trace_id": f"{span_context.trace_id:032x}",
            "span_id": f"{span_context.span_id:016x}",
            "parent_span_id": parent_span_id,
            "name": span_name,
            "model": None,  # Workflow spans don't have models
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cost_usd": 0.0,  # Workflow spans have no direct cost
            "start_time": span.start_time / 1e9,  # Convert nanoseconds to seconds
            "duration_ms": duration_ms,
            "tenant_id": tenant_id,
        }
        
        try:
            self.span_repo.create_span_summary(summary)
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.error("Failed to write workflow span to database", error=str(e), span_name=span_name)

    def shutdown(self) -> None:
        """Shutdown processor."""
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush spans."""
        return True

