"""
gRPC Interceptor for LLMObserve Context Propagation and Cost Tracking

Patches grpcio to inject context metadata and track costs using ORCA (Open Request Cost Aggregation).
ORCA is the official gRPC standard for cost tracking - works with ANY gRPC API that supports it.
"""

import logging
import time
import uuid
from typing import Any, Callable, Optional, Dict

from llmobserve import config, context, buffer
from llmobserve.grpc_costs import get_grpc_cost, parse_grpc_method

logger = logging.getLogger("llmobserve")

_grpc_patched = False


def patch_grpc() -> bool:
    """
    Patch grpcio to inject LLMObserve context as gRPC metadata.
    
    Returns:
        bool: True if patching succeeded, False otherwise.
    """
    global _grpc_patched
    
    if _grpc_patched:
        logger.debug("[llmobserve] gRPC already patched")
        return True
    
    try:
        import grpc
        from grpc import UnaryUnaryClientInterceptor, UnaryStreamClientInterceptor
    except ImportError:
        logger.debug("[llmobserve] grpcio not installed, skipping gRPC patching")
        return False
    
    try:
        # Create custom interceptor
        class LLMObserveInterceptor(UnaryUnaryClientInterceptor, UnaryStreamClientInterceptor):
            """Interceptor that injects LLMObserve context and tracks costs using ORCA."""
            
            def _inject_metadata(self, client_call_details):
                """Inject context into gRPC metadata."""
                if not config.is_enabled():
                    return client_call_details
                
                # Get existing metadata
                metadata = []
                if client_call_details.metadata is not None:
                    metadata = list(client_call_details.metadata)
                
                try:
                    # Inject LLMObserve context
                    metadata.append(("x-llmobserve-run-id", context.get_run_id()))
                    metadata.append(("x-llmobserve-span-id", str(uuid.uuid4())))
                    
                    parent_span = context.get_current_span_id()
                    if parent_span:
                        metadata.append(("x-llmobserve-parent-span-id", parent_span))
                    
                    metadata.append(("x-llmobserve-section", context.get_current_section()))
                    metadata.append(("x-llmobserve-section-path", context.get_section_path()))
                    
                    customer = context.get_customer_id()
                    if customer:
                        metadata.append(("x-llmobserve-customer-id", customer))
                    
                    logger.debug(f"[llmobserve] Injected context into gRPC call: {client_call_details.method}")
                except Exception as e:
                    # Fail-open: if injection fails, continue anyway
                    logger.debug(f"[llmobserve] gRPC metadata injection failed: {e}")
                
                # Create new call details with updated metadata
                return grpc._interceptor._ClientCallDetails(
                    method=client_call_details.method,
                    timeout=client_call_details.timeout,
                    metadata=metadata,
                    credentials=client_call_details.credentials,
                    wait_for_ready=client_call_details.wait_for_ready,
                    compression=client_call_details.compression
                )
            
            def _extract_orca_cost(self, trailing_metadata) -> Optional[float]:
                """
                Extract cost from ORCA (Open Request Cost Aggregation) trailing metadata.
                
                ORCA is the official gRPC standard for cost tracking.
                Works with ANY gRPC API that implements ORCA.
                
                Args:
                    trailing_metadata: gRPC trailing metadata tuple list
                
                Returns:
                    Cost in USD if found, None otherwise
                """
                if not trailing_metadata:
                    return None
                
                try:
                    # Convert metadata to dict (handle both tuple and dict formats)
                    metadata_dict = {}
                    for item in trailing_metadata:
                        if isinstance(item, tuple) and len(item) == 2:
                            key, value = item
                            metadata_dict[key.lower()] = value
                        elif isinstance(item, dict):
                            metadata_dict.update({k.lower(): v for k, v in item.items()})
                    
                    # ORCA standard: "orca-cost" key contains cost in USD as string
                    orca_cost = metadata_dict.get("orca-cost")
                    if orca_cost:
                        try:
                            return float(orca_cost)
                        except (ValueError, TypeError):
                            logger.debug(f"[llmobserve] Invalid ORCA cost value: {orca_cost}")
                    
                    # Also check for other common cost metadata keys (non-standard)
                    for key in ["cost", "cost-usd", "request-cost"]:
                        if key in metadata_dict:
                            try:
                                return float(metadata_dict[key])
                            except (ValueError, TypeError):
                                pass
                
                except Exception as e:
                    logger.debug(f"[llmobserve] Error extracting ORCA cost: {e}")
                
                return None
            
            def _track_grpc_call(
                self,
                method: str,
                start_time: float,
                cost_usd: Optional[float] = None,
                error: Optional[Exception] = None,
                trailing_metadata: Optional[Any] = None,
                request_size: int = 0,
                response_size: int = 0
            ):
                """Track gRPC call and emit event."""
                if not config.is_enabled():
                    return
                
                try:
                    latency_ms = (time.time() - start_time) * 1000
                    
                    # Extract provider from method name (e.g., "/pinecone.Query/Query" -> "pinecone")
                    service, _ = parse_grpc_method(method)
                    provider = service
                    
                    # Map known services to provider names
                    if "pinecone" in provider:
                        provider = "pinecone"
                    elif "vertex" in provider or "aiplatform" in provider:
                        provider = "google"
                    
                    # Determine status
                    status = "error" if error else "ok"
                    
                    # Create event
                    event = {
                        "id": str(uuid.uuid4()),
                        "run_id": context.get_run_id(),
                        "span_id": context.get_current_span_id() or str(uuid.uuid4()),
                        "parent_span_id": context.get_parent_span_id(),
                        "section": context.get_current_section(),
                        "section_path": context.get_section_path(),
                        "span_type": "grpc_call",
                        "provider": provider,
                        "endpoint": method,
                        "model": None,
                        "cost_usd": cost_usd or 0.0,
                        "latency_ms": latency_ms,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "cached_tokens": 0,
                        "status": status,
                        "tenant_id": config.get_tenant_id(),
                        "customer_id": context.get_customer_id(),
                        "event_metadata": {
                            "grpc_method": method,
                            "orca_cost_available": cost_usd is not None and cost_usd > 0,
                            "cost_source": "orca" if (cost_usd and cost_usd > 0 and trailing_metadata) else ("configured" if get_grpc_cost(*parse_grpc_method(method)) > 0 else "estimated"),
                            "request_size_bytes": request_size,
                            "response_size_bytes": response_size,
                            "error": str(error) if error else None,
                        }
                    }
                    
                    buffer.add_event(event)
                    logger.debug(f"[llmobserve] Tracked gRPC call: {method}, cost: ${cost_usd or 0.0}")
                
                except Exception as e:
                    # Fail-open: don't break user's gRPC calls
                    logger.debug(f"[llmobserve] Failed to track gRPC call: {e}")
            
            def _estimate_cost_from_size(self, request_size: int, response_size: int) -> float:
                """
                Estimate cost based on request/response sizes (generic, no schemas needed).
                
                This is a heuristic approach - works for ANY gRPC API without schemas.
                Uses simple size-based estimation (can be improved with ML/historical data).
                
                Args:
                    request_size: Request size in bytes
                    response_size: Response size in bytes
                
                Returns:
                    Estimated cost in USD (heuristic)
                """
                # Simple heuristic: $0.000001 per KB of data transferred
                # This is generic and works for any API
                # Users can override with configure_grpc_cost() if they know actual costs
                total_bytes = request_size + response_size
                cost_per_kb = 0.000001  # $0.000001 per KB (very conservative estimate)
                estimated_cost = (total_bytes / 1024) * cost_per_kb
                
                # Cap at reasonable maximum (prevent outliers)
                return min(estimated_cost, 0.01)  # Max $0.01 per call
            
            def intercept_unary_unary(self, continuation, client_call_details, request):
                """Intercept unary-unary RPC calls."""
                if not config.is_enabled():
                    return continuation(client_call_details, request)
                
                new_details = self._inject_metadata(client_call_details)
                start_time = time.time()
                error = None
                
                # Estimate request size (generic, no parsing needed)
                request_size = 0
                try:
                    if hasattr(request, 'ByteSize'):
                        request_size = request.ByteSize()
                    elif hasattr(request, '__sizeof__'):
                        request_size = request.__sizeof__()
                except:
                    pass
                
                try:
                    # Use grpc.Call to access trailing metadata properly
                    response = continuation(new_details, request)
                    
                    # Estimate response size (generic, no parsing needed)
                    response_size = 0
                    try:
                        if hasattr(response, 'ByteSize'):
                            response_size = response.ByteSize()
                        elif hasattr(response, '__sizeof__'):
                            response_size = response.__sizeof__()
                    except:
                        pass
                    
                    # Extract ORCA cost from trailing metadata
                    # gRPC responses have trailing_metadata() method
                    trailing_metadata = None
                    cost_usd = None
                    
                    try:
                        # Try to get trailing metadata from response
                        # gRPC responses may have trailing_metadata() method or attribute
                        if hasattr(response, 'trailing_metadata'):
                            if callable(response.trailing_metadata):
                                trailing_metadata = response.trailing_metadata()
                            else:
                                trailing_metadata = response.trailing_metadata
                        
                        # Priority 1: ORCA cost (standard, most accurate)
                        cost_usd = self._extract_orca_cost(trailing_metadata)
                        
                        # Priority 2: Configured cost (if user set it)
                        if cost_usd is None:
                            service, method = parse_grpc_method(client_call_details.method)
                            configured_cost = get_grpc_cost(service, method)
                            if configured_cost > 0:
                                cost_usd = configured_cost
                                logger.debug(f"[llmobserve] Using configured cost for {service}/{method}: ${cost_usd}")
                        
                        # Priority 3: Size-based estimation (generic, works for ANY API)
                        if cost_usd is None or cost_usd == 0:
                            cost_usd = self._estimate_cost_from_size(request_size, response_size)
                            logger.debug(f"[llmobserve] Estimated cost from size: ${cost_usd:.6f} ({request_size + response_size} bytes)")
                    except Exception as e:
                        logger.debug(f"[llmobserve] Could not extract cost: {e}")
                        # Fallback to size estimation
                        cost_usd = self._estimate_cost_from_size(request_size, response_size)
                    
                    # Track the call
                    self._track_grpc_call(
                        method=client_call_details.method,
                        start_time=start_time,
                        cost_usd=cost_usd,
                        error=None,
                        trailing_metadata=trailing_metadata,
                        request_size=request_size,
                        response_size=response_size
                    )
                    
                    return response
                
                except Exception as e:
                    error = e
                    # Track error
                    self._track_grpc_call(
                        method=client_call_details.method,
                        start_time=start_time,
                        cost_usd=None,
                        error=error,
                        trailing_metadata=None
                    )
                    raise
            
            def intercept_unary_stream(self, continuation, client_call_details, request):
                """Intercept unary-stream RPC calls."""
                if not config.is_enabled():
                    return continuation(client_call_details, request)
                
                new_details = self._inject_metadata(client_call_details)
                start_time = time.time()
                
                # For streaming, we track when stream completes
                # Note: ORCA cost might come in trailing metadata at end of stream
                try:
                    response_stream = continuation(new_details, request)
                    
                    # Wrap stream to track completion
                    def tracked_stream():
                        error = None
                        trailing_metadata = None
                        try:
                            for item in response_stream:
                                yield item
                        except Exception as e:
                            error = e
                            raise
                        finally:
                            # Try to get trailing metadata if available
                            if hasattr(response_stream, 'trailing_metadata'):
                                trailing_metadata = response_stream.trailing_metadata
                            
                            # Priority 1: ORCA cost (standard)
                            cost_usd = self._extract_orca_cost(trailing_metadata)
                            
                            # Priority 2: Configured cost
                            if cost_usd is None:
                                service, method = parse_grpc_method(client_call_details.method)
                                configured_cost = get_grpc_cost(service, method)
                                if configured_cost > 0:
                                    cost_usd = configured_cost
                                    logger.debug(f"[llmobserve] Using configured cost for {service}/{method}: ${cost_usd}")
                            
                            # Priority 3: Size-based estimation (generic fallback)
                            # Note: For streaming, we can't easily get total size, so skip estimation
                            # Streaming costs should use ORCA or manual config
                            
                            # Track the call
                            self._track_grpc_call(
                                method=client_call_details.method,
                                start_time=start_time,
                                cost_usd=cost_usd,
                                error=error,
                                trailing_metadata=trailing_metadata
                            )
                    
                    return tracked_stream()
                
                except Exception as e:
                    # Track error
                    self._track_grpc_call(
                        method=client_call_details.method,
                        start_time=start_time,
                        cost_usd=None,
                        error=e,
                        trailing_metadata=None
                    )
                    raise
        
        # Patch grpc.insecure_channel and grpc.secure_channel
        original_insecure_channel = grpc.insecure_channel
        original_secure_channel = grpc.secure_channel
        
        def patched_insecure_channel(target, options=None, compression=None):
            """Patched insecure_channel that adds our interceptor."""
            channel = original_insecure_channel(target, options, compression)
            interceptor = LLMObserveInterceptor()
            return grpc.intercept_channel(channel, interceptor)
        
        def patched_secure_channel(target, credentials, options=None, compression=None):
            """Patched secure_channel that adds our interceptor."""
            channel = original_secure_channel(target, credentials, options, compression)
            interceptor = LLMObserveInterceptor()
            return grpc.intercept_channel(channel, interceptor)
        
        grpc.insecure_channel = patched_insecure_channel
        grpc.secure_channel = patched_secure_channel
        
        _grpc_patched = True
        logger.info("[llmobserve] ✓ gRPC channels patched (ORCA cost tracking enabled)")
        logger.info("[llmobserve]   → Works with ANY gRPC API that supports ORCA standard")
        return True
        
    except Exception as e:
        logger.warning(f"[llmobserve] Failed to patch gRPC: {e}")
        return False


def is_grpc_patched() -> bool:
    """Check if gRPC is patched."""
    return _grpc_patched

