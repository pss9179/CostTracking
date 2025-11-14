"""
Universal tool registration hooks for agent frameworks.

Provides wrap_all_tools() that works with LangChain, CrewAI, AutoGen,
LlamaIndex, and custom code without per-framework logic.
"""
from typing import Union, List, Dict, Callable, Any
from llmobserve.tool_wrapper import wrap_tool


def wrap_all_tools(tools: Union[List, Dict, Callable, Any]) -> Union[List, Dict, Callable, Any]:
    """
    Universal tool wrapping function that works with ANY framework.
    
    Handles:
    - Dict of callables (e.g., AutoGen function_map)
    - List/tuple of functions or tool objects (e.g., LangChain, CrewAI)
    - Single function or tool object
    - Tool objects with .run() method (e.g., LangChain BaseTool)
    
    Args:
        tools: Tools to wrap (dict, list, tuple, or single callable)
    
    Returns:
        Wrapped tools in the same format as input
    
    Usage:
        # LangChain
        from langchain.tools import DuckDuckGoSearchRun
        search = DuckDuckGoSearchRun()
        tools = wrap_all_tools([search, calculator])
        agent = initialize_agent(tools=tools, llm=llm)
        
        # CrewAI
        tools = wrap_all_tools([search_tool, scrape_tool])
        agent = Agent(role="researcher", tools=tools)
        
        # AutoGen
        function_map = wrap_all_tools({"search": search_fn, "calc": calc_fn})
        assistant = AssistantAgent(function_map=function_map)
        
        # LlamaIndex
        tools = wrap_all_tools([search_tool, qa_tool])
        agent = OpenAIAgent.from_tools(tools)
    """
    # Handle dict of callables (e.g., AutoGen)
    if isinstance(tools, dict):
        return {
            name: wrap_tool(fn, name)
            for name, fn in tools.items()
        }
    
    # Handle list/tuple of functions or tool objects
    if isinstance(tools, (list, tuple)):
        wrapped = []
        for t in tools:
            wrapped_tool = _wrap_single_tool(t)
            wrapped.append(wrapped_tool)
        
        # Return same type as input (list or tuple)
        return type(tools)(wrapped)
    
    # Single function or object
    return _wrap_single_tool(tools)


def _wrap_single_tool(tool: Any) -> Any:
    """
    Wrap a single tool (function or tool object).
    
    Handles:
    - Plain functions
    - Tool objects with .name attribute
    - Tool objects with .run() method
    - Callable classes
    """
    # Extract name with priority order
    name = (
        getattr(tool, "name", None)  # Tool object's .name attribute
        or getattr(tool, "__name__", None)  # Function name
        or tool.__class__.__name__  # Class name
    )
    
    # Case 1: Tool object with .run() method (e.g., LangChain BaseTool)
    if hasattr(tool, "run") and callable(tool.run):
        # Wrap the .run method in-place
        tool.run = wrap_tool(tool.run, name)
        return tool
    
    # Case 2: Callable (function, lambda, or class with __call__)
    if callable(tool):
        return wrap_tool(tool, name)
    
    # Case 3: Unknown type - return as-is (fail gracefully)
    return tool


def try_patch_frameworks():
    """
    OPTIONAL: Best-effort patching of common framework constructors.
    
    This is not required for tool wrapping to work. Users can manually
    call wrap_all_tools() before passing tools to frameworks.
    
    This function attempts to patch common constructors to automatically
    wrap tools, but it's fragile and may break with framework updates.
    
    Usage:
        observe(auto_wrap_frameworks=True)  # Calls this function
    """
    from importlib import import_module
    
    # List of (module_name, attr_name, ctor_attr) tuples to patch
    # ctor_attr is the method to wrap (e.g., "from_class", "from_defaults")
    # If None, wrap the class/function directly
    patches = [
        ("langchain.agents", "AgentExecutor", "from_agent_and_tools"),
        ("langchain.agents", "initialize_agent", None),
        ("crewai", "Agent", None),
        ("crewai", "Task", None),
        ("autogen", "AssistantAgent", None),
        ("llama_index.agent", "OpenAIAgent", "from_tools"),
        ("llama_index.tools", "FunctionTool", "from_defaults"),
    ]
    
    for module_name, attr, ctor_attr in patches:
        try:
            m = import_module(module_name)
        except ImportError:
            continue  # Framework not installed, skip
        
        target = getattr(m, attr, None)
        if target is None:
            continue  # Attribute doesn't exist, skip
        
        # Patch constructor method or function
        if ctor_attr:
            # Patch class method (e.g., from_tools, from_agent_and_tools)
            original = getattr(target, ctor_attr, None)
            if callable(original):
                wrapped = _wrap_constructor(original)
                setattr(target, ctor_attr, wrapped)
        elif callable(target):
            # Patch function or class constructor directly
            wrapped = _wrap_constructor(target)
            setattr(m, attr, wrapped)


def _wrap_constructor(ctor: Callable) -> Callable:
    """
    Wrap a constructor to automatically call wrap_all_tools on tools argument.
    
    This is a generic wrapper that works for most framework constructors.
    """
    import functools
    import inspect
    
    @functools.wraps(ctor)
    def wrapped_ctor(*args, **kwargs):
        # Wrap tools in kwargs
        if "tools" in kwargs and kwargs["tools"]:
            kwargs["tools"] = wrap_all_tools(kwargs["tools"])
        
        # Also handle function_map for AutoGen
        if "function_map" in kwargs and kwargs["function_map"]:
            kwargs["function_map"] = wrap_all_tools(kwargs["function_map"])
        
        # Call original constructor
        return ctor(*args, **kwargs)
    
    return wrapped_ctor

