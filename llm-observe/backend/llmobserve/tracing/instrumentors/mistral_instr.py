"""Mistral auto-instrumentation for OpenTelemetry."""

import functools
import time
from typing import Any, Callable, Optional

from opentelemetry import trace

from llmobserve.semantics import LLM_MODEL, LLM_PROVIDER, LLM_REQUEST_MODEL, LLM_RESPONSE_MODEL, LLM_STATUS_CODE
from llmobserve.tracing.enrichers import SpanEnricher
from llmobserve.tracing.instrumentors.base import Instrumentor, ensure_root_span

tracer = trace.get_tracer(__name__)


class MistralInstrumentor(Instrumentor):
    """Auto-instrumentation for Mistral library."""

    def __init__(self, span_enricher: Optional[SpanEnricher] = None):
        """Initialize with optional span enricher."""
        self.span_enricher = span_enricher or SpanEnricher()
        self._instrumented = False

    def instrument(self) -> None:
        """Apply Mistral instrumentation."""
        if self._instrumented:
            return

        try:
            import mistralai

            # Wrap Mistral client (follows OpenAI-style API)
            if hasattr(mistralai, "Mistral"):
                original_init = mistralai.Mistral.__init__

                def patched_init(mistral_self, *args, **kwargs):
                    original_init(mistral_self, *args, **kwargs)
                    # Prevents duplicate instrumentation during reloads or multiple setup calls
                    if hasattr(mistral_self.chat.completions.create, "_instrumented"):
                        return
                    if not hasattr(mistral_self.chat.completions, "_original_create"):
                        original_create = mistral_self.chat.completions.create
                        mistral_self.chat.completions._original_create = original_create
                        wrapped = self._wrap_chat_create(original_create)
                        wrapped._instrumented = True
                        mistral_self.chat.completions.create = wrapped

                mistralai.Mistral.__init__ = patched_init

            # Wrap AsyncMistral
            if hasattr(mistralai, "AsyncMistral"):
                original_async_init = mistralai.AsyncMistral.__init__

                def patched_async_init(async_mistral_self, *args, **kwargs):
                    original_async_init(async_mistral_self, *args, **kwargs)
                    # Prevents duplicate instrumentation during reloads or multiple setup calls
                    if hasattr(async_mistral_self.chat.completions.create, "_instrumented"):
                        return
                    if not hasattr(async_mistral_self.chat.completions, "_original_create"):
                        original_create = async_mistral_self.chat.completions.create
                        async_mistral_self.chat.completions._original_create = original_create
                        wrapped = self._wrap_chat_create_async(original_create)
                        wrapped._instrumented = True
                        async_mistral_self.chat.completions.create = wrapped

                mistralai.AsyncMistral.__init__ = patched_async_init

            self._instrumented = True
        except ImportError:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Mistral not installed, skipping instrumentation")
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Failed to instrument Mistral", error=str(e))

    def uninstrument(self) -> None:
        """Remove Mistral instrumentation."""
        self._instrumented = False

    def _wrap_chat_create(self, original_create: Callable) -> Callable:
        """Wrap chat.completions.create (sync)."""
        @functools.wraps(original_create)
        def sync_wrapper(*args, **kwargs):
            return self._trace_chat_call(original_create, *args, **kwargs)
        import inspect
        return sync_wrapper if not inspect.iscoroutinefunction(original_create) else self._wrap_chat_create_async(original_create)

    def _wrap_chat_create_async(self, original_create: Callable) -> Callable:
        """Wrap chat.completions.create (async)."""
        @functools.wraps(original_create)
        async def async_wrapper(*args, **kwargs):
            return await self._trace_chat_call_async(original_create, *args, **kwargs)
        return async_wrapper

    def _trace_chat_call(self, original_func: Callable, *args, **kwargs) -> Any:
        """Trace a chat completion call (sync)."""
        start_time = time.time()
        model = kwargs.get("model", "mistral-large")
        messages = kwargs.get("messages", [])

        with ensure_root_span("mistral"):
            with tracer.start_as_current_span("llm.request") as span:
                span.set_attribute(LLM_PROVIDER, "mistral")
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
                            self._process_response(span, response, model, messages, start_time)
                        else:
                            # Request failed before response - log with default cost
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

    async def _trace_chat_call_async(self, original_func: Callable, *args, **kwargs) -> Any:
        """Trace a chat completion call (async)."""
        start_time = time.time()
        model = kwargs.get("model", "mistral-large")
        messages = kwargs.get("messages", [])

        with ensure_root_span("mistral"):
            with tracer.start_as_current_span("llm.request") as span:
                span.set_attribute(LLM_PROVIDER, "mistral")
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
                            self._process_response(span, response, model, messages, start_time)
                        else:
                            # Request failed before response - log with default cost
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

    def _process_response(self, span: trace.Span, response: Any, model: str, messages: list, start_time: float) -> None:
        """Process response and enrich span."""
        prompt_tokens = 0
        completion_tokens = 0
        response_content = None
        response_model = model

        if hasattr(response, "usage"):
            usage = response.usage
            prompt_tokens = getattr(usage, "prompt_tokens", 0)
            completion_tokens = getattr(usage, "completion_tokens", 0)
            response_model = getattr(response, "model", model)

            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    response_content = choice.message.content

        span.set_attribute(LLM_RESPONSE_MODEL, response_model)
        span.set_attribute(LLM_STATUS_CODE, "success")

        self.span_enricher.enrich_llm_span(
            span=span,
            model=response_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            prompt_messages=messages,
            response_content=response_content,
            start_time=start_time,
        )

