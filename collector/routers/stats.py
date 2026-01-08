"""
Stats router - provides aggregated statistics.
"""
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, Header
from sqlmodel import Session, select, func, and_
from sqlalchemy import case, or_
from models import TraceEvent, User
from db import get_session
from auth import get_current_user_id
from clerk_auth import get_current_clerk_user

logger = logging.getLogger(__name__)

# =============================================================================
# SERVER-SIDE RESPONSE CACHE
# Caches identical queries to avoid repeated slow DB calls
# =============================================================================
_response_cache: Dict[str, Tuple[Any, float]] = {}
_cache_ttl_seconds = 300  # Cache for 5 minutes - Railway DB is very slow, need longer cache

def get_cached_response(cache_key: str) -> Optional[Any]:
    """Get cached response if it exists and is not expired."""
    if cache_key in _response_cache:
        data, timestamp = _response_cache[cache_key]
        if time.time() - timestamp < _cache_ttl_seconds:
            logger.debug(f"[CACHE HIT] {cache_key}")
            return data
        else:
            # Expired - remove from cache
            del _response_cache[cache_key]
    return None

def set_cached_response(cache_key: str, data: Any) -> None:
    """Store response in cache."""
    _response_cache[cache_key] = (data, time.time())
    # Limit cache size to prevent memory issues
    if len(_response_cache) > 1000:
        # Remove oldest entries
        sorted_keys = sorted(_response_cache.keys(), 
                            key=lambda k: _response_cache[k][1])
        for old_key in sorted_keys[:100]:
            del _response_cache[old_key]

def make_cache_key(endpoint: str, user_id: str, **params) -> str:
    """Create a unique cache key for a query."""
    param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()) if v is not None)
    return f"{endpoint}:{user_id}:{param_str}"

def clear_stats_cache():
    """Clear all cached stats responses."""
    global _response_cache
    count = len(_response_cache)
    _response_cache = {}
    return count

router = APIRouter(prefix="/stats", tags=["stats"])

@router.post("/clear-cache")
async def clear_cache():
    """Clear the stats response cache."""
    count = clear_stats_cache()
    return {"status": "success", "message": f"Cleared {count} cached responses"}

