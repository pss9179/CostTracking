"""
Stats router - provides aggregated statistics.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func, and_
from sqlalchemy import case
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
    
    # Exclude "internal" provider and customer-specific events (dashboard shows only non-customer data)
    statement = statement.where(
        and_(
            TraceEvent.provider != "internal",
            TraceEvent.customer_id.is_(None)  # Only show non-customer data in dashboard
        )
    )
    
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


@router.get("/by-model")
async def get_costs_by_model(
    hours: int = 24,
    tenant_id: Optional[str] = Query(None, description="Tenant identifier for multi-tenant isolation"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)  # Require Clerk authentication
) -> List[Dict[str, Any]]:
    """
    Get costs aggregated by model for the authenticated user for the last N hours.
    
    Requires Clerk authentication. Returns breakdown with total cost, call count, and percentage per model.
    """
    user_id = current_user.id
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Get model aggregations
    statement = select(
        TraceEvent.model,
        TraceEvent.provider,
        func.sum(TraceEvent.cost_usd).label("total_cost"),
        func.count(TraceEvent.id).label("call_count"),
        func.sum(TraceEvent.input_tokens).label("input_tokens"),
        func.sum(TraceEvent.output_tokens).label("output_tokens"),
        func.avg(TraceEvent.latency_ms).label("avg_latency")
    ).where(TraceEvent.created_at >= cutoff)
    
    # Filter by user_id
    if tenant_id:
        statement = statement.where(TraceEvent.tenant_id == tenant_id)
    elif user_id:
        statement = statement.where(
            and_(
                TraceEvent.user_id == user_id,
                TraceEvent.user_id.isnot(None)
            )
        )
    
    # Exclude internal/unknown, require model, and exclude customer-specific events
    statement = statement.where(
        and_(
            TraceEvent.customer_id.is_(None),  # Only show non-customer data in dashboard
            TraceEvent.provider != "internal",
            TraceEvent.model.isnot(None)
        )
    )
    
    statement = statement.group_by(TraceEvent.model, TraceEvent.provider).order_by(func.sum(TraceEvent.cost_usd).desc())
    
    results = session.exec(statement).all()
    
    # Calculate total for percentages
    total_cost = sum(r.total_cost or 0 for r in results)
    
    models = [
        {
            "model": r.model or "unknown",
            "provider": r.provider,
            "total_cost": r.total_cost or 0,
            "call_count": r.call_count,
            "input_tokens": r.input_tokens or 0,
            "output_tokens": r.output_tokens or 0,
            "avg_latency": round(r.avg_latency or 0, 2),
            "percentage": round((r.total_cost / total_cost * 100) if total_cost > 0 else 0, 2)
        }
        for r in results
    ]
    
    return models


@router.get("/daily")
async def get_daily_costs(
    days: int = Query(7, description="Number of days to return"),
    tenant_id: Optional[str] = Query(None, description="Tenant identifier for multi-tenant isolation"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)
) -> List[Dict[str, Any]]:
    """
    Get daily aggregated costs for the chart.
    Returns costs per day with provider breakdown.
    """
    user_id = current_user.id
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Get daily aggregations with provider breakdown
    statement = select(
        func.date(TraceEvent.created_at).label("date"),
        TraceEvent.provider,
        func.sum(TraceEvent.cost_usd).label("total_cost"),
        func.count(TraceEvent.id).label("call_count")
    ).where(TraceEvent.created_at >= cutoff)
    
    # Filter by user_id
    if tenant_id:
        statement = statement.where(TraceEvent.tenant_id == tenant_id)
    elif user_id:
        statement = statement.where(
            and_(
                TraceEvent.user_id == user_id,
                TraceEvent.user_id.isnot(None)
            )
        )
    
    # Exclude internal and customer-specific events (dashboard shows only non-customer data)
    statement = statement.where(
        and_(
            TraceEvent.provider != "internal",
            TraceEvent.customer_id.is_(None)  # Only show non-customer data in dashboard
        )
    )
    
    statement = statement.group_by(
        func.date(TraceEvent.created_at),
        TraceEvent.provider
    ).order_by(func.date(TraceEvent.created_at))
    
    results = session.exec(statement).all()
    
    # Group by date
    daily_data = {}
    for r in results:
        date_str = str(r.date)
        if date_str not in daily_data:
            daily_data[date_str] = {"date": date_str, "total": 0, "providers": {}}
        daily_data[date_str]["total"] += r.total_cost or 0
        daily_data[date_str]["providers"][r.provider] = {
            "cost": r.total_cost or 0,
            "calls": r.call_count
        }
    
    # Fill in missing days with zeros
    result_list = []
    for i in range(days):
        date = (datetime.utcnow() - timedelta(days=days-1-i)).date()
        date_str = str(date)
        if date_str in daily_data:
            result_list.append(daily_data[date_str])
        else:
            result_list.append({"date": date_str, "total": 0, "providers": {}})
    
    return result_list


@router.get("/timeseries")
async def get_cost_timeseries(
    hours: int = Query(24, description="Time window in hours"),
    tenant_id: Optional[str] = Query(None, description="Tenant identifier for multi-tenant isolation"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)
) -> List[Dict[str, Any]]:
    """
    Get cost timeseries with appropriate granularity based on time window.
    - 1-6 hours: 15-minute buckets
    - 6-48 hours: hourly buckets  
    - 2-14 days: 4-hour buckets
    - 14+ days: daily buckets
    """
    user_id = current_user.id
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Determine bucket size based on time range
    if hours <= 6:
        # 15-minute buckets for very short ranges
        bucket_minutes = 15
        bucket_count = (hours * 60) // bucket_minutes
    elif hours <= 48:
        # Hourly buckets for 1-2 days
        bucket_minutes = 60
        bucket_count = hours
    elif hours <= 14 * 24:
        # 4-hour buckets for up to 2 weeks
        bucket_minutes = 240
        bucket_count = (hours * 60) // bucket_minutes
    else:
        # Daily buckets for longer ranges
        bucket_minutes = 1440
        bucket_count = (hours * 60) // bucket_minutes
    
    # Query raw events within time window
    statement = select(
        TraceEvent.created_at,
        TraceEvent.provider,
        TraceEvent.cost_usd
    ).where(TraceEvent.created_at >= cutoff)
    
    # Filter by user
    if tenant_id:
        statement = statement.where(TraceEvent.tenant_id == tenant_id)
    elif user_id:
        statement = statement.where(
            and_(
                TraceEvent.user_id == user_id,
                TraceEvent.user_id.isnot(None)
            )
        )
    
    # Exclude internal and customer-specific events (dashboard shows only non-customer data)
    statement = statement.where(
        and_(
            TraceEvent.provider != "internal",
            TraceEvent.customer_id.is_(None)  # Only show non-customer data in dashboard
        )
    )
    statement = statement.order_by(TraceEvent.created_at)
    
    results = session.exec(statement).all()
    
    # Helper to get bucket key/label based on time and bucket size
    def get_bucket_info(dt: datetime, bucket_mins: int):
        if bucket_mins >= 1440:
            # Daily buckets
            bucket_key = dt.strftime("%Y-%m-%d")
            bucket_label = dt.strftime("%b %d")
        elif bucket_mins >= 60:
            # Multi-hour buckets: round hour down to bucket boundary
            hours_per_bucket = bucket_mins // 60
            rounded_hour = (dt.hour // hours_per_bucket) * hours_per_bucket
            bucket_key = dt.strftime(f"%Y-%m-%d {rounded_hour:02d}:00")
            bucket_label = dt.strftime(f"%b %d {rounded_hour:02d}:00")
        else:
            # Sub-hourly buckets
            minute_bucket = (dt.minute // bucket_mins) * bucket_mins
            bucket_key = dt.strftime(f"%Y-%m-%d %H:{minute_bucket:02d}")
            bucket_label = dt.strftime(f"%H:{minute_bucket:02d}")
        return bucket_key, bucket_label
    
    # Create time buckets
    now = datetime.utcnow()
    buckets = {}
    
    for i in range(bucket_count + 1):
        bucket_time = now - timedelta(minutes=bucket_minutes * (bucket_count - i))
        bucket_key, bucket_label = get_bucket_info(bucket_time, bucket_minutes)
        
        if bucket_key not in buckets:
            buckets[bucket_key] = {
                "date": bucket_label,
                "timestamp": bucket_key,
                "total": 0,
                "providers": {}
            }
    
    # Aggregate events into buckets
    for event in results:
        event_time = event.created_at
        bucket_key, _ = get_bucket_info(event_time, bucket_minutes)
        
        if bucket_key in buckets:
            buckets[bucket_key]["total"] += event.cost_usd or 0
            provider = event.provider or "unknown"
            if provider not in buckets[bucket_key]["providers"]:
                buckets[bucket_key]["providers"][provider] = {"cost": 0, "calls": 0}
            buckets[bucket_key]["providers"][provider]["cost"] += event.cost_usd or 0
            buckets[bucket_key]["providers"][provider]["calls"] += 1
    
    # Return sorted by timestamp
    result_list = sorted(buckets.values(), key=lambda x: x["timestamp"])
    return result_list


@router.get("/by-section")
async def get_costs_by_section(
    hours: int = Query(24, description="Time window in hours"),
    tenant_id: Optional[str] = Query(None, description="Tenant identifier for multi-tenant isolation"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)
) -> List[Dict[str, Any]]:
    """
    Get costs aggregated by section/feature for the authenticated user.
    
    This returns costs broken down by section_path (e.g., "feature:email_processing", 
    "agent:researcher", "step:analyze"). Use this to see which features cost the most.
    """
    user_id = current_user.id
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Get section aggregations
    statement = select(
        TraceEvent.section,
        TraceEvent.section_path,
        func.sum(TraceEvent.cost_usd).label("total_cost"),
        func.count(TraceEvent.id).label("call_count"),
        func.avg(TraceEvent.latency_ms).label("avg_latency_ms")
    ).where(TraceEvent.created_at >= cutoff)
    
    # Filter by user_id
    if tenant_id:
        statement = statement.where(TraceEvent.tenant_id == tenant_id)
    elif user_id:
        statement = statement.where(
            and_(
                TraceEvent.user_id == user_id,
                TraceEvent.user_id.isnot(None)
            )
        )
    
    # Exclude internal provider, require section, and exclude customer-specific events (features page shows only non-customer data)
    statement = statement.where(
        and_(
            TraceEvent.provider != "internal",
            TraceEvent.section.isnot(None),
            TraceEvent.section != "default",
            TraceEvent.customer_id.is_(None)  # Only show non-customer data in features page
        )
    )
    
    statement = statement.group_by(TraceEvent.section, TraceEvent.section_path).order_by(func.sum(TraceEvent.cost_usd).desc())
    
    results = session.exec(statement).all()
    
    # Calculate total for percentages
    total_cost = sum(r.total_cost or 0 for r in results)
    
    sections = [
        {
            "section": r.section,
            "section_path": r.section_path,
            "total_cost": r.total_cost or 0,
            "call_count": r.call_count,
            "avg_latency_ms": round(r.avg_latency_ms or 0, 2),
            "percentage": round((r.total_cost / total_cost * 100) if total_cost > 0 else 0, 2)
        }
        for r in results
    ]
    
    return sections


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

