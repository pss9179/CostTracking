"""
Stats router - provides aggregated statistics.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func, and_
from models import TraceEvent
from db import get_session
from auth import get_current_user_id

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/by-provider")
def get_costs_by_provider(
    hours: int = 24,
    user_id: Optional[UUID] = None,  # Made optional for MVP
    tenant_id: Optional[str] = Query(None, description="Tenant identifier for multi-tenant isolation"),
    session: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """
    Get costs aggregated by provider for the last N hours.
    
    For MVP: Returns all data if no user_id or tenant_id provided.
    Returns breakdown with total cost, call count, and percentage.
    """
    # Calculate time window
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Get provider aggregations
    statement = select(
        TraceEvent.provider,
        func.sum(TraceEvent.cost_usd).label("total_cost"),
        func.count(TraceEvent.id).label("call_count")
    ).where(TraceEvent.created_at >= cutoff)
    
    # Filter by tenant_id (preferred) or user_id
    if tenant_id:
        statement = statement.where(TraceEvent.tenant_id == tenant_id)
    elif user_id:
        statement = statement.where(TraceEvent.user_id == user_id)
    
    # Exclude "internal" provider from stats
    statement = statement.where(TraceEvent.provider != "internal")
    
    statement = statement.group_by(TraceEvent.provider).order_by(func.sum(TraceEvent.cost_usd).desc())
    
    results = session.exec(statement).all()
    
    # Calculate total for percentages (only non-internal providers)
    total_cost = sum(r.total_cost for r in results)
    
    providers = [
        {
            "provider": r.provider,
            "total_cost": r.total_cost,  # Don't round - let frontend format it
            "call_count": r.call_count,
            "percentage": round((r.total_cost / total_cost * 100) if total_cost > 0 else 0, 2)
        }
        for r in results
    ]
    
    return providers


@router.get("/by-customer")
def get_costs_by_customer(
    hours: int = Query(720, description="Time window in hours (default 30 days)"),
    user_id: Optional[UUID] = None,
    tenant_id: Optional[str] = Query(None, description="Tenant identifier for multi-tenant isolation"),
    session: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """
    Get costs aggregated by customer_id for the last N hours.
    
    Returns breakdown with total cost, call count, and average latency.
    """
    # Calculate time window
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Get customer aggregations
    statement = select(
        TraceEvent.customer_id,
        func.sum(TraceEvent.cost_usd).label("total_cost"),
        func.count(TraceEvent.id).label("call_count"),
        func.avg(TraceEvent.latency_ms).label("avg_latency_ms")
    ).where(TraceEvent.created_at >= cutoff)
    
    # Filter by tenant_id (preferred) or user_id
    if tenant_id:
        statement = statement.where(TraceEvent.tenant_id == tenant_id)
    elif user_id:
        statement = statement.where(TraceEvent.user_id == user_id)
    
    # Exclude "internal" provider and null customer_ids
    statement = statement.where(
        and_(
            TraceEvent.provider != "internal",
            TraceEvent.customer_id.isnot(None)
        )
    )
    
    statement = statement.group_by(TraceEvent.customer_id).order_by(func.sum(TraceEvent.cost_usd).desc())
    
    results = session.exec(statement).all()
    
    customers = [
        {
            "customer_id": r.customer_id,
            "total_cost": r.total_cost,
            "call_count": r.call_count,
            "avg_latency_ms": round(r.avg_latency_ms or 0, 2)
        }
        for r in results
    ]
    
    return customers

