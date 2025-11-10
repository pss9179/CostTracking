"""AWS Bedrock auto-instrumentation for OpenTelemetry."""

import functools
import json
import time
from typing import Any, Callable, Optional

from opentelemetry import trace

from llmobserve.semantics import LLM_MODEL, LLM_PROVIDER, LLM_REQUEST_MODEL, LLM_RESPONSE_MODEL, LLM_STATUS_CODE
from llmobserve.tracing.enrichers import SpanEnricher
from llmobserve.tracing.instrumentors.base import Instrumentor, ensure_root_span

tracer = trace.get_tracer(__name__)


class BedrockInstrumentor(Instrumentor):
    """Auto-instrumentation for AWS Bedrock (via boto3)."""

    def __init__(self, span_enricher: Optional[SpanEnricher] = None):
        """Initialize with optional span enricher."""
        self.span_enricher = span_enricher or SpanEnricher()
        self._instrumented = False

    def instrument(self) -> None:
        """Apply Bedrock instrumentation."""
        if self._instrumented:
            return

        try:
            import boto3

            # Wrap bedrock-runtime client invoke_model
            original_client = boto3.client

            def patched_client(*args, **kwargs):
                client = original_client(*args, **kwargs)
                if args and args[0] == "bedrock-runtime":
                    if not hasattr(client, "_llmobserve_instrumented"):
                        # Prevents duplicate instrumentation during reloads or multiple setup calls
                        if hasattr(client.invoke_model, "_instrumented"):
                            client._llmobserve_instrumented = True
                            return client
                        original_invoke = client.invoke_model
                        wrapped = self._wrap_invoke_model(original_invoke)
                        wrapped._instrumented = True
                        client.invoke_model = wrapped
                        client._llmobserve_instrumented = True
                return client

            boto3.client = patched_client

            self._instrumented = True
        except ImportError:
            import structlog
            logger = structlog.get_logger()
            logger.warning("boto3 not installed, skipping Bedrock instrumentation")
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Failed to instrument Bedrock", error=str(e))

    def uninstrument(self) -> None:
        """Remove Bedrock instrumentation."""
        self._instrumented = False

    def _wrap_invoke_model(self, original_func: Callable) -> Callable:
        """Wrap invoke_model()."""
        @functools.wraps(original_func)
        def wrapper(*args, **kwargs):
            return self._trace_invoke(original_func, *args, **kwargs)
        return wrapper

    def _trace_invoke(self, original_func: Callable, *args, **kwargs) -> Any:
        """Trace invoke_model call."""
        start_time = time.time()
        
        # Extract model from request body
        model = "unknown"
        if "body" in kwargs:
            try:
                body_str = kwargs["body"]
                if isinstance(body_str, (str, bytes)):
                    body = json.loads(body_str if isinstance(body_str, str) else body_str.decode())
                    model = body.get("modelId", kwargs.get("modelId", "unknown"))
            except Exception:
                model = kwargs.get("modelId", "unknown")
        else:
            model = kwargs.get("modelId", "unknown")

        with ensure_root_span("bedrock"):
            with tracer.start_as_current_span("llm.request") as span:
                span.set_attribute(LLM_PROVIDER, "bedrock")
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
                            self._process_response(span, response, model, start_time)
                        else:
                            # Request failed before response - log with default cost
                            self.span_enricher.enrich_llm_span(
                                span=span,
                                model=model,
                                prompt_tokens=0,
                                completion_tokens=0,
                                prompt_messages=[],
                                response_content=None,
                                start_time=start_time,
                            )
                    except Exception:
                        if error_occurred:
                            span.set_attribute(LLM_STATUS_CODE, "error")

    def _process_response(self, span: trace.Span, response: Any, model: str, start_time: float) -> None:
        """Process Bedrock response."""
        prompt_tokens = 0
        completion_tokens = 0

        # Parse response body
        if hasattr(response, "body"):
            try:
                body = json.loads(response["body"].read())
                if "usage" in body:
                    usage = body["usage"]
                    prompt_tokens = usage.get("input_tokens", 0)
                    completion_tokens = usage.get("output_tokens", 0)
            except Exception:
                pass

        span.set_attribute(LLM_RESPONSE_MODEL, model)
        span.set_attribute(LLM_STATUS_CODE, "success")

        self.span_enricher.enrich_llm_span(
            span=span,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            prompt_messages=[],
            response_content=None,
            start_time=start_time,
        )

