"""Official OpenTelemetry GenAI instrumentation wrapper.

This module provides integration with the official opentelemetry-instrumentation-openai
package, which follows GenAI semantic conventions and automatically captures:
- Token usage (prompt, completion, total)
- Model name
- Temperature, top_p, and other parameters
- Latency
- Request/response metadata

We add an additional wrapper layer to extract token usage from the response object
and ensure it's written to our database via the span processor.
"""

import functools
from typing import Optional, Any, Callable

from opentelemetry import trace

from llmobserve.tracing.enrichers import SpanEnricher
from llmobserve.tracing.instrumentors.base import Instrumentor, ensure_root_span


class GenAIInstrumentor(Instrumentor):
    """Wrapper for official OpenTelemetry GenAI instrumentation."""

    def __init__(self, span_enricher: Optional[SpanEnricher] = None):
        """Initialize GenAI instrumentor.
        
        Args:
            span_enricher: Optional span enricher for custom enrichment.
                          Note: The official instrumentor handles most enrichment automatically.
        """
        self.span_enricher = span_enricher
        self._instrumentor = None
        self._instrumented = False

    def instrument(self) -> None:
        """Apply official OpenTelemetry GenAI instrumentation."""
        if self._instrumented:
            return

        try:
            from opentelemetry.instrumentation.openai import OpenAIInstrumentor as OfficialOpenAIInstrumentor
            
            # Initialize the official instrumentor
            self._instrumentor = OfficialOpenAIInstrumentor()
            
            # Instrument OpenAI - this automatically captures:
            # - Token usage (gen_ai.token.count)
            # - Model name (gen_ai.model.name)
            # - Temperature, top_p, etc. (gen_ai.request.parameters.*)
            # - Latency (automatically calculated)
            # - Request/response content (if enabled)
            self._instrumentor.instrument()
            
            # Now wrap OpenAI client to extract tokens from response and set on span
            self._wrap_openai_client()
            
            self._instrumented = True
            
            import structlog
            logger = structlog.get_logger()
            logger.info("Official OpenTelemetry GenAI instrumentation enabled")
            
        except ImportError:
            import structlog
            logger = structlog.get_logger()
            logger.warning(
                "opentelemetry-instrumentation-openai not installed. "
                "Install with: pip install opentelemetry-instrumentation-openai"
            )
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.error("Failed to enable GenAI instrumentation", error=str(e))

    def _wrap_openai_client(self) -> None:
        """Wrap OpenAI client to extract token usage from response and set on span."""
        try:
            import openai
            from opentelemetry.trace import get_current_span
            
            # Wrap chat.completions.create to extract tokens
            if hasattr(openai, "OpenAI"):
                original_init = openai.OpenAI.__init__
                
                def patched_init(openai_self, *args, **kwargs):
                    original_init(openai_self, *args, **kwargs)
                    
                    # Wrap the create method
                    if hasattr(openai_self.chat.completions, "create"):
                        # Prevents duplicate instrumentation during reloads or multiple setup calls
                        if hasattr(openai_self.chat.completions.create, "_instrumented"):
                            return
                        original_create = openai_self.chat.completions.create
                        
                        @functools.wraps(original_create)
                        async def async_wrapper(*args, **kwargs):
                            # Auto-create root span if no active span exists (plug-and-play behavior)
                            # The official instrumentor will create "llm.request" spans, but we need
                            # to ensure there's a root trace if none exists
                            with ensure_root_span("openai"):
                                # Official instrumentor creates spans automatically, so this will
                                # link to the auto-root span if created, or to existing parent
                                response = await original_create(*args, **kwargs)
                                self._extract_tokens_from_response(response)
                                return response
                        
                        @functools.wraps(original_create)
                        def sync_wrapper(*args, **kwargs):
                            # Auto-create root span if no active span exists (plug-and-play behavior)
                            # The official instrumentor will create "llm.request" spans, but we need
                            # to ensure there's a root trace if none exists
                            with ensure_root_span("openai"):
                                # Official instrumentor creates spans automatically, so this will
                                # link to the auto-root span if created, or to existing parent
                                response = original_create(*args, **kwargs)
                                self._extract_tokens_from_response(response)
                                return response
                        
                        import inspect
                        if inspect.iscoroutinefunction(original_create):
                            async_wrapper._instrumented = True
                            openai_self.chat.completions.create = async_wrapper
                        else:
                            sync_wrapper._instrumented = True
                            openai_self.chat.completions.create = sync_wrapper
                
                openai.OpenAI.__init__ = patched_init
                
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Failed to wrap OpenAI client for token extraction", error=str(e))

    def _extract_tokens_from_response(self, response: Any) -> None:
        """Extract token usage from response and set on current span."""
        try:
            from opentelemetry.trace import get_current_span
            
            span = get_current_span()
            if not span or not hasattr(span, 'set_attribute'):
                return
            
            # Extract token usage from response (same as our custom instrumentor)
            prompt_tokens = 0
            completion_tokens = 0
            
            if hasattr(response, "usage"):
                usage = response.usage
                prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
                completion_tokens = getattr(usage, "completion_tokens", 0) or 0
            
            # Set token counts on span so span processor can read them
            if prompt_tokens > 0 or completion_tokens > 0:
                span.set_attribute("gen_ai.token.count.prompt", prompt_tokens)
                span.set_attribute("gen_ai.token.count.completion", completion_tokens)
                span.set_attribute("gen_ai.token.count", {
                    "prompt": prompt_tokens,
                    "completion": completion_tokens
                })
                # Also set our custom attributes for compatibility
                span.set_attribute("llm.usage.prompt_tokens", prompt_tokens)
                span.set_attribute("llm.usage.completion_tokens", completion_tokens)
                span.set_attribute("llm.usage.total_tokens", prompt_tokens + completion_tokens)
                
        except Exception as e:
            # Don't fail if token extraction fails
            import structlog
            logger = structlog.get_logger()
            logger.debug("Failed to extract tokens from response", error=str(e))

    def uninstrument(self) -> None:
        """Remove GenAI instrumentation."""
        if not self._instrumented or not self._instrumentor:
            return

        try:
            self._instrumentor.uninstrument()
            self._instrumented = False
            
            import structlog
            logger = structlog.get_logger()
            logger.info("GenAI instrumentation disabled")
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.error("Failed to disable GenAI instrumentation", error=str(e))

