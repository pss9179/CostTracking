"""Span processor to capture GenAI instrumentor spans and write them to database."""

from typing import Optional

from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor
from opentelemetry.trace import Span

from llmobserve.config import settings
from llmobserve.pricing import pricing_registry
from llmobserve.semantics import WORKFLOW_TENANT_ID
from llmobserve.storage.repo import SpanRepository
from opentelemetry import baggage


class GenAISpanProcessor(SpanProcessor):
    """Process spans from official GenAI instrumentor and write to database."""

    def __init__(self, span_repo: Optional[SpanRepository] = None):
        """Initialize processor with span repository."""
        self.span_repo = span_repo

    def on_start(self, span: Span, parent_context=None) -> None:
        """Called when a span starts."""
        pass

    def on_end(self, span: ReadableSpan) -> None:
        """Called when a span ends - write GenAI spans to database."""
        if not self.span_repo:
            return

        # Only process spans from GenAI instrumentor (openai.chat, etc.)
        span_name = span.name
        if not (span_name.startswith("openai.") or "gen_ai" in str(span.attributes)):
            return

        span_context = span.get_span_context()
        if not span_context.is_valid:
            return

        # Extract GenAI attributes
        attrs = dict(span.attributes) if hasattr(span, 'attributes') else {}
        
        # Get model name
        model = attrs.get("gen_ai.request.model") or attrs.get("gen_ai.model.name") or "unknown"
        
        # Extract token counts - check multiple attribute formats
        prompt_tokens = 0
        completion_tokens = 0
        
        # Method 1: Check gen_ai.token.count (dict format)
        token_count = attrs.get("gen_ai.token.count")
        if isinstance(token_count, dict):
            prompt_tokens = token_count.get("prompt", 0) or token_count.get("input", 0)
            completion_tokens = token_count.get("completion", 0) or token_count.get("output", 0)
        
        # Method 2: Check separate token count attributes (set by our wrapper)
        if prompt_tokens == 0:
            prompt_tokens = attrs.get("gen_ai.token.count.prompt", 0)
        if completion_tokens == 0:
            completion_tokens = attrs.get("gen_ai.token.count.completion", 0)
        
        # Method 3: Check LLM usage attributes (set by our wrapper)
        if prompt_tokens == 0:
            prompt_tokens = attrs.get("llm.usage.prompt_tokens", 0)
        if completion_tokens == 0:
            completion_tokens = attrs.get("llm.usage.completion_tokens", 0)
        
        # Method 4: Try other GenAI semantic convention formats
        if prompt_tokens == 0:
            prompt_tokens = (
                attrs.get("gen_ai.token.count.input", 0) or
                attrs.get("gen_ai.usage.prompt_tokens", 0)
            )
        if completion_tokens == 0:
            completion_tokens = (
                attrs.get("gen_ai.token.count.output", 0) or
                attrs.get("gen_ai.usage.completion_tokens", 0)
            )

        # Calculate cost
        total_tokens = prompt_tokens + completion_tokens
        cost = pricing_registry.cost_for(model, prompt_tokens, completion_tokens)

        # Get tenant ID
        tenant_id = baggage.get_baggage(WORKFLOW_TENANT_ID) or attrs.get(WORKFLOW_TENANT_ID) or "default"

        # Get parent span ID
        parent_span_id = None
        if span.parent:
            parent_span_id = f"{span.parent.span_id:016x}"

        # Calculate duration
        duration_ms = None
        if span.end_time and span.start_time:
            duration_ms = (span.end_time - span.start_time) / 1e6  # Convert nanoseconds to milliseconds

        # Write span summary
        summary = {
            "trace_id": f"{span_context.trace_id:032x}",
            "span_id": f"{span_context.span_id:016x}",
            "parent_span_id": parent_span_id,
            "name": span_name,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost_usd": cost,
            "start_time": span.start_time / 1e9,  # Convert nanoseconds to seconds
            "duration_ms": duration_ms,
            "tenant_id": tenant_id,
        }

        try:
            self.span_repo.create_span_summary(summary)
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.error("Failed to write GenAI span to database", error=str(e), span_name=span_name)

    def shutdown(self) -> None:
        """Shutdown processor."""
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush spans."""
        return True

