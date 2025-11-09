"""Google Gemini auto-instrumentation for OpenTelemetry."""

import functools
import time
from typing import Any, Callable, Optional

from opentelemetry import trace

from llmobserve.semantics import LLM_MODEL, LLM_PROVIDER, LLM_REQUEST_MODEL, LLM_RESPONSE_MODEL, LLM_STATUS_CODE
from llmobserve.tracing.enrichers import SpanEnricher
from llmobserve.tracing.instrumentors.base import Instrumentor, ensure_root_span

tracer = trace.get_tracer(__name__)


class GeminiInstrumentor(Instrumentor):
    """Auto-instrumentation for Google Gemini library."""

    def __init__(self, span_enricher: Optional[SpanEnricher] = None):
        """Initialize with optional span enricher."""
        self.span_enricher = span_enricher or SpanEnricher()
        self._instrumented = False

    def instrument(self) -> None:
        """Apply Gemini instrumentation."""
        if self._instrumented:
            return

        try:
            import google.generativeai as genai

            # Wrap GenerativeModel.generate_content()
            if hasattr(genai, "GenerativeModel"):
                original_init = genai.GenerativeModel.__init__

                def patched_init(model_self, *args, **kwargs):
                    original_init(model_self, *args, **kwargs)
                    if not hasattr(model_self, "_llmobserve_instrumented"):
                        if hasattr(model_self, "generate_content"):
                            # Prevents duplicate instrumentation during reloads or multiple setup calls
                            if not hasattr(model_self.generate_content, "_instrumented"):
                                original_generate = model_self.generate_content
                                wrapped = self._wrap_generate_content(original_generate)
                                wrapped._instrumented = True
                                model_self.generate_content = wrapped
                        if hasattr(model_self, "embed_content"):
                            # Prevents duplicate instrumentation during reloads or multiple setup calls
                            if not hasattr(model_self.embed_content, "_instrumented"):
                                original_embed = model_self.embed_content
                                wrapped = self._wrap_embed_content(original_embed)
                                wrapped._instrumented = True
                                model_self.embed_content = wrapped
                        model_self._llmobserve_instrumented = True

                genai.GenerativeModel.__init__ = patched_init

            self._instrumented = True
        except ImportError:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Google Gemini not installed, skipping instrumentation")
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Failed to instrument Gemini", error=str(e))

    def uninstrument(self) -> None:
        """Remove Gemini instrumentation."""
        self._instrumented = False

    def _wrap_generate_content(self, original_func: Callable) -> Callable:
        """Wrap generate_content()."""
        @functools.wraps(original_func)
        def wrapper(*args, **kwargs):
            return self._trace_generate(original_func, *args, **kwargs)
        return wrapper

    def _wrap_embed_content(self, original_func: Callable) -> Callable:
        """Wrap embed_content()."""
        @functools.wraps(original_func)
        def wrapper(*args, **kwargs):
            return self._trace_embed(original_func, *args, **kwargs)
        return wrapper

    def _trace_generate(self, original_func: Callable, *args, **kwargs) -> Any:
        """Trace generate_content call."""
        start_time = time.time()
        model_name = getattr(args[0] if args else None, "model_name", "gemini-1.5-pro") if args else "gemini-1.5-pro"

        with ensure_root_span("gemini"):
            with tracer.start_as_current_span("llm.request") as span:
                span.set_attribute(LLM_PROVIDER, "gemini")
                span.set_attribute(LLM_REQUEST_MODEL, model_name)
                span.set_attribute(LLM_MODEL, model_name)

                response = None
                error_occurred = False
                try:
                    response = original_func(*args, **kwargs)
                    return response
                except Exception as e:
                    error_occurred = True
                    span.set_attribute(LLM_STATUS_CODE, "error")
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
                finally:
                    # Ensures cost is logged even if the API call raises an exception
                    try:
                        if response is not None:
                            self._process_generate_response(span, response, model_name, start_time)
                        else:
                            # Request failed before response - log with default cost
                            self.span_enricher.enrich_llm_span(
                                span=span,
                                model=model_name,
                                prompt_tokens=0,
                                completion_tokens=0,
                                prompt_messages=[],
                                response_content=None,
                                start_time=start_time,
                            )
                    except Exception:
                        if error_occurred:
                            span.set_attribute(LLM_STATUS_CODE, "error")

    def _trace_embed(self, original_func: Callable, *args, **kwargs) -> Any:
        """Trace embed_content call."""
        start_time = time.time()
        model_name = getattr(args[0] if args else None, "model_name", "embedding-001") if args else "embedding-001"

        with ensure_root_span("gemini"):
            with tracer.start_as_current_span("api.embed") as span:
                span.set_attribute("api.provider", "gemini")
                span.set_attribute("api.operation", "embed")
                span.set_attribute(LLM_MODEL, model_name)

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
                    span.set_attribute("api.latency_ms", latency_ms)
                    
                    # Estimate tokens for embeddings (rough approximation), default to 0 if failed
                    prompt_tokens = 0
                    if not error_occurred and "content" in kwargs:
                        try:
                            prompt_tokens = int(kwargs.get("content", "").count(" ") * 1.3)
                        except Exception:
                            prompt_tokens = 0
                    
                    from llmobserve.pricing import pricing_registry
                    cost = pricing_registry.cost_for(model_name, prompt_tokens, 0) if not error_occurred else 0.0
                    span.set_attribute("api.cost_usd", cost)
                    
                    if self.span_enricher:
                        try:
                            self.span_enricher.enrich_api_span(span, "embed", latency_ms, 1, cost)
                        except Exception:
                            pass  # Don't fail if enrichment fails

    def _process_generate_response(self, span: trace.Span, response: Any, model: str, start_time: float) -> None:
        """Process generate response."""
        prompt_tokens = 0
        completion_tokens = 0
        response_content = None

        if hasattr(response, "usage_metadata"):
            usage = response.usage_metadata
            prompt_tokens = getattr(usage, "prompt_token_count", 0)
            completion_tokens = getattr(usage, "candidates_token_count", 0)

        if hasattr(response, "text"):
            response_content = response.text
        elif hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                response_content = candidate.content.parts[0].text if candidate.content.parts else None

        span.set_attribute(LLM_RESPONSE_MODEL, model)
        span.set_attribute(LLM_STATUS_CODE, "success")

        self.span_enricher.enrich_llm_span(
            span=span,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            prompt_messages=[],
            response_content=response_content,
            start_time=start_time,
        )

