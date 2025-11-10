"""Generic fallback instrumentor using regex matching for unknown SDKs."""

import functools
import re
import time
from typing import Any, Callable, Optional

from opentelemetry import trace

from llmobserve.pricing import pricing_registry
from llmobserve.semantics import AI_COST_USD, AI_LATENCY_MS, AI_MODEL, AI_OPERATION, AI_PROVIDER
from llmobserve.tracing.enrichers import SpanEnricher
from llmobserve.tracing.instrumentors.base import Instrumentor, ensure_root_span

tracer = trace.get_tracer(__name__)

# Provider detection patterns: regex pattern -> provider name
PROVIDER_PATTERNS = {
    r".*anthropic.*": "anthropic",
    r".*cohere.*": "cohere",
    r".*mistral.*": "mistral",
    r".*gemini.*": "gemini",
    r".*google.*generative.*": "gemini",
    r".*xai.*": "xai",
    r".*bedrock.*": "bedrock",
    r".*together.*": "together",
    r".*weaviate.*": "weaviate",
    r".*qdrant.*": "qdrant",
    r".*milvus.*": "milvus",
    r".*chroma.*": "chroma",
    r".*redis.*vector.*": "redisvector",
    r".*jina.*": "jinaai",
    r".*voyage.*": "voyageai",
    r".*replicate.*": "replicate",
    r".*huggingface.*": "huggingface",
    r".*deepgram.*": "deepgram",
    r".*elevenlabs.*": "elevenlabs",
}

# Operation detection patterns: function/method name -> operation type
OPERATION_PATTERNS = {
    r".*create.*": "create",
    r".*generate.*": "generate",
    r".*query.*": "query",
    r".*search.*": "search",
    r".*embed.*": "embed",
    r".*completion.*": "completion",
    r".*chat.*": "chat",
    r".*transcribe.*": "transcribe",
    r".*run.*": "run",
}


