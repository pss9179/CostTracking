"""
gRPC Interceptor for LLMObserve Context Propagation

Patches grpcio to inject context metadata into all gRPC calls.
"""

import logging
import uuid
from typing import Any, Callable, Optional

from llmobserve import config, context

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
            """Interceptor that injects LLMObserve context into gRPC metadata."""
            
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
            
            def intercept_unary_unary(self, continuation, client_call_details, request):
                """Intercept unary-unary RPC calls."""
                new_details = self._inject_metadata(client_call_details)
                return continuation(new_details, request)
            
            def intercept_unary_stream(self, continuation, client_call_details, request):
                """Intercept unary-stream RPC calls."""
                new_details = self._inject_metadata(client_call_details)
                return continuation(new_details, request)
        
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
        logger.info("[llmobserve] ✓ gRPC channels patched (context headers will be injected)")
        return True
        
    except Exception as e:
        logger.warning(f"[llmobserve] Failed to patch gRPC: {e}")
        return False


def is_grpc_patched() -> bool:
    """Check if gRPC is patched."""
    return _grpc_patched

