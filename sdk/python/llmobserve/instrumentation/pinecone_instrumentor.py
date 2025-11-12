"""
Pinecone SDK instrumentor with version guards and fail-open safety.
"""
import time
import uuid
import logging
import functools
from typing import Any, Optional

logger = logging.getLogger("llmobserve")

from llmobserve import config, context, buffer, pricing

# Supported Pinecone SDK versions
SUPPORTED_PINECONE_VERSIONS = {
    "7.0": "7.0.0",
    "7.1": "7.1.0",
    "7.2": "7.2.0",
    "6.0": "6.0.0",  # Legacy support
}


def check_pinecone_version() -> tuple[bool, Optional[str]]:
    """Check if Pinecone SDK version is supported."""
    try:
        import pinecone
        version = getattr(pinecone, "__version__", None)
        
        if version is None:
            logger.warning("[llmobserve] Pinecone SDK version unknown - proceeding with caution")
            return True, None
        
        major_version = version.split(".")[0]
        
        if major_version in SUPPORTED_PINECONE_VERSIONS:
            logger.debug(f"[llmobserve] Pinecone SDK version {version} is supported")
            return True, version
        
        # Check if it's a newer minor version
        try:
            major_int = int(major_version)
            if major_int >= 6:
                logger.warning(
                    f"[llmobserve] Pinecone SDK version {version} not explicitly tested. "
                    "Proceeding with caution."
                )
                return True, version
        except ValueError:
            pass
        
        logger.warning(
            f"[llmobserve] Pinecone SDK version {version} may be incompatible. "
            "Skipping instrumentation."
        )
        return False, version
        
    except ImportError:
        logger.debug("[llmobserve] Pinecone SDK not installed")
        return False, None


def _track_pinecone_call(
    operation: str,
    start_time: float,
    error: Optional[Exception] = None,
    extra_params: Optional[dict] = None
) -> None:
    """Track a Pinecone API call with fail-open safety."""
    if not config.is_enabled():
        return
    
    try:
        latency_ms = (time.time() - start_time) * 1000
        model = extra_params.get("model") if extra_params else None
        
        cost = pricing.compute_cost(
            provider="pinecone",
            model=model or operation,
            input_tokens=0,
            output_tokens=0
        )
        
        section_path = context.get_section_path()
        span_id = context.get_current_span_id() or str(uuid.uuid4())
        parent_span_id = context.get_parent_span_id()
        
        event = {
            "id": str(uuid.uuid4()),
            "run_id": context.get_run_id(),
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "section": context.get_current_section(),
            "section_path": section_path,
            "span_type": "vector_db",
            "provider": "pinecone",
            "endpoint": operation,
            "model": None,
            "tenant_id": config.get_tenant_id(),

            "customer_id": context.get_customer_id(),
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": cost,
            "latency_ms": latency_ms,
            "status": "error" if error else "ok",
            "is_streaming": False,
            "stream_cancelled": False,
            "event_metadata": extra_params if extra_params else {},
            "schema_version": "1.0",
        }
        
        buffer.add_event(event)
    except Exception as e:
        logger.debug(f"[llmobserve] Failed to track Pinecone call: {e}")


def _create_safe_wrapper(operation: str, original_method: Any) -> Any:
    """Create a fail-open wrapper for a Pinecone method."""
    @functools.wraps(original_method)
    def patched_method(self, *args, **kwargs):
        """Patched method with fail-open safety."""
        start_time = time.time()
        error = None
        
        try:
            # Call original method (critical path - never fail here)
            result = original_method(self, *args, **kwargs)
            return result
        except Exception as e:
            error = e
            raise
        finally:
            # Track call (fail-open)
            try:
                _track_pinecone_call(operation, start_time, error)
            except Exception as e:
                logger.debug(f"[llmobserve] Failed to track {operation}: {e}")
    
    return patched_method


