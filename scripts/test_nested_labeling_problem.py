"""
PROBLEM: Nested labeling gets messed up when there's code BETWEEN section start and API call.

Scenario:
- Tool A calls Tool B
- Tool B has setup work BEFORE entering its section
- That setup work (or API calls) won't be properly attributed to Tool B
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from llmobserve import observe, section
from llmobserve.context import _get_section_stack, get_section_path

observe("http://localhost:8000")

def print_state(label: str):
    stack = _get_section_stack()
    path = get_section_path()
    print(f"\n[{label}]")
    print(f"  Path: {path}")
    print(f"  Stack: {[s['label'] for s in stack]}")

print("=" * 80)
print("❌ PROBLEM: Setup code outside section")
print("=" * 80)

def tool_B():
    """Tool B has setup work BEFORE its section."""
    print("\n--- Inside tool_B() ---")
    
    # ❌ PROBLEM: This code runs OUTSIDE any section
    # If this makes an API call, it won't be attributed to tool:B
    print("  → Setup work (fetching config, validating input, etc.)")
    print("  → If an API call happens here, it's NOT in tool:B's section!")
    
    # Only NOW do we enter the section
    with section("tool:B"):
        print("  → Now inside tool:B section")
        print("  → API call happens here - properly tracked")
        # response = client.chat.completions.create(...)
    
    print("  → More work after section (also not tracked as tool:B)")

def tool_A():
    """Tool A calls Tool B."""
    with section("tool:A"):
        print("\n--- Inside tool_A() with tool:A section ---")
        print("  → Tool A setup work")
        
        # Call Tool B
        print("  → Calling tool_B()")
        tool_B()
        
        print("  → Tool A cleanup")

print("\n🔴 PROBLEM SCENARIO:")
print_state("Before tool_A")
tool_A()
print_state("After tool_A")

print("\n" + "=" * 80)
print("✅ SOLUTION 1: Wrap entire function in section")
print("=" * 80)

def tool_B_fixed_v1():
    """Solution: Wrap entire function."""
    with section("tool:B"):
        print("\n--- Inside tool_B_fixed_v1() ---")
        print("  → Setup work (NOW inside tool:B section)")
        print("  → API call (properly tracked)")
        print("  → Cleanup (also tracked)")

def tool_A_fixed_v1():
    with section("tool:A"):
        print("\n--- Inside tool_A_fixed_v1() ---")
        tool_B_fixed_v1()

print("\n✅ FIXED SCENARIO 1:")
print_state("Before tool_A_fixed_v1")
tool_A_fixed_v1()
print_state("After tool_A_fixed_v1")

print("\n" + "=" * 80)
print("✅ SOLUTION 2: Use step: sections for internal work")
print("=" * 80)

def tool_B_fixed_v2():
    """Solution: Use step: for internal work."""
    with section("tool:B"):
        # Setup work gets its own step
        with section("step:setup"):
            print("\n--- Inside tool_B_fixed_v2() ---")
            print("  → Setup work (tracked as tool:B/step:setup)")
        
        # Main API call
        print("  → API call (tracked as tool:B)")
        # response = client.chat.completions.create(...)
        
        # Cleanup
        with section("step:cleanup"):
            print("  → Cleanup (tracked as tool:B/step:cleanup)")

def tool_A_fixed_v2():
    with section("tool:A"):
        tool_B_fixed_v2()

print("\n✅ FIXED SCENARIO 2:")
print_state("Before tool_A_fixed_v2")
tool_A_fixed_v2()
print_state("After tool_A_fixed_v2")

print("\n" + "=" * 80)
print("✅ SOLUTION 3: Decorator (automatic wrapping)")
print("=" * 80)

from llmobserve import trace

@trace(tool="B")
def tool_B_fixed_v3():
    """Solution: Use @trace decorator - automatically wraps entire function."""
    print("\n--- Inside tool_B_fixed_v3() (auto-wrapped by @trace) ---")
    print("  → Setup work (automatically in tool:B section)")
    print("  → API call (properly tracked)")
    print("  → Cleanup (also tracked)")

@trace(tool="A")
def tool_A_fixed_v3():
    tool_B_fixed_v3()

print("\n✅ FIXED SCENARIO 3:")
print_state("Before tool_A_fixed_v3")
tool_A_fixed_v3()
print_state("After tool_A_fixed_v3")

print("\n" + "=" * 80)
print("📝 SUMMARY")
print("=" * 80)
print("""
PROBLEM:
  - If you have setup code BEFORE entering a section, that code isn't tracked
  - API calls in that setup code won't be attributed to the tool

SOLUTIONS:
  1. Wrap entire function in section() - simplest
  2. Use step: sections for internal work - more granular
  3. Use @trace decorator - automatic, but less control

RECOMMENDATION:
  - For simple tools: Wrap entire function
  - For complex tools: Use step: sections for clarity
  - For many tools: Use @trace decorator for convenience
""")

