"""
AI-powered automatic instrumentation for LLMObserve.

Uses LLMObserve backend (Claude API) to analyze code and suggest/apply agent labels.
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
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class AIInstrumenter:
    """AI-powered code instrumenter using LLMObserve backend."""
    
    def __init__(
        self, 
        collector_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize AI instrumenter.
        
        Args:
            collector_url: LLMObserve collector URL (e.g., "https://llmobserve-production.up.railway.app")
            api_key: Your LLMObserve API key
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests package not installed. "
                "Install with: pip install requests"
            )
        
        self.collector_url = collector_url or os.getenv("LLMOBSERVE_COLLECTOR_URL")
        self.api_key = api_key or os.getenv("LLMOBSERVE_API_KEY")
        
        if not self.collector_url:
            raise ValueError(
                "LLMObserve collector URL required. "
                "Set LLMOBSERVE_COLLECTOR_URL env var or pass collector_url parameter."
            )
        
        if not self.api_key:
            raise ValueError(
                "LLMObserve API key required. "
                "Set LLMOBSERVE_API_KEY env var or pass api_key parameter. "
                "Get your API key from https://llmobserve.com/settings"
            )
        
        # Determine AI endpoint based on collector URL
        if "railway.app" in self.collector_url or "localhost" in self.collector_url:
            # Production or local backend
            self.ai_endpoint = self.collector_url.replace(":8000", "").rstrip("/") + "/api/ai-instrument"
        else:
            # Default to web app endpoint
            self.ai_endpoint = "https://llmobserve.com/api/ai-instrument"
    
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
        Analyze Python code and suggest instrumentation using LLMObserve backend.
        
        Args:
            code: Python code to analyze
            file_path: Optional file path for context
            
        Returns:
            Dict with 'suggestions' (list of instrumentation suggestions)
        """
        try:
            # Call LLMObserve backend API
            response = requests.post(
                self.ai_endpoint,
                json={
                    "code": code,
                    "file_path": file_path
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=60  # AI analysis can take a bit
            )
            
            if response.status_code == 401:
                raise ValueError(
                    "Invalid API key. Get your API key from https://llmobserve.com/settings"
                )
            
            if not response.ok:
                error_data = response.json() if response.headers.get("content-type") == "application/json" else {}
                raise RuntimeError(
                    f"Backend API error: {response.status_code} - {error_data.get('error', response.text)}"
                )
            
            data = response.json()
            
            return {
                "file_path": file_path,
                "suggestions": data.get("suggestions", []),
                "response_text": data.get("response_text", "")
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[ai_instrument] Network error: {e}")
            raise RuntimeError(f"Failed to connect to LLMObserve backend: {e}")
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


def preview_instrumentation(
    file_path: str, 
    collector_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> None:
    """
    Preview AI-suggested instrumentation without applying.
    
    Args:
        file_path: Path to Python file
        collector_url: LLMObserve collector URL
        api_key: Your LLMObserve API key
    """
    instrumenter = AIInstrumenter(collector_url=collector_url, api_key=api_key)
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
    collector_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict:
    """
    Auto-instrument a Python file with LLMObserve labels.
    
    Args:
        file_path: Path to Python file
        auto_apply: If True, automatically apply changes
        collector_url: LLMObserve collector URL
        api_key: Your LLMObserve API key
        
    Returns:
        Dict with analysis and instrumentation results
    """
    instrumenter = AIInstrumenter(collector_url=collector_url, api_key=api_key)
    result = instrumenter.instrument_file(file_path, auto_apply=auto_apply)
    
    if result['applied']:
        print(f"\n✅ Applied {len(result['suggestions'])} changes to {file_path}")
        print(f"   Backup created: {file_path}.bak")
    else:
        print(f"\n📋 {result['message']}")
    
    return result

