"""
Tenants router - provides per-tenant statistics and management.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func, and_
from db import get_session
from models import TraceEvent

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("/stats", response_model=List[Dict[str, Any]])
def get_tenant_stats(
    *,
    session: Session = Depends(get_session),
    days: int = Query(7, ge=1, le=90, description="Number of days to look back")
) -> List[Dict[str, Any]]:
    """
    Get aggregated stats per tenant for the last N days.
    
    Returns total cost, call count, and average latency per tenant.
    """
    time_ago = datetime.utcnow() - timedelta(days=days)
    
    statement = (
        select(
            TraceEvent.tenant_id,
            func.sum(TraceEvent.cost_usd).label("total_cost"),
            func.count(TraceEvent.id).label("call_count"),
            func.avg(TraceEvent.latency_ms).label("avg_latency")
        )
        .where(and_(
            TraceEvent.created_at >= time_ago,
            TraceEvent.tenant_id.isnot(None)
        ))
        .group_by(TraceEvent.tenant_id)
        .order_by(func.sum(TraceEvent.cost_usd).desc())
    )
    
    results = session.exec(statement).all()
    
    return [
        {
            "tenant_id": r.tenant_id,
            "total_cost": round(r.total_cost, 6),
            "call_count": r.call_count,
            "avg_latency_ms": round(r.avg_latency, 2) if r.avg_latency else 0.0
        }
        for r in results
    ]


@router.get("/list")
def get_tenant_list(
    *,
    session: Session = Depends(get_session)
) -> List[str]:
    """
    Get list of all tenant IDs that have events.
    
    Returns a sorted list of unique tenant IDs.
    """
    statement = (
        select(TraceEvent.tenant_id)
        .where(TraceEvent.tenant_id.isnot(None))
        .distinct()
    )
    results = session.exec(statement).all()
    return sorted([r for r in results if r])


@router.get("/{tenant_id}/customers", response_model=List[Dict[str, Any]])
def get_customer_stats_by_tenant(
    *,
    tenant_id: str,
    session: Session = Depends(get_session),
    days: int = Query(7, ge=1, le=90, description="Number of days to look back")
) -> List[Dict[str, Any]]:
    """
    Get aggregated stats per customer for a specific tenant.
    
    Returns cost, call count, and latency breakdown by customer_id within the tenant.
    """
    time_ago = datetime.utcnow() - timedelta(days=days)
    
    statement = (
        select(
            TraceEvent.customer_id,
            func.sum(TraceEvent.cost_usd).label("total_cost"),
            func.count(TraceEvent.id).label("call_count"),
            func.avg(TraceEvent.latency_ms).label("avg_latency")
        )
        .where(and_(
            TraceEvent.tenant_id == tenant_id,
            TraceEvent.customer_id.isnot(None),
            TraceEvent.created_at >= time_ago
        ))
        .group_by(TraceEvent.customer_id)
        .order_by(func.sum(TraceEvent.cost_usd).desc())
    )
    
    results = session.exec(statement).all()
    
    return [
        {
            "customer_id": r.customer_id,
            "total_cost": round(r.total_cost, 6),
            "call_count": r.call_count,
            "avg_latency_ms": round(r.avg_latency, 2) if r.avg_latency else 0.0
        }
        for r in results
    ]

