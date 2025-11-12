"""
Spending Caps API Router

Endpoints for managing spending caps and viewing alerts.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func, and_, or_

from models import (
    SpendingCap,
    Alert,
    CapCreate,
    CapUpdate,
    CapResponse,
    AlertResponse,
    TraceEvent,
    User,
)
from db import get_session
from clerk_auth import get_current_clerk_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/caps", tags=["caps"])


def get_period_dates(period: str) -> tuple[datetime, datetime]:
    """Calculate start and end dates for a period."""
    now = datetime.utcnow()
    
    if period == "daily":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    elif period == "weekly":
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)
    elif period == "monthly":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Next month
        if now.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
    else:
        raise ValueError(f"Invalid period: {period}")
    
    return start, end


def calculate_current_spend(
    session: Session,
    user_id: UUID,
    cap_type: str,
    target_name: Optional[str],
    period_start: datetime,
    period_end: datetime,
) -> float:
    """Calculate current spend for a cap."""
    query = select(func.sum(TraceEvent.cost_usd)).where(
        and_(
            TraceEvent.user_id == user_id,
            TraceEvent.created_at >= period_start,
            TraceEvent.created_at < period_end,
        )
    )
    
    # Add scope filters
    if cap_type == "provider" and target_name:
        query = query.where(TraceEvent.provider == target_name)
    elif cap_type == "model" and target_name:
        query = query.where(TraceEvent.model_id == target_name)
    elif cap_type == "agent" and target_name:
        query = query.where(TraceEvent.agent == target_name)
    elif cap_type == "customer" and target_name:
        query = query.where(TraceEvent.customer_id == target_name)
    # 'global' doesn't add any filter
    
    result = session.exec(query).first()
    return float(result or 0.0)


@router.post("/", response_model=CapResponse)
async def create_cap(
    cap_data: CapCreate,
    user: User = Depends(get_current_clerk_user),
    session: Session = Depends(get_session),
):
    """Create a new spending cap."""
    # Validate period
    if cap_data.period not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Period must be 'daily', 'weekly', or 'monthly'")
    
    # Validate cap_type
    if cap_data.cap_type not in ["global", "provider", "model", "agent", "customer"]:
        raise HTTPException(status_code=400, detail="Invalid cap_type")
    
    # Validate target_name for non-global caps
    if cap_data.cap_type != "global" and not cap_data.target_name:
        raise HTTPException(status_code=400, detail=f"target_name required for cap_type '{cap_data.cap_type}'")
    
    cap = SpendingCap(
        user_id=user.id,
        cap_type=cap_data.cap_type,
        target_name=cap_data.target_name,
        limit_amount=cap_data.limit_amount,
        period=cap_data.period,
        alert_threshold=cap_data.alert_threshold,
        alert_email=cap_data.alert_email,
    )
    
    session.add(cap)
    session.commit()
    session.refresh(cap)
    
    # Calculate current spend
    period_start, period_end = get_period_dates(cap.period)
    current_spend = calculate_current_spend(
        session, user.id, cap.cap_type, cap.target_name, period_start, period_end
    )
    
    logger.info(f"Created spending cap: {cap.cap_type} ${cap.limit_amount}/{cap.period} for user {user.email}")
    
    return CapResponse(
        id=cap.id,
        cap_type=cap.cap_type,
        target_name=cap.target_name,
        limit_amount=cap.limit_amount,
        period=cap.period,
        alert_threshold=cap.alert_threshold,
        alert_email=cap.alert_email,
        enabled=cap.enabled,
        current_spend=current_spend,
        percentage_used=(current_spend / cap.limit_amount * 100) if cap.limit_amount > 0 else 0,
        created_at=cap.created_at,
        updated_at=cap.updated_at,
    )


@router.get("/", response_model=List[CapResponse])
async def list_caps(
    user: User = Depends(get_current_clerk_user),
    session: Session = Depends(get_session),
):
    """List all spending caps for the current user."""
    caps = session.exec(
        select(SpendingCap).where(SpendingCap.user_id == user.id).order_by(SpendingCap.created_at.desc())
    ).all()
    
    result = []
    for cap in caps:
        period_start, period_end = get_period_dates(cap.period)
        current_spend = calculate_current_spend(
            session, user.id, cap.cap_type, cap.target_name, period_start, period_end
        )
        
        result.append(CapResponse(
            id=cap.id,
            cap_type=cap.cap_type,
            target_name=cap.target_name,
            limit_amount=cap.limit_amount,
            period=cap.period,
            alert_threshold=cap.alert_threshold,
            alert_email=cap.alert_email,
            enabled=cap.enabled,
            current_spend=current_spend,
            percentage_used=(current_spend / cap.limit_amount * 100) if cap.limit_amount > 0 else 0,
            created_at=cap.created_at,
            updated_at=cap.updated_at,
        ))
    
    return result


@router.get("/{cap_id}", response_model=CapResponse)
async def get_cap(
    cap_id: UUID,
    user: User = Depends(get_current_clerk_user),
    session: Session = Depends(get_session),
):
    """Get a specific spending cap."""
    cap = session.get(SpendingCap, cap_id)
    if not cap or cap.user_id != user.id:
        raise HTTPException(status_code=404, detail="Cap not found")
    
    period_start, period_end = get_period_dates(cap.period)
    current_spend = calculate_current_spend(
        session, user.id, cap.cap_type, cap.target_name, period_start, period_end
    )
    
    return CapResponse(
        id=cap.id,
        cap_type=cap.cap_type,
        target_name=cap.target_name,
        limit_amount=cap.limit_amount,
        period=cap.period,
        alert_threshold=cap.alert_threshold,
        alert_email=cap.alert_email,
        enabled=cap.enabled,
        current_spend=current_spend,
        percentage_used=(current_spend / cap.limit_amount * 100) if cap.limit_amount > 0 else 0,
        created_at=cap.created_at,
        updated_at=cap.updated_at,
    )


@router.patch("/{cap_id}", response_model=CapResponse)
async def update_cap(
    cap_id: UUID,
    cap_update: CapUpdate,
    user: User = Depends(get_current_clerk_user),
    session: Session = Depends(get_session),
):
    """Update a spending cap."""
    cap = session.get(SpendingCap, cap_id)
    if not cap or cap.user_id != user.id:
        raise HTTPException(status_code=404, detail="Cap not found")
    
    if cap_update.limit_amount is not None:
        cap.limit_amount = cap_update.limit_amount
    if cap_update.alert_threshold is not None:
        cap.alert_threshold = cap_update.alert_threshold
    if cap_update.alert_email is not None:
        cap.alert_email = cap_update.alert_email
    if cap_update.enabled is not None:
        cap.enabled = cap_update.enabled
    
    cap.updated_at = datetime.utcnow()
    session.add(cap)
    session.commit()
    session.refresh(cap)
    
    period_start, period_end = get_period_dates(cap.period)
    current_spend = calculate_current_spend(
        session, user.id, cap.cap_type, cap.target_name, period_start, period_end
    )
    
    logger.info(f"Updated spending cap {cap_id} for user {user.email}")
    
    return CapResponse(
        id=cap.id,
        cap_type=cap.cap_type,
        target_name=cap.target_name,
        limit_amount=cap.limit_amount,
        period=cap.period,
        alert_threshold=cap.alert_threshold,
        alert_email=cap.alert_email,
        enabled=cap.enabled,
        current_spend=current_spend,
        percentage_used=(current_spend / cap.limit_amount * 100) if cap.limit_amount > 0 else 0,
        created_at=cap.created_at,
        updated_at=cap.updated_at,
    )


@router.delete("/{cap_id}")
async def delete_cap(
    cap_id: UUID,
    user: User = Depends(get_current_clerk_user),
    session: Session = Depends(get_session),
):
    """Delete a spending cap."""
    cap = session.get(SpendingCap, cap_id)
    if not cap or cap.user_id != user.id:
        raise HTTPException(status_code=404, detail="Cap not found")
    
    session.delete(cap)
    session.commit()
    
    logger.info(f"Deleted spending cap {cap_id} for user {user.email}")
    
    return {"status": "success", "message": "Cap deleted"}


@router.get("/alerts/", response_model=List[AlertResponse])
async def list_alerts(
    limit: int = Query(default=50, le=200),
    user: User = Depends(get_current_clerk_user),
    session: Session = Depends(get_session),
):
    """List alerts for the current user."""
    alerts = session.exec(
        select(Alert)
        .where(Alert.user_id == user.id)
        .order_by(Alert.created_at.desc())
        .limit(limit)
    ).all()
    
    return [
        AlertResponse(
            id=alert.id,
            alert_type=alert.alert_type,
            current_spend=alert.current_spend,
            cap_limit=alert.cap_limit,
            percentage=alert.percentage,
            target_type=alert.target_type,
            target_name=alert.target_name,
            period_start=alert.period_start,
            period_end=alert.period_end,
            email_sent=alert.email_sent,
            created_at=alert.created_at,
        )
        for alert in alerts
    ]

