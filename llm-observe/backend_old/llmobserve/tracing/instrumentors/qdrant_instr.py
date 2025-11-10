"""Qdrant auto-instrumentation for OpenTelemetry."""

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


class QdrantInstrumentor(Instrumentor):
    """Auto-instrumentation for Qdrant library."""

    def __init__(self, span_enricher: Optional[SpanEnricher] = None):
        """Initialize with optional span enricher."""
        self.span_enricher = span_enricher or SpanEnricher()
        self._instrumented = False

    def instrument(self) -> None:
        """Apply Qdrant instrumentation."""
        if self._instrumented:
            return

        try:
            import qdrant_client

            # Wrap QdrantClient.search(), scroll(), retrieve()
            if hasattr(qdrant_client, "QdrantClient"):
                original_init = qdrant_client.QdrantClient.__init__

                def patched_init(client_self, *args, **kwargs):
                    original_init(client_self, *args, **kwargs)
                    if not hasattr(client_self, "_llmobserve_instrumented"):
                        if hasattr(client_self, "search"):
                            # Prevents duplicate instrumentation during reloads or multiple setup calls
                            if not hasattr(client_self.search, "_instrumented"):
                                original_search = client_self.search
                                wrapped = self._wrap_search(original_search)
                                wrapped._instrumented = True
                                client_self.search = MethodType(wrapped, client_self)
                        if hasattr(client_self, "scroll"):
                            # Prevents duplicate instrumentation during reloads or multiple setup calls
                            if not hasattr(client_self.scroll, "_instrumented"):
                                original_scroll = client_self.scroll
                                wrapped = self._wrap_scroll(original_scroll)
                                wrapped._instrumented = True
                                client_self.scroll = MethodType(wrapped, client_self)
                        if hasattr(client_self, "retrieve"):
                            # Prevents duplicate instrumentation during reloads or multiple setup calls
                            if not hasattr(client_self.retrieve, "_instrumented"):
                                original_retrieve = client_self.retrieve
                                wrapped = self._wrap_retrieve(original_retrieve)
                                wrapped._instrumented = True
                                client_self.retrieve = MethodType(wrapped, client_self)
                        client_self._llmobserve_instrumented = True

                qdrant_client.QdrantClient.__init__ = patched_init

            self._instrumented = True
        except ImportError:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Qdrant not installed, skipping instrumentation")
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Failed to instrument Qdrant", error=str(e))

    def uninstrument(self) -> None:
        """Remove Qdrant instrumentation."""
        self._instrumented = False

    def _wrap_search(self, original_func: Callable) -> Callable:
        """Wrap search()."""
        @functools.wraps(original_func)
        def wrapper(self_instance, *args, **kwargs):
            return self._trace_api_call("search", original_func, self_instance, *args, **kwargs)
        return wrapper

    def _wrap_scroll(self, original_func: Callable) -> Callable:
        """Wrap scroll()."""
        @functools.wraps(original_func)
        def wrapper(self_instance, *args, **kwargs):
            return self._trace_api_call("scroll", original_func, self_instance, *args, **kwargs)
        return wrapper

    def _wrap_retrieve(self, original_func: Callable) -> Callable:
        """Wrap retrieve()."""
        @functools.wraps(original_func)
        def wrapper(self_instance, *args, **kwargs):
            return self._trace_api_call("retrieve", original_func, self_instance, *args, **kwargs)
        return wrapper

    def _trace_api_call(self, operation: str, original_func: Callable, client_self: Any, *args, **kwargs) -> Any:
        """Trace a Qdrant API call."""
        start_time = time.time()
        span_name = f"qdrant.{operation}"

        # Extract collection name (first positional arg or from kwargs)
        collection_name = args[0] if args else kwargs.get("collection_name", "unknown")
        top_k = kwargs.get("limit") or kwargs.get("top", 0)

        with ensure_root_span("qdrant"):
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute(API_PROVIDER, "qdrant")
                span.set_attribute(API_OPERATION, operation)
                span.set_attribute("vector.provider", "qdrant")
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

                    # Calculate cost (default to 0 if request failed)
                    cost = 0.0 if error_occurred else pricing_registry.cost_for_vector_db("qdrant", operation, 1)
                    span.set_attribute(API_COST_USD, cost)
                    span.set_attribute("vector.cost_usd", cost)

                    # Enrich span
                    if self.span_enricher:
                        try:
                            self.span_enricher.enrich_vector_span(
                                span, "qdrant", operation, latency_ms, 1, cost, collection_name, top_k
                            )
                        except Exception:
                            pass  # Don't fail if enrichment fails

