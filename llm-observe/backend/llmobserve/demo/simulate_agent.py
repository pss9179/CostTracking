"""Agent workflow simulation with GPT and Pinecone calls."""

import os
from typing import Optional

from opentelemetry import trace

from llmobserve.config import settings
from llmobserve.demo.utils import infer_workflow_name
from llmobserve.semantics import SPAN_NAME_AGENT_WORKFLOW, WORKFLOW_NAME
from llmobserve.tracing.otel_setup import get_tracer

# Get enricher from storage (avoid circular import)
from llmobserve.storage.repo import SpanRepository
from llmobserve.tracing.enrichers import SpanEnricher

# Create enricher instance (will use same repo as main app)
_span_repo = SpanRepository()
_span_enricher = SpanEnricher(span_repo=_span_repo)

tracer = get_tracer(__name__)


async def simulate_agent_workflow(workflow_name: Optional[str] = None) -> dict:
    """
    Simulate an agent workflow with GPT → Pinecone → GPT flow.
    
    Args:
        workflow_name: Optional workflow name. If not provided, auto-inferred.
    
    Returns:
        Dictionary with trace_id, workflow_name, and simulated outputs
    """
    # Auto-infer workflow name if not provided
    if not workflow_name:
        workflow_name = infer_workflow_name()
    
    import time
    start_time = time.time()
    
    with tracer.start_as_current_span(SPAN_NAME_AGENT_WORKFLOW) as root_span:
        root_span.set_attribute(WORKFLOW_NAME, workflow_name)
        root_span.set_attribute("agent.type", "simulated")
        root_span.set_attribute("workflow.simulation", True)
        
        # Step 1: GPT call for query generation
        query_result = await _generate_query("What is machine learning?")
        root_span.set_attribute("step.query_generation.result_length", len(query_result))
        
        # Step 2: Pinecone query
        retrieval_result = await _query_pinecone(query_result)
        root_span.set_attribute("step.pinecone_query.result_count", len(retrieval_result) if isinstance(retrieval_result, list) else 1)
        
        # Step 3: GPT call for summarization
        summary_result = await _summarize_results(query_result, retrieval_result)
        root_span.set_attribute("step.summarization.result_length", len(summary_result))
        
        # Calculate root span duration and cost (sum of all child spans)
        duration_ms = (time.time() - start_time) * 1000
        
        # Get all child spans to calculate total cost
        # Note: Child spans are written async, so we'll calculate from spans later
        # For now, write root span with 0 cost (will be updated during aggregation)
        
        # Write root span to database
        span_context = root_span.get_span_context()
        if span_context.is_valid:
            from opentelemetry import baggage
            from llmobserve.semantics import WORKFLOW_TENANT_ID
            
            tenant_id = baggage.get_baggage(WORKFLOW_TENANT_ID) or "default"
            
            root_span_summary = {
                "trace_id": f"{span_context.trace_id:032x}",
                "span_id": f"{span_context.span_id:016x}",
                "parent_span_id": None,  # Root span has no parent
                "name": root_span.name,
                "model": None,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "cost_usd": 0.0,  # Will be calculated from children during aggregation
                "start_time": root_span.start_time / 1e9,
                "duration_ms": duration_ms,
                "tenant_id": tenant_id,
            }
            _span_repo.create_span_summary(root_span_summary)
        
        # Return trace ID and results
        trace_id = f"{root_span.get_span_context().trace_id:032x}"
        return {
            "trace_id": trace_id,
            "workflow_name": workflow_name,
            "query": query_result,
            "retrieval": retrieval_result,
            "summary": summary_result,
        }


async def _generate_query(topic: str) -> str:
    """Generate a search query using GPT. Auto-instrumented spans will be created."""
    try:
        import openai
        
        client = openai.OpenAI(api_key=settings.openai_api_key)
        
        # The auto-instrumentor will create an llm.request span that inherits from the root span
        # Users can rename it in the frontend to "GPT Query Generation" or similar
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a search query generator. Generate concise search queries."},
                {"role": "user", "content": f"Generate a search query for: {topic}"},
            ],
            max_tokens=50,
        )
        
        result = response.choices[0].message.content
        return result
    except ImportError:
        return f"[Mock query for: {topic}]"
    except Exception as e:
        return f"[Query generation error: {str(e)}]"


async def _query_pinecone(query: str) -> list:
    """Query Pinecone index. The Pinecone instrumentor will automatically create spans."""
    try:
        from pinecone import Pinecone
        
        # Initialize Pinecone client
        pc = Pinecone(api_key=settings.pinecone_api_key)
        
        # Use index name from settings
        index_name = settings.pinecone_index_name or "test"
        
        # Get index - the instrumentor will automatically wrap query/upsert/delete methods
        index = pc.Index(index_name)
        
        # Use dimension 1024 (we know this from the index setup)
        dimension = 1024
        
        # Generate a simple embedding vector (mock - in production use real embeddings)
        import random
        vector = [random.random() for _ in range(dimension)]
        
        # Query Pinecone (run in executor to avoid blocking async event loop)
        # The instrumentor will automatically create a span for this call
        # We need to propagate OpenTelemetry context AND baggage into the thread pool
        import asyncio
        from opentelemetry import context, baggage
        from llmobserve.semantics import WORKFLOW_TENANT_ID
        
        # Capture current OpenTelemetry context and baggage
        otel_context = context.get_current()
        tenant_id = baggage.get_baggage(WORKFLOW_TENANT_ID) or "default"
        
        def query_with_context():
            # Restore OpenTelemetry context in the thread
            token = context.attach(otel_context)
            try:
                # Restore baggage (tenant_id) in the thread
                if tenant_id:
                    baggage.set_baggage(WORKFLOW_TENANT_ID, tenant_id)
                return index.query(
                    vector=vector,
                    top_k=3,
                    include_metadata=True
                )
            finally:
                context.detach(token)
        
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, query_with_context)
        
        # Extract matches
        matches = results.get("matches", [])
        return matches
    except ImportError:
        # Pinecone library not installed
        return [{"id": "mock1", "score": 0.9, "metadata": {"text": "Mock Pinecone result"}}]
    except Exception as e:
        # If query fails, return mock results
        # The instrumentor should have already created an error span
        return [
            {"id": "doc1", "score": 0.95, "metadata": {"text": f"Mock result for: {query[:50]}"}},
            {"id": "doc2", "score": 0.87, "metadata": {"text": "Mock result 2"}},
        ]


async def _summarize_results(query: str, retrieval_results: list) -> str:
    """Summarize retrieval results using GPT. Auto-instrumented spans will be created."""
    try:
        import openai
        
        client = openai.OpenAI(api_key=settings.openai_api_key)
        
        # Build context from retrieval results
        context = "\n".join([
            result.get("metadata", {}).get("text", str(result))
            for result in retrieval_results[:3]
        ])
        
        # The auto-instrumentor will create an llm.request span that inherits from the root span
        # Users can rename it in the frontend to "GPT Summarization" or similar
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a summarization assistant. Provide concise summaries."},
                {"role": "user", "content": f"Query: {query}\n\nContext:\n{context[:500]}\n\nSummarize the key points."},
            ],
            max_tokens=150,
        )
        
        result = response.choices[0].message.content
        return result
    except ImportError:
        return f"[Mock summary for query: {query[:50]}]"
    except Exception as e:
        return f"[Summarization error: {str(e)}]"
