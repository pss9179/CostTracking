#!/usr/bin/env python3
"""
Comprehensive Nested Agent Detection Tests

Tests nested agents, complex hierarchies, and multi-level structures
across TypeScript, JavaScript, Go, Java, and Python.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from llmobserve.multi_language_analyzer import preview_multi_language_tree, analyze_multi_language_code


def test_nested_structure(name: str, code: str, language: str, expected_structure: dict):
    """Test nested agent structure detection."""
    print(f"\n{'='*70}")
    print(f"TEST: {name} ({language.upper()})")
    print('='*70)
    
    try:
        result = analyze_multi_language_code(code, language)
        
        if "error" in result:
            print(f"❌ ERROR: {result['error']}")
            return False
        
        preview = preview_multi_language_tree(code=code, language=language)
        print(preview)
        
        # Verify structure
        agents = result["agents"]
        agents_found = result["total_agents"]
        
        print(f"\n📊 Structure Analysis:")
        print(f"   Agents found: {agents_found}")
        
        def count_nodes_recursive(node, node_type=None):
            """Count nodes recursively."""
            count = 0
            if node_type is None or node["type"] == node_type:
                count = 1
            for child in node.get("children", []):
                count += count_nodes_recursive(child, node_type)
            return count
        
        def get_structure_recursive(node, indent=0):
            """Get structure recursively."""
            structure = []
            prefix = "  " * indent
            structure.append(f"{prefix}{node['type']}:{node['name']}")
            for child in node.get("children", []):
                structure.extend(get_structure_recursive(child, indent + 1))
            return structure
        
        # Print structure
        print(f"\n🌳 Detected Structure:")
        for agent in agents:
            structure = get_structure_recursive(agent)
            for line in structure:
                print(f"   {line}")
        
        # Count nodes by type
        total_agents = sum(count_nodes_recursive(agent, "agent") for agent in agents)
        total_tools = sum(count_nodes_recursive(agent, "tool") for agent in agents)
        total_steps = sum(count_nodes_recursive(agent, "step") for agent in agents)
        
        print(f"\n📈 Counts:")
        print(f"   Agents: {total_agents}")
        print(f"   Tools: {total_tools}")
        print(f"   Steps: {total_steps}")
        
        # Verify expected structure
        success = True
        if "expected_agents" in expected_structure:
            if total_agents != expected_structure["expected_agents"]:
                print(f"   ⚠️  Expected {expected_structure['expected_agents']} agents, got {total_agents}")
                success = False
        
        if "expected_tools" in expected_structure:
            if total_tools != expected_structure["expected_tools"]:
                print(f"   ⚠️  Expected {expected_structure['expected_tools']} tools, got {total_tools}")
                success = False
        
        if "expected_steps" in expected_structure:
            if total_steps != expected_structure["expected_steps"]:
                print(f"   ⚠️  Expected {expected_structure['expected_steps']} steps, got {total_steps}")
                success = False
        
        if success:
            print(f"\n✅ PASSED: Structure detected correctly!")
        else:
            print(f"\n⚠️  PARTIAL: Structure detected but counts differ")
        
        return success
    
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run comprehensive nested agent tests."""
    print("\n" + "="*70)
    print("🌳 COMPREHENSIVE NESTED AGENT DETECTION TEST SUITE")
    print("="*70)
    
    test_cases = [
        # TypeScript Tests
        ("TypeScript: Simple Nested Agents", """
export async function coordinatorAgent() {
    await plannerAgent();
    await executorAgent();
}

async function plannerAgent() {
    const response = await fetch('https://api.example.com/plan');
    return await response.json();
}

async function executorAgent() {
    const response = await fetch('https://api.example.com/execute');
    return await response.json();
}
""", "typescript", {"expected_agents": 3, "expected_tools": 0}),
        
        ("TypeScript: Agent with Tools", """
export async function researchAgent(query: string) {
    const searchResults = await webSearchTool(query);
    const analysis = await analyzeTool(searchResults);
    return analysis;
}

async function webSearchTool(query: string) {
    const response = await fetch(`https://api.example.com/search?q=${query}`);
    return await response.text();
}

async function analyzeTool(data: string) {
    const response = await fetch('https://api.example.com/analyze', {
        method: 'POST',
        body: JSON.stringify({ data })
    });
    return await response.json();
}
""", "typescript", {"expected_agents": 1, "expected_tools": 2}),
        
        ("TypeScript: Deep Nesting (3 levels)", """
export async function mainOrchestrator() {
    await coordinatorAgent();
}

async function coordinatorAgent() {
    await plannerAgent();
    await executorAgent();
}

async function plannerAgent() {
    await planningTool();
}

async function executorAgent() {
    await executionTool();
}

async function planningTool() {
    const response = await fetch('https://api.example.com/plan');
    return await response.json();
}

async function executionTool() {
    const response = await fetch('https://api.example.com/execute');
    return await response.json();
}
""", "typescript", {"expected_agents": 3, "expected_tools": 2}),
        
        ("TypeScript: Agent with Steps", """
export async function workflowAgent(data: string) {
    await extractStep(data);
    await transformStep(data);
    await loadStep(data);
}

async function extractStep(data: string) {
    const response = await fetch('https://api.example.com/extract', {
        method: 'POST',
        body: JSON.stringify({ data })
    });
    return await response.json();
}

async function transformStep(data: string) {
    const response = await fetch('https://api.example.com/transform', {
        method: 'POST',
        body: JSON.stringify({ data })
    });
    return await response.json();
}

async function loadStep(data: string) {
    const response = await fetch('https://api.example.com/load', {
        method: 'POST',
        body: JSON.stringify({ data })
    });
    return await response.json();
}
""", "typescript", {"expected_agents": 1, "expected_steps": 3}),
        
        ("TypeScript: Complex Hierarchy", """
export async function mainOrchestrator() {
    await planningAgent();
    await executionAgent();
    await reviewAgent();
}

async function planningAgent() {
    await planStep1();
    await planStep2();
}

async function executionAgent() {
    await execTool1();
    await execTool2();
    await execStep1();
}

async function reviewAgent() {
    await reviewTool();
}

async function planStep1() {
    const response = await fetch('https://api.example.com/plan1');
    return await response.json();
}

async function planStep2() {
    const response = await fetch('https://api.example.com/plan2');
    return await response.json();
}

async function execTool1() {
    const response = await fetch('https://api.example.com/exec1');
    return await response.json();
}

async function execTool2() {
    const response = await fetch('https://api.example.com/exec2');
    return await response.json();
}

async function execStep1() {
    const response = await fetch('https://api.example.com/exec-step1');
    return await response.json();
}

async function reviewTool() {
    const response = await fetch('https://api.example.com/review');
    return await response.json();
}
""", "typescript", {"expected_agents": 4, "expected_tools": 3, "expected_steps": 3}),
        
        # JavaScript Tests
        ("JavaScript: Nested Agents", """
async function coordinatorAgent() {
    await plannerAgent();
    await executorAgent();
}

async function plannerAgent() {
    const response = await fetch('https://api.example.com/plan');
    return await response.json();
}

async function executorAgent() {
    const response = await fetch('https://api.example.com/execute');
    return await response.json();
}
""", "javascript", {"expected_agents": 3, "expected_tools": 0}),
        
        ("JavaScript: Agent with Multiple Tools", """
async function researchAgent(query) {
    const searchResults = await webSearchTool(query);
    const analysis = await analyzeTool(searchResults);
    const summary = await summarizeTool(analysis);
    return summary;
}

async function webSearchTool(query) {
    const response = await fetch(`https://api.example.com/search?q=${query}`);
    return await response.text();
}

async function analyzeTool(data) {
    const response = await fetch('https://api.example.com/analyze', {
        method: 'POST',
        body: JSON.stringify({ data })
    });
    return await response.json();
}

async function summarizeTool(data) {
    const response = await fetch('https://api.example.com/summarize', {
        method: 'POST',
        body: JSON.stringify({ data })
    });
    return await response.json();
}
""", "javascript", {"expected_agents": 1, "expected_tools": 3}),
        
        # Go Tests
        ("Go: Nested Agents", """
package main

func coordinatorAgent() {
    plannerAgent()
    executorAgent()
}

func plannerAgent() {
    resp, _ := http.Get("https://api.example.com/plan")
    _ = resp.Body
}

func executorAgent() {
    resp, _ := http.Get("https://api.example.com/execute")
    _ = resp.Body
}
""", "go", {"expected_agents": 3, "expected_tools": 0}),
        
        ("Go: Agent with Tools", """
package main

func researchAgent(query string) string {
    results := webSearchTool(query)
    analysis := analyzeTool(results)
    return analysis
}

func webSearchTool(query string) string {
    resp, _ := http.Get("https://api.example.com/search?q=" + query)
    return resp.Body
}

func analyzeTool(data string) string {
    resp, _ := http.Post("https://api.example.com/analyze", "application/json", strings.NewReader(data))
    return resp.Body
}
""", "go", {"expected_agents": 1, "expected_tools": 2}),
        
        # Java Tests
        ("Java: Nested Agents", """
public class CoordinatorAgent {
    public void coordinatorAgent() {
        plannerAgent();
        executorAgent();
    }
    
    private void plannerAgent() {
        // HTTP call
    }
    
    private void executorAgent() {
        // HTTP call
    }
}
""", "java", {"expected_agents": 3, "expected_tools": 0}),
        
        ("Java: Agent with Tools", """
public class ResearchAgent {
    public String researchAgent(String query) {
        String results = webSearchTool(query);
        String analysis = analyzeTool(results);
        return analysis;
    }
    
    private String webSearchTool(String query) {
        // HTTP call
        return "results";
    }
    
    private String analyzeTool(String data) {
        // HTTP call
        return "analysis";
    }
}
""", "java", {"expected_agents": 1, "expected_tools": 2}),
        
        # Python Tests
        ("Python: Nested Agents", """
def coordinator_agent():
    planner_agent()
    executor_agent()

def planner_agent():
    import requests
    requests.get("https://api.example.com/plan")

def executor_agent():
    import requests
    requests.get("https://api.example.com/execute")
""", "python", {"expected_agents": 3, "expected_tools": 0}),
        
        ("Python: Agent with Tools", """
def research_agent(query: str):
    web_search_tool(query)
    analyze_tool(query)
    summarize_tool(query)

def web_search_tool(query: str):
    import requests
    requests.get(f"https://api.example.com/search?q={query}")

def analyze_tool(query: str):
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])

def summarize_tool(query: str):
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])
""", "python", {"expected_agents": 1, "expected_tools": 3}),
        
        ("Python: Deep Nesting (4 levels)", """
def main_orchestrator():
    coordinator_agent()

def coordinator_agent():
    planner_agent()
    executor_agent()

def planner_agent():
    planning_tool()

def executor_agent():
    execution_tool()

def planning_tool():
    import requests
    requests.get("https://api.example.com/plan")

def execution_tool():
    import requests
    requests.get("https://api.example.com/execute")
""", "python", {"expected_agents": 3, "expected_tools": 2}),
        
        ("Python: Complex Mixed Hierarchy", """
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
    requests.get("https://api.example.com/plan2")

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
""", "python", {"expected_agents": 4, "expected_tools": 3, "expected_steps": 3}),
        
        # TypeScript: Class-based nested agents
        ("TypeScript: Class-based Nested Agents", """
export class CoordinatorAgent {
    async run() {
        await this.plannerAgent();
        await this.executorAgent();
    }
    
    private async plannerAgent() {
        const response = await fetch('https://api.example.com/plan');
        return await response.json();
    }
    
    private async executorAgent() {
        const response = await fetch('https://api.example.com/execute');
        return await response.json();
    }
}
""", "typescript", {"expected_agents": 3, "expected_tools": 0}),
        
        # JavaScript: Arrow functions
        ("JavaScript: Arrow Function Agents", """
const coordinatorAgent = async () => {
    await plannerAgent();
    await executorAgent();
};

const plannerAgent = async () => {
    const response = await fetch('https://api.example.com/plan');
    return await response.json();
};

const executorAgent = async () => {
    const response = await fetch('https://api.example.com/execute');
    return await response.json();
};
""", "javascript", {"expected_agents": 3, "expected_tools": 0}),
        
        # TypeScript: Agent calling agent calling tool
        ("TypeScript: Agent -> Agent -> Tool", """
export async function mainAgent() {
    await subAgent();
}

async function subAgent() {
    await toolFunction();
}

async function toolFunction() {
    const response = await fetch('https://api.example.com/tool');
    return await response.json();
}
""", "typescript", {"expected_agents": 2, "expected_tools": 1}),
        
        # Python: Agent with loop calling tools
        ("Python: Agent Loop with Tools", """
def research_agent(query: str, iterations: int = 3):
    for i in range(iterations):
        web_search_tool(query)
        analyze_tool(query)

def web_search_tool(query: str):
    import requests
    requests.get(f"https://api.example.com/search?q={query}")

def analyze_tool(query: str):
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create(model="gpt-4", messages=[])
""", "python", {"expected_agents": 1, "expected_tools": 2}),
        
        # TypeScript: Multiple top-level agents
        ("TypeScript: Multiple Top-Level Agents", """
export async function researchAgent(query: string) {
    const response = await fetch(`https://api.example.com/research?q=${query}`);
    return await response.json();
}

export async function planningAgent(task: string) {
    const response = await fetch(`https://api.example.com/plan?task=${task}`);
    return await response.json();
}

export async function executionAgent(action: string) {
    const response = await fetch(`https://api.example.com/execute?action=${action}`);
    return await response.json();
}
""", "typescript", {"expected_agents": 3, "expected_tools": 0}),
    ]
    
    passed = 0
    failed = 0
    
    for name, code, language, expected in test_cases:
        success = test_nested_structure(name, code, language, expected)
        if success:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*70)
    print("📊 NESTED AGENT TEST SUMMARY")
    print("="*70)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📝 Total: {len(test_cases)}")
    accuracy = (passed / len(test_cases)) * 100
    print(f"🎯 Accuracy: {accuracy:.1f}%")
    print("="*70)
    
    if accuracy >= 90:
        print("\n🎉 EXCELLENT: Nested agent detection is very accurate!")
    elif accuracy >= 75:
        print("\n✅ GOOD: Nested agent detection is working well")
    elif accuracy >= 50:
        print("\n⚠️  MODERATE: Nested agent detection needs improvement")
    else:
        print("\n❌ POOR: Nested agent detection needs significant work")


if __name__ == "__main__":
    main()

