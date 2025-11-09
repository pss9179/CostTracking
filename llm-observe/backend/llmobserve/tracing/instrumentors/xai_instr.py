"""xAI auto-instrumentation for OpenTelemetry."""

import functools
import time
from typing import Any, Callable, Optional

from opentelemetry import trace

from llmobserve.semantics import LLM_MODEL, LLM_PROVIDER, LLM_REQUEST_MODEL, LLM_RESPONSE_MODEL, LLM_STATUS_CODE
from llmobserve.tracing.enrichers import SpanEnricher
from llmobserve.tracing.instrumentors.base import Instrumentor, ensure_root_span

tracer = trace.get_tracer(__name__)


class XAIInstrumentor(Instrumentor):
    """Auto-instrumentation for xAI library (follows OpenAI-style API)."""

    def __init__(self, span_enricher: Optional[SpanEnricher] = None):
        """Initialize with optional span enricher."""
        self.span_enricher = span_enricher or SpanEnricher()
        self._instrumented = False

    def instrument(self) -> None:
        """Apply xAI instrumentation."""
        if self._instrumented:
            return

        try:
            import xai

            # Wrap Client (OpenAI-style API)
            if hasattr(xai, "Client"):
                original_init = xai.Client.__init__

                def patched_init(client_self, *args, **kwargs):
                    original_init(client_self, *args, **kwargs)
                    # Prevents duplicate instrumentation during reloads or multiple setup calls
                    if hasattr(client_self.chat.completions.create, "_instrumented"):
                        return
                    if not hasattr(client_self.chat.completions, "_original_create"):
                        original_create = client_self.chat.completions.create
                        client_self.chat.completions._original_create = original_create
                        wrapped = self._wrap_chat_create(original_create)
                        wrapped._instrumented = True
                        client_self.chat.completions.create = wrapped

                xai.Client.__init__ = patched_init

            self._instrumented = True
        except ImportError:
            import structlog
            logger = structlog.get_logger()
            logger.warning("xAI not installed, skipping instrumentation")
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Failed to instrument xAI", error=str(e))

    def uninstrument(self) -> None:
        """Remove xAI instrumentation."""
        self._instrumented = False

    def _wrap_chat_create(self, original_create: Callable) -> Callable:
        """Wrap chat.completions.create."""
        @functools.wraps(original_create)
        async def async_wrapper(*args, **kwargs):
            return await self._trace_chat_call_async(original_create, *args, **kwargs)

        @functools.wraps(original_create)
        def sync_wrapper(*args, **kwargs):
            return self._trace_chat_call(original_create, *args, **kwargs)

        import inspect
        return async_wrapper if inspect.iscoroutinefunction(original_create) else sync_wrapper

    def _trace_chat_call(self, original_func: Callable, *args, **kwargs) -> Any:
        """Trace chat completion (sync)."""
        start_time = time.time()
        model = kwargs.get("model", "grok-beta")
        messages = kwargs.get("messages", [])

        with ensure_root_span("xai"):
            with tracer.start_as_current_span("llm.request") as span:
                span.set_attribute(LLM_PROVIDER, "xai")
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
        """Trace chat completion (async)."""
        start_time = time.time()
        model = kwargs.get("model", "grok-beta")
        messages = kwargs.get("messages", [])

        with ensure_root_span("xai"):
            with tracer.start_as_current_span("llm.request") as span:
                span.set_attribute(LLM_PROVIDER, "xai")
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
        """Process response (OpenAI-style)."""
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

