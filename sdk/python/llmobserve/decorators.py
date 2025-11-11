"""
Convenience decorators for semantic tracing.
"""
import functools
import asyncio
from typing import Optional, Callable, TypeVar, Any
from llmobserve.context import section

F = TypeVar('F', bound=Callable[..., Any])


def trace(
    agent: Optional[str] = None,
    tool: Optional[str] = None,
    step: Optional[str] = None
) -> Callable[[F], F]:
    """
    Decorator to automatically label a function with semantic sections.
    
    Supports semantic labels for hierarchical tracing:
    - agent:<name> → for orchestrators or autonomous agents
    - tool:<name>  → for external API or function calls
    - step:<name>  → for multi-step logic or workflows
    
    Priority: agent > tool > step (uses first non-None value)
    
    Usage:
        @trace(agent="researcher")
        async def my_agent():
            # This entire function will be traced as "agent:researcher"
            ...
        
        @trace(tool="web_search")
        def search_web(query: str):
            # This function will be traced as "tool:web_search"
            ...
        
        @trace(step="analyze_results")
        def analyze(data):
            # This function will be traced as "step:analyze_results"
            ...
    
    Args:
        agent: Agent name (e.g., "researcher", "planner", "executor")
        tool: Tool name (e.g., "web_search", "calculator", "database")
        step: Step name (e.g., "analyze", "transform", "validate")
    
    Returns:
        Decorated function that automatically creates a section context
    """
    # Determine label (priority: agent > tool > step)
    if agent:
        label = f"agent:{agent}"
    elif tool:
        label = f"tool:{tool}"
    elif step:
        label = f"step:{step}"
    else:
        raise ValueError("@trace requires at least one of: agent, tool, or step")
    
    def decorator(func: F) -> F:
        # Handle async functions
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                with section(label):
                    return await func(*args, **kwargs)
            return async_wrapper  # type: ignore
        
        # Handle sync functions
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                with section(label):
                    return func(*args, **kwargs)
            return sync_wrapper  # type: ignore
    
    return decorator

