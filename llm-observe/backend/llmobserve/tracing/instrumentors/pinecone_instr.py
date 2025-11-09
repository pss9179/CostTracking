"""Pinecone auto-instrumentation for OpenTelemetry."""

import functools
import time
from types import MethodType
from typing import Any, Callable, Optional

from opentelemetry import trace

from llmobserve.pricing import pricing_registry
from llmobserve.semantics import API_COST_USD, API_LATENCY_MS, API_OPERATION, API_PROVIDER, API_REQUEST_SIZE
from llmobserve.tracing.enrichers import SpanEnricher
from llmobserve.tracing.instrumentors.base import Instrumentor, ensure_root_span

tracer = trace.get_tracer(__name__)


class PineconeInstrumentor(Instrumentor):
    """Auto-instrumentation for Pinecone library."""

    def __init__(self, span_enricher: Optional[SpanEnricher] = None):
        """Initialize with optional span enricher."""
        self.span_enricher = span_enricher or SpanEnricher()
        self._original_index_descriptor = None
        self._instrumented = False

    def instrument(self) -> None:
        """Apply Pinecone instrumentation."""
        if self._instrumented:
            return

        try:
            from pinecone import Pinecone

            # Pinecone v7: Index is a descriptor accessed via Pinecone(api_key).Index(name)
            # We need to wrap Pinecone.Index descriptor to instrument returned Index instances
            if hasattr(Pinecone, "Index"):
                # Store original Index descriptor
                self._original_index_descriptor = Pinecone.Index
                
                # Create a descriptor wrapper that instruments the returned Index instance
                class IndexDescriptor:
                    """Descriptor wrapper that instruments Index instances."""
                    
                    def __init__(self, original_descriptor, instrumentor_instance):
                        self.original_descriptor = original_descriptor
                        self.instrumentor = instrumentor_instance
                    
                    def __get__(self, obj, objtype=None):
                        """Return a bound method that wraps Index creation."""
                        if obj is None:
                            return self
                        
                        # Get the original bound method
                        original_method = self.original_descriptor.__get__(obj, objtype)
                        
                        # Create wrapper that instruments the returned Index instance
                        def wrapped_index(name: str, *args, **kwargs):
                            """Wrap Index() call to instrument the returned instance."""
                            # Call original Index method to get the instance
                            index_instance = original_method(name, *args, **kwargs)
                            
                            # Instrument the instance methods if not already done
                            if not hasattr(index_instance, "_llmobserve_instrumented"):
                                # Wrap query method
                                if hasattr(index_instance, "query"):
                                    # Prevents duplicate instrumentation during reloads or multiple setup calls
                                    if not hasattr(index_instance.query, "_instrumented"):
                                        original_query = index_instance.query
                                        
                                        def wrapped_query(self_instance, *args, **kwargs):
                                            # original_query is already bound, so call it directly
                                            return self.instrumentor._trace_api_call(
                                                "query", original_query, index_instance, *args, **kwargs
                                            )
                                        # Use MethodType to properly bind as a method
                                        wrapped_query = functools.wraps(original_query)(wrapped_query)
                                        wrapped_query._instrumented = True
                                        index_instance.query = MethodType(wrapped_query, index_instance)
                                
                                # Wrap upsert method
                                if hasattr(index_instance, "upsert"):
                                    # Prevents duplicate instrumentation during reloads or multiple setup calls
                                    if not hasattr(index_instance.upsert, "_instrumented"):
                                        original_upsert = index_instance.upsert
                                        
                                        def wrapped_upsert(self_instance, *args, **kwargs):
                                            return self.instrumentor._trace_api_call(
                                                "upsert", original_upsert, index_instance, *args, **kwargs
                                            )
                                        wrapped_upsert = functools.wraps(original_upsert)(wrapped_upsert)
                                        wrapped_upsert._instrumented = True
                                        index_instance.upsert = MethodType(wrapped_upsert, index_instance)
                                
                                # Wrap delete method
                                if hasattr(index_instance, "delete"):
                                    # Prevents duplicate instrumentation during reloads or multiple setup calls
                                    if not hasattr(index_instance.delete, "_instrumented"):
                                        original_delete = index_instance.delete
                                        
                                        def wrapped_delete(self_instance, *args, **kwargs):
                                            return self.instrumentor._trace_api_call(
                                                "delete", original_delete, index_instance, *args, **kwargs
                                            )
                                        wrapped_delete = functools.wraps(original_delete)(wrapped_delete)
                                        wrapped_delete._instrumented = True
                                        index_instance.delete = MethodType(wrapped_delete, index_instance)
                                
                                index_instance._llmobserve_instrumented = True
                            
                            return index_instance
                        
                        return wrapped_index
                
                # Replace Pinecone.Index with our descriptor wrapper
                Pinecone.Index = IndexDescriptor(self._original_index_descriptor, self)
                
                self._instrumented = True
        except ImportError:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Pinecone not installed, skipping instrumentation")
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Failed to instrument Pinecone", error=str(e), exc_info=True)

    def uninstrument(self) -> None:
        """Remove Pinecone instrumentation."""
        if not self._instrumented:
            return

        try:
            from pinecone import Pinecone

            if self._original_index_descriptor:
                Pinecone.Index = self._original_index_descriptor

            self._instrumented = False
        except ImportError:
            pass
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Failed to uninstrument Pinecone", error=str(e))

    def _trace_api_call(self, operation: str, original_func: Callable, index_self: Any, *args, **kwargs) -> Any:
        """Trace a Pinecone API call."""
        start_time = time.time()
        span_name = f"pinecone.{operation}"

        # Auto-create root span if no active span exists (plug-and-play behavior)
        # This ensures every API call gets a trace, even without manual setup
        with ensure_root_span("pinecone"):
            # Create child span for the actual API operation
            # If ensure_root_span created a parent, this will link to it
            # If a parent already existed, this will link to that parent
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute(API_PROVIDER, "pinecone")
                span.set_attribute(API_OPERATION, operation)

                # Calculate request size
                request_size = self._calculate_request_size(operation, *args, **kwargs)
                if request_size:
                    span.set_attribute(API_REQUEST_SIZE, request_size)

                response = None
                error_occurred = False
                try:
                    # original_func is already a bound method, so call it directly without index_self
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
                    
                    # Calculate cost (default to 0 if request failed)
                    cost = 0.0
                    if not error_occurred:
                        try:
                            cost = self._calculate_cost(operation, request_size)
                        except Exception:
                            cost = 0.0
                    span.set_attribute(API_COST_USD, cost)

                    # Enrich span if enricher available
                    if self.span_enricher:
                        try:
                            self.span_enricher.enrich_api_span(span, operation, latency_ms, request_size, cost)
                        except Exception:
                            pass  # Don't fail if enrichment fails

    def _calculate_request_size(self, operation: str, *args, **kwargs) -> Optional[int]:
        """Calculate request size based on operation type."""
        if operation == "query":
            # For query, count the number of queries (top_k or vector count)
            top_k = kwargs.get("top_k", 1)
            if "queries" in kwargs:
                queries = kwargs["queries"]
                if isinstance(queries, list):
                    return len(queries) * top_k
                return top_k
            return top_k
        elif operation == "upsert":
            # For upsert, count vectors
            if "vectors" in kwargs:
                vectors = kwargs["vectors"]
                if isinstance(vectors, list):
                    return len(vectors)
            return 0
        elif operation == "delete":
            # For delete, count IDs
            if "ids" in kwargs:
                ids = kwargs["ids"]
                if isinstance(ids, list):
                    return len(ids)
            return 1
        return None

    def _calculate_cost(self, operation: str, request_size: Optional[int]) -> float:
        """Calculate cost for Pinecone operation."""
        if operation == "query":
            # $0.096 per 1K queries
            # For query operations, cost is per query (not per top_k), so always use 1
            # regardless of request_size
            cost = (1 / 1000) * 0.096
            return cost
        
        if not request_size:
            return 0.0
        elif operation == "upsert":
            # $0.12 per 100K vectors
            cost = (request_size / 100000) * 0.12
        elif operation == "delete":
            # Deletes are free
            cost = 0.0
        else:
            cost = 0.0

        return cost


