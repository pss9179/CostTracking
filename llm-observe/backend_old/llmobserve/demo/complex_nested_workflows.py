"""
Complex nested agent workflows for testing workflow tracing.

This file contains multiple complex workflows with:
- GPT + Vapi + Google Calendar combinations
- Vapi + Google Calendar + Pinecone combinations  
- Nested workflows with async operations
- Complex async nesting scenarios

Expected Flow Mappings:
=======================

Workflow 1: gpt_vapi_google_workflow
  workflow.gpt_vapi_google_workflow (root)
    ├── llm.request (GPT: analyze call purpose)
    ├── vapi.create_call
    ├── vapi.get_call_status
    ├── llm.request (GPT: generate summary)
    └── gcal.create_event

Workflow 2: vapi_google_pinecone_workflow
  workflow.vapi_google_pinecone_workflow (root)
    ├── vapi.create_call
    ├── gcal.list_events
    ├── llm.request (GPT: generate search query)
    ├── pinecone.query
    └── llm.request (GPT: summarize results)

Workflow 3: nested_async_workflow (MOST COMPLEX)
  workflow.nested_async_workflow (root)
    ├── llm.request (GPT: initial analysis)
    ├── workflow.gpt_vapi_google_workflow (nested workflow)
    │   ├── llm.request (GPT: analyze call purpose)
    │   ├── vapi.create_call
    │   ├── vapi.get_call_status
    │   ├── llm.request (GPT: generate summary)
    │   └── gcal.create_event
    ├── workflow.vapi_google_pinecone_workflow (nested workflow)
    │   ├── vapi.create_call
    │   ├── gcal.list_events
    │   ├── llm.request (GPT: generate search query)
    │   ├── pinecone.query
    │   └── llm.request (GPT: summarize results)
    └── llm.request (GPT: final synthesis)

Workflow 4: parallel_workflows_with_nesting
  workflow.parallel_workflows_with_nesting (root)
    ├── workflow.gpt_vapi_google_workflow (parallel task 1)
    │   ├── llm.request (GPT: analyze call purpose)
    │   ├── vapi.create_call
    │   ├── vapi.get_call_status
    │   ├── llm.request (GPT: generate summary)
    │   └── gcal.create_event
    └── workflow.vapi_google_pinecone_workflow (parallel task 2)
        ├── vapi.create_call
        ├── gcal.list_events
        ├── llm.request (GPT: generate search query)
        ├── pinecone.query
        └── llm.request (GPT: summarize results)

Workflow 5: deeply_nested_workflow
  workflow.deeply_nested_workflow (root)
    ├── llm.request (GPT: initial query)
    ├── workflow.helper_workflow_level_1 (nested level 1)
    │   ├── workflow.helper_workflow_level_2 (nested level 2)
    │   │   ├── llm.request (GPT: inner analysis)
    │   │   └── vapi.create_call
    │   └── gcal.create_event
    └── pinecone.query
"""

import asyncio
from typing import Dict, List

import openai
from pinecone import Pinecone
from llmobserve.config import settings
from llmobserve.tracing.function_tracer import workflow_trace

# Import mock clients from multi_workflows
from llmobserve.demo.multi_workflows import MockVapiClient, MockCalendarClient


# Mock Pinecone client for testing
class MockPineconeClient:
    """Mock Pinecone client for testing."""
    
    @staticmethod
    async def query(vector: List[float], top_k: int = 3, include_metadata: bool = True) -> Dict:
        """Mock query API call - creates a span for visualization."""
        from opentelemetry import trace
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("pinecone.query") as span:
            span.set_attribute("pinecone.top_k", top_k)
            span.set_attribute("pinecone.include_metadata", include_metadata)
            await asyncio.sleep(0.1)  # Simulate API latency
            return {
                "matches": [
                    {"id": "vec1", "score": 0.95, "metadata": {"text": "Sample document 1"}},
                    {"id": "vec2", "score": 0.89, "metadata": {"text": "Sample document 2"}},
                    {"id": "vec3", "score": 0.82, "metadata": {"text": "Sample document 3"}},
                ]
            }


