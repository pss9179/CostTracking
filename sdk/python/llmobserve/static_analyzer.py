"""
Static Code Analyzer for Agent Tree Preview

Analyzes Python code BEFORE execution to build agent tree structure.
Shows what agents/tools/steps will be called without running the code.
"""
import ast
import inspect
import logging
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path

logger = logging.getLogger("llmobserve")

# Patterns for detection
AGENT_PATTERNS = [
    r"agent",
    r"orchestrat",
    r"workflow",
    r"pipeline",
]

TOOL_PATTERNS = [
    r"tool",
    r"function",
    r"call",
    r"invoke",
]

STEP_PATTERNS = [
    r"step",
    r"stage",
    r"phase",
    r"task",
]

# API call patterns
API_CALL_PATTERNS = [
    "client.chat.completions.create",
    "client.messages.create",
    "client.embeddings.create",
    "requests.get",
    "requests.post",
    "httpx.get",
    "httpx.post",
]


class AgentNode:
    """Represents a node in the agent tree."""
    def __init__(self, name: str, node_type: str, line_number: int):
        self.name = name
        self.type = node_type  # "agent", "tool", "step"
        self.line_number = line_number
        self.children: List[AgentNode] = []
        self.api_calls: List[Dict] = []  # API calls made in this node
        self.calls: List[str] = []  # Functions called from this node
    
    def add_child(self, child: 'AgentNode'):
        """Add a child node."""
        self.children.append(child)
    
    def add_api_call(self, api_call: Dict):
        """Add an API call."""
        self.api_calls.append(api_call)
    
    def add_call(self, func_name: str):
        """Add a function call."""
        if func_name not in self.calls:
            self.calls.append(func_name)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "type": self.type,
            "line_number": self.line_number,
            "children": [child.to_dict() for child in self.children],
            "api_calls": self.api_calls,
            "calls": self.calls,
        }


