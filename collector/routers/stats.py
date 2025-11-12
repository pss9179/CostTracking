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
    session: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """
    Get costs aggregated by provider for the last N hours.
    
    For MVP: Returns all data if no user_id provided.
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
    
    # Filter by user_id if provided
    if user_id:
        statement = statement.where(TraceEvent.user_id == user_id)
    
    statement = statement.group_by(TraceEvent.provider).order_by(func.sum(TraceEvent.cost_usd).desc())
    
    results = session.exec(statement).all()
    
    # Calculate total for percentages
    total_cost = sum(r.total_cost for r in results)
    
    providers = [
        {
            "provider": r.provider,
            "total_cost": round(r.total_cost, 6),
            "call_count": r.call_count,
            "percentage": round((r.total_cost / total_cost * 100) if total_cost > 0 else 0, 2)
        }
        for r in results
    ]
    
    return providers

