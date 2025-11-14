#!/usr/bin/env python3
"""
Extensive Edge Case Tests for Agent Detection

Tests tricky cases that might cause false positives or negatives.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from llmobserve.static_analyzer import analyze_code_string


def test_edge_case(name: str, code: str, should_be_agent: bool, description: str = ""):
    """Test an edge case."""
    print(f"\n{'='*70}")
    print(f"EDGE CASE: {name}")
    if description:
        print(f"Description: {description}")
    print('='*70)
    
    try:
        result = analyze_code_string(code, filename=f"test_{name.lower().replace(' ', '_')}.py")
        
        if "error" in result:
            print(f"❌ ERROR: {result['error']}")
            return False
        
        agents_found = result["total_agents"]
        agent_names = [agent["name"] for agent in result["agents"]]
        
        detected = agents_found > 0
        
        print(f"\n📊 Results:")
        print(f"   Agents detected: {agents_found}")
        print(f"   Agent names: {agent_names}")
        print(f"   Expected: {'Agent' if should_be_agent else 'Not Agent'}")
        print(f"   Got: {'Agent' if detected else 'Not Agent'}")
        
        correct = detected == should_be_agent
        
        if correct:
            print(f"\n✅ CORRECT")
        else:
            print(f"\n❌ INCORRECT - {'False positive' if detected and not should_be_agent else 'False negative'}")
        
        return correct
    
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run extensive edge case tests."""
    print("\n" + "="*70)
    print("🔬 EXTENSIVE EDGE CASE TEST SUITE")
    print("="*70)
    
    edge_cases = [
        # False positive tests (should NOT be detected as agents)
        ("Tool Function", """
def web_search_tool(query: str):
    return query
""", False, "Tool function should not be detected as agent"),
        
        ("Tool with Underscore", """
def my_tool_function(data: str):
    return data
""", False, "Tool function should not be detected as agent"),
        
        ("Step Function", """
def analyze_step(data: str):
    return data
""", False, "Step function should not be detected as agent"),
        
        ("Stage Function", """
def process_stage(items: list):
    return items
""", False, "Stage function should not be detected as agent"),
        
        ("Task Function", """
def execute_task(action: str):
    return action
""", False, "Task function should not be detected as agent"),
        
        ("Regular Function", """
def process_data(data: str):
    return data.upper()
""", False, "Regular function should not be detected as agent"),
        
        ("Helper Function", """
def helper_function(x: int):
    return x * 2
""", False, "Helper function should not be detected as agent"),
        
        ("Utility Function", """
def format_string(text: str):
    return text.strip()
""", False, "Utility function should not be detected as agent"),
        
        ("Calculator Function", """
def calculate_sum(a: int, b: int):
    return a + b
""", False, "Calculator function should not be detected as agent"),
        
        ("Database Function", """
def query_database(sql: str):
    return sql
""", False, "Database function should not be detected as agent"),
        
        # True positive tests (SHOULD be detected as agents)
        ("Research Agent", """
def research_agent(query: str):
    return query
""", True, "Research agent should be detected"),
        
        ("Planning Agent", """
def planning_agent(task: str):
    return task
""", True, "Planning agent should be detected"),
        
        ("Execution Agent", """
def execution_agent(action: str):
    return action
""", True, "Execution agent should be detected"),
        
        ("Workflow Orchestrator", """
def workflow_orchestrator(data: str):
    return data
""", True, "Workflow orchestrator should be detected"),
        
        ("Pipeline Executor", """
def pipeline_executor(items: list):
    return items
""", True, "Pipeline executor should be detected"),
        
        ("Run Agent", """
def run_agent(query: str):
    return query
""", True, "Run agent should be detected"),
        
        ("Execute Agent", """
def execute_agent(task: str):
    return task
""", True, "Execute agent should be detected"),
        
        # Ambiguous cases
        ("Agentic Behavior", """
def agentic_behavior(query: str):
    return query
""", True, "Contains 'agent' so might be detected"),
        
        ("Orchestrate Function", """
def orchestrate_tasks(tasks: list):
    return tasks
""", True, "Contains 'orchestrat' pattern"),
        
        ("Workflow Manager", """
def workflow_manager(data: str):
    return data
""", True, "Contains 'workflow' pattern"),
        
        ("Pipeline Processor", """
def pipeline_processor(items: list):
    return items
""", True, "Contains 'pipeline' pattern"),
        
        # Complex cases
        ("Agent with Tool Call", """
def research_agent(query: str):
    web_search_tool(query)
    return query

def web_search_tool(query: str):
    return query
""", True, "Agent calling tool should be detected"),
        
        ("Agent with Step Call", """
def workflow_agent(data: str):
    extract_step(data)
    return data

def extract_step(data: str):
    return data
""", True, "Agent calling step should be detected"),
        
        ("Nested Agent", """
def coordinator_agent():
    research_agent("query")

def research_agent(query: str):
    return query
""", True, "Nested agent should be detected"),
        
        ("Agent with API Call", """
def research_agent(query: str):
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])
    return query
""", True, "Agent with API call should be detected"),
        
        ("Agent with Multiple Tools", """
def research_agent(query: str):
    web_search_tool(query)
    analyze_tool(query)
    summarize_tool(query)
    return query

def web_search_tool(query: str):
    return query

def analyze_tool(query: str):
    return query

def summarize_tool(query: str):
    return query
""", True, "Agent with multiple tools should be detected"),
        
        # Edge cases with similar names
        ("Agent vs Agentic", """
def agent_function(query: str):
    return query

def agentic_behavior(data: str):
    return data
""", True, "Both contain 'agent' pattern"),
        
        ("Orchestrator vs Orchestrate", """
def orchestrator_function(query: str):
    return query

def orchestrate_tasks(tasks: list):
    return tasks
""", True, "Both contain 'orchestrat' pattern"),
        
        ("Workflow vs Work", """
def workflow_manager(data: str):
    return data

def work_function(item: str):
    return item
""", True, "Workflow should be detected, work should not"),
        
        ("Pipeline vs Pipe", """
def pipeline_executor(items: list):
    return items

def pipe_data(data: str):
    return data
""", True, "Pipeline should be detected, pipe should not"),
        
        # Real-world patterns
        ("LangChain Agent", """
def langchain_agent(query: str):
    from langchain.agents import AgentExecutor
    agent = AgentExecutor(...)
    return agent.run(query)
""", True, "LangChain agent pattern"),
        
        ("AutoGPT Agent", """
def autogpt_agent(task: str):
    # AutoGPT logic
    return task
""", True, "AutoGPT agent pattern"),
        
        ("CrewAI Agent", """
def crewai_agent(goal: str):
    # CrewAI logic
    return goal
""", True, "CrewAI agent pattern"),
        
        ("LlamaIndex Agent", """
def llamaindex_agent(query: str):
    # LlamaIndex logic
    return query
""", True, "LlamaIndex agent pattern"),
        
        # Special Python features
        ("Agent with Decorator", """
@some_decorator
def research_agent(query: str):
    return query
""", True, "Agent with decorator should be detected"),
        
        ("Agent with Type Hints", """
def research_agent(query: str) -> str:
    return query
""", True, "Agent with type hints should be detected"),
        
        ("Agent with Default Args", """
def research_agent(query: str = "default"):
    return query
""", True, "Agent with default args should be detected"),
        
        ("Agent with *args", """
def research_agent(*args):
    return args
""", True, "Agent with *args should be detected"),
        
        ("Agent with **kwargs", """
def research_agent(**kwargs):
    return kwargs
""", True, "Agent with **kwargs should be detected"),
        
        ("Async Agent", """
async def research_agent(query: str):
    return query
""", True, "Async agent should be detected"),
        
        ("Agent in Class", """
class MyClass:
    def research_agent(self, query: str):
        return query
""", True, "Agent in class should be detected"),
        
        ("Agent in Nested Function", """
def outer_function():
    def research_agent(query: str):
        return query
    return research_agent("test")
""", True, "Agent in nested function should be detected"),
    ]
    
    passed = 0
    failed = 0
    false_positives = 0
    false_negatives = 0
    
    for name, code, should_be_agent, description in edge_cases:
        success = test_edge_case(name, code, should_be_agent, description)
        if success:
            passed += 1
        else:
            failed += 1
            # Check if it's a false positive or false negative
            result = analyze_code_string(code)
            detected = result["total_agents"] > 0
            if detected and not should_be_agent:
                false_positives += 1
            elif not detected and should_be_agent:
                false_negatives += 1
    
    print("\n" + "="*70)
    print("📊 EDGE CASE TEST SUMMARY")
    print("="*70)
    print(f"✅ Correct: {passed}")
    print(f"❌ Incorrect: {failed}")
    print(f"   - False Positives: {false_positives}")
    print(f"   - False Negatives: {false_negatives}")
    print(f"📝 Total Tests: {len(edge_cases)}")
    accuracy = (passed / len(edge_cases)) * 100
    print(f"🎯 Accuracy: {accuracy:.1f}%")
    print("="*70)
    
    if false_positives > 0:
        print(f"\n⚠️  False Positives: {false_positives} functions incorrectly detected as agents")
    if false_negatives > 0:
        print(f"\n⚠️  False Negatives: {false_negatives} agents incorrectly not detected")
    
    if accuracy >= 95:
        print("\n🎉 EXCELLENT: Very high accuracy!")
    elif accuracy >= 85:
        print("\n✅ GOOD: High accuracy")
    elif accuracy >= 75:
        print("\n⚠️  MODERATE: Accuracy needs improvement")
    else:
        print("\n❌ POOR: Accuracy needs significant improvement")


if __name__ == "__main__":
    main()

