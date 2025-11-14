#!/usr/bin/env python3
"""
Comprehensive Test Suite: Runtime Agent/Tool Detection Accuracy

Tests that runtime detection correctly identifies agents and tools
automatically from call stack analysis.
"""
import sys
import os
from pathlib import Path

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

# Mock the proxy and collector for testing
import json
from unittest.mock import Mock, patch
from typing import List, Dict, Any

# Import runtime detection
from llmobserve.agent_detector import detect_agent_from_stack, detect_hierarchical_context
from llmobserve.context import set_section, get_current_section, get_section_path


class MockCollector:
    """Mock collector to capture events."""
    def __init__(self):
        self.events = []
    
    def add_event(self, event: Dict[str, Any]):
        """Add event to collection."""
        self.events.append(event)
    
    def get_events(self) -> List[Dict[str, Any]]:
        """Get all collected events."""
        return self.events
    
    def get_agents(self) -> List[str]:
        """Extract unique agents from events."""
        agents = set()
        for event in self.events:
            section = event.get("section", "")
            if section.startswith("agent:"):
                agents.add(section)
        return sorted(list(agents))
    
    def get_tools(self) -> List[str]:
        """Extract unique tools from events."""
        tools = set()
        for event in self.events:
            section = event.get("section", "")
            if section.startswith("tool:"):
                tools.add(section)
        return sorted(list(tools))
    
    def get_section_paths(self) -> List[str]:
        """Extract unique section paths from events."""
        paths = set()
        for event in self.events:
            path = event.get("section_path", "")
            if path:
                paths.add(path)
        return sorted(list(paths))


# Test cases
TEST_CASES = [
    {
        "name": "Simple Agent with Tool",
        "code": """
def research_agent(query):
    results = web_search_tool(query)
    return results

def web_search_tool(query):
    # Simulate API call
    return f"Results for {query}"
""",
        "expected_agents": ["agent:research"],
        "expected_tools": ["tool:web_search"],
        "call": lambda: research_agent("test"),
    },
    {
        "name": "Agent with Multiple Tools",
        "code": """
def research_agent(query):
    results = web_search_tool(query)
    analysis = analyze_tool(results)
    summary = summarize_tool(analysis)
    return summary

def web_search_tool(query):
    return f"Results for {query}"

def analyze_tool(data):
    return f"Analysis: {data}"

def summarize_tool(data):
    return f"Summary: {data}"
""",
        "expected_agents": ["agent:research"],
        "expected_tools": ["tool:web_search", "tool:analyze", "tool:summarize"],
        "call": lambda: research_agent("test"),
    },
    {
        "name": "Nested Agents",
        "code": """
def main_agent(task):
    result = sub_agent(task)
    return result

def sub_agent(task):
    data = fetch_tool(task)
    return data

def fetch_tool(task):
    return f"Data for {task}"
""",
        "expected_agents": ["agent:main", "agent:sub"],
        "expected_tools": ["tool:fetch"],
        "call": lambda: main_agent("test"),
    },
    {
        "name": "Agent with Step",
        "code": """
def research_agent(query):
    step1_result = step_one(query)
    step2_result = step_two(step1_result)
    return step2_result

def step_one(query):
    return f"Step 1: {query}"

def step_two(data):
    return f"Step 2: {data}"
""",
        "expected_agents": ["agent:research"],
        "expected_steps": ["step:one", "step:two"],
        "call": lambda: research_agent("test"),
    },
    {
        "name": "Class-based Agent",
        "code": """
class ResearchAgent:
    def run(self, query):
        results = self.web_search_tool(query)
        return results
    
    def web_search_tool(self, query):
        return f"Results for {query}"
""",
        "expected_agents": ["agent:research"],
        "expected_tools": ["tool:web_search"],
        "call": lambda: ResearchAgent().run("test"),
    },
    {
        "name": "Agent with Async Tools",
        "code": """
async def research_agent(query):
    results = await web_search_tool(query)
    return results

async def web_search_tool(query):
    return f"Results for {query}"
""",
        "expected_agents": ["agent:research"],
        "expected_tools": ["tool:web_search"],
        "call": lambda: None,  # Would need async test
    },
    {
        "name": "Complex Nested Structure",
        "code": """
def main_agent(task):
    planning = planning_agent(task)
    execution = execution_agent(planning)
    return execution

def planning_agent(task):
    plan = plan_tool(task)
    return plan

def execution_agent(plan):
    result = execute_tool(plan)
    return result

def plan_tool(task):
    return f"Plan for {task}"

def execute_tool(plan):
    return f"Executed: {plan}"
""",
        "expected_agents": ["agent:main", "agent:planning", "agent:execution"],
        "expected_tools": ["tool:plan", "tool:execute"],
        "call": lambda: main_agent("test"),
    },
]


