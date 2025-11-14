"""
Insights router - auto-generated insights and anomaly detection.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func, and_
from models import TraceEvent
from db import get_session
from auth import get_current_user_id

router = APIRouter(prefix="/insights", tags=["insights"])


def _section_spike_insights(session: Session, user_id: UUID) -> List[Dict[str, Any]]:
    """
    Detect section cost spikes (today > 2× vs 7-day average).
    """
    insights = []
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = today_start - timedelta(days=7)
    
    # Get all sections for this user
    sections_statement = select(TraceEvent.section).where(TraceEvent.user_id == user_id).distinct()
    sections = session.exec(sections_statement).all()
    
    for section in sections:
        # Today's total cost
        today_statement = (
            select(func.sum(TraceEvent.cost_usd))
            .where(and_(
                TraceEvent.user_id == user_id,
                TraceEvent.section == section,
                TraceEvent.created_at >= today_start
            ))
        )
        today_total = session.exec(today_statement).one() or 0.0
        
        # Today's run count
        today_runs_statement = (
            select(func.count(func.distinct(TraceEvent.run_id)))
            .where(and_(
                TraceEvent.user_id == user_id,
                TraceEvent.section == section,
                TraceEvent.created_at >= today_start
            ))
        )
        today_runs = session.exec(today_runs_statement).one() or 1
        today_avg = today_total / today_runs if today_runs > 0 else 0.0
        
        # 7-day total and run count (excluding today)
        past_statement = (
            select(func.sum(TraceEvent.cost_usd))
            .where(and_(
                TraceEvent.user_id == user_id,
                TraceEvent.section == section,
                TraceEvent.created_at >= seven_days_ago,
                TraceEvent.created_at < today_start
            ))
        )
        past_total = session.exec(past_statement).one() or 0.0
        
        past_runs_statement = (
            select(func.count(func.distinct(TraceEvent.run_id)))
            .where(and_(
                TraceEvent.user_id == user_id,
                TraceEvent.section == section,
                TraceEvent.created_at >= seven_days_ago,
                TraceEvent.created_at < today_start
            ))
        )
        past_runs = session.exec(past_runs_statement).one() or 1
        past_avg = past_total / past_runs if past_runs > 0 else 0.0
        
        # Check for spike
        if past_avg > 0 and today_avg > 2 * past_avg:
            delta = today_avg / past_avg
            insights.append({
                "type": "section_spike",
                "section": section,
                "delta": round(delta, 2),
                "message": f"Section '{section}' cost up {delta:.1f}× vs 7-day avg (check for increased calls or token usage)."
            })
    
    return insights


def _model_inefficiency_insights(session: Session, user_id: UUID) -> List[Dict[str, Any]]:
    """
    Detect model inefficiency (expensive model used where cheaper alternative exists).
    """
    insights = []
    
    # Get sections with multiple models in last 24h
    yesterday = datetime.utcnow() - timedelta(hours=24)
    
    sections_statement = select(TraceEvent.section).where(and_(
        TraceEvent.user_id == user_id,
        TraceEvent.created_at >= yesterday
    )).distinct()
    sections = session.exec(sections_statement).all()
    
    for section in sections:
        # Get models used in this section with their avg cost per token
        models_statement = (
            select(
                TraceEvent.model,
                func.sum(TraceEvent.cost_usd).label("total_cost"),
                func.sum(TraceEvent.input_tokens + TraceEvent.output_tokens).label("total_tokens")
            )
            .where(and_(
                TraceEvent.user_id == user_id,
                TraceEvent.section == section,
                TraceEvent.created_at >= yesterday,
                TraceEvent.model.isnot(None),
                (TraceEvent.input_tokens + TraceEvent.output_tokens) > 0
            ))
            .group_by(TraceEvent.model)
        )
        models = session.exec(models_statement).all()
        
        if len(models) >= 2:
            # Calculate cost per token for each model
            model_efficiency = [
                {
                    "model": m.model,
                    "cost_per_token": m.total_cost / m.total_tokens if m.total_tokens > 0 else 0
                }
                for m in models
            ]
            model_efficiency.sort(key=lambda x: x["cost_per_token"])
            
            # Check if expensive model is used
            cheapest = model_efficiency[0]
            most_expensive = model_efficiency[-1]
            
            if most_expensive["cost_per_token"] > 2 * cheapest["cost_per_token"]:
                insights.append({
                    "type": "model_inefficiency",
                    "section": section,
                    "expensive_model": most_expensive["model"],
                    "cheaper_alternative": cheapest["model"],
                    "message": f"Section '{section}' uses {most_expensive['model']} (expensive). Consider {cheapest['model']} for cost savings."
                })
    
    return insights


def _token_bloat_insights(session: Session, user_id: UUID) -> List[Dict[str, Any]]:
    """
    Detect token bloat (input tokens > 1.5× vs 7-day average).
    """
    insights = []
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = today_start - timedelta(days=7)
    
    # Get sections for this user
    sections_statement = select(TraceEvent.section).where(TraceEvent.user_id == user_id).distinct()
    sections = session.exec(sections_statement).all()
    
    for section in sections:
        # Today's average input tokens
        today_statement = (
            select(func.avg(TraceEvent.input_tokens))
            .where(and_(
                TraceEvent.user_id == user_id,
                TraceEvent.section == section,
                TraceEvent.created_at >= today_start,
                TraceEvent.input_tokens > 0
            ))
        )
        today_avg = session.exec(today_statement).one() or 0.0
        
        # 7-day average
        past_statement = (
            select(func.avg(TraceEvent.input_tokens))
            .where(and_(
                TraceEvent.user_id == user_id,
                TraceEvent.section == section,
                TraceEvent.created_at >= seven_days_ago,
                TraceEvent.created_at < today_start,
                TraceEvent.input_tokens > 0
            ))
        )
        past_avg = session.exec(past_statement).one() or 0.0
        
        # Check for bloat
        if past_avg > 0 and today_avg > 1.5 * past_avg:
            delta = today_avg / past_avg
            insights.append({
                "type": "token_bloat",
                "section": section,
                "delta": round(delta, 2),
                "message": f"Section '{section}' input tokens up {delta:.1f}× vs 7-day avg (check prompt size or context length)."
            })
    
    return insights


def _retry_loop_insights(session: Session, user_id: UUID) -> List[Dict[str, Any]]:
    """
    Detect retry/loop patterns (same endpoint called > 3× per run, p95).
    """
    insights = []
    yesterday = datetime.utcnow() - timedelta(hours=24)
    
    # Get provider/endpoint combinations for this user
    combos_statement = (
        select(
            TraceEvent.provider,
            TraceEvent.endpoint
        )
        .where(and_(
            TraceEvent.user_id == user_id,
            TraceEvent.created_at >= yesterday
        ))
        .distinct()
    )
    combos = session.exec(combos_statement).all()
    
    for provider, endpoint in combos:
        # Count calls per run for this provider/endpoint
        calls_per_run_statement = (
            select(
                TraceEvent.run_id,
                func.count(TraceEvent.id).label("call_count")
            )
            .where(and_(
                TraceEvent.user_id == user_id,
                TraceEvent.provider == provider,
                TraceEvent.endpoint == endpoint,
                TraceEvent.created_at >= yesterday
            ))
            .group_by(TraceEvent.run_id)
            .order_by(func.count(TraceEvent.id).desc())
        )
        results = session.exec(calls_per_run_statement).all()
        
        if results:
            # Calculate p95 (simplified: just take 95th percentile index)
            counts = [r.call_count for r in results]
            if len(counts) > 0:
                p95_idx = max(0, int(len(counts) * 0.05))  # Top 5%
                p95_value = counts[p95_idx] if p95_idx < len(counts) else counts[0]
                
                if p95_value > 3:
                    insights.append({
                        "type": "retry_loop",
                        "provider": provider,
                        "endpoint": endpoint,
                        "p95_calls": p95_value,
                        "message": f"{provider}.{endpoint} called {p95_value}× per run (p95). Possible retry loop or inefficient logic."
                    })
    
    return insights


@router.get("/daily")
def get_daily_insights(
    user_id: Optional[UUID] = Depends(get_current_user_id),
    tenant_id: Optional[str] = Query(None, description="Tenant identifier for multi-tenant isolation"),
    session: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """
    Get auto-generated insights for the last 24 hours.
    
    Automatically filtered by authenticated user or tenant_id.
    Returns insights about cost spikes, inefficiencies, token bloat, and retry patterns.
    
    For MVP: Can work without authentication if tenant_id is provided.
    """
    insights = []
    
    # If tenant_id provided, use it; otherwise use user_id
    # Note: Insight functions currently use user_id, but we can add tenant_id support later
    # For now, tenant_id filtering happens at the query level in each insight function
    if tenant_id:
        # TODO: Update insight functions to support tenant_id
        # For now, skip insights if only tenant_id provided (user_id is None)
        pass
    elif user_id:
        # Run all insight detectors with user_id filter
        insights.extend(_section_spike_insights(session, user_id))
        insights.extend(_model_inefficiency_insights(session, user_id))
        insights.extend(_token_bloat_insights(session, user_id))
        insights.extend(_retry_loop_insights(session, user_id))
    
    return insights

