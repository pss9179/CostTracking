"""OpenAI auto-instrumentation for OpenTelemetry."""

import functools
import time
from typing import Any, Callable, Optional

from opentelemetry import trace

from llmobserve.semantics import LLM_MODEL, LLM_PROVIDER, LLM_REQUEST_MODEL, LLM_RESPONSE_MODEL, LLM_STATUS_CODE
from llmobserve.tracing.enrichers import SpanEnricher
from llmobserve.tracing.instrumentors.base import Instrumentor, ensure_root_span
from llmobserve.tracing.tracer import get_wrapped_tracer

# TODO: Production hardening
# 1. Implement tail-based sampling for high-volume traces
# 2. Add rate limiting for instrumentor calls
# 3. Support async/await patterns more robustly
# 4. Add retry logic for failed span exports
# 5. Implement span batching for better throughput

# Use wrapped tracer instead of raw OpenTelemetry tracer
tracer = get_wrapped_tracer(__name__)


class OpenAIInstrumentor(Instrumentor):
    """Auto-instrumentation for OpenAI library."""

    def __init__(self, span_enricher: Optional[SpanEnricher] = None):
        """Initialize with optional span enricher."""
        self.span_enricher = span_enricher or SpanEnricher()
        self._original_chat_create = None
        self._original_responses_create = None
        self._instrumented = False

    def instrument(self) -> None:
        """Apply OpenAI instrumentation."""
        if self._instrumented:
            return

        try:
            import openai

            # Wrap for OpenAI v1+ (client.chat.completions.create) - most common
            if hasattr(openai, "OpenAI"):
                # Patch the class __init__ to wrap create method on instance creation
                original_init = openai.OpenAI.__init__

                def patched_init(openai_self, *args, **kwargs):
                    original_init(openai_self, *args, **kwargs)
                    # Prevents duplicate instrumentation during reloads or multiple setup calls
                    if hasattr(openai_self.chat.completions.create, "_instrumented"):
                        return
                    if not hasattr(openai_self.chat.completions, "_original_create"):
                        original_create = openai_self.chat.completions.create
                        openai_self.chat.completions._original_create = original_create
                        wrapped = self._wrap_chat_create_v1(original_create)
                        wrapped._instrumented = True
                        openai_self.chat.completions.create = wrapped

                openai.OpenAI.__init__ = patched_init

            # Wrap chat.completions.create for OpenAI v0.x (legacy)
            if hasattr(openai, "ChatCompletion") and hasattr(openai.ChatCompletion, "create"):
                try:
                    # Prevents duplicate instrumentation during reloads or multiple setup calls
                    if hasattr(openai.ChatCompletion.create, "_instrumented"):
                        pass
                    else:
                        self._original_chat_create = openai.ChatCompletion.create
                        if callable(self._original_chat_create):
                            wrapped = self._wrap_chat_create(self._original_chat_create)
                            wrapped._instrumented = True
                            openai.ChatCompletion.create = wrapped
                except Exception:
                    pass  # Skip if can't wrap

            self._instrumented = True
        except ImportError:
            import structlog
            logger = structlog.get_logger()
            logger.warning("OpenAI not installed, skipping instrumentation")
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Failed to instrument OpenAI", error=str(e))

    def uninstrument(self) -> None:
        """Remove OpenAI instrumentation."""
        if not self._instrumented:
            return

        try:
            import openai

            if self._original_chat_create:
                openai.ChatCompletion.create = self._original_chat_create

            # Restore v1+ client (would need to track instances for full restoration)
            # For demo purposes, just mark as uninstrumented
            self._instrumented = False
        except ImportError:
            pass

    def _wrap_chat_create(self, original_create: Callable) -> Callable:
        """Wrap chat.completions.create for OpenAI v0.x."""
        if not callable(original_create):
            return original_create

        def wrapper(*args, **kwargs):
            return self._trace_chat_call(original_create, *args, **kwargs)
        
        # Copy attributes if possible
        try:
            wrapper.__name__ = getattr(original_create, "__name__", "wrapped_create")
            wrapper.__doc__ = getattr(original_create, "__doc__", None)
        except Exception:
            pass

        return wrapper

    def _wrap_chat_create_v1(self, original_create: Callable) -> Callable:
        """Wrap chat.completions.create for OpenAI v1+."""

        @functools.wraps(original_create)
        async def async_wrapper(*args, **kwargs):
            return await self._trace_chat_call_async(original_create, *args, **kwargs)

        @functools.wraps(original_create)
        def sync_wrapper(*args, **kwargs):
            return self._trace_chat_call(original_create, *args, **kwargs)

        # Return appropriate wrapper based on if original is async
        import inspect
        if inspect.iscoroutinefunction(original_create):
            return async_wrapper
        return sync_wrapper

    def _trace_chat_call(self, original_func: Callable, *args, **kwargs) -> Any:
        """Trace a chat completion call (sync)."""
        start_time = time.time()
        model = kwargs.get("model", "gpt-3.5-turbo")
        messages = kwargs.get("messages", [])

        # Auto-create root span if no active span exists (plug-and-play behavior)
        # This ensures every API call gets a trace, even without manual setup
        with ensure_root_span("openai"):
            # Create child span for the actual LLM request
            # If ensure_root_span created a parent, this will link to it
            # If a parent already existed, this will link to that parent
            with tracer.start_span("llm.request") as span:
                span.set_attribute(LLM_PROVIDER, "openai")
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
                        # If enrichment fails, at least ensure span is marked as error
                        if error_occurred:
                            span.set_attribute(LLM_STATUS_CODE, "error")

    async def _trace_chat_call_async(self, original_func: Callable, *args, **kwargs) -> Any:
        """Trace a chat completion call (async)."""
        start_time = time.time()
        model = kwargs.get("model", "gpt-3.5-turbo")
        messages = kwargs.get("messages", [])

        # Auto-create root span if no active span exists (plug-and-play behavior)
        # This ensures every API call gets a trace, even without manual setup
        with ensure_root_span("openai"):
            # Create child span for the actual LLM request
            # If ensure_root_span created a parent, this will link to it
            # If a parent already existed, this will link to that parent
            with tracer.start_span("llm.request") as span:
                span.set_attribute(LLM_PROVIDER, "openai")
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
                        # If enrichment fails, at least ensure span is marked as error
                        if error_occurred:
                            span.set_attribute(LLM_STATUS_CODE, "error")

    def _process_response(
        self,
        span: trace.Span,
        response: Any,
        model: str,
        messages: list,
        start_time: float,
    ) -> None:
        """Process response and enrich span."""
        # Extract usage and content from response
        prompt_tokens = 0
        completion_tokens = 0
        response_content = None
        response_model = model

        # Handle OpenAI v0.x response format
        if hasattr(response, "usage"):
            usage = response.usage
            prompt_tokens = getattr(usage, "prompt_tokens", 0)
            completion_tokens = getattr(usage, "completion_tokens", 0)
            response_model = getattr(response, "model", model)

            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    response_content = choice.message.content

        # Handle OpenAI v1+ response format
        elif hasattr(response, "model"):
            response_model = response.model
            if hasattr(response, "usage"):
                prompt_tokens = response.usage.prompt_tokens or 0
                completion_tokens = response.usage.completion_tokens or 0
            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    response_content = choice.message.content

        span.set_attribute(LLM_RESPONSE_MODEL, response_model)
        span.set_attribute(LLM_STATUS_CODE, "success")

        # Enrich span with usage, cost, and content/hashes
        self.span_enricher.enrich_llm_span(
            span=span,
            model=response_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            prompt_messages=messages,
            response_content=response_content,
            start_time=start_time,
        )