@router.get("/debug-user-data")
async def debug_user_data(
    clerk_id: str = Query(None, description="Clerk user ID to check (optional if token provided)"),
    session: Session = Depends(get_session),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Debug endpoint to check what data exists for a user."""
    from sqlmodel import select, func
    from models import TraceEvent, User
    from datetime import datetime, timedelta
    from sqlalchemy import or_
    import base64
    import json
    
    token_clerk_id = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        try:
            parts = token.split('.')
            if len(parts) == 3:
                payload = parts[1]
                padding = len(payload) % 4
                if padding:
                    payload += '=' * (4 - padding)
                decoded = base64.urlsafe_b64decode(payload)
                token_data = json.loads(decoded)
                token_clerk_id = token_data.get("sub") or token_data.get("user_id")
        except Exception as e:
            token_clerk_id = f"ERROR: {str(e)}"
    
    # Use token clerk_id if available, otherwise use query param
    effective_clerk_id = token_clerk_id if token_clerk_id and not token_clerk_id.startswith("ERROR") else clerk_id
    
    if not effective_clerk_id:
        return {"error": "No clerk_id provided (neither in query param nor extractable from token)"}
    
    # Find the user
    user_stmt = select(User).where(User.clerk_user_id == effective_clerk_id)
    user = session.exec(user_stmt).first()
    
    if not user:
        return {
            "error": f"User with clerk_id {effective_clerk_id} not found",
            "token_clerk_id": token_clerk_id,
            "query_clerk_id": clerk_id
        }
    
    cutoff = datetime.utcnow() - timedelta(hours=168)
    
    # Count events
    event_stmt = select(
        TraceEvent.provider,
        func.count(TraceEvent.id).label("count"),
        func.sum(TraceEvent.cost_usd).label("cost")
    ).where(
        TraceEvent.created_at >= cutoff,
        TraceEvent.customer_id.is_(None),
        TraceEvent.provider != "internal",
        or_(
            TraceEvent.tenant_id == clerk_id,
            TraceEvent.user_id == user.id
        )
    ).group_by(TraceEvent.provider)
    
    results = session.exec(event_stmt).all()
    
    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "clerk_user_id": user.clerk_user_id
        },
        "query_info": {
            "clerk_id_from_token": token_clerk_id,
            "clerk_id_from_query": clerk_id,
            "effective_clerk_id": effective_clerk_id,
            "user_id_used": str(user.id),
            "cutoff": str(cutoff)
        },
        "providers": [
            {"provider": r.provider, "count": r.count, "cost": float(r.cost or 0)}
            for r in results
        ],
        "total_providers": len(results)
    }


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
    customer_id: Optional[str] = Query(None, description="Filter by customer_id (for customer page)"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)  # Require Clerk authentication
) -> List[Dict[str, Any]]:
    """
    Get costs aggregated by provider for the authenticated user for the last N hours.
    
    If customer_id is provided, shows data for that customer only.
    If customer_id is None, shows only non-customer data (for dashboard).
    
    Requires Clerk authentication. Returns breakdown with total cost, call count, and percentage.
    """
    start_time = time.time()
    user_id = current_user.id
    print(f"[by-provider] START user={str(user_id)[:8]}... hours={hours}", flush=True)
    
    # Check server-side cache first
    cache_key = make_cache_key("by-provider", str(user_id), hours=hours, tenant_id=tenant_id, customer_id=customer_id)
    cached = get_cached_response(cache_key)
    if cached is not None:
        print(f"[by-provider] CACHE HIT in {(time.time()-start_time)*1000:.0f}ms", flush=True)
        return cached
    
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
                TraceEvent.user_id.isnot(None)
            )
        )
    
    # Filter by customer_id if provided, otherwise exclude customer data
    if customer_id:
        statement = statement.where(TraceEvent.customer_id == customer_id)
    else:
        # Dashboard: exclude customer-specific events
        statement = statement.where(TraceEvent.customer_id.is_(None))
    
    # Exclude "internal" provider
    statement = statement.where(TraceEvent.provider != "internal")
    
    statement = statement.group_by(TraceEvent.provider).order_by(func.sum(TraceEvent.cost_usd).desc())
    
    query_start = time.time()
    results = session.exec(statement).all()
    query_time = (time.time() - query_start) * 1000
    print(f"[by-provider] QUERY took {query_time:.0f}ms, rows={len(results)}", flush=True)
    
    # Calculate total for percentages (only non-internal providers)
    total_cost = sum(r.total_cost or 0 for r in results)
    
    providers = [
        {
            "provider": r.provider,
            "total_cost": r.total_cost,  # Don't round - let frontend format it
            "call_count": r.call_count,
            "percentage": round((r.total_cost / total_cost * 100) if total_cost > 0 else 0, 2)
        }
        for r in results
    ]
    
    # Cache the response
    set_cached_response(cache_key, providers)
    total_time = (time.time() - start_time) * 1000
    print(f"[by-provider] DONE in {total_time:.0f}ms", flush=True)
    return providers


@router.get("/by-model")
async def get_costs_by_model(
    hours: int = 24,
    tenant_id: Optional[str] = Query(None, description="Tenant identifier for multi-tenant isolation"),
    customer_id: Optional[str] = Query(None, description="Filter by customer_id (for customer page)"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)  # Require Clerk authentication
) -> List[Dict[str, Any]]:
    """
    Get costs aggregated by model for the authenticated user for the last N hours.
    
    If customer_id is provided, shows data for that customer only.
    If customer_id is None, shows only non-customer data (for dashboard).
    
    Requires Clerk authentication. Returns breakdown with total cost, call count, and percentage per model.
    """
    user_id = current_user.id
    
    # Check server-side cache first
    cache_key = make_cache_key("by-model", str(user_id), hours=hours, tenant_id=tenant_id, customer_id=customer_id)
    cached = get_cached_response(cache_key)
    if cached is not None:
        return cached
    
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
    
    # Filter by tenant_id (preferred) or user_id
    # IMPORTANT: Exclude events with NULL user_id to prevent data leakage between users
    if tenant_id:
        statement = statement.where(TraceEvent.tenant_id == tenant_id)
    elif user_id:
        statement = statement.where(
            and_(
                TraceEvent.user_id == user_id,
                TraceEvent.user_id.isnot(None)
            )
        )
    
    # Filter by customer_id if provided, otherwise exclude customer data
    if customer_id:
        statement = statement.where(TraceEvent.customer_id == customer_id)
    else:
        # Dashboard: exclude customer-specific events
        statement = statement.where(TraceEvent.customer_id.is_(None))
    
    # Exclude internal/unknown and require model
    statement = statement.where(
        and_(
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
    
    # Cache the response
    set_cached_response(cache_key, models)
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
    
    # Check server-side cache first
    cache_key = make_cache_key("daily", str(user_id), days=days, tenant_id=tenant_id)
    cached = get_cached_response(cache_key)
    if cached is not None:
        return cached
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Get daily aggregations with provider breakdown
    statement = select(
        func.date(TraceEvent.created_at).label("date"),
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
    
    # Cache the response
    set_cached_response(cache_key, result_list)
    return result_list


@router.get("/timeseries")
async def get_cost_timeseries(
    hours: int = Query(24, description="Time window in hours"),
    tenant_id: Optional[str] = Query(None, description="Tenant identifier for multi-tenant isolation"),
    customer_id: Optional[str] = Query(None, description="Filter by customer_id (for customer page)"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)
) -> List[Dict[str, Any]]:
    """
    Get cost timeseries with appropriate granularity based on time window.
    - 1-6 hours: 15-minute buckets
    - 6-48 hours: hourly buckets  
    - 2-14 days: 4-hour buckets
    - 14+ days: daily buckets
    
    If customer_id is provided, shows data for that customer only.
    If customer_id is None, shows only non-customer data (for dashboard).
    """
    user_id = current_user.id
    
    # Check server-side cache first
    cache_key = make_cache_key("timeseries", str(user_id), hours=hours, tenant_id=tenant_id, customer_id=customer_id)
    cached = get_cached_response(cache_key)
    if cached is not None:
        return cached
    
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
    
    # Filter by tenant_id (preferred) or user_id
    # IMPORTANT: Exclude events with NULL user_id to prevent data leakage between users
    if tenant_id:
        statement = statement.where(TraceEvent.tenant_id == tenant_id)
    elif user_id:
        statement = statement.where(
            and_(
                TraceEvent.user_id == user_id,
                TraceEvent.user_id.isnot(None)
            )
        )
    
    # Filter by customer_id if provided, otherwise exclude customer data
    if customer_id:
        statement = statement.where(TraceEvent.customer_id == customer_id)
    else:
        # Dashboard: exclude customer-specific events
        statement = statement.where(TraceEvent.customer_id.is_(None))
    
    # Exclude internal provider
    statement = statement.where(TraceEvent.provider != "internal")
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
    
    # Cache the response
    set_cached_response(cache_key, result_list)
    return result_list


@router.get("/by-section")
async def get_costs_by_section(
    hours: int = Query(24, description="Time window in hours"),
    tenant_id: Optional[str] = Query(None, description="Tenant identifier for multi-tenant isolation"),
    customer_id: Optional[str] = Query(None, description="Filter by customer_id (for customer page)"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)
) -> List[Dict[str, Any]]:
    """
    Get costs aggregated by section/feature for the authenticated user.
    
    This returns costs broken down by section_path (e.g., "feature:email_processing", 
    "agent:researcher", "step:analyze"). Use this to see which features cost the most.
    
    If customer_id is provided, shows data for that customer only.
    If customer_id is None, shows only non-customer data (for features page).
    """
    user_id = current_user.id
    
    # Check server-side cache first
    cache_key = make_cache_key("by-section", str(user_id), hours=hours, tenant_id=tenant_id, customer_id=customer_id)
    cached = get_cached_response(cache_key)
    if cached is not None:
        return cached
    
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Get section aggregations
    statement = select(
        TraceEvent.section,
        TraceEvent.section_path,
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
                TraceEvent.user_id.isnot(None)
            )
        )
    
    # Filter by customer_id if provided, otherwise exclude customer data
    if customer_id:
        statement = statement.where(TraceEvent.customer_id == customer_id)
    else:
        # Features page: exclude customer-specific events
        statement = statement.where(TraceEvent.customer_id.is_(None))
    
    # Exclude internal provider and require section
    statement = statement.where(
        and_(
            TraceEvent.provider != "internal",
            TraceEvent.section.isnot(None),
            TraceEvent.section != "default"
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
    
    # Cache the response
    set_cached_response(cache_key, sections)
    return sections


@router.get("/debug-customers")
async def debug_customers(
    hours: int = Query(720, description="Time window in hours"),
    clerk_id: str = Query(None, description="Clerk user ID to check"),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Debug endpoint to see customer data query details (no auth required for debugging)."""
    # Get the clerk_user_id for ethanzzheng@gmail.com
    user_stmt = select(User).where(User.email == "ethanzzheng@gmail.com")
    user = session.exec(user_stmt).first()
    user_id = user.id if user else None
    clerk_user_id = user.clerk_user_id if user else clerk_id
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Count events with customer_id for this user (by tenant_id) - WITH TIME FILTER
    tenant_count_stmt = select(func.count(TraceEvent.id)).where(
        and_(
            TraceEvent.customer_id.isnot(None),
            TraceEvent.tenant_id == clerk_user_id,
            TraceEvent.created_at >= cutoff
        )
    )
    tenant_count = session.exec(tenant_count_stmt).first() or 0
    
    # Count events with customer_id for this user (by user_id) - WITH TIME FILTER
    user_count_stmt = select(func.count(TraceEvent.id)).where(
        and_(
            TraceEvent.customer_id.isnot(None),
            TraceEvent.user_id == user_id,
            TraceEvent.created_at >= cutoff
        )
    )
    user_count = session.exec(user_count_stmt).first() or 0
    
    # Count ALL events with customer_id - WITH TIME FILTER
    all_count_stmt = select(func.count(TraceEvent.id)).where(
        and_(
            TraceEvent.customer_id.isnot(None),
            TraceEvent.created_at >= cutoff
        )
    )
    all_count = session.exec(all_count_stmt).first() or 0
    
    # Count events WITHOUT time filter
    no_time_count_stmt = select(func.count(TraceEvent.id)).where(
        TraceEvent.customer_id.isnot(None)
    )
    no_time_count = session.exec(no_time_count_stmt).first() or 0
    
    # Get recent events with customer_id
    recent_stmt = select(TraceEvent.tenant_id, TraceEvent.customer_id, TraceEvent.created_at, TraceEvent.provider).where(
        and_(
            TraceEvent.customer_id.isnot(None),
            TraceEvent.created_at >= cutoff
        )
    ).order_by(TraceEvent.created_at.desc()).limit(10)
    recent = session.exec(recent_stmt).all()
    
    return {
        "current_user_id": str(user_id),
        "current_clerk_user_id": clerk_user_id,
        "cutoff_time": str(cutoff),
        "hours": hours,
        "events_by_tenant_id_with_time": tenant_count,
        "events_by_user_id_with_time": user_count,
        "events_with_customer_id_with_time": all_count,
        "events_with_customer_id_no_time": no_time_count,
        "recent_events": [
            {
                "tenant_id": r.tenant_id, 
                "customer_id": r.customer_id, 
                "created_at": str(r.created_at),
                "provider": r.provider
            } for r in recent
        ]
    }


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
    try:
        user_id = current_user.id
        clerk_user_id = current_user.clerk_user_id  # Get Clerk user ID for tenant filtering
        
        # DEBUG: Log what we're looking for
        print(f"[by-customer] user_id={user_id}, clerk_user_id={clerk_user_id}, hours={hours}", flush=True)
        
        # Check server-side cache first
        cache_key = make_cache_key("by-customer", str(user_id), hours=hours, tenant_id=tenant_id)
        cached = get_cached_response(cache_key)
        if cached is not None:
            print(f"[by-customer] Returning cached response with {len(cached)} customers", flush=True)
            return cached
        
        # Calculate time window
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        # Get customer aggregations
        statement = select(
            TraceEvent.customer_id,
            func.sum(TraceEvent.cost_usd).label("total_cost"),
            func.count(TraceEvent.id).label("call_count"),
            func.avg(TraceEvent.latency_ms).label("avg_latency_ms")
        ).where(TraceEvent.created_at >= cutoff)
        
        # Filter by tenant_id (Clerk user ID) OR user_id to catch all events
        # - tenant_id: Set when events created via API key (matches API key owner's clerk_user_id)
        # - user_id: Fallback for events created through other means
        if clerk_user_id:
            statement = statement.where(
                or_(
                    TraceEvent.tenant_id == clerk_user_id,
                    TraceEvent.user_id == user_id
                )
            )
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
        print(f"[by-customer] Query returned {len(results)} customers", flush=True)
        
        customers = [
            {
                "customer_id": r.customer_id,
                "total_cost": r.total_cost,
                "call_count": r.call_count,
                "avg_latency_ms": round(r.avg_latency_ms or 0, 2)
            }
            for r in results
        ]
        
        # Cache the response
        set_cached_response(cache_key, customers)
        return customers
    except Exception as e:
        # Log error but return empty list instead of crashing
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Database error in get_costs_by_customer: {e}")
        # Return empty list so frontend can render gracefully
        return []


@router.get("/customer/{customer_id}")
async def get_customer_detail(
    customer_id: str,
    days: int = Query(30, ge=1, le=90, description="Number of days to look back"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)  # Require Clerk authentication
) -> Dict[str, Any]:
    """
    Get detailed breakdown for a specific customer.
    
    Requires Clerk authentication. Returns cost, calls, latency breakdown by provider and model.
    """
    try:
        user_id = current_user.id
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Overall stats for this customer
        stats_stmt = (
            select(
                func.sum(TraceEvent.cost_usd).label("total_cost"),
                func.count(TraceEvent.id).label("call_count"),
                func.avg(TraceEvent.latency_ms).label("avg_latency")
            )
            .where(and_(
                TraceEvent.user_id == user_id,
                TraceEvent.customer_id == customer_id,
                TraceEvent.created_at >= cutoff
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
            TraceEvent.user_id == user_id,
            TraceEvent.customer_id == customer_id,
            TraceEvent.created_at >= cutoff,
            TraceEvent.provider != "internal"
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
            TraceEvent.user_id == user_id,
            TraceEvent.customer_id == customer_id,
            TraceEvent.model.isnot(None),
            TraceEvent.created_at >= cutoff
        ))
        .group_by(TraceEvent.model)
        .order_by(func.sum(TraceEvent.cost_usd).desc())
        .limit(10)
        )
        models = session.exec(model_stmt).all()
        
        return {
            "customer_id": customer_id,
            "total_cost": round(stats.total_cost or 0, 6),
            "call_count": stats.call_count or 0,
            "avg_latency_ms": round(stats.avg_latency or 0, 2),
            "by_provider": [
                {
                    "provider": p.provider,
                    "cost": round(p.cost or 0, 6),
                    "calls": p.calls
                }
                for p in providers
            ],
            "top_models": [
                {
                    "model": m.model,
                    "cost": round(m.cost or 0, 6),
                    "calls": m.calls
                }
                for m in models
            ],
            "period_days": days
        }
    except Exception as e:
        # Log error but return empty data structure instead of crashing
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Database error in get_customer_detail: {e}")
        # Return empty structure so frontend can render gracefully
        return {
            "customer_id": customer_id,
            "total_cost": 0,
            "call_count": 0,
            "avg_latency_ms": 0,
            "by_provider": [],
            "top_models": [],
            "period_days": days
        }


# =============================================================================
# CONSOLIDATED DASHBOARD ENDPOINT
# Returns ALL dashboard data in a single request to minimize HTTP overhead
# =============================================================================
@router.get("/dashboard-all")
async def get_dashboard_all(
    hours: int = Query(168, description="Time window in hours for stats"),
    days: int = Query(7, description="Number of days for daily aggregates"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)
) -> Dict[str, Any]:
    """
    Consolidated endpoint that returns ALL dashboard data in one request.
    
    This reduces 5 parallel HTTP requests to 1, eliminating:
    - 5 CORS preflight requests
    - 5 separate TCP connections
    - Network overhead multiplied by 5
    
    Returns: provider stats, model stats, timeseries, and daily aggregates
    """
    import asyncio
    start_time = time.time()
    user_id = current_user.id
    clerk_user_id = current_user.clerk_user_id  # Use Clerk user ID for tenant filtering
    
    # Check cache first
    cache_key = make_cache_key("dashboard-all", str(user_id), hours=hours, days=days)
    cached = get_cached_response(cache_key)
    if cached is not None:
        print(f"[dashboard-all] CACHE HIT in {(time.time()-start_time)*1000:.0f}ms", flush=True)
        return cached
    
    print(f"[dashboard-all] START user_id={user_id} clerk_user_id={clerk_user_id} email={current_user.email} hours={hours} days={days}", flush=True)
    
    cutoff_hours = datetime.utcnow() - timedelta(hours=hours)
    cutoff_days = datetime.utcnow() - timedelta(days=days)
    
    # Run all queries (they share the same session/connection)
    query_start = time.time()
    
    # 1. Provider stats
    # CRITICAL: Filter by tenant_id OR user_id to match both API key events and direct events
    provider_conditions = [
        TraceEvent.created_at >= cutoff_hours,
        TraceEvent.customer_id.is_(None),
        TraceEvent.provider != "internal"
    ]
    # Filter by tenant_id (Clerk user ID) OR user_id - ensures we catch all events
    # - tenant_id: Set when events created via API key (matches API key owner's clerk_user_id)
    # - user_id: Fallback for events created through other means
    if clerk_user_id:
        provider_conditions.append(
            or_(
                TraceEvent.tenant_id == clerk_user_id,
                TraceEvent.user_id == user_id
            )
        )
    else:
        provider_conditions.append(TraceEvent.user_id == user_id)
    
    provider_stmt = select(
        TraceEvent.provider,
        func.sum(TraceEvent.cost_usd).label("total_cost"),
        func.count(TraceEvent.id).label("call_count")
    ).where(and_(*provider_conditions)).group_by(TraceEvent.provider).order_by(func.sum(TraceEvent.cost_usd).desc())
    
    provider_results = session.exec(provider_stmt).all()
    provider_total = sum(r.total_cost or 0 for r in provider_results)
    
    print(f"[dashboard-all] QUERY RESULT: Found {len(provider_results)} providers, total_cost={provider_total}", flush=True)
    
    providers = [
        {
            "provider": r.provider,
            "total_cost": r.total_cost or 0,
            "call_count": r.call_count,
            "percentage": round((r.total_cost or 0) / provider_total * 100, 1) if provider_total > 0 else 0
        }
        for r in provider_results
    ]
    
    # 2. Model stats
    # CRITICAL: Filter by tenant_id OR user_id to match both API key events and direct events
    model_conditions = [
        TraceEvent.created_at >= cutoff_hours,
        TraceEvent.customer_id.is_(None),
        TraceEvent.model.isnot(None)
    ]
    # Same user filtering as provider query
    if clerk_user_id:
        model_conditions.append(
            or_(
                TraceEvent.tenant_id == clerk_user_id,
                TraceEvent.user_id == user_id
            )
        )
    else:
        model_conditions.append(TraceEvent.user_id == user_id)
    
    model_stmt = select(
        TraceEvent.provider,
        TraceEvent.model,
        func.sum(TraceEvent.cost_usd).label("total_cost"),
        func.count(TraceEvent.id).label("call_count"),
        func.sum(TraceEvent.input_tokens).label("input_tokens"),
        func.sum(TraceEvent.output_tokens).label("output_tokens"),
        func.avg(TraceEvent.latency_ms).label("avg_latency")
    ).where(and_(*model_conditions)).group_by(TraceEvent.provider, TraceEvent.model).order_by(func.sum(TraceEvent.cost_usd).desc())
    
    model_results = session.exec(model_stmt).all()
    
    models = [
        {
            "provider": r.provider,
            "model": r.model,
            "total_cost": r.total_cost or 0,
            "call_count": r.call_count,
            "input_tokens": r.input_tokens or 0,
            "output_tokens": r.output_tokens or 0,
            "avg_latency": round(r.avg_latency or 0, 2)
        }
        for r in model_results
    ]
    
    # 3. Daily aggregates (for the chart)
    from db import IS_POSTGRESQL
    if IS_POSTGRESQL:
        date_trunc = func.date_trunc('day', TraceEvent.created_at)
    else:
        date_trunc = func.date(TraceEvent.created_at)
    
    # 3. Daily aggregates - filter by tenant_id OR user_id to match both API key events and direct events
    daily_conditions = [
        TraceEvent.created_at >= cutoff_days,
        TraceEvent.customer_id.is_(None)
    ]
    # Same user filtering as other queries
    if clerk_user_id:
        daily_conditions.append(
            or_(
                TraceEvent.tenant_id == clerk_user_id,
                TraceEvent.user_id == user_id
            )
        )
    else:
        daily_conditions.append(TraceEvent.user_id == user_id)
    
    daily_stmt = select(
        date_trunc.label("date"),
        func.sum(TraceEvent.cost_usd).label("total_cost"),
        func.count(TraceEvent.id).label("call_count")
    ).where(and_(*daily_conditions)).group_by(date_trunc).order_by(date_trunc)
    
    daily_results = session.exec(daily_stmt).all()
    
    daily = [
        {
            "date": str(r.date)[:10] if r.date else None,
            "total_cost": r.total_cost or 0,
            "call_count": r.call_count
        }
        for r in daily_results
    ]
    
    query_time = (time.time() - query_start) * 1000
    total_time = (time.time() - start_time) * 1000
    print(f"[dashboard-all] DONE queries={query_time:.0f}ms total={total_time:.0f}ms", flush=True)
    
    result = {
        "providers": providers,
        "models": models,
        "daily": daily,
        "hours": hours,
        "days": days,
        "generated_at": datetime.utcnow().isoformat()
    }
    
    # Cache the result
    set_cached_response(cache_key, result)
    
    return result

