"""
AI-Powered Codebase Labeling

Uses LLM to analyze code and suggest section() labels automatically.
"""

import ast
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Simulate LLM call (replace with actual OpenAI/Anthropic API)
def ask_ai_to_label_code(code_snippet: str, context: str = "") -> Dict[str, Any]:
    """
    Send code to LLM and get section label suggestions.
    
    In production, this would call:
    - OpenAI API (gpt-4o)
    - Anthropic API (claude-3.5-sonnet)
    - Or your own LLM endpoint
    """
    # For demo, return mock suggestions
    # In real implementation, you'd do:
    # response = openai.ChatCompletion.create(
    #     model="gpt-4o",
    #     messages=[
    #         {"role": "system", "content": "You are a code analyzer. Suggest section labels for LLM observability."},
    #         {"role": "user", "content": f"Analyze this code and suggest section labels:\n\n{code_snippet}"}
    #     ]
    # )
    
    # Mock response for demo
    suggestions = []
    
    # Simple heuristics (AI would do better)
    if "chat.completions" in code_snippet or "completions.create" in code_snippet:
        if "search" in code_snippet.lower() or "query" in code_snippet.lower():
            suggestions.append({
                "line": 1,
                "type": "tool",
                "name": "web_search",
                "confidence": 0.8,
                "reason": "Contains search/query logic with LLM"
            })
        else:
            suggestions.append({
                "line": 1,
                "type": "tool",
                "name": "openai_chat",
                "confidence": 0.9,
                "reason": "OpenAI chat completion call"
            })
    
    if "pinecone" in code_snippet.lower() or "query" in code_snippet.lower() and "vector" in code_snippet.lower():
        suggestions.append({
            "line": 1,
            "type": "tool",
            "name": "vector_search",
            "confidence": 0.85,
            "reason": "Vector database query"
        })
    
    # Check for agent-like patterns
    if "def " in code_snippet and ("agent" in code_snippet.lower() or "orchestrat" in code_snippet.lower()):
        func_name = code_snippet.split("def ")[1].split("(")[0] if "def " in code_snippet else "agent"
        suggestions.append({
            "line": 1,
            "type": "agent",
            "name": func_name,
            "confidence": 0.7,
            "reason": "Function appears to be an agent orchestrator"
        })
    
    return {
        "suggestions": suggestions,
        "code": code_snippet,
    }


def extract_code_context(filepath: Path, line_start: int, line_end: int, context_lines: int = 5) -> str:
    """Extract code with context around a specific line range."""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Get context before and after
    start = max(0, line_start - context_lines - 1)
    end = min(len(lines), line_end + context_lines)
    
    code = "".join(lines[start:end])
    return code


def find_api_calls_with_context(filepath: Path) -> List[Dict[str, Any]]:
    """Find API calls and extract surrounding context."""
    with open(filepath, 'r') as f:
        content = f.read()
        tree = ast.parse(content, filename=str(filepath))
    
    api_calls = []
    
    class APICallVisitor(ast.NodeVisitor):
        def visit_Call(self, node):
            if isinstance(node.func, ast.Attribute):
                call_chain = []
                current = node.func
                while isinstance(current, ast.Attribute):
                    call_chain.insert(0, current.attr)
                    current = current.value
                
                if isinstance(current, ast.Name):
                    call_chain.insert(0, current.id)
                
                call_str = ".".join(call_chain)
                
                # Detect API calls
                api_keywords = ["openai", "anthropic", "cohere", "pinecone", 
                              "chat", "completions", "embeddings", "query", "upsert"]
                if any(kw in call_str.lower() for kw in api_keywords):
                    # Get surrounding code
                    code_context = extract_code_context(filepath, node.lineno, node.end_lineno or node.lineno)
                    
                    api_calls.append({
                        "call": call_str,
                        "line": node.lineno,
                        "end_line": node.end_lineno or node.lineno,
                        "context": code_context,
                    })
            
            self.generic_visit(node)
    
    visitor = APICallVisitor()
    visitor.visit(tree)
    return api_calls


def analyze_and_suggest_labels(filepath: Path) -> Dict[str, Any]:
    """Analyze file and get AI suggestions for labels."""
    api_calls = find_api_calls_with_context(filepath)
    
    suggestions = []
    for api_call in api_calls:
        # Ask AI to suggest labels
        ai_response = ask_ai_to_label_code(api_call["context"])
        
        for suggestion in ai_response["suggestions"]:
            suggestions.append({
                **suggestion,
                "file": str(filepath),
                "api_call_line": api_call["line"],
                "api_call": api_call["call"],
            })
    
    return {
        "file": str(filepath),
        "api_calls": api_calls,
        "suggestions": suggestions,
    }


def generate_labeled_code(filepath: Path, suggestions: List[Dict[str, Any]]) -> str:
    """Generate code with suggested labels applied."""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Group suggestions by line
    suggestions_by_line = {}
    for sug in suggestions:
        line = sug["api_call_line"]
        if line not in suggestions_by_line:
            suggestions_by_line[line] = []
        suggestions_by_line[line].append(sug)
    
    # Generate labeled version
    output = []
    i = 0
    while i < len(lines):
        line_num = i + 1
        
        # Check if we need to add a section before this line
        if line_num in suggestions_by_line:
            for sug in suggestions_by_line[line_num]:
                section_type = sug["type"]  # "agent" or "tool"
                section_name = sug["name"]
                
                # Add section wrapper
                indent = len(lines[i]) - len(lines[i].lstrip())
                section_label = f"{section_type}:{section_name}"
                output.append(" " * indent + f"with section(\"{section_label}\"):\n")
                output.append(" " * (indent + 4) + lines[i])  # Indent original line
                
                # Find matching closing (simplified - real version needs AST)
                # For demo, just add closing after a few lines
                if i + 3 < len(lines):
                    output.append(" " * indent + "# Section ends here\n")
                i += 1
                break
        else:
            output.append(lines[i])
            i += 1
    
    return "".join(output)


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("AI-POWERED CODEBASE LABELING")
    print("=" * 80)
    
    # Test on a sample file
    test_file = Path("scripts/test_agent.py")
    if test_file.exists():
        print(f"\n📁 Analyzing: {test_file}")
        result = analyze_and_suggest_labels(test_file)
        
        print(f"\n📊 Found {len(result['api_calls'])} API calls")
        print(f"💡 Generated {len(result['suggestions'])} label suggestions\n")
        
        for sug in result['suggestions'][:3]:  # Show first 3
            print(f"  Line {sug['api_call_line']}: {sug['api_call']}")
            print(f"    → Suggest: {sug['type']}:{sug['name']} (confidence: {sug['confidence']})")
            print(f"    → Reason: {sug['reason']}\n")
    
    print("=" * 80)
    print("HOW IT WORKS:")
    print("=" * 80)
    print("""
1. CLI scans codebase (AST parsing)
2. Finds API calls (OpenAI, Anthropic, etc.)
3. Extracts code context around each call
4. Sends to LLM (OpenAI/Anthropic) for analysis
5. LLM suggests section labels based on:
   - Function names
   - Variable names
   - Code comments
   - Call patterns
6. CLI generates labeled code (or suggests edits)

PRODUCTION IMPLEMENTATION:
- Use OpenAI API (gpt-4o) or Anthropic (claude-3.5-sonnet)
- Batch process multiple files
- Allow user to review/approve suggestions
- Generate diff/patch files
- Support interactive mode (accept/reject per suggestion)
    """)
    
    print("\n💡 This is how you make CLI read codebase 'like an AI'!")
    print("   Combine AST parsing (structure) + LLM (semantic understanding)")


