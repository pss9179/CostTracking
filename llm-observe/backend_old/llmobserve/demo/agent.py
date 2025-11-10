"""Agent workflow with root span and two tool calls."""

from opentelemetry import trace

from llmobserve.demo.tools import tool_reason, tool_search
from llmobserve.semantics import SPAN_NAME_AGENT_WORKFLOW, WORKFLOW_NAME
from llmobserve.tracing.otel_setup import get_tracer

tracer = get_tracer(__name__)


async def run_agent_workflow() -> str:
    """
    Run agent workflow with root span and two tool calls.
    
    Returns:
        trace_id as hex string
    """
    with tracer.start_as_current_span(SPAN_NAME_AGENT_WORKFLOW) as root_span:
        root_span.set_attribute(WORKFLOW_NAME, "demo_agent")
        root_span.set_attribute("agent.type", "demo")
        
        # Tool 1: Search
        search_result = await tool_search("OpenTelemetry Python")
        root_span.set_attribute("tool.search.result_length", len(search_result))
        
        # Tool 2: Reason
        reasoning_result = await tool_reason(
            "What is OpenTelemetry?",
            context=search_result[:200]  # Use search result as context
        )
        root_span.set_attribute("tool.reason.result_length", len(reasoning_result))
        
        # Return trace ID for reference
        trace_id = f"{root_span.get_span_context().trace_id:032x}"
        return trace_id