class GenericInstrumentor(Instrumentor):
    """
    Generic fallback instrumentor that uses regex matching to detect providers.
    
    This instrumentor attempts to detect AI/vector SDKs by matching class and
    function names against known patterns. It creates spans with generic
    attributes and uses a dynamic pricing table.
    """

    def __init__(self, span_enricher: Optional[SpanEnricher] = None, dynamic_pricing: Optional[dict] = None):
        """Initialize generic instrumentor.
        
        Args:
            span_enricher: Optional span enricher for span enrichment
            dynamic_pricing: Optional dynamic pricing table (can be updated via API)
        """
        self.span_enricher = span_enricher or SpanEnricher()
        self.dynamic_pricing = dynamic_pricing or {}
        self._instrumented_modules = {}
        self._instrumented = False

    def instrument(self) -> None:
        """Apply generic instrumentation to common AI SDK patterns."""
        if self._instrumented:
            return

        # Try to instrument common module patterns
        # This is a best-effort approach for unknown SDKs
        try:
            import sys
            import importlib
            
            # Common module names to check
            modules_to_check = [
                "anthropic", "cohere", "mistralai", "google.generativeai",
                "xai", "boto3", "together", "weaviate", "qdrant_client",
                "pymilvus", "chromadb", "redis", "jinaai", "voyageai",
                "replicate", "huggingface_hub", "deepgram", "elevenlabs"
            ]
            
            for module_name in modules_to_check:
                if module_name in sys.modules:
                    try:
                        module = sys.modules[module_name]
                        self._try_instrument_module(module, module_name)
                    except Exception:
                        pass  # Skip if can't instrument
                        
            self._instrumented = True
            
            import structlog
            logger = structlog.get_logger()
            logger.info("Generic instrumentor enabled (fallback mode)")
            
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Failed to enable generic instrumentor", error=str(e))

    def _try_instrument_module(self, module: Any, module_name: str) -> None:
        """Try to instrument a module by wrapping common patterns."""
        # Detect provider from module name
        provider = self._detect_provider(module_name)
        if not provider:
            return

        # Try to find and wrap common client classes
        for attr_name in dir(module):
            if not attr_name[0].isupper():  # Skip non-classes
                continue
                
            try:
                attr = getattr(module, attr_name)
                if not isinstance(attr, type):
                    continue
                    
                # Check if it looks like a client class
                if any(keyword in attr_name.lower() for keyword in ["client", "api", "model"]):
                    self._wrap_client_class(attr, provider)
            except Exception:
                pass  # Skip if can't wrap

    def _wrap_client_class(self, client_class: type, provider: str) -> None:
        """Wrap methods on a client class."""
        # Find methods that match operation patterns
        for method_name in dir(client_class):
            if method_name.startswith("_"):
                continue
                
            operation = self._detect_operation(method_name)
            if not operation:
                continue
                
            try:
                original_method = getattr(client_class, method_name)
                if not callable(original_method):
                    continue
                    
                wrapped = self._create_wrapper(original_method, provider, operation)
                setattr(client_class, method_name, wrapped)
            except Exception:
                pass  # Skip if can't wrap

    def _create_wrapper(self, original_func: Callable, provider: str, operation: str) -> Callable:
        """Create a wrapper function for an API call."""
        @functools.wraps(original_func)
        async def async_wrapper(*args, **kwargs):
            return await self._trace_call_async(original_func, provider, operation, *args, **kwargs)
        
        @functools.wraps(original_func)
        def sync_wrapper(*args, **kwargs):
            return self._trace_call_sync(original_func, provider, operation, *args, **kwargs)
        
        import inspect
        if inspect.iscoroutinefunction(original_func):
            return async_wrapper
        return sync_wrapper

    async def _trace_call_async(self, original_func: Callable, provider: str, operation: str, *args, **kwargs) -> Any:
        """Trace an async API call with generic attributes."""
        start_time = time.time()
        span_name = f"{provider}.{operation}"

        # Auto-create root span if no active span exists
        with ensure_root_span(provider):
            with tracer.start_as_current_span(span_name) as span:
                # Set generic AI attributes
                span.set_attribute(AI_PROVIDER, provider)
                span.set_attribute(AI_OPERATION, operation)
                
                # Try to extract model from kwargs
                model = kwargs.get("model") or kwargs.get("model_name") or "unknown"
                if model != "unknown":
                    span.set_attribute(AI_MODEL, model)

                result = None
                error_occurred = False
                try:
                    # Call original async function
                    result = await original_func(*args, **kwargs)
                    return result
                except Exception as e:
                    error_occurred = True
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
                finally:
                    # Ensures cost is logged even if the API call raises an exception
                    latency_ms = (time.time() - start_time) * 1000
                    span.set_attribute(AI_LATENCY_MS, latency_ms)
                    
                    # Calculate cost using dynamic pricing or fallback, default to 0 if failed
                    cost = 0.0 if error_occurred else self._calculate_cost(provider, operation, model)
                    span.set_attribute(AI_COST_USD, cost)
                    
                    # Enrich span if enricher available
                    if self.span_enricher:
                        try:
                            # Use API enricher for generic spans
                            self.span_enricher.enrich_api_span(span, operation, latency_ms, 1, cost)
                        except Exception:
                            pass  # Don't fail if enrichment fails

    def _trace_call_sync(self, original_func: Callable, provider: str, operation: str, *args, **kwargs) -> Any:
        """Trace a sync API call with generic attributes."""
        start_time = time.time()
        span_name = f"{provider}.{operation}"

        # Auto-create root span if no active span exists
        with ensure_root_span(provider):
            with tracer.start_as_current_span(span_name) as span:
                # Set generic AI attributes
                span.set_attribute(AI_PROVIDER, provider)
                span.set_attribute(AI_OPERATION, operation)
                
                # Try to extract model from kwargs
                model = kwargs.get("model") or kwargs.get("model_name") or "unknown"
                if model != "unknown":
                    span.set_attribute(AI_MODEL, model)

                result = None
                error_occurred = False
                try:
                    # Call original sync function
                    result = original_func(*args, **kwargs)
                    return result
                except Exception as e:
                    error_occurred = True
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
                finally:
                    # Ensures cost is logged even if the API call raises an exception
                    latency_ms = (time.time() - start_time) * 1000
                    span.set_attribute(AI_LATENCY_MS, latency_ms)
                    
                    # Calculate cost using dynamic pricing or fallback, default to 0 if failed
                    cost = 0.0 if error_occurred else self._calculate_cost(provider, operation, model)
                    span.set_attribute(AI_COST_USD, cost)
                    
                    # Enrich span if enricher available
                    if self.span_enricher:
                        try:
                            # Use API enricher for generic spans
                            self.span_enricher.enrich_api_span(span, operation, latency_ms, 1, cost)
                        except Exception:
                            pass  # Don't fail if enrichment fails

    def _detect_provider(self, name: str) -> Optional[str]:
        """Detect provider name from class/module name using regex patterns."""
        name_lower = name.lower()
        for pattern, provider in PROVIDER_PATTERNS.items():
            if re.match(pattern, name_lower):
                return provider
        return None

    def _detect_operation(self, name: str) -> Optional[str]:
        """Detect operation type from function/method name."""
        name_lower = name.lower()
        for pattern, operation in OPERATION_PATTERNS.items():
            if re.match(pattern, name_lower):
                return operation
        return None

    def _calculate_cost(self, provider: str, operation: str, model: str) -> float:
        """Calculate cost using dynamic pricing or fallback to pricing_registry."""
        # Try dynamic pricing first
        pricing_key = f"{provider}-{operation}"
        if pricing_key in self.dynamic_pricing:
            price_info = self.dynamic_pricing[pricing_key]
            if isinstance(price_info, dict):
                return price_info.get("request", 0.0)
            return float(price_info) if price_info else 0.0
        
        # Try model-based pricing for LLMs
        if model and model != "unknown":
            price = pricing_registry.get_price(model)
            if price:
                # For LLMs, we'd need token counts - default to 0 for generic
                return 0.0
        
        # Try vector DB pricing
        cost = pricing_registry.cost_for_vector_db(provider, operation, 1)
        if cost > 0:
            return cost
        
        # Fallback to 0 if no pricing found
        return 0.0

    def update_dynamic_pricing(self, pricing: dict) -> None:
        """Update dynamic pricing table (can be called via API)."""
        self.dynamic_pricing.update(pricing)

    def uninstrument(self) -> None:
        """Remove generic instrumentation."""
        # Generic instrumentor doesn't track original methods well,
        # so uninstrumentation is limited
        self._instrumented = False
        
        import structlog
        logger = structlog.get_logger()
        logger.info("Generic instrumentor disabled")