@workflow_trace
async def gpt_vapi_google_workflow() -> Dict:
    """
    Workflow 1: GPT + Vapi + Google Calendar
    
    Flow: GPT analyzes → Vapi call → GPT summarizes → Calendar event created
    """
    vapi = MockVapiClient()
    calendar = MockCalendarClient()
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    # Step 1: Use GPT to analyze what kind of call should be made
    analysis_resp = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a call analysis assistant."},
            {"role": "user", "content": "Analyze: Should I make a call to discuss project status? What should the call be about?"}
        ],
        max_tokens=100,
        temperature=0.7,
    )
    analysis = analysis_resp.choices[0].message.content
    
    # Step 2: Create Vapi call based on analysis
    call = await vapi.create_call(
        phone_number="+1234567890",
        assistant_id="assistant_123"
    )
    
    # Step 3: Check call status
    status = await vapi.get_call_status(call["call_id"])
    
    # Step 4: Use GPT to generate a summary of the call
    summary_resp = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a call summarization assistant."},
            {"role": "user", "content": f"Generate a summary for a call that lasted {status.get('duration', 0)} seconds. Original analysis: {analysis}"}
        ],
        max_tokens=100,
        temperature=0.7,
    )
    call_summary = summary_resp.choices[0].message.content
    
    # Step 5: Create calendar event based on call summary
    event = await calendar.create_event(
        summary=f"Follow-up: {call_summary[:50]}" if call_summary else "Call Follow-up",
        start_time="2024-01-15T14:00:00Z",
        end_time="2024-01-15T15:00:00Z"
    )
    
    return {
        "workflow": "gpt_vapi_google_workflow",
        "sequence": "gpt → vapi → gpt → gcal",
        "analysis": analysis,
        "call_id": call["call_id"],
        "call_summary": call_summary,
        "calendar_event": event,
    }


@workflow_trace
async def vapi_google_pinecone_workflow() -> Dict:
    """
    Workflow 2: Vapi + Google Calendar + Pinecone
    
    Flow: Vapi call → Calendar check → GPT query → Pinecone search → GPT summarize
    """
    vapi = MockVapiClient()
    calendar = MockCalendarClient()
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    # Step 1: Create Vapi call
    call = await vapi.create_call(
        phone_number="+1987654321",
        assistant_id="assistant_456"
    )
    
    # Step 2: Check calendar events
    events = await calendar.list_events(calendar_id="primary", max_results=10)
    
    # Step 3: Use GPT to generate a search query based on calendar events
    query_resp = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a search query generator."},
            {"role": "user", "content": f"Based on these calendar events: {events}, generate a search query to find relevant information."}
        ],
        max_tokens=50,
        temperature=0.7,
    )
    search_query = query_resp.choices[0].message.content
    
    # Step 4: Query Pinecone (using mock for testing, but real one would work too)
    if settings.pinecone_api_key:
        try:
            index = Pinecone(api_key=settings.pinecone_api_key).Index(settings.pinecone_index_name or "test")
            pinecone_results = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: index.query(vector=[0.0] * 1024, top_k=3, include_metadata=True)
            )
        except Exception:
            # Fallback to mock if real Pinecone fails
            mock_pinecone = MockPineconeClient()
            pinecone_results = await mock_pinecone.query([0.0] * 1024, top_k=3)
    else:
        # Use mock if no API key
        mock_pinecone = MockPineconeClient()
        pinecone_results = await mock_pinecone.query([0.0] * 1024, top_k=3)
    
    # Step 5: Use GPT to summarize the Pinecone results
    context = "\n".join([
        m.get("metadata", {}).get("text", str(m)) 
        for m in pinecone_results.get("matches", [])[:3]
    ])
    
    summary_resp = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a summarization assistant."},
            {"role": "user", "content": f"Query: {search_query}\n\nContext:\n{context[:500]}\n\nSummarize the key points."}
        ],
        max_tokens=150,
        temperature=0.5,
    )
    summary = summary_resp.choices[0].message.content
    
    return {
        "workflow": "vapi_google_pinecone_workflow",
        "sequence": "vapi → gcal → gpt → pinecone → gpt",
        "call_id": call["call_id"],
        "events_found": len(events),
        "search_query": search_query,
        "pinecone_results": pinecone_results.get("matches", []),
        "summary": summary,
    }


