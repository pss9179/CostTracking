"""Chroma auto-instrumentation for OpenTelemetry."""

import functools
import time
from types import MethodType
from typing import Any, Callable, Optional

from opentelemetry import trace

from llmobserve.pricing import pricing_registry
from llmobserve.semantics import API_COST_USD, API_LATENCY_MS, API_OPERATION, API_PROVIDER
from llmobserve.tracing.enrichers import SpanEnricher
from llmobserve.tracing.instrumentors.base import Instrumentor, ensure_root_span

tracer = trace.get_tracer(__name__)


class ChromaInstrumentor(Instrumentor):
    """Auto-instrumentation for Chroma library."""

    def __init__(self, span_enricher: Optional[SpanEnricher] = None):
        """Initialize with optional span enricher."""
        self.span_enricher = span_enricher or SpanEnricher()
        self._instrumented = False

    def instrument(self) -> None:
        """Apply Chroma instrumentation."""
        if self._instrumented:
            return

        try:
            import chromadb

            # Wrap Collection.query() and Collection.get()
            if hasattr(chromadb, "Client"):
                original_client_init = chromadb.Client.__init__

                def patched_client_init(client_self, *args, **kwargs):
                    original_client_init(client_self, *args, **kwargs)
                    if not hasattr(client_self, "_llmobserve_instrumented"):
                        # Chroma collections are accessed via client.get_or_create_collection()
                        # We need to wrap the collection methods when collections are created
                        original_get_collection = client_self.get_or_create_collection

                        def wrapped_get_collection(*col_args, **col_kwargs):
                            collection = original_get_collection(*col_args, **col_kwargs)
                            if not hasattr(collection, "_llmobserve_instrumented"):
                                if hasattr(collection, "query"):
                                    # Prevents duplicate instrumentation during reloads or multiple setup calls
                                    if not hasattr(collection.query, "_instrumented"):
                                        wrapped = self._wrap_query(collection.query)
                                        wrapped._instrumented = True
                                        collection.query = MethodType(wrapped, collection)
                                if hasattr(collection, "get"):
                                    # Prevents duplicate instrumentation during reloads or multiple setup calls
                                    if not hasattr(collection.get, "_instrumented"):
                                        wrapped = self._wrap_get(collection.get)
                                        wrapped._instrumented = True
                                        collection.get = MethodType(wrapped, collection)
                                collection._llmobserve_instrumented = True
                            return collection

                        client_self.get_or_create_collection = wrapped_get_collection
                        client_self._llmobserve_instrumented = True

                chromadb.Client.__init__ = patched_client_init

            self._instrumented = True
        except ImportError:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Chroma not installed, skipping instrumentation")
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Failed to instrument Chroma", error=str(e))

    def uninstrument(self) -> None:
        """Remove Chroma instrumentation."""
        self._instrumented = False

    def _wrap_query(self, original_func: Callable) -> Callable:
        """Wrap Collection.query()."""
        @functools.wraps(original_func)
        def wrapper(self_instance, *args, **kwargs):
            return self._trace_call("query", original_func, self_instance, *args, **kwargs)
        return wrapper

    def _wrap_get(self, original_func: Callable) -> Callable:
        """Wrap Collection.get()."""
        @functools.wraps(original_func)
        def wrapper(self_instance, *args, **kwargs):
            return self._trace_call("get", original_func, self_instance, *args, **kwargs)
        return wrapper

    def _trace_call(self, operation: str, original_func: Callable, collection_self: Any, *args, **kwargs) -> Any:
        """Trace a Chroma API call."""
        start_time = time.time()
        span_name = f"chroma.{operation}"

        # Extract collection name
        collection_name = getattr(collection_self, "name", "unknown")
        top_k = kwargs.get("n_results") or kwargs.get("limit", 0)

        with ensure_root_span("chroma"):
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute(API_PROVIDER, "chroma")
                span.set_attribute(API_OPERATION, operation)
                span.set_attribute("vector.provider", "chroma")
                if collection_name != "unknown":
                    span.set_attribute("vector.index_name", collection_name)
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

                    cost = 0.0 if error_occurred else pricing_registry.cost_for_vector_db("chroma", operation, 1)
                    span.set_attribute(API_COST_USD, cost)
                    span.set_attribute("vector.cost_usd", cost)

                    if self.span_enricher:
                        try:
                            self.span_enricher.enrich_vector_span(
                                span, "chroma", operation, latency_ms, 1, cost, collection_name, top_k
                            )
                        except Exception:
                            pass  # Don't fail if enrichment fails
