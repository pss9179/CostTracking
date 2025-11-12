"""
Monkey-patch for Pinecone client to auto-track vector DB operations.

Patches:
  • Index.query() - Read units
  • Index.upsert() - Write units
  • Index.delete() - Write units
  • Index.update() - Write units
  • Index.fetch() - Read units
 • Index.list() - Read units
  • Index.describe_index_stats() - Read units
  • inference.embed() - Embedding API
  • inference.rerank() - Reranking API
"""
import time
import uuid
import logging
from typing import Any, Optional
from llmobserve import config, context, buffer, pricing
from llmobserve.robustness import check_pinecone_version

logger = logging.getLogger("llmobserve")


def _track_pinecone_call(
    operation: str,
    start_time: float,
    error: Optional[Exception] = None,
    extra_params: Optional[dict] = None
) -> None:
    """
    Track a Pinecone API call.
    
    Args:
        operation: Operation name (e.g., "query", "upsert", "delete")
        start_time: Start timestamp
        error: Optional exception if call failed
        extra_params: Additional parameters (e.g., model for inference)
    """
    if not config.is_enabled():
        return
    
    latency_ms = (time.time() - start_time) * 1000
    
    # Get model if provided (for inference API)
    model = extra_params.get("model") if extra_params else None
    
    # Pinecone uses per_million or per_1k_requests pricing
    cost = pricing.compute_cost(
        provider="pinecone",
        model=model or operation,
        input_tokens=0,
        output_tokens=0
    )
    
    # Get hierarchical section information
    section_path = context.get_section_path()
    span_id = context.get_current_span_id() or str(uuid.uuid4())
    parent_span_id = context.get_parent_span_id()
    
    # Create event with hierarchical span tracking
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "section": context.get_current_section(),  # Backward compatibility (last segment only)
        "section_path": section_path,  # NEW: Full hierarchical path
        "span_type": "vector_db",
        "provider": "pinecone",
        "endpoint": operation,
        "model": None,
        "tenant_id": config.get_tenant_id(),

        "customer_id": config.get_customer_id(),
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": cost,
        "latency_ms": latency_ms,
        "status": "error" if error else "ok",
        "event_metadata": None
    }
    
    buffer.add_event(event)


