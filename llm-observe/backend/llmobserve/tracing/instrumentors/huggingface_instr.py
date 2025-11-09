"""HuggingFace Inference API auto-instrumentation for OpenTelemetry."""

import functools
import time
from typing import Any, Callable, Optional

from opentelemetry import trace

from llmobserve.pricing import pricing_registry
from llmobserve.semantics import API_COST_USD, API_LATENCY_MS, API_OPERATION, API_PROVIDER
from llmobserve.tracing.enrichers import SpanEnricher
from llmobserve.tracing.instrumentors.base import Instrumentor, ensure_root_span

tracer = trace.get_tracer(__name__)


class HuggingFaceInstrumentor(Instrumentor):
    """Auto-instrumentation for HuggingFace Inference API."""

    def __init__(self, span_enricher: Optional[SpanEnricher] = None):
        """Initialize with optional span enricher."""
        self.span_enricher = span_enricher or SpanEnricher()
        self._instrumented = False

    def instrument(self) -> None:
        """Apply HuggingFace instrumentation."""
        if self._instrumented:
            return

        try:
            import huggingface_hub

            # Wrap InferenceClient.text_generation() and feature_extraction()
            if hasattr(huggingface_hub, "InferenceClient"):
                original_init = huggingface_hub.InferenceClient.__init__

                def patched_init(client_self, *args, **kwargs):
                    original_init(client_self, *args, **kwargs)
                    if not hasattr(client_self, "_llmobserve_instrumented"):
                        if hasattr(client_self, "text_generation"):
                            # Prevents duplicate instrumentation during reloads or multiple setup calls
                            if not hasattr(client_self.text_generation, "_instrumented"):
                                wrapped = self._wrap_text_generation(client_self.text_generation)
                                wrapped._instrumented = True
                                client_self.text_generation = wrapped
                        if hasattr(client_self, "feature_extraction"):
                            # Prevents duplicate instrumentation during reloads or multiple setup calls
                            if not hasattr(client_self.feature_extraction, "_instrumented"):
                                wrapped = self._wrap_feature_extraction(client_self.feature_extraction)
                                wrapped._instrumented = True
                                client_self.feature_extraction = wrapped
                        client_self._llmobserve_instrumented = True

                huggingface_hub.InferenceClient.__init__ = patched_init

            self._instrumented = True
        except ImportError:
            import structlog
            logger = structlog.get_logger()
            logger.warning("HuggingFace Hub not installed, skipping instrumentation")
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Failed to instrument HuggingFace", error=str(e))

    def uninstrument(self) -> None:
        """Remove HuggingFace instrumentation."""
        self._instrumented = False

    def _wrap_text_generation(self, original_func: Callable) -> Callable:
        """Wrap text_generation()."""
        @functools.wraps(original_func)
        def wrapper(*args, **kwargs):
            return self._trace_api_call("text_generation", original_func, *args, **kwargs)
        return wrapper

    def _wrap_feature_extraction(self, original_func: Callable) -> Callable:
        """Wrap feature_extraction()."""
        @functools.wraps(original_func)
        def wrapper(*args, **kwargs):
            return self._trace_api_call("feature_extraction", original_func, *args, **kwargs)
        return wrapper

    def _trace_api_call(self, operation: str, original_func: Callable, *args, **kwargs) -> Any:
        """Trace an API call."""
        start_time = time.time()
        model = kwargs.get("model") or (args[0] if args else "unknown")

        with ensure_root_span("huggingface"):
            with tracer.start_as_current_span(f"api.{operation}") as span:
                span.set_attribute(API_PROVIDER, "huggingface")
                span.set_attribute(API_OPERATION, operation)
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

                    cost = 0.0 if error_occurred else pricing_registry.cost_for_vector_db("huggingface", operation, 1)
                    span.set_attribute(API_COST_USD, cost)

                    if self.span_enricher:
                        try:
                            self.span_enricher.enrich_api_span(span, operation, latency_ms, 1, cost)
                        except Exception:
                            pass  # Don't fail if enrichment fails