@workflow_trace
async def nested_async_workflow() -> Dict:
    """
    Workflow 3: Nested workflows with async operations (MOST COMPLEX)
    
    Flow: GPT analysis → Nested workflow 1 (GPT+Vapi+Google) → Nested workflow 2 (Vapi+Google+Pinecone) → GPT synthesis
    
    This tests nested workflow tracing where workflows call other workflows.
    """
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    # Step 1: Initial GPT analysis
    initial_resp = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a workflow orchestrator."},
            {"role": "user", "content": "Analyze what workflows should be executed: 1) Call management workflow, 2) Search and retrieval workflow"}
        ],
        max_tokens=100,
        temperature=0.7,
    )
    initial_analysis = initial_resp.choices[0].message.content
    
    # Step 2: Execute nested workflow 1 (GPT + Vapi + Google)
    nested_result_1 = await gpt_vapi_google_workflow()
    
    # Step 3: Execute nested workflow 2 (Vapi + Google + Pinecone)
    nested_result_2 = await vapi_google_pinecone_workflow()
    
    # Step 4: Final GPT synthesis combining both workflows
    synthesis_resp = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a synthesis assistant."},
            {"role": "user", "content": f"Initial analysis: {initial_analysis}\n\nWorkflow 1 results: {nested_result_1}\n\nWorkflow 2 results: {nested_result_2}\n\nSynthesize the key outcomes."}
        ],
        max_tokens=200,
        temperature=0.7,
    )
    synthesis = synthesis_resp.choices[0].message.content
    
    return {
        "workflow": "nested_async_workflow",
        "sequence": "gpt → [nested: gpt+vapi+gcal] → [nested: vapi+gcal+pinecone] → gpt",
        "initial_analysis": initial_analysis,
        "nested_workflow_1": nested_result_1,
        "nested_workflow_2": nested_result_2,
        "final_synthesis": synthesis,
    }


@workflow_trace
async def parallel_workflows_with_nesting() -> Dict:
    """
    Workflow 4: Parallel workflows executed concurrently
    
    Flow: Run workflow 1 and workflow 2 in parallel, then combine results
    
    This tests async parallel execution of workflows.
    """
    # Execute both workflows in parallel
    results = await asyncio.gather(
        gpt_vapi_google_workflow(),
        vapi_google_pinecone_workflow(),
    )
    
    workflow_1_result = results[0]
    workflow_2_result = results[1]
    
    return {
        "workflow": "parallel_workflows_with_nesting",
        "sequence": "parallel([gpt+vapi+gcal], [vapi+gcal+pinecone])",
        "workflow_1": workflow_1_result,
        "workflow_2": workflow_2_result,
    }


@workflow_trace
async def helper_workflow_level_2() -> Dict:
    """
    Helper workflow level 2: Used for deep nesting tests
    """
    vapi = MockVapiClient()
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    # GPT analysis
    analysis_resp = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helper assistant."},
            {"role": "user", "content": "Analyze: What should be done next?"}
        ],
        max_tokens=50,
        temperature=0.7,
    )
    analysis = analysis_resp.choices[0].message.content
    
    # Vapi call
    call = await vapi.create_call(
        phone_number="+1555555555",
        assistant_id="assistant_789"
    )
    
    return {
        "workflow": "helper_workflow_level_2",
        "analysis": analysis,
        "call_id": call["call_id"],
    }


