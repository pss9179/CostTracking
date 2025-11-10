"""LangChain callback handler for tracking LLM usage and costs."""

import time
from typing import Any, Dict, List, Optional
from uuid import UUID

from langchain.callbacks.base import BaseCallbackHandler
from opentelemetry import baggage, trace
from opentelemetry.trace import Status, StatusCode

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


class AgentObserveHandler(LLMObserveHandler):
    """
    Extended handler that creates organizational OpenTelemetry spans for agent reasoning steps.
    
    Creates a hierarchical span structure:
    - Agent span (wraps entire agent execution)
    - Step spans (each reasoning step)
    - ToolCall spans (each tool invocation)
    - LLM spans (handled by parent class)
    - AgentSummary span (summary at end)
    
    These are "meta spans" for visualization only - cost tracking remains unchanged.
    """

    def __init__(self, agent_name: Optional[str] = None):
        """
        Initialize agent observer handler.
        
        Args:
            agent_name: Optional agent name (will try to extract from metadata if not provided)
        """
        super().__init__()
        self._agent_name = agent_name
        self._agent_tracer = trace.get_tracer("llmobserve.agent")
        
        # Track active spans for proper nesting
        self._active_spans: Dict[UUID, trace.Span] = {}
        self._agent_span: Optional[trace.Span] = None
        self._step_spans: Dict[UUID, trace.Span] = {}
        self._tool_spans: Dict[UUID, trace.Span] = {}
        
        # Statistics for AgentSummary
        self._total_cost: float = 0.0
        self._total_duration_ms: float = 0.0
        self._llm_call_count: int = 0
        self._tool_call_count: int = 0
        self._step_count: int = 0
        self._agent_start_time: Optional[float] = None
        
    def _get_agent_name(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Extract agent name from metadata or use default."""
        if self._agent_name:
            return self._agent_name
        
        if metadata:
            agent_type = metadata.get("agent_type")
            if agent_type:
                # Convert snake_case to TitleCase
                return "".join(word.capitalize() for word in agent_type.split("_"))
        
        # Try to get from current span attributes
        current_span = trace.get_current_span()
        if current_span:
            agent_type = current_span.attributes.get("agent_type")
            if agent_type:
                return "".join(word.capitalize() for word in str(agent_type).split("_"))
        
        return "Agent"
    
    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Called when a chain (agent step) starts.
        
        Creates:
        - Agent span on first chain start (if not exists)
        - Step span for each reasoning step
        """
        try:
            chain_name = serialized.get("name", "unknown")
            
            # Check if this is the top-level agent executor (no parent_run_id)
            if chain_name == "AgentExecutor" and parent_run_id is None and self._agent_span is None:
                # Create agent-level span
                agent_name = self._get_agent_name(metadata)
                self._agent_start_time = time.time()
                
                # Get current context (should be workflow span)
                current_ctx = trace.context_api.get_current()
                
                # Create agent span with proper context (will nest under workflow span)
                self._agent_span = self._agent_tracer.start_span(
                    f"Agent: {agent_name}",
                    context=current_ctx,
                    attributes={
                        "agent.name": agent_name,
                        "agent.type": metadata.get("agent_type", "unknown") if metadata else "unknown",
                    }
                )
                self._active_spans[run_id] = self._agent_span
            
            # Create step span for reasoning steps (LLMChain or nested AgentExecutor calls)
            elif chain_name in ["LLMChain", "AgentExecutor"] and self._agent_span is not None and parent_run_id is not None:
                # This is a reasoning step (has a parent, so it's nested)
                step_num = self._step_count + 1
                # Create step span nested under agent span
                step_ctx = trace.set_span_in_context(self._agent_span)
                step_span = self._agent_tracer.start_span(
                    f"AgentStep",
                    context=step_ctx,
                    attributes={
                        "step.number": step_num,
                        "step.name": chain_name,
                    }
                )
                self._step_spans[run_id] = step_span
                self._step_count += 1
            
            # Call parent for cost tracking
            super().on_chain_start(serialized, inputs, run_id=run_id, parent_run_id=parent_run_id, tags=tags, metadata=metadata, **kwargs)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in AgentObserveHandler.on_chain_start: {e}", exc_info=True)
    
    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """
        Called when a chain (agent step) ends.
        
        Ends the step span and updates statistics.
        """
        try:
            # End step span if exists
            if run_id in self._step_spans:
                step_span = self._step_spans.pop(run_id)
                step_span.end()
            
            # If this is the agent executor ending and we haven't created summary yet
            # (fallback in case on_agent_finish isn't called)
            if run_id in self._active_spans and self._active_spans[run_id] == self._agent_span:
                # Agent executor is ending - create summary if not already done
                if self._agent_span is not None:
                    self._create_agent_summary(outputs)
            
            # Call parent for cost tracking
            super().on_chain_end(outputs, run_id=run_id, parent_run_id=parent_run_id, **kwargs)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in AgentObserveHandler.on_chain_end: {e}", exc_info=True)
    
    def _create_agent_summary(self, outputs: Optional[Dict[str, Any]] = None) -> None:
        """Create AgentSummary span and end agent span."""
        if self._agent_span is None:
            return
        
        # Calculate total duration
        if self._agent_start_time:
            self._total_duration_ms = (time.time() - self._agent_start_time) * 1000
        
        # Get final output
        final_output = ""
        if outputs:
            final_output = str(outputs.get("output", outputs.get("return_values", {}).get("output", "")))[:200]
        
        # Create AgentSummary span (nested under agent span)
        summary_ctx = trace.set_span_in_context(self._agent_span)
        summary_span = self._agent_tracer.start_span(
            "AgentSummary",
            context=summary_ctx,
            attributes={
                "agent.total_cost_usd": self._total_cost,
                "agent.total_duration_ms": self._total_duration_ms,
                "agent.llm_call_count": self._llm_call_count,
                "agent.tool_call_count": self._tool_call_count,
                "agent.step_count": self._step_count,
                "agent.final_output": final_output,
            }
        )
        summary_span.end()
        
        # End agent span
        self._agent_span.end()
        self._agent_span = None
    
    def on_chain_error(
        self,
        error: Exception,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when chain errors - end span and record error."""
        try:
            if run_id in self._step_spans:
                step_span = self._step_spans.pop(run_id)
                step_span.record_exception(error)
                step_span.set_status(Status(StatusCode.ERROR, str(error)))
                step_span.end()
            
            super().on_chain_error(error, run_id=run_id, parent_run_id=parent_run_id, **kwargs)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in AgentObserveHandler.on_chain_error: {e}", exc_info=True)
    
    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Called when tool starts.
        
        Creates a ToolCall span for visualization.
        """
        try:
            tool_name = serialized.get("name", "unknown")
            
            # Get current span (should be step span or agent span)
            current_span = trace.get_current_span()
            if not current_span:
                # Fallback to agent span
                current_span = self._agent_span
            
            # Create tool call span nested under current span
            tool_ctx = trace.set_span_in_context(current_span) if current_span else None
            tool_span = self._agent_tracer.start_span(
                f"ToolCall: {tool_name}",
                context=tool_ctx,
                attributes={
                    "tool.name": tool_name,
                    "tool.input": str(input_str)[:200],  # Truncate long inputs
                }
            )
            self._tool_spans[run_id] = tool_span
            self._tool_call_count += 1
            
            # Call parent for cost tracking
            super().on_tool_start(serialized, input_str, run_id=run_id, parent_run_id=parent_run_id, tags=tags, metadata=metadata, **kwargs)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in AgentObserveHandler.on_tool_start: {e}", exc_info=True)
    
    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """
        Called when tool ends.
        
        Ends the ToolCall span and updates statistics.
        """
        try:
            # End tool span if exists
            if run_id in self._tool_spans:
                tool_span = self._tool_spans.pop(run_id)
                tool_span.set_attribute("tool.output", str(output)[:200])  # Truncate long outputs
                tool_span.end()
            
            # Call parent for cost tracking
            super().on_tool_end(output, run_id=run_id, parent_run_id=parent_run_id, **kwargs)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in AgentObserveHandler.on_tool_end: {e}", exc_info=True)
    
    def on_tool_error(
        self,
        error: Exception,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when tool errors - end span and record error."""
        try:
            if run_id in self._tool_spans:
                tool_span = self._tool_spans.pop(run_id)
                tool_span.record_exception(error)
                tool_span.set_status(Status(StatusCode.ERROR, str(error)))
                tool_span.end()
            
            super().on_tool_error(error, run_id=run_id, parent_run_id=parent_run_id, **kwargs)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in AgentObserveHandler.on_tool_error: {e}", exc_info=True)
    
    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """
        Called when LLM ends.
        
        Updates statistics and calls parent for cost tracking.
        """
        try:
            # Update statistics
            self._llm_call_count += 1
            
            # Extract cost from kwargs if available
            llm_output = kwargs.get("llm_output", {})
            prompt_tokens = llm_output.get("token_usage", {}).get("prompt_tokens", 0)
            completion_tokens = llm_output.get("token_usage", {}).get("completion_tokens", 0)
            model_name = kwargs.get("model_name") or llm_output.get("model_name")
            
            if model_name and prompt_tokens > 0:
                cost = pricing_registry.cost_for(model_name, prompt_tokens, completion_tokens)
                self._total_cost += cost
            
            # Call parent for cost tracking
            super().on_llm_end(response, **kwargs)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in AgentObserveHandler.on_llm_end: {e}", exc_info=True)
    
    def on_agent_finish(
        self,
        finish: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """
        Called when agent finishes.
        
        Creates AgentSummary span and ends agent span.
        """
        try:
            if self._agent_span is None:
                return
            
            # Create summary with finish data
            self._create_agent_summary(finish.get("return_values", {}))
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in AgentObserveHandler.on_agent_finish: {e}", exc_info=True)

