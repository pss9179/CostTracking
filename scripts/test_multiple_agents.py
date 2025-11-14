"""
Test: Multiple agents - how does it know when one ends and a new one starts?

Key: When a section exits, it pops from stack. Empty stack = new root span.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

import llmobserve
from llmobserve import observe, section, set_customer_id
from llmobserve.context import _get_section_stack, get_section_path

COLLECTOR_URL = os.getenv("LLMOBSERVE_COLLECTOR_URL", "http://localhost:8000")
observe(collector_url=COLLECTOR_URL)
set_customer_id("multi-agent-test")

def print_stack(label: str):
    stack = _get_section_stack()
    path = get_section_path()
    print(f"\n[{label}]")
    print(f"  Stack: {len(stack)} items, Path: {path}")
    if stack:
        for i, entry in enumerate(stack):
            print(f"    [{i}] {entry['label']} (span={entry['span_id'][:8]}...)")

print("=" * 80)
print("FIRST AGENT")
print("=" * 80)

print_stack("Before agent1")

with section("agent:researcher"):
    print_stack("Inside agent1")
    with section("tool:search"):
        print_stack("Inside tool (nested under agent1)")
    print_stack("Back in agent1 after tool")

print_stack("After agent1 EXITS (popped from stack)")

print("\n" + "=" * 80)
print("SECOND AGENT (NEW ROOT)")
print("=" * 80)

print_stack("Before agent2 (stack should be empty)")

with section("agent:analyzer"):
    print_stack("Inside agent2 (parent=None because stack was empty)")
    with section("tool:llm"):
        print_stack("Inside tool (nested under agent2)")

print_stack("After agent2 EXITS")

print("\n" + "=" * 80)
print("RESULT: Two separate root agents")
print("=" * 80)
print("""
agent:researcher (root, parent=None)
└── tool:search (parent=agent:researcher)

agent:analyzer (root, parent=None)  ← SEPARATE ROOT!
└── tool:llm (parent=agent:analyzer)
""")


