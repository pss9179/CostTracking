"""Replicate auto-instrumentation for OpenTelemetry."""

import functools
import time
from typing import Any, Callable, Optional

from opentelemetry import trace

from llmobserve.pricing import pricing_registry
from llmobserve.semantics import API_COST_USD, API_LATENCY_MS, API_OPERATION, API_PROVIDER
from llmobserve.tracing.enrichers import SpanEnricher
from llmobserve.tracing.instrumentors.base import Instrumentor, ensure_root_span

tracer = trace.get_tracer(__name__)


class ReplicateInstrumentor(Instrumentor):
    """Auto-instrumentation for Replicate inference API."""

    def __init__(self, span_enricher: Optional[SpanEnricher] = None):
        """Initialize with optional span enricher."""
        self.span_enricher = span_enricher or SpanEnricher()
        self._instrumented = False

    def instrument(self) -> None:
        """Apply Replicate instrumentation."""
        if self._instrumented:
            return

        try:
            import replicate

            # Wrap Client.run()
            if hasattr(replicate, "Client"):
                original_init = replicate.Client.__init__

                def patched_init(client_self, *args, **kwargs):
                    original_init(client_self, *args, **kwargs)
                    if not hasattr(client_self, "_llmobserve_instrumented"):
                        if hasattr(client_self, "run"):
                            # Prevents duplicate instrumentation during reloads or multiple setup calls
                            if not hasattr(client_self.run, "_instrumented"):
                                original_run = client_self.run
                                wrapped = self._wrap_run(original_run)
                                wrapped._instrumented = True
                                client_self.run = wrapped
                        client_self._llmobserve_instrumented = True

                replicate.Client.__init__ = patched_init

            # Also wrap module-level run() if it exists
            if hasattr(replicate, "run"):
                # Prevents duplicate instrumentation during reloads or multiple setup calls
                if not hasattr(replicate.run, "_instrumented"):
                    original_module_run = replicate.run
                    wrapped = self._wrap_run(original_module_run)
                    wrapped._instrumented = True
                    replicate.run = wrapped

            self._instrumented = True
        except ImportError:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Replicate not installed, skipping instrumentation")
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Failed to instrument Replicate", error=str(e))

    def uninstrument(self) -> None:
        """Remove Replicate instrumentation."""
        self._instrumented = False

    def _wrap_run(self, original_func: Callable) -> Callable:
        """Wrap run()."""
        @functools.wraps(original_func)
        def wrapper(*args, **kwargs):
            return self._trace_run(original_func, *args, **kwargs)
        return wrapper

    def _trace_run(self, original_func: Callable, *args, **kwargs) -> Any:
        """Trace a run() call."""
        start_time = time.time()
        # Extract model from first positional arg (model identifier)
        model = args[0] if args else kwargs.get("model", "unknown")

        with ensure_root_span("replicate"):
            with tracer.start_as_current_span("api.run") as span:
                span.set_attribute(API_PROVIDER, "replicate")
                span.set_attribute(API_OPERATION, "run")
                span.set_attribute("ai.model", model)

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

                    # Replicate pricing varies by model - use generic pricing, default to 0 if failed
                    cost = 0.0 if error_occurred else pricing_registry.cost_for_vector_db("replicate", "run", 1)
                    span.set_attribute(API_COST_USD, cost)

                    if self.span_enricher:
                        try:
                            self.span_enricher.enrich_api_span(span, "run", latency_ms, 1, cost)
                        except Exception:
                            pass  # Don't fail if enrichment fails