class SimplePineconeInstrumentor(Instrumentor):
    """
    Simplified auto-instrumentation for Pinecone SDK using wrapt.
    
    Automatically patches Pinecone v7.x Index.query() calls to create spans,
    capture attributes, and calculate costs. Once instrumented, all Pinecone
    query calls are automatically traced without requiring manual span creation.
    """

    def __init__(self, span_enricher: Optional[SpanEnricher] = None):
        """Initialize with optional span enricher."""
        self.span_enricher = span_enricher or SpanEnricher()
        self._original_index_descriptor = None
        self._instrumented = False

    def instrument(self) -> None:
        """Apply Pinecone instrumentation using wrapt."""
        if self._instrumented:
            return

        try:
            import wrapt
            from pinecone import Pinecone

            # Pinecone v7.x: Index is a descriptor accessed via Pinecone(api_key).Index(name)
            # We need to wrap the descriptor to capture index name and instrument query method
            if hasattr(Pinecone, "Index"):
                self._original_index_descriptor = Pinecone.Index

                class IndexDescriptor:
                    """Descriptor wrapper that stores index name and instruments query method."""

                    def __init__(self, original_descriptor, instrumentor_instance):
                        self.original_descriptor = original_descriptor
                        self.instrumentor = instrumentor_instance

                    def __get__(self, obj, objtype=None):
                        """Return wrapped Index creation method."""
                        if obj is None:
                            return self

                        original_method = self.original_descriptor.__get__(obj, objtype)

                        def wrapped_index(name: str, *args, **kwargs):
                            """Wrap Index() call to store name and instrument query."""
                            # Extract index name (first positional arg or from kwargs)
                            index_name = name if name else kwargs.get("name", "unknown")

                            # Call original to get Index instance
                            index_instance = original_method(name, *args, **kwargs)

                            # Store index name on instance for later use
                            if not hasattr(index_instance, "_llmobserve_index_name"):
                                index_instance._llmobserve_index_name = index_name

                            # Instrument query method if not already done
                            if not hasattr(index_instance, "_llmobserve_simple_instrumented"):
                                # Prevents duplicate instrumentation during reloads or multiple setup calls
                                if not hasattr(index_instance.query, "_instrumented"):
                                    original_query = index_instance.query

                                    def wrapped_query(self_instance, *query_args, **query_kwargs):
                                        """Wrap query() method to create span and capture attributes."""
                                        return self.instrumentor._trace_query(
                                            index_instance, original_query, query_args, query_kwargs
                                        )

                                    # Use functools.wraps and MethodType to properly bind as a method
                                    wrapped_query = functools.wraps(original_query)(wrapped_query)
                                    wrapped_query._instrumented = True
                                    index_instance.query = MethodType(wrapped_query, index_instance)
                                    index_instance._llmobserve_simple_instrumented = True

                            return index_instance

                        return wrapped_index

                Pinecone.Index = IndexDescriptor(self._original_index_descriptor, self)
                self._instrumented = True

                import structlog
                logger = structlog.get_logger()
                logger.info("SimplePineconeInstrumentor enabled")

        except ImportError as e:
            import structlog
            logger = structlog.get_logger()
            if "wrapt" in str(e) or "pinecone" in str(e):
                logger.warning("Pinecone or wrapt not installed, skipping SimplePineconeInstrumentor")
            else:
                logger.warning("Failed to enable SimplePineconeInstrumentor", error=str(e))
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.error("Failed to instrument Pinecone", error=str(e), exc_info=True)

    def uninstrument(self) -> None:
        """Remove Pinecone instrumentation."""
        if not self._instrumented:
            return

        try:
            from pinecone import Pinecone

            if self._original_index_descriptor:
                Pinecone.Index = self._original_index_descriptor

            self._instrumented = False
        except ImportError:
            pass
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.warning("Failed to uninstrument Pinecone", error=str(e))

    def _trace_query(
        self, index_instance: Any, original_query: Callable, args: tuple, kwargs: dict
    ) -> Any:
        """Trace a Pinecone query call with required attributes."""
        import time

        start_time = time.time()
        span_name = "pinecone.query"

        # Extract index name from instance
        index_name = getattr(index_instance, "_llmobserve_index_name", "unknown")

        # Auto-create root span if no active span exists (plug-and-play behavior)
        # This ensures every API call gets a trace, even without manual setup
        with ensure_root_span("pinecone"):
            # Create child span for the actual query operation
            # If ensure_root_span created a parent, this will link to it
            # If a parent already existed, this will link to that parent
            with tracer.start_as_current_span(span_name) as span:
                # Set required attributes
                span.set_attribute("service.name", "pinecone")
                span.set_attribute("pinecone.index_name", index_name)
                span.set_attribute("pinecone.top_k", kwargs.get("top_k", 0))
                span.set_attribute("pinecone.query_units", 1)

                # Set standard API attributes for compatibility
                span.set_attribute(API_PROVIDER, "pinecone")
                span.set_attribute(API_OPERATION, "query")

                result = None
                error_occurred = False
                try:
                    # Call original query method
                    result = original_query(*args, **kwargs)
                    return result
                except Exception as e:
                    error_occurred = True
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
                finally:
                    # Ensures cost is logged even if the API call raises an exception
                    latency_ms = (time.time() - start_time) * 1000
                    span.set_attribute(API_LATENCY_MS, latency_ms)
                    
                    # Extract result_count from response if available
                    if result is not None and isinstance(result, dict) and "matches" in result:
                        result_count = len(result["matches"])
                        span.set_attribute("pinecone.result_count", result_count)

                    # Calculate cost (same as existing instrumentor: $0.096 per 1K queries)
                    # Default to 0 if request failed
                    cost = 0.0 if error_occurred else ((1 / 1000) * 0.096)
                    span.set_attribute(API_COST_USD, cost)

                    # Enrich span using SpanEnricher (writes to DB)
                    if self.span_enricher:
                        try:
                            # Request size is 1 for query operations
                            self.span_enricher.enrich_api_span(span, "query", latency_ms, 1, cost)
                        except Exception:
                            pass  # Don't fail if enrichment fails