class AgentTreeAnalyzer(ast.NodeVisitor):
    """AST visitor that analyzes code to build agent tree."""
    
    def __init__(self):
        self.agents: Dict[str, AgentNode] = {}
        self.functions: Dict[str, ast.FunctionDef] = {}
        self.current_agent: Optional[AgentNode] = None
        self.call_graph: Dict[str, List[str]] = {}  # function -> [called functions]
        self.function_to_node: Dict[str, AgentNode] = {}  # function name -> node
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definitions."""
        self._visit_function(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definitions."""
        self._visit_function(node)
    
    def _visit_function(self, node):
        """Visit function definitions."""
        func_name = node.name
        self.functions[func_name] = node
        
        # Store previous agent context
        previous_agent = self.current_agent
        
        # Check if this is an agent
        if self._is_agent(func_name):
            agent_node = AgentNode(
                name=f"agent:{func_name.replace('_agent', '').replace('agent_', '')}",
                node_type="agent",
                line_number=node.lineno
            )
            self.agents[func_name] = agent_node
            self.function_to_node[func_name] = agent_node
            self.current_agent = agent_node
        
        # Check if this is a tool
        elif self._is_tool(func_name):
            tool_name = f"tool:{func_name.replace('_tool', '').replace('tool_', '')}"
            tool_node = AgentNode(
                name=tool_name,
                node_type="tool",
                line_number=node.lineno
            )
            self.function_to_node[func_name] = tool_node
            
            if self.current_agent:
                self.current_agent.add_child(tool_node)
            else:
                # Standalone tool
                self.agents[func_name] = tool_node
        
        # Check if this is a step
        elif self._is_step(func_name):
            step_name = f"step:{func_name.replace('_step', '').replace('step_', '')}"
            step_node = AgentNode(
                name=step_name,
                node_type="step",
                line_number=node.lineno
            )
            self.function_to_node[func_name] = step_node
            
            if self.current_agent:
                self.current_agent.add_child(step_node)
        
        # Analyze function body for API calls and function calls
        self._analyze_function_body(node)
        
        # Restore previous agent context
        self.current_agent = previous_agent
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Visit function calls."""
        # Detect API calls
        api_call = self._detect_api_call(node)
        if api_call and self.current_agent:
            self.current_agent.add_api_call(api_call)
        
        # Track function calls
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if self.current_agent:
                self.current_agent.add_call(func_name)
        
        self.generic_visit(node)
    
    def _is_agent(self, name: str) -> bool:
        """Check if function name matches agent pattern."""
        name_lower = name.lower()
        return any(pattern in name_lower for pattern in AGENT_PATTERNS)
    
    def _is_tool(self, name: str) -> bool:
        """Check if function name matches tool pattern."""
        name_lower = name.lower()
        return any(pattern in name_lower for pattern in TOOL_PATTERNS)
    
    def _is_step(self, name: str) -> bool:
        """Check if function name matches step pattern."""
        name_lower = name.lower()
        return any(pattern in name_lower for pattern in STEP_PATTERNS)
    
    def _detect_api_call(self, node: ast.Call) -> Optional[Dict]:
        """Detect API calls in AST."""
        # Check for client.chat.completions.create() pattern
        if isinstance(node.func, ast.Attribute):
            call_path = self._get_call_path(node.func)
            
            # OpenAI patterns
            if "chat.completions.create" in call_path:
                return {
                    "type": "openai_chat",
                    "path": call_path,
                    "line": node.lineno
                }
            elif "embeddings.create" in call_path:
                return {
                    "type": "openai_embedding",
                    "path": call_path,
                    "line": node.lineno
                }
            
            # Anthropic patterns
            elif "messages.create" in call_path:
                return {
                    "type": "anthropic_chat",
                    "path": call_path,
                    "line": node.lineno
                }
            
            # HTTP patterns
            elif call_path in ["requests.get", "requests.post", "httpx.get", "httpx.post"]:
                return {
                    "type": "http_request",
                    "path": call_path,
                    "line": node.lineno
                }
        
        return None
    
    def _get_call_path(self, node: ast.Attribute) -> str:
        """Get full call path like 'client.chat.completions.create'."""
        parts = []
        current = node
        
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        
        if isinstance(current, ast.Name):
            parts.append(current.id)
        
        return ".".join(reversed(parts))
    
    def _build_full_tree(self):
        """Build full call graph tree by linking function calls."""
        # Track which functions are called by agents (so we don't show them as standalone)
        called_by_agents = set()
        
        # For each agent, recursively find all called functions
        for func_name, agent_node in list(self.agents.items()):
            if agent_node.type == "agent":
                self._link_calls_recursive(func_name, agent_node, set(), called_by_agents)
        
        # Remove tools/steps that are called by agents from standalone agents dict
        # But keep agents even if called by other agents (they'll be shown as nested)
        for func_name in list(self.agents.keys()):
            if func_name in called_by_agents:
                # Only remove non-agent nodes (tools/steps) that are called by agents
                if self.agents[func_name].type != "agent":
                    del self.agents[func_name]
    
    def _link_calls_recursive(self, func_name: str, parent_node: AgentNode, visited: Set[str], called_by_agents: Set[str]):
        """Recursively link function calls to build full tree."""
        if func_name in visited:
            return  # Avoid cycles
        
        visited.add(func_name)
        
        # Get calls made by this function
        calls = self.call_graph.get(func_name, [])
        
        for called_func in calls:
            # Check if called function is a tool/step
            if called_func in self.function_to_node:
                called_node = self.function_to_node[called_func]
                called_by_agents.add(called_func)  # Mark as called by an agent
                
                # Check if already added as child
                if not any(child.name == called_node.name for child in parent_node.children):
                    parent_node.add_child(called_node)
                
                # Recursively process called function
                self._link_calls_recursive(called_func, called_node, visited.copy(), called_by_agents)
    
    def _analyze_function_body(self, node: ast.FunctionDef):
        """Analyze function body for calls."""
        func_name = node.name
        current_node = self.function_to_node.get(func_name) or self.current_agent
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                # Detect API calls
                api_call = self._detect_api_call(child)
                if api_call and current_node:
                    current_node.add_api_call(api_call)
                
                # Track function calls and build call graph
                if isinstance(child.func, ast.Name):
                    called_func = child.func.id
                    if current_node:
                        current_node.add_call(called_func)
                    
                    # Build call graph
                    if func_name not in self.call_graph:
                        self.call_graph[func_name] = []
                    if called_func not in self.call_graph[func_name]:
                        self.call_graph[func_name].append(called_func)


def analyze_code_file(file_path: str) -> Dict:
    """
    Analyze a Python file to build agent tree preview.
    
    Args:
        file_path: Path to Python file
    
    Returns:
        Dictionary with agent tree structure
    """
    try:
        with open(file_path, 'r') as f:
            code = f.read()
        
        tree = ast.parse(code)
        analyzer = AgentTreeAnalyzer()
        analyzer.visit(tree)
        
        # Build full call graph tree
        analyzer._build_full_tree()
        
        # Build result
        result = {
            "file": file_path,
            "agents": [agent.to_dict() for agent in analyzer.agents.values()],
            "total_agents": len(analyzer.agents),
            "total_functions": len(analyzer.functions),
            "call_graph": analyzer.call_graph,
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Error analyzing file {file_path}: {e}")
        return {
            "file": file_path,
            "error": str(e),
            "agents": [],
        }


def analyze_code_string(code: str, filename: str = "<string>") -> Dict:
    """
    Analyze Python code string to build agent tree preview.
    
    Args:
        code: Python code as string
        filename: Optional filename for reference
    
    Returns:
        Dictionary with agent tree structure
    """
    try:
        tree = ast.parse(code)
        analyzer = AgentTreeAnalyzer()
        analyzer.visit(tree)
        
        # Build full call graph tree
        analyzer._build_full_tree()
        
        result = {
            "file": filename,
            "agents": [agent.to_dict() for agent in analyzer.agents.values()],
            "total_agents": len(analyzer.agents),
            "total_functions": len(analyzer.functions),
            "call_graph": analyzer.call_graph,
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Error analyzing code: {e}")
        return {
            "file": filename,
            "error": str(e),
            "agents": [],
        }


def preview_agent_tree(file_path: Optional[str] = None, code: Optional[str] = None, filename: str = "<string>") -> str:
    """
    Generate a preview of the agent tree as a string.
    
    Args:
        file_path: Path to Python file (or None)
        code: Python code as string (or None)
    
    Returns:
        Formatted string showing agent tree structure
    """
    if file_path:
        result = analyze_code_file(file_path)
    elif code:
        result = analyze_code_string(code, filename=filename)
    else:
        return "Error: Provide either file_path or code"
    
    if "error" in result:
        return f"Error: {result['error']}"
    
    if not result["agents"]:
        return "No agents detected in code."
    
    lines = []
    lines.append(f"📊 Agent Tree Preview ({result['file']})")
    lines.append("=" * 60)
    lines.append(f"Total Agents: {result['total_agents']}")
    lines.append(f"Total Functions: {result['total_functions']}")
    lines.append("")
    
    def format_node(node: Dict, indent: int = 0):
        """Recursively format node."""
        prefix = "  " * indent
        node_type_emoji = {
            "agent": "🤖",
            "tool": "🔧",
            "step": "📝"
        }
        emoji = node_type_emoji.get(node["type"], "•")
        
        lines.append(f"{prefix}{emoji} {node['name']} (line {node['line_number']})")
        
        # Show API calls
        if node["api_calls"]:
            for api_call in node["api_calls"]:
                lines.append(f"{prefix}  └─ API: {api_call['type']} (line {api_call['line']})")
        
        # Show function calls
        if node["calls"]:
            for call in node["calls"]:
                lines.append(f"{prefix}  └─ Calls: {call}()")
        
        # Show children
        for child in node["children"]:
            format_node(child, indent + 1)
    
    for agent in result["agents"]:
        format_node(agent)
        lines.append("")
    
    return "\n".join(lines)

