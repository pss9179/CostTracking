"""Repository for span and trace data access."""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlmodel import Session, select

from llmobserve.storage.db import get_session
from llmobserve.storage.models import SpanSummary, Trace

# TODO: Production hardening
# 1. Implement Redis caching for frequently accessed traces/metrics
# 2. Add connection pooling configuration
# 3. Implement batch writes for better throughput
# 4. Add database query optimization (indexes, query plans)
# 5. Support ClickHouse/TimeScaleDB for time-series data


class SpanRepository:
    """Repository for span and trace operations."""

    def create_span_summary(self, summary: dict) -> SpanSummary:
        """Create a span summary record."""
        with get_session() as session:
            span = SpanSummary(**summary)
            session.add(span)
            session.commit()
            session.refresh(span)
            return span

    def get_spans(
        self,
        tenant_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SpanSummary]:
        """Get spans with optional filtering."""
        with get_session() as session:
            statement = select(SpanSummary)
            if tenant_id:
                statement = statement.where(SpanSummary.tenant_id == tenant_id)
            if trace_id:
                statement = statement.where(SpanSummary.trace_id == trace_id)
            statement = statement.order_by(SpanSummary.start_time.desc()).limit(limit).offset(offset)
            return list(session.exec(statement).all())

    def get_trace(self, trace_id: str, tenant_id: Optional[str] = None) -> Optional[Trace]:
        """Get trace by ID."""
        with get_session() as session:
            statement = select(Trace).where(Trace.trace_id == trace_id)
            if tenant_id:
                statement = statement.where(Trace.tenant_id == tenant_id)
            return session.exec(statement).first()

    def get_traces(
        self,
        tenant_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Trace]:
        """Get traces with optional tenant filtering."""
        with get_session() as session:
            statement = select(Trace)
            if tenant_id:
                statement = statement.where(Trace.tenant_id == tenant_id)
            statement = statement.order_by(Trace.start_time.desc()).limit(limit).offset(offset)
            return list(session.exec(statement).all())

    def get_trace_spans(self, trace_id: str, tenant_id: Optional[str] = None) -> List[SpanSummary]:
        """Get all spans for a trace."""
        return self.get_spans(tenant_id=tenant_id, trace_id=trace_id, limit=1000)

    def aggregate_trace(self, trace_id: str, tenant_id: str, workflow_name: Optional[str] = None) -> Trace:
        """Aggregate spans into trace summary."""
        spans = self.get_trace_spans(trace_id, tenant_id)
        if not spans:
            raise ValueError(f"Trace {trace_id} not found")

        total_cost = sum(s.cost_usd for s in spans)
        total_tokens = sum(s.total_tokens for s in spans)
        start_times = [s.start_time for s in spans if s.start_time]
        end_times = [
            s.start_time + (s.duration_ms / 1000) for s in spans if s.start_time and s.duration_ms
        ]

        root_span = next((s for s in spans if not s.parent_span_id), spans[0] if spans else None)
        root_span_name = root_span.name if root_span else None

        trace_start = min(start_times) if start_times else 0.0
        trace_end = max(end_times) if end_times else None
        duration_ms = (trace_end - trace_start) * 1000 if trace_end else None

        trace = Trace(
            trace_id=trace_id,
            tenant_id=tenant_id,
            root_span_name=root_span_name,
            workflow_name=workflow_name,
            total_cost_usd=total_cost,
            total_tokens=total_tokens,
            span_count=len(spans),
            start_time=trace_start,
            duration_ms=duration_ms,
        )

        with get_session() as session:
            # Upsert trace
            existing = session.exec(select(Trace).where(Trace.trace_id == trace_id)).first()
            if existing:
                for key, value in trace.dict(exclude={"id"}).items():
                    setattr(existing, key, value)
                trace = existing
            else:
                session.add(trace)
            session.commit()
            session.refresh(trace)
            return trace

    def get_metrics(
        self,
        tenant_id: Optional[str] = None,
        days: int = 7,
    ) -> dict:
        """Get aggregated metrics for dashboard."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        cutoff_timestamp = cutoff.timestamp()

        with get_session() as session:
            statement = select(SpanSummary).where(SpanSummary.start_time >= cutoff_timestamp)
            if tenant_id:
                statement = statement.where(SpanSummary.tenant_id == tenant_id)
            spans = list(session.exec(statement).all())

        total_cost = sum(s.cost_usd for s in spans)
        total_tokens = sum(s.total_tokens for s in spans)
        total_requests = len(spans)

        # Cost by model
        cost_by_model: dict[str, float] = {}
        for span in spans:
            if span.model:
                cost_by_model[span.model] = cost_by_model.get(span.model, 0.0) + span.cost_usd

        # Cost over time (daily buckets)
        cost_over_time: dict[str, float] = {}
        for span in spans:
            date_key = datetime.fromtimestamp(span.start_time).strftime("%Y-%m-%d")
            cost_over_time[date_key] = cost_over_time.get(date_key, 0.0) + span.cost_usd

        return {
            "total_cost_usd": total_cost,
            "total_tokens": total_tokens,
            "total_requests": total_requests,
            "cost_by_model": cost_by_model,
            "cost_over_time": cost_over_time,
        }

    def update_span_name(self, span_id: str, span_name: str, tenant_id: Optional[str] = None) -> SpanSummary:
        """Update span name."""
        with get_session() as session:
            statement = select(SpanSummary).where(SpanSummary.span_id == span_id)
            if tenant_id:
                statement = statement.where(SpanSummary.tenant_id == tenant_id)
            span = session.exec(statement).first()
            if not span:
                raise ValueError(f"Span {span_id} not found")
            
            span.name = span_name
            session.add(span)
            session.commit()
            session.refresh(span)
            return span

    def update_workflow_name(self, trace_id: str, workflow_name: str, tenant_id: Optional[str] = None) -> Trace:
        """Update workflow name for a trace."""
        with get_session() as session:
            statement = select(Trace).where(Trace.trace_id == trace_id)
            if tenant_id:
                statement = statement.where(Trace.tenant_id == tenant_id)
            trace = session.exec(statement).first()
            if not trace:
                raise ValueError(f"Trace {trace_id} not found")
            
            trace.workflow_name = workflow_name
            session.add(trace)
            session.commit()
            session.refresh(trace)
            return trace

    def get_workflows(
        self,
        tenant_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[dict]:
        """Get workflows with aggregated stats grouped by workflow_name."""
        with get_session() as session:
            # Get all traces with workflow_name
            statement = select(Trace).where(Trace.workflow_name.isnot(None))
            if tenant_id:
                statement = statement.where(Trace.tenant_id == tenant_id)
            traces = list(session.exec(statement).all())
        
        # Group by workflow_name
        workflows: dict[str, dict] = {}
        for trace in traces:
            workflow_name = trace.workflow_name
            if workflow_name not in workflows:
                workflows[workflow_name] = {
                    "workflow_name": workflow_name,
                    "total_cost_usd": 0.0,
                    "total_tokens": 0,
                    "total_runs": 0,
                    "avg_latency_ms": 0.0,
                    "span_count": 0,
                    "last_run": trace.start_time,
                }
            
            workflows[workflow_name]["total_cost_usd"] += trace.total_cost_usd
            workflows[workflow_name]["total_tokens"] += trace.total_tokens
            workflows[workflow_name]["total_runs"] += 1
            workflows[workflow_name]["span_count"] += trace.span_count
            if trace.start_time > workflows[workflow_name]["last_run"]:
                workflows[workflow_name]["last_run"] = trace.start_time
        
        # Calculate average latency
        for workflow_name, stats in workflows.items():
            workflow_traces = [t for t in traces if t.workflow_name == workflow_name and t.duration_ms]
            if workflow_traces:
                avg_latency = sum(t.duration_ms for t in workflow_traces) / len(workflow_traces)
                stats["avg_latency_ms"] = avg_latency
        
        # Sort by last_run descending and limit
        workflow_list = sorted(workflows.values(), key=lambda x: x["last_run"], reverse=True)
        return workflow_list[:limit]

