"""
REAL TEST: Nested tool calls - tool calling another tool.

This demonstrates:
1. Agent section
2. Tool section that calls another tool section (nested)
3. How the stack properly tracks parent-child relationships
"""

import os
import sys
from pathlib import Path

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

import llmobserve
from llmobserve import observe, section, set_customer_id
from llmobserve.context import _get_section_stack, get_section_path

# Configuration
COLLECTOR_URL = os.getenv("LLMOBSERVE_COLLECTOR_URL", "http://localhost:8000")

print("=" * 80)
print("🧪 NESTED TOOL CALLS TEST")
print("=" * 80)
print(f"Collector: {COLLECTOR_URL}")
print()

# Initialize observability
observe(collector_url=COLLECTOR_URL)
set_customer_id("nested-test")

def print_stack_state(label: str):
    """Print current stack state for debugging."""
    stack = _get_section_stack()
    path = get_section_path()
    print(f"\n[{label}]")
    print(f"  Stack depth: {len(stack)}")
    print(f"  Section path: {path}")
    if stack:
        print("  Stack contents:")
        for i, entry in enumerate(stack):
            parent_info = f"parent={entry['parent_span_id'][:8]}..." if entry.get('parent_span_id') else "parent=None"
            print(f"    [{i}] {entry['label']} (span={entry['span_id'][:8]}..., {parent_info})")
    else:
        print("  Stack: []")
    print()


# Simulate a tool that calls another tool
def inner_tool_function():
    """This is a tool that gets called FROM another tool."""
    print_stack_state("INSIDE inner_tool_function (before section)")
    
    with section("tool:openai_api"):
        print_stack_state("INSIDE tool:openai_api section")
        # Simulate API call - this would normally be tracked by HTTP interceptor
        print("  → Making OpenAI API call (would be tracked automatically)")
        print("  → This API call's parent_span_id would be tool:openai_api's span_id")
    
    print_stack_state("AFTER tool:openai_api section (popped)")


def outer_tool_function():
    """This is a tool that calls another tool."""
    print_stack_state("INSIDE outer_tool_function (before section)")
    
    with section("tool:web_search"):
        print_stack_state("INSIDE tool:web_search section")
        print("  → Making web search API call")
        
        # HERE'S THE NESTED TOOL CALL
        print("\n  → Calling inner tool (tool:openai_api) from within tool:web_search")
        inner_tool_function()
        
        print_stack_state("BACK in tool:web_search after inner_tool_function")
        print("  → Making another web search API call")
    
    print_stack_state("AFTER tool:web_search section (popped)")


# Main agent code
print("\n" + "=" * 80)
print("STARTING AGENT")
print("=" * 80)

print_stack_state("BEFORE agent section")

with section("agent:researcher"):
    print_stack_state("INSIDE agent:researcher section")
    
    print("\n→ Agent starting work...")
    
    # Call the outer tool
    print("\n→ Calling outer_tool_function (tool:web_search)")
    outer_tool_function()
    
    print_stack_state("BACK in agent:researcher after outer_tool_function")
    
    # Call another tool sequentially
    print("\n→ Calling another tool sequentially")
    with section("tool:pinecone_query"):
        print_stack_state("INSIDE tool:pinecone_query section")
        print("  → Making Pinecone query")
    
    print_stack_state("AFTER tool:pinecone_query section (popped)")

print_stack_state("AFTER agent:researcher section (popped)")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print("\nExpected tree structure:")
print("""
agent:researcher
├── tool:web_search
│   ├── [web search API call] (parent = tool:web_search)
│   └── tool:openai_api  ← NESTED TOOL!
│       └── [OpenAI API call] (parent = tool:openai_api)
│   └── [another web search API call] (parent = tool:web_search)
└── tool:pinecone_query
    └── [Pinecone query] (parent = tool:pinecone_query)
""")

print("\n✅ If the stack state above shows correct nesting, it works!")
print("✅ The key is: when tool:openai_api opens, stack[-1] is tool:web_search")
print("✅ When tool:openai_api closes, it pops, and stack[-1] is back to tool:web_search")


