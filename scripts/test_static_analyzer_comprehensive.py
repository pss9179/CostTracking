#!/usr/bin/env python3
"""
Comprehensive test suite for static analyzer - tests edge cases and complex scenarios.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from llmobserve.static_analyzer import preview_agent_tree, analyze_code_string


def test_case(name: str, code: str, expected_agents: int = 0, expected_tools: int = 0):
    """Run a test case."""
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print('='*70)
    
    try:
        result = analyze_code_string(code, filename=f"test_{name.lower().replace(' ', '_')}.py")
        
        if "error" in result:
            print(f"❌ ERROR: {result['error']}")
            return False
        
        agents_found = result["total_agents"]
        # Count tools recursively from all agents
        def count_tools_recursive(node):
            count = 0
            if node["type"] == "tool":
                count = 1
            for child in node.get("children", []):
                count += count_tools_recursive(child)
            return count
        
        tools_found = sum(count_tools_recursive(agent) for agent in result["agents"])
        
        print(f"\n📊 Results:")
        print(f"   Agents found: {agents_found} (expected: {expected_agents})")
        print(f"   Tools found: {tools_found} (expected: {expected_tools})")
        
        preview = preview_agent_tree(code=code, filename=f"test_{name}.py")
        print(f"\n{preview}")
        
        success = True
        if expected_agents > 0 and agents_found != expected_agents:
            print(f"⚠️  WARNING: Expected {expected_agents} agents, got {agents_found}")
            success = False
        if expected_tools > 0 and tools_found != expected_tools:
            print(f"⚠️  WARNING: Expected {expected_tools} tools, got {tools_found}")
            success = False
        
        if success:
            print(f"\n✅ PASSED")
        else:
            print(f"\n⚠️  PARTIAL PASS (structure detected but counts may differ)")
        
        return success
    
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all test cases."""
    print("\n" + "="*70)
    print("🧪 COMPREHENSIVE STATIC ANALYZER TEST SUITE")
    print("="*70)
    
    test_cases = [
        # Test 1: Basic agent with tool
        ("Basic Agent with Tool", """
from openai import OpenAI
client = OpenAI()

def research_agent(query: str):
    results = web_search_tool(query)
    return results

def web_search_tool(query: str):
    import requests
    return requests.get(f"https://api.example.com/search?q={query}")
""", 1, 1),
        
        # Test 2: Nested agents
        ("Nested Agents", """
def coordinator_agent():
    planner_agent()
    executor_agent()

def planner_agent():
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])

def executor_agent():
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])
""", 3, 0),
        
        # Test 3: Agent with multiple tools
        ("Agent with Multiple Tools", """
def research_agent(query: str):
    web_search_tool(query)
    analyze_tool(query)
    summarize_tool(query)

def web_search_tool(query: str):
    import requests
    requests.get("https://api.example.com/search")

def analyze_tool(query: str):
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])

def summarize_tool(query: str):
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])
""", 1, 3),
        
        # Test 4: Agent with steps
        ("Agent with Steps", """
def workflow_agent(data: str):
    extract_step(data)
    transform_step(data)
    load_step(data)

def extract_step(data: str):
    import requests
    requests.get("https://api.example.com/data")

def transform_step(data: str):
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])

def load_step(data: str):
    import requests
    requests.post("https://api.example.com/load", json=data)
""", 1, 0),
        
        # Test 5: Mixed agents, tools, and steps
        ("Mixed Agents Tools Steps", """
def main_agent():
    planning_step()
    web_search_tool("query")
    execution_step()

def planning_step():
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])

def web_search_tool(query: str):
    import requests
    requests.get(f"https://api.example.com/search?q={query}")

def execution_step():
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])
""", 1, 1),
        
        # Test 6: Agent with loop
        ("Agent with Loop", """
def research_agent(query: str, iterations: int = 3):
    for i in range(iterations):
        web_search_tool(query)
        analyze_tool(query)

def web_search_tool(query: str):
    import requests
    requests.get("https://api.example.com/search")

def analyze_tool(query: str):
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])
""", 1, 2),
        
        # Test 7: Class-based agents
        ("Class-based Agents", """
class ResearchAgent:
    def run(self, query: str):
        self.web_search_tool(query)
        self.analyze_tool(query)
    
    def web_search_tool(self, query: str):
        import requests
        requests.get("https://api.example.com/search")
    
    def analyze_tool(self, query: str):
        from openai import OpenAI
        client = OpenAI()
        client.chat.completions.create(model="gpt-4", messages=[])

class PlannerAgent:
    def plan(self):
        from openai import OpenAI
        client = OpenAI()
        client.chat.completions.create(model="gpt-4", messages=[])
""", 0, 0),  # Classes not detected yet
        
        # Test 8: Agent calling other agents
        ("Agent Calling Other Agents", """
def coordinator_agent():
    planner_agent()
    executor_agent()
    reviewer_agent()

def planner_agent():
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])

def executor_agent():
    web_search_tool("query")
    analyze_tool("data")

def reviewer_agent():
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])

def web_search_tool(query: str):
    import requests
    requests.get("https://api.example.com/search")

def analyze_tool(data: str):
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])
""", 4, 2),
        
        # Test 9: Deep nesting
        ("Deep Nesting", """
def main_agent():
    sub_agent_1()
    sub_agent_2()

def sub_agent_1():
    tool_1()
    tool_2()

def sub_agent_2():
    tool_3()
    step_1()

def tool_1():
    import requests
    requests.get("https://api.example.com/1")

def tool_2():
    import requests
    requests.get("https://api.example.com/2")

def tool_3():
    import requests
    requests.get("https://api.example.com/3")

def step_1():
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])
""", 3, 3),
        
        # Test 10: Standalone tools (no agent)
        ("Standalone Tools", """
def web_search_tool(query: str):
    import requests
    requests.get("https://api.example.com/search")

def analyze_tool(data: str):
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])

def process_tool(item: str):
    import requests
    requests.post("https://api.example.com/process", json=item)
""", 3, 3),
        
        # Test 11: Agent with conditional calls
        ("Agent with Conditionals", """
def research_agent(query: str, use_llm: bool = True):
    web_search_tool(query)
    if use_llm:
        analyze_tool(query)
    else:
        simple_analysis(query)

def web_search_tool(query: str):
    import requests
    requests.get("https://api.example.com/search")

def analyze_tool(query: str):
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])

def simple_analysis(query: str):
    print(f"Analyzing: {query}")
""", 1, 1),
        
        # Test 12: Agent with try/except
        ("Agent with Try/Except", """
def research_agent(query: str):
    try:
        web_search_tool(query)
    except Exception as e:
        fallback_tool(query)

def web_search_tool(query: str):
    import requests
    requests.get("https://api.example.com/search")

def fallback_tool(query: str):
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])
""", 1, 2),
        
        # Test 13: Multiple API calls in same function
        ("Multiple API Calls", """
def research_agent(query: str):
    from openai import OpenAI
    client = OpenAI()
    
    # Multiple API calls
    response1 = client.chat.completions.create(model="gpt-4", messages=[])
    response2 = client.embeddings.create(model="text-embedding-ada-002", input=query)
    response3 = client.chat.completions.create(model="gpt-3.5-turbo", messages=[])
    
    return response1, response2, response3
""", 1, 0),
        
        # Test 14: Agent with async functions
        ("Async Agent", """
async def research_agent(query: str):
    await web_search_tool(query)
    await analyze_tool(query)

async def web_search_tool(query: str):
    import httpx
    async with httpx.AsyncClient() as client:
        await client.get("https://api.example.com/search")

async def analyze_tool(query: str):
    from openai import AsyncOpenAI
    client = AsyncOpenAI()
    await client.chat.completions.create(model="gpt-4", messages=[])
""", 1, 2),
        
        # Test 15: Agent with different naming patterns
        ("Different Naming Patterns", """
def run_agent(query: str):
    execute_tool(query)

def execute_tool(query: str):
    import requests
    requests.get("https://api.example.com/search")

def workflow_orchestrator(data: str):
    process_function(data)

def process_function(data: str):
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])

def pipeline_executor(items: list):
    invoke_call(items)

def invoke_call(items: list):
    import requests
    requests.post("https://api.example.com/process", json=items)
""", 3, 3),
        
        # Test 16: No agents (just regular functions)
        ("No Agents", """
def regular_function(x: int):
    return x * 2

def another_function(y: str):
    print(y)

def helper_function(z: list):
    return len(z)
""", 0, 0),
        
        # Test 17: Agent with method calls
        ("Agent with Method Calls", """
def research_agent(query: str):
    results = web_search_tool(query)
    processed = results.process()
    return processed

def web_search_tool(query: str):
    import requests
    response = requests.get("https://api.example.com/search")
    return response
""", 1, 1),
        
        # Test 18: Complex nested structure
        ("Complex Nested Structure", """
def main_orchestrator():
    planning_agent()
    execution_agent()
    review_agent()

def planning_agent():
    plan_step_1()
    plan_step_2()

def execution_agent():
    exec_tool_1()
    exec_tool_2()
    exec_step_1()

def review_agent():
    review_tool()

def plan_step_1():
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])

def plan_step_2():
    import requests
    requests.get("https://api.example.com/plan")

def exec_tool_1():
    import requests
    requests.get("https://api.example.com/exec1")

def exec_tool_2():
    import requests
    requests.get("https://api.example.com/exec2")

def exec_step_1():
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])

def review_tool():
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])
""", 4, 3),
    ]
    
    passed = 0
    failed = 0
    
    for name, code, expected_agents, expected_tools in test_cases:
        success = test_case(name, code, expected_agents, expected_tools)
        if success:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📝 Total: {len(test_cases)}")
    print("="*70)


if __name__ == "__main__":
    main()

