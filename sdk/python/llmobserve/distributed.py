"""
Distributed tracing support for background workers and multi-process systems.

Provides context export/import for maintaining trace continuity across
Celery tasks, RQ jobs, and other background worker systems.
"""
from typing import Dict, Any
from llmobserve import context


def export_context() -> Dict[str, Any]:
    """
    Export current tracing context for serialization.
    
    Use before enqueuing a background task to maintain trace continuity.
    
    Returns:
        Dictionary with trace_id, span_id, run_id, customer_id, and section_stack
    
    Usage:
        # In producer (web request handler)
        ctx = export_context()
        celery_task.apply_async(args=[ctx, other_args])
    """
    stack = context._get_section_stack()
    
    return {
        "trace_id": context.get_trace_id(),
        "span_id": stack[-1]["span_id"] if stack else None,
        "run_id": context.get_run_id(),
        "customer_id": context.get_customer_id(),
        "tenant_id": context.get_tenant_id(),
        "section_stack": stack,
    }


def import_context(ctx: Dict[str, Any]) -> None:
    """
    Import tracing context from serialized data.
    
    Use at the start of a background task to restore trace continuity.
    Creates a new child span under the parent span from the producer.
    
    Args:
        ctx: Dictionary from export_context()
    
    Usage:
        # In worker (Celery task)
        @celery.task
        def my_task(ctx, other_args):
            import_context(ctx)
            # All spans now part of original trace
            with section("tool:background_processor"):
                process_data(other_args)
    """
    if not ctx:
        return
    
    # Restore trace_id (maintains trace continuity across processes)
    if "trace_id" in ctx and ctx["trace_id"]:
        context.set_trace_id(ctx["trace_id"])
    
    # Restore run_id
    if "run_id" in ctx and ctx["run_id"]:
        context.set_run_id(ctx["run_id"])
    
    # Restore customer_id
    if "customer_id" in ctx:
        context.set_customer_id(ctx.get("customer_id"))
    
    # Restore tenant_id
    if "tenant_id" in ctx:
        context.set_tenant_id(ctx.get("tenant_id"))
    
    # Optionally restore section_stack (or start fresh with parent span context)
    # NOTE: We don't restore the full stack to avoid long-lived spans across process boundaries.
    # Instead, we just maintain trace_id and run_id for grouping.
    # Workers should create their own agent/tool spans.
    
    # If you want to restore the parent span relationship:
    # if "section_stack" in ctx and ctx["section_stack"]:
    #     context._section_stack_var.set(ctx["section_stack"])

