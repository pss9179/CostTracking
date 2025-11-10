"""Cohere auto-instrumentation for OpenTelemetry."""

import functools
import time
from typing import Any, Callable, Optional

from opentelemetry import trace

from llmobserve.semantics import LLM_MODEL, LLM_PROVIDER, LLM_REQUEST_MODEL, LLM_RESPONSE_MODEL, LLM_STATUS_CODE
from llmobserve.tracing.enrichers import SpanEnricher
from llmobserve.tracing.instrumentors.base import Instrumentor, ensure_root_span

tracer = trace.get_tracer(__name__)


class CohereInstrumentor(Instrumentor):
    """Auto-instrumentation for Cohere library."""

    def __init__(self, span_enricher: Optional[SpanEnricher] = None):
        """Initialize with optional span enricher."""
        self.span_enricher = span_enricher or SpanEnricher()
        self._instrumented = False

    def instrument(self) -> None:
        """Apply Cohere instrumentation."""
        if self._instrumented:
            return

        try:
            import cohere

            # Wrap Client.generate() and Client.embed()
            if hasattr(cohere, "Client"):
                original_init = cohere.Client.__init__

                def patched_init(cohere_self, *args, **kwargs):
                    original_init(cohere_self, *args, **kwargs)
                    if not hasattr(cohere_self, "_llmobserve_instrumented"):
                        # Wrap generate (chat completions)
                        if hasattr(cohere_self, "generate"):
                            # Prevents duplicate instrumentation during reloads or multiple setup calls
                            if not hasattr(cohere_self.generate, "_instrumented"):
                                original_generate = cohere_self.generate
                                wrapped = self._wrap_generate(original_generate)
                                wrapped._instrumented = True
                                cohere_self.generate = wrapped
                        # Wrap embed (embeddings)
                        if hasattr(cohere_self, "embed"):
                            # Prevents duplicate instrumentation during reloads or multiple setup calls
                            if not hasattr(cohere_self.embed, "_instrumented"):
                                original_embed = cohere_self.embed
                                wrapped = self._wrap_embed(original_embed)
                                wrapped._instrumented = True
                                cohere_self.embed = wrapped
                        cohere_self._llmobserve_instrumented = True

                cohere.Client.__init__ = patched_init

            # Wrap AsyncClient
            if hasattr(cohere, "AsyncClient"):
                original_async_init = cohere.AsyncClient.__init__

                def patched_async_init(async_cohere_self, *args, **kwargs):
                    original_async_init(async_cohere_self, *args, **kwargs)
                    if not hasattr(async_cohere_self, "_llmobserve_instrumented"):
                        if hasattr(async_cohere_self, "generate"):
                            # Prevents duplicate instrumentation during reloads or multiple setup calls
                            if not hasattr(async_cohere_self.generate, "_instrumented"):
                                original_generate = async_cohere_self.generate
                                wrapped = self._wrap_generate_async(original_generate)
                                wrapped._instrumented = True
                                async_cohere_self.generate = wrapped
                        if hasattr(async_cohere_self, "embed"):
                            # Prevents duplicate instrumentation during reloads or multiple setup calls
                            if not hasattr(async_cohere_self.embed, "_instrumented"):
                                original_embed = async_cohere_self.embed
                                wrapped = self._wrap_embed_async(original_embed)
                                wrapped._instrumented = True
                                async_cohere_self.embed = wrapped
                        async_cohere_self._llmobserve_instrumented = True

                cohere.AsyncClient.__init__ = patched_async_init

            self._instrumented = True
        except ImportError:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Cohere not installed, skipping instrumentation")
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Failed to instrument Cohere", error=str(e))

    def uninstrument(self) -> None:
        """Remove Cohere instrumentation."""
        self._instrumented = False

    def _wrap_generate(self, original_func: Callable) -> Callable:
        """Wrap generate() for Cohere (sync)."""
        @functools.wraps(original_func)
        def wrapper(*args, **kwargs):
            return self._trace_generate(original_func, *args, **kwargs)
        return wrapper

    def _wrap_generate_async(self, original_func: Callable) -> Callable:
        """Wrap generate() for Cohere (async)."""
        @functools.wraps(original_func)
        async def wrapper(*args, **kwargs):
            return await self._trace_generate_async(original_func, *args, **kwargs)
        return wrapper

    def _wrap_embed(self, original_func: Callable) -> Callable:
        """Wrap embed() for Cohere (sync)."""
        @functools.wraps(original_func)
        def wrapper(*args, **kwargs):
            return self._trace_embed(original_func, *args, **kwargs)
        return wrapper

    def _wrap_embed_async(self, original_func: Callable) -> Callable:
        """Wrap embed() for Cohere (async)."""
        @functools.wraps(original_func)
        async def wrapper(*args, **kwargs):
            return await self._trace_embed_async(original_func, *args, **kwargs)
        return wrapper

    def _trace_generate(self, original_func: Callable, *args, **kwargs) -> Any:
        """Trace a generate call (sync)."""
        start_time = time.time()
        model = kwargs.get("model", "command-r-plus")
        prompt = kwargs.get("prompt", "")

        with ensure_root_span("cohere"):
            with tracer.start_as_current_span("llm.request") as span:
                span.set_attribute(LLM_PROVIDER, "cohere")
                span.set_attribute(LLM_REQUEST_MODEL, model)
                span.set_attribute(LLM_MODEL, model)

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
                            self._process_generate_response(span, response, model, prompt, start_time)
                        else:
                            # Request failed before response - log with default cost
                            messages = [{"role": "user", "content": prompt}] if prompt else []
                            self.span_enricher.enrich_llm_span(
                                span=span,
                                model=model,
                                prompt_tokens=0,
                                completion_tokens=0,
                                prompt_messages=messages,
                                response_content=None,
                                start_time=start_time,
                            )
                    except Exception:
                        if error_occurred:
                            span.set_attribute(LLM_STATUS_CODE, "error")

    async def _trace_generate_async(self, original_func: Callable, *args, **kwargs) -> Any:
        """Trace a generate call (async)."""
        start_time = time.time()
        model = kwargs.get("model", "command-r-plus")
        prompt = kwargs.get("prompt", "")

        with ensure_root_span("cohere"):
            with tracer.start_as_current_span("llm.request") as span:
                span.set_attribute(LLM_PROVIDER, "cohere")
                span.set_attribute(LLM_REQUEST_MODEL, model)
                span.set_attribute(LLM_MODEL, model)

                response = None
                error_occurred = False
                try:
                    response = await original_func(*args, **kwargs)
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
                            self._process_generate_response(span, response, model, prompt, start_time)
                        else:
                            # Request failed before response - log with default cost
                            messages = [{"role": "user", "content": prompt}] if prompt else []
                            self.span_enricher.enrich_llm_span(
                                span=span,
                                model=model,
                                prompt_tokens=0,
                                completion_tokens=0,
                                prompt_messages=messages,
                                response_content=None,
                                start_time=start_time,
                            )
                    except Exception:
                        if error_occurred:
                            span.set_attribute(LLM_STATUS_CODE, "error")

    def _trace_embed(self, original_func: Callable, *args, **kwargs) -> Any:
        """Trace an embed call (sync) - treated as API call, not LLM."""
        start_time = time.time()
        model = kwargs.get("model", "embed-english-v3.0")

        with ensure_root_span("cohere"):
            with tracer.start_as_current_span("api.embed") as span:
                span.set_attribute("api.provider", "cohere")
                span.set_attribute("api.operation", "embed")
                span.set_attribute(LLM_MODEL, model)

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
                    
                    # Extract token counts if available, default to 0 if failed
                    prompt_tokens = 0
                    if response is not None:
                        try:
                            prompt_tokens = getattr(response, "meta", {}).get("billed_units", {}).get("input_tokens", 0) if hasattr(response, "meta") else 0
                        except Exception:
                            prompt_tokens = 0
                    
                    from llmobserve.pricing import pricing_registry
                    cost = pricing_registry.cost_for(model, prompt_tokens, 0) if not error_occurred else 0.0
                    span.set_attribute("api.cost_usd", cost)
                    
                    if self.span_enricher:
                        try:
                            self.span_enricher.enrich_api_span(span, "embed", latency_ms, 1, cost)
                        except Exception:
                            pass  # Don't fail if enrichment fails

    async def _trace_embed_async(self, original_func: Callable, *args, **kwargs) -> Any:
        """Trace an embed call (async) - treated as API call."""
        start_time = time.time()
        model = kwargs.get("model", "embed-english-v3.0")

        with ensure_root_span("cohere"):
            with tracer.start_as_current_span("api.embed") as span:
                span.set_attribute("api.provider", "cohere")
                span.set_attribute("api.operation", "embed")
                span.set_attribute(LLM_MODEL, model)

                response = None
                error_occurred = False
                try:
                    response = await original_func(*args, **kwargs)
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
                    
                    # Extract token counts if available, default to 0 if failed
                    prompt_tokens = 0
                    if response is not None:
                        try:
                            prompt_tokens = getattr(response, "meta", {}).get("billed_units", {}).get("input_tokens", 0) if hasattr(response, "meta") else 0
                        except Exception:
                            prompt_tokens = 0
                    
                    from llmobserve.pricing import pricing_registry
                    cost = pricing_registry.cost_for(model, prompt_tokens, 0) if not error_occurred else 0.0
                    span.set_attribute("api.cost_usd", cost)
                    
                    if self.span_enricher:
                        try:
                            self.span_enricher.enrich_api_span(span, "embed", latency_ms, 1, cost)
                        except Exception:
                            pass  # Don't fail if enrichment fails

    def _process_generate_response(self, span: trace.Span, response: Any, model: str, prompt: str, start_time: float) -> None:
        """Process generate response and enrich span."""
        prompt_tokens = 0
        completion_tokens = 0
        response_content = None

        if hasattr(response, "generations") and response.generations:
            response_content = response.generations[0].text if hasattr(response.generations[0], "text") else str(response.generations[0])

        if hasattr(response, "meta") and hasattr(response.meta, "billed_units"):
            billed = response.meta.billed_units
            prompt_tokens = getattr(billed, "input_tokens", 0)
            completion_tokens = getattr(billed, "output_tokens", 0)

        span.set_attribute(LLM_RESPONSE_MODEL, model)
        span.set_attribute(LLM_STATUS_CODE, "success")

        messages = [{"role": "user", "content": prompt}] if prompt else []
        self.span_enricher.enrich_llm_span(
            span=span,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            prompt_messages=messages,
            response_content=response_content,
            start_time=start_time,
        )

