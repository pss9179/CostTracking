"""VoyageAI auto-instrumentation for OpenTelemetry."""

import functools
import time
from typing import Any, Callable, Optional

from opentelemetry import trace

from llmobserve.pricing import pricing_registry
from llmobserve.semantics import API_COST_USD, API_LATENCY_MS, API_OPERATION, API_PROVIDER
from llmobserve.tracing.enrichers import SpanEnricher
from llmobserve.tracing.instrumentors.base import Instrumentor, ensure_root_span

tracer = trace.get_tracer(__name__)


class VoyageAIInstrumentor(Instrumentor):
    """Auto-instrumentation for VoyageAI embeddings library."""

    def __init__(self, span_enricher: Optional[SpanEnricher] = None):
        """Initialize with optional span enricher."""
        self.span_enricher = span_enricher or SpanEnricher()
        self._instrumented = False

    def instrument(self) -> None:
        """Apply VoyageAI instrumentation."""
        if self._instrumented:
            return

        try:
            import voyageai

            # Wrap Client.embeddings.create()
            if hasattr(voyageai, "Client"):
                original_init = voyageai.Client.__init__

                def patched_init(client_self, *args, **kwargs):
                    original_init(client_self, *args, **kwargs)
                    if not hasattr(client_self, "_llmobserve_instrumented"):
                        if hasattr(client_self, "embeddings") and hasattr(client_self.embeddings, "create"):
                            # Prevents duplicate instrumentation during reloads or multiple setup calls
                            if not hasattr(client_self.embeddings.create, "_instrumented"):
                                original_create = client_self.embeddings.create
                                wrapped = self._wrap_embed(original_create)
                                wrapped._instrumented = True
                                client_self.embeddings.create = wrapped
                        client_self._llmobserve_instrumented = True

                voyageai.Client.__init__ = patched_init

            self._instrumented = True
        except ImportError:
            import structlog
            logger = structlog.get_logger()
            logger.warning("VoyageAI not installed, skipping instrumentation")
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Failed to instrument VoyageAI", error=str(e))

    def uninstrument(self) -> None:
        """Remove VoyageAI instrumentation."""
        self._instrumented = False

    def _wrap_embed(self, original_func: Callable) -> Callable:
        """Wrap embeddings.create()."""
        @functools.wraps(original_func)
        def wrapper(*args, **kwargs):
            return self._trace_embed(original_func, *args, **kwargs)
        return wrapper

    def _trace_embed(self, original_func: Callable, *args, **kwargs) -> Any:
        """Trace an embed call."""
        start_time = time.time()
        model = kwargs.get("model", "voyage-2")

        with ensure_root_span("voyageai"):
            with tracer.start_as_current_span("api.embed") as span:
                span.set_attribute(API_PROVIDER, "voyageai")
                span.set_attribute(API_OPERATION, "embed")
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

                    # Estimate tokens, default to 0 if failed
                    prompt_tokens = 0
                    if not error_occurred:
                        try:
                            input_text = kwargs.get("input", [])
                            if isinstance(input_text, list):
                                input_text = " ".join(input_text)
                            prompt_tokens = int(len(input_text.split()) * 1.3) if input_text else 0
                        except Exception:
                            prompt_tokens = 0
                    
                    cost = pricing_registry.cost_for(model, prompt_tokens, 0) if not error_occurred else 0.0
                    span.set_attribute(API_COST_USD, cost)

                    if self.span_enricher:
                        try:
                            self.span_enricher.enrich_api_span(span, "embed", latency_ms, 1, cost)
                        except Exception:
                            pass  # Don't fail if enrichment fails
