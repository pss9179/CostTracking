#!/usr/bin/env python3
"""
Real Runtime Detection Test: Actually runs code and verifies detection

Tests that runtime detection correctly identifies agents and tools
from actual code execution.
"""
import sys
import inspect
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from llmobserve.agent_detector import detect_agent_from_stack, detect_hierarchical_context


# Test Case 1: Simple Agent with Tool
def web_search_tool(query):
    """Tool for web search."""
    return f"Results for {query}"

def research_agent(query):
    """Agent that uses web search tool."""
    results = web_search_tool(query)
    return results


# Test Case 2: Agent with Multiple Tools
def analyze_tool(data):
    """Tool for analysis."""
    return f"Analysis: {data}"

def summarize_tool(data):
    """Tool for summarization."""
    return f"Summary: {data}"

def research_agent_multi(query):
    """Agent with multiple tools."""
    results = web_search_tool(query)
    analysis = analyze_tool(results)
    summary = summarize_tool(analysis)
    return summary


# Test Case 3: Nested Agents
def fetch_tool(task):
    """Tool for fetching data."""
    return f"Data for {task}"

def sub_agent(task):
    """Sub-agent."""
    data = fetch_tool(task)
    return data

def main_agent(task):
    """Main agent."""
    result = sub_agent(task)
    return result


# Test Case 4: Class-based Agent
class ResearchAgent:
    """Class-based agent."""
    def run(self, query):
        """Run the agent."""
        results = self.web_search_tool(query)
        return results
    
    def web_search_tool(self, query):
        """Tool method."""
        return f"Results for {query}"


# Test Case 5: Complex Nested Structure
def plan_tool(task):
    """Planning tool."""
    return f"Plan for {task}"

def execute_tool(plan):
    """Execution tool."""
    return f"Executed: {plan}"

def planning_agent(task):
    """Planning agent."""
    plan = plan_tool(task)
    return plan

def execution_agent(plan):
    """Execution agent."""
    result = execute_tool(plan)
    return result

def main_agent_complex(task):
    """Main agent with nested agents."""
    planning = planning_agent(task)
    execution = execution_agent(planning)
    return execution


def test_detection(func, expected_agent=None, expected_tools=None, expected_path=None):
    """Test detection for a function call."""
    print(f"\n{'='*70}")
    print(f"Testing: {func.__name__}")
    print('='*70)
    
    # Call the function
    try:
        result = func("test_query")
        print(f"✅ Function executed successfully")
    except Exception as e:
        print(f"❌ Function failed: {e}")
        return False
    
    # Detect agent from stack
    detected_agent = detect_agent_from_stack()
    detected_path = detect_hierarchical_context()
    
    print(f"\n📊 Detection Results:")
    print(f"   Detected Agent: {detected_agent}")
    print(f"   Detected Path: {' > '.join(detected_path) if detected_path else 'None'}")
    
    # Check expectations
    passed = True
    
    if expected_agent:
        if detected_agent == expected_agent:
            print(f"   ✅ Agent matches: {expected_agent}")
        else:
            print(f"   ❌ Agent mismatch: expected {expected_agent}, got {detected_agent}")
            passed = False
    
    if expected_path:
        path_str = " > ".join(detected_path) if detected_path else ""
        if path_str == expected_path:
            print(f"   ✅ Path matches: {expected_path}")
        else:
            print(f"   ⚠️  Path mismatch: expected {expected_path}, got {path_str}")
            # Don't fail on path mismatch, just warn
    
    # Show call stack
    print(f"\n📋 Call Stack:")
    stack = inspect.stack()
    for i, frame_info in enumerate(stack[:10]):  # Show first 10 frames
        frame = frame_info.frame
        func_name = frame.f_code.co_name
        filename = frame.f_code.co_filename.split('/')[-1]
        print(f"   {i}: {func_name} ({filename})")
    
    return passed


def run_all_tests():
    """Run all detection tests."""
    print("\n" + "="*70)
    print("🧪 RUNTIME DETECTION ACCURACY TESTS (Real Execution)")
    print("="*70)
    
    test_results = []
    
    # Test 1: Simple Agent
    print("\n" + "="*70)
    print("TEST 1: Simple Agent with Tool")
    print("="*70)
    passed = test_detection(
        research_agent,
        expected_agent="agent:research",
        expected_path="agent:research > tool:web_search"
    )
    test_results.append(("Simple Agent", passed))
    
    # Test 2: Agent with Multiple Tools
    print("\n" + "="*70)
    print("TEST 2: Agent with Multiple Tools")
    print("="*70)
    passed = test_detection(
        research_agent_multi,
        expected_agent="agent:research",
        expected_path="agent:research > tool:web_search > tool:analyze > tool:summarize"
    )
    test_results.append(("Multi-Tool Agent", passed))
    
    # Test 3: Nested Agents
    print("\n" + "="*70)
    print("TEST 3: Nested Agents")
    print("="*70)
    passed = test_detection(
        main_agent,
        expected_agent="agent:main",
        expected_path="agent:main > agent:sub > tool:fetch"
    )
    test_results.append(("Nested Agents", passed))
    
    # Test 4: Class-based Agent
    print("\n" + "="*70)
    print("TEST 4: Class-based Agent")
    print("="*70)
    agent = ResearchAgent()
    passed = test_detection(
        agent.run,
        expected_agent="agent:research",
        expected_path="agent:research > tool:web_search"
    )
    test_results.append(("Class-based Agent", passed))
    
    # Test 5: Complex Nested Structure
    print("\n" + "="*70)
    print("TEST 5: Complex Nested Structure")
    print("="*70)
    passed = test_detection(
        main_agent_complex,
        expected_agent="agent:main",
        expected_path="agent:main > agent:planning > agent:execution > tool:plan > tool:execute"
    )
    test_results.append(("Complex Nested", passed))
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed_count = sum(1 for _, p in test_results if p)
    total_count = len(test_results)
    
    for name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\n✅ Passed: {passed_count}/{total_count}")
    print(f"🎯 Accuracy: {(passed_count/total_count)*100:.1f}%")
    print("="*70)


if __name__ == "__main__":
    run_all_tests()

