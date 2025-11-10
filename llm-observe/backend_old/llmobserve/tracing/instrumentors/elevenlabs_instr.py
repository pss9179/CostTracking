"""ElevenLabs auto-instrumentation for OpenTelemetry."""

import functools
import time
from typing import Any, Callable, Optional

from opentelemetry import trace

from llmobserve.pricing import pricing_registry
from llmobserve.semantics import API_COST_USD, API_LATENCY_MS, API_OPERATION, API_PROVIDER
from llmobserve.tracing.enrichers import SpanEnricher
from llmobserve.tracing.instrumentors.base import Instrumentor, ensure_root_span

tracer = trace.get_tracer(__name__)


class ElevenLabsInstrumentor(Instrumentor):
    """Auto-instrumentation for ElevenLabs text-to-speech API."""

    def __init__(self, span_enricher: Optional[SpanEnricher] = None):
        """Initialize with optional span enricher."""
        self.span_enricher = span_enricher or SpanEnricher()
        self._instrumented = False

    def instrument(self) -> None:
        """Apply ElevenLabs instrumentation."""
        if self._instrumented:
            return

        try:
            import elevenlabs

            # Wrap client.generate() or Client.generate()
            if hasattr(elevenlabs, "Client"):
                original_init = elevenlabs.Client.__init__

                def patched_init(client_self, *args, **kwargs):
                    original_init(client_self, *args, **kwargs)
                    if not hasattr(client_self, "_llmobserve_instrumented"):
                        if hasattr(client_self, "generate"):
                            # Prevents duplicate instrumentation during reloads or multiple setup calls
                            if not hasattr(client_self.generate, "_instrumented"):
                                wrapped = self._wrap_generate(client_self.generate)
                                wrapped._instrumented = True
                                client_self.generate = wrapped
                        client_self._llmobserve_instrumented = True

                elevenlabs.Client.__init__ = patched_init

            # Also check for module-level generate
            if hasattr(elevenlabs, "generate"):
                # Prevents duplicate instrumentation during reloads or multiple setup calls
                if not hasattr(elevenlabs.generate, "_instrumented"):
                    original_module_generate = elevenlabs.generate
                    wrapped = self._wrap_generate(original_module_generate)
                    wrapped._instrumented = True
                    elevenlabs.generate = wrapped

            self._instrumented = True
        except ImportError:
            import structlog
            logger = structlog.get_logger()
            logger.warning("ElevenLabs not installed, skipping instrumentation")
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Failed to instrument ElevenLabs", error=str(e))

    def uninstrument(self) -> None:
        """Remove ElevenLabs instrumentation."""
        self._instrumented = False

    def _wrap_generate(self, original_func: Callable) -> Callable:
        """Wrap generate()."""
        @functools.wraps(original_func)
        def wrapper(*args, **kwargs):
            return self._trace_generate(original_func, *args, **kwargs)
        return wrapper

    def _trace_generate(self, original_func: Callable, *args, **kwargs) -> Any:
        """Trace a generate call."""
        start_time = time.time()
        model = kwargs.get("voice") or kwargs.get("model", "eleven_multilingual_v2")

        with ensure_root_span("elevenlabs"):
            with tracer.start_as_current_span("api.generate") as span:
                span.set_attribute(API_PROVIDER, "elevenlabs")
                span.set_attribute(API_OPERATION, "generate")
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

                    # ElevenLabs pricing is per 1000 characters, default to 0 if failed
                    characters = 0
                    if not error_occurred:
                        try:
                            text = kwargs.get("text", "") or (args[0] if args else "")
                            characters = len(text) if text else 0
                        except Exception:
                            characters = 0
                    
                    cost = 0.0 if error_occurred else pricing_registry.cost_for_vector_db("elevenlabs", "generate", characters)
                    span.set_attribute(API_COST_USD, cost)

                    if self.span_enricher:
                        try:
                            self.span_enricher.enrich_api_span(span, "generate", latency_ms, 1, cost)
                        except Exception:
                            pass  # Don't fail if enrichment fails
