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
from clerk_auth import get_current_clerk_user

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/llms")
async def get_llm_stats(
    hours: int = Query(24, description="Time window in hours"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)  # Require Clerk authentication
) -> List[Dict[str, Any]]:
    """
    Get aggregated LLM stats by provider and model.
    
    Returns breakdown of costs, tokens, calls, latency per model.
    """
    user_id = current_user.id
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Aggregate by provider + model
    statement = select(
        TraceEvent.provider,
        TraceEvent.model,
        func.sum(TraceEvent.cost_usd).label("total_cost"),
        func.count(TraceEvent.id).label("call_count"),
        func.sum(TraceEvent.input_tokens).label("prompt_tokens"),
        func.sum(TraceEvent.output_tokens).label("completion_tokens"),
        func.avg(TraceEvent.latency_ms).label("avg_latency"),
        func.sum(case((TraceEvent.status == "error", 1), else_=0)).label("errors")
    ).where(
        and_(
            TraceEvent.created_at >= cutoff,
            TraceEvent.user_id == user_id,
            TraceEvent.user_id.isnot(None),
            TraceEvent.model.isnot(None),  # Only include events with model info
            TraceEvent.provider.notin_(["internal", "websocket", "unknown"])  # Filter out non-LLM providers
        )
    ).group_by(TraceEvent.provider, TraceEvent.model).order_by(func.sum(TraceEvent.cost_usd).desc())
    
    results = session.exec(statement).all()
    
    return [
        {
            "provider": r.provider,
            "model_id": r.model or "unknown",
            "cost": round(r.total_cost or 0.0, 6),
            "calls": r.call_count,
            "tokens_prompt": r.prompt_tokens or 0,
            "tokens_completion": r.completion_tokens or 0,
            "tokens_total": (r.prompt_tokens or 0) + (r.completion_tokens or 0),
            "avg_latency": round(r.avg_latency or 0.0, 2),
            "errors": r.errors or 0
        }
        for r in results
    ]


@router.get("/infrastructure")
async def get_infrastructure_stats(
    hours: int = Query(24, description="Time window in hours"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)  # Require Clerk authentication
) -> List[Dict[str, Any]]:
    """
    Get aggregated infrastructure stats (databases, caches, etc).
    
    Returns breakdown of costs, calls, latency for non-LLM services.
    """
    user_id = current_user.id
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Aggregate infrastructure services (non-LLM providers)
    # Infrastructure providers: pinecone, redis, postgres, mongodb, elasticsearch, etc.
    infrastructure_providers = ["pinecone", "redis", "postgres", "mongodb", "elasticsearch", "milvus", "weaviate", "qdrant"]
    
    statement = select(
        TraceEvent.provider,
        TraceEvent.endpoint,
        func.sum(TraceEvent.cost_usd).label("total_cost"),
        func.count(TraceEvent.id).label("call_count"),
        func.avg(TraceEvent.latency_ms).label("avg_latency"),
        func.sum(case((TraceEvent.status == "error", 1), else_=0)).label("errors")
    ).where(
        and_(
            TraceEvent.created_at >= cutoff,
            TraceEvent.user_id == user_id,
            TraceEvent.user_id.isnot(None),
            TraceEvent.provider.in_(infrastructure_providers)
        )
    ).group_by(TraceEvent.provider, TraceEvent.endpoint).order_by(func.sum(TraceEvent.cost_usd).desc())
    
    results = session.exec(statement).all()
    
    return [
        {
            "provider": r.provider,
            "service_api": r.endpoint or "unknown",
            "cost": round(r.total_cost or 0.0, 6),
            "calls": r.call_count,
            "reads": 0,  # TODO: Parse from endpoint if needed
            "writes": 0,  # TODO: Parse from endpoint if needed
            "avg_latency": round(r.avg_latency or 0.0, 2),
            "errors": r.errors or 0,
            "percent_of_total": 0.0  # Will be calculated on frontend
        }
        for r in results
    ]


@router.get("/by-provider")
async def get_costs_by_provider(
    hours: int = 24,
    tenant_id: Optional[str] = Query(None, description="Tenant identifier for multi-tenant isolation"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)  # Require Clerk authentication
) -> List[Dict[str, Any]]:
    """
    Get costs aggregated by provider for the authenticated user for the last N hours.
    
    Requires Clerk authentication. Returns breakdown with total cost, call count, and percentage.
    """
    user_id = current_user.id
    # Calculate time window
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Get provider aggregations
    statement = select(
        TraceEvent.provider,
        func.sum(TraceEvent.cost_usd).label("total_cost"),
        func.count(TraceEvent.id).label("call_count")
    ).where(TraceEvent.created_at >= cutoff)
    
    # Filter by tenant_id (preferred) or user_id
    # IMPORTANT: Exclude events with NULL user_id to prevent data leakage between users
    if tenant_id:
        statement = statement.where(TraceEvent.tenant_id == tenant_id)
    elif user_id:
        statement = statement.where(
            and_(
                TraceEvent.user_id == user_id,
                TraceEvent.user_id.isnot(None)  # Exclude NULL user_id events
            )
        )
    
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
async def get_costs_by_customer(
    hours: int = Query(720, description="Time window in hours (default 30 days)"),
    tenant_id: Optional[str] = Query(None, description="Tenant identifier for multi-tenant isolation"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)  # Require Clerk authentication
) -> List[Dict[str, Any]]:
    """
    Get costs aggregated by customer_id for the authenticated user for the last N hours.
    
    Requires Clerk authentication. Returns breakdown with total cost, call count, and average latency.
    """
    user_id = current_user.id
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
    # IMPORTANT: Exclude events with NULL user_id to prevent data leakage between users
    if tenant_id:
        statement = statement.where(TraceEvent.tenant_id == tenant_id)
    elif user_id:
        statement = statement.where(
            and_(
                TraceEvent.user_id == user_id,
                TraceEvent.user_id.isnot(None)  # Exclude NULL user_id events
            )
        )
    
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

