"""LangChain callback handler for tracking LLM usage and costs."""

import time
from typing import Any, Dict, List, Optional

from langchain.callbacks.base import BaseCallbackHandler
from opentelemetry import baggage

from llmobserve.exporter import get_exporter
from llmobserve.pricing import pricing_registry
from llmobserve.tracer import get_current_trace_id, get_current_span_id


class LLMObserveHandler(BaseCallbackHandler):
    """Callback handler that tracks LLM calls and records cost events."""

    def __init__(self):
        """Initialize handler."""
        super().__init__()
        self._exporter = get_exporter()

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any,
    ) -> None:
        """Called when LLM starts."""
        pass

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """
        Called when LLM ends - extract usage and record cost.

        Args:
            response: LLM response object with usage information
            **kwargs: Additional arguments
        """
        try:
            # Extract usage from response
            llm_output = kwargs.get("llm_output", {})
            
            # Get token usage
            prompt_tokens = llm_output.get("token_usage", {}).get("prompt_tokens", 0)
            completion_tokens = llm_output.get("token_usage", {}).get("completion_tokens", 0)
            total_tokens = llm_output.get("token_usage", {}).get("total_tokens", 0)
            
            # Get model name
            model_name = kwargs.get("model_name") or llm_output.get("model_name")
            if not model_name:
                # Try to extract from serialized
                serialized = kwargs.get("serialized", {})
                model_name = serialized.get("id", [None])[-1] if isinstance(serialized.get("id"), list) else None
            
            # Get provider (default to openai)
            provider = kwargs.get("provider", "openai")
            
            # Calculate cost
            if model_name and prompt_tokens > 0:
                cost_usd = pricing_registry.cost_for(model_name, prompt_tokens, completion_tokens)
            else:
                cost_usd = 0.0
            
            # Get duration
            duration_ms = kwargs.get("duration_ms", 0.0)
            if duration_ms == 0.0:
                # Try to calculate from start/end times
                start_time = kwargs.get("start_time")
                end_time = kwargs.get("end_time")
                if start_time and end_time:
                    duration_ms = (end_time - start_time) * 1000
            
            # Get tenant and workflow from context
            tenant_id = baggage.get_baggage("tenant_id") or "default"
            workflow_id = baggage.get_baggage("workflow_id")
            
            # Get trace/span IDs
            trace_id = get_current_trace_id()
            span_id = get_current_span_id()
            
            # Record cost event
            self._exporter.record_cost(
                tenant_id=tenant_id,
                provider=provider,
                cost_usd=cost_usd,
                duration_ms=duration_ms,
                workflow_id=workflow_id,
                model=model_name,
                trace_id=trace_id,
                span_id=span_id,
                prompt_tokens=prompt_tokens if prompt_tokens > 0 else None,
                completion_tokens=completion_tokens if completion_tokens > 0 else None,
                total_tokens=total_tokens if total_tokens > 0 else None,
                operation="llm",
            )
        except Exception as e:
            # Don't crash on errors
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in LLMObserveHandler.on_llm_end: {e}", exc_info=True)

    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when LLM errors."""
        pass

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        """Called when tool starts."""
        pass

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """
        Called when tool ends - track tool usage.

        Args:
            output: Tool output
            **kwargs: Additional arguments
        """
        try:
            # Get tool name
            tool_name = kwargs.get("name", "unknown")
            
            # Get duration
            duration_ms = kwargs.get("duration_ms", 0.0)
            
            # Get tenant and workflow
            tenant_id = baggage.get_baggage("tenant_id") or "default"
            workflow_id = baggage.get_baggage("workflow_id")
            
            # Get trace/span IDs
            trace_id = get_current_trace_id()
            span_id = get_current_span_id()
            
            # Record tool usage (no cost for tools, but track duration)
            self._exporter.record_cost(
                tenant_id=tenant_id,
                provider="tool",
                cost_usd=0.0,
                duration_ms=duration_ms,
                workflow_id=workflow_id,
                model=tool_name,
                trace_id=trace_id,
                span_id=span_id,
                operation="tool",
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in LLMObserveHandler.on_tool_end: {e}", exc_info=True)

    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when tool errors."""
        pass

