"""
AI-powered automatic instrumentation for LLMObserve.

Uses Claude API to analyze code and suggest/apply agent labels.
"""
import os
import re
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json

logger = logging.getLogger("llmobserve")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class AIInstrumenter:
    """AI-powered code instrumenter using Claude."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize AI instrumenter.
        
        Args:
            api_key: Anthropic API key. If None, reads from ANTHROPIC_API_KEY env var.
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )
        
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. "
                "Set ANTHROPIC_API_KEY env var or pass api_key parameter."
            )
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def analyze_file(self, file_path: str) -> Dict:
        """
        Analyze a Python file and suggest instrumentation.
        
        Args:
            file_path: Path to Python file to analyze
            
        Returns:
            Dict with 'suggestions' (list of instrumentation suggestions)
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path.suffix == ".py":
            raise ValueError(f"Only Python files supported, got: {path.suffix}")
        
        with open(path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        return self.analyze_code(code, file_path=str(path))
    
    def analyze_code(self, code: str, file_path: Optional[str] = None) -> Dict:
        """
        Analyze Python code and suggest instrumentation.
        
        Args:
            code: Python code to analyze
            file_path: Optional file path for context
            
        Returns:
            Dict with 'suggestions' (list of instrumentation suggestions)
        """
        prompt = self._build_analysis_prompt(code, file_path)
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract text from response
            response_text = response.content[0].text
            
            # Parse JSON response
            suggestions = self._parse_response(response_text)
            
            return {
                "file_path": file_path,
                "suggestions": suggestions,
                "response_text": response_text
            }
            
        except Exception as e:
            logger.error(f"[ai_instrument] Analysis failed: {e}")
            raise
    
    def instrument_file(
        self, 
        file_path: str, 
        auto_apply: bool = False,
        backup: bool = True
    ) -> Dict:
        """
        Analyze and optionally apply instrumentation to a file.
        
        Args:
            file_path: Path to Python file
            auto_apply: If True, automatically apply changes
            backup: If True, create .bak backup before modifying
            
        Returns:
            Dict with analysis results and applied changes
        """
        # Analyze file
        analysis = self.analyze_file(file_path)
        
        if not analysis['suggestions']:
            return {
                **analysis,
                "applied": False,
                "message": "No instrumentation needed"
            }
        
        if not auto_apply:
            return {
                **analysis,
                "applied": False,
                "message": "Review suggestions and run with --auto-apply to apply"
            }
        
        # Apply changes
        path = Path(file_path)
        
        # Create backup
        if backup:
            backup_path = path.with_suffix(path.suffix + '.bak')
            import shutil
            shutil.copy2(path, backup_path)
            logger.info(f"[ai_instrument] Created backup: {backup_path}")
        
        # Read original code
        with open(path, 'r', encoding='utf-8') as f:
            original_code = f.read()
        
        # Apply suggestions
        modified_code = self._apply_suggestions(original_code, analysis['suggestions'])
        
        # Write modified code
        with open(path, 'w', encoding='utf-8') as f:
            f.write(modified_code)
        
        return {
            **analysis,
            "applied": True,
            "modified_code": modified_code,
            "message": f"Applied {len(analysis['suggestions'])} changes"
        }
    
    def _build_analysis_prompt(self, code: str, file_path: Optional[str] = None) -> str:
        """Build prompt for Claude to analyze code."""
        return f"""You are an expert Python developer helping instrument code for LLMObserve cost tracking.

LLMObserve tracks LLM API costs using these labeling methods:

1. **@agent decorator** - Mark agent entry points:
```python
from llmobserve import agent

@agent("researcher")
def research_agent(query):
    # All API calls here auto-labeled as "agent:researcher"
    return result
```

2. **section() context manager** - Label code blocks:
```python
from llmobserve import section

with section("agent:researcher"):
    # All API calls here auto-labeled
    response = openai_call()
```

3. **wrap_all_tools()** - Wrap tool lists for frameworks:
```python
from llmobserve import wrap_all_tools

tools = [web_search, calculator]
wrapped_tools = wrap_all_tools(tools)
agent = Agent(tools=wrapped_tools)  # LangChain, CrewAI, etc.
```

**Your task:**
Analyze this Python code and suggest where to add LLMObserve instrumentation.

**Focus on:**
- Functions that orchestrate LLM calls (likely agents)
- Framework usage (LangChain, CrewAI, AutoGen, LlamaIndex)
- Tool definitions
- Multi-step workflows

**Output format:**
Return ONLY valid JSON with this structure:
```json
{{
  "suggestions": [
    {{
      "type": "decorator" | "context_manager" | "wrap_tools",
      "line_number": <int>,
      "function_name": "<name>",
      "suggested_label": "<label>",
      "code_before": "<original line>",
      "code_after": "<modified line>",
      "reason": "<why this needs instrumentation>"
    }}
  ]
}}
```

**File:** {file_path or "N/A"}

**Code to analyze:**
```python
{code}
```

**Important:**
- Return ONLY JSON, no markdown or explanations
- Suggest agent names based on function purpose (e.g., "researcher", "writer", "analyzer")
- For LangChain agents, suggest wrap_all_tools() on the tools list
- Don't suggest instrumentation for non-LLM code
- Be conservative - only suggest where it clearly makes sense"""

    def _parse_response(self, response_text: str) -> List[Dict]:
        """Parse Claude's JSON response."""
        try:
            # Try to extract JSON from response
            # Sometimes Claude wraps it in markdown
            json_match = re.search(r'```json\s*\n(.*?)\n```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # Try without markdown
                json_text = response_text.strip()
            
            data = json.loads(json_text)
            return data.get("suggestions", [])
        except json.JSONDecodeError as e:
            logger.error(f"[ai_instrument] Failed to parse response: {e}")
            logger.debug(f"[ai_instrument] Response text: {response_text}")
            return []
    
    def _apply_suggestions(self, code: str, suggestions: List[Dict]) -> str:
        """Apply instrumentation suggestions to code."""
        lines = code.split('\n')
        
        # Check if llmobserve imports exist
        has_llmobserve_import = any('from llmobserve import' in line or 'import llmobserve' in line for line in lines)
        
        # Collect needed imports
        needed_imports = set()
        for suggestion in suggestions:
            if suggestion['type'] == 'decorator':
                needed_imports.add('agent')
            elif suggestion['type'] == 'context_manager':
                needed_imports.add('section')
            elif suggestion['type'] == 'wrap_tools':
                needed_imports.add('wrap_all_tools')
        
        # Add imports if needed
        if needed_imports and not has_llmobserve_import:
            import_line = f"from llmobserve import {', '.join(sorted(needed_imports))}"
            # Find where to insert (after docstrings and existing imports)
            insert_index = 0
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                    if not stripped.startswith('import ') and not stripped.startswith('from '):
                        insert_index = i
                        break
            lines.insert(insert_index, import_line)
            logger.info(f"[ai_instrument] Added import: {import_line}")
        
        # Sort suggestions by line number (descending) to avoid line number shifts
        sorted_suggestions = sorted(suggestions, key=lambda s: s.get('line_number', 0), reverse=True)
        
        # Apply each suggestion
        for suggestion in sorted_suggestions:
            line_num = suggestion.get('line_number', 0)
            if line_num <= 0 or line_num > len(lines):
                logger.warning(f"[ai_instrument] Invalid line number: {line_num}")
                continue
            
            # Line numbers are 1-indexed
            idx = line_num - 1
            
            if suggestion['type'] == 'decorator':
                # Add decorator before function
                label = suggestion['suggested_label']
                indent = len(lines[idx]) - len(lines[idx].lstrip())
                decorator_line = ' ' * indent + f'@agent("{label}")'
                lines.insert(idx, decorator_line)
                logger.info(f"[ai_instrument] Added decorator at line {line_num}: {decorator_line.strip()}")
            
            elif suggestion['type'] == 'context_manager':
                # Wrap block with section() - this is more complex
                # For now, just add a comment suggesting manual wrapping
                label = suggestion['suggested_label']
                indent = len(lines[idx]) - len(lines[idx].lstrip())
                comment_line = ' ' * indent + f'# TODO: Wrap with: with section("{label}"):'
                lines.insert(idx, comment_line)
                logger.info(f"[ai_instrument] Added comment at line {line_num}: {comment_line.strip()}")
            
            elif suggestion['type'] == 'wrap_tools':
                # Replace tools = [...] with tools = wrap_all_tools([...])
                original = lines[idx]
                if 'wrap_all_tools' not in original:
                    # Simple replacement: find tools = and wrap the value
                    modified = re.sub(
                        r'(\w+\s*=\s*)(\[.*\])',
                        r'\1wrap_all_tools(\2)',
                        original
                    )
                    if modified != original:
                        lines[idx] = modified
                        logger.info(f"[ai_instrument] Wrapped tools at line {line_num}")
        
        return '\n'.join(lines)


def preview_instrumentation(file_path: str, api_key: Optional[str] = None) -> None:
    """
    Preview AI-suggested instrumentation without applying.
    
    Args:
        file_path: Path to Python file
        api_key: Optional Anthropic API key
    """
    instrumenter = AIInstrumenter(api_key=api_key)
    result = instrumenter.analyze_file(file_path)
    
    print(f"\n🔍 Analysis of {file_path}\n")
    
    if not result['suggestions']:
        print("✅ No instrumentation needed - code looks good!")
        return
    
    print(f"Found {len(result['suggestions'])} suggestions:\n")
    
    for i, suggestion in enumerate(result['suggestions'], 1):
        print(f"{i}. Line {suggestion.get('line_number', 'N/A')} - {suggestion.get('type', 'unknown')}")
        print(f"   Label: {suggestion.get('suggested_label', 'N/A')}")
        print(f"   Function: {suggestion.get('function_name', 'N/A')}")
        print(f"   Reason: {suggestion.get('reason', 'N/A')}")
        print(f"   Before: {suggestion.get('code_before', 'N/A')}")
        print(f"   After:  {suggestion.get('code_after', 'N/A')}")
        print()
    
    print("💡 To apply these changes, run with --auto-apply flag")
    print("   A backup (.bak) will be created automatically")


def auto_instrument(
    file_path: str, 
    auto_apply: bool = False,
    api_key: Optional[str] = None
) -> Dict:
    """
    Auto-instrument a Python file with LLMObserve labels.
    
    Args:
        file_path: Path to Python file
        auto_apply: If True, automatically apply changes
        api_key: Optional Anthropic API key
        
    Returns:
        Dict with analysis and instrumentation results
    """
    instrumenter = AIInstrumenter(api_key=api_key)
    result = instrumenter.instrument_file(file_path, auto_apply=auto_apply)
    
    if result['applied']:
        print(f"\n✅ Applied {len(result['suggestions'])} changes to {file_path}")
        print(f"   Backup created: {file_path}.bak")
    else:
        print(f"\n📋 {result['message']}")
    
    return result