def patch_pinecone() -> None:
    """
    Apply monkey-patches to Pinecone client.
    
    Patches all billable operations:
    - Database: query, upsert, delete, update, fetch, list, describe_index_stats
    - Inference: embed, rerank
    
    Compatible with Pinecone SDK v7.x (new API structure).
    """
    try:
        # Try new Pinecone SDK v7.x structure
        from pinecone.db_data.index import Index
    except ImportError:
        try:
            # Fallback for older SDK versions
            from pinecone import Index
        except ImportError:
            logger.debug("[llmobserve] Pinecone SDK not installed, skipping patches")
            return
    
    # Version compatibility check
    version_status = check_pinecone_version()
    if version_status:
        logger.debug(f"[llmobserve] Pinecone SDK version detected")
    
    logger.info("[llmobserve] Patching Pinecone client...")
    
    # ============================================================================
    # DATABASE OPERATIONS (Index methods)
    # ============================================================================
    
    # Patch query (read units)
    if hasattr(Index, "query"):
        original_query = Index.query
        
        def patched_query(self, *args, **kwargs):
            """Patched Index.query (read units)."""
            start_time = time.time()
            error = None
            try:
                result = original_query(self, *args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                _track_pinecone_call("query", start_time, error)
        
        Index.query = patched_query
        logger.info("[llmobserve] ✓ Patched Index.query")
    
    # Patch upsert (write units)
    if hasattr(Index, "upsert"):
        original_upsert = Index.upsert
        
        def patched_upsert(self, *args, **kwargs):
            """Patched Index.upsert (write units)."""
            start_time = time.time()
            error = None
            try:
                result = original_upsert(self, *args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                _track_pinecone_call("upsert", start_time, error)
        
        Index.upsert = patched_upsert
        logger.info("[llmobserve] ✓ Patched Index.upsert")
    
    # Patch delete (write units)
    if hasattr(Index, "delete"):
        original_delete = Index.delete
        
        def patched_delete(self, *args, **kwargs):
            """Patched Index.delete (write units)."""
            start_time = time.time()
            error = None
            try:
                result = original_delete(self, *args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                _track_pinecone_call("delete", start_time, error)
        
        Index.delete = patched_delete
        logger.info("[llmobserve] ✓ Patched Index.delete")
    
    # Patch update (write units)
    if hasattr(Index, "update"):
        original_update = Index.update
        
        def patched_update(self, *args, **kwargs):
            """Patched Index.update (write units)."""
            start_time = time.time()
            error = None
            try:
                result = original_update(self, *args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                _track_pinecone_call("update", start_time, error)
        
        Index.update = patched_update
        logger.info("[llmobserve] ✓ Patched Index.update")
    
    # Patch fetch (read units)
    if hasattr(Index, "fetch"):
        original_fetch = Index.fetch
        
        def patched_fetch(self, *args, **kwargs):
            """Patched Index.fetch (read units)."""
            start_time = time.time()
            error = None
            try:
                result = original_fetch(self, *args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                _track_pinecone_call("fetch", start_time, error)
        
        Index.fetch = patched_fetch
        logger.info("[llmobserve] ✓ Patched Index.fetch")
    
    # Patch list (read units)
    if hasattr(Index, "list"):
        original_list = Index.list
        
        def patched_list(self, *args, **kwargs):
            """Patched Index.list (read units)."""
            start_time = time.time()
            error = None
            try:
                result = original_list(self, *args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                _track_pinecone_call("list", start_time, error)
        
        Index.list = patched_list
        logger.info("[llmobserve] ✓ Patched Index.list")
    
    # Patch describe_index_stats (read units)
    if hasattr(Index, "describe_index_stats"):
        original_describe = Index.describe_index_stats
        
        def patched_describe(self, *args, **kwargs):
            """Patched Index.describe_index_stats (read units)."""
            start_time = time.time()
            error = None
            try:
                result = original_describe(self, *args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                _track_pinecone_call("describe_index_stats", start_time, error)
        
        Index.describe_index_stats = patched_describe
        logger.info("[llmobserve] ✓ Patched Index.describe_index_stats")
    
    # ============================================================================
    # INFERENCE API
    # ============================================================================
    
    # Patch inference.embed (embedding models)
    try:
        from pinecone import inference
        
        if hasattr(inference, "embed"):
            original_embed = inference.embed
            
            def patched_embed(*args, **kwargs):
                """Patched inference.embed (embedding API)."""
                start_time = time.time()
                error = None
                model = kwargs.get("model", "unknown")
                try:
                    result = original_embed(*args, **kwargs)
                    return result
                except Exception as e:
                    error = e
                    raise
                finally:
                    _track_pinecone_call("embed", start_time, error, {"model": model})
            
            inference.embed = patched_embed
            logger.info("[llmobserve] ✓ Patched inference.embed")
    except (ImportError, AttributeError):
        pass
    
    # Patch inference.rerank (reranking models)
    try:
        from pinecone import inference
        
        if hasattr(inference, "rerank"):
            original_rerank = inference.rerank
            
            def patched_rerank(*args, **kwargs):
                """Patched inference.rerank (reranking API)."""
                start_time = time.time()
                error = None
                model = kwargs.get("model", "unknown")
                try:
                    result = original_rerank(*args, **kwargs)
                    return result
                except Exception as e:
                    error = e
                    raise
                finally:
                    _track_pinecone_call("rerank", start_time, error, {"model": model})
            
            inference.rerank = patched_rerank
            logger.info("[llmobserve] ✓ Patched inference.rerank")
    except (ImportError, AttributeError):
        pass

