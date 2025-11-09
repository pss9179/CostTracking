"""Endpoints for spans, traces, and metrics."""

from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from llmobserve.storage.models import SpanSummary, Trace
from llmobserve.storage.repo import SpanRepository

router = APIRouter()
repo = SpanRepository()


class UpdateWorkflowNameRequest(BaseModel):
    """Request model for updating workflow name."""
    workflow_name: str


class UpdateSpanNameRequest(BaseModel):
    """Request model for updating span name."""
    span_name: str


@router.get("/spans", response_model=List[dict])
async def get_spans(
    trace_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id"),
):
    """Get spans with optional filtering."""
    tenant_id = x_tenant_id or "default"
    spans = repo.get_spans(tenant_id=tenant_id, trace_id=trace_id, limit=limit, offset=offset)
    return [span.dict() for span in spans]


@router.get("/traces/{trace_id}", response_model=dict)
async def get_trace(
    trace_id: str,
    x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id"),
):
    """Get trace by ID with all spans."""
    tenant_id = x_tenant_id or "default"
    trace = repo.get_trace(trace_id, tenant_id)
    if not trace:
        # Try to aggregate from spans
        spans = repo.get_trace_spans(trace_id, tenant_id)
        if not spans:
            raise HTTPException(status_code=404, detail="Trace not found")
        trace = repo.aggregate_trace(trace_id, tenant_id)

    spans = repo.get_trace_spans(trace_id, tenant_id)
    return {
        "trace": trace.dict(),
        "spans": [span.dict() for span in spans],
    }


@router.get("/traces", response_model=List[dict])
async def get_traces(
    limit: int = 100,
    offset: int = 0,
    x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id"),
):
    """Get traces with optional tenant filtering."""
    tenant_id = x_tenant_id or "default"
    traces = repo.get_traces(tenant_id=tenant_id, limit=limit, offset=offset)
    return [trace.dict() for trace in traces]


@router.get("/metrics", response_model=dict)
async def get_metrics(
    days: int = 7,
    x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id"),
):
    """Get aggregated metrics for dashboard."""
    tenant_id = x_tenant_id or "default"
    metrics = repo.get_metrics(tenant_id=tenant_id, days=days)
    return metrics


@router.get("/workflows", response_model=List[dict])
async def get_workflows(
    limit: int = 100,
    x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id"),
):
    """Get workflows with aggregated stats."""
    tenant_id = x_tenant_id or "default"
    workflows = repo.get_workflows(tenant_id=tenant_id, limit=limit)
    return workflows


@router.patch("/spans/{span_id}/name")
async def update_span_name(
    span_id: str,
    request: UpdateSpanNameRequest,
    x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id"),
):
    """Update span name."""
    tenant_id = x_tenant_id or "default"
    span = repo.update_span_name(span_id, request.span_name, tenant_id)
    return {"status": "success", "span": span.dict()}


@router.patch("/traces/{trace_id}/workflow-name")
async def update_workflow_name(
    trace_id: str,
    request: UpdateWorkflowNameRequest,
    x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id"),
):
    """Update workflow name for a trace."""
    tenant_id = x_tenant_id or "default"
    try:
        trace = repo.update_workflow_name(trace_id, request.workflow_name, tenant_id)
        return {"status": "success", "trace": trace.dict()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

