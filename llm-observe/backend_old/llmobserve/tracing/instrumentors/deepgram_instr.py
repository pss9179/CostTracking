"""Deepgram auto-instrumentation for OpenTelemetry."""

import functools
import time
from typing import Any, Callable, Optional

from opentelemetry import trace

from llmobserve.pricing import pricing_registry
from llmobserve.semantics import API_COST_USD, API_LATENCY_MS, API_OPERATION, API_PROVIDER
from llmobserve.tracing.enrichers import SpanEnricher
from llmobserve.tracing.instrumentors.base import Instrumentor, ensure_root_span

tracer = trace.get_tracer(__name__)


class DeepgramInstrumentor(Instrumentor):
    """Auto-instrumentation for Deepgram speech-to-text API."""

    def __init__(self, span_enricher: Optional[SpanEnricher] = None):
        """Initialize with optional span enricher."""
        self.span_enricher = span_enricher or SpanEnricher()
        self._instrumented = False

    def instrument(self) -> None:
        """Apply Deepgram instrumentation."""
        if self._instrumented:
            return

        try:
            import deepgram

            # Wrap DeepgramClient.listen.prerecorded.v1.transcribe_file()
            if hasattr(deepgram, "DeepgramClient"):
                original_init = deepgram.DeepgramClient.__init__

                def patched_init(client_self, *args, **kwargs):
                    original_init(client_self, *args, **kwargs)
                    if not hasattr(client_self, "_llmobserve_instrumented"):
                        # Navigate to listen.prerecorded.v1.transcribe_file
                        if hasattr(client_self, "listen"):
                            listen_obj = client_self.listen
                            if hasattr(listen_obj, "prerecorded"):
                                prerecorded_obj = listen_obj.prerecorded
                                if hasattr(prerecorded_obj, "v1"):
                                    v1_obj = prerecorded_obj.v1
                                    if hasattr(v1_obj, "transcribe_file"):
                                        # Prevents duplicate instrumentation during reloads or multiple setup calls
                                        if not hasattr(v1_obj.transcribe_file, "_instrumented"):
                                            original_transcribe = v1_obj.transcribe_file
                                            wrapped = self._wrap_transcribe(original_transcribe)
                                            wrapped._instrumented = True
                                            v1_obj.transcribe_file = wrapped
                        client_self._llmobserve_instrumented = True

                deepgram.DeepgramClient.__init__ = patched_init

            self._instrumented = True
        except ImportError:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Deepgram not installed, skipping instrumentation")
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Failed to instrument Deepgram", error=str(e))

    def uninstrument(self) -> None:
        """Remove Deepgram instrumentation."""
        self._instrumented = False

    def _wrap_transcribe(self, original_func: Callable) -> Callable:
        """Wrap transcribe_file()."""
        @functools.wraps(original_func)
        def wrapper(*args, **kwargs):
            return self._trace_transcribe(original_func, *args, **kwargs)
        return wrapper

    def _trace_transcribe(self, original_func: Callable, *args, **kwargs) -> Any:
        """Trace a transcribe call."""
        start_time = time.time()
        model = kwargs.get("model", "nova-2")

        with ensure_root_span("deepgram"):
            with tracer.start_as_current_span("api.transcribe") as span:
                span.set_attribute(API_PROVIDER, "deepgram")
                span.set_attribute(API_OPERATION, "transcribe")
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

                    # Deepgram pricing is per minute of audio, default to 0 if failed
                    duration_minutes = 1.0  # Default estimate
                    if not error_occurred and response is not None:
                        try:
                            if hasattr(response, "metadata") and hasattr(response.metadata, "duration"):
                                duration_minutes = response.metadata.duration / 60.0
                        except Exception:
                            duration_minutes = 1.0
                    
                    cost = 0.0 if error_occurred else pricing_registry.cost_for_vector_db("deepgram", "transcribe", int(duration_minutes * 60))
                    span.set_attribute(API_COST_USD, cost)

                    if self.span_enricher:
                        try:
                            self.span_enricher.enrich_api_span(span, "transcribe", latency_ms, 1, cost)
                        except Exception:
                            pass  # Don't fail if enrichment fails
