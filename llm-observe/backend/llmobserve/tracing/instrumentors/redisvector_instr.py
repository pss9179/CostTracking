"""RedisVector auto-instrumentation for OpenTelemetry."""

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


class RedisVectorInstrumentor(Instrumentor):
    """Auto-instrumentation for RedisVector (redis-py with vector search)."""

    def __init__(self, span_enricher: Optional[SpanEnricher] = None):
        """Initialize with optional span enricher."""
        self.span_enricher = span_enricher or SpanEnricher()
        self._instrumented = False

    def instrument(self) -> None:
        """Apply RedisVector instrumentation."""
        if self._instrumented:
            return

        try:
            import redis
            from redis.commands.search import Search

            # Wrap Search.search() and Search.ft() (FT.SEARCH)
            if hasattr(redis, "Redis"):
                original_init = redis.Redis.__init__

                def patched_init(redis_self, *args, **kwargs):
                    original_init(redis_self, *args, **kwargs)
                    if not hasattr(redis_self, "_llmobserve_instrumented"):
                        # Wrap ft() method which returns Search object
                        if hasattr(redis_self, "ft"):
                            original_ft = redis_self.ft

                            def wrapped_ft(index_name: str):
                                search_obj = original_ft(index_name)
                                if not hasattr(search_obj, "_llmobserve_instrumented"):
                                    if hasattr(search_obj, "search"):
                                        # Prevents duplicate instrumentation during reloads or multiple setup calls
                                        if not hasattr(search_obj.search, "_instrumented"):
                                            wrapped = self._wrap_search(search_obj.search, index_name)
                                            wrapped._instrumented = True
                                            search_obj.search = MethodType(wrapped, search_obj)
                                    search_obj._llmobserve_instrumented = True
                                return search_obj

                            redis_self.ft = wrapped_ft
                        redis_self._llmobserve_instrumented = True

                redis.Redis.__init__ = patched_init

            self._instrumented = True
        except ImportError:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Redis not installed, skipping RedisVector instrumentation")
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Failed to instrument RedisVector", error=str(e))

    def uninstrument(self) -> None:
        """Remove RedisVector instrumentation."""
        self._instrumented = False

    def _wrap_search(self, original_func: Callable, index_name: str) -> Callable:
        """Wrap Search.search()."""
        @functools.wraps(original_func)
        def wrapper(self_instance, *args, **kwargs):
            return self._trace_call("search", original_func, self_instance, index_name, *args, **kwargs)
        return wrapper

    def _trace_call(self, operation: str, original_func: Callable, search_self: Any, index_name: str, *args, **kwargs) -> Any:
        """Trace a RedisVector API call."""
        start_time = time.time()
        span_name = f"redisvector.{operation}"

        # Extract limit/top_k from query or kwargs
        top_k = kwargs.get("limit") or kwargs.get("num", 0)

        with ensure_root_span("redisvector"):
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute(API_PROVIDER, "redisvector")
                span.set_attribute(API_OPERATION, operation)
                span.set_attribute("vector.provider", "redisvector")
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

                    cost = 0.0 if error_occurred else pricing_registry.cost_for_vector_db("redisvector", operation, 1)
                    span.set_attribute(API_COST_USD, cost)
                    span.set_attribute("vector.cost_usd", cost)

                    if self.span_enricher:
                        try:
                            self.span_enricher.enrich_vector_span(
                                span, "redisvector", operation, latency_ms, 1, cost, index_name, top_k
                            )
                        except Exception:
                            pass  # Don't fail if enrichment fails