def run_test_case(test_case: Dict[str, Any], collector: MockCollector) -> Dict[str, Any]:
    """Run a single test case and verify results."""
    name = test_case["name"]
    code = test_case["code"]
    expected_agents = test_case.get("expected_agents", [])
    expected_tools = test_case.get("expected_tools", [])
    expected_steps = test_case.get("expected_steps", [])
    call_func = test_case.get("call")
    
    # Execute code in namespace
    namespace = {}
    exec(code, namespace)
    
    # Clear collector
    collector.events = []
    
    # Mock event emission
    def mock_emit_event(event):
        collector.add_event(event)
    
    # Run the code with detection
    try:
        if call_func:
            # Simulate runtime detection
            with patch('llmobserve.context._emit_event', side_effect=mock_emit_event):
                # Set up context
                set_section("default")
                
                # Call the function
                result = call_func()
                
                # Detect agents/tools from stack
                detected_agent = detect_agent_from_stack()
                detected_path = detect_hierarchical_context()
                
                # Create mock event
                event = {
                    "section": detected_agent or "default",
                    "section_path": " > ".join(detected_path) if detected_path else "default",
                    "provider": "test",
                    "endpoint": "test",
                }
                collector.add_event(event)
        else:
            # Skip async tests for now
            return {
                "name": name,
                "status": "skipped",
                "reason": "Async test"
            }
    except Exception as e:
        return {
            "name": name,
            "status": "error",
            "error": str(e)
        }
    
    # Extract detected agents/tools
    detected_agents = collector.get_agents()
    detected_tools = collector.get_tools()
    detected_paths = collector.get_section_paths()
    
    # Check accuracy
    agents_correct = set(detected_agents) == set(expected_agents)
    tools_correct = set(detected_tools) == set(expected_tools)
    
    return {
        "name": name,
        "status": "passed" if (agents_correct and tools_correct) else "failed",
        "expected_agents": expected_agents,
        "detected_agents": detected_agents,
        "expected_tools": expected_tools,
        "detected_tools": detected_tools,
        "detected_paths": detected_paths,
        "agents_correct": agents_correct,
        "tools_correct": tools_correct,
    }


def run_all_tests():
    """Run all test cases and report results."""
    print("\n" + "="*70)
    print("🧪 RUNTIME AGENT/TOOL DETECTION ACCURACY TESTS")
    print("="*70)
    
    collector = MockCollector()
    results = []
    
    for test_case in TEST_CASES:
        print(f"\n{'='*70}")
        print(f"TEST: {test_case['name']}")
        print('='*70)
        
        result = run_test_case(test_case, collector)
        results.append(result)
        
        if result["status"] == "skipped":
            print(f"⏭️  SKIPPED: {result.get('reason', 'Unknown')}")
            continue
        
        if result["status"] == "error":
            print(f"❌ ERROR: {result.get('error', 'Unknown error')}")
            continue
        
        print(f"\n📊 Expected Agents: {result['expected_agents']}")
        print(f"📊 Detected Agents: {result['detected_agents']}")
        print(f"✅ Agents Match: {result['agents_correct']}")
        
        print(f"\n📊 Expected Tools: {result['expected_tools']}")
        print(f"📊 Detected Tools: {result['detected_tools']}")
        print(f"✅ Tools Match: {result['tools_correct']}")
        
        if result['detected_paths']:
            print(f"\n📊 Detected Paths: {result['detected_paths']}")
        
        if result["status"] == "passed":
            print(f"\n✅ PASSED")
        else:
            print(f"\n❌ FAILED")
            if not result['agents_correct']:
                print(f"   - Agents mismatch")
            if not result['tools_correct']:
                print(f"   - Tools mismatch")
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for r in results if r["status"] == "passed")
    failed = sum(1 for r in results if r["status"] == "failed")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    errors = sum(1 for r in results if r["status"] == "error")
    total = len(results)
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⏭️  Skipped: {skipped}")
    print(f"💥 Errors: {errors}")
    print(f"📝 Total: {total}")
    
    if total > 0:
        accuracy = (passed / (total - skipped)) * 100 if (total - skipped) > 0 else 0
        print(f"🎯 Accuracy: {accuracy:.1f}%")
    
    print("="*70)
    
    # Detailed failures
    if failed > 0:
        print("\n❌ FAILED TESTS:")
        for result in results:
            if result["status"] == "failed":
                print(f"\n  {result['name']}:")
                if not result['agents_correct']:
                    print(f"    Expected agents: {result['expected_agents']}")
                    print(f"    Detected agents: {result['detected_agents']}")
                if not result['tools_correct']:
                    print(f"    Expected tools: {result['expected_tools']}")
                    print(f"    Detected tools: {result['detected_tools']}")
    
    return results


if __name__ == "__main__":
    run_all_tests()

