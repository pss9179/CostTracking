"""Lightweight wrapper for Pinecone Index to track costs."""

import time
from typing import Any, Optional

from opentelemetry import baggage

from llmobserve.exporter import get_exporter
from llmobserve.pricing import pricing_registry
from llmobserve.tracer import get_current_trace_id, get_current_span_id


def pinecone_index(original_index: Any) -> Any:
    """
    Wrap Pinecone Index to track costs.

    Usage:
        from llmobserve.providers import pinecone_index
        index = pinecone_index(pc.Index("my-index"))
    """
    class TrackedPineconeIndex:
        def __init__(self, index):
            self._index = index
            self._exporter = get_exporter()

        def query(self, *args, **kwargs):
            """Track query operation."""
            start_time = time.time()
            
            # Call original
            response = self._index.query(*args, **kwargs)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Get request size (top_k)
            top_k = kwargs.get("top_k", 1)
            
            # Calculate cost
            cost_usd = pricing_registry.cost_for_vector_db("pinecone", "query", request_size=top_k)
            
            # Get context
            tenant_id = baggage.get_baggage("tenant_id") or "default"
            workflow_id = baggage.get_baggage("workflow_id")
            trace_id = get_current_trace_id()
            span_id = get_current_span_id()
            
            # Record cost
            self._exporter.record_cost(
                tenant_id=tenant_id,
                provider="pinecone",
                cost_usd=cost_usd,
                duration_ms=duration_ms,
                workflow_id=workflow_id,
                trace_id=trace_id,
                span_id=span_id,
                operation="query",
            )
            
            return response

        def upsert(self, *args, **kwargs):
            """Track upsert operation."""
            start_time = time.time()
            
            # Call original
            response = self._index.upsert(*args, **kwargs)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Get request size (number of vectors)
            vectors = kwargs.get("vectors", [])
            if isinstance(vectors, list):
                request_size = len(vectors)
            else:
                request_size = 1
            
            # Calculate cost
            cost_usd = pricing_registry.cost_for_vector_db("pinecone", "upsert", request_size=request_size)
            
            # Get context
            tenant_id = baggage.get_baggage("tenant_id") or "default"
            workflow_id = baggage.get_baggage("workflow_id")
            trace_id = get_current_trace_id()
            span_id = get_current_span_id()
            
            # Record cost
            self._exporter.record_cost(
                tenant_id=tenant_id,
                provider="pinecone",
                cost_usd=cost_usd,
                duration_ms=duration_ms,
                workflow_id=workflow_id,
                trace_id=trace_id,
                span_id=span_id,
                operation="upsert",
            )
            
            return response

        def __getattr__(self, name):
            """Delegate other attributes to original index."""
            return getattr(self._index, name)

    return TrackedPineconeIndex(original_index)

