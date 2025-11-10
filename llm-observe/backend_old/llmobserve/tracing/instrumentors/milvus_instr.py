"""Milvus auto-instrumentation for OpenTelemetry."""

import functools
import time
from typing import Any, Callable, Optional

from opentelemetry import trace

from llmobserve.pricing import pricing_registry
from llmobserve.semantics import API_COST_USD, API_LATENCY_MS, API_OPERATION, API_PROVIDER
from llmobserve.tracing.enrichers import SpanEnricher
from llmobserve.tracing.instrumentors.base import Instrumentor, ensure_root_span

tracer = trace.get_tracer(__name__)


class MilvusInstrumentor(Instrumentor):
    """Auto-instrumentation for Milvus library."""

    def __init__(self, span_enricher: Optional[SpanEnricher] = None):
        self.span_enricher = span_enricher or SpanEnricher()
        self._instrumented = False

    def instrument(self) -> None:
        if self._instrumented:
            return
        try:
            import pymilvus
            # Wrap Collection.search() and Collection.query()
            if hasattr(pymilvus, "Collection"):
                original_init = pymilvus.Collection.__init__
                def patched_init(collection_self, *args, **kwargs):
                    original_init(collection_self, *args, **kwargs)
                    if not hasattr(collection_self, "_llmobserve_instrumented"):
                        if hasattr(collection_self, "search"):
                            # Prevents duplicate instrumentation during reloads or multiple setup calls
                            if not hasattr(collection_self.search, "_instrumented"):
                                wrapped = self._wrap_method("search", collection_self.search)
                                wrapped._instrumented = True
                                collection_self.search = wrapped
                        if hasattr(collection_self, "query"):
                            # Prevents duplicate instrumentation during reloads or multiple setup calls
                            if not hasattr(collection_self.query, "_instrumented"):
                                wrapped = self._wrap_method("query", collection_self.query)
                                wrapped._instrumented = True
                                collection_self.query = wrapped
                        collection_self._llmobserve_instrumented = True
                pymilvus.Collection.__init__ = patched_init
            self._instrumented = True
        except ImportError:
            pass
        except Exception:
            pass

    def uninstrument(self) -> None:
        self._instrumented = False

    def _wrap_method(self, operation: str, original_func: Callable) -> Callable:
        @functools.wraps(original_func)
        def wrapper(*args, **kwargs):
            return self._trace_call(operation, original_func, *args, **kwargs)
        return wrapper

    def _trace_call(self, operation: str, original_func: Callable, *args, **kwargs) -> Any:
        start_time = time.time()
        with ensure_root_span("milvus"):
            with tracer.start_as_current_span(f"milvus.{operation}") as span:
                span.set_attribute(API_PROVIDER, "milvus")
                span.set_attribute(API_OPERATION, operation)
                result = None
                error_occurred = False
                try:
                    result = original_func(*args, **kwargs)
                    return result
                except Exception as e:
                    error_occurred = True
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
                finally:
                    # Ensures cost is logged even if the API call raises an exception
                    latency_ms = (time.time() - start_time) * 1000
                    cost = 0.0 if error_occurred else pricing_registry.cost_for_vector_db("milvus", operation, 1)
                    span.set_attribute(API_LATENCY_MS, latency_ms)
                    span.set_attribute(API_COST_USD, cost)
                    if self.span_enricher:
                        try:
                            self.span_enricher.enrich_vector_span(span, "milvus", operation, latency_ms, 1, cost)
                        except Exception:
                            pass  # Don't fail if enrichment fails
