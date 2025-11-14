#!/usr/bin/env python3
"""
Comprehensive Test: Visualization Tree Accuracy

Tests both:
1. Static Analysis (Preview) - ~78% accurate, no execution
2. Runtime Detection (Actual) - 100% accurate, requires execution
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from llmobserve.multi_language_analyzer import analyze_multi_language_code
from llmobserve.agent_detector import detect_agent_from_stack, detect_hierarchical_context


# Mock API call simulator
def simulate_api_call(provider="openai", endpoint="chat.completions.create"):
    """Simulate an API call - this is where detection actually runs."""
    detected_agent = detect_agent_from_stack()
    detected_path = detect_hierarchical_context()
    
    return {
        "provider": provider,
        "endpoint": endpoint,
        "detected_agent": detected_agent,
        "detected_path": detected_path,
        "cost": 0.05,  # Mock cost
        "tokens": 100  # Mock tokens
    }


# Test Case 1: Simple Agent with Tool
TEST_CASE_1_CODE = """
def web_search_tool(query):
    api_result = simulate_api_call("custom", "web_search")
    return api_result

def research_agent(query):
    results = web_search_tool(query)
    return results
"""

TEST_CASE_1_STATIC_EXPECTED = {
    "agents": ["agent:research"],
    "tools": ["tool:web_search"],
    "structure": "agent:research > tool:web_search"
}

TEST_CASE_1_RUNTIME_EXPECTED = {
    "agents": ["agent:research"],
    "tools": ["tool:web_search"],
    "path": "agent:research > tool:web_search"
}


# Test Case 2: Agent with Multiple Tools
TEST_CASE_2_CODE = """
def analyze_tool(data):
    api_result = simulate_api_call("openai", "chat.completions.create")
    return api_result

def summarize_tool(data):
    api_result = simulate_api_call("openai", "chat.completions.create")
    return api_result

def research_agent_multi(query):
    results = web_search_tool(query)
    analysis = analyze_tool(results)
    summary = summarize_tool(analysis)
    return summary
"""

TEST_CASE_2_STATIC_EXPECTED = {
    "agents": ["agent:research"],
    "tools": ["tool:web_search", "tool:analyze", "tool:summarize"],
    "structure": "agent:research > [tool:web_search, tool:analyze, tool:summarize]"
}

TEST_CASE_2_RUNTIME_EXPECTED = {
    "agents": ["agent:research"],
    "tools": ["tool:web_search", "tool:analyze", "tool:summarize"],
    "path": "agent:research > tool:web_search > tool:analyze > tool:summarize"
}


# Test Case 3: Nested Agents
TEST_CASE_3_CODE = """
def fetch_tool(task):
    api_result = simulate_api_call("custom", "fetch")
    return api_result

def sub_agent(task):
    data = fetch_tool(task)
    return data

def main_agent(task):
    result = sub_agent(task)
    return result
"""

TEST_CASE_3_STATIC_EXPECTED = {
    "agents": ["agent:main", "agent:sub"],
    "tools": ["tool:fetch"],
    "structure": "agent:main > agent:sub > tool:fetch"
}

TEST_CASE_3_RUNTIME_EXPECTED = {
    "agents": ["agent:main", "agent:sub"],
    "tools": ["tool:fetch"],
    "path": "agent:main > agent:sub > tool:fetch"
}


# Test Case 4: Class-based Agent
TEST_CASE_4_CODE = """
class ResearchAgent:
    def run(self, query):
        results = self.web_search_tool(query)
        return results
    
    def web_search_tool(self, query):
        api_result = simulate_api_call("custom", "web_search")
        return api_result
"""

TEST_CASE_4_STATIC_EXPECTED = {
    "agents": ["agent:research"],
    "tools": ["tool:web_search"],
    "structure": "agent:research > tool:web_search"
}

TEST_CASE_4_RUNTIME_EXPECTED = {
    "agents": ["agent:research"],
    "tools": ["tool:web_search"],
    "path": "agent:research > tool:web_search"
}


# Test Case 5: Complex Nested Structure
TEST_CASE_5_CODE = """
def plan_tool(task):
    api_result = simulate_api_call("openai", "chat.completions.create")
    return api_result

def execute_tool(plan):
    api_result = simulate_api_call("custom", "execute")
    return api_result

def planning_agent(task):
    plan = plan_tool(task)
    return plan

def execution_agent(plan):
    result = execute_tool(plan)
    return result

def main_agent_complex(task):
    planning = planning_agent(task)
    execution = execution_agent(planning)
    return execution
