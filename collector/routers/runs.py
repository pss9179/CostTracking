"""
Runs router - provides run-level aggregations and details.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func, text
from models import TraceEvent
from db import get_session, IS_POSTGRESQL
from auth import get_current_user_id
from clerk_auth import get_current_clerk_user

router = APIRouter(prefix="/runs", tags=["runs"])


def extract_top_level_section(section_path: str) -> str:
    """
    Extract top-level section from hierarchical path.
    
    Examples:
        "agent:research_assistant/step:analyze/retry:attempt_1" -> "agent:research_assistant"
        "tool:web_search" -> "tool:web_search"
        "retry:llm_analysis:attempt_1" -> None (filter out internal sections)
    """
    if not section_path:
        return None
    
    # Split by / to get first segment
    first_segment = section_path.split("/")[0] if "/" in section_path else section_path
    
    # Filter out internal/retry sections
    if first_segment.startswith("retry:") or first_segment.startswith("test:"):
        return None
    
    return first_segment


@router.get("/latest")
async def get_latest_runs(
    limit: int = 50,
    tenant_id: Optional[str] = Query(None, description="Tenant identifier for multi-tenant isolation"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)  # Require Clerk authentication
) -> List[Dict[str, Any]]:
    """
    Get latest runs with aggregated metrics for the authenticated user.
    
    Requires Clerk authentication. Returns only runs belonging to the authenticated user.
    
    Returns: List of runs with total_cost, call_count, sections, etc.
    """
    user_id = current_user.id
    # Group by run_id and aggregate
    # Use string_agg for PostgreSQL, group_concat for SQLite
    if IS_POSTGRESQL:
        sections_agg = func.string_agg(func.distinct(TraceEvent.section), text("','"))
    else:
        sections_agg = func.group_concat(func.distinct(TraceEvent.section))
    
    statement = select(
        TraceEvent.run_id,
        func.min(TraceEvent.created_at).label("started_at"),
        func.sum(TraceEvent.cost_usd).label("total_cost"),
        func.count(TraceEvent.id).label("call_count"),
        sections_agg.label("sections")
    ).group_by(TraceEvent.run_id)
    
    # Filter by tenant_id (preferred for multi-tenancy) or user_id
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
    
    statement = statement.order_by(func.min(TraceEvent.created_at).desc()).limit(limit)
    
    results = session.exec(statement).all()
    
    runs = []
    for result in results:
        # Get top-level section from section_path (e.g., "agent:research_assistant")
        section_path_statement = (
            select(TraceEvent.section_path)
            .where(TraceEvent.run_id == result.run_id)
            .where(TraceEvent.section_path.isnot(None))
        )
        # Apply same tenant/user filter
        if tenant_id:
            section_path_statement = section_path_statement.where(TraceEvent.tenant_id == tenant_id)
        elif user_id:
            section_path_statement = section_path_statement.where(TraceEvent.user_id == user_id)
        section_path_statement = section_path_statement.limit(1)
        section_path_result = session.exec(section_path_statement).first()
        
        # Extract top-level section
        top_section = None
        if section_path_result:
            top_section = extract_top_level_section(section_path_result)
        
        # Fallback to section field if no section_path
        if not top_section:
            section_statement = (
                select(TraceEvent.section)
                .where(TraceEvent.run_id == result.run_id)
            )
            # Apply same tenant/user filter
            if tenant_id:
                section_statement = section_statement.where(TraceEvent.tenant_id == tenant_id)
            elif user_id:
                section_statement = section_statement.where(TraceEvent.user_id == user_id)
            section_statement = section_statement.limit(1)
            section_result = session.exec(section_statement).first()
            top_section = section_result if section_result else "unknown"
        
        runs.append({
            "run_id": result.run_id,
            "started_at": result.started_at.isoformat(),
            "total_cost": result.total_cost,  # Don't round - let frontend format it
            "call_count": result.call_count,
            "sections": result.sections.split(",") if result.sections else [],
            "top_section": top_section
        })
    
    return runs


@router.get("/sections/top")
def get_top_sections(
    hours: int = Query(24, description="Time window in hours"),
    limit: int = Query(10, description="Number of sections to return"),
    user_id: Optional[UUID] = None,  # Made optional for MVP
    tenant_id: Optional[str] = Query(None, description="Tenant identifier for multi-tenant isolation"),
    session: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """
    Get top sections (agent/tool/step level) aggregated by cost.
    
    For MVP: Returns all data if no user_id or tenant_id provided.
    Returns agent-level sections like "agent:research_assistant",
    NOT internal retry/test sections.
    """
    from datetime import datetime, timedelta
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Get all events in timeframe
    statement = select(TraceEvent).where(TraceEvent.created_at >= cutoff_time).where(TraceEvent.section_path.isnot(None))
    # Filter by tenant_id (preferred) or user_id
    if tenant_id:
        statement = statement.where(TraceEvent.tenant_id == tenant_id)
    elif user_id:
        statement = statement.where(TraceEvent.user_id == user_id)
    
    events = session.exec(statement).all()
    
    # Aggregate by top-level section
    section_stats = {}
    for event in events:
        top_section = extract_top_level_section(event.section_path)
        if not top_section:  # Skip internal sections
            continue
        
        if top_section not in section_stats:
            section_stats[top_section] = {
                "section": top_section,
                "cost": 0.0,
                "calls": 0,
                "avg_latency": 0.0,
                "latencies": []
            }
        
        section_stats[top_section]["cost"] += event.cost_usd
        section_stats[top_section]["calls"] += 1
        section_stats[top_section]["latencies"].append(event.latency_ms)
    
    # Calculate averages and sort
    results = []
    for section, stats in section_stats.items():
        avg_latency = sum(stats["latencies"]) / len(stats["latencies"]) if stats["latencies"] else 0
        results.append({
            "section": section,
            "cost": round(stats["cost"], 6),
            "calls": stats["calls"],
            "avg_latency_ms": round(avg_latency, 2)
        })
    
    # Sort by cost descending
    results.sort(key=lambda x: x["cost"], reverse=True)
    
    return results[:limit]


@router.get("/{run_id}")
async def get_run_detail(
    run_id: str,
    tenant_id: Optional[str] = Query(None, description="Tenant identifier for multi-tenant isolation"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_clerk_user)  # Require Clerk authentication
) -> Dict[str, Any]:
    """
    Get detailed breakdown for a specific run belonging to the authenticated user.
    
    Requires Clerk authentication. Returns breakdown by section, provider, and model with percentages.
    """
    user_id = current_user.id
    # Check if run exists
    statement = select(TraceEvent).where(TraceEvent.run_id == run_id)
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
    statement = statement.limit(1)
    
    exists = session.exec(statement).first()
    
    if not exists:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    # Get total cost for percentage calculations
    total_statement = select(func.sum(TraceEvent.cost_usd)).where(TraceEvent.run_id == run_id)
    if tenant_id:
        total_statement = total_statement.where(TraceEvent.tenant_id == tenant_id)
    elif user_id:
        total_statement = total_statement.where(TraceEvent.user_id == user_id)
    total_cost = session.exec(total_statement).one() or 0.0
    
    # Breakdown by section
    section_statement = select(
        TraceEvent.section,
        func.sum(TraceEvent.cost_usd).label("cost"),
        func.count(TraceEvent.id).label("count")
    ).where(TraceEvent.run_id == run_id)
    if tenant_id:
        section_statement = section_statement.where(TraceEvent.tenant_id == tenant_id)
    elif user_id:
        section_statement = section_statement.where(TraceEvent.user_id == user_id)
    section_statement = section_statement.group_by(TraceEvent.section).order_by(func.sum(TraceEvent.cost_usd).desc())
    section_results = session.exec(section_statement).all()
    
    sections = [
        {
            "section": r.section,
            "cost": round(r.cost, 6),
            "count": r.count,
            "percentage": round((r.cost / total_cost * 100) if total_cost > 0 else 0, 2)
        }
        for r in section_results
    ]
    
    # Breakdown by provider
    provider_statement = select(
        TraceEvent.provider,
        func.sum(TraceEvent.cost_usd).label("cost"),
        func.count(TraceEvent.id).label("count")
    ).where(TraceEvent.run_id == run_id)
    if tenant_id:
        provider_statement = provider_statement.where(TraceEvent.tenant_id == tenant_id)
    elif user_id:
        provider_statement = provider_statement.where(TraceEvent.user_id == user_id)
    provider_statement = provider_statement.group_by(TraceEvent.provider).order_by(func.sum(TraceEvent.cost_usd).desc())
    provider_results = session.exec(provider_statement).all()
    
    providers = [
        {
            "provider": r.provider,
            "cost": round(r.cost, 6),
            "count": r.count,
            "percentage": round((r.cost / total_cost * 100) if total_cost > 0 else 0, 2)
        }
        for r in provider_results
    ]
    
    # Breakdown by model
    model_statement = select(
        TraceEvent.model,
        func.sum(TraceEvent.cost_usd).label("cost"),
        func.count(TraceEvent.id).label("count")
    ).where(TraceEvent.run_id == run_id).where(TraceEvent.model.isnot(None))
    if tenant_id:
        model_statement = model_statement.where(TraceEvent.tenant_id == tenant_id)
    elif user_id:
        model_statement = model_statement.where(TraceEvent.user_id == user_id)
    model_statement = model_statement.group_by(TraceEvent.model).order_by(func.sum(TraceEvent.cost_usd).desc())
    model_results = session.exec(model_statement).all()
    
    models = [
        {
            "model": r.model,
            "cost": round(r.cost, 6),
            "count": r.count,
            "percentage": round((r.cost / total_cost * 100) if total_cost > 0 else 0, 2)
        }
        for r in model_results
    ]
    
    # Get individual events (latest 50)
    events_statement = select(TraceEvent).where(TraceEvent.run_id == run_id)
    if tenant_id:
        events_statement = events_statement.where(TraceEvent.tenant_id == tenant_id)
    elif user_id:
        events_statement = events_statement.where(TraceEvent.user_id == user_id)
    events_statement = events_statement.order_by(TraceEvent.created_at.desc()).limit(50)
    events = session.exec(events_statement).all()
    
    events_list = [
        {
            "id": e.id,
            "span_id": e.span_id,
            "parent_span_id": e.parent_span_id,
            "section": e.section,
            "section_path": e.section_path,
            "provider": e.provider,
            "endpoint": e.endpoint,
            "model": e.model,
            "cost_usd": round(e.cost_usd, 6),
            "latency_ms": round(e.latency_ms, 2),
            "input_tokens": e.input_tokens,
            "output_tokens": e.output_tokens,
            "status": e.status,
            "created_at": e.created_at.isoformat(),
            "customer_id": e.customer_id,  # Include customer_id for filtering
        }
        for e in events
    ]
    
    return {
        "run_id": run_id,
        "total_cost": round(total_cost, 6),
        "breakdown": {
            "by_section": sections,
            "by_provider": providers,
            "by_model": models
        },
        "events": events_list
    }

