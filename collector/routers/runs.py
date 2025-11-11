"""
Runs router - provides run-level aggregations and details.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func
from models import TraceEvent
from db import get_session

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
def get_latest_runs(
    limit: int = 50,
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    session: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """
    Get latest runs with aggregated metrics.
    
    Returns: List of runs with total_cost, call_count, sections, etc.
    """
    # Group by run_id and aggregate
    statement = (
        select(
            TraceEvent.run_id,
            func.min(TraceEvent.created_at).label("started_at"),
            func.sum(TraceEvent.cost_usd).label("total_cost"),
            func.count(TraceEvent.id).label("call_count"),
            func.group_concat(func.distinct(TraceEvent.section)).label("sections")
        )
        .group_by(TraceEvent.run_id)
        .order_by(func.min(TraceEvent.created_at).desc())
        .limit(limit)
    )
    
    # Filter by tenant if provided
    if tenant_id:
        statement = statement.where(TraceEvent.tenant_id == tenant_id)
    
    results = session.exec(statement).all()
    
    runs = []
    for result in results:
        # Get top-level section from section_path (e.g., "agent:research_assistant")
        section_path_statement = (
            select(TraceEvent.section_path)
            .where(TraceEvent.run_id == result.run_id)
            .where(TraceEvent.section_path.isnot(None))
            .limit(1)
        )
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
                .limit(1)
            )
            section_result = session.exec(section_statement).first()
            top_section = section_result if section_result else "unknown"
        
        runs.append({
            "run_id": result.run_id,
            "started_at": result.started_at.isoformat(),
            "total_cost": round(result.total_cost, 6),
            "call_count": result.call_count,
            "sections": result.sections.split(",") if result.sections else [],
            "top_section": top_section
        })
    
    return runs


@router.get("/sections/top")
def get_top_sections(
    hours: int = Query(24, description="Time window in hours"),
    limit: int = Query(10, description="Number of sections to return"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    session: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """
    Get top sections (agent/tool/step level) aggregated by cost.
    
    Returns agent-level sections like "agent:research_assistant",
    NOT internal retry/test sections.
    """
    from datetime import datetime, timedelta
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Get all events in timeframe
    statement = (
        select(TraceEvent)
        .where(TraceEvent.created_at >= cutoff_time)
        .where(TraceEvent.section_path.isnot(None))
    )
    
    if tenant_id:
        statement = statement.where(TraceEvent.tenant_id == tenant_id)
    
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
def get_run_detail(
    run_id: str,
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get detailed breakdown for a specific run.
    
    Returns breakdown by section, provider, and model with percentages.
    """
    # Check if run exists
    statement = select(TraceEvent).where(TraceEvent.run_id == run_id)
    if tenant_id:
        statement = statement.where(TraceEvent.tenant_id == tenant_id)
    statement = statement.limit(1)
    exists = session.exec(statement).first()
    
    if not exists:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    # Get total cost for percentage calculations
    total_statement = select(func.sum(TraceEvent.cost_usd)).where(TraceEvent.run_id == run_id)
    if tenant_id:
        total_statement = total_statement.where(TraceEvent.tenant_id == tenant_id)
    total_cost = session.exec(total_statement).one() or 0.0
    
    # Breakdown by section
    section_statement = (
        select(
            TraceEvent.section,
            func.sum(TraceEvent.cost_usd).label("cost"),
            func.count(TraceEvent.id).label("count")
        )
        .where(TraceEvent.run_id == run_id)
        .group_by(TraceEvent.section)
        .order_by(func.sum(TraceEvent.cost_usd).desc())
    )
    if tenant_id:
        section_statement = section_statement.where(TraceEvent.tenant_id == tenant_id)
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
    provider_statement = (
        select(
            TraceEvent.provider,
            func.sum(TraceEvent.cost_usd).label("cost"),
            func.count(TraceEvent.id).label("count")
        )
        .where(TraceEvent.run_id == run_id)
        .group_by(TraceEvent.provider)
        .order_by(func.sum(TraceEvent.cost_usd).desc())
    )
    if tenant_id:
        provider_statement = provider_statement.where(TraceEvent.tenant_id == tenant_id)
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
    model_statement = (
        select(
            TraceEvent.model,
            func.sum(TraceEvent.cost_usd).label("cost"),
            func.count(TraceEvent.id).label("count")
        )
        .where(TraceEvent.run_id == run_id)
        .where(TraceEvent.model.isnot(None))
        .group_by(TraceEvent.model)
        .order_by(func.sum(TraceEvent.cost_usd).desc())
    )
    if tenant_id:
        model_statement = model_statement.where(TraceEvent.tenant_id == tenant_id)
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
    events_statement = (
        select(TraceEvent)
        .where(TraceEvent.run_id == run_id)
        .order_by(TraceEvent.created_at.desc())
        .limit(50)
    )
    if tenant_id:
        events_statement = events_statement.where(TraceEvent.tenant_id == tenant_id)
    events = session.exec(events_statement).all()
    
    events_list = [
        {
            "id": e.id,
            "section": e.section,
            "provider": e.provider,
            "endpoint": e.endpoint,
            "model": e.model,
            "cost_usd": round(e.cost_usd, 6),
            "latency_ms": round(e.latency_ms, 2),
            "input_tokens": e.input_tokens,
            "output_tokens": e.output_tokens,
            "status": e.status,
            "created_at": e.created_at.isoformat()
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

