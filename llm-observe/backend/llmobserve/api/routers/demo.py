"""Demo endpoints for agent workflow and fake app."""

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional

from llmobserve.demo.agent import run_agent_workflow
from llmobserve.demo.fake_app import run_fake_app
from llmobserve.demo.simulate_agent import simulate_agent_workflow
from llmobserve.demo.multi_workflows import (
    gmail_workflow,
    calendar_workflow,
    vapi_workflow,
    run_all_workflows,
)
from llmobserve.demo.complex_nested_workflows import (
    run_all_complex_workflows,
    gpt_vapi_google_workflow,
    vapi_google_pinecone_workflow,
    nested_async_workflow,
    parallel_workflows_with_nesting,
    deeply_nested_workflow,
)
from llmobserve.storage.repo import SpanRepository
from llmobserve.storage.db import get_session
from llmobserve.storage.models import SpanSummary, Trace
from sqlmodel import delete
from llmobserve.tracing.enrichers import add_tenant_baggage

router = APIRouter()
repo = SpanRepository()


class SimulateAgentRequest(BaseModel):
    """Request model for simulate agent endpoint."""
    workflow_name: Optional[str] = None


@router.post("/run")
async def demo_run(
    x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id"),
):
    """Run demo agent workflow with 2 tool calls."""
    tenant_id = x_tenant_id or "default"
    add_tenant_baggage(tenant_id)

    try:
        trace_id = await run_agent_workflow()
        return {"status": "success", "trace_id": trace_id, "tenant_id": tenant_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fake_app")
async def demo_fake_app(
    x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id"),
):
    """Run fake app with GPT calls (no manual spans - validates auto-instrumentation)."""
    tenant_id = x_tenant_id or "default"
    add_tenant_baggage(tenant_id)

    try:
        await run_fake_app()
        return {"status": "success", "message": "Fake app executed - check traces", "tenant_id": tenant_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate-agent")
async def simulate_agent(
    request: SimulateAgentRequest,
    x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id"),
):
    """Run simulated agent workflow with GPT → Pinecone → GPT flow."""
    tenant_id = x_tenant_id or "default"
    add_tenant_baggage(tenant_id)

    try:
        result = await simulate_agent_workflow()
        
        # Get trace_id from the most recent trace (auto-created by instrumentation)
        import asyncio
        await asyncio.sleep(1)  # Wait for spans to be written
        
        traces = repo.get_traces(limit=1)
        trace_id = traces[0].trace_id if traces else None
        workflow_name = traces[0].workflow_name if traces else None
        
        return {
            "status": "success",
            "trace_id": trace_id,
            "workflow_name": workflow_name,
            "tenant_id": tenant_id,
            "outputs": {
                "query": result["query"],
                "retrieval_count": len(result["retrieval"]) if isinstance(result["retrieval"], list) else 0,
                "summary": result["summary"],
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gmail-workflow")
async def demo_gmail_workflow(
    x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id"),
):
    """Run Gmail workflow: List emails → Get details → GPT summary."""
    tenant_id = x_tenant_id or "default"
    add_tenant_baggage(tenant_id)

    try:
        result = await gmail_workflow()
        
        import asyncio
        await asyncio.sleep(1)
        
        traces = repo.get_traces(limit=1)
        trace_id = traces[0].trace_id if traces else None
        workflow_name = traces[0].workflow_name if traces else None
        
        return {
            "status": "success",
            "trace_id": trace_id,
            "workflow_name": workflow_name,
            "tenant_id": tenant_id,
            "result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calendar-workflow")
async def demo_calendar_workflow(
    x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id"),
):
    """Run Google Calendar workflow: List events → Create → Update with GPT."""
    tenant_id = x_tenant_id or "default"
    add_tenant_baggage(tenant_id)

    try:
        result = await calendar_workflow()
        
        import asyncio
        await asyncio.sleep(1)
        
        traces = repo.get_traces(limit=1)
        trace_id = traces[0].trace_id if traces else None
        workflow_name = traces[0].workflow_name if traces else None
        
        return {
            "status": "success",
            "trace_id": trace_id,
            "workflow_name": workflow_name,
            "tenant_id": tenant_id,
            "result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vapi-workflow")
async def demo_vapi_workflow(
    x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id"),
):
    """Run Vapi workflow: Create call → Check status → GPT summary."""
    tenant_id = x_tenant_id or "default"
    add_tenant_baggage(tenant_id)

    try:
        result = await vapi_workflow()
        
        import asyncio
        await asyncio.sleep(1)
        
        traces = repo.get_traces(limit=1)
        trace_id = traces[0].trace_id if traces else None
        workflow_name = traces[0].workflow_name if traces else None
        
        return {
            "status": "success",
            "trace_id": trace_id,
            "workflow_name": workflow_name,
            "tenant_id": tenant_id,
            "result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-all-workflows")
async def demo_run_all_workflows(
    x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id"),
):
    """Run all workflows: Gmail → Calendar → Vapi."""
    tenant_id = x_tenant_id or "default"
    add_tenant_baggage(tenant_id)

    try:
        result = await run_all_workflows()
        
        import asyncio
        await asyncio.sleep(2)  # Wait longer for all workflows
        
        traces = repo.get_traces(limit=4)  # Get last 4 traces (3 workflows + 1 parent)
        trace_id = traces[0].trace_id if traces else None
        workflow_name = traces[0].workflow_name if traces else None
        
        return {
            "status": "success",
            "trace_id": trace_id,
            "workflow_name": workflow_name,
            "tenant_id": tenant_id,
            "result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complex-workflows")
async def demo_complex_workflows(
    x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id"),
):
    """Run all complex nested workflows: GPT+Vapi+Google, Vapi+Google+Pinecone, nested, parallel, deeply nested."""
    tenant_id = x_tenant_id or "default"
    add_tenant_baggage(tenant_id)

    try:
        result = await run_all_complex_workflows()
        
        import asyncio
        await asyncio.sleep(3)  # Wait longer for all complex workflows
        
        traces = repo.get_traces(limit=10)  # Get last 10 traces (5 workflows + nested ones)
        trace_ids = [t.trace_id for t in traces[:5]] if traces else []
        workflow_names = [t.workflow_name for t in traces[:5]] if traces else []
        
        return {
            "status": "success",
            "trace_ids": trace_ids,
            "workflow_names": workflow_names,
            "tenant_id": tenant_id,
            "result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complex-workflows/{workflow_num}")
async def demo_complex_workflow_single(
    workflow_num: int,
    x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id"),
):
    """Run a specific complex workflow by number (1-5)."""
    tenant_id = x_tenant_id or "default"
    add_tenant_baggage(tenant_id)

    workflows = {
        1: ("GPT + Vapi + Google Calendar", gpt_vapi_google_workflow),
        2: ("Vapi + Google Calendar + Pinecone", vapi_google_pinecone_workflow),
        3: ("Nested Async Workflow (MOST COMPLEX)", nested_async_workflow),
        4: ("Parallel Workflows", parallel_workflows_with_nesting),
        5: ("Deeply Nested Workflow", deeply_nested_workflow),
    }

    if workflow_num not in workflows:
        raise HTTPException(status_code=400, detail=f"Invalid workflow number: {workflow_num}. Valid options: 1-5")

    try:
        name, func = workflows[workflow_num]
        result = await func()
        
        import asyncio
        await asyncio.sleep(2)
        
        traces = repo.get_traces(limit=1)
        trace_id = traces[0].trace_id if traces else None
        workflow_name = traces[0].workflow_name if traces else None
        
        return {
            "status": "success",
            "trace_id": trace_id,
            "workflow_name": workflow_name,
            "workflow_description": name,
            "tenant_id": tenant_id,
            "result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-data")
async def demo_clear_data(
    x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id"),
):
    """Clear all spans and traces from the database."""
    tenant_id = x_tenant_id or "default"
    
    try:
        with get_session() as session:
            # Delete all spans
            spans_deleted = session.exec(delete(SpanSummary)).rowcount
            
            # Delete all traces
            traces_deleted = session.exec(delete(Trace)).rowcount
            
            session.commit()
        
        return {
            "status": "success",
            "message": "All data cleared",
            "spans_deleted": spans_deleted,
            "traces_deleted": traces_deleted,
            "tenant_id": tenant_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

