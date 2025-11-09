"""Anthropic auto-instrumentation for OpenTelemetry."""

import functools
import time
from typing import Any, Callable, Optional

from opentelemetry import trace

from llmobserve.semantics import LLM_MODEL, LLM_PROVIDER, LLM_REQUEST_MODEL, LLM_RESPONSE_MODEL, LLM_STATUS_CODE
from llmobserve.tracing.enrichers import SpanEnricher
from llmobserve.tracing.instrumentors.base import Instrumentor, ensure_root_span

tracer = trace.get_tracer(__name__)


class AnthropicInstrumentor(Instrumentor):
    """Auto-instrumentation for Anthropic library."""

    def __init__(self, span_enricher: Optional[SpanEnricher] = None):
        """Initialize with optional span enricher."""
        self.span_enricher = span_enricher or SpanEnricher()
        self._original_messages_create = None
        self._original_completions_create = None
        self._instrumented = False

    def instrument(self) -> None:
        """Apply Anthropic instrumentation."""
        if self._instrumented:
            return

        try:
            import anthropic

            # Wrap Anthropic v1+ (client.messages.create) - most common
            if hasattr(anthropic, "Anthropic"):
                original_init = anthropic.Anthropic.__init__

                def patched_init(anthropic_self, *args, **kwargs):
                    original_init(anthropic_self, *args, **kwargs)
                    # Prevents duplicate instrumentation during reloads or multiple setup calls
                    if hasattr(anthropic_self.messages.create, "_instrumented"):
                        return
                    if not hasattr(anthropic_self.messages, "_original_create"):
                        original_create = anthropic_self.messages.create
                        anthropic_self.messages._original_create = original_create
                        wrapped = self._wrap_messages_create(original_create)
                        wrapped._instrumented = True
                        anthropic_self.messages.create = wrapped

                anthropic.Anthropic.__init__ = patched_init

            # Wrap AsyncAnthropic
            if hasattr(anthropic, "AsyncAnthropic"):
                original_async_init = anthropic.AsyncAnthropic.__init__

                def patched_async_init(async_anthropic_self, *args, **kwargs):
                    original_async_init(async_anthropic_self, *args, **kwargs)
                    # Prevents duplicate instrumentation during reloads or multiple setup calls
                    if hasattr(async_anthropic_self.messages.create, "_instrumented"):
                        return
                    if not hasattr(async_anthropic_self.messages, "_original_create"):
                        original_create = async_anthropic_self.messages.create
                        async_anthropic_self.messages._original_create = original_create
                        wrapped = self._wrap_messages_create_async(original_create)
                        wrapped._instrumented = True
                        async_anthropic_self.messages.create = wrapped

                anthropic.AsyncAnthropic.__init__ = patched_async_init

            # Wrap legacy completions.create (if exists)
            if hasattr(anthropic, "Anthropic") and hasattr(anthropic.Anthropic, "completions"):
                try:
                    original_completions_init = anthropic.Anthropic.__init__
                    # Note: completions API is deprecated, but we'll wrap it if it exists
                except Exception:
                    pass

            self._instrumented = True
        except ImportError:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Anthropic not installed, skipping instrumentation")
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Failed to instrument Anthropic", error=str(e))

    def uninstrument(self) -> None:
        """Remove Anthropic instrumentation."""
        if not self._instrumented:
            return

        try:
            import anthropic

            # Restore would require tracking instances - for demo, just mark as uninstrumented
            self._instrumented = False
        except ImportError:
            pass

    def _wrap_messages_create(self, original_create: Callable) -> Callable:
        """Wrap messages.create for Anthropic (sync)."""

        @functools.wraps(original_create)
        def sync_wrapper(*args, **kwargs):
            return self._trace_messages_call(original_create, *args, **kwargs)

        return sync_wrapper

    def _wrap_messages_create_async(self, original_create: Callable) -> Callable:
        """Wrap messages.create for Anthropic (async)."""

        @functools.wraps(original_create)
        async def async_wrapper(*args, **kwargs):
            return await self._trace_messages_call_async(original_create, *args, **kwargs)

        return async_wrapper

    def _trace_messages_call(self, original_func: Callable, *args, **kwargs) -> Any:
        """Trace a messages.create call (sync)."""
        start_time = time.time()
        model = kwargs.get("model", "claude-3-5-sonnet")
        messages = kwargs.get("messages", [])

        # Auto-create root span if no active span exists (plug-and-play behavior)
        with ensure_root_span("anthropic"):
            # Create child span for the actual LLM request
            with tracer.start_as_current_span("llm.request") as span:
                span.set_attribute(LLM_PROVIDER, "anthropic")
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

    async def _trace_messages_call_async(self, original_func: Callable, *args, **kwargs) -> Any:
        """Trace a messages.create call (async)."""
        start_time = time.time()
        model = kwargs.get("model", "claude-3-5-sonnet")
        messages = kwargs.get("messages", [])

        # Auto-create root span if no active span exists (plug-and-play behavior)
        with ensure_root_span("anthropic"):
            # Create child span for the actual LLM request
            with tracer.start_as_current_span("llm.request") as span:
                span.set_attribute(LLM_PROVIDER, "anthropic")
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
        # Extract usage and content from Anthropic response
        prompt_tokens = 0
        completion_tokens = 0
        response_content = None
        response_model = model

        # Handle Anthropic response format
        if hasattr(response, "usage"):
            usage = response.usage
            prompt_tokens = getattr(usage, "input_tokens", 0)
            completion_tokens = getattr(usage, "output_tokens", 0)
            response_model = getattr(response, "model", model)

            # Extract content from first text block
            if hasattr(response, "content") and response.content:
                for block in response.content:
                    if hasattr(block, "text"):
                        response_content = block.text
                        break

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

