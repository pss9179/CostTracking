"""Weaviate auto-instrumentation for OpenTelemetry."""

import functools
import time
from types import MethodType
from typing import Any, Callable, Optional

from opentelemetry import trace

from llmobserve.pricing import pricing_registry
from llmobserve.semantics import API_COST_USD, API_LATENCY_MS, API_OPERATION, API_PROVIDER, API_REQUEST_SIZE
from llmobserve.tracing.enrichers import SpanEnricher
from llmobserve.tracing.instrumentors.base import Instrumentor, ensure_root_span

tracer = trace.get_tracer(__name__)


class WeaviateInstrumentor(Instrumentor):
    """Auto-instrumentation for Weaviate library."""

    def __init__(self, span_enricher: Optional[SpanEnricher] = None):
        """Initialize with optional span enricher."""
        self.span_enricher = span_enricher or SpanEnricher()
        self._instrumented = False

    def instrument(self) -> None:
        """Apply Weaviate instrumentation."""
        if self._instrumented:
            return

        try:
            import weaviate

            # Wrap Client.query.get() and Client.query.near_text()
            if hasattr(weaviate, "Client"):
                original_init = weaviate.Client.__init__

                def patched_init(client_self, *args, **kwargs):
                    original_init(client_self, *args, **kwargs)
                    if not hasattr(client_self, "_llmobserve_instrumented"):
                        # Wrap query.get()
                        if hasattr(client_self, "query"):
                            query_obj = client_self.query
                            if hasattr(query_obj, "get"):
                                # Prevents duplicate instrumentation during reloads or multiple setup calls
                                if not hasattr(query_obj.get, "_instrumented"):
                                    original_get = query_obj.get
                                    wrapped = self._wrap_get(original_get)
                                    wrapped._instrumented = True
                                    query_obj.get = MethodType(wrapped, query_obj)
                            if hasattr(query_obj, "near_text"):
                                # Prevents duplicate instrumentation during reloads or multiple setup calls
                                if not hasattr(query_obj.near_text, "_instrumented"):
                                    original_near_text = query_obj.near_text
                                    wrapped = self._wrap_near_text(original_near_text)
                                    wrapped._instrumented = True
                                    query_obj.near_text = MethodType(wrapped, query_obj)
                        client_self._llmobserve_instrumented = True

                weaviate.Client.__init__ = patched_init

            self._instrumented = True
        except ImportError:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Weaviate not installed, skipping instrumentation")
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Failed to instrument Weaviate", error=str(e))

    def uninstrument(self) -> None:
        """Remove Weaviate instrumentation."""
        self._instrumented = False

    def _wrap_get(self, original_func: Callable) -> Callable:
        """Wrap query.get()."""
        @functools.wraps(original_func)
        def wrapper(self_instance, *args, **kwargs):
            return self._trace_query("get", original_func, self_instance, *args, **kwargs)
        return wrapper

    def _wrap_near_text(self, original_func: Callable) -> Callable:
        """Wrap query.near_text()."""
        @functools.wraps(original_func)
        def wrapper(self_instance, *args, **kwargs):
            return self._trace_query("near_text", original_func, self_instance, *args, **kwargs)
        return wrapper

    def _trace_query(self, operation: str, original_func: Callable, query_self: Any, *args, **kwargs) -> Any:
        """Trace a Weaviate query call."""
        start_time = time.time()
        span_name = f"weaviate.query.{operation}"

        # Extract class name (index name) from query builder
        index_name = "unknown"
        if hasattr(query_self, "class_name"):
            index_name = query_self.class_name

        # Extract top_k/limit
        top_k = kwargs.get("limit") or kwargs.get("top_k", 0)

        with ensure_root_span("weaviate"):
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute(API_PROVIDER, "weaviate")
                span.set_attribute(API_OPERATION, operation)
                span.set_attribute("vector.provider", "weaviate")
                if index_name != "unknown":
                    span.set_attribute("vector.index_name", index_name)
                if top_k:
                    span.set_attribute("vector.top_k", top_k)

                response = None
                error_occurred = False
                try:
                    response = original_func(*args, **kwargs)
                    return response
                except Exception as e:
                    error_occurred = True
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
                finally:
                    # Ensures cost is logged even if the API call raises an exception
                    latency_ms = (time.time() - start_time) * 1000
                    span.set_attribute(API_LATENCY_MS, latency_ms)

                    # Calculate cost (default to 0 if request failed)
                    cost = 0.0 if error_occurred else pricing_registry.cost_for_vector_db("weaviate", operation, 1)
                    span.set_attribute(API_COST_USD, cost)
                    span.set_attribute("vector.cost_usd", cost)

                    # Enrich span
                    if self.span_enricher:
                        try:
                            self.span_enricher.enrich_vector_span(
                                span, "weaviate", operation, latency_ms, 1, cost, index_name, top_k
                            )
                        except Exception:
                            pass  # Don't fail if enrichment fails

