"""
Multi-Language Static Analyzer

Supports TypeScript, JavaScript, Go, Python, and more!
Detects agents/tools/steps across all languages.
"""
import os
import re
import logging
from typing import Dict, List, Optional, Set
from pathlib import Path

logger = logging.getLogger("llmobserve")

# Agent patterns (language-agnostic)
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

# API call patterns by language
API_PATTERNS = {
    "typescript": [
        r"\.chat\.completions\.create",
        r"\.messages\.create",
        r"\.embeddings\.create",
        r"fetch\(",
        r"axios\.",
        r"\.get\(",
        r"\.post\(",
    ],
    "javascript": [
        r"\.chat\.completions\.create",
        r"\.messages\.create",
        r"fetch\(",
        r"axios\.",
        r"\.get\(",
        r"\.post\(",
    ],
    "python": [
        r"\.chat\.completions\.create",
        r"\.messages\.create",
        r"requests\.(get|post)",
        r"httpx\.(get|post)",
    ],
    "go": [
        r"http\.(Get|Post)",
        r"\.Do\(",
        r"client\.(Get|Post)",
    ],
    "java": [
        r"\.execute\(",
        r"HttpClient\.(get|post)",
        r"RestTemplate\.(get|post)",
    ],
}


class AgentNode:
    """Represents a node in the agent tree."""
    def __init__(self, name: str, node_type: str, line_number: int, language: str):
        self.name = name
        self.type = node_type
        self.line_number = line_number
        self.language = language
        self.children: List[AgentNode] = []
        self.api_calls: List[Dict] = []
        self.calls: List[str] = []
    
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
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "line_number": self.line_number,
            "language": self.language,
            "children": [child.to_dict() for child in self.children],
            "api_calls": self.api_calls,
            "calls": self.calls,
        }