@workflow_trace
async def helper_workflow_level_1() -> Dict:
    """
    Helper workflow level 1: Calls level 2, then creates calendar event
    """
    calendar = MockCalendarClient()
    
    # Call nested workflow level 2
    nested_result = await helper_workflow_level_2()
    
    # Create calendar event
    event = await calendar.create_event(
        summary=f"Follow-up from nested workflow: {nested_result.get('call_id', '')}",
        start_time="2024-01-20T10:00:00Z",
        end_time="2024-01-20T11:00:00Z"
    )
    
    return {
        "workflow": "helper_workflow_level_1",
        "nested_result": nested_result,
        "calendar_event": event,
    }


@workflow_trace
async def deeply_nested_workflow() -> Dict:
    """
    Workflow 5: Deeply nested workflows (3 levels deep)
    
    Flow: GPT query → Level 1 workflow → Level 2 workflow → Pinecone query
    
    This tests very deep nesting scenarios.
    """
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    # Step 1: Initial GPT query
    query_resp = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a query generator."},
            {"role": "user", "content": "Generate a query for deep workflow analysis"}
        ],
        max_tokens=50,
        temperature=0.7,
    )
    query = query_resp.choices[0].message.content
    
    # Step 2: Call level 1 workflow (which calls level 2)
    level_1_result = await helper_workflow_level_1()
    
    # Step 3: Query Pinecone
    if settings.pinecone_api_key:
        try:
            index = Pinecone(api_key=settings.pinecone_api_key).Index(settings.pinecone_index_name or "test")
            pinecone_results = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: index.query(vector=[0.0] * 1024, top_k=3, include_metadata=True)
            )
        except Exception:
            mock_pinecone = MockPineconeClient()
            pinecone_results = await mock_pinecone.query([0.0] * 1024, top_k=3)
    else:
        mock_pinecone = MockPineconeClient()
        pinecone_results = await mock_pinecone.query([0.0] * 1024, top_k=3)
    
    return {
        "workflow": "deeply_nested_workflow",
        "sequence": "gpt → [level1 → [level2 → gpt+vapi]] → pinecone",
        "query": query,
        "level_1_result": level_1_result,
        "pinecone_results": pinecone_results.get("matches", []),
    }


async def run_all_complex_workflows() -> Dict:
    """
    Run all complex workflows sequentially.
    
    NOTE: This function is NOT wrapped with @workflow_trace because each
    individual workflow should have its own separate trace.
    """
    results = {}
    
    print("Running Workflow 1: GPT + Vapi + Google Calendar...")
    results["workflow_1"] = await gpt_vapi_google_workflow()
    await asyncio.sleep(0.1)
    
    print("Running Workflow 2: Vapi + Google Calendar + Pinecone...")
    results["workflow_2"] = await vapi_google_pinecone_workflow()
    await asyncio.sleep(0.1)
    
    print("Running Workflow 3: Nested Async Workflow (MOST COMPLEX)...")
    results["workflow_3"] = await nested_async_workflow()
    await asyncio.sleep(0.1)
    
    print("Running Workflow 4: Parallel Workflows...")
    results["workflow_4"] = await parallel_workflows_with_nesting()
    await asyncio.sleep(0.1)
    
    print("Running Workflow 5: Deeply Nested Workflow...")
    results["workflow_5"] = await deeply_nested_workflow()
    
    return {
        "workflow": "run_all_complex_workflows",
        "total_workflows": 5,
        "workflow_descriptions": {
            "workflow_1": "GPT + Vapi + Google Calendar",
            "workflow_2": "Vapi + Google Calendar + Pinecone",
            "workflow_3": "Nested Async Workflow (calls workflows 1 & 2)",
            "workflow_4": "Parallel Workflows (workflows 1 & 2 in parallel)",
            "workflow_5": "Deeply Nested Workflow (3 levels deep)",
        },
        "results": results,
    }


if __name__ == "__main__":
    import asyncio
    
    async def main():
        results = await run_all_complex_workflows()
        print("\n" + "="*80)
        print("ALL WORKFLOWS COMPLETED")
        print("="*80)
        print(f"Total workflows executed: {results['total_workflows']}")
        print("\nCheck your tracing UI to see the workflow traces!")
    
    asyncio.run(main())

