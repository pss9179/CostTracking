"""API routes for cost tracking dashboard."""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Query
from sqlmodel import select, func

from llmobserve.models import CostEvent

# Import get_session here so it can be patched in tests
# Don't import at module level - import inside function so patching works
def _get_session():
    """Get database session - can be patched in tests."""
    from llmobserve.db import get_session
    return get_session()

router = APIRouter()


@router.get("/costs")
async def get_costs(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """
    Get cost events with optional filtering.

    Returns:
        List of cost events
    """
    session = _get_session()
    try:
        statement = select(CostEvent)
        
        # Apply filters
        if tenant_id:
            statement = statement.where(CostEvent.tenant_id == tenant_id)
        if workflow_id:
            statement = statement.where(CostEvent.workflow_id == workflow_id)
        if provider:
            statement = statement.where(CostEvent.provider == provider)
        
        # Date filtering
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                statement = statement.where(CostEvent.timestamp >= start_dt)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                # Add one day to include the full end date
                end_dt = end_dt + timedelta(days=1)
                statement = statement.where(CostEvent.timestamp < end_dt)
            except ValueError:
                pass
        
        # Order and limit
        statement = statement.order_by(CostEvent.timestamp.desc()).limit(limit).offset(offset)
        
        events = list(session.exec(statement).all())
        
        return {
            "events": [
                {
                    "id": e.id,
                    "tenant_id": e.tenant_id,
                    "workflow_id": e.workflow_id,
                    "provider": e.provider,
                    "model": e.model,
                    "cost_usd": e.cost_usd,
                    "duration_ms": e.duration_ms,
                    "timestamp": e.timestamp.isoformat(),
                    "prompt_tokens": e.prompt_tokens,
                    "completion_tokens": e.completion_tokens,
                    "total_tokens": e.total_tokens,
                    "operation": e.operation,
                    "trace_id": e.trace_id,
                    "span_id": e.span_id,
                }
                for e in events
            ],
            "total": len(events),
        }
    finally:
        session.close()


@router.get("/tenants")
async def get_tenants():
    """
    Get list of tenants with cost totals.

    Returns:
        List of tenants with aggregated costs
    """
    session = _get_session()
    try:
        # Group by tenant_id and aggregate
        statement = select(
            CostEvent.tenant_id,
            func.sum(CostEvent.cost_usd).label("total_cost"),
            func.sum(CostEvent.total_tokens).label("total_tokens"),
            func.count(CostEvent.id).label("total_requests"),
        ).group_by(CostEvent.tenant_id)
        
        results = session.exec(statement).all()
        
        tenants = []
        for row in results:
            tenants.append({
                "tenant_id": row[0],
                "total_cost_usd": float(row[1] or 0),
                "total_tokens": int(row[2] or 0),
                "total_requests": int(row[3] or 0),
            })
        
        return {"tenants": tenants}
    finally:
        session.close()


@router.get("/workflows")
async def get_workflows(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
):
    """
    Get list of workflows with cost totals.

    Returns:
        List of workflows with aggregated costs
    """
    session = _get_session()
    try:
        statement = select(
            CostEvent.workflow_id,
            CostEvent.tenant_id,
            func.sum(CostEvent.cost_usd).label("total_cost"),
            func.sum(CostEvent.total_tokens).label("total_tokens"),
            func.count(CostEvent.id).label("total_requests"),
        ).where(CostEvent.workflow_id.isnot(None))
        
        if tenant_id:
            statement = statement.where(CostEvent.tenant_id == tenant_id)
        
        statement = statement.group_by(CostEvent.workflow_id, CostEvent.tenant_id)
        
        results = session.exec(statement).all()
        
        workflows = []
        for row in results:
            workflows.append({
                "workflow_id": row[0],
                "tenant_id": row[1],
                "total_cost_usd": float(row[2] or 0),
                "total_tokens": int(row[3] or 0),
                "total_requests": int(row[4] or 0),
            })
        
        return {"workflows": workflows}
    finally:
        session.close()


@router.get("/metrics")
async def get_metrics(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    days: int = Query(7, ge=1, le=365, description="Number of days to aggregate"),
):
    """
    Get aggregated metrics for dashboard.

    Returns:
        Aggregated metrics including cost by provider, cost over time, etc.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    session = _get_session()
    try:
        # Base query
        statement = select(CostEvent).where(CostEvent.timestamp >= cutoff_date)
        
        if tenant_id:
            statement = statement.where(CostEvent.tenant_id == tenant_id)
        
        events = list(session.exec(statement).all())
        
        # Calculate totals
        total_cost = sum(e.cost_usd for e in events)
        total_tokens = sum(e.total_tokens or 0 for e in events)
        total_requests = len(events)
        
        # Cost by provider
        cost_by_provider = {}
        for e in events:
            cost_by_provider[e.provider] = cost_by_provider.get(e.provider, 0.0) + e.cost_usd
        
        # Cost by model
        cost_by_model = {}
        for e in events:
            if e.model:
                cost_by_model[e.model] = cost_by_model.get(e.model, 0.0) + e.cost_usd
        
        # Cost over time (daily buckets)
        cost_over_time = {}
        for e in events:
            date_key = e.timestamp.strftime("%Y-%m-%d")
            cost_over_time[date_key] = cost_over_time.get(date_key, 0.0) + e.cost_usd
        
        return {
            "total_cost_usd": total_cost,
            "total_tokens": total_tokens,
            "total_requests": total_requests,
            "cost_by_provider": cost_by_provider,
            "cost_by_model": cost_by_model,
            "cost_over_time": cost_over_time,
        }
    finally:
        session.close()

