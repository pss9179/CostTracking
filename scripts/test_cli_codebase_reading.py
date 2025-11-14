"""
Test: Can a CLI read a codebase like an AI?

Answer: Partially - can parse AST, find patterns, but no semantic understanding.
"""

import ast
import os
from pathlib import Path
from typing import List, Dict, Any

def find_python_files(root: str) -> List[Path]:
    """Find all Python files in codebase."""
    files = []
    for path in Path(root).rglob("*.py"):
        # Skip common directories
        if any(skip in str(path) for skip in ["__pycache__", ".git", "node_modules", ".venv", "venv"]):
            continue
        files.append(path)
    return files

def parse_file(filepath: Path) -> Dict[str, Any]:
    """Parse a Python file and extract structure."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content, filename=str(filepath))
    except Exception as e:
        return {"error": str(e), "file": str(filepath)}
    
    info = {
        "file": str(filepath),
        "functions": [],
        "classes": [],
        "imports": [],
        "api_calls": [],  # OpenAI, Anthropic, etc.
        "section_usage": [],  # Uses of section()
        "has_llmobserve": False,
    }
    
    class APICallVisitor(ast.NodeVisitor):
        def __init__(self):
            self.api_calls = []
            self.sections = []
            self.imports = []
            self.functions = []
            self.classes = []
            self.has_llmobserve = False
        
        def visit_Import(self, node):
            for alias in node.names:
                self.imports.append(alias.name)
                if "llmobserve" in alias.name:
                    self.has_llmobserve = True
        
        def visit_ImportFrom(self, node):
            if node.module:
                self.imports.append(node.module)
                if "llmobserve" in node.module:
                    self.has_llmobserve = True
        
        def visit_FunctionDef(self, node):
            self.functions.append({
                "name": node.name,
                "line": node.lineno,
                "args": [arg.arg for arg in node.args.args],
            })
            self.generic_visit(node)
        
        def visit_ClassDef(self, node):
            self.classes.append({
                "name": node.name,
                "line": node.lineno,
            })
            self.generic_visit(node)
        
        def visit_Call(self, node):
            # Detect API calls (OpenAI, Anthropic, etc.)
            if isinstance(node.func, ast.Attribute):
                # e.g., client.chat.completions.create()
                call_chain = []
                current = node.func
                while isinstance(current, ast.Attribute):
                    call_chain.insert(0, current.attr)
                    current = current.value
                
                if isinstance(current, ast.Name):
                    call_chain.insert(0, current.id)
                
                call_str = ".".join(call_chain)
                
                # Detect common API patterns
                api_keywords = ["openai", "anthropic", "cohere", "pinecone", 
                              "chat", "completions", "embeddings", "query", "upsert"]
                if any(kw in call_str.lower() for kw in api_keywords):
                    self.api_calls.append({
                        "call": call_str,
                        "line": node.lineno,
                    })
            
            # Detect section() usage
            if isinstance(node.func, ast.Name) and node.func.id == "section":
                self.sections.append({
                    "line": node.lineno,
                    "args": [ast.unparse(arg) if hasattr(ast, 'unparse') else str(arg) 
                            for arg in node.args],
                })
            elif isinstance(node.func, ast.Attribute) and node.func.attr == "section":
                self.sections.append({
                    "line": node.lineno,
                    "args": [ast.unparse(arg) if hasattr(ast, 'unparse') else str(arg) 
                            for arg in node.args],
                })
            
            self.generic_visit(node)
        
        def visit_With(self, node):
            # Detect with section("...") blocks
            for item in node.items:
                if isinstance(item.context_expr, ast.Call):
                    if isinstance(item.context_expr.func, ast.Name):
                        if item.context_expr.func.id == "section":
                            # Extract section name
                            if item.context_expr.args:
                                section_name = ast.unparse(item.context_expr.args[0]) if hasattr(ast, 'unparse') else str(item.context_expr.args[0])
                                self.sections.append({
                                    "line": node.lineno,
                                    "type": "with_statement",
                                    "name": section_name,
                                })
            self.generic_visit(node)
    
    visitor = APICallVisitor()
    visitor.visit(tree)
    
    info.update({
        "functions": visitor.functions,
        "classes": visitor.classes,
        "imports": visitor.imports,
        "api_calls": visitor.api_calls,
        "section_usage": visitor.sections,
        "has_llmobserve": visitor.has_llmobserve,
    })
    
    return info

def analyze_codebase(root: str = ".") -> Dict[str, Any]:
    """Analyze entire codebase."""
    files = find_python_files(root)
    
    results = {
        "total_files": len(files),
        "files_with_llmobserve": 0,
        "files_with_api_calls": 0,
        "files_with_sections": 0,
        "total_api_calls": 0,
        "total_sections": 0,
        "unlabeled_api_calls": [],
        "file_details": [],
    }
    
    for filepath in files:
        info = parse_file(filepath)
        if "error" in info:
            continue
        
        if info["has_llmobserve"]:
            results["files_with_llmobserve"] += 1
        
        if info["api_calls"]:
            results["files_with_api_calls"] += 1
            results["total_api_calls"] += len(info["api_calls"])
            
            # Check if API calls are inside sections
            for api_call in info["api_calls"]:
                # Simple heuristic: if file has sections, assume they might be labeled
                # (Real implementation would need to check actual nesting)
                if not info["section_usage"]:
                    results["unlabeled_api_calls"].append({
                        "file": info["file"],
                        "call": api_call["call"],
                        "line": api_call["line"],
                    })
        
        if info["section_usage"]:
            results["files_with_sections"] += 1
            results["total_sections"] += len(info["section_usage"])
        
        results["file_details"].append(info)
    
    return results

# Test it
if __name__ == "__main__":
    print("=" * 80)
    print("CLI CODEBASE ANALYSIS TEST")
    print("=" * 80)
    print("\nAnalyzing current codebase...\n")
    
    # Analyze scripts directory as example
    results = analyze_codebase("scripts")
    
    print(f"📊 Results:")
    print(f"  Total Python files: {results['total_files']}")
    print(f"  Files using llmobserve: {results['files_with_llmobserve']}")
    print(f"  Files with API calls: {results['files_with_api_calls']}")
    print(f"  Files with sections: {results['files_with_sections']}")
    print(f"  Total API calls found: {results['total_api_calls']}")
    print(f"  Total sections found: {results['total_sections']}")
    print(f"  Unlabeled API calls: {len(results['unlabeled_api_calls'])}")
    
    if results['unlabeled_api_calls']:
        print("\n⚠️  Unlabeled API calls:")
        for call in results['unlabeled_api_calls'][:5]:  # Show first 5
            print(f"  - {call['file']}:{call['line']} - {call['call']}")
    
    print("\n" + "=" * 80)
    print("LIMITATIONS:")
    print("=" * 80)
    print("✅ Can parse AST (functions, classes, imports)")
    print("✅ Can find API call patterns (OpenAI, Anthropic, etc.)")
    print("✅ Can detect section() usage")
    print("❌ Cannot understand semantic meaning")
    print("❌ Cannot check if API calls are actually inside sections")
    print("❌ Cannot suggest good section names")
    print("❌ No understanding of code flow/context")
    print("\n💡 This is why AI (like me) is better for complex analysis!")