class MultiLanguageAnalyzer:
    """Analyzes code in multiple languages."""
    
    def __init__(self):
        self.agents: Dict[str, AgentNode] = {}
        self.functions: Dict[str, Dict] = {}
        self.call_graph: Dict[str, List[str]] = {}
        self.function_to_node: Dict[str, AgentNode] = {}
    
    def detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lower()
        language_map = {
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
            ".py": "python",
            ".go": "go",
            ".java": "java",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".c": "c",
        }
        return language_map.get(ext, "unknown")
    
    def analyze_file(self, file_path: str) -> Dict:
        """Analyze a file in any language."""
        language = self.detect_language(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            return self.analyze_code(code, language, file_path)
        
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return {
                "file": file_path,
                "language": language,
                "error": str(e),
                "agents": [],
            }
    
    def analyze_code(self, code: str, language: str, filename: str = "<string>") -> Dict:
        """Analyze code in any language."""
        self.agents = {}
        self.functions = {}
        self.call_graph = {}
        self.function_to_node = {}
        
        # Use language-specific parser
        if language == "python":
            return self._analyze_python(code, filename)
        elif language in ["typescript", "javascript"]:
            return self._analyze_typescript_javascript(code, language, filename)
        elif language == "go":
            return self._analyze_go(code, filename)
        elif language == "java":
            return self._analyze_java(code, filename)
        else:
            # Fallback: generic regex-based analysis
            return self._analyze_generic(code, language, filename)
    
    def _analyze_python(self, code: str, filename: str) -> Dict:
        """Analyze Python code using AST."""
        try:
            import ast
            from llmobserve.static_analyzer import analyze_code_string
            result = analyze_code_string(code, filename)
            # Add language field to all agents
            for agent in result.get("agents", []):
                agent["language"] = "python"
                for child in agent.get("children", []):
                    child["language"] = "python"
            result["language"] = "python"
            return result
        except Exception as e:
            logger.error(f"Error analyzing Python: {e}")
            return self._analyze_generic(code, "python", filename)
    
    def _analyze_typescript_javascript(self, code: str, language: str, filename: str) -> Dict:
        """Analyze TypeScript/JavaScript code."""
        # Extract functions using regex (works for most cases)
        # Pattern 1: function functionName() {}
        function_pattern = r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{"
        
        # Pattern 2: const/let functionName = () => {}
        arrow_function_pattern = r"(?:const|let|var)\s+(\w+)\s*[:=]\s*(?:async\s+)?\([^)]*\)\s*=>"
        
        # Pattern 3: functionName: function() {} or functionName() {}
        method_pattern = r"(\w+)\s*[:=]\s*(?:async\s+)?\([^)]*\)\s*(?::\s*[^{]+)?\s*\{"
        
        functions = []
        seen_functions = set()
        
        # Pattern 1: function functionName() {}
        for match in re.finditer(function_pattern, code, re.MULTILINE):
            func_name = match.group(1)
            if func_name not in seen_functions:
                line_number = code[:match.start()].count('\n') + 1
                functions.append({
                    "name": func_name,
                    "line": line_number,
                    "body_start": match.end(),
                })
                seen_functions.add(func_name)
        
        # Pattern 2: const/let functionName = () => {}
        for match in re.finditer(arrow_function_pattern, code, re.MULTILINE):
            func_name = match.group(1)
            if func_name not in seen_functions:
                line_number = code[:match.start()].count('\n') + 1
                functions.append({
                    "name": func_name,
                    "line": line_number,
                    "body_start": match.end(),
                })
                seen_functions.add(func_name)
        
        # Pattern 3: Class methods (methodName() {})
        class_method_pattern = r"(?:public\s+|private\s+|protected\s+)?(?:async\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{"
        for match in re.finditer(class_method_pattern, code, re.MULTILINE):
            func_name = match.group(1)
            if func_name not in seen_functions and func_name not in ["constructor", "get", "set"]:
                line_number = code[:match.start()].count('\n') + 1
                functions.append({
                    "name": func_name,
                    "line": line_number,
                    "body_start": match.end(),
                })
                seen_functions.add(func_name)
        
        # Pattern 4: Function expressions: const name = function() {}
        function_expr_pattern = r"(?:const|let|var)\s+(\w+)\s*=\s*function\s*\([^)]*\)"
        for match in re.finditer(function_expr_pattern, code, re.MULTILINE):
            func_name = match.group(1)
            if func_name not in seen_functions:
                line_number = code[:match.start()].count('\n') + 1
                functions.append({
                    "name": func_name,
                    "line": line_number,
                    "body_start": match.end(),
                })
                seen_functions.add(func_name)
        
        # Pattern 5: Object methods: { methodName: function() {} } or { methodName() {} }
        object_method_pattern = r"(\w+)\s*[:=]\s*(?:async\s+)?(?:function\s*\([^)]*\)|\([^)]*\)\s*=>)"
        for match in re.finditer(object_method_pattern, code, re.MULTILINE):
            func_name = match.group(1)
            if func_name not in seen_functions:
                line_number = code[:match.start()].count('\n') + 1
                functions.append({
                    "name": func_name,
                    "line": line_number,
                    "body_start": match.end(),
                })
                seen_functions.add(func_name)
        
        # Process each function
        for func_info in functions:
            func_name = func_info["name"]
            line_number = func_info["line"]
            
            # Get function body (simplified - find next closing brace)
            body_start = func_info.get("body_start", 0)
            body = code[body_start:]
            
            # Detect agent/tool/step
            node = None
            if self._matches_pattern(func_name, AGENT_PATTERNS):
                node = AgentNode(
                    name=f"agent:{func_name.replace('_agent', '').replace('agent_', '').replace('Agent', '')}",
                    node_type="agent",
                    line_number=line_number,
                    language=language
                )
                self.agents[func_name] = node
                self.function_to_node[func_name] = node
            elif self._matches_pattern(func_name, TOOL_PATTERNS):
                node = AgentNode(
                    name=f"tool:{func_name.replace('_tool', '').replace('tool_', '').replace('Tool', '')}",
                    node_type="tool",
                    line_number=line_number,
                    language=language
                )
                self.function_to_node[func_name] = node
                if not self.agents:  # Standalone tool
                    self.agents[func_name] = node
            elif self._matches_pattern(func_name, STEP_PATTERNS):
                node = AgentNode(
                    name=f"step:{func_name.replace('_step', '').replace('step_', '').replace('Step', '')}",
                    node_type="step",
                    line_number=line_number,
                    language=language
                )
                self.function_to_node[func_name] = node
            
            if node:
                # Detect API calls in function body
                api_patterns = API_PATTERNS.get(language, [])
                for pattern in api_patterns:
                    for api_match in re.finditer(pattern, body):
                        node.api_calls.append({
                            "type": "api_call",
                            "pattern": pattern,
                            "line": line_number + body[:api_match.start()].count('\n'),
                        })
                
                # Detect function calls
                call_pattern = rf"{func_name}\s*\([^)]*\)"
                for call_match in re.finditer(r"(\w+)\s*\(", body):
                    called_func = call_match.group(1)
                    if called_func != func_name and called_func not in ["if", "for", "while", "switch", "return"]:
                        node.calls.append(called_func)
                        if func_name not in self.call_graph:
                            self.call_graph[func_name] = []
                        if called_func not in self.call_graph[func_name]:
                            self.call_graph[func_name].append(called_func)
        
        # Build tree
        self._build_tree()
        
        return {
            "file": filename,
            "language": language,
            "agents": [agent.to_dict() for agent in self.agents.values()],
            "total_agents": len([a for a in self.agents.values() if a.type == "agent"]),
            "total_functions": len(functions),
        }
    
    def _analyze_go(self, code: str, filename: str) -> Dict:
        """Analyze Go code."""
        # Go function pattern: func FunctionName(...) {...}
        function_pattern = r"func\s+(\w+)\s*\([^)]*\)\s*(?:\([^)]*\))?\s*\{"
        
        functions = []
        for match in re.finditer(function_pattern, code, re.MULTILINE):
            func_name = match.group(1)
            line_number = code[:match.start()].count('\n') + 1
            functions.append({
                "name": func_name,
                "line": line_number,
                "body_start": match.end(),
            })
        
        # Process similar to TypeScript
        return self._process_functions(code, functions, "go", filename)
    
    def _analyze_java(self, code: str, filename: str) -> Dict:
        """Analyze Java code."""
        # Java method pattern: [modifiers] returnType methodName(...) {...}
        function_pattern = r"(?:public|private|protected)?\s*(?:static\s+)?\w+\s+(\w+)\s*\([^)]*\)\s*\{"
        
        functions = []
        for match in re.finditer(function_pattern, code, re.MULTILINE):
            func_name = match.group(1)
            line_number = code[:match.start()].count('\n') + 1
            functions.append({
                "name": func_name,
                "line": line_number,
                "body_start": match.end(),
            })
        
        return self._process_functions(code, functions, "java", filename)
    
    def _process_functions(self, code: str, functions: List[Dict], language: str, filename: str) -> Dict:
        """Process functions for any language."""
        for func_info in functions:
            func_name = func_info["name"]
            line_number = func_info["line"]
            
            body_start = func_info.get("body_start", 0)
            body = code[body_start:]
            
            # Detect agent/tool/step
            node = None
            if self._matches_pattern(func_name, AGENT_PATTERNS):
                node = AgentNode(
                    name=f"agent:{func_name.replace('Agent', '')}",
                    node_type="agent",
                    line_number=line_number,
                    language=language
                )
                self.agents[func_name] = node
                self.function_to_node[func_name] = node
            elif self._matches_pattern(func_name, TOOL_PATTERNS):
                node = AgentNode(
                    name=f"tool:{func_name.replace('Tool', '')}",
                    node_type="tool",
                    line_number=line_number,
                    language=language
                )
                self.function_to_node[func_name] = node
                if not self.agents:
                    self.agents[func_name] = node
            
            if node:
                # Detect API calls
                api_patterns = API_PATTERNS.get(language, [])
                for pattern in api_patterns:
                    for api_match in re.finditer(pattern, body):
                        node.api_calls.append({
                            "type": "api_call",
                            "pattern": pattern,
                            "line": line_number + body[:api_match.start()].count('\n'),
                        })
                
                # Detect function calls
                for call_match in re.finditer(r"(\w+)\s*\(", body):
                    called_func = call_match.group(1)
                    if called_func != func_name:
                        node.calls.append(called_func)
                        if func_name not in self.call_graph:
                            self.call_graph[func_name] = []
                        if called_func not in self.call_graph[func_name]:
                            self.call_graph[func_name].append(called_func)
        
        self._build_tree()
        
        return {
            "file": filename,
            "language": language,
            "agents": [agent.to_dict() for agent in self.agents.values()],
            "total_agents": len([a for a in self.agents.values() if a.type == "agent"]),
            "total_functions": len(functions),
        }
    
    def _analyze_generic(self, code: str, language: str, filename: str) -> Dict:
        """Generic regex-based analysis for unknown languages."""
        # Try to find function-like patterns
        function_patterns = [
            r"function\s+(\w+)",
            r"(\w+)\s*[:=]\s*function",
            r"(\w+)\s*[:=]\s*\([^)]*\)\s*=>",
            r"def\s+(\w+)",
            r"func\s+(\w+)",
            r"(\w+)\s*\([^)]*\)\s*\{",
        ]
        
        functions = []
        for pattern in function_patterns:
            for match in re.finditer(pattern, code, re.MULTILINE):
                func_name = match.group(1) if match.groups() else match.group(0).split('(')[0].strip()
                line_number = code[:match.start()].count('\n') + 1
                functions.append({
                    "name": func_name,
                    "line": line_number,
                })
        
        return self._process_functions(code, functions, language, filename)
    
    def _matches_pattern(self, name: str, patterns: List[str]) -> bool:
        """Check if name matches any pattern."""
        name_lower = name.lower()
        for pattern in patterns:
            if re.search(pattern, name_lower, re.IGNORECASE):
                return True
        return False
    
    def _build_tree(self):
        """Build call graph tree."""
        called_by_agents = set()
        called_by_other_agents = set()  # Track agents called by other agents
        
        # First pass: build tree and track what's called by agents
        for func_name, agent_node in list(self.agents.items()):
            if agent_node.type == "agent":
                self._link_calls_recursive(func_name, agent_node, set(), called_by_agents, called_by_other_agents)
        
        # Remove tools/steps that are called by agents (they should be children, not standalone)
        for func_name in list(self.agents.keys()):
            if func_name in called_by_agents and self.agents[func_name].type != "agent":
                del self.agents[func_name]
        
        # Remove agents that are called by other agents (they should be children, not standalone)
        for func_name in list(self.agents.keys()):
            if func_name in called_by_other_agents:
                del self.agents[func_name]
    
    def _link_calls_recursive(self, func_name: str, parent_node: AgentNode, visited: Set[str], called_by_agents: Set[str], called_by_other_agents: Set[str]):
        """Recursively link function calls."""
        if func_name in visited:
            return
        
        visited.add(func_name)
        calls = self.call_graph.get(func_name, [])
        
        for called_func in calls:
            if called_func in self.function_to_node:
                called_node = self.function_to_node[called_func]
                called_by_agents.add(called_func)
                
                # If called function is an agent and parent is also an agent, mark it
                if called_node.type == "agent" and parent_node.type == "agent":
                    called_by_other_agents.add(called_func)
                
                if not any(child.name == called_node.name for child in parent_node.children):
                    parent_node.add_child(called_node)
                
                self._link_calls_recursive(called_func, called_node, visited.copy(), called_by_agents, called_by_other_agents)


def analyze_multi_language_file(file_path: str) -> Dict:
    """Analyze a file in any supported language."""
    analyzer = MultiLanguageAnalyzer()
    return analyzer.analyze_file(file_path)


def analyze_multi_language_code(code: str, language: str, filename: str = "<string>") -> Dict:
    """Analyze code in any supported language."""
    analyzer = MultiLanguageAnalyzer()
    return analyzer.analyze_code(code, language, filename)


def preview_multi_language_tree(file_path: Optional[str] = None, code: Optional[str] = None, language: Optional[str] = None) -> str:
    """Generate preview for any language."""
    analyzer = MultiLanguageAnalyzer()
    
    if file_path:
        result = analyzer.analyze_file(file_path)
    elif code and language:
        result = analyzer.analyze_code(code, language)
    else:
        return "Error: Provide either file_path or (code + language)"
    
    if "error" in result:
        return f"Error: {result['error']}"
    
    if not result["agents"]:
        return f"No agents detected in {result.get('language', 'code')}."
    
    lines = []
    lines.append(f"📊 Agent Tree Preview ({result['file']}) - {result.get('language', 'unknown').upper()}")
    lines.append("=" * 60)
    lines.append(f"Total Agents: {result['total_agents']}")
    lines.append(f"Total Functions: {result['total_functions']}")
    lines.append("")
    
    def format_node(node: Dict, indent: int = 0):
        prefix = "  " * indent
        node_type_emoji = {
            "agent": "🤖",
            "tool": "🔧",
            "step": "📝"
        }
        emoji = node_type_emoji.get(node["type"], "•")
        
        lines.append(f"{prefix}{emoji} {node['name']} ({node['language']}) (line {node['line_number']})")
        
        if node["api_calls"]:
            for api_call in node["api_calls"]:
                lines.append(f"{prefix}  └─ API: {api_call.get('pattern', 'api_call')} (line {api_call.get('line', '?')})")
        
        if node["calls"]:
            for call in node["calls"][:5]:  # Limit to 5 calls
                lines.append(f"{prefix}  └─ Calls: {call}()")
        
        for child in node["children"]:
            format_node(child, indent + 1)
    
    for agent in result["agents"]:
        format_node(agent)
        lines.append("")
    
    return "\n".join(lines)