def instrument_pinecone() -> bool:
    """Instrument Pinecone SDK with fail-open safety and version guards."""
    # Check version compatibility
    is_supported, version = check_pinecone_version()
    if not is_supported:
        logger.warning(f"[llmobserve] Skipping Pinecone instrumentation (version {version} not supported)")
        return False
    
    # Try to import Pinecone
    Index = None
    try:
        from pinecone.db_data.index import Index
    except ImportError:
        try:
            from pinecone import Index
        except ImportError:
            logger.debug("[llmobserve] Pinecone SDK not installed, skipping instrumentation")
            return False
    
    # Check if already instrumented
    if hasattr(Index, "_llmobserve_instrumented"):
        logger.debug("[llmobserve] Pinecone already instrumented, skipping")
        return True
    
    logger.info("[llmobserve] Instrumenting Pinecone client...")
    
    patched_count = 0
    failed_count = 0
    
    # Database operations
    operations = [
        ("query", "query"),
        ("upsert", "upsert"),
        ("delete", "delete"),
        ("update", "update"),
        ("fetch", "fetch"),
        ("list", "list"),
        ("describe_index_stats", "describe_index_stats"),
    ]
    
    for method_name, operation in operations:
        try:
            if not hasattr(Index, method_name):
                logger.debug(f"[llmobserve] Skipping Index.{method_name} (not found)")
                continue
            
            original_method = getattr(Index, method_name)
            
            if hasattr(original_method, "_llmobserve_instrumented"):
                logger.debug(f"[llmobserve] Index.{method_name} already instrumented")
                continue
            
            wrapped_method = _create_safe_wrapper(operation, original_method)
            
            try:
                setattr(Index, method_name, wrapped_method)
                wrapped_method._llmobserve_instrumented = True
                wrapped_method._llmobserve_original = original_method
                patched_count += 1
                logger.debug(f"[llmobserve] ✓ Instrumented Index.{method_name}")
            except Exception as e:
                logger.warning(f"[llmobserve] Failed to instrument Index.{method_name}: {e}")
                failed_count += 1
                
        except Exception as e:
            logger.warning(f"[llmobserve] Error instrumenting Index.{method_name}: {e}")
            failed_count += 1
    
    # Inference API
    try:
        from pinecone import inference
        
        inference_operations = [
            ("embed", "embed"),
            ("rerank", "rerank"),
        ]
        
        for method_name, operation in inference_operations:
            try:
                if not hasattr(inference, method_name):
                    continue
                
                original_method = getattr(inference, method_name)
                
                if hasattr(original_method, "_llmobserve_instrumented"):
                    continue
                
                @functools.wraps(original_method)
                def patched_inference(*args, **kwargs):
                    start_time = time.time()
                    error = None
                    model = kwargs.get("model", "unknown")
                    
                    try:
                        result = original_method(*args, **kwargs)
                        return result
                    except Exception as e:
                        error = e
                        raise
                    finally:
                        try:
                            _track_pinecone_call(operation, start_time, error, {"model": model})
                        except Exception:
                            pass
                
                setattr(inference, method_name, patched_inference)
                patched_inference._llmobserve_instrumented = True
                patched_inference._llmobserve_original = original_method
                patched_count += 1
                logger.debug(f"[llmobserve] ✓ Instrumented inference.{method_name}")
                
            except Exception as e:
                logger.warning(f"[llmobserve] Failed to instrument inference.{method_name}: {e}")
                failed_count += 1
                
    except (ImportError, AttributeError):
        logger.debug("[llmobserve] Inference API not available")
    
    # Mark as instrumented
    if patched_count > 0:
        try:
            setattr(Index, "_llmobserve_instrumented", True)
            logger.info(
                f"[llmobserve] Pinecone SDK instrumented successfully "
                f"({patched_count} endpoints, {failed_count} failed)"
            )
            return True
        except Exception:
            pass
    
    if failed_count > 0:
        logger.warning(
            f"[llmobserve] Pinecone instrumentation partially failed "
            f"({patched_count} succeeded, {failed_count} failed)"
        )
        return patched_count > 0
    
    logger.warning("[llmobserve] Failed to instrument any Pinecone endpoints")
    return False

