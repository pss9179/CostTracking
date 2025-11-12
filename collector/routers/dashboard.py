"""
User-scoped dashboard endpoints.

These endpoints require authentication and only return data for the authenticated user.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func, and_
from uuid import UUID
from db import get_session
from models import TraceEvent
from auth import get_current_user_id

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/customers", response_model=List[Dict[str, Any]])
async def get_my_customers(
    *,
    user_id: Optional[UUID] = None,  # Made optional for MVP
    session: Session = Depends(get_session),
    days: int = Query(7, ge=1, le=90, description="Number of days to look back")
) -> List[Dict[str, Any]]:
    """
    Get customer breakdown.
    
    For MVP: Returns all customer data if no user_id provided.
    Returns cost, calls, and latency per customer.
    """
    time_ago = datetime.utcnow() - timedelta(days=days)
    
    statement = select(
        TraceEvent.customer_id,
        func.sum(TraceEvent.cost_usd).label("total_cost"),
        func.count(TraceEvent.id).label("call_count"),
        func.avg(TraceEvent.latency_ms).label("avg_latency")
    ).where(and_(
        TraceEvent.customer_id.isnot(None),
        TraceEvent.created_at >= time_ago
    ))
    
    # Filter by user_id if provided
    if user_id:
        statement = statement.where(TraceEvent.user_id == user_id)
    
    statement = statement.group_by(TraceEvent.customer_id).order_by(func.sum(TraceEvent.cost_usd).desc())
    
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


@router.get("/stats", response_model=Dict[str, Any])
async def get_my_stats(
    *,
    user_id: UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session),
    days: int = Query(7, ge=1, le=90, description="Number of days to look back")
) -> Dict[str, Any]:
    """
    Get overall stats for authenticated user.
    
    Requires Authorization: Bearer <api_key> header.
    """
    time_ago = datetime.utcnow() - timedelta(days=days)
    
    # Total cost and calls
    statement = (
        select(
            func.sum(TraceEvent.cost_usd).label("total_cost"),
            func.count(TraceEvent.id).label("call_count"),
            func.avg(TraceEvent.latency_ms).label("avg_latency")
        )
        .where(and_(
            TraceEvent.user_id == str(user_id),
            TraceEvent.created_at >= time_ago
        ))
    )
    
    result = session.exec(statement).first()
    
    # Count unique customers
    customer_count_stmt = (
        select(func.count(func.distinct(TraceEvent.customer_id)))
        .where(and_(
            TraceEvent.user_id == str(user_id),
            TraceEvent.customer_id.isnot(None),
            TraceEvent.created_at >= time_ago
        ))
    )
    customer_count = session.exec(customer_count_stmt).first() or 0
    
    # Top customer
    top_customer_stmt = (
        select(
            TraceEvent.customer_id,
            func.sum(TraceEvent.cost_usd).label("cost")
        )
        .where(and_(
            TraceEvent.user_id == str(user_id),
            TraceEvent.customer_id.isnot(None),
            TraceEvent.created_at >= time_ago
        ))
        .group_by(TraceEvent.customer_id)
        .order_by(func.sum(TraceEvent.cost_usd).desc())
        .limit(1)
    )
    top_customer = session.exec(top_customer_stmt).first()
    
    return {
        "total_cost": round(result.total_cost, 6) if result.total_cost else 0.0,
        "call_count": result.call_count if result.call_count else 0,
        "avg_latency_ms": round(result.avg_latency, 2) if result.avg_latency else 0.0,
        "customer_count": customer_count,
        "top_customer": {
            "customer_id": top_customer.customer_id if top_customer else None,
            "cost": round(top_customer.cost, 6) if top_customer else 0.0
        },
        "period_days": days
    }


@router.get("/customers/{customer_id}/detail", response_model=Dict[str, Any])
async def get_customer_detail(
    *,
    customer_id: str,
    user_id: UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session),
    days: int = Query(7, ge=1, le=90)
) -> Dict[str, Any]:
    """
    Get detailed breakdown for a specific customer within authenticated user's data.
    
    Requires Authorization: Bearer <api_key> header.
    """
    time_ago = datetime.utcnow() - timedelta(days=days)
    
    # Overall stats for this customer
    stats_stmt = (
        select(
            func.sum(TraceEvent.cost_usd).label("total_cost"),
            func.count(TraceEvent.id).label("call_count"),
            func.avg(TraceEvent.latency_ms).label("avg_latency")
        )
        .where(and_(
            TraceEvent.user_id == str(user_id),
            TraceEvent.customer_id == customer_id,
            TraceEvent.created_at >= time_ago
        ))
    )
    stats = session.exec(stats_stmt).first()
    
    # Breakdown by provider
    provider_stmt = (
        select(
            TraceEvent.provider,
            func.sum(TraceEvent.cost_usd).label("cost"),
            func.count(TraceEvent.id).label("calls")
        )
        .where(and_(
            TraceEvent.user_id == str(user_id),
            TraceEvent.customer_id == customer_id,
            TraceEvent.created_at >= time_ago
        ))
        .group_by(TraceEvent.provider)
        .order_by(func.sum(TraceEvent.cost_usd).desc())
    )
    providers = session.exec(provider_stmt).all()
    
    # Breakdown by model
    model_stmt = (
        select(
            TraceEvent.model,
            func.sum(TraceEvent.cost_usd).label("cost"),
            func.count(TraceEvent.id).label("calls")
        )
        .where(and_(
            TraceEvent.user_id == str(user_id),
            TraceEvent.customer_id == customer_id,
            TraceEvent.model.isnot(None),
            TraceEvent.created_at >= time_ago
        ))
        .group_by(TraceEvent.model)
        .order_by(func.sum(TraceEvent.cost_usd).desc())
        .limit(10)
    )
    models = session.exec(model_stmt).all()
    
    return {
        "customer_id": customer_id,
        "total_cost": round(stats.total_cost, 6) if stats.total_cost else 0.0,
        "call_count": stats.call_count if stats.call_count else 0,
        "avg_latency_ms": round(stats.avg_latency, 2) if stats.avg_latency else 0.0,
        "by_provider": [
            {
                "provider": p.provider,
                "cost": round(p.cost, 6),
                "calls": p.calls
            }
            for p in providers
        ],
        "top_models": [
            {
                "model": m.model,
                "cost": round(m.cost, 6),
                "calls": m.calls
            }
            for m in models
        ],
        "period_days": days
    }

