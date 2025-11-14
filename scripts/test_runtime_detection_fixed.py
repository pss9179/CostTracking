#!/usr/bin/env python3
"""
Fixed Runtime Detection Test: Calls detection from within agent functions

Tests that runtime detection correctly identifies agents and tools
when called from within the actual agent/tool functions.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from llmobserve.agent_detector import detect_agent_from_stack, detect_hierarchical_context


# Test Case 1: Simple Agent with Tool
def web_search_tool(query):
    """Tool for web search."""
    # Detect from within tool
    detected = detect_agent_from_stack()
    path = detect_hierarchical_context()
    return {
        "result": f"Results for {query}",
        "detected_agent": detected,
        "detected_path": path
    }

def research_agent(query):
    """Agent that uses web search tool."""
    # Detect from within agent
    detected = detect_agent_from_stack()
    path = detect_hierarchical_context()
    
    results = web_search_tool(query)
    
    return {
        "agent_detected": detected,
        "agent_path": path,
        "tool_detected": results["detected_agent"],
        "tool_path": results["detected_path"],
        "data": results["result"]
    }


# Test Case 2: Agent with Multiple Tools
def analyze_tool(data):
    """Tool for analysis."""
    detected = detect_agent_from_stack()
    path = detect_hierarchical_context()
    return {
        "result": f"Analysis: {data}",
        "detected_agent": detected,
        "detected_path": path
    }

def summarize_tool(data):
    """Tool for summarization."""
    detected = detect_agent_from_stack()
    path = detect_hierarchical_context()
    return {
        "result": f"Summary: {data}",
        "detected_agent": detected,
        "detected_path": path
    }

def research_agent_multi(query):
    """Agent with multiple tools."""
    agent_detected = detect_agent_from_stack()
    agent_path = detect_hierarchical_context()
    
    results = web_search_tool(query)
    analysis = analyze_tool(results["result"])
    summary = summarize_tool(analysis["result"])
    
    return {
        "agent_detected": agent_detected,
        "agent_path": agent_path,
        "tools": [
            {"name": "web_search", "detected": results["detected_agent"], "path": results["detected_path"]},
            {"name": "analyze", "detected": analysis["detected_agent"], "path": analysis["detected_path"]},
            {"name": "summarize", "detected": summary["detected_agent"], "path": summary["detected_path"]},
        ]
    }


# Test Case 3: Nested Agents
def fetch_tool(task):
    """Tool for fetching data."""
    detected = detect_agent_from_stack()
    path = detect_hierarchical_context()
    return {
        "result": f"Data for {task}",
        "detected_agent": detected,
        "detected_path": path
    }

def sub_agent(task):
    """Sub-agent."""
    agent_detected = detect_agent_from_stack()
    agent_path = detect_hierarchical_context()
    
    data = fetch_tool(task)
    
    return {
        "agent_detected": agent_detected,
        "agent_path": agent_path,
        "tool_detected": data["detected_agent"],
        "tool_path": data["detected_path"],
        "data": data["result"]
    }

def main_agent(task):
    """Main agent."""
    agent_detected = detect_agent_from_stack()
    agent_path = detect_hierarchical_context()
    
    result = sub_agent(task)
    
    return {
        "main_agent_detected": agent_detected,
        "main_agent_path": agent_path,
        "sub_agent": result
    }


# Test Case 4: Class-based Agent
class ResearchAgent:
    """Class-based agent."""
    def run(self, query):
        """Run the agent."""
        agent_detected = detect_agent_from_stack()
        agent_path = detect_hierarchical_context()
        
        results = self.web_search_tool(query)
        
        return {
            "agent_detected": agent_detected,
            "agent_path": agent_path,
            "tool_detected": results["detected_agent"],
            "tool_path": results["detected_path"],
            "data": results["result"]
        }
    
    def web_search_tool(self, query):
        """Tool method."""
        detected = detect_agent_from_stack()
        path = detect_hierarchical_context()
        return {
            "result": f"Results for {query}",
            "detected_agent": detected,
            "detected_path": path
        }


# Test Case 5: Complex Nested Structure
def plan_tool(task):
    """Planning tool."""
    detected = detect_agent_from_stack()
    path = detect_hierarchical_context()
    return {
        "result": f"Plan for {task}",
        "detected_agent": detected,
        "detected_path": path
    }

def execute_tool(plan):
    """Execution tool."""
    detected = detect_agent_from_stack()
    path = detect_hierarchical_context()
    return {
        "result": f"Executed: {plan}",
        "detected_agent": detected,
        "detected_path": path
    }

def planning_agent(task):
    """Planning agent."""
    agent_detected = detect_agent_from_stack()
    agent_path = detect_hierarchical_context()
    
    plan = plan_tool(task)
    
    return {
        "agent_detected": agent_detected,
        "agent_path": agent_path,
        "tool_detected": plan["detected_agent"],
        "tool_path": plan["detected_path"],
        "plan": plan["result"]
    }

def execution_agent(plan):
    """Execution agent."""
    agent_detected = detect_agent_from_stack()
    agent_path = detect_hierarchical_context()
    
    result = execute_tool(plan)
    
    return {
        "agent_detected": agent_detected,
        "agent_path": agent_path,
        "tool_detected": result["detected_agent"],
        "tool_path": result["detected_path"],
        "result": result["result"]
    }

def main_agent_complex(task):
    """Main agent with nested agents."""
    agent_detected = detect_agent_from_stack()
    agent_path = detect_hierarchical_context()
    
    planning = planning_agent(task)
    execution = execution_agent(planning["plan"])
    
    return {
        "main_agent_detected": agent_detected,
        "main_agent_path": agent_path,
        "planning_agent": planning,
        "execution_agent": execution
    }


def test_case(name, func, expected_agent=None, expected_tool=None):
    """Test a single case."""
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print('='*70)
    
    try:
        result = func("test_query")
        print(f"✅ Function executed successfully")
    except Exception as e:
        print(f"❌ Function failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Check agent detection
    agent_detected = result.get("agent_detected") or result.get("main_agent_detected")
    agent_path = result.get("agent_path") or result.get("main_agent_path") or []
    
    print(f"\n📊 Agent Detection:")
    print(f"   Detected: {agent_detected}")
    print(f"   Path: {' > '.join(agent_path) if agent_path else 'None'}")
    
    if expected_agent:
        if agent_detected == expected_agent:
            print(f"   ✅ Matches expected: {expected_agent}")
        else:
            print(f"   ❌ Expected: {expected_agent}, Got: {agent_detected}")
    
    # Check tool detection
    tool_detected = result.get("tool_detected")
    if tool_detected:
        print(f"\n📊 Tool Detection:")
        print(f"   Detected: {tool_detected}")
        if expected_tool:
            if tool_detected == expected_tool:
                print(f"   ✅ Matches expected: {expected_tool}")
            else:
                print(f"   ⚠️  Expected: {expected_tool}, Got: {tool_detected}")
    
    # Check multiple tools
    tools = result.get("tools", [])
    if tools:
        print(f"\n📊 Multiple Tools Detected:")
        for tool in tools:
            print(f"   - {tool['name']}: {tool['detected']}")
    
    # Overall result
    agent_match = (not expected_agent) or (agent_detected == expected_agent)
    tool_match = (not expected_tool) or (tool_detected == expected_tool)
    
    if agent_match and tool_match:
        print(f"\n✅ TEST PASSED")
        return True
    else:
        print(f"\n❌ TEST FAILED")
        return False


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("🧪 RUNTIME DETECTION ACCURACY TESTS")
    print("="*70)
    
    results = []
    
    # Test 1
    passed = test_case(
        "Simple Agent with Tool",
        research_agent,
        expected_agent="agent:research",
        expected_tool="tool:web_search"
    )
    results.append(("Simple Agent", passed))
    
    # Test 2
    passed = test_case(
        "Agent with Multiple Tools",
        research_agent_multi,
        expected_agent="agent:research"
    )
    results.append(("Multi-Tool Agent", passed))
    
    # Test 3
    passed = test_case(
        "Nested Agents",
        main_agent,
        expected_agent="agent:main"
    )
    results.append(("Nested Agents", passed))
    
    # Test 4
    agent = ResearchAgent()
    passed = test_case(
        "Class-based Agent",
        agent.run,
        expected_agent="agent:research",
        expected_tool="tool:web_search"
    )
    results.append(("Class-based Agent", passed))
    
    # Test 5
    passed = test_case(
        "Complex Nested Structure",
        main_agent_complex,
        expected_agent="agent:main"
    )
    results.append(("Complex Nested", passed))
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\n✅ Passed: {passed_count}/{total_count}")
    if total_count > 0:
        accuracy = (passed_count / total_count) * 100
        print(f"🎯 Accuracy: {accuracy:.1f}%")
    print("="*70)
    
    return results


if __name__ == "__main__":
    run_all_tests()

