#!/usr/bin/env python3
"""
Comprehensive Agent Detection Accuracy Tests

Tests various patterns to measure how accurately agents are detected.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from llmobserve.static_analyzer import analyze_code_string


def test_detection(name: str, code: str, should_detect_agents: bool, expected_agent_names: list = None):
    """Test agent detection accuracy."""
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print('='*70)
    
    try:
        result = analyze_code_string(code, filename=f"test_{name.lower().replace(' ', '_')}.py")
        
        if "error" in result:
            print(f"❌ ERROR: {result['error']}")
            return False
        
        agents_found = result["total_agents"]
        agent_names = [agent["name"] for agent in result["agents"]]
        
        print(f"\n📊 Detection Results:")
        print(f"   Agents detected: {agents_found}")
        print(f"   Agent names: {agent_names}")
        
        # Check if detection matches expectation
        detected = agents_found > 0
        correct = detected == should_detect_agents
        
        if expected_agent_names:
            matches = all(name in agent_names for name in expected_agent_names)
            if matches:
                print(f"   ✅ Expected agents found: {expected_agent_names}")
            else:
                print(f"   ⚠️  Expected: {expected_agent_names}, Got: {agent_names}")
                correct = False
        
        if correct:
            print(f"\n✅ CORRECT: {'Detected' if detected else 'Not detected'} as expected")
        else:
            print(f"\n❌ INCORRECT: Expected {'detection' if should_detect_agents else 'no detection'}, got {'detection' if detected else 'no detection'}")
        
        return correct
    
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all accuracy tests."""
    print("\n" + "="*70)
    print("🎯 AGENT DETECTION ACCURACY TEST SUITE")
    print("="*70)
    
    test_cases = [
        # Test 1: Simple agent pattern
        ("Simple Agent Pattern", """
def research_agent(query: str):
    return query
""", True, ["agent:research"]),
        
        # Test 2: Agent with underscore
        ("Agent with Underscore", """
def my_research_agent(query: str):
    return query
""", True, ["agent:my_research"]),
        
        # Test 3: Agent prefix
        ("Agent Prefix Pattern", """
def agent_researcher(query: str):
    return query
""", True, ["agent:researcher"]),
        
        # Test 4: Orchestrator pattern
        ("Orchestrator Pattern", """
def workflow_orchestrator(data: str):
    return data
""", True, ["agent:workflow_orchestrator"]),
        
        # Test 5: Pipeline pattern
        ("Pipeline Pattern", """
def data_pipeline(items: list):
    return items
""", True, ["agent:data_pipeline"]),
        
        # Test 6: Run agent pattern
        ("Run Agent Pattern", """
def run_agent(query: str):
    return query
""", True, ["agent:run"]),
        
        # Test 7: Execute agent pattern
        ("Execute Agent Pattern", """
def execute_agent(task: str):
    return task
""", True, ["agent:execute"]),
        
        # Test 8: False positive - regular function
        ("False Positive: Regular Function", """
def process_data(data: str):
    return data.upper()
""", False),
        
        # Test 9: False positive - helper function
        ("False Positive: Helper Function", """
def helper_function(x: int):
    return x * 2
""", False),
        
        # Test 10: False positive - utility function
        ("False Positive: Utility Function", """
def format_string(text: str):
    return text.strip()
""", False),
        
        # Test 11: Agent in class method
        ("Agent in Class Method", """
class MyClass:
    def research_agent(self, query: str):
        return query
""", True, ["agent:research"]),
        
        # Test 12: Multiple agents
        ("Multiple Agents", """
def research_agent(query: str):
    return query

def planning_agent(task: str):
    return task

def execution_agent(action: str):
    return action
""", True, ["agent:research", "agent:planning", "agent:execution"]),
        
        # Test 13: Agent with numbers
        ("Agent with Numbers", """
def agent_v2(query: str):
    return query

def research_agent_2024(data: str):
    return data
""", True),
        
        # Test 14: CamelCase agent (should not detect)
        ("CamelCase Agent (Not Detected)", """
def ResearchAgent(query: str):
    return query
""", False),  # Function names are lowercase in Python
        
        # Test 15: Agent with special characters
        ("Agent with Special Chars", """
def research_agent_v2(query: str):
    return query
""", True),
        
        # Test 16: Very long agent name
        ("Very Long Agent Name", """
def very_long_research_agent_with_many_words(query: str):
    return query
""", True),
        
        # Test 17: Agent in nested function
        ("Agent in Nested Function", """
def outer_function():
    def research_agent(query: str):
        return query
    return research_agent("test")
""", True, ["agent:research"]),
        
        # Test 18: Agent with async
        ("Async Agent", """
async def research_agent(query: str):
    return query
""", True, ["agent:research"]),
        
        # Test 19: Agent with decorator
        ("Agent with Decorator", """
@some_decorator
def research_agent(query: str):
    return query
""", True, ["agent:research"]),
        
        # Test 20: Agent with type hints
        ("Agent with Type Hints", """
def research_agent(query: str) -> str:
    return query
""", True, ["agent:research"]),
        
        # Test 21: Agent with default args
        ("Agent with Default Args", """
def research_agent(query: str = "default"):
    return query
""", True, ["agent:research"]),
        
        # Test 22: Agent with *args
        ("Agent with *args", """
def research_agent(*args):
    return args
""", True, ["agent:research"]),
        
        # Test 23: Agent with **kwargs
        ("Agent with **kwargs", """
def research_agent(**kwargs):
    return kwargs
""", True, ["agent:research"]),
        
        # Test 24: Agent calling other agent
        ("Agent Calling Other Agent", """
def coordinator_agent():
    research_agent("query")

def research_agent(query: str):
    return query
""", True, ["agent:coordinator", "agent:research"]),
        
        # Test 25: Tool pattern (should not be agent)
        ("Tool Pattern (Not Agent)", """
def web_search_tool(query: str):
    return query
""", False),
        
        # Test 26: Step pattern (should not be agent)
        ("Step Pattern (Not Agent)", """
def analyze_step(data: str):
    return data
""", False),
        
        # Test 27: Agent-like but not agent
        ("Agent-like but Not Agent", """
def agentic_behavior(query: str):
    return query
""", True),  # Contains "agent" so might be detected
        
        # Test 28: Workflow pattern
        ("Workflow Pattern", """
def data_workflow(items: list):
    return items
""", True, ["agent:data_workflow"]),
        
        # Test 29: Pipeline executor
        ("Pipeline Executor", """
def pipeline_executor(data: str):
    return data
""", True),
        
        # Test 30: Orchestrator with different suffix
        ("Orchestrator Variant", """
def task_orchestrator(tasks: list):
    return tasks
""", True),
        
        # Test 31: Real-world LangChain-like pattern
        ("LangChain-like Pattern", """
def langchain_agent(query: str):
    from langchain.agents import AgentExecutor
    agent = AgentExecutor(...)
    return agent.run(query)
""", True, ["agent:langchain"]),
        
        # Test 32: AutoGPT-like pattern
        ("AutoGPT-like Pattern", """
def autogpt_agent(task: str):
    # AutoGPT agent logic
    return task
""", True),
        
        # Test 33: CrewAI-like pattern
        ("CrewAI-like Pattern", """
def crewai_agent(goal: str):
    # CrewAI agent logic
    return goal
""", True),
        
        # Test 34: LlamaIndex-like pattern
        ("LlamaIndex-like Pattern", """
def llamaindex_agent(query: str):
    # LlamaIndex agent logic
    return query
""", True),
        
        # Test 35: Agent with lambda (should not detect lambda as agent)
        ("Agent with Lambda", """
def research_agent(query: str):
    func = lambda x: x.upper()
    return func(query)
""", True, ["agent:research"]),
        
        # Test 36: Agent with list comprehension
        ("Agent with List Comprehension", """
def research_agent(items: list):
    return [item.upper() for item in items]
""", True, ["agent:research"]),
        
        # Test 37: Agent with generator
        ("Agent with Generator", """
def research_agent(items: list):
    for item in items:
        yield item.upper()
""", True, ["agent:research"]),
        
        # Test 38: Agent with context manager
        ("Agent with Context Manager", """
def research_agent(query: str):
    with open("file.txt") as f:
        return f.read()
""", True, ["agent:research"]),
        
        # Test 39: Agent with exception handling
        ("Agent with Exception Handling", """
def research_agent(query: str):
    try:
        return query.upper()
    except Exception as e:
        return str(e)
""", True, ["agent:research"]),
        
        # Test 40: Agent with multiple returns
        ("Agent with Multiple Returns", """
def research_agent(query: str):
    if query:
        return query.upper()
    return "default"
""", True, ["agent:research"]),
        
        # Test 41: Agent with class instantiation
        ("Agent with Class Instantiation", """
def research_agent(query: str):
    client = SomeClient()
    return client.process(query)
""", True, ["agent:research"]),
        
        # Test 42: Agent with import
        ("Agent with Import", """
def research_agent(query: str):
    from some_module import some_function
    return some_function(query)
""", True, ["agent:research"]),
        
        # Test 43: Agent with global variable
        ("Agent with Global Variable", """
GLOBAL_VAR = "test"

def research_agent(query: str):
    return GLOBAL_VAR + query
""", True, ["agent:research"]),
        
        # Test 44: Agent with nonlocal
        ("Agent with Nonlocal", """
def outer():
    x = "test"
    def research_agent(query: str):
        nonlocal x
        return x + query
    return research_agent("query")
""", True, ["agent:research"]),
        
        # Test 45: Agent with walrus operator
        ("Agent with Walrus Operator", """
def research_agent(query: str):
    if (result := query.upper()):
        return result
    return "default"
""", True, ["agent:research"]),
        
        # Test 46: Agent with match/case (Python 3.10+)
        ("Agent with Match/Case", """
def research_agent(query: str):
    match query:
        case "test":
            return "matched"
        case _:
            return "default"
""", True, ["agent:research"]),
        
        # Test 47: Agent with f-string
        ("Agent with F-string", """
def research_agent(query: str):
    return f"Result: {query}"
""", True, ["agent:research"]),
        
        # Test 48: Agent with dict comprehension
        ("Agent with Dict Comprehension", """
def research_agent(items: list):
    return {item: item.upper() for item in items}
""", True, ["agent:research"]),
        
        # Test 49: Agent with set comprehension
        ("Agent with Set Comprehension", """
def research_agent(items: list):
    return {item.upper() for item in items}
""", True, ["agent:research"]),
        
        # Test 50: Agent with tuple unpacking
        ("Agent with Tuple Unpacking", """
def research_agent(data: tuple):
    a, b, c = data
    return a + b + c
""", True, ["agent:research"]),
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        if len(test_case) == 4:
            name, code, should_detect, expected_names = test_case
        else:
            name, code, should_detect = test_case
            expected_names = None
        success = test_detection(name, code, should_detect, expected_names)
        if success:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*70)
    print("📊 ACCURACY SUMMARY")
    print("="*70)
    print(f"✅ Correct Detections: {passed}")
    print(f"❌ Incorrect Detections: {failed}")
    print(f"📝 Total Tests: {len(test_cases)}")
    accuracy = (passed / len(test_cases)) * 100
    print(f"🎯 Accuracy: {accuracy:.1f}%")
    print("="*70)
    
    if accuracy >= 90:
        print("\n🎉 EXCELLENT: Detection accuracy is very high!")
    elif accuracy >= 75:
        print("\n✅ GOOD: Detection accuracy is acceptable")
    elif accuracy >= 50:
        print("\n⚠️  MODERATE: Detection accuracy needs improvement")
    else:
        print("\n❌ POOR: Detection accuracy needs significant improvement")


if __name__ == "__main__":
    main()

