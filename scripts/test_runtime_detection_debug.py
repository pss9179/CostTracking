#!/usr/bin/env python3
"""
Debug Runtime Detection: See what's actually being detected

Shows the call stack and what patterns match.
"""
import sys
import inspect
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from llmobserve.agent_detector import (
    detect_agent_from_stack,
    detect_hierarchical_context,
    AGENT_PATTERNS,
    TOOL_PATTERNS,
    STEP_PATTERNS
)
import re


def _matches_pattern(name: str, patterns):
    """Check if name matches any pattern."""
    for pattern in patterns:
        if re.search(pattern, name, re.IGNORECASE):
            return True
    return False


def web_search_tool(query):
    """Tool for web search."""
    print("\n" + "="*70)
    print("Inside web_search_tool()")
    print("="*70)
    
    # Show call stack
    stack = inspect.stack()
    print("\n📋 Call Stack:")
    for i, frame_info in enumerate(stack[:8]):
        frame = frame_info.frame
        func_name = frame.f_code.co_name
        filename = frame.f_code.co_filename.split('/')[-1]
        
        # Check patterns
        is_agent = _matches_pattern(func_name, AGENT_PATTERNS)
        is_tool = _matches_pattern(func_name, TOOL_PATTERNS)
        is_step = _matches_pattern(func_name, STEP_PATTERNS)
        
        print(f"  {i}: {func_name} ({filename})")
        if is_agent:
            print(f"      ✅ Matches AGENT pattern")
        if is_tool:
            print(f"      ✅ Matches TOOL pattern")
        if is_step:
            print(f"      ✅ Matches STEP pattern")
    
    # Detect
    detected = detect_agent_from_stack()
    path = detect_hierarchical_context()
    
    print(f"\n📊 Detection Results:")
    print(f"   Detected: {detected}")
    print(f"   Path: {' > '.join(path) if path else 'None'}")
    
    return f"Results for {query}"


def research_agent(query):
    """Agent that uses web search tool."""
    print("\n" + "="*70)
    print("Inside research_agent()")
    print("="*70)
    
    # Show call stack
    stack = inspect.stack()
    print("\n📋 Call Stack:")
    for i, frame_info in enumerate(stack[:8]):
        frame = frame_info.frame
        func_name = frame.f_code.co_name
        filename = frame.f_code.co_filename.split('/')[-1]
        
        # Check patterns
        is_agent = _matches_pattern(func_name, AGENT_PATTERNS)
        is_tool = _matches_pattern(func_name, TOOL_PATTERNS)
        is_step = _matches_pattern(func_name, STEP_PATTERNS)
        
        print(f"  {i}: {func_name} ({filename})")
        if is_agent:
            print(f"      ✅ Matches AGENT pattern")
        if is_tool:
            print(f"      ✅ Matches TOOL pattern")
        if is_step:
            print(f"      ✅ Matches STEP pattern")
    
    # Detect
    detected = detect_agent_from_stack()
    path = detect_hierarchical_context()
    
    print(f"\n📊 Detection Results:")
    print(f"   Detected: {detected}")
    print(f"   Path: {' > '.join(path) if path else 'None'}")
    
    results = web_search_tool(query)
    return results


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔍 DEBUG: Runtime Detection")
    print("="*70)
    
    print("\n📋 Patterns:")
    print(f"   AGENT_PATTERNS: {AGENT_PATTERNS[:3]}...")
    print(f"   TOOL_PATTERNS: {TOOL_PATTERNS[:3]}...")
    print(f"   STEP_PATTERNS: {STEP_PATTERNS[:3]}...")
    
    result = research_agent("test")

