"""
Automatic Agent Detection

Automatically detects agents, tools, and workflows from call stack analysis.
No manual tagging needed - works transparently!
"""
import inspect
import logging
import re
from typing import Optional, List, Tuple

logger = logging.getLogger("llmobserve")

# Common agent framework patterns
AGENT_PATTERNS = [
    # Function names
    r"agent[_\w]*",
    r"run[_\w]*agent",
    r"execute[_\w]*agent",
    r"orchestrat[eor]*",
    r"workflow[_\w]*",
    r"pipeline[_\w]*",
    
    # Class names
    r"Agent\w*",
    r"Workflow\w*",
    r"Pipeline\w*",
    r"Orchestrat[eor]*\w*",
    
    # Framework-specific
    r"langchain.*agent",
    r"autogpt",
    r"crewai",
    r"llamaindex.*agent",
    r"haystack.*agent",
]

# Tool patterns
TOOL_PATTERNS = [
    r"tool[_\w]*",
    r"function[_\w]*",
    r"call[_\w]*",
    r"invoke[_\w]*",
    r"execute[_\w]*tool",
]

# Step patterns
STEP_PATTERNS = [
    r"step[_\w]*",
    r"stage[_\w]*",
    r"phase[_\w]*",
    r"task[_\w]*",
]

# Known agent frameworks
KNOWN_FRAMEWORKS = {
    "langchain": {
        "agent_classes": ["Agent", "AgentExecutor", "ReActAgent", "ConversationalAgent"],
        "detect": lambda frame: "langchain" in str(frame.f_code.co_filename).lower()
    },
    "llamaindex": {
        "agent_classes": ["AgentRunner", "OpenAIAgent", "ReActAgent"],
        "detect": lambda frame: "llama_index" in str(frame.f_code.co_filename).lower() or "llamaindex" in str(frame.f_code.co_filename).lower()
    },
    "autogpt": {
        "agent_classes": ["Agent"],
        "detect": lambda frame: "autogpt" in str(frame.f_code.co_filename).lower()
    },
    "crewai": {
        "agent_classes": ["Agent", "Crew"],
        "detect": lambda frame: "crewai" in str(frame.f_code.co_filename).lower()
    },
}


def _matches_pattern(name: str, patterns: List[str]) -> bool:
    """Check if name matches any pattern."""
    name_lower = name.lower()
    for pattern in patterns:
        if re.search(pattern, name_lower, re.IGNORECASE):
            return True
    return False


def _detect_framework(frame) -> Optional[str]:
    """Detect known agent framework from frame."""
    for framework_name, config in KNOWN_FRAMEWORKS.items():
        if config["detect"](frame):
            return framework_name
    return None


def _extract_agent_name(frame) -> Optional[str]:
    """Extract agent name from frame."""
    # Try function name
    func_name = frame.f_code.co_name
    if _matches_pattern(func_name, AGENT_PATTERNS):
        # Clean up name (remove common prefixes/suffixes)
        name = func_name.replace("_agent", "").replace("agent_", "")
        return f"agent:{name}"
    
    # Try class name
    if 'self' in frame.f_locals:
        self_obj = frame.f_locals['self']
        class_name = self_obj.__class__.__name__
        if _matches_pattern(class_name, AGENT_PATTERNS):
            name = class_name.replace("Agent", "").lower()
            return f"agent:{name}" if name else "agent:unknown"
    
    # Try framework detection
    framework = _detect_framework(frame)
    if framework:
        return f"agent:{framework}"
    
    return None


def _extract_tool_name(frame) -> Optional[str]:
    """Extract tool name from frame."""
    func_name = frame.f_code.co_name
    if _matches_pattern(func_name, TOOL_PATTERNS):
        name = func_name.replace("_tool", "").replace("tool_", "")
        return f"tool:{name}"
    
    if 'self' in frame.f_locals:
        self_obj = frame.f_locals['self']
        class_name = self_obj.__class__.__name__
        if _matches_pattern(class_name, TOOL_PATTERNS):
            name = class_name.replace("Tool", "").lower()
            return f"tool:{name}" if name else "tool:unknown"
    
    return None


def _extract_step_name(frame) -> Optional[str]:
    """Extract step name from frame."""
    func_name = frame.f_code.co_name
    if _matches_pattern(func_name, STEP_PATTERNS):
        name = func_name.replace("_step", "").replace("step_", "")
        return f"step:{name}"
    
    return None


def detect_agent_from_stack(max_depth: int = 10) -> Optional[str]:
    """
    Automatically detect agent/workflow from call stack.
    
    Analyzes the call stack to find agent, tool, or step patterns.
    Works transparently - no manual tagging needed!
    
    Args:
        max_depth: Maximum stack frames to analyze
    
    Returns:
        Section label (e.g., "agent:research_assistant") or None
    """
    try:
        stack = inspect.stack()
        
        # Skip our own frames (agent_detector, context, etc.)
        skip_modules = ["llmobserve.agent_detector", "llmobserve.context", "llmobserve.http_interceptor"]
        
        for i, frame_info in enumerate(stack[2:max_depth+2], start=2):  # Skip current and caller
            frame = frame_info.frame
            
            # Skip our own code
            filename = frame.f_code.co_filename
            if any(skip in filename for skip in skip_modules):
                continue
            
            # Try to detect agent
            agent_name = _extract_agent_name(frame)
            if agent_name:
                logger.debug(f"[llmobserve] Auto-detected agent from stack: {agent_name} (frame: {frame.f_code.co_name})")
                return agent_name
            
            # Try to detect tool
            tool_name = _extract_tool_name(frame)
            if tool_name:
                logger.debug(f"[llmobserve] Auto-detected tool from stack: {tool_name} (frame: {frame.f_code.co_name})")
                return tool_name
            
            # Try to detect step
            step_name = _extract_step_name(frame)
            if step_name:
                logger.debug(f"[llmobserve] Auto-detected step from stack: {step_name} (frame: {frame.f_code.co_name})")
                return step_name
        
        return None
    
    except Exception as e:
        logger.debug(f"[llmobserve] Error detecting agent from stack: {e}")
        return None


def detect_hierarchical_context(max_depth: int = 15) -> List[str]:
    """
    Detect full hierarchical context from call stack.
    
    Returns list of sections in order (outermost to innermost).
    Example: ["agent:research_assistant", "tool:web_search", "step:analyze"]
    
    Args:
        max_depth: Maximum stack frames to analyze
    
    Returns:
        List of section labels
    """
    try:
        stack = inspect.stack()
        sections = []
        seen_agents = set()
        
        skip_modules = ["llmobserve.agent_detector", "llmobserve.context", "llmobserve.http_interceptor"]
        
        for i, frame_info in enumerate(stack[2:max_depth+2], start=2):
            frame = frame_info.frame
            
            # Skip our own code
            filename = frame.f_code.co_filename
            if any(skip in filename for skip in skip_modules):
                continue
            
            # Detect agent (only one per hierarchy)
            agent_name = _extract_agent_name(frame)
            if agent_name and agent_name not in seen_agents:
                sections.insert(0, agent_name)  # Agents are outermost
                seen_agents.add(agent_name)
                continue
            
            # Detect tool
            tool_name = _extract_tool_name(frame)
            if tool_name:
                sections.append(tool_name)
                continue
            
            # Detect step
            step_name = _extract_step_name(frame)
            if step_name:
                sections.append(step_name)
        
        return sections
    
    except Exception as e:
        logger.debug(f"[llmobserve] Error detecting hierarchical context: {e}")
        return []

