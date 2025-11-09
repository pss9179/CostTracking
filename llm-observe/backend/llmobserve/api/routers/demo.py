"""Demo endpoints for agent workflow and fake app."""

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional

from llmobserve.demo.agent import run_agent_workflow
from llmobserve.demo.fake_app import run_fake_app
from llmobserve.demo.simulate_agent import simulate_agent_workflow
from llmobserve.storage.repo import SpanRepository
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

