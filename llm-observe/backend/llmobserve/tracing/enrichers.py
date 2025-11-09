"""Span enrichment with latency, usage, cost, and privacy handling."""

import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty
from typing import Optional

from opentelemetry import baggage, trace
from opentelemetry.sdk.trace import Span

from llmobserve.config import settings
from llmobserve.pricing import pricing_registry
from llmobserve.semantics import (
    API_COST_USD,
    API_LATENCY_MS,
    API_OPERATION,
    API_PROVIDER,
    API_REQUEST_SIZE,
    LLM_COST_USD,
    LLM_PROMPT_CONTENT,
    LLM_PROMPT_HASH,
    LLM_RESPONSE_CONTENT,
    LLM_RESPONSE_HASH,
    LLM_USAGE_COMPLETION_TOKENS,
    LLM_USAGE_PROMPT_TOKENS,
    LLM_USAGE_TOTAL_TOKENS,
    WORKFLOW_TENANT_ID,
    hash_prompt,
    hash_response,
)
from llmobserve.storage.repo import SpanRepository

# TODO: Production hardening
# 1. Implement proper backpressure handling for write queue
# 2. Add metrics for queue depth and write failures
# 3. Implement circuit breaker for DB writes
# 4. Add alerting for write failures


class SpanEnricher:
    """Enriches spans with computed attributes and async DB writes."""

    def __init__(self, span_repo: Optional[SpanRepository] = None):
        """Initialize with optional span repository for async writes."""
        self.span_repo = span_repo
        self._write_queue: Queue = Queue()
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="span-writer")

        if self.span_repo:
            self._start_async_writer()

    def enrich_llm_span(
        self,
        span: Span,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        prompt_messages: Optional[list] = None,
        response_content: Optional[str] = None,
        start_time: Optional[float] = None,
    ) -> None:
        """
        Enrich LLM span with usage, cost, and optionally content/hashes.

        Args:
            span: OpenTelemetry span to enrich
            model: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            prompt_messages: Original prompt messages (for hashing)
            response_content: Response content (for hashing)
            start_time: Span start time for latency calculation
        """
        total_tokens = prompt_tokens + completion_tokens
        cost = pricing_registry.cost_for(model, prompt_tokens, completion_tokens)

        # Add usage attributes
        span.set_attribute(LLM_USAGE_PROMPT_TOKENS, prompt_tokens)
        span.set_attribute(LLM_USAGE_COMPLETION_TOKENS, completion_tokens)
        span.set_attribute(LLM_USAGE_TOTAL_TOKENS, total_tokens)
        span.set_attribute(LLM_COST_USD, cost)

        # Handle privacy: hash by default, store content if allowed
        if prompt_messages:
            prompt_hash = hash_prompt(prompt_messages)
            span.set_attribute(LLM_PROMPT_HASH, prompt_hash)
            if settings.allow_content_capture:
                # Store first message content as example
                if prompt_messages and isinstance(prompt_messages[0], dict):
                    span.set_attribute(LLM_PROMPT_CONTENT, str(prompt_messages[0].get("content", ""))[:500])

        if response_content:
            response_hash = hash_response(response_content)
            span.set_attribute(LLM_RESPONSE_HASH, response_hash)
            if settings.allow_content_capture:
                span.set_attribute(LLM_RESPONSE_CONTENT, response_content[:1000])

        # Calculate latency if start_time provided
        if start_time:
            latency_ms = (time.time() - start_time) * 1000
            span.set_attribute("llm.latency_ms", latency_ms)

        # Add tenant from baggage
        tenant_id = baggage.get_baggage(WORKFLOW_TENANT_ID)
        if tenant_id:
            span.set_attribute(WORKFLOW_TENANT_ID, tenant_id)

        # Queue for async DB write if repo available
        if self.span_repo:
            self._queue_span_write(span, model, prompt_tokens, completion_tokens, cost)

    def _queue_span_write(
        self,
        span: Span,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float,
    ) -> None:
        """Queue span summary for async database write."""
        span_context = span.get_span_context()
        if not span_context.is_valid:
            return

        # Capture tenant_id from baggage or span attributes
        # Try baggage first, then check span attributes (set by enrich_api_span)
        tenant_id = baggage.get_baggage(WORKFLOW_TENANT_ID)
        if not tenant_id:
            # Fallback to span attribute if baggage not available
            tenant_id = span.attributes.get(WORKFLOW_TENANT_ID) if hasattr(span, 'attributes') else None
        tenant_id = tenant_id or "default"

        # Get parent span_id - span.parent is a SpanContext, so we can access span_id directly
        parent_span_id = None
        if span.parent:
            parent_span_id = f"{span.parent.span_id:016x}"

        # Enhance span name with function name if available
        span_name = span.name
        if hasattr(span, 'attributes') and span.attributes:
            function_name = span.attributes.get("function.name")
            if function_name:
                # Update name to include function: "llm.request" -> "llm.request (generate_query)"
                clean_name = function_name.replace("_", "").replace("generatequery", "generate_query").replace("summarizeresults", "summarize_results")
                span_name = f"{span.name} ({clean_name})"

        summary = {
            "trace_id": f"{span_context.trace_id:032x}",
            "span_id": f"{span_context.span_id:016x}",
            "parent_span_id": parent_span_id,
            "name": span_name,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost_usd": cost,
            "start_time": span.start_time / 1e9,  # Convert nanoseconds to seconds
            "duration_ms": (span.end_time - span.start_time) / 1e6 if span.end_time else None,
            "tenant_id": tenant_id,
        }
        self._write_queue.put(summary)

    def _start_async_writer(self) -> None:
        """Start background thread to write spans from queue."""
        def writer_loop():
            while True:
                try:
                    summary = self._write_queue.get(timeout=1.0)
                    if summary is None:  # Shutdown signal
                        break
                    self.span_repo.create_span_summary(summary)
                except Empty:
                    # Timeout is normal - just continue waiting
                    continue
                except Exception as e:
                    # Log actual errors but don't crash
                    import structlog
                    logger = structlog.get_logger()
                    logger.error("Failed to write span", error=str(e), exc_info=True)

        self._executor.submit(writer_loop)

    def enrich_api_span(
        self,
        span: Span,
        operation: str,
        latency_ms: float,
        request_size: Optional[int],
        cost: float,
    ) -> None:
        """
        Enrich API span (Pinecone, etc.) with attributes and queue for DB write.
        
        Args:
            span: OpenTelemetry span
            operation: API operation name (e.g., "query", "upsert")
            latency_ms: Latency in milliseconds
            request_size: Request size (e.g., number of vectors, queries)
            cost: Cost in USD
        """
        span_context = span.get_span_context()
        if not span_context.is_valid:
            return

        # Get tenant from baggage
        tenant_id = baggage.get_baggage(WORKFLOW_TENANT_ID) or "default"
        if tenant_id:
            span.set_attribute(WORKFLOW_TENANT_ID, tenant_id)

        # Queue for async DB write if repo available
        if self.span_repo:
            self._queue_api_span_write(span, operation, latency_ms, request_size, cost)

    def _queue_api_span_write(
        self,
        span: Span,
        operation: str,
        latency_ms: float,
        request_size: Optional[int],
        cost: float,
    ) -> None:
        """Queue API span summary for async database write."""
        span_context = span.get_span_context()
        if not span_context.is_valid:
            return

        # Capture tenant_id from baggage or span attributes
        # Try baggage first, then check span attributes (set by enrich_api_span)
        tenant_id = baggage.get_baggage(WORKFLOW_TENANT_ID)
        if not tenant_id:
            # Fallback to span attribute if baggage not available
            tenant_id = span.attributes.get(WORKFLOW_TENANT_ID) if hasattr(span, 'attributes') else None
        tenant_id = tenant_id or "default"

        summary = {
            "trace_id": f"{span_context.trace_id:032x}",
            "span_id": f"{span_context.span_id:016x}",
            "parent_span_id": f"{span.parent.span_id:016x}" if span.parent else None,
            "name": span.name,
            "model": None,  # API spans don't have models
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cost_usd": cost,
            "start_time": span.start_time / 1e9,  # Convert nanoseconds to seconds
            "duration_ms": latency_ms,
            "tenant_id": tenant_id,
        }
        self._write_queue.put(summary)

    def shutdown(self) -> None:
        """Shutdown async writer."""
        self._write_queue.put(None)  # Shutdown signal
        self._executor.shutdown(wait=True)


def add_tenant_baggage(tenant_id: str) -> None:
    """Add tenant_id to OpenTelemetry baggage for propagation."""
    baggage.set_baggage(WORKFLOW_TENANT_ID, tenant_id)

