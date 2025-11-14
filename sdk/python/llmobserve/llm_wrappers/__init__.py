"""
LLM wrappers for tool-calling workflows.

These wrappers extract tool_calls from LLM responses and create
proper span hierarchies for agent workflows. They complement the
existing instrumentors (which provide basic cost tracking).

Key differences:
- Instrumentors: Basic cost tracking for all LLM calls
- LLM Wrappers: Extract tool_calls metadata for agent workflows

Both can coexist. LLM wrappers take priority when both are active.
"""
from typing import Any, Optional
import logging

logger = logging.getLogger("llmobserve")

__all__ = [
    "wrap_openai_client",
    "wrap_anthropic_client",
]


def wrap_openai_client(client: Any) -> Any:
    """
    Wrap an OpenAI client to extract tool_calls from responses.
    
    Use this for agent workflows with tool calling to get proper
    tool_call metadata in LLM spans.
    
    Args:
        client: OpenAI client instance
    
    Returns:
        Wrapped client that extracts tool_calls
    
    Usage:
        import openai
        from llmobserve.llm_wrappers import wrap_openai_client
        
        client = openai.OpenAI(api_key="...")
        client = wrap_openai_client(client)
        
        # Now tool_calls will be extracted and attached to spans
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[...],
            tools=[...]
        )
    """
    try:
        from llmobserve.llm_wrappers.openai_wrapper import wrap_openai_client as _wrap
        return _wrap(client)
    except Exception as e:
        logger.warning(f"[llmobserve] Failed to wrap OpenAI client: {e}")
        return client  # Return unwrapped client (graceful degradation)


def wrap_anthropic_client(client: Any) -> Any:
    """
    Wrap an Anthropic client to extract tool_use from responses.
    
    Use this for agent workflows with tool calling to get proper
    tool_use metadata in LLM spans.
    
    Args:
        client: Anthropic client instance
    
    Returns:
        Wrapped client that extracts tool_use
    
    Usage:
        import anthropic
        from llmobserve.llm_wrappers import wrap_anthropic_client
        
        client = anthropic.Anthropic(api_key="...")
        client = wrap_anthropic_client(client)
        
        # Now tool_use will be extracted and attached to spans
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=[...],
            tools=[...]
        )
    """
    try:
        from llmobserve.llm_wrappers.anthropic_wrapper import wrap_anthropic_client as _wrap
        return _wrap(client)
    except Exception as e:
        logger.warning(f"[llmobserve] Failed to wrap Anthropic client: {e}")
        return client  # Return unwrapped client (graceful degradation)