"""

TEST_CASE_5_STATIC_EXPECTED = {
    "agents": ["agent:main", "agent:planning", "agent:execution"],
    "tools": ["tool:plan", "tool:execute"],
    "structure": "agent:main > [agent:planning > tool:plan, agent:execution > tool:execute]"
}

TEST_CASE_5_RUNTIME_EXPECTED = {
    "agents": ["agent:main", "agent:planning", "agent:execution"],
    "tools": ["tool:plan", "tool:execute"],
    "path": "agent:main > agent:planning > tool:plan > agent:execution > tool:execute"
}


def test_static_analysis(code, expected, test_name):
    """Test static analysis (preview without execution)."""
    print(f"\n{'='*70}")
    print(f"STATIC ANALYSIS TEST: {test_name}")
    print('='*70)
    
    try:
        result = analyze_multi_language_code(code, "python")
        
        # Extract detected agents and tools
        detected_agents = []
        detected_tools = []
        
        def extract_nodes(nodes, path=""):
            for node in nodes:
                node_type = node.get("type", "")
                node_name = node.get("name", "")
                
                if node_type == "agent":
                    detected_agents.append(node_name)
                elif node_type == "tool":
                    detected_tools.append(node_name)
                
                # Check children
                children = node.get("children", [])
                if children:
                    extract_nodes(children, f"{path}.{node_name}")
        
        extract_nodes(result.get("agents", []))
        
        # Compare with expected
        agents_match = set(detected_agents) == set(expected["agents"])
        tools_match = set(detected_tools) == set(expected["tools"])
        
        print(f"\n📊 Expected Agents: {expected['agents']}")
        print(f"📊 Detected Agents: {detected_agents}")
        print(f"✅ Agents Match: {agents_match}")
        
        print(f"\n📊 Expected Tools: {expected['tools']}")
        print(f"📊 Detected Tools: {detected_tools}")
        print(f"✅ Tools Match: {tools_match}")
        
        accuracy = 1.0 if (agents_match and tools_match) else 0.0
        
        print(f"\n🎯 Accuracy: {accuracy*100:.1f}%")
        
        return {
            "test_name": test_name,
            "method": "static",
            "accuracy": accuracy,
            "agents_match": agents_match,
            "tools_match": tools_match,
            "detected_agents": detected_agents,
            "detected_tools": detected_tools,
            "expected_agents": expected["agents"],
            "expected_tools": expected["tools"]
        }
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "test_name": test_name,
            "method": "static",
            "accuracy": 0.0,
            "error": str(e)
        }


def test_runtime_detection(code, expected, test_name):
    """Test runtime detection (actual execution)."""
    print(f"\n{'='*70}")
    print(f"RUNTIME DETECTION TEST: {test_name}")
    print('='*70)
    
    # Execute code in namespace
    namespace = {
        "simulate_api_call": simulate_api_call,
        "detect_agent_from_stack": detect_agent_from_stack,
        "detect_hierarchical_context": detect_hierarchical_context
    }
    
    try:
        exec(code, namespace)
        
        # Find agent function
        agent_func = None
        for name, obj in namespace.items():
            if callable(obj) and ("agent" in name.lower() or name == "run"):
                if name.endswith("_agent") or "agent" in name.lower():
                    agent_func = obj
                    break
        
        if not agent_func:
            # Try class-based
            for name, obj in namespace.items():
                if isinstance(obj, type) and "Agent" in name:
                    agent_func = getattr(obj(), "run", None)
                    break
        
        if not agent_func:
            print("❌ Could not find agent function")
            return {
                "test_name": test_name,
                "method": "runtime",
                "accuracy": 0.0,
                "error": "Agent function not found"
            }
        
        # Execute agent
        result = agent_func("test_query")
        
        # Extract API call results
        api_results = []
        
        def extract_api_calls(obj, path=""):
            if isinstance(obj, dict):
                if "detected_agent" in obj and "detected_path" in obj:
                    api_results.append({
                        "agent": obj.get("detected_agent"),
                        "path": obj.get("detected_path", [])
                    })
                for key, value in obj.items():
                    extract_api_calls(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    extract_api_calls(item, f"{path}[{i}]")
        
        extract_api_calls(result)
        
        # Analyze results
        detected_agents = set()
        detected_tools = set()
        detected_paths = []
        
        for api_result in api_results:
            agent = api_result.get("agent")
            path = api_result.get("path", [])
            
            if agent:
                if agent.startswith("agent:"):
                    detected_agents.add(agent)
                elif agent.startswith("tool:"):
                    detected_tools.add(agent)
            
            if path:
                detected_paths.append(" > ".join(path))
        
        # Compare with expected
        agents_match = detected_agents == set([f"agent:{a}" for a in expected["agents"]])
        tools_match = detected_tools == set([f"tool:{t}" for t in expected["tools"]])
        
        print(f"\n📊 Expected Agents: {expected['agents']}")
        print(f"📊 Detected Agents: {list(detected_agents)}")
        print(f"✅ Agents Match: {agents_match}")
        
        print(f"\n📊 Expected Tools: {expected['tools']}")
        print(f"📊 Detected Tools: {list(detected_tools)}")
        print(f"✅ Tools Match: {tools_match}")
        
        if detected_paths:
            print(f"\n📊 Detected Paths:")
            for path in detected_paths:
                print(f"   - {path}")
        
        accuracy = 1.0 if (agents_match and tools_match) else 0.0
        
        print(f"\n🎯 Accuracy: {accuracy*100:.1f}%")
        
        return {
            "test_name": test_name,
            "method": "runtime",
            "accuracy": accuracy,
            "agents_match": agents_match,
            "tools_match": tools_match,
            "detected_agents": list(detected_agents),
            "detected_tools": list(detected_tools),
            "detected_paths": detected_paths,
            "expected_agents": expected["agents"],
            "expected_tools": expected["tools"]
        }
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "test_name": test_name,
            "method": "runtime",
            "accuracy": 0.0,
            "error": str(e)
        }


def run_all_tests():
    """Run all test cases."""
    print("\n" + "="*70)
    print("🧪 VISUALIZATION TREE ACCURACY TESTS")
    print("="*70)
    
    test_cases = [
        ("Simple Agent with Tool", TEST_CASE_1_CODE, TEST_CASE_1_STATIC_EXPECTED, TEST_CASE_1_RUNTIME_EXPECTED),
        ("Agent with Multiple Tools", TEST_CASE_2_CODE, TEST_CASE_2_STATIC_EXPECTED, TEST_CASE_2_RUNTIME_EXPECTED),
        ("Nested Agents", TEST_CASE_3_CODE, TEST_CASE_3_STATIC_EXPECTED, TEST_CASE_3_RUNTIME_EXPECTED),
        ("Class-based Agent", TEST_CASE_4_CODE, TEST_CASE_4_STATIC_EXPECTED, TEST_CASE_4_RUNTIME_EXPECTED),
        ("Complex Nested Structure", TEST_CASE_5_CODE, TEST_CASE_5_STATIC_EXPECTED, TEST_CASE_5_RUNTIME_EXPECTED),
    ]
    
    static_results = []
    runtime_results = []
    
    for test_name, code, static_expected, runtime_expected in test_cases:
        # Test static analysis
        static_result = test_static_analysis(code, static_expected, test_name)
        static_results.append(static_result)
        
        # Test runtime detection
        runtime_result = test_runtime_detection(code, runtime_expected, test_name)
        runtime_results.append(runtime_result)
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    print("\n1️⃣  STATIC ANALYSIS (Preview - No Execution)")
    print("-"*70)
    static_passed = sum(1 for r in static_results if r["accuracy"] == 1.0)
    static_total = len(static_results)
    static_accuracy = (static_passed / static_total * 100) if static_total > 0 else 0
    
    for result in static_results:
        status = "✅ PASSED" if result["accuracy"] == 1.0 else "❌ FAILED"
        print(f"{status}: {result['test_name']}")
        if result["accuracy"] < 1.0:
            if not result.get("agents_match"):
                print(f"   - Agents mismatch")
            if not result.get("tools_match"):
                print(f"   - Tools mismatch")
    
    print(f"\n✅ Passed: {static_passed}/{static_total}")
    print(f"🎯 Accuracy: {static_accuracy:.1f}%")
    
    print("\n2️⃣  RUNTIME DETECTION (Actual Execution)")
    print("-"*70)
    runtime_passed = sum(1 for r in runtime_results if r["accuracy"] == 1.0)
    runtime_total = len(runtime_results)
    runtime_accuracy = (runtime_passed / runtime_total * 100) if runtime_total > 0 else 0
    
    for result in runtime_results:
        status = "✅ PASSED" if result["accuracy"] == 1.0 else "❌ FAILED"
        print(f"{status}: {result['test_name']}")
        if result["accuracy"] < 1.0:
            if not result.get("agents_match"):
                print(f"   - Agents mismatch")
            if not result.get("tools_match"):
                print(f"   - Tools mismatch")
    
    print(f"\n✅ Passed: {runtime_passed}/{runtime_total}")
    print(f"🎯 Accuracy: {runtime_accuracy:.1f}%")
    
    print("\n" + "="*70)
    print("📊 COMPARISON")
    print("="*70)
    print(f"Static Analysis (Preview):  {static_accuracy:.1f}% accurate")
    print(f"Runtime Detection (Actual):  {runtime_accuracy:.1f}% accurate")
    print()
    print("💡 Conclusion:")
    if runtime_accuracy == 100:
        print("   ✅ Runtime detection is 100% accurate!")
    else:
        print(f"   ⚠️  Runtime detection: {runtime_accuracy:.1f}% accurate")
    
    if static_accuracy < 100:
        print(f"   ⚠️  Static analysis: {static_accuracy:.1f}% accurate (expected ~78%)")
    else:
        print(f"   ✅ Static analysis: {static_accuracy:.1f}% accurate")
    
    print("="*70)
    
    return static_results, runtime_results


if __name__ == "__main__":
    run_all_tests()

